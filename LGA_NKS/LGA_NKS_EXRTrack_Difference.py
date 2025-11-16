"""
____________________________________________________________

  LGA_NKS_EXRTrack_Difference v1.1 - 2024 - Lega
  Alterna el modo de mezcla del track TRACK_comp_EXR a "Difference"
  
  v1.1: Centralización del nombre del track usando TRACK_comp_EXR del módulo LGA_NKS_GetClip
____________________________________________________________

"""

import hiero.core
import hiero.ui
from pathlib import Path
import sys

# Importar utilidades para obtener clips
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import TRACK_comp_EXR
else:
    # Fallback si no se encuentra el módulo
    TRACK_comp_EXR = "_comp_"

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

def main():
    try:
        # Obtiene la secuencia activa
        seq = hiero.ui.activeSequence()

        if not seq:
            debug_print("No hay una secuencia activa.")
            return

        # Itera sobre los tracks de video para encontrar el track TRACK_comp_EXR
        for index, track in enumerate(seq.videoTracks()):
            if track.name() == TRACK_comp_EXR:
                # Verifica si el blend mode ya esta activado
                if track.isBlendEnabled():
                    # Si esta activado, lo desactiva
                    track.setBlendEnabled(False)
                    debug_print(f"Blend mode desactivado para el track '{TRACK_comp_EXR}' en el indice: {index}")
                else:
                    # Si no esta activado, lo activa y cambia el modo a "Difference"
                    track.setBlendEnabled(True)
                    track.setBlendMode("difference")
                    debug_print(f"Blend mode 'Difference' activado para el track '{TRACK_comp_EXR}' en el indice: {index}")
                break
        else:
            debug_print(f"No se encontro un track llamado '{TRACK_comp_EXR}'.")
    except Exception as e:
        debug_print(f"Error durante la operacion: {e}")
