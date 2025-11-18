# LGA_NKS_FrameNumber

## Objetivo

Este script posiciona un elemento de texto (box) en el viewer de Hiero. El elemento debe estar en un track llamado "BurnIn" y debe llamarse "Frame_Only". El script puede funcionar en dos modos:

- **Modo Absoluto**: La posición del box se calcula basándose en las dimensiones completas de la imagen, sin importar el nivel de zoom o pan del viewer.
- **Modo Relativo**: La posición del box se calcula basándose en el área visible del viewer, considerando el zoom y el pan. El box se posiciona a 30px del borde izquierdo y a 30px del bottom del área visible.

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

## Obtención del Pan del Viewer

El script usa `player.translation()` para obtener el pan del viewer. Este método devuelve un `QPointF` con el offset X e Y del área visible:

```python
player = viewer.player()
translation = player.translation()  # Devuelve QPointF(x, y)
pan_x = translation.x()  # Offset X del área visible
pan_y = translation.y()  # Offset Y del área visible
```

### Funcionamiento Actual

- ✅ Obtener el zoom del player: `player.zoom()` funciona correctamente
- ✅ Obtener el pan del viewer: `player.translation()` devuelve el pan como `QPointF`
- ✅ Calcular el área visible basándose en el zoom, aspect ratio y pan
- ✅ Posicionar el box correctamente en modo relativo en ambos ejes (X e Y)
- ✅ El cálculo de X e Y es consistente: ambos usan el mismo método limpio sin correcciones especiales

### ⚠️ Limitaciones Conocidas

- **Aspect ratio del viewer**: Cuando el viewer tiene una proporción muy diferente a la imagen (más ancho o más alto), puede haber pequeñas inconsistencias en los márgenes. El comportamiento es funcional pero puede variar ligeramente según la proporción del viewer.

## Implementación Técnica

El script calcula el área visible del viewer usando:

- **Zoom**: `player.zoom()` - factor de escala del viewer
- **Pan**: `player.translation()` - devuelve `QPointF(x, y)` con el offset del área visible
- **Aspect ratio**: Compara el aspect ratio del viewer con el de la imagen para determinar qué dimensión limita el área visible

El cálculo de posición es consistente para ambos ejes (X e Y): se calcula el centro visible restando el pan del centro de la imagen, y luego se obtiene el offset restando la mitad de las dimensiones visibles.

**Archivo principal**: `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber.py`  
**Función principal**: `print_box_values()`
