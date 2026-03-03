import streamlit as st
import re
import os
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Autoclip Engine", layout="centered")

st.title("🚀 Autoclip Engine (Cloud Stable Edition)")
st.write("Sekali klik, AI membedah video, memotong klip, dan menulis HEADLINE VIRAL!")

# =========================
# AMBIL TRANSKRIP (FIXED VERSION)
# =========================
def dapatkan_transkrip(url):
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id:
        return None, "Link tidak valid"

    vid = video_id.group(1)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(vid)

        try:
            transcript = transcript_list.find_transcript(['id'])
        except:
            transcript = transcript_list.find_transcript(['en'])

        data = transcript.fetch()
        teks = " ".join([item['text'] for item in data])

        return teks, None

    except Exception as e:
        return None, f"Gagal ambil subtitle: {e}"


# =========================
# DOWNLOAD VIDEO
# =========================
def download_video(url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'video.mp4'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# =========================
# POTONG VIDEO (FFMPEG)
# =========================
def potong_video(start, durasi, output):
    command = [
        "ffmpeg",
        "-y",
        "-i", "video.mp4",
        "-ss", str(start),
        "-t", str(durasi),
        "-vf", "scale=720:1280",
        "-c:a", "copy",
        output
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# =========================
# UI
# =========================
url = st.text_input("Tempel Link YouTube:")

if st.button("🚀 Cetak Sekarang"):
    if not url:
        st.error("Masukkan link dulu!")
    else:
        with st.spinner("Memproses..."):
            
            # 1️⃣ Ambil Transkrip
            st.write("1️⃣ Mengambil transkrip...")
            teks, error = dapatkan_transkrip(url)

            if error:
                st.error(error)
                st.stop()

            st.success("Transkrip berhasil diambil!")

            # 2️⃣ Download Video
            st.write("2️⃣ Download video...")
            download_video(url)
            st.success("Video berhasil didownload!")

            # 3️⃣ Potong 60 detik pertama (demo)
            st.write("3️⃣ Membuat klip...")
            potong_video(0, 60, "hasil.mp4")
            st.success("Klip berhasil dibuat!")

            # 4️⃣ Tampilkan Hasil
            st.video("hasil.mp4")

            st.subheader("🧠 HEADLINE VIRAL:")
            st.write(teks[:200] + "...")
