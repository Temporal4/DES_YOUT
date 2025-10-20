import yt_dlp
import streamlit as st
import subprocess
import os
import re
import tempfile

# 📌 Limpia caracteres no válidos de nombres
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)

# 📌 Guarda cookies si el usuario sube un archivo
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# 📌 Obtener configuración según calidad
def opciones_por_calidad(calidad, cookies_path=None):
    opciones = {'outtmpl': 'temp_video.%(ext)s', 'quiet': True, 'no_warnings': True}
    if cookies_path:
        opciones['cookiesfromfile'] = cookies_path

    if calidad == "alta":
        opciones['format'] = 'bestvideo+bestaudio/best'
    elif calidad == "normal":
        opciones['format'] = 'bv[height<=480]+ba/b[height<=480]'
    elif calidad == "baja":
        opciones['format'] = 'worstvideo+worstaudio/worst'
    else:
        opciones['format'] = 'best'
    return opciones

# 📌 Descargar MP4
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        st.info(f"🎬 Descargando video en calidad **{calidad.upper()}**...")
        opciones = opciones_por_calidad(calidad, cookies_path)

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
            titulo_video = limpiar_nombre(info.get("title", "video"))
            nombre_salida = f"{titulo_video}.mp4"

        # Convertir a H.264 MP4
        comando_ffmpeg = [
            "ffmpeg", "-y", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
            nombre_salida
        ]
        subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(nombre_original)

        st.success("✅ Video descargado y convertido con éxito.")
        with open(nombre_salida, "rb") as f:
            st.download_button("⬇️ Descargar MP4", f, file_name=nombre_salida, mime="video/mp4")
        os.remove(nombre_salida)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# 📌 Descargar MP3
def descargar_mp3(url, cookies_path=None):
    try:
        st.info("🎧 Descargando audio...")
        opciones = {'format': 'bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True}
        if cookies_path:
            opciones['cookiesfromfile'] = cookies_path

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
            titulo_audio = limpiar_nombre(info.get("title", "audio"))
            nombre_salida = f"{titulo_audio}.mp3"

        subprocess.run([
            "ffmpeg", "-y", "-i", nombre_original,
            "-vn", "-ab", "192k", "-ar", "44100", "-f", "mp3",
            nombre_salida
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(nombre_original)

        st.success("✅ Audio descargado con éxito.")
        with open(nombre_salida, "rb") as f:
            st.download_button("⬇️ Descargar MP3", f, file_name=nombre_salida, mime="audio/mpeg")
        os.remove(nombre_salida)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# 📌 Interfaz Streamlit
st.title("📥 Descargador de YouTube (MP4 y MP3 mejorado)")
url = st.text_input("🎯 Pega la URL del video:")
opcion = st.radio("Selecciona formato:", ["MP4", "MP3"])
cookies_file = st.file_uploader("Subir cookies.txt (opcional)", type=["txt"])

if opcion == "MP4":
    calidad = st.selectbox("Elige la calidad:", ["alta", "normal", "baja"])
else:
    calidad = None

if st.button("Descargar"):
    if url.strip():
        cookies_path = guardar_cookies_archivo(cookies_file)
        if opcion == "MP4":
            descargar_mp4(url, calidad, cookies_path)
        else:
            descargar_mp3(url, cookies_path)
    else:
        st.warning("⚠️ Por favor ingresa una URL válida.")
