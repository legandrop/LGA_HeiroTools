"""
____________________________________________________________________________________

  LGA_NKS_FileManager_OpenPath v1.0 | Lega
  Abre la carpeta del shot seleccionado en FileManager usando CLI
____________________________________________________________________________________
"""

from pathlib import Path
import sys
import os

# Agregar ruta del módulo utilitario
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clip_to_process
    import LGA_NKS_GetClip as clip_utils

# Variable global para activar o desactivar los prints
DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def main():
    """Función principal que obtiene la ruta del clip seleccionado y la imprime para debug"""
    debug_print("=== FILEMANAGER OPEN PATH ===")

    try:
        # Obtener el clip usando el método híbrido inteligente (playhead primero, selección como fallback)
        clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

        if not clip:
            debug_print("No se encontró clip para procesar")
            return

        # Obtener la ruta del archivo del clip
        file_path = clip.source().mediaSource().fileinfos()[0].filename() if clip.source().mediaSource().fileinfos() else None

        if file_path:
            debug_print(f"Ruta del clip seleccionado: {file_path}")
            debug_print(f"Carpeta del clip: {os.path.dirname(file_path)}")
        else:
            debug_print("No se pudo obtener la ruta del archivo del clip")

    except Exception as e:
        debug_print(f"Error al obtener la ruta del clip: {e}")

if __name__ == "__main__":
    main()