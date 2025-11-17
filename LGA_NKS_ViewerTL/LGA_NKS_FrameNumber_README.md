# LGA_NKS_FrameNumber

## Objetivo

Este script posiciona un elemento de texto (box) en el viewer de Hiero. El elemento debe estar en un track llamado "BurnIn" y debe llamarse "Frame_Only". El script puede funcionar en dos modos:

- **Modo Absoluto**: La posición del box se calcula basándose en las dimensiones completas de la imagen, sin importar el nivel de zoom o pan del viewer.
- **Modo Relativo**: La posición del box se calcula basándose en el área visible del viewer, considerando el zoom y el pan. El box se posiciona a 30px del borde izquierdo del área visible y centrado verticalmente.

## Configuración

Al inicio del script hay dos flags principales:

```python
TRACK_NAME = "BurnIn"
CLIP_NAME = "Frame_Only"
DEBUG = True  # Activar para ver información de depuración

# Modo de posicionamiento:
# True = Absoluto: posición basada en las dimensiones completas de la imagen (sin importar zoom/pan)
# False = Relativo: posición basada en el área visible del viewer (considera zoom y pan)
USE_ABSOLUTE_POSITION = False
```

## Problema Actual

### ✅ SOLUCIÓN ENCONTRADA: `player.translation()`

**El problema ha sido resuelto**. Se encontró que `player.translation()` devuelve un `QPointF` con el pan (offset X e Y) del viewer.

**Uso**:
```python
player = viewer.player()
translation = player.translation()  # Devuelve QPointF(x, y)
pan_x = translation.x()  # Offset X del área visible
pan_y = translation.y()  # Offset Y del área visible
```

### Lo que funciona ahora

- ✅ Obtener el zoom del player: `player.zoom()` funciona correctamente
- ✅ Obtener el pan del viewer: `player.translation()` devuelve el pan como `QPointF`
- ✅ Calcular el área visible basándose en el zoom, aspect ratio y pan
- ✅ Posicionar el box correctamente en modo relativo considerando el pan
- ✅ Validar que el box no se salga de los límites de la imagen

### Historia del Problema (Resuelto)

Inicialmente, el script no podía obtener el pan del viewer y siempre asumía que el área visible estaba centrada. Después de múltiples exploraciones exhaustivas, se descubrió que `player.translation()` es el método correcto para obtener el pan.

## Scripts Auxiliares de Exploración

Se crearon múltiples scripts auxiliares para investigar cómo obtener el pan del viewer. La mayoría fueron eliminados después de encontrar la solución, quedando solo:

### LGA_Test_Translation.py

**Ubicación**: `+Building_Blocks/Hiero/Viewer/LGA_Test_Translation.py`

**Objetivo**: Prueba específicamente el método `player.translation()` que resultó ser la solución.

**Resultado**: ✅ **ÉXITO** - `player.translation()` devuelve un `QPointF` con el pan (offset X e Y) del viewer.

**Nota**: Los demás scripts de exploración fueron eliminados después de encontrar la solución, ya que su propósito era investigar y ya no son necesarios.

## Análisis de los Resultados

Después de múltiples exploraciones exhaustivas, se encontró que **`player.translation()` es el método correcto para obtener el pan del viewer**.

### Hallazgos Clave

1. **`player.pan()` es solo un setter**: Acepta parámetros pero devuelve `None`, confirmando que es solo para establecer el pan, no para obtenerlo.

2. **`player.translation()` es el getter correcto**: 
   - Devuelve un `QPointF` con las coordenadas del pan (offset X e Y)
   - Es un built-in method sin signature accesible, pero funciona llamándolo sin parámetros
   - Ejemplo: `translation = player.translation()` devuelve `QPointF(x, y)`

3. **El pan está disponible en la API pública**: Aunque no estaba documentado, el método `translation()` expone el pan del viewer.

4. **Los widgets internos no son necesarios**: No necesitamos acceder a widgets internos (QGLWidget, QGraphicsView, etc.) ya que el player expone el pan directamente.

## Conclusión

**✅ SOLUCIÓN ENCONTRADA**: `player.translation()` devuelve el pan del viewer como `QPointF(x, y)`, permitiendo calcular correctamente el área visible del viewer en modo relativo.

### Implementación

```python
# Obtener el pan del viewer
player = viewer.player()
translation = player.translation()  # QPointF
pan_x = translation.x()  # Offset X del área visible
pan_y = translation.y()  # Offset Y del área visible

# Calcular el área visible
zoom = player.zoom()
viewer_width = viewer.image().width()
viewer_height = viewer.image().height()

visible_width = viewer_width / zoom
visible_height = viewer_height / zoom

visible_x = pan_x
visible_y = pan_y
```

## Scripts de Exploración

Durante la exploración se crearon múltiples scripts, pero la mayoría fueron eliminados después de encontrar la solución. El único script que se mantiene es:

### LGA_Test_Translation.py

**Ubicación**: `+Building_Blocks/Hiero/Viewer/LGA_Test_Translation.py`

**Objetivo**: Prueba específicamente el método `player.translation()` que resultó ser la solución.

**Resultado**: ✅ **ÉXITO** - `player.translation()` devuelve un `QPointF` con el pan (offset X e Y) del viewer.

**Ejemplo de uso**:
```python
player = viewer.player()
translation = player.translation()  # QPointF(x, y)
pan_x = translation.x()  # Offset X
pan_y = translation.y()  # Offset Y
```

**Nota**: Los demás scripts de exploración (LGA_Explorar_*, LGA_Test_*) fueron eliminados después de encontrar la solución, ya que su propósito era investigar y ya no son necesarios.

## Versión

v0.53 - Solución encontrada: `player.translation()` devuelve el pan del viewer

## Autor

Lega

