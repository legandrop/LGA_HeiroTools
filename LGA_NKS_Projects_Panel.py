"""
Panel de Proyectos LGA integrado para Hiero con recarga inteligente.
- Escanea proyectos en T:\, muestra versiones y secuencias abiertas.
- Permite abrir proyectos y secuencias (cross-project) sin perder ajustes de viewer.
- Incluye botón de reimport/redock para aplicar cambios al vuelo.

VERSION: 2.2 - Display formateado: PROYECTO (vXXX), emojis ▼▶, sin _SUP_
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

# Lista global para almacenar mensajes de debug en hilos separados
debug_messages = []

# Variable global para controlar si se debe crear panel automáticamente
# Se usa en smart reload para evitar creación duplicada
AUTO_CREATE_PANEL = True


def debug_print(*message):
    """Imprime un mensaje de debug si la variable DEBUG es True."""
    if DEBUG:
        # En hilos separados, almacenar en lista para imprimir al final
        # En hilo principal, imprimir inmediatamente
        if len(debug_messages) < 200:  # Máximo 200 mensajes para evitar memory issues
            debug_messages.append(" ".join(str(m) for m in message))


def print_debug_messages():
    """Imprime todos los mensajes de debug almacenados y limpia la lista."""
    if DEBUG and debug_messages:
        print("\n".join(debug_messages))
        debug_messages.clear()


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
    debug_output = QtCore.Signal()  # Señal para imprimir logs al final


class ScanWorker(QtCore.QRunnable):
    """Worker para escanear proyectos en background"""

    def __init__(self, base_path="T:\\"):
        super(ScanWorker, self).__init__()
        self.base_path = base_path
        self.signals = WorkerSignals()

    def run(self):
        """Ejecuta el escaneo en hilo secundario"""
        debug_print(f"⚙️ ScanWorker.run() ejecutándose en hilo secundario...")
        debug_print(f"   📍 Base path: {self.base_path}")
        try:
            debug_print("🔍 Ejecutando scan_projects_on_disk()...")
            proyectos_encontrados = scan_projects_on_disk(self.base_path)
            debug_print("📂 Ejecutando get_open_projects_info()...")
            proyectos_abiertos = get_open_projects_info()
            debug_print("📡 Emitiendo señal scan_finished...")
            self.signals.scan_finished.emit(proyectos_encontrados, proyectos_abiertos)
            debug_print("✅ ScanWorker completado exitosamente")
            # Emitir señal para imprimir logs al final
            self.signals.debug_output.emit()
        except Exception as e:
            debug_print(f"💥 ERROR en ScanWorker: {str(e)}")
            import traceback
            debug_print(f"Traceback: {traceback.format_exc()}")
            self.signals.error.emit(f"Error durante escaneo: {str(e)}")
            # Emitir señal para imprimir logs al final incluso en error
            self.signals.debug_output.emit()


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
        self.project_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.project_label.setWordWrap(False)  # No word wrap para mantener en una línea
        self.project_label.setMinimumWidth(300)  # Ancho mínimo mayor
        self.project_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        # Asegurar que el texto no se trunque
        self.project_label.setTextFormat(QtCore.Qt.PlainText)
        # El event filter se instalará desde ProjectsPanel
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

        # Extraer nombre del proyecto (antes de _SUP_)
        project_name = nombre
        if "_SUP" in nombre:
            project_name = nombre.split("_SUP")[0]

        # Limpiar versión (quitar 'v' inicial)
        clean_version = version.lstrip('v')

        # Crear texto formateado: "NOMBRE (vXXX)"
        formatted_text = f"{project_name} (v{clean_version})"

        # Agregar emoji según estado
        if self.is_open and self.sequences:
            display_text = f"▼ {formatted_text}"
            self.project_label.setStyleSheet("font-size: 13px; color: #cccccc;")
            self.show_sequences()
        else:
            display_text = f"▶ {formatted_text}"
            self.project_label.setStyleSheet("font-size: 13px; color: #cccccc;")
            self.sequences_widget.hide()

        # Debug: mostrar exactamente qué texto se está configurando
        debug_print(f"UI: Configurando texto para {project_name}: '{display_text}' (longitud: {len(display_text)})")

        self.project_label.setText(display_text)

        # Forzar actualización del tamaño del label para asegurar que muestre todo el texto
        self.project_label.adjustSize()

        # Calcular el tamaño necesario para el texto completo
        font_metrics = self.project_label.fontMetrics()
        text_width = font_metrics.width(display_text)
        text_height = font_metrics.height()

        # Establecer tamaño mínimo basado en el texto
        min_width = max(300, text_width + 20)  # +20 para padding
        self.project_label.setMinimumWidth(min_width)

        # Forzar actualización del layout
        self.project_label.update()
        self.update()

        # Verificar que el texto se aplicó correctamente
        actual_text = self.project_label.text()
        debug_print(f"UI: Texto aplicado al QLabel: '{actual_text}' (longitud: {len(actual_text)})")
        if actual_text != display_text:
            debug_print(f"ERROR: Texto aplicado difiere del esperado!")
            # Debug detallado carácter por carácter
            debug_print(f"Esperado: {[c for c in display_text]}")
            debug_print(f"Actual:   {[c for c in actual_text]}")

        # Información adicional de debug
        size = self.project_label.size()
        debug_print(f"UI: QLabel size: {size.width()}x{size.height()}, texto requiere: {text_width}x{text_height}")

        # Información adicional de debug
        size = self.project_label.size()
        min_size = self.project_label.minimumSize()
        debug_print(f"UI: QLabel size: {size.width()}x{size.height()}, min_size: {min_size.width()}x{min_size.height()}")

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
            seq_label = QtWidgets.QLabel(f"> {seq_name}")
            seq_label.setStyleSheet("color: #77bdd4;")
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


        # Barra de herramientas
        toolbar_layout = QtWidgets.QHBoxLayout()

        # Configurar iconos para el botón refresh
        refresh_icon_path = os.path.join(os.path.dirname(__file__), "LGA_Projects_Panel", "refresh.svg")
        refresh_hover_icon_path = os.path.join(os.path.dirname(__file__), "LGA_Projects_Panel", "refresh_white.svg")

        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_button.setToolTip("Re-escanear proyectos")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
                background: transparent;
            }
        """)

        # Cargar iconos SVG si existen
        if os.path.exists(refresh_icon_path) and os.path.exists(refresh_hover_icon_path):
            self.refresh_icon_normal = QtGui.QIcon(refresh_icon_path)
            self.refresh_icon_hover = QtGui.QIcon(refresh_hover_icon_path)
            self.refresh_button.setIcon(self.refresh_icon_normal)
            self.refresh_button.setIconSize(QtCore.QSize(20, 20))  # Tamaño aproximado al botón original

            # Instalar event filter para manejar hover
            self.refresh_button.installEventFilter(self)
        else:
            # Fallback si no se encuentran los iconos
            self.refresh_button.setText("🔄 Refresh")

        toolbar_layout.addWidget(self.refresh_button)

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

    def eventFilter(self, obj, event):
        """Manejar eventos de hover para botones y labels"""
        # Manejar hover del botón refresh
        if obj == self.refresh_button:
            if event.type() == QtCore.QEvent.Enter:
                if hasattr(self, 'refresh_icon_hover'):
                    self.refresh_button.setIcon(self.refresh_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                if hasattr(self, 'refresh_icon_normal'):
                    self.refresh_button.setIcon(self.refresh_icon_normal)

        # Manejar hover de los project labels
        elif hasattr(obj, 'setStyleSheet') and obj != self.refresh_button:
            # Verificar si es un project label (tiene cursor de pointing hand)
            if obj.cursor().shape() == QtCore.Qt.PointingHandCursor:
                if event.type() == QtCore.QEvent.Enter:
                    # Cambiar a color hover (#ffffff)
                    current_style = obj.styleSheet()
                    if 'color: #cccccc' in current_style:
                        new_style = current_style.replace('color: #cccccc', 'color: #ffffff')
                        obj.setStyleSheet(new_style)
                elif event.type() == QtCore.QEvent.Leave:
                    # Volver a color normal (#cccccc)
                    current_style = obj.styleSheet()
                    if 'color: #ffffff' in current_style:
                        new_style = current_style.replace('color: #ffffff', 'color: #cccccc')
                        obj.setStyleSheet(new_style)

        return super().eventFilter(obj, event)

    def start_scan(self):
        debug_print("🚀 Iniciando escaneo desde botón refresh...")
        self.refresh_button.setEnabled(False)

        debug_print("👷 Creando ScanWorker...")
        worker = ScanWorker()
        worker.signals.scan_finished.connect(self.on_scan_finished)
        worker.signals.error.connect(self.on_scan_error)
        worker.signals.debug_output.connect(lambda: print_debug_messages())
        debug_print("🏃 Ejecutando ScanWorker en thread pool...")
        QtCore.QThreadPool.globalInstance().start(worker)
        debug_print("✅ ScanWorker enviado a thread pool")

    def on_scan_finished(self, proyectos_encontrados, proyectos_abiertos):
        debug_print("🎉 Escaneo completado exitosamente!")
        debug_print(f"   📊 Proyectos encontrados: {len(proyectos_encontrados)}")
        debug_print(f"   📂 Grupos de proyectos abiertos: {len(proyectos_abiertos)}")

        self.proyectos_encontrados = proyectos_encontrados
        self.proyectos_abiertos = proyectos_abiertos

        self.refresh_button.setEnabled(True)

        debug_print("🔄 Llamando a update_projects_display...")
        self.update_projects_display()

    def on_scan_error(self, error_msg):
        debug_print(f"❌ ERROR durante el escaneo: {error_msg}")
        self.refresh_button.setEnabled(True)
        QtWidgets.QMessageBox.warning(self, "Error de Escaneo", error_msg)

    def update_projects_display(self):
        debug_print("🔄 Actualizando display de proyectos...")
        debug_print(f"   📊 Proyectos encontrados: {len(self.proyectos_encontrados)}")
        debug_print(f"   📂 Proyectos abiertos: {len(self.proyectos_abiertos)} grupos")

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

            item = ProjectItem(proyecto_info)
            item.project_label.mousePressEvent = lambda e, p=proyecto_info: self.on_project_click(p)
            # Instalar event filter para hover del project label
            item.project_label.installEventFilter(self)

            is_open = is_project_open(ruta_hrox, self.proyectos_abiertos)
            debug_print(f"      Estado abierto: {is_open}")

            if is_open:
                debug_print("      Este proyecto aparecera como ABIERTO en la UI")

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

        debug_print(f"✅ UI actualizada completamente!")
        debug_print(f"   📊 Total items en UI: {len(self.project_items)}")
        debug_print(f"   📂 Proyectos marcados como abiertos: {proyectos_abiertos_count}")
        debug_print(f"   📋 Etiqueta inferior: '{self.info_label.text()}'")

        # Mostrar resumen detallado de lo que se muestra en UI
        debug_print("RESUMEN DE PROYECTOS EN UI:")
        for nombre_base, item in sorted(self.project_items.items()):
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

    def on_project_click(self, proyecto_info):
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
