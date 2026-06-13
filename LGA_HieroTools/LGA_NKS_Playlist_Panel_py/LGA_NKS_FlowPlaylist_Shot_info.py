"""
____________________________________________________________________

  LGA_NKS_FlowPlaylist_Shot_info v0.02 | Lega

  Muestra informacion hibrida del shot y detalle de playlists vendor.

  v0.02: project_name se extrae del segmento "VFX-NOMBRE" de la ruta
         (extract_project_name_from_path); fallback al nombre del timeline o al
         primer bloque del filename. Ver docs/Docu_ProjectName_Extraction.md.
  v0.01: Logging avanzado a archivo
         Lookup vendor usando proyecto del timeline normalizado
         Descripcion Tarea desde pipesync.db
         Versiones/notas/replies/attachments desde pipesync_playlists.db
____________________________________________________________________

"""

import hiero.core
import hiero.ui
import os
import re
import sys
import sqlite3
import subprocess
import platform
import logging
import queue
import time
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import (
    QtWidgets,
    QtGui,
    QtCore,
    QShortcut,
    QApplication,
)

QCoreApplication = QApplication
Qt = QtCore.Qt
QKeySequence = QtGui.QKeySequence
QPixmap = QtGui.QPixmap
QCursor = QtGui.QCursor
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
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


def setup_debug_logging(script_name="FlowPlaylist_ShotInfo"):
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
    file_handler.setFormatter(RelativeTimeFormatter("[%(relative_time)s] %(message)s"))

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


debug_logger = setup_debug_logging(script_name="FlowPlaylist_ShotInfo")


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


flow_shared_dir = Path(__file__).parent.parent / "LGA_NKS_Shared"
sys.path.append(str(flow_shared_dir))
from LGA_NKS_Flow_NamingUtils import (  # noqa: E402
    extract_shot_code,
    extract_project_name,
    extract_project_name_from_path,
    clean_base_name,
)

utils_path = Path(__file__).parent.parent / "LGA_NKS_Shared"
HAS_CLIP_UTILS = False
if utils_path.exists():
    try:
        sys.path.insert(0, str(utils_path))
        from LGA_NKS_Shared.LGA_NKS_GetClip import (  # noqa: E402
            get_clip_to_process,
            get_selected_clips,
        )
        from LGA_NKS_Shared import LGA_NKS_GetClip as clip_utils  # noqa: E402

        HAS_CLIP_UTILS = True
    except ImportError as e:
        debug_print(f"Error importando modulo LGA_NKS_GetClip: {e}", level="warning")


def parse_flow_datetime(value):
    """Convierte timestamps de Flow/SQLite a datetime."""
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        pass

    formats = [
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def format_friendly_datetime(value):
    """Devuelve fecha/hora amigable en castellano."""
    dt = parse_flow_datetime(value)
    if not dt:
        return str(value or "")

    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    day_delta = (now.date() - dt.date()).days
    time_part = dt.strftime("%I:%M%p").lstrip("0").lower()
    weekdays = {
        0: "lunes",
        1: "martes",
        2: "miercoles",
        3: "jueves",
        4: "viernes",
        5: "sabado",
        6: "domingo",
    }

    if day_delta == 0:
        return f"hoy {time_part}"
    if day_delta == 1:
        return f"ayer {time_part}"
    if 1 < day_delta < 7:
        return f"{weekdays[dt.weekday()]} {time_part}"
    return f"{dt.strftime('%Y-%m-%d')} {time_part}"


def extract_version_label(version_code):
    """Extrae una etiqueta v### desde version_code."""
    if not version_code:
        return "v???"

    match = re.search(r"_v(\d+)$", version_code, re.IGNORECASE)
    if match:
        return f"v{int(match.group(1)):03d}"

    match = re.search(r"(v\d+)", version_code, re.IGNORECASE)
    if match:
        digits = re.sub(r"\D", "", match.group(1))
        if digits:
            return f"v{int(digits):03d}"
        return match.group(1).lower()

    return version_code


def extract_frame_from_filename(filename):
    """Extrae frame number desde un nombre de archivo."""
    try:
        name_without_ext = os.path.splitext(os.path.basename(filename))[0]
        parts = name_without_ext.split("_")

        for i, part in enumerate(parts):
            if part.lower().startswith("v") and len(part) > 1 and part[1:].isdigit():
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    return parts[i + 1]

        for part in parts:
            if part.isdigit() and 1 <= len(part) <= 5:
                return part

        if parts and parts[-1].isdigit():
            return parts[-1]
    except Exception as exc:
        debug_print(f"Error al extraer frame: {exc}", level="warning")
    return "---"


class ThumbnailWidget(QLabel):
    """Widget para mostrar thumbnails clickeables."""

    def __init__(self, image_path, open_path=None, thumbnail_size=80):
        super().__init__()
        self.image_path = image_path
        self.open_path = open_path or image_path
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
        try:
            if self.image_path and os.path.exists(self.image_path):
                self.original_pixmap = QPixmap(self.image_path)
                if self.original_pixmap.isNull():
                    self.create_placeholder()
            else:
                self.create_placeholder()
        except Exception as exc:
            debug_print(f"Error al cargar imagen {self.image_path}: {exc}", level="warning")
            self.create_placeholder()

    def create_placeholder(self):
        self.original_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        self.original_pixmap.fill(Qt.gray)

    def update_size(self):
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.setPixmap(scaled_pixmap)
            self.setFixedSize(self.thumbnail_size + 4, self.thumbnail_size + 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            debug_print(f"Abriendo imagen: {self.open_path}")
            try:
                if platform.system() == "Windows":
                    os.startfile(self.open_path)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", self.open_path])
                else:
                    subprocess.Popen(["xdg-open", self.open_path])
            except Exception as exc:
                debug_print(f"Error al abrir imagen: {exc}", level="warning")
        super().mousePressEvent(event)


class ThumbnailContainerWidget(QWidget):
    """Widget contenedor de thumbnail y frame."""

    def __init__(self, thumb_path, open_path=None, frame_number=None, thumbnail_size=80):
        super().__init__()
        self.thumb_path = thumb_path
        self.open_path = open_path or thumb_path
        self.frame_number = frame_number
        self.thumbnail_size = thumbnail_size
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        self.thumbnail = ThumbnailWidget(
            self.thumb_path, open_path=self.open_path, thumbnail_size=self.thumbnail_size
        )
        layout.addWidget(self.thumbnail, alignment=Qt.AlignCenter)

        frame_text = self.frame_number
        if frame_text in (None, ""):
            frame_text = extract_frame_from_filename(self.open_path or self.thumb_path)

        self.frame_label = QLabel(f"f{frame_text}")
        self.frame_label.setStyleSheet(
            "color: #cccccc; font-size: 10px; background-color: transparent;"
        )
        self.frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.frame_label, alignment=Qt.AlignCenter)


app = None
window = None


class MainDbManager:
    """Lectura puntual desde pipesync.db."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def find_shot_task_info(self, project_name, shot_code, task_name="comp"):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                p.project_name,
                s.shot_name,
                s.sequence,
                t.task_type,
                t.task_description,
                ta.assigned_to
            FROM shots s
            JOIN projects p ON s.project_id = p.id
            LEFT JOIN tasks t
                ON t.shot_id = s.id
               AND lower(t.task_type) = lower(?)
            LEFT JOIN task_assignments ta ON ta.task_id = t.id
            WHERE p.project_name = ? AND s.shot_name = ?
            """,
            (task_name, project_name, shot_code),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def close(self):
        if self.conn:
            self.conn.close()


class PlaylistDbManager:
    """Lectura de detalle playlist desde pipesync_playlists.db."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def get_playlist_entries_for_shot(self, shot_code):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                pv.id,
                pv.playlist_id,
                p.code AS playlist_code,
                p.created_at_flow AS playlist_created_at,
                p.updated_at_flow AS playlist_updated_at,
                p.last_comment_at_flow,
                pv.position,
                pv.version_sg_id,
                pv.version_code,
                pv.shot_code,
                pv.version_review_message,
                pv.version_status,
                pv.version_created_at,
                pv.version_updated_at,
                pv.version_user,
                pv.version_user_type,
                pv.client_approved_at,
                pv.client_approved_by,
                pv.local_thumb_path
            FROM playlist_versions pv
            JOIN playlists p ON pv.playlist_id = p.id
            WHERE pv.shot_code = ?
            ORDER BY
                p.created_at_flow DESC,
                pv.version_created_at DESC,
                pv.position ASC,
                pv.id DESC
            """,
            (shot_code,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_notes_for_version(self, playlist_id, version_sg_id):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                note_sg_id,
                version_sg_id,
                version_code,
                shot_code,
                subject,
                content,
                author_name,
                author_type,
                author_avatar_path,
                created_at_flow,
                updated_at_flow,
                attachment_count,
                reply_count,
                sort_order
            FROM playlist_notes
            WHERE playlist_id = ? AND version_sg_id = ?
            ORDER BY sort_order ASC, created_at_flow ASC, id ASC
            """,
            (playlist_id, version_sg_id),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_replies_for_note(self, note_id):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                reply_sg_id,
                content,
                author_name,
                author_type,
                author_avatar_path,
                created_at_flow,
                updated_at_flow,
                attachment_count,
                sort_order
            FROM playlist_note_replies
            WHERE note_id = ?
            ORDER BY sort_order ASC, created_at_flow ASC, id ASC
            """,
            (note_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_attachments_for_note(self, note_id):
        return self._get_attachments_by_parent("note_id", note_id)

    def get_attachments_for_reply(self, reply_id):
        return self._get_attachments_by_parent("reply_id", reply_id)

    def _get_attachments_by_parent(self, parent_column, parent_id):
        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT
                id,
                parent_type,
                parent_sg_id,
                attachment_sg_id,
                display_name,
                local_thumb_path,
                local_file_path,
                frame_number,
                created_at_flow,
                created_by_name,
                sort_order
            FROM playlist_note_attachments
            WHERE {parent_column} = ?
            ORDER BY sort_order ASC, created_at_flow ASC, id ASC
            """,
            (parent_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()


class HieroOperations:
    """Operaciones de lectura y armado de modelo para la UI."""

    def __init__(self, main_db_manager, playlist_db_manager):
        self.main_db_manager = main_db_manager
        self.playlist_db_manager = playlist_db_manager
        if HAS_CLIP_UTILS:
            clip_utils.DEBUG = DEBUG

    def parse_exr_name(self, file_name):
        base_name = clean_base_name(file_name)
        version_match = re.search(r"_v(\d+)", file_name)
        version_number = version_match.group(1) if version_match else "Unknown"
        return base_name, version_number

    def get_timeline_project_name(self):
        sequence = hiero.ui.activeSequence()
        if not sequence:
            debug_print(
                "No hay secuencia activa para resolver el proyecto del timeline.",
                level="warning",
            )
            return None

        for project in hiero.core.projects():
            try:
                for project_sequence in project.sequences():
                    if project_sequence == sequence:
                        project_name = project.name()
                        debug_print(
                            "Timeline context:",
                            f"sequence_name='{sequence.name()}'",
                            f"timeline_project_name='{project_name}'",
                        )
                        return project_name
            except Exception as exc:
                debug_print(
                    "Error iterando proyectos para resolver timeline project:",
                    str(exc),
                    level="warning",
                )

        debug_print(
            "No se pudo encontrar el proyecto que contiene la secuencia activa.",
            f"sequence_name='{sequence.name()}'",
            level="warning",
        )
        return None

    def normalize_timeline_project_name(self, timeline_project_name):
        if not timeline_project_name:
            return None

        normalized_name = re.sub(
            r"_(SUP|LEG|DIR|EDIT|COMP|ROTO|PREVIZ)(?:_v\d+)?$",
            "",
            timeline_project_name,
            flags=re.IGNORECASE,
        )

        if normalized_name != timeline_project_name:
            debug_print(
                "Normalized timeline project name:",
                f"timeline_project_name='{timeline_project_name}'",
                f"normalized_timeline_project_name='{normalized_name}'",
            )
        else:
            debug_print(
                "Timeline project name did not require normalization:",
                f"timeline_project_name='{timeline_project_name}'",
            )

        return normalized_name

    def process_selected_clips(self):
        debug_print("Processing selected clips...")

        if not HAS_CLIP_UTILS:
            debug_print(
                "ERROR: Modulo LGA_NKS_GetClip no disponible. No se pueden procesar clips.",
                level="error",
            )
            return []

        playhead_clip = get_clip_to_process(track_name=None)

        if playhead_clip:
            clips_to_process = [playhead_clip]
            debug_print(
                ">>> Usando clip del playhead en track TRACK_comp_EXR; fallback a seleccion si no hay"
            )
        else:
            clips_to_process = get_selected_clips()
            debug_print(
                ">>> No hay clip en playhead sobre TRACK_comp_EXR; usando clips seleccionados como fallback"
            )

        if not clips_to_process:
            debug_print("No se encontraron clips para procesar.")
            return []

        results = []

        for clip in clips_to_process:
            if isinstance(clip, hiero.core.EffectTrackItem):
                continue

            file_path = clip.source().mediaSource().fileinfos()[0].filename()
            exr_name = os.path.basename(file_path)
            base_name, _ = self.parse_exr_name(exr_name)
            try:
                clip_name = clip.name()
            except Exception:
                clip_name = exr_name

            parsed_project_name = extract_project_name(base_name)
            shot_code = extract_shot_code(base_name)
            timeline_project_name = self.get_timeline_project_name()
            normalized_timeline_project_name = self.normalize_timeline_project_name(
                timeline_project_name
            )
            # Primario: project_name desde el segmento "VFX-NOMBRE" de la ruta.
            # Fallback: nombre del timeline o primer bloque del filename (comportamiento anterior).
            project_name = extract_project_name_from_path(file_path)
            if project_name:
                debug_print(f"Project name (from path): {project_name}")
            else:
                project_name = normalized_timeline_project_name or parsed_project_name
                debug_print(
                    f"Project name (from timeline/filename fallback): {project_name}"
                )

            debug_print(
                "Clip context:",
                f"clip_name='{clip_name}'",
                f"file_path='{file_path}'",
                f"exr_name='{exr_name}'",
                f"base_name='{base_name}'",
                f"parsed_project_name='{parsed_project_name}'",
                f"timeline_project_name='{timeline_project_name}'",
                f"normalized_timeline_project_name='{normalized_timeline_project_name}'",
                f"search_project_name='{project_name}'",
                f"shot_code='{shot_code}'",
            )

            QCoreApplication.processEvents()
            main_shot_info = self.main_db_manager.find_shot_task_info(project_name, shot_code)
            debug_print(f"Main DB shot/task info: {main_shot_info}")
            if not main_shot_info:
                debug_print(
                    "No se encontro shot/task en pipesync.db para la combinacion parseada.",
                    f"project_name='{project_name}'",
                    f"parsed_project_name='{parsed_project_name}'",
                    f"timeline_project_name='{timeline_project_name}'",
                    f"normalized_timeline_project_name='{normalized_timeline_project_name}'",
                    f"shot_code='{shot_code}'",
                    level="warning",
                )

            playlist_entries = self.playlist_db_manager.get_playlist_entries_for_shot(
                shot_code
            )
            debug_print(
                f"Playlist entries found for shot_code='{shot_code}': {len(playlist_entries)}"
            )

            if not main_shot_info and not playlist_entries:
                QCoreApplication.processEvents()
                continue

            shot_result = {
                "shot_code": shot_code,
                "task_description": (
                    main_shot_info.get("task_description") if main_shot_info else ""
                )
                or "Sin descripcion de tarea",
                "entries": self.build_playlist_entries(playlist_entries),
            }
            results.append(shot_result)
            QCoreApplication.processEvents()

        debug_print("Processing completed.")
        return results

    def build_playlist_entries(self, playlist_entries):
        entries = []
        for entry in playlist_entries:
            notes = []
            note_rows = self.playlist_db_manager.get_notes_for_version(
                entry["playlist_id"], entry["version_sg_id"]
            )
            for note_row in note_rows:
                note_row["attachments"] = self.playlist_db_manager.get_attachments_for_note(
                    note_row["id"]
                )
                replies = []
                for reply_row in self.playlist_db_manager.get_replies_for_note(note_row["id"]):
                    reply_row["attachments"] = (
                        self.playlist_db_manager.get_attachments_for_reply(reply_row["id"])
                    )
                    replies.append(reply_row)
                note_row["replies"] = replies
                notes.append(note_row)

            entry_payload = {
                "playlist_code": entry["playlist_code"],
                "playlist_created_at": entry["playlist_created_at"],
                "version_sg_id": entry["version_sg_id"],
                "version_code": entry["version_code"],
                "version_label": extract_version_label(entry["version_code"]),
                "version_user": entry["version_user"] or "Unknown",
                "version_review_message": entry["version_review_message"] or "",
                "version_created_at": entry["version_created_at"],
                "version_status": entry["version_status"] or "",
                "client_approved_at": entry["client_approved_at"] or "",
                "client_approved_by": entry["client_approved_by"] or "",
                "notes": notes,
            }
            debug_print(f"Built playlist entry: {entry_payload}")
            entries.append(entry_payload)
        return entries


class GUIWindow(QWidget):
    def __init__(self, hiero_ops, parent=None):
        super(GUIWindow, self).__init__(parent)
        self.hiero_ops = hiero_ops
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Info")
        self.setStyleSheet("background-color: #2a2a2a; color: #cccccc;")
        self.setMinimumSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

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

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        shortcut.activated.connect(self.close)

    def closeEvent(self, event):
        if getattr(self.hiero_ops, "main_db_manager", None):
            self.hiero_ops.main_db_manager.close()
            self.hiero_ops.main_db_manager = None
        if getattr(self.hiero_ops, "playlist_db_manager", None):
            self.hiero_ops.playlist_db_manager.close()
            self.hiero_ops.playlist_db_manager = None
        super(GUIWindow, self).closeEvent(event)

    def create_shot_header_widget(self, shot_code, task_description):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(f"<b style='color:#CCCC00; font-size:14px;'>{shot_code}</b>")
        title_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(title_label)

        desc_label = QLabel(
            f"<span style='color:#009688; font-weight:bold;'>Descripcion Tarea:</span> {task_description}"
        )
        desc_label.setStyleSheet("background-color: transparent;")
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)

        return header_widget

    def create_version_widget(self, entry):
        version_widget = QWidget()
        version_layout = QVBoxLayout(version_widget)
        version_layout.setSpacing(4)
        version_layout.setContentsMargins(20, 20, 0, 20)

        version_line = (
            f"<span style='color:#007ACC; font-weight:bold;'>{entry['version_label']}</span> | "
            f"<span style='color:#AAAAAA;'>Subida por {entry['version_user']}</span> | "
            f"<span style='color:#AAAAAA;'>{format_friendly_datetime(entry['playlist_created_at'])}</span> | "
            f"<span style='color:#AAAAAA;'>playlist \"{entry['playlist_code']}\"</span>"
        )
        version_header = QLabel(version_line)
        version_header.setStyleSheet(
            "background-color: transparent; padding: 0px; margin: 0px; line-height: 0.8;"
        )
        version_header.setWordWrap(True)
        version_layout.addWidget(version_header)

        version_description = entry.get("version_review_message") or "Sin descripcion de version"
        version_desc_label = QLabel(
            f"<span style='color:#009688; font-weight:bold;'>Descripcion Version:</span> {version_description}"
        )
        version_desc_label.setStyleSheet("background-color: transparent;")
        version_desc_label.setWordWrap(True)
        version_layout.addWidget(version_desc_label)

        if not entry.get("notes"):
            no_comments_label = QLabel(
                "<span style='color:#888888;'>Sin comentarios para esta aparicion en playlist.</span>"
            )
            no_comments_label.setStyleSheet("background-color: transparent;")
            version_layout.addWidget(no_comments_label)
            return version_widget

        for note in entry["notes"]:
            version_layout.addWidget(self.create_note_widget(note))

        return version_widget

    def create_note_widget(self, note):
        note_widget = QWidget()
        note_layout = QVBoxLayout(note_widget)
        note_layout.setSpacing(5)
        note_layout.setContentsMargins(30, 0, 0, 0)

        header_label = QLabel(
            f"<b style='color:#AAAAAA;'>Comentario {note.get('author_name') or 'Unknown'}:</b> "
            f"<span style='color:#888888;'>{format_friendly_datetime(note.get('created_at_flow'))}</span>"
        )
        header_label.setStyleSheet("background-color: transparent;")
        header_label.setWordWrap(True)
        note_layout.addWidget(header_label)

        content = note.get("content") or ""
        if content:
            content_label = QLabel(content.replace("\n\n", "<br><br>").replace("\n", "<br>"))
            content_label.setStyleSheet("background-color: transparent; color: #CCCCCC;")
            content_label.setWordWrap(True)
            note_layout.addWidget(content_label)

        attachments = note.get("attachments", [])
        if attachments:
            note_layout.addWidget(self.create_thumbnails_widget(attachments))

        for reply in note.get("replies", []):
            note_layout.addWidget(self.create_reply_widget(reply))

        return note_widget

    def create_reply_widget(self, reply):
        reply_widget = QWidget()
        reply_layout = QVBoxLayout(reply_widget)
        reply_layout.setSpacing(5)
        reply_layout.setContentsMargins(35, 2, 0, 2)

        reply_widget.setStyleSheet(
            "QWidget { border-left: 2px solid #555555; background-color: transparent; }"
        )

        header_label = QLabel(
            f"<b style='color:#AAAAAA;'>{reply.get('author_name') or 'Unknown'}:</b> "
            f"<span style='color:#888888;'>{format_friendly_datetime(reply.get('created_at_flow'))}</span>"
        )
        header_label.setStyleSheet("background-color: transparent;")
        header_label.setWordWrap(True)
        reply_layout.addWidget(header_label)

        content = reply.get("content") or ""
        if content:
            content_label = QLabel(content.replace("\n\n", "<br><br>").replace("\n", "<br>"))
            content_label.setStyleSheet("background-color: transparent; color: #CCCCCC;")
            content_label.setWordWrap(True)
            reply_layout.addWidget(content_label)

        attachments = reply.get("attachments", [])
        if attachments:
            reply_layout.addWidget(self.create_thumbnails_widget(attachments))

        return reply_widget

    def create_thumbnails_widget(self, attachments):
        thumbnails_widget = QWidget()
        thumbnails_layout = QHBoxLayout(thumbnails_widget)
        thumbnails_layout.setSpacing(5)
        thumbnails_layout.setContentsMargins(0, 5, 0, 5)
        thumbnails_layout.setAlignment(Qt.AlignLeft)

        for attachment in attachments:
            thumb_path = attachment.get("local_thumb_path") or attachment.get("local_file_path")
            open_path = attachment.get("local_file_path") or attachment.get("local_thumb_path")
            if not thumb_path or not os.path.exists(thumb_path):
                continue
            thumbnails_layout.addWidget(
                ThumbnailContainerWidget(
                    thumb_path,
                    open_path=open_path,
                    frame_number=attachment.get("frame_number"),
                    thumbnail_size=80,
                )
            )

        thumbnails_layout.addStretch()
        return thumbnails_widget

    def display_results(self, results):
        debug_print("Displaying results...")

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

            shot_layout.addWidget(
                self.create_shot_header_widget(
                    result["shot_code"],
                    result["task_description"],
                )
            )

            for entry in result.get("entries", []):
                shot_layout.addWidget(self.create_version_widget(entry))

            self.scroll_layout.addWidget(shot_widget)

        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.show()
        debug_print("Results displayed successfully.")


def main():
    global app, window

    if platform.system() == "Windows":
        main_db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
        playlist_db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync_playlists.db"
    elif platform.system() == "Darwin":
        main_db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
        playlist_db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync_playlists.db"
    else:
        debug_print(f"Sistema operativo no soportado: {platform.system()}", level="error")
        return

    if not os.path.exists(main_db_path):
        debug_print(f"Main DB file not found at path: {main_db_path}", level="error")
        return
    if not os.path.exists(playlist_db_path):
        debug_print(
            f"Playlist DB file not found at path: {playlist_db_path}", level="error"
        )
        return

    main_db_manager = MainDbManager(main_db_path)
    playlist_db_manager = PlaylistDbManager(playlist_db_path)
    hiero_ops = HieroOperations(main_db_manager, playlist_db_manager)

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
