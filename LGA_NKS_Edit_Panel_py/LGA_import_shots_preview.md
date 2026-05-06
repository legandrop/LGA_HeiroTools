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
| 2 | Timeline unificado: anterior \| nuevo \| siguiente | stretch |

La columna 2 es un único widget (`_build_timeline_row_widget`) con eje de tiempo
compartido para las tres zonas. Los clips se ven adyacentes cuando son contiguos
en el timeline, sin separadores visuales entre zonas.

### Aspecto de los chips

El color de TODOS los chips (anterior, nuevo, siguiente) se deriva del mismo color de barra del track. La diferencia entre "nuevo" y "contexto" es la intensidad:

- **Clip nuevo** (ítem a importar): fondo = `mix_colors(track_color, base, 0.38)`, borde = `track_color`, texto = `mix_colors(track_color, "#ffffff", 0.55)`, bold. Más destacado.
- **Clip anterior / siguiente** (contexto existente): fondo = `mix_colors(track_color, base, 0.10)`, borde = `mix_colors(track_color, base, 0.45)`, texto = `mix_colors(track_color, "#ffffff", 0.50)`. Más sutil.
- **Celda vacía**: widget transparente vacío.
- Todos los chips muestran la duración en frames (`480f`) junto al nombre, en texto más pequeño y sutil.

La función `mix_colors(hex_color, base="#1a1a1a", factor)` interpola linealmente entre `hex_color` (factor=1.0) y `base` (factor=0.0).

### Timeline unificado y anchos proporcionales

La columna de timeline (col 2) usa un único widget (`_build_timeline_row_widget`) con un eje de tiempo compartido. Esto evita separadores visuales artificiales entre zonas y permite que clips adyacentes aparezcan sin espacios.

**Referencia:** `ref_dur = max(max_new_clip_duration, frames_to_push, 1)`

**K = 1000 unidades por zona, 3000 en total:**

```
Zona 1 (antes):    [left_spacer] [before_chip] [before_gap]
Zona 2 (nuevo):    [new_chip] [new_trail]
Zona 3 (después):  [after_offset] [after_chip] [after_trail]
```

- `before_chip_K = min(1, before_dur/ref_dur) × 1000`
- `before_gap_K = min(1, (insert_frame − tl_out − 1) / ref_dur) × 1000`
  → gap entre fin del clip anterior y el insert_frame
- `new_chip_K = min(1, new_dur/ref_dur) × 1000`
  → el clip de duración máxima ocupa todos los 1000 de la zona
- `after_offset_K = min(1, (frames_to_push − new_dur) / ref_dur) × 1000`
  → gap entre fin del nuevo clip (para este track) y inicio del siguiente
- `after_chip_K = min(1, after_dur/ref_dur) × 1000`

Cuando dos clips son adyacentes en el timeline (gap=0), sus chips quedan visualmente pegados. Las duraciones se loguean con `debug_print` para cada fila.

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

`_find_adjacent_clips` ahora maneja el caso de clips que **abarcan** el punto de inserción (`tl_in < insert_frame <= tl_out`). Este patrón es típico del track `_comp_`, que suele tener un clip largo que cubre todo el timeline. En ese caso:
- El clip se trata como "before" con `tl_out_efectivo = insert_frame - 1`.
- La duración efectiva es la porción visible antes del insert.

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
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._build_page_import`, `_update_import_page`, `_populate_import_table`, `_build_timeline_row_widget`, `_go_to_import`, `_do_import`, `_make_chip_label`, `_build_track_combo`, `_on_track_combo_changed`, `_inject_preview_logger`, `_track_bar_color`, `_item_section_color`, `_fmt_duration` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `_find_or_create_shot_bin`, `_import_item_to_bin`, `_place_clip_in_timeline` |

### Documentación relacionada

- `LGA_NKS_Edit_Panel_py/LGA_import_shots.md` — documentación general de la herramienta
- `+Building_Blocks/LGA_NKS_CreateV000_Plan.md` — referencia para el flujo de importación Hiero (bin, track item, setTimes, setVersionLinkedToBin)
