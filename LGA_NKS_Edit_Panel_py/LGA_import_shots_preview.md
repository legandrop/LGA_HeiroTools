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
| 2 | Clip anterior (chip dimmed) | stretch |
| 3 | Clip(s) nuevo(s) a importar (chip destacado) | stretch |
| 4 | Clip siguiente (chip dimmed) | stretch |

### Aspecto de los chips

- **Clip anterior / siguiente** (contexto): fondo `#2e2e2e`, borde `#444444`, texto `#888888`.
- **Clip nuevo** (ítem a importar): fondo `#2e2547`, borde `#5a4faa`, texto `#cccccc` bold.
- **Celda vacía** (sin clip adyacente o sin ítem nuevo para ese track): widget transparente vacío.

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

Debajo de todos los tracks, si hay ítems sin track asignado (track `None`, `"?"` o `"— sin track —"` en el combo), aparece un separador de sección gris con el encabezado `SIN TRACK ASIGNADO` y debajo un ítem por línea. Estos ítems **no se importan al timeline** al pulsar "Import Now".

---

## Reglas de inclusión de tracks

`build_import_preview_data()` itera todos los `videoTracks()` de la secuencia activa.

Un track se incluye en la tabla si cumple al menos una condición:

- Tiene ítems nuevos asignados (chequeados en la página Media con ese track seleccionado).
- Tiene clips adyacentes (before o after) al punto de inserción.

Se excluyen los tracks de burn-in (`burnin`, `burn in`, `burn_in`).

Si un ítem está asignado a un track que **no existe en el timeline**, ese track se incluye igual (con `before = None` y `after = None`), porque el ítem necesita ser colocado allí.

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
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_preview.py` | `build_import_preview_data`, `classify_track_type`, `_find_adjacent_clips`, `_is_burnin` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `ImportShotDialog._build_page_import`, `_update_import_page`, `_populate_import_table`, `_go_to_import`, `_do_import`, `_make_clip_chip`, `_track_bar_color` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `_find_or_create_shot_bin`, `_import_item_to_bin`, `_place_clip_in_timeline` |

### Documentación relacionada

- `LGA_NKS_Edit_Panel_py/LGA_import_shots.md` — documentación general de la herramienta
- `+Building_Blocks/LGA_NKS_CreateV000_Plan.md` — referencia para el flujo de importación Hiero (bin, track item, setTimes, setVersionLinkedToBin)
