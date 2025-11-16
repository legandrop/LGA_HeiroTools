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

def remove_compare_track(seq):
    # Verificar si existe un track llamado "COMPARE" y eliminarlo
    for track in seq.videoTracks():
        if track.name() == "COMPARE":
            seq.removeTrack(track)
            print("Track 'COMPARE' removed.")
            return True
    print("Track 'COMPARE' not found.")
    return False

def disable_difference_mode_for_exr(seq):
    # Iterar sobre los tracks de video para encontrar el track TRACK_comp_EXR
    for track in seq.videoTracks():
        if track.name() == TRACK_comp_EXR:
            # Verificar si el blend mode esta activado
            if track.isBlendEnabled() and track.blendMode() == "difference":
                track.setBlendEnabled(False)
                print(f"Blend mode 'Difference' disabled for track '{TRACK_comp_EXR}'.")
            else:
                print(f"Blend mode 'Difference' is not enabled for track '{TRACK_comp_EXR}'.")
            return True
    print(f"Track '{TRACK_comp_EXR}' not found.")
    return False

def main():
    # Obtener la secuencia activa en el timeline
    seq = hiero.ui.activeSequence()
    if not seq:
        print("No active sequence found.")
        return

    # Iniciar una accion de undo para las operaciones
    project = seq.project()
    project.beginUndo(f"Remove COMPARE Track and Disable {TRACK_comp_EXR} Difference Mode")

    try:
        # Remover el track "COMPARE"
        remove_compare_track(seq)

        # Desactivar el modo "Difference" para el track TRACK_comp_EXR
        disable_difference_mode_for_exr(seq)
    except Exception as e:
        print(f"Error during operation: {e}")
    finally:
        # Finalizar la accion de undo
        project.endUndo()

# Llamar a la funcion principal
if __name__ == "__main__":
    main()
