> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_import_shots — Sección Import Real

Subsección de la herramienta `LGA_import_shots`.

Ejecuta la importación física de los ítems seleccionados al bin de Hiero y al timeline.
Se activa al pulsar "Import Now" en la página de Import Preview (PAGE_IMPORT).

---

## Flujo de navegación

```
Página Import Preview (PAGE_IMPORT)
  └─ click "Import Now"
       └─ ImportShotDialog._do_import()
            ├─ [DEV] filtro _IMPORT_ONLY_COMP
            ├─ Paso 1: push_clips_right()       → hace espacio en el timeline
            ├─ Paso 2: confirmación del usuario → QMessageBox.question
            └─ Paso 3: import_item_to_bin()
                        place_clip_in_timeline()
                        → self.accept()
```

---

## Flag de desarrollo: `_IMPORT_ONLY_COMP`

```python
_IMPORT_ONLY_COMP = True  # DEV: solo importa el track _comp_. Borrar al generalizar.
```

Definido a nivel de módulo en `LGA_import_shots.py`, cerca de `Transcode_TEST_Mode`.

Cuando está activo:
- De todos los ítems chequeados con track asignado, se conserva **únicamente** el asignado al track `_comp_`.
- Si no hay ítem en `_comp_`, se muestra un `QMessageBox.information` y el import se cancela sin modificar el timeline.
- Permite desarrollar y debuggear el flujo completo con un solo track antes de generalizarlo.

**Para generalizar:** cambiar a `False` y eliminar el bloque de filtrado en `_do_import()`.

---

## Paso 1 — Hacer espacio (`push_clips_right`)

### Cuándo se ejecuta

Solo si `self.frames_to_push > 0`. Este valor lo calcula `_find_insert_frame()` al abrir el diálogo: si el nuevo shot va al final del timeline, no hay nada que empujar.

### Mensaje de debug

Antes de ejecutar el push se muestra un `QMessageBox.information` con el texto:

```
PASO 1: Hacer espacio en el timeline.

Se van a mover todos los clips desde el frame {insert_frame}
hacia la derecha {frames_to_push} frames.
```

Y se logea con `debug_print`.

### Implementación

`timeline_mod.push_clips_right(seq, from_frame, amount)`:

- Itera todos los `videoTracks()` de la secuencia, **excluyendo** los tracks BurnIn.
- Recolecta todos los `TrackItem` (no `EffectTrackItem`) cuyo `timelineIn() >= from_frame`.
- Selecciona los ítems en el Timeline Editor con `hiero.ui.getTimelineEditor(seq).setSelection(items)` para visibilidad de debug.
- Los ordena de **derecha a izquierda** (por `timelineIn()` descendente) para evitar colisiones.
- Para cada ítem, mueve:
  ```python
  item.setTimelineOut(item.timelineOut() + amount)  # out primero
  item.setTimelineIn(item.timelineIn()  + amount)   # luego in
  ```
  Se mueve `out` primero para que el clip no colapse si Hiero valida `out >= in` al aplicar `setTimelineIn`.

### Tracks BurnIn

Los tracks BurnIn se **excluyen** del push. Se estiran por separado con `stretch_burnin()` (no implementado aún en el flujo actual; se agregará cuando el import esté generalizado).

La detección de BurnIn: `track_name.lower().strip() in {"burnin", "burn in", "burn_in"}`.

---

## Paso 2 — Confirmación del usuario

Se muestra un `QMessageBox.question` por cada ítem que se va a importar:

```
PASO 2: Importar al bin y colocar en timeline.

Clip:    <nombre del clip>
Bin:     F <seq_name> / <shot_name>
Track:   <track_name>
Frames:  <insert_frame> – <insert_frame + frame_count - 1>  (<frame_count> frames)

¿Continuar?
```

Botones: **OK** / **Cancelar**. Si el usuario cancela, el import se aborta sin deshacer el push ya realizado.

---

## Paso 3 — Import al bin y colocación en timeline

Todo el paso 3 está envuelto en `project.beginUndo() / endUndo("Import Shot: <shot_name>")`.

### Bin destino

```
clipsBin / F <seq_name> / <shot_name>
```

`bin_mod.find_or_create_shot_bin(seq, shot_name)` busca o crea la estructura.
Si los bins no existen se crean en cascada.

### Import al bin

`bin_mod.import_item_to_bin(item, target_bin)`:
- `kind == "exr_seq"` → `hiero.core.Clip(str(item["first_file"]))`
- `kind == "mov"` → `hiero.core.Clip(str(item["path"]))`
- Crea `hiero.core.BinItem(clip)` y lo agrega al bin.
- Retorna `(clip, error_str)`.

### Colocación en timeline

`timeline_mod.place_clip_in_timeline(seq, clip, track_name, tl_in, frame_count, shot_name)`:
- Busca el track por nombre. Si no existe, retorna error (no crea tracks automáticamente).
- `tl_out = tl_in + frame_count - 1`
- Llama `track.addTrackItem(clip, tl_in)`.
- Ajusta: `track_item.setTimes(tl_in, tl_out, 0, frame_count - 1)`
- Finalmente: `track_item.setVersionLinkedToBin(True)` (siempre al final, cuando el item ya está insertado y sus tiempos están ajustados).
- Retorna `(track_item, error_str)`.

### Manejo de errores

Los errores de bin o timeline se acumulan en una lista `errors`. Al finalizar:
- Si hay errores: `QMessageBox.warning` con la lista.
- Si todo OK: log con `debug_print`.

En ambos casos se llama `self.accept()` para cerrar el diálogo.

---

## `frame_count` por ítem

El `frame_count` se obtiene en este orden:
1. `item.get("frame_count")` — campo que setea `_scan_input_folder` / `_scan_publish_folders`.
2. Fallback: `clip.duration()` (después de importar al bin, Hiero ya conoce el clip).

---

## Logging

Prefijos de log usados por `_do_import()`:
- `"_do_import: _IMPORT_ONLY_COMP activo — solo se importará _comp_"`
- `"_do_import → PASO 1: ..."`
- `"_do_import: %d clips movidos %d frames"`
- `"_do_import → confirmación para '<clip>'"`
- `"_do_import: usuario aceptó/canceló importación de '<clip>'"`
- `"_do_import → PASO 3: Importando al bin..."`
- `"_do_import: error bin '<clip>' → <msg>"`
- `"_do_import: error timeline '<clip>' → <msg>"`
- `"_do_import: colocado '<clip>' en track '<track>' frame <N>"`

Módulos auxiliares usan `set_debug_print()` inyectado desde `_inject_preview_logger()`.

Archivo de log: `logs/debugPy_ImportShots.log`.

---

## Bin destino — estructura

```
project.clipsBin()
  └── F <seq_name>          ← creado si no existe
        └── <shot_name>     ← creado si no existe
              └── <clip>    ← BinItem del clip importado
```

Ejemplo: `F MOR_101 / MOR_1012C_010`.

La misma estructura que usa `LGA_NKS_OrganizeProject.py`.

---

## Colocación en timeline — políticas

| Política | Detalle |
|----------|---------|
| Source in/out | Siempre `0 .. frame_count-1`. Los EXR físicos empiezan en `1001`; Hiero mapea internamente. |
| `setVersionLinkedToBin(True)` | Solo después de que el TrackItem ya está insertado y sus tiempos ajustados. |
| Track no encontrado | Error por clip, continua con los demás. No crea tracks automáticamente. |
| Nombre del TrackItem | `shot_name` (solo el código del shot, sin nombre completo del archivo). |

---

## Pendiente

- **Generalizar:** quitar `_IMPORT_ONLY_COMP` y procesar todos los tracks.
- **`stretch_burnin`:** llamar después del push para estirar el track BurnIn.
- **Post-import — SetShotName:** llamar `LGA_NKS_SetShotName` para renombrar los clips.
- **Post-import — CreateV000:** dialogo para crear v000 en tasks sin versiones.

---

## Referencias técnicas

| Archivo | Funciones / clases clave |
|---------|--------------------------|
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._do_import()`, `_find_insert_frame()`, `_IMPORT_ONLY_COMP`, `_inject_preview_logger()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_timeline.py` | `push_clips_right()`, `place_clip_in_timeline()`, `stretch_burnin()`, `_is_burnin_track()`, `_find_video_track()`, `set_debug_print()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_bin.py` | `find_or_create_shot_bin()`, `import_item_to_bin()`, `set_debug_print()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_preview.md` | Documentación de la página de preview que precede al import |
| `+Building_Blocks/Hiero/Timeline/LGA_H-SelectFromPlayhead.py` | Referencia del patrón `setTimelineOut/setTimelineIn` para mover clips |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_CreateV000.py` | Referencia del flujo de import al bin (`hiero.core.Clip`, `BinItem`, `addTrackItem`, `setTimes`, `setVersionLinkedToBin`) |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_OrganizeProject.py` | Estructura de bins `F <seq_name>/<shot_name>` |
