"""
____________________________________________________________________________________

  LGA_NKS_Playlist_Debug_Context v0.01 | Lega
  Script temporal de exploracion para imprimir:
  - clip detectado por playhead
  - timeline activo
  - proyecto al que pertenece el timeline

  v0.01: Primera version para validar contexto base del Playlist Panel.
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui

from LGA_NKS_Shared.LGA_NKS_GetClip import get_clip_to_process


def find_project_for_sequence(target_sequence):
    """Busca el proyecto que contiene la secuencia activa."""
    if not target_sequence:
        return None

    for project in hiero.core.projects():
        try:
            for sequence in project.sequences():
                if sequence == target_sequence:
                    return project
        except Exception:
            continue
    return None


def main():
    sequence = hiero.ui.activeSequence()

    if not sequence:
        print("No hay secuencia activa.")
        return

    project = find_project_for_sequence(sequence)
    clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

    clip_name = None
    if clip and not isinstance(clip, list):
        try:
            clip_name = clip.name()
        except Exception:
            clip_name = str(clip)

    print("=== Playlist Context Debug ===")
    print("Timeline activo:", sequence.name())
    print("Proyecto del timeline:", project.name() if project else "No encontrado")
    print("Clip detectado por playhead:", clip_name if clip_name else "No encontrado")


main()
