"""
____________________________________________________________________

  LGA_H-CreateV000_ImportExplore | Lega

  Exploracion segura para investigar importacion de una secuencia EXR v000
  en Hiero/Nuke Studio antes de tocar LGA_NKS_CreateV000.py.

  Fase 2: salida corta. Ya no imprime arbol completo ni inventario de APIs.
  Solo valida:
  - contexto activo minimo
  - bin destino segun OrganizeProject
  - track destino segun task
  - variantes de path para construir un hiero.core.Clip detached

  Fase actual: prueba mutante controlada con source relativo.
____________________________________________________________________
"""

import os
import re
import traceback

import hiero.core
import hiero.ui


# Puede ser:
# - un primer frame: T:/.../SHOT_comp_v000_1001.exr
# - un patron si Hiero local lo acepta: T:/.../SHOT_comp_v000_####.exr
# - vacio: el script solo inspecciona APIs/contexto.
TEST_EXR_PATH = "T:/VFX-MOR/101/MOR_1003_020/Roto/4_publish/MOR_1003_020_roto_v000/MOR_1003_020_roto_v000_1001.exr"

# Prueba variantes comunes para ver cual interpreta mejor Hiero como secuencia.
TEST_PATH_VARIANTS = True

TEST_TASK = "roto"
TEST_TIMELINE_IN = 3813
TEST_TIMELINE_OUT = 4242
TEST_SOURCE_FIRST = 1001
TEST_SOURCE_LAST = 1429

# Crear un Clip en memoria desde TEST_EXR_PATH. En principio no lo agrega al proyecto.
ALLOW_CREATE_DETACHED_CLIP = True

# Prueba mutante controlada. El script cancela si hay overlap en el track destino.
ALLOW_PROJECT_MUTATION = True
ALLOW_TEMP_BIN_ADD = False
ALLOW_TIMELINE_ADD = False
ALLOW_FINAL_FLOW_TEST = True

TEMP_BIN_PATH = "_LGA_DEBUG/CreateV000_ImportExplore"

TASK_TRACKS = {
    "comp": "_comp_",
    "roto": "_roto_",
    "cleanup": "_cleanup_",
}

SHOT_NAME_RE = re.compile(r"^(.+?)_(?:comp|roto|cleanup)_v\d+", re.IGNORECASE)


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


def find_child_bin(parent_bin, bin_name):
    if not parent_bin:
        return None
    for item in parent_bin.items():
        if isinstance(item, hiero.core.Bin) and item.name() == bin_name:
            return item
    return None


def find_or_create_child_bin(parent_bin, bin_name):
    found = find_child_bin(parent_bin, bin_name)
    if found:
        return found
    new_bin = hiero.core.Bin(bin_name)
    parent_bin.addItem(new_bin)
    return new_bin


def find_or_create_bin_path(project, bin_path):
    current_bin = safe_call(project, "clipsBin") if project else None
    if not current_bin:
        return None
    for bin_name in [part for part in bin_path.split("/") if part]:
        current_bin = find_or_create_child_bin(current_bin, bin_name)
    return current_bin


def find_track(seq, track_name):
    if not seq:
        return None
    for track in seq.videoTracks():
        if safe_call(track, "name") == track_name:
            return track
    return None


def derive_organize_project_bin_path(media_path):
    normalized = normalize_media_path(media_path)
    parts = normalized.split("/")
    if len(parts) <= 3:
        return None
    return "F %s/%s" % (parts[2], parts[3])


def print_min_context(project, seq):
    section("CONTEXTO MINIMO")
    log("Proyecto: %s" % (safe_call(project, "name", "<sin proyecto>") if project else "<sin proyecto>"))
    log("Sequence: %s" % (safe_call(seq, "name", "<sin sequence>") if seq else "<sin sequence>"))
    log("Task: %s" % TEST_TASK)
    log("Timeline esperado: %s - %s" % (TEST_TIMELINE_IN, TEST_TIMELINE_OUT))
    log("Source esperado: %s - %s" % (TEST_SOURCE_FIRST, TEST_SOURCE_LAST))

    fmt = safe_call(seq, "format")
    if fmt:
        log("Formato sequence: %sx%s @ %s" % (
            safe_call(fmt, "width", "?"),
            safe_call(fmt, "height", "?"),
            safe_call(seq, "framerate", "?"),
        ))

    bin_path = derive_organize_project_bin_path(TEST_EXR_PATH)
    log("Bin esperado segun OrganizeProject: Sequences/%s" % bin_path)

    clips_bin = safe_call(project, "clipsBin") if project else None
    target_bin = None
    if clips_bin and bin_path:
        folder_name, shot_name = bin_path.split("/", 1)
        folder_bin = find_child_bin(clips_bin, folder_name)
        target_bin = find_child_bin(folder_bin, shot_name) if folder_bin else None
    log("Bin destino existe: %s" % bool(target_bin))

    target_track_name = TASK_TRACKS.get(TEST_TASK)
    target_track = find_track(seq, target_track_name)
    log("Track destino: %s | existe=%s" % (target_track_name, bool(target_track)))
    if target_track:
        overlaps = find_overlaps(target_track, TEST_TIMELINE_IN, TEST_TIMELINE_OUT)
        log("Overlaps en track destino para rango esperado: %d" % len(overlaps))
        for item in overlaps:
            log("  overlap: %s | TL %s-%s | SRC %s-%s" % (
                safe_call(item, "name", "<sin nombre>"),
                safe_call(item, "timelineIn", "?"),
                safe_call(item, "timelineOut", "?"),
                safe_call(item, "sourceIn", "?"),
                safe_call(item, "sourceOut", "?"),
            ))


def normalize_media_path(path):
    if not path:
        return ""
    return os.path.normpath(path).replace("\\", "/")


def shot_name_from_v000_path(path):
    filename = os.path.basename(normalize_media_path(path))
    name, _ = os.path.splitext(filename)
    name = re.sub(r"_(?:%04d|#+|\d+)$", "", name)
    match = SHOT_NAME_RE.match(name)
    return match.group(1) if match else name


def find_overlaps(track, timeline_in, timeline_out):
    overlaps = []
    if not track:
        return overlaps
    for item in track.items():
        if isinstance(item, hiero.core.EffectTrackItem):
            continue
        try:
            item_in = int(item.timelineIn())
            item_out = int(item.timelineOut())
        except Exception:
            continue
        if item_in < timeline_out and item_out > timeline_in:
            overlaps.append(item)
    return overlaps


def find_existing_bin_item_by_path(bin_obj, media_path):
    media_path = normalize_media_path(media_path)
    if not bin_obj:
        return None
    for item in bin_obj.items():
        if isinstance(item, hiero.core.Bin):
            found = find_existing_bin_item_by_path(item, media_path)
            if found:
                return found
            continue
        if not isinstance(item, hiero.core.BinItem):
            continue
        active_item = safe_call(item, "activeItem")
        if not isinstance(active_item, hiero.core.Clip):
            continue
        media_source = safe_call(active_item, "mediaSource")
        fileinfos = safe_call(media_source, "fileinfos", []) if media_source else []
        for fileinfo in fileinfos or []:
            filename = normalize_media_path(safe_call(fileinfo, "filename", ""))
            if filename == media_path:
                return item
            if filename.replace("%04d", "1001") == media_path:
                return item
    return None


def inspect_clip(clip, label):
    if not clip:
        log("Clip no disponible.")
        return

    log("  Clip name: %s" % safe_call(clip, "name", "<sin nombre>"))
    log("  Clip sourceIn/sourceOut: %s - %s | duration=%s" % (
        safe_call(clip, "sourceIn", "?"),
        safe_call(clip, "sourceOut", "?"),
        safe_call(clip, "duration", "?"),
    ))
    log("  Clip binItem attached: %s" % bool(safe_call(clip, "binItem", None)))

    media_source = safe_call(clip, "mediaSource")
    if not media_source and hasattr(clip, "source"):
        source = safe_call(clip, "source")
        media_source = safe_call(source, "mediaSource") if source else None

    log("  MediaSource type: %s" % (type_name(media_source) if media_source else "None"))
    if not media_source:
        return

    log("  Media duration/startTime: %s / %s" % (
        safe_call(media_source, "duration", "?"),
        safe_call(media_source, "startTime", "?"),
    ))
    log("  Media hasVideo/hasAudio: %s / %s" % (
        safe_call(media_source, "hasVideo", "?"),
        safe_call(media_source, "hasAudio", "?"),
    ))
    log("  Media width/height: %s x %s" % (
        safe_call(media_source, "width", "?"),
        safe_call(media_source, "height", "?"),
    ))

    fileinfos = safe_call(media_source, "fileinfos", []) or []
    log("  fileinfos count: %d" % len(fileinfos))
    for index, fileinfo in enumerate(fileinfos[:2]):
        log("    [%d] filename=%s | start=%s | end=%s" % (
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
    path = normalize_media_path(path)
    if not path:
        log("TEST_EXR_PATH vacio. Se omite prueba de creacion de Clip.")
        return None

    exists = os.path.exists(path)
    parent_exists = os.path.isdir(os.path.dirname(path))
    log("  path: %s" % path)
    log("  existe path exacto: %s | carpeta padre: %s" % (exists, parent_exists))

    if not ALLOW_CREATE_DETACHED_CLIP:
        log("ALLOW_CREATE_DETACHED_CLIP=False. Se omite hiero.core.Clip(path).")
        return None

    try:
        clip = hiero.core.Clip(path)
        log("  OK: hiero.core.Clip(path)")
        inspect_clip(clip, "detached clip")
        return clip
    except Exception as exc:
        log("ERROR creando hiero.core.Clip(path): %s" % exc)
        log(traceback.format_exc())
        return None


def path_variants_from_first_frame(path):
    path = normalize_media_path(path)
    if not path:
        return []

    variants = [("first_frame", path)]
    dirname, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)

    if name.endswith("_1001"):
        stem = name[:-5]
        variants.append(("hashes", normalize_media_path(os.path.join(dirname, stem + "_####" + ext))))
        variants.append(("printf", normalize_media_path(os.path.join(dirname, stem + "_%04d" + ext))))
        variants.append(("six_hashes", normalize_media_path(os.path.join(dirname, stem + "_######" + ext))))

    return variants


def test_detached_clip_variants(path):
    section("PRUEBA VARIANTES DE PATH COMO CLIP DETACHED")
    variants = path_variants_from_first_frame(path)
    if not variants:
        log("Sin variantes para probar.")
        return None

    best_clip = None
    for label, variant_path in variants:
        log("")
        log("-- Variante: %s" % label)
        clip = test_detached_clip(variant_path)
        if clip and best_clip is None:
            best_clip = clip
    return best_clip


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


def test_final_flow(project, seq, clip):
    section("PRUEBA FINAL CONTROLADA: BIN + TIMELINE")
    if not (ALLOW_PROJECT_MUTATION and ALLOW_FINAL_FLOW_TEST):
        log("Deshabilitada. Para ejecutar: ALLOW_PROJECT_MUTATION=True y ALLOW_FINAL_FLOW_TEST=True.")
        return None
    if not project or not seq or not clip:
        log("Falta project, sequence o clip.")
        return None

    bin_path = derive_organize_project_bin_path(TEST_EXR_PATH)
    target_track_name = TASK_TRACKS.get(TEST_TASK)
    target_track = find_track(seq, target_track_name)
    if not bin_path or not target_track:
        log("Falta bin_path o target_track.")
        return None

    overlaps = find_overlaps(target_track, TEST_TIMELINE_IN, TEST_TIMELINE_OUT)
    if overlaps:
        log("Cancelado: hay overlaps en %s para %s-%s." % (
            target_track_name,
            TEST_TIMELINE_IN,
            TEST_TIMELINE_OUT,
        ))
        for item in overlaps:
            log("  overlap: %s | TL %s-%s" % (
                safe_call(item, "name", "<sin nombre>"),
                safe_call(item, "timelineIn", "?"),
                safe_call(item, "timelineOut", "?"),
            ))
        return None

    with project.beginUndo("CreateV000 ImportExplore - final flow"):
        target_bin = find_or_create_bin_path(project, bin_path)
        existing_item = find_existing_bin_item_by_path(target_bin, TEST_EXR_PATH)
        if existing_item:
            bin_item = existing_item
            source_clip = safe_call(bin_item, "activeItem")
            log("Reusando BinItem existente: %s" % safe_call(bin_item, "name", "<sin nombre>"))
        else:
            bin_item = hiero.core.BinItem(clip)
            target_bin.addItem(bin_item)
            source_clip = clip
            log("Agregado BinItem a Sequences/%s: %s" % (
                bin_path,
                safe_call(bin_item, "name", "<sin nombre>"),
            ))

        shot_name = shot_name_from_v000_path(TEST_EXR_PATH)
        track_item = target_track.addTrackItem(source_clip, TEST_TIMELINE_IN)
        track_item.setName(shot_name)
        log("TrackItem creado con target_track.addTrackItem(source_clip, %s)" % TEST_TIMELINE_IN)
        log("Estado inicial addTrackItem:")
        inspect_track_item(track_item)

        source_in = 0
        source_out = int(TEST_TIMELINE_OUT) - int(TEST_TIMELINE_IN) - 1
        timeline_out = int(TEST_TIMELINE_OUT) - 1
        log("Usando source relativo: %s - %s" % (source_in, source_out))
        log("Usando timeline out inclusivo para TrackItem: %s - %s" % (TEST_TIMELINE_IN, timeline_out))
        track_item.setTimes(TEST_TIMELINE_IN, timeline_out, source_in, source_out)
        log("TrackItem ajustado en %s." % target_track_name)
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
    log("Version linked to bin: %s" % safe_call(track_item, "versionLinkedToBin", "<no disponible>"))
    log("Parent track: %s" % safe_call(safe_call(track_item, "parentTrack"), "name", "<sin track>"))


def main():
    section("INICIO")
    log("ALLOW_PROJECT_MUTATION=%s" % ALLOW_PROJECT_MUTATION)
    log("ALLOW_TEMP_BIN_ADD=%s" % ALLOW_TEMP_BIN_ADD)
    log("ALLOW_TIMELINE_ADD=%s" % ALLOW_TIMELINE_ADD)
    log("ALLOW_FINAL_FLOW_TEST=%s" % ALLOW_FINAL_FLOW_TEST)

    project = get_active_project()
    seq = hiero.ui.activeSequence()

    print_min_context(project, seq)

    if TEST_PATH_VARIANTS:
        detached_clip = test_detached_clip_variants(TEST_EXR_PATH)
    else:
        detached_clip = test_detached_clip(TEST_EXR_PATH)
    test_optional_bin_add(project, detached_clip)
    test_optional_timeline_add(project, seq, detached_clip)
    test_final_flow(project, seq, detached_clip)

    section("FIN")
    log("Exploracion terminada.")


if __name__ == "__main__":
    main()
