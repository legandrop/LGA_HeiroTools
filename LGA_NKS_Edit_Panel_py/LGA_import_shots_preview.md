> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_import_shots — Sección Import Preview

Subseccion de la herramienta `LGA_import_shots`.

Muestra una preview visual tipo timeline de cómo quedará el timeline de Nuke Studio una vez que se importen los ítems seleccionados.

## Propósito

Antes de ejecutar la importación real, el usuario puede revisar:

- En qué track irá cada ítem seleccionado.
- Qué clips existen actualmente a la izquierda y a la derecha del punto de inserción en cada track.
- Qué ítems no tienen track asignado y quedarán fuera del timeline.

Esta página es la pantalla final del flujo de importación. Desde aquí se ejecuta la importación real.

---

## Flujo de navegación

```
Página Media (PAGE_MEDIA)
  └─ click "Import"
       └─ Página Import Preview (PAGE_IMPORT)
            ├─ click "← Go Back"  →  Página Media
            └─ click "Import Now" →  _do_import() → cierra el diálogo
```

El botón "Import" en la página Media (antes `self.accept`) ahora llama a `_go_to_import()`.

---

## Tabla timeline

La tabla NO usa el look estándar de las otras secciones (Rename, Transcode). Su aspecto imita un timeline de Nuke Studio: filas horizontales = tracks, celdas = bloques de clips.

### Columnas

| Col | Contenido | Ancho |
|-----|-----------|-------|
| 0 | Barra de color de track (4 px) | 10 px fijo |
| 1 | Nombre del track | 130 px fijo |
| 2 | **Shot Anterior** — eje temporal del shot previo | stretch igual |
| 3 | **Shot Nuevo** — eje temporal del shot importado | stretch igual |
| 4 | **Shot Siguiente** — eje temporal del shot siguiente | stretch igual |

Cada columna representa un **shot completo** con su propio eje de tiempo independiente:

- **Shot Anterior**: el rango temporal va desde el `tl_in` mínimo hasta el `tl_out` máximo de todos los before clips en el timeline. El clip más largo llena el 100 % de la columna. Clips más cortos o desplazados se posicionan con offset proporcional según su `tl_in` relativo al inicio del shot.
- **Shot Nuevo**: todos los clips empiezan en TC 0 (sin offset). El clip con más frames llena el 100 %. Otros clips se escalan proporcionalmente.
- **Shot Siguiente**: igual que Shot Anterior pero para los after clips.

Entre columnas hay un separador visual de 2-4 px (padding de celdas).

### Aspecto de los chips

El color de TODOS los chips (anterior, nuevo, siguiente) es **idéntico** — mismo fondo, mismo borde, mismo color de texto — derivado del track color:

- `bg     = mix_colors(track_color, "#1a1a1a", 0.35)`
- `border = track_color`
- `text   = mix_colors(track_color, "#ffffff", 0.75)`
- `weight = "bold"` solo para clips nuevos (a importar), `"normal"` para clips de contexto.

Los chips **no muestran la duración en el texto**. La duración (frames + segundos) se muestra en el **tooltip** al hacer hover.

Los chips pueden shrinkear por debajo de su `sizeHint` (`QSizePolicy.Ignored`, `minimumWidth=1`). Si el chip es muy angosto, el texto se cropea naturalmente por la izquierda del padding. Esto garantiza que los anchos porcentuales se respeten sin que el texto fuerce un mínimo.

### Tooltip de clips

Al hacer hover sobre cualquier chip, se muestra un tooltip estilizado con:
- Nombre completo del clip (accent color del track)
- Duración en frames y segundos

Implementado via `LGA_NKS_Shared/LGA_tooltip_helper.py` → `set_clip_tooltip()`. El stylesheet global de `QToolTip` se aplica una sola vez en `_build_page_import()` via `apply_tooltip_stylesheet()`.

### Anchos proporcionales por columna (K = 1000)

Cada columna usa `K = 1000` unidades de stretch. Los chips se construyen con `QHBoxLayout` usando `addWidget(label, chip_K)` y `addStretch(trail_K)`.

**Shot Anterior** (`_build_before_cell`):

```
shot_start = min(tl_in de todos los before clips)
shot_dur   = max(tl_out) − shot_start + 1

offset_K   = (clip.tl_in − shot_start) / shot_dur × K
chip_K     = clip.duration / shot_dur × K
trail_K    = K − offset_K − chip_K

layout: [spacer(offset_K)] [chip(chip_K)] [spacer(trail_K)]
```

**Shot Nuevo** (`_build_new_cell`):

```
shot_dur = max(frame_count de todos los clips nuevos)

chip_K   = clip.frame_count / shot_dur × K   (sin offset)
trail_K  = K − chip_K

layout: [chip(chip_K)] [spacer(trail_K)]
```

**Shot Siguiente** (`_build_after_cell`):

```
shot_start = min(tl_in de todos los after clips)
shot_dur   = max(tl_out) − shot_start + 1

offset_K   = (clip.tl_in − shot_start) / shot_dur × K
chip_K     = clip.duration / shot_dur × K
trail_K    = K − offset_K − chip_K

layout: [spacer(offset_K)] [chip(chip_K)] [spacer(trail_K)]
```

Las métricas (`before_shot_start`, `before_shot_dur`, etc.) se calculan **globalmente** en `_populate_import_table` antes de iterar los tracks, para que todos los clips se comparen contra el mismo eje temporal. Los cálculos se loguean con `debug_print` usando prefijos `[before_cell]`, `[new_cell]`, `[after_cell]`.

### Colores de barra de track

Los mismos que usa la página principal de media:

| Tipo | Color |
|------|-------|
| plate | `#42616d` (`_CLR_PLATES`) |
| editref | `#aa9e54` (`_CLR_REFS`) |
| comp | `#3381e0` (`_CLR_COMP`) |
| roto | `#2abf7e` (`_CLR_ROTO`) |
| cleanup | `#27c8c3` (`_CLR_CLEANUP`) |
| other | `#555555` |

### Sección "SIN TRACK ASIGNADO"

Debajo de todos los tracks, si hay ítems sin track asignado (track `None`, `"?"` o `"— sin track —"` en el combo), aparece un separador de sección gris con el encabezado `SIN TRACK ASIGNADO` y debajo un chip por ítem.

Los chips de la sección unassigned:
- Usan el color de su sección de origen (plates → `_CLR_PLATES`, refs → `_CLR_REFS`, publish → color de task).
- Muestran el nombre y la duración igual que los chips de tracks.
- Estos ítems **no se importan al timeline** al pulsar "Import Now".

---

## Reglas de inclusión de tracks

`build_import_preview_data()` itera todos los `videoTracks()` de la secuencia activa.

Hiero devuelve los tracks de abajo hacia arriba. Se aplica `reversed()` para recorrerlos de arriba hacia abajo, que es el orden visual del timeline.

Se incluyen **TODOS** los tracks del timeline sin excepción (incluyendo burn-in, efectos, etc.).

Un track puede aparecer con todas sus columnas vacías (sin antes, sin nuevo, sin después). Esto es intencional: el usuario ve todos los tracks del timeline existente como contexto, no solo los relevantes.

Si un ítem está asignado a un track que **no existe en el timeline**, ese track se añade al final de la lista (con `before = None` y `after = None`).

---

## Un clip por track

La página principal (Media) aplica la regla de **un solo clip por track** en dos momentos:

**En carga inicial** (`_build_track_combo`):
- Al construir el combo de cada fila, se verifica si el track auto-detectado ya está ocupado.
- Prioridad EXR: si el ítem actual es `exr_seq` y el existente es `mov`, el EXR desplaza al MOV.
- Si el existente gana (ya era EXR o MOV), el ítem actual queda en `"— sin track —"`.
- Los conflictos se loguean con `debug_print`.

**Por interacción del usuario** (`_on_track_combo_changed`):
- Cuando el usuario cambia un dropdown a un track ya ocupado, el anterior ítem en ese track queda en `"— sin track —"` automáticamente.

### Clips que cruzan el insert_frame

`_find_adjacent_clips` clasifica clips en tres categorías según su relación con `insert_frame`:

| Condición | Bucket |
|-----------|--------|
| `tl_out < insert_frame` | **before** (clip enteramente antes) |
| `tl_in >= insert_frame` | **after** (clip enteramente después) |
| `tl_in < insert_frame <= tl_out` | **solo after**, con rango COMPLETO (`tl_in` original) |

Los clips que cruzan `insert_frame` **NO contribuyen al bucket before**. Esto es intencional: la columna "Shot Anterior" debe mostrar únicamente los clips del shot anterior completo (ej. `TEST_013_010`), no una porción cropeada de un clip que ya pertenece al shot siguiente.

Los clips que cruzan se muestran en "Shot Siguiente" con su `tl_in` real (no desde `insert_frame`), lo que permite visualizar correctamente su posición y duración dentro de la ventana temporal del shot siguiente.

**Ejemplo**:
- `_comp_`: `TEST_013_010` TL 0-479 (480f) → **before**
- `_comp_`: `TEST_013_030_Chroma_AutoDia` TL 480-715 (236f) cruza insert_frame=548 → **after (rango completo, tl_in=480)**
- `bPlate`: `TEST_013_030_Chroma_AutoDia` TL 548-613 (66f), tl_in=548=insert_frame → **after (enteramente después)**

## Deduplicación de versiones

En `_update_import_page()`, antes de llamar a `build_import_preview_data()`, se deduplica por track: si hay múltiples ítems chequeados asignados al mismo track (ej. `aPlate_v01` y `aPlate_v02` ambos chequeados), **solo se importa el de mayor `version_num`**.

Esto garantiza que siempre se importa la versión más alta, independientemente de cuántas versiones haya chequeado el usuario.

---

## Logging

El módulo usa un logger inyectable. El módulo principal llama a `set_debug_print(debug_print)` justo después de importar `preview_mod`. Esto se realiza en `_inject_preview_logger()`.

Los mensajes de debug se escriben en el mismo log que el resto de la herramienta (`logs/DebugPy_EditToolsPanel.log`) con prefijos como `[preview_row]`, `[populate_import_table]`, `_find_adjacent_clips`, etc.

---

## Función principal: `build_import_preview_data`

**Archivo:** `LGA_NKS_Edit_Panel_py/LGA_import_shots_preview.py`

```python
def build_import_preview_data(
    seq,
    shot_name: str,
    insert_frame: int,
    items_by_track: dict[str, list[dict]],
    unassigned_items: list[dict],
) -> dict:
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `seq` | `hiero.core.Sequence` | Secuencia activa del timeline |
| `shot_name` | `str` | Nombre del shot que se importa |
| `insert_frame` | `int` | Frame de inserción calculado por `_find_insert_frame()` |
| `items_by_track` | `dict[str, list[dict]]` | Ítems chequeados agrupados por nombre de track |
| `unassigned_items` | `list[dict]` | Ítems sin track asignado |

### Retorno

```python
{
  "tracks": [
    {
      "track_name": str,
      "track_type": "plate" | "editref" | "comp" | "roto" | "cleanup" | "other",
      "before_clip": {"name": str, "tl_in": int, "tl_out": int} | None,
      "new_items":   [item_dict],
      "after_clip":  {"name": str, "tl_in": int, "tl_out": int} | None,
    },
    ...
  ],
  "unassigned": [item_dict],
}
```

### Lógica de before/after

Para cada track, `_find_adjacent_clips(track, insert_frame)` encuentra:

- **before**: el clip con mayor `timelineOut` que sea menor que `insert_frame`.
- **after**: el clip con menor `timelineIn` que sea mayor o igual a `insert_frame`.

`EffectTrackItem` se ignora en todos los recorridos.

---

## Funciones auxiliares: importación real

**Archivo:** `LGA_NKS_Edit_Panel_py/LGA_import_shots.py`

### `_find_or_create_shot_bin(seq, shot_name)`

Localiza o crea el bin destino:

```
project.clipsBin() / F <seq_name> / <shot_name>
```

Sigue la misma estructura que `LGA_NKS_OrganizeProject.py`.

### `_import_item_to_bin(item, target_bin)`

Crea un `hiero.core.Clip` desde el path del ítem y lo agrega al bin destino.

- Para `exr_seq`: usa `item["first_file"]` (primer frame real de la secuencia).
- Para `mov`: usa `item["path"]`.

Retorna `(clip, error_str)`.

### `_do_import()` (método de `ImportShotDialog`)

Orquesta la importación completa:

1. Recopilar ítems chequeados con track asignado.
2. Llamar `_find_or_create_shot_bin()`.
3. Por cada ítem: `_import_item_to_bin()` → `_place_clip_in_timeline()`.
4. Todo envuelto en `project.beginUndo() / endUndo()`.
5. Si hay errores parciales: muestra `QMessageBox.warning`.
6. Cierra el diálogo con `self.accept()`.

---

## Referencias técnicas

### Archivos principales

| Archivo | Función / Clase |
|---------|----------------|
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_preview.py` | `build_import_preview_data`, `classify_track_type`, `mix_colors`, `_find_adjacent_clips`, `set_debug_print`, `_log` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._build_page_import`, `_update_import_page`, `_populate_import_table`, `_build_before_cell`, `_build_new_cell`, `_build_after_cell`, `_go_to_import`, `_do_import`, `_make_chip_label`, `_build_track_combo`, `_on_track_combo_changed`, `_inject_preview_logger`, `_track_bar_color`, `_item_section_color`, `_fmt_duration` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `_find_or_create_shot_bin`, `_import_item_to_bin`, `_place_clip_in_timeline` |

### Documentación relacionada

- `LGA_NKS_Edit_Panel_py/LGA_import_shots.md` — documentación general de la herramienta
- `+Building_Blocks/LGA_NKS_CreateV000_Plan.md` — referencia para el flujo de importación Hiero (bin, track item, setTimes, setVersionLinkedToBin)
