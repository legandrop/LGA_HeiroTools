"""
Ventana de Testing - Panel de Proyectos LGA
===========================================

Esta es una ventana independiente (QMainWindow) para testing de la funcionalidad
completa del panel de proyectos antes de convertirla en panel integrado de Hiero.

Ejecución directa: exec(open("LGA_Projects_Panel_Window.py").read())

IMPORTANTE: Usa LGA_QtAdapter_HieroTools para compatibilidad Nuke 15/16
"""

import hiero.core
import hiero.ui
import os
import sys
from pathlib import Path

# Importar compatibilidad Qt para Hiero Panels
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt

# Reasignar clases para compatibilidad con código existente
QRunnable = QtCore.QRunnable
QThreadPool = QtCore.QThreadPool
Signal = QtCore.Signal
QObject = QtCore.QObject

# Variable global para mantener referencia a la ventana (como en los ejemplos que funcionan)
_projects_panel_window = None

# Buscar y añadir la ruta del módulo de escaneo al sys.path
projects_panel_path = None

# Método 1: Buscar usando __file__ (este script está en LGA_Projects_Panel/)
if '__file__' in globals() and __file__:
    try:
        script_dir = Path(__file__).resolve().parent
        # El script está en: LGA_Projects_Panel/
        # Necesitamos esta misma carpeta para LGA_Projects_Panel_ScanProjects.py
        if (script_dir / "LGA_Projects_Panel_ScanProjects.py").exists():
            projects_panel_path = script_dir
    except Exception:
        pass

# Método 2: Buscar en sys.path
if projects_panel_path is None:
    for path_str in sys.path:
        try:
            path = Path(path_str)
            test_file = path / "LGA_Projects_Panel_ScanProjects.py"
            if test_file.exists():
                projects_panel_path = path
                break
            # Buscar en subcarpetas
            if path.exists():
                subdirs = [d for d in path.iterdir() if d.is_dir() and d.name.startswith("LGA_")]
                for subdir in subdirs:
                    test_file = subdir / "LGA_Projects_Panel_ScanProjects.py"
                    if test_file.exists():
                        projects_panel_path = subdir
                        break
                if projects_panel_path:
                    break
        except Exception:
            continue

# Método 3: Buscar en rutas estándar
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
        get_project_sequences
    )
except ImportError as e:
    raise ImportError(f"No se pudo importar el módulo LGA_Projects_Panel_ScanProjects: {e}. "
                     f"Verificado en: {projects_panel_path}")

# Importar función de cambio de secuencia
try:
    from LGA_Projects_Panel_SwitchSequence import switch_to_sequence
except ImportError as e:
    raise ImportError(f"No se pudo importar el módulo LGA_Projects_Panel_SwitchSequence: {e}")


class WorkerSignals(QObject):
    """Señales para comunicar resultados del worker de escaneo"""
    scan_finished = Signal(list, dict)  # proyectos_encontrados, proyectos_abiertos
    error = Signal(str)


class ScanWorker(QRunnable):
    """Worker para escanear proyectos en background"""

    def __init__(self, base_path="T:\\"):
        super(ScanWorker, self).__init__()
        self.base_path = base_path
        self.signals = WorkerSignals()

    def run(self):
        """Ejecuta el escaneo en hilo secundario"""
        try:
            # Escanear proyectos en disco
            proyectos_encontrados = scan_projects_on_disk(self.base_path)

            # Obtener información de proyectos abiertos
            proyectos_abiertos = get_open_projects_info()

            # Emitir resultados
            self.signals.scan_finished.emit(proyectos_encontrados, proyectos_abiertos)

        except Exception as e:
            self.signals.error.emit(f"Error durante escaneo: {str(e)}")


class ProjectItem(QtWidgets.QWidget):
    """Widget personalizado para mostrar un proyecto en la lista"""

    def __init__(self, project_info, parent=None):
        super(ProjectItem, self).__init__(parent)
        self.project_info = project_info
        self.is_open = False
        self.sequences = []

        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz del item"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Nombre del proyecto (clickable)
        self.project_label = QtWidgets.QLabel()
        self.project_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.project_label.setStyleSheet("font-weight: bold; color: #2E86C1;")
        self.project_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        layout.addWidget(self.project_label)

        # Contenedor para secuencias (inicialmente oculto)
        self.sequences_widget = QtWidgets.QWidget()
        self.sequences_layout = QtWidgets.QVBoxLayout(self.sequences_widget)
        self.sequences_layout.setContentsMargins(20, 0, 0, 0)  # Indentación
        self.sequences_widget.hide()
        layout.addWidget(self.sequences_widget)

        self.update_display()

    def update_display(self):
        """Actualizar visualización del proyecto"""
        nombre = self.project_info.get("nombre_base", "")
        version = self.project_info.get("version", "")

        if self.is_open and self.sequences:
            # Proyecto abierto con secuencias
            self.project_label.setText(f"📂 {nombre}_{version} (Abierto)")
            self.project_label.setStyleSheet("font-weight: bold; color: #28B463;")

            # Mostrar secuencias
            self.show_sequences()
        else:
            # Proyecto cerrado
            self.project_label.setText(f"📁 {nombre}_{version}")
            self.project_label.setStyleSheet("font-weight: bold; color: #2E86C1;")

            # Ocultar secuencias si estaban visibles
            self.sequences_widget.hide()

    def show_sequences(self):
        """Mostrar las secuencias del proyecto"""
        # Limpiar secuencias anteriores
        for i in reversed(range(self.sequences_layout.count())):
            self.sequences_layout.itemAt(i).widget().setParent(None)

        # Obtener objetos Sequence del proyecto (no solo nombres)
        proyecto_obj = self.project_info.get("proyecto_obj")
        sequences_dict = {}  # nombre -> objeto Sequence

        if proyecto_obj:
            try:
                all_sequences = proyecto_obj.sequences()
                for seq in all_sequences:
                    try:
                        seq_name = seq.name()
                        sequences_dict[seq_name] = seq
                    except Exception:
                        continue
            except Exception:
                pass

        # Agregar secuencias (usar objetos Sequence si están disponibles)
        for seq_name in self.sequences:
            seq_label = QtWidgets.QLabel(f"▶ {seq_name}")
            # Color claro que contrasta bien con fondo oscuro #323232
            seq_label.setStyleSheet("color: #66BB6A;")  # Verde claro legible
            seq_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            seq_label.setProperty("sequence_name", seq_name)
            
            # Guardar objeto Sequence si está disponible
            if seq_name in sequences_dict:
                seq_label.setProperty("sequence_obj", sequences_dict[seq_name])
            
            seq_label.mousePressEvent = lambda e, name=seq_name, seq_obj=sequences_dict.get(seq_name): self.on_sequence_click(name, seq_obj)
            self.sequences_layout.addWidget(seq_label)

        self.sequences_widget.show()

    def on_sequence_click(self, sequence_name, sequence_obj=None):
        """Manejador de click en secuencia"""
        # Usar la función avanzada de cambio de secuencia (v3 híbrida)
        # Si tenemos el objeto Sequence, pasarlo directamente (funciona cross-project)
        try:
            if sequence_obj:
                # Pasar objeto Sequence directamente - funciona incluso cross-project
                success = switch_to_sequence(sequence_name, sequence_obj=sequence_obj)
            else:
                # Fallback: buscar por nombre (comportamiento anterior)
                success = switch_to_sequence(sequence_name)
            
            if success:
                print(f"✅ Secuencia '{sequence_name}' cambiada exitosamente")
                # Nota: La UI se actualiza automáticamente por el cambio de secuencia
                # Si necesitas refresh manual, usa el botón "Refresh"
            else:
                print(f"❌ Error cambiando a secuencia '{sequence_name}'")
        except Exception as e:
            print(f"❌ Error en cambio de secuencia '{sequence_name}': {e}")
            import traceback
            print(traceback.format_exc())

    def set_open_state(self, is_open, sequences=None, proyecto_obj=None):
        """Actualizar estado de apertura del proyecto"""
        self.is_open = is_open
        if sequences:
            self.sequences = sequences
        if proyecto_obj:
            self.project_info["proyecto_obj"] = proyecto_obj
        self.update_display()


class ProjectPanelWindow(QtWidgets.QWidget):
    """Ventana principal de testing del panel de proyectos"""

    def __init__(self):
        super(ProjectPanelWindow, self).__init__()

        # Configurar atributo para que no se destruya al cerrar (como en LGA_NKS_mediaMissingFrames.py)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Datos del estado
        self.proyectos_encontrados = []
        self.proyectos_abiertos = {}
        self.project_items = {}  # nombre_base -> ProjectItem

        self.setup_ui()
        self.setup_connections()

        # Escaneo inicial automático
        self.start_scan()

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        self.setWindowTitle("Project Panel - Testing")
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumWidth(350)

        # Layout principal para QWidget
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Título
        title_label = QtWidgets.QLabel("Panel de Proyectos LGA")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
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
        self.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.info_label)

    def setup_connections(self):
        """Configurar conexiones de señales"""
        self.refresh_button.clicked.connect(self.start_scan)

    def start_scan(self):
        """Iniciar escaneo de proyectos en background"""
        self.status_label.setText("Escaneando...")
        self.status_label.setStyleSheet("color: #F39C12;")
        self.refresh_button.setEnabled(False)

        # Crear worker
        worker = ScanWorker()

        # Conectar señales
        worker.signals.scan_finished.connect(self.on_scan_finished)
        worker.signals.error.connect(self.on_scan_error)

        # Ejecutar en hilo separado
        QThreadPool.globalInstance().start(worker)

    def on_scan_finished(self, proyectos_encontrados, proyectos_abiertos):
        """Manejador de finalización de escaneo"""
        self.proyectos_encontrados = proyectos_encontrados
        self.proyectos_abiertos = proyectos_abiertos

        self.status_label.setText("Listo")
        self.status_label.setStyleSheet("color: #28B463;")
        self.refresh_button.setEnabled(True)

        self.update_projects_display()

    def on_scan_error(self, error_msg):
        """Manejador de error de escaneo"""
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #E74C3C;")
        self.refresh_button.setEnabled(True)

        QtWidgets.QMessageBox.warning(self, "Error de Escaneo", error_msg)

    def update_projects_display(self):
        """Actualizar la visualización de proyectos"""
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

        # Crear items para cada proyecto
        for proyecto_info in sorted(self.proyectos_encontrados, key=lambda x: x.get("nombre_base", "")):
            item = ProjectItem(proyecto_info)
            item.project_label.mousePressEvent = lambda e, p=proyecto_info: self.on_project_click(p)

            # Verificar si está abierto
            ruta_hrox = proyecto_info.get("ruta_hrox", "")
            is_open = is_project_open(ruta_hrox, self.proyectos_abiertos)

            if is_open:
                # Obtener secuencias del proyecto abierto
                nombre_base = proyecto_info.get("nombre_base", "")
                if nombre_base in self.proyectos_abiertos:
                    proyecto_abierto = self.proyectos_abiertos[nombre_base][0]  # Tomar el primero
                    proyecto_obj = proyecto_abierto["proyecto"]
                    sequences = get_project_sequences(proyecto_obj)

                    item.set_open_state(True, sequences, proyecto_obj)

            self.project_items[proyecto_info.get("nombre_base", "")] = item
            self.projects_layout.addWidget(item)

        # Actualizar información
        total_proyectos = len(self.proyectos_encontrados)
        proyectos_abiertos_count = sum(1 for item in self.project_items.values() if item.is_open)

        self.info_label.setText(f"{total_proyectos} proyectos encontrados, {proyectos_abiertos_count} abiertos")

    def on_project_click(self, proyecto_info):
        """Manejador de click en proyecto"""
        ruta_hrox = proyecto_info.get("ruta_hrox", "")
        nombre_base = proyecto_info.get("nombre_base", "")

        try:
            # Abrir proyecto en Hiero
            proyecto = hiero.core.openProject(ruta_hrox)
            print(f"Proyecto abierto: {proyecto.name()}")

            # Actualizar vista después de abrir
            self.start_scan()  # Re-escanear para actualizar estado

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error al abrir proyecto",
                f"No se pudo abrir el proyecto {nombre_base}:\n{str(e)}"
            )

    def closeEvent(self, event):
        """Manejador de cierre de ventana"""
        # Aceptar el evento de cierre
        event.accept()


def main():
    """Función principal para ejecutar la ventana de testing"""
    global _projects_panel_window

    try:
        # Crear y mostrar ventana (como en LGA_NKS_mediaMissingFrames.py)
        _projects_panel_window = ProjectPanelWindow()
        _projects_panel_window.show()
        return _projects_panel_window
    except Exception as e:
        print(f"Error mostrando ventana de proyectos: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    main()
