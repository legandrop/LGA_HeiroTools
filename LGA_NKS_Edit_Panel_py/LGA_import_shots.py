"""
____________________________________________________________________

  LGA_import_shots v1.00 | Lega

  Importa shots al proyecto de Nuke Studio.
  Analiza la carpeta _input del shot, detecta plates/editrefs/seqrefs
  y versiones en publish, y los coloca en el timeline en la posicion
  alfabeticamente correcta.

____________________________________________________________________
"""

import os
import re
import sys
import json
import logging
import platform
import queue
import subprocess
import time
from pathlib import Path
from logging.handlers import QueueHandler, QueueListener

import hiero.core
import hiero.ui

CURRENT_DIR = Path(__file__).resolve().parent
STARTUP_DIR = CURRENT_DIR.parent
SHARED_DIR = STARTUP_DIR / "LGA_NKS_Shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(STARTUP_DIR))

# ── herramientas externas (rutas relativas a SHARED_DIR) ──────────
# Windows: OIIO_Win/oiiotool.exe y FFmpeg_Win/bin/ffprobe.exe
# macOS/Linux: pendiente de implementar rutas para esas plataformas
_OS = platform.system()
if _OS == "Windows":
    _OIIOTOOL = SHARED_DIR / "OIIO_Win" / "oiiotool.exe"
    _FFPROBE   = SHARED_DIR / "FFmpeg_Win" / "bin" / "ffprobe.exe"
    _SUBPROCESS_EXTRA = {"creationflags": subprocess.CREATE_NO_WINDOW}
else:
    _OIIOTOOL = None
    _FFPROBE   = None
    _SUBPROCESS_EXTRA = {}

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore
from LGA_NKS_Flow_NamingUtils import clean_base_name, extract_shot_code

# ── logging ────────────────────────────────────────────────────────
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
script_start_time = None
debug_log_listener = None


class RelativeTimeFormatter(logging.Formatter):
    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        record.relative_time = "%.3fs" % (record.created - script_start_time)
        return super().format(record)


def setup_debug_logging(script_name="ImportShots"):
    global debug_log_listener
    log_path = STARTUP_DIR / "logs" / ("debugPy_%s.log" % script_name)
    log_path.parent.mkdir(exist_ok=True)
    try:
        log_path.write_text("Fecha: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    except Exception:
        pass
    logger = logging.getLogger("%s_logger" % script_name.lower())
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        logger.handlers.clear()
    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(RelativeTimeFormatter("[%(relative_time)s] %(message)s"))
    lq = queue.Queue()
    qh = QueueHandler(lq)
    qh.setLevel(logging.DEBUG)
    logger.addHandler(qh)
    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass
    debug_log_listener = QueueListener(lq, fh, respect_handler_level=True)
    debug_log_listener.daemon = True
    debug_log_listener.start()
    return logger


debug_logger = setup_debug_logging(script_name="ImportShots")


def debug_print(*message, level="info"):
    global script_start_time
    if not (DEBUG and DEBUG_LOG):
        return
    msg = " ".join(str(a) for a in message)
    if script_start_time is None:
        script_start_time = time.time()
    getattr(debug_logger, level)(msg)
    if DEBUG and DEBUG_CONSOLE:
        print("[%.3fs] %s" % (time.time() - script_start_time, msg))


def cleanup_logging():
    global debug_log_listener
    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass


import atexit
atexit.register(cleanup_logging)


# ── colores (igual que CreateV000) ────────────────────────────────
PATH_SHOT_COLOR = "#c56cf0"
PATH_SEP_COLOR  = "#bbbbbb"
PATH_LEVEL_COLORS = {
    0: "#ffff66", 1: "#28b5b5", 2: "#ff9a8a", 3: "#0088ff",
    4: "#ffd369", 5: "#28b5b5", 6: "#ff9a8a", 7: "#6bc9ff",
    8: "#ffd369", 9: "#28b5b5", 10: "#ff9a8a", 11: "#6bc9ff",
}

# ── constantes de track ────────────────────────────────────────────
BURNIN_TRACK_NAMES = {"burnin", "burn in", "burn_in"}

PLATE_KEYWORDS = [
    ("seqref",       None),           # None = solo bin
    ("editrefclean", "EditRefClean"),
    ("editref",      "EditRef"),
    ("fgplate",      "fgPlate"),
    ("bgplate",      "bgPlate"),
    ("aplate",       "aPlate"),
    ("bplate",       "bPlate"),
    ("cplate",       "cPlate"),
    ("dplate",       "dPlate"),
    ("eplate",       "ePlate"),
]

TASK_FOLDERS = {
    "comp":    ("Comp",    "_comp_"),
    "roto":    ("Roto",    "_roto_"),
    "cleanup": ("Cleanup", "_cleanup_"),
    "dmp":     ("DMP",     "_dmp_"),
}

EXR_EXTENSIONS  = {".exr"}
MOV_EXTENSIONS  = {".mov", ".mxf", ".mp4"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dpx"}


# ══════════════════════════════════════════════════════════════════
#  Helpers de carpeta / media
# ══════════════════════════════════════════════════════════════════

def _detect_track_from_name(name):
    """Devuelve nombre de track o None (solo bin) segun keywords."""
    lower = name.lower()
    for kw, track in PLATE_KEYWORDS:
        if kw in lower:
            return track   # puede ser None (seqref)
    return None


def _version_number(name):
    """Extrae numero de version de un nombre (v01, v001, v002). Retorna -1 si no hay."""
    m = re.search(r"[_\-]v(\d+)", name, re.IGNORECASE)
    return int(m.group(1)) if m else -1


def _scan_exr_sequence(folder_path):
    """Escanea una carpeta y retorna (first_frame, last_frame, count, first_file_path)."""
    try:
        files = sorted(
            f for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in EXR_EXTENSIONS
        )
    except Exception:
        return None, None, 0, None
    if not files:
        return None, None, 0, None

    def _frame_num(fname):
        m = re.search(r"(\d+)\.exr$", fname, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    frames = [_frame_num(f) for f in files]
    frames = [f for f in frames if f > 0]
    if not frames:
        return None, None, len(files), os.path.join(folder_path, files[0])
    return min(frames), max(frames), len(files), os.path.join(folder_path, files[0])


def _read_exr_metadata(exr_path):
    """Resolucion y compresion de un frame EXR via oiiotool --info -v."""
    w, h, fps, comp = None, None, None, None
    if not (_OIIOTOOL and _OIIOTOOL.exists()):
        debug_print("_read_exr_metadata: oiiotool no disponible", level="warning")
        return w, h, fps, comp
    try:
        r = subprocess.run(
            [str(_OIIOTOOL), "--info", "-v", str(exr_path)],
            capture_output=True, text=True, timeout=10,
            **_SUBPROCESS_EXTRA,
        )
        out = r.stdout + r.stderr
        debug_print("oiiotool output para %s:\n%s" % (Path(exr_path).name, out[:600]))
        # "path/to/file.exr:  1920 x 1080, 3 channel, half openexr"
        m = re.search(r"(\d+)\s*x\s*(\d+)", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
        # 'framesPerSecond: 24/1'  o  'framesPerSecond: 24'
        m = re.search(r'[Ff]rames[Pp]er[Ss]econd[:\s]+"?(\d+)/(\d+)"?', out)
        if m:
            num, den = int(m.group(1)), int(m.group(2))
            if den:
                fps = float(num) / float(den)
        if fps is None:
            m = re.search(r'[Ff]rames[Pp]er[Ss]econd[:\s]+"?([\d.]+)"?', out)
            if m:
                try:
                    fps = float(m.group(1))
                except Exception:
                    pass
        # '    compression: "zip"'  o  '    compression: dwaa'
        m = re.search(r'compression[:\s]+"?([A-Za-z0-9_]+)"?', out, re.IGNORECASE)
        if m:
            comp = m.group(1)
        debug_print("EXR meta: %sx%s fps=%s comp=%s" % (w, h, fps, comp))
    except Exception as e:
        debug_print("_read_exr_metadata error: %s" % e, level="error")
    return w, h, fps, comp


def _read_mov_metadata(mov_path):
    """Resolucion, fps, codec y nb_frames de un MOV/MXF via ffprobe (JSON)."""
    w, h, fps, codec, nb_frames = None, None, None, None, None
    if not (_FFPROBE and _FFPROBE.exists()):
        debug_print("_read_mov_metadata: ffprobe no disponible", level="warning")
        return w, h, fps, codec, nb_frames
    try:
        r = subprocess.run(
            [str(_FFPROBE), "-v", "quiet", "-print_format", "json",
             "-show_streams", str(mov_path)],
            capture_output=True, text=True, timeout=15,
            **_SUBPROCESS_EXTRA,
        )
        data = json.loads(r.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                w     = stream.get("width")
                h     = stream.get("height")
                codec = stream.get("codec_name")
                rfr   = stream.get("r_frame_rate", "")
                if "/" in rfr:
                    num, den = rfr.split("/")
                    try:
                        fps = float(num) / float(den)
                    except Exception:
                        pass
                # nb_frames: campo directo o calculado desde duracion * fps
                raw_nb = stream.get("nb_frames")
                if raw_nb:
                    try:
                        nb_frames = int(raw_nb)
                    except Exception:
                        pass
                if nb_frames is None and fps and stream.get("duration"):
                    try:
                        nb_frames = int(round(float(stream["duration"]) * fps))
                    except Exception:
                        pass
                break
        debug_print("MOV meta %s: %sx%s fps=%s codec=%s frames=%s" % (
            Path(mov_path).name, w, h, fps, codec, nb_frames))
    except Exception as e:
        debug_print("_read_mov_metadata error: %s" % e, level="error")
    # codec se almacena en el campo "compression" del item
    return w, h, fps, codec, nb_frames


def _scan_input_folder(shot_root):
    """
    Escanea {shot_root}/_input/ y retorna lista de dicts con info de cada item.
    Cada dict: {name, path, kind, track, first_frame, last_frame, frame_count,
                first_file, width, height, fps, compression, is_latest, version_num}
    kind: 'exr_seq' | 'mov' | 'other'
    """
    input_dir = Path(shot_root) / "_input"
    if not input_dir.exists():
        return []

    items = []

    # 1. Subcarpetas → secuencias EXR
    try:
        subdirs = sorted(d for d in input_dir.iterdir() if d.is_dir())
    except Exception:
        subdirs = []

    # Agrupar por nombre base (sin version) para detectar la mas alta
    plate_groups = {}  # base_key → [subdir, ...]
    for sd in subdirs:
        first_f, last_f, count, first_file = _scan_exr_sequence(str(sd))
        if count == 0:
            continue
        track = _detect_track_from_name(sd.name)
        # Agrupar: quitamos la parte _vNN al final para la clave de grupo
        base_key = re.sub(r"[_\-]v\d+$", "", sd.name, flags=re.IGNORECASE).lower()
        plate_groups.setdefault(base_key, []).append({
            "name": sd.name,
            "path": str(sd),
            "kind": "exr_seq",
            "track": track,
            "first_frame": first_f,
            "last_frame": last_f,
            "frame_count": count,
            "first_file": first_file,
            "version_num": _version_number(sd.name),
        })

    for base_key, group in plate_groups.items():
        group.sort(key=lambda x: x["version_num"])
        max_ver = max(x["version_num"] for x in group)
        has_multiple_versions = len(group) > 1
        for entry in group:
            entry["is_latest"] = (entry["version_num"] == max_ver)
            entry["has_multiple_versions"] = has_multiple_versions
            # Leer metadata solo del primer archivo
            w, h, fps, comp = (None, None, None, None)
            if entry["first_file"]:
                w, h, fps, comp = _read_exr_metadata(entry["first_file"])
            entry.update({"width": w, "height": h, "fps": fps, "compression": comp})
            items.append(entry)

    # 2. Archivos sueltos en _input/
    try:
        loose = sorted(f for f in input_dir.iterdir() if f.is_file())
    except Exception:
        loose = []

    for f in loose:
        ext = f.suffix.lower()
        if ext in MOV_EXTENSIONS:
            # MOVs sueltos: solo detectamos seqref y editref.
            # Nunca heredan track de plates aunque compartan nombre base con un EXR.
            stem_lower = f.stem.lower()
            if "seqref" in stem_lower:
                track = None          # bin only
            elif "editrefclean" in stem_lower:
                track = "EditRefClean"
            elif "editref" in stem_lower:
                track = "EditRef"
            else:
                track = "?"           # desconocido, usuario decide
            mw, mh, mfps, mcodec, mnb = _read_mov_metadata(str(f))
            items.append({
                "name": f.stem,
                "path": str(f),
                "kind": "mov",
                "ext": f.suffix.lstrip(".").upper(),  # "MOV", "MXF", "MP4"
                "track": track,
                "first_frame": 1 if mnb else None,
                "last_frame": mnb,
                "frame_count": mnb,
                "first_file": str(f),
                "width": mw, "height": mh, "fps": mfps, "compression": mcodec,
                "is_latest": True,
                "version_num": _version_number(f.stem),
            })
        elif ext in IMAGE_EXTENSIONS:
            items.append({
                "name": f.name,
                "path": str(f),
                "kind": "other",
                "track": None,
                "first_frame": None, "last_frame": None, "frame_count": None,
                "first_file": str(f),
                "width": None, "height": None, "fps": None, "compression": None,
                "is_latest": True,
                "version_num": -1,
            })

    # Ordenar: plates por track-name luego version, movs, otros
    def _sort_key(x):
        order = {"exr_seq": 0, "mov": 1, "other": 2}
        return (order.get(x["kind"], 9), x.get("track") or "zzz", x["version_num"])

    items.sort(key=_sort_key)
    return items


def _scan_publish_folders(shot_root):
    """
    Escanea las carpetas de task en shot_root y retorna lista de dicts.
    {task, folder_name, track, publish_dir, version_dir, version_num,
     first_file, first_frame, last_frame, frame_count,
     width, height, fps, compression, has_versions, publish_exists}
    """
    results = []
    shot_path = Path(shot_root)
    for task, (folder_name, track) in TASK_FOLDERS.items():
        task_dir = shot_path / folder_name
        if not task_dir.exists():
            continue
        publish_dir = task_dir / "4_publish"
        publish_exists = publish_dir.exists()

        if not publish_exists:
            results.append({
                "task": task, "folder_name": folder_name, "track": track,
                "publish_exists": False, "has_versions": False,
                "version_dir": None, "version_num": -1,
                "first_file": None, "first_frame": None, "last_frame": None,
                "frame_count": 0, "width": None, "height": None,
                "fps": None, "compression": None,
            })
            continue

        # Buscar subcarpetas de version
        try:
            version_dirs = [
                d for d in publish_dir.iterdir()
                if d.is_dir() and re.search(r"_v\d+$", d.name, re.IGNORECASE)
            ]
        except Exception:
            version_dirs = []

        if not version_dirs:
            results.append({
                "task": task, "folder_name": folder_name, "track": track,
                "publish_exists": True, "has_versions": False,
                "version_dir": None, "version_num": -1,
                "first_file": None, "first_frame": None, "last_frame": None,
                "frame_count": 0, "width": None, "height": None,
                "fps": None, "compression": None,
            })
            continue

        # Tomar la de version mas alta
        version_dirs.sort(key=lambda d: _version_number(d.name))
        best = version_dirs[-1]
        first_f, last_f, count, first_file = _scan_exr_sequence(str(best))
        w, h, fps, comp = (None, None, None, None)
        if first_file:
            w, h, fps, comp = _read_exr_metadata(first_file)

        results.append({
            "task": task, "folder_name": folder_name, "track": track,
            "publish_exists": True, "has_versions": True,
            "version_dir": str(best), "version_name": best.name,
            "version_num": _version_number(best.name),
            "first_file": first_file,
            "first_frame": first_f, "last_frame": last_f, "frame_count": count,
            "width": w, "height": h, "fps": fps, "compression": comp,
        })

    return results


# ══════════════════════════════════════════════════════════════════
#  Helpers de timeline
# ══════════════════════════════════════════════════════════════════

def _is_burnin_track(track_name):
    return track_name.lower().strip() in BURNIN_TRACK_NAMES


def _get_shot_name_from_folder(folder_path):
    return Path(folder_path).name


def _collect_timeline_shots(seq):
    """
    Escanea tracks aPlate y EditRef para construir lista de shots existentes.
    Retorna list de {shot_name, timeline_in, timeline_out, track_name}.
    """
    shots = []
    seen_names = set()
    for track in seq.videoTracks():
        tname = track.name()
        if not (re.search(r"plate$", tname, re.IGNORECASE) or
                re.search(r"editref", tname, re.IGNORECASE)):
            continue
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            try:
                name = item.name()
                tl_in = int(item.timelineIn())
                tl_out = int(item.timelineOut())
            except Exception:
                continue
            if name not in seen_names:
                seen_names.add(name)
                shots.append({
                    "shot_name": name,
                    "timeline_in": tl_in,
                    "timeline_out": tl_out,
                    "track_name": tname,
                })
    shots.sort(key=lambda x: x["timeline_in"])
    return shots


def _shot_exists_in_timeline(seq, shot_name, shot_root):
    """
    Doble criterio: nombre del TrackItem Y path de la media contiene el shot root.
    """
    shot_name_lower = shot_name.lower()
    shot_root_norm = shot_root.replace("\\", "/").rstrip("/").lower()

    for track in seq.videoTracks():
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            try:
                if item.name().lower() == shot_name_lower:
                    return True
                # Chequear path de media
                try:
                    fi = item.source().mediaSource().fileinfos()
                    if fi:
                        media_path = fi[0].filename().replace("\\", "/").lower()
                        if shot_root_norm in media_path:
                            return True
                except Exception:
                    pass
            except Exception:
                continue
    return False


def _find_insert_frame(seq, shot_name, duration):
    """
    Determina el frame donde insertar el shot nuevo basandose en orden alfabetico.
    Retorna (insert_frame, frames_to_push).
    """
    shots = _collect_timeline_shots(seq)
    if not shots:
        return 0, 0

    # Ordenar los shots existentes alfabeticamente por nombre
    shots_alpha = sorted(shots, key=lambda x: x["shot_name"].lower())

    # Encontrar donde encaja el nuevo shot
    insert_before = None
    for s in shots_alpha:
        if shot_name.lower() < s["shot_name"].lower():
            insert_before = s
            break

    if insert_before is None:
        # El nuevo shot va al final
        last = max(shots, key=lambda x: x["timeline_out"])
        insert_frame = last["timeline_out"] + 1
        return insert_frame, 0

    # Insertar antes de insert_before: usamos su timeline_in actual
    insert_frame = insert_before["timeline_in"]
    return insert_frame, duration


def _push_clips_right(seq, from_frame, amount):
    """
    Mueve todos los clips >= from_frame hacia la derecha por 'amount' frames.
    Excluye tracks BurnIn.
    """
    if amount <= 0:
        return
    for track in seq.videoTracks():
        if _is_burnin_track(track.name()):
            continue
        items_to_move = []
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            try:
                if int(item.timelineIn()) >= from_frame:
                    items_to_move.append(item)
            except Exception:
                continue
        # Mover de derecha a izquierda para evitar colisiones
        items_to_move.sort(key=lambda x: x.timelineIn(), reverse=True)
        for item in items_to_move:
            try:
                tl_in = int(item.timelineIn())
                tl_out = int(item.timelineOut())
                src_in = int(item.sourceIn())
                src_out = int(item.sourceOut())
                item.setTimes(tl_in + amount, tl_out + amount, src_in, src_out)
            except Exception as e:
                debug_print("Error moving clip %s: %s" % (item.name(), e), level="warning")


def _stretch_burnin(seq, new_end_frame):
    """Estira el clip BurnIn para cubrir hasta new_end_frame."""
    for track in seq.videoTracks():
        if not _is_burnin_track(track.name()):
            continue
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            try:
                tl_in = int(item.timelineIn())
                src_in = int(item.sourceIn())
                new_out = max(int(item.timelineOut()), new_end_frame)
                new_src_out = src_in + (new_out - tl_in)
                item.setTimes(tl_in, new_out, src_in, new_src_out)
                debug_print("BurnIn stretched to frame %d" % new_out)
            except Exception as e:
                debug_print("Could not stretch BurnIn: %s" % e, level="warning")
        break


def _find_or_create_bin(project, bin_path):
    """Navega/crea la ruta de bin. bin_path ej: 'F 101/MOR_1012C_010'"""
    current = project.clipsBin()
    for part in [p for p in bin_path.split("/") if p]:
        found = None
        for child in current.items():
            if isinstance(child, hiero.core.Bin) and child.name() == part:
                found = child
                break
        if not found:
            found = hiero.core.Bin(part)
            current.addItem(found)
        current = found
    return current


def _bin_path_for_shot(shot_root, shot_name):
    """Construye 'F <grupo>/<shot_name>' desde el shot_root."""
    parts = Path(shot_root).parts
    # Estructura: disco / proyecto / grupo / shot
    # Ej: T: / VFX-MOR / 101 / MOR_1012C_010
    if len(parts) >= 3:
        grupo = parts[-2]
    else:
        grupo = "Shots"
    return "F %s/%s" % (grupo, shot_name)


def _import_clip_to_bin(target_bin, first_file_path, clip_name):
    """Importa una secuencia al bin. Retorna (clip, bin_item, error)."""
    try:
        clip = hiero.core.Clip(first_file_path)
        clip.setName(clip_name)
        bin_item = hiero.core.BinItem(clip)
        target_bin.addItem(bin_item)
        debug_print("Imported to bin: %s" % clip_name)
        return clip, bin_item, None
    except Exception as e:
        return None, None, str(e)


def _find_video_track(seq, track_name):
    for track in seq.videoTracks():
        if track.name() == track_name:
            return track
    return None


def _place_clip_in_timeline(seq, clip, track_name, tl_in, frame_count, shot_name):
    """Coloca el clip en el track indicado. Retorna (track_item, error)."""
    target_track = _find_video_track(seq, track_name)
    if not target_track:
        return None, "Track no encontrado: %s" % track_name

    tl_out = tl_in + frame_count - 1
    try:
        track_item = target_track.addTrackItem(clip, tl_in)
        track_item.setName(shot_name)
        track_item.setTimes(tl_in, tl_out, 0, frame_count - 1)
        track_item.setVersionLinkedToBin(True)
        return track_item, None
    except Exception as e:
        return None, str(e)


# ══════════════════════════════════════════════════════════════════
#  Helpers UI
# ══════════════════════════════════════════════════════════════════

_DIALOG_STYLE = """
QDialog {
    background-color: #2B2B2B;
    border: 1px solid #555555;
}
QLabel {
    color: #a7a7a7;
}
"""

_TABLE_STYLE = """
QTableWidget {
    background-color: #272727;
    border: 1px solid #333333;
    color: #a7a7a7;
    gridline-color: #333333;
    outline: none;
}
QHeaderView::section {
    background-color: #2B2B2B;
    color: #999999;
    padding: 4px 8px;
    border: 0px;
    border-bottom: 1px solid #444444;
    font-weight: bold;
}
QTableWidget::item { padding-left: 6px; padding-right: 6px; }
QTableWidget::item:selected { background-color: #353535; color: #cccccc; }
"""

_BTN_CANCEL = """
QPushButton {
    background-color: #555555;
    border: 1px solid #666666;
    color: #CCCCCC;
    padding: 7px 18px;
    border-radius: 3px;
}
QPushButton:hover { background-color: #666666; }
"""

_BTN_PRIMARY = """
QPushButton {
    background-color: #2a4d3a;
    border: 1px solid #3a7a55;
    color: #CCCCCC;
    padding: 7px 18px;
    border-radius: 3px;
    font-weight: bold;
}
QPushButton:hover { background-color: #3a6b50; }
QPushButton:disabled { background-color: #1e3328; color: #666666; border-color: #2a4d3a; }
"""

_BTN_SECONDARY = """
QPushButton {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    color: #CCCCCC;
    padding: 7px 18px;
    border-radius: 3px;
}
QPushButton:hover { background-color: #4a4a4a; }
QPushButton:disabled { background-color: #2a2a2a; color: #666666; border-color: #3a3a3a; }
"""


def _section_label(text):
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 4px;")
    return lbl


def _separator(orientation="h"):
    sep = QtWidgets.QFrame()
    sep.setFrameShape(
        QtWidgets.QFrame.HLine if orientation == "h" else QtWidgets.QFrame.VLine
    )
    sep.setFrameShadow(QtWidgets.QFrame.Sunken)
    sep.setStyleSheet("color: #444444; margin: 0px;")
    return sep



# ══════════════════════════════════════════════════════════════════
#  Dialogo principal
# ══════════════════════════════════════════════════════════════════

class ImportShotDialog(QtWidgets.QDialog):

    PAGE_MEDIA   = "media"
    PAGE_RENAME  = "rename"
    PAGE_CONVERT = "convert"

    def __init__(self, shot_root, shot_name, seq, insert_frame, frames_to_push,
                 input_items, publish_items, parent=None):
        super(ImportShotDialog, self).__init__(parent)
        self.shot_root      = shot_root
        self.shot_name      = shot_name
        self.seq            = seq
        self.insert_frame   = insert_frame
        self.frames_to_push = frames_to_push
        self.input_items    = input_items
        self.publish_items  = publish_items

        self._track_overrides = {}
        self._create_v000_tasks = set()

        self.setWindowTitle("Import Shot — %s" % shot_name)
        self.setObjectName("LGA_ImportShotDialog")
        self.setModal(True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumWidth(820)
        self.setMinimumHeight(500)
        self.setStyleSheet(_DIALOG_STYLE)

        self._root_layout = QtWidgets.QVBoxLayout(self)
        self._root_layout.setSpacing(8)

        self._build_header()
        self._root_layout.addWidget(_separator())

        self._content_area = QtWidgets.QStackedWidget()
        self._root_layout.addWidget(self._content_area, 1)

        self._page_media   = self._build_page_media()
        self._page_rename  = self._build_page_rename()
        self._page_convert = self._build_page_convert()

        self._content_area.addWidget(self._page_media)
        self._content_area.addWidget(self._page_rename)
        self._content_area.addWidget(self._page_convert)

        self._show_page(self.PAGE_MEDIA)

    # ── header ───────────────────────────────────────────────────

    def _build_header(self):
        row = QtWidgets.QHBoxLayout()
        shot_lbl = QtWidgets.QLabel(
            "<span style='color:#6AB5CA;'>%s</span> / "
            "<span style='color:#B56AB5;'>%s</span>"
            % (self._seq_name(), self.shot_name)
        )
        shot_lbl.setTextFormat(QtCore.Qt.RichText)
        shot_lbl.setStyleSheet(
            "color:#CCCCCC; font-size:14px; font-weight:bold; padding:4px 5px 0 5px;"
        )
        row.addWidget(shot_lbl, 0, QtCore.Qt.AlignLeft)
        row.addStretch()
        title = QtWidgets.QLabel("Import Shot")
        title.setStyleSheet(
            "color:#CCCCCC; font-size:14px; font-weight:bold; padding:4px 5px 0 5px;"
        )
        row.addWidget(title, 0, QtCore.Qt.AlignRight)
        self._root_layout.addLayout(row)

    def _seq_name(self):
        try:
            return self.seq.name()
        except Exception:
            return ""

    # ── navegación entre páginas ─────────────────────────────────

    def _show_page(self, page):
        if page == self.PAGE_MEDIA:
            self._content_area.setCurrentWidget(self._page_media)
        elif page == self.PAGE_RENAME:
            self._content_area.setCurrentWidget(self._page_rename)
        elif page == self.PAGE_CONVERT:
            self._content_area.setCurrentWidget(self._page_convert)

    # ══════════════════════════════════════════════════════════
    #  PAGINA PRINCIPAL: tabla de media
    # ══════════════════════════════════════════════════════════

    def _build_page_media(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(_section_label("MEDIA ENCONTRADA"))

        self._media_table = self._build_media_table()
        layout.addWidget(self._media_table, 1)

        layout.addWidget(_separator())

        # Botones de acción — operan sobre los items con checkbox marcado
        btn_row = QtWidgets.QHBoxLayout()

        self._rename_btn = QtWidgets.QPushButton("Rename")
        self._rename_btn.setStyleSheet(_BTN_SECONDARY)
        self._rename_btn.setToolTip("Renombrar los items seleccionados")
        self._rename_btn.clicked.connect(self._go_to_rename)
        btn_row.addWidget(self._rename_btn)

        btn_row.addSpacing(6)

        self._convert_btn = QtWidgets.QPushButton("EXR Convert")
        self._convert_btn.setStyleSheet(_BTN_SECONDARY)
        self._convert_btn.setToolTip(
            "Convertir EXR sequences seleccionadas (DWAA, resolución, etc.)"
        )
        self._convert_btn.clicked.connect(self._go_to_convert)
        btn_row.addWidget(self._convert_btn)

        btn_row.addStretch()

        self._import_btn = QtWidgets.QPushButton("✓  Import")
        self._import_btn.setStyleSheet(_BTN_PRIMARY)
        self._import_btn.setToolTip("Importar los items seleccionados al timeline")
        self._import_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._import_btn)

        layout.addLayout(btn_row)

        self._update_action_btns()
        return page

    def _build_media_table(self):
        headers = ["", "Nombre", "Tipo", "Res", "FPS", "Compresión", "Frames", "Track"]
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setStyleSheet(_TABLE_STYLE)
        table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        rows = self._build_table_rows()
        self._table_rows = rows  # guardamos para referencias posteriores
        table.setRowCount(len(rows))

        self._checkboxes = {}
        self._track_combos = {}

        for i, row_data in enumerate(rows):
            self._populate_media_row(table, i, row_data)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        table.setColumnWidth(0, 28)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        for col in range(2, len(headers) - 1):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(len(headers) - 1, QtWidgets.QHeaderView.ResizeToContents)

        # Click en cualquier celda (excepto col 0) togglea el checkbox de esa fila
        table.cellClicked.connect(self._on_media_row_clicked)

        return table

    def _on_media_row_clicked(self, row, col):
        if col == 0:
            return  # el checkbox maneja su propio click
        if row in self._checkboxes:
            chk = self._checkboxes[row]
            chk.setChecked(not chk.isChecked())

    def _build_table_rows(self):
        """Construye la lista de filas para la tabla de media."""
        rows = []
        # Input items
        for item in self.input_items:
            rows.append({"source": "input", "item": item})
        # Publish items (solo los que tienen versiones)
        for pub in self.publish_items:
            if pub["has_versions"]:
                rows.append({"source": "publish", "item": pub})
        return rows

    def _populate_media_row(self, table, row, row_data):
        source = row_data["source"]
        item   = row_data["item"]

        is_input_exr = (source == "input" and item["kind"] == "exr_seq")
        is_seqref    = (item.get("track") is None and
                        "seqref" in item.get("name", "").lower())
        is_latest    = item.get("is_latest", True)

        # Col 0: checkbox
        chk = QtWidgets.QCheckBox()
        chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        # Solo EXR de input marcados por defecto (la version mas alta)
        chk.setChecked(is_input_exr and is_latest)
        chk.stateChanged.connect(self._update_action_btns)
        self._checkboxes[row] = chk
        container = QtWidgets.QWidget()
        cl = QtWidgets.QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setAlignment(QtCore.Qt.AlignCenter)
        cl.addWidget(chk)
        table.setCellWidget(row, 0, container)

        # Col 1: nombre (★ solo si hay varias versiones y es la mas alta, ⚠ si seqref)
        name = item.get("name") or item.get("version_name") or ""
        has_multi = item.get("has_multiple_versions", False)
        if is_input_exr and is_latest and has_multi:
            display_name = name + " ★"
        elif is_seqref:
            display_name = name + " ⚠"
        else:
            display_name = name
        name_item = QtWidgets.QTableWidgetItem(display_name)
        name_item.setForeground(
            QtGui.QColor("#d9a441") if is_seqref else
            QtGui.QColor("#CCCCCC") if (is_input_exr and is_latest) else
            QtGui.QColor("#a7a7a7")
        )
        if is_seqref:
            name_item.setToolTip("Se importará al bin. No se coloca en el timeline.")
        table.setItem(row, 1, name_item)

        # Col 2: tipo
        if source == "publish":
            kind_str = "EXR seq"
        elif item.get("kind") == "exr_seq":
            kind_str = "EXR seq"
        elif item.get("kind") == "mov":
            kind_str = item.get("ext") or Path(item.get("path", "")).suffix.lstrip(".").upper() or "MOV"
        else:
            kind_str = "Archivo"
        table.setItem(row, 2, QtWidgets.QTableWidgetItem(kind_str))

        # Col 3: resolución
        w, h = item.get("width"), item.get("height")
        res_str = ("%d×%d" % (w, h)) if (w and h) else "—"
        table.setItem(row, 3, QtWidgets.QTableWidgetItem(res_str))

        # Col 4: fps
        fps = item.get("fps")
        fps_str = ("%.5g" % fps) if fps else "—"
        table.setItem(row, 4, QtWidgets.QTableWidgetItem(fps_str))

        # Col 5: compresión
        comp = item.get("compression") or "—"
        table.setItem(row, 5, QtWidgets.QTableWidgetItem(comp))

        # Col 6: frames
        ff, lf = item.get("first_frame"), item.get("last_frame")
        if ff is not None and lf is not None:
            frames_str = "%d – %d" % (ff, lf)
        else:
            frames_str = "—"
        table.setItem(row, 6, QtWidgets.QTableWidgetItem(frames_str))

        # Col 7: track (combo editable para inputs, label para publish)
        track = item.get("track")
        if source == "input" and item.get("kind") in ("exr_seq", "mov"):
            combo = self._build_track_combo(track, row)
            table.setCellWidget(row, 7, combo)
            self._track_combos[row] = combo
        else:
            track_str = track if track else "—"
            if source == "publish":
                track_str = item.get("track", "—")
            lbl = QtWidgets.QLabel(track_str)
            lbl.setStyleSheet("color:#888888; padding:2px 6px;")
            table.setCellWidget(row, 7, lbl)

        # Colorear fila de publish en gris mas oscuro
        if source == "publish":
            for col in range(1, 7):
                it = table.item(row, col)
                if it:
                    it.setForeground(QtGui.QColor("#777777"))

    def _build_track_combo(self, current_track, row_id):
        track_options = [
            "aPlate", "bPlate", "cPlate", "dPlate", "ePlate",
            "fgPlate", "bgPlate", "EditRef", "EditRefClean",
            "_comp_", "_roto_", "_cleanup_",
        ]
        combo = QtWidgets.QComboBox()
        combo.setStyleSheet("""
            QComboBox {
                background-color: #272727;
                border: 0px;
                color: #a7a7a7;
                padding: 1px 4px;
                selection-background-color: transparent;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 14px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666666;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2B2B2B;
                border: 1px solid #444444;
                color: #a7a7a7;
                selection-background-color: #3a3a3a;
                outline: none;
            }
        """)
        # "?" como primera opcion para tracks desconocidos (MOVs no identificados)
        track_options_display = ["— sin track —", "?"] + track_options
        for opt in track_options_display:
            combo.addItem(opt)
        if current_track == "?":
            combo.setCurrentText("?")
        elif current_track and current_track in track_options:
            combo.setCurrentText(current_track)
        else:
            combo.setCurrentIndex(0)
        combo.currentTextChanged.connect(
            lambda txt, rid=row_id: self._track_overrides.__setitem__(rid, txt)
        )
        return combo

    def _get_track_for_row(self, row):
        if row in self._track_combos:
            txt = self._track_combos[row].currentText()
            if txt in ("— sin track —", "?"):
                return None
            return txt
        return self._table_rows[row]["item"].get("track")

    def _update_action_btns(self):
        any_checked = any(chk.isChecked() for chk in self._checkboxes.values())
        has_exr_checked = any(
            chk.isChecked()
            and self._table_rows[row]["source"] == "input"
            and self._table_rows[row]["item"].get("kind") == "exr_seq"
            for row, chk in self._checkboxes.items()
        )
        self._rename_btn.setEnabled(any_checked)
        self._convert_btn.setEnabled(has_exr_checked)
        self._import_btn.setEnabled(any_checked)

    def _go_to_rename(self):
        self._show_page(self.PAGE_RENAME)

    def _go_to_convert(self):
        self._update_convert_page()
        self._show_page(self.PAGE_CONVERT)

    # ══════════════════════════════════════════════════════════
    #  PAGINA: Rename (stub)
    # ══════════════════════════════════════════════════════════

    def _build_page_rename(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(_section_label("RENOMBRAR"))

        placeholder = QtWidgets.QLabel(
            "Rename en desarrollo. Próximamente: find/replace con preview en tiempo real."
        )
        placeholder.setStyleSheet(
            "color:#666666; font-style:italic; padding:20px 6px;"
        )
        layout.addWidget(placeholder)

        layout.addStretch()
        layout.addWidget(_separator())

        btn_row = QtWidgets.QHBoxLayout()
        cancel_btn = QtWidgets.QPushButton("← Cancelar")
        cancel_btn.setStyleSheet(_BTN_CANCEL)
        cancel_btn.clicked.connect(lambda: self._show_page(self.PAGE_MEDIA))
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        rename_btn = QtWidgets.QPushButton("Rename")
        rename_btn.setStyleSheet(_BTN_SECONDARY)
        rename_btn.setEnabled(False)
        rename_btn.setToolTip("Pendiente de implementación")
        btn_row.addWidget(rename_btn)
        layout.addLayout(btn_row)

        return page

    # ══════════════════════════════════════════════════════════
    #  PAGINA: EXR Convert (stub)
    # ══════════════════════════════════════════════════════════

    def _build_page_convert(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(_section_label("EXR CONVERT"))

        # Advertencias por MOVs seleccionados
        self._convert_warnings_lbl = QtWidgets.QLabel("")
        self._convert_warnings_lbl.setStyleSheet("color:#d9a441; padding:2px 0px;")
        self._convert_warnings_lbl.setWordWrap(True)
        self._convert_warnings_lbl.hide()
        layout.addWidget(self._convert_warnings_lbl)

        # Lista de EXRs a convertir
        self._convert_items_lbl = QtWidgets.QLabel("")
        self._convert_items_lbl.setStyleSheet("color:#888888; padding:2px 0px;")
        self._convert_items_lbl.setWordWrap(True)
        layout.addWidget(self._convert_items_lbl)

        layout.addWidget(_separator())

        # Opciones de conversión
        self._convert_dwaa_chk = QtWidgets.QCheckBox("Convertir a DWAA")
        self._convert_dwaa_chk.setChecked(True)
        self._convert_dwaa_chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        layout.addWidget(self._convert_dwaa_chk)

        res_lbl = QtWidgets.QLabel("Resolución destino:")
        res_lbl.setStyleSheet("color:#a7a7a7; margin-top:6px;")
        layout.addWidget(res_lbl)

        self._res_combo = QtWidgets.QComboBox()
        self._res_combo.setStyleSheet("""
            QComboBox {
                background-color: #272727; border: 1px solid #444;
                color: #a7a7a7; padding: 3px 6px;
            }
            QComboBox::drop-down { border: 0px; width: 14px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666666;
                width: 0px; height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2B2B2B; color: #a7a7a7;
                selection-background-color: #3a3a3a;
            }
        """)
        for preset in ["Original", "2K — 2048×1152", "4K — 4096×2304", "Custom..."]:
            self._res_combo.addItem(preset)
        layout.addWidget(self._res_combo)

        self._move_originals_chk = QtWidgets.QCheckBox("Mover originales a /Originals")
        self._move_originals_chk.setChecked(True)
        self._move_originals_chk.setStyleSheet("color:#a7a7a7; padding:2px; margin-top:8px;")
        layout.addWidget(self._move_originals_chk)

        self._delete_originals_chk = QtWidgets.QCheckBox("Borrar /Originals al terminar")
        self._delete_originals_chk.setChecked(False)
        self._delete_originals_chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        layout.addWidget(self._delete_originals_chk)

        pending_note = QtWidgets.QLabel(
            "⚠  La conversión real se habilitará cuando se integre la herramienta externa."
        )
        pending_note.setStyleSheet("color:#888888; font-style:italic; margin-top:12px;")
        layout.addWidget(pending_note)

        layout.addStretch()

        # Log panel (3 líneas, expandible)
        layout.addWidget(_separator())
        log_row = QtWidgets.QHBoxLayout()
        self._convert_log = QtWidgets.QPlainTextEdit()
        self._convert_log.setReadOnly(True)
        self._convert_log.setMaximumHeight(60)
        self._convert_log.setStyleSheet(
            "background:#1e1e1e; border:1px solid #333; color:#888888; padding:3px;"
        )
        log_row.addWidget(self._convert_log, 1)
        self._log_expand_btn = QtWidgets.QPushButton("▲")
        self._log_expand_btn.setFixedSize(24, 24)
        self._log_expand_btn.setStyleSheet(
            "background:#333; border:1px solid #555; color:#aaa; border-radius:3px;"
        )
        self._log_expand_btn.setToolTip("Expandir log")
        self._log_expand_btn.clicked.connect(self._toggle_convert_log)
        self._log_expanded = False
        log_row.addWidget(self._log_expand_btn, 0, QtCore.Qt.AlignBottom)
        layout.addLayout(log_row)

        # Botones
        btn_row = QtWidgets.QHBoxLayout()
        cancel_btn = QtWidgets.QPushButton("← Cancelar")
        cancel_btn.setStyleSheet(_BTN_CANCEL)
        cancel_btn.clicked.connect(lambda: self._show_page(self.PAGE_MEDIA))
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        convert_btn = QtWidgets.QPushButton("Convertir")
        convert_btn.setStyleSheet(_BTN_SECONDARY)
        convert_btn.setEnabled(False)
        convert_btn.setToolTip("Pendiente de implementación")
        btn_row.addWidget(convert_btn)
        layout.addLayout(btn_row)

        return page

    def _update_convert_page(self):
        exr_names = []
        mov_names = []
        for row, chk in self._checkboxes.items():
            if not chk.isChecked():
                continue
            row_data = self._table_rows[row]
            item = row_data["item"]
            name = item.get("name", "")
            if row_data["source"] == "input" and item.get("kind") == "exr_seq":
                exr_names.append(name)
            elif row_data["source"] == "input" and item.get("kind") == "mov":
                mov_names.append(name)

        if mov_names:
            warnings = "\n".join(
                "⚠  %s no será convertido (solo EXR sequences)" % n for n in mov_names
            )
            self._convert_warnings_lbl.setText(warnings)
            self._convert_warnings_lbl.show()
        else:
            self._convert_warnings_lbl.hide()

        if exr_names:
            self._convert_items_lbl.setText(
                "EXR sequences a convertir:\n" + "\n".join("  •  " + n for n in exr_names)
            )
        else:
            self._convert_items_lbl.setText("No hay EXR sequences seleccionadas.")

    def _toggle_convert_log(self):
        self._log_expanded = not self._log_expanded
        if self._log_expanded:
            self._convert_log.setMaximumHeight(16777215)
            self._log_expand_btn.setText("▼")
            self._log_expand_btn.setToolTip("Colapsar log")
        else:
            self._convert_log.setMaximumHeight(60)
            self._log_expand_btn.setText("▲")
            self._log_expand_btn.setToolTip("Expandir log")

    # ══════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════

    def _show_error(self, msg):
        QtWidgets.QMessageBox.critical(self, "Import Shot — Error", msg)

    def _run_set_shot_name(self):
        try:
            from LGA_NKS_Edit_Panel_py import LGA_NKS_SetShotName  # noqa: F401
        except Exception:
            pass

    def _run_create_v000(self):
        try:
            from LGA_NKS_Edit_Panel_py import LGA_NKS_CreateV000  # noqa: F401
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════

def main():
    debug_print("=== LGA_import_shots start ===")

    seq = hiero.ui.activeSequence()
    if not seq:
        QtWidgets.QMessageBox.warning(
            None, "Import Shot", "No hay sequence activa."
        )
        return

    # Seleccionar carpeta
    shot_root = QtWidgets.QFileDialog.getExistingDirectory(
        None,
        "Seleccionar carpeta del shot",
        "",
        QtWidgets.QFileDialog.ShowDirsOnly,
    )
    if not shot_root:
        debug_print("Cancelled — no folder selected")
        return

    shot_root = shot_root.replace("\\", "/")
    shot_name = _get_shot_name_from_folder(shot_root)
    debug_print("Shot root: %s  shot_name: %s" % (shot_root, shot_name))

    # Verificar si ya existe
    if _shot_exists_in_timeline(seq, shot_name, shot_root):
        QtWidgets.QMessageBox.critical(
            None,
            "Import Shot",
            "El shot '%s' ya existe en el timeline.\n\n"
            "No se puede importar un shot duplicado." % shot_name,
        )
        debug_print("Aborted — shot already exists: %s" % shot_name, level="warning")
        return

    # Analizar carpeta
    debug_print("Scanning _input...")
    input_items = _scan_input_folder(shot_root)
    debug_print("Found %d input items" % len(input_items))

    debug_print("Scanning publish folders...")
    publish_items = _scan_publish_folders(shot_root)
    debug_print("Found %d publish entries" % len(publish_items))

    # Calcular duracion del plate mas largo para posicionamiento
    max_frames = max(
        (it["frame_count"] for it in input_items
         if it["kind"] == "exr_seq" and it.get("is_latest")),
        default=0
    )
    if max_frames == 0:
        max_frames = 100  # fallback si no hay EXR todavia

    insert_frame, frames_to_push = _find_insert_frame(seq, shot_name, max_frames)
    debug_print("Insert frame: %d  push: %d  duration: %d" % (
        insert_frame, frames_to_push, max_frames))

    # Abrir dialogo
    parent = hiero.ui.mainWindow() if hasattr(hiero.ui, "mainWindow") else None
    dlg = ImportShotDialog(
        shot_root, shot_name, seq,
        insert_frame, frames_to_push,
        input_items, publish_items,
        parent=parent,
    )
    dlg.exec_()


if __name__ == "__main__":
    main()
