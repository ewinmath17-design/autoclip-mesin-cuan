import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import os
import subprocess
import re

# --- 1. SETUP TAMPILAN HALAMAN ---
st.set_page_config(page_title="AutoClip Cuan Engine - Ultimate", page_icon="📱", layout="wide")

# ==========================================
# 🔒 SISTEM GEMBOK KEAMANAN VIP 🔒
# ==========================================
st.sidebar.markdown("### 🔑 Gerbang Akses VIP")
kode_akses = st.sidebar.text_input("Masukkan Password VIP Anda:", type="password")

# Ganti "CUAN99" dengan password rahasia yang akan Master berikan ke pembeli
PASSWORD_RAHASIA = "CUAN99" 

if kode_akses != PASSWORD_RAHASIA:
    st.error("🚨 MESIN TERKUNCI! Silakan masukkan Password VIP di panel kiri untuk membuka pabrik.")
    st.info("💡 Belum punya akses? Hubungi Admin Kavling Digital untuk membeli lisensi.")
    st.stop() # Menghentikan mesin agar tidak bisa dipakai sebelum login
# ==========================================

# CSS Premium untuk tampilan aplikasi
st.markdown("""
<style>
    .main-title { color: #D32F2F; font-size: 36px; font-weight: 900; font-family: 'Arial Black', sans-serif; text-align: center; margin-bottom: 5px; }
    .sub-title { color: #555; text-align: center; font-size: 16px; margin-bottom: 30px; }
    .success-box { background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 10px; }
    .txt-box { background-color: #FFFDE7; padding: 10px; border-radius: 5px; border: 1px dashed #FBC02D; font-family: monospace; font-size: 12px; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 2. PANEL KENDALI (SIDEBAR) ---
st.sidebar.markdown("### ⚙️ Pengaturan Mesin")
api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password", help="Dapatkan API Key gratis di Google AI Studio")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎥 Kendali Kamera")
kamera_fokus = st.sidebar.radio("Posisi pembicara di video asli:", ["Tengah (Default)", "Kiri (Host)", "Kanan (Tamu)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎬 Magic Multi-Clip")
jumlah_klip = st.sidebar.slider("Berapa klip yang ingin dicetak?", min_value=1, max_value=20, value=3)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Tameng Algoritma")
anti_banned = st.sidebar.checkbox("Aktifkan Anti-Banned (TikTok/FB Pro)", value=True, help="Manipulasi durasi 5% agar lolos filter unoriginal content")

# --- 3. TAMPILAN UTAMA ---
st.markdown('<div class="main-title">📱 AutoClip Cuan Engine (Ultimate Edition)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sekali klik, AI akan membedah video, mencetak puluhan klip vertikal, dan menulis File Caption untuk Anda!</div>', unsafe_allow_html=True)

link_youtube = st.text_input("🔗 Tempel Link YouTube di Sini:", placeholder="https://www.youtube.com/watch?v=...")

# --- FUNGSI PENDUKUNG ---
def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def bersihkan_nama_file(teks):
    return re.sub(r'[\\/*?:"<>|]', "", teks)

def proses_pemotongan_video(url, start, end, output_filename, fokus, anti_ban):
    if fokus == "Kiri (Host)":
        crop_filter = "crop=ih*9/16:ih:0:0"
    elif fokus == "Kanan (Tamu)":
        crop_filter = "crop=ih*9/16:ih:iw-ih*9/16:0"
    else:
        crop_filter = "crop=ih*9/16:ih:iw/2-ih*9/32:0" 

    if anti_ban:
        filter_kompleks = f"{crop_filter},setpts=0.95*PTS;atempo=1.05"
    else:
        filter_kompleks = crop_filter

    cmd = [
        "yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4", 
        "--download-sections", f"*{start}-{end}",
        "-o", output_filename,
        "--force-keyframes-at-cuts",
        "--postprocessor-args", f"ffmpeg: -vf {filter_kompleks}",
        url
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        return False

# --- 4. MESIN UTAMA BERJALAN ---
if st.button("🪄 Cetak Mesin Cuan Sekarang!", use_container_width=True):
    if not api_key:
        st.error("🚨 Harap masukkan Gemini API Key di panel kiri terlebih dahulu!")
    elif not link_youtube:
        st.error("🚨 Harap tempelkan link YouTube yang valid!")
    else:
        video_id = get_video_id(link_youtube)
        
        if video_id:
            with st.status("🚀 Mengoperasikan Pabrik Cuan...", expanded=True) as status:
                
                # LANGKAH 1: MENYEDOT TRANSKRIP (VERSI TERBARU)
                st.write("1️⃣ Menyedot transkrip video dari YouTube...")
                try:
                    ytt_api = YouTubeTranscriptApi()
                    fetched = ytt_api.fetch(video_id, languages=['id', 'en'])
                    transcript_list = fetched.to_raw_data()
                    full_text = " ".join([t['text'] for t in transcript_list])
                    st.success("Transkrip berhasil disedot!")
                except Exception as e:
                    status.update(label="❌ Gagal Menyedot Transkrip", state="error", expanded=True)
                    st.error(f"Video ini tidak memiliki Subtitle/CC yang menyala. Silakan gunakan video lain. Detail: {e}")
                    st.stop()

                # LANGKAH 2: OTAK GEMINI BEKERJA
                st.write(f"2️⃣ Otak Gemini sedang menyeleksi {jumlah_klip} momen viral & menulis file Caption...")
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    
                    prompt = f"""
                    Kamu adalah Copywriter Direct Response dan Video Editor pro. Analisis transkrip YouTube ini.
                    Cari {jumlah_klip} momen paling viral, memancing emosi, atau penuh daging berdurasi 30 hingga 59 detik.
                    
                    Untuk setiap klip, kamu WAJIB membalas dengan format KAKU dipisahkan oleh tanda `|` seperti ini:
                    [Waktu Mulai Detik] | [Waktu Selesai Detik] | [Judul Clickbait Maks 7 Kata] | [Caption TikTok yang memancing interaksi] | [3-5 Hashtag Viral]
                    
                    Contoh:
                    120 | 165 | BONGKAR RAHASIA KAYA DARI NOL! | Ternyata begini rahasia bandar mainin uang kita! Tonton sampai habis biar gak jadi korban. Gimana menurut kalian? | #bisnis #cuan #investasi
                    
                    PENTING: Hanya balas dengan format di atas, jangan ada teks tambahan!
                    
                    Transkrip:
                    {full_text[:25000]}
                    """
                    
                    response = model.generate_content(prompt)
                    hasil_gemini = response.text.strip().split('\n')
                    
                    hasil_gemini = [baris for baris in hasil_gemini if "|" in baris]
                    
                    if not hasil_gemini:
                        st.error("AI kebingungan mencari titik potong. Coba video yang bahasanya lebih jelas.")
                        st.stop()
                        
                    st.success(f"Berhasil! AI telah meracik {len(hasil_gemini)} ide konten beserta naskahnya!")
                    
                except Exception as e:
                    status.update(label="❌ AI Mengalami Kendala", state="error", expanded=True)
                    st.error(f"Gagal memproses AI. Pastikan API Key benar. Detail: {e}")
                    st.stop()

                # LANGKAH 3: PEMOTONGAN & PEMBUATAN FILE TXT
                st.write("3️⃣ Gunting Mesin menyala! Mulai memotong video dan mencetak File Teks...")
                
                output_folder = "Hasil_Panen_Cuan"
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                kolom_hasil = st.columns(min(3, len(hasil_gemini)))
                
                for i, data in enumerate(hasil_gemini):
                    try:
                        parts = data.split('|')
                        start_time = int(float(parts[0].strip()))
                        end_time = int(float(parts[1].strip()))
                        judul = bersihkan_nama_file(parts[2].strip())
                        caption = parts[3].strip()
                        hashtags = parts[4].strip()
                        
                        nama_file_mp4 = os.path.join(output_folder, f"Klip_{i+1}_{judul}.mp4")
                        nama_file_txt = os.path.join(output_folder, f"Caption_{i+1}.txt")
                        
                        st.write(f"⏳ Sedang menjahit Klip {i+1}: *{judul}*...")
                        
                        sukses_potong = proses_pemotongan_video(link_youtube, start_time, end_time, nama_file_mp4, kamera_fokus, anti_banned)
                        
                        if sukses_potong:
                            with open(nama_file_txt, "w", encoding="utf-8") as f:
                                f.write(f"🔥 JUDUL DI VIDEO:\n{judul}\n")
                                f.write("=" * 30 + "\n\n")
                                f.write(f"📝 CAPTION TIKTOK (Siap Copy-Paste):\n{caption}\n\n")
                                f.write(f"🏷️ HASHTAG:\n{hashtags}\n")

                            col_idx = i % 3
                            with kolom_hasil[col_idx]:
                                st.markdown(f'<div class="success-box"><b>🔥 KLIP {i+1}:</b><br>{judul}</div>', unsafe_allow_html=True)
                                if os.path.exists(nama_file_mp4):
                                    st.video(nama_file_mp4)
                                    with open(nama_file_mp4, "rb") as vid_file:
                                        st.download_button(label=f"⬇️ Download Video {i+1}", data=vid_file, file_name=f"{judul}.mp4", mime="video/mp4", key=f"vid_{i}")
                                
                                st.markdown(f'<div class="txt-box"><b>📝 PREVIEW CAPTION:</b><br>{caption}<br><br>{hashtags}</div>', unsafe_allow_html=True)
                                with open(nama_file_txt, "rb") as txt_file:
                                    st.download_button(label=f"📄 Download Text Caption", data=txt_file, file_name=f"Caption_Klip_{i+1}.txt", mime="text/plain", key=f"txt_{i}")
                                    
                    except Exception as e:
                        st.warning(f"Klip {i+1} dilewati karena kegagalan render.")

                status.update(label="✅ PABRIK MASIF SELESAI! SEMUA KONTEN SIAP UPLOAD!", state="complete", expanded=True)
                st.balloons()
