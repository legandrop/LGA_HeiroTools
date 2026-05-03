"""
____________________________________________________________________

  LGA_H-CreateV000_RemoveOverlap_Explore | Lega

  Exploracion controlada para validar borrado de clips con overlap en el
  track destino antes de implementar "Replace Timeline Clip" en Create v000.

  Por defecto NO borra nada. Primero lista los overlaps detectados.
____________________________________________________________________
"""

import traceback

import hiero.core
import hiero.ui


ALLOW_REMOVE = True

TEST_TASK = "roto"
TEST_TRACK_NAME = "_roto_"
TEST_TIMELINE_IN = 3813
TEST_TIMELINE_OUT = 4242  # exclusivo, como params["timeline_out"]


def log(message=""):
    print("[RemoveOverlap Explore] %s" % message)


def section(title):
    log("")
    log("=" * 90)
    log(title)
    log("=" * 90)


def safe_call(obj, method_name, default=None):
    if obj is None:
        return default
    try:
        attr = getattr(obj, method_name)
    except Exception:
        return default
    try:
        return attr() if callable(attr) else attr
    except Exception as exc:
        return "<ERROR %s: %s>" % (method_name, exc)


def find_track(seq, track_name):
    if not seq:
        return None
    for track in seq.videoTracks():
        if safe_call(track, "name") == track_name:
            return track
    return None


def find_overlaps(track, timeline_in, timeline_out_exclusive):
    overlaps = []
    if not track:
        return overlaps

    new_in = int(timeline_in)
    new_out = int(timeline_out_exclusive) - 1

    for item in track.items():
        if isinstance(item, hiero.core.EffectTrackItem):
            continue
        try:
            item_in = int(item.timelineIn())
            item_out = int(item.timelineOut())
        except Exception:
            continue
        if item_in <= new_out and item_out >= new_in:
            overlaps.append(item)

    return overlaps


def media_path(track_item):
    try:
        fileinfos = track_item.source().mediaSource().fileinfos()
        if fileinfos:
            return fileinfos[0].filename()
    except Exception:
        pass
    return ""


def print_item(prefix, item):
    log("%s name: %s" % (prefix, safe_call(item, "name", "<sin nombre>")))
    log("%s track: %s" % (prefix, safe_call(safe_call(item, "parentTrack"), "name", "<sin track>")))
    log("%s timeline: %s - %s | duration=%s" % (
        prefix,
        safe_call(item, "timelineIn", "?"),
        safe_call(item, "timelineOut", "?"),
        safe_call(item, "duration", "?"),
    ))
    log("%s source: %s - %s | sourceDuration=%s" % (
        prefix,
        safe_call(item, "sourceIn", "?"),
        safe_call(item, "sourceOut", "?"),
        safe_call(item, "sourceDuration", "?"),
    ))
    log("%s versionLinkedToBin: %s" % (
        prefix,
        safe_call(item, "versionLinkedToBin", "<no disponible>"),
    ))
    log("%s media: %s" % (prefix, media_path(item)))


def main():
    section("INICIO")
    log("ALLOW_REMOVE=%s" % ALLOW_REMOVE)
    log("Task: %s" % TEST_TASK)
    log("Track destino: %s" % TEST_TRACK_NAME)
    log("Rango destino: %s - %s (out exclusivo)" % (TEST_TIMELINE_IN, TEST_TIMELINE_OUT))

    seq = hiero.ui.activeSequence()
    if not seq:
        log("No active sequence.")
        return

    project = seq.project()
    track = find_track(seq, TEST_TRACK_NAME)
    if not track:
        log("Track no encontrado: %s" % TEST_TRACK_NAME)
        return

    before = find_overlaps(track, TEST_TIMELINE_IN, TEST_TIMELINE_OUT)
    section("OVERLAPS ANTES")
    log("Cantidad: %d" % len(before))
    for index, item in enumerate(before, start=1):
        print_item("[%d]" % index, item)

    if not before:
        section("FIN")
        log("No hay overlaps para borrar.")
        return

    if not ALLOW_REMOVE:
        section("FIN")
        log("Borrado deshabilitado. Cambiar ALLOW_REMOVE=True para probar removeItem().")
        return

    section("BORRADO")
    try:
        with project.beginUndo("Explore Remove Overlap"):
            for item in before:
                log("removeItem: %s" % safe_call(item, "name", "<sin nombre>"))
                track.removeItem(item)
    except Exception:
        log("ERROR durante removeItem:")
        log(traceback.format_exc())
        return

    after = find_overlaps(track, TEST_TIMELINE_IN, TEST_TIMELINE_OUT)
    section("OVERLAPS DESPUES")
    log("Cantidad: %d" % len(after))
    for index, item in enumerate(after, start=1):
        print_item("[%d]" % index, item)

    section("FIN")


if __name__ == "__main__":
    main()
