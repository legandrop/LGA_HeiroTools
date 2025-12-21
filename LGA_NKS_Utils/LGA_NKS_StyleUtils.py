# LGA_NKS_StyleUtils.py
"""
Utilidades para estilos dinámicos de botones en paneles Hiero.
Incluye funciones para conversión de colores, cálculo de bordes dinámicos y gradientes.
"""

import re


# Funciones de conversión de colores
def hex_to_rgb(hex_color):
    """Convierte color hex a RGB (0-255)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convierte RGB (0-255) a hex"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def rgb_to_hsv(r, g, b):
    """Convierte RGB (0-255) a HSV (0-360, 0-100, 0-100)"""
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn

    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360

    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100

    v = mx * 100
    return h, s, v


def hsv_to_rgb(h, s, v):
    """Convierte HSV (0-360, 0-100, 0-100) a RGB (0-255)"""
    h, s, v = h, s/100.0, v/100.0

    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    elif 300 <= h < 360:
        r, g, b = c, 0, x
    else:
        r, g, b = 0, 0, 0

    r = int((r + m) * 255)
    g = int((g + m) * 255)
    b = int((b + m) * 255)

    return r, g, b


# Funciones para gradientes
def extract_gradient_colors(gradient_css):
    """Extrae colores hex de una definición de gradiente CSS"""
    # Buscar patrones como stop: 0 #color, stop: 1 #color
    color_pattern = r'stop:\s*\d+\s*#([a-fA-F0-9]{6})'
    matches = re.findall(color_pattern, gradient_css)
    return ['#' + color for color in matches]


# Funciones para estilos dinámicos
def calculate_dynamic_border(style):
    """
    Calcula un color de borde dinámico basado en el estilo del botón.
    Para gradientes, usa el color con mayor brillo (value).
    Para colores sólidos, aumenta el brillo manteniendo hue/saturación.
    """
    if style.startswith("gradient_"):
        # Para gradientes, extraer colores y usar el más brillante
        gradient_colors = []
        if style == "gradient_magenta_violet":
            gradient_colors = ["#5c166c", "#36166c"]

        if not gradient_colors:
            return "#616161"  # Color fallback

        # Encontrar el color con mayor value (brillo)
        max_value = 0
        brightest_color = gradient_colors[0]

        for color in gradient_colors:
            r, g, b = hex_to_rgb(color)
            h, s, v = rgb_to_hsv(r, g, b)
            if v > max_value:
                max_value = v
                brightest_color = color

        base_color = brightest_color
    else:
        # Para colores sólidos, usar el color directamente
        base_color = style

    # Convertir a HSV y aumentar el value (brillo) en un 20%
    r, g, b = hex_to_rgb(base_color)
    h, s, v = rgb_to_hsv(r, g, b)

    # Aumentar el brillo pero mantener hue y saturación
    new_v = min(100, v + 20)  # Aumentar value máximo 20 puntos

    # Convertir de vuelta a RGB y hex
    new_r, new_g, new_b = hsv_to_rgb(h, s, new_v)
    return rgb_to_hex((new_r, new_g, new_b))


def calculate_dynamic_hover(style):
    """
    Calcula colores hover dinámicos más brillantes que los bordes.
    Para gradientes, crea un gradiente más brillante.
    Para colores sólidos, color más brillante que el borde.
    """
    if style.startswith("gradient_"):
        # Para gradientes, crear versión más brillante de todo el gradiente
        if style == "gradient_magenta_violet":
            # Colores base del gradiente
            base_colors = ["#5c166c", "#36166c"]
            hover_colors = []

            for color in base_colors:
                r, g, b = hex_to_rgb(color)
                h, s, v = rgb_to_hsv(r, g, b)
                # Aumentar brillo más que el borde (26% en lugar de 20%)
                new_v = min(100, v + 26)
                new_r, new_g, new_b = hsv_to_rgb(h, s, new_v)
                hover_colors.append(rgb_to_hex((new_r, new_g, new_b)))

            return {
                "inicio": hover_colors[0],
                "fin": hover_colors[1]
            }

        return None  # Gradiente no reconocido

    else:
        # Para colores sólidos, hacer hover aún más brillante que el borde
        base_color = style
        r, g, b = hex_to_rgb(base_color)
        h, s, v = rgb_to_hsv(r, g, b)

        # El borde ya es +20%, el hover será +28% para ser más brillante pero no tanto
        new_v = min(100, v + 28)

        new_r, new_g, new_b = hsv_to_rgb(h, s, new_v)
        return rgb_to_hex((new_r, new_g, new_b))


def calculate_dynamic_tooltip(style):
    """
    Calcula colores de tooltip dinámicos basados en el color del botón.
    Crea tooltips que respeten el color del botón y mantengan buena legibilidad.
    """
    if style.startswith("gradient_"):
        # Para gradientes, usar el color más brillante como base
        if style == "gradient_magenta_violet":
            base_color = "#5c166c"  # Color más brillante del gradiente
        else:
            base_color = "#36166c"  # Fallback
    else:
        # Para colores sólidos, usar el color del botón
        base_color = style

    # Calcular colores del tooltip
    r, g, b = hex_to_rgb(base_color)
    h, s, v = rgb_to_hsv(r, g, b)

    # Fondo: ligeramente más oscuro que el botón para contraste
    bg_v = max(10, v - 8)  # Reducir brillo para fondo (menos oscuro)
    bg_r, bg_g, bg_b = hsv_to_rgb(h, s, bg_v)
    background_color = rgb_to_hex((bg_r, bg_g, bg_b))

    # Borde: usar el borde dinámico del botón
    border_color = calculate_dynamic_border(style)

    # Texto: blanco para máximo contraste
    text_color = "#ffffff"

    return {
        "background": background_color,
        "border": border_color,
        "text": text_color
    }


def create_tooltip_stylesheet(style):
    """
    Crea un stylesheet CSS completo para tooltip basado en el color del botón.
    """
    colors = calculate_dynamic_tooltip(style)
    return f"""
        QToolTip {{
            color: {colors['text']};
            background-color: {colors['background']};
            border: 1px solid {colors['border']};
            border-radius: 3px;
            padding: 4px;
        }}
    """


# Función para crear estilos de gradiente completos (opcional, para reutilización)
def create_gradient_style(gradient_type, include_hover=True):
    """
    Crea un estilo CSS completo para un gradiente específico.
    Útil para reutilizar en múltiples paneles.
    """
    gradients = {
        "gradient_magenta_violet": {
            "inicio": "#5c166c",
            "fin": "#36166c"
        }
        # Agregar más gradientes aquí según se necesiten
    }

    if gradient_type not in gradients:
        return None

    config = gradients[gradient_type]
    border_color = calculate_dynamic_border(gradient_type)

    style = f"""
        QPushButton {{
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {config['inicio']},
                stop: 1 {config['fin']}
            );
            border: 1px solid {border_color};
            border-radius: 3px;
            color: #d8d8d8;
            padding: 2px 3px;
        }}
    """

    if include_hover:
        hover_colors = calculate_dynamic_hover(gradient_type)
        if hover_colors:
            style += f"""
        QPushButton:hover {{
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {hover_colors['inicio']},
                stop: 1 {hover_colors['fin']}
            );
        }}
            """

    style += """
        QPushButton:pressed {
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #5c166c,
                stop: 1 #2a1450
            );
        }
    """

    return style