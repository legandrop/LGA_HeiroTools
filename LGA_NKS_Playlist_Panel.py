"""
____________________________________________________________________

  LGA_NKS_Playlist_Panel v0.01 | Lega

  Panel base para flujos de playlists vendor en Hiero / Nuke Studio.
  Esta primera version solo monta la UI del panel y valida si el usuario actual
  tiene rol Master en PipeSync antes de cargarlo.

  v0.01: Creacion inicial del panel, deteccion de Master y botones placeholder.
____________________________________________________________________
"""

import hiero.ui
import hiero.core
import importlib.util
import logging
import os
import queue
import time
from logging.handlers import QueueHandler, QueueListener

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore
from LGA_NKS_Shared.LGA_NKS_GetClip import get_clip_to_process

from LGA_NKS_Shared.LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover,
)

from LGA_NKS_Playlist_Panel_py.LGA_NKS_Playlist_Panel_Permissions import (
    get_master_detection_details,
    is_current_user_master,
)


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


def setup_debug_logging(script_name="PlaylistPanel"):
    """Configura el logging para escribir solo en archivo."""
    global debug_log_listener

    log_filename = f"DebugPy_{script_name}.log"
    log_file_path = os.path.join(os.path.dirname(__file__), "logs", log_filename)

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


debug_logger = setup_debug_logging(script_name="PlaylistPanel")


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


class CustomButton(QtWidgets.QPushButton):
    """Boton con soporte para Shift+Click, como en el Flow Panel."""

    def __init__(self, text):
        super(CustomButton, self).__init__(text)
        self._custom_click_handler = None
        self._shift_click_handler = None

    def setCustomClickHandler(self, handler):
        self._custom_click_handler = handler

    def setShiftClickHandler(self, handler):
        self._shift_click_handler = handler

    def mousePressEvent(self, event):
        if self._custom_click_handler and self._shift_click_handler:
            modifiers = event.modifiers()
            if modifiers & QtCore.Qt.ShiftModifier:
                self._shift_click_handler()
            else:
                self._custom_click_handler()
        else:
            super(CustomButton, self).mousePressEvent(event)


class PlaylistPanelWidget(QtWidgets.QWidget):
    def __init__(self):
        super(PlaylistPanelWidget, self).__init__()

        self.setObjectName("com.lega.PlaylistPanel")
        self.setWindowTitle("Playlist")
        debug_print("=== PlaylistPanel init ===")

        self.root_layout = QtWidgets.QVBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setLayout(self.root_layout)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.root_layout.addWidget(self.scroll_area)

        self.scroll_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.layout.setHorizontalSpacing(6)
        self.layout.setVerticalSpacing(3)
        self.scroll_widget.setLayout(self.layout)
        self.scroll_area.setWidget(self.scroll_widget)

        self.buttons = [
            {
                "name": "Playlist Pull",
                "style": "#1f1f1f",
                "action": "playlist_pull",
            },
            {
                "name": "Sho&t Info",
                "style": "#1f1f1f",
                "action": "shot_info",
            },
            {
                "name": "Review Pic",
                "style": "#1f1f1f",
                "action": "review_pic",
            },
            {
                "name": "Corrections",
                "style": "#2e77d4",
                "action": "corrections",
            },
            {
                "name": "Send Note",
                "style": "#1f1f1f",
                "action": "send_note",
            },
            {
                "name": "Rev Dir",
                "style": "#98c054",
                "action": "rev_dir",
            },
            {
                "name": "Approved",
                "style": "#244c19",
                "action": "approve",
            },
            {
                "name": "Show Playlist",
                "style": "#1f1f1f",
                "action": "show_playlist",
            },
        ]

        self.num_columns = 1
        self.button_width_hint = 0
        self.create_buttons()
        self.adjust_columns_on_resize()
        self.resizeEvent = self.adjust_columns_on_resize

    def find_project_for_sequence(self, target_sequence):
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

    def get_vendor_check_context(self):
        """Obtiene contexto basico para validar si el timeline actual es vendor."""
        sequence = hiero.ui.activeSequence()
        project = self.find_project_for_sequence(sequence) if sequence else None
        clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

        clip_name = ""
        if clip and not isinstance(clip, list):
            try:
                clip_name = clip.name()
            except Exception:
                clip_name = str(clip)

        sequence_name = sequence.name() if sequence else ""
        project_name = project.name() if project else ""

        project_prefix = project_name.split("_")[0].strip().upper() if project_name else ""
        clip_prefix = clip_name.split("_")[0].strip().upper() if clip_name else ""
        is_vendor = bool(project_prefix and clip_prefix and project_prefix != clip_prefix)

        return {
            "sequence_name": sequence_name,
            "project_name": project_name,
            "clip_name": clip_name,
            "project_prefix": project_prefix,
            "clip_prefix": clip_prefix,
            "is_vendor": is_vendor,
        }

    def ensure_vendor_timeline(self, action_name):
        """Valida si el timeline actual es vendor antes de ejecutar una accion."""
        context = self.get_vendor_check_context()
        debug_print(
            "Vendor check:",
            f"action={action_name}",
            f"sequence={context['sequence_name']}",
            f"project={context['project_name']}",
            f"clip={context['clip_name']}",
            f"project_prefix={context['project_prefix']}",
            f"clip_prefix={context['clip_prefix']}",
            f"is_vendor={context['is_vendor']}",
        )

        if context["is_vendor"]:
            return True

        message = (
            "La accion no se ejecutara porque el timeline actual no parece vendor.\n\n"
            f"Timeline: {context['sequence_name'] or 'No encontrado'}\n"
            f"Proyecto: {context['project_name'] or 'No encontrado'}\n"
            f"Clip: {context['clip_name'] or 'No encontrado'}"
        )
        QtWidgets.QMessageBox.information(self, "Playlist Panel", message)
        return False

    def create_buttons(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        max_button_width = 0

        for index, button_info in enumerate(self.buttons):
            button = CustomButton(button_info["name"])
            style = button_info["style"]
            border_color = calculate_dynamic_border(style)
            hover_color = calculate_dynamic_hover(style)

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {style};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    color: #d8d8d8;
                    padding: 0px 0px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton:pressed {{
                    background-color: {style}aa;
                }}
                """
            )

            action = button_info["action"]
            if "shortcut" in button_info:
                button.setShortcut(button_info["shortcut"])

            if action == "playlist_pull":
                button.setCustomClickHandler(self.handle_playlist_pull_all)
                button.setShiftClickHandler(
                    self.handle_playlist_pull_selected
                )
            elif action == "shot_info":
                button.clicked.connect(self.handle_shot_info)
            elif action == "review_pic":
                button.clicked.connect(self.handle_review_pic)
            elif action == "corrections":
                button.clicked.connect(self.handle_corrections)
            elif action == "rev_dir":
                button.clicked.connect(self.handle_rev_dir)
            elif action == "approve":
                button.clicked.connect(self.handle_approved)
            else:
                button.clicked.connect(self.handle_placeholder_action(action))

            max_button_width = max(max_button_width, button.sizeHint().width())
            row = index // self.num_columns
            column = index % self.num_columns
            self.layout.addWidget(button, row, column)

        if max_button_width > 0:
            self.button_width_hint = max_button_width

        num_rows = (len(self.buttons) + self.num_columns - 1) // self.num_columns
        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.layout.addItem(spacer, num_rows, 0, 1, self.num_columns)

    def _load_playlist_panel_module(self, file_name, module_name):
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Playlist_Panel_py", file_name
        )
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script no encontrado: {script_path}")

        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"No se pudo cargar el módulo: {module_name}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _run_with_project_undo(self, description, callback):
        project = hiero.core.projects()[0] if hiero.core.projects() else None
        if not project:
            debug_print("No se encontro proyecto activo para ejecutar la accion.", level="warning")
            return

        project.beginUndo(description)
        try:
            callback()
        except Exception as exc:
            debug_print(f"Error ejecutando accion '{description}': {exc}", level="error")
            QtWidgets.QMessageBox.warning(
                self,
                "Playlist Panel",
                f"Error ejecutando '{description}': {exc}",
            )
        finally:
            project.endUndo()

    def run_clear_tag_script(self):
        try:
            seq = hiero.ui.activeSequence()
            if not seq:
                return

            te = hiero.ui.getTimelineEditor(seq)
            selected_items = te.selection()

            for item in selected_items:
                if isinstance(item, hiero.core.EffectTrackItem):
                    continue

                script_path = os.path.join(
                    os.path.dirname(__file__),
                    "LGA_NKS_Shared",
                    "LGA_NKS_Delete_ClipTags.py",
                )
                if not os.path.exists(script_path):
                    continue

                spec = importlib.util.spec_from_file_location(
                    "LGA_H_DeleteClipTags", script_path
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.delete_tags_from_clip(item)
        except Exception as exc:
            debug_print(f"Error ejecutando clear tags: {exc}", level="warning")

    def handle_playlist_pull_all(self):
        if not self.ensure_vendor_timeline("playlist_pull"):
            return

        def _run():
            module = self._load_playlist_panel_module(
                "LGA_NKS_FlowPlaylist_Pull.py", "LGA_NKS_Playlist_FlowPlaylist_Pull"
            )
            module.FPT_Hiero(force_all_clips=True)

        self._run_with_project_undo("Playlist Pull", _run)

    def handle_playlist_pull_selected(self):
        if not self.ensure_vendor_timeline("playlist_pull_shift"):
            return

        def _run():
            module = self._load_playlist_panel_module(
                "LGA_NKS_FlowPlaylist_Pull.py", "LGA_NKS_Playlist_FlowPlaylist_Pull"
            )
            module.FPT_Hiero()

        self._run_with_project_undo("Playlist Pull Selected", _run)

    def handle_shot_info(self):
        if not self.ensure_vendor_timeline("shot_info"):
            return

        def _run():
            module = self._load_playlist_panel_module(
                "LGA_NKS_FlowPlaylist_Shot_info.py", "LGA_NKS_Playlist_FlowPlaylist_ShotInfo"
            )
            module.main()

        self._run_with_project_undo("Playlist Shot Info", _run)

    def handle_review_pic(self):
        if not self.ensure_vendor_timeline("review_pic"):
            return

        def _run():
            module = self._load_playlist_panel_module(
                "LGA_NKS_FlowPlaylist_ReviewPic.py", "LGA_NKS_Playlist_FlowPlaylist_ReviewPic"
            )
            module.main()

        try:
            _run()
        except Exception as exc:
            debug_print(f"Error ejecutando review pic: {exc}", level="error")
            QtWidgets.QMessageBox.warning(
                self,
                "Playlist Panel",
                f"Error ejecutando Review Pic: {exc}",
            )

    def handle_push_status(self, button_name):
        if not self.ensure_vendor_timeline(button_name):
            return

        def _run():
            module = self._load_playlist_panel_module(
                "LGA_NKS_FlowPlaylist_Push.py", "LGA_NKS_Playlist_FlowPlaylist_Push"
            )
            module.push_from_selected_clips(button_name)
            if button_name in ["Rev Dir", "Corrections"]:
                self.run_clear_tag_script()

        self._run_with_project_undo(f"Playlist {button_name}", _run)

    def handle_corrections(self):
        self.handle_push_status("Corrections")

    def handle_rev_dir(self):
        self.handle_push_status("Rev Dir")

    def handle_approved(self):
        self.handle_push_status("Approved")

    def handle_placeholder_action(self, action_name):
        def _handler(*_args):
            if not self.ensure_vendor_timeline(action_name):
                return

            QtWidgets.QMessageBox.information(
                self,
                "Playlist Panel",
                f"{action_name}: placeholder v0.01.",
            )
            debug_print(f"Placeholder action ejecutada: {action_name}")

        return _handler

    def adjust_columns_on_resize(self, event=None):
        viewport_width = (
            self.scroll_area.viewport().width() if self.scroll_area else self.width()
        )
        scroll_width = self.scroll_area.width() if self.scroll_area else self.width()
        self_width = self.width()
        panel_width = min(viewport_width, scroll_width, self_width)

        button_width = self.button_width_hint if self.button_width_hint > 0 else 120
        spacing = self.layout.horizontalSpacing()
        if spacing < 0:
            spacing = self.layout.spacing()
        margins = self.layout.contentsMargins()
        available_width = panel_width - (margins.left() + margins.right())
        min_button_spacing = max(0, spacing)

        new_num_columns = max(
            1,
            (available_width + min_button_spacing)
            // (button_width + min_button_spacing),
        )

        if new_num_columns != self.num_columns:
            self.num_columns = new_num_columns
            self.create_buttons()


def register_playlist_panel():
    details = get_master_detection_details()
    debug_print(
        "Master detection:",
        f"flow_login={details.get('flow_login', '')}",
        f"is_master={details.get('is_master', False)}",
        f"master_emails={details.get('master_emails', [])}",
    )

    if not is_current_user_master():
        debug_print("Usuario actual no es Master. El Playlist Panel no se cargara.")
        return None

    playlist_panel = PlaylistPanelWidget()
    wm = hiero.ui.windowManager()
    wm.addWindow(playlist_panel)
    debug_print("Playlist Panel cargado correctamente.")
    return playlist_panel


playlistPanel = register_playlist_panel()
