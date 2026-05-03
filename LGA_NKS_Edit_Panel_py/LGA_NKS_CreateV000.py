"""
____________________________________________________________________

  LGA_NKS_CreateV000 v1.02 | Lega

  Crea una secuencia EXR negra v000 para el shot activo en Hiero/Nuke Studio.
  Permite elegir frame range, resolucion, handle persistente y una o varias
  tasks destino (comp, roto, cleanup), procesadas en orden.

  La v000 se importa al bin del shot, se colorea como v_00, y si se coloca en
  timeline queda deshabilitada. Tambien permite previsualizar el rango con
  Preview In/Out antes de crearla.

  Si ya existen EXRs, permite reemplazarlos. Si hay solape en timeline, permite
  crear solo los EXRs, crear/importar al bin sin insertar, o reemplazar los
  clips solapados por la nueva v000.

  v1.02: Agregado sistema de logging dual con archivo propio debugPy_CreateV000.log
  v1.01: Actualizado para usar compression dwaa en oiiotool

____________________________________________________________________

"""

import os
import configparser
import logging
import queue
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from logging.handlers import QueueHandler, QueueListener

import hiero.core
import hiero.ui

START_FRAME = 1001
VERSION = "v000"
V000_CLIP_COLOR_RGB = (138, 138, 138)
DEFAULT_HANDLE = 4
CONFIG_DIR_NAME = "LGA"
CONFIG_SUBDIR_NAME = "HieroTools"
CONFIG_FILE_NAME = "CreateV000.ini"
CONFIG_SECTION = "Settings"
CONFIG_HANDLE_KEY = "handle"
TASKS = ("comp", "roto", "cleanup")
TASK_FOLDER = {
    "comp": "Comp",
    "roto": "Roto",
    "cleanup": "Cleanup",
}
RANGE_SOURCE_EDITREF = "editref"
TASK_COLORS = {
    "comp":    "#3381e0",
    "roto":    "#2abf7e",
    "cleanup": "#27c8c3",
}

# Sistema de colores de path por nivel (igual que LGA_mediaManager / LGA_PipeSync)
PATH_SHOT_COLOR = "#c56cf0"   # lavanda — segmentos dentro del shot folder
PATH_SEP_COLOR  = "#bbbbbb"   # gris claro — separadores /
VALUE_COLOR     = "#e8c97a"   # amarillo dorado — valores numéricos en el output
PATH_LEVEL_COLORS = {
    0: "#ffff66",   # Amarillo       disco
    1: "#28b5b5",   # Verde cian     proyecto
    2: "#ff9a8a",   # Naranja pastel grupo
    3: "#0088ff",   # Azul           shot
    4: "#ffd369",   # Amarillo mostaza
    5: "#28b5b5",   # Verde cian
    6: "#ff9a8a",   # Naranja pastel
    7: "#6bc9ff",   # Celeste
    8: "#ffd369",
    9: "#28b5b5",
    10: "#ff9a8a",
    11: "#6bc9ff",
}
RANGE_SOURCE_PLATE = "plate"

CURRENT_DIR = Path(__file__).resolve().parent
STARTUP_DIR = CURRENT_DIR.parent
SHARED_DIR = STARTUP_DIR / "LGA_NKS_Shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(STARTUP_DIR))

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore
from LGA_NKS_Flow_NamingUtils import clean_base_name, extract_project_name, extract_shot_code
from LGA_NKS_TaskSelectionDialog import track_for_task
from LGA_NKS_Flow_Task_Config import get_task_color


# Variables globales de logging (valores por defecto)
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
script_start_time = None
debug_log_listener = None


class RelativeTimeFormatter(logging.Formatter):
    """Formatter que incluye tiempo relativo desde el inicio del script."""
    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created

        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="CreateV000"):
    """Configura el logging para escribir SOLO en archivo."""
    global debug_log_listener

    log_filename = f"debugPy_{script_name}.log"
    log_file_path = os.path.join(
        os.path.dirname(__file__), "..", "logs", log_filename
    )

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception:
        pass

    logger_name = f"{script_name.lower()}_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    formatter = RelativeTimeFormatter("[%(relative_time)s] %(message)s")
    file_handler.setFormatter(formatter)

    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass

    debug_log_listener = QueueListener(
        log_queue, file_handler, respect_handler_level=True
    )
    debug_log_listener.daemon = True
    debug_log_listener.start()

    return logger


debug_logger = setup_debug_logging(script_name="CreateV000")


def debug_print(*message, level="info"):
    """Funcion de logging dual con switches por consola/archivo."""
    global script_start_time

    msg = " ".join(str(arg) for arg in message)

    if DEBUG and DEBUG_LOG:
        if script_start_time is None:
            script_start_time = time.time()

        if level == "debug":
            debug_logger.debug(msg)
        elif level == "warning":
            debug_logger.warning(msg)
        elif level == "error":
            debug_logger.error(msg)
        else:
            debug_logger.info(msg)

    if DEBUG and DEBUG_CONSOLE:
        if script_start_time is None:
            script_start_time = time.time()

        relative_time = time.time() - script_start_time
        print(f"[{relative_time:.3f}s] {msg}")


def cleanup_logging():
    """Detiene el listener de logging al terminar."""
    global debug_log_listener
    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass


try:
    import atexit
    atexit.register(cleanup_logging)
except Exception:
    pass


debug_print("Iniciando LGA_NKS_CreateV000.py...")


def _user_config_root():
    if sys.platform.startswith("win"):
        config_root = os.getenv("APPDATA")
        if config_root:
            return config_root
        return os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.path.expanduser("~/.config")


def _config_path():
    return os.path.join(
        _user_config_root(),
        CONFIG_DIR_NAME,
        CONFIG_SUBDIR_NAME,
        CONFIG_FILE_NAME,
    )


def _clamp_handle(value):
    try:
        return max(0, min(99, int(value)))
    except Exception:
        return DEFAULT_HANDLE


def _write_handle_setting(handle_value):
    config_file = _config_path()
    config_dir = os.path.dirname(config_file)
    try:
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)

        config = configparser.ConfigParser()
        config[CONFIG_SECTION] = {
            CONFIG_HANDLE_KEY: str(_clamp_handle(handle_value)),
        }
        with open(config_file, "w", encoding="utf-8") as file_handle:
            config.write(file_handle)
        return None
    except Exception as exc:
        return "Failed to write Create v000 settings: %s" % exc


def _read_handle_setting():
    config_file = _config_path()
    if not os.path.isfile(config_file):
        error = _write_handle_setting(DEFAULT_HANDLE)
        if error:
            debug_print(error)
        return DEFAULT_HANDLE

    config = configparser.ConfigParser()
    try:
        config.read(config_file, encoding="utf-8")
        missing_setting = (
            not config.has_section(CONFIG_SECTION)
            or not config.has_option(CONFIG_SECTION, CONFIG_HANDLE_KEY)
        )
        value = config.get(CONFIG_SECTION, CONFIG_HANDLE_KEY, fallback=str(DEFAULT_HANDLE))
    except Exception as exc:
        debug_print("Failed to read Create v000 settings:", exc)
        missing_setting = True
        value = DEFAULT_HANDLE

    handle = _clamp_handle(value)
    if missing_setting or str(handle) != str(value).strip():
        error = _write_handle_setting(handle)
        if error:
            debug_print(error)
    return handle


def _colorize_path(path, shot_root):
    """Retorna el path como HTML coloreado por niveles.

    Los segmentos dentro del shot_root reciben el color lavanda (PATH_SHOT_COLOR).
    Los segmentos posteriores reciben el color de su nivel absoluto (PATH_LEVEL_COLORS).
    Los separadores / van en gris claro (PATH_SEP_COLOR).
    """
    parts = path.replace("\\", "/").split("/")
    shot_depth = len(shot_root.replace("\\", "/").split("/"))

    colored = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if i < shot_depth:
            color = PATH_SHOT_COLOR
        else:
            color = PATH_LEVEL_COLORS.get(i, "#bbbbbb")
        colored.append('<span style="color: %s;">%s</span>' % (color, part))

    sep = '<span style="color: %s;">/</span>' % PATH_SEP_COLOR
    return sep.join(colored)



def _current_time():
    viewer = hiero.ui.currentViewer()
    if not viewer:
        return None
    try:
        return viewer.time()
    except Exception:
        player = viewer.player() if hasattr(viewer, "player") else None
        return player.time() if player else None


def _clip_media_path(clip):
    try:
        fileinfos = clip.source().mediaSource().fileinfos()
        if fileinfos:
            return fileinfos[0].filename()
    except Exception:
        pass
    return ""


def _clip_file_name(clip):
    return os.path.basename(_clip_media_path(clip).replace("\\", "/"))


def _frame_count(timeline_in, timeline_out):
    return max(0, int(timeline_out) - int(timeline_in) + 1)


def _timeline_resolution(seq):
    try:
        fmt = seq.format()
        return int(fmt.width()), int(fmt.height())
    except Exception:
        return None, None


def _call_int_method(obj, names):
    for name in names:
        if not hasattr(obj, name):
            continue
        try:
            value = getattr(obj, name)()
            if value:
                return int(value)
        except Exception:
            pass
    return None


def _metadata_resolution(metadata):
    if not metadata:
        return None, None

    width_keys = (
        "foundry.source.width",
        "input/width",
        "exr/displayWindow/width",
        "exr/dataWindow/width",
        "width",
    )
    height_keys = (
        "foundry.source.height",
        "input/height",
        "exr/displayWindow/height",
        "exr/dataWindow/height",
        "height",
    )

    def read(keys):
        for key in keys:
            try:
                value = metadata.get(key)
            except Exception:
                value = metadata[key] if key in metadata else None
            if value:
                try:
                    return int(float(value))
                except Exception:
                    pass
        return None

    return read(width_keys), read(height_keys)


def _plate_resolution(clip):
    try:
        source = clip.source()
        media_source = source.mediaSource()
    except Exception:
        return None, None

    for obj in (source, media_source):
        width = _call_int_method(obj, ("width",))
        height = _call_int_method(obj, ("height",))
        if width and height:
            return width, height

    try:
        metadata = media_source.metadata()
        width, height = _metadata_resolution(metadata)
        if width and height:
            return width, height
    except Exception:
        pass

    try:
        fileinfos = media_source.fileinfos()
        for fileinfo in fileinfos:
            width = _call_int_method(fileinfo, ("width",))
            height = _call_int_method(fileinfo, ("height",))
            if width and height:
                return width, height
    except Exception:
        pass

    return None, None


def _derive_shot_root(media_path):
    normalized = media_path.replace("\\", "/")
    parts = normalized.split("/")
    input_index = None
    for index, part in enumerate(parts):
        if part.lower() == "_input":
            input_index = index
            break
    if input_index is None or input_index == 0:
        return None
    return "/".join(parts[:input_index])


def _derive_shot_code(clip, shot_root):
    file_name = _clip_file_name(clip)
    base_name = clean_base_name(file_name)
    shot_code = extract_shot_code(base_name)
    if shot_code:
        return shot_code
    if shot_root:
        return os.path.basename(shot_root.rstrip("/\\"))
    try:
        return clip.name()
    except Exception:
        return ""


def _find_clip_at_time(track, current_time):
    if current_time is None:
        return None
    for item in track.items():
        if isinstance(item, hiero.core.EffectTrackItem):
            continue
        try:
            if item.timelineIn() <= current_time <= item.timelineOut():
                return item
        except Exception:
            pass
    return None


def _is_plate_track(track_name):
    return bool(re.search(r"plate$", track_name, flags=re.IGNORECASE))


def _is_editref_track(track_name):
    return bool(re.search(r"editref", track_name, flags=re.IGNORECASE))


def _range_source_from_clip(track_name, track_index, clip, source_type):
    media_path = _clip_media_path(clip)
    width, height = _plate_resolution(clip) if source_type == RANGE_SOURCE_PLATE else (None, None)
    return {
        "track_name": track_name,
        "track_index": track_index,
        "source_type": source_type,
        "clip": clip,
        "clip_name": clip.name(),
        "timeline_in": int(clip.timelineIn()),
        "timeline_out": int(clip.timelineOut()),
        "frame_count": _frame_count(clip.timelineIn(), clip.timelineOut()),
        "width": width,
        "height": height,
        "media_path": media_path,
    }


def _collect_range_sources(seq, current_time):
    tracks = list(seq.videoTracks())
    editrefs = []
    plates = []

    # Hiero usually exposes tracks bottom-to-top; reverse keeps the visual top first.
    for track_index, track in reversed(list(enumerate(tracks))):
        track_name = track.name()
        if _is_editref_track(track_name):
            source_type = RANGE_SOURCE_EDITREF
        elif _is_plate_track(track_name):
            source_type = RANGE_SOURCE_PLATE
        else:
            continue

        clip = _find_clip_at_time(track, current_time)
        if not clip:
            continue

        source = _range_source_from_clip(track_name, track_index, clip, source_type)
        if source_type == RANGE_SOURCE_EDITREF:
            editrefs.append(source)
        else:
            plates.append(source)

    return editrefs + plates, plates


def _oiio_tool_path():
    if not sys.platform.startswith("win"):
        return None
    tool_path = SHARED_DIR / "OIIO_Win" / "oiiotool.exe"
    return tool_path if tool_path.exists() else None


def _frame_file_name(pattern, frame):
    return pattern.replace("####", "%04d" % frame)


def _first_frame_path(params):
    return "/".join(
        [
            params["output_dir"].rstrip("/\\"),
            _frame_file_name(params["output_name_pattern"], params["source_first_frame"]),
        ]
    )


def _output_has_exrs(params):
    output_dir = Path(params["output_dir"])
    return output_dir.exists() and bool(list(output_dir.glob("*.exr")))


def _active_project_for_sequence(seq):
    try:
        project = seq.project()
        if project:
            return project
    except Exception:
        pass

    projects = hiero.core.projects()
    return projects[-1] if projects else None


def _find_child_bin(parent_bin, bin_name):
    if not parent_bin:
        return None
    for item in parent_bin.items():
        if isinstance(item, hiero.core.Bin) and item.name() == bin_name:
            return item
    return None


def _find_or_create_child_bin(parent_bin, bin_name):
    found = _find_child_bin(parent_bin, bin_name)
    if found:
        return found
    new_bin = hiero.core.Bin(bin_name)
    parent_bin.addItem(new_bin)
    return new_bin


def _target_bin_path_from_media_path(media_path):
    normalized = media_path.replace("\\", "/")
    parts = normalized.split("/")
    if len(parts) <= 3:
        return None
    return "F %s/%s" % (parts[2], parts[3])


def _find_or_create_bin_path(project, bin_path):
    current_bin = project.clipsBin()
    for bin_name in [part for part in bin_path.split("/") if part]:
        current_bin = _find_or_create_child_bin(current_bin, bin_name)
    return current_bin


def _find_bin_item_by_media_path(bin_item, first_frame_path):
    first_frame_path = first_frame_path.replace("\\", "/")
    for item in bin_item.items():
        if isinstance(item, hiero.core.Bin):
            found = _find_bin_item_by_media_path(item, first_frame_path)
            if found:
                return found
            continue
        if not isinstance(item, hiero.core.BinItem):
            continue
        try:
            active_item = item.activeItem()
        except Exception:
            continue
        if not isinstance(active_item, hiero.core.Clip):
            continue
        try:
            fileinfos = active_item.mediaSource().fileinfos()
        except Exception:
            fileinfos = []
        for fileinfo in fileinfos:
            try:
                filename = fileinfo.filename().replace("\\", "/")
            except Exception:
                continue
            if filename == first_frame_path or filename.replace("%04d", "1001") == first_frame_path:
                return item
    return None


def _import_v000_to_bin(project, params):
    first_frame_path = _first_frame_path(params)
    bin_path = _target_bin_path_from_media_path(first_frame_path)
    if not bin_path:
        return None, None, "Could not derive target bin path from: %s" % first_frame_path

    target_bin = _find_or_create_bin_path(project, bin_path)
    existing_bin_item = _find_bin_item_by_media_path(target_bin, first_frame_path)
    if existing_bin_item:
        return existing_bin_item.activeItem(), existing_bin_item, None

    clip = hiero.core.Clip(first_frame_path)
    clip.setName("%s_%s" % (params["shot_code"], params["task"]))
    bin_item = hiero.core.BinItem(clip)
    target_bin.addItem(bin_item)
    return clip, bin_item, None


def _set_v000_clip_color(bin_item):
    color = QtGui.QColor(*V000_CLIP_COLOR_RGB)
    try:
        bin_item.setColor(color)
        return None
    except Exception as exc:
        return "Failed to set v000 clip color: %s" % exc


def _find_video_track(seq, track_name):
    for track in seq.videoTracks():
        if track.name() == track_name:
            return track
    return None


def _timeline_overlaps(track, timeline_in, timeline_out):
    overlaps = []
    new_in = int(timeline_in)
    new_out = int(timeline_out)
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


def _overlap_summary(overlaps):
    lines = []
    for item in overlaps:
        try:
            track_name = item.parentTrack().name()
        except Exception:
            track_name = "<unknown>"
        lines.append(
            "%s | %s | %s - %s"
            % (item.name(), track_name, item.timelineIn(), item.timelineOut())
        )
    return "\n".join(lines)


def _insert_v000_in_timeline(seq, clip, params):
    track_name = track_for_task(params["task"])
    target_track = _find_video_track(seq, track_name)
    if not target_track:
        return None, "Target track not found: %s" % track_name

    overlaps = _timeline_overlaps(target_track, params["timeline_in"], params["timeline_out"])
    if overlaps:
        return None, "Target track has overlaps:\n%s" % _overlap_summary(overlaps)

    frame_count = int(params["frame_count"])
    timeline_in = int(params["timeline_in"])
    timeline_out = int(params["timeline_out"])
    source_in = 0
    source_out = frame_count - 1

    track_item = target_track.addTrackItem(clip, timeline_in)
    track_item.setName(params["shot_code"])
    track_item.setTimes(timeline_in, timeline_out, source_in, source_out)
    track_item.setVersionLinkedToBin(True)
    return track_item, None


def _disable_timeline_item(track_item):
    try:
        track_item.setEnabled(False)
        return None
    except Exception as exc:
        return "Failed to disable v000 timeline clip: %s" % exc


def _zoom_timeline_to_preview_range(seq, timeline_in, timeline_items=None, dialog=None):
    try:
        if dialog:
            dialog.hide()
            QtWidgets.QApplication.processEvents()

        viewer = hiero.ui.currentViewer()
        if viewer:
            viewer.setTime(int(timeline_in))

        timeline_editor = hiero.ui.getTimelineEditor(seq)
        if timeline_editor:
            if timeline_items:
                timeline_editor.setSelection(list(timeline_items))
            window = timeline_editor.window()
            window.activateWindow()
            window.setFocus()

        def zoom_to_fit():
            hiero.ui.findMenuAction("Zoom to Fit").trigger()

        def restore_dialog():
            if timeline_editor:
                timeline_editor.selectNone()
            if dialog:
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

        QtCore.QTimer.singleShot(50, zoom_to_fit)
        QtCore.QTimer.singleShot(250, restore_dialog)
        return None
    except Exception as exc:
        if dialog:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        return "Failed to zoom timeline to v000 range: %s" % exc


def _remove_timeline_items(track, items):
    for item in list(items):
        track.removeItem(item)


def _create_black_exr_sequence(params, replace=False):
    oiiotool = _oiio_tool_path()
    if not oiiotool:
        return False, "error", "OIIO Windows tool not found. Mac implementation is pending."

    output_dir = Path(params["output_dir"])
    if output_dir.exists():
        existing_exrs = list(output_dir.glob("*.exr"))
        if existing_exrs:
            if not replace:
                return False, "exists", "Output folder already contains EXR files: %s" % output_dir
            try:
                shutil.rmtree(str(output_dir))
            except Exception as exc:
                return False, "error", "Failed to remove existing v000 folder: %s" % exc
            output_dir.mkdir(parents=True)
    else:
        output_dir.mkdir(parents=True)

    first_frame = int(params["source_first_frame"])
    last_frame = int(params["source_last_frame"])
    frame_count = int(params["frame_count"])
    width, height = params["resolution"]
    pattern = params["output_name_pattern"]

    first_file = output_dir / _frame_file_name(pattern, first_frame)
    cmd = [
        str(oiiotool),
        "--create",
        "%dx%d" % (int(width), int(height)),
        "3",
        "--chnames",
        "R,G,B",
        "-d",
        "half",
        "--compression",
        "dwaa",
        "-o",
        str(first_file),
    ]

    env = os.environ.copy()
    env["PATH"] = str(oiiotool.parent) + os.pathsep + env.get("PATH", "")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(oiiotool.parent),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
    except Exception as exc:
        return False, "error", "Failed to run oiiotool: %s" % exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        return False, "error", "oiiotool failed: %s" % (stderr or result.returncode)
    if not first_file.exists():
        return False, "error", "oiiotool did not create the first EXR frame."

    try:
        for frame in range(first_frame + 1, last_frame + 1):
            target = output_dir / _frame_file_name(pattern, frame)
            shutil.copyfile(str(first_file), str(target))
    except Exception as exc:
        return False, "error", "Failed while duplicating EXR frames: %s" % exc

    written = list(output_dir.glob("*.exr"))
    if len(written) != frame_count:
        return False, "error", "Expected %d EXR files, found %d." % (frame_count, len(written))

    return True, "created", "Created %d EXR frames in %s" % (frame_count, output_dir)


def _collect_context():
    seq = hiero.ui.activeSequence()
    if not seq:
        return None, "No active sequence."

    current_time = _current_time()
    if current_time is None:
        return None, "No active viewer/playhead."

    range_sources, plates = _collect_range_sources(seq, current_time)
    if not range_sources:
        return None, "No editref or plate tracks found."
    if not plates:
        return None, "No plate tracks found."

    default_plate = plates[0]
    shot_root = _derive_shot_root(default_plate["media_path"])
    shot_code = _derive_shot_code(default_plate["clip"], shot_root)
    if not shot_code:
        return None, "Could not detect shot."

    width, height = _timeline_resolution(seq)
    try:
        project_name = extract_project_name(clean_base_name(_clip_file_name(default_plate["clip"]))) or ""
    except Exception:
        project_name = ""
    return {
        "sequence": seq,
        "shot_code": shot_code,
        "project_name": project_name,
        "shot_root_path": shot_root,
        "range_sources": range_sources,
        "plates": plates,
        "timeline_resolution": (width, height),
    }, None


class CreateV000Dialog(QtWidgets.QDialog):
    def __init__(self, context, parent=None):
        super(CreateV000Dialog, self).__init__(parent)
        self.context = context
        self.plate_checks = []
        self._syncing_range_checks = False
        self.resolution_buttons = {}
        self.task_buttons = {}
        self.saved_handle_value = _read_handle_setting()

        self.setWindowTitle("Create v000 - %s" % context["shot_code"])
        self.setMinimumWidth(720)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
            """
        )
        self._build_ui()
        self._update_state()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        project_name = self.context.get("project_name") or ""
        shot_code = self.context.get("shot_code") or ""
        if project_name:
            info_text = (
                "<span style='color:#6AB5CA;'>%s</span> / "
                "<span style='color:#B56AB5;'>%s</span>"
            ) % (project_name, shot_code)
        else:
            info_text = "<span style='color:#B56AB5;'>%s</span>" % shot_code

        header_row = QtWidgets.QHBoxLayout()
        info_label = QtWidgets.QLabel(info_text)
        info_label.setTextFormat(QtCore.Qt.RichText)
        info_label.setStyleSheet(
            "color: #CCCCCC; padding: 2px 5px 0px 5px; font-size: 14px; font-weight: bold;"
        )
        header_row.addWidget(info_label, 0, QtCore.Qt.AlignLeft)
        header_row.addStretch()
        title = QtWidgets.QLabel("Create v000")
        title.setStyleSheet(
            "color: #CCCCCC; padding: 2px 5px 0px 5px; font-size: 14px; font-weight: bold;"
        )
        header_row.addWidget(title, 0, QtCore.Qt.AlignRight)
        layout.addLayout(header_row)

        self.warning_label = QtWidgets.QLabel("")
        self.warning_label.setStyleSheet("color: #d9a441; padding: 2px 5px;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(16)

        frame_range_col = QtWidgets.QVBoxLayout()
        frame_range_col.addWidget(self._section_label("FRAME RANGE"))
        frame_range_col.addWidget(self._build_plates_table())
        frame_range_col.addStretch()
        top_row.addLayout(frame_range_col, 1)
        top_row.addWidget(self._build_separator("v"))

        resolution_col = QtWidgets.QVBoxLayout()
        resolution_col.addWidget(self._section_label("RESOLUTION"))
        resolution_col.addWidget(self._build_resolution_box())
        resolution_col.addStretch()
        top_row.addLayout(resolution_col, 1)
        layout.addLayout(top_row)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        middle_row = QtWidgets.QHBoxLayout()
        middle_row.setSpacing(16)

        handle_col = QtWidgets.QVBoxLayout()
        handle_col.addWidget(self._section_label("HANDLE"))
        handle_col.addWidget(self._build_handle_box())
        handle_col.addStretch()
        middle_row.addLayout(handle_col, 1)
        middle_row.addWidget(self._build_separator("v"))

        task_col = QtWidgets.QVBoxLayout()
        task_col.addWidget(self._section_label("TASK"))
        task_col.addWidget(self._build_task_box())
        task_col.addStretch()
        middle_row.addLayout(task_col, 1)
        layout.addLayout(middle_row)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        layout.addWidget(self._section_label("OUTPUT"))
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(128)
        self.output_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 5px;
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(self.output_text)

        buttons = QtWidgets.QHBoxLayout()
        self.preview_in_out_btn = QtWidgets.QPushButton("Preview In/Out")
        self.preview_in_out_btn.clicked.connect(self._preview_in_out)
        self.preview_in_out_btn.setToolTip("Set timeline In/Out to the v000 range")
        self.preview_in_out_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                color: #CCCCCC;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:disabled { background-color: #2a2a2a; color: #666666; border: 1px solid #3a3a3a; }
            """
        )
        buttons.addWidget(self.preview_in_out_btn)
        buttons.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #CCCCCC;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #666666; }
            """
        )
        self.create_btn = QtWidgets.QPushButton("Create v000")
        self.create_btn.clicked.connect(self._create_v000)
        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #443a91;
                color: #b2b2b2;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #774dcb; color: #CCCCCC; }
            QPushButton:disabled { background-color: #2f2a5e; color: #6a6a6a; }
            """
        )
        buttons.addWidget(cancel_btn)
        buttons.addSpacing(10)
        buttons.addWidget(self.create_btn)
        layout.addLayout(buttons)

    def _section_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 5px;")
        return label

    def _build_separator(self, orientation="h"):
        sep = QtWidgets.QFrame()
        if orientation == "v":
            sep.setFrameShape(QtWidgets.QFrame.VLine)
        else:
            sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        sep.setStyleSheet("color: #444444; margin: 0px;")
        return sep

    def _build_plates_table(self):
        table = QtWidgets.QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Use", "Track", "TL IN", "TL OUT", "Frames"])
        table.setRowCount(len(self.context["range_sources"]))
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        table.setShowGrid(False)
        table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        table.setStyleSheet(
            """
            QTableWidget {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                gridline-color: #333333;
            }
            QHeaderView::section {
                background-color: #2B2B2B;
                color: #999999;
                padding: 4px 8px;
                border: 0px;
                border-bottom: 1px solid #444444;
                font-weight: bold;
            }
            QTableWidget::item { padding-left: 10px; padding-right: 10px; }
            """
        )

        for row, plate in enumerate(self.context["range_sources"]):
            check = QtWidgets.QCheckBox()
            check.setStyleSheet("color: #a7a7a7; padding: 2px;")
            check.setChecked(row == 0)
            check.stateChanged.connect(lambda state, changed_check=check: self._on_range_check_changed(changed_check))
            self.plate_checks.append((check, plate))
            check_container = QtWidgets.QWidget()
            check_layout = QtWidgets.QHBoxLayout(check_container)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(QtCore.Qt.AlignCenter)
            check_layout.addWidget(check)
            table.setCellWidget(row, 0, check_container)
            values = (
                plate["track_name"],
                str(plate["timeline_in"]),
                str(plate["timeline_out"]),
                str(plate["frame_count"]),
            )
            for col, value in enumerate(values, start=1):
                item = QtWidgets.QTableWidgetItem(value)
                table.setItem(row, col, item)

        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(4):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)

        row_count = len(self.context["range_sources"])
        row_height = table.verticalHeader().defaultSectionSize()
        table.setMinimumHeight(header.height() + (row_count * row_height) + 2) # extra 2px de altura para que no aparezca el scrollbar (NO CAMBIAR!!)
        table.setMaximumHeight(header.height() + (row_count * row_height) + 2) # extra 2px de altura para que no aparezca el scrollbar (NO CAMBIAR!!)    
        return table

    def _build_resolution_box(self):
        box = QtWidgets.QVBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)

        tw, th = self.context["timeline_resolution"]
        timeline_text = "Timeline    %s x %s" % (tw or "N/A", th or "N/A")
        timeline_btn = QtWidgets.QRadioButton(timeline_text)
        timeline_btn.setStyleSheet("color: #a7a7a7; padding: 2px;")
        timeline_btn.setChecked(True)
        timeline_btn.toggled.connect(self._update_state)
        group.addButton(timeline_btn)
        self.resolution_buttons[timeline_btn] = {
            "source": "Timeline",
            "width": tw,
            "height": th,
        }
        box.addWidget(timeline_btn)

        for plate in self.context["plates"]:
            width, height = plate["width"], plate["height"]
            text = "%s    %s x %s" % (
                plate["track_name"],
                width or "N/A",
                height or "N/A",
            )
            btn = QtWidgets.QRadioButton(text)
            btn.setStyleSheet("color: #a7a7a7; padding: 2px;")
            btn.setEnabled(bool(width and height))
            btn.toggled.connect(self._update_state)
            group.addButton(btn)
            self.resolution_buttons[btn] = {
                "source": plate["track_name"],
                "width": width,
                "height": height,
            }
            box.addWidget(btn)

        container = QtWidgets.QWidget()
        container.setLayout(box)
        return container

    def _build_handle_box(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)

        self.handle_value = self.saved_handle_value
        handle_style = """
            QPushButton {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 2px 0px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
                color: #cfcfcf;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #232323;
                border: 1px solid #303030;
                color: #555555;
            }
        """

        self.handle_down_btn = QtWidgets.QPushButton("▼")
        self.handle_down_btn.setFixedSize(22, 24)
        self.handle_down_btn.setStyleSheet(
            handle_style
            + """
            QPushButton {
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-right: 0px;
            }
            """
        )
        self.handle_down_btn.clicked.connect(lambda: self._step_handle(-1))

        self.handle_value_label = QtWidgets.QLineEdit(str(self.handle_value))
        self.handle_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.handle_value_label.setReadOnly(True)
        self.handle_value_label.setFixedSize(30, 24)
        self.handle_value_label.setStyleSheet(
            """
            QLineEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 2px 0px;
                selection-background-color: #cfcfcf;
                selection-color: #2B2B2B;
            }
            QLineEdit:disabled {
                background-color: #232323;
                border: 1px solid #303030;
                color: #555555;
            }
            """
        )

        self.handle_up_btn = QtWidgets.QPushButton("▲")
        self.handle_up_btn.setFixedSize(22, 24)
        self.handle_up_btn.setStyleSheet(
            handle_style
            + """
            QPushButton {
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: 0px;
            }
            """
        )
        self.handle_up_btn.clicked.connect(lambda: self._step_handle(1))

        layout.addWidget(self.handle_down_btn)
        layout.addWidget(self.handle_value_label)
        layout.addWidget(self.handle_up_btn)
        layout.addStretch()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def _step_handle(self, delta):
        if not self.handle_up_btn.isEnabled():
            return
        self.handle_value = max(0, min(99, self.handle_value + delta))
        self.saved_handle_value = self.handle_value
        self.handle_value_label.setText(str(self.handle_value))
        save_error = _write_handle_setting(self.saved_handle_value)
        if save_error:
            debug_print(save_error)
        self._update_state()

    def _build_task_box(self):
        layout = QtWidgets.QHBoxLayout()

        for task in TASKS:
            btn = QtWidgets.QPushButton(task)
            btn.setCheckable(True)
            btn.setMinimumWidth(90)
            task_color = TASK_COLORS.get(task.lower(), "#3B9ACA")
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #2B2B2B;
                    border: 1px solid #444444;
                    color: %(color)s;
                    padding: 6px 14px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover:!checked:!disabled {
                    background-color: #333333;
                }
                QPushButton:checked {
                    background-color: #3a3a3a;
                    color: %(color)s;
                    border: 1px solid %(color)s;
                }
                QPushButton:disabled {
                    background-color: #232323;
                    color: #555555;
                    border: 1px solid #333333;
                }
                """
                % {"color": task_color}
            )
            btn.toggled.connect(self._update_state)
            self.task_buttons[task] = btn
            layout.addWidget(btn)
        layout.addStretch()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def _select_default_task(self):
        return

    def _on_range_check_changed(self, changed_check):
        if self._syncing_range_checks:
            return

        changed_source = None
        for check, source in self.plate_checks:
            if check is changed_check:
                changed_source = source
                break

        if changed_check.isChecked() and changed_source:
            selected_type = changed_source["source_type"]
            self._syncing_range_checks = True
            try:
                for check, source in self.plate_checks:
                    if check is changed_check:
                        continue
                    if (
                        selected_type == RANGE_SOURCE_EDITREF
                        or source["source_type"] != selected_type
                    ):
                        check.setChecked(False)
            finally:
                self._syncing_range_checks = False

        self._update_state()

    def _selected_plates(self):
        return [plate for check, plate in self.plate_checks if check.isChecked()]

    def _selected_range_uses_editref(self):
        return any(
            source["source_type"] == RANGE_SOURCE_EDITREF
            for check, source in self.plate_checks
            if check.isChecked()
        )

    def _selected_task(self):
        for task, btn in self.task_buttons.items():
            if btn.isChecked():
                return task
        return None

    def _selected_tasks(self):
        return [task for task in TASKS if self.task_buttons[task].isChecked()]

    def _selected_resolution_info(self):
        for btn, info in self.resolution_buttons.items():
            if btn.isChecked():
                return info
        return None

    def _build_output(self, task=None):
        plates = self._selected_plates()
        task = task or self._selected_task()
        resolution = self._selected_resolution_info()
        shot_root = self.context["shot_root_path"]
        shot_code = self.context["shot_code"]

        if not plates:
            return None, "Select at least one plate."
        if not task:
            return None, "Select at least one task."
        if not resolution:
            return None, "Select a resolution."
        if not shot_root:
            return None, "Could not derive shot root from _input path."
        if not resolution.get("width") or not resolution.get("height"):
            return None, "Selected resolution is unavailable."

        base_timeline_in = min(p["timeline_in"] for p in plates)
        base_timeline_out = max(p["timeline_out"] for p in plates)
        handle = self.handle_value if self._selected_range_uses_editref() else 0
        timeline_in = base_timeline_in - handle
        timeline_out = base_timeline_out + handle
        frame_count = _frame_count(timeline_in, timeline_out)
        if frame_count <= 0:
            return None, "Invalid frame range."

        source_first = START_FRAME
        source_last = START_FRAME + frame_count - 1
        version_name = "%s_%s_%s" % (shot_code, task, VERSION)
        output_dir = "/".join(
            [
                shot_root.rstrip("/\\"),
                TASK_FOLDER[task],
                "4_publish",
                version_name,
            ]
        )

        return {
            "shot_code": shot_code,
            "task": task,
            "shot_root": shot_root,
            "selected_range_sources": [
                {
                    "track_name": p["track_name"],
                    "source_type": p["source_type"],
                }
                for p in plates
            ],
            "selected_plates": [p["track_name"] for p in plates],
            "base_timeline_in": base_timeline_in,
            "base_timeline_out": base_timeline_out,
            "handle": handle,
            "timeline_in": timeline_in,
            "timeline_out": timeline_out,
            "frame_count": frame_count,
            "source_first_frame": source_first,
            "source_last_frame": source_last,
            "resolution": (resolution["width"], resolution["height"]),
            "resolution_source": resolution["source"],
            "output_dir": output_dir,
            "output_name_pattern": "%s_####.exr" % version_name,
        }, None

    def _build_outputs(self):
        params_list = []
        for task in self._selected_tasks():
            params, warning = self._build_output(task)
            if warning:
                return None, warning
            params_list.append(params)
        if not params_list:
            return None, "Select at least one task."
        return params_list, None

    def _set_warning(self, message):
        if message:
            self.warning_label.setText(message)
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setText("")
            self.warning_label.setVisible(False)

    def _set_handle_enabled(self, enabled):
        self.handle_down_btn.setEnabled(enabled)
        self.handle_up_btn.setEnabled(enabled)
        self.handle_value_label.setEnabled(enabled)
        if enabled and self.handle_value == 0:
            self.handle_value = self.saved_handle_value
            self.handle_value_label.setText(str(self.saved_handle_value))
        if not enabled and self.handle_value != 0:
            self.handle_value = 0
            self.handle_value_label.setText("0")

    def _update_state(self, *args):
        self._set_handle_enabled(self._selected_range_uses_editref())

        params_list, warning = self._build_outputs()
        if warning:
            self._set_warning(warning)
            self.create_btn.setEnabled(False)
            self.preview_in_out_btn.setEnabled(False)
            self.output_text.setHtml(warning.replace("\n", "<br>"))
            return

        self._set_warning("")
        self.create_btn.setEnabled(True)
        self.preview_in_out_btn.setEnabled(True)
        preview_blocks = []
        for params in params_list:
            task = params["task"]
            task_color = TASK_COLORS.get(task.lower(), "#a7a7a7")
            format_dict = dict(params)
            format_dict["task_colored"] = '<span style="color: {color}; font-weight: bold;">{task}</span>'.format(
                color=task_color,
                task=task.capitalize()
            )
            format_dict["path_colored"] = _colorize_path(
                params["output_dir"], params["shot_root"]
            )
            file_level = len(params["output_dir"].replace("\\", "/").split("/"))
            file_color = PATH_LEVEL_COLORS.get(file_level, "#bbbbbb")
            format_dict["name_colored"] = '<span style="color: %s;">%s</span>' % (
                file_color, params["output_name_pattern"]
            )
            v = '<span style="color: %s;">%%s</span>' % VALUE_COLOR
            preview_blocks.append(
                'Task: {task_colored}<br>'
                'Path: {path_colored}<br>'
                'Name: {name_colored}<br>'
                'Timeline: {tl_in} - {tl_out} (handle {handle})<br>'
                'Frames: {fr_first} - {fr_last} ({frame_count} frames)<br>'
                'Resolution: {res_w} x {res_h} ({resolution_source})'.format(
                    tl_in=v % params["timeline_in"],
                    tl_out=v % params["timeline_out"],
                    fr_first=v % params["source_first_frame"],
                    fr_last=v % params["source_last_frame"],
                    res_w=v % params["resolution"][0],
                    res_h=v % params["resolution"][1],
                    **format_dict
                )
            )
        self.output_text.setHtml("<br><br>".join(preview_blocks))

    def _preview_in_out(self):
        params_list, warning = self._build_outputs()
        if warning:
            self._set_warning(warning)
            return

        params = params_list[0]
        seq = self.context["sequence"]
        try:
            seq.setInTime(int(params["timeline_in"]))
            seq.setOutTime(int(params["timeline_out"]))
            zoom_items = [source["clip"] for source in self._selected_plates()]
            zoom_error = _zoom_timeline_to_preview_range(
                seq,
                params["timeline_in"],
                zoom_items,
                self,
            )
        except Exception as exc:
            message = "Failed to set timeline In/Out: %s" % exc
            self._set_warning(message)
            QtWidgets.QMessageBox.warning(self, "Create v000", message)
            debug_print(message)
            return

        if zoom_error:
            debug_print(zoom_error)

        self._set_warning("")
        debug_print(
            "Preview In/Out:",
            params["timeline_in"],
            params["timeline_out"],
        )

    def _create_v000(self):
        params_list, warning = self._build_outputs()
        if warning:
            self._set_warning(warning)
            return

        seq = self.context["sequence"]
        project = _active_project_for_sequence(seq)
        if not project:
            message = "No active project found."
            self._set_warning(message)
            QtWidgets.QMessageBox.warning(self, "Create v000", message)
            return

        created_count = 0
        for params in params_list:
            if self._create_v000_for_params(seq, project, params):
                created_count += 1

        if created_count:
            self.accept()
        else:
            self._update_state()

    def _task_confirm_dialog(self, task, message, confirm_label, cancel_label="Cancelar"):
        """Diálogo de confirmación con badge de task coloreado.

        Devuelve True si el usuario confirma, False si cancela.
        """
        task_color = TASK_COLORS.get(task.lower(), "#a7a7a7")
        parent = self

        dialog = QtWidgets.QDialog(parent)
        dialog.setWindowTitle("Create v000")
        dialog.setModal(True)
        dialog.setMinimumWidth(340)
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
            """
        )

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        # Header: badge de task coloreado
        header_row = QtWidgets.QHBoxLayout()
        badge = QtWidgets.QLabel(task.upper())
        badge.setStyleSheet(
            "color: %s; font-weight: bold; font-size: 13px; padding: 2px 0px;" % task_color
        )
        header_row.addWidget(badge)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Separador
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        sep.setStyleSheet("color: #444444; margin: 0px;")
        layout.addWidget(sep)

        # Mensaje
        msg_label = QtWidgets.QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #CCCCCC; padding: 4px 0px;")
        layout.addWidget(msg_label)

        # Botones
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QtWidgets.QPushButton(cancel_label)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #CCCCCC;
                padding: 6px 14px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #666666; }
            """
        )
        cancel_btn.clicked.connect(dialog.reject)

        confirm_btn = QtWidgets.QPushButton(confirm_label)
        confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #443a91;
                color: #b2b2b2;
                padding: 6px 14px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #774dcb; color: #CCCCCC; }
            """
        )
        confirm_btn.clicked.connect(dialog.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

        return dialog.exec_() == QtWidgets.QDialog.Accepted

    def _task_overlap_dialog(self, task, overlaps):
        """Diálogo de overlap con badge de task, lista de clips solapados y opciones de acción.

        Devuelve uno de: 'exrs_only', 'bin_only', 'replace_timeline', None (cancelar).
        """
        task_color = TASK_COLORS.get(task.lower(), "#a7a7a7")

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Create v000")
        dialog.setModal(True)
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
            """
        )

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        # Badge de task
        badge = QtWidgets.QLabel(task.upper())
        badge.setStyleSheet(
            "color: %s; font-weight: bold; font-size: 13px; padding: 2px 0px;" % task_color
        )
        layout.addWidget(badge)

        # Separador
        def make_sep():
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setFrameShadow(QtWidgets.QFrame.Sunken)
            sep.setStyleSheet("color: #444444; margin: 0px;")
            return sep

        layout.addWidget(make_sep())

        # Mensaje principal
        msg = QtWidgets.QLabel("actualmente en el track %s del timeline,\nhay clips ocupando el espacio donde debería ir esta v000:" % task.capitalize())
        msg.setStyleSheet("color: #CCCCCC; padding: 4px 0px;")
        layout.addWidget(msg)

        # Lista de clips solapados
        summary_lines = []
        for item in overlaps:
            try:
                track_name = item.parentTrack().name()
            except Exception:
                track_name = "<unknown>"
            summary_lines.append(
                "%s  |  %s  |  %s - %s"
                % (item.name(), track_name, item.timelineIn(), item.timelineOut())
            )
        summary_box = QtWidgets.QPlainTextEdit("\n".join(summary_lines))
        summary_box.setReadOnly(True)
        summary_box.setFocusPolicy(QtCore.Qt.NoFocus)
        summary_box.setFont(QtGui.QFont("Monospace", 8))
        summary_box.setMaximumHeight(20 + 18 * len(overlaps))
        summary_box.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 4px 6px;
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(summary_box)

        layout.addWidget(make_sep())

        # Estilos de botones de acción
        action_style = """
            QPushButton {
                background-color: #443a91;
                color: #b2b2b2;
                padding: 7px 14px;
                border-radius: 3px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover { background-color: #774dcb; color: #CCCCCC; }
        """

        result = {"choice": None}

        def make_action(label, value):
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet(action_style)
            def on_click():
                result["choice"] = value
                dialog.accept()
            btn.clicked.connect(on_click)
            return btn

        layout.addWidget(make_action("  Solo crear EXRs", "exrs_only"))
        layout.addWidget(make_action("  Crear + importar al Bin", "bin_only"))
        layout.addWidget(make_action("  Crear + reemplazar en timeline", "replace_timeline"))

        # Cancelar alineado a la derecha
        cancel_row = QtWidgets.QHBoxLayout()
        cancel_row.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancelar")
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #CCCCCC;
                padding: 6px 14px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #666666; }
            """
        )
        cancel_btn.clicked.connect(dialog.reject)
        cancel_row.addWidget(cancel_btn)
        layout.addLayout(cancel_row)

        dialog.exec_()
        return result["choice"]

    def _create_v000_for_params(self, seq, project, params):
        replace_existing = False
        if _output_has_exrs(params):
            confirmed = self._task_confirm_dialog(
                task=params["task"],
                message="Ya existe una seq de EXR para la v000\n¿Querés eliminarla y crear una nueva?",
                confirm_label="Reemplazar",
            )
            if not confirmed:
                return False
            replace_existing = True

        integration_mode = "timeline"
        target_track_name = track_for_task(params["task"])
        target_track = _find_video_track(seq, target_track_name)
        if not target_track:
            message = "Target track not found: %s" % target_track_name
            self._set_warning(message)
            QtWidgets.QMessageBox.warning(self, "Create v000", message)
            return False

        overlaps = _timeline_overlaps(target_track, params["timeline_in"], params["timeline_out"])
        if overlaps:
            choice = self._task_overlap_dialog(params["task"], overlaps)
            if not choice:
                return False
            integration_mode = choice

        success, status, message = _create_black_exr_sequence(params, replace=replace_existing)

        if not success:
            self._set_warning(message)
            QtWidgets.QMessageBox.warning(self, "Create v000", message)
            debug_print("error:", message)
            return False

        import_message = ""
        if integration_mode != "exrs_only":
            try:
                with project.beginUndo("Import Create v000"):
                    clip, bin_item, import_error = _import_v000_to_bin(project, params)
                    if import_error:
                        raise RuntimeError(import_error)
                    color_error = _set_v000_clip_color(bin_item)

                    import_message = "\nImported to bin: %s" % bin_item.parentBin().name()
                    if color_error:
                        debug_print(color_error)
                    else:
                        import_message += "\nClip color: #8a8a8a"
                    if integration_mode == "timeline":
                        track_item, timeline_error = _insert_v000_in_timeline(seq, clip, params)
                        if timeline_error:
                            raise RuntimeError(timeline_error)
                        disable_error = _disable_timeline_item(track_item)
                        if disable_error:
                            debug_print(disable_error)
                        import_message += "\nPlaced in timeline: %s (%s - %s)" % (
                            track_item.parentTrack().name(),
                            track_item.timelineIn(),
                            track_item.timelineOut(),
                        )
                        if not disable_error:
                            import_message += "\nTimeline clip disabled"
                    elif integration_mode == "replace_timeline":
                        current_overlaps = _timeline_overlaps(
                            target_track,
                            params["timeline_in"],
                            params["timeline_out"],
                        )
                        _remove_timeline_items(target_track, current_overlaps)
                        track_item, timeline_error = _insert_v000_in_timeline(seq, clip, params)
                        if timeline_error:
                            raise RuntimeError(timeline_error)
                        disable_error = _disable_timeline_item(track_item)
                        if disable_error:
                            debug_print(disable_error)
                        import_message += "\nReplaced %d timeline clip(s) on %s." % (
                            len(current_overlaps),
                            track_item.parentTrack().name(),
                        )
                        if not disable_error:
                            import_message += "\nTimeline clip disabled"
            except Exception as exc:
                message = "%s\n\nEXRs were created, but Hiero import/placement failed:\n%s" % (message, exc)
                self._set_warning(str(exc))
                QtWidgets.QMessageBox.warning(self, "Create v000", message)
                debug_print("import error:", exc)
                return False

        debug_print("created:", params)
        if import_message:
            debug_print(import_message.strip())
        return True


def open_create_v000_dialog():
    context, error = _collect_context()
    if error:
        QtWidgets.QMessageBox.warning(None, "Create v000", error)
        debug_print(error)
        return None

    dialog = CreateV000Dialog(context)
    result = dialog.exec_()
    return result


def main():
    return open_create_v000_dialog()


if __name__ == "__main__":
    main()
