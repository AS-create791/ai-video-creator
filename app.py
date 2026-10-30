import os
import time
import asyncio
from io import BytesIO
import streamlit as st
from PIL import Image
from deep_translator import GoogleTranslator
import edge_tts

# MoviePy এর বিভিন্ন ভার্সনের জন্য সেইফ ইম্পোর্ট
try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Story Video Maker", page_icon="🎬", layout="centered")

st.title("🎬 AI Story Video Maker")
st.write("আপনার গল্প এবং একাধিক ছবি দিয়ে আকর্ষণীয় এআই ভয়েসসহ ভিডিও তৈরি করুন!")

user_story = st.text_area("আপনার গল্প এখানে লিখুন:", placeholder="এখানে গল্প লিখুন...")

language_option = st.selectbox(
    "ভয়েস এবং অনুবাদের ভাষা সিলেক্ট করুন:",
    ("বাংলা (Bengali)", "English", "हिन्दी (Hindi)")
)

lang_code_map = {
    "বাংলা (Bengali)": "bn",
    "English": "en",
    "हिन्दी (Hindi)": "hi"
}
selected_lang_code = lang_code_map[language_option]

# ভাষা অনুযায়ী আকর্ষণীয় ন্যাচারাল ভয়েস (প্রাকৃতিক কন্ঠস্বর) সিলেক্ট করা
voice_map = {
    "bn": "bn-BD-PradeepNeural",  # বাংলায় খুব সুন্দর ও মিষ্টি পুরুষ কন্ঠ (অথবা নারী কন্ঠের জন্য 'bn-BD-NabanitaNeural' দিতে পারেন)
    "en": "en-US-AriaNeural",     # ইংরেজিতে অত্যন্ত আকর্ষণীয় ও জনপ্রিয় নারী কন্ঠ
    "hi": "hi-IN-SwaraNeural"     # হিন্দিতে মিষ্টি ও ন্যাচারাল কন্ঠ
}
selected_voice = voice_map[selected_lang_code]

# একাধিক ছবি আপলোড করার সুবিধা
uploaded_images = st.file_uploader(
    "আপনার গল্পের ছবিগুলো আপলোড করুন (JPG/PNG):", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

# ছবিকে স্বয়ংক্রিয়ভাবে ১৯০ KB এর নিচে নামিয়ে আনার ফাংশন
def compress_image_to_target_size(image_file, target_size_kb=190):
    img = Image.open(image_file)
    img.thumbnail((1200, 1200))
    
    quality = 95
    output_io = BytesIO()
    
    while quality > 10:
        output_io.seek(0)
        output_io.truncate(0)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.save(output_io, format="JPEG", quality=quality)
        size_kb = output_io.tell() / 1024
        
        if size_kb <= target_size_kb:
            break
        quality -= 5
        
    return output_io.getvalue()

# এজ-টিটিএস দিয়ে ন্যাচারাল ভয়েস তৈরির অ্যাসিনক্রোনাস ফাংশন
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("🎥 ভিডিও জেনারেট করুন"):
    if not user_story.strip():
        st.warning("দয়া করে কিছু গল্প লিখুন!")
    elif not uploaded_images:
        st.warning("দয়া করে অন্তত একটি ছবি আপলোড করুন!")
    else:
        with st.spinner("আকর্ষণীয় এআই ভয়েস ও ভিডিও তৈরি হচ্ছে, একটু অপেক্ষা করুন..."):
            try:
                os.makedirs("temp_files", exist_ok=True)
                
                # ১. নিরাপদ অনুবাদ
                translated_text = ""
                for attempt in range(3):
                    try:
                        time.sleep(1)
                        translated_text = GoogleTranslator(source='auto', target=selected_lang_code).translate(user_story)
                        if translated_text:
                            break
                    except Exception:
                        time.sleep(3)
                
                if not translated_text:
                    translated_text = user_story
                
                # ২. ন্যাচারাল ও মিষ্টি ভয়েস তৈরি (Edge-TTS)
                audio_path = os.path.join("temp_files", "voice.mp3")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(generate_edge_tts(translated_text, selected_voice, audio_path))
                
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                
                # ৩. একাধিক ছবির জন্য ক্লিপ তৈরি
                num_images = len(uploaded_images)
                clip_duration = total_duration / num_images if num_images > 0 else total_duration
                
                image_clips = []
                for i, target_image in enumerate(uploaded_images):
                    image_path = os.path.join("temp_files", `processed_image_{i}.jpg`)
                    
                    compressed_bytes = compress_image_to_target_size(target_image, target_size_kb=190)
                    with open(image_path, "wb") as f:
                        f.write(compressed_bytes)
                    
                    img_clip = ImageClip(image_path, duration=clip_duration)
                    image_clips.append(img_clip)
                
                if len(image_clips) > 1:
                    final_image_clip = concatenate_videoclips(image_clips)
                else:
                    final_image_clip = image_clips[0]
                
                if hasattr(final_image_clip, "with_audio"):
                    video_clip = final_image_clip.with_audio(audio_clip)
                else:
                    video_clip = final_image_clip.set_audio(audio_clip)
                
                output_video_path = os.path.join("temp_files", "final_story_video.mp4")
                video_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")
                
                audio_clip.close()
                video_clip.close()
                
                st.success("🎉 আকর্ষণীয় ভয়েসসহ ভিডিও সফলভাবে তৈরি হয়েছে!")
                st.video(output_video_path)
                
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 গ্যালারিতে ভিডিও ডাউনলোড করুন",
                        data=file,
                        file_name="ai_story_video.mp4",
                        mime="video/mp4"
                    )
                    
            except Exception as e:
                st.error(f"একটি সমস্যা হয়েছে: {e}")
