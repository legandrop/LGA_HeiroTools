# Panel de Proyectos LGA - Documentación

## Concepto

Panel personalizado `com.lega.ProjectPanel` que escanea proyectos VFX en disco T:, muestra la última versión de cada proyecto encontrado, y permite abrir proyectos y sus secuencias directamente desde el panel.

**Título visible del panel:** `Project`

## Funcionalidad

### Escaneo de Proyectos
- Escanea `T:\` buscando carpetas que empiecen con `VFX-`
- Para cada carpeta encontrada, busca subcarpeta `*_SUP` (ejemplo: `T:\VFX-LC\LC_SUP`)
- En cada carpeta SUP, encuentra el archivo `.hrox` con la versión más alta
- Muestra proyectos con formato: `NOMBREPROYECTO_SUP_v###` (ejemplo: `ETDM_SUP_v472`)

### Visualización
- **Proyectos no abiertos:** Solo se muestra el nombre del proyecto con su versión
- **Proyectos abiertos:** Se muestra el nombre del proyecto y debajo (con indentación) todas sus secuencias:
  ```
  ETDM_SUP_v472
    000-100
    Renders_Alta
  LC_SUP_v32
  PHLDA_SUP_v21
    011-020
  ```

### Interacción
- **Click en proyecto no abierto:** Abre el proyecto en Hiero y actualiza la vista mostrando sus secuencias
- **Click en secuencia:** Abre la secuencia en el timeline de Hiero (usando `hiero.ui.openInTimeline()`)

### Escaneo
- Escaneo automático al abrir el panel
- Botón "Refresh" para re-escanear manualmente
- Escaneo en background usando threads (no bloquea la UI)
- Muestra "Scanning..." mientras escanea

## Estructura de Carpetas Esperada

```
T:\
  VFX-NOMBREPROYECTO1\
    NOMBREPROYECTO1_SUP\
      proyecto_v001.hrox
      proyecto_v002.hrox
      proyecto_v003.hrox  ← Última versión detectada
  VFX-NOMBREPROYECTO2\
    NOMBREPROYECTO2_SUP\
      proyecto_v021.hrox
      proyecto_v022.hrox  ← Última versión detectada
```

## Compatibilidad Qt (Nuke 15/16)

**IMPORTANTE:** **TODOS** los scripts (tanto de exploración como finales) deben usar `LGA_QtAdapter_HieroTools` para compatibilidad entre Nuke 15 (PySide2) y Nuke 16 (PySide6).

**Esto aplica a:**
- ✅ Scripts de exploración en `exploracion/`
- ✅ Scripts finales del panel
- ✅ Cualquier script que use Qt en este proyecto

### Imports Correctos
```python
# ✅ CORRECTO - Usar QtAdapter SIEMPRE
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, QApplication
from LGA_QtAdapter_HieroTools import QRunnable, QThreadPool, Signal, QObject

# ❌ INCORRECTO - NUNCA importar directamente
# from PySide2 import QtWidgets  # NO HACER ESTO
# from PySide6 import QtWidgets  # NO HACER ESTO
```

### Funciones Helper Disponibles
- `horizontal_advance(metrics, text)` - Ancho de texto compatible Qt5/Qt6
- `primary_screen_geometry(pos)` - Geometría de pantalla con multi-monitor
- `set_layout_margin(layout, margin)` - Márgenes de layout compatibles

### Referencias
- [`LGA_QtAdapter_HieroTools.py`](../LGA_QtAdapter_HieroTools.py) - Adaptador Qt para Hiero
- [`c:\Users\leg4-pc\.nuke\Docu_LGA_QtAdapter.md`](../../Docu_LGA_QtAdapter.md) - Documentación completa del sistema QtAdapter

### Testing
- Los scripts de exploración se ejecutarán primero en **Nuke 15** para obtener resultados
- Al final se verificará también en **Nuke 16**
- Todos los scripts deben funcionar en ambas versiones gracias al QtAdapter

## Referencias a Código Existente

### Detección y Manejo de Versiones
- **[`LGA_NKS/LGA_NKS_CheckProjectVersions.py`](../LGA_NKS/LGA_NKS_CheckProjectVersions.py)**
  - `extraer_version(ruta_disco)` (líneas 36-61) - Extrae número de versión de ruta de archivo
  - `comparar_versiones(version1, version2)` (líneas 64-85) - Compara dos versiones y devuelve la mayor
  - `encontrar_version_mas_alta(ruta_actual)` (líneas 88-148) - Encuentra archivo con versión más alta en carpeta
  - `obtener_nombre_base_proyecto(ruta)` (líneas 639-652) - Extrae nombre base sin versión ni extensión

### Detección de Proyectos Abiertos
- **[`LGA_NKS/LGA_NKS_CheckProjectVersions.py`](../LGA_NKS/LGA_NKS_CheckProjectVersions.py)**
  - Lógica para detectar proyectos abiertos (líneas 326-348):
    ```python
    proyectos_abiertos_por_base = {}
    for proyecto in hiero.core.projects():
        ruta_disco = proyecto.path()
        nombre_base = obtener_nombre_base_proyecto(ruta_disco)
        # Agrupar por nombre base y comparar versiones
    ```
  - Comparación por nombre base + versión para determinar si proyecto ya está abierto (líneas 394-403)

### Apertura de Proyectos
- **[`LGA_NKS/LGA_NKS_CheckProjectVersions.py`](../LGA_NKS/LGA_NKS_CheckProjectVersions.py)**
  - `hiero.core.openProject(ruta_nueva_version)` (línea 509) - Abre proyecto desde ruta de archivo

### Obtención de Secuencias
- **[`+Building_Blocks/Hiero/Bin/LGA_H-Bin-Print_Only_Sequences.py`](../+Building_Blocks/Hiero/Bin/LGA_H-Bin-Print_Only_Sequences.py)**
  - `find_sequences(bin_item)` (líneas 25-41) - Busca recursivamente todas las secuencias en un Bin
  - `list_sequences_in_project(project)` (líneas 3-23) - Lista todas las secuencias de un proyecto

### Apertura de Secuencias
- **[`+Building_Blocks/Hiero/Viewer/LGA_Abrir_Nuevo_CompTimelineViewers.py`](../+Building_Blocks/Hiero/Viewer/LGA_Abrir_Nuevo_CompTimelineViewers.py)**
  - `find_sequence_by_name(project, sequence_name)` (líneas 4-26) - Busca secuencia por nombre en proyecto
  - `hiero.ui.openInTimeline(sequence)` (línea 54) - Abre secuencia en timeline

### Threading y Operaciones en Background
- **[`LGA_NKS_Hilos_Hiero.md`](../LGA_NKS_Hilos_Hiero.md)**
  - Patrón completo para usar `QRunnable` y `QThreadPool` sin bloquear el hilo principal
  - Ejemplo de `WorkerSignals(QObject)` con señales `result_ready` y `error`
  - Ejemplo de `Worker(QRunnable)` para operaciones pesadas

### Ejemplos de Workers Existentes
- **[`LGA_NKS_Flow/LGA_NKS_Flow_Push.py`](../LGA_NKS_Flow/LGA_NKS_Flow_Push.py)**
  - Clase `WorkerSignals` (líneas 1343-1350) - Señales para comunicación
  - Clase `Worker(QRunnable)` (líneas 1353+) - Worker para operaciones en background
- **[`LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShowInFlow.py`](../LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShowInFlow.py)**
  - Ejemplo de worker con señales y uso de `QThreadPool.globalInstance().start(worker)`

## Estructura de Archivos del Proyecto

Todos los archivos irán en `LGA_Projects_Panel/`:

1. **`LGA_Projects_Panel.md`** (este archivo)
   - Documentación del concepto y referencias

2. **`exploracion/`** (subcarpeta)
   - Scripts de exploración para entender la estructura y APIs
   - Se ejecutan en Hiero para obtener información sobre nombres de funciones, métodos, etc.
   - Los resultados se comparten para escribir el código final correctamente
   - **Todos usan `LGA_QtAdapter_HieroTools`** para compatibilidad Qt
   - Ejemplos:
     - `LGA_Projects_Panel_Explorer_01_ScanDisk.py` - Explora estructura de T:\
     - `LGA_Projects_Panel_Explorer_02_OpenProjects.py` - Explora proyectos abiertos
     - `LGA_Projects_Panel_Explorer_03_Sequences.py` - Explora secuencias

3. **`LGA_Projects_Panel_ScanProjects.py`**
   - Módulo con funciones reutilizables para escanear proyectos
   - Funciones para detectar proyectos abiertos
   - Funciones para obtener secuencias de proyectos
   - **Usa `LGA_QtAdapter_HieroTools`** para compatibilidad Qt

4. **`LGA_Projects_Panel_Window.py`**
   - Ventana independiente (`QMainWindow`) para testing
   - Implementación completa de funcionalidad antes de convertir a panel
   - Más fácil de testear ejecutando el script directamente
   - **Usa `LGA_QtAdapter_HieroTools`** para compatibilidad Qt

5. **`LGA_Projects_Panel.py`**
   - Panel final integrado con Hiero
   - Hereda de `QWidget` en lugar de `QMainWindow`
   - Se registra con `hiero.ui.windowManager().addWindow()`
   - Se abre automáticamente al iniciar Hiero
   - **Usa `LGA_QtAdapter_HieroTools`** para compatibilidad Qt

## Orden de Implementación

1. ✅ **Crear MD con documentación** (este archivo)
2. ✅ **Crear subcarpeta `exploracion/` y scripts de exploración**
3. ✅ **Ejecutar Exploración 01: Escaneo de Disco T:** - COMPLETADO
   - Ver [`exploracion/AVANCES_Y_DESCUBRIMIENTOS.md`](exploracion/AVANCES_Y_DESCUBRIMIENTOS.md) para detalles
4. ✅ **Ejecutar Exploración 02: Proyectos Abiertos** - COMPLETADO
5. ✅ **Ejecutar Exploración 03: Secuencias** - COMPLETADO
6. ✅ **Crear módulo de escaneo** (`LGA_Projects_Panel_ScanProjects.py`) - COMPLETADO
   - Módulo con 4 funciones reutilizables listas para usar
7. ✅ **Crear ventana de testing** (`LGA_Projects_Panel_Window.py`) - COMPLETADO
   - QMainWindow independiente con funcionalidad completa
   - Worker de escaneo en background, UI completa, interacciones
   - Patrón de importaciones corregido siguiendo scripts existentes
8. 🔄 Probar ventana exhaustivamente en Nuke 15 - SIGUIENTE
9. Convertir ventana en panel (`LGA_Projects_Panel.py`)
10. Probar panel integrado en Nuke 15 y Nuke 16

## Documentación de Avances

Ver [`exploracion/AVANCES_Y_DESCUBRIMIENTOS.md`](exploracion/AVANCES_Y_DESCUBRIMIENTOS.md) para:
- Descubrimientos de cada exploración
- Decisiones técnicas tomadas
- Próximos pasos
- Preguntas abiertas

## Notas de Implementación

### Detección de Proyectos Abiertos
- Usar `proyecto.path()` para obtener ruta completa del archivo `.hrox`
- Comparar por nombre base (sin versión) + número de versión
- Un proyecto está abierto si su nombre base y versión coinciden con uno en `hiero.core.projects()`

### Escaneo en Background
- Usar patrón `QRunnable` + `QThreadPool` de `LGA_NKS_Hilos_Hiero.md`
- NO usar `thread.join()` - bloquea el hilo principal
- Obtener datos de Hiero en el hilo principal ANTES del worker
- Usar señales para comunicar resultados al hilo principal

### Compatibilidad Qt
- **SIEMPRE** importar desde `LGA_QtAdapter_HieroTools` en TODOS los scripts (exploración y finales)
- **NUNCA** importar directamente de `PySide2` o `PySide6`
- Usar funciones helper cuando sea necesario (`set_layout_margin`, etc.)
- Los scripts de exploración también deben usar el QtAdapter aunque no usen Qt directamente (para mantener consistencia)

### Visualización de Secuencias
- Solo mostrar secuencias de proyectos que están abiertos
- Usar indentación visual para mostrar jerarquía proyecto → secuencias
- Actualizar vista automáticamente cuando se abre un proyecto

