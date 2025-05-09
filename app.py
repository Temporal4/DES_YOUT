import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import re

# Guardar archivo de cookies
def guardar_cookies_archivo(cookies_file):
    if cookies_file is not None:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

# Obtener calidades disponibles del video
def obtener_calidades_disponibles(url, cookies_path=None):
    opciones = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
    }
    if cookies_path:
        opciones['cookiefile'] = cookies_path

    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(url, download=False)
        formatos = info.get("formats", [])

    calidades = []
    for f in formatos:
        if f.get("vcodec") != "none" and f.get("acodec") == "none":
            height = f.get("height")
            fps = f.get("fps", 0)
            format_id = f.get("format_id")
            if height and height >= 480:
                etiqueta = f"{height}p{fps if fps else ''}"
                calidades.append((etiqueta, format_id))

    # Eliminar duplicados y filtrar solo la mejor calidad de 720p
    calidades = sorted(list(set(calidades)), key=lambda x: int(re.match(r"(\d+)p", x[0]).group(1)))
    mejor_720p = None
    calidades_filtradas = []
    
    for calidad in calidades:
        if "720p" in calidad[0]:
            if mejor_720p is None:
                mejor_720p = calidad
        else:
            calidades_filtradas.append(calidad)
    
    if mejor_720p:
        calidades_filtradas.append(mejor_720p)
    
    return calidades_filtradas

# Descargar MP4 con calidad específica con barra de progreso
def descargar_mp4_especifico(url, format_id, cookies_path=None):
    try:
        archivo_temporal = "temp_video"
        nombre_salida = "video_convertido.mp4"
        opciones = {
            'format': f"{format_id}+bestaudio/best",
            'outtmpl': f'{archivo_temporal}.%(ext)s'
        }
        if cookies_path:
            opciones['cookiefile'] = cookies_path

        progreso = st.progress(0, text="🔄 Iniciando descarga...")

        progreso.progress(10, text="🔽 Descargando video...")
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            nombre_original = ydl.prepare_filename(info)
        progreso.progress(70, text="⚙️ Convirtiendo video...")

        subprocess.run([  # Usamos ffmpeg para convertir
            "ffmpeg", "-i", nombre_original,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-preset", "ultrafast", "-crf", "24",
            nombre_salida
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        os.remove(nombre_original)
        progreso.progress(100, text="✅ Conversión finalizada")

        st.success("🎉 Video descargado y convertido con éxito")
        with open(nombre_salida, "rb") as f:
            st.download_button(
                label="⬇️ Descargar MP4",
                data=f,
                file_name=nombre_salida,
                mime="video/mp4"
            )
        os.remove(nombre_salida)

    except Exception as e:
        st.error(f"❌ Error al descargar MP4: {e}")

# Interfaz principal
def main():
    st.title("Descargador de YouTube: MP4 y MP3")
    tipo_archivo = st.selectbox("Selecciona el tipo de archivo", ["MP4", "MP3"])
    cookies_file = st.file_uploader("Sube tu archivo de cookies (cookies.txt)", type=["txt"])
    cookies_path = guardar_cookies_archivo(cookies_file)

    if tipo_archivo == "MP4":
        url = st.text_input("Ingresa el enlace del video (MP4)")
        if st.button("Siguiente") and url:
            calidades_disponibles = obtener_calidades_disponibles(url, cookies_path)
            if not calidades_disponibles:
                st.warning("No se encontraron calidades adecuadas (mínimo 480p).")
                return
            calidad_seleccionada = st.selectbox("Selecciona la calidad disponible", [f"{c[0]}" for c in calidades_disponibles])
            format_id_map = {c[0]: c[1] for c in calidades_disponibles}
            if calidad_seleccionada:
                st.session_state.calidad_seleccionada = calidad_seleccionada
            if 'calidad_seleccionada' in st.session_state and st.session_state.calidad_seleccionada:
                format_id = format_id_map.get(st.session_state.calidad_seleccionada)
                if st.button("Descargar MP4"):
                    descargar_mp4_especifico(url, format_id, cookies_path)
        elif not url:
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
