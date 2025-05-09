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

# Obtener formatos disponibles
def obtener_calidades(url, cookies_path=None):
    try:
        opciones = {'quiet': True, 'skip_download': True}
        if cookies_path:
            opciones['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)
            formatos = info.get("formats", [])
            calidades = {}
            for f in formatos:
                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    height = f.get("height")
                    fps = f.get("fps", 30)
                    label = f"{height}p ({fps}fps)"
                    if label not in calidades:
                        calidades[label] = f["format_id"]
            return calidades
    except Exception as e:
        st.error(f"Error al obtener calidades: {e}")
        return {}

# Descargar video MP4
def descargar_mp4(url, format_id, cookies_path=None):
    try:
        archivo_temporal = "temp_video"
        nombre_salida = "video_convertido.mp4"

        opciones = {
            'format': format_id,
            'outtmpl': f'{archivo_temporal}.%(ext)s',
            'socket_timeout': 30
        }
        if cookies_path:
            opciones['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)

        subprocess.run([
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
            "-c:a", "aac", "-strict", "experimental",
            nombre_salida
        ], check=True)

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

    except subprocess.CalledProcessError:
        st.error("❌ Error al convertir el video con ffmpeg.")
    except yt_dlp.utils.DownloadError as e:
        st.error(f"❌ Error al descargar el video: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

# Descargar MP3 en paralelo
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
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(descargar_individual, link) for link in links]
        for future in concurrent.futures.as_completed(futures):
            resultados.append(future.result())

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
        if url and st.button("Ver calidades disponibles"):
            calidades = obtener_calidades(url, cookies_path)
            if calidades:
                calidad_seleccionada = st.selectbox("Selecciona una calidad", list(calidades.keys()))
                if st.button("Descargar MP4"):
                    descargar_mp4(url, calidades[calidad_seleccionada], cookies_path)

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
