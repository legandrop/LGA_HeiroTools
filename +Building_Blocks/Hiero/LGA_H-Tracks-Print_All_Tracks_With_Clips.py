import hiero.core
import hiero.ui


def safe_call(obj, method_name, default=None):
    if obj is None or not hasattr(obj, method_name):
        return default

    try:
        method = getattr(obj, method_name)
        return method() if callable(method) else method
    except Exception as e:
        return "<ERROR %s: %s>" % (method_name, e)


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
    sign = "-" if int(frame) < 0 else ""
    total_frames = abs(int(frame))
    frames = total_frames % fps_int
    total_seconds = total_frames // fps_int
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return "%s%02d:%02d:%02d:%02d" % (sign, hours, minutes, seconds, frames)


def tc_to_frames(tc_value, fps):
    if tc_value is None:
        return None

    if isinstance(tc_value, int):
        return tc_value

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

    fmt = safe_call(seq, "format")
    fmt_fps = safe_call(fmt, "fps") if fmt else None
    if fmt_fps is not None:
        try:
            return float(fmt_fps)
        except Exception:
            pass

    return 24.0


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
    if frame is None:
        return "N/A"
    try:
        return frames_to_tc(int(frame) + int(seq_tc_start), fps)
    except Exception:
        return "N/A"


def media_path(track_item):
    try:
        fileinfos = track_item.source().mediaSource().fileinfos()
        if fileinfos:
            return fileinfos[0].filename()
    except Exception:
        pass
    return ""


def media_present(track_item):
    try:
        media_source = track_item.source().mediaSource()
        present = safe_call(media_source, "isMediaPresent")
        return present if present is not None else "N/A"
    except Exception:
        return "N/A"


def item_is_enabled(track_item):
    value = safe_call(track_item, "isEnabled")
    return value if value is not None else "N/A"


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def sorted_track_items(track):
    try:
        items = list(track.items())
    except Exception:
        return []

    # No filtramos por enabled/disabled ni por media online/offline: se imprimen
    # todos los TrackItem reales que el track devuelve.
    clips = [
        item for item in items
        if not isinstance(item, hiero.core.EffectTrackItem)
    ]

    def sort_key(item):
        timeline_in = safe_call(item, "timelineIn", 0)
        timeline_out = safe_call(item, "timelineOut", 0)
        return (
            safe_int(timeline_in),
            safe_int(timeline_out),
            str(safe_call(item, "name", "")),
        )

    return sorted(clips, key=sort_key)


def print_clip(track_label, clip_index, clip, fps, seq_tc_start):
    name = safe_call(clip, "name", "<sin nombre>")
    timeline_in = safe_call(clip, "timelineIn")
    timeline_out = safe_call(clip, "timelineOut")

    try:
        duration = int(timeline_out) - int(timeline_in) + 1
    except Exception:
        duration = "N/A"

    source_in = safe_call(clip, "sourceIn", "N/A")
    source_out = safe_call(clip, "sourceOut", "N/A")

    print(
        "    %02d | %s | TL %s - %s | TC %s - %s | frames: %s | "
        "enabled: %s | mediaPresent: %s | SRC %s - %s"
        % (
            clip_index,
            name,
            timeline_in,
            timeline_out,
            tc_label(timeline_in, fps, seq_tc_start),
            tc_label(timeline_out, fps, seq_tc_start),
            duration,
            item_is_enabled(clip),
            media_present(clip),
            source_in,
            source_out,
        )
    )

    path = media_path(clip)
    if path:
        print("       media: %s" % path)


def print_track_list(label, tracks, fps, seq_tc_start):
    tracks = list(tracks)
    print("\n--- %s tracks (%d) ---" % (label, len(tracks)))

    if not tracks:
        print("No hay tracks de %s." % label.lower())
        return

    # Hiero devuelve los tracks de abajo hacia arriba; invertimos la lista para
    # imprimirlos como se ven en el timeline, de arriba hacia abajo.
    for display_index, track in enumerate(reversed(tracks)):
        native_index = len(tracks) - 1 - display_index
        track_name = safe_call(track, "name", "<sin nombre>")
        track_index = safe_call(track, "trackIndex", native_index)
        track_enabled = safe_call(track, "isEnabled", "N/A")
        track_locked = safe_call(track, "isLocked", "N/A")

        clips = sorted_track_items(track)
        print(
            "%02d | %s | nativeIndex: %s | trackIndex: %s | "
            "enabled: %s | locked: %s | clips: %d"
            % (
                display_index,
                track_name,
                native_index,
                track_index,
                track_enabled,
                track_locked,
                len(clips),
            )
        )

        if not clips:
            print("    <sin clips>")
            continue

        for clip_index, clip in enumerate(clips):
            print_clip(label, clip_index, clip, fps, seq_tc_start)


def print_all_tracks_and_clips_in_active_timeline():
    seq = hiero.ui.activeSequence()

    if not seq:
        print("No hay una secuencia activa.")
        return

    fps = get_sequence_fps(seq)
    seq_tc_start = get_sequence_tc_start(seq, fps)

    print("=" * 80)
    print("TRACKS Y CLIPS DEL TIMELINE ACTIVO")
    print("=" * 80)
    print("Secuencia activa: %s" % seq.name())
    print("FPS detectado: %s" % fps)
    print(
        "Timecode start: %s (offset %s frames)"
        % (frames_to_tc(seq_tc_start, fps), seq_tc_start)
    )
    print("Orden de tracks: de arriba hacia abajo, como se ve en el timeline.")
    print("Orden de clips: timelineIn ascendente dentro de cada track.")
    print("OUT de clip: timelineOut() inclusivo.")

    try:
        print_track_list("Video", seq.videoTracks(), fps, seq_tc_start)
    except Exception as e:
        print("\nError leyendo video tracks: %s" % e)

    try:
        print_track_list("Audio", seq.audioTracks(), fps, seq_tc_start)
    except Exception as e:
        print("\nError leyendo audio tracks: %s" % e)


print_all_tracks_and_clips_in_active_timeline()
