import streamlit as st
import os
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# --- PENGATURAN HALAMAN ---
st.set_page_config(page_title="AutoClip Cuan Engine", page_icon="🎬", layout="wide")
st.title("📱 AutoClip Cuan Engine (Ultimate Edition)")
st.write("Sekali klik, AI akan membedah video, mencetak klip, dan menulis HEADLINE VIRAL untuk Anda!")

# --- SIDEBAR: KONTROL MESIN ---
st.sidebar.header("🔑 Panel Kendali Utama")
api_key = st.sidebar.text_input("1. Masukkan Gemini API Key:", type="password")

st.sidebar.markdown("---")
st.sidebar.header("🎥 Kendali Kamera")
posisi_kamera = st.sidebar.radio(
    "Posisi pembicara di video asli:",
    ("Tengah (Default)", "Kiri (Host)", "Kanan (Tamu)")
)

st.sidebar.markdown("---")
st.sidebar.header("🪄 Magic Multi-Clip")
jumlah_klip = st.sidebar.slider("Berapa klip yang ingin dicetak?", min_value=1, max_value=5, value=3)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Tameng Algoritma")
mode_antibanned = st.sidebar.checkbox("Aktifkan Anti-Banned TikTok", value=True)

if not api_key:
    st.warning("⚠️ Silakan masukkan Gemini API Key di panel sebelah kiri.")
    st.stop()

genai.configure(api_key=api_key)

@st.cache_resource(show_spinner=False)
def siapkan_model(_api_key):
    try:
        model_tersedia = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for nama in model_tersedia:
            if 'flash' in nama.lower() and '1.5' in nama.lower(): return genai.GenerativeModel(nama)
        for nama in model_tersedia:
            if 'pro' in nama.lower() and '1.5' in nama.lower(): return genai.GenerativeModel(nama)
        for nama in model_tersedia:
            if 'flash' in nama.lower(): return genai.GenerativeModel(nama)
        if model_tersedia: return genai.GenerativeModel(model_tersedia[0])
    except Exception: pass
    return None

model = siapkan_model(api_key)
if not model:
    st.error("⚠️ Gagal terhubung ke Otak AI.")
    st.stop()

def dapatkan_transkrip(url):
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id: return None, "Link YouTube tidak valid."
    vid = video_id.group(1)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(vid)
        try: transcript = transcript_list.find_transcript(['id'])
        except: transcript = transcript_list.find_transcript(['en'])
        transkrip_mentah = transcript.fetch()
        teks_full = " ".join([t['text'] for t in transkrip_mentah])
        return teks_full, None
    except Exception:
        try:
            ytt_api = YouTubeTranscriptApi()
            transkrip_mentah = ytt_api.fetch(vid, languages=['id', 'en'])
            teks_full = " ".join([t.text if hasattr(t, 'text') else t['text'] for t in transkrip_mentah])
            return teks_full, None
        except Exception as e2: return None, f"Gagal menyedot subtitle. Error: {e2}"

def cari_banyak_titik_potong(teks, jumlah):
    prompt = f"""
    Kamu adalah Copywriter dan Editor Video TikTok viral yang jenius. Temukan {jumlah} bagian PALING MENARIK dari teks ini.
    Syarat:
    1. Tiap bagian berdurasi 30-59 detik. Tidak boleh tumpang tindih waktunya.
    2. Buatkan 1 JUDUL HEADLINE (Hook) yang sangat clickbait, memancing rasa penasaran, maksimal 7 kata untuk tiap bagian!
    
    Wajib balas HANYA dengan format ini (pisahkan dengan garis vertikal '|'):
    Detik_Mulai | Detik_Selesai | JUDUL HEADLINE VIRAL
    
    Teks Transkrip:
    {teks}
    """
    try:
        response = model.generate_content(prompt)
        baris_waktu = response.text.strip().split('\n')
        hasil_klip = []
        for baris in baris_waktu:
            if '|' in baris:
                bagian = baris.split('|')
                try:
                    mulai = int(bagian[0].strip())
                    selesai = int(bagian[1].strip())
                    judul = bagian[2].strip()
                    hasil_klip.append((mulai, selesai, judul))
                except: pass
        return hasil_klip[:jumlah], None
    except Exception as e: return None, f"AI gagal merespon. Error: {e}"

def potong_video_sutradara(url, start, end, posisi, anti_banned, urutan):
    output_name = f"Klip_Viral_{urutan}.mp4"
    if os.path.exists(output_name): os.remove(output_name)
    
    if posisi == "Kiri (Host)": dasar_kamera = 'crop=ih*(9/16):ih:0:0'
    elif posisi == "Kanan (Tamu)": dasar_kamera = 'crop=ih*(9/16):ih:iw-ow:0'
    else: dasar_kamera = 'crop=ih*(9/16):ih'
        
    postprocessor_args = []
    if anti_banned:
        filter_visual = f"{dasar_kamera},setpts=0.95*PTS,eq=saturation=1.1"
        filter_audio = "atempo=1.05"
        postprocessor_args.extend(['-vf', filter_visual, '-af', filter_audio, '-map_metadata', '-1'])
    else:
        postprocessor_args.extend(['-vf', dasar_kamera])

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_name,
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
        'force_keyframes_at_cuts': True,
        'quiet': True,
        'postprocessor_args': postprocessor_args
    }
    
    # KECERDASAN DETEKSI LOKASI ALAT (Lokal vs Awan)
    markas_pabrik = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(markas_pabrik, "ffmpeg.exe")):
        ydl_opts['ffmpeg_location'] = markas_pabrik

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_name

# --- ANTARMUKA UTAMA ---
st.markdown("---")
url_youtube = st.text_input("🔗 Tempel Link YouTube di Sini:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🪄 Cetak Mesin Cuan Sekarang!"):
    if not url_youtube: st.error("Masukkan link YouTube dulu!")
    else:
        with st.status(f"🚀 Menjalankan Pabrik... (Target: {jumlah_klip} Klip)", expanded=True) as status:
            st.write("1️⃣ Menyedot transkrip video...")
            teks, err_teks = dapatkan_transkrip(url_youtube)
            if err_teks:
                status.update(label="Gagal", state="error"); st.error(err_teks)
            else:
                st.write(f"2️⃣ Otak Gemini sedang menyeleksi {jumlah_klip} Hook sekaligus menulis Headline...")
                daftar_klip, err_ai = cari_banyak_titik_potong(teks, jumlah_klip)
                
                if err_ai or not daftar_klip:
                    status.update(label="Gagal", state="error"); st.error("AI kebingungan mencari titik potong.")
                else:
                    st.success(f"Berhasil! AI telah meracik {len(daftar_klip)} video beserta Headline-nya!")
                    
                    st.markdown("### 🎬 Hasil Panen Kliping Anda:")
                    kolom_tampilan = st.columns(len(daftar_klip))
                    
                    for i, (mulai, selesai, judul_viral) in enumerate(daftar_klip):
                        urutan_klip = i + 1
                        st.write(f"⏳ Sedang menjahit Klip {urutan_klip}...")
                        try:
                            nama_file = potong_video_sutradara(url_youtube, mulai, selesai, posisi_kamera, mode_antibanned, urutan_klip)
                            
                            with kolom_tampilan[i]:
                                st.success(f"🔥 {judul_viral}") 
                                st.video(nama_file)
                                with open(nama_file, "rb") as file:
                                    st.download_button(
                                        label=f"⬇️ Download Video",
                                        data=file,
                                        file_name=f"Klip_MasterEwin_{urutan_klip}.mp4",
                                        mime="video/mp4",
                                        key=f"btn_dl_{urutan_klip}"
                                    )
                        except Exception as e:
                            st.error(f"Klip {urutan_klip} gagal diproses: {e}")
                    
                    status.update(label="✅ Produksi Massal Selesai!", state="complete", expanded=False)
