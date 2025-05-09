import streamlit as st
import yt_dlp
import subprocess
import os

# Función para descargar MP4
def descargar_mp4(url, calidad, cookies=None):
    try:
        archivo_temporal = "temp_video"
        nombre_salida = "video_convertido.mp4"

        # Configurar calidad
        if calidad == "alta":
            opciones = {'format': 'bestvideo+bestaudio/best', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        elif calidad == "normal":
            opciones = {'format': 'bv[height<=480]+ba/b[height<=480]', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        elif calidad == "baja":
            opciones = {'format': 'worstvideo+worstaudio/worst', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        else:
            st.error("Calidad no válida.")
            return

        if cookies:
            opciones['cookiefile'] = cookies

        # Descargar
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)

        # Convertir con FFmpeg
        subprocess.run([
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-preset", "fast", "-crf", "23",
            nombre_salida
        ])

        os.remove(nombre_original)
        st.success(f"✅ Video descargado y convertido: {nombre_salida}")
    except Exception as e:
        st.error(f"Error al descargar MP4: {e}")

# Función para descargar varios MP3
def descargar_mp3(links, cookies=None):
    try:
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

        if cookies:
            opciones['cookiefile'] = cookies

        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download(links)

        st.success("✅ MP3 descargado(s) con éxito")
    except Exception as e:
        st.error(f"Error al descargar MP3: {e}")

# Interfaz principal
def main():
    st.title("Descargador de YouTube: MP4 y MP3")

    tipo_archivo = st.selectbox("Selecciona el tipo de archivo", ["MP4", "MP3"])

    cookies = st.text_input("Ruta al archivo de cookies (opcional)")

    if tipo_archivo == "MP4":
        url = st.text_input("Ingresa el enlace del video (MP4)")
        calidad = st.selectbox("Selecciona la calidad del video", ["alta", "normal", "baja"])
        if st.button("Descargar"):
            if url:
                descargar_mp4(url, calidad, cookies if cookies else None)
            else:
                st.warning("Por favor ingresa un enlace válido.")
    elif tipo_archivo == "MP3":
        enlaces = st.text_area("Ingresa hasta 10 enlaces (uno por línea)")
        if st.button("Descargar"):
            links = [link.strip() for link in enlaces.strip().splitlines() if link.strip()]
            if links and len(links) <= 10:
                descargar_mp3(links, cookies if cookies else None)
            else:
                st.warning("Ingresa entre 1 y 10 enlaces válidos.")

if __name__ == "__main__":
    main()
