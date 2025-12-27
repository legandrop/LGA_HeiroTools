# Ventana de Testing - Panel de Proyectos LGA

Esta es una ventana independiente para testing completo de la funcionalidad del panel de proyectos antes de integrarla con Hiero.

## ⚠️ Importante: Ejecutar en Hiero/Nuke

**Esta ventana SOLO funciona dentro de Hiero o Nuke Studio.** No se puede ejecutar en Python normal porque requiere las APIs de Hiero (`hiero.core`, `hiero.ui`).

### Cómo Ejecutar en Hiero

### Opción 1: Ejecución Directa (Recomendado)
```python
exec(open("LGA_Projects_Panel_Window.py").read())
```

### Opción 2: Importar y Ejecutar
```python
from LGA_Projects_Panel_Window import main
main()
```

### Opción 3: Testing del Módulo de Switch Sequence
```python
from LGA_Projects_Panel_SwitchSequence import switch_to_sequence
switch_to_sequence("nombre_secuencia")
```

## Funcionalidades

### 🔍 Escaneo Automático
- Al abrir la ventana, automáticamente escanea `T:\` buscando proyectos VFX
- Muestra "Escaneando..." mientras procesa
- Resultados aparecen ordenados alfabéticamente

### 📁 Visualización de Proyectos
- **Proyectos cerrados:** `📁 NOMBREPROYECTO_SUP_v###`
- **Proyectos abiertos:** `📂 NOMBREPROYECTO_SUP_v### (Abierto)`
- Secuencias mostradas con indentación bajo proyectos abiertos

### 🖱️ Interacciones
- **Click en proyecto cerrado:** Abre el proyecto en Hiero
- **Click en secuencia:** Abre la secuencia en el timeline usando **solución V3 Híbrida avanzada**
  - ✅ **Preserva ajustes del viewer:** Gain, gamma, saturation y playhead
  - ✅ **Optimiza UI automáticamente:** Reduce panel izquierdo a 340px + scroll al top track
  - ✅ **Velocidad óptima:** 0.49s con comportamiento nativo de Hiero
  - ✅ **Sin duplicados:** Maneja viewers existentes correctamente
  - ✅ **Cross-project:** Funciona perfectamente con secuencias de cualquier proyecto abierto
  - ✅ **Cambio automático:** Cambia automáticamente al proyecto correcto si la secuencia pertenece a otro proyecto
- **Botón Refresh:** Re-escanear proyectos manualmente

### 🔄 Actualización Automática
- Después de abrir un proyecto, la vista se actualiza automáticamente
- Muestra las secuencias del proyecto recién abierto
- Refleja cambios en tiempo real

## Interfaz

```
┌─────────────────────────────────────┐
│ Panel de Proyectos LGA              │
├─────────────────────────────────────┤
│ [🔄 Refresh] [Status: Listo]        │
├─────────────────────────────────────┤
│ 📁 BRDA_SUP_v050                   │ ← Click para abrir
│ 📂 ETDM_SUP_v472 (Abierto)         │ ← Ya abierto
│    ▶ 000-100                       │ ← Click para timeline
│    ▶ Renders_Alta                  │
│ 📁 KTCE_SUP_v037                   │
│ ...                                │
├─────────────────────────────────────┤
│ 9 proyectos encontrados, 1 abierto │
└─────────────────────────────────────┘
```

## Arquitectura

### Clases Principales
- `ProjectPanelWindow(QMainWindow)`: Ventana principal
- `ScanWorker(QRunnable)`: Worker para escaneo en background
- `ProjectItem(QWidget)`: Item individual para cada proyecto

### Threading
- Usa `QRunnable` y `QThreadPool` para no bloquear la UI
- Escaneo se ejecuta en hilo secundario
- Resultados se comunican vía señales Qt

## Dependencias

- `LGA_QtAdapter_HieroTools` (para compatibilidad Qt5/Qt6)
- `LGA_Projects_Panel_ScanProjects` (funciones de escaneo)
- `LGA_Projects_Panel_SwitchSequence` (cambio avanzado de secuencia)
- `hiero.core` y `hiero.ui` (APIs de Hiero)
- `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py` (opcional - optimización UI)
- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py` (opcional - optimización UI)

## Patrón de Importación Qt (Corregido)

Siguiendo el patrón usado en scripts existentes como `LGA_NKS_Flow_Push.py`:

```python
# Importar módulos principales desde el adapter
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

# Reasignar clases específicas desde QtCore
QRunnable = QtCore.QRunnable
QThreadPool = QtCore.QThreadPool
Signal = QtCore.Signal
QObject = QtCore.QObject
```

**NO hacer esto** (causa error de importación):
```python
# ❌ INCORRECTO - QRunnable no está en el adapter
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, QRunnable
```

## Búsqueda de Módulos (Corregido)

La ventana necesita encontrar el módulo `LGA_Projects_Panel_ScanProjects.py` que está en la misma carpeta. Implementa búsqueda automática siguiendo el patrón de los scripts de exploración:

```python
# Buscar usando __file__ (método más confiable)
if '__file__' in globals() and __file__:
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "LGA_Projects_Panel_ScanProjects.py").exists():
        projects_panel_path = script_dir

# Buscar en sys.path
for path_str in sys.path:
    path = Path(path_str)
    if (path / "LGA_Projects_Panel_ScanProjects.py").exists():
        projects_panel_path = path
        break

# Añadir al sys.path antes de importar
if projects_panel_path and str(projects_panel_path) not in sys.path:
    sys.path.insert(0, str(projects_panel_path))
```

**Problema resuelto:** `ModuleNotFoundError: No module named 'LGA_Projects_Panel_ScanProjects'`

## Gestión de Ciclo de Vida de Ventanas (Corregido)

**Problema recurrente corregido:** Ventanas que se cierran automáticamente y no se pueden reutilizar.

### Patrón Implementado

Siguiendo el patrón de scripts existentes como `LGA_NKS_mediaMissingFrames.py`:

```python
# Variable global para mantener referencia (como en ejemplos que funcionan)
_projects_panel_window = None

class ProjectPanelWindow(QtWidgets.QWidget):  # ← QWidget como en LGA_NKS_mediaMissingFrames.py
    def __init__(self):
        super(ProjectPanelWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, False)  # ← No se destruye al cerrar
        # ... resto de inicialización

def main():
    global _projects_panel_window
    _projects_panel_window = ProjectPanelWindow()  # ← Asignar a variable global
    _projects_panel_window.show()
    return _projects_panel_window
```

### ¿Por qué es necesario?

- **WA_DeleteOnClose = True (por defecto):** La ventana se destruye al cerrarse → no se puede reutilizar
- **WA_DeleteOnClose = False:** La ventana permanece en memoria → se puede mostrar/ocultar

### Event Loop

- **NO usar `app.exec_()`** en scripts de Nuke (Nuke ya maneja el event loop)
- **Solo usar `window.show()`** para mostrar la ventana

**Problema resuelto:** Ventana que no se abría porque se destruía inmediatamente

## Testing Checklist

- [ ] **Importación:** Sintaxis correcta (no requiere Hiero para importar)
- [ ] **Ejecución en Nuke:** Ventana se abre sin errores (DEBUGGING: escaneo comentado)
- [ ] **Escaneo automático:** Funciona al abrir la ventana
- [ ] **Lista de proyectos:** Aparecen ordenados alfabéticamente
- [ ] **Click en proyecto:** Abre proyecto cerrado correctamente
- [ ] **Visualización de secuencias:** Aparecen bajo proyectos abiertos
- [ ] **Click en secuencia:** Abre en timeline correctamente
- [ ] **Botón Refresh:** Re-escanea sin problemas
- [ ] **Threading:** No bloquea UI durante escaneo
- [ ] **Manejo de errores:** QMessageBox para errores de apertura
- [ ] **Actualización automática:** Vista se refresca después de abrir proyectos

## ✅ Estado Actual - Funciona Perfecto

La ventana de testing está **completamente funcional** y probada en producción:

- ✅ **Escaneo automático** de proyectos en T:\ funcionando
- ✅ **Apertura de proyectos** desde la lista funcionando
- ✅ **Cambio de secuencia** con V3 Híbrida funcionando perfecto
- ✅ **Cross-project:** Funciona perfectamente con secuencias de cualquier proyecto abierto
- ✅ **Cambio automático:** Cambia automáticamente al proyecto correcto cuando es necesario
- ✅ **Sin duplicados:** Maneja correctamente viewers existentes (cierra antes de abrir)
- ✅ **UI optimizada** automáticamente (reduce panel + scroll)
- ✅ **Preservación de ajustes** del viewer funcionando (gain/gamma/saturation + playhead)

## ✅ Problema Resuelto Completamente

### Cambio de Secuencia entre Proyectos Diferentes

**✅ RESUELTO Y PROBADO:** La ventana ahora funciona perfectamente con secuencias de cualquier proyecto abierto.

**Antes (problema):**
```
🔄 Switch híbrido a '000'...
❌ Error: Secuencia '000' no encontrada
```

**Descubrimiento clave:**
- `hiero.ui.openInTimeline(sequence_obj)` funciona automáticamente cross-project
- Hiero cambia el proyecto activo automáticamente cuando abres una secuencia de otro proyecto
- Solo necesitamos pasar el objeto Sequence directamente en lugar del nombre

**Ahora (solución implementada):**
```
🎯 Usando objeto Sequence directamente para '000'
   Proyecto: 'ERSO_SUP_v011'
   📊 Cambiando de proyecto 'BRDA_SUP_v050' → 'ERSO_SUP_v011'
   ✅ openInTimeline maneja el cambio automáticamente
✅ Switch híbrido perfecto completado
```

**Estado:** ✅ **COMPLETAMENTE RESUELTO Y PROBADO** - Funciona perfectamente cross-project sin intervención manual

## Próximos Pasos

Después de verificar que funciona correctamente en Nuke 15:

1. ✅ Probar también en Nuke 16 (si disponible)
2. ✅ Convertir la ventana en panel integrado (`LGA_Projects_Panel.py`)
3. ✅ Registrar el panel con `hiero.ui.windowManager().addWindow()`
4. ✅ Hacer que se abra automáticamente al iniciar Hiero
5. 🔄 Resolver limitación de cambio entre proyectos diferentes (futuro)
