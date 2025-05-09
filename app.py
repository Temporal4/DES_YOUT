import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import concurrent.futures

# Guardar archivo de cookies
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# Descargar video MP4 con barra de progreso
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

        progreso = st.progress(0, text="🔄 Iniciando descarga...")

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
            
            # Actualizamos la barra de progreso durante la descarga
            for i in range(100):
                progreso.progress(i + 1)

        # Convertir video con ffmpeg
        subprocess.run([
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-preset", "ultrafast", "-crf", "24",
            nombre_salida
        ])

        os.remove(nombre_original)
        st.success("✅ Video descargado y convertido con éxito")

        with open(nombre_salida, "rb") as f:
            st.download_button(
                label="⬇️ Descargar MP4",
                data=f,
                file_name=nombre_salida,
                mime="video/mp4"
            )
        os.remove(nombre_salida)

    except Exception as e:
        st.error(f"Error al descargar MP4: {e}")

# Descargar MP3 con barra de progreso en paralelo
def descargar_mp3(links, cookies_path=None):
    def descargar_individual(link):
        try:
            opciones = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'retries': 3,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
            }
            if cookies_path:
                opciones['cookiefile'] = cookies_path

            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(link, download=True)
                nombre = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
                return nombre
        except Exception as e:
            return f"error::{link}::{e}"

    resultados = []
    progreso = st.progress(0, text="🔄 Iniciando descarga de MP3...")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(descargar_individual, link) for link in links]
        completados = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            resultados.append(future.result())
            completados += 1
            progreso.progress(completados / total)
    
    for resultado in resultados:
        if resultado.startswith("error::"):
            _, link_fallido, mensaje = resultado.split("::", 2)
            st.error(f"❌ Error al descargar {link_fallido}: {mensaje}")
        else:
            with open(resultado, "rb") as f:
                st.download_button(
                    label=f"⬇️ Descargar MP3: {os.path.basename(resultado)}",
                    data=f,
                    file_name=os.path.basename(resultado),
                    mime="audio/mpeg"
                )
            os.remove(resultado)

    st.success("✅ Descargas completadas")

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
