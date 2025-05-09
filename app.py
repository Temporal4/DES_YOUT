import streamlit as st
import yt_dlp
import subprocess
import os
import re

# Función para limpiar el título y eliminar caracteres no válidos para los nombres de archivo
def limpiar_titulo(titulo):
    # Reemplazar caracteres no válidos en el nombre del archivo
    return re.sub(r'[<>:"/\\|?*]', '_', titulo)

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

        # Limpiar el título para eliminar caracteres no válidos en el nombre de archivo
        nombre_limpio = limpiar_titulo(info['title'])

        # Definir el nombre del archivo final convertido a H.264
        nombre_salida = f"{nombre_limpio}.mp4"

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
        calidad = st.selectbox("Selecciona la calidad del video", ["alta", "normal", "baja"])
        url = st.text_input("Ingresa la URL del video de YouTube")

        # Cargar cookies opcionales
        cookies = st.file_uploader("Cargar cookies (opcional)", type=["txt"])

        if st.button("Descargar MP4"):
            if url:
                if cookies:
                    cookies = cookies.getvalue().decode("utf-8")
                descargar_mp4(url, calidad, cookies)
            else:
                st.error("Por favor, ingresa una URL válida.")

    elif tipo_archivo == "MP3":
        # Cargar múltiples links
        links_input = st.text_area("Ingresa hasta 10 enlaces de YouTube (uno por línea)")
        links = [link.strip() for link in links_input.split("\n") if link.strip()]

        # Cargar cookies opcionales
        cookies = st.file_uploader("Cargar cookies (opcional)", type=["txt"])

        if st.button("Descargar MP3"):
            if links:
                if cookies:
                    cookies = cookies.getvalue().decode("utf-8")
                descargar_mp3(links, cookies)
            else:
                st.error("Por favor, ingresa al menos un enlace.")

if __name__ == "__main__":
    main()
