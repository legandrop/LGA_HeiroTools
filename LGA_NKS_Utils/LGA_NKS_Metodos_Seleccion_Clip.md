# Métodos de Selección de Clip en Scripts LGA_NKS

Este documento describe los dos métodos principales utilizados en los scripts para determinar sobre qué clip se está actuando.

**Nota:** Este documento refleja el estado actual de los scripts. No incluye historial de cambios ni logs de actualizaciones.

---

## Método 1: Clip Seleccionado (`te.selection()`)

### Descripción
Este método utiliza los clips que están actualmente seleccionados en el timeline de Hiero/Nuke Studio. Se obtiene mediante `te.selection()` donde `te` es el `TimelineEditor` de la secuencia activa.

### Ventajas
- Permite trabajar con múltiples clips a la vez
- El usuario tiene control explícito sobre qué clips procesar
- Funciona independientemente de la posición del playhead

### Desventajas
- Requiere que el usuario seleccione manualmente los clips
- Puede ser menos intuitivo cuando se quiere trabajar con el clip visible en el viewer

### Scripts que usan este método:

#### Scripts de Flow:
- **`LGA_NKS_Flow/LGA_NKS_Flow_Push.py`** (línea 1357) - `selected_clips = te.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_Pull.py`** (línea 557) - `selected_clips = te.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_Thumbs.py`** (línea 52) - `selected_clips = timeline_editor.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_CreateShot_Thumbs.py`** (línea 70) - `selected_clips = timeline_editor.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_CreateShot.py`** (línea 136) - `selected_clips = timeline_editor.selection()`

#### Paneles:
- **`LGA_NKS_Flow_Assignee_Panel.py`** (líneas 287, 347, 410) - `selected_items = te.selection()`
- **`LGA_NKS_Flow_FlowProd_Panel.py`** - Llama a scripts que usan selección

#### Scripts de NKS:
- **`LGA_NKS/LGA_NKS_Trim_In.py`** (línea 396) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Trim_Out.py`** (línea 295) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Compare_Versions.py`** (línea 25) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`** - Similar al anterior
- **`LGA_NKS/LGA_NKS_OpenInNukeX.py`** (línea 335) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_RevealInExplorer.py`** (línea 62) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_RevealNK_Script.py`** (línea 44) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_SelfReplaceClip.py`** (línea 164) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Reconnect.py`** (línea 94) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_ON_Clips_OFF_v00-Clips.py`** - Procesa clips seleccionados o todos

#### Paneles de EditTools:
- **`LGA_NKS_EditTools_Panel.py`** - Múltiples funciones usan `selected_clips = te.selection()`

---

## Método 2: Clip del Track EXR que coincide con el Playhead (Método Híbrido)

### Descripción
Este método obtiene la posición actual del playhead (`viewer.time()`) y busca el clip en el track EXR que coincide con esa posición temporal. El clip se encuentra cuando `clip.timelineIn() <= current_time < clip.timelineOut()`.

**Método Híbrido Recomendado:**
1. **Primero intenta**: Obtener el clip del track EXR en la posición del playhead
2. **Fallback**: Si no encuentra clip en playhead, usa los clips seleccionados

### Ventajas
- Más intuitivo: trabaja con el clip que está visible en el viewer
- No requiere selección manual (aunque tiene fallback)
- Permite trabajar rápidamente mientras se navega por el timeline
- Ideal para workflows donde siempre se trabaja con el track EXR

### Desventajas
- Solo funciona con un clip a la vez (en modo playhead)
- Requiere que exista un track llamado "EXR" (o el track especificado)
- Depende de la posición del playhead

### Scripts que usan este método:

- [x] **`LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`** - Usa módulo centralizado `LGA_NKS_GetClip` (prioriza playhead)
- [x] **`LGA_NKS_Flow/LGA_NKS_Flow_ShowInFlow.py`** - Usa módulo centralizado `LGA_NKS_GetClip` (prioriza múltiples selecciones)
- [ ] **`LGA_NKS_Flow/LGA_NKS_ReviewPic.py`** (línea 39) - Función `get_clip_info_at_playhead()` busca en track EXR
- [ ] **`LGA_NKS/LGA_NKS_Clip_DisableEXR.py`** (líneas 25-95) - Función `find_exr_clip_at_position()` busca en track EXR
- [ ] **`LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`** (líneas 417-482) - Busca clip en track EXR según playhead
- [ ] **`LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`** (líneas 417-485) - Busca clip en track REV según playhead
- [ ] **`LGA_NKS/LGA_NKS_InOut_Editref.py`** (línea 38) - Usa playhead para buscar en track EditRef o EditRefClean
- [ ] **`LGA_NKS/LGA_NKS_PrevNext_Rev.py`** (línea 36) - Usa playhead para navegar entre clips con colores específicos

**Leyenda:** 
- [x] = Usa módulo centralizado `LGA_NKS_GetClip`
- [ ] = Implementación manual
- **(prioriza playhead)** = Usa `prioritize_multiple_selection=False` (comportamiento por defecto)
- **(prioriza múltiples selecciones)** = Usa `prioritize_multiple_selection=True` cuando hay múltiples clips seleccionados en el track

---

## Módulo Utilitario Centralizado: `LGA_NKS_GetClip`

### Ubicación
**`LGA_NKS_Utils/LGA_NKS_GetClip.py`**

Este módulo centraliza la funcionalidad de obtención de clips para evitar duplicación de código y facilitar el mantenimiento. Implementa el método híbrido recomendado.

### Funciones Disponibles

#### `get_clip_to_process(track_name=None, prioritize_multiple_selection=False)`
**Función principal recomendada** - Implementa el método híbrido:
1. Si `prioritize_multiple_selection=True` y hay múltiples clips seleccionados en el track, devuelve lista de esos clips
2. Si no, intenta obtener el clip del track especificado en la posición del playhead
3. Si no encuentra, usa el primer clip seleccionado como fallback

**Parámetros:**
- `track_name` (str, optional): Nombre del track a buscar. Si es `None`, usa `DEFAULT_TRACK_NAME` ("EXR" por defecto)
- `prioritize_multiple_selection` (bool): Si `True` y hay múltiples clips seleccionados en el track especificado, 
  prioriza esos clips sobre el playhead. Si `False` (por defecto), usa playhead primero.

**Cuándo usar `prioritize_multiple_selection=True`:**
- Cuando tu script puede procesar múltiples clips a la vez (ej: abrir múltiples URLs, procesar batch)
- Cuando quieres que la selección múltiple tenga prioridad sobre el playhead

**Cuándo usar `prioritize_multiple_selection=False` (por defecto):**
- Cuando tu script procesa un solo clip a la vez
- Cuando quieres priorizar el clip visible en el viewer (playhead)

**Retorna:**
- Clip encontrado, lista de clips (si `prioritize_multiple_selection=True` y hay múltiples), o `None` si no se encuentra ningún clip

**Ejemplo de uso:**
```python
from LGA_NKS_GetClip import get_clip_to_process

# Usar track por defecto (EXR) - prioriza playhead
clip = get_clip_to_process()

# Especificar otro track - prioriza playhead
clip = get_clip_to_process(track_name="REV")

# Priorizar múltiples clips seleccionados sobre playhead (para scripts que procesan múltiples clips)
clips = get_clip_to_process(track_name="EXR", prioritize_multiple_selection=True)
if isinstance(clips, list):
    # Procesar múltiples clips
    for clip in clips:
        # ... procesar cada clip
elif clips:
    # Procesar un solo clip
    # ... procesar clip
```

#### `find_clip_at_playhead_in_track(seq, track_name=None)`
Busca el clip en un track específico que coincide con la posición del playhead.

**Parámetros:**
- `seq`: Secuencia activa de Hiero
- `track_name` (str, optional): Nombre del track. Si es `None`, usa `DEFAULT_TRACK_NAME`

**Retorna:**
- Clip encontrado o `None`

#### `get_clips_to_process(track_name=None, prioritize_multiple_selection=False)`
Obtiene los clips a procesar usando el método híbrido. **Siempre devuelve una lista** (puede contener 0, 1 o más clips).

**Recomendado para scripts que procesan múltiples clips.** Usa esta función cuando necesites iterar sobre los clips.

**Parámetros:**
- `track_name` (str, optional): Nombre del track a buscar. Si es `None`, usa `DEFAULT_TRACK_NAME`
- `prioritize_multiple_selection` (bool): Si `True` y hay múltiples clips seleccionados en el track, prioriza esos clips sobre el playhead

**Retorna:**
- Lista de clips encontrados (puede estar vacía)

**Ejemplo de uso:**
```python
from LGA_NKS_GetClip import get_clips_to_process

# Obtener clips (siempre devuelve lista)
clips = get_clips_to_process(track_name="EXR", prioritize_multiple_selection=True)

for clip in clips:
    # Procesar cada clip
    file_path = clip.source().mediaSource().fileinfos()[0].filename()
    # ... resto del código
```

#### `get_selected_clips()`
Obtiene todos los clips seleccionados en el timeline (excluyendo efectos).

**Retorna:**
- Lista de clips seleccionados o lista vacía

#### `get_selected_clips_in_track(seq, track_name=None)`
Obtiene todos los clips seleccionados que pertenecen al track especificado.

**Parámetros:**
- `seq`: Secuencia activa de Hiero
- `track_name` (str, optional): Nombre del track. Si es `None`, usa `DEFAULT_TRACK_NAME`

**Retorna:**
- Lista de clips seleccionados en el track especificado (excluyendo efectos) o lista vacía

### Configuración

#### Variable `DEFAULT_TRACK_NAME`
Puede modificarse en el módulo para cambiar el track por defecto:

```python
# En LGA_NKS_Utils/LGA_NKS_GetClip.py
DEFAULT_TRACK_NAME = "EXR"  # Cambiar según el workflow
```

#### Variable `DEBUG`
Controla los mensajes de debug:

```python
import LGA_NKS_GetClip as clip_utils
clip_utils.DEBUG = True  # Activar debug
```

### Cómo Usar en Nuevos Scripts

**Paso 1:** Importar el módulo
```python
from pathlib import Path
import sys

# Agregar ruta del módulo utilitario
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clip_to_process
    import LGA_NKS_GetClip as clip_utils
    # Sincronizar debug si es necesario
    clip_utils.DEBUG = DEBUG  # Donde DEBUG es tu variable de debug
```

**Paso 2:** Usar la función en el hilo principal

**Para scripts que procesan un solo clip (prioriza playhead):**
```python
def mi_funcion():
    # Obtener clip (debe ejecutarse en hilo principal)
    clip = get_clip_to_process()  # prioritize_multiple_selection=False por defecto
    
    if not clip:
        print("No se encontró clip")
        return
    
    # Procesar clip
    fileinfos = clip.source().mediaSource().fileinfos()
    if fileinfos:
        file_path = fileinfos[0].filename()
        # ... resto del procesamiento
```

**Para scripts que procesan múltiples clips (prioriza selección múltiple):**
```python
def mi_funcion():
    # Obtener clips (debe ejecutarse en hilo principal)
    # Usar get_clips_to_process() que siempre devuelve lista
    clips = get_clips_to_process(track_name="EXR", prioritize_multiple_selection=True)
    
    if not clips:
        print("No se encontraron clips")
        return
    
    # Procesar cada clip
    for clip in clips:
        fileinfos = clip.source().mediaSource().fileinfos()
        if fileinfos:
            file_path = fileinfos[0].filename()
            # ... resto del procesamiento
```

**⚠️ IMPORTANTE:** Las funciones de este módulo **deben ejecutarse en el hilo principal** de Hiero. Si tu script usa threading, obtén el clip ANTES de crear el hilo secundario.

### Ejemplo Completo de Implementación

**Ejemplo 1: Script que procesa un solo clip (prioriza playhead)**
```python
from pathlib import Path
import sys

# Importar módulo utilitario
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clip_to_process
    import LGA_NKS_GetClip as clip_utils
    clip_utils.DEBUG = False  # Sincronizar debug

def procesar_clip():
    # Obtener clip en hilo principal (prioriza playhead)
    clip = get_clip_to_process()
    
    if not clip:
        print("No se encontró clip para procesar")
        return
    
    # Verificar que tenga media
    if not clip.source().mediaSource().isMediaPresent():
        print("El clip no tiene media presente")
        return
    
    # Obtener información del clip
    fileinfos = clip.source().mediaSource().fileinfos()
    if not fileinfos:
        return
    
    file_path = fileinfos[0].filename()
    print(f"Procesando: {file_path}")
    
    # ... resto del procesamiento
```

**Ejemplo 2: Script que procesa múltiples clips (prioriza selección múltiple)**
```python
from pathlib import Path
import sys

# Importar módulo utilitario
utils_path = Path(__file__).parent.parent / "LGA_NKS_Utils"
if utils_path.exists():
    sys.path.insert(0, str(utils_path))
    from LGA_NKS_GetClip import get_clips_to_process
    import LGA_NKS_GetClip as clip_utils
    clip_utils.DEBUG = False  # Sincronizar debug

def procesar_clips():
    # Obtener clips en hilo principal (prioriza múltiples selecciones)
    clips = get_clips_to_process(track_name="EXR", prioritize_multiple_selection=True)
    
    if not clips:
        print("No se encontraron clips para procesar")
        return
    
    # Procesar cada clip
    for clip in clips:
        # Verificar que tenga media
        if not clip.source().mediaSource().isMediaPresent():
            print(f"El clip {clip.name()} no tiene media presente")
            continue
        
        # Obtener información del clip
        fileinfos = clip.source().mediaSource().fileinfos()
        if not fileinfos:
            continue
        
        file_path = fileinfos[0].filename()
        print(f"Procesando: {file_path}")
        
        # ... resto del procesamiento
```

---

## Recomendación

**Se recomienda usar el módulo utilitario `LGA_NKS_GetClip`** que implementa el Método 2 (playhead en track EXR) con fallback a selección porque:
- ✅ **Código centralizado**: Evita duplicación y facilita el mantenimiento
- ✅ **Configuración flexible**: Permite cambiar el track por defecto fácilmente
- ✅ **Más intuitivo**: Trabaja con el clip visible en el viewer
- ✅ **Rápido**: Permite trabajar sin necesidad de seleccionar clips manualmente
- ✅ **Compatible**: Mantiene fallback a selección manual cuando es necesario
- ✅ **Consistente**: Comportamiento uniforme en todos los scripts que lo usan

**Para nuevos scripts:** Usa `get_clip_to_process()` del módulo `LGA_NKS_GetClip` en lugar de implementar la lógica manualmente.

---

## Notas de Implementación

### ⚠️ IMPORTANTE: Usa el Módulo Utilitario

**Para nuevos scripts, usa el módulo `LGA_NKS_GetClip`** en lugar de implementar manualmente:

```python
from LGA_NKS_GetClip import get_clip_to_process
clip = get_clip_to_process()
```

### Implementación Manual (Solo para Referencia)

Si necesitas implementar manualmente (no recomendado), aquí están los ejemplos:

#### Para obtener el playhead:
```python
viewer = hiero.ui.currentViewer()
if viewer:
    current_time = viewer.time()
```

#### Para buscar clip en track EXR:
```python
exr_track = None
for track in seq.videoTracks():
    if track.name().upper() == "EXR":
        exr_track = track
        break

if exr_track:
    for clip in exr_track:
        if isinstance(clip, hiero.core.EffectTrackItem):
            continue
        if clip.timelineIn() <= current_time < clip.timelineOut():
            return clip
```

#### Para obtener clips seleccionados:
```python
te = hiero.ui.getTimelineEditor(seq)
selected_clips = te.selection()
```
