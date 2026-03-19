"""
____________________________________________________________________________________

  LGA_NKS_ProjectsPanel_Logging v1.01 | Lega
  Helper de logging compartido para el Projects Panel.

  v1.01: Agregado reset del log por cambio de timeline y setup compartido para scripts del panel
  v1.00: Helper inicial de logging asincrono a archivo para Projects Panel
____________________________________________________________________________________
"""

import atexit
import logging
import os
import queue
import threading
import time
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

DEBUG = True
DEBUG_CONSOLE = False
DEBUG_LOG = True

script_start_time = None
debug_log_listener = None
current_script_name = "ProjectsPanel"
debug_logger = None
debug_queue_handler = None
debug_file_handler = None
debug_logger_name = None
_logging_lock = threading.RLock()


class RelativeTimeFormatter(logging.Formatter):
    """Formatter que incluye tiempo relativo desde el inicio del script."""

    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created
        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)


def setup_debug_logging(script_name="ProjectsPanel"):
    """Configura el logging asincrono para escribir solo en archivo."""
    global current_script_name, debug_log_listener, debug_logger
    global debug_queue_handler, debug_file_handler, debug_logger_name

    with _logging_lock:
        current_script_name = script_name
        log_filename = f"DebugPy_{script_name}.log"
        log_file_path = Path(__file__).resolve().parent.parent / "logs" / log_filename
        os.makedirs(log_file_path.parent, exist_ok=True)

        try:
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                log_file.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception:
            pass

        debug_logger_name = f"{script_name.lower()}_logger"
        logger = logging.getLogger(debug_logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            logger.handlers.clear()

        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(RelativeTimeFormatter("[%(relative_time)s] %(message)s"))

        log_queue = queue.Queue()
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)

        debug_log_listener = QueueListener(
            log_queue, file_handler, respect_handler_level=True
        )
        debug_log_listener.daemon = True
        debug_log_listener.start()

        debug_logger = logger
        debug_queue_handler = queue_handler
        debug_file_handler = file_handler
        return logger


debug_logger = setup_debug_logging(script_name="ProjectsPanel")


def debug_print(*message, level="info"):
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


def print_debug_messages():
    """Compatibilidad con la interfaz anterior del panel."""
    return None


def reset_debug_log():
    """Reinicia el archivo de log y el contador relativo para una nueva sesion."""
    global script_start_time
    with _logging_lock:
        script_start_time = None
        cleanup_logging()
        return setup_debug_logging(script_name=current_script_name)


def cleanup_logging():
    global debug_log_listener, debug_logger, debug_queue_handler, debug_file_handler
    with _logging_lock:
        if debug_log_listener:
            try:
                debug_log_listener.stop()
            except Exception:
                pass
            debug_log_listener = None

        if debug_logger and debug_queue_handler:
            try:
                debug_logger.removeHandler(debug_queue_handler)
            except Exception:
                pass

        if debug_queue_handler:
            try:
                debug_queue_handler.close()
            except Exception:
                pass
            debug_queue_handler = None

        if debug_file_handler:
            try:
                debug_file_handler.flush()
            except Exception:
                pass
            try:
                debug_file_handler.close()
            except Exception:
                pass
            debug_file_handler = None


atexit.register(cleanup_logging)
