import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import re
import concurrent.futures

# Limpiar nombre de archivo
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)

# Guardar cookies
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# Detectar y manejar errores
def manejar_error(e):
    err_str = str(e).lower()
    if "403" in err_str:
        return "🚫 Bloqueo por IP o restricción geográfica (HTTP 403). Prueba con cookies o desde otra red."
    elif "requested format is not available" in err_str:
        return "⚠️ Formato de video no disponible. Intentando con formato alternativo..."
    elif "cookies" in err_str:
        return "🔑 El video requiere que inicies sesión (cookies)."
    else:
        return f"❌ Error inesperado: {e}"

# Descargar MP4
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        archivo_temporal = "temp_video"

        # Mapear calidad
        if calidad == "alta":
            formato = 'bestvideo+bestaudio/best'
        elif calidad == "normal":
            formato = 'bv[height<=480]+ba/b[height<=480]'
        elif calidad == "baja":
            formato = 'worstvideo+worstaudio/worst'
        else:
            st.error("Calidad no válida.")
            return

        opciones = {
            'format': formato,
            'outtmpl': f'{archivo_temporal}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'merge_output_format': 'mp4'
        }
        if cookies_path:
            opciones['cookiefile'] = cookies_path

        progreso = st.progress(0, text="🔄 Iniciando descarga...")

        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=True)
                nombre_original = ydl.prepare_filename(info)
        except Exception as e:
            st.warning(manejar_error(e))
            # Intentar con formato alternativo
            opciones['format'] = 'best'
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=True)
                nombre_original = ydl.prepare_filename(info)

        titulo_video = limpiar_nombre(info.get('title', 'video'))
        nombre_salida = f"{titulo_video}.mp4"

        # Simular barra de progreso
        for i in range(100):
            progreso.progress((i+1)/100)

        # Convertir con ffmpeg
        subprocess.run([
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-preset", "ultrafast", "-crf", "26",
            nombre_salida
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
        st.error(manejar_error(e))

# Descargar MP3
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
                titulo = limpiar_nombre(info.get('title', 'audio'))
                return f"{titulo}.mp3"
        except Exception as e:
            return f"error::{link}::{manejar_error(e)}"

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
            st.error(f"❌ {link_fallido}: {mensaje}")
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

# Interfaz
def main():
    st.title("🎥 Descargador de YouTube: MP4 y MP3 con detección de errores")

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
