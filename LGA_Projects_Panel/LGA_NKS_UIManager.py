"""
Gestor de interfaz de usuario para el panel de proyectos LGA.
"""

import os
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt

# Importar variable global
# Esta será importada desde el archivo principal cuando se importe este módulo
REIMPORT_BUTTON = None


def initialize_ui_dependencies(reimport_flag):
    """Inicializar las dependencias globales necesarias para el UI manager"""
    global REIMPORT_BUTTON
    REIMPORT_BUTTON = reimport_flag


class UIManager:
    """Clase para manejar la configuración y gestión de la interfaz de usuario"""

    @staticmethod
    def setup_ui(panel):
        """Configurar la interfaz de usuario del panel"""
        # Layout principal horizontal para dividir en dos columnas
        panel.main_layout = QtWidgets.QHBoxLayout(panel)

        # Columna izquierda: proyectos y settings (stack)
        left_column = QtWidgets.QVBoxLayout()

        panel.content_stack = QtWidgets.QStackedWidget()

        # Contenedor de proyectos
        panel.projects_container = QtWidgets.QWidget()
        projects_container_layout = QtWidgets.QVBoxLayout(panel.projects_container)
        projects_container_layout.setContentsMargins(0, 0, 0, 0)

        # Área de scroll para la lista de proyectos
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        panel.projects_widget = QtWidgets.QWidget()
        panel.projects_layout = QtWidgets.QVBoxLayout(panel.projects_widget)
        panel.projects_layout.setAlignment(QtCore.Qt.AlignTop)

        scroll_area.setWidget(panel.projects_widget)
        projects_container_layout.addWidget(scroll_area)

        # Información de estado
        panel.info_label = QtWidgets.QLabel("")
        panel.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 6px;")
        panel.info_label.setAlignment(QtCore.Qt.AlignCenter)
        projects_container_layout.addWidget(panel.info_label)

        panel.content_stack.addWidget(panel.projects_container)
        left_column.addWidget(panel.content_stack)

        # Añadir columna izquierda al layout principal (con stretch para que tome el espacio disponible)
        panel.main_layout.addLayout(left_column, 1)  # stretch factor 1

        # Columna derecha: botones
        right_column = QtWidgets.QVBoxLayout()
        right_column.setAlignment(QtCore.Qt.AlignTop)
        right_column.setSpacing(2)  # Espacio pequeño entre botones

        # Configurar iconos para el botón refresh
        refresh_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "refresh.svg")
        refresh_hover_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "refresh_white.svg")

        panel.refresh_button = QtWidgets.QPushButton()
        panel.refresh_button.setToolTip("Re-escanear proyectos")
        panel.refresh_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
                background: transparent;
            }
        """)

        # Cargar iconos SVG si existen
        if os.path.exists(refresh_icon_path) and os.path.exists(refresh_hover_icon_path):
            panel.refresh_icon_normal = QtGui.QIcon(refresh_icon_path)
            panel.refresh_icon_hover = QtGui.QIcon(refresh_hover_icon_path)
            panel.refresh_button.setIcon(panel.refresh_icon_normal)
            panel.refresh_button.setIconSize(QtCore.QSize(20, 20))  # Tamaño aproximado al botón original

            # Instalar event filter para manejar hover
            panel.refresh_button.installEventFilter(panel)
        else:
            # Fallback si no se encuentran los iconos
            panel.refresh_button.setText("🔄 Refresh")

        # Añadir botón refresh a la columna derecha
        right_column.addWidget(panel.refresh_button)

        # Botón Settings
        settings_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "settings.svg")
        settings_hover_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "settings_white.svg")

        panel.settings_button = QtWidgets.QPushButton()
        panel.settings_button.setToolTip("Settings")
        panel.settings_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
                background: transparent;
            }
        """)

        if os.path.exists(settings_icon_path) and os.path.exists(settings_hover_icon_path):
            panel.settings_icon_normal = QtGui.QIcon(settings_icon_path)
            panel.settings_icon_hover = QtGui.QIcon(settings_hover_icon_path)
            panel.settings_button.setIcon(panel.settings_icon_normal)
            panel.settings_button.setIconSize(QtCore.QSize(20, 20))
            panel.settings_button.installEventFilter(panel)
        else:
            panel.settings_button.setText("⚙ Settings")

        right_column.addWidget(panel.settings_button)

        # Configurar iconos para el botón reimport
        reimport_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "recargar_script.svg")
        reimport_hover_icon_path = os.path.join(os.path.dirname(__file__), "..", "LGA_Projects_Panel", "recargar_script_white.svg")

        # Botón de reimport con iconos SVG (solo si la flag está activada)
        if REIMPORT_BUTTON:
            panel.reimport_button = QtWidgets.QPushButton()
            panel.reimport_button.setToolTip("Recarga y redockea el panel con el script externo")
            panel.reimport_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 5px;
                    background: transparent;
                }
            """)

            # Cargar iconos SVG si existen
            if os.path.exists(reimport_icon_path) and os.path.exists(reimport_hover_icon_path):
                panel.reimport_icon_normal = QtGui.QIcon(reimport_icon_path)
                panel.reimport_icon_hover = QtGui.QIcon(reimport_hover_icon_path)
                panel.reimport_button.setIcon(panel.reimport_icon_normal)
                panel.reimport_button.setIconSize(QtCore.QSize(20, 20))  # Tamaño aproximado al botón original

                # Instalar event filter para manejar hover
                panel.reimport_button.installEventFilter(panel)
            else:
                # Fallback si no se encuentran los iconos
                panel.reimport_button.setText("♻")

            right_column.addWidget(panel.reimport_button)

        # Añadir columna derecha al layout principal (sin stretch para mantener tamaño pequeño)
        panel.main_layout.addLayout(right_column, 0)  # stretch factor 0

    @staticmethod
    def setup_connections(panel):
        """Configurar las conexiones de señales del panel"""
        panel.refresh_button.clicked.connect(panel.start_scan)
        if hasattr(panel, 'settings_button'):
            panel.settings_button.clicked.connect(panel.show_settings_view)
        if REIMPORT_BUTTON and hasattr(panel, 'reimport_button'):
            panel.reimport_button.clicked.connect(panel.reimport_panel)

    @staticmethod
    def eventFilter(panel, obj, event):
        """Manejar eventos de hover para botones y labels"""
        # Manejar hover del botón refresh
        if obj == panel.refresh_button:
            if event.type() == QtCore.QEvent.Enter:
                if hasattr(panel, 'refresh_icon_hover'):
                    panel.refresh_button.setIcon(panel.refresh_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                if hasattr(panel, 'refresh_icon_normal'):
                    panel.refresh_button.setIcon(panel.refresh_icon_normal)

        # Hover botón settings
        elif obj == getattr(panel, "settings_button", None):
            if event.type() == QtCore.QEvent.Enter:
                if hasattr(panel, 'settings_icon_hover'):
                    panel.settings_button.setIcon(panel.settings_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                if hasattr(panel, 'settings_icon_normal'):
                    panel.settings_button.setIcon(panel.settings_icon_normal)

        # Manejar hover del botón reimport
        elif obj == getattr(panel, "reimport_button", None):
            if event.type() == QtCore.QEvent.Enter:
                if hasattr(panel, 'reimport_icon_hover'):
                    panel.reimport_button.setIcon(panel.reimport_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                if hasattr(panel, 'reimport_icon_normal'):
                    panel.reimport_button.setIcon(panel.reimport_icon_normal)

        # Manejar hover del botón update (buscar en todos los project items)
        elif hasattr(obj, 'toolTip') and obj.toolTip() == "Actualizar a versión más nueva":
            # Es un botón de update
            if event.type() == QtCore.QEvent.Enter:
                # Cambiar a ícono hover
                if hasattr(obj, 'update_icon_hover'):
                    obj.setIcon(obj.update_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                # Cambiar a ícono normal
                if hasattr(obj, 'update_icon_normal'):
                    obj.setIcon(obj.update_icon_normal)

        # Manejar hover de los project labels y sequence labels
        elif hasattr(obj, 'setStyleSheet') and obj != panel.refresh_button:
            # Verificar si es un label con cursor de pointing hand
            if obj.cursor().shape() == QtCore.Qt.PointingHandCursor:
                if event.type() == QtCore.QEvent.Enter:
                    # Cambiar a color hover usando las propiedades guardadas
                    hover_color = obj.property("hover_color")
                    if hover_color:
                        if obj.property("is_project_label"):
                            # Project label: mantener font-size
                            obj.setStyleSheet(f"font-size: 13px; color: {hover_color};")
                        else:
                            # Sequence label: solo color
                            obj.setStyleSheet(f"color: {hover_color};")
                elif event.type() == QtCore.QEvent.Leave:
                    # Volver a color base usando las propiedades guardadas
                    base_color = obj.property("base_color")
                    if base_color:
                        if obj.property("is_project_label"):
                            # Project label: mantener font-size
                            obj.setStyleSheet(f"font-size: 13px; color: {base_color};")
                        else:
                            # Sequence label: solo color
                            obj.setStyleSheet(f"color: {base_color};")

        return super(panel.__class__, panel).eventFilter(obj, event)
