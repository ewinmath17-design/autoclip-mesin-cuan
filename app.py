import streamlit as st
import os
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# ==============================
# PENGATURAN HALAMAN
# ==============================
st.set_page_config(page_title="AutoClip Cuan Engine", page_icon="🎬", layout="wide")
st.title("📱 AutoClip Cuan Engine (Cloud Stable Edition)")
st.write("Sekali klik, AI membedah video, memotong klip, dan menulis HEADLINE VIRAL!")

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("🔑 Panel Kendali")

api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

st.sidebar.markdown("---")
posisi_kamera = st.sidebar.radio(
    "Posisi pembicara:",
    ("Tengah", "Kiri", "Kanan")
)

st.sidebar.markdown("---")
jumlah_klip = st.sidebar.slider("Jumlah klip:", 1, 5, 3)

st.sidebar.markdown("---")
mode_antibanned = st.sidebar.checkbox("Aktifkan Anti-Banned", value=True)

if not api_key:
    st.warning("Masukkan Gemini API Key dulu.")
    st.stop()

genai.configure(api_key=api_key)

# ==============================
# LOAD MODEL GEMINI
# ==============================
@st.cache_resource
def load_model():
    models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    for m in models:
        if "flash" in m.lower():
            return genai.GenerativeModel(m)
    return genai.GenerativeModel(models[0])

model = load_model()

# ==============================
# AMBIL TRANSKRIP
# ==============================
def dapatkan_transkrip(url):
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id:
        return None, "Link tidak valid"

    vid = video_id.group(1)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['id','en'])
        teks = " ".join([t['text'] for t in transcript])
        return teks, None
    except Exception as e:
        return None, f"Gagal ambil subtitle: {e}"

# ==============================
# CARI TITIK POTONG AI
# ==============================
def cari_klip(teks, jumlah):
    prompt = f"""
    Temukan {jumlah} bagian paling menarik dari teks berikut.
    Durasi tiap bagian 30-59 detik.
    Format jawaban:
    DetikMulai | DetikSelesai | Judul Viral

    {teks}
    """

    try:
        response = model.generate_content(prompt)
        lines = response.text.strip().split("\n")

        hasil = []
        for l in lines:
            if "|" in l:
                parts = l.split("|")
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    title = parts[2].strip()
                    hasil.append((start, end, title))
                except:
                    pass
        return hasil[:jumlah], None
    except Exception as e:
        return None, str(e)

# ==============================
# POTONG VIDEO (VERSI STABIL)
# ==============================
def potong_video(url, start, end, posisi, anti_banned, urutan):

    output_name = f"klip_{urutan}.mp4"
    if os.path.exists(output_name):
        os.remove(output_name)

    # crop 9:16
    if posisi == "Kiri":
        crop = "crop=ih*(9/16):ih:0:0"
    elif posisi == "Kanan":
        crop = "crop=ih*(9/16):ih:iw-ow:0"
    else:
        crop = "crop=ih*(9/16):ih"

    filter_chain = crop

    if anti_banned:
        filter_chain += ",setpts=0.98*PTS,eq=saturation=1.05"
        audio_filter = "atempo=1.02"
    else:
        audio_filter = None

    post_args = ['-vf', filter_chain]
    if audio_filter:
        post_args += ['-af', audio_filter]

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_name,
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
        'force_keyframes_at_cuts': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'postprocessor_args': {
            'ffmpeg': post_args
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_name

# ==============================
# UI UTAMA
# ==============================
st.markdown("---")
url = st.text_input("Tempel Link YouTube:")

if st.button("🚀 Cetak Sekarang"):
    if not url:
        st.error("Masukkan link dulu")
    else:
        with st.status("Memproses...", expanded=True):

            st.write("1️⃣ Mengambil transkrip...")
            teks, err = dapatkan_transkrip(url)

            if err:
                st.error(err)
                st.stop()

            st.write("2️⃣ AI memilih bagian viral...")
            klip_list, err = cari_klip(teks, jumlah_klip)

            if err or not klip_list:
                st.error("AI gagal memilih klip")
                st.stop()

            st.success(f"Berhasil menemukan {len(klip_list)} klip!")

            cols = st.columns(len(klip_list))

            for i, (start, end, title) in enumerate(klip_list):
                with cols[i]:
                    st.write(f"⏳ Memproses klip {i+1}")

                    try:
                        file = potong_video(url, start, end, posisi_kamera, mode_antibanned, i+1)

                        st.success(title)
                        st.video(file)

                        with open(file, "rb") as f:
                            st.download_button(
                                "Download",
                                f,
                                file_name=f"klip_{i+1}.mp4",
                                mime="video/mp4"
                            )
                    except Exception as e:
                        st.error(f"Gagal proses klip {i+1}: {e}")

            st.success("✅ Semua proses selesai!")
