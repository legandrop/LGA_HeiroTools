"""
LGA_NKS_OrganizeProject.py
Script para organizar clips en bins basado en rutas de archivos.

Extraído de LGA_NKS_EditTools_Panel.py
"""

import hiero.ui
import hiero.core

# Variable global para activar o desactivar los prints
DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

def get_active_project():
    """
    Obtiene el proyecto activo en Hiero.

    Returns:
    - hiero.core.Project o None: El proyecto activo, o None si no se encuentra ninguno.
    """
    projects = hiero.core.projects()
    if projects:
        return projects[0]  # Devuelve el primer proyecto en la lista
    else:
        return None

class OrganizeProject:
    def find_or_create_bin(self, root_bin, bin_name):
        for item in root_bin.items():
            if isinstance(item, hiero.core.Bin) and item.name() == bin_name:
                return item
        new_bin = hiero.core.Bin(bin_name)
        root_bin.addItem(new_bin)
        return new_bin

    def move_clips_from_bin(self, bin_item):
        if (
            bin_item.name() == "Published"
        ):  # Ignorar el bin 'Published' y sus subcarpetas
            return
        for item in bin_item.items():
            if isinstance(item, hiero.core.BinItem) and isinstance(
                item.activeItem(), hiero.core.Clip
            ):
                clip = item.activeItem()
                media_source = clip.mediaSource()
                if media_source and media_source.fileinfos():
                    file_path = media_source.fileinfos()[0].filename()
                    parts = file_path.split("/")
                    if len(parts) > 3:
                        folder_name = f"F {parts[2]}"
                        shot_name = parts[3]
                        folder_bin = self.find_or_create_bin(
                            self.project.clipsBin(), folder_name
                        )
                        shot_bin = self.find_or_create_bin(folder_bin, shot_name)
                        clip_item = clip.binItem()
                        if clip_item.parentBin() != shot_bin:
                            clip_item.parentBin().removeItem(clip_item)
                            shot_bin.addItem(clip_item)
            elif isinstance(item, hiero.core.Bin):
                self.move_clips_from_bin(item)

    def clean_empty_bins(self, bin_item):
        if bin_item.name() == "Published":
            return
        items_to_check = list(bin_item.items())
        for item in items_to_check:
            if isinstance(item, hiero.core.Bin):
                self.clean_empty_bins(item)
        if not bin_item.items() and bin_item.parentBin():
            bin_item.parentBin().removeItem(bin_item)

    def move_clips_based_on_path(self, project):
        self.project = project
        with project.beginUndo("Reorganize Clips Based on Path"):
            for bin_item in project.clipsBin().items():
                if isinstance(bin_item, hiero.core.Bin):
                    self.move_clips_from_bin(bin_item)

            for bin_item in list(project.clipsBin().items()):
                if isinstance(bin_item, hiero.core.Bin):
                    self.clean_empty_bins(bin_item)

    def organize_project(self):
        project = get_active_project()
        if project:
            self.move_clips_based_on_path(project)
        else:
            debug_print("No se encontro un proyecto abierto en Hiero.")

def main():
    """Función principal que ejecuta organize_project."""
    organizer = OrganizeProject()
    organizer.organize_project()

if __name__ == "__main__":
    main()