import hiero.core
import os
import re
import shotgun_api3
import sys
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QMessageBox

# Importar utilidades de naming
naming_utils_path = os.path.join(os.path.dirname(__file__), "..", "..", "LGA_NKS_Flow")
if os.path.isdir(naming_utils_path):
    sys.path.insert(0, os.path.abspath(naming_utils_path))
try:
    from LGA_NKS_Flow_NamingUtils import (
        extract_shot_code,
        extract_project_name,
        clean_base_name,
    )
except ImportError:
    extract_shot_code = None
    extract_project_name = None
    clean_base_name = None

class ShotGridManager:
    """Clase para manejar operaciones en ShotGrid."""
    def __init__(self, url, login, password):
        self.sg = shotgun_api3.Shotgun(url, login=login, password=password)

    def find_shot_and_tasks(self, project_name, shot_code):
        """Encuentra el shot en ShotGrid."""
        projects = self.sg.find("Project", [['name', 'is', project_name]], ['id', 'name'])
        if projects:
            project_id = projects[0]['id']
            filters = [
                ['project', 'is', {'type': 'Project', 'id': project_id}],
                ['code', 'is', shot_code]
            ]
            fields = ['id', 'code', 'description']
            shots = self.sg.find("Shot", filters, fields)
            if shots:
                return shots[0]
            else:
                return None
        else:
            return None

    def find_tasks_for_shot(self, shot_id):
        """Encuentra las tareas asociadas a un shot."""
        filters = [['entity', 'is', {'type': 'Shot', 'id': shot_id}]]
        fields = ['id', 'content', 'sg_status_list']
        return self.sg.find("Task", filters, fields)


class HieroOperations:
    """Clase para manejar operaciones en Hiero."""
    def __init__(self, shotgrid_manager):
        self.sg_manager = shotgrid_manager

    def parse_exr_name(self, file_name):
        """Extrae el nombre base del archivo EXR y el numero de version."""
        if clean_base_name:
            base_name = clean_base_name(file_name)
        else:
            base_name = re.sub(r'_%04d\.exr$', '', file_name)
        version_match = re.search(r'_v(\d+)', file_name)
        version_number = version_match.group(1) if version_match else 'Unknown'
        return base_name, version_number

    def process_selected_clips(self):
        """Procesa los clips seleccionados en el timeline de Hiero."""
        seq = hiero.ui.activeSequence()
        if seq:
            te = hiero.ui.getTimelineEditor(seq)
            selected_clips = te.selection()
            results = []

            if selected_clips:
                for clip in selected_clips:
                    file_path = clip.source().mediaSource().fileinfos()[0].filename()
                    exr_name = os.path.basename(file_path)
                    base_name, version_number = self.parse_exr_name(exr_name)

                    parts = base_name.split('_')
                    project_name = (
                        extract_project_name(base_name)
                        if extract_project_name
                        else (parts[0] if parts else "")
                    )
                    shot_code = (
                        extract_shot_code(base_name)
                        if extract_shot_code
                        else '_'.join(parts[:5])
                    )

                    # Realizar operacion intensiva en ShotGrid
                    QCoreApplication.processEvents()
                    shot = self.sg_manager.find_shot_and_tasks(project_name, shot_code)
                    
                    QCoreApplication.processEvents()
                    if shot:
                        shot_info = {
                            "shot_code": shot['code'],
                            "description": shot['description']
                        }
                        results.append(shot_info)
                    QCoreApplication.processEvents()
            self.display_results(results)
        else:
            print("No se encontro una secuencia activa en Hiero.")

    def display_results(self, results):
        """Muestra los resultados recopilados en una ventana simple."""
        from PySide2.QtWidgets import QDialog, QVBoxLayout, QTextEdit

        message = """
        <style>
            p { line-height: 1.5; margin: 0; padding: 0; }
        </style>
        """
        for result in results:
            description = result['description'] if result['description'] is not None else "No info available"
            message += f"<p><b style='color:#CCCC00;'>{result['shot_code']}</b><br>"
            message += f"{description}</p><br>"

        dialog = QDialog()
        dialog.setWindowTitle("Info")

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(message)
        layout.addWidget(text_edit)

        dialog.setLayout(layout)
        dialog.adjustSize()  # Ajusta el tamano del dialogo segun su contenido

        # Obtener el tamano ajustado y sumar pixeles al ancho
        width = dialog.sizeHint().width() + 10
        height = dialog.sizeHint().height()

        dialog.resize(width, height)  # Redimensiona el dialogo con el nuevo ancho

        dialog.exec_()


def main():
    sg_url = os.getenv('SHOTGRID_URL')
    sg_login = os.getenv('SHOTGRID_LOGIN')
    sg_password = os.getenv('SHOTGRID_PASSWORD')

    if not sg_url or not sg_login or not sg_password:
        print("Las variables de entorno SHOTGRID_URL, SHOTGRID_LOGIN y SHOTGRID_PASSWORD deben estar configuradas.")
        return

    sg_manager = ShotGridManager(sg_url, sg_login, sg_password)
    hiero_ops = HieroOperations(sg_manager)
    hiero_ops.process_selected_clips()    


if __name__ == "__main__":
    main()
