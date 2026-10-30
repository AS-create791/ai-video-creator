import os
import time
from io import BytesIO
import streamlit as st
from PIL import Image
from deep_translator import GoogleTranslator
from gtts import gTTS

# MoviePy এর বিভিন্ন ভার্সনের জন্য সেইফ ইম্পোর্ট
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip

st.set_page_config(page_title="AI Story Video Maker", page_icon="🎬", layout="centered")

st.title("🎬 AI Story Video Maker")
st.write("আপনার গল্প এবং ছবি দিয়ে সহজে ভিডিও তৈরি করুন!")

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

# একাধিক ছবি আপলোড করার সুবিধা (Multiple File Uploader)
uploaded_images = st.file_uploader(
    "আপনার গল্পের ছবিগুলো আপলোড করুন (JPG/PNG):", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

# ছবিকে নির্দিষ্ট সাইজের (যেমন ১৯০ KB এর নিচে) আনার ফাংশন
def compress_image_to_target_size(image_file, target_size_kb=190):
    img = Image.open(image_file)
    
    # যদি ছবি অনেক বড় হয়, রেজোলিউশ একটু কমিয়ে নেওয়া ভালো
    img.thumbnail((1200, 1200))
    
    quality = 95
    output_io = BytesIO()
    
    # লুপ চালিয়ে কোয়ালিটি কমিয়ে কাঙ্ক্ষিত সাইজে নিয়ে আসা
    while quality > 10:
        output_io.seek(0)
        output_io.truncate(0)
        
        # RGB মোডে কনভার্ট করা (PNG বা অন্য ফরম্যাটের জন্য জরুরি)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.save(output_io, format="JPEG", quality=quality)
        size_kb = output_io.tell() / 1024
        
        if size_kb <= target_size_kb:
            break
        quality -= 5
        
    return output_io.getvalue()

if st.button("🎥 ভিডিও জেনারেট করুন"):
    if not user_story.strip():
        st.warning("দয়া করে কিছু গল্প লিখুন!")
    elif not uploaded_images:
        st.warning("দয়া করে অন্তত একটি ছবি আপলোড করুন!")
    else:
        with st.spinner("এআই ভিডিও তৈরি হচ্ছে, একটু অপেক্ষা করুন... প্রস্তুত করা হচ্ছে..."):
            try:
                os.makedirs("temp_files", exist_ok=True)
                
                # প্রথম ছবি নিয়ে আপাতত কাজ শুরু করছি (একাধিক ছবি হলে পরবর্তীতে লুপ চালাতে পারবেন)
                target_image = uploaded_images[0]
                image_path = os.path.join("temp_files", "processed_image.jpg")
                
                # স্বয়ংক্রিয়ভাবে ১৯০ KB এর নিচে কম্প্রেস করে সেভ করা
                compressed_bytes = compress_image_to_target_size(target_image, target_size_kb=190)
                with open(image_path, "wb") as f:
                    f.write(compressed_bytes)
                
                time.sleep(1)
                
                # অনুবাদ
                try:
                    translated_text = GoogleTranslator(source='auto', target=selected_lang_code).translate(user_story)
                except Exception:
                    time.sleep(2)
                    translated_text = GoogleTranslator(source='auto', target=selected_lang_code).translate(user_story)
                
                # ভয়েস তৈরি
                audio_path = os.path.join("temp_files", "voice.mp3")
                tts = gTTS(text=translated_text, lang=selected_lang_code, slow=False)
                tts.save(audio_path)
                
                # ভিডিও তৈরি
                audio_clip = AudioFileClip(audio_path)
                image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
                video_clip = image_clip.set_audio(audio_clip)
                
                output_video_path = os.path.join("temp_files", "final_story_video.mp4")
                video_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")
                
                audio_clip.close()
                image_clip.close()
                video_clip.close()
                
                st.success("🎉 ভিডিও সফলভাবে তৈরি হয়েছে!")
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
                
                
              
