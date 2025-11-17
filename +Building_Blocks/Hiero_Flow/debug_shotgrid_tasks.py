"""
Script de debug para investigar por que el shot ETDM_5027_0220_Chroma_Camioneta
no encuentra sus tasks asociadas en ShotGrid.
"""

import os
import shotgun_api3


def debug_shotgrid_shot():
    # Configuracion hardcodeada para debug
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")

    if not all([sg_url, sg_login, sg_password]):
        print("ERROR: Variables de entorno no configuradas")
        return

    sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)

    # Datos del problema
    project_name = "ETDM"
    shot_code = "ETDM_5027_0220_Chroma_Camioneta"

    print(f"=== DEBUG SHOTGRID SHOT SEARCH ===")
    print(f"Buscando proyecto: {project_name}")
    print(f"Buscando shot: {shot_code}")
    print("")

    # 1. Buscar el proyecto
    projects = sg.find("Project", [["name", "is", project_name]], ["id", "name"])
    print(f"Proyectos encontrados: {len(projects)}")
    for p in projects:
        print(f"  - {p['name']} (ID: {p['id']})")

    if not projects:
        print("ERROR: No se encontro el proyecto")
        return

    project_id = projects[0]["id"]
    print(f"\nUsando proyecto ID: {project_id}")

    # 2. Buscar el shot exacto
    print(f"\n=== BUSQUEDA EXACTA DEL SHOT ===")
    filters = [
        ["project", "is", {"type": "Project", "id": project_id}],
        ["code", "is", shot_code],
    ]
    fields = ["id", "code", "description"]
    shots = sg.find("Shot", filters, fields)

    print(f"Shots encontrados con codigo exacto '{shot_code}': {len(shots)}")
    for shot in shots:
        print(
            f"  - {shot['code']} (ID: {shot['id']}) - Desc: {shot.get('description', 'None')}"
        )

    # 3. Buscar shots similares
    print(f"\n=== BUSQUEDA DE SHOTS SIMILARES ===")
    similar_filters = [
        ["project", "is", {"type": "Project", "id": project_id}],
        ["code", "contains", "ETDM_5027_0220"],
    ]
    similar_shots = sg.find("Shot", similar_filters, fields)

    print(f"Shots encontrados que contienen 'ETDM_5027_0220': {len(similar_shots)}")
    for shot in similar_shots:
        print(
            f"  - {shot['code']} (ID: {shot['id']}) - Desc: {shot.get('description', 'None')}"
        )

    # 4. Si encontramos el shot, buscar sus tasks
    if shots:
        shot_id = shots[0]["id"]
        print(f"\n=== BUSQUEDA DE TASKS PARA SHOT ID {shot_id} ===")

        # Buscar tasks con diferentes filtros para debug
        task_filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
        task_fields = [
            "id",
            "content",
            "sg_status_list",
            "sg_description",
            "entity",
            "project",
        ]

        tasks = sg.find("Task", task_filters, task_fields)
        print(f"Tasks encontradas: {len(tasks)}")

        for task in tasks:
            print(f"  - Task ID: {task['id']}")
            print(f"    Nombre: {task['content']}")
            print(f"    Estado: {task['sg_status_list']}")
            print(f"    Descripcion: {task.get('sg_description', 'None')}")
            print(f"    Entity: {task['entity']}")
            print(f"    Project: {task['project']}")
            print("")

    # 5. Buscar la task especifica del URL proporcionado
    print(f"\n=== BUSQUEDA DE TASK ESPECIFICA ID 17842 ===")
    specific_task = sg.find_one(
        "Task",
        [["id", "is", 17842]],
        ["id", "content", "sg_status_list", "entity", "project"],
    )

    if specific_task:
        print(f"Task 17842 encontrada:")
        print(f"  - Nombre: {specific_task['content']}")
        print(f"  - Estado: {specific_task['sg_status_list']}")
        print(f"  - Entity: {specific_task['entity']}")
        print(f"  - Project: {specific_task['project']}")

        # Verificar si esta task esta asociada a nuestro shot
        if specific_task["entity"]["id"] == shots[0]["id"] if shots else False:
            print("  - Esta task SI esta asociada al shot que buscamos")
        else:
            print("  - Esta task NO esta asociada al shot que buscamos")
            if shots:
                print(f"    Shot esperado ID: {shots[0]['id']}")
                print(f"    Shot real de la task: {specific_task['entity']['id']}")
    else:
        print("Task 17842 no encontrada")


if __name__ == "__main__":
    debug_shotgrid_shot()
