import os
import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS

# MoviePy এর বিভিন্ন ভার্সনের জন্য সেইফ ইম্পোর্ট
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip

# ১. পেজ সেটআপ
st.set_page_config(page_title="AI Story Video Maker", page_icon="🎬", layout="centered")

st.title("🎬 AI Story Video Maker")
st.write("আপনার গল্প এবং ছবি দিয়ে সহজে ভিডিও তৈরি করুন এবং গ্যালারিতে ডাউনলোড করুন!")

# ২. ইনপুট বক্স
user_story = st.text_area("আপনার গল্প এখানে লিখুন:", placeholder="এখানে গল্প লিখুন...")

# ভাষা নির্বাচনের ড্রপডাউন
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

# ৩. ছবি আপলোড
uploaded_image = st.file_uploader("আপনার গল্পের ছবি আপলোড করুন (JPG/PNG):", type=["jpg", "jpeg", "png"])

# ৪. ভিডিও তৈরির প্রক্রিয়া
if st.button("🎥 ভিডিও জেনারেট করুন"):
    if not user_story.strip():
        st.warning("দয়া করে কিছু গল্প লিখুন!")
    elif uploaded_image is None:
        st.warning("দয়া করে একটি ছবি আপলোড করুন!")
    else:
        with st.spinner("এআই ভিডিও তৈরি হচ্ছে, একটু অপেক্ষা করুন..."):
            try:
                os.makedirs("temp_files", exist_ok=True)
                image_path = os.path.join("temp_files", uploaded_image.name)
                
                with open(image_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())
                
                # ক. অনুবাদ
                translated_text = GoogleTranslator(source='auto', target=selected_lang_code).translate(user_story)
                
                # খ. ভয়েস তৈরি
                audio_path = os.path.join("temp_files", "voice.mp3")
                tts = gTTS(text=translated_text, lang=selected_lang_code, slow=False)
                tts.save(audio_path)
                
                # গ. ভিডিও তৈরি
                audio_clip = AudioFileClip(audio_path)
                image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
                video_clip = image_clip.set_audio(audio_clip)
                
                output_video_path = os.path.join("temp_files", "final_story_video.mp4")
                video_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")
                
                audio_clip.close()
                image_clip.close()
                video_clip.close()
                
                st.success("🎉 ভিডিও সফলভাবে তৈরি হয়েছে!")
                
                # ঘ. প্রিভিউ ও ডাউনলোড
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
                
              
