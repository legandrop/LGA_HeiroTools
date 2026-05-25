"""
____________________________________________________________________

  LGA_H-TrackItem_LinkStatus_Explore | Lega

  Exploracion read-only del estado "Link Status" en clips seleccionados
  del timeline. No modifica el proyecto.

  Objetivo:
  - confirmar si el icono de Link Status corresponde a versionLinkedToBin()
  - comparar clips creados manualmente vs clips creados por Python
  - listar metodos relacionados con link/version/bin disponibles localmente
____________________________________________________________________
"""

import traceback

import hiero.core
import hiero.ui


KEYWORDS = ("link", "version", "bin", "current", "active", "source")


def log(message=""):
    print("[LinkStatus Explore] %s" % message)


def section(title):
    log("")
    log("=" * 90)
    log(title)
    log("=" * 90)


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


def type_name(obj):
    if obj is None:
        return "None"
    try:
        return "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)
    except Exception:
        return str(type(obj))


def filtered_methods(obj):
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


def print_methods(label, obj):
    log("")
    log("Metodos relacionados: %s [%s]" % (label, type_name(obj)))
    for name in filtered_methods(obj):
        log("  %s" % name)


def get_media_path(clip):
    media_source = safe_call(clip, "mediaSource")
    fileinfos = safe_call(media_source, "fileinfos", []) if media_source else []
    if fileinfos:
        return safe_call(fileinfos[0], "filename", "")
    return ""


def get_source_bin_item(track_item):
    source = safe_call(track_item, "source")
    if source and hasattr(source, "binItem"):
        return safe_call(source, "binItem")
    return None


def print_version_info(prefix, obj):
    if obj is None:
        log("%s: None" % prefix)
        return

    log("%s type: %s" % (prefix, type_name(obj)))
    log("%s name: %s" % (prefix, safe_call(obj, "name", "<sin nombre>")))
    for method_name in (
        "versionLinkedToBin",
        "numVersions",
        "currentVersion",
        "activeVersion",
        "activeVersionIndex",
        "versionIndex",
    ):
        if hasattr(obj, method_name):
            log("%s %s: %s" % (prefix, method_name, safe_call(obj, method_name, "<error>")))


def inspect_track_item(track_item, index):
    section("SELECCION #%d" % index)
    log("Object type: %s" % type_name(track_item))
    if isinstance(track_item, hiero.core.EffectTrackItem):
        log("Es EffectTrackItem. Se omite.")
        return
    if not isinstance(track_item, hiero.core.TrackItem):
        log("No es TrackItem. Se omite.")
        return

    log("TrackItem name: %s" % safe_call(track_item, "name", "<sin nombre>"))
    log("Track: %s" % safe_call(safe_call(track_item, "parentTrack"), "name", "<sin track>"))
    log("Timeline: %s - %s | duration=%s" % (
        safe_call(track_item, "timelineIn", "?"),
        safe_call(track_item, "timelineOut", "?"),
        safe_call(track_item, "duration", "?"),
    ))
    log("Source: %s - %s | sourceDuration=%s" % (
        safe_call(track_item, "sourceIn", "?"),
        safe_call(track_item, "sourceOut", "?"),
        safe_call(track_item, "sourceDuration", "?"),
    ))
    log("Playback speed: %s" % safe_call(track_item, "playbackSpeed", "<no disponible>"))
    log("versionLinkedToBin: %s" % safe_call(track_item, "versionLinkedToBin", "<no disponible>"))

    linked_items = safe_call(track_item, "linkedItems", [])
    log("linkedItems count: %s" % (len(linked_items) if isinstance(linked_items, (list, tuple)) else linked_items))

    source = safe_call(track_item, "source")
    bin_item = get_source_bin_item(track_item)

    print_version_info("TrackItem", track_item)
    print_version_info("SourceClip", source)
    print_version_info("BinItem", bin_item)

    log("Source media path: %s" % get_media_path(source))
    log("BinItem parent bin: %s" % safe_call(safe_call(bin_item, "parentBin"), "name", "<sin parent bin>"))

    print_methods("TrackItem object", track_item)
    print_methods("Source Clip object", source)
    print_methods("BinItem object", bin_item)


def main():
    section("INICIO")
    project = hiero.core.projects()[-1] if hiero.core.projects() else None
    seq = hiero.ui.activeSequence()
    log("Proyecto: %s" % safe_call(project, "name", "<sin proyecto>"))
    log("Sequence: %s" % safe_call(seq, "name", "<sin sequence>"))
    log("Project trackItemVersionsLinkedToBin: %s" % safe_call(project, "trackItemVersionsLinkedToBin", "<no disponible>"))

    if not seq:
        log("No active sequence.")
        return

    editor = hiero.ui.getTimelineEditor(seq)
    selection = editor.selection() if editor else []
    log("Seleccionados: %d" % len(selection))
    if not selection:
        log("Selecciona uno o mas clips del timeline y corre de nuevo.")
        return

    for index, item in enumerate(selection, start=1):
        try:
            inspect_track_item(item, index)
        except Exception:
            log("ERROR inspeccionando seleccion #%d" % index)
            log(traceback.format_exc())

    section("FIN")


if __name__ == "__main__":
    main()
