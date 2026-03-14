"""
______________________________________________________________________________________________

  LGA_NKS_Clip_DisableEXR v1.21 | Lega

  Habilita o deshabilita el clip en el track especificado (por defecto usa TRACK_comp_EXR del módulo LGA_NKS_GetClip).

  Funcionamiento:
  1. Obtiene el clip del track especificado en la posición del playhead usando el módulo centralizado
  2. Si no encuentra clip en playhead, usa el clip seleccionado como fallback
  3. Invierte el estado de habilitación del clip (enabled/disabled)

  v1.21 - Usa TRACK_comp_EXR del módulo en lugar de hardcodear "EXR", permitiendo cambiar el track por defecto
  v1.10 - Usa el módulo utilitario LGA_NKS_GetClip para obtener el clip (no permite selecciones múltiples)
______________________________________________________________________________________________
"""

import hiero.core
import hiero.ui
from pathlib import Path
import sys

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

# Importar utilidades para obtener clips
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_Shared.LGA_NKS_GetClip import get_clip_to_process
    # Sincronizar el debug con el módulo utilitario
    from LGA_NKS_Shared import LGA_NKS_GetClip as clip_utils
    clip_utils.DEBUG = DEBUG
else:
    debug_print("ERROR: No se encontró el módulo LGA_NKS_GetClip")

def toggle_clip_enabled(clip):
    """
    Invierte el estado de habilitación del clip.
    """
    if not clip:
        return False

    try:
        # Obtener el estado actual y cambiarlo
        nuevo_estado = not clip.isEnabled()
        clip.setEnabled(nuevo_estado)
        
        estado_texto = "habilitado" if nuevo_estado else "deshabilitado"
        debug_print(f"Clip {clip.name()} {estado_texto}")
        return True
    except Exception as e:
        debug_print(f"Error al cambiar el estado del clip: {e}")
        return False

def main():
    """
    Función principal que ejecuta la secuencia de operaciones.
    """
    # 1. Obtener clip usando el módulo centralizado (NO permite selecciones múltiples)
    # Usa TRACK_comp_EXR del módulo LGA_NKS_GetClip (None = usa el valor por defecto)
    clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)
    if not clip:
        debug_print("No se encontró un clip en el track especificado en la posición actual o seleccionado.")
        return

    # 2. Cambiar el estado del clip
    if toggle_clip_enabled(clip):
        debug_print("Operación completada con éxito.")
    else:
        debug_print("No se pudo cambiar el estado del clip.")

if __name__ == "__main__":
    main() 
