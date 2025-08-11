import yt_dlp
import streamlit as st
import subprocess
import os
import re
import tempfile

# Limpia caracteres no válidos en nombres
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)

# Guardar cookies si las sube el usuario
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# Nueva función: elegir formato automáticamente
def elegir_formato(url, cookies_path=None):
    opciones_info = {
        "quiet": True,
        "no_warnings": True
    }
    if cookies_path:
        opciones_info["cookiefile"] = cookies_path

    try:
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info = ydl.extract_info(url, download=False)
            formatos = info.get("formats", [])
            # Buscar el mejor MP4 disponible
            for f in reversed(formatos):
                if f.get("ext") == "mp4" and f.get("vcodec") != "none":
                    return f["format_id"]
            return "best"  # fallback
    except yt_dlp.utils.DownloadError as e:
        if "Sign in to confirm your age" in str(e):
            raise Exception("⚠️ El video tiene restricción de edad. Sube tus cookies.")
        elif "This video is private" in str(e):
            raise Exception("❌ El video es privado. No se puede descargar sin acceso.")
        else:
            raise Exception(f"❌ No se pudo obtener información del video: {e}")

# Descargar MP4
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        st.info("🔍 Buscando formatos disponibles...")
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

        # Convertir a H.264
        subprocess.run([
            "ffmpeg", "-y", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
            nombre_salida
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(nombre_original)

        st.success("✅ Video descargado y convertido con éxito.")
        with open(nombre_salida, "rb") as f:
            st.download_button(
                label="⬇️ Descargar MP4",
                data=f,
                file_name=nombre_salida,
                mime="video/mp4"
            )
        os.remove(nombre_salida)

    except Exception as e:
        st.error(str(e))
