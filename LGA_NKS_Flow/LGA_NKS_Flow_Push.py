"""
_____________________________________________________________

  LGA_NKS_Flow_Push v3.75 | Lega

  Envia a flow nuevos estados de las tasks comps.
  En algunos estados permite enviar un mensaje a la version
  También actualiza la base de datos local para mantenerla sincronizada
  Muestra thumbnails de imagenes capturadas en el dialogo de notas para referencia visual
  y envía las imagenes a la nota en Flow
_____________________________________________________________

"""

import os
import re
import shotgun_api3
import sqlite3
import platform
import glob
import shutil
import tempfile
import json
from PySide2.QtCore import QRunnable, Slot, QThreadPool, Signal, QObject, Qt
import datetime
import subprocess  # Importar subprocess para abrir archivos
import sys
from pathlib import Path

# Importar el módulo de configuración segura
sys.path.append(str(Path(__file__).parent))
from SecureConfig_Reader import get_flow_credentials

# from PySide2.QtCore import QWaitCondition, QMutex
from PySide2.QtWidgets import (
    QApplication,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QShortcut,
    QScrollArea,
    QWidget,
    QCheckBox,
)
from PySide2.QtGui import QKeySequence, QPixmap

# Diccionario de traduccion de estados
status_translation = {
    "Corrections": "corr",
    "Corrs_Lega": "revleg",
    "Rev Sebas": "rev_su",
    "Rev Javi": "revjav",
    "Rev Lega": "revleg",
    "Rev Dir": "rev_di",
    "Approved": "apr",
    "Delivery Ok": "check",
    "Rev Dir Den": "rev_di",
    "Rev_Hold": "revhld",
}

# Variable global para activar o desactivar los prints // En esta version el Debug se imprime al final del script
DEBUG = True
debug_messages = []


def debug_print(message):
    if DEBUG:
        debug_messages.append(message)

def call_flow_connector(operation, **kwargs):
    """
    Llama al conector de Flow usando el Python personalizado
    Esta es la función más simple posible para delegar operaciones de red
    """
    try:
        # Configuración del Python personalizado para Windows
        WINDOWS_PYTHON_PATH = r"C:\Portable\LGA\PipeSync\python_runtime\windows\python.exe"

        # Obtener credenciales y agregarlas a los parámetros
        sg_url, sg_login, sg_password = get_flow_credentials()
        kwargs['url'] = sg_url
        kwargs['login'] = sg_login
        kwargs['password'] = sg_password

        # Ruta al script conector
        connector_script = os.path.join(os.path.dirname(__file__), "flow_connector.py")

        if not os.path.exists(connector_script):
            debug_print(f"Conector no encontrado: {connector_script}")
            return {"success": False, "error": "Conector no encontrado"}

        # Preparar comando
        if platform.system() == "Windows" and os.path.exists(WINDOWS_PYTHON_PATH):
            cmd = [WINDOWS_PYTHON_PATH, connector_script, operation]
        else:
            cmd = [sys.executable, connector_script, operation]

        debug_print(f"Llamando conector: {' '.join(cmd)}")

        # Timeout dinámico basado en la operación
        if operation == "attach_images":
            timeout_seconds = 30  # Más tiempo para subir imágenes
        else:
            timeout_seconds = 10  # Tiempo normal para otras operaciones

        # Ejecutar conector
        result = subprocess.run(
            cmd,
            input=json.dumps(kwargs),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        if result.returncode == 0:
            try:
                response = json.loads(result.stdout.strip())
                debug_print(f"Conector completado: {response}")
                return response
            except json.JSONDecodeError:
                debug_print(f"Error parseando respuesta: {result.stdout}")
                return {"success": False, "error": f"Respuesta inválida: {result.stdout}"}
        else:
            error_msg = f"Conector falló: {result.stderr}"
            debug_print(error_msg)
            return {"success": False, "error": error_msg}

    except subprocess.TimeoutExpired:
        debug_print("Timeout en conector")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        debug_print(f"Error llamando conector: {e}")
        return {"success": False, "error": str(e)}


def find_review_images(base_name):
    """
    Busca imagenes de ReviewPic para el shot y version especificados.
    Retorna una lista de rutas de imagenes encontradas.
    """
    try:
        # Extraer informacion del nombre base
        parts = base_name.split("_")

        # Buscar numero de version
        version_number_str = None
        for part in parts:
            if part.startswith("v") and part[1:].isdigit():
                version_number_str = part
                break

        if not version_number_str:
            debug_print("No se encontro numero de version en el nombre base")
            return []

        # Construir el nombre de la carpeta del clip siguiendo el mismo patron que ReviewPic
        # El patron es: {base_name_sin_version}_v{version}
        # Ejemplo: si base_name es "PROJ_SEQ_SHOT_comp_v001_001.exr"
        # necesitamos "PROJ_SEQ_SHOT_comp_v001"

        # Encontrar la posicion de la version en el nombre
        version_index = -1
        for i, part in enumerate(parts):
            if part == version_number_str:
                version_index = i
                break

        if version_index == -1:
            debug_print(
                f"No se pudo encontrar la version {version_number_str} en las partes del nombre"
            )
            return []

        # Tomar todas las partes hasta la version (inclusive)
        base_parts = parts[: version_index + 1]
        clip_folder_name = "_".join(base_parts)

        # Obtener la ruta del script actual
        script_dir = os.path.dirname(__file__)
        cache_dir = os.path.join(script_dir, "ReviewPic_Cache")
        clip_dir = os.path.join(cache_dir, clip_folder_name)

        debug_print(f"Buscando imagenes en: {clip_dir}")
        debug_print(f"Nombre de carpeta construido: {clip_folder_name}")

        # Buscar archivos JPG en la carpeta
        if os.path.exists(clip_dir):
            image_pattern = os.path.join(clip_dir, "*.jpg")
            images = glob.glob(image_pattern)
            debug_print(f"Imagenes encontradas: {len(images)}")
            return sorted(images)  # Ordenar para mostrar en orden consistente
        else:
            debug_print(f"Carpeta no existe: {clip_dir}")
            return []

    except Exception as e:
        debug_print(f"Error buscando imagenes de review: {e}")
        return []


class DBManager:
    """Clase para manejar operaciones con la base de datos SQLite local."""

    def __init__(self):
        # Selecciona la ruta de la base de datos segun el sistema operativo
        if platform.system() == "Windows":
            self.db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
        elif platform.system() == "Darwin":
            self.db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
        else:
            debug_print(f"Sistema operativo no soportado: {platform.system()}")
            self.db_path = None

        if self.db_path and os.path.exists(self.db_path):
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                debug_print(f"Conexión exitosa a la base de datos: {self.db_path}")
            except Exception as e:
                debug_print(f"Error al conectar a la base de datos: {e}")
                self.conn = None
        else:
            debug_print(f"DB file not found at path: {self.db_path}")
            self.conn = None

    def find_project(self, project_name):
        """Busca un proyecto por nombre en la base de datos."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM projects WHERE project_name = ?", (project_name,)
            )
            return cur.fetchone()
        except Exception as e:
            debug_print(f"Error al buscar proyecto {project_name}: {e}")
            return None

    def find_shot(self, project_name, shot_code):
        """Busca un shot por nombre y código en la base de datos."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT s.* FROM shots s
                JOIN projects p ON s.project_id = p.id
                WHERE p.project_name = ? AND s.shot_name = ?
                """,
                (project_name, shot_code),
            )
            return cur.fetchone()
        except Exception as e:
            debug_print(
                f"Error al buscar shot {shot_code} en proyecto {project_name}: {e}"
            )
            return None

    def find_task(self, shot_id, task_name):
        """Busca una tarea específica por nombre y shot_id."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT * FROM tasks 
                WHERE shot_id = ? AND LOWER(task_type) = LOWER(?)
                """,
                (shot_id, task_name),
            )
            return cur.fetchone()
        except Exception as e:
            debug_print(
                f"Error al buscar tarea {task_name} para shot_id {shot_id}: {e}"
            )
            return None

    def update_task_status(self, task_id, status):
        """Actualiza el estado de una tarea en la base de datos."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE tasks SET task_status = ? WHERE id = ?", (status, task_id)
            )
            self.conn.commit()
            debug_print(
                f"Estado de la tarea (ID: {task_id}) actualizado a '{status}' en la base de datos local"
            )
            return True
        except Exception as e:
            debug_print(
                f"Error al actualizar el estado de la tarea en la DB local: {e}"
            )
            return False

    def update_version_status(self, task_id, version_number, status):
        """Actualiza el estado de una versión específica en la base de datos."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return False

        try:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE versions SET status = ? WHERE task_id = ? AND version_number = ?",
                (status, task_id, version_number),
            )
            self.conn.commit()
            debug_print(
                f"Estado de la versión {version_number} (task_id: {task_id}) actualizado a '{status}' en la base de datos local"
            )
            return True
        except Exception as e:
            debug_print(
                f"Error al actualizar el estado de la versión en la DB local: {e}"
            )
            return False

    def get_user_name(self):
        """Obtiene el nombre del usuario actual desde app_settings."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos para obtener user_name")
            return "Desconocido"
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = 'user_name'"
            )
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
            else:
                return "Desconocido"
        except Exception as e:
            debug_print(f"Error al obtener user_name de app_settings: {e}")
            return "Desconocido"

    def add_version_note(self, version_id, content, created_by=None):
        """Añade una nota a una versión en la base de datos."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return False
        if created_by is None:
            created_by = self.get_user_name()
        # Obtener fecha y hora local con zona horaria en formato igual a Flow
        created_on = (
            datetime.datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")
        )
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO version_notes (version_id, content, created_by, created_on) 
                VALUES (?, ?, ?, ?)
                """,
                (version_id, content, created_by, created_on),
            )
            self.conn.commit()
            debug_print(
                f"Nota añadida a la versión (ID: {version_id}) en la base de datos local por {created_by} en {created_on}"
            )
            return True
        except Exception as e:
            debug_print(f"Error al añadir nota a la versión en la DB local: {e}")
            return False

    def find_latest_version(self, task_id):
        """Encuentra la versión más reciente para una tarea específica."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return None

        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT * FROM versions 
                WHERE task_id = ? 
                ORDER BY version_number DESC 
                LIMIT 1
                """,
                (task_id,),
            )
            return cur.fetchone()
        except Exception as e:
            debug_print(
                f"Error al buscar la última versión para task_id {task_id}: {e}"
            )
            return None

    def close(self):
        """Cierra la conexión a la base de datos."""
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
                self.conn = None
                debug_print("Conexión a la base de datos cerrada")
            except Exception as e:
                debug_print(f"Error al cerrar la conexión a la base de datos: {e}")


class InputDialog(QDialog):
    def __init__(self, base_name):
        super(InputDialog, self).__init__()
        self.setWindowTitle("Input Dialog")
        self.base_name = base_name
        self.review_images = []
        self.delete_images_checkbox = None

        self.layout = QVBoxLayout(self)

        # Label para el mensaje
        self.label = QLabel(f"Message for {base_name}:")
        self.layout.addWidget(self.label)

        # Area de texto para el mensaje
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setFixedHeight(120)  # Ajustar la altura de la caja de texto
        self.layout.addWidget(self.text_edit)

        # Buscar imagenes de ReviewPic y mostrar thumbnails si existen
        self.review_images = find_review_images(base_name)
        if self.review_images:
            self.add_thumbnails_section(self.review_images)
            self.adjust_window_size()  # Esto establece el ancho y la altura actual
            self.setFixedWidth(
                self.width()
            )  # Fijar el ancho para que adjustSize solo afecte la altura

        # Boton OK
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        # Conectar Ctrl+Enter al metodo accept
        shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return), self)
        shortcut.activated.connect(self.accept)

        # Ajustar el tamaño del diálogo para que se ajuste a su contenido (ahora solo ajusta la altura)
        self.adjustSize()

    def add_thumbnails_section(self, image_paths):
        """
        Agrega una seccion con thumbnails de las imagenes encontradas.
        """
        try:
            # Label para la seccion de thumbnails
            """ "
            thumbnails_label = QLabel("Review Images:")
            thumbnails_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.layout.addWidget(thumbnails_label)
            """

            # Crear scroll area para los thumbnails
            scroll_area = QScrollArea()
            scroll_area.setMaximumHeight(
                220
            )  # Aumentar altura para incluir numeros de frame
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            # Widget contenedor para los thumbnails
            thumbnails_widget = QWidget()
            thumbnails_layout = QHBoxLayout(thumbnails_widget)
            thumbnails_layout.setSpacing(10)

            # Crear thumbnails con numeros de frame
            for image_path in image_paths:
                if os.path.exists(image_path):
                    # Crear contenedor vertical para imagen + numero de frame
                    thumbnail_container = QWidget()
                    container_layout = QVBoxLayout(thumbnail_container)
                    container_layout.setSpacing(2)
                    container_layout.setContentsMargins(0, 0, 0, 0)

                    # Crear label para mostrar la imagen
                    image_label = QLabel()

                    # Cargar y redimensionar la imagen
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # Redimensionar manteniendo aspecto, ancho maximo 150px
                        scaled_pixmap = pixmap.scaledToWidth(
                            150, Qt.SmoothTransformation
                        )
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setToolTip(
                            os.path.basename(image_path)
                        )  # Mostrar nombre al hacer hover
                        image_label.setAlignment(Qt.AlignCenter)

                        # Agregar borde al thumbnail
                        image_label.setStyleSheet(
                            "border: 1px solid #ccc; padding: 2px;"
                        )

                        # Conectar el evento de clic del thumbnail
                        image_label.mousePressEvent = lambda event, path=image_path: self.open_image_with_default_viewer(
                            path
                        )

                        container_layout.addWidget(
                            image_label, alignment=Qt.AlignCenter
                        )

                        # Agregar numero de frame debajo de la imagen
                        frame_number = self.extract_frame_number_from_filename(
                            image_path
                        )
                        frame_label = QLabel(f"Frame: {frame_number}")
                        frame_label.setStyleSheet(
                            "color: #9c9c9c; font-size: 11px; margin-left: 4px;"
                        )
                        frame_label.setAlignment(Qt.AlignLeft)
                        container_layout.addWidget(frame_label)

                        thumbnails_layout.addWidget(thumbnail_container)
                        debug_print(
                            f"Thumbnail agregado: {os.path.basename(image_path)} - Frame: {frame_number}"
                        )

            # Agregar stretch al final para alinear thumbnails a la izquierda
            thumbnails_layout.addStretch()

            # Configurar el scroll area
            scroll_area.setWidget(thumbnails_widget)
            self.layout.addWidget(scroll_area)

            # Agregar checkbox para borrar imagenes
            self.delete_images_checkbox = QCheckBox(
                "Delete all saved review images from disk"
            )
            self.delete_images_checkbox.setChecked(True)  # Tildado por defecto
            self.delete_images_checkbox.setStyleSheet("margin-top: 5px;")
            self.layout.addWidget(self.delete_images_checkbox)

            debug_print(
                f"Seccion de thumbnails agregada con {len(image_paths)} imagenes"
            )

        except Exception as e:
            debug_print(f"Error agregando seccion de thumbnails: {e}")

    def extract_frame_number_from_filename(self, filename):
        """
        Extrae el numero de frame de un nombre de archivo.
        Busca patrones como _0001.jpg, _1234.jpg, etc.
        """
        try:
            # Obtener solo el nombre sin extension
            name_without_ext = os.path.splitext(os.path.basename(filename))[0]

            # Buscar el ultimo grupo de 4 digitos precedido por guion bajo
            import re

            match = re.search(r"_(\d{4})(?:_\d+)?$", name_without_ext)
            if match:
                return match.group(1)

            # Si no encuentra el patron, buscar cualquier numero al final
            match = re.search(r"_(\d+)(?:_\d+)?$", name_without_ext)
            if match:
                return match.group(1).zfill(4)  # Rellenar con ceros a la izquierda

            return "----"

        except Exception as e:
            debug_print(f"Error extrayendo numero de frame: {e}")
            return "----"

    def adjust_window_size(self):
        """
        Ajusta el ancho de la ventana basado en el numero de thumbnails.
        Minimo: ancho actual, Maximo: 1500px
        """
        try:
            if not self.review_images:
                return

            # Calcular ancho necesario basado en thumbnails
            thumbnail_width = 150
            thumbnail_spacing = 10
            margin = 40  # Margen total (izquierda + derecha)

            num_images = len(self.review_images)
            required_width = (
                (num_images * thumbnail_width)
                + ((num_images - 1) * thumbnail_spacing)
                + margin
            )

            # Obtener ancho actual de la ventana
            current_width = self.width() if hasattr(self, "width") else 400

            # Aplicar limites: minimo el ancho actual, maximo 1500
            min_width = max(current_width, 400)
            max_width = 1500

            new_width = max(min_width, min(required_width, max_width))

            debug_print(
                f"Ajustando ancho de ventana: {num_images} imagenes, ancho requerido: {required_width}, nuevo ancho: {new_width}"
            )

            self.resize(new_width, self.height())

        except Exception as e:
            debug_print(f"Error ajustando tamaño de ventana: {e}")

    def get_text(self):
        if self.exec_() == QDialog.Accepted:
            return self.text_edit.toPlainText()
        else:
            return None

    def should_delete_images(self):
        """
        Retorna True si el usuario marco el checkbox para borrar imagenes.
        """
        return self.delete_images_checkbox and self.delete_images_checkbox.isChecked()

    def get_review_images(self):
        """
        Retorna la lista de imagenes de review encontradas.
        """
        return self.review_images

    def open_image_with_default_viewer(self, image_path):
        """
        Abre la imagen especificada con el visor de imagenes predeterminado del sistema operativo.
        """
        debug_print(f"Intentando abrir imagen: {image_path}")
        try:
            if platform.system() == "Windows":
                os.startfile(image_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", image_path])
            else:  # Linux y otros
                subprocess.call(["xdg-open", image_path])
            debug_print(f"Imagen abierta exitosamente: {image_path}")
        except Exception as e:
            debug_print(f"Error al abrir la imagen {image_path}: {e}")


def delete_review_pic_cache():
    """
    Borra completamente la carpeta ReviewPic_Cache y todo su contenido.
    """
    try:
        script_dir = os.path.dirname(__file__)
        cache_dir = os.path.join(script_dir, "ReviewPic_Cache")

        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            debug_print(f"Carpeta ReviewPic_Cache borrada: {cache_dir}")
            return True
        else:
            debug_print(f"Carpeta ReviewPic_Cache no existe: {cache_dir}")
            return False

    except Exception as e:
        debug_print(f"Error borrando carpeta ReviewPic_Cache: {e}")
        return False


class ShotGridManager:
    def __init__(self, url, login, password):
        debug_print("Inicializando conexion a ShotGrid (usando conector externo)")
        # Ya no necesitamos inicializar shotgun_api3 aquí
        # Las operaciones se delegarán al conector externo
        self.url = url
        self.login = login
        self.password = password

    def find_shot_and_tasks(self, project_name, shot_code):
        debug_print(f"Buscando proyecto y shot usando conector externo: {project_name} / {shot_code}")
        result = call_flow_connector("find_shot_and_tasks",
                                   project_name=project_name,
                                   shot_code=shot_code)

        if result["success"]:
            project = result.get("project")
            shot = result.get("shot")
            tasks = result.get("tasks")
            debug_print(f"Resultado: project={project is not None}, shot={shot is not None}, tasks={len(tasks) if tasks else 0}")
            return project, shot, tasks
        else:
            debug_print(f"Error en find_shot_and_tasks: {result.get('error', 'Unknown error')}")
            return None, None, None

    def find_tasks_for_shot(self, shot_id):
        debug_print(f"Buscando tareas para shot_id {shot_id} usando conector externo")
        # Este método se llama desde find_shot_and_tasks, así que las tareas ya están incluidas en el resultado
        # Por simplicidad, devolveremos una lista vacía ya que no necesitamos este método por separado
        debug_print("find_tasks_for_shot: método simplificado, tareas obtenidas en find_shot_and_tasks")
        return []

    def find_highest_version_for_shot(self, shot_id):
        debug_print(f"Buscando versión más alta para shot_id {shot_id} usando conector externo")
        result = call_flow_connector("find_highest_version", shot_id=shot_id)

        if result["success"]:
            version = result.get("version")
            version_number = result.get("version_number")
            user_id = result.get("user_id")
            debug_print(f"Versión encontrada: {version_number}, user_id: {user_id}")
            return version, version_number, user_id
        else:
            debug_print(f"Error en find_highest_version_for_shot: {result.get('error', 'Unknown error')}")
            return None, None, None

    def update_task_status(self, task_id, new_status):
        debug_print(f"Actualizando tarea {task_id} a {new_status} usando conector externo")
        result = call_flow_connector("update_task", task_id=task_id, status=new_status)

        if not result["success"]:
            debug_print(f"Error en update_task_status: {result.get('error', 'Unknown error')}")

    def update_version_status(self, project_name, shot_code, version_str, new_status):
        debug_print(f"Actualizando versión {version_str} de {shot_code} a {new_status} usando conector externo")
        result = call_flow_connector("update_version",
                                   project_name=project_name,
                                   shot_code=shot_code,
                                   version_str=version_str,
                                   status=new_status)

        if not result["success"]:
            debug_print(f"Error en update_version_status: {result.get('error', 'Unknown error')}")

    def get_task_assignee(self, task_id):
        debug_print(f"Obteniendo asignado de tarea {task_id} usando conector externo")
        result = call_flow_connector("get_task_assignee", task_id=task_id)

        if result["success"]:
            return result.get("assignee_id")
        else:
            debug_print(f"Error en get_task_assignee: {result.get('error', 'Unknown error')}")
            return None

    def add_comment_to_version(
        self, version_id, project_id, comment, user_id, task_assignee_id, shot_id=None
    ):
        debug_print(f"Agregando comentario a versión {version_id} usando conector externo")
        result = call_flow_connector("add_comment",
                                   version_id=version_id,
                                   project_id=project_id,
                                   comment=comment,
                                   user_id=user_id,
                                   task_assignee_id=task_assignee_id,
                                   shot_id=shot_id)

        if result["success"]:
            return result.get("note")
        else:
            debug_print(f"Error en add_comment_to_version: {result.get('error', 'Unknown error')}")
            return None

    def attach_images_to_note(self, note_id, version_id, image_paths):
        debug_print(f"Adjuntando {len(image_paths)} imágenes a nota {note_id} usando conector externo")
        result = call_flow_connector("attach_images",
                                   note_id=note_id,
                                   version_id=version_id,
                                   image_paths=image_paths)

        if result["success"]:
            debug_print("Imágenes adjuntadas exitosamente")
            return True
        else:
            debug_print(f"Error en attach_images_to_note: {result.get('error', 'Unknown error')}")
            return False

    def extract_frame_number_from_path(self, image_path):
        """
        Método simplificado - la lógica real está en el conector externo
        """
        debug_print("extract_frame_number_from_path: método simplificado")
        return "0001"

    def get_project_id_from_version(self, version_id):
        """
        Método simplificado - obtiene el ID del proyecto usando conector externo
        """
        debug_print(f"Obteniendo project_id de versión {version_id} usando conector externo")
        # Este método no se usa frecuentemente, devolver None por simplicidad
        debug_print("get_project_id_from_version: método simplificado, retornando None")
        return None


class WorkerSignals(QObject):
    result_ready = Signal(str, int, int)
    task_finished = Signal(bool)  # Ahora incluye el estado de exito
    debug_output = Signal()  # Nueva señal para imprimir logs
    version_check_result = Signal(dict)  # Nueva señal para resultado de verificación de versiones


class Worker(QRunnable):
    def __init__(
        self,
        button_name,
        base_name,
        message,
        review_images=None,
        should_delete_images=False,
    ):
        super(Worker, self).__init__()
        self.button_name = button_name
        self.base_name = base_name
        self.message = message
        self.review_images = review_images or []
        self.should_delete_images = should_delete_images
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        db_manager = DBManager()  # Crear la conexión en el hilo correcto
        success = False

        try:
            debug_print(f"Worker: Iniciando operación {self.button_name} para {self.base_name}")

            # PRIMERO: Verificar versiones de forma asíncrona (a menos que se indique saltar)
            skip_check = getattr(self, 'skip_version_check', False)

            if not skip_check:
                version_check = call_flow_connector("check_version", base_name=self.base_name)

                if version_check["success"] and version_check["needs_confirmation"]:
                    # Emitir señal para que el hilo principal muestre el diálogo
                    debug_print("Worker: Se necesita confirmación del usuario para versiones")
                    self.signals.version_check_result.emit(version_check)
                    # El Worker terminará aquí, el hilo principal continuará cuando el usuario confirme
                    return

                # Si no necesita confirmación, continuar con la operación normal
                debug_print("Worker: No se necesita confirmación, procediendo con la operación")
            else:
                debug_print("Worker: Saltando verificación de versiones (ya confirmada por usuario)")

            # Usar la operación optimizada que hace todo en una sola llamada
            result = call_flow_connector("execute_full_push",
                                       button_name=self.button_name,
                                       base_name=self.base_name,
                                       message=self.message,
                                       review_images=self.review_images)

            if result["success"]:
                debug_print("Worker: Operación de red completada exitosamente")
                success = True

                # Si fue exitoso, actualizar también la base de datos local
                self.update_local_database(db_manager)
            else:
                debug_print(f"Worker: Error en operación de red: {result.get('error', 'Unknown error')}")
                success = False

        except Exception as e:
            debug_print(f"Worker: Exception in Worker.run: {e}")
            success = False
        finally:
            # Cerrar la conexión a la base de datos
            if db_manager:
                db_manager.close()

            # Borrar imagenes SOLO si se completó exitosamente y el usuario lo solicitó
            if success and self.should_delete_images:
                debug_print("Worker: Operacion exitosa: Borrando carpeta ReviewPic_Cache como solicitó el usuario")
                delete_review_pic_cache()
            elif not success and self.should_delete_images:
                debug_print("Worker: Operacion fallida: NO se borra la carpeta ReviewPic_Cache")

            self.signals.task_finished.emit(success)
            self.signals.debug_output.emit()  # Emitir señal al finalizar

    def continue_after_version_check(self):
        """Método para continuar la operación después de que el usuario confirme la versión"""
        debug_print("Worker: Continuando después de verificación de versiones")

        # Crear una nueva instancia del Worker con skip_version_check=True
        new_worker = Worker(
            self.button_name,
            self.base_name,
            self.message,
            self.review_images,
            self.should_delete_images
        )

        # Conectar las mismas señales
        new_worker.signals.result_ready.connect(self.signals.result_ready)
        new_worker.signals.task_finished.connect(self.signals.task_finished)
        new_worker.signals.debug_output.connect(self.signals.debug_output)
        new_worker.signals.version_check_result.connect(self.signals.version_check_result)

        # Marcar que debe saltar la verificación de versiones
        new_worker.skip_version_check = True

        # Ejecutar el nuevo Worker
        QThreadPool.globalInstance().start(new_worker)

    def update_local_database(self, db_manager):
        """Actualiza la base de datos local con los cambios"""
        try:
            project_name = self.base_name.split("_")[0]
            parts = self.base_name.split("_")
            shot_code = "_".join(parts[:5])

            version_number_str = None
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    version_number_str = part
                    break

            if not version_number_str:
                return

            version_index = parts.index(version_number_str)
            task_name = parts[version_index - 1].lower()
            sg_status = status_translation.get(self.button_name, None)

            if not sg_status:
                return

            # Buscar shot en base de datos local
            db_shot = db_manager.find_shot(project_name, shot_code)
            if not db_shot:
                debug_print(f"Worker: No se encontró el shot {shot_code} en la base de datos local")
                return

            # Buscar tarea en base de datos local
            db_task = db_manager.find_task(db_shot["id"], task_name)
            if not db_task:
                debug_print(f"Worker: No se encontró la tarea {task_name} en la base de datos local")
                return

            # Actualizar estado de tarea local
            debug_print(f"Worker: Actualizando estado de tarea local (ID: {db_task['id']}) a: {sg_status}")
            db_manager.update_task_status(db_task["id"], sg_status)

            # Obtener la última versión para esta tarea
            latest_version = db_manager.find_latest_version(db_task["id"])
            if latest_version:
                # Decidir qué estado aplicar a la versión dependiendo del estado de la tarea
                version_status = None
                if sg_status == "rev_di" or sg_status == "corr":
                    version_status = "vwd"
                elif sg_status == "rev_su":
                    version_status = "rev"
                elif sg_status == "revleg":
                    version_status = "unvleg"

                if version_status:
                    debug_print(
                        f"Worker: Actualizando estado de versión local (ID: {latest_version['id']}, version: {latest_version['version_number']}) a: {version_status}"
                    )
                    db_manager.update_version_status(
                        db_task["id"],
                        latest_version["version_number"],
                        version_status,
                    )

                # Añadir nota si hay mensaje
                if self.message:
                    debug_print(f"Worker: Añadiendo nota a versión local (ID: {latest_version['id']})")
                    db_manager.add_version_note(latest_version["id"], self.message)

        except Exception as e:
            debug_print(f"Worker: Error actualizando base de datos local: {e}")


class MessageBoxManager:
    def __init__(self):
        self.message_boxes = []

    def show_warning_message(self, info):
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        msg_box = QMessageBox()
        msg_box.setTextFormat(Qt.RichText)  # Permite el formato HTML
        msg_box.setText(info)
        msg_box.setWindowTitle("ShotGrid Version Warning")
        msg_box.setWindowModality(Qt.NonModal)
        msg_box.show()
        self.message_boxes.append(msg_box)


class MultipleShotsDialog(QDialog):
    """Diálogo para informar sobre múltiples shots encontrados"""

    def __init__(self, shots, shot_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Múltiples Shots Encontrados")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Mensaje principal
        msg = QLabel(f"Se encontraron {len(shots)} shots con el nombre '{shot_code}':")
        msg.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(msg)

        # Lista de shots con sus IDs
        for shot in shots:
            shot_info = QLabel(f"• Shot ID: {shot['id']} - {shot['code']}")
            shot_info.setStyleSheet("margin-left: 20px; margin-bottom: 5px;")
            layout.addWidget(shot_info)

        # Mensaje de error
        error_msg = QLabel(
            "No se puede proceder con la operación cuando existen múltiples shots con el mismo nombre."
        )
        error_msg.setStyleSheet(
            "color: #B95C5C; margin-top: 10px; margin-bottom: 10px;"
        )
        layout.addWidget(error_msg)

        # Botón OK
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self.adjustSize()


def show_version_dialog(base_name, local_version, flow_version):
    """Muestra un diálogo preguntando si se desea continuar cuando la versión local es más antigua."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    msgBox = QMessageBox()
    msgBox.setWindowTitle("Verificación de Versión")
    msgBox.setTextFormat(Qt.RichText)

    # Formatear el nombre base con la versión resaltada
    base_version_highlighted = re.sub(
        r"(_)(v\d+)", r'\1<span style="color: #ff9900;">\2</span>', base_name
    )

    msgBox.setText(
        f"<div style='text-align: center;'>"
        f"<span style='color: #ff9900;'><b>¡Atención!</b></span><br><br>"
        f"La versión que intentas actualizar no es la más reciente:<br><br>"
        f"<span style='font-weight: bold;'>{base_version_highlighted}</span><br><br>"
        f"Versión local: <span style='color: #ff9900;'>v{local_version}</span><br>"
        f"Última versión en Flow: <span style='color: #00ff00;'>v{flow_version}</span><br><br>"
        f"¿Deseas continuar de todos modos?</div>"
    )

    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    msgBox.button(QMessageBox.Yes).setText("Continuar de todos modos")
    msgBox.button(QMessageBox.No).setText("Cancelar")

    response = msgBox.exec_()
    return response == QMessageBox.Yes


def handle_results(info, sg_version_number, version_number):
    if sg_version_number > version_number:
        msg_manager.show_warning_message(info)


def handle_version_check_result(version_check_result, worker, update_callback):
    """Maneja el resultado de la verificación de versiones desde el Worker"""
    debug_print("Manejando resultado de verificación de versiones")

    if version_check_result["needs_confirmation"]:
        # Mostrar diálogo de confirmación en el hilo principal
        local_version = version_check_result["local_version"]
        flow_version = version_check_result["flow_version"]
        base_name = version_check_result["base_name"]

        debug_print(f"Mostrando diálogo de confirmación: v{local_version} vs v{flow_version}")

        # Mostrar el diálogo y esperar respuesta del usuario
        if show_version_dialog(base_name, local_version, flow_version):
            # Usuario confirmó, continuar con la operación
            debug_print("Usuario confirmó, continuando con la operación")
            # Aquí podríamos crear un nuevo Worker o continuar el actual
            # Por simplicidad, vamos a crear un nuevo Worker sin verificación
            worker.continue_after_version_check()
        else:
            debug_print("Usuario canceló la operación")
            # Emitir señal de finalización con fallo
            worker.signals.task_finished.emit(False)
            worker.signals.debug_output.emit()


def Push_Task_Status(button_name, base_name, update_callback=None):
    global msg_manager

    # Verificar que tengamos las credenciales disponibles
    sg_url, sg_login, sg_password = get_flow_credentials()

    if not sg_url or not sg_login or not sg_password:
        debug_print(
            "No se pudieron obtener las credenciales de Flow desde la configuración encriptada."
        )
        return False  # Retornar False si faltan credenciales

    # Primero solicitar el mensaje al usuario para ciertos estados
    message = None
    review_images = []
    should_delete_images = False
    sg_status = status_translation.get(button_name, None)
    if sg_status in ["rev_di", "corr", "revleg", "revhld", "revjav"]:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        input_dialog = InputDialog(base_name)
        message = input_dialog.get_text()
        if message is None:
            # Operación cancelada por el usuario al cerrar el diálogo de comentarios
            print_debug_messages()  # Imprimir logs si el usuario cancela
            return False

        # Obtener información adicional del diálogo
        review_images = input_dialog.get_review_images()
        should_delete_images = bool(input_dialog.should_delete_images())
        print_debug_messages()  # Imprimir logs después de obtener la información del diálogo

    # No hacer verificación de versiones aquí - se hace en el Worker
    # Esto evita congelar la UI mientras se consulta Flow

    # Una vez que el usuario ha confirmado (o no hay problema de versiones), proceder con las actualizaciones
    if sg_status in ["rev_di", "corr", "revleg", "revhld", "revjav"]:
        worker = Worker(
            button_name,
            base_name,
            message,
            review_images,
            should_delete_images,
        )
        # Conectar señales
        worker.signals.result_ready.connect(handle_results)
        worker.signals.debug_output.connect(lambda: print_debug_messages())
        worker.signals.version_check_result.connect(
            lambda result: handle_version_check_result(result, worker, update_callback)
        )
        if update_callback:
            worker.signals.task_finished.connect(update_callback)
        QThreadPool.globalInstance().start(worker)
    else:
        worker = Worker(button_name, base_name, None, [], False)
        worker.signals.result_ready.connect(handle_results)
        worker.signals.debug_output.connect(lambda: print_debug_messages())
        worker.signals.version_check_result.connect(
            lambda result: handle_version_check_result(result, worker, update_callback)
        )
        if update_callback:
            worker.signals.task_finished.connect(update_callback)
        QThreadPool.globalInstance().start(worker)

    return True  # Retornar True indicando que la operación fue iniciada


def print_debug_messages():
    if DEBUG:
        print("\n".join(debug_messages))
        debug_messages.clear()  # Limpiar mensajes después de imprimir


msg_manager = MessageBoxManager()
