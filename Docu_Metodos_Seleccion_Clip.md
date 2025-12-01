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
- **`LGA_NKS_Flow/LGA_NKS_Flow_Push.py`** - **Método Híbrido:** La función `push_from_selected_clips()` usa el módulo centralizado `LGA_NKS_GetClip` (permite selecciones múltiples). La función legacy `Push_Task_Status()` recibe `base_name` como parámetro (compatible con paneles que usan Método 1).
- **`LGA_NKS_Flow/LGA_NKS_Flow_Pull.py`** (línea 557) - `selected_clips = te.selection()` + usa `TRACK_comp_EXR` para filtrar tracks (v3.30)
- **`LGA_NKS_Flow/LGA_NKS_Flow_Thumbs.py`** (línea 52) - `selected_clips = timeline_editor.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_CreateShot_Thumbs.py`** (línea 70) - `selected_clips = timeline_editor.selection()`
- **`LGA_NKS_Flow/LGA_NKS_Flow_CreateShot.py`** (línea 136) - `selected_clips = timeline_editor.selection()`

#### Paneles:
- [x] **`LGA_NKS_Flow_Assignee_Panel.py`** - Usa `get_clips_to_process()` del módulo `LGA_NKS_GetClip` con `prioritize_multiple_selection=True` (método híbrido: selección múltiple prioritaria, playhead para selección simple)
- **`LGA_NKS_Flow_FlowProd_Panel.py`** - Llama a scripts que usan selección

#### Scripts de NKS:
- **`LGA_NKS/LGA_NKS_Trim_In.py`** (línea 396) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Trim_Out.py`** (línea 295) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Compare_Versions.py`** (línea 25) - `selected_clips = te.selection()` + usa `TRACK_comp_EXR` para identificar track
- **`LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`** - Usa `TRACK_comp_EXR` para identificar track
- **`LGA_NKS/LGA_NKS_OpenInNukeX.py`** (línea 335) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_RevealInExplorer.py`** (línea 62) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_RevealNK_Script.py`** (línea 44) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_SelfReplaceClip.py`** (línea 164) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_Reconnect.py`** (línea 94) - `selected_clips = te.selection()`
- **`LGA_NKS/LGA_NKS_ON_Clips_OFF_v00-Clips.py`** - Procesa clips seleccionados o todos

#### Paneles de EditTools:
- **`LGA_NKS_EditTools_Panel.py`** - Múltiples funciones usan `selected_clips = te.selection()`

---

## Método 2: Clip del Track que coincide con el Playhead (Método Híbrido Inteligente)

### Descripción
Este método obtiene la posición actual del playhead (`viewer.time()`) y busca el clip en el track especificado (por defecto `_comp_`, definido en `TRACK_comp_EXR`) que coincide con esa posición temporal. El clip se encuentra cuando `clip.timelineIn() <= current_time < clip.timelineOut()`.

**⚠️ IMPORTANTE:** El track por defecto ahora se llama `_comp_` (definido en `TRACK_comp_EXR`), anteriormente se llamaba `EXR`.

**Método Híbrido Inteligente Recomendado:**
1. **Advertencia automática**: Si hay clips seleccionados en tracks que no son el objetivo, muestra mensaje informativo
2. **Lógica inteligente para selección simple**: Si hay un solo clip seleccionado fuera del track objetivo pero del mismo shot, automáticamente usa el clip del track correcto (con mensaje informativo)
3. **Primero intenta**: Obtener el clip del track especificado (por defecto `_comp_`) en la posición del playhead
4. **Fallback**: Si no encuentra clip en playhead, usa los clips seleccionados

### Ventajas
- **Más intuitivo**: trabaja con el clip visible en el viewer
- **Lógica inteligente**: corrige automáticamente selecciones erróneas del mismo shot
- **Feedback informativo**: muestra mensajes claros cuando hay discrepancias entre shots
- No requiere selección manual (aunque tiene fallback inteligente)
- Permite trabajar rápidamente mientras se navega por el timeline
- Ideal para workflows donde siempre se trabaja con el mismo track (configurable mediante `TRACK_comp_EXR`)
- **Soporta selecciones múltiples**: Si el script está configurado con `prioritize_multiple_selection=True` o usa `get_clips_to_process()`, puede procesar múltiples clips cuando hay múltiples clips seleccionados en el track

### Desventajas
- **En modo playhead por defecto**: Funciona con un clip a la vez (el clip visible en el viewer)
  - **EXCEPCIÓN**: Si el script permite selecciones múltiples (`prioritize_multiple_selection=True` o `get_clips_to_process()`) y hay múltiples clips seleccionados en el track, procesará todos esos clips en lugar de solo el del playhead
- Requiere que exista un track con el nombre especificado (por defecto `_comp_`, configurable en `TRACK_comp_EXR`)

### Scripts que usan este método:

- [x] **`LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con `track_name=None` (NO permite selecciones múltiples)
- [x] **`LGA_NKS_Flow/LGA_NKS_Flow_Push.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con `track_name=None` en función `push_from_selected_clips()` (permite selecciones múltiples, con límite de 4 clips requiere confirmación)
- [x] **`LGA_NKS_Flow/LGA_NKS_Flow_ShowInFlow.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con `track_name=None` (permite selecciones múltiples)
- [x] **`LGA_NKS_Flow_Assignee_Panel.py`** - Usa `get_clips_to_process()` del módulo `LGA_NKS_GetClip` con `prioritize_multiple_selection=True` (método híbrido: selección múltiple prioritaria, playhead para selección simple)
- [x] **`LGA_NKS_Flow/LGA_NKS_ReviewPic.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con `track_name=None` (NO permite selecciones múltiples)
- [x] **`LGA_NKS/LGA_NKS_Clip_DisableEXR.py`** - Usa módulo centralizado `LGA_NKS_GetClip` (NO permite selecciones múltiples)
- [x] **`LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`** - Usa módulo centralizado `LGA_NKS_GetClip` (permite selecciones múltiples)
- [x] **`LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con método híbrido para buscar clip en track REV (playhead primero, luego selección como fallback)
- [x] **`LGA_NKS/LGA_NKS_InOut_Editref.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con método híbrido para buscar en track EditRef o EditRefClean
- [x] **`LGA_NKS/LGA_NKS_PrevNext_Rev.py`** - Usa módulo centralizado `LGA_NKS_GetClip` con método híbrido para buscar clips EditRef cuando la posición coincide con el playhead

**Leyenda:** 
- [x] = Usa módulo centralizado `LGA_NKS_GetClip`
- [ ] = Implementación manual
- **(permite selecciones múltiples)** = Usa `prioritize_multiple_selection=True` o `get_clips_to_process()` para procesar múltiples clips
- **(NO permite selecciones múltiples)** = Usa `prioritize_multiple_selection=False` (comportamiento por defecto) y procesa solo un clip a la vez

### Scripts que usan TRACK_comp_EXR directamente (no a través del módulo centralizado)

Estos scripts importan `TRACK_comp_EXR` del módulo `LGA_NKS_GetClip` pero hacen comparaciones directas con tracks en lugar de usar las funciones del módulo:

- [x] **`LGA_NKS/LGA_NKS_Compare_Versions.py`** - Importa `TRACK_comp_EXR` y lo usa para buscar el track (v1.2)
- [x] **`LGA_NKS/LGA_NKS_EXRTrack_Difference.py`** - Importa `TRACK_comp_EXR` y lo usa para alternar blend mode (v1.1)
- [x] **`LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`** - Importa `TRACK_comp_EXR` y lo usa para desactivar blend mode

**Nota:** Estos scripts usan selección manual (Método 1) pero también necesitan identificar el track específico por nombre, por lo que importan `TRACK_comp_EXR` para mantener la centralización del nombre del track.

---

## Módulo Utilitario Centralizado: `LGA_NKS_GetClip`

### Ubicación
**`LGA_NKS_Utils/LGA_NKS_GetClip.py`**

Este módulo centraliza la funcionalidad de obtención de clips para evitar duplicación de código y facilitar el mantenimiento. Implementa el método híbrido recomendado.

### ⚠️⚠️⚠️ IMPORTANTE: Cambio de Nombre del Track ⚠️⚠️⚠️

**El track que antes se llamaba "EXR" ahora se llama "_comp_" y está definido en la variable `TRACK_comp_EXR`.**

**Información crítica:**
- **Nombre actual del track:** `_comp_`
- **Variable en el módulo:** `TRACK_comp_EXR = "_comp_"` (en `LGA_NKS_Utils/LGA_NKS_GetClip.py`)
- **Nombre anterior:** `"EXR"` (ya no se usa)
- **Contenido del track:** Contiene los archivos EXR con el render de COMP

**Track REV:**
- **Nombre actual del track:** `_rev_`
- **Variable en el módulo:** `TRACK_comp_REV = "_rev_"` (en `LGA_NKS_Utils/LGA_NKS_GetClip.py`)
- **Nombre anterior:** `"REV"` (ya no se usa)
- **Contenido del track:** Contiene los archivos MOV o MXF con el render de COMP

**Es MUY IMPORTANTE verificar en los scripts que modificamos que:**
1. ✅ Usen la variable `TRACK_comp_EXR` del módulo
2. ✅ NO tengan hardcodeado `"EXR"` o cualquier otro nombre de track
3. ✅ Usen `track_name=None` en las llamadas a funciones para respetar `TRACK_comp_EXR`

**Si encuentras código hardcodeado con "EXR" o cualquier otro nombre de track, debe cambiarse para usar `track_name=None` y así respetar el valor actual `_comp_`.**

### ⚠️ IMPORTANTE: Revisar Hardcodeo de Nombre de Track

**Antes de migrar un script al módulo centralizado, es CRÍTICO revisar si tiene hardcodeado el nombre del track.**

**Problema común:**
- Muchos scripts tienen hardcodeado `track_name="EXR"` (o el nombre antiguo) en las llamadas a funciones
- Esto sobrescribe el `TRACK_comp_EXR` del módulo centralizado (actualmente `"_comp_"`)
- El script seguirá buscando en el nombre hardcodeado aunque cambies `TRACK_comp_EXR` a otro valor
- **Actualmente el track se llama `_comp_`, NO `EXR`**

**Solución:**
- **Usar `track_name=None`** o **no pasar el parámetro** para que use `TRACK_comp_EXR` del módulo
- **NO hardcodear** nombres de tracks como `track_name="EXR"` en las llamadas

**Ejemplo incorrecto:**
```python
# ❌ INCORRECTO: Hardcodea "EXR" (nombre antiguo), ignora TRACK_comp_EXR (actualmente "_comp_")
clip = get_clip_to_process(track_name="EXR")
# ❌ INCORRECTO: Hardcodea cualquier nombre, ignora TRACK_comp_EXR
clip = get_clip_to_process(track_name="_comp_")  # Aunque sea el nombre correcto, no debe hardcodearse
```

**Ejemplo correcto:**
```python
# ✅ CORRECTO: Usa TRACK_comp_EXR del módulo
clip = get_clip_to_process(track_name=None)
# O simplemente:
clip = get_clip_to_process()  # None es el valor por defecto
```

**Al migrar scripts existentes:**
1. Buscar todas las llamadas con `track_name="EXR"` o cualquier nombre hardcodeado
2. Cambiarlas a `track_name=None` o eliminar el parámetro
3. Verificar que el script ahora respete `TRACK_comp_EXR` del módulo

### Funciones Disponibles

#### `get_clip_to_process(track_name=None, prioritize_multiple_selection=False)`
**Función principal recomendada** - Implementa el método híbrido inteligente:
1. **Advertencia automática**: Si hay clips seleccionados en tracks que no son el objetivo, muestra mensaje informativo
2. **Lógica inteligente para selección simple**: Si hay un solo clip seleccionado fuera del track objetivo pero del mismo shot, automáticamente usa el clip del track correcto (con mensaje informativo)
3. Si `prioritize_multiple_selection=True` y hay múltiples clips seleccionados en el track, devuelve lista de esos clips
4. Si no, intenta obtener el clip del track especificado en la posición del playhead
5. Si no encuentra, usa el primer clip seleccionado como fallback

**Parámetros:**
- `track_name` (str, optional): Nombre del track a buscar. Si es `None`, usa `TRACK_comp_EXR` (actualmente `"_comp_"`)
- `prioritize_multiple_selection` (bool): Si `True` y hay múltiples clips seleccionados en el track especificado, 
  devuelve lista de esos clips. Si `False` (por defecto), procesa solo un clip a la vez usando playhead primero.

**Cuándo usar `prioritize_multiple_selection=True`:**
- Cuando tu script **permite procesar múltiples clips** a la vez (ej: abrir múltiples URLs, procesar batch)
- Cuando quieres que la selección múltiple tenga prioridad sobre el playhead

**Cuándo usar `prioritize_multiple_selection=False` (por defecto):**
- Cuando tu script **NO permite selecciones múltiples** y procesa solo un clip a la vez
- Cuando quieres priorizar el clip visible en el viewer (playhead)

**Retorna:**
- Clip encontrado, lista de clips (si `prioritize_multiple_selection=True` y hay múltiples), o `None` si no se encuentra ningún clip

**Ejemplo de uso:**
```python
from LGA_NKS_GetClip import get_clip_to_process

# Usar track por defecto (TRACK_comp_EXR) - NO permite selecciones múltiples
# ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
clip = get_clip_to_process(track_name=None)
# O simplemente: clip = get_clip_to_process()

# Especificar otro track explícitamente (solo si realmente necesitas un track específico)
clip = get_clip_to_process(track_name="REV")

# Para scripts que permiten selecciones múltiples (procesa múltiples clips)
# ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
clips = get_clip_to_process(track_name=None, prioritize_multiple_selection=True)
if isinstance(clips, list):
    # Procesar múltiples clips
    for clip in clips:
        # ... procesar cada clip
elif clips:
    # Procesar un solo clip
    # ... procesar clip
```

**Comportamiento inteligente para selección simple:**
- Si seleccionás un clip de otro track pero del mismo shot que el clip visible en `_comp_`, automáticamente usa el clip de `_comp_` (con mensaje informativo)
- Si los shots no coinciden, muestra advertencia y usa el clip de `_comp_` (playhead)
- Si no hay clip en `_comp_`, usa el clip seleccionado como fallback

#### `find_clip_at_playhead_in_track(seq, track_name=None)`
Busca el clip en un track específico que coincide con la posición del playhead.

**Parámetros:**
- `seq`: Secuencia activa de Hiero
- `track_name` (str, optional): Nombre del track. Si es `None`, usa `TRACK_comp_EXR`

**Retorna:**
- Clip encontrado o `None`

#### `get_clips_to_process(track_name=None, prioritize_multiple_selection=False)`
Obtiene los clips a procesar usando el método híbrido. **Siempre devuelve una lista** (puede contener 0, 1 o más clips).

**Recomendado para scripts que procesan múltiples clips.** Usa esta función cuando necesites iterar sobre los clips.

**Características:**
- Muestra advertencia automática cuando hay clips seleccionados en tracks que no son el objetivo
- Filtra por track igual que `get_clip_to_process()`

**Parámetros:**
- `track_name` (str, optional): Nombre del track a buscar. Si es `None`, usa `TRACK_comp_EXR`
- `prioritize_multiple_selection` (bool): Si `True` y hay múltiples clips seleccionados en el track, devuelve lista de esos clips (permite selecciones múltiples)

**Retorna:**
- Lista de clips encontrados (puede estar vacía)

**Ejemplo de uso:**
```python
from LGA_NKS_GetClip import get_clips_to_process

# Obtener clips (siempre devuelve lista)
# ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
clips = get_clips_to_process(track_name=None, prioritize_multiple_selection=True)

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
- `track_name` (str, optional): Nombre del track. Si es `None`, usa `TRACK_comp_EXR`

**Retorna:**
- Lista de clips seleccionados en el track especificado (excluyendo efectos) o lista vacía

#### `extract_shot_code_from_clip(clip)`
Extrae el shot code de un clip usando las utilidades de naming compatibles con ambos formatos de nomenclatura.
Maneja errores gracefully si no hay media o el archivo no existe.

**Parámetros:**
- `clip`: Clip de Hiero del cual extraer el shot code

**Retorna:**
- `str`: Shot code extraído o cadena vacía si hay error


### Configuración

#### Variable `TRACK_comp_EXR`
**⚠️ IMPORTANTE:** Esta variable define el nombre del track por defecto. Actualmente está configurada como `"_comp_"`.

**Contenido del track:** Este track contiene los archivos EXR con el render de COMP.

**Historial de cambios:**
- **Anteriormente:** `DEFAULT_TRACK_NAME = "EXR"` → `DEFAULT_TRACK_NAME = "_comp_"`
- **Actualmente:** `TRACK_comp_EXR = "_comp_"`

Puede modificarse en el módulo para cambiar el track por defecto:

```python
# En LGA_NKS_Utils/LGA_NKS_GetClip.py
TRACK_comp_EXR = "_comp_"  # Es el track que contiene a los EXR con el render de COMP
```

**⚠️ CRÍTICO:** Al cambiar esta variable, TODOS los scripts que usen `track_name=None` automáticamente usarán el nuevo nombre. Los scripts con nombres hardcodeados seguirán usando el nombre antiguo.

#### Variable `TRACK_comp_REV`
**⚠️ IMPORTANTE:** Esta variable define el nombre del track REV por defecto. Actualmente está configurada como `"_rev_"`.

**Contenido del track:** Este track contiene los archivos MOV o MXF con el render de COMP.

**Historial de cambios:**
- **Anteriormente:** Se usaba `"REV"` hardcodeado → `DEFAULT_REV_TRACK_NAME = "_rev_"`
- **Actualmente:** `TRACK_comp_REV = "_rev_"`

Puede modificarse en el módulo para cambiar el track por defecto:

```python
# En LGA_NKS_Utils/LGA_NKS_GetClip.py
TRACK_comp_REV = "_rev_"  # Es el track que contiene a los MOV o MXF con el render de COMP
```

**⚠️ CRÍTICO:** Al cambiar esta variable, TODOS los scripts que la importen automáticamente usarán el nuevo nombre. Los scripts con nombres hardcodeados seguirán usando el nombre antiguo.

#### Variable `DEBUG`
Controla los mensajes de debug:

```python
import LGA_NKS_GetClip as clip_utils
clip_utils.DEBUG = False  # Activar debug
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

**Para scripts que NO permiten selecciones múltiples (procesa un solo clip):**
```python
def mi_funcion():
    # Obtener clip (debe ejecutarse en hilo principal)
    # ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
    clip = get_clip_to_process(track_name=None)  # prioritize_multiple_selection=False por defecto
    # O simplemente: clip = get_clip_to_process()
    
    if not clip:
        print("No se encontró clip")
        return
    
    # Procesar clip
    fileinfos = clip.source().mediaSource().fileinfos()
    if fileinfos:
        file_path = fileinfos[0].filename()
        # ... resto del procesamiento
```

**Para scripts que permiten selecciones múltiples (procesa múltiples clips):**
```python
def mi_funcion():
    # Obtener clips (debe ejecutarse en hilo principal)
    # ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
    # Usar get_clips_to_process() que siempre devuelve lista
    clips = get_clips_to_process(track_name=None, prioritize_multiple_selection=True)
    
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

**Ejemplo 1: Script que NO permite selecciones múltiples (procesa un solo clip)**
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
    # Obtener clip en hilo principal (NO permite selecciones múltiples)
    # ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
    clip = get_clip_to_process(track_name=None)
    
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

**Ejemplo 2: Script que permite selecciones múltiples (procesa múltiples clips)**
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
    # Obtener clips en hilo principal (permite selecciones múltiples)
    # ⚠️ IMPORTANTE: Usar track_name=None para respetar TRACK_comp_EXR del módulo
    clips = get_clips_to_process(track_name=None, prioritize_multiple_selection=True)
    
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

**Se recomienda usar el módulo utilitario `LGA_NKS_GetClip`** que implementa el Método 2 (playhead en track especificado por `TRACK_comp_EXR`, actualmente `_comp_`) con fallback a selección porque:
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
