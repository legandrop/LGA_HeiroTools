import os
import shotgun_api3


def debug_print(*args):
    print("[DEBUG]:", *args)


def main():
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")

    if not sg_url or not sg_login or not sg_password:
        print(
            "Faltan variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y/o SHOTGRID_PASSWORD."
        )
        return

    sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)

    # Obtener campos disponibles para Shot
    shot_fields = sg.schema_field_read("Shot")
    debug_print("Campos disponibles para Shot:")
    for field in ["project", "code", "description", "sg_sequence", "task_template"]:
        print(f" - {field}: {'✓' if field in shot_fields else '✗'}")

    # Obtener campos disponibles para Task
    task_fields = sg.schema_field_read("Task")
    debug_print("Campos disponibles para Task:")
    for field in ["content", "entity", "task_template", "sg_status_list"]:
        print(f" - {field}: {'✓' if field in task_fields else '✗'}")

    # Verificar si existe el Task Template "Template_comp"
    filters = [["code", "is", "Template_comp"]]
    fields = ["id", "code"]
    templates = sg.find("TaskTemplate", filters, fields)

    if templates:
        debug_print(
            f'Se encontró Task Template "Template_comp" con ID: {templates[0]["id"]}'
        )
    else:
        debug_print('No se encontró Task Template llamado "Template_comp"')


if __name__ == "__main__":
    main()
