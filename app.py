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

# 📌 Detecta el mejor formato disponible
def elegir_formato(url, cookies_path=None, solo_audio=False):
    opciones_info = {"quiet": True, "no_warnings": True}
    if cookies_path:
        opciones_info["cookiefile"] = cookies_path

    try:
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info = ydl.extract_info(url, download=False)
            formatos = info.get("formats", [])

            if solo_audio:
                # Buscar mejor formato de audio
                for f in reversed(formatos):
                    if f.get("acodec") != "none":
                        return f["format_id"]
            else:
                # Buscar mejor formato MP4
                for f in reversed(formatos):
                    if f.get("ext") == "mp4" and f.get("vcodec") != "none":
                        return f["format_id"]

            return "best"
    except yt_dlp.utils.DownloadError as e:
        if "Sign in to confirm your age" in str(e):
            raise Exception("⚠️ El video tiene restricción de edad. Sube tus cookies.")
        elif "This video is private" in str(e):
            raise Exception("❌ El video es privado. No se puede descargar sin acceso.")
        elif "HTTP Error 403" in str(e):
            raise Exception("🚫 Error 403: Acceso denegado. Puede ser por geobloqueo o cookies.")
        else:
            raise Exception(f"❌ No se pudo obtener información del video: {e}")

# 📌 Descargar MP4
def descargar_mp4(url, cookies_path=None):
    try:
        st.info("🔍 Buscando formatos MP4 disponibles...")
        formato_id = elegir_formato(url, cookies_path)

        opciones = {
            "format": formato_id,
            "outtmpl": "temp_video.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "http_headers": {"User-Agent": "Mozilla/5.0"}
        }
        if cookies_path:
            opciones["cookiefile"] = cookies_path

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
            titulo_video = limpiar_nombre(info.get("title", "video"))
            nombre_salida = f"{titulo_video}.mp4"

        subprocess.run([
            "ffmpeg", "-y", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
            nombre_salida
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(nombre_original)

        st.success("✅ Video descargado y convertido con éxito.")
        with open(nombre_salida, "rb") as f:
            st.download_button("⬇️ Descargar MP4", f, file_name=nombre_salida, mime="video/mp4")
        os.remove(nombre_salida)

    except Exception as e:
        st.error(str(e))

# 📌 Descargar MP3
def descargar_mp3(url, cookies_path=None):
    try:
        st.info("🔍 Buscando formatos de audio disponibles...")
        formato_id = elegir_formato(url, cookies_path, solo_audio=True)

        opciones = {
            "format": formato_id,
            "outtmpl": "temp_audio.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "http_headers": {"User-Agent": "Mozilla/5.0"}
        }
        if cookies_path:
            opciones["cookiefile"] = cookies_path

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
        st.error(str(e))

# 📌 Interfaz Streamlit
st.title("📥 Descargador de YouTube (MP4 y MP3)")
url = st.text_input("🎯 Pega la URL del video:")
opcion = st.radio("Selecciona formato:", ["MP4", "MP3"])
cookies_file = st.file_uploader("Subir cookies.txt (opcional)", type=["txt"])

if st.button("Descargar"):
    if url.strip():
        cookies_path = guardar_cookies_archivo(cookies_file)
        if opcion == "MP4":
            descargar_mp4(url, cookies_path)
        else:
            descargar_mp3(url, cookies_path)
    else:
        st.warning("⚠️ Por favor ingresa una URL válida.")
