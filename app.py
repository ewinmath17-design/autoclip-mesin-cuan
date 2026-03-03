import streamlit as st
import re
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Autoclip Engine", layout="centered")

st.title("🚀 Autoclip Engine (Ultra Stable)")
st.write("Sekali klik, AI membedah video & membuat klip!")

# =========================
# AMBIL TRANSKRIP (VERSI PALING AMAN)
# =========================
def dapatkan_transkrip(url):
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    
    if not video_id_match:
        return None, "Link YouTube tidak valid"

    video_id = video_id_match.group(1)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        teks = " ".join([item['text'] for item in transcript])
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
# POTONG VIDEO
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

            # 3️⃣ Potong 60 detik pertama
            st.write("3️⃣ Membuat klip...")
            potong_video(0, 60, "hasil.mp4")
            st.success("Klip berhasil dibuat!")

            st.video("hasil.mp4")

            st.subheader("🧠 HEADLINE SAMPLE:")
            st.write(teks[:300] + "...")
