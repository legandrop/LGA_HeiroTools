# Avances y Descubrimientos - Panel de Proyectos LGA

Este documento registra los descubrimientos de los scripts de exploración y los próximos pasos.

---

## Exploración 01: Escaneo de Disco T: ✅ COMPLETADO

**Fecha:** Ejecutado en Nuke 15  
**Script:** `LGA_Projects_Panel_Explorer_01_ScanDisk.py`

### Descubrimientos Importantes

#### 1. Importación de Módulos
- ✅ **Funciona:** El script encontró correctamente `LGA_NKS_CheckProjectVersions.py` en `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS`
- ✅ **Método exitoso:** Buscar el archivo directamente en `sys.path` funciona mejor que asumir estructura de carpetas
- ✅ **Funciones importadas:** `extraer_version()`, `comparar_versiones()`, `encontrar_version_mas_alta()`, `obtener_nombre_base_proyecto()` funcionan correctamente

#### 2. Estructura de Carpetas
- ✅ **Patrón confirmado:** `T:\VFX-NOMBREPROYECTO\NOMBREPROYECTO_SUP\`
- ✅ **Total encontrado:** 11 carpetas `VFX-*`, de las cuales 9 tienen carpetas `*_SUP` válidas
- ✅ **Proyectos sin SUP:** `VFX-EHQALPV` y `VFX-TOC` no tienen carpetas `*_SUP` (se ignoran)

#### 3. Archivos .hrox y Versiones
- ✅ **Formato estándar:** `NOMBREPROYECTO_SUP_v###.hrox` funciona correctamente
- ✅ **Extracción de versión:** Las funciones extraen correctamente versiones como `v001`, `v050`, `v472`, etc.
- ⚠️ **Caso especial detectado:** `YM_SUP_Plates&Charts_2.hrox` tiene formato diferente:
  - No sigue el patrón `NOMBRE_v###.hrox`
  - Tiene formato `NOMBRE_Descripcion_#.hrox`
  - La función `extraer_version()` lo detecta como `v2` (correcto)
  - **Acción:** Verificar si este caso necesita manejo especial o si está bien así

#### 4. Rangos de Versiones Encontrados
- `BRDA_SUP`: v001 a v050 (29 archivos)
- `ERSO_SUP`: v001 a v011 (11 archivos)
- `ETDM_SUP`: v200 a v472 (134 archivos) - **Proyecto grande**
- `KTCE_SUP`: v037 (última versión)
- `LC_SUP`: v30 (última versión) - **Nota:** versión sin ceros a la izquierda
- `MOR_SUP`: v010 (última versión)
- `PHLDA_SUP`: v086 (última versión)
- `VLLF_SUP`: v039 (última versión)
- `YM_SUP`: v2 (caso especial con formato diferente)

#### 5. Funciones de Extracción de Versión
- ✅ `extraer_version()` funciona correctamente con todos los formatos encontrados
- ✅ `comparar_versiones()` maneja correctamente versiones con y sin ceros a la izquierda
- ✅ `encontrar_version_mas_alta()` encuentra correctamente la versión más alta en cada carpeta
- ✅ `obtener_nombre_base_proyecto()` extrae correctamente el nombre base sin versión

### Resumen de Proyectos Válidos Encontrados

| Proyecto | Carpeta VFX | Versión | Archivo .hrox | Ruta Completa |
|----------|-------------|---------|---------------|---------------|
| BRDA_SUP | VFX-BRDA | v050 | BRDA_SUP_v050.hrox | T:\VFX-BRDA\BRDA_SUP\BRDA_SUP_v050.hrox |
| ERSO_SUP | VFX-ERSO | v011 | ERSO_SUP_v011.hrox | T:\VFX-ERSO\ERSO_SUP\ERSO_SUP_v011.hrox |
| ETDM_SUP | VFX-ETDM | v472 | ETDM_SUP_v472.hrox | T:\VFX-ETDM\ETDM_SUP\ETDM_SUP_v472.hrox |
| KTCE_SUP | VFX-KTCE | v037 | KTCE_SUP_v037.hrox | T:\VFX-KTCE\KTCE_SUP\KTCE_SUP_v037.hrox |
| LC_SUP | VFX-LC | v30 | LC_SUP_v30.hrox | T:\VFX-LC\LC_SUP\LC_SUP_v30.hrox |
| MOR_SUP | VFX-MOR | v010 | MOR_SUP_v010.hrox | T:\VFX-MOR\MOR_SUP\MOR_SUP_v010.hrox |
| PHLDA_SUP | VFX-PHLDA | v086 | PHLDA_SUP_v086.hrox | T:\VFX-PHLDA\PHLDA_SUP\PHLDA_SUP_v086.hrox |
| VLLF_SUP | VFX-VLLF | v039 | VLLF_SUP_v039.hrox | T:\VFX-VLLF\VLLF_SUP\VLLF_SUP_v039.hrox |
| YM_SUP | VFX-YM | v2 | YM_SUP_Plates&Charts_2.hrox | T:\VFX-YM\YM_SUP\YM_SUP_Plates&Charts_2.hrox |

### Decisiones Tomadas

1. ✅ **Usar funciones existentes:** Las funciones de `LGA_NKS_CheckProjectVersions.py` funcionan perfectamente, no necesitamos reescribirlas
2. ✅ **Estructura de datos:** Usar diccionarios con estructura:
   ```python
   {
       "nombre_base": "BRDA_SUP",
       "vfx_folder": "VFX-BRDA",
       "sup_folder": "BRDA_SUP",
       "ruta_hrox": "T:\\VFX-BRDA\\BRDA_SUP\\BRDA_SUP_v050.hrox",
       "version": "v050",
       "ruta_proyecto": "T:\\VFX-BRDA\\BRDA_SUP"
   }
   ```
3. ⚠️ **Caso especial YM_SUP:** Monitorear si causa problemas, por ahora las funciones lo manejan correctamente

---

## Exploración 02: Proyectos Abiertos en Hiero ✅ COMPLETADO

**Fecha:** Ejecutado en Nuke 15  
**Script:** `LGA_Projects_Panel_Explorer_02_OpenProjects.py`

### Descubrimientos Importantes

#### 1. Obtener Proyectos Abiertos
- ✅ **Funciona:** `hiero.core.projects()` retorna lista de proyectos abiertos
- ✅ **Resultado:** En el test había 1 proyecto abierto (`LC_SUP_v30`)

#### 2. Información de Proyectos
- ✅ **proyecto.name():** Retorna nombre del proyecto (ej: `LC_SUP_v30`)
- ✅ **proyecto.path():** Retorna ruta completa del archivo .hrox (ej: `T:/VFX-LC/LC_SUP/LC_SUP_v30.hrox`)
- ✅ **Nota importante:** Las rutas usan barras `/` en lugar de `\` cuando vienen de `proyecto.path()`
- ✅ **Métodos disponibles:** 100+ métodos disponibles en objeto proyecto, incluyendo:
  - `name()`, `path()`, `clipsBin()`, `sequences()`, `close()`, `save()`

#### 3. Extracción de Información
- ✅ **obtener_nombre_base_proyecto():** Funciona correctamente con rutas de proyectos abiertos
- ✅ **extraer_version():** Funciona correctamente (ej: `v30` de `LC_SUP_v30.hrox`)
- ✅ **Comparación numérica:** Versión `v30` se convierte correctamente a número `30`

#### 4. Comparación con Proyectos del Disco
- ✅ **Función de verificación:** La función `is_project_open()` funciona correctamente
- ✅ **Lógica confirmada:** Comparar por nombre base + número de versión es correcto
- ✅ **Resultado del test:** 
  - `BRDA_SUP_v050` → NO está abierto ✓
  - `ETDM_SUP_v472` → NO está abierto ✓
  - `LC_SUP_v30` → ESTÁ ABIERTO ✓

#### 5. Agrupación por Nombre Base
- ✅ **Estructura confirmada:** Agrupar proyectos abiertos por nombre base funciona como en `CheckProjectVersions`
- ✅ **Formato de datos:** Diccionario con estructura:
  ```python
  {
      "proyecto": proyecto_obj,
      "ruta": "T:/VFX-LC/LC_SUP/LC_SUP_v30.hrox",
      "version_num": 30,
      "version_str": "v30",
      "nombre": "LC_SUP_v30"
  }
  ```

### Decisiones Tomadas

1. ✅ **Usar `hiero.core.projects()`:** Método estándar para obtener proyectos abiertos
2. ✅ **Comparación robusta:** Usar nombre base + número de versión para comparar
3. ✅ **Normalizar rutas:** Las rutas de `proyecto.path()` usan `/`, las del disco usan `\` - las funciones manejan ambos formatos correctamente
4. ✅ **Función de verificación:** La función `is_project_open()` está lista para usar en el código final

---

## Próximos Pasos

### Exploración 03: Secuencias de Proyectos ✅ COMPLETADO

**Fecha:** Ejecutado en Nuke 15  
**Script:** `LGA_Projects_Panel_Explorer_03_Sequences.py`

**Descubrimientos:**
- ✅ **3 métodos funcionan:** `proyecto.sequences()`, `hiero.core.findItems()`, `find_sequences(clipsBin())`
- ✅ **Método recomendado:** `proyecto.sequences()` es el más simple y directo
- ✅ **Estructura:** BinItem contiene Sequence, usar `activeItem()` para obtener Sequence real
- ✅ **Nombres:** `sequence.name()` retorna nombres correctamente (ej: `'104'`, `'101'`, `'000'`)
- ✅ **Búsqueda:** `find_sequence_by_name()` funciona para buscar por nombre
- ✅ **Apertura:** `hiero.ui.openInTimeline(sequence)` disponible para abrir secuencias
- ✅ **Test exitoso:** Proyecto LC_SUP_v30 tiene 3 secuencias, todas detectadas correctamente

**Función recomendada:**
```python
def get_project_sequences(proyecto):
    sequences = proyecto.sequences()
    return [seq.name() for seq in sequences if hasattr(seq, 'name')]
```

### Módulo de Escaneo ✅ COMPLETADO
**Objetivo:** Crear módulo reutilizable `LGA_Projects_Panel_ScanProjects.py`

**Archivo creado:** `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py`

**Funciones implementadas:**

1. ✅ **`scan_projects_on_disk(base_path="T:\\")`**
   - Basada en Exploración 01
   - Escanea T:\ buscando carpetas VFX-*
   - Encuentra carpetas *_SUP y archivos .hrox
   - Encuentra versión más alta usando `encontrar_version_mas_alta()`
   - Retorna lista de diccionarios con información completa de proyectos

2. ✅ **`get_open_projects_info()`**
   - Basada en Exploración 02
   - Usa `hiero.core.projects()` para obtener proyectos abiertos
   - Agrupa por nombre base usando `obtener_nombre_base_proyecto()`
   - Extrae versiones usando `extraer_version()`
   - Retorna diccionario estructurado por nombre base

3. ✅ **`is_project_open(ruta_hrox, proyectos_abiertos_info)`**
   - Basada en Exploración 02
   - Compara proyecto del disco con proyectos abiertos
   - Compara por nombre base + número de versión
   - Retorna True/False

4. ✅ **`get_project_sequences(proyecto)`**
   - Basada en Exploración 03
   - Usa `proyecto.sequences()` (método más simple)
   - Retorna lista de nombres de secuencias (strings)

**Características:**
- ✅ Usa `LGA_QtAdapter_HieroTools` para compatibilidad Qt (aunque este módulo no usa Qt directamente)
- ✅ Reutiliza funciones de `LGA_NKS_CheckProjectVersions.py`
- ✅ Manejo robusto de errores (try/except en funciones críticas)
- ✅ Documentación completa de cada función
- ✅ Búsqueda automática del módulo LGA_NKS en sys.path

**Nota:** Este módulo NO hace nada al ejecutarse directamente. Solo define funciones que deben ser importadas y usadas por otros scripts (ventana de testing, panel final, etc.)

---

## Ventana de Testing ✅ COMPLETADO

**Fecha:** Implementado y listo para testing en Nuke 15
**Archivo creado:** `LGA_Projects_Panel/LGA_Projects_Panel_Window.py`

### Funcionalidades Implementadas

#### 1. ✅ Arquitectura QMainWindow Independiente
- Ventana independiente que NO depende del sistema de paneles de Hiero
- Fácil de testear ejecutando directamente: `exec(open("LGA_Projects_Panel_Window.py").read())`
- Usa `LGA_QtAdapter_HieroTools` para compatibilidad Qt5/Qt6

#### 2. ✅ Worker de Escaneo en Background
- `ScanWorker(QRunnable)` para escaneo sin bloquear UI
- Usa patrón `WorkerSignals` con señales `scan_finished` y `error`
- Se ejecuta en `QThreadPool.globalInstance()` sin bloquear hilo principal

#### 3. ✅ Interfaz de Usuario Completa
- Lista scrollable de proyectos encontrados
- `ProjectItem` personalizado para cada proyecto con visualización jerárquica
- Botón "Refresh" para re-escanear manualmente
- Indicador de estado (Escaneando/Listo/Error)
- Información de resumen (total proyectos, proyectos abiertos)

#### 4. ✅ Visualización de Estado de Proyectos
- **Proyectos cerrados:** `📁 NOMBREPROYECTO_SUP_v###` (azul)
- **Proyectos abiertos:** `📂 NOMBREPROYECTO_SUP_v### (Abierto)` (verde)
- Secuencias mostradas con indentación visual bajo proyectos abiertos
- Secuencias con icono `▶` y color púrpura

#### 5. ✅ Interacción Completa
- **Click en proyecto cerrado:** Abre proyecto en Hiero y actualiza vista
- **Click en secuencia:** Abre secuencia en timeline usando `hiero.ui.openInTimeline()`
- **Botón Refresh:** Re-escanear proyectos en cualquier momento
- Escaneo automático al abrir la ventana

#### 6. ✅ Manejo Robusto de Estados
- Actualización automática de vista después de abrir proyectos
- Manejo de errores con `QMessageBox` para usuario
- Estado consistente entre múltiples operaciones
- Limpieza apropiada al cerrar ventana

#### 7. ✅ Patrón de Importación Qt Corregido
- **Error corregido:** `ImportError: cannot import name 'QRunnable'`
- **Solución:** Seguir patrón de `LGA_NKS_Flow_Push.py`
- **Método correcto:**
  ```python
  # Importar módulos principales desde adapter
  from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

  # Reasignar clases específicas desde QtCore
  QRunnable = QtCore.QRunnable
  QThreadPool = QtCore.QThreadPool
  Signal = QtCore.Signal
  QObject = QtCore.QObject
  ```
- **Método incorrecto (evitado):**
  ```python
  # ❌ NO HACER - QRunnable no está exportado por el adapter
  from LGA_QtAdapter_HieroTools import QRunnable
  ```

#### 8. ✅ Búsqueda Automática de Módulos
- **Error corregido:** `ModuleNotFoundError: No module named 'LGA_Projects_Panel_ScanProjects'`
- **Solución:** Implementar búsqueda automática siguiendo patrón de scripts de exploración
- **Método implementado:**
  ```python
  # Buscar usando __file__ (más confiable)
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
- **Resultado:** Módulo encontrado y importado correctamente

#### 9. ✅ Gestión de Ciclo de Vida de Ventanas
- **Error corregido:** Ventana que no se abría porque se destruía automáticamente
- **Problema:** `WA_DeleteOnClose = True` por defecto → ventana se destruye al cerrar
- **Solución:** `self.setAttribute(Qt.WA_DeleteOnClose, False)` siguiendo patrón de `LGA_NKS_Flow_Assignee.py`
- **Event loop:** Remover `app.exec_()` (Nuke ya maneja el event loop)
- **Resultado:** Ventana permanece abierta y reutilizable

**Patrón implementado:**
```python
# Variable global para mantener referencia (como en ejemplos que funcionan)
_projects_panel_window = None

class ProjectPanelWindow(QtWidgets.QWidget):  # ← QWidget como en LGA_NKS_mediaMissingFrames.py
    def __init__(self):
        super(ProjectPanelWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, False)  # ← No se destruye al cerrar

def main():
    global _projects_panel_window
    _projects_panel_window = ProjectPanelWindow()  # ← Asignar a variable global
    _projects_panel_window.show()
    return _projects_panel_window
```

### Estructura de Clases

```python
ProjectPanelWindow(QMainWindow)    # Ventana principal
├── ScanWorker(QRunnable)         # Worker para escaneo
├── ProjectItem(QWidget)          # Item individual de proyecto
│   ├── QLabel (nombre proyecto)
│   └── QWidget (contenedor secuencias)
│       └── QLabel[] (secuencias)
```

### Próximos Pasos de Testing

1. **Ejecutar en Nuke 15:** Verificar funcionamiento básico
2. **Probar interacciones:** Abrir proyectos, abrir secuencias
3. **Verificar threading:** Que no bloquee la UI durante escaneo
4. **Testear casos edge:** Proyectos sin secuencias, errores de apertura
5. **Comparar con especificaciones:** Verificar que cumple todos los requisitos

---

## Notas Técnicas

### Rutas y Paths
- ✅ Usar `Path` de `pathlib` para manejo de rutas
- ✅ Buscar archivos directamente en `sys.path` es más confiable
- ✅ Rutas de Windows funcionan correctamente con barras invertidas `\`

### Compatibilidad Qt
- ✅ Todos los scripts usan `LGA_QtAdapter_HieroTools` (aunque este script no usa Qt directamente)
- ✅ Mantener consistencia en imports

### Manejo de Errores
- ✅ El script maneja correctamente proyectos sin carpeta `*_SUP`
- ✅ El script maneja correctamente carpetas con permisos restringidos
- ✅ Las funciones de extracción de versión manejan casos especiales

---

## Preguntas Abiertas

1. ⚠️ **YM_SUP_Plates&Charts_2.hrox:** ¿Este formato especial necesita manejo diferente o está bien como está?
2. ❓ **Proyectos sin SUP:** ¿Debemos mostrar proyectos VFX que no tienen carpeta `*_SUP` o ignorarlos completamente? (Actualmente se ignoran)
3. ❓ **Actualización automática:** ¿El panel debe actualizarse automáticamente cuando se abre/cierra un proyecto o solo manualmente con Refresh?

---

**Última actualización:** Después de crear Ventana de Testing
**Próxima actualización:** Después de probar Ventana de Testing en Nuke 15

