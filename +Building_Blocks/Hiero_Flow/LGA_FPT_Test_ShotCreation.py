import os
import sys

# Agregar la ruta de shotgun_api3 al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "LGA_ToolPack"))

import shotgun_api3


def debug_print(*args):
    print("[DEBUG]:", *args)


class ShotTester:
    """Clase para testear que un shot existe y tiene las propiedades correctas."""

    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def test_shot_properties(
        self,
        project_name,
        shot_code,
        expected_sequence,
        expected_description,
        expected_task_template,
    ):
        """Verifica que el shot existe y tiene las propiedades esperadas."""
        debug_print(f"Testeando shot: {shot_code}")

        # Buscar proyecto
        projects = self.sg.find(
            "Project", [["name", "is", project_name]], ["id", "name"]
        )
        if not projects:
            print(f"ERROR: No se encontro el proyecto '{project_name}'")
            return False

        project_id = projects[0]["id"]
        debug_print(f"Proyecto encontrado: {projects[0]['name']} (ID: {project_id})")

        # Buscar shot con todas sus propiedades
        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", shot_code],
        ]
        fields = ["id", "code", "description", "sg_sequence", "task_template"]

        shots = self.sg.find("Shot", filters, fields)
        if not shots:
            print(f"ERROR: No se encontro el shot '{shot_code}'")
            return False

        shot = shots[0]
        debug_print(f"Shot encontrado: {shot['code']} (ID: {shot['id']})")

        # Verificar propiedades del shot
        test_results = []

        # 1. Verificar descripción
        if shot.get("description") == expected_description:
            print(f"✓ Descripcion correcta: '{shot['description']}'")
            test_results.append(True)
        else:
            print(
                f"✗ Descripcion incorrecta. Esperado: '{expected_description}', Actual: '{shot.get('description')}'"
            )
            test_results.append(False)

        # 2. Verificar secuencia
        if shot.get("sg_sequence"):
            sequence_id = shot["sg_sequence"]["id"]
            sequence_info = self.sg.find_one(
                "Sequence", [["id", "is", sequence_id]], ["id", "code"]
            )
            if sequence_info and sequence_info["code"] == expected_sequence:
                print(
                    f"✓ Secuencia correcta: '{sequence_info['code']}' (ID: {sequence_id})"
                )
                test_results.append(True)
            else:
                print(
                    f"✗ Secuencia incorrecta. Esperado: '{expected_sequence}', Actual: '{sequence_info['code'] if sequence_info else 'None'}'"
                )
                test_results.append(False)
        else:
            print(f"✗ No se encontro secuencia asignada al shot")
            test_results.append(False)

        # 3. Verificar task template
        if shot.get("task_template"):
            template_id = shot["task_template"]["id"]
            template_info = self.sg.find_one(
                "TaskTemplate", [["id", "is", template_id]], ["id", "code"]
            )
            if template_info and template_info["code"] == expected_task_template:
                print(
                    f"✓ Task Template correcto: '{template_info['code']}' (ID: {template_id})"
                )
                test_results.append(True)
            else:
                print(
                    f"✗ Task Template incorrecto. Esperado: '{expected_task_template}', Actual: '{template_info['code'] if template_info else 'None'}'"
                )
                test_results.append(False)
        else:
            print(f"✗ No se encontro task template asignado al shot")
            test_results.append(False)

        # 4. Verificar que se crearon las tareas
        tasks = self.sg.find(
            "Task",
            [["entity", "is", {"type": "Shot", "id": shot["id"]}]],
            ["id", "content", "sg_status_list"],
        )
        if tasks:
            print(f"✓ Tareas creadas: {len(tasks)} tarea(s)")
            for task in tasks:
                print(f"  - {task['content']} (Estado: {task['sg_status_list']})")
            test_results.append(True)
        else:
            print(f"✗ No se encontraron tareas asociadas al shot")
            test_results.append(False)

        # Resultado final
        all_passed = all(test_results)
        if all_passed:
            print(
                f"\n✓ EXITO: Todas las propiedades del shot '{shot_code}' son correctas"
            )
        else:
            print(
                f"\n✗ FALLO: Algunas propiedades del shot '{shot_code}' no son correctas"
            )

        return all_passed


def main():
    # Configuracion hardcodeada - misma que en el script de creación
    shot_code = "ETDM_3061_0015_DeAging_AutoNoche_backup"
    project_name = "ETDM"
    expected_sequence = "103"
    expected_description = "Descripcion test"
    expected_task_template = "Template_comp"

    # Variables de entorno para ShotGrid
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")

    if not sg_url or not sg_login or not sg_password:
        print(
            "ERROR: Las variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y SHOTGRID_PASSWORD deben estar configuradas."
        )
        return

    debug_print("Conectando a ShotGrid para test...")
    shot_tester = ShotTester(sg_url, sg_login, sg_password)

    result = shot_tester.test_shot_properties(
        project_name=project_name,
        shot_code=shot_code,
        expected_sequence=expected_sequence,
        expected_description=expected_description,
        expected_task_template=expected_task_template,
    )

    if result:
        print(
            f"\n🎉 TEST PASSED: El shot '{shot_code}' tiene todas las propiedades correctas."
        )
    else:
        print(
            f"\n❌ TEST FAILED: El shot '{shot_code}' no tiene todas las propiedades correctas."
        )


if __name__ == "__main__":
    main()
