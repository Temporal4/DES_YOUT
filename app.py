import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile

# Función para guardar archivo de cookies subido
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# Función para descargar video MP4
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        archivo_temporal = "temp_video"
        nombre_salida = "video_convertido.mp4"

        if calidad == "alta":
            opciones = {'format': 'bestvideo+bestaudio/best', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        elif calidad == "normal":
            opciones = {'format': 'bv[height<=480]+ba/b[height<=480]', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        elif calidad == "baja":
            opciones = {'format': 'worstvideo+worstaudio/worst', 'outtmpl': f'{archivo_temporal}.%(ext)s'}
        else:
            st.error("Calidad no válida.")
            return None

        if cookies_path:
            opciones['cookiefile'] = cookies_path

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
        st.success("✅ Video descargado y convertido con éxito")
        
        # Leer archivo convertido para descarga
        with open(nombre_salida, "rb") as f:
            st.download_button(
                label="⬇️ Descargar MP4",
                data=f,
                file_name=nombre_salida,
                mime="video/mp4"
            )
    except Exception as e:
        st.error(f"Error al descargar MP4: {e}")

# Función para descargar MP3
def descargar_mp3(links, cookies_path=None):
    try:
        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }],
        }

        if cookies_path:
            opciones['cookiefile'] = cookies_path

        for link in links:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(link, download=True)
                nombre = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
                if os.path.exists(nombre):
                    with open(nombre, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Descargar MP3: {os.path.basename(nombre)}",
                            data=f,
                            file_name=os.path.basename(nombre),
                            mime="audio/mpeg"
                        )

        st.success("✅ MP3 descargado(s) con éxito")
    except Exception as e:
        st.error(f"Error al descargar MP3: {e}")

# Interfaz principal
def main():
    st.title("Descargador de YouTube: MP4 y MP3")

    tipo_archivo = st.selectbox("Selecciona el tipo de archivo", ["MP4", "MP3"])
    cookies_file = st.file_uploader("Sube tu archivo de cookies (cookies.txt)", type=["txt"])
    cookies_path = guardar_cookies_archivo(cookies_file)

    if tipo_archivo == "MP4":
        url = st.text_input("Ingresa el enlace del video (MP4)")
        calidad = st.selectbox("Selecciona la calidad del video", ["alta", "normal", "baja"])
        if st.button("Descargar MP4"):
            if url:
                descargar_mp4(url, calidad, cookies_path)
            else:
                st.warning("Por favor ingresa un enlace válido.")

    elif tipo_archivo == "MP3":
        enlaces = st.text_area("Ingresa hasta 10 enlaces (uno por línea)")
        if st.button("Descargar MP3"):
            links = [link.strip() for link in enlaces.strip().splitlines() if link.strip()]
            if links and len(links) <= 10:
                descargar_mp3(links, cookies_path)
            else:
                st.warning("Ingresa entre 1 y 10 enlaces válidos.")

if __name__ == "__main__":
    main()
