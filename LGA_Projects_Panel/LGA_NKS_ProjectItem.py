"""
Widget personalizado para mostrar proyectos y secuencias en el panel de proyectos LGA.
"""

from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt

# Importar funciones necesarias del módulo principal
# Estas serán importadas desde el archivo principal cuando se importe este módulo
get_project_colors = None
debug_print = None
switch_to_sequence = None


def initialize_dependencies(colors_func, debug_func, switch_func):
    """Inicializar las dependencias externas necesarias para ProjectItem"""
    global get_project_colors, debug_print, switch_to_sequence
    get_project_colors = colors_func
    debug_print = debug_func
    switch_to_sequence = switch_func


class ProjectItem(QtWidgets.QWidget):
    """Widget personalizado para mostrar un proyecto y sus secuencias"""

    def __init__(self, project_info, panel=None, parent=None):
        super(ProjectItem, self).__init__(parent)
        self.project_info = project_info
        self.panel = panel  # Referencia al ProjectsPanel para el event filter
        self.is_open = False
        self.sequences = []
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Contenedor horizontal para el proyecto (para evitar expansión horizontal)
        project_container = QtWidgets.QWidget()
        project_layout = QtWidgets.QHBoxLayout(project_container)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.setSpacing(0)

        # Nombre del proyecto (clickable)
        self.project_label = QtWidgets.QLabel()
        self.project_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.project_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.project_label.setWordWrap(False)  # No word wrap para mantener en una línea
        self.project_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # Asegurar que el texto no se trunque
        self.project_label.setTextFormat(QtCore.Qt.PlainText)
        # El event filter se instalará desde ProjectsPanel
        project_layout.addWidget(self.project_label)

        # Spacer horizontal para empujar el label a la izquierda
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        project_layout.addItem(spacer)

        layout.addWidget(project_container)

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

        # Obtener colores para este proyecto
        debug_print(f"🎨 Aplicando colores para proyecto: '{project_name}' (desde nombre_base: '{nombre}')")
        base_color, hover_color = get_project_colors(project_name)
        debug_print(f"🎨 Colores aplicados - Base: {base_color}, Hover: {hover_color}")

        # Agregar emoji según estado
        if self.is_open and self.sequences:
            display_text = f"▼ {formatted_text}"
            self.project_label.setStyleSheet(f"font-size: 13px; color: {base_color};")
            # Guardar colores para el event filter
            self.project_label.setProperty("base_color", base_color)
            self.project_label.setProperty("hover_color", hover_color)
            self.project_label.setProperty("is_project_label", True)  # Para distinguir del resto
            self.show_sequences()
        else:
            display_text = f"▶ {formatted_text}"
            self.project_label.setStyleSheet(f"font-size: 13px; color: {base_color};")
            # Guardar colores para el event filter
            self.project_label.setProperty("base_color", base_color)
            self.project_label.setProperty("hover_color", hover_color)
            self.project_label.setProperty("is_project_label", True)  # Para distinguir del resto
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

        # Establecer tamaño mínimo basado en el texto (más conservador)
        min_width = text_width + 20  # +20 para padding
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

        # Obtener colores para las secuencias (mismo que el proyecto padre)
        project_name = self.project_info.get("nombre_base", "")
        if "_SUP" in project_name:
            project_name = project_name.split("_SUP")[0]
        base_color, hover_color = get_project_colors(project_name)

        for seq_name in sorted(self.sequences):
            # Contenedor horizontal para la secuencia
            seq_container = QtWidgets.QWidget()
            seq_layout = QtWidgets.QHBoxLayout(seq_container)
            seq_layout.setContentsMargins(0, 0, 0, 0)
            seq_layout.setSpacing(0)

            seq_label = QtWidgets.QLabel(f"> {seq_name}")
            seq_label.setStyleSheet(f"color: {base_color};")
            seq_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            seq_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            seq_label.adjustSize()  # Ajustar tamaño al contenido del texto
            # Guardar colores para el event filter
            seq_label.setProperty("base_color", base_color)
            seq_label.setProperty("hover_color", hover_color)

            # Instalar event filter para hover (si hay panel disponible)
            if self.panel:
                seq_label.installEventFilter(self.panel)

            seq_obj = sequences_dict.get(seq_name)
            seq_label.mousePressEvent = (
                lambda e, name=seq_name, so=seq_obj, po=self.project_info.get("proyecto_obj"): self.on_sequence_click(name, so, po)
            )

            seq_layout.addWidget(seq_label)

            # Spacer horizontal para empujar el label a la izquierda
            seq_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            seq_layout.addItem(seq_spacer)

            self.sequences_layout.addWidget(seq_container)

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
