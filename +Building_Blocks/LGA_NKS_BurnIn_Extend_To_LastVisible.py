"""
Extiende los soft effects del track BurnIn hasta el timelineOut del ultimo clip
visible con imagen en la secuencia activa.

Este script SI modifica el timeline.
"""

import hiero.core
import hiero.ui


TRACK_NAME = "BurnIn"
DEBUG = True


def debug_print(*message):
    if DEBUG:
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


def get_sequence_fps(seq):
    fps = safe_call(seq, "fps")
    if fps is not None:
        try:
            return float(fps)
        except Exception:
            pass

    fps = safe_call(seq, "framerate")
    if fps is not None:
        try:
            return float(fps)
        except Exception:
            pass

        for attr_name in ("toFloat", "asFloat", "fps", "value", "numerator"):
            value = safe_call(fps, attr_name)
            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

    return 24.0


def normalize_fps_int(fps):
    try:
        fps_int = int(round(float(fps)))
        return fps_int if fps_int > 0 else 24
    except Exception:
        return 24


def frames_to_tc(frame, fps):
    if frame is None:
        return "N/A"

    fps_int = normalize_fps_int(fps)
    sign = "-" if frame < 0 else ""
    total_frames = abs(int(frame))
    frames = total_frames % fps_int
    total_seconds = total_frames // fps_int
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def tc_to_frames(tc_value, fps):
    if tc_value is None:
        return None

    try:
        return int(tc_value)
    except Exception:
        pass

    tc_str = str(tc_value).strip()
    if not tc_str:
        return None

    negative = tc_str.startswith("-")
    if negative:
        tc_str = tc_str[1:]

    parts = tc_str.split(":")
    if len(parts) != 4:
        return None

    try:
        hours, minutes, seconds, frames = [int(part) for part in parts]
    except Exception:
        return None

    fps_int = normalize_fps_int(fps)
    total = (((hours * 60) + minutes) * 60 + seconds) * fps_int + frames
    return -total if negative else total


def get_sequence_tc_start(seq, fps):
    candidates = [
        safe_call(seq, "timecodeStart"),
        safe_call(seq, "startTimecode"),
        safe_call(seq, "sourceTimecodeStart"),
    ]

    for candidate in candidates:
        if candidate is None:
            continue

        try:
            return int(candidate)
        except Exception:
            pass

        parsed = tc_to_frames(candidate, fps)
        if parsed is not None:
            return parsed

    return 0


def tc_label(frame, fps, seq_tc_start):
    tc_frame = None if frame is None else int(frame) + int(seq_tc_start)
    return f"{frames_to_tc(tc_frame, fps)} (frame {frame})"


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


def get_last_visible_clip(seq):
    last_track = None
    last_item = None
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

            if last_out is None or timeline_out > last_out:
                last_track = track
                last_item = item
                last_out = int(timeline_out)

    return last_track, last_item, last_out


def get_burnin_track(seq):
    for track in seq.videoTracks():
        if safe_call(track, "name") == TRACK_NAME:
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


def get_active_project():
    seq = hiero.ui.activeSequence()
    if seq:
        project = safe_call(seq, "project")
        if project:
            return project

    projects = hiero.core.projects()
    return projects[-1] if projects else None


def main():
    print("=" * 100)
    print("LGA_NKS_BurnIn_Extend_To_LastVisible")
    print("=" * 100)

    seq = hiero.ui.activeSequence()
    if not seq:
        print("No hay una secuencia activa.")
        return

    fps = get_sequence_fps(seq)
    seq_tc_start = get_sequence_tc_start(seq, fps)
    burnin_track = get_burnin_track(seq)
    if not burnin_track:
        print(f"No se encontro el track '{TRACK_NAME}'.")
        return

    effects = get_burnin_effects(burnin_track)
    if not effects:
        print(f"El track '{TRACK_NAME}' no tiene soft effects para extender.")
        return

    last_track, last_item, target_timeline_out = get_last_visible_clip(seq)
    if last_item is None or target_timeline_out is None:
        print("No se pudo encontrar un ultimo clip visible con imagen.")
        return

    target_last_visible = target_timeline_out - 1

    print(f"Secuencia activa: {safe_call(seq, 'name', '<sin nombre>')}")
    print(f"Track BurnIn: {safe_call(burnin_track, 'name', '<sin nombre>')}")
    print(
        f"Ultimo clip visible: {safe_call(last_item, 'name', '<sin nombre>')} "
        f"en track {safe_call(last_track, 'name', '<sin nombre>')}"
    )
    print(f"timelineOut objetivo: {tc_label(target_timeline_out, fps, seq_tc_start)}")
    print(f"ultimo TC con imagen: {tc_label(target_last_visible, fps, seq_tc_start)}")
    print("")

    project = get_active_project()
    if not project:
        print("No se pudo obtener el proyecto activo para crear un undo.")
        return

    changed = []
    unchanged = []
    errors = []

    with project.beginUndo("Extend BurnIn to Last Visible"):
        for effect in effects:
            effect_name = safe_call(effect, "name", "<sin nombre>")
            old_out = safe_call(effect, "timelineOut")
            old_in = safe_call(effect, "timelineIn")

            if old_out is None:
                errors.append((effect_name, "timelineOut es None"))
                continue

            old_out = int(old_out)

            if old_out == target_timeline_out:
                unchanged.append((effect_name, old_in, old_out))
                continue

            try:
                effect.setTimelineOut(int(target_timeline_out))
                changed.append((effect_name, old_in, old_out, target_timeline_out))
            except Exception as exc:
                errors.append((effect_name, str(exc)))

    if changed:
        print("Efectos ajustados:")
        for effect_name, old_in, old_out, new_out in changed:
            print(
                f"  - {effect_name}: "
                f"{tc_label(old_out, fps, seq_tc_start)} -> {tc_label(new_out, fps, seq_tc_start)}"
            )

    if unchanged:
        print("Efectos que ya estaban correctos:")
        for effect_name, old_in, old_out in unchanged:
            print(f"  - {effect_name}: {tc_label(old_out, fps, seq_tc_start)}")

    if errors:
        print("Efectos con error:")
        for effect_name, error_text in errors:
            print(f"  - {effect_name}: {error_text}")

    print("")
    print(
        f"Resumen: {len(changed)} efecto(s) ajustado(s), "
        f"{len(unchanged)} sin cambios, {len(errors)} con error."
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
