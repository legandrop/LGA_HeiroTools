import hiero.core
import os
import re
import shotgun_api3


class ShotGridManager:
    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def get_shot_version(self, project_name, shot_code):
        projects = self.sg.find("Project", [["name", "is", project_name]], ["id"])
        if not projects:
            return None
        project_id = projects[0]["id"]
        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", shot_code],
        ]
        fields = ["code", "sg_version"]
        shots = self.sg.find("Shot", filters, fields)
        return shots[0] if shots else None


def parse_shot_code(file_name):
    base_name = re.sub(r"_%04d\.exr$", "", file_name)
    parts = base_name.split("_")
    return parts[0], "_".join(parts[:5])  # (project_name, shot_code)


def main():
    sg_url = os.getenv("SHOTGRID_URL")
    sg_login = os.getenv("SHOTGRID_LOGIN")
    sg_password = os.getenv("SHOTGRID_PASSWORD")
    if not sg_url or not sg_login or not sg_password:
        print("Faltan variables de entorno.")
        return

    seq = hiero.ui.activeSequence()
    if not seq:
        print("No hay secuencia activa.")
        return

    te = hiero.ui.getTimelineEditor(seq)
    selected = te.selection()
    if not selected:
        print("No hay clips seleccionados.")
        return

    file_path = selected[0].source().mediaSource().fileinfos()[0].filename()
    exr_name = os.path.basename(file_path)
    project_name, shot_code = parse_shot_code(exr_name)

    sg = ShotGridManager(sg_url, sg_login, sg_password)
    shot = sg.get_shot_version(project_name, shot_code)
    if shot:
        print("Nombre del shot:", shot["code"])
        print("Campo custom Version:", shot.get("sg_version", "N/A"))
    else:
        print("Shot no encontrado en ShotGrid.")


main()
