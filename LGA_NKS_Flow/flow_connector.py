"""
LGA_NKS_Flow_Connector | Conector simple para operaciones de red con Flow
Este script se ejecuta con Python personalizado para evitar problemas de dependencias
"""

import os
import re
import sys
import tempfile
import shutil
from pathlib import Path

# Agregar la ruta de shotgun_api3 al sys.path
script_dir = os.path.dirname(__file__)
shotgun_path = os.path.join(script_dir, "shotgun_api3")
if os.path.exists(shotgun_path):
    sys.path.insert(0, shotgun_path)

import shotgun_api3

# Diccionario de traduccion de estados (igual que en el script principal)
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

# Variable global para activar o desactivar los prints
DEBUG = False

def debug_print(message):
    if DEBUG:
        print(message)

class ShotGridManager:
    def __init__(self, url, login, password):
        debug_print("Inicializando conexion a ShotGrid")
        try:
            self.sg = shotgun_api3.Shotgun(url, login=login, password=password)
            debug_print("Conexion a ShotGrid inicializada exitosamente")
        except Exception as e:
            debug_print(f"Error al inicializar la conexion a ShotGrid: {e}")
            self.sg = None

    def find_shot_and_tasks(self, project_name, shot_code):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return None, None, None
        debug_print(f"Buscando proyecto con nombre: {project_name}")
        try:
            projects = self.sg.find(
                "Project", [["name", "is", project_name]], ["id", "name"]
            )
        except Exception as e:
            debug_print(f"Error buscando proyecto: {e}")
            return None, None, None
        if projects:
            project = projects[0]
            project_id = project["id"]
            debug_print(f"Proyecto encontrado: {project['name']} (ID: {project_id})")
            filters = [
                ["project", "is", {"type": "Project", "id": project_id}],
                ["code", "is", shot_code],
            ]
            fields = ["id", "code", "description"]
            try:
                shots = self.sg.find("Shot", filters, fields)
            except Exception as e:
                debug_print(f"Error buscando shot: {e}")
                return project, None, None
            if shots:
                # Si hay múltiples shots con el mismo nombre, tomar el primero
                if len(shots) > 1:
                    debug_print(
                        f"Múltiples shots encontrados ({len(shots)}) para el código: {shot_code}, usando el primero"
                    )

                shot = shots[0]
                shot_id = shot["id"]
                debug_print(f"Shot encontrado: {shot['code']} (ID: {shot_id})")
                tasks = self.find_tasks_for_shot(shot_id)
                return project, shot, tasks
            else:
                debug_print("No se encontro el Shot con el codigo especificado.")
                return project, None, None
        else:
            debug_print("No se encontro el proyecto con el nombre especificado.")
            return None, None, None

    def find_tasks_for_shot(self, shot_id):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return []
        filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
        fields = ["id", "content", "sg_status_list"]
        try:
            return self.sg.find("Task", filters, fields)
        except Exception as e:
            debug_print(f"Error buscando tareas para shot_id {shot_id}: {e}")
            return []

    def find_highest_version_for_shot(self, shot_id):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return None, None, None
        filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
        fields = ["code", "created_at", "user", "sg_status_list", "description"]
        try:
            versions = self.sg.find("Version", filters, fields)
        except Exception as e:
            debug_print(f"Error buscando versiones para shot_id {shot_id}: {e}")
            return None, None, None
        comp_versions = [v for v in versions if "_comp_" in v["code"].lower()]
        if comp_versions:

            def safe_version_num(v):
                m = re.search(r"_v(\d+)", v["code"])
                return int(m.group(1)) if m else -1

            highest_version = max(comp_versions, key=safe_version_num)
            m = re.search(r"_v(\d+)", highest_version["code"])
            version_number = m.group(1) if m else "0"
            user_id = (
                highest_version["user"]["id"]
                if highest_version.get("user") and highest_version["user"].get("id")
                else None
            )
            return highest_version, version_number, user_id
        return None, None, None

    def update_task_status(self, task_id, new_status):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return
        try:
            debug_print(
                f"Actualizando estado de la tarea (ID: {task_id}) a: {new_status}"
            )
            self.sg.update("Task", task_id, {"sg_status_list": new_status})
        except Exception as e:
            debug_print(f"Error al actualizar el estado de la tarea: {e}")

    def update_version_status(self, project_name, shot_code, version_str, new_status):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return
        try:
            debug_print(
                f"Actualizando estado de la version para el Shot: {shot_code}, Version: {version_str} a: {new_status}"
            )
            filters = [
                ["project.Project.name", "is", project_name],
                ["entity.Shot.code", "is", shot_code],
                ["code", "contains", version_str],
            ]
            versions = self.sg.find("Version", filters, ["id"])
            for version in versions:
                debug_print(
                    f"Actualizando version (ID: {version['id']}) a estado: {new_status}"
                )
                self.sg.update("Version", version["id"], {"sg_status_list": new_status})
        except Exception as e:
            debug_print(f"Error al actualizar el estado de la version: {e}")

    def get_task_assignee(self, task_id):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return None
        try:
            task = self.sg.find_one("Task", [["id", "is", task_id]], ["task_assignees"])
            if task and task["task_assignees"]:
                return task["task_assignees"][0]["id"]
            return None
        except Exception as e:
            debug_print(f"Error al obtener el asignado de la tarea: {e}")
            return None

    def add_comment_to_version(
        self, version_id, project_id, comment, user_id, task_assignee_id, shot_id=None
    ):
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return
        try:
            debug_print(
                f"Agregando comentario a la version (ID: {version_id}): {comment}"
            )
            addressings_to = [{"type": "HumanUser", "id": user_id}]
            if task_assignee_id and task_assignee_id != user_id:
                addressings_to.append({"type": "HumanUser", "id": task_assignee_id})
            note_data = {
                "project": {"type": "Project", "id": project_id},
                "content": comment,
                "note_links": [
                    {"type": "Version", "id": version_id},
                    {"type": "Shot", "id": shot_id},
                ],
                "addressings_to": addressings_to,
            }
            created_note = self.sg.create("Note", note_data)
            return created_note
        except Exception as e:
            debug_print(f"Error al agregar comentario a la version: {e}")
            return None

    def attach_images_to_note(self, note_id, version_id, image_paths):
        """
        Adjunta imagenes a una nota con numeros de frame siguiendo la convencion de ShotGrid.
        Usa upload directo a Note que es el metodo mas simple y efectivo.
        """
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return False

        try:
            # Crear una carpeta temporal para los archivos renombrados
            temp_dir = tempfile.mkdtemp()
            debug_print(f"Carpeta temporal creada: {temp_dir}")

            attached_count = 0

            for image_path in image_paths:
                if not os.path.exists(image_path):
                    debug_print(f"Imagen no encontrada: {image_path}")
                    continue

                # Extraer numero de frame del nombre del archivo
                frame_number = self.extract_frame_number_from_path(image_path)

                # Crear nombre de archivo con convencion de ShotGrid para mostrar frame number
                # Formato: annot_version_<version_id>.<frame_number>.jpg
                file_extension = os.path.splitext(image_path)[1]
                new_filename = (
                    f"annot_version_{version_id}.{frame_number}{file_extension}"
                )
                temp_file_path = os.path.join(temp_dir, new_filename)

                # Copiar archivo con el nuevo nombre
                shutil.copy2(image_path, temp_file_path)
                debug_print(f"Archivo copiado: {image_path} -> {temp_file_path}")

                # Subir archivo directamente a la nota usando el metodo que funciono en exploracion
                try:
                    uploaded_attachment_id = self.sg.upload(
                        "Note", note_id, temp_file_path, field_name="attachments"
                    )

                    if uploaded_attachment_id:
                        attached_count += 1
                        debug_print(
                            f"Imagen adjuntada exitosamente: {new_filename} (ID: {uploaded_attachment_id})"
                        )
                    else:
                        debug_print(
                            f"Error: No se obtuvo ID de attachment para {new_filename}"
                        )

                except Exception as upload_error:
                    debug_print(
                        f"Error subiendo archivo {new_filename}: {upload_error}"
                    )
                    continue

            # Limpiar carpeta temporal
            try:
                shutil.rmtree(temp_dir)
                debug_print(f"Carpeta temporal eliminada: {temp_dir}")
            except Exception as cleanup_error:
                debug_print(f"Error limpiando carpeta temporal: {cleanup_error}")

            debug_print(
                f"Adjuntadas {attached_count} imagenes de {len(image_paths)} totales"
            )
            return attached_count > 0

        except Exception as e:
            debug_print(f"Error adjuntando imagenes a la nota: {e}")
            return False

    def extract_frame_number_from_path(self, image_path):
        """
        Extrae el numero de frame de la ruta de una imagen.
        Busca patrones como _0001.jpg, _1234.jpg, etc.
        """
        try:
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]

            # Buscar el ultimo grupo de 4 digitos precedido por guion bajo
            match = re.search(r"_(\d{4})(?:_\d+)?$", name_without_ext)
            if match:
                return match.group(1)

            # Si no encuentra el patron, buscar cualquier numero al final
            match = re.search(r"_(\d+)(?:_\d+)?$", name_without_ext)
            if match:
                return match.group(1).zfill(4)  # Rellenar con ceros a la izquierda

            return "0001"  # Valor por defecto

        except Exception as e:
            debug_print(f"Error extrayendo numero de frame de {image_path}: {e}")
            return "0001"

    def get_project_id_from_version(self, version_id):
        """
        Obtiene el ID del proyecto a partir del ID de una version.
        """
        if not self.sg:
            debug_print("ShotGrid no inicializado")
            return None
        try:
            version = self.sg.find_one(
                "Version", [["id", "is", version_id]], ["project"]
            )
            if version and version.get("project"):
                return version["project"]["id"]
            return None
        except Exception as e:
            debug_print(f"Error obteniendo project_id de version {version_id}: {e}")
            return None


def execute_full_push_operation(sg_manager, button_name, base_name, message, review_images):
    """
    Ejecuta todo el proceso de push en una sola operación para mayor eficiencia
    """
    try:
        debug_print(f"Ejecutando push completo: {button_name} para {base_name}")

        # Parsear el nombre base
        project_name = base_name.split("_")[0]
        parts = base_name.split("_")
        shot_code = "_".join(parts[:5])

        version_number_str = None
        for part in parts:
            if part.startswith("v") and part[1:].isdigit():
                version_number_str = part
                break

        if not version_number_str:
            return {"success": False, "error": "No se encontró número de versión válido"}

        version_number = int(version_number_str.replace("v", ""))
        version_index = parts.index(version_number_str)
        task_name = parts[version_index - 1].lower()

        debug_print(f"Proyecto: {project_name}, Shot: {shot_code}, Task: {task_name}, Version: {version_number}")

        # Buscar proyecto, shot y tareas
        project, shot, tasks = sg_manager.find_shot_and_tasks(project_name, shot_code)
        if not shot:
            return {"success": False, "error": f"No se encontró el shot {shot_code}"}

        # Encontrar la tarea correspondiente
        sg_status = status_translation.get(button_name)
        if not sg_status:
            return {"success": False, "error": f"No se encontró estado válido para {button_name}"}

        task_id = None
        task_assignee_id = None

        for task in tasks:
            if task["content"].lower() == task_name:
                debug_print(f"Actualizando tarea: {task['content']} (ID: {task['id']})")
                sg_manager.update_task_status(task["id"], sg_status)
                task_id = task["id"]
                task_assignee_id = sg_manager.get_task_assignee(task_id)
                break

        if not task_id:
            return {"success": False, "error": f"No se encontró la tarea {task_name}"}

        # Buscar versión más alta y actualizar estados
        sg_highest_version, sg_version_number, user_id = sg_manager.find_highest_version_for_shot(shot["id"])

        if sg_status in ["rev_di", "corr", "revleg", "revjav"]:
            debug_print(f"Actualizando versión a vwd")
            sg_manager.update_version_status(project_name, shot_code, version_number_str, "vwd")

            # Agregar comentario si hay mensaje
            if message and sg_highest_version:
                debug_print(f"Agregando comentario a versión {sg_highest_version['id']}")
                created_note = sg_manager.add_comment_to_version(
                    sg_highest_version["id"], project["id"], message,
                    user_id, task_assignee_id, shot["id"]
                )

                # Adjuntar imágenes si existen y se creó la nota
                if created_note and review_images:
                    debug_print(f"Adjuntando {len(review_images)} imágenes")
                    sg_manager.attach_images_to_note(
                        created_note["id"], sg_highest_version["id"], review_images
                    )

        elif sg_status == "rev_su":
            debug_print(f"Actualizando versión a rev")
            sg_manager.update_version_status(project_name, shot_code, version_number_str, "rev")

        elif sg_status == "revleg":
            debug_print(f"Actualizando versión a unvleg")
            sg_manager.update_version_status(project_name, shot_code, version_number_str, "unvleg")

        debug_print("Push completado exitosamente")
        return {"success": True, "message": "Push completado exitosamente"}

    except Exception as e:
        error_msg = f"Error en push completo: {str(e)}"
        debug_print(error_msg)
        return {"success": False, "error": error_msg}


def execute_flow_operation(operation, **kwargs):
    """
    Función principal que ejecuta operaciones de Flow
    Se llama desde el script principal usando subprocess
    """
    try:
        # Obtener credenciales
        url = kwargs.get('url')
        login = kwargs.get('login')
        password = kwargs.get('password')

        if not url or not login or not password:
            print("ERROR: Credenciales faltantes")
            return {"success": False, "error": "Credenciales faltantes"}

        # Crear manager
        sg_manager = ShotGridManager(url, login, password)

        if operation == "find_shot_and_tasks":
            project_name = kwargs.get('project_name')
            shot_code = kwargs.get('shot_code')
            project, shot, tasks = sg_manager.find_shot_and_tasks(project_name, shot_code)

            # Convertir objetos datetime a strings para JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, dict):
                    return {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                           for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                else:
                    return obj

            return {
                "success": True,
                "project": convert_datetime(project) if project else None,
                "shot": convert_datetime(shot) if shot else None,
                "tasks": convert_datetime(tasks) if tasks else []
            }

        elif operation == "find_highest_version":
            shot_id = kwargs.get('shot_id')
            version, version_num, user_id = sg_manager.find_highest_version_for_shot(shot_id)

            # Convertir objetos datetime a strings para JSON serialization
            if version:
                version = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                          for k, v in version.items()}

            return {
                "success": True,
                "version": version,
                "version_number": version_num,
                "user_id": user_id
            }

        elif operation == "update_task":
            task_id = kwargs.get('task_id')
            status = kwargs.get('status')
            sg_manager.update_task_status(task_id, status)
            return {"success": True}

        elif operation == "update_version":
            project_name = kwargs.get('project_name')
            shot_code = kwargs.get('shot_code')
            version_str = kwargs.get('version_str')
            status = kwargs.get('status')
            sg_manager.update_version_status(project_name, shot_code, version_str, status)
            return {"success": True}

        elif operation == "get_task_assignee":
            task_id = kwargs.get('task_id')
            assignee_id = sg_manager.get_task_assignee(task_id)
            return {"success": True, "assignee_id": assignee_id}

        elif operation == "add_comment":
            version_id = kwargs.get('version_id')
            project_id = kwargs.get('project_id')
            comment = kwargs.get('comment')
            user_id = kwargs.get('user_id')
            task_assignee_id = kwargs.get('task_assignee_id')
            shot_id = kwargs.get('shot_id')
            note = sg_manager.add_comment_to_version(
                version_id, project_id, comment, user_id, task_assignee_id, shot_id
            )

            # Convertir objetos datetime a strings para JSON serialization
            if note:
                note = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                       for k, v in note.items()}

            return {"success": True, "note": note}

        elif operation == "attach_images":
            note_id = kwargs.get('note_id')
            version_id = kwargs.get('version_id')
            image_paths = kwargs.get('image_paths', [])
            success = sg_manager.attach_images_to_note(note_id, version_id, image_paths)
            return {"success": success}

        elif operation == "execute_full_push":
            # Operación optimizada que hace todo el push de una vez
            button_name = kwargs.get('button_name')
            base_name = kwargs.get('base_name')
            message = kwargs.get('message')
            review_images = kwargs.get('review_images', [])

            return execute_full_push_operation(sg_manager, button_name, base_name, message, review_images)

        elif operation == "check_version":
            # Verificación de versiones para evitar congelar UI
            base_name = kwargs.get('base_name')

            # Parsear el nombre base
            project_name = base_name.split("_")[0]
            parts = base_name.split("_")
            shot_code = "_".join(parts[:5])

            version_number_str = None
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    version_number_str = part
                    break

            if not version_number_str:
                return {"success": True, "needs_confirmation": False}  # Continuar sin verificación

            local_version = int(version_number_str.replace("v", ""))

            # Buscar shot en Flow
            project, shot, _ = sg_manager.find_shot_and_tasks(project_name, shot_code)
            if not shot:
                return {"success": True, "needs_confirmation": False}  # Continuar sin verificación

            # Buscar versión más alta
            sg_highest_version, sg_version_number, _ = sg_manager.find_highest_version_for_shot(shot["id"])

            if sg_highest_version and sg_version_number and int(sg_version_number) > local_version:
                return {
                    "success": True,
                    "needs_confirmation": True,
                    "local_version": local_version,
                    "flow_version": int(sg_version_number),
                    "base_name": base_name
                }

            return {"success": True, "needs_confirmation": False}

        else:
            return {"success": False, "error": f"Operación no soportada: {operation}"}

    except Exception as e:
        print(f"ERROR en flow_connector: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Este código se ejecuta cuando se llama el script directamente
    import json
    import sys

    if len(sys.argv) < 2:
        print("ERROR: Falta operación")
        sys.exit(1)

    operation = sys.argv[1]

    # Leer parámetros desde stdin como JSON
    try:
        params = json.loads(sys.stdin.read())
        result = execute_flow_operation(operation, **params)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Error procesando parámetros: {str(e)}"}))
