import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import concurrent.futures
import re

# ------------------------------
# Función para limpiar nombres
# ------------------------------
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)

# ------------------------------
# Guardar archivo de cookies
# ------------------------------
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# ------------------------------
# Detectar causa de error
# ------------------------------
def detectar_causa_error(error_msg):
    e = error_msg.lower()
    if "cookies" in e or "login" in e:
        return "🔑 El video requiere cookies o inicio de sesión."
    elif "private" in e or "members-only" in e:
        return "🔒 El video es privado o solo para miembros."
    elif "403" in e:
        return "🚫 Acceso denegado (HTTP 403). Puede ser por restricción geográfica o de sesión."
    elif "unavailable" in e or "not available" in e:
        return "❌ El video no está disponible en el formato solicitado."
    else:
        return "⚠️ Error desconocido. Revisa la URL o tus cookies."

# ------------------------------
# Descargar MP4
# ------------------------------
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        archivo_temporal = "temp_video"

        # Fallbacks en formatos
        if calidad == "alta":
            formato = 'bestvideo+bestaudio/best'
        elif calidad == "normal":
            formato = 'bv[height<=480]+ba/b[height<=480]/best[height<=480]'
        elif calidad == "baja":
            formato = 'worstvideo+worstaudio/worst'
        else:
            st.error("Calidad no válida.")
            return None

        opciones = {
            'format': formato,
            'outtmpl': f'{archivo_temporal}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'headers': {'User-Agent': 'Mozilla/5.0'}
        }

        if cookies_path:
            opciones['cookiefile'] = cookies_path

        progreso = st.progress(0, text="🔄 Iniciando descarga...")

        with yt_dlp.YoutubeDL(opciones) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                st.error(detectar_causa_error(str(e)))
                return
            nombre_original = ydl.prepare_filename(info)
            titulo_video = limpiar_no
