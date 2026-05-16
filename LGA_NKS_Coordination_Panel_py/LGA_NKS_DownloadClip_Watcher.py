"""
____________________________________________________________________

  LGA_NKS_DownloadClip_Watcher v1.01 | Lega

  Watcher de finalizacion de descargas del boton "Download Clip"
  (LGA_NKS_FileManager_DownloadClip.py).

  Lo arranca el Coordination Panel (LGA_NKS_Coordination_Panel.py) al
  cargarse en el arranque de Hiero. Cada pocos segundos revisa la carpeta
  de marcadores (logs/download_clip_done/) donde FileManager escribe un
  .json al terminar cada descarga CLI lanzada con --notify-completion.
  Cuando aparece un marcador, busca el/los clip(s) cuyo media coincide
  con la ruta descargada y los reconecta automaticamente.

  Diseno:
  - Corre en el hilo principal de Hiero via QTimer (la reconexion toca
    la API de Hiero y debe ejecutarse en el main thread). No bloquea: el
    callback es trabajo de milisegundos.
  - Es stateless entre ticks: solo reacciona a marcadores que aparecen.
    Si una descarga se cancela, FileManager se cierra o crashea, no se
    escribe marcador y el watcher simplemente sigue idle.
  - Cada marcador se borra siempre tras procesarlo (haya match o no).
  - Marcadores sin clip que matchee se reintentan hasta un TTL y luego
    se descartan, para evitar huerfanos eternos.
____________________________________________________________________
"""

import os
import sys
import json
import glob
import time
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
import traceback

# Intervalo de sondeo de la carpeta de marcadores
POLL_INTERVAL_MS = 5000
# Tiempo maximo que se conserva un marcador sin clip que matchee
MARKER_TTL_SECONDS = 1800  # 30 min

# Variables globales de logging
DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True
script_start_time = None
debug_log_listener = None
debug_logger = None

# Importar QtCore (mismo adaptador que usan los paneles)
QtCore = None
try:
    # La raiz Startup es el padre de la carpeta de este script
    _startup_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _startup_dir not in sys.path:
        sys.path.insert(0, _startup_dir)
    from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtCore  # type: ignore
except Exception as _qt_err:
    try:
        from PySide6 import QtCore  # type: ignore
    except Exception:
        try:
            from PySide2 import QtCore  # type: ignore
        except Exception:
            print(f"[DownloadClipWatcher] No se pudo importar QtCore: {_qt_err}")


class RelativeTimeFormatter(logging.Formatter):
    """Formatter que incluye tiempo relativo desde el inicio del script."""

    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="DownloadClipWatcher"):
    """Configura el logging para escribir SOLO en archivo (limpieza por ejecucion)."""
    global debug_log_listener

    log_filename = f"debugPy_{script_name}.log"
    log_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "logs", log_filename
    )
    log_file_path = os.path.abspath(log_file_path)
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"[DownloadClipWatcher] Warning: no se pudo limpiar el log: {e}")

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


try:
    debug_logger = setup_debug_logging(script_name="DownloadClipWatcher")
except Exception as _e:
    print(f"[DownloadClipWatcher] FALLO al inicializar logger: {_e}")


def debug_print(*message, level="info"):
    global script_start_time

    msg = " ".join(str(arg) for arg in message)

    if DEBUG and DEBUG_LOG and debug_logger is not None:
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


def get_marker_dir():
    """Carpeta vigilada donde FileManager escribe los marcadores de finalizacion.

    Debe coincidir con get_notify_dir() de LGA_NKS_FileManager_DownloadClip.py.
    """
    marker_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "logs", "download_clip_done"
    )
    return os.path.abspath(marker_dir)


def _normalize_path(path):
    """Normaliza una ruta para comparar (Windows es case-insensitive)."""
    norm = os.path.normpath(str(path)).replace("\\", "/").lower()
    return norm.rstrip("/")


def _safe_remove(path):
    try:
        os.remove(path)
    except Exception as e:
        debug_print(f"No se pudo borrar el marcador {path}: {e}", level="warning")


def _iter_all_track_items():
    """Itera todos los track items de todas las secuencias abiertas en Hiero."""
    try:
        import hiero.core
    except Exception as e:
        debug_print(f"hiero.core no disponible: {e}", level="error")
        return

    sequences = []
    try:
        for project in hiero.core.projects():
            try:
                sequences.extend(project.sequences())
            except Exception:
                pass
    except Exception as e:
        debug_print(f"No se pudieron listar proyectos: {e}", level="warning")

    if not sequences:
        try:
            import hiero.ui

            active = hiero.ui.activeSequence()
            if active:
                sequences = [active]
        except Exception:
            pass

    for seq in sequences:
        try:
            for track in seq.videoTracks():
                for item in track.items():
                    yield item
        except Exception:
            continue


def _reconnect_clip(item):
    """Reconecta el media de un track item (reconnectMedia con fallback refresh)."""
    try:
        clip_name = item.name()
    except Exception:
        clip_name = "<sin nombre>"

    try:
        source = item.source()
        media_source = source.mediaSource()
        was_online = media_source.isMediaPresent()
    except Exception as e:
        debug_print(f"No se pudo acceder al media de '{clip_name}': {e}", level="error")
        return False

    try:
        source.reconnectMedia()
        debug_print(f"reconnectMedia ejecutado para: {clip_name}")
    except Exception as reconnect_error:
        debug_print(
            f"reconnectMedia fallo ({reconnect_error}), intentando refresh",
            level="warning",
        )
        try:
            media_source.refresh()
            debug_print(f"refresh ejecutado como fallback para: {clip_name}")
        except Exception as refresh_error:
            debug_print(f"refresh tambien fallo: {refresh_error}", level="error")

    try:
        now_online = item.source().mediaSource().isMediaPresent()
    except Exception:
        now_online = False

    debug_print(f"Clip '{clip_name}': online {was_online} -> {now_online}")
    return True


def _find_and_reconnect(target_path, kind):
    """Busca y reconecta los clips cuyo media coincide con target_path.

    kind == 'file'   -> match exacto contra la ruta del media.
    kind == 'folder' -> match contra el dirname del media (secuencia).
    Devuelve la cantidad de clips encontrados (procesados).
    """
    target_norm = _normalize_path(target_path)
    matched = 0

    try:
        import hiero.core
    except Exception:
        hiero = None

    for item in _iter_all_track_items():
        try:
            if hiero is not None and isinstance(item, hiero.core.EffectTrackItem):
                continue
        except Exception:
            pass

        try:
            media_source = item.source().mediaSource()
            fileinfos = media_source.fileinfos()
            if not fileinfos:
                continue
            clip_path = fileinfos[0].filename()
        except Exception:
            continue

        if kind == "folder":
            clip_key = _normalize_path(os.path.dirname(clip_path))
        else:
            clip_key = _normalize_path(clip_path)

        if clip_key == target_norm:
            try:
                item_name = item.name()
            except Exception:
                item_name = "?"
            debug_print(f"Match ({kind}): clip '{item_name}' <- {target_path}")
            _reconnect_clip(item)
            matched += 1

    return matched


def _process_marker(marker_path):
    """Procesa un marcador .json: reconecta los clips y/o borra el marcador."""
    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        debug_print(
            f"Marcador corrupto, se descarta: {marker_path} ({e})", level="error"
        )
        _safe_remove(marker_path)
        return

    task_id = data.get("task_id", "?")
    success = bool(data.get("success", False))
    items = data.get("items", []) or []

    if not success:
        debug_print(
            f"Descarga fallida (task {task_id}): no se reconecta. Marcador descartado.",
            level="warning",
        )
        _safe_remove(marker_path)
        return

    total_matched = 0
    for entry in items:
        path = entry.get("path")
        kind = entry.get("kind", "file")
        if not path:
            continue
        total_matched += _find_and_reconnect(path, kind)

    if total_matched > 0:
        debug_print(
            f"Marcador {task_id} procesado: {total_matched} clip(s) reconectado(s). Se borra."
        )
        _safe_remove(marker_path)
        return

    # No se encontro ningun clip que matchee: reintentar hasta el TTL
    try:
        age = time.time() - os.path.getmtime(marker_path)
    except Exception:
        age = MARKER_TTL_SECONDS + 1

    if age > MARKER_TTL_SECONDS:
        debug_print(
            f"Marcador {task_id} sin clip que matchee y vencido ({age:.0f}s). Se descarta.",
            level="warning",
        )
        _safe_remove(marker_path)
    else:
        debug_print(
            f"Marcador {task_id}: sin clip que matchee aun, se reintentara (edad {age:.0f}s)"
        )


def _scan_markers():
    """Escanea la carpeta de marcadores y procesa los .json presentes."""
    marker_dir = get_marker_dir()
    if not os.path.isdir(marker_dir):
        return

    markers = glob.glob(os.path.join(marker_dir, "*.json"))
    for marker_path in markers:
        try:
            _process_marker(marker_path)
        except Exception as e:
            debug_print(
                f"Error procesando marcador {marker_path}: {e}", level="error"
            )
            debug_print(traceback.format_exc(), level="error")


if QtCore is not None:

    class DownloadClipWatcher(QtCore.QObject):
        """QObject con un QTimer que vigila la carpeta de marcadores."""

        def __init__(self):
            super(DownloadClipWatcher, self).__init__()
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(POLL_INTERVAL_MS)
            self._timer.timeout.connect(self._on_tick)
            self._timer.start()
            debug_print(
                f"=== DownloadClip Watcher iniciado (cada {POLL_INTERVAL_MS} ms) ==="
            )
            debug_print(f"Vigilando: {get_marker_dir()}")

        def _on_tick(self):
            try:
                _scan_markers()
            except Exception as e:
                debug_print(f"Error en tick del watcher: {e}", level="error")
                debug_print(traceback.format_exc(), level="error")


# Instancia global del watcher (referencia para evitar garbage collection)
_watcher_instance = None


def start_watcher():
    """Inicia el watcher si aun no esta corriendo."""
    global _watcher_instance
    if QtCore is None:
        print("[DownloadClipWatcher] QtCore no disponible, watcher no iniciado")
        return
    if _watcher_instance is None:
        _watcher_instance = DownloadClipWatcher()


# Al cargarse el modulo, arrancar el watcher automaticamente.
try:
    start_watcher()
except Exception as _e:
    print(f"[DownloadClipWatcher] No se pudo iniciar el watcher: {_e}")
    traceback.print_exc()
