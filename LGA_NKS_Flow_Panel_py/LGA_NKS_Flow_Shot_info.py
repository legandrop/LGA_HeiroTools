"""
__________________________________________________________________

  LGA_NKS_Flow_Shot_info v1.87 | Lega
  Imprime informacion del shot y las versiones de la task seleccionada
  (comp, roto o cleanup) en el playhead.

  v1.87: Filtra notas auto-generadas por PipeSync al subir una version.
         Cuando el usuario sube una version desde PipeSync, se crea un
         comentario con el mismo contenido que la descripcion de la version,
         por el mismo usuario y unos segundos despues. Ese comentario duplicado
         ahora se descarta (umbral configurable, default 120s).
  v1.86: Soporte multi-task. Si el playhead atraviesa clips de varias tasks
         (TASK_EXR_TRACKS), muestra el popover compartido `LGA_NKS_TaskSelectionDialog`
         para que el usuario elija. Antes pedía siempre la task 'comp', así que
         nunca mostraba descripción/notas de roto o cleanup.
  v1.85: Actualizado para usar las clases del adapter para compatibilidad PySide2/6
  
  V1.84: Actualizado para ser compatible con ambos sistemas de nomenclatura:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)
__________________________________________________________________

"""

import hiero.core
import hiero.ui
import os
import re
import json
import sys
import sqlite3
import subprocess
import platform
import logging
import queue
import time
import importlib
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
# Importar compatibilidad Qt para Hiero Panels
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, QShortcut, QApplication

# Usar directamente las clases del adapter (ya manejan compatibilidad PySide2/6)
QCoreApplication = QApplication  # Para compatibilidad
Qt = QtCore.Qt
QSize = QtCore.QSize
Signal = QtCore.Signal
QFontMetrics = QtGui.QFontMetrics
QKeySequence = QtGui.QKeySequence
QPixmap = QtGui.QPixmap
QCursor = QtGui.QCursor
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QTextEdit = QtWidgets.QTextEdit
QScrollArea = QtWidgets.QScrollArea
QLabel = QtWidgets.QLabel
QFrame = QtWidgets.QFrame

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


def setup_debug_logging(script_name="FlowShotInfo"):
    """Configura el logging para escribir solo en archivo."""
    global debug_log_listener

    log_filename = f"DebugPy_{script_name}.log"
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", log_filename)
    log_file_path = os.path.normpath(log_file_path)

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    try:
        with open(log_file_path, "w", encoding="utf-8") as handle:
            handle.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
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


debug_logger = setup_debug_logging(script_name="FlowShotInfo")


def debug_print(*message, level="info"):
    """Loggea por defecto a archivo y opcionalmente a consola."""
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

# Importar utilidades de naming desde shareds de dominio Flow
flow_shared_dir = Path(__file__).parent.parent / "LGA_NKS_Shared"
sys.path.append(str(flow_shared_dir))
from LGA_NKS_Flow_NamingUtils import (
    extract_shot_code,
    extract_project_name,
    clean_base_name,
)

# Importar módulo utilitario para obtener clips
utils_path = Path(__file__).parent.parent / "LGA_NKS_Shared"
HAS_CLIP_UTILS = False
if utils_path.exists():
    try:
        sys.path.insert(0, str(utils_path))
        from LGA_NKS_Shared.LGA_NKS_GetClip import get_clip_to_process, get_selected_clips
        from LGA_NKS_Shared import LGA_NKS_GetClip as clip_utils
        from LGA_NKS_Shared.LGA_NKS_TaskSelectionDialog import (
            resolve_task_at_playhead,
            track_for_task,
        )
        HAS_CLIP_UTILS = True
    except ImportError as e:
        debug_print(f"Error importando módulo LGA_NKS_GetClip: {e}")


# Umbral (en segundos) para considerar que una nota fue auto-generada al subir
# una version desde PipeSync. Si la nota tiene mismo autor y mismo contenido
# que la descripcion de la version, y se creo dentro de este umbral, se descarta.
VERSION_DUPLICATE_NOTE_WINDOW_SECONDS = 600


def _parse_pipesync_datetime(value):
    """Parsea el formato de fecha de pipesync.db ('YYYY-MM-DD HH:MM:SS[+/-HH:MM]').

    Retorna un datetime con tzinfo o None si no se puede parsear.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    # SQLite suele guardar 'YYYY-MM-DD HH:MM:SS-03:00'. fromisoformat necesita 'T'.
    iso = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        try:
            dt = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_version_upload_duplicate_note(note, version_description, version_created_by, version_created_on):
    """Detecta si una nota es la auto-generada por PipeSync al subir la version.

    Se considera duplicada cuando:
    - Mismo autor que la version.
    - Contenido (trim) igual a la descripcion de la version.
    - Fecha dentro de VERSION_DUPLICATE_NOTE_WINDOW_SECONDS respecto de la version.
    """
    note_user = (note["created_by"] or "").strip()
    version_user = (version_created_by or "").strip()
    if not note_user or note_user != version_user:
        return False

    note_text = (note["content"] or "").strip()
    desc_text = (version_description or "").strip()
    if not note_text or not desc_text or note_text != desc_text:
        return False

    note_dt = _parse_pipesync_datetime(note["created_on"])
    version_dt = _parse_pipesync_datetime(version_created_on)
    if not note_dt or not version_dt:
        # Si falta fecha pero coinciden autor y contenido, lo tratamos como duplicado.
        return True

    delta = abs((note_dt - version_dt).total_seconds())
    return delta <= VERSION_DUPLICATE_NOTE_WINDOW_SECONDS


def extract_frame_from_filename(filename):
    """
    Extrae el numero de frame de un nombre de archivo de attachment.
    Los archivos siguen el patron: {shot_name}_{task_name}_v{version_number}_{frame_number}[_{counter}].{extension}
    Retorna el numero de frame o "---" si no encuentra
    """
    try:
        # Obtener solo el nombre sin extension
        name_without_ext = os.path.splitext(os.path.basename(filename))[0]
        debug_print(f"Extrayendo frame de: {name_without_ext}")

        # Separar por guiones bajos
        parts = name_without_ext.split("_")

        # Patron 1: Buscar despues de v{numero} debe venir el frame
        for i, part in enumerate(parts):
            if part.lower().startswith("v") and len(part) > 1 and part[1:].isdigit():
                # Encontramos la version, el siguiente elemento deberia ser el frame
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    frame_number = parts[i + 1]
                    debug_print(f"Frame encontrado (patron v_frame): {frame_number}")
                    return frame_number

        # Patron 2: Buscar cualquier parte que sea solo numeros y tenga 2-4 digitos (frame range tipico)
        for part in parts:
            if part.isdigit() and 2 <= len(part) <= 4:
                debug_print(f"Frame encontrado (patron numerico): {part}")
                return part

        # Patron 3: Buscar numeros al final del nombre
        if parts and parts[-1].isdigit():
            debug_print(f"Frame encontrado (final): {parts[-1]}")
            return parts[-1]

        debug_print("No se encontro numero de frame en el nombre del archivo")
        return "---"

    except Exception as e:
        debug_print(f"Error al extraer frame: {e}")
        return "---"


class ThumbnailWidget(QLabel):
    """Widget personalizado para mostrar un thumbnail clickeable"""

    def __init__(self, image_path, thumbnail_size=80):
        super().__init__()
        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.original_pixmap = None
        self.load_image()
        self.update_size()
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(
            """
            QLabel {
                border: 0px solid #444444;
                background-color: #2a2a2a;
                margin: 2px;
                padding: 2px;
            }
            QLabel:hover {
                border: 0px solid #007ACC;
            }
        """
        )

    def load_image(self):
        """Carga la imagen original"""
        try:
            if os.path.exists(self.image_path):
                self.original_pixmap = QPixmap(self.image_path)
                if self.original_pixmap.isNull():
                    debug_print(f"No se pudo cargar la imagen: {self.image_path}")
                    self.create_placeholder()
            else:
                debug_print(f"Archivo de imagen no existe: {self.image_path}")
                self.create_placeholder()
        except Exception as e:
            debug_print(f"Error al cargar imagen {self.image_path}: {e}")
            self.create_placeholder()

    def create_placeholder(self):
        """Crea un pixmap de placeholder"""
        self.original_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        self.original_pixmap.fill(Qt.gray)

    def update_size(self):
        """Actualiza el tamaño del thumbnail manteniendo la relación de aspecto"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.setPixmap(scaled_pixmap)
            self.setFixedSize(
                self.thumbnail_size + 4, self.thumbnail_size + 4
            )  # +4 for border and padding

    def mousePressEvent(self, event):
        """Maneja el evento de clic del mouse para abrir la imagen"""
        if event.button() == Qt.LeftButton:
            debug_print(f"Abriendo imagen: {self.image_path}")
            try:
                if platform.system() == "Windows":
                    os.startfile(self.image_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", self.image_path])
                else:  # Linux
                    subprocess.Popen(["xdg-open", self.image_path])
            except Exception as e:
                debug_print(f"Error al abrir imagen: {e}")
        super().mousePressEvent(event)


class ThumbnailContainerWidget(QWidget):
    """Widget contenedor que incluye thumbnail y frame number"""

    def __init__(self, image_path, thumbnail_size=80):
        super().__init__()
        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del contenedor"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        # Thumbnail principal
        self.thumbnail = ThumbnailWidget(self.image_path, self.thumbnail_size)
        layout.addWidget(self.thumbnail, alignment=Qt.AlignCenter)

        # Label de frame number
        frame_number = extract_frame_from_filename(self.image_path)
        self.frame_label = QLabel(f"f{frame_number}")
        self.frame_label.setStyleSheet(
            "color: #cccccc; font-size: 10px; background-color: transparent;"
        )
        self.frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.frame_label, alignment=Qt.AlignCenter)


app = None
window = None


def find_project_for_sequence(target_sequence):
    """Busca el proyecto que contiene la secuencia activa."""
    if not target_sequence:
        return None

    for project in hiero.core.projects():
        try:
            for sequence in project.sequences():
                if sequence == target_sequence:
                    return project
        except Exception:
            continue
    return None


def get_playlist_panel_registration_state():
    """Chequea si el Playlist Panel fue registrado en esta sesion."""
    try:
        playlist_panel_module = sys.modules.get("LGA_NKS_Playlist_Panel")
        if playlist_panel_module is None:
            return False
        return getattr(playlist_panel_module, "playlistPanel", None) is not None
    except Exception as exc:
        debug_print("Error chequeando registro del Playlist Panel:", str(exc), level="warning")
        return False


def should_redirect_to_playlist_shot_info():
    """Determina si Flow Shot Info debe delegar al Shot Info de playlist."""
    if not HAS_CLIP_UTILS:
        return False

    sequence = hiero.ui.activeSequence()
    project = find_project_for_sequence(sequence)
    clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

    if not sequence or not project or not clip or isinstance(clip, list):
        debug_print(
            "Vendor dispatch skipped due to missing context.",
            f"sequence_present={bool(sequence)}",
            f"project_present={bool(project)}",
            f"clip_present={bool(clip)}",
            level="debug",
        )
        return False

    try:
        clip_name = clip.name()
    except Exception:
        clip_name = ""

    project_prefix = project.name().split("_")[0] if project.name() else ""
    clip_prefix = clip_name.split("_")[0] if clip_name else ""
    is_vendor = bool(project_prefix and clip_prefix and project_prefix != clip_prefix)

    playlist_panel_registered = get_playlist_panel_registration_state()
    current_user_is_master = False

    if not playlist_panel_registered:
        try:
            from LGA_NKS_Playlist_Panel_py.LGA_NKS_Playlist_Panel_Permissions import (
                is_current_user_master,
            )

            current_user_is_master = is_current_user_master()
        except Exception as exc:
            debug_print(
                "No se pudo chequear Master para vendor dispatch:",
                str(exc),
                level="warning",
            )

    debug_print(
        "Vendor dispatch context:",
        f"sequence_name='{sequence.name()}'",
        f"timeline_project_name='{project.name()}'",
        f"clip_name='{clip_name}'",
        f"project_prefix='{project_prefix}'",
        f"clip_prefix='{clip_prefix}'",
        f"is_vendor={is_vendor}",
        f"playlist_panel_registered={playlist_panel_registered}",
        f"current_user_is_master={current_user_is_master}",
    )

    return is_vendor and (playlist_panel_registered or current_user_is_master)


def run_playlist_shot_info():
    """Ejecuta el Shot Info del Playlist Panel."""
    module = importlib.import_module(
        "LGA_NKS_Playlist_Panel_py.LGA_NKS_FlowPlaylist_Shot_info"
    )
    module.main()


class ShotGridManager:
    """Clase para manejar operaciones con datos de la base de datos SQLite en lugar de JSON."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def find_project(self, project_name):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM projects WHERE project_name = ?", (project_name,))
        return cur.fetchone()

    def find_shot(self, project_name, shot_code):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT s.* FROM shots s
            JOIN projects p ON s.project_id = p.id
            WHERE p.project_name = ? AND s.shot_name = ?
            """,
            (project_name, shot_code),
        )
        shot = cur.fetchone()
        if not shot:
            return None
        # Estructura igual al JSON original
        shot_dict = {
            "shot_name": shot["shot_name"],
            "sequence": shot["sequence"],
            "tasks": [],
        }
        # Obtener las tasks asociadas a este shot
        cur.execute("SELECT * FROM tasks WHERE shot_id = ?", (shot["id"],))
        tasks = cur.fetchall()
        for task in tasks:
            task_dict = {
                "task_type": task["task_type"],
                "task_description": task["task_description"],
                "task_status": task["task_status"],
                "task_assigned_to": None,
                "versions": [],
            }
            # Obtener asignado
            cur.execute(
                "SELECT assigned_to FROM task_assignments WHERE task_id = ?",
                (task["id"],),
            )
            assign = cur.fetchone()
            if assign:
                task_dict["task_assigned_to"] = assign["assigned_to"]
            else:
                task_dict["task_assigned_to"] = "No asignado"
            # Obtener versiones
            cur.execute(
                "SELECT * FROM versions WHERE task_id = ? ORDER BY version_number DESC",
                (task["id"],),
            )
            versions = cur.fetchall()
            for v in versions:
                # Obtener comentarios/notas de la version con información de attachments
                cur.execute(
                    "SELECT content, created_by, created_on, local_attachment_paths FROM version_notes WHERE version_id = ? ORDER BY created_on DESC",
                    (v["id"],),
                )
                notes = cur.fetchall()
                comments = []
                for n in notes:
                    # Saltar la nota auto-generada por PipeSync al subir la version
                    # (mismo autor + mismo contenido que la descripcion + fecha cercana).
                    if _is_version_upload_duplicate_note(
                        n,
                        v["description"],
                        v["created_by"],
                        v["created_on"],
                    ):
                        debug_print(
                            "Skipping auto-generated upload note:",
                            f"version_id={v['id']}",
                            f"user='{n['created_by']}'",
                            f"note_date='{n['created_on']}'",
                            f"version_date='{v['created_on']}'",
                            level="debug",
                        )
                        continue
                    # Procesar attachment paths si existen
                    attachment_paths = []
                    if n["local_attachment_paths"]:
                        # Los paths están separados por punto y coma
                        paths = n["local_attachment_paths"].split(";")
                        for path in paths:
                            path = path.strip()
                            if path and os.path.exists(path):
                                attachment_paths.append(path)

                    comments.append(
                        {
                            "user": n["created_by"] or "",
                            "text": n["content"] or "",
                            "date": n["created_on"],
                            "attachments": attachment_paths,
                        }
                    )
                version_dict = {
                    "version_number": f"v{v['version_number']:03d}",
                    "version_description": v["description"] or "",
                    "version_date": v["created_on"] or "",
                    "created_by": v["created_by"] or "Unknown",
                    "comments": comments,
                }
                task_dict["versions"].append(version_dict)
            shot_dict["tasks"].append(task_dict)
        return shot_dict

    def find_task(self, shot, task_name):
        for t in shot["tasks"]:
            if t["task_type"].lower() == task_name.lower():
                return t
        return None

    def close(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()


class HieroOperations:
    """Clase para manejar operaciones en Hiero."""

    def __init__(self, shotgrid_manager):
        self.sg_manager = shotgrid_manager
        # Sincronizar debug con el módulo utilitario
        if HAS_CLIP_UTILS:
            clip_utils.DEBUG = DEBUG

    def parse_exr_name(self, file_name):
        """Extrae el nombre base del archivo EXR y el numero de version."""
        # Usar función compartida para limpiar el nombre base
        base_name = clean_base_name(file_name)
        # Buscar versión en el nombre original (antes de limpiar)
        version_match = re.search(r"_v(\d+)", file_name)
        version_number = version_match.group(1) if version_match else "Unknown"
        return base_name, version_number

    def process_selected_clips(self):
        """Procesa el clip del playhead resolviendo la task entre las disponibles.

        Si en el playhead hay clips de varias tasks (`_comp_`, `_roto_`, `_cleanup_`),
        muestra un popover para elegir cuál mostrar. Si hay una sola, la usa
        automáticamente. Si no hay clip en ninguna, cae al método actual con
        TRACK_comp_EXR y selección como fallback.
        """
        debug_print("Processing selected clips...")

        if not HAS_CLIP_UTILS:
            debug_print("ERROR: Módulo LGA_NKS_GetClip no disponible. No se pueden procesar clips.")
            return []

        seq = hiero.ui.activeSequence()
        resolved_task = resolve_task_at_playhead(seq, title="Select task") if seq else None
        debug_print(f"Task resuelta para Shot_info: {resolved_task}")

        if resolved_task:
            target_track = track_for_task(resolved_task)
            playhead_clip = get_clip_to_process(track_name=target_track)
        else:
            playhead_clip = get_clip_to_process(track_name=None)

        if playhead_clip:
            clips_to_process = [playhead_clip]
            debug_print(
                f">>> Usando clip del playhead. resolved_task='{resolved_task}'"
            )
        else:
            clips_to_process = get_selected_clips()
            debug_print(
                ">>> No hay clip en playhead; usando clips seleccionados como fallback"
            )

        # Task name a usar en find_task: la resuelta del playhead, o 'comp' por compatibilidad
        active_task_name = resolved_task or "comp"

        results = []
        if not clips_to_process:
            debug_print("No se encontraron clips para procesar.")
            return results

        for clip in clips_to_process:
            if isinstance(clip, hiero.core.EffectTrackItem):
                continue  # Pasar de largo los clips que sean efectos

            file_path = clip.source().mediaSource().fileinfos()[0].filename()
            exr_name = os.path.basename(file_path)
            base_name, version_number = self.parse_exr_name(exr_name)
            clip_name = ""
            try:
                clip_name = clip.name()
            except Exception:
                clip_name = exr_name

            # Usar funciones compartidas para extraer información
            project_name = extract_project_name(base_name)
            shot_code = extract_shot_code(base_name)
            debug_print(
                "Clip context:",
                f"clip_name='{clip_name}'",
                f"file_path='{file_path}'",
                f"exr_name='{exr_name}'",
                f"base_name='{base_name}'",
                f"project_name='{project_name}'",
                f"shot_code='{shot_code}'",
            )

            # Operaciones intensivas: ceder tiempo de UI
            QCoreApplication.processEvents()
            shot = self.sg_manager.find_shot(project_name, shot_code)
            debug_print(f"Shot found: {shot}")
            if not shot:
                debug_print(
                    "No se encontro shot en pipesync.db para la combinacion parseada.",
                    f"project_name='{project_name}'",
                    f"shot_code='{shot_code}'",
                    level="warning",
                )

            QCoreApplication.processEvents()
            if shot:
                task = self.sg_manager.find_task(shot, active_task_name)
                debug_print(f"Task found ({active_task_name}): {task}")
                task_description = (
                    task["task_description"] if task else "No info available"
                )
                assignee = task["task_assigned_to"] if task else "No assignee"
                versions = task["versions"] if task else []

                last_versions = sorted(
                    versions, key=lambda v: v["version_date"], reverse=True
                )
                version_info = []
                for v in last_versions:
                    match = re.search(r"v(\d+)", v["version_number"])
                    version_number = match.group() if match else v["version_number"]
                    version_info.append(
                        {
                            "version_number": version_number,
                            "version_description": v["version_description"]
                            or "No description",
                            "comments": v.get("comments", []),
                            "created_by": v.get("created_by", "Unknown"),
                        }
                    )

                shot_info = {
                    "shot_code": shot["shot_name"],
                    "description": task_description,
                    "assignee": assignee,
                    "versions": version_info,
                }
                results.append(shot_info)
            QCoreApplication.processEvents()

        debug_print("Processing completed.")
        return results


class GUIWindow(QWidget):
    def __init__(self, hiero_ops, parent=None):
        super(GUIWindow, self).__init__(parent)
        self.hiero_ops = hiero_ops
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Info")
        self.setStyleSheet("background-color: #2a2a2a; color: #cccccc;")
        self.setMinimumSize(800, 600)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Scroll area para el contenido
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #2a2a2a;
            }
            QScrollBar:vertical {
                background-color: #333333;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888888;
            }
        """
        )

        # Widget contenedor para el scroll
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # Anadir evento para cerrar la ventana con la tecla ESC
        shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        shortcut.activated.connect(self.close)

    def closeEvent(self, event):
        # Cerrar la conexión de sg_manager si existe
        if hasattr(self.hiero_ops, "sg_manager") and self.hiero_ops.sg_manager:
            self.hiero_ops.sg_manager.close()
            self.hiero_ops.sg_manager = None
        super(GUIWindow, self).closeEvent(event)

    def create_shot_header_widget(self, shot_code, assignee, description):
        """Crea el widget de cabecera para un shot"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Titulo del shot y asignado
        title_label = QLabel(
            f"<b style='color:#CCCC00; font-size:14px;'>{shot_code}</b> | <span style='color:#007ACC; font-weight:bold;'>{assignee}</span>"
        )
        title_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(title_label)

        # Descripcion
        if description and description != "Sin descripcion":
            desc_label = QLabel(
                f"<span style='color:#009688; font-weight:bold;'>Description:</span> {description}"
            )
            desc_label.setStyleSheet("background-color: transparent;")
            desc_label.setWordWrap(True)
            header_layout.addWidget(desc_label)

        return header_widget

    def create_version_widget(self, version):
        """Crea el widget para una version"""
        version_widget = QWidget()
        version_layout = QVBoxLayout(version_widget)
        version_layout.setSpacing(0)
        version_layout.setContentsMargins(
            20, 20, 0, 20
        )  # Indentacion para las versiones, sin margenes extras

        # Titulo de la version y descripcion combinados
        version_number = version["version_number"].split("_")[-1]
        version_creator = version.get("created_by", "Unknown")
        version_description = version["version_description"] or ""

        # Combinar en un solo QLabel con HTML y salto de linea
        combined_text = (
            f"<span style='color:#007ACC; font-weight:bold;'>{version_number}</span> | "
            f"<span style='color:#AAAAAA;'>{version_creator}</span>"
        )

        if version_description:
            combined_text += f"<br/><br/><span style='color:#CCCCCC; font-size:12px;'>{version_description}</span>"

        version_label = QLabel(combined_text)
        # Ajustar line-height y eliminar margenes/rellenos para reducir el espacio vertical
        version_label.setStyleSheet(
            "background-color: transparent; padding: 0px; margin: 0px; line-height: 0.8;"
        )
        version_label.setWordWrap(True)
        version_layout.addWidget(version_label)

        # Comentarios de la version
        for comment in version.get("comments", []):
            comment_widget = self.create_comment_widget(comment)
            version_layout.addWidget(comment_widget)

        return version_widget

    def create_comment_widget(self, comment):
        """Crea el widget para un comentario con sus attachments"""
        comment_widget = QWidget()
        comment_layout = QVBoxLayout(comment_widget)
        comment_layout.setSpacing(5)
        comment_layout.setContentsMargins(
            30, 0, 0, 0
        )  # Indentacion para los comentarios

        # Texto del comentario
        comment_user = comment["user"]
        comment_text = comment["text"] if comment["text"] else ""
        attachments = comment.get("attachments", [])

        # Si hay texto de comentario, mostrarlo
        if comment_text:
            # Procesar saltos de linea para el display
            comment_text_processed = comment_text.replace("\n\n", "<br><br>").replace(
                "\n", "<br>"
            )
            comment_label = QLabel(
                f"<b style='color:#AAAAAA;'>{comment_user}:</b> {comment_text_processed}"
            )
            comment_label.setStyleSheet("background-color: transparent;")
            comment_label.setWordWrap(True)
            comment_layout.addWidget(comment_label)
        elif attachments:
            # Si no hay texto pero hay attachments, mostrar solo el usuario
            user_label = QLabel(f"<b style='color:#AAAAAA;'>{comment_user}:</b>")
            user_label.setStyleSheet("background-color: transparent;")
            comment_layout.addWidget(user_label)

        # Thumbnails de attachments si existen
        if attachments:
            thumbnails_widget = self.create_thumbnails_widget(attachments)
            comment_layout.addWidget(thumbnails_widget)

        return comment_widget

    def create_thumbnails_widget(self, attachment_paths):
        """Crea el widget que contiene los thumbnails de los attachments"""
        thumbnails_widget = QWidget()
        thumbnails_layout = QHBoxLayout(thumbnails_widget)
        thumbnails_layout.setSpacing(5)
        thumbnails_layout.setContentsMargins(0, 5, 0, 5)
        thumbnails_layout.setAlignment(Qt.AlignLeft)

        for attachment_path in attachment_paths:
            # Verificar que sea un archivo de imagen
            if attachment_path.lower().endswith(
                (".jpg", ".jpeg", ".png", ".tiff", ".tif")
            ):
                thumbnail_container = ThumbnailContainerWidget(
                    attachment_path, thumbnail_size=80
                )
                thumbnails_layout.addWidget(thumbnail_container)

        # Añadir stretch para empujar thumbnails a la izquierda
        thumbnails_layout.addStretch()

        return thumbnails_widget

    def display_results(self, results):
        """Muestra los resultados recopilados en una ventana independiente."""
        debug_print("Displaying results...")

        # Limpiar contenido anterior
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not results:
            no_results_label = QLabel("No se encontraron resultados")
            no_results_label.setAlignment(Qt.AlignCenter)
            no_results_label.setStyleSheet("color: #888888; font-size: 14px;")
            self.scroll_layout.addWidget(no_results_label)
            self.show()
            return

        for result in results:
            debug_print(f"Processing result: {result}")

            # Procesar datos del shot
            description = (
                result["description"]
                if result["description"] is not None
                else "Sin descripcion"
            )
            assignee = (
                result["assignee"] if result["assignee"] is not None else "No assignee"
            )
            shot_code = result["shot_code"]
            versions = result["versions"]

            # Crear widget del shot
            shot_widget = QFrame()
            shot_widget.setFrameStyle(QFrame.Box)
            shot_widget.setStyleSheet(
                """
                QFrame {
                    border: 0px solid #444444;
                    border-radius: 5px;
                    background-color: #333333;
                    margin: 5px;
                    padding: 10px;
                }
            """
            )

            shot_layout = QVBoxLayout(shot_widget)
            shot_layout.setSpacing(10)

            # Agregar cabecera del shot
            header_widget = self.create_shot_header_widget(
                shot_code, assignee, description
            )
            shot_layout.addWidget(header_widget)

            # Agregar versiones
            for version in versions:
                version_widget = self.create_version_widget(version)
                shot_layout.addWidget(version_widget)

            self.scroll_layout.addWidget(shot_widget)

        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.show()
        debug_print("Results displayed successfully.")


def main():
    global app, window
    if should_redirect_to_playlist_shot_info():
        debug_print(
            "Vendor timeline detectado desde Flow Shot Info. Redirigiendo a Playlist Shot Info."
        )
        run_playlist_shot_info()
        return

    # Selecciona la ruta de la base de datos segun el sistema operativo
    if platform.system() == "Windows":
        db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
    elif platform.system() == "Darwin":  # macOS
        db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
    else:
        debug_print(f"Sistema operativo no soportado: {platform.system()}")
        return

    if not os.path.exists(db_path):
        debug_print(f"DB file not found at path: {db_path}")
        return
    sg_manager = ShotGridManager(db_path)
    hiero_ops = HieroOperations(sg_manager)
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    window = GUIWindow(hiero_ops)
    results = hiero_ops.process_selected_clips()
    debug_print(f"Results: {results}")
    window.display_results(results)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
