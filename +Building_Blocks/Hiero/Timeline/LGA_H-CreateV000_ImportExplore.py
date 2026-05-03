"""
____________________________________________________________________

  LGA_H-CreateV000_ImportExplore | Lega

  Exploracion segura para investigar importacion de una secuencia EXR v000
  en Hiero/Nuke Studio antes de tocar LGA_NKS_CreateV000.py.

  Por defecto NO modifica el proyecto:
  - imprime proyecto, sequence, bins y tracks activos
  - imprime metodos relevantes disponibles en las clases/objetos locales
  - opcionalmente crea un hiero.core.Clip detached desde TEST_EXR_PATH

  Para pruebas con modificacion, cambiar explicitamente los flags ALLOW_*.
____________________________________________________________________
"""

import os
import traceback

import hiero.core
import hiero.ui


# Puede ser:
# - un primer frame: T:/.../SHOT_comp_v000_1001.exr
# - un patron si Hiero local lo acepta: T:/.../SHOT_comp_v000_####.exr
# - vacio: el script solo inspecciona APIs/contexto.
TEST_EXR_PATH = ""

# Crear un Clip en memoria desde TEST_EXR_PATH. En principio no lo agrega al proyecto.
ALLOW_CREATE_DETACHED_CLIP = True

# Flags destructivos/desactivados por defecto. No habilitar hasta validar la salida seca.
ALLOW_PROJECT_MUTATION = False
ALLOW_TEMP_BIN_ADD = False
ALLOW_TIMELINE_ADD = False

TEMP_BIN_PATH = "_LGA_DEBUG/CreateV000_ImportExplore"

TASK_TRACKS = {
    "comp": "_comp_",
    "roto": "_roto_",
    "cleanup": "_cleanup_",
}

METHOD_KEYWORDS = (
    "add",
    "bin",
    "clip",
    "create",
    "duration",
    "file",
    "frame",
    "import",
    "insert",
    "item",
    "media",
    "name",
    "out",
    "parent",
    "project",
    "remove",
    "source",
    "time",
    "track",
)


def log(message=""):
    print("[CreateV000 ImportExplore] %s" % message)


def section(title):
    log("")
    log("=" * 90)
    log(title)
    log("=" * 90)


def safe_call(obj, method_name, default=None):
    try:
        attr = getattr(obj, method_name)
    except Exception:
        return default

    try:
        return attr() if callable(attr) else attr
    except Exception as exc:
        return "<ERROR %s: %s>" % (method_name, exc)


def type_name(obj):
    try:
        return "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)
    except Exception:
        return str(type(obj))


def filtered_methods(obj_or_class, keywords=METHOD_KEYWORDS):
    try:
        names = dir(obj_or_class)
    except Exception as exc:
        return ["<dir error: %s>" % exc]

    filtered = []
    for name in names:
        lower = name.lower()
        if lower.startswith("__"):
            continue
        if any(keyword in lower for keyword in keywords):
            filtered.append(name)
    return sorted(set(filtered))


def print_methods(label, obj_or_class):
    section("METODOS: %s" % label)
    log("Tipo: %s" % type_name(obj_or_class))
    for name in filtered_methods(obj_or_class):
        log("  %s" % name)


def get_active_project():
    projects = hiero.core.projects()
    if not projects:
        return None

    seq = hiero.ui.activeSequence()
    if seq:
        project = safe_call(seq, "project")
        if project:
            return project

    return projects[-1]


def print_bin_tree(bin_obj, indent=0, max_depth=3):
    if not bin_obj:
        log("%s<no bin>" % ("  " * indent))
        return

    prefix = "  " * indent
    log("%s- %s [%s]" % (prefix, safe_call(bin_obj, "name", "<sin nombre>"), type_name(bin_obj)))
    if indent >= max_depth:
        return

    try:
        items = list(bin_obj.items())
    except Exception as exc:
        log("%s  <items error: %s>" % (prefix, exc))
        return

    for item in items:
        item_name = safe_call(item, "name", "<sin nombre>")
        if isinstance(item, hiero.core.Bin):
            print_bin_tree(item, indent + 1, max_depth)
        else:
            log("%s  - %s [%s]" % (prefix, item_name, type_name(item)))


def print_project_context(project):
    section("CONTEXTO DE PROYECTO")
    if not project:
        log("No hay proyecto activo.")
        return

    log("Proyecto: %s" % safe_call(project, "name", "<sin nombre>"))
    log("Project type: %s" % type_name(project))
    log("Project path: %s" % safe_call(project, "path", "<sin path>"))

    clips_bin = safe_call(project, "clipsBin")
    log("clipsBin: %s [%s]" % (safe_call(clips_bin, "name", "<sin nombre>"), type_name(clips_bin)))

    root_bin = safe_call(project, "rootBin")
    if root_bin:
        log("rootBin: %s [%s]" % (safe_call(root_bin, "name", "<sin nombre>"), type_name(root_bin)))
    else:
        log("rootBin: no disponible o no expuesto en esta version.")

    section("ARBOL clipsBin (max depth 3)")
    print_bin_tree(clips_bin, max_depth=3)


def print_sequence_context(seq):
    section("CONTEXTO DE SEQUENCE")
    if not seq:
        log("No hay sequence activa.")
        return

    log("Sequence: %s [%s]" % (safe_call(seq, "name", "<sin nombre>"), type_name(seq)))
    log("Duration: %s" % safe_call(seq, "duration", "<sin duration>"))
    log("Framerate: %s" % safe_call(seq, "framerate", "<sin framerate>"))
    fmt = safe_call(seq, "format")
    if fmt:
        log("Format: %s | %sx%s" % (
            safe_call(fmt, "name", "<sin nombre>"),
            safe_call(fmt, "width", "?"),
            safe_call(fmt, "height", "?"),
        ))

    tracks = []
    try:
        tracks = list(seq.videoTracks())
    except Exception as exc:
        log("No se pudieron leer videoTracks: %s" % exc)

    log("Video tracks: %d" % len(tracks))
    for index, track in enumerate(tracks):
        try:
            items = list(track.items())
        except Exception:
            items = []

        log("  [%02d] %s | items=%d | type=%s" % (
            index,
            safe_call(track, "name", "<sin nombre>"),
            len(items),
            type_name(track),
        ))
        for item in items:
            if isinstance(item, hiero.core.EffectTrackItem):
                item_type = "EffectTrackItem"
            else:
                item_type = "TrackItem"
            log("      %s | TL %s-%s | SRC %s-%s | %s" % (
                safe_call(item, "name", "<sin nombre>"),
                safe_call(item, "timelineIn", "?"),
                safe_call(item, "timelineOut", "?"),
                safe_call(item, "sourceIn", "?"),
                safe_call(item, "sourceOut", "?"),
                item_type,
            ))

    section("TRACKS DE TASK ESPERADOS")
    existing_names = [safe_call(track, "name", "") for track in tracks]
    for task, track_name in TASK_TRACKS.items():
        log("%s -> %s | existe=%s" % (task, track_name, track_name in existing_names))


def normalize_media_path(path):
    if not path:
        return ""
    return os.path.normpath(path).replace("\\", "/")


def inspect_clip(clip, label):
    section("CLIP INSPECTION: %s" % label)
    if not clip:
        log("Clip no disponible.")
        return

    log("Clip type: %s" % type_name(clip))
    log("Clip name: %s" % safe_call(clip, "name", "<sin nombre>"))
    log("Clip sourceIn/sourceOut: %s - %s" % (safe_call(clip, "sourceIn", "?"), safe_call(clip, "sourceOut", "?")))
    log("Clip duration: %s" % safe_call(clip, "duration", "?"))
    log("Clip binItem: %s" % safe_call(clip, "binItem", None))

    media_source = safe_call(clip, "mediaSource")
    if not media_source and hasattr(clip, "source"):
        source = safe_call(clip, "source")
        media_source = safe_call(source, "mediaSource") if source else None

    log("MediaSource: %s [%s]" % (media_source, type_name(media_source) if media_source else "None"))
    if not media_source:
        return

    log("Media duration: %s" % safe_call(media_source, "duration", "?"))
    log("Media startTime: %s" % safe_call(media_source, "startTime", "?"))
    log("Media hasVideo/hasAudio: %s / %s" % (
        safe_call(media_source, "hasVideo", "?"),
        safe_call(media_source, "hasAudio", "?"),
    ))
    log("Media width/height: %s x %s" % (
        safe_call(media_source, "width", "?"),
        safe_call(media_source, "height", "?"),
    ))

    fileinfos = safe_call(media_source, "fileinfos", []) or []
    log("fileinfos count: %d" % len(fileinfos))
    for index, fileinfo in enumerate(fileinfos[:5]):
        log("  fileinfo[%d] filename=%s | start=%s | end=%s" % (
            index,
            safe_call(fileinfo, "filename", "?"),
            safe_call(fileinfo, "startFrame", "?"),
            safe_call(fileinfo, "endFrame", "?"),
        ))


def find_or_create_bin(project, bin_path):
    current_bin = safe_call(project, "clipsBin")
    if not current_bin:
        return None

    for bin_name in [part for part in bin_path.split("/") if part]:
        found = None
        for item in current_bin.items():
            if isinstance(item, hiero.core.Bin) and item.name() == bin_name:
                found = item
                break
        if not found:
            found = hiero.core.Bin(bin_name)
            current_bin.addItem(found)
        current_bin = found
    return current_bin


def test_detached_clip(path):
    section("PRUEBA CLIP DETACHED DESDE PATH")
    path = normalize_media_path(path)
    if not path:
        log("TEST_EXR_PATH vacio. Se omite prueba de creacion de Clip.")
        return None

    exists = os.path.exists(path)
    parent_exists = os.path.isdir(os.path.dirname(path))
    log("TEST_EXR_PATH: %s" % path)
    log("Existe path exacto: %s" % exists)
    log("Existe carpeta padre: %s" % parent_exists)

    if not ALLOW_CREATE_DETACHED_CLIP:
        log("ALLOW_CREATE_DETACHED_CLIP=False. Se omite hiero.core.Clip(path).")
        return None

    try:
        clip = hiero.core.Clip(path)
        log("OK: hiero.core.Clip(path) creo un clip detached.")
        inspect_clip(clip, "detached clip")
        return clip
    except Exception as exc:
        log("ERROR creando hiero.core.Clip(path): %s" % exc)
        log(traceback.format_exc())
        return None


def test_optional_bin_add(project, clip):
    section("PRUEBA OPCIONAL: AGREGAR A TEMP BIN")
    if not project or not clip:
        log("Falta project o clip. Se omite.")
        return None

    if not (ALLOW_PROJECT_MUTATION and ALLOW_TEMP_BIN_ADD):
        log("Mutacion deshabilitada. No se crea BinItem ni se agrega al proyecto.")
        log("Flujo probable a validar luego: temp_bin.addItem(hiero.core.BinItem(clip))")
        return None

    with project.beginUndo("CreateV000 ImportExplore - temp bin add"):
        temp_bin = find_or_create_bin(project, TEMP_BIN_PATH)
        bin_item = hiero.core.BinItem(clip)
        temp_bin.addItem(bin_item)
        log("OK: agregado BinItem al bin %s" % TEMP_BIN_PATH)
        return bin_item


def test_optional_timeline_add(project, seq, clip):
    section("PRUEBA OPCIONAL: AGREGAR A TIMELINE")
    if not project or not seq or not clip:
        log("Falta project, sequence o clip. Se omite.")
        return None

    if not (ALLOW_PROJECT_MUTATION and ALLOW_TIMELINE_ADD):
        log("Mutacion deshabilitada. No se agrega nada al timeline.")
        log("Flujos probables a validar luego:")
        log("  1) track.addTrackItem(clip, timeline_in)")
        log("  2) item = track.createTrackItem(name); item.setSource(clip); item.setTimes(...); track.addItem(item)")
        log("  3) seq.addClip(clip, time, videoTrackIndex, -1)")
        return None

    tracks = list(seq.videoTracks())
    if not tracks:
        log("No hay video tracks.")
        return None

    target_track = tracks[0]
    timeline_in = 0
    try:
        timeline_in = int(hiero.ui.currentViewer().time())
    except Exception:
        pass

    with project.beginUndo("CreateV000 ImportExplore - timeline add"):
        track_item = target_track.addTrackItem(clip, timeline_in)
        log("OK: addTrackItem devolvio %s [%s]" % (track_item, type_name(track_item)))
        inspect_track_item(track_item)
        return track_item


def inspect_track_item(track_item):
    section("TRACK ITEM RESULTANTE")
    if not track_item:
        log("TrackItem no disponible.")
        return

    log("Name: %s" % safe_call(track_item, "name", "<sin nombre>"))
    log("Timeline: %s - %s" % (safe_call(track_item, "timelineIn", "?"), safe_call(track_item, "timelineOut", "?")))
    log("Source: %s - %s" % (safe_call(track_item, "sourceIn", "?"), safe_call(track_item, "sourceOut", "?")))
    log("Source duration: %s" % safe_call(track_item, "sourceDuration", "?"))
    log("Parent track: %s" % safe_call(safe_call(track_item, "parentTrack"), "name", "<sin track>"))


def print_api_inventory(project, seq):
    print_methods("hiero.core.Project class", getattr(hiero.core, "Project", None))
    if project:
        print_methods("project object", project)

    print_methods("hiero.core.Bin class", getattr(hiero.core, "Bin", None))
    clips_bin = safe_call(project, "clipsBin") if project else None
    if clips_bin:
        print_methods("project.clipsBin object", clips_bin)

    print_methods("hiero.core.BinItem class", getattr(hiero.core, "BinItem", None))
    print_methods("hiero.core.Clip class", getattr(hiero.core, "Clip", None))
    print_methods("hiero.core.Sequence class", getattr(hiero.core, "Sequence", None))
    if seq:
        print_methods("active sequence object", seq)

    print_methods("hiero.core.VideoTrack class", getattr(hiero.core, "VideoTrack", None))
    tracks = list(seq.videoTracks()) if seq else []
    if tracks:
        print_methods("first video track object", tracks[0])

    print_methods("hiero.core.TrackItem class", getattr(hiero.core, "TrackItem", None))


def main():
    section("INICIO")
    log("ALLOW_PROJECT_MUTATION=%s" % ALLOW_PROJECT_MUTATION)
    log("ALLOW_TEMP_BIN_ADD=%s" % ALLOW_TEMP_BIN_ADD)
    log("ALLOW_TIMELINE_ADD=%s" % ALLOW_TIMELINE_ADD)

    project = get_active_project()
    seq = hiero.ui.activeSequence()

    print_project_context(project)
    print_sequence_context(seq)
    print_api_inventory(project, seq)

    detached_clip = test_detached_clip(TEST_EXR_PATH)
    test_optional_bin_add(project, detached_clip)
    test_optional_timeline_add(project, seq, detached_clip)

    section("FIN")
    log("Exploracion terminada.")


if __name__ == "__main__":
    main()
