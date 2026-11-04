
import os
import time
import streamlit as st
from deep_translator import GoogleTranslator
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
from PIL import Image
import io

st.set_page_config(page_title="AI Story Video Generator", page_icon="🎬", layout="centered")

st.title("🎬 এআই স্টোরি ভিডিও জেনারেটর (থাম্বনেইল ও ফিক্সড সাইজ)")
st.write("আপনার গল্প, ভয়েস, ছবি এবং থাম্বনেইল দিয়ে সুন্দর ভিডিও তৈরি করুন।")

# ছবিকে একদম নিখুঁত এইচডি সাইজে (১১২০x৭২০) ফিক্সড করে ৫০০ কেবির মধ্যে রাখার ফাংশন
def process_and_resize_image(uploaded_file, target_size_kb=500):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # ভিডিওর জন্য একটি নির্দিষ্ট স্ট্যান্ডার্ড সাইজ (যেমন ১২৮০x৭২০) ফিক্স করে দেওয়া হলো, যাতে ছবি না ফাটে
    target_width, target_height = 1280, 720
    
    # ইমেজকে সঠিক অনুপাতে রিসাইজ করে ব্যাকগ্রাউন্ড ঠিক করা
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    quality = 95
    while quality > 10:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        size_kb = buffer.tell() / 1024
        if size_kb <= target_size_kb or quality <= 15:
            break
        quality -= 5
    buffer.seek(0)
    return buffer.read()

# ইনপুট সেকশন
user_story = st.text_area("আপনার গল্প বা টেক্সট এখানে লিখুন:", height=150)

# ১. ভাষা সিলেক্ট করার অপশন (বাংলা, ইংরেজি, হিন্দি)
language_options = {
    "বাংলা (Bengali)": "bn",
    "English (ইংরেজি)": "en",
    "हिन्दी (Hindi)": "hi"
}
selected_lang_name = st.selectbox("ভাষার কোড সিলেক্ট করুন:", list(language_options.keys()))
selected_lang_code = language_options[selected_lang_name]

# একাধিক ছবি আপলোড অপশন
uploaded_images = st.file_uploader(
    "ভিডিওর মূল ছবিগুলো আপলোড করুন (একাধিক ছবি)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

# থাম্বনেইল আপলোড অপশন
thumbnail_file = st.file_uploader(
    "ভিডিওর জন্য কাস্টম থাম্বনেইল (Thumbnail) আপলোড করুন", 
    type=["jpg", "png", "jpeg"]
)

if st.button("🚀 ভিডিও তৈরি করুন"):
    if not user_story.strip():
        st.warning("দয়া করে কিছু টেক্সট বা গল্প লিখুন।")
    elif not uploaded_images:
        st.warning("দয়া করে অন্তত একটি ছবি আপলোড করুন।")
    else:
        if not os.path.exists("temp_files"):
            os.makedirs("temp_files")
            
        with st.spinner("ভিডিও তৈরি হচ্ছে, দয়া করে অপেক্ষা করুন..."):
            try:
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
                
                # ২. gTTS দিয়ে অডিও তৈরি
                audio_path = os.path.join("temp_files", "voice.mp3")
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                
                success_audio = False
                for attempt in range(3):
                    try:
                        tts = gTTS(text=translated_text, lang=selected_lang_code, slow=False)
                        tts.save(audio_path)
                        
                        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                            success_audio = True
                            break
                    except Exception:
                        time.sleep(2)
                
                if not success_audio:
                    raise Exception("অডিও তৈরি করতে সমস্যা হয়েছে। দয়া করে ইন্টারনেট কানেকশন চেক করুন।")
                
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                
                # ৩. থাম্বনেইল এবং একাধিক ছবির জন্য ক্লিপ তৈরি (ফিক্সড সাইজসহ)
                image_clips = []
                
                thumbnail_duration = 1.5  
                if thumbnail_file is not None:
                    thumb_path = os.path.join("temp_files", "thumbnail_image.jpg")
                    compressed_thumb_bytes = process_and_resize_image(thumbnail_file, target_size_kb=500)
                    with open(thumb_path, "wb") as f:
                        f.write(compressed_thumb_bytes)
                    
                    thumb_clip = ImageClip(thumb_path, duration=thumbnail_duration)
                    image_clips.append(thumb_clip)
                
                remaining_duration = max(0, total_duration - thumbnail_duration) if thumbnail_file is not None else total_duration
                num_images = len(uploaded_images)
                clip_duration = remaining_duration / num_images if num_images > 0 else total_duration
                
                for i, target_image in enumerate(uploaded_images):
                    image_path = os.path.join("temp_files", f"processed_image_{i}.jpg")
                    
                    compressed_bytes = process_and_resize_image(target_image, target_size_kb=500)
                    with open(image_path, "wb") as f:
                        f.write(compressed_bytes)
                    
                    img_clip = ImageClip(image_path, duration=clip_duration)
                    image_clips.append(img_clip)
                
                if len(image_clips) > 1:
                    final_image_clip = concatenate_videoclips(image_clips, method="compose")
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
                
                st.success("🎉 এবার ছবি আর ফাটবে না! একদম পরিষ্কার ভিডিও তৈরি হয়েছে!")
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
