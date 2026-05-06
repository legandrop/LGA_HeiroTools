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
import importlib
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

# During tool development, force the helper to reload on every panel execution.
_TRANSCODE_HELPER = "LGA_NKS_Edit_Panel_py.LGA_import_shots_transcode"
if _TRANSCODE_HELPER in sys.modules:
    del sys.modules[_TRANSCODE_HELPER]
_transcode_mod = importlib.import_module(_TRANSCODE_HELPER)
TranscodeWorker         = _transcode_mod.TranscodeWorker
check_existing_outputs  = _transcode_mod.check_existing_outputs
delete_existing_outputs = _transcode_mod.delete_existing_outputs
show_overwrite_warning  = _transcode_mod.show_overwrite_warning

_SETTINGS_HELPER = "LGA_NKS_Edit_Panel_py.LGA_import_shots_settings"
if _SETTINGS_HELPER in sys.modules:
    del sys.modules[_SETTINGS_HELPER]
settings_mod = importlib.import_module(_SETTINGS_HELPER)

_RENAME_SETTINGS_HELPER = "LGA_NKS_Edit_Panel_py.LGA_import_shots_rename_settings"
if _RENAME_SETTINGS_HELPER in sys.modules:
    del sys.modules[_RENAME_SETTINGS_HELPER]
rename_settings_mod = importlib.import_module(_RENAME_SETTINGS_HELPER)

_RENAME_HELPER = "LGA_NKS_Edit_Panel_py.LGA_import_shots_rename"
if _RENAME_HELPER in sys.modules:
    del sys.modules[_RENAME_HELPER]
rename_mod = importlib.import_module(_RENAME_HELPER)

# ── flags ──────────────────────────────────────────────────────────
# Si True, el transcode escribe a {seq_path}/test_transcode/ y los
# checkboxes "Mover originales" / "Borrar /Originals" quedan inertes.
Transcode_TEST_Mode = False
# Si True, Rename trabaja sobre copia en carpeta "renamned" y no toca originales.
Rename_Test_mode = True

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

# ── colores de tabla de media (borde izquierdo por tipo de fila) ──
# task colors: igual que TASK_COLORS en CreateV000
_CLR_COMP    = "#3381e0"   # comp publish
_CLR_ROTO    = "#2abf7e"   # roto publish
_CLR_CLEANUP = "#27c8c3"   # cleanup publish
_CLR_DMP     = "#e08033"   # dmp publish
_CLR_PLATES  = "#42616d"   # plates input (EXR seq)
_CLR_REFS    = "#aa9e54"   # references (editref / seqref)

_TASK_ROW_COLORS = {
    "comp":    _CLR_COMP,
    "roto":    _CLR_ROTO,
    "cleanup": _CLR_CLEANUP,
    "dmp":     _CLR_DMP,
}
_TASK_ORDER = {"comp": 0, "roto": 1, "cleanup": 2, "dmp": 3}

# ── colores para anotaciones en tabla / dropdowns ─────────────────
# Derivados de la paleta PATH_LEVEL_COLORS pero desaturados ~40 %
# para no competir con el texto base #a7a7a7.
_CLR_AR            = "#a89060"   # aspect ratio          — dorado suave
_CLR_PAR           = "#c4787a"   # pixel aspect ratio    — rosa muted
_CLR_FRAMES        = "#b09040"   # cantidad de frames    — ámbar cálido
_CLR_COMP_ZIP      = "#a06060"   # compresión zip/piz    — rojo suave
_CLR_COMP_DWAA     = "#6a9960"   # compresión dwaa/dwab  — verde suave
_CLR_STATUS_PENDING  = "#5a9ab5" # estado Pendiente      — cian suave
_CLR_STATUS_DONE     = "#6a9960" # estado Terminado      — verde suave
_CLR_STATUS_ERROR    = "#a06060" # estado Error          — rojo suave
_CLR_STATUS_UPSCALE  = "#a06060" # estado Upscale (bloq) — rojo suave

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


def _is_plate_track(track_name):
    """True si el nombre de track corresponde a un plate."""
    if not track_name:
        return False
    return str(track_name).strip().lower().endswith("plate")


def _version_number(name):
    """Extrae numero de version de un nombre (v01, v001, v002). Retorna -1 si no hay."""
    m = re.search(r"[_\-]v(\d+)", name, re.IGNORECASE)
    return int(m.group(1)) if m else -1


def _folder_size_bytes(folder_path):
    """Suma el tamaño en bytes de los archivos directos de una carpeta (no recursivo)."""
    total = 0
    try:
        for f in os.listdir(folder_path):
            p = os.path.join(folder_path, f)
            if os.path.isfile(p):
                try:
                    total += os.path.getsize(p)
                except Exception:
                    pass
    except Exception:
        return 0
    return total


def _format_bytes(n):
    """Formatea bytes a string legible (KB/MB/GB)."""
    if not n:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return ("%.0f %s" % (n, unit)) if unit in ("B", "KB") else ("%.2f %s" % (n, unit))
        n /= 1024.0
    return "%.2f PB" % n


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
    """Resolucion, compresion, bit depth, channels y PAR de un frame EXR via oiiotool --info -v."""
    w, h, fps, comp, bitdepth, channels, par = None, None, None, None, None, None, None
    if not (_OIIOTOOL and _OIIOTOOL.exists()):
        debug_print("_read_exr_metadata: oiiotool no disponible", level="warning")
        return w, h, fps, comp, bitdepth, channels, par
    try:
        r = subprocess.run(
            [str(_OIIOTOOL), "--info", "-v", str(exr_path)],
            capture_output=True, text=True, timeout=10,
            **_SUBPROCESS_EXTRA,
        )
        out = r.stdout + r.stderr
        debug_print("oiiotool output para %s:\n%s" % (Path(exr_path).name, out[:600]))
        # "path/to/file.exr:  1920 x 1080, 3 channel, half openexr"
        m = re.search(r"(\d+)\s*x\s*(\d+),\s*(\d+)\s*channel,\s*(\w+)", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            channels = int(m.group(3))
            bitdepth = m.group(4)
        else:
            m = re.search(r"(\d+)\s*x\s*(\d+)", out)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
            m = re.search(r"(\d+)\s*channel", out)
            if m:
                channels = int(m.group(1))
            m = re.search(r"channel,\s*(\w+)", out)
            if m:
                bitdepth = m.group(1)
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
        # '    PixelAspectRatio: 1'  o  '    PixelAspectRatio: 2'
        m = re.search(r'[Pp]ixel[Aa]spect[Rr]atio[:\s]+"?([\d.]+)"?', out)
        if m:
            try:
                par = float(m.group(1))
            except Exception:
                pass
        debug_print("EXR meta: %sx%s fps=%s comp=%s bd=%s ch=%s par=%s" % (
            w, h, fps, comp, bitdepth, channels, par))
    except Exception as e:
        debug_print("_read_exr_metadata error: %s" % e, level="error")
    return w, h, fps, comp, bitdepth, channels, par


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
            w, h, fps, comp, bd, ch, par = (None,) * 7
            if entry["first_file"]:
                w, h, fps, comp, bd, ch, par = _read_exr_metadata(entry["first_file"])
            entry.update({"width": w, "height": h, "fps": fps, "compression": comp,
                          "bitdepth": bd, "channels": ch, "pixel_aspect_ratio": par})
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
            elif "plate" in stem_lower:
                # Si el nombre contiene "plate", se distribuye como plate.
                track = _detect_track_from_name(f.stem) or "aPlate"
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
                "bitdepth": None, "channels": None,
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
                "bitdepth": None, "channels": None,
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
    Escanea las carpetas de task en shot_root y retorna una lista de dicts,
    una entrada por cada version encontrada (no solo la mas alta).
    Cada dict incluye is_latest=True solo para la version mas alta de cada task.
    Orden: por task (TASK_FOLDERS insertion order), luego version descendente.
    """
    results = []
    shot_path = Path(shot_root)
    for task, (folder_name, track) in TASK_FOLDERS.items():
        task_dir = shot_path / folder_name
        if not task_dir.exists():
            continue
        publish_dir = task_dir / "4_publish"
        if not publish_dir.exists():
            continue

        # Buscar TODAS las subcarpetas de version
        try:
            version_dirs = [
                d for d in publish_dir.iterdir()
                if d.is_dir() and re.search(r"_v\d+$", d.name, re.IGNORECASE)
            ]
        except Exception:
            version_dirs = []

        if not version_dirs:
            continue

        # Ordenar descendente (mayor version primero)
        version_dirs.sort(key=lambda d: _version_number(d.name), reverse=True)
        max_ver = _version_number(version_dirs[0].name)

        for vd in version_dirs:
            first_f, last_f, count, first_file = _scan_exr_sequence(str(vd))
            w, h, fps, comp, bd, ch, par = (None,) * 7
            if first_file:
                w, h, fps, comp, bd, ch, par = _read_exr_metadata(first_file)
            ver_num = _version_number(vd.name)
            results.append({
                "task": task, "folder_name": folder_name, "track": track,
                "publish_exists": True, "has_versions": True,
                "version_dir": str(vd), "version_name": vd.name,
                "version_num": ver_num,
                "is_latest": (ver_num == max_ver),
                "first_file": first_file,
                "first_frame": first_f, "last_frame": last_f, "frame_count": count,
                "width": w, "height": h, "fps": fps, "compression": comp,
                "bitdepth": bd, "channels": ch, "pixel_aspect_ratio": par,
                "path": str(vd),
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
    background-color: #443a91;
    border: 1px solid #5a4faa;
    color: #CCCCCC;
    padding: 7px 18px;
    border-radius: 3px;
    font-weight: bold;
}
QPushButton:hover { background-color: #774dcb; }
QPushButton:disabled { background-color: #2a2540; color: #666666; border-color: #443a91; }
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

_BTN_SMALL = """
QPushButton {
    background-color: #2e2e2e;
    border: 1px solid #444444;
    color: #999999;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 11px;
}
QPushButton:hover { background-color: #383838; color: #cccccc; }
QPushButton:disabled { background-color: #272727; color: #555555; }
"""

# ✅✅ Espacio (px) entre el separador horizontal y la fila de botones de acción.
# Se aplica en todas las páginas (media y convert) para mantener equilibrio visual.
_BTN_ROW_TOP_SPACING = 15


def _section_label(text):
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 4px;")
    return lbl


def _cell_html_label(html, bg="#272727"):
    """QLabel con HTML coloreado para usar como cellWidget en tablas.
    Transparente a eventos de mouse para que el cellClicked de la tabla
    siga funcionando correctamente."""
    lbl = QtWidgets.QLabel()
    lbl.setTextFormat(QtCore.Qt.RichText)
    lbl.setText(html)
    lbl.setStyleSheet("background:%s; padding:2px 6px;" % bg)
    lbl.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
    return lbl


def _comp_color(comp, greyed=False):
    """Devuelve el color HTML para una compresión EXR dada."""
    cl = (comp or "").lower()
    if cl in ("dwaa", "dwab"):
        return "#4a6e4a" if greyed else _CLR_COMP_DWAA
    if cl in ("zip", "zips", "piz"):
        return "#6e4a4a" if greyed else _CLR_COMP_ZIP
    return "#666666" if greyed else "#888888"


def _separator(orientation="h"):
    sep = QtWidgets.QFrame()
    sep.setFrameShape(
        QtWidgets.QFrame.HLine if orientation == "h" else QtWidgets.QFrame.VLine
    )
    sep.setFrameShadow(QtWidgets.QFrame.Sunken)
    sep.setStyleSheet("color: #444444; margin: 0px;")
    return sep


class GradientTextLabel(QtWidgets.QLabel):
    """QLabel que pinta su texto con un gradiente lineal limitado al ancho del texto."""

    def __init__(self, text, colors, bg_color="#313131", parent=None):
        super().__init__(text, parent)
        self._colors = colors
        self._bg_color = bg_color

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        painter.setFont(self.font())
        # Fondo
        painter.fillRect(self.rect(), QtGui.QColor(self._bg_color))

        # Calcular el bounding rect real del texto
        fm = QtGui.QFontMetrics(self.font())
        text = self.text()
        text_w = fm.horizontalAdvance(text) if hasattr(fm, "horizontalAdvance") else fm.width(text)
        text_h = fm.height()
        margins = self.contentsMargins()
        # Posicion del texto: alineado a la izquierda con padding-left
        x0 = margins.left()
        y0 = (self.height() - text_h) // 2
        text_rect = QtCore.QRect(x0, y0, text_w, text_h)

        # Gradiente horizontal limitado al ancho del texto
        gradient = QtGui.QLinearGradient(x0, 0, x0 + text_w, 0)
        n = len(self._colors)
        for i, c in enumerate(self._colors):
            pos = i / (n - 1) if n > 1 else 0
            gradient.setColorAt(pos, QtGui.QColor(c))
        pen = QtGui.QPen(QtGui.QBrush(gradient), 1)
        painter.setPen(pen)
        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)
        painter.end()


# ══════════════════════════════════════════════════════════════════
#  ComboBox custom — pinta la flecha con QPainter
# ══════════════════════════════════════════════════════════════════

class _ArrowComboBox(QtWidgets.QComboBox):
    """QComboBox que pinta su propia flecha ▼ via paintEvent.
    Requiere que el stylesheet oculte la flecha nativa con
    `QComboBox::down-arrow { image: none; width:0; height:0; }`."""

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        cx = rect.right() - 10
        cy = rect.center().y() + 1
        path = QtGui.QPainterPath()
        path.moveTo(cx - 4, cy - 2)
        path.lineTo(cx + 4, cy - 2)
        path.lineTo(cx, cy + 3)
        path.closeSubpath()
        p.fillPath(path, QtGui.QColor("#999999"))
        p.end()


# ══════════════════════════════════════════════════════════════════
#  SpinBox custom — dibuja las flechas ▲▼ con QPainter (igual patrón que
#  _ArrowComboBox). La stylesheet oculta las flechas nativas; los botones
#  nativos del SO siguen siendo clickeables (solo se reemplaza la imagen).
# ══════════════════════════════════════════════════════════════════

class _ArrowSpinBox(QtWidgets.QSpinBox):
    """QSpinBox que dibuja sus propias flechas ▲▼ via paintEvent.
    Solución análoga a _ArrowComboBox: los botones nativos funcionan,
    solo se pinta encima. Selección de texto: fondo gris claro / texto oscuro."""

    _STYLE = (
        "QSpinBox { background:#272727; border:1px solid #444; color:#a7a7a7;"
        " padding:2px 20px 2px 4px;"
        " selection-background-color:#505060; selection-color:#d0d0d0; }"
        "QSpinBox::up-button, QSpinBox::down-button"
        " { background:transparent; border:none; width:18px; }"
        "QSpinBox::up-arrow, QSpinBox::down-arrow"
        " { image:none; width:0; height:0; }"
    )

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = self.rect()
        cx = r.right() - 9
        # Flecha ▲ (cuarto superior derecho)
        cy_up = r.height() // 4
        path_up = QtGui.QPainterPath()
        path_up.moveTo(cx - 4, cy_up + 2)
        path_up.lineTo(cx + 4, cy_up + 2)
        path_up.lineTo(cx,     cy_up - 2)
        path_up.closeSubpath()
        p.fillPath(path_up, QtGui.QColor("#999999"))
        # Flecha ▼ (cuarto inferior derecho)
        cy_dn = r.height() * 3 // 4
        path_dn = QtGui.QPainterPath()
        path_dn.moveTo(cx - 4, cy_dn - 2)
        path_dn.lineTo(cx + 4, cy_dn - 2)
        path_dn.lineTo(cx,     cy_dn + 2)
        path_dn.closeSubpath()
        p.fillPath(path_dn, QtGui.QColor("#999999"))
        p.end()


# ══════════════════════════════════════════════════════════════════
#  Stylesheet base para _ArrowComboBox
#  Uso: combo.setStyleSheet(_COMBO_ARROW_STYLE) + combo.setView(QListView())
# ══════════════════════════════════════════════════════════════════

_COMBO_BASE = (
    "QComboBox { background-color:#272727; border:1px solid #444; "
    "color:#a7a7a7; padding:3px 6px; }"
    "QComboBox::drop-down { border:0px; width:18px; }"
    "QComboBox::down-arrow { image:none; width:0px; height:0px; }"
    "QComboBox QAbstractItemView { background-color:#2B2B2B; color:#a7a7a7; "
    "selection-background-color:#272727; selection-color:#a7a7a7; outline:0; }"
)


def _ar_str(w, h):
    """Devuelve el aspect ratio como '16:9', '2.39:1', etc."""
    if not w or not h:
        return ""
    try:
        from math import gcd
        g = gcd(int(w), int(h))
        rw, rh = int(w) // g, int(h) // g
        if rw <= 32 and rh <= 32:
            return "%d:%d" % (rw, rh)
        return "%.2f:1" % (w / float(h))
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════
#  Delegate para combo de resolución (AR en dorado)
# ══════════════════════════════════════════════════════════════════

# Ancho del área de click del ícono de papelera en el dropdown de presets
_PRESET_TRASH_W = 26


class _ResPresetListView(QtWidgets.QListView):
    """QListView usado como popup del combo de resoluciones.

    El QComboBoxPrivateContainer instala un eventFilter en el listview mismo, lo que
    intercepta los MouseButtonRelease antes de que lleguen a nuestro override de
    mouseReleaseEvent. Por eso instalamos nuestro filtro en el viewport(), que NO
    está filtrado por el container.
    """

    def __init__(self, on_delete_cb, parent=None):
        super(_ResPresetListView, self).__init__(parent)
        self._on_delete = on_delete_cb
        self._hovered_trash_row = -1
        self.setMouseTracking(True)

    def showEvent(self, event):
        """Instalamos el filtro en el viewport cuando el popup se muestra."""
        super(_ResPresetListView, self).showEvent(event)
        vp = self.viewport()
        if vp:
            vp.setMouseTracking(True)
            vp.installEventFilter(self)

    def hideEvent(self, event):
        """Limpiamos el hover al cerrar el popup."""
        super(_ResPresetListView, self).hideEvent(event)
        self._hovered_trash_row = -1

    @staticmethod
    def _is_deletable(text):
        t = text.strip()
        return (not t.startswith("Original")
                and t != "Custom..."
                and not t.startswith("Timeline"))

    def _in_trash_zone(self, row, pos):
        m = self.model()
        if not m:
            return False
        vrect = self.visualRect(m.index(row, 0))
        return pos.x() >= vrect.right() - _PRESET_TRASH_W

    def _update_hover(self, pos):
        m = self.model()
        if not m:
            return
        idx = self.indexAt(pos)
        row = idx.row() if idx.isValid() else -1
        new_hover = -1
        if row >= 0:
            text = m.data(m.index(row, 0)) or ""
            if self._is_deletable(text) and self._in_trash_zone(row, pos):
                new_hover = row
        if new_hover != self._hovered_trash_row:
            old = self._hovered_trash_row
            self._hovered_trash_row = new_hover
            vp = self.viewport()
            for r in (old, new_hover):
                if r >= 0:
                    vp.update(self.visualRect(m.index(r, 0)))

    def eventFilter(self, obj, event):
        vp = self.viewport()
        if obj is vp:
            etype = event.type()
            if etype == QtCore.QEvent.MouseMove:
                self._update_hover(event.pos())
            elif etype == QtCore.QEvent.Leave:
                old = self._hovered_trash_row
                self._hovered_trash_row = -1
                m = self.model()
                if m and old >= 0:
                    self.viewport().update(self.visualRect(m.index(old, 0)))
            elif etype == QtCore.QEvent.MouseButtonRelease:
                m = self.model()
                if m:
                    idx = self.indexAt(event.pos())
                    row = idx.row() if idx.isValid() else -1
                    if row >= 0:
                        text = m.data(m.index(row, 0)) or ""
                        if self._is_deletable(text) and self._in_trash_zone(row, event.pos()):
                            self._on_delete(row)
                            return True  # consumir → no seleccionar ni cerrar popup
        return super(_ResPresetListView, self).eventFilter(obj, event)


class _ResPresetDelegate(QtWidgets.QStyledItemDelegate):
    """Pinta items del combo de resoluciones con [AR] en dorado y trash icon a la derecha."""

    _CLR_TEXT = "#a7a7a7"
    _CLR_AR   = "#a89060"

    def __init__(self, list_view, pix_trash, pix_hover, parent=None):
        super(_ResPresetDelegate, self).__init__(parent)
        self._view      = list_view
        self._pix_trash = pix_trash
        self._pix_hover = pix_hover

    @staticmethod
    def _is_deletable(text):
        t = text.strip()
        return (not t.startswith("Original")
                and t != "Custom..."
                and not t.startswith("Timeline"))

    def paint(self, painter, option, index):
        painter.save()
        bg = (QtGui.QColor("#353535")
              if (option.state & QtWidgets.QStyle.State_Selected)
              else QtGui.QColor("#2B2B2B"))
        painter.fillRect(option.rect, bg)

        text = index.data() or ""
        deletable = self._is_deletable(text)

        # Área de texto: si deletable reservar espacio para el trash
        text_rect = option.rect.adjusted(6, 0, -(_PRESET_TRASH_W + 4) if deletable else -4, 0)

        segments = re.split(r'(\[[^\]]*\])', text)
        fm = painter.fontMetrics()
        x  = text_rect.x()

        for seg in segments:
            if not seg:
                continue
            is_ar = seg.startswith("[")
            painter.setPen(QtGui.QColor(self._CLR_AR if is_ar else self._CLR_TEXT))
            sw = fm.horizontalAdvance(seg)
            painter.drawText(x, text_rect.top(), sw, text_rect.height(),
                             QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, seg)
            x += sw

        if deletable:
            hovered = (self._view._hovered_trash_row == index.row())
            pix = (self._pix_hover if (hovered and self._pix_hover and not self._pix_hover.isNull())
                   else self._pix_trash)
            if pix and not pix.isNull():
                icon_sz = 14
                tx = option.rect.right() - _PRESET_TRASH_W + (_PRESET_TRASH_W - icon_sz) // 2
                ty = option.rect.top() + (option.rect.height() - icon_sz) // 2
                scaled = pix.scaled(icon_sz, icon_sz,
                                    QtCore.Qt.KeepAspectRatio,
                                    QtCore.Qt.SmoothTransformation)
                painter.drawPixmap(tx, ty, scaled)

        painter.restore()

    def sizeHint(self, option, index):
        sh = super(_ResPresetDelegate, self).sizeHint(option, index)
        return sh.expandedTo(QtCore.QSize(0, 24))


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
        self._rename_happened = False

        # Custom resolution + Preserve AR
        self._custom_ar_updating = False   # evita recursión al actualizar spinboxes
        self._custom_master = "w"          # "w" | "h" — última dimensión editada

        # Resolución del timeline (para el preset "Timeline" hardcoded)
        try:
            fmt = self.seq.format()
            self._tl_w, self._tl_h = int(fmt.width()), int(fmt.height())
        except Exception:
            self._tl_w, self._tl_h = None, None

        # Cargar settings persistentes ANTES de construir la UI.
        # _res_presets_raw = solo los presets del INI (sin Original/Timeline/Custom...).
        # _res_presets     = lista completa con hardcoded head+tail añadidos.
        self._imp_settings    = settings_mod.load_all_settings()
        self._res_presets_raw = settings_mod.load_res_presets()
        self._res_presets     = self._build_full_presets()

        self.setWindowTitle("Import Shot — %s" % shot_name)
        self.setObjectName("LGA_ImportShotDialog")
        self.setModal(True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMinimumWidth(1300)
        self.setMinimumHeight(650)
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
            if getattr(self, "_transcode_happened", False):
                self._transcode_happened = False
                self._refresh_media_page()
            if getattr(self, "_rename_happened", False):
                self._rename_happened = False
                self._refresh_media_page()
            self._content_area.setCurrentWidget(self._page_media)
        elif page == self.PAGE_RENAME:
            self._refresh_rename_preview()
            self._content_area.setCurrentWidget(self._page_rename)
        elif page == self.PAGE_CONVERT:
            self._content_area.setCurrentWidget(self._page_convert)

    def _refresh_media_page(self):
        """Re-escanea el shot y reconstruye la tabla de media."""
        self.input_items   = _scan_input_folder(self.shot_root)
        self.publish_items = _scan_publish_folders(self.shot_root)

        layout = self._page_media.layout()
        # El widget de tabla está en la posición 1 del layout (después del section label)
        old_item = layout.takeAt(1)
        if old_item and old_item.widget():
            old_item.widget().deleteLater()

        self._media_table = self._build_media_table()
        layout.insertWidget(1, self._media_table, 1)
        self._update_action_btns()

    # ══════════════════════════════════════════════════════════
    #  PAGINA PRINCIPAL: tabla de media
    # ══════════════════════════════════════════════════════════

    def _build_page_media(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(6)

        layout.addWidget(_section_label("MEDIA ENCONTRADA"))

        self._media_table = self._build_media_table()
        layout.addWidget(self._media_table, 1)

        # Fila de selección rápida
        sel_row = QtWidgets.QHBoxLayout()
        sel_row.setSpacing(4)
        for label, slot in [
            ("Select All",    self._select_all),
            ("Clear",         self._clear_selection),
            ("Plates",        lambda: self._select_section("plates")),
            ("References",    lambda: self._select_section("refs")),
            ("Publish",       lambda: self._select_section("publish")),
        ]:
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet(_BTN_SMALL)
            btn.clicked.connect(slot)
            sel_row.addWidget(btn)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        layout.addWidget(_separator())
        layout.addSpacing(_BTN_ROW_TOP_SPACING)

        # Botones de acción — operan sobre los items con checkbox marcado
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()

        self._rename_btn = QtWidgets.QPushButton("Rename")
        self._rename_btn.setStyleSheet(_BTN_SECONDARY)
        self._rename_btn.setToolTip("Renombrar los items seleccionados")
        self._rename_btn.clicked.connect(self._go_to_rename)
        btn_row.addWidget(self._rename_btn)

        btn_row.addSpacing(6)

        self._convert_btn = QtWidgets.QPushButton("Transcode Plates")
        self._convert_btn.setStyleSheet(_BTN_SECONDARY)
        self._convert_btn.setToolTip(
            "Transcodear los plates seleccionados (DWAA, resolución, etc.)"
        )
        self._convert_btn.clicked.connect(self._go_to_convert)
        btn_row.addWidget(self._convert_btn)

        btn_row.addSpacing(6)

        self._import_btn = QtWidgets.QPushButton("Import")
        self._import_btn.setStyleSheet(_BTN_PRIMARY)
        self._import_btn.setToolTip("Importar los items seleccionados al timeline")
        self._import_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._import_btn)

        layout.addLayout(btn_row)

        self._update_action_btns()
        return page

    def _build_media_table(self):
        # col 0: barra de color (4 px)  col 1: checkbox (28 px)
        # col 2: Nombre  3: Tipo  4: Resolución  5: FPS  6: Compresión  7: Frames/Duration  8: Track
        headers = ["", "", "Nombre", "Tipo", "Resolución", "FPS", "Compresión", "Frames/Duration", "Track"]
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
        self._table_rows = rows
        table.setRowCount(len(rows))

        self._checkboxes = {}
        self._track_combos = {}

        for i, row_data in enumerate(rows):
            if row_data["type"] == "section_header":
                self._populate_section_header_row(table, i, row_data)
            else:
                self._populate_data_row(table, i, row_data)

        header = table.horizontalHeader()
        header.setMinimumSectionSize(1)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        table.setColumnWidth(0, 10)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        table.setColumnWidth(1, 28)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        # Tipo, FPS, Compresión — ajustan al contenido
        for col in (3, 5, 6):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        # Resolución (col 4) — mínimo 165px para "2048×1152 (2.39:1)"
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Interactive)
        table.setColumnWidth(4, 165)
        # Frames/Duration (col 7) — mínimo 210px para "1001–1480  (480f - 20.0s)"
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.Interactive)
        table.setColumnWidth(7, 210)
        # Track — ajusta al contenido
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeToContents)

        table.cellClicked.connect(self._on_media_row_clicked)
        return table

    def _on_media_row_clicked(self, row, col):
        if col <= 1:
            return  # barra de color y checkbox manejan sus propios eventos
        if row in self._checkboxes:
            chk = self._checkboxes[row]
            chk.setChecked(not chk.isChecked())

    def _on_convert_row_clicked(self, row, col):
        if col <= 1:
            return  # barra de color y checkbox manejan sus propios eventos
        if row in self._convert_checkboxes:
            chk = self._convert_checkboxes[row]
            if chk.isEnabled():
                chk.setChecked(not chk.isChecked())
        self._update_transcode_btn_state()

    def _on_convert_row_double_clicked(self, row, col):
        """Doble click en la tabla de transcode: restaura checkbox (cancela el toggle del
        primer click) y abre la carpeta del item en el explorador del sistema."""
        import os, subprocess
        # El primer click ya hizo toggle del checkbox; lo invertimos para dejarlo como estaba.
        if col > 1 and row in self._convert_checkboxes:
            chk = self._convert_checkboxes[row]
            if chk.isEnabled():
                chk.setChecked(not chk.isChecked())
            self._update_transcode_btn_state()
        # Abrir carpeta en el explorador
        if not hasattr(self, "_convert_rows") or row >= len(self._convert_rows):
            return
        item = self._convert_rows[row]
        path = item.get("path", "")
        if not path:
            return
        if os.name == "nt":
            os.startfile(path)
        elif os.name == "posix":
            subprocess.Popen(["open", path])

    def _build_table_rows(self):
        """
        Construye la lista de filas con secciones intercaladas.
        Tipos: 'section_header' | 'data'
        También puebla self._section_data_rows: {section -> [row_indices]}.
        """
        rows = []
        self._section_data_rows = {"publish": [], "plates": [], "refs": []}

        # PUBLISH — todas las versiones, ordenadas por task y luego version desc
        pub_sorted = sorted(
            (p for p in self.publish_items if p.get("has_versions")),
            key=lambda p: (_TASK_ORDER.get(p["task"], 9), -p["version_num"])
        )
        if pub_sorted:
            rows.append({"type": "section_header", "label": "PUBLISH", "color": "#777777"})
            for p in pub_sorted:
                idx = len(rows)
                self._section_data_rows["publish"].append(idx)
                rows.append({"type": "data", "source": "publish", "item": p,
                             "section": "publish"})

        # PLATES — EXR sequences + MOVs detectados como plates
        plates = [i for i in self.input_items
                  if i["kind"] == "exr_seq"
                  or (i["kind"] == "mov" and _is_plate_track(i.get("track")))]
        if plates:
            rows.append({"type": "section_header", "label": "PLATES", "color": _CLR_PLATES, "text_color": "#6fc9d9"})
            for item in plates:
                idx = len(rows)
                self._section_data_rows["plates"].append(idx)
                rows.append({"type": "data", "source": "input", "item": item,
                             "section": "plates"})

        # REFERENCES — MOVs de _input (editref primero, seqref despues)
        def _ref_sort_key(x):
            n = x.get("name", "").lower()
            if "editrefclean" in n: return 0
            if "editref" in n:      return 1
            if "seqref" in n:       return 2
            return 3

        refs = sorted(
            [i for i in self.input_items
             if i["kind"] == "mov" and not _is_plate_track(i.get("track"))],
            key=_ref_sort_key
        )
        if refs:
            rows.append({"type": "section_header", "label": "REFERENCES",
                         "color": _CLR_REFS})
            for item in refs:
                idx = len(rows)
                self._section_data_rows["refs"].append(idx)
                rows.append({"type": "data", "source": "input", "item": item,
                             "section": "refs"})

        return rows

    def _populate_section_header_row(self, table, row_i, row_data):
        ncols = table.columnCount()
        color = row_data["color"]
        text_color = row_data.get("text_color", color)
        label = row_data["label"]

        # Para PUBLISH, usar gradiente de colores (cleanup → roto → comp)
        if label == "PUBLISH":
            gradient = QtGui.QLinearGradient(0, 0, 0, 1)
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setColorAt(0.0, QtGui.QColor("#27c8c3"))   # cleanup
            gradient.setColorAt(0.5, QtGui.QColor("#2abf7e"))   # roto
            gradient.setColorAt(1.0, QtGui.QColor("#3381e0"))   # comp
            bar = QtWidgets.QTableWidgetItem()
            bar.setBackground(QtGui.QBrush(gradient))
            bar.setFlags(QtCore.Qt.NoItemFlags)
            table.setItem(row_i, 0, bar)
        else:
            # Para otras secciones, color sólido
            bar = QtWidgets.QTableWidgetItem()
            bar.setBackground(QtGui.QColor(color))
            bar.setFlags(QtCore.Qt.NoItemFlags)
            table.setItem(row_i, 0, bar)

        table.setSpan(row_i, 1, 1, ncols - 1)
        if label == "PUBLISH":
            lbl = GradientTextLabel(
                "  " + label, ["#3381e0", "#2abf7e", "#27c8c3"]
            )
            lbl.setContentsMargins(8, 3, 8, 3)
            font = lbl.font()
            font.setBold(True)
            font.setPointSize(8)
            lbl.setFont(font)
        else:
            lbl = QtWidgets.QLabel("  " + label)
            lbl.setStyleSheet(
                "color: %s; font-weight: bold; font-size: 11px; "
                "padding: 3px 8px; background: #313131; letter-spacing: 1px;" % text_color
            )
        table.setCellWidget(row_i, 1, lbl)
        table.setRowHeight(row_i, 24)

    def _populate_data_row(self, table, row_i, row_data):
        source  = row_data["source"]
        item    = row_data["item"]
        section = row_data.get("section", "")

        is_input_exr = (source == "input" and item.get("kind") == "exr_seq")
        is_latest    = item.get("is_latest", True)
        is_seqref    = (source == "input" and item.get("track") is None
                        and "seqref" in item.get("name", "").lower())

        # Col 0: barra de color (indica tipo/task de la fila)
        if section == "publish":
            bar_color = _TASK_ROW_COLORS.get(item.get("task", ""), "#555555")
        elif section == "plates":
            bar_color = _CLR_PLATES
        else:
            bar_color = _CLR_REFS
        bar_item = QtWidgets.QTableWidgetItem()
        bar_item.setBackground(QtGui.QColor(bar_color))
        bar_item.setFlags(QtCore.Qt.NoItemFlags)
        table.setItem(row_i, 0, bar_item)

        # Col 1: checkbox
        chk = QtWidgets.QCheckBox()
        chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        chk.setChecked(True)
        chk.stateChanged.connect(self._update_action_btns)
        self._checkboxes[row_i] = chk
        container = QtWidgets.QWidget()
        cl = QtWidgets.QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setAlignment(QtCore.Qt.AlignCenter)
        cl.addWidget(chk)
        table.setCellWidget(row_i, 1, container)

        # Col 2: Nombre
        name = item.get("name") or item.get("version_name") or ""
        if is_seqref:
            name_color = _CLR_REFS
            tooltip    = "Se importará al bin. No se coloca en el timeline."
        elif section == "publish":
            name_color = "#CCCCCC" if is_latest else "#777777"
            tooltip    = ""
        else:
            name_color = "#CCCCCC" if is_latest else "#888888"
            tooltip    = ""
        name_item = QtWidgets.QTableWidgetItem(name)
        name_item.setForeground(QtGui.QColor(name_color))
        if tooltip:
            name_item.setToolTip(tooltip)
        table.setItem(row_i, 2, name_item)

        # Col 3: Tipo
        if source == "publish" or item.get("kind") == "exr_seq":
            kind_str = "EXR seq"
        elif item.get("kind") == "mov":
            kind_str = (item.get("ext") or
                        Path(item.get("path", "")).suffix.lstrip(".").upper() or "MOV")
        else:
            kind_str = "Archivo"
        tipo_item = QtWidgets.QTableWidgetItem(kind_str)
        tipo_item.setForeground(QtGui.QColor("#888888"))
        table.setItem(row_i, 3, tipo_item)

        # Color base para esta fila (más apagado si no es la versión latest)
        _dim = "#888888" if is_latest else "#666666"

        # Col 4: Res — dimensiones en dim, AR en dorado suave
        w, h = item.get("width"), item.get("height")
        if w and h:
            ar = _ar_str(w, h)
            if ar:
                ar_clr = _CLR_AR if is_latest else "#786840"
                res_html = ("<span style='color:%s;'>%d×%d</span>"
                            " <span style='color:%s;'>(%s)</span>" % (_dim, w, h, ar_clr, ar))
                table.setCellWidget(row_i, 4, _cell_html_label(res_html))
            else:
                ri = QtWidgets.QTableWidgetItem("%d×%d" % (w, h))
                ri.setForeground(QtGui.QColor(_dim))
                table.setItem(row_i, 4, ri)
        else:
            ri = QtWidgets.QTableWidgetItem("—")
            ri.setForeground(QtGui.QColor(_dim))
            table.setItem(row_i, 4, ri)

        # Col 5: FPS
        fps = item.get("fps")
        fps_str = ("%.5g" % fps) if fps else "—"
        fps_item = QtWidgets.QTableWidgetItem(fps_str)
        fps_item.setForeground(QtGui.QColor(_dim))
        table.setItem(row_i, 5, fps_item)

        # Col 6: Compresión — coloreada según tipo (dwaa=verde, zip/piz=rojo)
        comp = item.get("compression") or "—"
        cc = _comp_color(comp, greyed=not is_latest)
        if cc != _dim:
            comp_html = "<span style='color:%s;'>%s</span>" % (cc, comp)
            table.setCellWidget(row_i, 6, _cell_html_label(comp_html))
        else:
            ci = QtWidgets.QTableWidgetItem(comp)
            ci.setForeground(QtGui.QColor(cc))
            table.setItem(row_i, 6, ci)

        # Col 7: Frames  "1001–1480  (480f - 20.0s)"
        ff = item.get("first_frame")
        lf = item.get("last_frame")
        fc = item.get("frame_count")
        if ff is not None and lf is not None:
            fc_val = fc if fc is not None else (lf - ff + 1)
            fps_val = item.get("fps")
            secs_txt = (" - %.1fs" % (fc_val / float(fps_val))) if fps_val else ""
            fc_clr = _CLR_FRAMES if is_latest else "#786830"
            frames_html = (
                "<span style='color:%s;'>%d–%d</span>"
                "  (<span style='color:%s;'>%df%s</span>)" % (
                    _dim, ff, lf, fc_clr, fc_val, secs_txt))
            table.setCellWidget(row_i, 7, _cell_html_label(frames_html))
        else:
            fi = QtWidgets.QTableWidgetItem("—")
            fi.setForeground(QtGui.QColor(_dim))
            table.setItem(row_i, 7, fi)

        # Col 8: Track (dropdown editable para inputs, label para publish)
        track = item.get("track")
        if source == "input" and item.get("kind") in ("exr_seq", "mov"):
            combo = self._build_track_combo(track, row_i)
            table.setCellWidget(row_i, 8, combo)
            self._track_combos[row_i] = combo
        else:
            track_str = track if track else "—"
            lbl = QtWidgets.QLabel(track_str)
            lbl.setStyleSheet("color:#888888; padding:2px 6px;")
            table.setCellWidget(row_i, 8, lbl)

    def _build_track_combo(self, current_track, row_id):
        track_options = [
            "aPlate", "bPlate", "cPlate", "dPlate", "ePlate",
            "fgPlate", "bgPlate", "EditRef", "EditRefClean",
            "_comp_", "_roto_", "_cleanup_",
        ]
        combo = _ArrowComboBox()
        combo.setView(QtWidgets.QListView())
        combo.setStyleSheet(
            "QComboBox { background-color:#272727; border:0px; "
            "color:#a7a7a7; padding:1px 4px; }"
            "QComboBox::drop-down { border:0px; width:14px; }"
            "QComboBox::down-arrow { image:none; width:0px; height:0px; }"
            "QComboBox QAbstractItemView { background-color:#2B2B2B; "
            "border:1px solid #444444; color:#a7a7a7; "
            "selection-background-color:#272727; selection-color:#a7a7a7; outline:none; }"
        )
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
        row_data = self._table_rows[row]
        if row_data.get("type") == "section_header":
            return None
        return row_data["item"].get("track")

    def _update_action_btns(self):
        any_checked = any(chk.isChecked() for chk in self._checkboxes.values())
        has_plate_checked = any(
            chk.isChecked()
            and self._table_rows[row].get("section") == "plates"
            for row, chk in self._checkboxes.items()
        )
        self._rename_btn.setEnabled(any_checked)
        self._convert_btn.setEnabled(has_plate_checked)
        self._import_btn.setEnabled(any_checked)

    # ── selección rápida ─────────────────────────────────────────

    def _select_all(self):
        for chk in self._checkboxes.values():
            chk.setChecked(True)

    def _clear_selection(self):
        for chk in self._checkboxes.values():
            chk.setChecked(False)

    def _select_section(self, section):
        for row_i in self._section_data_rows.get(section, []):
            if row_i in self._checkboxes:
                self._checkboxes[row_i].setChecked(True)

    def _go_to_rename(self):
        self._update_rename_page()
        self._show_page(self.PAGE_RENAME)

    def _go_to_convert(self):
        self._update_convert_page()
        self._show_page(self.PAGE_CONVERT)

    # ══════════════════════════════════════════════════════════
    #  PAGINA: Rename
    # ══════════════════════════════════════════════════════════

    def _on_rename_row_clicked(self, row, col):
        if col <= 1:
            return
        if row in self._rename_checkboxes:
            chk = self._rename_checkboxes[row]
            if chk.isEnabled():
                chk.setChecked(not chk.isChecked())
        self._update_rename_btn_state()

    def _on_rename_row_double_clicked(self, row, col):
        import os
        import subprocess
        if col > 1 and row in self._rename_checkboxes:
            chk = self._rename_checkboxes[row]
            if chk.isEnabled():
                chk.setChecked(not chk.isChecked())
            self._update_rename_btn_state()
        if not hasattr(self, "_rename_preview_rows") or row >= len(self._rename_preview_rows):
            return
        it = self._rename_preview_rows[row]
        p = it.get("folder_path") if it.get("is_sequence") else it.get("item_path")
        if not p:
            return
        if os.name == "nt":
            os.startfile(p)
        elif os.name == "posix":
            subprocess.Popen(["open", p])

    def _build_page_rename(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(_section_label("RENOMBRAR"))

        self._rename_table = QtWidgets.QTableWidget()
        self._rename_table.setColumnCount(8)
        self._rename_table.setHorizontalHeaderLabels(
            ["", "", "Original", "→", "Renamed", "Folder Orig", "Folder Renamed", "Estado"]
        )
        self._rename_table.verticalHeader().setVisible(False)
        self._rename_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._rename_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._rename_table.setFocusPolicy(QtCore.Qt.NoFocus)
        self._rename_table.setShowGrid(False)
        self._rename_table.setStyleSheet(_TABLE_STYLE)
        self._rename_table.setMinimumHeight(120)
        self._rename_table.setMaximumHeight(250)
        hdr = self._rename_table.horizontalHeader()
        hdr.setMinimumSectionSize(1)
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self._rename_table.setColumnWidth(0, 10)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self._rename_table.setColumnWidth(1, 28)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.Interactive)
        self._rename_table.setColumnWidth(5, 210)
        hdr.setSectionResizeMode(6, QtWidgets.QHeaderView.Interactive)
        self._rename_table.setColumnWidth(6, 210)
        hdr.setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch)
        hdr.setStretchLastSection(True)
        self._rename_table.cellClicked.connect(self._on_rename_row_clicked)
        self._rename_table.cellDoubleClicked.connect(self._on_rename_row_double_clicked)
        layout.addWidget(self._rename_table)

        self._rename_summary_lbl = QtWidgets.QLabel("")
        self._rename_summary_lbl.setStyleSheet("color:#888888; padding:2px 6px;")
        layout.addWidget(self._rename_summary_lbl)

        layout.addWidget(_separator())

        line_style = (
            "QLineEdit { background-color:#272727; border:1px solid #555555;"
            " color:#cccccc; padding:4px 8px; border-radius:3px; }"
            "QLineEdit:focus { border:1px solid #666666; }"
        )

        # Etapa 1
        sr1_box = QtWidgets.QGroupBox("Step 1 — Search & Replace")
        sr1_box.setStyleSheet("QGroupBox{color:#a7a7a7; border:1px solid #3a3a3a; margin-top:8px; padding-top:8px;}")
        sr1_layout = QtWidgets.QHBoxLayout(sr1_box)
        self._rename_sr1_search = QtWidgets.QLineEdit()
        self._rename_sr1_search.setPlaceholderText("Search")
        self._rename_sr1_search.setStyleSheet(line_style)
        self._rename_sr1_replace = QtWidgets.QLineEdit()
        self._rename_sr1_replace.setPlaceholderText("Replace")
        self._rename_sr1_replace.setStyleSheet(line_style)
        self._rename_sr1_case = QtWidgets.QCheckBox("Case Sensitive")
        self._rename_sr1_case.setStyleSheet("color:#a7a7a7; padding:2px;")
        sr1_layout.addWidget(self._rename_sr1_search, 1)
        sr1_layout.addWidget(self._rename_sr1_replace, 1)
        sr1_layout.addWidget(self._rename_sr1_case, 0)
        layout.addWidget(sr1_box)

        # Etapa 2
        sr2_box = QtWidgets.QGroupBox("Step 2 — Search & Replace")
        sr2_box.setStyleSheet("QGroupBox{color:#a7a7a7; border:1px solid #3a3a3a; margin-top:8px; padding-top:8px;}")
        sr2_layout = QtWidgets.QHBoxLayout(sr2_box)
        self._rename_sr2_search = QtWidgets.QLineEdit()
        self._rename_sr2_search.setPlaceholderText("Search")
        self._rename_sr2_search.setStyleSheet(line_style)
        self._rename_sr2_replace = QtWidgets.QLineEdit()
        self._rename_sr2_replace.setPlaceholderText("Replace")
        self._rename_sr2_replace.setStyleSheet(line_style)
        self._rename_sr2_case = QtWidgets.QCheckBox("Case Sensitive")
        self._rename_sr2_case.setStyleSheet("color:#a7a7a7; padding:2px;")
        sr2_layout.addWidget(self._rename_sr2_search, 1)
        sr2_layout.addWidget(self._rename_sr2_replace, 1)
        sr2_layout.addWidget(self._rename_sr2_case, 0)
        layout.addWidget(sr2_box)

        # Etapa 3
        delim_col = QtWidgets.QVBoxLayout()
        delim_col.addWidget(_section_label("Step 3 — Delimiter"))
        delim_row = QtWidgets.QHBoxLayout()
        delim_lbl = QtWidgets.QLabel("Before frame:")
        delim_lbl.setStyleSheet("color:#a7a7a7;")
        delim_row.addWidget(delim_lbl)
        self._rename_delim_combo = _ArrowComboBox()
        self._rename_delim_combo.setStyleSheet(self._COMBO_STYLE)
        self._rename_delim_combo.setView(QtWidgets.QListView())
        self._rename_delim_combo.addItems(["_", "."])
        self._rename_delim_combo.setFixedWidth(80)
        delim_row.addWidget(self._rename_delim_combo)
        delim_row.addStretch()
        delim_col.addLayout(delim_row)
        layout.addLayout(delim_col)

        # Etapa 4 (debajo de la etapa 3)
        pad_col = QtWidgets.QVBoxLayout()
        pad_col.addWidget(_section_label("Step 4 — Frame Digits"))
        pad_row = QtWidgets.QHBoxLayout()
        pad_lbl = QtWidgets.QLabel("Digits:")
        pad_lbl.setStyleSheet("color:#a7a7a7;")
        pad_row.addWidget(pad_lbl)
        self._rename_digits_spin = _ArrowSpinBox()
        self._rename_digits_spin.setRange(1, 12)
        self._rename_digits_spin.setValue(4)
        self._rename_digits_spin.setStyleSheet(_ArrowSpinBox._STYLE)
        self._rename_digits_spin.setFixedWidth(88)
        pad_row.addWidget(self._rename_digits_spin)
        pad_row.addStretch()
        pad_col.addLayout(pad_row)
        layout.addLayout(pad_col)

        if Rename_Test_mode:
            test_mode_lbl = QtWidgets.QLabel(
                "WARNING: Rename_Test_mode activo. Se copia a carpeta 'renamned' y solo se renombra esa copia."
            )
            test_mode_lbl.setStyleSheet("color:#d9a441; padding:2px 6px;")
            layout.addWidget(test_mode_lbl)
        layout.addStretch()
        layout.addWidget(_separator())

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self._rename_back_btn = QtWidgets.QPushButton("← Go Back")
        self._rename_back_btn.setStyleSheet(_BTN_SECONDARY)
        self._rename_back_btn.clicked.connect(lambda: self._show_page(self.PAGE_MEDIA))
        btn_row.addWidget(self._rename_back_btn)
        btn_row.addSpacing(6)
        self._apply_rename_btn = QtWidgets.QPushButton("Rename")
        self._apply_rename_btn.setStyleSheet(_BTN_PRIMARY)
        self._apply_rename_btn.setEnabled(False)
        self._apply_rename_btn.clicked.connect(self._run_rename)
        btn_row.addWidget(self._apply_rename_btn)
        layout.addSpacing(_BTN_ROW_TOP_SPACING)
        layout.addLayout(btn_row)

        self._rename_checkboxes = {}
        self._rename_selected_rows = []
        self._rename_preview_rows = []
        self._rename_settings = rename_settings_mod.load_settings()
        self._load_rename_settings_to_ui()
        self._connect_rename_autosave()
        self._refresh_rename_preview()
        return page

    def _connect_rename_autosave(self):
        for _w, _sig in [
            (self._rename_sr1_search, "textChanged"),
            (self._rename_sr1_replace, "textChanged"),
            (self._rename_sr1_case, "stateChanged"),
            (self._rename_sr2_search, "textChanged"),
            (self._rename_sr2_replace, "textChanged"),
            (self._rename_sr2_case, "stateChanged"),
            (self._rename_delim_combo, "currentIndexChanged"),
            (self._rename_digits_spin, "valueChanged"),
        ]:
            getattr(_w, _sig).connect(self._on_rename_settings_changed)

    def _load_rename_settings_to_ui(self):
        s = self._rename_settings
        sr1 = s.get("sr1", {})
        sr2 = s.get("sr2", {})
        dm = s.get("delimiter", {})
        pd = s.get("padding", {})
        self._rename_sr1_search.setText(sr1.get("search", ""))
        self._rename_sr1_replace.setText(sr1.get("replace", ""))
        self._rename_sr1_case.setChecked(sr1.get("case_sensitive", "false").lower() == "true")
        self._rename_sr2_search.setText(sr2.get("search", ""))
        self._rename_sr2_replace.setText(sr2.get("replace", ""))
        self._rename_sr2_case.setChecked(sr2.get("case_sensitive", "false").lower() == "true")
        d = dm.get("char", "_")
        self._rename_delim_combo.setCurrentIndex(1 if d == "." else 0)
        try:
            self._rename_digits_spin.setValue(int(pd.get("digits", "4")))
        except Exception:
            self._rename_digits_spin.setValue(4)

    def _collect_rename_settings_from_ui(self):
        return {
            "sr1": {
                "search": self._rename_sr1_search.text(),
                "replace": self._rename_sr1_replace.text(),
                "case_sensitive": str(self._rename_sr1_case.isChecked()).lower(),
            },
            "sr2": {
                "search": self._rename_sr2_search.text(),
                "replace": self._rename_sr2_replace.text(),
                "case_sensitive": str(self._rename_sr2_case.isChecked()).lower(),
            },
            "delimiter": {
                "char": self._rename_delim_combo.currentText(),
            },
            "padding": {
                "digits": str(self._rename_digits_spin.value()),
            },
        }

    def _on_rename_settings_changed(self, *_):
        self._rename_settings = self._collect_rename_settings_from_ui()
        rename_settings_mod.save_settings(self._rename_settings)
        self._refresh_rename_preview()

    def _update_rename_page(self):
        selected = []
        for row, chk in self._checkboxes.items():
            if not chk.isChecked():
                continue
            row_data = self._table_rows[row]
            if row_data.get("type") != "data":
                continue
            item = dict(row_data.get("item", {}))
            item["source"] = row_data.get("section")
            selected.append(item)
        self._rename_selected_rows = rename_mod.build_selected_rows(selected)
        self._refresh_rename_preview()

    def _refresh_rename_preview(self):
        if not hasattr(self, "_rename_table"):
            return
        colors = {
            1: _CLR_AR,
            2: _CLR_PAR,
            3: _CLR_COMP,
            4: _CLR_FRAMES,
        }
        self._rename_preview_rows = rename_mod.compute_preview(
            getattr(self, "_rename_selected_rows", []),
            self._collect_rename_settings_from_ui() if hasattr(self, "_rename_sr1_search") else getattr(self, "_rename_settings", {}),
            colors,
        )
        rows = self._rename_preview_rows
        self._rename_table.setRowCount(len(rows))
        self._rename_checkboxes = {}
        blocked_n = 0
        checked_ok = 0
        for i, it in enumerate(rows):
            blocked = it.get("blocked", False)
            fg = "#666666" if blocked else "#a7a7a7"

            bar = QtWidgets.QTableWidgetItem()
            bar.setBackground(QtGui.QColor(_CLR_PLATES if it.get("is_sequence") else _CLR_REFS))
            if blocked:
                bar.setBackground(QtGui.QColor("#444444"))
            bar.setFlags(QtCore.Qt.NoItemFlags)
            self._rename_table.setItem(i, 0, bar)

            chk = QtWidgets.QCheckBox()
            chk.setStyleSheet("color:#a7a7a7; padding:2px;")
            chk.setChecked(not blocked)
            chk.setEnabled(not blocked)
            chk.stateChanged.connect(lambda *_: self._update_rename_btn_state())
            self._rename_checkboxes[i] = chk
            cbox = QtWidgets.QWidget()
            cl = QtWidgets.QHBoxLayout(cbox)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(QtCore.Qt.AlignCenter)
            cl.addWidget(chk)
            self._rename_table.setCellWidget(i, 1, cbox)

            self._rename_table.setCellWidget(i, 2, _cell_html_label(it.get("original_html", "")))
            arrow = QtWidgets.QTableWidgetItem("→")
            arrow.setForeground(QtGui.QColor("#444444" if blocked else "#666666"))
            arrow.setTextAlignment(QtCore.Qt.AlignCenter)
            self._rename_table.setItem(i, 3, arrow)
            self._rename_table.setCellWidget(i, 4, _cell_html_label(it.get("renamed_html", "")))

            folder_orig_item = QtWidgets.QTableWidgetItem(it.get("folder_name", ""))
            folder_orig_item.setForeground(QtGui.QColor(fg))
            self._rename_table.setItem(i, 5, folder_orig_item)

            folder_new_item = QtWidgets.QTableWidgetItem(it.get("target_folder_name", it.get("folder_name", "")))
            folder_new_item.setForeground(QtGui.QColor(fg))
            self._rename_table.setItem(i, 6, folder_new_item)

            st_color = _CLR_STATUS_PENDING
            st = it.get("status", "Pendiente")
            if blocked:
                st_color = _CLR_STATUS_UPSCALE
            elif not it.get("has_changes"):
                st_color = "#888888"
            self._rename_table.setCellWidget(i, 7, _cell_html_label(
                "<span style='color:%s;'>%s</span>" % (st_color, st)
            ))

            if blocked:
                blocked_n += 1
            elif chk.isChecked() and it.get("has_changes"):
                checked_ok += 1

        self._rename_summary_lbl.setText(
            "%d items · %d listos para rename · %d bloqueados" % (
                len(rows), checked_ok, blocked_n
            )
        )
        self._update_rename_btn_state()

    def _update_rename_btn_state(self):
        ready = False
        for i, chk in self._rename_checkboxes.items():
            if not chk.isEnabled() or not chk.isChecked():
                continue
            if i < len(self._rename_preview_rows) and self._rename_preview_rows[i].get("has_changes"):
                ready = True
                break
        self._apply_rename_btn.setEnabled(ready)
        self._apply_rename_btn.setToolTip("" if ready else "No hay filas válidas con cambios")

    def _run_rename(self):
        to_apply = []
        for i, chk in self._rename_checkboxes.items():
            if not chk.isEnabled() or not chk.isChecked():
                continue
            if i < len(self._rename_preview_rows):
                row = self._rename_preview_rows[i]
                if row.get("blocked") or not row.get("has_changes"):
                    continue
                to_apply.append(row)
        if Rename_Test_mode:
            QtWidgets.QMessageBox.information(
                self,
                "Rename Test Mode",
                "Rename_Test_mode está activo.\n"
                "Se creará la carpeta 'renamned' en paralelo y se renombrará SOLO sobre la copia.",
            )
        result = rename_mod.execute_ops(to_apply, test_mode=Rename_Test_mode, test_folder_name="renamned")
        if result.get("errors"):
            QtWidgets.QMessageBox.warning(
                self,
                "Rename",
                "Se produjo un error durante el rename:\n%s" % "\n".join(result["errors"]),
            )
            return
        applied = int(result.get("applied", 0))
        if applied > 0:
            self._rename_happened = True
            self._update_rename_page()
        self._refresh_rename_preview()

    # ══════════════════════════════════════════════════════════
    #  PAGINA: Transcode Plates
    # ══════════════════════════════════════════════════════════

    # Presets de resolución: label → (W, H) o None (original)
    _COMBO_STYLE = (
        "QComboBox { background-color:#272727; border:1px solid #444; "
        "color:#a7a7a7; padding:3px 6px; }"
        "QComboBox::drop-down { border:0px; width:18px; }"
        "QComboBox::down-arrow { image:none; width:0px; height:0px; }"
        "QComboBox QAbstractItemView { background-color:#2B2B2B; color:#a7a7a7; "
        "selection-background-color:#272727; selection-color:#a7a7a7; outline:0; }"
    )

    _SPIN_STYLE = """
        QSpinBox, QDoubleSpinBox {
            background-color: #272727; border: 1px solid #444;
            color: #a7a7a7; padding: 2px 20px 2px 4px;
        }
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            subcontrol-origin: border; subcontrol-position: top right;
            width: 18px; border-left: 1px solid #444;
            background-color: #2e2e2e;
        }
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
            background-color: #3a3a3a;
        }
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 4px solid #888;
            width: 0px; height: 0px;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            subcontrol-origin: border; subcontrol-position: bottom right;
            width: 18px; border-left: 1px solid #444;
            background-color: #2e2e2e;
        }
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #3a3a3a;
        }
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #888;
            width: 0px; height: 0px;
        }
    """

    def _build_page_convert(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(_section_label("TRANSCODE PLATES"))

        # Tabla de plates a transcodear
        # col 0: barra color (10px)  col 1: checkbox (28px)
        # col 2: Nombre  col 3: Origen  col 4: →  col 5: Destino  col 6: Tamaño  col 7: Estado
        self._convert_table = QtWidgets.QTableWidget()
        self._convert_table.setColumnCount(8)
        self._convert_table.setHorizontalHeaderLabels(
            ["", "", "Nombre", "Origen", "→", "Destino", "Tamaño", "Estado"]
        )
        self._convert_table.verticalHeader().setVisible(False)
        self._convert_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._convert_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._convert_table.setFocusPolicy(QtCore.Qt.NoFocus)
        self._convert_table.setShowGrid(False)
        self._convert_table.setStyleSheet(_TABLE_STYLE)
        self._convert_table.setMinimumHeight(120)
        self._convert_table.setMaximumHeight(220)
        hdr = self._convert_table.horizontalHeader()
        hdr.setMinimumSectionSize(1)
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self._convert_table.setColumnWidth(0, 10)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self._convert_table.setColumnWidth(1, 28)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        # Origen (col 3) — 400px para "4096×2160 (2.39:1) (2) · 16b · RGB · dwaa · 480f - 20.0s"
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)
        self._convert_table.setColumnWidth(3, 400)
        # Flecha (col 4)
        hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        # Destino (col 5) — mínimo 320px para "2048×858 (2.39:1) · half · RGB · dwaa"
        hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.Interactive)
        self._convert_table.setColumnWidth(5, 320)
        # Tamaño — ajusta al contenido; Estado — ancho fijo para caber barra de progreso
        hdr.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(7, QtWidgets.QHeaderView.Interactive)
        self._convert_table.setColumnWidth(7, 130)
        self._convert_checkboxes = {}
        self._convert_table.cellClicked.connect(self._on_convert_row_clicked)
        self._convert_table.cellDoubleClicked.connect(self._on_convert_row_double_clicked)
        layout.addWidget(self._convert_table)

        layout.addWidget(_separator())

        # ── Opciones en 2 columnas ─────────────────────────────────
        opts_row = QtWidgets.QHBoxLayout()
        opts_row.setSpacing(20)

        # Columna izquierda — Codec / Calidad
        col_codec = QtWidgets.QVBoxLayout()
        col_codec.setSpacing(6)
        col_codec.addWidget(_section_label("Codec / Calidad"))

        self._convert_dwaa_chk = QtWidgets.QCheckBox("Convertir a DWAA")
        self._convert_dwaa_chk.setChecked(True)
        self._convert_dwaa_chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        self._convert_dwaa_chk.stateChanged.connect(self._on_dwaa_chk_changed)
        col_codec.addWidget(self._convert_dwaa_chk)

        # Contenedor del nivel (se oculta cuando DWAA está desactivado)
        self._dwaa_level_widget = QtWidgets.QWidget()
        dwaa_row = QtWidgets.QHBoxLayout(self._dwaa_level_widget)
        dwaa_row.setContentsMargins(0, 0, 0, 0)
        dwaa_lbl = QtWidgets.QLabel("DWAA level:")
        dwaa_lbl.setStyleSheet("color:#a7a7a7;")
        dwaa_row.addWidget(dwaa_lbl)
        self._convert_dwaa_level = QtWidgets.QSpinBox()
        self._convert_dwaa_level.setRange(30, 60)
        self._convert_dwaa_level.setValue(45)
        self._convert_dwaa_level.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self._convert_dwaa_level.setAlignment(QtCore.Qt.AlignCenter)
        self._convert_dwaa_level.setFixedWidth(60)
        self._convert_dwaa_level.setStyleSheet("""
            QSpinBox {
                background-color: #272727;
                color: #a7a7a7;
                border: 1px solid #444;
                padding: 2px 4px;
                selection-background-color: #505060;
                selection-color: #d0d0d0;
            }
        """)
        dwaa_row.addWidget(self._convert_dwaa_level)
        self._convert_dwaa_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._convert_dwaa_slider.setRange(30, 60)
        self._convert_dwaa_slider.setValue(45)
        self._convert_dwaa_slider.setFixedWidth(120)
        self._convert_dwaa_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 2px; background:#333; border-radius:1px;
            }
            QSlider::handle:horizontal {
                background:#888; width:10px; margin:-4px 0; border-radius:5px;
            }
            QSlider::handle:horizontal:hover { background:#aaa; }
            QSlider::sub-page:horizontal { background:#5a5a5a; border-radius:1px; }
        """)
        self._convert_dwaa_slider.valueChanged.connect(self._convert_dwaa_level.setValue)
        self._convert_dwaa_level.valueChanged.connect(self._convert_dwaa_slider.setValue)
        self._convert_dwaa_level.valueChanged.connect(lambda *_: self._refresh_convert_destinos())
        dwaa_row.addWidget(self._convert_dwaa_slider)
        dwaa_row.addStretch()
        col_codec.addWidget(self._dwaa_level_widget)

        ch_row = QtWidgets.QHBoxLayout()
        ch_lbl = QtWidgets.QLabel("Channels:")
        ch_lbl.setStyleSheet("color:#a7a7a7;")
        ch_row.addWidget(ch_lbl)
        self._convert_channels = _ArrowComboBox()
        self._convert_channels.setStyleSheet(self._COMBO_STYLE)
        self._convert_channels.setView(QtWidgets.QListView())
        for opt in ("Mantener", "Reducir a RGB"):
            self._convert_channels.addItem(opt)
        self._convert_channels.setFixedWidth(170)
        self._convert_channels.currentIndexChanged.connect(
            lambda *_: self._refresh_convert_destinos()
        )
        ch_row.addWidget(self._convert_channels)
        ch_row.addStretch()
        col_codec.addLayout(ch_row)

        col_codec.addStretch()
        opts_row.addLayout(col_codec, 1)

        # Separador vertical
        opts_row.addWidget(_separator("v"))

        # Columna derecha — Resolución
        col_res = QtWidgets.QVBoxLayout()
        col_res.setSpacing(6)
        col_res.addWidget(_section_label("Resolución"))

        res_row = QtWidgets.QHBoxLayout()
        res_lbl = QtWidgets.QLabel("Destino:")
        res_lbl.setStyleSheet("color:#a7a7a7;")
        res_row.addWidget(res_lbl)
        self._res_combo = _ArrowComboBox()
        self._res_combo.setStyleSheet(self._COMBO_STYLE)
        _pix_trash = QtGui.QPixmap(str(SHARED_DIR / "icons" / "trash.svg"))
        _pix_hover = QtGui.QPixmap(str(SHARED_DIR / "icons" / "trash_hover.svg"))
        _res_list = _ResPresetListView(self._on_delete_preset)
        self._res_combo.setView(_res_list)
        _res_list.setItemDelegate(_ResPresetDelegate(_res_list, _pix_trash, _pix_hover))
        for label, preset in self._res_presets:
            if preset and preset not in ("custom", "timeline"):
                tw, th = preset
                ar = _ar_str(tw, th)
                display = ("%s  [%s]" % (label, ar)) if ar else label
            else:
                display = label
            self._res_combo.addItem(display)
        self._res_combo.currentIndexChanged.connect(self._on_res_preset_changed)
        self._res_combo.setMinimumWidth(260)
        res_row.addWidget(self._res_combo)
        res_row.addStretch()
        col_res.addLayout(res_row)

        # Custom W × H (oculto salvo Custom) — usa _ArrowSpinBox (solución ganadora)
        self._custom_res_widget = QtWidgets.QWidget()
        cr_row = QtWidgets.QHBoxLayout(self._custom_res_widget)
        cr_row.setContentsMargins(0, 0, 0, 0)
        self._convert_custom_w = _ArrowSpinBox()
        self._convert_custom_w.setRange(1, 16384)
        self._convert_custom_w.setValue(2048)
        self._convert_custom_w.setStyleSheet(_ArrowSpinBox._STYLE)
        self._convert_custom_w.setFixedWidth(88)
        self._convert_custom_h = _ArrowSpinBox()
        self._convert_custom_h.setRange(1, 16384)
        self._convert_custom_h.setValue(1152)
        self._convert_custom_h.setStyleSheet(_ArrowSpinBox._STYLE)
        self._convert_custom_h.setFixedWidth(88)
        x_lbl = QtWidgets.QLabel("×")
        x_lbl.setStyleSheet("color:#a7a7a7;")
        self._save_preset_btn = QtWidgets.QPushButton("Save preset")
        self._save_preset_btn.setStyleSheet(_BTN_SMALL)
        self._save_preset_btn.setFixedHeight(24)
        self._save_preset_btn.setToolTip("Guardar esta resolución como preset")
        self._save_preset_btn.clicked.connect(self._on_save_preset_clicked)
        cr_row.addWidget(self._convert_custom_w)
        cr_row.addWidget(x_lbl)
        cr_row.addWidget(self._convert_custom_h)
        cr_row.addSpacing(8)
        cr_row.addWidget(self._save_preset_btn)
        cr_row.addStretch()
        self._custom_res_widget.hide()
        col_res.addWidget(self._custom_res_widget)
        self._convert_custom_w.valueChanged.connect(self._on_custom_w_changed)
        self._convert_custom_h.valueChanged.connect(self._on_custom_h_changed)

        # Preserve aspect ratio — siempre visible
        self._convert_keep_ar = QtWidgets.QCheckBox("Preserve aspect ratio")
        self._convert_keep_ar.setChecked(True)
        self._convert_keep_ar.setStyleSheet("color:#a7a7a7; padding:2px;")
        self._convert_keep_ar.stateChanged.connect(self._on_keep_ar_changed)
        col_res.addWidget(self._convert_keep_ar)

        # Match dimension (visible solo si PAR activo)
        self._match_dim_widget = QtWidgets.QWidget()
        md_row = QtWidgets.QHBoxLayout(self._match_dim_widget)
        md_row.setContentsMargins(16, 0, 0, 0)
        md_lbl = QtWidgets.QLabel("Dimensión que manda:")
        md_lbl.setStyleSheet("color:#a7a7a7;")
        md_row.addWidget(md_lbl)
        self._convert_match_dim = _ArrowComboBox()
        self._convert_match_dim.setStyleSheet(self._COMBO_STYLE)
        self._convert_match_dim.setView(QtWidgets.QListView())
        for opt in ("Match target width", "Match target height"):
            self._convert_match_dim.addItem(opt)
        self._convert_match_dim.setFixedWidth(180)
        self._convert_match_dim.currentIndexChanged.connect(self._refresh_convert_destinos)
        md_row.addWidget(self._convert_match_dim)
        md_row.addStretch()
        col_res.addWidget(self._match_dim_widget)

        # Desanamorfizar (bake desqueeze)
        self._convert_deana_chk = QtWidgets.QCheckBox("Desanamorfizar (Pixel Aspect Ratio)")
        self._convert_deana_chk.setChecked(False)
        self._convert_deana_chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        self._convert_deana_chk.stateChanged.connect(self._on_deana_chk_changed)
        col_res.addWidget(self._convert_deana_chk)

        self._deana_par_widget = QtWidgets.QWidget()
        deana_row = QtWidgets.QHBoxLayout(self._deana_par_widget)
        deana_row.setContentsMargins(16, 0, 0, 0)
        deana_lbl = QtWidgets.QLabel("PAR fuente:")
        deana_lbl.setStyleSheet("color:#a7a7a7;")
        deana_row.addWidget(deana_lbl)
        self._convert_deana_par = _ArrowComboBox()
        self._convert_deana_par.setStyleSheet(self._COMBO_STYLE)
        self._convert_deana_par.setView(QtWidgets.QListView())
        for opt in ("1.3", "1.5", "1.8", "2.0"):
            self._convert_deana_par.addItem(opt)
        self._convert_deana_par.setFixedWidth(80)
        self._convert_deana_par.currentIndexChanged.connect(
            lambda *_: self._refresh_convert_destinos()
        )
        deana_row.addWidget(self._convert_deana_par)
        deana_row.addStretch()
        self._deana_par_widget.hide()
        col_res.addWidget(self._deana_par_widget)

        flt_row = QtWidgets.QHBoxLayout()
        flt_lbl = QtWidgets.QLabel("Filtro resampling:")
        flt_lbl.setStyleSheet("color:#a7a7a7;")
        flt_row.addWidget(flt_lbl)
        self._convert_filter = _ArrowComboBox()
        self._convert_filter.setStyleSheet(self._COMBO_STYLE)
        self._convert_filter.setView(QtWidgets.QListView())
        for opt in ("lanczos3", "cubic", "box"):
            self._convert_filter.addItem(opt)
        self._convert_filter.setFixedWidth(150)
        flt_row.addWidget(self._convert_filter)
        flt_row.addStretch()
        col_res.addLayout(flt_row)

        self._convert_no_upscale = QtWidgets.QCheckBox(
            "Aplicar solo si la resolución origen es mayor"
        )
        self._convert_no_upscale.setChecked(True)
        self._convert_no_upscale.setStyleSheet("color:#a7a7a7; padding:2px;")
        self._convert_no_upscale.stateChanged.connect(self._refresh_convert_destinos)
        col_res.addWidget(self._convert_no_upscale)

        col_res.addStretch()
        opts_row.addLayout(col_res, 1)

        layout.addLayout(opts_row)

        layout.addWidget(_separator())

        # Manejo de originales
        orig_lbl = _section_label("Manejo de originales")
        layout.addWidget(orig_lbl)

        # Aviso de test mode
        if Transcode_TEST_Mode:
            test_warn = QtWidgets.QLabel(
                "🧪  TEST MODE — el output va a {seq}/test_transcode/. "
                "Los originales no se mueven."
            )
            test_warn.setStyleSheet(
                "color:#d9a441; font-style:italic; padding:4px 0px;"
            )
            test_warn.setWordWrap(True)
            layout.addWidget(test_warn)

        self._delete_originals_chk = QtWidgets.QCheckBox("Borrar /Originals al terminar")
        self._delete_originals_chk.setChecked(False)
        self._delete_originals_chk.setEnabled(not Transcode_TEST_Mode)
        self._delete_originals_chk.setStyleSheet("color:#a7a7a7; padding:2px;")
        self._delete_originals_chk.setToolTip(
            "Los originales siempre se mueven a _input/Originals/<plate>/ antes del transcode.\n"
            "Activa para borrarlos automáticamente al terminar."
        )
        layout.addWidget(self._delete_originals_chk)

        # Resumen (totales sin estimaciones)
        layout.addWidget(_separator())
        self._convert_summary_lbl = QtWidgets.QLabel("")
        self._convert_summary_lbl.setStyleSheet(
            "color:#cccccc; padding:4px 0px; font-weight:bold;"
        )
        layout.addWidget(self._convert_summary_lbl)

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
        btn_row.addStretch()
        self._go_back_btn = QtWidgets.QPushButton("← Go Back")
        self._go_back_btn.setStyleSheet(_BTN_SECONDARY)
        self._go_back_btn.clicked.connect(lambda: self._show_page(self.PAGE_MEDIA))
        btn_row.addWidget(self._go_back_btn)
        btn_row.addSpacing(6)
        self._start_transcode_btn = QtWidgets.QPushButton("Start Transcode")
        self._start_transcode_btn.setStyleSheet(_BTN_PRIMARY)
        self._start_transcode_btn.setEnabled(False)
        self._start_transcode_btn.setToolTip("Selecciona al menos un EXR")
        self._start_transcode_btn.clicked.connect(self._run_transcode)
        btn_row.addWidget(self._start_transcode_btn)
        layout.addSpacing(_BTN_ROW_TOP_SPACING)
        layout.addLayout(btn_row)

        # Aplicar settings guardados (después de que todos los widgets existen)
        self._load_settings_to_ui()

        # Conectar auto-guardado DESPUÉS de cargar (para no disparar saves innecesarios)
        for _w, _sig in [
            (self._convert_dwaa_chk,     "stateChanged"),
            (self._convert_dwaa_level,   "valueChanged"),
            (self._convert_channels,     "currentIndexChanged"),
            (self._convert_filter,       "currentIndexChanged"),
            (self._res_combo,            "currentIndexChanged"),
            (self._convert_custom_w,     "valueChanged"),
            (self._convert_custom_h,     "valueChanged"),
            (self._convert_keep_ar,      "stateChanged"),
            (self._convert_match_dim,    "currentIndexChanged"),
            (self._convert_no_upscale,   "stateChanged"),
            (self._convert_deana_chk,    "stateChanged"),
            (self._convert_deana_par,    "currentIndexChanged"),
            (self._delete_originals_chk, "stateChanged"),
        ]:
            getattr(_w, _sig).connect(self._save_all_settings)

        return page

    def _on_res_preset_changed(self, idx):
        preset = self._res_presets[idx][1] if 0 <= idx < len(self._res_presets) else None
        self._custom_res_widget.setVisible(preset == "custom")
        self._save_preset_btn.setVisible(preset == "custom")
        self._update_match_dim_visibility()
        self._refresh_convert_destinos()

    def _on_keep_ar_changed(self):
        self._update_match_dim_visibility()
        self._refresh_convert_destinos()

    def _update_match_dim_visibility(self):
        """Muestra 'Dimensión que manda' solo cuando PAR activo y preset NO es Custom."""
        idx = self._res_combo.currentIndex()
        preset_val = self._res_presets[idx][1] if 0 <= idx < len(self._res_presets) else None
        is_custom = (preset_val == "custom")
        self._match_dim_widget.setVisible(
            self._convert_keep_ar.isChecked() and not is_custom
        )

    def _get_representative_res(self):
        """Devuelve (src_w, src_h) del primer EXR disponible, o (None, None)."""
        if hasattr(self, "_convert_rows"):
            for it in self._convert_rows:
                if it.get("kind") != "mov" and it.get("width") and it.get("height"):
                    return it["width"], it["height"]
        return None, None

    def _on_custom_w_changed(self):
        """Cuando el usuario edita el width en Custom, actualiza height si PAR activo."""
        if self._custom_ar_updating:
            return
        self._custom_master = "w"
        idx = self._res_combo.currentIndex()
        is_custom = (0 <= idx < len(self._res_presets)
                     and self._res_presets[idx][1] == "custom")  # noqa: E501
        if is_custom and self._convert_keep_ar.isChecked():
            src_w, src_h = self._get_representative_res()
            if src_w and src_h:
                new_h = int(round(self._convert_custom_w.value() * src_h / float(src_w)))
                self._custom_ar_updating = True
                self._convert_custom_h.setValue(max(1, new_h))
                self._custom_ar_updating = False
        self._refresh_convert_destinos()

    def _on_custom_h_changed(self):
        """Cuando el usuario edita el height en Custom, actualiza width si PAR activo."""
        if self._custom_ar_updating:
            return
        self._custom_master = "h"
        idx = self._res_combo.currentIndex()
        is_custom = (0 <= idx < len(self._res_presets)
                     and self._res_presets[idx][1] == "custom")  # noqa: E501
        if is_custom and self._convert_keep_ar.isChecked():
            src_w, src_h = self._get_representative_res()
            if src_w and src_h:
                new_w = int(round(self._convert_custom_h.value() * src_w / float(src_h)))
                self._custom_ar_updating = True
                self._convert_custom_w.setValue(max(1, new_w))
                self._custom_ar_updating = False
        self._refresh_convert_destinos()

    def _current_target_res(self, src_w, src_h):
        """Devuelve (tw, th) destino segun preset y opciones de aspect ratio.

        - Original:  devuelve dimensiones del origen (sin cambio).
        - Preset fijo: si PAR activo, ajusta la dimensión secundaria.
        - Custom:    si PAR activo, la dimensión "master" (última editada)
                     se mantiene y la otra se recalcula por ítem usando el AR
                     del source; si PAR desactivado, usa los spinboxes tal cual.
        """
        idx = self._res_combo.currentIndex()
        preset = self._res_presets[idx][1] if 0 <= idx < len(self._res_presets) else None
        if preset is None:
            return src_w, src_h          # Original
        if preset == "timeline":
            tw = self._tl_w or src_w
            th = self._tl_h or src_h
            if self._convert_keep_ar.isChecked() and src_w and src_h:
                match_width = self._convert_match_dim.currentText().startswith("Match target width")
                if match_width:
                    th = int(round(tw * src_h / float(src_w)))
                else:
                    tw = int(round(th * src_w / float(src_h)))
            return tw, th
        if preset == "custom":
            if self._convert_keep_ar.isChecked() and src_w and src_h:
                # La dimensión master determina; la otra se calcula por ítem
                if self._custom_master == "w":
                    tw = self._convert_custom_w.value()
                    th = int(round(tw * src_h / float(src_w)))
                else:
                    th = self._convert_custom_h.value()
                    tw = int(round(th * src_w / float(src_h)))
                return tw, th
            return self._convert_custom_w.value(), self._convert_custom_h.value()
        # preset fijo (w, h)
        tw, th = preset
        if self._convert_keep_ar.isChecked() and src_w and src_h:
            match_width = self._convert_match_dim.currentText().startswith("Match target width")
            if match_width:
                th = int(round(tw * src_h / float(src_w)))
            else:
                tw = int(round(th * src_w / float(src_h)))
        return tw, th

    def _update_res_combo_labels(self):
        """Actualiza los items del combo con la resolución final real y AR."""
        src_w, src_h = self._get_representative_res()
        for i, (label, preset) in enumerate(self._res_presets):
            if preset is None:
                # "Original": mostrar AR del source si está disponible
                if src_w and src_h:
                    ar = _ar_str(src_w, src_h)
                    self._res_combo.setItemText(
                        i, ("%s  [%s]" % (label, ar)) if ar else label)
                else:
                    self._res_combo.setItemText(i, label)
                continue
            if preset == "custom":
                self._res_combo.setItemText(i, label)
                continue
            if preset == "timeline":
                tl_w = self._tl_w or src_w
                tl_h = self._tl_h or src_h
                if tl_w and tl_h:
                    base_ar = _ar_str(tl_w, tl_h)
                    base_res = "Timeline  %d×%d" % (tl_w, tl_h)
                    base = ("%s  [%s]" % (base_res, base_ar)) if base_ar else base_res
                    if src_w and src_h:
                        tw, th = tl_w, tl_h
                        if self._convert_keep_ar.isChecked():
                            match_width = self._convert_match_dim.currentText().startswith("Match target width")
                            if match_width:
                                th = int(round(tw * src_h / float(src_w)))
                            else:
                                tw = int(round(th * src_w / float(src_h)))
                        tw, th = self._apply_deana_if_active(tw, th)
                        comp_ar = _ar_str(tw, th)
                        ar_part = ("  [%s]" % comp_ar) if comp_ar else ""
                        self._res_combo.setItemText(
                            i, "%s  →  %d×%d%s" % (base, tw, th, ar_part))
                    else:
                        self._res_combo.setItemText(i, base)
                else:
                    self._res_combo.setItemText(i, "Timeline")
                continue
            tw, th = preset
            preset_ar = _ar_str(tw, th)
            if not src_w or not src_h:
                base = ("%s  [%s]" % (label, preset_ar)) if preset_ar else label
                self._res_combo.setItemText(i, base)
                continue
            # Con source: calculamos resolución real según PAR y match_dim
            if self._convert_keep_ar.isChecked():
                match_width = self._convert_match_dim.currentText().startswith("Match target width")
                if match_width:
                    th = int(round(tw * src_h / float(src_w)))
                else:
                    tw = int(round(th * src_w / float(src_h)))
            tw, th = self._apply_deana_if_active(tw, th)
            computed_ar = _ar_str(tw, th)
            base = ("%s  [%s]" % (label, preset_ar)) if preset_ar else label
            ar_part = ("  [%s]" % computed_ar) if computed_ar else ""
            self._res_combo.setItemText(
                i, "%s  →  %d×%d%s" % (base, tw, th, ar_part))

    def _on_dwaa_chk_changed(self, state):
        """Muestra u oculta el control de DWAA level según el estado del checkbox."""
        self._dwaa_level_widget.setVisible(state == QtCore.Qt.Checked)
        self._refresh_convert_destinos()

    def _on_deana_chk_changed(self, state):
        """Muestra u oculta el selector de PAR de desanamorfizado."""
        self._deana_par_widget.setVisible(state == QtCore.Qt.Checked)
        self._refresh_convert_destinos()

    # ── Presets helpers ────────────────────────────────────────────────────────

    _N_HEAD = 2   # entradas hardcoded al inicio: Original + Timeline
    _N_TAIL = 1   # entradas hardcoded al final:  Custom...

    def _build_full_presets(self):
        """Construye la lista completa de presets (head hardcoded + INI + tail hardcoded)."""
        tl_lbl = "Timeline"
        if self._tl_w and self._tl_h:
            ar = _ar_str(self._tl_w, self._tl_h)
            res_part = "%d\u00d7%d" % (self._tl_w, self._tl_h)
            tl_lbl = ("Timeline  %s  [%s]" % (res_part, ar)) if ar else ("Timeline  %s" % res_part)
        head = [
            ("Original", None),
            (tl_lbl, "timeline"),
        ]
        mid  = [settings_mod.preset_to_tuple(p) for p in self._res_presets_raw]
        tail = [("Custom...", "custom")]
        return head + mid + tail

    # ── Settings persistentes ──────────────────────────────────────────────────

    def _load_settings_to_ui(self):
        """Aplica los settings cargados desde el INI a los widgets."""
        s   = self._imp_settings
        cod = s.get("codec", {})
        res = s.get("res", {})
        org = s.get("originals", {})

        # Codec
        self._convert_dwaa_chk.setChecked(cod.get("dwaa", "true").lower() == "true")
        try:
            self._convert_dwaa_level.setValue(int(cod.get("dwaa_level", "45")))
        except ValueError:
            pass
        ch_val = cod.get("channels", "all")
        self._convert_channels.setCurrentIndex(1 if ch_val == "rgb" else 0)
        flt_idx = self._convert_filter.findText(cod.get("filter", "lanczos3"))
        self._convert_filter.setCurrentIndex(max(0, flt_idx))

        # Resolution
        try:
            pi = int(res.get("preset_index", "0"))
            pi = max(0, min(pi, self._res_combo.count() - 1))
            self._res_combo.setCurrentIndex(pi)
        except ValueError:
            pass
        try:
            self._convert_custom_w.setValue(int(res.get("custom_w", "2048")))
        except ValueError:
            pass
        try:
            self._convert_custom_h.setValue(int(res.get("custom_h", "1152")))
        except ValueError:
            pass
        self._convert_keep_ar.setChecked(res.get("keep_ar", "true").lower() == "true")
        try:
            md_idx = int(res.get("match_dim", "0"))
            self._convert_match_dim.setCurrentIndex(max(0, min(md_idx, 1)))
        except ValueError:
            pass
        self._convert_no_upscale.setChecked(res.get("no_upscale", "true").lower() == "true")
        self._convert_deana_chk.setChecked(res.get("deana", "false").lower() == "true")
        dp_idx = self._convert_deana_par.findText(res.get("deana_par", "2.0"))
        self._convert_deana_par.setCurrentIndex(max(0, dp_idx))

        # Originals (solo si no estamos en test mode)
        if not Transcode_TEST_Mode:
            self._delete_originals_chk.setChecked(org.get("delete", "false").lower() == "true")

    def _save_all_settings(self, *_):
        """Guarda todos los settings al INI."""
        settings_mod.save_all_settings({
            "codec": {
                "dwaa":       str(self._convert_dwaa_chk.isChecked()).lower(),
                "dwaa_level": str(self._convert_dwaa_level.value()),
                "channels":   ("rgb" if self._convert_channels.currentText() == "Reducir a RGB"
                               else "all"),
                "filter":     self._convert_filter.currentText(),
            },
            "res": {
                "preset_index": str(self._res_combo.currentIndex()),
                "custom_w":     str(self._convert_custom_w.value()),
                "custom_h":     str(self._convert_custom_h.value()),
                "keep_ar":      str(self._convert_keep_ar.isChecked()).lower(),
                "match_dim":    str(self._convert_match_dim.currentIndex()),
                "no_upscale":   str(self._convert_no_upscale.isChecked()).lower(),
                "deana":        str(self._convert_deana_chk.isChecked()).lower(),
                "deana_par":    self._convert_deana_par.currentText(),
            },
            "originals": {
                "delete": str(self._delete_originals_chk.isChecked()).lower(),
            },
        })

    # ── Presets de resolución dinámicos ────────────────────────────────────────

    def _rebuild_res_combo(self, select_idx=None):
        """Reconstruye el combo desde _res_presets_raw (INI) + hardcoded head/tail."""
        self._res_presets = self._build_full_presets()

        prev_idx = self._res_combo.currentIndex() if select_idx is None else select_idx

        self._res_combo.blockSignals(True)
        self._res_combo.clear()
        for label, preset in self._res_presets:
            if preset and preset not in ("custom", "timeline"):
                tw, th = preset
                ar = _ar_str(tw, th)
                display = ("%s  [%s]" % (label, ar)) if ar else label
            else:
                display = label
            self._res_combo.addItem(display)

        valid_idx = max(0, min(prev_idx, self._res_combo.count() - 1))
        self._res_combo.setCurrentIndex(valid_idx)
        self._res_combo.blockSignals(False)

        self._on_res_preset_changed(valid_idx)
        self._update_res_combo_labels()

    def _on_delete_preset(self, row):
        """Elimina el preset en la posición row del combo (y del INI)."""
        n_head = self._N_HEAD
        n_tail = self._N_TAIL
        n_total = len(self._res_presets)

        # Proteger hardcoded head (Original, Timeline) y tail (Custom...)
        if row < n_head or row >= n_total - n_tail:
            return

        ini_row = row - n_head  # índice en _res_presets_raw

        cur_idx = self._res_combo.currentIndex()
        if cur_idx == row:
            new_idx = max(0, row - 1)  # seleccionar el de arriba
        elif cur_idx > row:
            new_idx = cur_idx - 1
        else:
            new_idx = cur_idx

        del self._res_presets_raw[ini_row]
        settings_mod.save_res_presets(self._res_presets_raw)
        # Cerrar popup para que Qt recalcule el alto del desplegable sin filas vacías.
        self._res_combo.hidePopup()
        self._rebuild_res_combo(select_idx=new_idx)
        self._save_all_settings()

    def _on_save_preset_clicked(self):
        """Abre el diálogo de guardar preset y añade el nuevo a la lista."""
        w = self._convert_custom_w.value()
        h = self._convert_custom_h.value()
        name = settings_mod.show_save_preset_dialog(w, h, parent=self)
        if not name:
            return

        # Insertar al final de los presets INI (antes de Custom... hardcoded)
        ini_insert = len(self._res_presets_raw)
        self._res_presets_raw.append({"name": name, "w": w, "h": h})
        settings_mod.save_res_presets(self._res_presets_raw)
        # El índice en el combo = offset head + posición INI
        combo_idx = self._N_HEAD + ini_insert
        self._rebuild_res_combo(select_idx=combo_idx)
        self._save_all_settings()

    def _apply_deana_if_active(self, tw, th):
        """Multiplica el ancho por el PAR elegido si desanamorfizar está activo."""
        if (hasattr(self, "_convert_deana_chk")
                and self._convert_deana_chk.isChecked()
                and tw):
            par = float(self._convert_deana_par.currentText())
            tw  = int(round(tw * par))
        return tw, th

    def _target_compression(self, src_comp):
        return "dwaa" if self._convert_dwaa_chk.isChecked() else (src_comp or "—")

    def _target_bitdepth(self, src_bd):
        return src_bd or "—"

    def _target_channels(self, src_ch):
        sel = self._convert_channels.currentText()
        if sel == "Reducir a RGB":
            return 3
        return src_ch  # Mantener

    @staticmethod
    def _ch_str(ch):
        if isinstance(ch, int):
            if ch == 1:  return "Y"
            if ch == 3:  return "RGB"
            if ch == 4:  return "RGBA"
            return "%dch" % ch
        return "—"

    @staticmethod
    def _fmt_bd(bd):
        """Convierte 'half'→'16b', 'float'→'32b'. Resto se muestra tal cual."""
        if bd == "half":   return "16b"
        if bd == "float":  return "32b"
        return bd or "—"

    @staticmethod
    def _fmt_par(par):
        """Formatea PAR numérico para display: 1.0→'1', 2.0→'2', 1.33→'1.33'."""
        if par is None:
            return None
        v = float(par)
        return ("%d" % int(v)) if v == int(v) else ("%.4g" % v)

    def _refresh_convert_destinos(self):
        """Recalcula columnas 'Destino' y 'Estado' y las labels del combo (EXR solamente).

        Detecta automáticamente los casos de upscale bloqueado por 'no upscale':
        - Destino: muestra la resolución final (griseado si upscale bloqueado o desactivado)
        - Estado:  'Pendiente' (cian) | '⚠ Upscale' (rojo) | '—' (gris, fila desactivada)
        """
        if not hasattr(self, "_convert_table") or not hasattr(self, "_convert_rows"):
            return
        self._update_res_combo_labels()
        for row_i, item in enumerate(self._convert_rows):
            if item.get("kind") == "mov":
                continue

            # ── Fila desactivada (checkbox off) ──────────────────────────
            chk = self._convert_checkboxes.get(row_i) if hasattr(self, "_convert_checkboxes") else None
            if chk is not None and not chk.isChecked():
                self._convert_table.setCellWidget(
                    row_i, 5, _cell_html_label("<span style='color:#444444;'>—</span>")
                )
                self._convert_table.setCellWidget(
                    row_i, 7, _cell_html_label("<span style='color:#444444;'>—</span>")
                )
                continue

            sw, sh = item.get("width"), item.get("height")
            tw, th = self._current_target_res(sw, sh)

            # ¿El resize resultaría en upscale y está bloqueado?
            is_upscale_blocked = (
                self._convert_no_upscale.isChecked()
                and sw and sh and tw and th
                and (tw > sw or th > sh)
            )
            if is_upscale_blocked:
                tw, th = sw, sh  # se mantiene el original

            # Aplicar desanamorfizado DESPUÉS del check de upscale
            tw, th = self._apply_deana_if_active(tw, th)

            # ── Columna 5: Destino ────────────────────────────────────────
            dest_fg = "#555555" if is_upscale_blocked else "#a7a7a7"
            comp = self._target_compression(item.get("compression"))
            bd   = self._fmt_bd(self._target_bitdepth(item.get("bitdepth")))
            ch   = self._target_channels(item.get("channels"))
            if tw and th:
                ar = _ar_str(tw, th)
                ar_clr = "#5a4a30" if is_upscale_blocked else _CLR_AR
                if ar:
                    res_h = ("<span style='color:%s;'>%d×%d</span>"
                             " <span style='color:%s;'>(%s)</span>" % (
                                 dest_fg, tw, th, ar_clr, ar))
                else:
                    res_h = "<span style='color:%s;'>%d×%d</span>" % (dest_fg, tw, th)
            else:
                res_h = "<span style='color:%s;'>—</span>" % dest_fg
            # PAR destino: 1 si desanamorfizando, PAR fuente si no
            if hasattr(self, "_convert_deana_chk") and self._convert_deana_chk.isChecked():
                tpar_fmt = "1"
            else:
                tpar_fmt = self._fmt_par(item.get("pixel_aspect_ratio"))
            par_clr = "#5a3a3a" if is_upscale_blocked else _CLR_PAR
            tpar_h = (" <span style='color:%s;'>(%s)</span>" % (par_clr, tpar_fmt)) if tpar_fmt else ""
            comp_clr = dest_fg if is_upscale_blocked else _comp_color(comp)
            bd_h   = "<span style='color:%s;'>%s</span>" % (dest_fg, bd or "—")
            ch_h   = "<span style='color:%s;'>%s</span>" % (dest_fg, self._ch_str(ch))
            comp_h = "<span style='color:%s;'>%s</span>" % (comp_clr, comp)
            dest_html = "%s%s · %s · %s · %s" % (res_h, tpar_h, bd_h, ch_h, comp_h)
            self._convert_table.setCellWidget(row_i, 5, _cell_html_label(dest_html))

            # ── Columna 7: Estado ─────────────────────────────────────────
            if is_upscale_blocked:
                st_html = ("<span style='color:%s;'>⚠ Upscale</span>"
                           % _CLR_STATUS_UPSCALE)
            else:
                st_html = ("<span style='color:%s;'>Pendiente</span>"
                           % _CLR_STATUS_PENDING)
            self._convert_table.setCellWidget(row_i, 7, _cell_html_label(st_html))

    def _update_convert_page(self):
        # Recolectar plates chequeados (todos los items de la sección PLATES,
        # independientemente del formato; MOVs entran pero estarán deshabilitados)
        plate_items = []
        for row, chk in self._checkboxes.items():
            if not chk.isChecked():
                continue
            row_data = self._table_rows[row]
            if row_data.get("section") == "plates":
                plate_items.append(row_data["item"])

        # Poblar tabla
        self._convert_rows = plate_items
        self._convert_table.setRowCount(len(plate_items))

        self._convert_checkboxes = {}
        total_size = 0
        total_frames = 0
        for i, it in enumerate(plate_items):
            is_mov = it.get("kind") == "mov"
            dim_color = "#555555" if is_mov else "#888888"
            name_color = "#666666" if is_mov else "#cccccc"

            # Col 0: barra de color (plates)
            bar = QtWidgets.QTableWidgetItem()
            bar.setBackground(QtGui.QColor(_CLR_PLATES if not is_mov else "#444444"))
            bar.setFlags(QtCore.Qt.NoItemFlags)
            self._convert_table.setItem(i, 0, bar)

            # Col 1: checkbox (deshabilitado para MOVs)
            chk = QtWidgets.QCheckBox()
            chk.setStyleSheet("color:#a7a7a7; padding:2px;")
            if is_mov:
                chk.setChecked(False)
                chk.setEnabled(False)
                chk.setToolTip("Transcode de MOV pendiente de implementación")
            else:
                chk.setChecked(True)
            chk.stateChanged.connect(lambda *_: self._update_transcode_btn_state())
            chk.stateChanged.connect(lambda *_: self._refresh_convert_destinos())
            self._convert_checkboxes[i] = chk
            chk_container = QtWidgets.QWidget()
            cl = QtWidgets.QHBoxLayout(chk_container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(QtCore.Qt.AlignCenter)
            cl.addWidget(chk)
            self._convert_table.setCellWidget(i, 1, chk_container)

            # Col 2: Nombre
            name_item = QtWidgets.QTableWidgetItem(it.get("name", ""))
            name_item.setForeground(QtGui.QColor(name_color))
            if is_mov:
                name_item.setToolTip("Transcode de MOV pendiente de implementación")
            self._convert_table.setItem(i, 2, name_item)

            # Col 3: Origen "WxH [AR] · bd · Nch · comp · #f - Xs"
            sw, sh = it.get("width"), it.get("height")
            sc = it.get("compression") or "—"
            sbd = self._fmt_bd(it.get("bitdepth"))
            sch = it.get("channels")
            fc = it.get("frame_count") or 0
            fps_val = it.get("fps")
            if not is_mov:
                total_frames += fc
            # resolución con AR coloreado
            if sw and sh:
                ar = _ar_str(sw, sh)
                ar_clr = "#555555" if is_mov else _CLR_AR
                if ar:
                    res_h = ("<span style='color:%s;'>%d×%d</span>"
                             " <span style='color:%s;'>(%s)</span>" % (
                                 dim_color, sw, sh, ar_clr, ar))
                else:
                    res_h = "<span style='color:%s;'>%d×%d</span>" % (dim_color, sw, sh)
            else:
                res_h = "<span style='color:%s;'>—</span>" % dim_color
            # PAR en rosa (solo si está disponible)
            spar = self._fmt_par(it.get("pixel_aspect_ratio"))
            par_clr = "#555555" if is_mov else _CLR_PAR
            par_h = (" <span style='color:%s;'>(%s)</span>" % (par_clr, spar)) if spar else ""
            # compresión coloreada
            sc_clr = _comp_color(sc, greyed=is_mov)
            sc_h = "<span style='color:%s;'>%s</span>" % (sc_clr, sc)
            # frames con segundos coloreados
            fc_clr = "#555555" if is_mov else _CLR_FRAMES
            secs_txt = (" - %.1fs" % (fc / float(fps_val))) if fps_val and fc else ""
            fc_h = "<span style='color:%s;'>%df%s</span>" % (fc_clr, fc, secs_txt)
            bd_h = "<span style='color:%s;'>%s</span>" % (dim_color, sbd)
            ch_h = "<span style='color:%s;'>%s</span>" % (dim_color, self._ch_str(sch))
            origen_html = "%s%s · %s · %s · %s · %s" % (res_h, par_h, bd_h, ch_h, sc_h, fc_h)
            self._convert_table.setCellWidget(i, 3, _cell_html_label(origen_html))

            # Col 4: flecha
            arrow = QtWidgets.QTableWidgetItem("→")
            arrow.setForeground(QtGui.QColor("#444444" if is_mov else "#666666"))
            arrow.setTextAlignment(QtCore.Qt.AlignCenter)
            self._convert_table.setItem(i, 4, arrow)

            # Col 5: Destino — placeholder; se completa en _refresh_convert_destinos
            if is_mov:
                self._convert_table.setCellWidget(
                    i, 5, _cell_html_label("<span style='color:#555555;'>—</span>"))
            else:
                self._convert_table.setItem(i, 5, QtWidgets.QTableWidgetItem(""))

            # Col 6: Tamaño actual
            size_b = _folder_size_bytes(it.get("path", ""))
            if not is_mov:
                total_size += size_b
            s_item = QtWidgets.QTableWidgetItem(_format_bytes(size_b))
            s_item.setForeground(QtGui.QColor(dim_color))
            s_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self._convert_table.setItem(i, 6, s_item)

            # Col 7: Estado inicial (se reescribe en _refresh_convert_destinos para EXR)
            if is_mov:
                st_html = "<span style='color:#555555;'>No soportado</span>"
            else:
                st_html = "<span style='color:%s;'>Pendiente</span>" % _CLR_STATUS_PENDING
            self._convert_table.setCellWidget(i, 7, _cell_html_label(st_html))

        self._refresh_convert_destinos()

        # Resumen
        if plate_items:
            self._convert_summary_lbl.setText(
                "%d plate%s · %d frames · %s en disco" % (
                    len(plate_items), "" if len(plate_items) == 1 else "s",
                    total_frames, _format_bytes(total_size),
                )
            )
        else:
            self._convert_summary_lbl.setText("No hay plates seleccionados.")

        self._update_transcode_btn_state()

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
    #  Transcode — estado del botón y ejecución
    # ══════════════════════════════════════════════════════════

    def _update_transcode_btn_state(self):
        """Habilita Start Transcode si hay al menos un EXR habilitado y chequeado."""
        if not hasattr(self, "_convert_checkboxes") or not hasattr(self, "_start_transcode_btn"):
            return
        has_exr = any(
            chk.isChecked() and chk.isEnabled()
            for chk in self._convert_checkboxes.values()
        )
        self._start_transcode_btn.setEnabled(has_exr)
        self._start_transcode_btn.setToolTip(
            "" if has_exr else "Selecciona al menos un EXR"
        )

    def _run_transcode(self):
        """Handler del botón Start Transcode.

        Inicializa la cola de secuencias y arranca la primera.
        Las siguientes se procesan una a una en _start_next_sequence(),
        que se llama al finalizar cada worker.
        """
        if not hasattr(self, "_convert_checkboxes") or not hasattr(self, "_convert_rows"):
            return

        # Recolectar secuencias EXR con checkbox activo
        job_sequences = []
        for row_i, chk in self._convert_checkboxes.items():
            if not chk.isChecked() or not chk.isEnabled():
                continue
            item = self._convert_rows[row_i]
            tw, th = self._current_target_res(item.get("width"), item.get("height"))
            sw, sh = item.get("width"), item.get("height")
            if self._convert_no_upscale.isChecked() and sw and sh and tw and th:
                if tw > sw or th > sh:
                    tw, th = sw, sh
            # Aplicar desanamorfizado DESPUÉS del check de upscale
            tw, th = self._apply_deana_if_active(tw, th)
            job_sequences.append((row_i, item, tw, th))

        if not job_sequences:
            return

        # Guardar estado compartido para toda la cola
        self._sequence_queue       = list(job_sequences)
        self._transcode_results_all = []
        self._transcode_flags = {
            "test_mode":        Transcode_TEST_Mode,
            "move_originals":   not Transcode_TEST_Mode,  # siempre True en modo normal
            "delete_originals": self._delete_originals_chk.isChecked(),
        }
        _deana_active = (hasattr(self, "_convert_deana_chk")
                         and self._convert_deana_chk.isChecked())
        self._transcode_global_opts = {
            "compression":        self._target_compression(None),
            "dwa_level":          self._convert_dwaa_level.value(),
            "resize_filter":      self._convert_filter.currentText(),
            "workers":            6,
            "channels":           ("rgb" if self._convert_channels.currentText() == "Reducir a RGB"
                                   else "all"),
            "pixel_aspect_ratio": 1.0 if _deana_active else None,
        }

        # Deshabilitar botones mientras hay trabajo en curso
        self._start_transcode_btn.setEnabled(False)
        self._go_back_btn.setEnabled(False)
        self._convert_log.clear()

        self._start_next_sequence()

    def _start_next_sequence(self):
        """Saca la siguiente secuencia de la cola, la verifica y lanza su worker.

        - Si hay conflicto de archivos: muestra el diálogo de warning.
          Si el usuario cancela esa secuencia, pasa a la siguiente.
          Si confirma, borra los EXR existentes antes de empezar.
        - Cuando la cola se vacía, llama a _finalize_transcode().
        """
        flags = self._transcode_flags
        while self._sequence_queue:
            row_i, item, tw, th = self._sequence_queue.pop(0)
            has_conflict, conflict_desc = check_existing_outputs(
                item, flags["test_mode"], flags["move_originals"]
            )
            if has_conflict:
                seq_name = item.get("name") or Path(item["path"]).name
                proceed  = show_overwrite_warning(seq_name, conflict_desc, parent=self)
                if not proceed:
                    continue  # saltar esta secuencia, probar la siguiente
                delete_existing_outputs(
                    item, flags["test_mode"], flags["move_originals"]
                )

            # Lanzar worker para esta única secuencia
            worker = TranscodeWorker(
                [(row_i, item, tw, th)],
                self._transcode_global_opts,
                test_mode        = flags["test_mode"],
                move_originals   = flags["move_originals"],
                delete_originals = flags["delete_originals"],
                shared_dir       = str(SHARED_DIR),
            )
            worker.signals.log_message.connect(self._on_transcode_log)
            worker.signals.sequence_started.connect(self._on_sequence_started)
            worker.signals.sequence_done.connect(self._on_sequence_done)
            worker.signals.all_done.connect(self._on_worker_batch_done)
            worker.signals.error.connect(self._on_transcode_error)
            QtCore.QThreadPool.globalInstance().start(worker)
            debug_print("TranscodeWorker iniciado — secuencia %d" % row_i)
            return  # esperar a que termine antes de continuar con la cola

        # Cola vacía: todas las secuencias se procesaron (o se cancelaron)
        self._finalize_transcode()

    # ── Handlers de señales del worker ─────────────────────────

    def _on_transcode_log(self, msg):
        """Agrega una línea al panel de log de transcode."""
        self._convert_log.appendPlainText(msg)

    # Estilo de la barra de progreso de transcode
    _PBAR_STYLE = """
        QProgressBar {
            background-color: #393959;
            border: none;
            border-radius: 5px;
            text-align: center;
            color: #cccccc;
            font-size: 9px;
            min-height: 16px;
            max-height: 22px;
        }
        QProgressBar::chunk {
            background-color: #443a91;
            border-radius: 5px;
        }
    """

    def _on_sequence_started(self, row_i, dst_dir_str, total_frames):
        """Crea barra de progreso en la columna Estado e inicia polling QTimer."""
        if row_i >= self._convert_table.rowCount():
            return

        pbar = QtWidgets.QProgressBar()
        pbar.setRange(0, max(total_frames, 1))
        pbar.setValue(0)
        pbar.setFormat("%v/%m")
        pbar.setStyleSheet(self._PBAR_STYLE)
        self._convert_table.setCellWidget(row_i, 7, pbar)

        # Inicializar dicts de timers/pbars si no existen
        if not hasattr(self, "_transcode_timers"):
            self._transcode_timers = {}
        if not hasattr(self, "_transcode_pbars"):
            self._transcode_pbars = {}

        dst_dir = Path(dst_dir_str)
        self._transcode_pbars[row_i] = pbar

        timer = QtCore.QTimer()
        timer.setInterval(300)
        timer.timeout.connect(
            lambda: self._poll_transcode_progress(row_i, dst_dir, total_frames, pbar)
        )
        self._transcode_timers[row_i] = timer
        timer.start()

    def _poll_transcode_progress(self, row_i, dst_dir, total_frames, pbar):
        """Cuenta archivos .exr en dst_dir y actualiza la barra de progreso."""
        if not dst_dir.exists():
            return
        try:
            done = sum(1 for _ in dst_dir.glob("*.exr"))
            pbar.setValue(min(done, total_frames))
        except Exception:
            pass

    def _on_sequence_done(self, row_i, ok, stats):
        """Detiene el timer de progreso y actualiza el Estado a '✓ Listo' o '✗ Error'."""
        # Detener y eliminar timer
        if hasattr(self, "_transcode_timers") and row_i in self._transcode_timers:
            self._transcode_timers[row_i].stop()
            del self._transcode_timers[row_i]
        if hasattr(self, "_transcode_pbars"):
            self._transcode_pbars.pop(row_i, None)

        if row_i < self._convert_table.rowCount():
            if ok:
                html = "<span style='color:%s;'>✓ Listo</span>" % _CLR_STATUS_DONE
            else:
                html = "<span style='color:%s;'>✗ Error</span>" % _CLR_STATUS_ERROR
            self._convert_table.setCellWidget(row_i, 7, _cell_html_label(html))

    def _on_worker_batch_done(self, results):
        """El worker de una secuencia terminó. Acumula resultados y arranca la siguiente."""
        self._transcode_results_all.extend(results)
        self._start_next_sequence()

    def _finalize_transcode(self):
        """Se llama cuando la cola queda vacía. Muestra resumen y re-habilita botones."""
        results  = self._transcode_results_all
        total    = len(results)
        ok_count = sum(1 for r in results if r.get("ok"))
        if total == 0:
            summary = "⚠ Todas las secuencias fueron canceladas"
        elif ok_count == total:
            summary = "✓ Transcode completo: %d/%d OK" % (ok_count, total)
        else:
            summary = "⚠ Transcode: %d/%d OK, %d con errores" % (
                ok_count, total, total - ok_count
            )
        self._on_transcode_log(summary)
        self._start_transcode_btn.setEnabled(True)
        self._go_back_btn.setEnabled(True)
        self._transcode_happened = True  # para triggerar refresh al volver a PAGE_MEDIA
        debug_print("Transcode all_done — %d/%d OK" % (ok_count, total))

    def _on_transcode_error(self, msg):
        """Error fatal en el worker: vacía la cola, re-habilita botones."""
        self._on_transcode_log("ERROR FATAL: " + msg)
        debug_print("Transcode error fatal: %s" % msg, level="error")
        if hasattr(self, "_sequence_queue"):
            self._sequence_queue.clear()
        self._finalize_transcode()

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
