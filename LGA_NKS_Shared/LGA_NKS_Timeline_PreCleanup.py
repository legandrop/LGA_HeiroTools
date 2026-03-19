"""
____________________________________________________________________________________

  LGA_NKS_Timeline_PreCleanup v1.00 | Lega
  Limpieza previa del timeline para Refresh Timeline y Switch Sequence.
  Elimina tracks NukeVFX y extiende los efectos de BurnIn
  hasta el ultimo clip visible con imagen.

  v1.00: Version inicial. Elimina tracks con tag icon 'icons:NukeVFX.png'
         y extiende los efectos del track BurnIn hasta el timelineOut
         del ultimo clip visible.
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui


TARGET_BURNIN_TRACK = "BurnIn"
TARGET_NUKEVFX_ICON = "icons:NukeVFX.png"


def debug_print(*message):
    print(*message)


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


def remove_nukevfx_tracks(seq):
    tracks_to_remove = [track for track in seq.videoTracks() if has_nukevfx_tag(track)]

    for track in tracks_to_remove:
        track_name = safe_call(track, "name", "<sin nombre>")
        seq.removeTrack(track)
        debug_print(f"Track NukeVFX eliminado: {track_name}")

    return len(tracks_to_remove)


def clip_has_visible_media(item):
    if isinstance(item, hiero.core.EffectTrackItem):
        return False

    source = safe_call(item, "source")
    if not source:
        return False

    media_source = safe_call(source, "mediaSource")
    if not media_source:
        return False

    media_present = safe_call(media_source, "isMediaPresent")
    if media_present is False:
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
            if not clip_has_visible_media(item):
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
        debug_print("No se pudo calcular el ultimo timelineOut visible.")
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
