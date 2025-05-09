import streamlit as st
import yt_dlp
import subprocess
import os

# Función para descargar MP4
def descargar_mp4(url, calidad, cookies=None):
    try:
        # Ruta temporal para descargar el archivo
        archivo_temporal = "temp_video"

        # Opciones de descarga según la calidad seleccionada
        if calidad == "alta":
            opciones = {
                'format': 'bestvideo+bestaudio/best',  # Mejor calidad de video y audio
                'outtmpl': f'{archivo_temporal}.%(ext)s'  # Guardar como archivo temporal
            }
        elif calidad == "normal":
            opciones = {
                'format': 'bv[height<=480]+ba/b[height<=480]',  # Calidad estándar (480p o menor)
                'outtmpl': f'{archivo_temporal}.%(ext)s'  # Guardar como archivo temporal
            }
        elif calidad == "baja":
            opciones = {
                'format': 'worstvideo+worstaudio/worst',  # Peor calidad posible
                'outtmpl': f'{archivo_temporal}.%(ext)s'  # Guardar como archivo temporal
            }
        else:
            st.error("Por favor selecciona una opción válida: alta, normal o baja.")
            return

        if cookies:
            opciones['cookiefile'] = cookies  # Cargar cookies si se proporcionan

        # Descargar el video
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)  # Descargar video
            nombre_original = ydl.prepare_filename(info)  # Obtener el nombre original del archivo

        # Definir el nombre del archivo final convertido a H.264
        nombre_salida = f"{info['title']}.mp4"

        # Convertir el video descargado a H.264 usando FFmpeg (incluyendo el audio)
        comando_ffmpeg = [
            "ffmpeg",
            "-i", nombre_original,            # Archivo de entrada
            "-c:v", "libx264",                # Codificación H.264 para video
            "-c:a", "aac",                    # Codificación AAC para audio
            "-strict", "experimental",        # Compatibilidad para formatos más antiguos
            "-preset", "fast",                # Mejor rendimiento
            "-crf", "23",                     # Calidad de codificación (ajustable)
            nombre_salida                     # Archivo de salida
        ]

        # Ejecutar la conversión
        subprocess.run(comando_ffmpeg)

        # Eliminar el archivo temporal original
        os.remove(nombre_original)

        st.success(f"Descarga y conversión completadas. Archivo guardado como: {nombre_salida}")
    except Exception as e:
        st.error(f"Error al descargar o convertir el video: {e}")


# Función para descargar MP3 (soporte múltiples links)
def descargar_mp3(links, cookies=None):
    try:
        # Opciones de descarga para MP3
        opciones = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',  # Calidad máxima
            }],
        }

        if cookies:
            opciones['cookiefile'] = cookies  # Cargar cookies si se proporcionan

        # Descargar los audios
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download(links)

        st.success("✅ Descarga completada con éxito 🎵")
    except Exception as e:
        st.error(f"Error al descargar los audios: {e}")


# Streamlit app interface
def main():
    st.title("YouTube Downloader")

    # Selección de tipo de archivo
    tipo_archivo = st.selectbox("Selecciona el tipo de archivo", ["MP4", "MP3"])

    # Opciones de calidad
    if tipo_archivo == "MP4":
        calidad = st.selectbox("Selecciona la
