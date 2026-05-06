> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios.

# LGA_import_shots — Rename

Documentacion especifica de la sub-vista `Rename` del dialogo de Import Shot.

## Objetivo

Permitir renombrado masivo con preview en vivo, de forma segura y modular.

- Aplica sobre todos los items seleccionados en la tabla principal (input y publish).
- En secuencias EXR, renombra la secuencia y su carpeta contenedora.
- Bloquea automaticamente casos inseguros (mismatch de carpeta/secuencia, conflictos de destino).

## Archivos involucrados

- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots.py`
  - `ImportShotDialog._build_page_rename()`
  - `ImportShotDialog._update_rename_page()`
  - `ImportShotDialog._refresh_rename_preview()`
  - `ImportShotDialog._run_rename()`
- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots_rename.py`
  - `build_selected_rows()`
  - `compute_preview()`
  - `build_row_ops()`
  - `execute_ops()`
- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots_rename_settings.py`
  - `load_settings()`
  - `save_settings()`
  - `get_settings_path()`

## Tabla de preview

### Secciones

La tabla está organizada en **secciones** igual que la tabla principal, con el mismo sistema
de cabeceras de color. Solo se muestran las secciones que tienen ítems en la selección activa:

| Sección | Color | Condición |
|---------|-------|-----------|
| PUBLISH | gradiente comp→roto→cleanup | items de `source = "publish"` |
| PLATES | `#42616d` azul petróleo | items de `source = "plates"` |
| REFERENCES | `#aa9e54` dorado | items de `source = "refs"` |

La barra de color de cada fila de dato usa el color de la tarea (para publish) o el color de
sección (para plates/references). Para publish: comp=`#3381e0`, roto=`#2abf7e`,
cleanup=`#27c8c3`, dmp=`#e08033`.

### Columnas

| Col | Header | Ancho inicial | Resize |
|-----|--------|---------------|--------|
| 0 | (barra color) | 10 px | Fixed |
| 1 | (checkbox) | 28 px | Fixed |
| 2 | `Original` | 300 px | Interactive |
| 3 | `→` | 24 px | Fixed |
| 4 | `Renamed` | 300 px | Interactive |
| 5 | `Folder Original` | 210 px | Interactive |
| 6 | `Folder Renamed` | 210 px | Interactive |
| 7 | `Estado` | 220 px | Interactive |

Todas las columnas de contenido (2, 4, 5, 6, 7) son **resizables** por el usuario.

### Comportamiento de cols 4, 6 y 7 según checkbox

Cuando el checkbox de una fila está **desactivado** (no bloqueado, sino desmarcado por el
usuario), las columnas `Renamed`, `Folder Renamed` y `Estado` se muestran **vacías**.
Al volver a marcar el checkbox, se restauran los valores del preview.

Esta actualización es en vivo (sin recalcular el preview completo) mediante
`_on_rename_chk_changed(row_i)`.

### Estructura interna: display rows

La tabla usa `_rename_display_rows` (lista de dicts) que mezcla filas de sección y filas de
dato, igual que `_table_rows` en la tabla principal:

```
{"type": "section_header", "label": "PLATES", "color": "#42616d", "source": "plates"}
{"type": "data", "preview_row": <dict de compute_preview>}
```

`_rename_checkboxes` y los handlers de click usan el índice de display row (no de preview row).
Las filas de tipo `section_header` son ignoradas en los handlers de click/doble-click y en
`_update_rename_btn_state()` / `_run_rename()`.

Para secuencias EXR se muestra una sola entrada con placeholder de padding:

- `nombre_####.exr`
- `nombre.####.exr`

La cantidad de `#` refleja el padding real en origen y el calculado en destino.

## Pipeline secuencial (4 etapas)

El preview aplica estas etapas en orden:

1. Search/Replace 1 (`case_sensitive` opcional)
2. Search/Replace 2 (`case_sensitive` opcional)
3. Delimiter antes del frame (`_` o `.`)
4. Padding de frames (spinbox)

Cada etapa tiene color propio, reutilizando la paleta ya existente de transcode:

- etapa 1: `_CLR_AR` (amarillo)
- etapa 2: `_CLR_PAR` (rosa)
- etapa 3: `_CLR_COMP_DWAA` (verde)
- etapa 4: `_CLR_STATUS_PENDING` (cyan)

## Reglas de bloqueo

Una fila queda en gris y excluida del rename cuando:

- Secuencia EXR: nombre de carpeta distinto del prefijo de secuencia.
  - Ejemplo valido:
    - carpeta: `TEST_013_030_aPlate_v01`
    - secuencia: `TEST_013_030_aPlate_v01_1001.exr`
- El destino colisiona con un path existente que no esta dentro del mismo batch.
- Dos filas del batch apuntan al mismo destino final.

## Ejecucion segura

La ejecucion usa dos fases para minimizar conflictos:

1. Renombra cada origen a nombre temporal unico (`.__rename_tmp_*__`).
2. Renombra temporales a destinos finales.

Incluye rollback basico si falla durante la segunda fase.

## Persistencia de settings

Archivo INI dedicado:

- `%APPDATA%\LGA\HieroTools\ImportShotsRename.ini`

Secciones:

- `[SearchReplace1]`
- `[SearchReplace2]`
- `[Delimiter]`
- `[Padding]`

Valores persistidos:

- `search`, `replace`, `case_sensitive` (para SR1/SR2)
- `char` (`_` o `.`)
- `digits` (padding)
