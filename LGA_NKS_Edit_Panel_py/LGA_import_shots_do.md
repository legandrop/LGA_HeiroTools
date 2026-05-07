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
            ├─ Paso 1: push_clips_right()       → hace espacio en el timeline
            └─ Paso 2: import_item_to_bin()
                        bin_item.setColor()
                        place_clip_in_timeline()
                        → self.accept()
```

---

## Recolección de ítems

```python
# items_by_track: {track_name: [(item_dict, hex_color), ...]}
```

Para cada fila chequeada con track asignado:
- Se obtiene `row_data` de `_table_rows[row]`
- Se extrae `item = row_data.get("item", {})` y `track` del dropdown
- Se calcula el color con `_item_hiero_color(row_data)` (ver abajo)
- Se almacena la tupla `(item, color)` en `items_by_track[track]`

---

## Color por ítem: `_item_hiero_color`

```python
def _item_hiero_color(self, row_data: dict) -> str:
```

Devuelve el color hex que se aplica al `BinItem` en Hiero. Misma lógica que `_chip_color` en el preview:

| Sección | Color |
|---------|-------|
| `"plates"` | `_CLR_PLATES` = `#42616d` |
| `"refs"` | `_CLR_REFS` = `#aa9e54` |
| `"publish"` / comp | `_CLR_COMP` = `#3381e0` |
| `"publish"` / roto | `_CLR_ROTO` = `#2abf7e` |
| `"publish"` / cleanup | `_CLR_CLEANUP` = `#27c8c3` |
| `"publish"` / dmp | `_CLR_DMP` = `#e08033` |
| Publish v000 | `#474747` (gris oscuro) |

La regla v000: si el track_type es `comp`, `roto` o `cleanup` y el nombre del clip contiene `_v000`, `_v00`, etc. (regex `[._]v0{2,}(?:\b|_|$)`), el color es `#474747`.

---

## Paso 1 — Hacer espacio (`push_clips_right`)

### Cuándo se ejecuta

Solo si `self.frames_to_push > 0`. Este valor lo calcula `_find_insert_frame()` al abrir el diálogo: si el nuevo shot va al final del timeline, no hay nada que empujar.

### Implementación

`timeline_mod.push_clips_right(seq, from_frame, amount)` → `(moved_count, effective_insert_frame)`:

- Itera todos los `videoTracks()` de la secuencia, **excluyendo** los tracks BurnIn.
- Recolecta todos los `TrackItem` (no `EffectTrackItem`) cuyo `tl_out >= from_frame`.
  - Criterio `tl_out >= from_frame`: captura tanto clips que empiezan en `from_frame` o después, como clips que **cruzan** `from_frame` (empiezan antes, terminan después). Estos últimos son los del shot siguiente con inicio desalineado entre tracks.
- Calcula `effective_insert_frame = min(tl_in de todos los clips seleccionados)` **antes de moverlos**. Este es el frame real donde debe empezar el nuevo shot para quedar adyacente al siguiente sin gap ni overlap.
- Selecciona los ítems en el Timeline Editor con `hiero.ui.getTimelineEditor(seq).setSelection(items)`.
- Los ordena de **derecha a izquierda** (por `timelineIn()` descendente) para evitar colisiones.
- Para cada ítem, mueve:
  ```python
  item.setTimelineOut(item.timelineOut() + amount)  # out primero
  item.setTimelineIn(item.timelineIn()  + amount)   # luego in
  ```
  Se mueve `out` primero para que el clip no colapse si Hiero valida `out >= in`.
- Retorna `(moved_count, effective_insert_frame)`.

### Por qué `effective_insert_frame` ≠ `self.insert_frame`

`self.insert_frame` se calcula desde el TCIN del clip del shot siguiente en el track más a la derecha (bPlate en el ejemplo). Pero otros tracks pueden tener clips del shot siguiente que empiezan **antes** de ese frame. El `effective_insert_frame` es el mínimo de todos, garantizando que el nuevo clip quede pegado al slot siguiente sin importar qué track lo define.

Ejemplo:
- `insert_frame` = 548 (desde bPlate)
- `_comp_` y `aPlate` del shot siguiente empiezan en 480
- `effective_insert_frame` = 480
- Después del push de 484f: _comp_/aPlate del shot sig. quedan en 964
- Nuevo clip: 480–963 → adyacente ✓

### Tracks BurnIn

Se **excluyen** del push. Se estiran por separado con `stretch_burnin()` (pendiente de implementar en el flujo de import generalizado).

---

## Paso 2 — Import al bin, color y colocación en timeline

### Bin destino

```
clipsBin / F <seq_name> / <shot_name>
```

`bin_mod.find_or_create_shot_bin(seq, shot_name)` busca o crea la estructura.

### Import al bin

`bin_mod.import_item_to_bin(item, target_bin)` → `(clip, error_str)`:
- `kind == "exr_seq"` → `hiero.core.Clip(str(item["first_file"]))` — Hiero detecta la secuencia completa automáticamente desde el primer frame.
- `kind == "mov"` → `hiero.core.Clip(str(item["path"]))`
- Llama `clip.setName(name)`, crea `hiero.core.BinItem(clip)` y lo agrega al bin.
- Llama `clip.rescan()` y loguea el rango detectado.
- Los publish items tienen `kind="exr_seq"` garantizado por `_scan_publish_folders`.

### Color del BinItem

Inmediatamente después de importar al bin, se colorea el `BinItem`:

```python
bin_item = clip.binItem()
bin_item.setColor(QtGui.QColor(clip_color))
```

Donde `clip_color` es el hex calculado por `_item_hiero_color()` al momento de la recolección. Esto hace que el clip aparezca con el mismo color que el chip del preview tanto en el bin como en el timeline.

### `frame_count` por ítem

En este orden:
1. `item.get("frame_count")` — campo que setea `_scan_input_folder` / `_scan_publish_folders`.
2. Fallback: `clip.mediaSource().duration()` (después del rescan, Hiero tiene el rango real).

### Colocación en timeline

`timeline_mod.place_clip_in_timeline(seq, clip, track_name, tl_in, frame_count, shot_name)`:
- Busca el track por nombre. Si no existe, retorna error (no crea tracks automáticamente).
- `tl_out = tl_in + frame_count - 1`
- Llama `track.addTrackItem(clip, tl_in)`.
- Ajusta: `track_item.setTimes(tl_in, tl_out, 0, frame_count - 1)`
- Finalmente: `track_item.setVersionLinkedToBin(True)`.
- `tl_in` = `effective_insert_frame` (no `self.insert_frame`).

---

## Bloque de undo

`project.beginUndo("Import Shot: <shot_name>")` se abre **antes del Paso 1** (push), de manera que todo el flujo —push de clips, import al bin y colocación en timeline— queda dentro de un único bloque de undo.

`project.endUndo()` se cierra siempre en el bloque `finally`.

---

## Manejo de errores

Los errores de bin o timeline se acumulan en una lista `errors`. Al finalizar:
- Si hay errores: `QMessageBox.warning` con la lista.
- Si todo OK: log con `debug_print`.

En ambos casos se llama `self.accept()` para cerrar el diálogo.

---

## Colocación en timeline — políticas

| Política | Detalle |
|----------|---------|
| `tl_in` | `effective_insert_frame` (min tl_in de los clips empujados, no `self.insert_frame`) |
| Source in/out | Siempre `0 .. frame_count-1`. Los EXR físicos empiezan en `1001`; Hiero mapea internamente. |
| `setVersionLinkedToBin(True)` | Solo después de que el TrackItem ya está insertado y sus tiempos ajustados. |
| Track no encontrado | Error por clip, continua con los demás. No crea tracks automáticamente. |
| Nombre del TrackItem | `shot_name` (solo el código del shot). |

---

## Pendiente

- **`stretch_burnin`:** llamar después del push para estirar el track BurnIn.
- **Post-import — SetShotName:** llamar `LGA_NKS_SetShotName` para renombrar los clips.
- **Post-import — CreateV000:** dialogo para crear v000 en tasks sin versiones.

---

## Referencias técnicas

| Archivo | Funciones / clases clave |
|---------|--------------------------|
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._do_import()`, `_item_hiero_color()`, `_item_section_color()`, `_chip_color()`, `_find_insert_frame()`, `_inject_preview_logger()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_timeline.py` | `push_clips_right()`, `place_clip_in_timeline()`, `stretch_burnin()`, `_is_burnin_track()`, `set_debug_print()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_bin.py` | `find_or_create_shot_bin()`, `import_item_to_bin()`, `set_debug_print()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_preview.md` | Documentación de la página de preview que precede al import |
| `+Building_Blocks/Hiero/Timeline/LGA_H-SelectFromPlayhead.py` | Referencia del patrón `setTimelineOut/setTimelineIn` para mover clips |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_CreateV000.py` | Referencia del flujo: `_import_v000_to_bin`, `_set_v000_clip_color`, `bin_item.setColor()` |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_OrganizeProject.py` | Estructura de bins `F <seq_name>/<shot_name>` |
