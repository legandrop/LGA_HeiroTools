> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_NKS_StyleUtils

Módulo de utilidades para estilos dinámicos de botones en paneles de Hiero/Nuke.

## Funciones Disponibles

### Conversión de Colores
- `hex_to_rgb(hex_color)`: Hex a RGB
- `rgb_to_hex(rgb_tuple)`: RGB a Hex
- `rgb_to_hsv(r, g, b)`: RGB a HSV
- `hsv_to_rgb(h, s, v)`: HSV a RGB

### Utilidades de Gradientes
- `extract_gradient_colors(css_string)`: Extrae colores de definiciones CSS de gradientes

### Cálculos Dinámicos
- `calculate_dynamic_border(style)`: Calcula color de borde dinámico
- `calculate_dynamic_hover(style)`: Calcula color hover dinámico
- `calculate_dynamic_tooltip(style)`: Calcula colores de tooltip dinámico

### Funciones de Alto Nivel
- `create_gradient_style(gradient_type, include_hover=True)`: Crea CSS completo para gradientes predefinidos
- `create_tooltip_stylesheet(style)`: Crea CSS completo para tooltip basado en color del botón

## Uso en Paneles

```python
# Importación
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import calculate_dynamic_border, calculate_dynamic_hover

# Uso
border_color = calculate_dynamic_border("#36166c")  # Para colores sólidos
hover_colors = calculate_dynamic_hover("gradient_magenta_violet")  # Para gradientes
```

## Gradientes Predefinidos

- `gradient_magenta_violet`: Gradiente de magenta a violeta horizontal

## Notas Técnicas

- Los cálculos dinámicos mantienen Hue/Saturación y ajustan solo el Value (brillo)
- Bordes: +20% brillo del color base
- Hover: +28% sólidos, +26% gradientes del color base (más brillante que bordes)
- Tooltips: -8% brillo del color base para fondo (ligeramente más oscuro para contraste)
- Para gradientes, usa el color más brillante como base para cálculos
- Tooltips requieren `objectName` único por botón para estilos específicos

## Dependencias

- Módulo `re` para expresiones regulares
- Funciones puras, sin dependencias externas