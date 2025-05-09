# app.py
import streamlit as st
import yt_dlp
import os
import shutil
from pathlib import Path

def descargar_videos(links, tipo, calidad, cookies=None):
    resultados = []
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    # Opciones comunes
    options = {
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'noplaylist': True
    }

    if cookies:
        options['cookiefile'] = cookies

    if tipo == 'MP3':
        options.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0'
            }]
        })
    else:  # MP4
        if calidad == 'Alta':
            fmt = 'bestvideo+bestaudio/best'
        elif calidad == 'Normal':
            fmt = 'bv[height<=480]+ba/b[height<=480]'
        else:  # Baja
            fmt = 'worstvideo+worstaudio/worst'

        options.update({
            'format': fmt,
            'merge_output_format': 'mp4'
        })

    with yt_dlp.YoutubeDL(options) as ydl:
        for link in links:
            try:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)
                ext = '.mp3' if tipo == 'MP3' else '.mp4'
                final_name = info['title'] + ext
                final_path = temp_dir / final_name
                if final_path.exists():
                    resultados.append((final_name, final_path))
            except Exception as e:
                resultados.append((f"Error al procesar: {link}", None))
    return resultados

st.title("Descargador de YouTube: MP3 / MP4")

with st.form("formulario"):
    tipo = st.radio("Selecciona el formato:", ['MP3', 'MP4'])
    calidad = None
    if tipo == 'MP4':
        calidad = st.selectbox("Selecciona la calidad:", ['Alta', 'Normal', 'Baja'])
    enlaces = st.text_area("Ingresa uno o varios enlaces de YouTube (1 por línea):")
    cookies = st.file_uploader("(Opcional) Sube archivo de cookies.txt para videos restringidos")
    submit = st.form_submit_button("Descargar")

if submit:
    links = [l.strip() for l in enlaces.strip().splitlines() if l.strip()]
    if not links:
        st.warning("Debes ingresar al menos un enlace válido.")
    else:
        st.info("Procesando las descargas... espera un momento.")
        cookie_path = None
        if cookies:
            cookie_path = Path("cookies.txt")
            with open(cookie_path, "wb") as f:
                f.write(cookies.read())

        resultados = descargar_videos(links, tipo, calidad, str(cookie_path) if cookie_path else None)

        for nombre, ruta in resultados:
            if ruta and ruta.exists():
                with open(ruta, "rb") as f:
                    st.download_button(f"Descargar {nombre}", f, file_name=nombre)
            else:
                st.error(nombre)

        # Limpiar cookies y archivos temporales
        if cookie_path and cookie_path.exists():
            cookie_path.unlink()
        shutil.rmtree("temp")
