"""
LGA_NKS_Flow_Pull_BinItem v1.0 | Versión que usa binItem.items() directamente
Esta versión omite doScan y usa las versiones ya disponibles en el binItem
"""

import json
import hiero.core
import hiero.ui
import os
import re
import sys
import nuke
import shotgun_api3
import logging
import threading
import time
from pathlib import Path

# Importar utilidades de naming
sys.path.append(str(Path(__file__).parent.parent))
from LGA_NKS_Flow_NamingUtils import (
    extract_shot_code,
    extract_project_name,
    extract_task_name,
    clean_base_name,
)

# Importar utilidades para obtener clips
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import TRACK_comp_EXR
else:
    TRACK_comp_EXR = "_comp_"

from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt


# Configurar logging para escribir en tiempo real a un archivo
def setup_debug_logging():
    """Configura el logging para debug que escribe en tiempo real a un archivo."""
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'debugPy.log')

    # Asegurar que el directorio de logs existe
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Configurar el logger
    logger = logging.getLogger('debug_logger')
    logger.setLevel(logging.DEBUG)
    # 🔑 CLAVE: Desactivar propagación al logger root (consola CMD)
    logger.propagate = False

    # Limpiar handlers existentes para evitar duplicados
    if logger.handlers:
        logger.handlers.clear()

    # Crear handler para archivo con encoding UTF-8 y escritura inmediata
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Formato simple sin timestamp extra (ya que debug_print no los incluye)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def clear_debug_log():
    """Limpia el archivo de log al iniciar cada ejecución."""
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'debugPy.log')
    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"Warning: No se pudo limpiar el archivo de log: {e}")


# Inicializar el logger de debug
debug_logger = setup_debug_logging()


def debug_print(*message):
    """Función de debug para logging"""
    msg = ' '.join(str(arg) for arg in message)
    print(msg)  # Mantener el print original
    debug_logger.info(msg)  # Agregar escritura al archivo de log

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
    """Clase para manejar operaciones con datos de la base de datos SQLite."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        try:
            import sqlite3
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            debug_print(f"Error conectando a DB: {e}")

# El orden de los valores es:
        # (nombre en Flow/ShotGrid, color_hex[, tag XYplorer])
        self.task_status_dict = {
            "noread": ("Not Ready To Start", "#000000", None),
            "wts": ("Waiting to start", "#000000", None),
            "ready": ("Ready To Start", "#8a8a8a", None),
            "progre": ("In Progress", "#7d4cff", None),
            "corr": ("Corrections", "#2e77d4", "Corrections"),
            "rev_su": ("Review Sup", "#bd7f9f", "Rev_Sup"),
            "revjua": ("Review Juano", "#9a4a79", "Rev_Sup"),
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

    def find_shot(self, project_name, shot_code):
        """Busca un shot por nombre y codigo."""
        if not self.conn:
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
            shot = cur.fetchone()
            if not shot:
                return None

            # Obtener las tasks
            cur.execute("SELECT * FROM tasks WHERE shot_id = ?", (shot["id"],))
            tasks = cur.fetchall()
            shot_dict = dict(shot)
            shot_dict["tasks"] = []
            for task in tasks:
                task_dict = dict(task)
                cur.execute("SELECT assigned_to FROM task_assignments WHERE task_id = ?", (task["id"],))
                assign = cur.fetchone()
                if assign:
                    task_dict["task_assigned_to"] = assign["assigned_to"]
                else:
                    task_dict["task_assigned_to"] = None

                cur.execute("SELECT * FROM versions WHERE task_id = ? ORDER BY version_number DESC", (task["id"],))
                versions = cur.fetchall()
                task_dict["versions"] = [dict(v) for v in versions]
                shot_dict["tasks"].append(task_dict)
            return shot_dict
        except Exception as e:
            debug_print(f"Error en find_shot: {e}")
            return None

    def find_task(self, shot, task_name):
        """Busca una tarea especifica por nombre."""
        for t in shot["tasks"]:
            if t["task_type"].lower() == task_name.lower():
                return t
        return None

    def find_highest_version_for_shot(self, shot):
        """Encuentra la version mas alta de un shot."""
        all_versions = []
        for task in shot["tasks"]:
            all_versions.extend(task["versions"])
        if all_versions:
            highest_version = max(
                all_versions,
                key=lambda v: v["version_number"] if v["version_number"] is not None else 0
            )
            return {
                "version_number": f"{shot['shot_name']}_comp_v{highest_version['version_number']:03d}",
                "version_status": highest_version.get("status", ""),
                "version_description": highest_version.get("description", ""),
            }
        return None

class VersionManager:
    """Clase para manejar cambios de versión usando binItem.items() directamente"""

    def __init__(self, sg_manager):
        self.sg_manager = sg_manager

    def get_highest_version(self, binItem):
        """Obtiene la version mas alta de un binItem usando items() directamente (sin doScan)."""
        debug_print(f"Obteniendo versiones directamente de binItem para {binItem.name()} (sin doScan)")

        # Obtener versiones disponibles directamente del binItem (sin doScan)
        versions = binItem.items()
        debug_print(f"Versiones disponibles para {binItem.name()}:")
        for v in versions:
            debug_print(f"  - {v.name()}")

        if not versions:
            debug_print(f"No se encontraron versiones en binItem")
            return None

        try:
            highest_version = max(
                versions, key=lambda v: extract_version_number(v.name())
            )
            debug_print(f"Version mas alta seleccionada: {highest_version.name()}")
            return highest_version
        except Exception as e:
            debug_print(f"Error al obtener la version mas alta: {e}")
            return None

    def change_clip_to_highest_version(self, clip):
        """Cambia un clip a su versión más alta usando binItem.items() directamente."""
        debug_print(f"Procesando clip: {clip.name()}")

        try:
            # Obtener información del clip
            file_path = clip.source().mediaSource().fileinfos()[0].filename() if clip.source().mediaSource().fileinfos() else None
            if not file_path:
                debug_print(f"No se puede obtener file_path para {clip.name()}")
                return False

            if "_comp_" not in os.path.basename(file_path).lower():
                debug_print(f"El archivo no contiene '_comp_': {file_path}")
                return False

            # Extraer información del proyecto/shot
            base_name = os.path.basename(file_path)
            base_name_clean = clean_base_name(base_name)

            project_name = extract_project_name(base_name_clean)
            shot_code = extract_shot_code(base_name_clean)
            task_name = extract_task_name(base_name_clean)

            debug_print(f"Project: {project_name}, Shot: {shot_code}, Task: {task_name}")

            # Buscar shot en ShotGrid
            shot = self.sg_manager.find_shot(project_name, shot_code)
            if not shot:
                debug_print(f"Shot no encontrado: {shot_code}")
                return False

            task = self.sg_manager.find_task(shot, task_name)
            if not task:
                debug_print(f"Task no encontrada: {task_name}")
                return False

            highest_sg_version = self.sg_manager.find_highest_version_for_shot(shot)
            if not highest_sg_version:
                debug_print("No se encontró versión en SG")
                return False

            sg_version_num = extract_version_number(highest_sg_version["version_number"])

            # Verificar si el clip necesita actualización
            current_version_str = os.path.basename(file_path)
            current_version_num = extract_version_number(current_version_str)

            debug_print(f"Versión actual: v{current_version_num:03d}, Versión SG: v{sg_version_num:03d}")

            if sg_version_num <= current_version_num:
                debug_print(f"Clip ya está en versión correcta o superior")
                return True

            # Cambiar versión del clip
            bin_item = clip.source().binItem()
            if not bin_item:
                debug_print(f"No se puede obtener binItem")
                return False

            highest_version = self.get_highest_version(bin_item)
            if not highest_version:
                debug_print(f"No se pudo encontrar versión más alta")
                return False

            debug_print(f"Cambiando de {bin_item.activeVersion().name()} a {highest_version.name()}")
            bin_item.setActiveVersion(highest_version)

            # Verificar cambio
            new_version = bin_item.activeVersion()
            new_version_num = extract_version_number(new_version.name())
            debug_print(f"Versión cambiada exitosamente a: {new_version.name()}")

            return new_version_num >= sg_version_num

        except Exception as e:
            debug_print(f"Error procesando clip {clip.name()}: {e}")
            return False

def run_pull_with_binitem():
    """Ejecuta el pull usando binItem.items() directamente para el cambio de versiones"""

    # Limpiar el log al inicio de cada ejecución
    clear_debug_log()

    # Configurar DB path
    if platform.system() == "Windows":
        db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
    elif platform.system() == "Darwin":
        db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
    else:
        debug_print(f"Sistema operativo no soportado: {platform.system()}")
        return

    if not os.path.exists(db_path):
        debug_print(f"DB file not found: {db_path}")
        return

    # Inicializar managers
    sg_manager = ShotGridManager(db_path)
    version_manager = VersionManager(sg_manager)

    # Obtener clips seleccionados
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No active sequence")
        return

    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection() if te else []

    if not selected_clips:
        # Si no hay selección, procesar todos los clips del track comp
        all_tracks = seq.videoTracks()
        selected_clips = []
        for track in all_tracks:
            if track.name() == TRACK_comp_EXR:
                selected_clips.extend(track.items())
                break

    if not selected_clips:
        debug_print("No clips found to process")
        return

    # Procesar cada clip
    processed = 0
    updated = 0

    for clip in selected_clips:
        if isinstance(clip, hiero.core.EffectTrackItem):
            continue

        processed += 1
        if version_manager.change_clip_to_highest_version(clip):
            updated += 1

    debug_print(f"Procesamiento completado: {updated}/{processed} clips actualizados")

if __name__ == "__main__":
    import platform
    run_pull_with_binitem()
