"""
Elimina tracks vacios marcados con tag icon 'icons:NukeVFX.png'.

Basado en el mismo patron usado por Compare OFF:
- toma la secuencia activa
- abre bloque de undo en el proyecto
- recorre videoTracks()
- usa seq.removeTrack(track)

Este script SI modifica el timeline.
"""

import hiero.core
import hiero.ui


TARGET_ICON = "icons:NukeVFX.png"


def has_nukevfx_tag(track):
    """Devuelve True si el track tiene algun tag con icono NukeVFX."""
    if not hasattr(track, "tags"):
        return False

    try:
        tags = track.tags()
    except Exception:
        return False

    for tag in tags:
        try:
            if tag.icon() == TARGET_ICON:
                return True
        except Exception:
            continue

    return False


def remove_nukevfx_tracks(seq):
    """Remueve todos los tracks que tengan el icono NukeVFX en alguno de sus tags."""
    tracks_to_remove = []

    for track in seq.videoTracks():
        if has_nukevfx_tag(track):
            tracks_to_remove.append(track)

    if not tracks_to_remove:
        print(f"No se encontraron tracks con tag icon '{TARGET_ICON}'.")
        return 0

    removed_count = 0
    for track in tracks_to_remove:
        try:
            track_name = track.name()
        except Exception:
            track_name = "<sin nombre>"

        try:
            seq.removeTrack(track)
            print(f"Track eliminado: {track_name}")
            removed_count += 1
        except Exception as e:
            print(f"Error eliminando track '{track_name}': {e}")

    return removed_count


def main():
    seq = hiero.ui.activeSequence()
    if not seq:
        print("No active sequence found.")
        return

    project = seq.project()
    project.beginUndo("Delete NukeVFX Tracks")

    try:
        removed_count = remove_nukevfx_tracks(seq)
        print(f"Total de tracks eliminados: {removed_count}")
    except Exception as e:
        print(f"Error during operation: {e}")
    finally:
        project.endUndo()


if __name__ == "__main__":
    main()
