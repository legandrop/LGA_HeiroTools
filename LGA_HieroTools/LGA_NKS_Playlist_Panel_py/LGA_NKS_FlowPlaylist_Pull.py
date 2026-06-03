"""
____________________________________________________________________

  LGA_NKS_FlowPlaylist_Pull v0.01 | Lega

  Compara los estados de las task Comp de los shots del timeline de Hiero
  con los estados registrados en un archivo JSON basado en Flow PT
  Tambien aplica tags con los colores de los estados en xyplorer

  v3.37: Fix crash en pull batch cuando un clip entra en Version Mismatch y la task no tiene assignee.
  v3.36: Soporte multi-task: itera sobre TASK_EXR_TRACKS (comp + roto) en lugar de solo TRACK_comp_EXR
  v3.35: Eliminar spameo en consola con LGA_DEBUG_CONSOLE=0
  v3.34: Simplificación - doScan funciona correctamente en todas las versiones de Hiero, eliminada lógica condicional innecesaria
  v3.32: Debug_print ahora tambien escribe en un archivo de log para debug.
         Arreglos para Hiero 16 (PySide6): omitir doScan problemático, reconexión automática de clips offline y reintento de cambio de color.
  v3.31: Se permite cambiar la versión de un clip offline incluso si no hay media presente.
  v3.30: Centralización del nombre del track usando TRACK_comp_EXR del módulo LGA_NKS_GetClip
  v3.29: Soporta versiones de 2 y 3 dígitos
  v3.28: Actualizado para ser compatible con ambos sistemas de nomenclatura:
         - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
         - PROYECTO_SEQ_SHOT (3 bloques simplificado)
____________________________________________________________________

"""

import json
import hiero.core
import hiero.ui
import os
import re
import sys
import time
import nuke
import logging  # Agregar esta importación
import queue
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

shared_dir = Path(__file__).parent.parent / "LGA_NKS_Shared"
sys.path.insert(0, str(shared_dir))
import shotgun_api3

# Importar utilidades de naming desde shareds de dominio Flow
flow_shared_dir = shared_dir
sys.path.append(str(flow_shared_dir))
from LGA_NKS_Flow_NamingUtils import (
    extract_shot_code,
    extract_project_name,
    extract_task_name,
    clean_base_name,
)

# Importar utilidades para obtener clips
utils_path = Path(__file__).parent.parent / "LGA_NKS_Shared"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_Shared.LGA_NKS_GetClip import TRACK_comp_EXR, TASK_EXR_TRACKS
else:
    # Fallback si no se encuentra el módulo
    TRACK_comp_EXR = "_comp_"
    TASK_EXR_TRACKS = [TRACK_comp_EXR]
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt
QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QHeaderView = QtWidgets.QHeaderView
QColorDialog = QtWidgets.QColorDialog
QMessageBox = QtWidgets.QMessageBox
QStyledItemDelegate = QtWidgets.QStyledItemDelegate
QStyle = QtWidgets.QStyle
QColor = QtGui.QColor
QBrush = QtGui.QBrush
QScreen = QtGui.QScreen
QFont = QtGui.QFont
QPalette = QtGui.QPalette
import sys
import ctypes
import ctypes.wintypes
import platform
import sqlite3
import threading

# Variable global para almacenar el tiempo de inicio del script
script_start_time = None

# Variable global para trackear threads activos de XYplorer
active_xyplorer_threads = []

# Listener global para logging asincrono
debug_log_listener = None

# Evitar spamear el log con el mismo mensaje en macOS
logged_xyplorer_mac_notice = False


# Formatter personalizado para incluir tiempo relativo
class RelativeTimeFormatter(logging.Formatter):
    def format(self, record):
        global script_start_time
        if script_start_time is None:
            script_start_time = record.created

        # Calcular tiempo relativo en segundos con 3 decimales (milisegundos)
        relative_time = record.created - script_start_time
        record.relative_time = f"{relative_time:.3f}s"
        return super().format(record)

# Configurar logging para escribir en tiempo real a un archivo
def setup_debug_logging():
    """Configura el logging para debug que escribe en tiempo real a un archivo."""
    global debug_log_listener
    log_file_path = os.path.join(
        os.path.dirname(__file__), '..', 'logs', 'debugPy_FlowPull.log'
    )

    # Asegurar que el directorio de logs existe
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Limpiar el archivo de log al iniciar el script y escribir encabezado
    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"Warning: No se pudo limpiar el archivo de log: {e}")

    # Configurar el logger
    logger = logging.getLogger('debug_logger')
    logger.setLevel(logging.DEBUG)
    # 🔑 CLAVE: Desactivar propagación al logger root (consola CMD)
    logger.propagate = False

    # Limpiar handlers existentes para evitar duplicados
    if logger.handlers:
        logger.handlers.clear()

    # Crear handler para archivo con encoding UTF-8
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Usar formatter personalizado con tiempo relativo
    formatter = RelativeTimeFormatter('[%(relative_time)s] %(message)s')
    file_handler.setFormatter(formatter)

    # Usar logging asincrono para reducir bloqueos
    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    # Detener listener anterior si existe
    if debug_log_listener:
        try:
            debug_log_listener.stop()
        except Exception:
            pass

    debug_log_listener = QueueListener(log_queue, file_handler, respect_handler_level=True)
    debug_log_listener.daemon = True
    debug_log_listener.start()

    return logger


# Inicializar el logger de debug
debug_logger = setup_debug_logging()


# Incluir la funcion delete_tags_from_clip aqui
def delete_tags_from_clip(clip):
    tags = clip.tags()
    if tags:
        for tag in list(
            tags
        ):  # Usa list(tags) para evitar modificar la lista mientras se itera
            clip.removeTag(tag)
        # print(f"All tags removed from clip: {clip.name()}")


# Variable global para activar o desactivar los prints
DEBUG = True
XYPlorer_Tags = True
# Controla si se imprime en consola (mantiene log en archivo siempre)
DEBUG_PRINT_CONSOLE = os.getenv("LGA_DEBUG_CONSOLE", "0") == "1"


def debug_print(*message):
    global script_start_time
    if DEBUG:
        # Inicializar tiempo de inicio si no está establecido
        if script_start_time is None:
            script_start_time = time.time()

        # Crear el mensaje uniendo todos los argumentos
        msg = ' '.join(str(arg) for arg in message)

        # Calcular tiempo relativo para el print en consola
        relative_time = time.time() - script_start_time
        timestamped_msg = f"[{relative_time:.3f}s] {msg}"

        if DEBUG_PRINT_CONSOLE:
            print(timestamped_msg)  # Print con timestamp
        debug_logger.info(msg)  # El logger ya incluye el timestamp en el archivo


def extract_version_number(version_str):
    """Extrae el numero de version numerico de un string de version."""
    debug_print(f"Intentando extraer version de: {version_str}")
    match = re.search(r"_v(\d+)(?:[-\(][^)]+)?", version_str)

    if match:
        try:
            version_num = int(match.group(1))
            debug_print(f"Version extraida: {version_num}")
            return version_num
        except ValueError:
            debug_print(f"No se pudo convertir a entero: {match.group(1)}")
    debug_print(f"No se encontro numero de version en: {version_str}")
    return 0


class ShotGridManager:
    """Clase para manejar operaciones con datos de la base de datos SQLite en lugar de JSON."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Importante: Los colores deben ser en formato hexadecimal con minúsculas
        # El orden de los valores es: 
        # (nombre en Flow/ShotGrid, color_hex[, tag XYplorer])
        self.task_status_dict = {
            "noread": ("Not Ready To Start", "#000000", None),
            "wts": ("Waiting to start", "#000000", None),
            "ready": ("Ready To Start", "#8a8a8a", None),
            "progre": ("In Progress", "#7d4cff", None),
            "corr": ("Corrections", "#2e77d4", "Corrections"),
            "rev_su": ("Review Sup", "#bd7f9f", "Rev_Sup"),
            "revcha": ("Review Charly", "#a9909d", "Rev_Sup"),
            "review_charly": ("Review Charly", "#a9909d", "Rev_Sup"),
            "revjua": ("Review Juano", "#7F4B69", "Rev_Sup"),
            "revjav": ("Review Javi", "#9c3e5e", "Rev_Sup"),
            "revleg": ("Review Lega", "#69135e", "Rev_Lega"),
            "revhld": ("Review Hold", "#933100", "Rev Hold"),
            "rev_di": ("Review Dir", "#98c054", "ReviewDir"),
            "pubsh": ("Publish", "#244c19", "Approved"),
            "pbshed": ("Published", "#244c19", "Approved"),
            "apr": ("Approved", "#244c19", "Approved"),
            "check": ("Delivery Checked", "#52c233", "Approved"),
            "omit": ("Omitted", "#244c19", "Approved"),
            "enviad": ("Enviado", "#000000", "Approved"),
            "rev": ("Pending Review", "#000000", None),
            "vwd": ("Viewed", "#000000", None),
        }

    def find_project(self, project_name):
        """Busca un proyecto por nombre en la base de datos."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM projects WHERE project_name = ?", (project_name,))
        return cur.fetchone()

    def find_shot(self, project_name, shot_code):
        """Busca un shot por nombre y codigo en la base de datos."""
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
        # Obtener las tasks asociadas a este shot
        cur.execute("SELECT * FROM tasks WHERE shot_id = ?", (shot["id"],))
        tasks = cur.fetchall()
        shot_dict = dict(shot)
        shot_dict["tasks"] = []
        for task in tasks:
            task_dict = dict(task)
            # Obtener asignado
            cur.execute(
                "SELECT assigned_to FROM task_assignments WHERE task_id = ?",
                (task["id"],),
            )
            assign = cur.fetchone()
            if assign:
                task_dict["task_assigned_to"] = assign["assigned_to"]
            else:
                task_dict["task_assigned_to"] = None
            # Obtener versiones
            cur.execute(
                "SELECT * FROM versions WHERE task_id = ? ORDER BY version_number DESC",
                (task["id"],),
            )
            versions = cur.fetchall()
            task_dict["versions"] = [dict(v) for v in versions]
            shot_dict["tasks"].append(task_dict)
        return shot_dict

    def find_task(self, shot, task_name):
        """Busca una tarea especifica por nombre en un shot (dict)."""
        for t in shot["tasks"]:
            if t["task_type"].lower() == task_name.lower():
                return t
        return None

    def find_highest_version_for_shot(self, shot):
        """Encuentra la version mas alta de un shot basandose en la base de datos."""
        all_versions = []
        for task in shot["tasks"]:
            all_versions.extend(task["versions"])
        if all_versions:
            # Buscar la version con el mayor version_number
            highest_version = max(
                all_versions,
                key=lambda v: (
                    v["version_number"] if v["version_number"] is not None else 0
                ),
            )
            # Adaptar el formato esperado por el resto del script
            return {
                "version_number": f"{shot['shot_name']}_comp_v{highest_version['version_number']:03d}",
                "version_status": highest_version.get("status", ""),
                "version_description": highest_version.get("description", ""),
            }
        return None

    def close(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()


class GUI_Table(QWidget):
    def __init__(self, sg_manager, parent=None):
        super(GUI_Table, self).__init__(parent)
        self.sg_manager = sg_manager
        self.row_background_colors = (
            []
        )  # Lista para almacenar listas de colores de fondo por fila
        self.hiero_ops = None
        self.initUI()
        self.last_selected_index = (
            None  # Guardar el indice de la ultima fila seleccionada
        )

    def set_hiero_ops(self, hiero_ops):
        self.hiero_ops = hiero_ops  # Assign instance of HieroOperations
        self.update_table()  # Now you can check for changes and display the table

    def update_table(self):
        if self.hiero_ops:
            changes_exist = self.hiero_ops.process_selected_clips(
                self.table, self.sg_manager
            )
            if changes_exist:
                self.adjust_window_size()
                self.show()
            else:
                QMessageBox.information(
                    self,
                    "No Changes",
                    "No changes were detected in the selected shots.",
                )

    def add_color_to_background_list(self, row_colors):
        """Agrega una lista de colores de fondo para una nueva fila."""
        self.row_background_colors.append(row_colors)

    def initUI(self):
        self.setWindowTitle("Read Nodes EXR Info")
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(
            [
                "Shot",
                " v_NKS ",
                " v_SG ",
                " v_Status ",
                " Previous Status ",
                " New Status ",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet(
            """
            QTableView::item:selected {
                color: black;
                background-color: transparent;  // Hacer transparente el fondo de los items seleccionados
            }
        """
        )
        # Asigna el delegado personalizado
        delegate = ColorMixDelegate(self.table, self.row_background_colors)
        self.table.setItemDelegate(delegate)
        layout.addWidget(self.table)
        self.setLayout(layout)
        font = QFont()
        font.setBold(True)
        self.table.horizontalHeader().setFont(font)

    def mix_colors(self, original_color, mix_color=(88, 88, 88)):
        """Mezcla dos colores RGB."""
        r1, g1, b1 = original_color
        r2, g2, b2 = mix_color
        mixed_color = ((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)
        return mixed_color

    def adjust_window_size(self):
        # Ajustes para cambiar el tamano y posicion de la ventana de acuerdo a la pantalla
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.resizeColumnsToContents()
        width = self.table.verticalHeader().width() - 30
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i) + 20
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        max_width = screen_rect.width() * 0.8
        final_width = min(width, max_width)
        height = self.table.horizontalHeader().height() + 20
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i) + 4
        max_height = screen_rect.height() * 0.8
        final_height = min(height, max_height)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.resize(final_width, final_height)
        self.move(
            (screen_rect.width() - final_width) // 2,
            (screen_rect.height() - final_height) // 2,
        )

    def keyPressEvent(self, event):
        """Cierra la ventana cuando se presiona la tecla ESC."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super(GUI_Table, self).keyPressEvent(event)

    def closeEvent(self, event):
        if self.sg_manager:
            self.sg_manager.close()
            self.sg_manager = None
        super(GUI_Table, self).closeEvent(event)


class ColorMixDelegate(QStyledItemDelegate):
    def __init__(
        self, table_widget, background_colors, mix_color=(88, 88, 88), parent=None
    ):
        super(ColorMixDelegate, self).__init__(parent)
        self.table_widget = table_widget
        self.background_colors = background_colors
        self.mix_color = mix_color

    def paint(self, painter, option, index):
        row = index.row()
        column = index.column()
        if option.state & QStyle.State_Selected:
            original_color = QColor(self.background_colors[row][column])
            mixed_color = self.mix_colors(
                (original_color.red(), original_color.green(), original_color.blue()),
                self.mix_color,
            )
            option.palette.setColor(QPalette.Highlight, QColor(*mixed_color))
        else:
            original_color = QColor(self.background_colors[row][column])
            option.palette.setColor(QPalette.Base, original_color)
        super(ColorMixDelegate, self).paint(painter, option, index)

    def mix_colors(self, original_color, mix_color):
        r1, g1, b1 = original_color
        r2, g2, b2 = mix_color
        return ((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)


class HieroOperations:
    """Clase para manejar operaciones en Hiero."""

    def __init__(self, shotgrid_manager, gui_table):
        self.sg_manager = shotgrid_manager
        self.gui_table = gui_table  # Almacenar la referencia a GUI_Table
        self.hiero_status_dict = {
            "v_00": "#8a8a8a",
            "Rev Dir Den": "#4d21a8",
        }

    def parse_exr_name(self, file_name):
        """Extrae el nombre base del archivo y el numero de version con prefijo."""
        debug_print(f"Parseando nombre de archivo: {file_name}")

        # Usar función compartida para limpiar el nombre base
        base_name = clean_base_name(file_name)
        debug_print(f"Base name limpio: {base_name}")

        # Buscar versión en el nombre original (antes de limpiar)
        version_match = re.search(r"(_v\d+)", file_name)
        version_str = version_match.group(1) if version_match else "_vUnknown"
        debug_print(f"Version string extraida: {version_str}")

        return base_name, version_str

    def get_current_clip_color(self, item):
        """Obtiene el color actual del clip."""
        try:
            # Verificar si el clip tiene media presente antes de intentar acceder a propiedades
            if not item.source().mediaSource().isMediaPresent():
                debug_print(f"Clip offline detectado: {item.name()}")
                return None

            bin_item = item.source().binItem()
            if bin_item:
                active_version = bin_item.activeVersion()
                if active_version:
                    current_color = bin_item.color()
                    return current_color.name()  # Retorna el color en formato hexadecimal
        except Exception as e:
            debug_print(f"Error obteniendo color del clip {item.name()}: {e}")
            return None
        return None

    def add_row_to_table(
        self,
        table,
        gui_table,
        shot_code,
        version_number,
        prev_status,
        prev_color,
        new_status,
        new_color,
        sg_version_number,
        sg_status,
    ):
        row_count = table.rowCount()
        table.insertRow(row_count)
        # Extraer numeros de version de forma segura
        version_num = extract_version_number(version_number)
        sg_version_num = extract_version_number(sg_version_number)
        # Anadir un espacio al final de cada texto para mejorar la visualizacion
        shot_item = QTableWidgetItem(shot_code + "   ")
        version_item = QTableWidgetItem(str(version_num))
        sg_version_item = QTableWidgetItem(str(sg_version_num))
        sg_status_item = QTableWidgetItem(sg_status)
        prev_status_item = QTableWidgetItem(" " + prev_status + " ")
        new_status_item = QTableWidgetItem(new_status)
        # Centrado de algunas columnas
        version_item.setTextAlignment(Qt.AlignCenter)
        sg_version_item.setTextAlignment(Qt.AlignCenter)
        sg_status_item.setTextAlignment(Qt.AlignCenter)
        # Configuracion de color de fondo y texto para el nombre del shot
        # shot_color_bg = QColor('#323232')  # Color oscuro para el fondo
        # shot_color_text = QColor('#c8c8c8')  # Texto blanco para mejor contraste
        # shot_item.setBackground(QBrush(shot_color_bg))
        # shot_item.setForeground(QBrush(shot_color_text))
        # Configuracion del color de fondo para la columna v_SG basada en la condicion especifica
        if sg_version_num > version_num:  # Condicion para pintar la columna v_SG
            sg_version_item.setBackground(QBrush(QColor("#81395a")))
            sg_version_item.setForeground(
                QBrush(QColor("#c8c8c8"))
            )  # Texto blanco para mejor contraste
        # Configuracion del color de fondo para la columna v_Status basada en la condicion especifica
        if sg_status == "rev":  # Condicion para pintar la columna v_Status
            sg_status_item.setBackground(QBrush(QColor("#81395a")))
            sg_status_item.setForeground(
                QBrush(QColor("#c8c8c8"))
            )  # Texto blanco para mejor contraste
        # Configuracion de colores para columna de estado previo y nuevo
        prev_status_bg_color = QColor(prev_color)
        prev_status_text_color = self.color_for_background(prev_color)
        prev_status_item.setBackground(QBrush(prev_status_bg_color))
        prev_status_item.setForeground(QBrush(prev_status_text_color))
        prev_status_item.setTextAlignment(Qt.AlignCenter)
        new_status_bg_color = QColor(new_color)
        new_status_text_color = self.color_for_background(new_color)
        new_status_item.setBackground(QBrush(new_status_bg_color))
        new_status_item.setForeground(QBrush(new_status_text_color))
        new_status_item.setTextAlignment(Qt.AlignCenter)
        # Anadir los items a la fila
        table.setItem(row_count, 0, shot_item)
        table.setItem(row_count, 1, version_item)
        table.setItem(row_count, 2, sg_version_item)
        table.setItem(row_count, 3, sg_status_item)
        table.setItem(row_count, 4, prev_status_item)
        table.setItem(row_count, 5, new_status_item)
        # Configuracion de colores que se agregan a la lista para la linea de seleccion
        row_colors = ["#8a8a8a"] * 6  # Color por defecto para todas las columnas
        if sg_version_num > version_num:  # Si la version SG es mayor que la version NKS
            row_colors[2] = "#81395a"  # Color para la columna v_SG
        if sg_status == "rev":  # Si el estado es "rev"
            row_colors[3] = "#81395a"  # Color para la columna v_Status
        row_colors[4] = prev_color  # Color para la columna de estado previo
        row_colors[5] = new_color  # Color para la columna de nuevo estado
        gui_table.add_color_to_background_list(
            row_colors
        )  # Anadir la lista de colores al final del metodo
        table.resizeColumnsToContents()

    def luminance(self, color):
        """Calcula la luminancia de un color para determinar si es claro u oscuro."""
        red = color.red()
        green = color.green()
        blue = color.blue()
        return 0.299 * red + 0.587 * green + 0.114 * blue

    def color_for_background(self, hex_color):
        """Determina el color del texto basado en el color de fondo."""
        color = QColor(hex_color)
        return "#ffffff" if self.luminance(color) < 128 else "#000000"

    def change_clip_color(self, item, new_color_hex, task_status, task_name, shot_code):
        try:
            current_color_hex = self.get_current_clip_color(item)
            current_status = self.get_status_name_by_color(current_color_hex)

            # Si no se puede obtener el color actual (clip offline), asumir estado desconocido
            if current_color_hex is None:
                debug_print(f"No se puede obtener color actual del clip {item.name()}, asumiendo estado desconocido")
                current_status = "Unknown"

            # No cambiar el color si las condiciones especificas se cumplen
            if current_color_hex == new_color_hex:
                return ""
            if current_status == "v_00" and (
                task_status == "Not Ready To Start" or task_status == "Ready To Start"
            ):
                return ""
            if task_status == "In Progress" and current_status != "v_00":
                return ""

            # Verificar si el clip tiene media presente antes de intentar cambiar el color
            if not item.source().mediaSource().isMediaPresent():
                debug_print(f"No se puede cambiar color del clip offline: {item.name()}")
                return ""

            # Cambia el color del clip si no se cumplen las condiciones anteriores
            new_color = QColor(new_color_hex)
            bin_item = item.source().binItem()
            if not bin_item:
                debug_print(f"No se puede obtener binItem para el clip: {item.name()}")
                return ""

            previous_color_hex = current_color_hex if current_color_hex else "None"
            bin_item.setColor(new_color)
            # Formatea los nombres y colores de los estados para el mensaje
            text_color = self.color_for_background(new_color_hex)
            status_format = f"<span style='background-color: {new_color_hex}; color: {text_color};'>{task_status}</span>"
            previous_status_format = f"<span style='background-color: {previous_color_hex}; color: {self.color_for_background(previous_color_hex)};'>{current_status}</span>"
            return f"{shot_code} | {task_name} | {previous_status_format} -> {status_format}<br>"
        except Exception as e:
            debug_print(f"Error cambiando color del clip {item.name()}: {e}")
            return ""

    def get_status_name_by_color(self, color_hex):
        """Devuelve el nombre del estado basado en el color."""
        # Verificar primero en el diccionario de Hiero
        for status, color in self.hiero_status_dict.items():
            if color == color_hex:
                return status
        # Si no se encuentra en Hiero, buscar en el diccionario de ShotGrid
# El orden de los valores es:
        # (nombre en Flow/ShotGrid, color_hex[, tag XYplorer])
        for status, (name, color, tag) in self.sg_manager.task_status_dict.items():
            if color == color_hex:
                return name
        return "Unknown"

    def add_custom_tag_to_clip(
        self, clip, tag_name, tag_description, tag_icon, assignee
    ):
        """Anade un tag personalizado a un clip con una descripcion dinamica y un assignee separado."""
        new_tag = hiero.core.Tag(tag_name)
        new_tag.setIcon(tag_icon)
        # Anadir la nota
        safe_description = str(tag_description) if tag_description is not None else "-"
        new_tag.setNote(safe_description)
        # Anadir el assignee en los metadatos con la clave "Assignee" y espacio adicional
        safe_assignee = str(assignee).strip() if assignee is not None else ""
        formatted_assignee = (safe_assignee + " ") if safe_assignee else ""
        new_tag.metadata().setValue("tag.Assignee", formatted_assignee)
        clip.addTag(new_tag)
        debug_print(
            f"Added tag '{tag_name}' with note '{safe_description}' and assignee '{formatted_assignee}' to clip: {clip.name()}"
        )

    def process_selected_clips(self, table, sg_manager):
        seq = hiero.ui.activeSequence()
        changes_made = False
        if seq:
            te = hiero.ui.getTimelineEditor(seq)
            selected_clips = te.selection()

            # Si force_all_clips es True, obtener solo los clips del track TRACK_comp_EXR
            if (
                hasattr(self.gui_table, "force_all_clips")
                and self.gui_table.force_all_clips
            ):
                # Si force_all_clips es True, obtener todos los clips directamente
                all_tracks = seq.videoTracks()
                selected_clips = []
                for track in all_tracks:
                    # Procesar clips de todos los task tracks registrados
                    if track.name() in TASK_EXR_TRACKS:
                        selected_clips.extend(track.items())
                        debug_print(f"Procesando clips del track: {track.name()}")
            elif not selected_clips:
                # Comportamiento original cuando no hay selección
                all_tracks = seq.videoTracks()
                selected_clips = []
                for track in all_tracks:
                    selected_clips.extend(track.items())

            if selected_clips:
                project = hiero.core.projects()[0]
                for clip in selected_clips:
                    try:
                        debug_print(f"Procesando clip: {clip.name()}")
                        if isinstance(clip, hiero.core.EffectTrackItem):
                            debug_print(f"Ignore effect item: {clip.name()}")
                            continue
                        # Borrar los tags del clip antes de procesarlo
                        delete_tags_from_clip(clip)
                        file_path = (
                            clip.source().mediaSource().fileinfos()[0].filename()
                            if clip.source().mediaSource().fileinfos()
                            else None
                        )
                        debug_print(f"File path obtenido: {file_path}")
                        if not file_path:
                            debug_print(
                                f"No se pudo obtener file_path para el clip: {clip.name()}"
                            )
                            continue

                        file_basename = os.path.basename(file_path).lower()
                        debug_print(f"Basename del archivo: {file_basename}")

                        if "_comp_" not in file_basename:
                            debug_print(
                                f"El archivo no contiene '_comp_' en el nombre: {file_basename}"
                            )
                            continue
                        exr_name = os.path.basename(file_path)
                        debug_print(f"Nombre del archivo extraido: {exr_name}")

                        base_name, version_str = self.parse_exr_name(exr_name)
                        debug_print(
                            f"Base name: {base_name}, Version string: {version_str}"
                        )

                        version_number = extract_version_number(
                            version_str
                        )  # Use extracted version number
                        debug_print(f"Version extraida: {version_number} de {version_str}")

                        # Usar funciones compartidas para extraer información
                        project_name = extract_project_name(base_name)
                        debug_print(f"Project name: {project_name}")

                        shot_code = extract_shot_code(base_name)
                        debug_print(f"Shot code: {shot_code}")

                        # Extraer task_name usando función compartida
                        task_name_extracted = extract_task_name(base_name)
                        if task_name_extracted:
                            task_name = task_name_extracted.lower()
                        else:
                            # Fallback: buscar task antes de la versión en el nombre original
                            parts_original = exr_name.split("_")
                            version_index = None
                            # Buscar índice de versión en el nombre original
                            version_match = re.search(r"_v(\d+)", exr_name)
                            if version_match:
                                version_str_clean = version_match.group(1)
                                try:
                                    version_index = parts_original.index(f"v{version_str_clean}")
                                except ValueError:
                                    try:
                                        version_index = parts_original.index(version_str_clean)
                                    except ValueError:
                                        pass
                            
                            if version_index and version_index > 0:
                                task_name = parts_original[version_index - 1].lower()
                            else:
                                # Último recurso: buscar 'comp' en el nombre
                                if "comp" in base_name.lower():
                                    task_name = "comp"
                                else:
                                    task_name = "unknown"
                        
                        debug_print(f"Task name: {task_name}")
                    except Exception as e:
                        debug_print(f"Error procesando clip {clip.name()}: {e}")
                        import traceback
                        debug_print(f"Traceback completo: {traceback.format_exc()}")
                        continue

                    # Obtener la ruta base del shot (subimos un nivel adicional)
                    # Solo calcular si file_path es una ruta completa
                    # Usar os.path.normpath para normalizar separadores y luego dividir
                    normalized_path = os.path.normpath(file_path)
                    path_parts = normalized_path.split(os.sep)
                    debug_print(f"Ruta normalizada: {normalized_path}")
                    debug_print(f"Partes de la ruta: {len(path_parts)} - {path_parts}")

                    if os.path.isabs(file_path) and len(path_parts) >= 5:
                        shot_base_path = os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
                        )
                        debug_print(f"Ruta base del shot calculada: {shot_base_path}")
                    else:
                        shot_base_path = ""  # Ruta inválida
                        debug_print(f"Ruta base del shot: VACIA (no se puede calcular)")
                    debug_print(f"Ruta base del shot final: {shot_base_path}")
                    # Obtener el estado y el tag correspondiente
                    debug_print(
                        f"Buscando shot en SG: project='{project_name}', shot='{shot_code}'"
                    )
                    shot = sg_manager.find_shot(project_name, shot_code)
                    if shot:
                        debug_print(f"Shot encontrado: {shot_code}")
                        debug_print(f"Buscando task '{task_name}' en el shot")
                        task = sg_manager.find_task(shot, task_name)
                        if task:
                            debug_print(f"Task encontrada: {task_name}")
                            task_status_code = task["task_status"]
                            debug_print(f"task_status_code: '{task_status_code}'")
                            task_status_name, new_color_hex, xyplorer_tag = (
# El orden de los valores es:
                                # (nombre en Flow/ShotGrid, color_hex[, tag XYplorer])
                                sg_manager.task_status_dict.get(
                                    task_status_code,
                                    ("Estado desconocido", "#000000", None),
                                )
                            )
                            debug_print(f"task_status_name: '{task_status_name}', new_color_hex: '{new_color_hex}', xyplorer_tag: '{xyplorer_tag}'")
                            # Aplicar el tag correspondiente en XYplorer solo si XYPlorer_Tags es True y tenemos una ruta válida
                            debug_print(f"XYPlorer_Tags: {XYPlorer_Tags}, shot_base_path: '{shot_base_path}', xyplorer_tag: '{xyplorer_tag}'")
                            if XYPlorer_Tags and shot_base_path and xyplorer_tag:
                                debug_print(f"Llamando a tag_shot_folder con path='{shot_base_path}', tag='{xyplorer_tag}'")
                                tag_shot_folder(shot_base_path, xyplorer_tag)
                            else:
                                debug_print(f"No se aplicará tag XYplorer - XYPlorer_Tags: {XYPlorer_Tags}, shot_base_path vacío: {shot_base_path == ''}, xyplorer_tag: {xyplorer_tag}")
                            current_color_hex = self.get_current_clip_color(clip)
                            current_status = self.get_status_name_by_color(
                                current_color_hex
                            )
                            highest_version = sg_manager.find_highest_version_for_shot(
                                shot
                            )
                            if highest_version:
                                debug_print(
                                    f"Version mas alta en SG: {highest_version['version_number']}"
                                )
                            else:
                                debug_print("No se encontro version en SG")
                            sg_version_str = (
                                highest_version["version_number"]
                                if highest_version
                                else "No info"
                            )
                            sg_version_number = extract_version_number(
                                sg_version_str
                            )  # Use extracted SG version number
                            sg_status = (
                                highest_version["version_status"]
                                if highest_version
                                else "No info"
                            )
                            sg_description = (
                                highest_version["version_description"]
                                if highest_version
                                and "version_description" in highest_version
                                else "No description available"
                            )
                            # Obtener el nombre del asignado si existe
                            assignee = task.get("task_assigned_to", "No assignee")
                            debug_print(f"Assignee: {assignee}")
                            # Mantener sg_description sin el assignee
                            change = self.change_clip_color(
                                clip,
                                new_color_hex,
                                task_status_name,
                                task_name,
                                shot_code,
                            )
                            if change or sg_version_number > version_number:
                                prev_color_hex = (
                                    current_color_hex
                                    if current_color_hex
                                    else "#000000"
                                )
                                self.add_row_to_table(
                                    table,
                                    self.gui_table,
                                    shot_code,
                                    version_str,
                                    current_status,
                                    prev_color_hex,
                                    task_status_name,
                                    new_color_hex,
                                    sg_version_str,
                                    sg_status,
                                )
                                changes_made = True
                                # Recordar si el clip estaba offline antes del cambio de versión
                                was_offline_before_version_change = not clip.source().mediaSource().isMediaPresent()

                                if sg_version_number > version_number:
                                    # comente esta linea para que no agregue tags amarillos
                                    # self.add_custom_tag_to_clip(clip, "Updated Version", sg_description, "icons:TagYellow.png", assignee)
                                    highest_version = self.change_to_highest_version(
                                        clip
                                    )
                                    # Extraer el nuevo numero de version del clip actualizado
                                    if highest_version:
                                        new_version_str = highest_version.name().split(
                                            "_v"
                                        )[-1]
                                        new_version_number = int(new_version_str)
                                    else:
                                        new_version_number = version_number

                                    # Si el clip estaba offline antes del cambio de versión, intentar cambiar el color nuevamente
                                    if was_offline_before_version_change and highest_version:
                                        debug_print(f"Clip estaba offline antes del cambio de versión, intentando cambiar color nuevamente: {clip.name()}")
                                        # Reintentar cambio de color ahora que el clip debería estar online
                                        retry_color_change = self.change_clip_color(
                                            clip,
                                            new_color_hex,
                                            task_status_name,
                                            task_name,
                                            shot_code,
                                        )
                                        if retry_color_change:
                                            debug_print(f"Color cambiado exitosamente después del cambio de versión: {clip.name()}")
                                            change = retry_color_change  # Actualizar el mensaje de cambio
                                        else:
                                            debug_print(f"No se pudo cambiar color incluso después del cambio de versión: {clip.name()}")

                                    # Volver a comparar con la version de SG
                                    if sg_version_number > new_version_number:
                                        self.add_custom_tag_to_clip(
                                            clip,
                                            "Version Mismatch",
                                            f"SG Version: {sg_version_str}",
                                            "icons:TagRed.png",
                                            assignee,
                                        )
                        else:
                            debug_print(
                                f"No se encontro task '{task_name}' para el shot '{shot_code}'"
                            )
                            debug_print(
                                f"Tasks disponibles en el shot: {[t['task_type'] for t in shot['tasks']]}"
                            )
                            pass
                    else:
                        debug_print(
                            f"No se encontro shot '{shot_code}' en el proyecto '{project_name}'"
                        )
                        pass
                # Llamar a enable_or_disable_clips al final del proceso
                self.enable_or_disable_clips(selected_clips)
            else:
                debug_print("No clips found in the timeline.")
                pass
        else:
            debug_print("No active sequence found in Hiero.")
            pass
        return changes_made

    def get_highest_version(self, binItem):
        """Obtiene la version mas alta de un binItem."""
        versions = binItem.items()
        debug_print(f"Versiones disponibles para {binItem.name()}:")
        for v in versions:
            debug_print(f"  - {v.name()}")
        try:
            highest_version = max(
                versions, key=lambda v: extract_version_number(v.name())
            )
            debug_print(f"Version mas alta seleccionada: {highest_version.name()}")
            return highest_version
        except Exception as e:
            debug_print(f"Error al obtener la version mas alta: {e}")
            return None

    def change_to_highest_version(self, clip):
        """Cambia el clip a la versión mas alta disponible incluso si está offline."""
        debug_print(f"Cambiando a la version mas alta para el clip: {clip.name()}")
        try:
            # Si el clip está offline seguimos adelante igual: Hiero permite cambiar la
            # versión aunque no haya media presente, por lo que solo lo registramos.
            if not clip.source().mediaSource().isMediaPresent():
                debug_print(f"Clip offline, intentando igual cambiar version: {clip.name()}")

            debug_print(f"Obteniendo binItem para clip: {clip.name()}")
            binItem = clip.source().binItem()
            if not binItem:
                debug_print(f"No se puede obtener binItem para el clip: {clip.name()}")
                return None
            debug_print(f"binItem obtenido exitosamente: {binItem.name()}")

            debug_print(f"Obteniendo version activa para clip: {clip.name()}")
            activeVersion = binItem.activeVersion()
            if not activeVersion:
                debug_print(f"No hay version activa para el clip: {clip.name()}")
                return None
            debug_print(f"Version activa obtenida: {activeVersion.name()}")

            debug_print(f"Creando VersionScanner para clip: {clip.name()}")
            vc = hiero.core.VersionScanner()
            debug_print(f"VersionScanner creado, ejecutando doScan...")
            vc.doScan(activeVersion)
            debug_print(f"doScan completado para clip: {clip.name()}")

            debug_print(f"Obteniendo version mas alta para binItem: {binItem.name()}")
            highest_version = self.get_highest_version(binItem)
            if highest_version:
                debug_print(f"Version mas alta encontrada: {highest_version.name()}")
                debug_print(f"Ejecutando setActiveVersion para clip: {clip.name()}")
                binItem.setActiveVersion(highest_version)
                debug_print(f"setActiveVersion completado exitosamente para clip: {clip.name()}")

                # Si el clip estaba offline, intentar ponerlo online después del cambio de versión
                was_offline = not clip.source().mediaSource().isMediaPresent()
                if was_offline:
                    debug_print(f"Clip estaba offline, intentando reconectar media después del cambio de versión")
                    try:
                        # Intentar reconnectMedia primero (más específico para clips offline)
                        clip.source().reconnectMedia()
                        debug_print(f"reconnectMedia ejecutado para clip: {clip.name()}")
                    except Exception as reconnect_error:
                        debug_print(f"Error en reconnectMedia, intentando refresh: {reconnect_error}")
                        try:
                            # Fallback: usar refresh
                            clip.source().mediaSource().refresh()
                            debug_print(f"Media refresh ejecutado como fallback para clip: {clip.name()}")
                        except Exception as refresh_error:
                            debug_print(f"Error en media refresh fallback: {refresh_error}")

                    # Verificar si ahora está online
                    if clip.source().mediaSource().isMediaPresent():
                        debug_print(f"Clip ahora está online después del cambio de versión: {clip.name()}")
                    else:
                        debug_print(f"Clip sigue offline después del cambio de versión: {clip.name()}")
            else:
                debug_print("No se pudo determinar la version mas alta")
            return highest_version
        except Exception as e:
            debug_print(f"Error cambiando version del clip {clip.name()}: {e}")
            import traceback
            debug_print(f"Traceback completo: {traceback.format_exc()}")
            return None

    def enable_or_disable_clips(self, selected_clips):
        try:
            seq = hiero.ui.activeSequence()
            if not seq:
                debug_print("No active sequence found for enable/disable operation")
                return
            
            # Estados de review que deben habilitarse
            review_status_colors = {
                "#bd7f9f",  # rev_su - Review Sup
                "#a9909d",  # revcha - Review Charly
                "#7F4B69",  # revjua - Review Juano
                "#9c3e5e",  # revjav - Review Javi
                "#69135e",  # revleg - Review Lega
            }
            
            for item in selected_clips:
                if not isinstance(item, hiero.core.EffectTrackItem):
                    # Encontrar el track del clip
                    clip_track = None
                    for track in seq.videoTracks():
                        if item in track.items():
                            clip_track = track
                            break
                    
                    # Solo procesar clips de los task tracks registrados (comp, roto, etc.)
                    if clip_track and clip_track.name() not in TASK_EXR_TRACKS:
                        debug_print(f"Clip '{item.name()}' no está en ningún task track, saltando")
                        continue
                    
                    file_path = (
                        item.source().mediaSource().fileinfos()[0].filename()
                        if item.source().mediaSource().fileinfos()
                        else None
                    )
                    
                    if file_path:
                        filename = os.path.basename(file_path)
                        # Obtener el color actual del clip para verificar si está en review
                        current_color_hex = self.get_current_clip_color(item)

                        # Patrón regex para detectar versiones de 2 o 3 dígitos en cualquier task track
                        # Ej: _comp_v007, _roto_v003, _cmp_v01
                        task_pattern = "|".join(t.strip("_") for t in TASK_EXR_TRACKS) + "|cmp"
                        version_pattern = re.compile(rf'_(?:{task_pattern})_v(\d{{2,3}})', re.IGNORECASE)
                        version_match = version_pattern.search(filename.lower())
                        
                        # Si el clip está en un estado de review, habilitarlo
                        if current_color_hex and current_color_hex.lower() in [c.lower() for c in review_status_colors]:
                            item.setEnabled(True)
                            version_info = f" (versión v{version_match.group(1)})" if version_match else " (sin versión detectada)"
                            debug_print(f"Clip '{item.name()}' habilitado por estar en estado de review (color: {current_color_hex}){version_info}")
                        # Si es v00 o v000 (versión cero), deshabilitarlo
                        elif version_match:
                            version_number = version_match.group(1)
                            if version_number == '00' or version_number == '000':
                                item.setEnabled(False)
                                debug_print(f"Clip '{item.name()}' deshabilitado (versión v{version_number})")
                            else:
                                item.setEnabled(True)
                                debug_print(f"Clip '{item.name()}' habilitado (versión v{version_number})")
                        else:
                            item.setEnabled(True)
                            debug_print(f"Clip '{item.name()}' habilitado (sin versión detectada)")
                    else:
                        item.setEnabled(True)
        except Exception as e:
            debug_print(f"Error during enable/disable operation: {e}")


##### Aca empieza la joda del XYplorer


def get_xy_hwnd(xy_class="ThunderRT6FormDC"):
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
    )
    GetClassName = user32.GetClassNameW
    EnumChildWindows = user32.EnumChildWindows
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText = user32.GetWindowTextW
    found_hwnd = None

    def enum_windows_callback(hwnd, lParam):
        nonlocal found_hwnd
        class_name = ctypes.create_unicode_buffer(256)
        GetClassName(hwnd, class_name, 256)
        if class_name.value == xy_class:
            child_count = [0]

            def enum_child_windows_callback(hwnd_child, lParam_child):
                child_count[0] += 1
                return True

            EnumChildWindows(hwnd, EnumWindowsProc(enum_child_windows_callback), 0)
            if child_count[0] >= 10:
                found_hwnd = hwnd
                return False
        return True

    EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
    return found_hwnd


# Determina la arquitectura del sistema
if platform.architecture()[0] == "32bit":
    ULONG_PTR = ctypes.wintypes.ULONG
else:
    ULONG_PTR = ctypes.c_uint64


# Define la estructura COPYDATASTRUCT
class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ("dwData", ULONG_PTR),
        ("cbData", ctypes.wintypes.DWORD),
        ("lpData", ctypes.c_void_p),
    ]


def Send_WM_COPYDATA(xyHwnd, message):
    if not xyHwnd:
        return None
    cds = COPYDATASTRUCT()
    cds.dwData = 4194305
    cds.cbData = len(message.encode("utf-16-le"))
    cds_data = ctypes.create_unicode_buffer(message)
    cds.lpData = ctypes.cast(ctypes.addressof(cds_data), ctypes.c_void_p)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    result = user32.SendMessageW(xyHwnd, 74, 0, ctypes.byref(cds))
    return result


def _tag_shot_folder_thread(shot_base_path, tag):
    """Función que ejecuta el tagging de XYplorer en un thread separado para no bloquear Hiero."""
    debug_print(f"tag_shot_folder_thread started with shot_base_path='{shot_base_path}', tag='{tag}'")
    if tag is None:
        debug_print("Tag is None, returning without action")
        return  # No hacer nada si no hay tag definido para el estado
    try:
        debug_print("Getting XYplorer window handle...")
        hwnd = get_xy_hwnd()
        debug_print(f"XYplorer hwnd: {hwnd}")
        if hwnd:
            tag_command = f"::tag '{tag}', '{shot_base_path}';"
            debug_print(f"Sending command to XYplorer: {tag_command}")
            result = Send_WM_COPYDATA(hwnd, tag_command)
            debug_print(f"Send_WM_COPYDATA result: {result}")
            if result:
                debug_print(f"Tag '{tag}' applied to {shot_base_path}")
            else:
                debug_print(f"Failed to apply tag '{tag}' to {shot_base_path}")
        else:
            debug_print("XYplorer window not found.")
    except Exception as e:
        debug_print(f"Error applying tag in XYplorer: {e}")


def tag_shot_folder(shot_base_path, tag):
    """Inicia el tagging de XYplorer en un thread separado para no bloquear Hiero."""
    global active_xyplorer_threads, logged_xyplorer_mac_notice

    debug_print(f"tag_shot_folder called with shot_base_path='{shot_base_path}', tag='{tag}' - starting thread")

    # En macOS XYplorer no existe, no crear threads ni intentar tags
    if platform.system() == 'Darwin':
        if not logged_xyplorer_mac_notice:
            debug_print("macOS detectado - XYplorer desactivado (no compatible)")
            logged_xyplorer_mac_notice = True
        return

    try:
        # Limpiar threads terminados antes de crear nuevos
        cleanup_finished_threads()

        # Crear y iniciar un thread separado para el tagging de XYplorer
        xyplorer_thread = threading.Thread(
            target=_tag_shot_folder_thread,
            args=(shot_base_path, tag),
            daemon=True  # Thread daemon para que termine cuando termine el programa principal
        )
        xyplorer_thread.start()

        # Agregar thread a la lista de threads activos
        active_xyplorer_threads.append(xyplorer_thread)

        # Determinar si debemos esperar al thread (solo Windows/Linux con Hiero 16+)
        should_wait = False

        try:
            import hiero
            if hasattr(hiero, 'core') and hasattr(hiero.core, 'applicationVersion'):
                version = hiero.core.applicationVersion()
                if version and version.startswith('16'):
                    should_wait = True
                    debug_print(f"Hiero {version} en {platform.system()}, esperando XYplorer thread (PySide6)")
                else:
                    debug_print(f"Hiero {version} en {platform.system()}, XYplorer thread started (PySide2)")
            else:
                debug_print(f"Versión de Hiero no detectable en {platform.system()}, XYplorer thread started")
        except Exception as version_check_error:
            debug_print(f"Error detectando versión Hiero en {platform.system()}: {version_check_error}")
            debug_print("XYplorer thread started (fallback)")

        # Solo esperar si es necesario
        if should_wait:
            xyplorer_thread.join(timeout=5.0)  # Esperar máximo 5 segundos
            if xyplorer_thread.is_alive():
                debug_print(f"Timeout esperando al thread XYplorer")
            else:
                debug_print(f"Thread XYplorer terminado exitosamente")

    except Exception as e:
        debug_print(f"Error starting XYplorer tagging thread: {e}")


def cleanup_finished_threads():
    """Limpia threads de XYplorer que ya terminaron para evitar acumulación."""
    global active_xyplorer_threads

    # Filtrar threads que aún están vivos
    active_xyplorer_threads[:] = [t for t in active_xyplorer_threads if t.is_alive()]

    # Log opcional para debugging
    if len(active_xyplorer_threads) > 5:
        debug_print(f"Advertencia: {len(active_xyplorer_threads)} threads XYplorer activos (posible acumulación)")


##### Aca termina

app = None
window = None


def FPT_Hiero(force_all_clips=False):
    """
    Procesa los clips del timeline.

    Args:
        force_all_clips (bool): Si es True, procesa todos los clips independientemente
                               de la selección actual.
    """
    global app, window, hiero_ops, script_start_time
    # Reiniciar el tiempo de inicio para cada ejecución del pull
    script_start_time = time.time()
    debug_print("Iniciando ejecución del pull...")
    # Selecciona la ruta de la base de datos segun el sistema operativo
    if platform.system() == "Windows":
        db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
    elif platform.system() == "Darwin":
        db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
    else:
        debug_print(f"Sistema operativo no soportado: {platform.system()}")
        return
    if not os.path.exists(db_path):
        debug_print(f"DB file not found at path: {db_path}")
        return
    sg_manager = ShotGridManager(db_path)
    app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)
    window = GUI_Table(sg_manager)
    hiero_ops = HieroOperations(sg_manager, window)
    window.force_all_clips = force_all_clips
    window.set_hiero_ops(hiero_ops)
