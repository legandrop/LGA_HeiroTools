"""
____________________________________________________________________________________

  LGA_NKS_FileManager_Download v1.0 | Lega
  Descarga el shot seleccionado desde Wasabi S3 usando FileManager CLI
  Extrae la ruta del shot tomando las primeras 4 partes: unidad/proyecto/grupo/shot
  Soporta modo desarrollo con variable Desarrollo = True y verificación automática
____________________________________________________________________________________
"""

from pathlib import Path
import sys
import os
import subprocess

# Agregar ruta del módulo utilitario
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clip_to_process
    import LGA_NKS_GetClip as clip_utils

# Variable global para activar o desactivar los prints
DEBUG = False

# Variable de desarrollo para cambiar la ruta del ejecutable
Desarrollo = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def main():
    """Función principal que descarga el shot seleccionado desde Wasabi S3"""
    debug_print("=== FILEMANAGER DOWNLOAD SHOT ===")

    try:
        # Obtener el clip usando el método híbrido inteligente (playhead primero, selección como fallback)
        clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

        if not clip:
            debug_print("No se encontró clip para procesar")
            return

        # Obtener la ruta del archivo del clip
        file_path = clip.source().mediaSource().fileinfos()[0].filename() if clip.source().mediaSource().fileinfos() else None

        if file_path:
            # La estructura es: unidad:/proyecto/grupo/shot/_input/version/archivo
            # Necesitamos llegar a: unidad:/proyecto/grupo/shot
            # Partimos desde el archivo y subimos hasta encontrar la carpeta del shot

            # Normalizar la ruta y dividir por ambos separadores (/ y \)
            normalized_path = os.path.normpath(file_path)
            path_parts = normalized_path.replace('\\', '/').split('/')
            debug_print(f"Partes de la ruta: {path_parts}")

            # La estructura siempre es: unidad/proyecto/grupo/shot/...
            # Tomar las primeras 4 partes para la carpeta del shot
            if len(path_parts) >= 4:
                shot_path = '/'.join(path_parts[:4])
            else:
                # Fallback si no hay suficientes partes
                debug_print("Ruta no tiene suficientes partes, usando fallback")
                clip_folder = os.path.dirname(file_path)
                input_folder = os.path.dirname(clip_folder)
                shot_path = os.path.dirname(input_folder)

            debug_print(f"Ruta del archivo: {file_path}")
            debug_print(f"Ruta del shot: {shot_path}")

            # Ejecutar FileManager con --download
            if Desarrollo:
                dev_exe = r"C:\Portable\LGA_FileManager\build\FileManager.exe"
                if os.path.exists(dev_exe):
                    filemanager_exe = dev_exe
                    debug_print("Usando versión de desarrollo")
                else:
                    filemanager_exe = r"C:\Portable\LGA\FileManager\FileManager.exe"
                    debug_print("Versión de desarrollo no encontrada, usando producción")
            else:
                filemanager_exe = r"C:\Portable\LGA\FileManager\FileManager.exe"
            cmd = [filemanager_exe, "--download", shot_path]

            debug_print(f"Ejecutando: {' '.join(cmd)}")

            try:
                # Ejecutar el comando (no esperamos que termine, FileManager abre la GUI)
                subprocess.Popen(cmd, shell=False)
                debug_print("FileManager iniciado para descarga")
            except Exception as cmd_error:
                debug_print(f"Error al ejecutar FileManager: {cmd_error}")
        else:
            debug_print("No se pudo obtener la ruta del archivo del clip")

    except Exception as e:
        debug_print(f"Error al procesar el clip: {e}")

if __name__ == "__main__":
    main()