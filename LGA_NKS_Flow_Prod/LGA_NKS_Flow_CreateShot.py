"""
____________________________________________________________________________________

  LGA_NKS_Flow_CreateShot v1.34 | Lega
  Script para crear shots en ShotGrid basado en el nombre del clip seleccionado en Hiero
  SIN usar templates predefinidos - crea tasks manualmente para mayor control

  v1.34: Creación automática de estructura de carpetas por task
         Integración con módulo LGA_NKS_Flow_CreateShot_Folders
         Crea carpetas automáticamente después de crear shot y tasks en Flow

  v1.33: Pre-chequeo inteligente de existencia antes de mostrar la UI
         Muestra ventana "Comprobando existencia de los shots en Flow"
         Bloquea la creación si alguno ya existe (multi selección)
         Lanza automáticamente Modify Shot cuando el shot único ya existe

  v1.32: Agregado modo de modificación de shots existentes
         Reutiliza la misma UI compacta de creación
         Permite agregar/eliminar tasks y actualizar la descripción
         No afecta estados ni tiempos de las tasks existentes

  v1.31: Migración al método híbrido centralizado de selección de clips
         Soporte para selección múltiple usando módulo LGA_NKS_GetClip
         Respeta TRACK_comp_EXR del módulo (actualmente "_comp_")

  v1.30: Reducción automática del 30% en tiempo estimado antes de subir a Flow
           (ej: 1 día ingresado → 0.7 días en Flow)

  v1.29: UI compacta - Tasks deshabilitadas ocupan 1 línea sin campos ni divisores
         Checkbox a la izquierda del nombre, columnas aparecen solo cuando se habilita

  v1.28: Todas las tasks del pipeline agregadas con colores específicos
         Comp, Roto, Cleanup, DMP, Model, Retopo, Rigging, Shaders,
         Match Move, Animation, FX, Lighting

  v1.27: Sistema modular de tasks - Fácil agregar nuevas tasks (DRY)
         Agregada task Roto + enable/disable dinámico de campos

  v1.26: UI reorganizada en columnas

  v1.25: Agregado checkbox "High Priority" para asignar sg_prioridad="high"

  v1.24: Mensajes diferenciados para shots existentes vs creados + pipeline step Comp

  v1.23: Sistema de Logging Seguro para Hilos

  v1.22: Agregado campo para tiempo estimado en días (sg_estdias)

  v1.21: Asigna reviewers a la task usando el campo task_reviewers

  v1.20: Creación sin Templates

  v1.10: Sistema Dual de Nomenclatura:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)
_________________________________
"""

import hiero.core
import os
import re
import sys
from pathlib import Path
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt
QApplication = QtWidgets.QApplication
QMessageBox = QtWidgets.QMessageBox
QDialog = QtWidgets.QDialog
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QSizePolicy = QtWidgets.QSizePolicy
QTextEdit = QtWidgets.QTextEdit
QCheckBox = QtWidgets.QCheckBox
QFrame = QtWidgets.QFrame
QLineEdit = QtWidgets.QLineEdit
QFont = QtGui.QFont
QPixmap = QtGui.QPixmap
QRect = QtCore.QRect
QRunnable = QtCore.QRunnable
Slot = QtCore.Slot
QThreadPool = QtCore.QThreadPool
Signal = QtCore.Signal
QObject = QtCore.QObject
QDoubleValidator = QtGui.QDoubleValidator
QTimer = QtCore.QTimer

# Agregar la ruta de shotgun_api3 al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "LGA_ToolPack"))

import shotgun_api3

# Importar el modulo de configuracion segura
sys.path.append(str(Path(__file__).parent.parent / "LGA_NKS_Flow"))
from SecureConfig_Reader import get_flow_credentials

# Importar utilidades de naming
from LGA_NKS_Flow_NamingUtils import (
    extract_shot_code,
    extract_project_name,
    clean_base_name,
)

# Importar módulo centralizado para obtener clips
from pathlib import Path
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clips_to_process, get_clip_to_process
    import LGA_NKS_GetClip as clip_utils
    # La sincronización de DEBUG se hace después de su definición (ver más abajo)

from LGA_NKS_Flow_Task_Config import AVAILABLE_TASKS

# Importar módulo de creación de carpetas
folders_path = Path(__file__).parent
sys.path.insert(0, str(folders_path))
from LGA_NKS_Flow_CreateShot_Folders import create_folders_for_shot_tasks


DEBUG = True
debug_messages = []

# Sincronizar debug con el módulo centralizado de clips (después de definir DEBUG)
if 'clip_utils' in globals():
    clip_utils.DEBUG = DEBUG


def debug_print(message):
    """Imprime un mensaje de debug si la variable DEBUG es True."""
    if DEBUG:
        # Limitar mensajes de debug para evitar memory issues
        if len(debug_messages) < 100:  # Máximo 100 mensajes
            debug_messages.append(str(message))


def print_debug_messages():
    if DEBUG and debug_messages:
        print("\n".join(debug_messages))
        debug_messages.clear()


def get_active_sequence_name():
    """Obtiene el nombre de la secuencia activa en Hiero"""
    try:
        seq = hiero.ui.activeSequence()
        if seq:
            sequence_name = seq.name()
            debug_print(f"Secuencia activa encontrada: {sequence_name}")
            return sequence_name
        else:
            debug_print("ERROR: No se encontro una secuencia activa")
            return None
    except Exception as e:
        debug_print(f"ERROR obteniendo nombre de secuencia: {e}")
        return None


# Funciones para crear thumbnails de shots
def zoom_to_fill_in_viewer():
    """Aplica zoom to fill al viewer actual"""
    viewer = hiero.ui.currentViewer()
    if not viewer:
        debug_print("❌ No hay viewer activo")
        return False

    try:
        player = viewer.player()
        if not player:
            debug_print("❌ No se encontró el player del viewer")
            return False

        player.zoomToFill()
        debug_print("✅ Zoom to Fill aplicado con éxito")
        return True
    except Exception as e:
        debug_print(f"❌ Error aplicando zoomToFill: {e}")
        return False


def crop_to_aspect_ratio(qimage, target_aspect):
    """Recorta la imagen a la relacion de aspecto especificada."""
    width = qimage.width()
    height = qimage.height()

    current_aspect = width / height

    if current_aspect > target_aspect:
        new_width = int(height * target_aspect)
        offset_x = int((width - new_width) / 2)
        rect = QRect(offset_x, 0, new_width, height)
        cropped = qimage.copy(rect)
        return cropped
    else:
        new_height = int(width / target_aspect)
        offset_y = int((height - new_height) / 2)
        rect = QRect(0, offset_y, width, new_height)
        cropped = qimage.copy(rect)
        return cropped


def get_shot_name_from_selected_clip():
    """Obtiene el nombre del shot desde el clip seleccionado o desde el path del archivo.
    Usa el método híbrido centralizado (playhead primero, luego selección como fallback)."""
    sequence = hiero.ui.activeSequence()
    if not sequence:
        debug_print("No se encontró una secuencia activa.")
        return None

    # Usar módulo centralizado para obtener clip (método híbrido)
    # track_name=None para respetar TRACK_comp_EXR del módulo
    clip = get_clip_to_process(track_name=None, prioritize_multiple_selection=False)

    if not clip:
        debug_print("No se encontró clip en playhead ni clips seleccionados.")
        sequence_name = sequence.name()
        debug_print(f"Usando nombre de secuencia: {sequence_name}")
        return sequence_name

    try:
        # Intentar obtener el shot name del clip
        shot_name = clip.name()
        if shot_name:
            debug_print(f"Shot name desde clip.name(): {shot_name}")
            return shot_name
    except:
        pass

    try:
        # Si no hay shot name, extraerlo del path del archivo
        file_path = clip.source().mediaSource().fileinfos()[0].filename()
        debug_print(f"File path: {file_path}")

        # Extraer nombre base del archivo usando utilidades de naming
        exr_name = os.path.basename(file_path)
        base_name = clean_base_name(exr_name)

        # Extraer shot_code usando detección automática de formato
        shot_code = extract_shot_code(base_name)
        if shot_code:
            debug_print(f"Shot code extraído del path: {shot_code}")
            return shot_code
        else:
            debug_print(f"Nombre base del archivo: {base_name}")
            return base_name

    except Exception as e:
        debug_print(f"Error extrayendo shot name del path: {e}")

    # Como último recurso, usar el nombre de la secuencia
    sequence_name = sequence.name()
    debug_print(f"Usando nombre de secuencia como fallback: {sequence_name}")
    return sequence_name


def create_shot_thumbnail():
    """Crea un thumbnail del shot actual y retorna la ruta del archivo creado."""
    # Aplicar zoom to fill primero
    if not zoom_to_fill_in_viewer():
        debug_print("❌ No se pudo aplicar zoom to fill")
        return None

    # Obtener el shot name
    shot_name = get_shot_name_from_selected_clip()
    if not shot_name:
        debug_print("❌ No se pudo obtener el nombre del shot")
        return None

    # Limpiar el shot name para usarlo como nombre de archivo
    shot_name = re.sub(r'[<>:"/\\|?*]', "_", shot_name)  # Remover caracteres inválidos
    debug_print(f"Shot name limpio: {shot_name}")

    # Crear carpeta de cache relativa al script
    script_dir = os.path.dirname(__file__)
    cache_dir = os.path.join(script_dir, "ShotThumbs_Cache")

    # Crear directorio si no existe
    os.makedirs(cache_dir, exist_ok=True)
    debug_print(f"Carpeta de destino: {cache_dir}")

    # Obtener imagen del viewer
    viewer = hiero.ui.currentViewer()
    if not viewer:
        debug_print("❌ No hay viewer activo")
        return None

    qimage = viewer.image()
    if qimage is None or qimage.isNull():
        debug_print("❌ viewer.image() devolvió None o imagen nula")
        return None

    # Obtener la secuencia activa y su relacion de aspecto
    sequence = hiero.ui.activeSequence()
    if sequence is None:
        debug_print("No hay ninguna secuencia activa, usando 16:9 por defecto.")
        target_aspect = 16 / 9
    else:
        format = sequence.format()
        width = format.width()
        height = format.height()
        target_aspect = width / height
        debug_print(
            f"Relación de aspecto de la secuencia: {width} x {height} ({target_aspect:.2f})"
        )

    # Aplicar crop
    qimage_cropped = crop_to_aspect_ratio(qimage, target_aspect)
    debug_print(
        f"Snapshot size (cropped): {qimage_cropped.width()} × {qimage_cropped.height()}"
    )

    # Generar nombre de archivo único
    import time

    timestamp = int(time.time())
    filename = f"{shot_name}_{timestamp}.jpg"
    full_path = os.path.join(cache_dir, filename)

    # Guardar imagen
    ok = qimage_cropped.save(full_path, "JPEG")

    if ok and os.path.exists(full_path):
        debug_print(f"✅ Shot Thumbnail guardado: {filename}")
        debug_print(f"Ruta completa: {full_path}")
        return full_path
    else:
        debug_print("❌ No se pudo crear el archivo.")
        debug_print(f"save() result: {ok}, exists: {os.path.exists(full_path)}")
        return None


# Clase de ventana de configuracion para shots
class ShotConfigDialog(QDialog):
    def __init__(
        self,
        clips_info,
        sequence_name=None,
        parent=None,
        dialog_mode="create",
        action_button_label=None,
        allow_thumbnail_creation=True,
    ):
        super(ShotConfigDialog, self).__init__(parent)
        self.dialog_mode = dialog_mode
        self.allow_thumbnail_creation = allow_thumbnail_creation
        self.setWindowTitle(
            "Flow | Modify Shot" if dialog_mode == "modify" else "Flow | Shot Creation"
        )
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.clips_info = clips_info
        self.sequence_name = sequence_name
        self.shot_config = None
        self.existing_tasks = set()
        
        # Diccionario para almacenar widgets de tasks dinámicamente
        # Estructura: {task_name: {widget_key: widget_object}}
        self.task_widgets = {}

        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Titulo
        title_text = (
            "Configuracion para modificar shots"
            if dialog_mode == "modify"
            else "Configuracion para crear shots"
        )
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #CCCCCC; padding: 5px;")
        layout.addWidget(title_label)

        # Informacion de clips
        clips_label = QLabel(f"Se van a procesar {len(self.clips_info)} clips:")
        clips_label.setStyleSheet("color: #CCCCCC; padding: 2px 5px 0px 5px;")
        layout.addWidget(clips_label)

        # Lista de clips
        for clip_info in self.clips_info:
            clip_frame = QFrame()
            clip_frame.setStyleSheet(
                "border: none; border-radius: 3px; margin: 1px; padding: 2px;"
            )
            clip_layout = QVBoxLayout(clip_frame)

            project_shot_label = QLabel(
                f"<span style='color: #6AB5CA;'>{clip_info['project_name']}</span> / <span style='color: #B56AB5;'>{clip_info['shot_code']}</span>"
            )
            project_shot_label.setTextFormat(Qt.RichText)
            clip_layout.addWidget(project_shot_label)

            layout.addWidget(clip_frame)

        # Espacio pequeño antes del separador
        layout.addSpacing(5)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #444444; margin: 0px;")
        layout.addWidget(separator)

        # Espacio pequeño después del separador
        layout.addSpacing(5)

        # Layout horizontal para thumbnail y descripción
        thumbnail_description_layout = QHBoxLayout()

        # Columna izquierda: Thumbnail (primera columna)
        self.thumbnail_placeholder_layout = QVBoxLayout()
        thumbnail_label = QLabel("Shot Thumbnail:")
        thumbnail_label.setStyleSheet(
            "color: #CCCCCC; font-weight: bold; padding-top: 5px;"
        )
        self.thumbnail_placeholder_layout.addWidget(thumbnail_label)

        # Placeholder para el thumbnail con tamaño fijo igual a la descripción
        self.thumbnail_placeholder = QLabel()
        self.thumbnail_placeholder.setFixedSize(120, 80)  # Ancho proporcional, altura igual al campo de descripción
        self.thumbnail_placeholder.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #555555;
                border-radius: 3px;
                background-color: #1a1a1a;
                color: #666666;
                text-align: center;
                padding: 5px;
            }
        """
        )
        self.thumbnail_placeholder.setText("Thumbnail\n(120x80)")
        self.thumbnail_placeholder.setAlignment(Qt.AlignCenter)
        self.thumbnail_placeholder_layout.addWidget(self.thumbnail_placeholder)

        thumbnail_description_layout.addLayout(self.thumbnail_placeholder_layout, 1)  # Stretch factor reducido para dar más espacio a descripción

        # Espacio entre columnas
        thumbnail_description_layout.addSpacing(20)

        # Columna derecha: Descripción del shot (segunda columna)
        description_layout = QVBoxLayout()
        desc_label = QLabel("Shot Description:")
        desc_label.setStyleSheet(
            "color: #CCCCCC; font-weight: bold; padding-top: 5px;"
        )
        description_layout.addWidget(desc_label)

        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(80)  # 3 lineas aproximadamente
        self.description_text.setPlainText("")
        self.description_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 5px;
                border-radius: 3px;
            }
        """
        )
        description_layout.addWidget(self.description_text)
        thumbnail_description_layout.addLayout(description_layout, 3)  # Stretch factor mayor para más espacio horizontal

        # Layout de 3 columnas principales: [Thumb+Desc] | [Sequence] | [Status+Priority]
        main_three_column_layout = QHBoxLayout()

        # Columna 1: Thumbnail + Descripción del shot (ya creado arriba)
        main_three_column_layout.addLayout(thumbnail_description_layout, 4)  # Stretch factor mayor para dar más espacio al shot description

        # Espacio entre columnas principales
        main_three_column_layout.addSpacing(30)

        # Columna 2: Sequence
        sequence_column_layout = QVBoxLayout()
        seq_label = QLabel("Sequence:")
        seq_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 5px;")
        sequence_column_layout.addWidget(seq_label)

        self.sequence_line_edit = QLineEdit()
        self.sequence_line_edit.setText(self.sequence_name)
        self.sequence_line_edit.setMaximumWidth(120)  # Limitar ancho máximo
        self.sequence_line_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 5px;
                border-radius: 3px;
                height: 20px;
            }
        """
        )
        sequence_column_layout.addWidget(self.sequence_line_edit)

        # Espaciador para alinear hacia arriba
        sequence_column_layout.addStretch()

        main_three_column_layout.addLayout(sequence_column_layout, 1)  # Stretch factor 1

        # Espacio entre segunda y tercera columna
        main_three_column_layout.addSpacing(30)

        # Columna 3: Shot status + Priority (layout vertical)
        status_priority_column_layout = QVBoxLayout()

        # Shot status (arriba)
        shot_status_layout = QVBoxLayout()
        shot_status_label = QLabel("Shot status:")
        shot_status_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 5px;")
        shot_status_layout.addWidget(shot_status_label)

        self.shot_ready_cb = QCheckBox("Ready to start")
        self.shot_ready_cb.setChecked(True)  # Activado por defecto
        self.shot_ready_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        shot_status_layout.addWidget(self.shot_ready_cb)
        status_priority_column_layout.addLayout(shot_status_layout)

        # Espacio entre status y priority
        status_priority_column_layout.addSpacing(10)

        # Priority (abajo)
        priority_layout = QVBoxLayout()
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 5px;")
        priority_layout.addWidget(priority_label)

        self.high_priority_cb = QCheckBox("High")
        self.high_priority_cb.setChecked(False)  # Desactivado por defecto
        self.high_priority_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        priority_layout.addWidget(self.high_priority_cb)
        status_priority_column_layout.addLayout(priority_layout)

        main_three_column_layout.addLayout(status_priority_column_layout, 1)  # Stretch factor reducido

        layout.addLayout(main_three_column_layout)

        # Campo de tiempo estimado en días (se agrega en el layout de 5 columnas más abajo)
        self.estimated_days_line_edit = QLineEdit()
        self.estimated_days_line_edit.setText("0")
        self.estimated_days_line_edit.setMaxLength(5)  # Permitir decimales (ej: 12.5)
        self.estimated_days_line_edit.setFixedWidth(80)  # Ancho mayor para decimales
        self.estimated_days_line_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 5px;
                border-radius: 3px;
                height: 20px;
            }
        """
        )
        # Validación para números decimales
        validator = QDoubleValidator(0.0, 99.9, 1)  # Mínimo 0, máximo 99.9, 1 decimal
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.estimated_days_line_edit.setValidator(validator)

        # Espacio pequeño antes del separador
        layout.addSpacing(10)

        # ==================================================================================
        # GENERACIÓN DINÁMICA DE TASKS
        # ==================================================================================
        # Generar una sección para cada task configurada
        for task_config in AVAILABLE_TASKS:
            # Separador antes de cada task
            task_separator = QFrame()
            task_separator.setFrameShape(QFrame.HLine)
            task_separator.setFrameShadow(QFrame.Sunken)
            task_separator.setStyleSheet("color: #444444;")
            layout.addWidget(task_separator)
            
            # Espaciado pequeño y consistente después del separador
            layout.addSpacing(1)
            
            # Crear fila de task
            task_layout = self.create_task_row(task_config, task_separator)
            layout.addLayout(task_layout)

        # Thumbnail del shot (solo si hay un clip seleccionado)
        self.thumbnail_label = None
        self.thumbnail_path = None
        debug_print(f"[INFO] Numero de clips seleccionados: {len(self.clips_info)}")
        if self.allow_thumbnail_creation and len(self.clips_info) == 1:
            debug_print("[INFO] Creando thumbnail para clip unico...")
            self.create_and_show_thumbnail()
        else:
            debug_print("[INFO] No se crea thumbnail (modo modify o multiples clips)")

        # Espaciador
        layout.addStretch()

        # Botones
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #CCCCCC;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """
        )
        button_layout.addWidget(self.cancel_button)

        button_layout.addSpacing(10)  # Espacio pequeño entre botones

        button_text = action_button_label
        if not button_text:
            button_text = "Modify Shot" if dialog_mode == "modify" else "Create Shot"
        self.create_button = QPushButton(button_text)
        self.create_button.clicked.connect(self.accept_config)
        self.create_button.setStyleSheet(
            """
            QPushButton {
                background-color: #443a91;
                color: #b2b2b2;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #774dcb;
                color: #CCCCCC;
            }
        """
        )
        button_layout.addWidget(self.create_button)

        layout.addLayout(button_layout)

        # Estilo general del dialogo
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
        """
        )

    def create_task_row(self, task_config, task_separator):
        """
        Crea una fila de UI para una task de forma dinámica.
        
        Args:
            task_config (dict): Configuración de la task con keys: name, pipeline_step, enabled_by_default, color
            task_separator (QFrame): Separador asociado a esta task (para ocultarlo cuando está deshabilitada)
            
        Returns:
            QHBoxLayout: Layout con todos los widgets de la task
        """
        task_name = task_config["name"]
        enabled_by_default = task_config["enabled_by_default"]
        task_color = task_config.get("color", "#6AB5CA")  # Color por defecto si no está especificado
        
        # Inicializar diccionario para esta task
        self.task_widgets[task_name] = {}
        self.task_widgets[task_name]["separator"] = task_separator
        
        # Layout principal de 5 columnas
        task_layout = QHBoxLayout()

        # ===== Columna 1: Checkbox Enable y Nombre de Task =====
        name_layout = QHBoxLayout()  # Cambiado a horizontal
        name_layout.setSpacing(1)  # Espacio pequeño entre checkbox y nombre
        name_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes adicionales
        
        enabled_cb = QCheckBox("")  # Checkbox sin texto
        enabled_cb.setChecked(enabled_by_default)
        enabled_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        name_layout.addWidget(enabled_cb)
        
        name_label = QLabel(task_name.upper())
        name_label.setStyleSheet(f"color: {task_color}; font-weight: bold; padding-top: 0px; font-size: 12px;")
        name_layout.addWidget(name_label)
        
        # Espaciador para empujar todo a la izquierda
        name_layout.addStretch()
        
        task_layout.addLayout(name_layout, 1)
        
        self.task_widgets[task_name]["enabled"] = enabled_cb

        # Espacio entre columnas
        task_layout.addSpacing(30)

        # ===== Columna 2: Est. Days =====
        est_days_widget = QFrame()  # Widget contenedor para poder ocultarlo
        est_days_widget.setFrameShape(QFrame.NoFrame)  # Sin borde visible
        est_days_layout = QVBoxLayout(est_days_widget)
        est_days_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes adicionales
        est_days_label = QLabel("Est. Days")
        est_days_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 3px;")
        est_days_layout.addWidget(est_days_label)

        estimated_days_edit = QLineEdit()
        estimated_days_edit.setText("0")
        estimated_days_edit.setMaxLength(5)  # Permitir decimales (ej: 12.5)
        estimated_days_edit.setFixedWidth(80)
        estimated_days_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 2px 5px;
                border-radius: 3px;
                height: 20px;
            }
        """
        )
        # Validación para números decimales
        validator = QDoubleValidator(0.0, 99.9, 1)
        validator.setNotation(QDoubleValidator.StandardNotation)
        estimated_days_edit.setValidator(validator)
        
        est_days_layout.addWidget(estimated_days_edit)
        task_layout.addWidget(est_days_widget, 1)
        
        self.task_widgets[task_name]["estimated_days"] = estimated_days_edit
        self.task_widgets[task_name]["est_days_label"] = est_days_label
        self.task_widgets[task_name]["est_days_widget"] = est_days_widget

        # Espacio entre columnas
        task_layout.addSpacing(30)

        # ===== Columna 3: Status =====
        status_widget = QFrame()  # Widget contenedor para poder ocultarlo
        status_widget.setFrameShape(QFrame.NoFrame)  # Sin borde visible
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes adicionales
        status_label = QLabel("Status")
        status_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 0px;")
        status_layout.addWidget(status_label)

        task_ready_cb = QCheckBox("Ready to start")
        task_ready_cb.setChecked(True)  # Activado por defecto
        task_ready_cb.setStyleSheet("color: #a7a7a7; padding: 5px;")
        status_layout.addWidget(task_ready_cb)
        task_layout.addWidget(status_widget, 1)
        
        self.task_widgets[task_name]["task_ready"] = task_ready_cb
        self.task_widgets[task_name]["status_label"] = status_label
        self.task_widgets[task_name]["status_widget"] = status_widget

        # Espacio entre columnas
        task_layout.addSpacing(30)

        # ===== Columna 4: Description =====
        desc_widget = QFrame()  # Widget contenedor para poder ocultarlo
        desc_widget.setFrameShape(QFrame.NoFrame)  # Sin borde visible
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes adicionales
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 0px;")
        desc_layout.addWidget(desc_label)

        copy_description_cb = QCheckBox("copy from shot")
        copy_description_cb.setChecked(True)  # Activado por defecto
        copy_description_cb.setStyleSheet("color: #a7a7a7; padding: 5px;")
        desc_layout.addWidget(copy_description_cb)
        task_layout.addWidget(desc_widget, 1)
        
        self.task_widgets[task_name]["copy_description"] = copy_description_cb
        self.task_widgets[task_name]["desc_label"] = desc_label
        self.task_widgets[task_name]["desc_widget"] = desc_widget

        # Espacio entre columnas
        task_layout.addSpacing(30)

        # ===== Columna 5: Reviewers (más ancha) =====
        reviewers_widget = QFrame()  # Widget contenedor para poder ocultarlo
        reviewers_widget.setFrameShape(QFrame.NoFrame)  # Sin borde visible
        reviewers_layout = QVBoxLayout(reviewers_widget)
        reviewers_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes adicionales
        reviewers_label = QLabel("Reviewers")
        reviewers_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 0px;")
        reviewers_layout.addWidget(reviewers_label)

        # Reviewers checkboxes en línea horizontal
        reviewers_checkboxes_layout = QHBoxLayout()

        reviewer_lega_cb = QCheckBox("Lega")
        reviewer_lega_cb.setChecked(True)
        reviewer_lega_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        reviewers_checkboxes_layout.addWidget(reviewer_lega_cb)

        reviewer_sebas_cb = QCheckBox("Sebas")
        reviewer_sebas_cb.setChecked(True)
        reviewer_sebas_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        reviewers_checkboxes_layout.addWidget(reviewer_sebas_cb)

        reviewer_javi_cb = QCheckBox("Javi")
        reviewer_javi_cb.setChecked(True)
        reviewer_javi_cb.setStyleSheet("color: #a7a7a7; padding: 2px;")
        reviewers_checkboxes_layout.addWidget(reviewer_javi_cb)

        reviewers_layout.addLayout(reviewers_checkboxes_layout)
        task_layout.addWidget(reviewers_widget, 2)  # Stretch factor 2 para hacerla más ancha
        
        self.task_widgets[task_name]["reviewer_lega"] = reviewer_lega_cb
        self.task_widgets[task_name]["reviewer_sebas"] = reviewer_sebas_cb
        self.task_widgets[task_name]["reviewer_javi"] = reviewer_javi_cb
        self.task_widgets[task_name]["reviewers_label"] = reviewers_label
        self.task_widgets[task_name]["reviewers_widget"] = reviewers_widget

        # ===== Conectar checkbox de enable para habilitar/deshabilitar campos =====
        enabled_cb.toggled.connect(
            lambda checked, tn=task_name: self.toggle_task_fields(tn, checked)
        )
        
        # Aplicar estado inicial
        self.toggle_task_fields(task_name, enabled_by_default)

        return task_layout

    def toggle_task_fields(self, task_name, enabled):
        """
        Muestra u oculta las columnas de configuración de una task según el estado del checkbox.
        
        Args:
            task_name (str): Nombre de la task
            enabled (bool): Si está habilitada o no
        """
        widgets = self.task_widgets.get(task_name, {})
        
        # Ocultar/mostrar los widgets contenedores de las columnas (2-5)
        column_widgets = [
            "est_days_widget",
            "status_widget",
            "desc_widget",
            "reviewers_widget"
        ]
        
        for widget_key in column_widgets:
            widget = widgets.get(widget_key)
            if widget:
                widget.setVisible(enabled)
        
        # Mostrar/ocultar el separador
        separator = widgets.get("separator")
        if separator:
            separator.setVisible(enabled)
        
        # Ajustar el tamaño de la ventana para acomodar el cambio
        # Esperar un frame para que Qt actualice el layout
        QTimer.singleShot(0, self.adjust_window_size)
    
    def set_task_fields_editable(self, task_name, editable):
        """Habilita o deshabilita los campos editables de una task."""
        widgets = self.task_widgets.get(task_name, {})
        field_keys = [
            "estimated_days",
            "task_ready",
            "copy_description",
            "reviewer_lega",
            "reviewer_sebas",
            "reviewer_javi",
        ]
        for key in field_keys:
            widget = widgets.get(key)
            if widget:
                widget.setEnabled(editable)

    def set_shot_fields_editable(self, editable):
        """Habilita o deshabilita los campos generales del shot."""
        if hasattr(self, "shot_ready_cb"):
            self.shot_ready_cb.setEnabled(editable)
        if hasattr(self, "high_priority_cb"):
            self.high_priority_cb.setEnabled(editable)

    def prefill_from_existing_shot(
        self,
        shot_data,
        existing_tasks_map,
        lock_existing_task_fields=True,
    ):
        """Prefill de la UI con datos existentes (modo Modify)."""
        if not shot_data:
            return

        description = shot_data.get("description") or ""
        self.description_text.setPlainText(description)

        # Secuencia desde el shot si está disponible
        seq_entity = shot_data.get("sg_sequence") or {}
        sequence_value = (
            seq_entity.get("name")
            or seq_entity.get("code")
            or self.sequence_line_edit.text()
        )
        if sequence_value:
            self.sequence_line_edit.setText(sequence_value)

        # Estados actuales (solo informativos en modo modify)
        self.shot_ready_cb.setChecked(shot_data.get("sg_status_list") == "ready")
        self.high_priority_cb.setChecked(
            (shot_data.get("sg_prioridad") or "").lower() == "high"
        )

        if lock_existing_task_fields:
            self.set_shot_fields_editable(False)

        for task_name, task_info in existing_tasks_map.items():
            widgets = self.task_widgets.get(task_name)
            if not widgets:
                continue

            self.existing_tasks.add(task_name)

            widgets["enabled"].blockSignals(True)
            widgets["enabled"].setChecked(True)
            widgets["enabled"].blockSignals(False)

            self.toggle_task_fields(task_name, True)
            widgets["enabled"].setProperty("existing_task", True)

            if lock_existing_task_fields:
                self.set_task_fields_editable(task_name, False)
    
    def adjust_window_size(self):
        """Ajusta el tamaño de la ventana según el contenido visible"""
        self.adjustSize()
        self.updateGeometry()

    def accept_config(self):
        """Acepta la configuracion y guarda los valores"""
        # Configuración base del shot
        self.shot_config = {
            "description": self.description_text.toPlainText(),
            "sequence_name": self.sequence_line_edit.text().strip(),
            "shot_ready": self.shot_ready_cb.isChecked(),
            "high_priority": self.high_priority_cb.isChecked(),
        }
        
        # Recopilar configuración de tasks dinámicamente
        tasks_config = {}
        for task_name, widgets in self.task_widgets.items():
            # Obtener el valor de días estimados
            try:
                estimated_days_text = widgets["estimated_days"].text().strip()
                estimated_days = float(estimated_days_text) if estimated_days_text else 0.0
            except ValueError:
                estimated_days = 0.0
            
            tasks_config[task_name] = {
                "enabled": widgets["enabled"].isChecked(),
                "task_ready": widgets["task_ready"].isChecked(),
                "copy_description": widgets["copy_description"].isChecked(),
                "estimated_days": estimated_days,
                "reviewers": {
                    "lega_pugliese": widgets["reviewer_lega"].isChecked(),
                    "sebas_romano": widgets["reviewer_sebas"].isChecked(),
                    "javi_bravo": widgets["reviewer_javi"].isChecked(),
                }
            }
        
        self.shot_config["tasks"] = tasks_config
        self.accept()

    def get_config(self):
        """Retorna la configuracion seleccionada"""
        return self.shot_config

    def create_and_show_thumbnail(self):
        """Crea y muestra el thumbnail del shot en la columna derecha"""
        try:
            # Crear el thumbnail
            thumbnail_path = create_shot_thumbnail()
            if thumbnail_path:
                self.thumbnail_path = thumbnail_path

                # Remover el placeholder
                self.thumbnail_placeholder.hide()
                self.thumbnail_placeholder.setParent(None)

                # Widget para mostrar el thumbnail
                self.thumbnail_label = QLabel()
                self.thumbnail_label.setAlignment(Qt.AlignCenter)
                self.thumbnail_label.setStyleSheet(
                    """
                    QLabel {
                        border: none;
                        border-radius: 3px;
                        padding: 5px;
                        background-color: transparent;
                    }
                """
                )

                # Cargar y escalar la imagen
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    # Escalar la imagen manteniendo la relacion de aspecto, con altura fija de 80px
                    scaled_pixmap = pixmap.scaledToHeight(
                        80, Qt.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(scaled_pixmap)

                    # Ajustar el ancho para que quepa en el layout (máximo ~120px considerando padding)
                    label_width = min(scaled_pixmap.width() + 10, 120)
                    self.thumbnail_label.setFixedSize(label_width, 80)

                    # Reemplazar el placeholder con el thumbnail real
                    self.thumbnail_placeholder_layout.addWidget(self.thumbnail_label)
                    debug_print(f"✅ Thumbnail mostrado en la UI: {thumbnail_path}")
                else:
                    debug_print("❌ No se pudo cargar el pixmap del thumbnail")
                    # Mostrar mensaje de error en el placeholder
                    self.thumbnail_placeholder.setText("Error\ncargando\nthumbnail")
                    self.thumbnail_placeholder.setStyleSheet(
                        """
                        QLabel {
                            border: 2px dashed #C05050;
                            border-radius: 3px;
                            background-color: #1a1a1a;
                            color: #C05050;
                            text-align: center;
                            padding: 5px;
                        }
                    """
                    )
            else:
                debug_print("❌ No se pudo crear el thumbnail")
                # Mostrar mensaje cuando no se puede crear el thumbnail
                self.thumbnail_placeholder.setText("No se pudo\ncrear\nthumbnail")
                self.thumbnail_placeholder.setStyleSheet(
                    """
                    QLabel {
                        border: 2px dashed #C05050;
                        border-radius: 3px;
                        background-color: #1a1a1a;
                        color: #C05050;
                        text-align: center;
                        padding: 5px;
                    }
                """
                )
        except Exception as e:
            debug_print(f"❌ Error creando thumbnail: {e}")
            # Mostrar mensaje de error
            self.thumbnail_placeholder.setText("Error\ncreando\nthumbnail")
            self.thumbnail_placeholder.setStyleSheet(
                """
                QLabel {
                    border: 2px dashed #C05050;
                    border-radius: 3px;
                    background-color: #1a1a1a;
                    color: #C05050;
                    text-align: center;
                    padding: 5px;
                }
            """
            )

    def cleanup_thumbnail(self):
        """Limpia el archivo temporal del thumbnail"""
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            try:
                os.remove(self.thumbnail_path)
                debug_print(f"✅ Archivo temporal eliminado: {self.thumbnail_path}")
            except Exception as e:
                debug_print(f"❌ Error eliminando archivo temporal: {e}")

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para limpiar archivos temporales"""
        self.cleanup_thumbnail()
        super(ShotConfigDialog, self).closeEvent(event)

    def reject(self):
        """Sobrescribe reject para limpiar archivos temporales"""
        self.cleanup_thumbnail()
        super(ShotConfigDialog, self).reject()

    def accept(self):
        """Sobrescribe accept para limpiar archivos temporales después"""
        super(ShotConfigDialog, self).accept()
        # Nota: No limpiamos aquí porque el archivo podría usarse después
        # Se limpiará cuando se destruya la ventana


# Clase de ventana de estado para mostrar progreso de creacion de shot en Flow
class FlowStatusWindow(QDialog):
    def __init__(self, task_type="crear shot", parent=None):
        super(FlowStatusWindow, self).__init__(parent)
        self.task_type = task_type
        if task_type == "crear shot":
            self.setWindowTitle("Flow | Create Shot")
        elif task_type == "modificar shot":
            self.setWindowTitle("Flow | Modify Shot")
        else:
            self.setWindowTitle("Flow | Flow")
        self.setModal(False)  # Cambiar a no modal para evitar problemas
        self.setMinimumWidth(500)
        self.setMinimumHeight(150)  # Establecer una altura minima
        self.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )  # Permitir que se ajuste horizontalmente, pero fija verticalmente

        # Evitar que la ventana se cierre automáticamente
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Etiqueta de estado inicial con formato HTML para múltiples colores
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setTextFormat(Qt.RichText)  # Habilitar formato HTML

        # Mensaje inicial
        task_text_map = {
            "crear shot": "Creando shot en ShotGrid",
            "modificar shot": "Modificando shot en ShotGrid",
        }
        task_text = task_text_map.get(task_type, "Procesando")

        initial_message = (
            f"<div style='text-align: left;'>"
            f"<span style='color: #CCCCCC; '>{task_text}</span>"
            f"</div>"
        )

        font = QFont()
        font.setPointSize(10)
        self.status_label.setFont(font)
        self.status_label.setText(initial_message)
        self.status_label.setStyleSheet("padding: 10px;")

        layout.addWidget(self.status_label)

        # Etiqueta para mostrar el shot que se está procesando
        self.shot_label = QLabel("")
        self.shot_label.setAlignment(Qt.AlignLeft)
        self.shot_label.setWordWrap(True)
        self.shot_label.setTextFormat(Qt.RichText)
        self.shot_label.setStyleSheet("padding: 10px;")
        layout.addWidget(self.shot_label)

        # Etiqueta para mensajes de resultado
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setTextFormat(Qt.RichText)
        layout.addWidget(self.result_label)

        # Espaciador
        # layout.addStretch()

        # Botón de Close
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(
            False
        )  # Deshabilitado hasta que termine el procesamiento
        layout.addWidget(self.close_button)

    def update_shot_info(self, shot_name, project_name=None):
        """Actualiza la ventana con el shot que se está procesando"""
        shot_html = "<div style='text-align: left;'>"
        if project_name:
            shot_html += f"<span style='color: #CCCCCC; '>Proyecto:</span> <span style='color: #6AB5CA; '>{project_name}</span><br>"
        shot_html += f"<span style='color: #CCCCCC; '>Shot:</span> <span style='color: #B56AB5; '>{shot_name}</span>"
        shot_html += "</div>"
        self.shot_label.setText(shot_html)
        self._adjust_window_size()

    def show_processing_message(self):
        """Muestra el mensaje de procesamiento"""
        processing_html = f"<span style='color: #CCCCCC; '>Conectando a Flow Production Tracking...</span>"
        self.result_label.setText(processing_html)
        self.result_label.setStyleSheet("padding: 10px;")
        self._adjust_window_size()

    def show_step_message(self, message):
        """Muestra mensaje de paso actual"""
        step_html = f"<span style='color: #CCCCCC; '>{message}</span>"
        self.result_label.setText(step_html)
        self.result_label.setStyleSheet("padding: 10px;")
        self._adjust_window_size()

    def show_success(self, message):
        """Muestra mensaje de éxito en verde"""
        success_html = f"<span style='color: #00ff00; '>{message}</span>"
        self.result_label.setText(success_html)
        self.result_label.setStyleSheet("padding: 10px;")
        self.close_button.setEnabled(True)  # Habilitar botón de Close
        self._adjust_window_size()

    def show_error(self, message):
        """Muestra mensaje de error en rojo"""
        error_html = f"<span style='color: #C05050; '>{message}</span>"
        self.result_label.setText(error_html)
        self.result_label.setStyleSheet("padding: 10px;")
        self.close_button.setEnabled(True)  # Habilitar botón de Close
        self._adjust_window_size()

    def _adjust_window_size(self):
        """Ajusta el tamaño de la ventana basándose en el contenido"""
        self.adjustSize()
        self.updateGeometry()
        # Restar 20px de la altura para hacer la ventana mas compacta
        current_height = self.height()
        new_height = max(0, current_height + 5)
        self.setFixedHeight(new_height)

    def closeEvent(self, event):
        """
        Manejar el evento de cierre para evitar que se cierre automáticamente.
        Solo se cierra cuando el usuario hace clic en el botón Close o cuando ya terminó el procesamiento.
        """
        if not self.close_button.isEnabled():
            # Si el botón Close está deshabilitado, significa que aún está procesando
            # No permitir cerrar la ventana
            event.ignore()
        else:
            # Si el botón está habilitado, permitir cerrar
            event.accept()


class ShotGridManager:
    """Clase para manejar operaciones en ShotGrid."""

    def __init__(self, url, login, password):
        debug_print("Inicializando conexion a ShotGrid para crear shot")
        try:
            self.sg = shotgun_api3.Shotgun(url, login=login, password=password)
            debug_print("Conexion a ShotGrid inicializada exitosamente")
        except Exception as e:
            debug_print(f"Error al inicializar la conexion a ShotGrid: {e}")
            self.sg = None
        self.project_cache = {}

    def upload_thumbnail(self, entity_type, entity_id, thumbnail_path):
        """Sube un thumbnail a una entidad en ShotGrid."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return False

        if not thumbnail_path:
            debug_print("No se proporciono ruta de thumbnail")
            return False

        if not os.path.exists(thumbnail_path):
            debug_print(
                f"ERROR: No se encontro el archivo de thumbnail: {thumbnail_path}"
            )
            return False

        debug_print(f"Verificando archivo antes de subir: {thumbnail_path}")
        debug_print(f"Archivo existe: {os.path.exists(thumbnail_path)}")
        debug_print(
            f"Tamaño del archivo: {os.path.getsize(thumbnail_path) if os.path.exists(thumbnail_path) else 'N/A'}"
        )

        try:
            debug_print(f"Iniciando subida de thumbnail: {thumbnail_path}")
            result = self.sg.upload_thumbnail(entity_type, entity_id, thumbnail_path)
            debug_print(f"Thumbnail subido exitosamente: {result}")
            return True
        except Exception as e:
            debug_print(f"ERROR al subir thumbnail: {e}")
            import traceback

            debug_print(f"Traceback completo: {traceback.format_exc()}")
            return False

    def get_project_id(self, project_name):
        """Obtiene y cachea el ID del proyecto."""
        if not self.sg or not project_name:
            return None

        if project_name in self.project_cache:
            return self.project_cache[project_name]

        projects = self.sg.find(
            "Project",
            [["name", "is", project_name]],
            ["id", "name"],
        )
        if projects:
            project_id = projects[0]["id"]
            self.project_cache[project_name] = project_id
            return project_id

        debug_print(f"No se encontro el proyecto en ShotGrid: {project_name}")
        return None

    def shot_exists(self, project_name, shot_code):
        """Verifica si un shot existe en Flow."""
        if not self.sg:
            return False, None
        project_id = self.get_project_id(project_name)
        if not project_id:
            return False, None
        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", shot_code],
        ]
        fields = [
            "id",
            "code",
            "description",
            "sg_status_list",
            "sg_prioridad",
            "sg_sequence",
            "project",
        ]
        shots = self.sg.find("Shot", filters, fields)
        if shots:
            return True, shots[0]
        return False, None

    def find_shot_and_tasks(
        self,
        project_name,
        shot_code,
        shot_config=None,
        thumbnail_path=None,
        create_if_missing=True,
        file_path=None,
    ):
        """Encuentra el shot en ShotGrid y sus tareas asociadas. Si no existe, lo crea.
        Retorna: (shot, tasks, was_created) donde was_created es True si se creó nuevo."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return None, None, False
        project_id = self.get_project_id(project_name)
        if not project_id:
            return None, None, False

        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", shot_code],
        ]
        fields = [
            "id",
            "code",
            "description",
            "sg_status_list",
            "sg_prioridad",
            "sg_sequence",
            "project",
        ]
        shots = self.sg.find("Shot", filters, fields)
        if shots:
            shot_id = shots[0]["id"]
            debug_print(
                f"Shot existente encontrado: {shot_code}. No se realizarán modificaciones desde Create Shot."
            )

            tasks = self.find_tasks_for_shot(shot_id)
            return shots[0], tasks, False  # False = no fue creado, ya existía

        if not create_if_missing:
            debug_print(
                f"Shot '{shot_code}' no existe y create_if_missing=False (modo lectura)."
            )
            return None, None, False

        if not shot_config:
            debug_print("No se proporciono shot_config para crear el shot.")
            return None, None, False

        debug_print("No se encontro el shot. Creando shot...")
        created_shot = self.create_shot(
            project_id, shot_code, shot_config, thumbnail_path
        )
        if created_shot:
            tasks = self.find_tasks_for_shot(created_shot["id"])

            # ==================================================================================
            # CREAR CARPETAS PARA LAS TASKS HABILITADAS
            # ==================================================================================
            if file_path and shot_config:
                shot_base_path = self.calculate_shot_base_path(file_path)
                if shot_base_path:
                    # Obtener lista de tasks habilitadas
                    enabled_tasks = []
                    tasks_config = shot_config.get("tasks", {})
                    for task_name, task_cfg in tasks_config.items():
                        if task_cfg.get("enabled", False):
                            enabled_tasks.append(task_name)

                    if enabled_tasks:
                        debug_print(f"Creando carpetas para tasks: {', '.join(enabled_tasks)}")
                        folder_result, folder_logs = create_folders_for_shot_tasks(
                            shot_base_path, enabled_tasks
                        )
                        # Loguear todos los mensajes del proceso de carpetas
                        for log_msg in folder_logs:
                            debug_print(log_msg)
                    else:
                        debug_print("No hay tasks habilitadas para crear carpetas")
                else:
                    debug_print("No se pudo calcular shot_base_path para crear carpetas")

            return created_shot, tasks, True  # True = fue creado
        return None, None, False

    def find_tasks_for_shot(self, shot_id, shot_config=None):
        """Encuentra las tareas asociadas a un shot."""
        if not self.sg:
            return []

        try:
            filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
            fields = [
                "id",
                "content",
                "sg_status_list",
                "sg_description",
                "sg_estdias",
                "task_reviewers",
            ]
            tasks = self.sg.find("Task", filters, fields)
            debug_print(f"Encontradas {len(tasks)} tareas para el shot")

            # NOTA: Las tasks creadas manualmente ya tienen la configuración correcta
            # No necesitamos actualizarlas nuevamente para evitar conflictos
            debug_print(
                "Tasks procesadas correctamente (configuracion aplicada en creacion)"
            )

            return tasks
        except Exception as e:
            debug_print(f"Error en find_tasks_for_shot: {e}")
            return []

    def delete_task(self, task_id):
        """Elimina una task existente."""
        if not self.sg:
            return False
        try:
            self.sg.delete("Task", task_id)
            debug_print(f"Task eliminada (ID: {task_id})")
            return True
        except Exception as e:
            debug_print(f"Error eliminando task {task_id}: {e}")
            return False

    def update_shot_description(self, shot_id, description):
        """Actualiza la descripción del shot."""
        if not self.sg:
            return False
        try:
            self.sg.update("Shot", shot_id, {"description": description})
            debug_print("Descripcion del shot actualizada")
            return True
        except Exception as e:
            debug_print(f"Error actualizando descripcion del shot: {e}")
            return False

    def update_shot_status_if_needed(self, shot_id, shot_config):
        """Actualiza el estado del shot si es necesario."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return
        if shot_config["shot_ready"]:
            try:
                self.sg.update("Shot", shot_id, {"sg_status_list": "ready"})
                debug_print("Shot status actualizado a 'ready'")
            except Exception as e:
                debug_print(f"Error actualizando shot status: {e}")

    def update_task_status(self, task_id, status):
        """Actualiza el estado de una tarea."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return
        try:
            self.sg.update("Task", task_id, {"sg_status_list": status})
            debug_print(f"Task status actualizado a '{status}'")
        except Exception as e:
            debug_print(f"Error actualizando task status: {e}")

    def update_task_description(self, task_id, description):
        """Actualiza la descripcion de una tarea."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return
        try:
            self.sg.update("Task", task_id, {"sg_description": description})
            debug_print(f"Task description actualizada")
        except Exception as e:
            debug_print(f"Error actualizando task description: {e}")

    def create_shot(self, project_id, shot_code, shot_config, thumbnail_path=None):
        """Crea un shot en ShotGrid SIN usar templates - crea tasks manualmente."""
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return None

        sequence_name = shot_config.get("sequence_name")
        debug_print(f"Creando shot '{shot_code}' manualmente sin template...")

        # Buscar secuencia
        sequence_filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", sequence_name],
        ]
        sequences = self.sg.find("Sequence", sequence_filters, ["id", "code"])
        if not sequences:
            debug_print(f"ERROR: No se encontro la secuencia '{sequence_name}'")
            return None

        sequence_id = sequences[0]["id"]
        debug_print(f"Secuencia encontrada: {sequences[0]['code']} (ID: {sequence_id})")

        # Crear el shot SIN template
        shot_data = {
            "project": {"type": "Project", "id": project_id},
            "code": shot_code,
            "description": shot_config["description"],
            "sg_sequence": {"type": "Sequence", "id": sequence_id},
            # NOTA: No se incluye "task_template" para evitar usar templates predefinidos
        }

        # Agregar status si esta configurado
        if shot_config["shot_ready"]:
            shot_data["sg_status_list"] = "ready"

        # Agregar prioridad alta si esta configurada
        if shot_config.get("high_priority", False):
            shot_data["sg_prioridad"] = "high"

        try:
            new_shot = self.sg.create("Shot", shot_data)
            debug_print(
                f"Shot creado exitosamente: {new_shot['code']} (ID: {new_shot['id']})"
            )

            # ==================================================================================
            # CREAR TASKS DINÁMICAMENTE
            # ==================================================================================
            tasks_config = shot_config.get("tasks", {})
            
            for task_name, task_cfg in tasks_config.items():
                # Saltar tasks deshabilitadas
                if not task_cfg.get("enabled", False):
                    debug_print(f"Task '{task_name}' deshabilitada por configuración del usuario")
                    continue
                
                # Crear la task
                success = self.create_task_for_shot(
                    project_id=project_id,
                    shot_id=new_shot["id"],
                    task_name=task_name,
                    task_config=task_cfg,
                    shot_description=shot_config["description"]
                )
                
                if success:
                    debug_print(f"Task '{task_name}' creada exitosamente")
                else:
                    debug_print(f"Error creando task '{task_name}'")

            # Subir thumbnail si se proporciono
            if thumbnail_path:
                debug_print(f"Subiendo thumbnail para shot: {shot_code} - Path: {thumbnail_path}")
                debug_print(f"Archivo existe: {os.path.exists(thumbnail_path)}")
                upload_success = self.upload_thumbnail(
                    "Shot", new_shot["id"], thumbnail_path
                )
                if upload_success:
                    debug_print(f"Thumbnail subido exitosamente para shot: {shot_code}")
                else:
                    debug_print(f"Error subiendo thumbnail para shot: {shot_code}")
            else:
                debug_print(f"No se proporciono thumbnail_path para shot: {shot_code}")

            return new_shot
        except Exception as e:
            debug_print(f"ERROR al crear el shot: {e}")
            return None

    def create_task_for_shot(self, project_id, shot_id, task_name, task_config, shot_description):
        """
        Crea una task para un shot de forma genérica.
        
        Args:
            project_id (int): ID del proyecto
            shot_id (int): ID del shot
            task_name (str): Nombre de la task (ej: "Comp", "Roto")
            task_config (dict): Configuración de la task
            shot_description (str): Descripción del shot (para copiar si está habilitado)
            
        Returns:
            bool: True si se creó exitosamente, False si hubo error
        """
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return False
        
        try:
            # Buscar el pipeline step correspondiente
            # NOTA: Para encontrar el pipeline step, buscamos por el nombre de la task
            # que debe coincidir con el código del step en ShotGrid
            pipeline_step_name = None
            for task_cfg in AVAILABLE_TASKS:
                if task_cfg["name"] == task_name:
                    pipeline_step_name = task_cfg["pipeline_step"]
                    break
            
            if not pipeline_step_name:
                debug_print(f"ADVERTENCIA: No se encontró configuración para task '{task_name}'")
                pipeline_step_name = task_name  # Usar el nombre de la task como fallback
            
            step_filters = [["code", "is", pipeline_step_name]]
            steps = self.sg.find("Step", step_filters, ["id", "code"])
            step_id = None
            if steps:
                step_id = steps[0]["id"]
                debug_print(f"Pipeline step '{pipeline_step_name}' encontrado (ID: {step_id})")
            else:
                debug_print(f"ADVERTENCIA: No se encontró el pipeline step '{pipeline_step_name}'")
            
            # Crear data de la task
            task_data = {
                "content": task_name,
                "entity": {"type": "Shot", "id": shot_id},
                "sg_status_list": "noread",  # Estado inicial por defecto
                "project": {"type": "Project", "id": project_id},
            }
            
            # Asignar pipeline step si se encontró
            if step_id:
                task_data["step"] = {"type": "Step", "id": step_id}
            
            # Aplicar configuración de status
            if task_config.get("task_ready", False):
                task_data["sg_status_list"] = "ready"
            
            # Copiar descripción del shot si está habilitado
            if task_config.get("copy_description", False) and shot_description:
                task_data["sg_description"] = shot_description
            
            # Agregar tiempo estimado si es mayor que 0
            # Aplicar reducción del 30% antes de subir a Flow
            estimated_days = task_config.get("estimated_days", 0)
            if estimated_days > 0:
                # Reducir 30%: multiplicar por 0.7 (ej: 1 día -> 0.7 días)
                estimated_days_reduced = estimated_days * 0.7
                task_data["sg_estdias"] = estimated_days_reduced
                debug_print(f"Tiempo estimado: {estimated_days} días -> {estimated_days_reduced:.2f} días (reducción 30%)")
            
            # Crear la task
            new_task = self.sg.create("Task", task_data)
            debug_print(f"Task '{task_name}' creada exitosamente (ID: {new_task['id']})")
            
            # Asignar reviewers
            reviewers_config = task_config.get("reviewers", {})
            selected_reviewer_ids = []
            reviewer_names_to_assign = []
            
            if reviewers_config.get("lega_pugliese", False):
                reviewer_names_to_assign.append("Lega Pugliese")
            if reviewers_config.get("sebas_romano", False):
                reviewer_names_to_assign.append("Sebas Romano")
            if reviewers_config.get("javi_bravo", False):
                reviewer_names_to_assign.append("Javi Bravo")
            
            # Buscar IDs de todos los reviewers seleccionados
            for reviewer_name in reviewer_names_to_assign:
                try:
                    users = self.sg.find("HumanUser", [["name", "is", reviewer_name]], ["id", "name"])
                    if users:
                        selected_reviewer_ids.append({"type": "HumanUser", "id": users[0]["id"]})
                        debug_print(f"Reviewer '{reviewer_name}' encontrado (ID: {users[0]['id']})")
                    else:
                        debug_print(f"Usuario '{reviewer_name}' no encontrado")
                except Exception as e:
                    debug_print(f"Error buscando reviewer '{reviewer_name}': {e}")
            
            # Asignar todos los reviewers a la task usando task_reviewers
            if selected_reviewer_ids:
                try:
                    self.sg.update("Task", new_task["id"], {"task_reviewers": selected_reviewer_ids})
                    debug_print(f"Asignados {len(selected_reviewer_ids)} reviewers a task {task_name}")
                except Exception as e:
                    debug_print(f"Error asignando reviewers a task: {e}")
            else:
                debug_print(f"No se seleccionaron reviewers para task '{task_name}'")
            
            return True
            
        except Exception as e:
            debug_print(f"ERROR al crear task '{task_name}': {e}")
            return False


class HieroOperations:
    """Clase para manejar operaciones en Hiero."""

    def __init__(self, shotgrid_manager):
        self.sg_manager = shotgrid_manager

    def parse_exr_name(self, file_name):
        """Extrae el nombre base del archivo EXR y el numero de version."""
        base_name = clean_base_name(file_name)
        version_match = re.search(r"_v(\d+)", file_name)
        version_number = version_match.group(1) if version_match else "Unknown"
        return base_name, version_number

    def get_selected_clips_info(self):
        """Obtiene informacion de los clips usando el método híbrido centralizado.
        Permite selección múltiple: si hay múltiples clips seleccionados en el track,
        procesa todos ellos. Si no, usa el clip del playhead."""
        seq = hiero.ui.activeSequence()
        if not seq:
            debug_print("No se encontro una secuencia activa en Hiero.")
            return []
        
        # Usar módulo centralizado con selección múltiple habilitada
        # track_name=None para respetar TRACK_comp_EXR del módulo
        clips = get_clips_to_process(track_name=None, prioritize_multiple_selection=True)
        
        if not clips:
            debug_print("No se encontraron clips para procesar (ni en playhead ni seleccionados).")
            return []
        
        clips_info = []
        for clip in clips:
            try:
                file_path = clip.source().mediaSource().fileinfos()[0].filename()
                exr_name = os.path.basename(file_path)
                base_name, version_number = self.parse_exr_name(exr_name)

                # Usar funciones de naming utils para extraer información
                project_name = extract_project_name(base_name)
                shot_code = extract_shot_code(base_name)

                clips_info.append(
                    {
                        "base_name": base_name,
                        "project_name": project_name,
                        "shot_code": shot_code,
                        "version_number": version_number,
                        "file_path": file_path,
                    }
                )
            except Exception as e:
                debug_print(f"Error procesando clip {clip.name()}: {e}")
                continue
        
        return clips_info

    def calculate_shot_base_path(self, file_path):
        """
        Calcula el path base del shot desde un archivo EXR.
        Similar a la lógica en Push.py: 4 niveles arriba del archivo.

        Args:
            file_path: Path completo del archivo EXR

        Returns:
            str: Path base del shot o None si no se puede calcular
        """
        try:
            normalized_path = os.path.normpath(file_path)
            path_parts = normalized_path.split(os.sep)

            if os.path.isabs(file_path) and len(path_parts) >= 5:
                # Calcular 4 niveles arriba: dirname(dirname(dirname(dirname(file_path))))
                shot_base_path = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
                )
                debug_print(f"Shot base path calculado: {shot_base_path}")
                return shot_base_path
            else:
                debug_print("No se puede calcular shot_base_path (ruta inválida)")
                return None
        except Exception as e:
            debug_print(f"Error calculando shot_base_path para {file_path}: {e}")
            return None

    def process_selected_clips(self, shot_config, thumbnail_path=None):
        """Procesa los clips seleccionados en el timeline de Hiero."""
        clips_info = self.get_selected_clips_info()
        if not clips_info:
            return []

        results = []
        for clip_info in clips_info:
            shot, tasks, _ = self.sg_manager.find_shot_and_tasks(
                clip_info["project_name"],
                clip_info["shot_code"],
                shot_config,
                thumbnail_path,
                file_path=clip_info.get("file_path"),
            )
            if shot:
                debug_print(f"Clip seleccionado: {clip_info['base_name']}")
                debug_print(f"Shot de SG encontrado: {shot['code']}")
                debug_print(f"Descripcion del shot: {shot['description']}")
                debug_print("Tareas asociadas:")
                if tasks:
                    for task in tasks:
                        debug_print(f"- Nombre: {task['content']}")
                        debug_print(f"  Estado: {task['sg_status_list']}")
                else:
                    debug_print("No hay tareas asociadas a este shot.")

                results.append(
                    {
                        "clip_info": clip_info,
                        "shot": shot,
                        "tasks": tasks,
                        "success": True,
                    }
                )
            else:
                debug_print("No se encontro el shot correspondiente en ShotGrid.")
                results.append(
                    {
                        "clip_info": clip_info,
                        "shot": None,
                        "tasks": None,
                        "success": False,
                    }
                )

        return results


class WorkerSignals(QObject):
    shot_info_ready = Signal(str, str)  # shot_name, project_name
    step_update = Signal(str)  # step message
    finished = Signal(bool, str)  # success, message
    error = Signal(str)
    debug_output = Signal()  # Señal para imprimir logs al final


class ShotExistenceSignals(QObject):
    finished = Signal(list)  # Lista de dicts con clip_info y shot existente
    error = Signal(str)
    debug_output = Signal()


class CreateShotWorker(QRunnable):
    def __init__(self, status_window, shot_config, clips_info, thumbnail_path=None):
        super(CreateShotWorker, self).__init__()
        self.status_window = status_window
        self.shot_config = shot_config
        self.clips_info = clips_info  # Clips obtenidos en el hilo principal
        self.thumbnail_path = thumbnail_path
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            debug_print("=== Iniciando creacion de shots ===")

            # Obtener credenciales de Flow DENTRO del worker
            self.signals.step_update.emit("Obteniendo credenciales...")
            sg_url, sg_login, sg_password = get_flow_credentials_secure()
            if not all([sg_url, sg_login, sg_password]):
                self.signals.debug_output.emit()
                self.signals.error.emit(
                    "No se pudieron obtener las credenciales de Flow desde SecureConfig."
                )
                return

            # Crear manager ShotGrid DENTRO del worker
            self.signals.step_update.emit("Conectando a ShotGrid...")
            sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
            if not sg_manager.sg:
                self.signals.debug_output.emit()
                self.signals.error.emit(
                    "No se pudo inicializar la conexión a ShotGrid."
                )
                return

            # Usar clips_info que ya se obtuvieron en el hilo principal
            # NO obtenerlos de nuevo aquí porque las funciones del módulo centralizado
            # necesitan ejecutarse en el hilo principal (acceden al viewer de Hiero)
            clips_info = self.clips_info
            if not clips_info:
                self.signals.debug_output.emit()
                self.signals.error.emit(
                    "No se encontraron clips para procesar."
                )
                return

            # Procesar cada clip
            total_clips = len(clips_info)
            success_count = 0

            for i, clip_info in enumerate(clips_info, 1):
                # Emitir información del shot
                self.signals.shot_info_ready.emit(
                    clip_info["shot_code"], clip_info["project_name"]
                )

                self.signals.step_update.emit(
                    f"Procesando clip {i}/{total_clips}: {clip_info['shot_code']}"
                )

                # Procesar shot
                shot, tasks, was_created = sg_manager.find_shot_and_tasks(
                    clip_info["project_name"],
                    clip_info["shot_code"],
                    self.shot_config,
                    self.thumbnail_path,
                    file_path=clip_info.get("file_path"),
                )

                if shot and was_created:
                    # Shot creado exitosamente
                    success_count += 1
                    debug_print(f"Shot creado exitosamente: {shot['code']}")
                elif shot and not was_created:
                    # Shot ya existía
                    debug_print(f"Shot ya existe: {clip_info['shot_code']}")
                    self.signals.step_update.emit(
                        f"Shot '{clip_info['shot_code']}' ya existía en ShotGrid. No se realizaron modificaciones."
                    )
                    # No incrementar success_count, será tratado como error
                else:
                    # Error al procesar shot
                    debug_print(f"Error procesando shot: {clip_info['shot_code']}")
                    self.signals.step_update.emit(
                        f"ERROR: No se pudo procesar el shot '{clip_info['shot_code']}'"
                    )

            # Emitir señal para imprimir logs al final
            self.signals.debug_output.emit()

            # Mensaje final
            if success_count == total_clips:
                self.signals.finished.emit(
                    True,
                    f"Todos los shots ({success_count}/{total_clips}) fueron procesados exitosamente.",
                )
            elif success_count > 0:
                self.signals.finished.emit(
                    True,
                    f"Se procesaron {success_count}/{total_clips} shots exitosamente.",
                )
            else:
                self.signals.error.emit("No se pudieron procesar ninguno de los shots.")

        except Exception as e:
            debug_print(f"Error en CreateShotWorker: {e}")
            # Emitir señal para imprimir logs al final
            self.signals.debug_output.emit()
            self.signals.error.emit(f"Error: {str(e)}")


class ShotExistenceCheckWorker(QRunnable):
    def __init__(self, clips_info):
        super(ShotExistenceCheckWorker, self).__init__()
        self.clips_info = clips_info
        self.signals = ShotExistenceSignals()

    @Slot()
    def run(self):
        try:
            sg_url, sg_login, sg_password = get_flow_credentials_secure()
            if not all([sg_url, sg_login, sg_password]):
                self.signals.debug_output.emit()
                self.signals.error.emit(
                    "No se pudieron obtener las credenciales de Flow desde SecureConfig."
                )
                return

            sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
            if not sg_manager.sg:
                self.signals.debug_output.emit()
                self.signals.error.emit(
                    "No se pudo inicializar la conexión a ShotGrid."
                )
                return

            existing = []
            for clip_info in self.clips_info:
                project_name = clip_info.get("project_name")
                shot_code = clip_info.get("shot_code")
                if not project_name or not shot_code:
                    continue
                exists, shot_data = sg_manager.shot_exists(project_name, shot_code)
                if exists:
                    debug_print(f"Shot '{shot_code}' ya existe en Flow.")
                    existing.append(
                        {
                            "clip_info": clip_info,
                            "shot": shot_data,
                        }
                    )

            self.signals.debug_output.emit()
            self.signals.finished.emit(existing)
        except Exception as e:
            debug_print(f"Error en ShotExistenceCheckWorker: {e}")
            self.signals.debug_output.emit()
            self.signals.error.emit(str(e))


def get_flow_credentials_secure():
    sg_url, sg_login, sg_password = get_flow_credentials()
    if not sg_url or not sg_login or not sg_password:
        debug_print(
            "No se pudieron obtener las credenciales de Flow desde SecureConfig."
        )
        return None, None, None

    # Para Flow, usamos login directo en lugar de API key
    return sg_url, sg_login, sg_password


# Variables globales para mantener referencias
_status_window = None


def cleanup_thumbnail_file(thumbnail_path):
    """Limpia el archivo temporal del thumbnail."""
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            os.remove(thumbnail_path)
            debug_print(f"✅ Archivo temporal eliminado: {thumbnail_path}")
        except Exception as e:
            debug_print(f"❌ Error eliminando archivo temporal: {e}")


def launch_modify_shot_script():
    """Carga el script de Modify Shot y ejecuta su flujo principal."""
    script_path = Path(__file__).with_name("LGA_NKS_Flow_ModifyShot.py")
    if not script_path.exists():
        QMessageBox.warning(
            None,
            "Flow | Modify Shot",
            f"No se encontró el script Modify Shot en: {script_path}",
        )
        return
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "LGA_NKS_Flow_ModifyShot_runtime", str(script_path)
        )
        if spec is None or spec.loader is None:
            raise ImportError("No se pudo cargar el módulo Modify Shot.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()
    except Exception as e:
        QMessageBox.warning(None, "Flow | Modify Shot", str(e))


def create_shots_from_selected_clips():
    """
    Función principal del script de creación de shots.
    """
    global _status_window

    debug_print("=== Iniciando LGA_NKS_Flow_CreateShot ===")

    # Crear aplicación Qt si no existe
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Primero obtener informacion de clips para mostrar en el dialogo de configuracion
    hiero_ops_temp = HieroOperations(None)
    clips_info = hiero_ops_temp.get_selected_clips_info()

    if not clips_info:
        QMessageBox.warning(
            None, "Error", "No se encontraron clips seleccionados en Hiero."
        )
        return

    # Obtener nombre de la secuencia activa
    sequence_name = get_active_sequence_name()
    if not sequence_name:
        QMessageBox.warning(
            None,
            "Error",
            "No se pudo obtener el nombre de la secuencia activa en Hiero.",
        )
        return

    # Iniciar pre-chequeo de existencia
    start_shot_existence_check(clips_info, sequence_name)


def start_shot_existence_check(clips_info, sequence_name):
    """Abre ventana de estado y lanza worker para verificar existencia previa."""
    global _status_window

    _status_window = FlowStatusWindow("crear shot")
    _status_window.show()
    _status_window.show_step_message("Comprobando existencia de los shots en Flow...")

    worker = ShotExistenceCheckWorker(clips_info)

    worker.signals.finished.connect(
        lambda existing: handle_shot_existence_result(
            existing, clips_info, sequence_name
        )
    )
    worker.signals.error.connect(handle_shot_existence_error)
    worker.signals.debug_output.connect(lambda: print_debug_messages())

    QThreadPool.globalInstance().start(worker)


def handle_shot_existence_error(message):
    global _status_window
    if _status_window:
        _status_window.show_error(message)
    else:
        QMessageBox.warning(None, "Flow | Create Shot", message)


def handle_shot_existence_result(existing_shots, clips_info, sequence_name):
    global _status_window

    if existing_shots:
        shot_names = [item["clip_info"]["shot_code"] for item in existing_shots]
        formatted_list = "<br>".join(sorted(shot_names))

        if len(clips_info) == 1:
            if _status_window:
                _status_window.close()
                _status_window = None
            # Shot único ya existente: abrir Modify Shot directamente
            launch_modify_shot_script()
            return
        else:
            message = (
                "No se pueden crear los shots seleccionados porque ya existen:<br>"
                f"{formatted_list}"
            )
            if _status_window:
                _status_window.show_error(message)
            else:
                QMessageBox.warning(
                    None,
                    "Shots ya existentes",
                    "Ya existen en Flow:\n" + "\n".join(sorted(shot_names)),
                )
            return

    # Ningún shot existe: cerrar ventana y continuar con el flujo normal
    if _status_window:
        _status_window.close()
        _status_window = None

    show_shot_config_dialog(clips_info, sequence_name)


def show_shot_config_dialog(clips_info, sequence_name):
    """Muestra el dialogo de configuración y lanza la creación."""
    config_dialog = ShotConfigDialog(clips_info, sequence_name)
    if config_dialog.exec_() != QDialog.Accepted:
        config_dialog.cleanup_thumbnail()
        return

    shot_config = config_dialog.get_config()
    if not shot_config:
        config_dialog.cleanup_thumbnail()
        return

    thumbnail_path = config_dialog.thumbnail_path

    global _status_window
    _status_window = FlowStatusWindow("crear shot")
    _status_window.show()
    _status_window.show_processing_message()

    worker = CreateShotWorker(_status_window, shot_config, clips_info, thumbnail_path)

    worker.signals.shot_info_ready.connect(
        lambda shot_name, project_name, window=_status_window: window.update_shot_info(
            shot_name, project_name
        )
    )
    worker.signals.step_update.connect(
        lambda message, window=_status_window: window.show_step_message(message)
    )
    worker.signals.finished.connect(
        lambda success, message, window=_status_window: (
            window.show_success(message) if window else None,
            cleanup_thumbnail_file(thumbnail_path),
        )
    )
    worker.signals.error.connect(
        lambda error_msg, window=_status_window: (
            window.show_error(error_msg) if window else None,
            cleanup_thumbnail_file(thumbnail_path),
        )
    )
    worker.signals.debug_output.connect(lambda: print_debug_messages())

    QThreadPool.globalInstance().start(worker)
    debug_print("=== Worker iniciado en hilo separado ===")


def main():
    """Función principal para compatibilidad hacia atrás."""
    create_shots_from_selected_clips()


if __name__ == "__main__":
    main()
