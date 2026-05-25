import os
import sys

# Agregar la ruta de shotgun_api3 al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "LGA_ToolPack"))

import shotgun_api3


def debug_print(*args):
    print("[DEBUG]:", *args)


class ShotCreator:
    """Clase para crear shots en ShotGrid."""

    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def find_project_by_name(self, project_name):
        """Encuentra un proyecto por nombre."""
        projects = self.sg.find(
            "Project", [["name", "is", project_name]], ["id", "name"]
        )
        if projects:
            return projects[0]
        return None

    def find_sequence_by_name(self, project_id, sequence_name):
        """Encuentra una secuencia por nombre."""
        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", sequence_name],
        ]
        sequences = self.sg.find("Sequence", filters, ["id", "code"])
        if sequences:
            return sequences[0]
        return None

    def find_task_template_by_name(self, template_name):
        """Encuentra un task template por nombre."""
        templates = self.sg.find(
            "TaskTemplate", [["code", "is", template_name]], ["id", "code"]
        )
        if templates:
            return templates[0]
        return None

    def upload_thumbnail(self, entity_type, entity_id, thumbnail_path):
        """Sube un thumbnail a una entidad en ShotGrid."""
        if not os.path.exists(thumbnail_path):
            print(f"ERROR: No se encontro el archivo de thumbnail: {thumbnail_path}")
            return False

        try:
            debug_print(f"Subiendo thumbnail: {thumbnail_path}")
            result = self.sg.upload_thumbnail(entity_type, entity_id, thumbnail_path)
            debug_print(f"Thumbnail subido exitosamente: {result}")
            return True
        except Exception as e:
            print(f"ERROR al subir thumbnail: {e}")
            return False

    def create_shot(
        self,
        project_name,
        shot_code,
        sequence_name,
        description,
        task_template_name,
        thumbnail_path=None,
    ):
        """Crea un shot en ShotGrid."""
        debug_print(f"Iniciando creacion de shot: {shot_code}")

        # Buscar proyecto
        project = self.find_project_by_name(project_name)
        if not project:
            print(f"ERROR: No se encontro el proyecto '{project_name}'")
            return None

        debug_print(f"Proyecto encontrado: {project['name']} (ID: {project['id']})")

        # Buscar secuencia
        sequence = self.find_sequence_by_name(project["id"], sequence_name)
        if not sequence:
            print(
                f"ERROR: No se encontro la secuencia '{sequence_name}' en el proyecto '{project_name}'"
            )
            return None

        debug_print(f"Secuencia encontrada: {sequence['code']} (ID: {sequence['id']})")

        # Buscar task template
        task_template = self.find_task_template_by_name(task_template_name)
        if not task_template:
            print(f"ERROR: No se encontro el task template '{task_template_name}'")
            return None

        debug_print(
            f"Task Template encontrado: {task_template['code']} (ID: {task_template['id']})"
        )

        # Verificar si el shot ya existe
        existing_shot = self.sg.find(
            "Shot",
            [
                ["project", "is", {"type": "Project", "id": project["id"]}],
                ["code", "is", shot_code],
            ],
            ["id", "code"],
        )

        if existing_shot:
            print(f"El shot '{shot_code}' ya existe con ID: {existing_shot[0]['id']}")
            # Si existe y hay thumbnail, subirlo
            if thumbnail_path:
                self.upload_thumbnail("Shot", existing_shot[0]["id"], thumbnail_path)
            return existing_shot[0]

        # Crear el shot
        shot_data = {
            "project": {"type": "Project", "id": project["id"]},
            "code": shot_code,
            "description": description,
            "sg_sequence": {"type": "Sequence", "id": sequence["id"]},
            "task_template": {"type": "TaskTemplate", "id": task_template["id"]},
        }

        try:
            new_shot = self.sg.create("Shot", shot_data)
            debug_print(
                f"Shot creado exitosamente: {new_shot['code']} (ID: {new_shot['id']})"
            )

            # Subir thumbnail si se proporciono
            if thumbnail_path:
                self.upload_thumbnail("Shot", new_shot["id"], thumbnail_path)

            return new_shot
        except Exception as e:
            print(f"ERROR al crear el shot: {e}")
            return None


def main():
    # Configuracion hardcodeada
    shot_code = "ETDM_3061_0015_DeAging_AutoNoche_testo"
    project_name = "ETDM"  # Extraido del nombre del shot
    sequence_name = "103"
    description = "Descripcion test"
    task_template_name = "Template_comp"
    thumbnail_path = r"C:\Users\leg4-pc\.nuke\Python\Startup\LGA_HieroTools\LGA_NKS_Flow\ShotThumbs_Cache\ETDM_3028_0060_DeAging_CasaSangre_1752722135.jpg"

    # Variables de entorno para ShotGrid
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")

    if not sg_url or not sg_login or not sg_password:
        print(
            "ERROR: Las variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y SHOTGRID_PASSWORD deben estar configuradas."
        )
        return

    debug_print("Conectando a ShotGrid...")
    shot_creator = ShotCreator(sg_url, sg_login, sg_password)

    result = shot_creator.create_shot(
        project_name=project_name,
        shot_code=shot_code,
        sequence_name=sequence_name,
        description=description,
        task_template_name=task_template_name,
        thumbnail_path=thumbnail_path,
    )

    if result:
        print(f"EXITO: Shot '{shot_code}' procesado correctamente.")
    else:
        print(f"ERROR: No se pudo procesar el shot '{shot_code}'.")


if __name__ == "__main__":
    main()
