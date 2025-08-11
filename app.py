import yt_dlp

def descargar_video(url, cookies_path=None):
    opciones = {
        'outtmpl': '%(title)s.%(ext)s',
        'merge_output_format': 'mp4',  # Fuerza a guardar en MP4
    }

    if cookies_path:
        opciones['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"✅ Video descargado: {info['title']}.mp4")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    url = input("Pega el enlace de YouTube: ").strip()
    usar_cookies = input("¿Tienes cookies.txt? (s/n): ").strip().lower()

    cookies = None
    if usar_cookies == 's':
        cookies = input("Ruta del archivo cookies.txt: ").strip()

    descargar_video(url, cookies)
