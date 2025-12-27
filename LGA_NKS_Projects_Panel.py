"""
Panel de Proyectos LGA integrado para Hiero con recarga inteligente.
- Escanea proyectos en T:\, muestra versiones y secuencias abiertas.
- Permite abrir proyectos y secuencias (cross-project) sin perder ajustes de viewer.
- Incluye botón de reimport/redock para aplicar cambios al vuelo.
"""

import hiero.ui
import hiero.core
import os
import importlib
import sys
from pathlib import Path
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt

# Variable global para activar o desactivar los prints
DEBUG = True

# Variable global para controlar si se debe crear panel automáticamente
# Se usa en smart reload para evitar creación duplicada
AUTO_CREATE_PANEL = True


def debug_print(*message):
    if DEBUG:
        print(*message)


# Buscar y añadir la ruta del módulo de escaneo al sys.path
projects_panel_path = None

# Método 1: carpeta LGA_Projects_Panel junto a este script
try:
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir / "LGA_Projects_Panel"
    if (candidate / "LGA_Projects_Panel_ScanProjects.py").exists():
        projects_panel_path = candidate
except Exception:
    pass

# Método 2: Buscar en sys.path y subcarpetas LGA_*
if projects_panel_path is None:
    for path_str in sys.path:
        try:
            path = Path(path_str)
            if (path / "LGA_Projects_Panel_ScanProjects.py").exists():
                projects_panel_path = path
                break
            if path.exists():
                for subdir in path.iterdir():
                    if subdir.is_dir() and subdir.name.startswith("LGA_"):
                        if (subdir / "LGA_Projects_Panel_ScanProjects.py").exists():
                            projects_panel_path = subdir
                            break
                if projects_panel_path:
                    break
        except Exception:
            continue

# Método 3: rutas estándar en .nuke
if projects_panel_path is None:
    standard_paths = [
        Path.home() / ".nuke" / "Python" / "Startup" / "LGA_Projects_Panel",
        Path(os.path.expanduser("~")) / ".nuke" / "Python" / "Startup" / "LGA_Projects_Panel",
    ]
    for test_path in standard_paths:
        if (test_path / "LGA_Projects_Panel_ScanProjects.py").exists():
            projects_panel_path = test_path
            break

# Añadir al sys.path si se encontró
if projects_panel_path and projects_panel_path.exists():
    if str(projects_panel_path) not in sys.path:
        sys.path.insert(0, str(projects_panel_path))

# Importar funciones del módulo de escaneo
try:
    from LGA_Projects_Panel_ScanProjects import (
        scan_projects_on_disk,
        get_open_projects_info,
        is_project_open,
        get_project_sequences,
    )
except ImportError as e:
    raise ImportError(
        f"No se pudo importar LGA_Projects_Panel_ScanProjects: {e}. Buscado en: {projects_panel_path}"
    )

# Importar función de cambio de secuencia V3 híbrida
try:
    import importlib

    import LGA_Projects_Panel_SwitchSequence

    importlib.reload(LGA_Projects_Panel_SwitchSequence)
    from LGA_Projects_Panel_SwitchSequence import switch_to_sequence_hybrid as switch_to_sequence

    debug_print("✅ Módulo LGA_Projects_Panel_SwitchSequence recargado exitosamente")
except ImportError as e:
    raise ImportError(f"No se pudo importar LGA_Projects_Panel_SwitchSequence: {e}")


class WorkerSignals(QtCore.QObject):
    """Señales para comunicar resultados del worker de escaneo"""

    scan_finished = QtCore.Signal(list, dict)  # proyectos_encontrados, proyectos_abiertos
    error = QtCore.Signal(str)


class ScanWorker(QtCore.QRunnable):
    """Worker para escanear proyectos en background"""

    def __init__(self, base_path="T:\\"):
        super(ScanWorker, self).__init__()
        self.base_path = base_path
        self.signals = WorkerSignals()

    def run(self):
        """Ejecuta el escaneo en hilo secundario"""
        try:
            proyectos_encontrados = scan_projects_on_disk(self.base_path)
            proyectos_abiertos = get_open_projects_info()
            self.signals.scan_finished.emit(proyectos_encontrados, proyectos_abiertos)
        except Exception as e:
            self.signals.error.emit(f"Error durante escaneo: {str(e)}")


class ProjectItem(QtWidgets.QWidget):
    """Widget personalizado para mostrar un proyecto y sus secuencias"""

    def __init__(self, project_info, parent=None):
        super(ProjectItem, self).__init__(parent)
        self.project_info = project_info
        self.is_open = False
        self.sequences = []
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Nombre del proyecto (clickable)
        self.project_label = QtWidgets.QLabel()
        self.project_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.project_label.setStyleSheet("font-weight: bold; color: #2E86C1;")
        self.project_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        layout.addWidget(self.project_label)

        # Contenedor para secuencias
        self.sequences_widget = QtWidgets.QWidget()
        self.sequences_layout = QtWidgets.QVBoxLayout(self.sequences_widget)
        self.sequences_layout.setContentsMargins(20, 0, 0, 0)
        self.sequences_widget.hide()
        layout.addWidget(self.sequences_widget)

        self.update_display()

    def update_display(self):
        nombre = self.project_info.get("nombre_base", "")
        version = self.project_info.get("version", "")

        if self.is_open and self.sequences:
            self.project_label.setText(f"📂 {nombre}_{version} (Abierto)")
            self.project_label.setStyleSheet("font-weight: bold; color: #28B463;")
            self.show_sequences()
        else:
            self.project_label.setText(f"📁 {nombre}_{version}")
            self.project_label.setStyleSheet("font-weight: bold; color: #2E86C1;")
            self.sequences_widget.hide()

    def show_sequences(self):
        # Limpiar secuencias anteriores
        for i in reversed(range(self.sequences_layout.count())):
            self.sequences_layout.itemAt(i).widget().setParent(None)

        proyecto_obj = self.project_info.get("proyecto_obj")
        sequences_dict = {}

        if proyecto_obj:
            try:
                for seq in proyecto_obj.sequences():
                    try:
                        sequences_dict[seq.name()] = seq
                    except Exception:
                        continue
            except Exception:
                pass

        for seq_name in sorted(self.sequences):
            seq_label = QtWidgets.QLabel(f"▶ {seq_name}")
            seq_label.setStyleSheet("color: #66BB6A;")
            seq_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

            seq_obj = sequences_dict.get(seq_name)
            seq_label.mousePressEvent = (
                lambda e, name=seq_name, so=seq_obj, po=self.project_info.get("proyecto_obj"): self.on_sequence_click(name, so, po)
            )
            self.sequences_layout.addWidget(seq_label)

        self.sequences_widget.show()

    def on_sequence_click(self, sequence_name, sequence_obj=None, proyecto_obj=None):
        """Abrir secuencia en timeline preservando ajustes (cross-project)"""
        try:
            success = switch_to_sequence(sequence_name, target_project=proyecto_obj)
            if success:
                debug_print(f"✅ Secuencia '{sequence_name}' cambiada exitosamente")
            else:
                debug_print(f"❌ Error cambiando a secuencia '{sequence_name}'")
        except Exception as e:
            debug_print(f"❌ Error en cambio de secuencia '{sequence_name}': {e}")
            import traceback

            debug_print(traceback.format_exc())

    def set_open_state(self, is_open, sequences=None, proyecto_obj=None):
        self.is_open = is_open
        if sequences is not None:
            self.sequences = sequences
        if proyecto_obj:
            self.project_info["proyecto_obj"] = proyecto_obj
        self.update_display()


class ProjectsPanel(QtWidgets.QWidget):
    """Panel final integrado: escaneo, apertura y cambio de secuencias"""

    def __init__(self):
        super(ProjectsPanel, self).__init__()

        self.setObjectName("com.lega.ProjectsPanel")
        self.setWindowTitle("Projects")
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Estado
        self.proyectos_encontrados = []
        self.proyectos_abiertos = {}
        self.project_items = {}

        self.setup_ui()
        self.setup_connections()
        self.start_scan()

    def setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Título
        title_label = QtWidgets.QLabel("Panel de Proyectos LGA")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 6px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

        # Barra de herramientas
        toolbar_layout = QtWidgets.QHBoxLayout()

        self.refresh_button = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_button.setToolTip("Re-escanear proyectos")
        toolbar_layout.addWidget(self.refresh_button)

        self.status_label = QtWidgets.QLabel("Listo")
        self.status_label.setStyleSheet("color: #666;")
        toolbar_layout.addWidget(self.status_label)

        toolbar_layout.addStretch()

        self.reimport_button = QtWidgets.QPushButton("♻ Reimport")
        self.reimport_button.setToolTip("Recarga y redockea el panel con el script externo")
        toolbar_layout.addWidget(self.reimport_button)

        self.main_layout.addLayout(toolbar_layout)

        # Área de scroll para la lista de proyectos
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.projects_widget = QtWidgets.QWidget()
        self.projects_layout = QtWidgets.QVBoxLayout(self.projects_widget)
        self.projects_layout.setAlignment(QtCore.Qt.AlignTop)

        scroll_area.setWidget(self.projects_widget)
        self.main_layout.addWidget(scroll_area)

        # Información de estado
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 6px;")
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.info_label)

    def setup_connections(self):
        self.refresh_button.clicked.connect(self.start_scan)
        self.reimport_button.clicked.connect(self.reimport_panel)

    def start_scan(self):
        self.status_label.setText("Escaneando...")
        self.status_label.setStyleSheet("color: #F39C12;")
        self.refresh_button.setEnabled(False)

        worker = ScanWorker()
        worker.signals.scan_finished.connect(self.on_scan_finished)
        worker.signals.error.connect(self.on_scan_error)
        QtCore.QThreadPool.globalInstance().start(worker)

    def on_scan_finished(self, proyectos_encontrados, proyectos_abiertos):
        self.proyectos_encontrados = proyectos_encontrados
        self.proyectos_abiertos = proyectos_abiertos

        self.status_label.setText("Listo")
        self.status_label.setStyleSheet("color: #28B463;")
        self.refresh_button.setEnabled(True)

        self.update_projects_display()

    def on_scan_error(self, error_msg):
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #E74C3C;")
        self.refresh_button.setEnabled(True)
        QtWidgets.QMessageBox.warning(self, "Error de Escaneo", error_msg)

    def update_projects_display(self):
        # Limpiar items anteriores
        for i in reversed(range(self.projects_layout.count())):
            item = self.projects_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.project_items.clear()

        if not self.proyectos_encontrados:
            no_projects_label = QtWidgets.QLabel("No se encontraron proyectos en T:\\")
            no_projects_label.setStyleSheet("color: #666; font-style: italic;")
            no_projects_label.setAlignment(QtCore.Qt.AlignCenter)
            self.projects_layout.addWidget(no_projects_label)
            self.info_label.setText("")
            return

        for proyecto_info in sorted(self.proyectos_encontrados, key=lambda x: x.get("nombre_base", "")):
            item = ProjectItem(proyecto_info)
            item.project_label.mousePressEvent = lambda e, p=proyecto_info: self.on_project_click(p)

            ruta_hrox = proyecto_info.get("ruta_hrox", "")
            is_open = is_project_open(ruta_hrox, self.proyectos_abiertos)

            if is_open:
                nombre_base = proyecto_info.get("nombre_base", "")
                if nombre_base in self.proyectos_abiertos:
                    proyecto_abierto = self.proyectos_abiertos[nombre_base][0]
                    proyecto_obj = proyecto_abierto["proyecto"]
                    sequences = get_project_sequences(proyecto_obj)
                    item.set_open_state(True, sequences, proyecto_obj)

            self.project_items[proyecto_info.get("nombre_base", "")] = item
            self.projects_layout.addWidget(item)

        total_proyectos = len(self.proyectos_encontrados)
        proyectos_abiertos_count = sum(1 for item in self.project_items.values() if item.is_open)
        self.info_label.setText(f"{total_proyectos} proyectos encontrados, {proyectos_abiertos_count} abiertos")

    def on_project_click(self, proyecto_info):
        ruta_hrox = proyecto_info.get("ruta_hrox", "")
        nombre_base = proyecto_info.get("nombre_base", "")

        try:
            proyecto = hiero.core.openProject(ruta_hrox)
            debug_print(f"Proyecto abierto: {proyecto.name()}")
            self.start_scan()
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error al abrir proyecto",
                f"No se pudo abrir el proyecto {nombre_base}:\n{str(e)}",
            )

    def reimport_panel(self):
        """Recarga el panel usando el script externo de smart reload"""
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_Projects_Panel", "LGA_NKS_Projects_Panel_Smart_Reload.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_Projects_Panel_Smart_Reload", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                module.main()
                debug_print("Ejecutado LGA_NKS_Projects_Panel_Smart_Reload script.")
            else:
                debug_print(f"Script not found at path: {script_path}")
        except Exception as e:
            debug_print(f"Error durante reimportación: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Error durante reimportación:\n{str(e)}")


# Crear la instancia del widget y añadirlo al gestor de ventanas de Hiero
# SOLO si AUTO_CREATE_PANEL está activado (controlado por smart reload)
if AUTO_CREATE_PANEL:
    projectsPanel = ProjectsPanel()
    wm = hiero.ui.windowManager()
    wm.addWindow(projectsPanel)
