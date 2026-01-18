"""
____________________________________________________________________________________

  LGA_NKS_Flow_FlowProd_Panel v1.22 | Lega
  Panel para operaciones de producción con Flow:
  - Revelar clips en Flow
  - Crear shots automáticamente
  - Crear thumbnails
  - Cambiar prioridad de shots
  - Integración con FileManager (Open, Download, Upload)


  v1.22: Boton Check Shots Exist para chequear si los shots del track comp existen en Flow
  v1.21: Actualizado para usar estilos dinámicos con bordes y hover para todos los botones
         Agregado tooltip dinámico para todos los botones
         
  v1.20: Agregados botones de integración con FileManager CLI
         - Open in FileManager: Abre carpeta del shot en FileManager
         - Download Shot: Descarga shot desde Wasabi S3
         - Upload Shot: Sube shot a Wasabi S3
         Funcionan sobre la ruta del shot (unidad/proyecto/grupo/shot)

  v1.10: Actualizado para usar shift+click para abrir el shot completo en Flow

  v1.09: Agregado modo de modificación de shots existentes
         Reutiliza la misma UI compacta de creación
         Permite agregar/eliminar tasks y actualizar la descripción
         No afecta estados ni tiempos de las tasks existentes

  v1.08: Actualizado para ser compatible con ambos sistemas de nomenclatura:
        - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
        - PROYECTO_SEQ_SHOT (3 bloques simplificado)
____________________________________________________________________________________
"""

import hiero.ui
import hiero.core
import sys
import os
import re
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore


# Clase de botón personalizada que maneja el Shift+Click
class CustomButton(QtWidgets.QPushButton):
    def __init__(self, text):
        super(CustomButton, self).__init__(text)
        self._custom_click_handler = None
        self._shift_click_handler = None
        # Conectar la señal clicked para manejar tanto clicks normales como shortcuts
        self.clicked.connect(self._handle_click)

    def setCustomClickHandler(self, handler):
        self._custom_click_handler = handler

    def setShiftClickHandler(self, handler):
        self._shift_click_handler = handler

    def _handle_click(self):
        """Maneja los clicks del botón, verificando si es Shift+Click"""
        if self._custom_click_handler and self._shift_click_handler:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers & QtCore.Qt.ShiftModifier:
                self._shift_click_handler()
            else:
                self._custom_click_handler()
        else:
            # Si no hay handlers personalizados, comportamiento normal
            pass

# Importar función de limpieza de nombres desde NamingUtils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Flow"))
from LGA_NKS_Flow_NamingUtils import clean_base_name


# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


# Importar funciones de utilidad de estilos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover,
    create_tooltip_stylesheet
)


class FlowProdPanel(QtWidgets.QWidget):
    def __init__(self):
        super(FlowProdPanel, self).__init__()
        self.setObjectName("com.lega.FlowProdPanel")
        self.setWindowTitle("Coordination")
        self.layout = QtWidgets.QGridLayout()
        self.layout.setSpacing(6)  # Reducir espacio entre botones
        self.setLayout(self.layout)

        # Definir los botones fijos y sus colores/estilos
        self.fixed_buttons = [
            (
                "Reveal in Flow",
                self.show_in_flow_for_selected_clip,
                "#1f1f1f",
                "Ctrl+Shift+F",
                "Click: Abrir task comp en Flow\nShift+Click: Abrir Shot completo en Flow (Ctrl+Shift+F)",
            ),
            (
                "Thumbnail",
                self.create_thumbnail_for_selected_clip,
                "#3a2a4d",
                None,
                "Crear thumbnail en Flow basado en el clip seleccionado",
            ),
            (
                "Create Shot",
                self.create_shot_for_selected_clip,
                "#2a4d3a",
                None,
                "Crear shot en Flow basado en el clip seleccionado",
            ),
            (
                "Modify Shot",
                self.modify_shot_for_selected_clip,
                "#2a4d3a",
                None,
                "Modificar shot existente en Flow (1 clip a la vez)",
            ),
            (
                "Check Shots Exist",
                self.check_timeline_shots,
                "#2a4d3a",
                None,
                "Chequear si los shots del track comp existen en Flow",
            ),
            (
                "Shot Priority",
                self.toggle_shot_priority_for_selected_clip,
                "#450101",
                None,
                "Cambiar prioridad del shot (alta ↔ normal)",
            ),
            (
                "FileManager",
                self.open_shot_in_filemanager,
                "gradient_magenta_violet",
                None,
                "Abrir carpeta del shot en FileManager",
            ),
            (
                "Download Shot",
                self.download_shot_from_filemanager,
                "gradient_magenta_violet",
                None,
                "Descargar shot desde Wasabi S3",
            ),
            (
                "Upload Shot",
                self.upload_shot_to_filemanager,
                "gradient_magenta_violet",
                None,
                "Subir shot a Wasabi S3",
            ),
        ]

        # Solo botones fijos para este panel
        self.buttons = self.fixed_buttons

        self.num_columns = 1  # Inicialmente una columna
        self.create_buttons()

        # Conectar la senal de cambio de tamano del widget al metodo correspondiente
        self.adjust_columns_on_resize()
        self.resizeEvent = self.adjust_columns_on_resize

    def create_buttons(self):
        # Limpiar el layout actual antes de crear nuevos botones
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for index, button_info in enumerate(self.buttons):
            name = button_info[0]
            handler = button_info[1]
            style = button_info[2]

            # Solo botones fijos para este panel: (name, handler, style, [shortcut], [tooltip])
            shortcut = button_info[3] if len(button_info) > 3 else None
            tooltip = button_info[4] if len(button_info) > 4 else None

            # Determinar el estilo del botón
            if style == "gradient_magenta_violet":
                border_color = calculate_dynamic_border(style)
                hover_colors = calculate_dynamic_hover(style)
                button_stylesheet = f"""
                    QPushButton {{
                        background-color: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 0,
                            stop: 0 #443a91,
                            stop: 0.5 #543a91,
                            stop: 1 #5b3a91
                        );
                        border: 1px solid {border_color};
                        border-radius: 3px;
                        color: #d8d8d8;
                        padding: 0px 0px;
                        min-height: 24px;
                    }}
                    QPushButton:hover {{
                        background-color: qlineargradient(
                            x1: 0, y1: 1, x2: 1, y2: 0,
                            stop: 0 {hover_colors['inicio']},
                            stop: 0.5 #9a6cd8,
                            stop: 1 {hover_colors['fin']}
                        );
                    }}
                    QPushButton:pressed {{
                        background-color: qlineargradient(
                            x1: 0, y1: 1, x2: 1, y2: 0,
                            stop: 0 #5145ac,
                            stop: 0.5 #6a49b5,
                            stop: 1 #5b3a91
                        );
                    }}
                """
            else:
                border_color = calculate_dynamic_border(style)
                hover_color = calculate_dynamic_hover(style)
                button_stylesheet = f"""
                    QPushButton {{
                        background-color: {style};
                        border: 1px solid {border_color};
                        border-radius: 3px;
                        color: #d8d8d8;
                        padding: 0px 0px;
                        min-height: 24px;
                    }}
                    QPushButton:hover {{
                        background-color: {hover_color};
                    }}
                    QPushButton:pressed {{
                        background-color: {style}aa;
                    }}
                """

            # Usar CustomButton para el botón "Reveal in Flow" para soportar Shift+Click
            if name == "Reveal in Flow":
                button = CustomButton(name)
                button.setCustomClickHandler(handler)
                button.setShiftClickHandler(self.show_shot_in_flow_for_selected_clip)
            else:
                button = QtWidgets.QPushButton(name)
                button.clicked.connect(handler)

            # Aplicar estilos del botón
            button.setStyleSheet(button_stylesheet)

            # Agregar estilos de tooltip dinámicos si hay tooltip
            if tooltip:
                # Crear un selector único para este botón usando su objectName
                button_object_name = f"button_{index}"
                button.setObjectName(button_object_name)

                # Crear stylesheet de tooltip dinámico
                tooltip_stylesheet = create_tooltip_stylesheet(style)
                # Modificar el tooltip stylesheet para usar el selector del botón
                tooltip_stylesheet = tooltip_stylesheet.replace("QToolTip", f"#{button_object_name} QToolTip")

                # Combinar estilos del botón con estilos de tooltip
                full_stylesheet = button_stylesheet + tooltip_stylesheet
                button.setStyleSheet(full_stylesheet)

                # Agregar el tooltip
                button.setToolTip(tooltip)

            # Agregar shortcut si existe
            if shortcut:
                button.setShortcut(QtGui.QKeySequence(shortcut))

            row = index // self.num_columns
            column = index % self.num_columns
            self.layout.addWidget(button, row, column)

        # Calcular el numero de filas usadas
        num_rows = (len(self.buttons) + self.num_columns - 1) // self.num_columns

        # Anadir el espaciador vertical al final
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout.addItem(spacer, num_rows, 0, 1, self.num_columns)

    def adjust_columns_on_resize(self, event=None):
        # Obtener el ancho actual del widget
        panel_width = self.width()
        button_width = 100  # Ancho aproximado de cada boton
        min_button_spacing = 10  # Espacio minimo entre botones

        # Calcular el numero de columnas en funcion del ancho del widget
        new_num_columns = max(
            1, (panel_width + min_button_spacing) // (button_width + min_button_spacing)
        )

        if new_num_columns != self.num_columns:
            self.num_columns = new_num_columns
            # Volver a crear los botones con el nuevo numero de columnas
            self.create_buttons()

    def parse_exr_name(self, exr_name):
        """Extrae el nombre base del archivo EXR usando funciones compartidas de NamingUtils."""
        # Usar función compartida para limpiar el nombre base (compatible con ambos formatos)
        base_name = clean_base_name(exr_name)
        return base_name

    def show_in_flow_for_selected_clip(self):
        """Llama al script Show in Flow para abrir la task comp en Chrome"""
        debug_print("=== CLICK NORMAL: Show in Flow (Task Comp) ===")
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_ShowInFlow.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_ShowInFlow", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_ShowInFlow.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            debug_print("Llamando a show_in_flow_from_selected_clip()")
            module.show_in_flow_from_selected_clip()
        except Exception as e:
            debug_print(f"Error al ejecutar show_in_flow_from_selected_clip: {e}")
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def show_shot_in_flow_for_selected_clip(self):
        """Llama al script Show in Flow para abrir el Shot completo en Chrome (Shift+Click)"""
        debug_print("=== SHIFT+CLICK: Show Shot in Flow (Shot completo) ===")
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_ShowInFlow.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_ShowInFlow", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_ShowInFlow.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función para abrir el Shot (no la task comp)
            debug_print("Llamando a show_shot_in_flow_from_selected_clip()")
            module.show_shot_in_flow_from_selected_clip()
        except Exception as e:
            debug_print(f"Error al ejecutar show_shot_in_flow_from_selected_clip: {e}")
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def create_thumbnail_for_selected_clip(self):
        """Llama al script Thumbnail para crear un thumbnail del clip seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_Thumbs.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_Thumbs", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError("No se pudo cargar el módulo LGA_NKS_Flow_Thumbs.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def create_shot_for_selected_clip(self):
        """Llama al script Create Shot para crear shots basado en el clip seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_CreateShot.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_CreateShot", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_CreateShot.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def modify_shot_for_selected_clip(self):
        """Llama al script Modify Shot para ajustar shots existentes"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_ModifyShot.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_ModifyShot", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_ModifyShot.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def toggle_shot_priority_for_selected_clip(self):
        """Llama al script Shot Priority para cambiar la prioridad del shot seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_ShotPriority.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_ShotPriority", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_ShotPriority.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.toggle_shot_priority_from_selected_clip()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def open_shot_in_filemanager(self):
        """Llama al script FileManager para abrir la carpeta del shot seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_FileManager_OpenPath.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_FileManager_OpenPath", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_FileManager_OpenPath.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def download_shot_from_filemanager(self):
        """Llama al script FileManager para descargar el shot seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_FileManager_Download.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_FileManager_Download", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_FileManager_Download.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def upload_shot_to_filemanager(self):
        """Llama al script FileManager para subir el shot seleccionado"""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_FileManager_Upload.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_FileManager_Upload", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_FileManager_Upload.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Llamar a la función principal
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar", str(e))

    def check_timeline_shots(self):
        """Llama al script de chequeo de shots en el timeline."""
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_Flow_Prod", "LGA_NKS_Flow_CheckTimelineShots.py"
        )
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Script no encontrado",
                f"No se encontró el script en la ruta: {script_path}",
            )
            return
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_Flow_CheckTimelineShots", script_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar el módulo LGA_NKS_Flow_CheckTimelineShots.py"
                )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error al ejecutar Check Shots", str(e))


# Crear la instancia del panel y agregarlo al windowManager de Hiero
flowProdPanel = FlowProdPanel()
wm = hiero.ui.windowManager()
wm.addWindow(flowProdPanel)
