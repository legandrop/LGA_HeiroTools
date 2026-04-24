"""
____________________________________________________________________________________

  LGA_NKS_Playlist_Panel v0.01 | Lega
  Panel base para flujos de playlists vendor en Hiero / Nuke Studio.
  Esta primera version solo monta la UI del panel y valida si el usuario actual
  tiene rol Master en PipeSync antes de cargarlo.

  v0.01: Creacion inicial del panel, deteccion de Master y botones placeholder.
____________________________________________________________________________________
"""

import hiero.ui
import logging
import os
import queue
import time
from logging.handlers import QueueHandler, QueueListener

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore

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
                "shortcut": "Shift+T",
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
                button.setCustomClickHandler(self.handle_placeholder_action(action))
                button.setShiftClickHandler(
                    self.handle_placeholder_action(f"{action}_shift")
                )
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

    def handle_placeholder_action(self, action_name):
        def _handler(*_args):
            if action_name == "rev_dir":
                QtWidgets.QMessageBox.information(
                    self,
                    "Playlist Panel",
                    "Rev Dir: todavia no implementado.",
                )
            else:
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
