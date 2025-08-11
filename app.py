# app_streamlit_ytdlp.py
import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import concurrent.futures
import re
from typing import Optional, Dict, Any, List

# ------------------------------
# Helpers
# ------------------------------
def limpiar_nombre(nombre: str) -> str:
    return re.sub(r'[\\/:"*?<>|]+', '_', nombre).strip()

def guardar_cookies_archivo(cookies_file) -> Optional[str]:
    if cookies_file:
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        return cookies_path
    return None

def detectar_causa_error(msg: str) -> str:
    m = str(msg).lower()
    if "sign in" in m or "confirm your age" in m or "age" in m:
        return "edad"
    if "private" in m or "members-only" in m:
        return "privado"
    if "not available in your country" in m or "region" in m:
        return "geobloqueo"
    if "403" in m or "forbidden" in m:
        return "403"
    if "requested format is not available" in m or "format not available" in m:
        return "format"
    return "otro"

# ------------------------------
# Format selector - inspecciona formatos disponibles
# ------------------------------
def elegir_formato(info: Dict[str, Any], calidad: str) -> str:
    # Recolectar resoluciones de formatos de video (vcodec != 'none')
    heights = []
    for f in info.get('formats', []):
        h = f.get('height')
        if h is not None:
            heights.append(h)
    heights = sorted(set([h for h in heights if isinstance(h, int)]))
    # if no heights (solo audio o formatos sin height), fallback to best
    if not heights:
        if calidad == 'alta':
            return 'bestaudio/best'  # video puede no existir -> mayor fallback
        return 'best'

    # Alta: intenta bestvideo+bestaudio/best (fallback best)
    if calidad == 'alta':
        return 'bestvideo+bestaudio/best'
    # Normal: preferir <=480, si no hay usar best[height<=720] o best
    if calidad == 'normal':
        # si existe alguna ≤480
        posibles = [h for h in heights if h <= 480]
        if posibles:
            return 'bv[height<=480]+ba/best[height<=480]'
        # si no, elegir mejor <=720
        posibles = [h for h in heights if h <= 720]
        if posibles:
            return 'bv[height<=720]+ba/best[height<=720]/best'
        return 'best'
    # Baja: intentar worstvideo+worstaudio/worst o best[height<=360]/worst
    if calidad == 'baja':
        # existe <=240 o <=360?
        posibles = [h for h in heights if h <= 360]
        if posibles:
            return 'bv[height<=360]+ba/best[height<=360]/worst'
        return 'worstvideo+worstaudio/worst'

    return 'best'

# ------------------------------
# Función principal para descargar MP4
# ------------------------------
def descargar_mp4_proceso(url: str, calidad: str, cookies_path: Optional[str]=None) -> Dict[str, str]:
    """
    Intenta descargar y convertir a mp4. Devuelve dict con 'status' y 'message' o 'file'.
    status: 'ok', 'need_cookies', 'error', 'no_format'
    """
    archivo_temporal = "temp_video"
    opciones_base = {
        'quiet': True,
        'no_warnings': True,
        'retries': 3,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        },
    }
    if cookies_path:
        opciones_base['cookiefile'] = cookies_path

    try:
        # 1) primero extraer info (sin descargar) para conocer formatos y detectar errores tempranos
        with yt_dlp.YoutubeDL(opciones_base) as ydl_probe:
            try:
                info = ydl_probe.extract_info(url, download=False)
            except Exception as e:
                causa = detectar_causa_error(str(e))
                if causa in ('edad', 'privado', 'geobloqueo', '403'):
                    return {'status': 'need_cookies', 'message': causa}
                # si la extracción falló por otro motivo devolvemos error
                return {'status': 'error', 'message': str(e)}

        # 2) elegir formato apropiado según lo que devolvió info
        formato = elegir_formato(info, calidad)

        # 3) preparar opciones finales de descarga
        opciones = opciones_base.copy()
        opciones.update({
            'format': formato,
            'outtmpl': f'{archivo_temporal}.%(ext)s'
        })

        with yt_dlp.YoutubeDL(opciones) as ydl:
            try:
                info2 = ydl.extract_info(url, download=True)  # descarga
            except Exception as e:
                # si el error es "Requested format is not available", reintentar con 'best'
                msg = str(e).lower()
                if 'requested format is not available' in msg or 'format not available' in msg:
                    # reintento con best
                    opciones['format'] = 'best'
                    with yt_dlp.YoutubeDL(opciones) as ydl2:
                        info2 = ydl2.extract_info(url, download=True)
                else:
                    causa = detectar_causa_error(str(e))
                    if causa == 'need_cookies' or causa in ('edad','privado','geobloqueo','403'):
                        return {'status': 'need_cookies', 'message': causa}
                    return {'status': 'error', 'message': str(e)}

            nombre_original = ydl.prepare_filename(info2)
            titulo = limpiar_nombre(info2.get('title', 'video'))
            nombre_salida = f"{titulo}.mp4"

        # 4) convertir a H.264 con ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", nombre_original,
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "fast", "-crf", "23",
                nombre_salida
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            # conversión falló
            if os.path.exists(nombre_original):
                os.remove(nombre_original)
            return {'status': 'error', 'message': f'ffmpeg error: {e}'}

        # eliminar original temporal si existe
        if os.path.exists(nombre_original):
            os.remove(nombre_original)

        return {'status': 'ok', 'file': nombre_salida}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# ------------------------------
# Descargar MP3 (similar lógica, pero más simple)
# ------------------------------
def descargar_mp3_proceso(url: str, cookies_path: Optional[str]=None) -> Dict[str,str]:
    opciones = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'retries': 3,
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
            info = ydl.extract_info(url, download=True)
            titulo = limpiar_nombre(info.get('title','audio'))
            nombre = f"{titulo}.mp3"
            return {'status': 'ok', 'file': nombre}
    except Exception as e:
        causa = detectar_causa_error(str(e))
        if causa in ('edad','privado','geobloqueo','403'):
            return {'status': 'need_cookies', 'message': causa}
        return {'status': 'error', 'message': str(e)}

# ------------------------------
# Interfaz Streamlit (inteligente: prueba sin cookies, si falla pide cookies y reintenta)
# ------------------------------
def main():
    st.title("🎬 Descargador YouTube (MP4 / MP3) — Modo inteligente")
    st.write("Prueba sin cookies primero; si el video requiere login/region/edad te pediré cookies.txt y reintentaremos.")

    tipo = st.selectbox("Tipo", ["MP4", "MP3"])
    cookies_file = st.file_uploader("Sube cookies.txt (opcional)", type=["txt"])
    user_supplied_cookies = None
    if cookies_file:
        user_supplied_cookies = guardar_cookies_archivo(cookies_file)

    if tipo == "MP4":
        url = st.text_input("URL del video (MP4)")
        calidad = st.radio("Calidad", ["alta","normal","baja"], index=0)
        if st.button("Descargar MP4"):
            if not url:
                st.warning("Ingresa una URL válida.")
                return

            st.info("Intentando descarga SIN cookies...")
            res = descargar_mp4_proceso(url, calidad, cookies_path=None)
            if res['status'] == 'ok':
                # mostrar botón de descarga
                with open(res['file'], "rb") as f:
                    st.download_button("⬇️ Descargar MP4", f, file_name=res['file'], mime="video/mp4")
                os.remove(res['file'])
            elif res['status'] == 'need_cookies':
                st.warning("Parece que el video requiere inicio de sesión / cookies / está restringido por edad o región.")
                # si el usuario ya subió cookies, intentar reintentar
                if user_supplied_cookies:
                    st.info("Reintentando con las cookies que subiste...")
                    res2 = descargar_mp4_proceso(url, calidad, cookies_path=user_supplied_cookies)
                    if res2['status'] == 'ok':
                        with open(res2['file'], "rb") as f:
                            st.download_button("⬇️ Descargar MP4 (con cookies)", f, file_name=res2['file'], mime="video/mp4")
                        os.remove(res2['file'])
                    else:
                        st.error(f"No se pudo descargar incluso con cookies: {res2.get('message')}")
                else:
                    st.info("Por favor sube tu cookies.txt (desde el navegador donde estás logueado) y vuelve a intentar.")
            else:
                st.error(f"Error: {res.get('message')}")

    else:  # MP3
        st.write("Ingresa hasta 10 URLs (una por línea):")
        raw = st.text_area("", height=120)
        links = [l.strip() for l in raw.splitlines() if l.strip()]
        if st.button("Descargar MP3"):
            if not links:
                st.warning("Ingresa al menos una URL.")
                return
            if len(links) > 10:
                st.warning("Máximo 10 enlaces.")
                return

            st.info("Intentando descargas SIN cookies...")
            results = []
            for url in links:
                r = descargar_mp3_proceso(url, cookies_path=None)
                results.append((url, r))

            # ver si alguno necesita cookies
            need_cookies = [u for u,res in results if res['status']=='need_cookies']
            if need_cookies and not user_supplied_cookies:
                st.warning("Algunos videos requieren cookies (login/edad/region). Sube cookies.txt y reintenta para esos enlaces.")
                st.write("Videos que requieren cookies:")
                for u in need_cookies:
                    st.write("- " + u)
                return

            # si subió cookies, reintentar los que fallaron por necesidad de cookies
            final_files = []
            for url, r in results:
                if r['status'] == 'ok':
                    final_files.append(r['file'])
                elif r['status'] == 'need_cookies' and user_supplied_cookies:
                    st.info(f"Reintentando {url} con cookies...")
                    r2 = descargar_mp3_proceso(url, cookies_path=user_supplied_cookies)
                    if r2['status']=='ok':
                        final_files.append(r2['file'])
                    else:
                        st.error(f"Error con {url}: {r2.get('message')}")
                else:
                    st.error(f"Error con {url}: {r.get('message')}")

            # ofrecer botones de descarga para los archivos obtenidos
            for fpath in final_files:
                with open(fpath, "rb") as f:
                    st.download_button(f"⬇️ Descargar MP3: {os.path.basename(fpath)}", f, file_name=os.path.basename(fpath), mime="audio/mpeg")
                os.remove(fpath)

            if final_files:
                st.success("Descargas completadas.")

if __name__ == "__main__":
    main()
