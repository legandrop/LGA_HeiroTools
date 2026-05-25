"""
Test para verificar que el script corregido maneja correctamente los shots duplicados
"""

import os
import shotgun_api3


def test_fixed_shot_search():
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")

    if not all([sg_url, sg_login, sg_password]):
        print("ERROR: Variables de entorno no configuradas")
        return

    sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)

    def find_shot_and_tasks_fixed(project_name, shot_code):
        """Version corregida que maneja shots duplicados"""
        projects = sg.find("Project", [["name", "is", project_name]], ["id", "name"])
        if projects:
            project_id = projects[0]["id"]
            filters = [
                ["project", "is", {"type": "Project", "id": project_id}],
                ["code", "is", shot_code],
            ]
            fields = ["id", "code", "description"]
            shots = sg.find("Shot", filters, fields)
            if shots:
                print(f"Encontrados {len(shots)} shots con el mismo codigo:")
                for i, shot in enumerate(shots):
                    print(f"  Shot {i+1}: ID {shot['id']}")

                # Si hay múltiples shots con el mismo nombre, buscar el que tiene tasks
                for shot in shots:
                    shot_id = shot["id"]
                    task_filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
                    task_fields = ["id", "content", "sg_status_list"]
                    tasks = sg.find("Task", task_filters, task_fields)

                    print(f"  Shot ID {shot_id} tiene {len(tasks)} tasks")

                    if tasks:  # Si este shot tiene tasks, usarlo
                        print(
                            f"  -> Usando Shot ID {shot_id} (tiene {len(tasks)} tasks)"
                        )
                        return shot, tasks

                # Si ningún shot tiene tasks, usar el primero
                print(
                    f"  -> Ningun shot tiene tasks, usando el primero (ID {shots[0]['id']})"
                )
                return shots[0], []
            else:
                print("No se encontro el shot.")
        else:
            print("No se encontro el proyecto en ShotGrid.")
        return None, None

    # Test con el caso problemático
    project_name = "ETDM"
    shot_code = "ETDM_5027_0220_Chroma_Camioneta"

    print(f"=== TEST DEL SCRIPT CORREGIDO ===")
    print(f"Buscando: {shot_code}")

    shot, tasks = find_shot_and_tasks_fixed(project_name, shot_code)

    if shot and tasks:
        print(f"\n✅ EXITO: Shot encontrado con tasks!")
        print(f"Shot seleccionado: {shot['code']} (ID: {shot['id']})")
        print(f"Tasks encontradas: {len(tasks)}")
        for task in tasks:
            print(f"  - {task['content']} ({task['sg_status_list']})")
    else:
        print(f"\n❌ FALLO: No se encontraron tasks")


if __name__ == "__main__":
    test_fixed_shot_search()
