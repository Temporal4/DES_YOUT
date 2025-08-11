import streamlit as st
import yt_dlp
import os
import tempfile
import concurrent.futures
import re
import signal

# ===== Función para limpiar nombres =====
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)

# ===== Timeout seguro =====
class TimeoutException(Exception): pass
def timeout_handler(signum, frame):
    raise TimeoutException()

signal.signal(signal.SIGALRM, timeout_handler)

# ===== Guardar cookies =====
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# ===== Descargar MP4 =====
def descargar_mp4(url, calidad, cookies_path=None):
    try:
        archivo_temporal = "temp_video"

        # Formatos optimizados para evitar errores y bloqueos
        if calidad == "alta":
            formato = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif calidad == "normal":
            formato = 'bv[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480][ext=mp4]/best'
        elif calidad == "baja":
            formato = 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst'
        else:
            st.error("❌ Calidad no válida.")
            return

        opciones = {
            'format': formato,
            'outtmpl': f'{archivo_temporal}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'geo_bypass': True,
            'http_headers': {'User-Agent': 'Mozilla/5.0'}
        }

        if cookies_path:
            opciones['cookiefile'] = cookies_path

        progreso = st.progress(0, text="⏳ Descargando video...")

        signal.alarm(120)  # Máximo 2 minutos
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_archivo = ydl.prepare_filename(info)
            titulo_video = limpiar_nombre(info.get('title', 'video'))
            nombre_salida = f"{titulo_video}.mp4"
        signal.alarm(0)

        # Si no es MP4, convertir
        if not nombre_archivo.endswith(".mp4"):
            os.system(f'ffmpeg -i "{nombre_archivo}" -c:v libx264 -c:a aac "{nombre_salida}"')
            os.remove(nombre_archivo)
        else:
            os.rename(nombre_archivo, nombre_salida)

        progreso.progress(100, text="✅ Video listo")
        with open(nombre_salida, "rb") as f:
            st.download_button("⬇️ Descargar MP4", f, file_name=nombre_salida, mime="video/mp4")
        os.remove(nombre_salida)

    except TimeoutException:
        st.error("⏳ Tiempo de descarga agotado (puede requerir cookies o estar bloqueado por región).")
    except yt_dlp.utils.DownloadError as e:
        if "403" in str(e):
            st.error("❌ Acceso prohibido (puede ser restricción de sesión o cookies).")
        elif "Requested format is not available" in str(e):
            st.error("⚠️ El formato solicitado no está disponible. Prueba con otra calidad.")
        else:
            st.error(f"❌ Error de descarga: {e}")
    except Exception as e:
        st.error(f"⚠️ Error inesperado: {e}")

# ===== Descargar MP3 =====
def descargar_mp3(links, cookies_path=None):
    def descargar_individual(link):
        try:
            opciones = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'retries': 3,
                'geo_bypass': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
            }
            if cookies_path:
                opciones['cookiefile'] = cookies_path

            signal.alarm(120)  # Máximo 2 minutos por canción
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(link, download=True)
                nombre = limpiar_nombre(info.get('title', 'audio')) + ".mp3"
            signal.alarm(0)
            return nombre
        except TimeoutException:
            return f"error::{link}::Tiempo agotado"
        except Exception as e:
            return f"error::{link}::{e}"

    resultados = []
    progreso = st.progress(0, text="⏳ Descargando MP3...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(descargar_individual, link) for link in links]
        total = len(futures)
        completados = 0
        for future in concurrent.futures.as_completed(futures):
            resultados.append(future.result())
            completados += 1
            progreso.progress(completados / total)

    for r in resultados:
        if r.startswith("error::"):
            _, link_fallido, mensaje = r.split("::", 2)
            st.error(f"❌ Error en {link_fallido}: {mensaje}")
        else:
            with open(r, "rb") as f:
                st.download_button(f"⬇️ Descargar {os.path.basename(r)}", f, file_name=os.path.basename(r), mime="audio/mpeg")
            os.remove(r)

# ===== Interfaz principal =====
def main():
    st.title("🎬 Descargador YouTube MP4 / MP3 (Optimizado)")

    tipo_archivo = st.selectbox("Selecciona el tipo de archivo", ["MP4", "MP3"])
    cookies_file = st.file_uploader("Sube tu archivo de cookies (opcional)", type=["txt"])
    cookies_path = guardar_cookies_archivo(cookies_file)

    if tipo_archivo == "MP4":
        url = st.text_input("Enlace del video (MP4)")
        calidad = st.selectbox("Calidad", ["alta", "normal", "baja"])
        if st.button("Descargar MP4"):
            if url:
                descargar_mp4(url, calidad, cookies_path)
            else:
                st.warning("Por favor ingresa un enlace válido.")

    elif tipo_archivo == "MP3":
        enlaces = st.text_area("Ingresa hasta 10 enlaces (uno por línea)")
        if st.button("Descargar MP3"):
            links = [l.strip() for l in enlaces.splitlines() if l.strip()]
            if 1 <= len(links) <= 10:
                descargar_mp3(links, cookies_path)
            else:
                st.warning("Debes ingresar entre 1 y 10 enlaces.")

if __name__ == "__main__":
    main()
