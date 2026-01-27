"""
________________________________________________________________

  LGA_ViewerPanel v1.67 | Lega
  Panel con herramientas para el viewer y el timeline de Hiero

  v1.67: Agregado usuario Juano a botones dinámicos de prev/next rev.
  v1.66: Botones de prev/next rev para usuarios Lega, Javi y Sebas ahora son dinámicos y se muestran solo para el usuario actual.
  v1.65: Actualizado el script LGA_NKS_Viewer_Mask.py para usar el aspect ratio especificado
  v1.64: Actualizado para usar estilos dinámicos con bordes y hover para todos los botones
         Agregado tooltip dinámico para todos los botones
         Optimizado espaciado del layout y dimensiones de botones para mejor UX
  v1.63: Reorganización de scripts - Todos los scripts del viewer movidos
         a LGA_NKS_ViewerTL/ para mejor organización
  v1.62: Se agregó el botón Frame Number
  v1.61: Se agregaron tooltips
________________________________________________________________

"""

import hiero.ui
import hiero.core
import os
import subprocess
import socket
import sys
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

# Importar funciones de utilidad de estilos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover,
    create_tooltip_stylesheet
)

# Añadir el directorio padre al path para importar módulos de PipeSync
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

# Variable global para activar o desactivar los prints
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def obtener_usuario_actual():
    """
    Obtiene el usuario actual de PipeSync desde la configuración segura.

    Returns:
        str: Login del usuario actual, o None si no se puede determinar
    """
    try:
        from LGA_NKS_Flow.SecureConfig_Reader import get_flow_credentials

        url, login, password = get_flow_credentials()
        if login:
            debug_print(f"Usuario actual determinado: {login}")
            return login
    except Exception as e:
        debug_print(f"Error obteniendo usuario actual: {e}")

    return None


class ViewerPanel(QtWidgets.QWidget):
    def __init__(self):
        super(ViewerPanel, self).__init__()

        self.setObjectName("com.lega.ViewerPanel")
        self.setWindowTitle("ViewerTL")

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(6)  # Reducir espacio entre botones
        self.setLayout(self.layout)

        # Obtener usuario actual para crear botones dinámicos
        self.usuario_actual = obtener_usuario_actual()

        # Crear botones dinámicos según el usuario actual
        self.buttons = self.create_dynamic_buttons()

        self.num_columns = 1  # Inicialmente una columna
        self.create_buttons()

        # Conectar la senal de cambio de tamano del widget al metodo correspondiente
        self.adjust_columns_on_resize()
        self.resizeEvent = self.adjust_columns_on_resize

    def create_dynamic_buttons(self):
        """
        Crea la lista de botones dinámicamente según el usuario actual.
        Solo muestra los botones de navegación del usuario actual.
        """
        # Botones comunes (siempre visibles)
        common_buttons = [
            (
                "&Viewer | Rec709",
                self.rec709_viewer,
                "#311840",
                "Shift+V",
                "Shift+V\nCambia el LUT del viewer a ACES/Rec.709",
            ),
            (
                "Viewer | 2.35:1 ",
                self.viewer_235,
                "#311840",
                None,
                "Ajusta el overlay del viewer a 2.35:1 y alterna los estilos de máscara\n(None, Half, Full) ajustando el efecto Frame del track BurnIn",
            ),
            (
                "Viewer | 2:1 ",
                self.viewer_21,
                "#311840",
                None,
                "Ajusta el overlay del viewer a 2:1 y alterna los estilos de máscara\n(None, Half, Full) ajustando el efecto Frame del track BurnIn",
            ),
            (
                "Refresh Timeline",
                self.refresh_timeline,
                "#4c4350",
                None,
                "Refresca el timeline manteniendo el nivel de zoom original\n(cuando el timeline funciona mal lo resetea)",
            ),
            (
                "Top Track ",
                self.top_track,
                "#4c4350",
                "Ctrl+Shift+T",
                "Ctrl+Shift+T\nScrollea al track superior del timeline",
            ),
            (
                "In Out Editref",
                self.in_out_editref,
                "#4d462b",
                "Ctrl+Shift+U",
                "Ctrl+Shift+U\nEstablece los puntos In y Out de la secuencia basándose\nen el clip más cercano del track EditRef o EditRefClean",
            ),
        ]

        # Botones de usuario (solo del usuario actual)
        user_buttons = []

        if self.usuario_actual:
            # Normalizar el email del usuario (tomar parte antes del @)
            usuario_normalizado = self.usuario_actual.split('@')[0].lower()

            # Manejar caso especial de Sebas
            if usuario_normalizado == "sebasromano_post":
                usuario_normalizado = "sebas"

            # Alias de usuarios (login -> key en usuarios_config)
            usuario_aliases = {
                "juanolivares": "juano",
            }
            usuario_normalizado = usuario_aliases.get(
                usuario_normalizado, usuario_normalizado
            )

            debug_print(f"Usuario normalizado: {usuario_normalizado}")

            # Configuración de usuarios con sus emails normalizados
            usuarios_config = {
                "lega": {
                    "nombre": "Lega",
                    "color": "#69135e",
                    "prev_shortcut": "Ctrl+Alt+Shift+,",
                    "next_shortcut": "Ctrl+Alt+Shift+.",
                },
                "javi": {
                    "nombre": "Javi",
                    "color": "#9c3e5e",
                    "prev_shortcut": "Ctrl+Alt+Shift+,",  # Usar shortcuts de Lega
                    "next_shortcut": "Ctrl+Alt+Shift+.",  # Usar shortcuts de Lega
                },
                "sebas": {
                    "nombre": "Sebas",
                    "color": "#bd7f9f",
                    "prev_shortcut": "Ctrl+Alt+Shift+,",  # Usar shortcuts de Lega
                    "next_shortcut": "Ctrl+Alt+Shift+.",  # Usar shortcuts de Lega
                },
                "juano": {
                    "nombre": "Juano",
                    "color": "#9a4a79",
                    "prev_shortcut": "Ctrl+Alt+Shift+,",  # Usar shortcuts de Lega
                    "next_shortcut": "Ctrl+Alt+Shift+.",  # Usar shortcuts de Lega
                }
            }

            # Verificar si el usuario está en la configuración
            if usuario_normalizado in usuarios_config:
                config = usuarios_config[usuario_normalizado]

                user_buttons.extend([
                    (
                        f"Prev Rev {config['nombre']}",
                        getattr(self, f"prev_rev_{usuario_normalizado}"),
                        config['color'],
                        config['prev_shortcut'],
                        f"{config['prev_shortcut']}\nBusca el clip anterior con estado Rev {config['nombre']} y ajusta la vista\n(establece In/Out desde EditRef, selecciona clip, ajusta zoom)",
                    ),
                    (
                        f"Next Rev {config['nombre']}",
                        getattr(self, f"next_rev_{usuario_normalizado}"),
                        config['color'],
                        config['next_shortcut'],
                        f"{config['next_shortcut']}\nBusca el clip siguiente con estado Rev {config['nombre']} y ajusta la vista\n(establece In/Out desde EditRef, selecciona clip, ajusta zoom)",
                    ),
                ])
                debug_print(f"Mostrando botones para usuario: {config['nombre']}")
            else:
                debug_print(f"Usuario '{usuario_normalizado}' no reconocido en configuración")
        else:
            debug_print("No se pudo determinar usuario actual - no se mostrarán botones de usuario")

        # Botones finales (siempre visibles)
        final_buttons = [
            (
                "SnapShot",
                self.snapshot,
                "#2d5a3d",
                None,
                "Crea un snapshot de la imagen actual del viewer\n(cropeada al aspect ratio de la secuencia) y lo copia al portapapeles\nIdeal para enviar por telegram con algun comentario",
            ),
            (
                "Frame Number",
                self.frame_number_position,
                "#0e1f3b",
                "Shift+F",
                "Shift+F\nMueve el burnin de frame number al área visible\nabajo a la izquierda del viewer",
            ),
        ]

        # Combinar todos los botones
        all_buttons = common_buttons + user_buttons + final_buttons

        debug_print(f"Total de botones creados: {len(all_buttons)}")
        return all_buttons

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
                    min-height: 22px;
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

            button = QtWidgets.QPushButton(name)
            button.setObjectName(f"button_{index}")  # Para tooltips dinámicos
            button.setStyleSheet(button_stylesheet)
            button.clicked.connect(handler)
            if shortcut:
                button.setShortcut(QtGui.QKeySequence(shortcut))
            if tooltip:
                button.setToolTip(tooltip)

            row = index // self.num_columns
            column = index % self.num_columns
            self.layout.addWidget(button, row, column)

    def adjust_columns_on_resize(self, event=None):
        # Obtener el ancho actual del widget
        panel_width = self.width()
        button_width = 140  # Reducido el ancho aproximado de cada boton
        min_button_spacing = 5  # Reducido el espacio minimo entre botones

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

    ##### Rec709 en Viewer
    def rec709_viewer(self):
        try:
            current_viewer = hiero.ui.currentViewer()
            if current_viewer:
                current_viewer.player().setLUT("ACES/Rec.709")
                debug_print("LUT set to ACES/Rec.709")
            else:
                debug_print("No active viewer found.")
        except Exception as e:
            debug_print(f"Error setting Rec.709 LUT: {e}")

    def viewer_235(self):
        self.run_viewer_mask_script("2.35:1")

    def viewer_21(self):
        self.run_viewer_mask_script("2:1")

    def run_viewer_mask_script(self, aspect_ratio):
        """
        Ejecuta el script genérico de máscara del viewer con el aspect ratio especificado.

        Args:
            aspect_ratio (str): El aspect ratio a aplicar (ej: "2.35:1", "2:1")
        """
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_Viewer_Mask.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_Viewer_Mask", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la funcion main del script con el aspect ratio especificado
                module.main(aspect_ratio)
                debug_print(f"Executed LGA_NKS_Viewer_Mask script with aspect ratio {aspect_ratio}.")
            else:
                debug_print(f"Script not found at path: {script_path}")
        except Exception as e:
            debug_print(f"Error during running Viewer Mask script with aspect ratio {aspect_ratio}: {e}")

    ###### Refresh timeline
    def refresh_timeline(self):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_Timeline_Refresh_Wrap.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_Timeline_Refresh_Wrap", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la función main del script wrapper
                module.main()
                debug_print("Executed Timeline Refresh Wrap script.")
            else:
                debug_print(f"Script not found at path: {script_path}")
        except Exception as e:
            debug_print(f"Error during Timeline Refresh: {e}")

    ###### Top Track
    def top_track(self):
        # Ruta al script dentro de la subcarpeta LGA_NKS
        script_path = os.path.join(
            os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_ScrollTo_TopTrack.py"
        )
        if os.path.exists(script_path):
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "LGA_NKS_ScrollTo_TopTrack", script_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Llamar a la funcion principal del script
            module.main()
        else:
            debug_print(f"Script not found at path: {script_path}")

    ###### In Out Editref
    def in_out_editref(self):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_InOut_Editref.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_InOut_Editref", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la funcion principal del script
                module.main()
                debug_print("Ejecutado LGA_NKS_InOut_Editref script.")
            else:
                debug_print(f"Script no encontrado en la ruta: {script_path}")
        except Exception as e:
            debug_print(f"Error al ejecutar el script In Out Editref: {e}")

    def prev_rev_sup(self):
        self.execute_prevnext_rev("prev", "sup")

    def next_rev_sup(self):
        self.execute_prevnext_rev("next", "sup")

    def prev_rev_lega(self):
        self.execute_prevnext_rev("prev", "lega")

    def next_rev_lega(self):
        self.execute_prevnext_rev("next", "lega")

    def prev_rev_javi(self):
        self.execute_prevnext_rev("prev", "javi")

    def next_rev_javi(self):
        self.execute_prevnext_rev("next", "javi")

    def prev_rev_juano(self):
        self.execute_prevnext_rev("prev", "juano")

    def next_rev_juano(self):
        self.execute_prevnext_rev("next", "juano")

    # Métodos dinámicos para usuarios - delegan a los métodos existentes
    def prev_rev_sebas(self):
        self.execute_prevnext_rev("prev", "sup")  # Sebas usa "sup"

    def next_rev_sebas(self):
        self.execute_prevnext_rev("next", "sup")  # Sebas usa "sup"

    def execute_prevnext_rev(self, direction, rev_type):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_PrevNext_Rev.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_PrevNext_Rev", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.main(direction, rev_type)
                debug_print(
                    f"Ejecutado LGA_NKS_PrevNext_Rev script con dirección {direction} y tipo {rev_type}."
                )
            else:
                debug_print(f"Script no encontrado en la ruta: {script_path}")
        except Exception as e:
            debug_print(f"Error al ejecutar el script PrevNext Rev: {e}")

    ###### SnapShot
    def snapshot(self):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_SnapShot.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_SnapShot", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la funcion principal del script
                module.main()
                debug_print("Ejecutado LGA_NKS_SnapShot script.")
            else:
                debug_print(f"Script no encontrado en la ruta: {script_path}")
        except Exception as e:
            debug_print(f"Error al ejecutar el script SnapShot: {e}")

    ###### Frame Number Position
    def frame_number_position(self):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_NKS_ViewerTL", "LGA_NKS_FrameNumber.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_FrameNumber", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la funcion principal del script
                module.print_box_values()
                debug_print("Ejecutado LGA_NKS_FrameNumber script.")
            else:
                debug_print(f"Script no encontrado en la ruta: {script_path}")
        except Exception as e:
            debug_print(f"Error al ejecutar el script Frame Number Position: {e}")


# Crear la instancia del widget y anadirlo al gestor de ventanas de Hiero
viewerPanel = ViewerPanel()
wm = hiero.ui.windowManager()
wm.addWindow(viewerPanel)
