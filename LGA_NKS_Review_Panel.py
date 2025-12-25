"""
_________________________________________

  LGA_ReviewPanel v2.76 | Lega
  Tools panel for Hiero / Nuke Studio

  v2.76: Actualizado para usar estilos dinámicos con bordes y hover para todos los botones
         Agregado tooltip dinámico para todos los botones
         Optimizado espaciado del layout y dimensiones de botones para mejor UX
_________________________________________

"""

import hiero.ui
import hiero.core
import os
import re
import subprocess
import socket
import importlib.util
import sys
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

# Importar funciones de utilidad de estilos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover,
    create_tooltip_stylesheet
)


# Clase de botón personalizada que maneja el Shift+Click
class CustomButton(QtWidgets.QPushButton):
    def __init__(self, text):
        super(CustomButton, self).__init__(text)
        self._custom_click_handler = None
        self._shift_click_handler = None

    def setCustomClickHandler(self, handler):
        self._custom_click_handler = handler

    def setShiftClickHandler(self, handler):
        self._shift_click_handler = handler

    def mousePressEvent(self, event):
        if self._custom_click_handler and self._shift_click_handler:
            modifiers = event.modifiers()
            if modifiers & QtCore.Qt.ShiftModifier:
                self._shift_click_handler()
            else:
                self._custom_click_handler()
        else:
            super(CustomButton, self).mousePressEvent(event)

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


class ReviewPanel(QtWidgets.QWidget):
    def __init__(self):
        super(ReviewPanel, self).__init__()

        self.setObjectName("com.lega.RevtoolPanel")
        self.setWindowTitle("Review")

        self.layout = QtWidgets.QGridLayout(self)  # Usamos QGridLayout en lugar de QVBoxLayout
        self.layout.setSpacing(6)  # Reducir espacio entre botones
        self.setLayout(self.layout)

        # Crear botones y agregarlos al layout
        self.buttons = [
            ("ON Clips | OFF v00", self.execute_EnableOrDisableClips, "#0e1f3a", None, "Click: Activa todos los clips del timeline y desactiva los clips v00\nShift+Click: Solo en los clips seleccionados"),
            ("Self ReplaceClip", self.execute_SelfReplaceClip, "#0e1f3a", None, "Crea una nueva versión duplicada del clip seleccionado para que sea única (a veces arregla problemas"),
            ("ON OFF _comp_", self.execute_DisableEXR, "#0e1f3a", "Shift+D", "Shift+D\nHabilita/deshabilita el clip del track_comp_"),
            (
                "Difference Mode",
                self.execute_ToggleBlendModeForEXRTrack,
                "#283526",
                None,
                "Toggle del modo Difference del track _comp_",
            ),
            ("Compare Versions", self.execute_CompareVersions, "#273c24", None, "Crea un nuevo track 'COMPARE' con una versión anterior del clip seleccionado y pone al track en modo difference"),
            ("Compare OFF", self.execute_CompareVersionsOff, "#273c24", None, "Remueve el track 'COMPARE' y desactiva el modo Difference"),
            (
                "Reveal in &Explorer",
                self.execute_RevealInExplorer,
                "#321a1a",
                "Shift+E",
                "Shift+E\nRevela los archivos de los clips seleccionados en el explorer",
            ),
            ("Reveal NKS Project", self.execute_RevealNKSProject, "#321a1a", None, "Revela el proyecto NKS activo en el explorer"),
            (
                "Reveal NK Sc&ript",
                self.execute_RevealNKScript,
                "#321a1a",
                "Shift+R",
                "Shift+R\nAbre la carpeta que contiene al script de Nuke asociado al clip seleccionado",
            ),
            ("OpenInNuke&X", self.execute_OpenInNukeX, "#493800", "Shift+X", "Shift+X\nAbre en Nuke el script asociado al clip seleccionado"),
            (
                "Check Project Versions",
                self.execute_CheckProjectVersions,
                "#3a202e",
                None,
                "Chequea en el disco si hay versiones mayores de los proyectos abiertos en Nuke Studio",
            ),
        ]

        self.num_columns = 1  # Inicialmente una columna
        self.create_buttons()

        # Conectar la senal de cambio de tamano del widget al metodo correspondiente
        self.adjust_columns_on_resize()
        self.resizeEvent = self.adjust_columns_on_resize

        # Ejecutar el script de verificación de versiones de proyectos al iniciar el panel
        # Con un pequeño retraso para asegurar que Hiero haya cargado completamente
        QtCore.QTimer.singleShot(7000, self.execute_CheckProjectVersions)

    def create_buttons(self):
        for index, button_info in enumerate(self.buttons):
            name = button_info[0]
            handler = button_info[1]
            style = button_info[2]
            shortcut = button_info[3] if len(button_info) > 3 else None
            tooltip = button_info[4] if len(button_info) > 4 else None

            # Aplicar estilos dinámicos con bordes, hover y tooltips
            border_color = calculate_dynamic_border(style)
            hover_color = calculate_dynamic_hover(style)

            button_stylesheet = f"""
                QPushButton {{
                    background-color: {style};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    color: #d8d8d8;
                    padding: 0px 0px;
                    min-height: 18px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton:pressed {{
                    background-color: {style}aa;
                }}
            """

            # Agregar estilos de tooltip dinámicos si hay tooltip
            if tooltip:
                # Crear un selector único para este botón usando su objectName
                button_object_name = f"button_{index}"
                button_stylesheet += f"#{button_object_name} {{}} "  # Placeholder para el selector

                # Crear stylesheet de tooltip dinámico
                tooltip_stylesheet = create_tooltip_stylesheet(style)
                # Modificar el tooltip stylesheet para usar el selector del botón
                tooltip_stylesheet = tooltip_stylesheet.replace("QToolTip", f"#{button_object_name} QToolTip")

                # Combinar estilos del botón con estilos de tooltip
                button_stylesheet += tooltip_stylesheet

            # Usar CustomButton para el botón "ON Clips | OFF v00" para soportar Shift+Click
            if name == "ON Clips | OFF v00":
                button = CustomButton(name)
                button.setObjectName(f"button_{index}")  # Para tooltips dinámicos
                button.setStyleSheet(button_stylesheet)
                button.setCustomClickHandler(self.execute_EnableOrDisableClips_all_clips)
                button.setShiftClickHandler(handler)
                # Tooltip ya está definido en la tupla
                if tooltip:
                    button.setToolTip(tooltip)
            else:
                button = QtWidgets.QPushButton(name)
                button.setObjectName(f"button_{index}")  # Para tooltips dinámicos
                button.setStyleSheet(button_stylesheet)
                button.clicked.connect(handler)
                # Asignar tooltip si existe
                if tooltip:
                    button.setToolTip(tooltip)

            if shortcut:
                button.setShortcut(shortcut)

            row = index // self.num_columns
            column = index % self.num_columns
            self.layout.addWidget(button, row, column)

    def adjust_columns_on_resize(self, event=None):
        # Obtener el ancho actual del widget
        panel_width = self.width()
        button_width = 120  # Ancho aproximado de cada boton
        min_button_spacing = 10  # Espacio minimo entre botones

        # Calcular el numero de columnas en funcion del ancho del widget
        self.num_columns = max(
            1, (panel_width + min_button_spacing) // (button_width + min_button_spacing)
        )

        # Limpiar el layout actual y eliminar widgets solo si existen
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Volver a crear los botones con el nuevo numero de columnas
        self.create_buttons()

        # Calcular el numero de filas usadas
        num_rows = (len(self.buttons) + self.num_columns - 1) // self.num_columns

        # Anadir el espaciador vertical
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout.addItem(spacer, num_rows, 0, 1, self.num_columns)

    # Metodo generico para ejecutar scripts externos
    def execute_external_script(self, script_name):
        script_path = os.path.join(os.path.dirname(__file__), "LGA_NKS", script_name)
        if os.path.exists(script_path):
            try:
                spec = importlib.util.spec_from_file_location(
                    script_name[:-3], script_path
                )
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    module.main()
                else:
                    debug_print(
                        f"El modulo o loader no se encontraron para el script {script_name}"
                    )
            except Exception as e:
                debug_print(f"Error ejecutando el script {script_name}: {e}")
        else:
            debug_print(f"Script no encontrado en la ruta: {script_path}")

    def execute_external_script_from_edit(self, script_name):
        script_path = os.path.join(os.path.dirname(__file__), "LGA_NKS_Edit", script_name)
        if os.path.exists(script_path):
            try:
                spec = importlib.util.spec_from_file_location(
                    script_name[:-3], script_path
                )
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    module.main()
                else:
                    debug_print(
                        f"El modulo o loader no se encontraron para el script {script_name}"
                    )
            except Exception as e:
                debug_print(f"Error ejecutando el script {script_name}: {e}")
        else:
            debug_print(f"Script no encontrado en la ruta: {script_path}")

    # Handlers para cada boton que ejecutan scripts externos
    def execute_SelfReplaceClip(self):
        self.execute_external_script_from_edit("LGA_NKS_SelfReplaceClip.py")

    def execute_EnableOrDisableClips(self):
        self.execute_external_script("LGA_NKS_ON_Clips_OFF_v00-Clips.py")
    
    def execute_EnableOrDisableClips_all_clips(self):
        """Versión que procesa todos los clips del timeline, no solo los seleccionados"""
        script_path = os.path.join(os.path.dirname(__file__), "LGA_NKS", "LGA_NKS_ON_Clips_OFF_v00-Clips.py")
        if os.path.exists(script_path):
            try:
                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_ON_Clips_OFF_v00-Clips", script_path
                )
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # Llamar a main con force_all_clips=True
                    module.main(force_all_clips=True)
                else:
                    debug_print(
                        f"El módulo o loader no se encontraron para el script LGA_NKS_ON_Clips_OFF_v00-Clips.py"
                    )
            except Exception as e:
                debug_print(f"Error ejecutando el script con todos los clips: {e}")
        else:
            debug_print(f"Script no encontrado en la ruta: {script_path}")

    def execute_ToggleBlendModeForEXRTrack(self):
        self.execute_external_script("LGA_NKS_EXRTrack_Difference.py")

    def execute_CompareVersions(self):
        self.execute_external_script("LGA_NKS_Compare_Versions.py")

    def execute_CompareVersionsOff(self):
        self.execute_external_script("LGA_NKS_Compare_Versions_OFF.py")

    def execute_RevealInExplorer(self):
        self.execute_external_script("LGA_NKS_RevealInExplorer.py")

    def execute_RevealNKSProject(self):
        self.execute_external_script("LGA_NKS_RevealNKS_Project.py")

    def execute_RevealNKScript(self):
        self.execute_external_script("LGA_NKS_RevealNK_Script.py")

    def execute_OpenInNukeX(self):
        self.execute_external_script("LGA_NKS_OpenInNukeX.py")

    def execute_DisableEXR(self):
        self.execute_external_script("LGA_NKS_Clip_DisableEXR.py")

    def execute_CheckProjectVersions(self):
        self.execute_external_script("LGA_NKS_CheckProjectVersions.py")


# Crear la instancia del widget y anadirlo al gestor de ventanas de Hiero
reconnectWidget = ReviewPanel()
wm = hiero.ui.windowManager()
wm.addWindow(reconnectWidget)
