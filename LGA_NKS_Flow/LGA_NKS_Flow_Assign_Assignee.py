"""
________________________________________________________________

  LGA_NKS_Flow_Assign_Assignee v1.23 | Lega
  Asigna un usuario a una tarea en ShotGrid (Flow) a partir del base_name y nombre de usuario

  v1.23: Actualiza la base de datos local pipesync.db con la asignación
  
  v1.22: Verifica y asigna automáticamente el proyecto al usuario si no lo tiene asignado
        antes de asignar la task comp

  v1.21: Actualizado para ser compatible con ambos sistemas de nomenclatura:
        - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
        - PROYECTO_SEQ_SHOT (3 bloques simplificado)

________________________________________________________________
"""

import os
import sys
import json
import sqlite3
import platform
import shotgun_api3
from PySide2.QtCore import QRunnable, Slot, QThreadPool, Signal, QObject, Qt
from PySide2.QtWidgets import (
    QApplication,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide2.QtGui import QFont

# Agregar la ruta actual al sys.path para importar SecureConfig_Reader
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from SecureConfig_Reader import get_flow_credentials
from LGA_NKS_Flow_NamingUtils import (
    extract_shot_code,
    extract_project_name,
    extract_task_name,
)

DEBUG = False
debug_messages = []


class DBManager:
    """Clase simplificada para manejar operaciones con la base de datos SQLite local."""

    def __init__(self):
        # Selecciona la ruta de la base de datos según el sistema operativo
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

    def add_task_assignment(self, task_id, assigned_to):
        """Añade una asignación de tarea en la base de datos local."""
        if not self.conn:
            debug_print("No hay conexión a la base de datos")
            return False

        try:
            cur = self.conn.cursor()
            # Primero verificar si ya existe la asignación
            cur.execute(
                "SELECT id FROM task_assignments WHERE task_id = ? AND assigned_to = ?",
                (task_id, assigned_to)
            )
            existing = cur.fetchone()

            if existing:
                debug_print(f"La asignación ya existe en la base de datos local")
                return True

            # Si no existe, insertar nueva asignación
            cur.execute(
                """
                INSERT INTO task_assignments (task_id, assigned_to)
                VALUES (?, ?)
                """,
                (task_id, assigned_to),
            )
            self.conn.commit()
            debug_print(
                f"Asignación añadida a la tarea local (ID: {task_id}) para: {assigned_to}"
            )
            return True
        except Exception as e:
            debug_print(f"Error al añadir asignación a la tarea local: {e}")
            return False

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            self.conn = None


def debug_print(message):
    if DEBUG:
        debug_messages.append(str(message))


def print_debug_messages():
    if DEBUG and debug_messages:
        print("\n".join(debug_messages))
        debug_messages.clear()


def get_user_info_from_config(user_name):
    """
    Obtiene información del usuario desde el archivo de configuración.

    Args:
        user_name (str): Nombre del usuario en Flow

    Returns:
        tuple: (user_name, user_color) o (user_name, "#666666") si no se encuentra
    """
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "LGA_NKS_Flow_Users.json"
        )

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                users = config.get("users", [])

                for user in users:
                    if user.get("name") == user_name:
                        return user.get("name", user_name), user.get("color", "#666666")

        # Si no se encuentra, usar valores por defecto
        return user_name, "#666666"

    except Exception as e:
        debug_print(f"Error leyendo configuración de usuarios: {e}")
        return user_name, "#666666"


# Clase de ventana de estado para mostrar progreso de asignación en Flow
class FlowStatusWindow(QDialog):
    def __init__(self, user_name, user_color, task_type="asignar usuario", parent=None):
        super(FlowStatusWindow, self).__init__(parent)
        self.setWindowTitle("Flow | Assign User")
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
        if task_type == "asignar usuario":
            task_text = "Asignando usuario"
        elif task_type == "obtener asignados":
            task_text = "Obteniendo asignados"
        elif task_type == "limpiar asignados":
            task_text = "Limpiando asignados"
        else:
            task_text = "Procesando"

        initial_message = (
            f"<div style='text-align: left;'>"
            f"<span style='color: #CCCCCC; '>{task_text} </span>"
            f"<span style='color: #CCCCCC; background-color: {user_color}; '>{user_name}</span>"
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

    def update_shot_info(self, shot_name, task_name=None):
        """Actualiza la ventana con el shot que se está procesando"""
        shot_html = "<div style='text-align: left;'>"
        shot_html += f"<span style='color: #CCCCCC; '>Shot:</span> <span style='color: #6AB5CA; '>{shot_name}</span>"
        if task_name:
            shot_html += f"<br><span style='color: #CCCCCC; '>Task:</span> <span style='color: #B56AB5; '>{task_name}</span>"
        shot_html += "</div>"
        self.shot_label.setText(shot_html)
        self._adjust_window_size()

    def show_processing_message(self):
        """Muestra el mensaje de procesamiento"""
        processing_html = f"<span style='color: #CCCCCC; '>Conectando a Flow Production Tracking...</span>"
        self.result_label.setText(processing_html)
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
    def __init__(self, url, login, password):
        debug_print("Inicializando conexion a ShotGrid para asignar usuario")
        try:
            self.sg = shotgun_api3.Shotgun(url, login=login, password=password)
            debug_print("Conexion a ShotGrid inicializada exitosamente")
        except Exception as e:
            debug_print(f"Error al inicializar la conexion a ShotGrid: {e}")
            self.sg = None

    def find_shot_and_task_id(self, project_name, shot_code, task_name_lower):
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return None, None
        debug_print(f"Buscando proyecto con nombre: {project_name}")
        try:
            projects = self.sg.find(
                "Project", [["name", "is", project_name]], ["id", "name"]
            )
        except Exception as e:
            debug_print(f"Error buscando proyecto: {e}")
            return None, None
        if not projects:
            debug_print("No se encontro el proyecto con el nombre especificado.")
            return None, None
        project_id = projects[0]["id"]
        filters_shot = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", shot_code],
        ]
        fields_shot = ["id", "code"]
        shots = self.sg.find("Shot", filters_shot, fields_shot)
        if not shots:
            debug_print("No se encontro el Shot con el codigo especificado.")
            return None, None
        shot_id = shots[0]["id"]
        shot_code_found = shots[0]["code"]
        debug_print(f"Shot encontrado: {shot_code_found} (ID: {shot_id})")
        filters_task = [
            ["entity", "is", {"type": "Shot", "id": shot_id}],
            ["content", "is", task_name_lower],
        ]
        fields_task = ["id", "content", "task_assignees"]
        tasks = self.sg.find("Task", filters_task, fields_task)
        if not tasks:
            filters_task_all = [["entity", "is", {"type": "Shot", "id": shot_id}]]
            fields_task_all = ["id", "content", "task_assignees"]
            all_tasks = self.sg.find("Task", filters_task_all, fields_task_all)
            for task in all_tasks:
                if task["content"].lower() == task_name_lower:
                    tasks = [task]
                    break
        if tasks:
            task = tasks[0]
            debug_print(f"Task encontrada: {task['content']} (ID: {task['id']})")
            return shot_code_found, task
        else:
            debug_print(
                f"No se encontro la tarea '{task_name_lower}' para el shot {shot_code_found}."
            )
            return shot_code_found, None

    def find_user_by_name(self, user_name):
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return None
        try:
            users = self.sg.find(
                "HumanUser", [["name", "is", user_name]], ["id", "name"]
            )
            if users:
                debug_print(
                    f"Usuario encontrado: {users[0]['name']} (ID: {users[0]['id']})"
                )
                return users[0]
            else:
                debug_print(f"No se encontro el usuario '{user_name}' en ShotGrid.")
                return None
        except Exception as e:
            debug_print(f"Error buscando usuario: {e}")
            return None

    def check_user_has_project(self, user, project_name):
        """
        Verifica si un usuario tiene asignado un proyecto específico.

        Args:
            user (dict): Diccionario del usuario con campo 'projects'
            project_name (str): Nombre del proyecto a verificar

        Returns:
            tuple: (bool, int) - (True si tiene el proyecto, project_id)
        """
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return False, None

        try:
            # Buscar el proyecto
            projects = self.sg.find(
                "Project", [["name", "is", project_name]], ["id", "name"]
            )

            if not projects:
                debug_print(f"No se encontro el proyecto '{project_name}' en Flow.")
                return False, None

            project_id = projects[0]["id"]
            user_projects = user.get("projects", [])

            # Verificar si el proyecto está en la lista del usuario
            for proj_ref in user_projects:
                if proj_ref.get("id") == project_id:
                    debug_print(
                        f"Usuario ya tiene asignado el proyecto '{project_name}'"
                    )
                    return True, project_id

            debug_print(f"Usuario NO tiene asignado el proyecto '{project_name}'")
            return False, project_id

        except Exception as e:
            debug_print(f"Error al verificar proyecto del usuario: {e}")
            return False, None

    def assign_project_to_user(self, user_id, project_id):
        """
        Asigna un proyecto a un usuario en Flow.

        Args:
            user_id (int): ID del usuario
            project_id (int): ID del proyecto a asignar

        Returns:
            bool: True si se asignó exitosamente
        """
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return False

        try:
            # Obtener el usuario con sus proyectos actuales
            user = self.sg.find_one(
                "HumanUser", [["id", "is", user_id]], ["id", "name", "projects"]
            )

            if not user:
                debug_print(f"No se encontro el usuario con ID {user_id}")
                return False

            current_projects = user.get("projects", [])

            # Verificar si el proyecto ya está asignado
            for proj_ref in current_projects:
                if proj_ref.get("id") == project_id:
                    debug_print(f"El proyecto ya estaba asignado al usuario")
                    return True  # Ya está asignado, consideramos éxito

            # Agregar el proyecto a la lista
            new_project_ref = {"type": "Project", "id": project_id}
            new_projects = current_projects + [new_project_ref]

            # Actualizar el usuario
            result = self.sg.update("HumanUser", user_id, {"projects": new_projects})

            if result:
                debug_print(f"Proyecto asignado exitosamente al usuario {user_id}")
                return True
            else:
                debug_print(f"Fallo al asignar proyecto al usuario {user_id}")
                return False

        except Exception as e:
            debug_print(f"Error al asignar proyecto al usuario: {e}")
            return False

    def add_assignee_to_task(self, task_id, current_assignees, user):
        if not self.sg:
            debug_print("Conexion a ShotGrid no esta inicializada")
            return False, "Conexion a ShotGrid no inicializada"
        try:
            # Evitar duplicados
            assignees = current_assignees or []
            if any(u["id"] == user["id"] for u in assignees):
                debug_print(f"El usuario ya es asignado de la tarea.")
                return True, "El usuario ya estaba asignado a la tarea."
            new_assignees = assignees + [user]
            result = self.sg.update("Task", task_id, {"task_assignees": new_assignees})
            if result:
                debug_print(f"Usuario asignado exitosamente a la tarea {task_id}")
                return True, f"Usuario asignado exitosamente."
            else:
                debug_print(f"Fallo al asignar usuario a la tarea {task_id}")
                return False, f"Fallo al actualizar la tarea."
        except Exception as e:
            debug_print(f"Error al asignar usuario: {e}")
            return False, f"Error al asignar usuario: {e}"


class WorkerSignals(QObject):
    shot_info_ready = Signal(str, str)  # shot_name, task_name
    finished = Signal(bool, str)  # success, message
    error = Signal(str)


class AssignAssigneeWorker(QRunnable):
    def __init__(self, base_name, user_name, status_window):
        super(AssignAssigneeWorker, self).__init__()
        self.base_name = base_name
        self.user_name = user_name
        self.status_window = status_window
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            debug_print(f"=== Iniciando asignación para usuario: {self.user_name} ===")

            # Obtener credenciales de Flow DENTRO del worker
            sg_url, sg_login, sg_password = get_flow_credentials_secure()
            if not all([sg_url, sg_login, sg_password]):
                self.signals.error.emit(
                    "No se pudieron obtener las credenciales de Flow desde SecureConfig."
                )
                return

            # Crear manager ShotGrid DENTRO del worker
            sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
            if not sg_manager.sg:
                self.signals.error.emit(
                    "No se pudo inicializar la conexión a ShotGrid."
                )
                return

            # Extraer datos usando funciones compartidas de NamingUtils
            project_name = extract_project_name(self.base_name)
            shot_code = extract_shot_code(self.base_name)
            task_name_extracted = extract_task_name(self.base_name)

            if not task_name_extracted:
                self.signals.error.emit(
                    "Error: No se encontro un nombre de tarea valido en el nombre base."
                )
                return

            task_name = task_name_extracted.lower()

            # Emitir información del shot y task
            self.signals.shot_info_ready.emit(shot_code, task_name)

            debug_print(
                f"Buscando shot y tarea para el proyecto: {project_name}, Shot: {shot_code}, Tarea: {task_name}"
            )
            shot_name_found, task = sg_manager.find_shot_and_task_id(
                project_name, shot_code, task_name
            )
            shot_name = shot_name_found if shot_name_found else shot_code
            if not task:
                self.signals.error.emit(
                    f"No se encontro la tarea '{task_name}' para el shot {shot_name}."
                )
                return

            # Buscar el usuario (necesitamos obtener también el campo 'projects')
            user = sg_manager.find_user_by_name(self.user_name)
            if not user:
                self.signals.error.emit(
                    f"No se encontro el usuario '{self.user_name}' en ShotGrid."
                )
                return

            # Obtener el usuario completo con proyectos para verificar asignación
            user_with_projects = sg_manager.sg.find_one(
                "HumanUser", [["id", "is", user["id"]]], ["id", "name", "projects"]
            )

            if not user_with_projects:
                self.signals.error.emit(
                    f"No se pudo obtener información completa del usuario '{self.user_name}'."
                )
                return

            # Verificar si el usuario tiene asignado el proyecto
            project_assigned = False
            has_project, project_id = sg_manager.check_user_has_project(
                user_with_projects, project_name
            )

            if not has_project and project_id:
                # El usuario no tiene el proyecto asignado, asignarlo
                debug_print(
                    f"Asignando proyecto '{project_name}' al usuario '{self.user_name}'"
                )
                project_assigned = sg_manager.assign_project_to_user(
                    user_with_projects["id"], project_id
                )
                if not project_assigned:
                    debug_print(
                        f"Advertencia: No se pudo asignar el proyecto, pero continuando con la asignación de la task"
                    )

            # Asignar el usuario a la task
            current_assignees = task.get("task_assignees", [])
            success, message = sg_manager.add_assignee_to_task(
                task["id"], current_assignees, user
            )

            if success:
                # Actualizar base de datos local
                self.update_local_database(project_name, shot_name_found, task_name, self.user_name)

                # Construir mensaje de éxito
                success_message = f"Usuario '{self.user_name}' asignado exitosamente a {shot_name}/{task_name}"
                if project_assigned:
                    success_message += (
                        f" y proyecto '{project_name}' asignado al usuario"
                    )

                self.signals.finished.emit(True, success_message)
            else:
                self.signals.error.emit(message)

        except Exception as e:
            debug_print(f"Error en AssignAssigneeWorker: {e}")
            self.signals.error.emit(f"Error: {str(e)}")

    def update_local_database(self, project_name, shot_name, task_name, user_name):
        """Actualiza la base de datos local añadiendo el asignado a la tarea."""
        try:
            db_manager = DBManager()
            if not db_manager.conn:
                debug_print("No se pudo conectar a la base de datos local")
                return

            # Buscar shot en base de datos local
            db_shot = db_manager.find_shot(project_name, shot_name)
            if not db_shot:
                debug_print(f"No se encontró el shot {shot_name} en la base de datos local")
                db_manager.close()
                return

            # Buscar tarea en base de datos local
            db_task = db_manager.find_task(db_shot["id"], task_name)
            if not db_task:
                debug_print(f"No se encontró la tarea {task_name} en la base de datos local")
                db_manager.close()
                return

            # Añadir asignación a la tarea local
            debug_print(f"Añadiendo asignación a la tarea local (ID: {db_task['id']}) para: {user_name}")
            db_manager.add_task_assignment(db_task["id"], user_name)

            db_manager.close()

        except Exception as e:
            debug_print(f"Error actualizando base de datos local: {e}")


def get_flow_credentials_secure():
    sg_url, sg_login, sg_password = get_flow_credentials()
    if not sg_url or not sg_login or not sg_password:
        debug_print(
            "No se pudieron obtener las credenciales de Flow desde SecureConfig."
        )
        return None, None, None

    # Para Flow, usamos login directo en lugar de API key
    return sg_url, sg_login, sg_password


# Variable global para mantener referencia a la ventana
_status_window = None


def assign_assignee_to_task(base_name, user_name):
    """
    Función principal del script de asignación.

    Args:
        base_name (str): Nombre base del clip
        user_name (str): Nombre del usuario a asignar
    """
    global _status_window

    debug_print(
        f"=== Iniciando LGA_NKS_Flow_Assign_Assignee para usuario: {user_name} ==="
    )

    # Obtener información del usuario para la ventana
    user_display_name, user_color = get_user_info_from_config(user_name)

    # Crear aplicación Qt si no existe
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Crear y mostrar ventana de estado
    _status_window = FlowStatusWindow(user_display_name, user_color, "asignar usuario")
    _status_window.show()
    _status_window.show_processing_message()  # Mostrar mensaje de procesamiento

    # Crear worker para procesamiento en hilo separado
    worker = AssignAssigneeWorker(base_name, user_name, _status_window)

    # Conectar señales
    worker.signals.shot_info_ready.connect(
        lambda shot_name, task_name, window=_status_window: window.update_shot_info(
            shot_name, task_name
        )
    )
    worker.signals.finished.connect(
        lambda success, message, window=_status_window: window.show_success(message)
    )
    worker.signals.error.connect(
        lambda error_msg, window=_status_window: window.show_error(error_msg)
    )

    # Ejecutar en hilo separado
    QThreadPool.globalInstance().start(worker)

    debug_print("=== Worker iniciado en hilo separado ===")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python LGA_NKS_Flow_Assign_Assignee.py <base_name> <user_name>")
    else:
        base_name = sys.argv[1]
        user_name = sys.argv[2]
        assign_assignee_to_task(base_name, user_name)
