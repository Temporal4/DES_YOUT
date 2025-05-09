import streamlit as st
import yt_dlp
import os
import shutil
from pathlib import Path
import re  # Para eliminar caracteres especiales

# Función para limpiar el nombre del archivo (eliminar caracteres no deseados)
def limpiar_titulo(titulo):
    # Eliminar caracteres no válidos en los títulos (como : " * ? / \ |)
    return re.sub(r'[<>:"/\\|?*]', '', titulo)

def descargar_videos(links, tipo, calidad, cookies=None):
    resultados = []
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    # Opciones comunes
    options = {
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'noplaylist': True
    }

    if cookies:
        options['cookiefile'] = cookies

    if tipo == 'MP3':
        options.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0'
            }]
        })
    else:  # MP4
        if calidad == 'Alta':
            fmt = 'bestvideo+bestaudio/best'
        elif calidad == 'Normal':
            fmt = 'bv[height<=480]+ba/b[height<=480]'
        else:  # Baja
            fmt = 'worstvideo+worstaudio/worst'

        options.update({
            'format': fmt,
            'merge_output_format': 'mp4'
        })

    with yt_dlp.YoutubeDL(options) as ydl:
        for link in links:
            try:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)
                ext = '.mp3' if tipo == 'MP3' else '.mp4'
                final_name = limpiar_titulo(info['title']) + ext
                final_path = temp_dir / final_name

                # Convertir a H.264 (si es MP4) para que se pueda escuchar correctamente
                if tipo == 'MP4' and final_path.exists():
                    # Usar ffmpeg para convertir el video a H.264
                    output_path = final_path.with_suffix('.h264.mp4')
                    os.system(f"ffmpeg -i {final_path} -vcodec libx264 -acodec aac {output_path}")

                    # Eliminar el archivo original (si la conversión fue exitosa)
                    if output_path.exists():
                        os.remove(final_path)
                        final_path = output_path
                    else:
                        resultados.append((f"Error al procesar el archivo: {link}", None))
                
