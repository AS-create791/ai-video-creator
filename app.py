
import os
import time
import asyncio
import streamlit as st
from deep_translator import GoogleTranslator
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Story Video Generator", page_icon="🎬", layout="centered")

st.title("🎬 এআই স্টোরি ভিডিও জেনারেটর (থাম্বনেইলসহ)")
st.write("আপনার গল্প, ভয়েস, ছবি এবং থাম্বনেইল দিয়ে সুন্দর ভিডিও তৈরি করুন।")

# ইনপুট সেকশন
user_story = st.text_area("আপনার গল্প বা টেক্সট এখানে লিখুন:", height=150)
selected_lang_code = st.selectbox("ভাষার কোড সিলেক্ট করুন (যেমন: bn, en):", ["bn", "en", "hi"])
selected_voice = st.selectbox("ভয়েস সিলেক্ট করুন:", ["bn-BD-PradeepNeural", "bn-BD-NabanitaNeural"])

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
                
                # ২. ন্যাচারাল ও মিষ্টি ভয়েস তৈরি (Edge-TTS)
                audio_path = os.path.join("temp_files", "voice.mp3")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
                success_audio = False
                for attempt in range(3):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(generate_edge_tts(translated_text, selected_voice, audio_path))
                        
                        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                            success_audio = True
                            break
                    except Exception:
                        time.sleep(2)
                
                if not success_audio:
                    raise Exception("অডিও তৈরি করতে সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।")
                
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                
                # ৩. থাম্বনেইল এবং একাধিক ছবির জন্য ক্লিপ তৈরি (এখানে টার্গেট সাইজ ৩০০ KB করা হয়েছে)
                image_clips = []
                
                thumbnail_duration = 1.5  
                if thumbnail_file is not None:
                    thumb_path = os.path.join("temp_files", "thumbnail_image.jpg")
                    # থাম্বনেইলের সাইজ ৩০০ KB করা হলো
                    compressed_thumb_bytes = compress_image_to_target_size(thumbnail_file, target_size_kb=300)
                    with open(thumb_path, "wb") as f:
                        f.write(compressed_thumb_bytes)
                    
                    thumb_clip = ImageClip(thumb_path, duration=thumbnail_duration)
                    image_clips.append(thumb_clip)
                
                remaining_duration = max(0, total_duration - thumbnail_duration) if thumbnail_file is not None else total_duration
                num_images = len(uploaded_images)
                clip_duration = remaining_duration / num_images if num_images > 0 else total_duration
                
                for i, target_image in enumerate(uploaded_images):
                    image_path = os.path.join("temp_files", f"processed_image_{i}.jpg")
                    
                    # মূল ছবিগুলোর সাইজ 500 KB করা হলো
                    compressed_bytes = compress_image_to_target_size(target_image, target_size_kb=300)
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
                
                st.success("🎉 ৩০০ কেবি সাইজ এবং থাম্বনেইলসহ ভিডিও সফলভাবে তৈরি হয়েছে!")
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
