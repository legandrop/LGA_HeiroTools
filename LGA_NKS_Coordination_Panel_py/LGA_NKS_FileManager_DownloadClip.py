"""
____________________________________________________________________

  LGA_NKS_FileManager_DownloadClip v0.02 | Lega

  Descarga un clip individual (secuencia de imagenes o archivo de video)
  desde Wasabi S3 usando FileManager CLI.

  v0.02: Usa el Método 1 (selección pura de clips, sin playhead).
         Soporta uno o varios clips seleccionados a la vez.

  v0.01: Solo imprime via debug_print:
        - Nombre del clip
        - Ruta del clip
        - Estado online/offline del media
____________________________________________________________________
"""

from pathlib import Path
import sys
import os
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
import datetime
import time
import traceback

# Variables globales de logging
DEBUG = True
DEBUG_CONSOLE = True
DEBUG_LOG = True
script_start_time = None
debug_log_listener = None
debug_logger = None
_log_file_path_resolved = None


class RelativeTimeFormatter(logging.Formatter):
    """Formatter con hora absoluta y tiempo relativo desde el inicio."""

    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created

        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="FileManager_DownloadClip"):
    """Configura el logging para escribir SOLO en archivo (limpieza diaria)."""
    global debug_log_listener, _log_file_path_resolved

    log_filename = f"debugPy_{script_name}.log"
    log_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "logs", log_filename
    )
    log_file_path = os.path.abspath(log_file_path)
    _log_file_path_resolved = log_file_path

    print(f"[DownloadClip] log target: {log_file_path}")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    today_str = datetime.date.today().isoformat()
    should_reset = True
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            should_reset = first_line != f"Fecha: {today_str}"
        except Exception:
            should_reset = True

    if should_reset:
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"Fecha: {today_str}\n")
        except Exception as e:
            print(f"[DownloadClip] Warning: no se pudo resetear el log: {e}")

    logger_name = f"{script_name.lower()}_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = RelativeTimeFormatter(
        "[%(asctime)s] [%(relative_time)s] %(message)s", datefmt="%H:%M:%S"
    )
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


# Setup del logger con captura de cualquier fallo
try:
    debug_logger = setup_debug_logging(script_name="FileManager_DownloadClip")
    print("[DownloadClip] logger inicializado OK")
except Exception as _e:
    print(f"[DownloadClip] FALLO al inicializar logger: {_e}")
    traceback.print_exc()


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


def _get_selected_clips():
    """Obtiene los clips realmente seleccionados en el timeline (uno o varios).

    Usa el Metodo 1 (seleccion pura, sin playhead, sin filtro de track) via el
    helper compartido get_selected_clips(). Cae a seleccion directa si falla.
    """
    try:
        utils_path = Path(__file__).parent.parent / "LGA_NKS_Shared"
        if utils_path.exists() and str(utils_path) not in sys.path:
            sys.path.insert(0, str(utils_path))
        from LGA_NKS_Shared.LGA_NKS_GetClip import get_selected_clips
        return get_selected_clips()
    except Exception as e:
        debug_print(
            f"Fallback: no se pudo usar get_selected_clips: {e}", level="warning"
        )

    # Fallback: tomar la seleccion directamente del timeline
    try:
        import hiero.ui
        import hiero.core

        seq = hiero.ui.activeSequence()
        if seq is None:
            debug_print("No hay secuencia activa", level="warning")
            return []
        te = hiero.ui.getTimelineEditor(seq)
        sel = te.selection() if te else []
        return [
            item
            for item in sel
            if not isinstance(item, hiero.core.EffectTrackItem)
        ]
    except Exception as e:
        debug_print(f"Fallback de seleccion fallo: {e}", level="error")
    return []


def _report_clip(clip, index, total):
    """Imprime nombre, ruta y estado online/offline de un clip."""
    debug_print(f"--- Clip {index}/{total} ---")

    try:
        clip_name = clip.name()
    except Exception as e:
        clip_name = f"<error: {e}>"
    debug_print(f"Nombre del clip: {clip_name}")

    try:
        media_source = clip.source().mediaSource()
    except Exception as e:
        debug_print(f"No se pudo obtener mediaSource: {e}", level="error")
        return

    try:
        fileinfos = media_source.fileinfos()
    except Exception as e:
        fileinfos = None
        debug_print(f"No se pudieron obtener fileinfos: {e}", level="error")

    if fileinfos:
        try:
            file_path = fileinfos[0].filename()
            debug_print(f"Ruta del clip: {file_path}")
        except Exception as e:
            debug_print(f"No se pudo leer filename(): {e}", level="error")
    else:
        debug_print("fileinfos vacio", level="warning")

    try:
        is_present = media_source.isMediaPresent()
        estado = "ONLINE" if is_present else "OFFLINE"
        debug_print(f"Estado del media: {estado}")
    except Exception as e:
        debug_print(
            f"No se pudo determinar estado online/offline: {e}", level="warning"
        )


def main():
    """Imprime nombre, ruta y estado online/offline de los clips seleccionados."""
    debug_print("=== FILEMANAGER DOWNLOAD CLIP ===")
    debug_print(f"log file: {_log_file_path_resolved}")

    try:
        clips = _get_selected_clips()

        if not clips:
            debug_print(
                "No hay clips seleccionados en el timeline", level="warning"
            )
            return

        total = len(clips)
        debug_print(f"Clips seleccionados: {total}")

        for index, clip in enumerate(clips, start=1):
            _report_clip(clip, index, total)

    except Exception as e:
        debug_print(f"Error al procesar los clips: {e}", level="error")
        debug_print(traceback.format_exc(), level="error")


if __name__ == "__main__":
    main()
