# Métodos de Selección de Clip en Scripts LGA_NKS

Este documento describe los dos métodos principales utilizados en los scripts para determinar sobre qué clip se está actuando.

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

## Método 2: Clip del Track EXR que coincide con el Playhead

### Descripción
Este método obtiene la posición actual del playhead (`viewer.time()`) y busca el clip en el track EXR que coincide con esa posición temporal. El clip se encuentra cuando `clip.timelineIn() <= current_time < clip.timelineOut()`.

### Ventajas
- Más intuitivo: trabaja con el clip que está visible en el viewer
- No requiere selección manual
- Permite trabajar rápidamente mientras se navega por el timeline
- Ideal para workflows donde siempre se trabaja con el track EXR

### Desventajas
- Solo funciona con un clip a la vez
- Requiere que exista un track llamado "EXR"
- Depende de la posición del playhead

### Scripts que usan este método:

#### Scripts que usan playhead en EXR (con fallback a selección):
- **`LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`** (líneas 320-362)
  - Método `find_clip_at_playhead_in_track()` que busca en el track EXR
  - `process_selected_clips()` usa primero playhead, luego fallback a selección (método híbrido)
- **`LGA_NKS_Flow/LGA_NKS_Flow_ShowInFlow.py`** (líneas 217-277) ✅ **ACTUALIZADO v1.24**
  - Método `find_clip_at_playhead_in_track()` que busca en el track EXR
  - `process_selected_clips()` usa primero playhead, luego fallback a selección (método híbrido)
- **`LGA_NKS_Flow/LGA_NKS_ReviewPic.py`** (línea 39)
  - Función `get_clip_info_at_playhead()` busca en track EXR
- **`LGA_NKS/LGA_NKS_Clip_DisableEXR.py`** (líneas 25-95)
  - Busca clip en track EXR según posición del playhead
  - Función `find_exr_clip_at_position()`

#### Scripts de comparación (modo playhead):
- **`LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`** (líneas 417-482)
  - Busca clip en track EXR según playhead
  - Tiene modo `force_all_clips` para procesar todos los clips
- **`LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`** (líneas 417-485)
  - Busca clip en track REV según playhead
  - Tiene modo `force_all_clips` para procesar todos los clips

#### Scripts que usan playhead pero no específicamente EXR:
- **`LGA_NKS/LGA_NKS_InOut_Editref.py`** (línea 38)
  - Usa playhead para buscar en track EditRef o EditRefClean
- **`LGA_NKS/LGA_NKS_PrevNext_Rev.py`** (línea 36)
  - Usa playhead para navegar entre clips con colores específicos

---

## Método Híbrido (Recomendado)

Algunos scripts implementan un método híbrido que combina lo mejor de ambos:

1. **Primero intenta**: Obtener el clip del track EXR en la posición del playhead
2. **Fallback**: Si no encuentra clip en playhead, usa los clips seleccionados

### Scripts que usan método híbrido:
- **`LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`** (líneas 353-377)
  - Prioriza playhead en EXR, fallback a selección
- **`LGA_NKS_Flow/LGA_NKS_Flow_ShowInFlow.py`** (líneas 250-277) ✅ **ACTUALIZADO v1.24**
  - Prioriza playhead en EXR, fallback a selección

### Ejemplo de implementación:
```python
def process_selected_clips(self):
    seq = hiero.ui.activeSequence()
    if not seq:
        return []
    
    # Intentar obtener clip por playhead en track EXR
    playhead_clip = self.find_clip_at_playhead_in_track(seq, track_name="EXR")
    
    # Fallback a selección
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection() if te else []
    
    if playhead_clip:
        clips_to_process = [playhead_clip]
        debug_print(">>> Usando clip del playhead en track EXR")
    else:
        clips_to_process = selected_clips
        debug_print(">>> No hay clip en playhead; usando clips seleccionados")
    
    return clips_to_process
```

---

## Recomendación

**Se recomienda usar el Método 2 (playhead en track EXR) con fallback a selección** porque:
- Es más intuitivo para el usuario
- Permite trabajar rápidamente sin necesidad de seleccionar clips
- Mantiene compatibilidad con workflows que requieren selección manual
- Es consistente con el comportamiento esperado en herramientas de edición

---

## Notas de Implementación

### Para obtener el playhead:
```python
viewer = hiero.ui.currentViewer()
if viewer:
    current_time = viewer.time()
```

### Para buscar clip en track EXR:
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

### Para obtener clips seleccionados:
```python
te = hiero.ui.getTimelineEditor(seq)
selected_clips = te.selection()
```

---

## Historial de Cambios

- **2024**: Documentación inicial de los dos métodos
- **2024**: `LGA_NKS_Flow_ShowInFlow.py` migrado de Método 1 a Método 2 (híbrido) - v1.24

