import streamlit as st
import yt_dlp
import subprocess
import os

st.set_page_config(page_title="Descargador YouTube", layout="centered")

st.title("📥 Descargador de YouTube (MP3 / MP4)")
st.write("Selecciona el formato, calidad y pega el link del video de YouTube.")

formato = st.selectbox("Formato", ["MP4", "MP3"])
calidad = st.selectbox("Calidad", ["Alta", "Normal", "Baja"] if formato == "MP4" else ["Mejor calidad disponible"])
url = st.text_input("🔗 Enlace de YouTube (uno solo por ahora)")

usar_cookies = st.checkbox("¿Usar archivo de cookies (solo para videos con restricción)?")
cookies_file = None
if usar_cookies:
    cookies_file = st.file_uploader("Sube tu archivo cookies.txt", type="txt")

if st.button("Descargar"):
    if not url:
        st.error("Por favor, ingresa un enlace de YouTube.")
    else:
        archivo_temp = "temp_file"
        try:
            with open("cookies.txt", "wb") as f:
                if cookies_file:
                    f.write(cookies_file.getvalue())

            if formato == "MP4":
                if calidad == "Alta":
                    fmt = 'bestvideo+bestaudio/best'
                elif calidad == "Normal":
                    fmt = 'bv[height<=480]+ba/b[height<=480]'
                else:
                    fmt = 'worstvideo+worstaudio/worst'
                opciones = {
                    'format': fmt,
                    'outtmpl': f'{archivo_temp}.%(ext)s'
                }
            else:  # MP3
                opciones = {
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'outtmpl': '%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '0',
                    }],
                }

            if usar_cookies and cookies_file:
                opciones["cookiefile"] = "cookies.txt"

            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=True)
                if formato == "MP4":
                    nombre_original = ydl.prepare_filename(info)
                    salida = f"{info['title']}.mp4"
                    st.write("Convirtiendo a H.264...")
                    subprocess.run([
                        "ffmpeg", "-i", nombre_original,
                        "-c:v", "libx264", "-c:a", "aac",
                        "-strict", "experimental", salida
                    ])
                    os.remove(nombre_original)
                    st.success("✅ Video descargado y convertido.")
                else:
                    st.success("✅ Audio descargado.")

        except Exception as e:
            st.error(f"Error: {e}")
