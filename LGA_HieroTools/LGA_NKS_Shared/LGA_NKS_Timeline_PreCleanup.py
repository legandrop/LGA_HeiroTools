"""
____________________________________________________________________

  LGA_NKS_Timeline_PreCleanup v1.03 | Lega

  Limpieza previa del timeline para Refresh Timeline y Switch Sequence.
  Elimina tracks NukeVFX y extiende los efectos de BurnIn hasta el
  último clip real del timeline, incluso si esta offline.

  v1.03: Los tracks NukeVFX con contenido ya no se omiten: se les elimina
         el ícono NukeVFX.png para que dejen de identificarse como comp tracks.
  v1.02: Los tracks NukeVFX solo se eliminan si están vacíos (sin clips).
         Si tienen contenido se omiten y se loguea un aviso.
  v1.01: Agregado hook de debug handler para reutilizar el logger del panel que lo invoque
  v1.00: Version inicial. Elimina tracks con tag icon 'icons:NukeVFX.png'
         y extiende los efectos del track BurnIn hasta el timelineOut
         del ultimo clip real del timeline.
____________________________________________________________________
"""

import hiero.core
import hiero.ui


TARGET_BURNIN_TRACK = "BurnIn"
TARGET_NUKEVFX_ICON = "icons:NukeVFX.png"

_debug_handler = None


def debug_print(*message):
    if _debug_handler:
        _debug_handler(*message)
    else:
        print(*message)


def set_debug_handler(handler):
    global _debug_handler
    _debug_handler = handler


def safe_call(obj, attr_name, default=None):
    try:
        attr = getattr(obj, attr_name)
    except Exception:
        return default

    try:
        return attr() if callable(attr) else attr
    except Exception:
        return default


def has_nukevfx_tag(track):
    if not hasattr(track, "tags"):
        return False

    try:
        tags = track.tags()
    except Exception:
        return False

    for tag in tags:
        try:
            if tag.icon() == TARGET_NUKEVFX_ICON:
                return True
        except Exception:
            continue

    return False


def is_track_empty(track):
    try:
        return len(list(track.items())) == 0
    except Exception:
        return False


def remove_nukevfx_icon(track):
    try:
        tags = track.tags()
    except Exception:
        return False

    removed = False
    for tag in tags:
        try:
            if tag.icon() == TARGET_NUKEVFX_ICON:
                track.removeTag(tag)
                removed = True
        except Exception:
            continue

    return removed


def remove_nukevfx_tracks(seq):
    nukevfx_tracks = [track for track in seq.videoTracks() if has_nukevfx_tag(track)]

    removed = 0
    for track in nukevfx_tracks:
        track_name = safe_call(track, "name", "<sin nombre>")
        if is_track_empty(track):
            seq.removeTrack(track)
            debug_print(f"Track NukeVFX eliminado: {track_name}")
            removed += 1
        else:
            remove_nukevfx_icon(track)
            debug_print(f"Track NukeVFX con contenido, ícono eliminado: {track_name}")

    return removed


def clip_counts_for_timeline_extent(item):
    if isinstance(item, hiero.core.EffectTrackItem):
        return False

    timeline_in = safe_call(item, "timelineIn")
    timeline_out = safe_call(item, "timelineOut")
    if timeline_in is None or timeline_out is None:
        return False

    return True


def get_last_visible_timeline_out(seq):
    last_out = None

    for track in seq.videoTracks():
        try:
            items = list(track.items())
        except Exception:
            continue

        for item in items:
            if not clip_counts_for_timeline_extent(item):
                continue

            timeline_out = safe_call(item, "timelineOut")
            if timeline_out is None:
                continue

            timeline_out = int(timeline_out)
            if last_out is None or timeline_out > last_out:
                last_out = timeline_out

    return last_out


def get_burnin_track(seq):
    for track in seq.videoTracks():
        if safe_call(track, "name") == TARGET_BURNIN_TRACK:
            return track
    return None


def get_burnin_effects(track):
    effects = []
    items = safe_call(track, "subTrackItems", []) or []

    for group in items:
        if not group:
            continue
        for item in group:
            if isinstance(item, hiero.core.EffectTrackItem):
                effects.append(item)

    return effects


def extend_burnin_to_last_visible(seq):
    burnin_track = get_burnin_track(seq)
    if not burnin_track:
        debug_print("Track BurnIn no encontrado.")
        return 0

    effects = get_burnin_effects(burnin_track)
    if not effects:
        debug_print("No se encontraron efectos en BurnIn.")
        return 0

    target_timeline_out = get_last_visible_timeline_out(seq)
    if target_timeline_out is None:
        debug_print("No se pudo calcular el ultimo timelineOut del timeline.")
        return 0

    adjusted_count = 0
    for effect in effects:
        effect_name = safe_call(effect, "name", "<sin nombre>")
        current_out = safe_call(effect, "timelineOut")
        if current_out is None:
            continue

        current_out = int(current_out)
        if current_out == target_timeline_out:
            continue

        effect.setTimelineOut(target_timeline_out)
        debug_print(
            f"Effect BurnIn extendido: {effect_name} | {current_out} -> {target_timeline_out}"
        )
        adjusted_count += 1

    return adjusted_count


def main():
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No active sequence found.")
        return {"removed_tracks": 0, "adjusted_effects": 0}

    project = seq.project()
    if not project:
        debug_print("No active project found.")
        return {"removed_tracks": 0, "adjusted_effects": 0}

    removed_tracks = 0
    adjusted_effects = 0

    project.beginUndo("Timeline Pre-Cleanup")
    try:
        removed_tracks = remove_nukevfx_tracks(seq)
        adjusted_effects = extend_burnin_to_last_visible(seq)
    finally:
        project.endUndo()

    debug_print(
        f"Pre-cleanup finalizado | tracks eliminados: {removed_tracks} | "
        f"efectos BurnIn ajustados: {adjusted_effects}"
    )

    return {
        "removed_tracks": removed_tracks,
        "adjusted_effects": adjusted_effects,
    }


if __name__ == "__main__":
    main()
