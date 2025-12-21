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

### 2. Sistema de Estilos Unificado
En `create_buttons()`, crea lógica condicional para diferentes tipos de estilos:

```python
# Determinar el estilo del botón
if style.startswith("gradient_"):
    # Aplicar gradientes personalizados
    button_stylesheet = crear_estilo_gradiente(style)
elif style == "style_especial":
    # Estilos especiales
    button_stylesheet = crear_estilo_especial()
else:
    # Estilo base para colores sólidos
    button_stylesheet = f"""
        QPushButton {{
            background-color: {style};
            border: 1px solid #616161;  # Borde gris para consistencia
            border-radius: 3px;
            color: #d8d8d8;  # Texto gris claro (no blanco puro)
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: {style}dd;  # Más claro en hover
        }}
        QPushButton:pressed {{
            background-color: {style}aa;  # Más oscuro al presionar
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

#### Bordes y Hover Dinámicos
Los bordes y efectos hover se calculan automáticamente para crear jerarquía visual:

```python
border_color = calculate_dynamic_border(style)    # +20% brillo
hover_color = calculate_dynamic_hover(style)      # +35% brillo (gradientes) o +35% (sólidos)
```

**Jerarquía de brillo:**
- **Color base**: Color original del botón
- **Borde**: +20% más brillante que el color base
- **Hover**: +35% más brillante que el color base (más brillante que el borde)
- **Pressed**: Más oscuro para efecto de presión

**Para gradientes:**
- Mantiene la dirección y proporción del gradiente
- Hace todos los colores del gradiente más brillantes
- Hover mantiene el efecto de gradiente pero más luminoso

**Para colores sólidos:**
- Hover es un color uniforme más brillante que el borde

#### Rendimiento
- Evitar demasiados gradientes complejos
- Usar colores relacionados para mantener coherencia visual

#### Mantenimiento
- Crear funciones separadas para diferentes tipos de estilos
- Documentar identificadores de estilo usados
- Reinicio de Hiero puede ser necesario para ver cambios

### 5. Funciones de Ayuda Recomendadas

#### Funciones de Utilidad Incluidas
```python
# Conversión de colores
hex_to_rgb("#ff0000")  # -> (255, 0, 0)
rgb_to_hex((255, 0, 0))  # -> "#ff0000"

# Espacio de color HSV
rgb_to_hsv(r, g, b)  # RGB a HSV
hsv_to_rgb(h, s, v)  # HSV a RGB

# Extracción de gradientes
extract_gradient_colors("stop: 0 #color1, stop: 1 #color2")  # -> ["#color1", "#color2"]

# Cálculo de bordes y hover dinámicos
calculate_dynamic_border("#36166c")  # -> Borde +20% brillo
calculate_dynamic_border("gradient_magenta_violet")  # -> Borde basado en gradiente

calculate_dynamic_hover("#36166c")  # -> Hover +35% brillo
calculate_dynamic_hover("gradient_magenta_violet")  # -> {'inicio': color, 'fin': color}
```

#### Ejemplo de Función de Estilos
```python
def crear_estilo_gradiente(self, tipo_gradiente):
    """Crea estilos para diferentes tipos de gradientes"""
    gradientes = {
        "gradient_magenta_violet": {
            "inicio": "#5c166c", "fin": "#36166c"
        },
        "gradient_blue_green": {
            "inicio": "#1e3a8a", "fin": "#065f46"
        }
    }

    if tipo_gradiente in gradientes:
        config = gradientes[tipo_gradiente]
        border_color = calculate_dynamic_border(tipo_gradiente)
        hover_colors = calculate_dynamic_hover(tipo_gradiente)
        return f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {config['inicio']},
                    stop: 1 {config['fin']}
                );
                border: 1px solid {border_color};
                border-radius: 3px;
                color: #d8d8d8;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {hover_colors['inicio']},
                    stop: 1 {hover_colors['fin']}
                );
            }}
        """
```

## Problemas Comunes

- **Cambios no visibles**: Reiniciar Hiero completamente
- **Inconsistencias**: Verificar que todos los botones usen el nuevo sistema
- **Bordes dinámicos**: Si no se ven bien, verificar que `calculate_dynamic_border()` esté funcionando correctamente
- **Hover dinámico**: Verificar que `calculate_dynamic_hover()` retorne colores válidos
- **Gradientes hover**: Asegurarse que los gradientes mantengan buena legibilidad en hover
- **Rendimiento**: Evitar gradientes muy complejos o muchos cálculos de color
- **Colores HSV**: Verificar rangos (H: 0-360, S: 0-100, V: 0-100)

## Referencia Qt
[Qt Style Sheets - Linear Gradients](https://doc.qt.io/qtforpython-6.8/overviews/qtwidgets-stylesheet-reference.html)</contents>
</xai:function_call">Write