"""
Gestor de manejo de proyectos para el panel de proyectos LGA.
"""

import os
from LGA_QtAdapter_HieroTools import QtWidgets, QtCore
import hiero.core

# Importar funciones necesarias del módulo principal
# Estas serán importadas desde el archivo principal cuando se importe este módulo
ProjectItem = None
is_project_open = None
get_project_sequences = None
debug_print = None


def initialize_project_dependencies(project_item_class, is_open_func, get_seq_func, debug_func):
    """Inicializar las dependencias externas necesarias para el project handler"""
    global ProjectItem, is_project_open, get_project_sequences, debug_print
    ProjectItem = project_item_class
    is_project_open = is_open_func
    get_project_sequences = get_seq_func
    debug_print = debug_func


class ProjectHandler:
    """Clase para manejar las operaciones relacionadas con proyectos"""

    @staticmethod
    def update_projects_display(panel):
        """Actualizar la visualización de la lista de proyectos"""
        debug_print("🔄 Actualizando display de proyectos...")
        debug_print(f"   📊 Proyectos encontrados: {len(panel.proyectos_encontrados)}")
        debug_print(f"   📂 Proyectos abiertos: {len(panel.proyectos_abiertos)} grupos")

        # Limpiar items anteriores
        for i in reversed(range(panel.projects_layout.count())):
            item = panel.projects_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        panel.project_items.clear()

        if not panel.proyectos_encontrados:
            no_projects_label = QtWidgets.QLabel("No se encontraron proyectos en T:\\")
            no_projects_label.setStyleSheet("color: #666; font-style: italic;")
            no_projects_label.setAlignment(QtCore.Qt.AlignCenter)
            panel.projects_layout.addWidget(no_projects_label)
            panel.info_label.setText("")
            return

        for proyecto_info in sorted(panel.proyectos_encontrados, key=lambda x: x.get("nombre_base", "")):
            nombre_base = proyecto_info.get("nombre_base", "")
            version = proyecto_info.get("version", "")
            ruta_hrox = proyecto_info.get("ruta_hrox", "")
            vfx_folder = proyecto_info.get("vfx_folder", "")
            sup_folder = proyecto_info.get("sup_folder", "")

            # Calcular el display formateado
            project_display_name = nombre_base
            if "_SUP" in nombre_base:
                project_display_name = nombre_base.split("_SUP")[0]
            clean_ver = version.lstrip('v')
            formatted_display = f"{project_display_name} (v{clean_ver})"

            debug_print(f"   Creando item UI para: {nombre_base} {version}")
            debug_print(f"      Origen: {vfx_folder}/{sup_folder}")
            debug_print(f"      Archivo: {os.path.basename(ruta_hrox) if ruta_hrox else 'N/A'}")
            debug_print(f"      Display: {formatted_display}")

            item = ProjectItem(proyecto_info, panel)
            item.project_label.mousePressEvent = lambda e, p=proyecto_info: ProjectHandler.on_project_click(panel, p)
            # Instalar event filter para hover del project label
            item.project_label.installEventFilter(panel)

            is_open = is_project_open(ruta_hrox, panel.proyectos_abiertos)
            debug_print(f"      Estado abierto: {is_open}")

            if is_open:
                debug_print("      Este proyecto aparecera como ABIERTO en la UI")

            if is_open:
                nombre_base = proyecto_info.get("nombre_base", "")
                if nombre_base in panel.proyectos_abiertos:
                    proyecto_abierto = panel.proyectos_abiertos[nombre_base][0]
                    proyecto_obj = proyecto_abierto["proyecto"]
                    sequences = get_project_sequences(proyecto_obj)
                    item.set_open_state(True, sequences, proyecto_obj)

            panel.project_items[proyecto_info.get("nombre_base", "")] = item
            panel.projects_layout.addWidget(item)

        total_proyectos = len(panel.proyectos_encontrados)
        proyectos_abiertos_count = sum(1 for item in panel.project_items.values() if item.is_open)
        panel.info_label.setText(f"{total_proyectos} proyectos encontrados, {proyectos_abiertos_count} abiertos")

        debug_print(f"✅ UI actualizada completamente!")
        debug_print(f"   📊 Total items en UI: {len(panel.project_items)}")
        debug_print(f"   📂 Proyectos marcados como abiertos: {proyectos_abiertos_count}")
        debug_print(f"   📋 Etiqueta inferior: '{panel.info_label.text()}'")

        # Mostrar resumen detallado de lo que se muestra en UI
        debug_print("RESUMEN DE PROYECTOS EN UI:")
        for nombre_base, item in sorted(panel.project_items.items()):
            version = item.project_info.get("version", "")
            estado = "ABIERTA" if item.is_open else "cerrada"

            # Calcular display formateado igual que en UI
            project_display_name = nombre_base
            if "_SUP" in nombre_base:
                project_display_name = nombre_base.split("_SUP")[0]
            clean_ver = version.lstrip('v')
            formatted_display = f"{project_display_name} (v{clean_ver})"
            icono = "▼" if item.is_open else "▶"

            debug_print(f"   {icono} {formatted_display} ({estado})")

    @staticmethod
    def on_project_click(panel, proyecto_info):
        """Manejar el click en un proyecto para abrirlo"""
        ruta_hrox = proyecto_info.get("ruta_hrox", "")
        nombre_base = proyecto_info.get("nombre_base", "")
        version = proyecto_info.get("version", "")
        vfx_folder = proyecto_info.get("vfx_folder", "")
        sup_folder = proyecto_info.get("sup_folder", "")

        debug_print(f"🖱️ Click en proyecto: {nombre_base}")
        debug_print(f"   📁 Origen: {vfx_folder}/{sup_folder}")
        debug_print(f"   📄 Archivo: {os.path.basename(ruta_hrox) if ruta_hrox else 'N/A'}")
        debug_print(f"   🔢 Versión en UI: v{version}")

        try:
            debug_print(f"📂 Abriendo proyecto desde: {ruta_hrox}")
            proyecto = hiero.core.openProject(ruta_hrox)
            debug_print(f"✅ Proyecto abierto exitosamente: {proyecto.name()}")
            debug_print("🔄 Iniciando re-escaneo automático...")
            panel.start_scan()
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                panel,
                "Error al abrir proyecto",
                f"No se pudo abrir el proyecto {nombre_base}:\n{str(e)}",
            )
