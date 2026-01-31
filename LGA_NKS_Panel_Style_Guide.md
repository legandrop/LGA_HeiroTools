# Guía: Sistema de Estilos Personalizados para Paneles Hiero

## Sistema de Estilos Avanzado

Este sistema permite crear estilos personalizados para botones en paneles de Hiero, incluyendo gradientes, colores consistentes y efectos interactivos. **Cambia completamente la apariencia de TODOS los botones del panel**.

### 1. Cambiar Sistema de Colores
Reemplaza colores hexadecimales con identificadores personalizados:

```python
# Definición de botones con identificadores
self.fixed_buttons = [
    ("Botón Normal", handler, "#color_hex", shortcut, tooltip),
    ("Botón con Gradiente", handler, "gradient_tipo", shortcut, tooltip),
    # ...
]
```

### 2. Importar Utilidades de Estilos
Al inicio del archivo del panel, importar las funciones de utilidad:

```python
# Importar funciones de utilidad de estilos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover
)
```

### 3. Sistema de Estilos Unificado
En `create_buttons()`, crea lógica condicional para diferentes tipos de estilos:

```python
# Determinar el estilo del botón
if style.startswith("gradient_"):
    # Aplicar gradientes personalizados con bordes y hover dinámicos
    border_color = calculate_dynamic_border(style)
    hover_colors = calculate_dynamic_hover(style)
    button_stylesheet = f"""
        QPushButton {{
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #color_inicio,
                stop: 1 #color_fin
            );
            border: 1px solid {border_color};
            border-radius: 3px;
            color: #d8d8d8;
            padding: 2px 3px;
        }}
        QPushButton:hover {{
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {hover_colors['inicio']},
                stop: 1 {hover_colors['fin']}
            );
        }}
    """
elif style == "style_especial":
    # Estilos especiales
    button_stylesheet = crear_estilo_especial()
else:
    # Estilo base para colores sólidos con bordes y hover dinámicos
    border_color = calculate_dynamic_border(style)
    hover_color = calculate_dynamic_hover(style)
    button_stylesheet = f"""
        QPushButton {{
            background-color: {style};
            border: 1px solid {border_color};
            border-radius: 3px;
            color: #d8d8d8;
            padding: 2px 3px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {style}aa;
        }}
    """
```

### 3. Gradientes Disponibles

#### Sintaxis Básica
```python
button_stylesheet = """
    QPushButton {
        background-color: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,  # Dirección
            stop: 0 #color_inicio,
            stop: 1 #color_fin
        );
        border: 1px solid #color_borde;
        border-radius: 3px;
        color: #d8d8d8;
        padding: 5px;
    }
    QPushButton:hover { /* variaciones */ }
    QPushButton:pressed { /* variaciones */ }
"""
```

#### Direcciones
- **Horizontal**: `x1: 0, y1: 0, x2: 1, y2: 0`
- **Vertical**: `x1: 0, y1: 0, x2: 0, y2: 1`
- **Diagonal**: `x1: 0, y1: 0, x2: 1, y2: 1`

### 4. Mejores Prácticas

#### Colores Consistentes
- **Texto**: `#d8d8d8` (gris claro) en lugar de `white`
- **Bordes Dinámicos**: Calculados automáticamente basados en el color del botón
- **Estados**: Implementar `:hover` y `:pressed` siempre

#### Bordes, Hover y Tooltips Dinámicos
Los bordes, efectos hover y tooltips se calculan automáticamente para crear jerarquía visual completa:

```python
border_color = calculate_dynamic_border(style)    # +20% brillo
hover_color = calculate_dynamic_hover(style)      # +28% sólidos, +26% gradientes
tooltip_colors = calculate_dynamic_tooltip(style) # Colores adaptados al botón
```

**Jerarquía de brillo:**
- **Color base**: Color original del botón
- **Borde**: +20% más brillante que el color base
- **Hover**: +28% más brillante que el color base para sólidos, +26% para gradientes (más brillante que el borde)
- **Tooltip fondo**: -8% brillo del color base (ligeramente más oscuro para contraste)
- **Pressed**: Más oscuro para efecto de presión

**Tooltips dinámicos:**
- **Fondo**: Basado en el color del botón, ligeramente más oscuro para legibilidad
- **Borde**: Usa el mismo color de borde dinámico del botón
- **Texto**: Blanco para máximo contraste
- **Estilo**: Aplicado individualmente a cada botón

**Para gradientes:**
- Mantiene la dirección y proporción del gradiente
- Hace todos los colores del gradiente más brillantes
- Hover mantiene el efecto de gradiente pero más luminoso
- Tooltips usan el color más brillante del gradiente como base

**Para colores sólidos:**
- Hover es un color uniforme más brillante que el borde
- Tooltips usan el color del botón como base

#### Rendimiento
- Evitar demasiados gradientes complejos
- Usar colores relacionados para mantener coherencia visual

#### Mantenimiento
- Crear funciones separadas para diferentes tipos de estilos
- Documentar identificadores de estilo usados
- Reinicio de Hiero puede ser necesario para ver cambios

#### Scroll en paneles
- Usar `QScrollArea` para evitar solapamiento de botones cuando el panel tiene poca altura
- Definir un umbral de solapamiento (por ejemplo, `SCROLL_OVERLAP_THRESHOLD_PX`) para activar el scroll solo cuando el contenido excede la altura visible por mas de unos pocos pixeles
- Para columnas en `QGridLayout`, calcular el ancho disponible usando el minimo entre `self.width()`, `scroll_area.width()` y `scroll_area.viewport().width()` para evitar columnas extra por anchos inflados
- Por defecto, `SCROLLBAR_VISIBLE = False` para mantener la barra oculta (el scroll con rueda sigue funcionando)
- Paneles actualizados con este sistema: `LGA_NKS_Flow_Assignee_Panel`, `LGA_NKS_Flow_Panel`, `LGA_NKS_Flow_FlowProd_Panel`, `LGA_NKS_ViewerPanel`, `LGA_NKS_EditTools_Panel` y `LGA_NKS_Review_Panel`

### 5. Módulo de Utilidades de Estilos

#### Importación
```python
# Agregar al path y importar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "LGA_NKS_Utils"))
from LGA_NKS_StyleUtils import (
    calculate_dynamic_border,
    calculate_dynamic_hover,
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_hsv,
    hsv_to_rgb,
    extract_gradient_colors,
    create_gradient_style
)
```

#### Funciones Principales
```python
# Cálculo de bordes, hover y tooltips dinámicos
calculate_dynamic_border("#36166c")  # -> Borde +20% brillo
calculate_dynamic_border("gradient_magenta_violet")  # -> Borde basado en gradiente

calculate_dynamic_hover("#36166c")  # -> Hover +28% brillo
calculate_dynamic_hover("gradient_magenta_violet")  # -> {'inicio': color, 'fin': color}

calculate_dynamic_tooltip("#36166c")  # -> {'background': color, 'border': color, 'text': color}
calculate_dynamic_tooltip("gradient_magenta_violet")  # -> Colores basados en gradiente

create_tooltip_stylesheet("#36166c")  # -> CSS completo para tooltip
```

#### Funciones de Conversión de Color
```python
# Conversión básica
hex_to_rgb("#ff0000")  # -> (255, 0, 0)
rgb_to_hex((255, 0, 0))  # -> "#ff0000"

# Espacio de color HSV para cálculos avanzados
rgb_to_hsv(r, g, b)  # RGB a HSV (H: 0-360, S: 0-100, V: 0-100)
hsv_to_rgb(h, s, v)  # HSV a RGB

# Utilidades para gradientes
extract_gradient_colors("stop: 0 #color1, stop: 1 #color2")  # -> ["#color1", "#color2"]
```

#### Ejemplo Completo con Tooltips
```python
def crear_estilo_completo(self, tipo_estilo, button_index):
    """Crea estilos completos incluyendo tooltips dinámicos"""
    # Estilos base del botón
    if tipo_estilo.startswith("gradient_"):
        button_style = crear_estilo_gradiente(tipo_estilo)
    else:
        button_style = crear_estilo_solido(tipo_estilo)

    # Estilos de tooltip dinámicos
    tooltip_style = create_tooltip_stylesheet(tipo_estilo)
    button_name = f"button_{button_index}"
    tooltip_style = tooltip_style.replace("QToolTip", f"#{button_name} QToolTip")

    # Combinar estilos
    full_style = button_style + tooltip_style
    return full_style, button_name
```

#### Aplicación en el Panel
```python
# En create_buttons()
full_style, button_name = crear_estilo_completo(style, index)
button = QPushButton(name)
button.setObjectName(button_name)
button.setStyleSheet(full_style)
if tooltip:
    button.setToolTip(tooltip)
```

#### Uso de create_gradient_style() (Función de Alto Nivel)
```python
# Para estilos predefinidos, usar la función de alto nivel
from LGA_NKS_StyleUtils import create_gradient_style

style = create_gradient_style("gradient_magenta_violet", include_hover=True)
# Retorna CSS completo listo para usar
```

## Problemas Comunes

- **Cambios no visibles**: Reiniciar Hiero completamente
- **Inconsistencias**: Verificar que todos los botones usen el nuevo sistema
- **Importación del módulo**: Asegurarse que `LGA_NKS_StyleUtils.py` esté en la carpeta `LGA_NKS_Utils` y el path sea correcto
- **Bordes dinámicos**: Si no se ven bien, verificar que `calculate_dynamic_border()` esté funcionando correctamente
- **Hover dinámico**: Verificar que `calculate_dynamic_hover()` retorne colores válidos
- **Tooltips dinámicos**: Verificar que cada botón tenga `objectName` único y que `create_tooltip_stylesheet()` funcione
- **Gradientes hover**: Asegurarse que los gradientes mantengan buena legibilidad en hover
- **Tooltips sin estilo**: Verificar que el selector `#{button_name} QToolTip` esté funcionando correctamente
- **Rendimiento**: Evitar gradientes muy complejos o muchos cálculos de color
- **Colores HSV**: Verificar rangos (H: 0-360, S: 0-100, V: 0-100)
- **Módulo no encontrado**: Verificar que `sys.path.insert(0, ...)` apunte al directorio correcto

## Referencia Qt
[Qt Style Sheets - Linear Gradients](https://doc.qt.io/qtforpython-6.8/overviews/qtwidgets-stylesheet-reference.html)</contents>
</xai:function_call">Write
