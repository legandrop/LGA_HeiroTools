"""
____________________________________________________________________

  LGA_H-RescanSelectedClip_Explore | Lega

  Exploracion mutante controlada para probar el equivalente Python del
  boton Rescan del panel de propiedades del Read/clip seleccionado.

  Referencia Foundry Hiero Python Developers Guide:
  - Clip.refresh(): actualiza el clip si la media fuente cambio.
  - Clip.rescan(): actualiza el clip y recalcula el frame range si la
    media fuente cambio.
  - MediaSource.refresh(): actualiza info de source, pero NO actualiza
    el frame range.

  Este script llama source_clip.rescan() SOLO sobre clips seleccionados
  en timeline y luego imprime el estado antes/despues.
____________________________________________________________________
"""

import inspect
import traceback

import hiero.core
import hiero.ui

try:
    from PySide2 import QtWidgets
except Exception:
    try:
        from PySide6 import QtWidgets
    except Exception:
        QtWidgets = None


ALLOW_RESCAN = True


KEYWORDS = (
    "rescan",
    "refresh",
    "reload",
    "scan",
    "reconnect",
    "media",
    "range",
    "frame",
    "source",
    "file",
    "offline",
    "present",
)


def log(message=""):
    print("[RescanSelectedClip Explore] %s" % message)


def section(title):
    log("")
    log("=" * 90)
    log(title)
    log("=" * 90)


def type_name(obj):
    if obj is None:
        return "None"
    try:
        return "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)
    except Exception:
        return str(type(obj))


def safe_call(obj, method_name, default=None, *args):
    if obj is None:
        return default
    try:
        attr = getattr(obj, method_name)
    except Exception:
        return default
    try:
        return attr(*args) if callable(attr) else attr
    except Exception as exc:
        return "<ERROR %s: %s>" % (method_name, exc)


def filtered_names(obj):
    if obj is None:
        return []
    try:
        names = dir(obj)
    except Exception as exc:
        return ["<dir error: %s>" % exc]

    result = []
    for name in names:
        lower = name.lower()
        if lower.startswith("__"):
            continue
        if any(keyword in lower for keyword in KEYWORDS):
            result.append(name)
    return sorted(set(result))


def print_method_presence(label, obj, method_names):
    log("")
    log("%s [%s]" % (label, type_name(obj)))
    for method_name in method_names:
        exists = hasattr(obj, method_name) if obj is not None else False
        log("  has %s: %s" % (method_name, exists))


def print_filtered_api(label, obj):
    log("")
    log("API filtrada: %s [%s]" % (label, type_name(obj)))
    for name in filtered_names(obj):
        try:
            member = getattr(obj, name)
            callable_label = "callable" if callable(member) else "attr"
            signature = ""
            if callable(member):
                try:
                    signature = str(inspect.signature(member))
                except Exception:
                    signature = "()"
            log("  %s %s%s" % (callable_label, name, signature))
        except Exception as exc:
            log("  <error leyendo %s: %s>" % (name, exc))


def print_fileinfos(media_source):
    fileinfos = safe_call(media_source, "fileinfos", []) or []
    log("fileinfos count: %s" % len(fileinfos))
    for index, fileinfo in enumerate(fileinfos[:5]):
        log("  [%d] filename: %s" % (index, safe_call(fileinfo, "filename", "?")))
        log("      start/end: %s - %s" % (
            safe_call(fileinfo, "startFrame", "?"),
            safe_call(fileinfo, "endFrame", "?"),
        ))


def collect_state(track_item, source_clip, media_source):
    fileinfos = safe_call(media_source, "fileinfos", []) or []
    first_fileinfo = fileinfos[0] if fileinfos else None
    return {
        "track_timeline_in": safe_call(track_item, "timelineIn", None),
        "track_timeline_out": safe_call(track_item, "timelineOut", None),
        "track_duration": safe_call(track_item, "duration", None),
        "track_source_in": safe_call(track_item, "sourceIn", None),
        "track_source_out": safe_call(track_item, "sourceOut", None),
        "track_source_duration": safe_call(track_item, "sourceDuration", None),
        "clip_source_in": safe_call(source_clip, "sourceIn", None),
        "clip_source_out": safe_call(source_clip, "sourceOut", None),
        "clip_duration": safe_call(source_clip, "duration", None),
        "media_start": safe_call(media_source, "startTime", None),
        "media_duration": safe_call(media_source, "duration", None),
        "media_present": safe_call(media_source, "isMediaPresent", None),
        "media_offline": safe_call(media_source, "isOffline", None),
        "fileinfo_start": safe_call(first_fileinfo, "startFrame", None),
        "fileinfo_end": safe_call(first_fileinfo, "endFrame", None),
        "fileinfo_filename": safe_call(first_fileinfo, "filename", None),
    }


def print_state_delta(before, after):
    section("DELTA")
    keys = (
        "clip_source_in",
        "clip_source_out",
        "clip_duration",
        "media_start",
        "media_duration",
        "fileinfo_start",
        "fileinfo_end",
        "track_timeline_in",
        "track_timeline_out",
        "track_duration",
        "track_source_in",
        "track_source_out",
        "track_source_duration",
    )
    for key in keys:
        before_value = before.get(key)
        after_value = after.get(key)
        changed = "CHANGED" if before_value != after_value else "same"
        log("%s: %s -> %s [%s]" % (key, before_value, after_value, changed))


def print_clip_state(track_item, source_clip, media_source, bin_item, title="ESTADO"):
    section(title)
    log("TrackItem: %s [%s]" % (safe_call(track_item, "name", "<sin nombre>"), type_name(track_item)))
    log("Track: %s" % safe_call(safe_call(track_item, "parentTrack"), "name", "<sin track>"))
    log("TrackItem timeline: %s - %s | duration=%s" % (
        safe_call(track_item, "timelineIn", "?"),
        safe_call(track_item, "timelineOut", "?"),
        safe_call(track_item, "duration", "?"),
    ))
    log("TrackItem source: %s - %s | sourceDuration=%s" % (
        safe_call(track_item, "sourceIn", "?"),
        safe_call(track_item, "sourceOut", "?"),
        safe_call(track_item, "sourceDuration", "?"),
    ))

    log("")
    log("Source Clip: %s [%s]" % (safe_call(source_clip, "name", "<sin nombre>"), type_name(source_clip)))
    log("Clip sourceIn/sourceOut: %s - %s | duration=%s" % (
        safe_call(source_clip, "sourceIn", "?"),
        safe_call(source_clip, "sourceOut", "?"),
        safe_call(source_clip, "duration", "?"),
    ))
    log("Clip binItem: %s" % safe_call(bin_item, "name", "<sin bin item>"))

    log("")
    log("MediaSource [%s]" % type_name(media_source))
    log("Media startTime/duration: %s / %s" % (
        safe_call(media_source, "startTime", "?"),
        safe_call(media_source, "duration", "?"),
    ))
    log("Media present/offline: %s / %s" % (
        safe_call(media_source, "isMediaPresent", "?"),
        safe_call(media_source, "isOffline", "?"),
    ))
    log("Media width/height: %s x %s" % (
        safe_call(media_source, "width", "?"),
        safe_call(media_source, "height", "?"),
    ))
    print_fileinfos(media_source)


def inspect_selection(track_item, index):
    section("SELECCION #%d" % index)
    if isinstance(track_item, hiero.core.EffectTrackItem):
        log("Es EffectTrackItem. Se omite.")
        return
    if not isinstance(track_item, hiero.core.TrackItem):
        log("No es TrackItem. Tipo: %s" % type_name(track_item))
        return

    source_clip = safe_call(track_item, "source")
    media_source = safe_call(source_clip, "mediaSource")
    bin_item = safe_call(source_clip, "binItem")

    before = collect_state(track_item, source_clip, media_source)
    print_clip_state(track_item, source_clip, media_source, bin_item, "ESTADO ANTES")

    section("METODOS CANDIDATOS")
    candidates = ("rescan", "refresh", "reconnectMedia", "setFrameRange")
    print_method_presence("Source Clip", source_clip, candidates)
    print_method_presence("MediaSource", media_source, ("rescan", "refresh"))
    print_method_presence("TrackItem", track_item, candidates)
    print_method_presence("BinItem", bin_item, candidates)

    section("API FILTRADA")
    print_filtered_api("TrackItem", track_item)
    print_filtered_api("Source Clip", source_clip)
    print_filtered_api("MediaSource", media_source)
    print_filtered_api("BinItem", bin_item)

    section("RESCAN")
    if not ALLOW_RESCAN:
        log("ALLOW_RESCAN=False. No se llama rescan().")
        return
    if not hasattr(source_clip, "rescan"):
        log("El Source Clip no tiene rescan().")
        return

    log("Llamando source_clip.rescan() sobre: %s" % safe_call(source_clip, "name", "<sin nombre>"))
    try:
        result = source_clip.rescan()
        log("source_clip.rescan() retorno: %s" % result)
    except Exception:
        log("ERROR llamando source_clip.rescan()")
        log(traceback.format_exc())
        return

    if QtWidgets:
        try:
            QtWidgets.QApplication.processEvents()
            log("QtWidgets.QApplication.processEvents() ejecutado.")
        except Exception as exc:
            log("processEvents fallo: %s" % exc)

    media_source_after = safe_call(source_clip, "mediaSource")
    after = collect_state(track_item, source_clip, media_source_after)
    print_clip_state(track_item, source_clip, media_source_after, bin_item, "ESTADO DESPUES")
    print_state_delta(before, after)


def main():
    section("INICIO")
    log("ALLOW_RESCAN=%s" % ALLOW_RESCAN)
    seq = hiero.ui.activeSequence()
    if not seq:
        log("No active sequence.")
        return

    editor = hiero.ui.getTimelineEditor(seq)
    selection = editor.selection() if editor else []
    log("Sequence: %s" % safe_call(seq, "name", "<sin sequence>"))
    log("Seleccionados: %d" % len(selection))

    if not selection:
        log("Selecciona el clip v000 en timeline y corre de nuevo.")
        return

    for index, item in enumerate(selection, start=1):
        try:
            inspect_selection(item, index)
        except Exception:
            log("ERROR inspeccionando seleccion #%d" % index)
            log(traceback.format_exc())

    section("FIN")
    log("Exploracion terminada.")


if __name__ == "__main__":
    main()
