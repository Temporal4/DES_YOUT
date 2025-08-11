import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import concurrent.futures
import re


# 🔹 Limpiar nombres de archivo
def limpiar_nombre(nombre):
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre)


# 🔹 Guardar cookies temporalmente
def guardar_cookies_archivo(cookies_file):
    if cookies_file:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None


# 🔹 Detectar causa del error
def detectar_causa_error(mensaje):
    mensaje = str(mensaje).lower()
    if "sign in" in mensaje or "confirm your age" in mensaje:
        return "edad"
    elif "private video" in mensaje:
        return "privado"
    elif "not available in your country" in mensaje:
        return "geobloqueo"
    elif "403" in mensaje:
        return "403"
    elif "unavailable" in mensaje:
        return "no_disponible"
    return None


# 🔹 Descargar MP4 (con opción cookies)
def descargar_mp4(url, calidad, cookies_path=None):
    archivo_temporal = "temp_video"

    # Calidad
    formatos = {
        "alta": 'bestvideo+bestaudio/best',
        "normal": 'bv[height<=480]+ba/b[height<=480]',
        "baja": 'worstvideo+worstaudio/worst'
    }
    formato = formatos.get(calidad, 'bestvideo+bestaudio/best')

    opciones = {
        'format': formato,
        'outtmpl': f'{archivo_temporal}.%(ext)s',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'retries': 10,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    }
    if cookies_path:
        opciones['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
            titulo = limpiar_nombre(info.get('title', 'video'))
            nombre_salida = f"{titulo}.mp4"

        subprocess.run([
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast", "-crf", "23",
            nombre_salida
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        os.remove(nombre_original)
        with open(nombre_salida, "rb") as f:
            st.download_button(
                "⬇️ Descargar MP4",
                f,
                file_name=nombre_salida,
                mime="video/mp4"
            )
        os.remove(nombre_salida)
        return True

    except Exception as e:
        return detectar_causa_error(e)


# 🔹 Descargar MP3 (hasta 10 enlaces, con opción cookies)
def descargar_mp3(urls, cookies_path=None):
    def descargar(link):
        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'retries': 10,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0'
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        }
        if cookies_path:
            opciones['cookiefile'] = cookies_path
        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(link, download=True)
                nombre = limpiar_nombre(info.get('title', 'audio')) + ".mp3"
                return nombre
        except Exception as e:
            return "error", link, detectar_causa_error(e)

    resultados = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for r in executor.map(descargar, urls):
            resultados.append(r)

    for r in resultados:
        if isinstance(r, tuple) and r[0] == "error":
            st.error(f"❌ Error en {r[1]}: {r[2]}")
        else:
            with open(r, "rb") as f:
                st.download_button(
                    f"⬇️ Descargar MP3: {os.path.basename(r)}",
                    f,
                    file_name=os.path.basename(r),
                    mime="audio/mpeg"
                )
            os.remove(r)


# 🔹 App principal
def main():
    st.title("🎬 Descargador Inteligente YouTube MP4 / MP3")
    tipo = st.selectbox("Tipo de descarga", ["MP4", "MP3"])

    if tipo == "MP4":
        url = st.text_input("🔗 Ingresa el enlace")
        calidad = st.selectbox("Calidad", ["alta", "normal", "baja"])
        if st.button("⬇️ Descargar"):
            if url:
                st.info("Intentando descarga sin cookies...")
                resultado = descargar_mp4(url, calidad)

                if resultado in ["edad", "privado", "geobloqueo", "403"]:
                    st.warning("⚠️ Se requiere cookies.txt para este video. Súbelas y reintenta.")
                    cookies_file = st.file_uploader("Sube tu cookies.txt", type=["txt"])
                    if cookies_file:
                        cookies_path = guardar_cookies_archivo(cookies_file)
                        descargar_mp4(url, calidad, cookies_path)
            else:
                st.warning("Ingresa un enlace válido.")

    else:
        enlaces = st.text_area("🔗 Ingresa hasta 10 enlaces (uno por línea)")
        if st.button("⬇️ Descargar MP3"):
            links = [l.strip() for l in enlaces.splitlines() if l.strip()]
            if links:
                st.info("Intentando descarga sin cookies...")
                descargar_mp3(links)
            else:
                st.warning("Ingresa al menos un enlace válido.")


if __name__ == "__main__":
    main()
