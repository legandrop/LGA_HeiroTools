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

| Sección | Color barra | Texto header | Condición |
|---------|-------------|--------------|-----------|
| PUBLISH | gradiente comp→roto→cleanup | gradiente | items de `source = "publish"` |
| PLATES | `#42616d` azul petróleo | `#6fc9d9` celeste (= tabla principal) | items de `source = "plates"` |
| REFERENCES | `#aa9e54` dorado | `#aa9e54` dorado | items de `source = "refs"` |

La barra de color de cada fila de dato usa el color de la tarea (para publish) o el color de
sección (para plates/references). Para publish: comp=`#3381e0`, roto=`#2abf7e`,
cleanup=`#27c8c3`, dmp=`#e08033`. La barra nunca se grisea aunque la fila esté bloqueada.

### Columnas

| Col | Header | Ancho inicial | Resize | Notas |
|-----|--------|---------------|--------|-------|
| 0 | (barra color) | 10 px | Fixed | |
| 1 | (checkbox) | 28 px | Fixed | |
| 2 | `Original` | 300 px | Interactive | |
| 3 | `→` | 24 px | Fixed | |
| 4 | `Renamed` | 300 px | Interactive | vacío/`—` si checkbox off |
| 5 | `Folder Original` | 210 px | Interactive | |
| 6 | `Folder Renamed` | 210 px | Interactive | vacío/`—` si checkbox off |
| 7 | `Estado` | 220 px | Interactive | alineado a la izquierda |

Todas las columnas de contenido (2, 4, 5, 6, 7) son **resizables** por el usuario.

### Comportamiento de cols según checkbox

Los colores de preview (original y renamed) solo se muestran para filas con checkbox activo.
Filas bloqueadas (mismatch, conflicto) y filas desactivadas por el usuario muestran siempre
texto plano `#a7a7a7`, sin ningún resaltado de cambio.

| Condición | Original (2) | Folder Orig (5) | Renamed (4) | Folder Renamed (6) | Estado (7) |
|-----------|-------------|-----------------|-------------|-------------------|------------|
| Activo, con cambios | coloreado | coloreado | preview coloreado | preview coloreado | `Pendiente` cian |
| Activo, sin cambios | nombre igual | folder igual | nombre igual | folder igual | `Sin cambios` gris |
| Desactivado por usuario | plano `#a7a7a7` | plano `#a7a7a7` | `—` `#444444` | `—` `#444444` | `—` `#444444` |
| Bloqueado (mismatch, conflicto) | plano `#a7a7a7` | plano `#a7a7a7` | `—` `#444444` | `—` `#444444` | warning rojo |

La **barra de color** (col 0) siempre usa el color de sección/tarea, independientemente de
si la fila está bloqueada o desactivada.

La actualización de cols 2, 4, 5, 6, 7 es en vivo (sin recalcular el preview completo)
mediante `_on_rename_chk_changed(row_i)`.

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

1. Search/Replace 1 (`case_sensitive` opcional) — botón ⇄ intercambia Search y Replace
2. Search/Replace 2 (`case_sensitive` opcional) — botón ⇄ intercambia Search y Replace
3. Delimiter antes del frame (`_` o `.`)
4. Padding de frames (spinbox) — respeta el mínimo de dígitos necesario por secuencia

Cada etapa tiene color propio, reutilizando la paleta ya existente de transcode:

- etapa 1: `_CLR_AR` (amarillo)
- etapa 2: `_CLR_PAR` (rosa)
- etapa 3: `_CLR_COMP_DWAA` (verde)
- etapa 4: `_CLR_STATUS_PENDING` (cyan)

## Botón ⇄ (Swap Search / Replace)

Cada sección SR1 y SR2 tiene un botón pequeño `⇄` entre el campo Search y el Replace.
Al pulsarlo, intercambia el texto de ambos campos (método `_swap_sr(search_edit, replace_edit)`).
El swap dispara `textChanged` en ambos campos, por lo que el preview se actualiza
automáticamente igual que si el usuario hubiera editado manualmente.

## Preservación de checkboxes en refresh

Cada vez que `_refresh_rename_preview()` reconstruye la tabla (al cambiar cualquier setting),
se preserva el estado de cada checkbox usando `item_path` como clave de identidad.
El estado inicial del checkbox en la nueva tabla se toma del estado guardado; si el item es
nuevo (no tenía estado previo), se usa el default (`True` para no bloqueados, `False` para
bloqueados).

## Dígitos mínimos por secuencia (Step 4)

El spinbox de "Frame Digits" fija el padding solicitado por el usuario (`user_digits`), pero
`compute_preview` aplica un `effective_digits` por secuencia:

```
effective_digits = max(user_digits, min_digits_needed)
min_digits_needed = len(str(last_frame))   # frame más alto de la secuencia
```

Ejemplos:

| Secuencia | Frame máx | min_digits | user_digits | effective | Cambio de padding |
|-----------|-----------|------------|-------------|-----------|-------------------|
| seq_####  | 9999      | 4          | 3           | 4         | NO (4 == 4)       |
| seq_####  | 9999      | 4          | 5           | 5         | SÍ (4 → 5)        |
| seq_####### | 98776  | 5          | 3           | 5         | SÍ (7 → 5)        |
| seq_####### | 98776  | 5          | 5           | 5         | SÍ (7 → 5)        |
| seq_####### | 98776  | 5          | 7           | 7         | NO (7 == 7)       |

- Si `effective_digits == original_padding` → Stage 4 no genera cambio; sin color en la tabla.
- El preview muestra `#####` (effective_digits hashes), no los user_digits solicitados.
- `min_digits_needed` se calcula en `build_selected_rows()` a partir de `item["last_frame"]`.
- El preview row almacena `"effective_digits"` y `"user_digits"` para referencia futura.

## Reglas de bloqueo

Una fila queda bloqueada y excluida del rename cuando:

- **Mismatch carpeta/seq**: en secuencias EXR el nombre de carpeta difiere del prefijo.
  - Ejemplo válido: carpeta `TEST_013_030_aPlate_v01` + secuencia `TEST_013_030_aPlate_v01_####.exr`
- **Conflicto de destino**: el destino ya existe en disco Y la fuente (`op.src`) también existe
  (ambas condiciones necesarias; si la fuente ya no existe significa que el rename fue exitoso
  y no hay conflicto real).
- **Destino duplicado en batch**: dos filas del mismo batch apuntan al mismo destino final.

## Ejecucion segura

La ejecucion usa dos fases para minimizar conflictos:

1. Renombra cada origen a nombre temporal unico (`.__rename_tmp_*__`).
2. Renombra temporales a destinos finales.

Incluye rollback basico si falla durante la segunda fase.

## Refresh de la tabla tras rename exitoso

Después de que `execute_ops` completa sin errores, `_run_rename` hace:

1. **Actualiza `self._table_rows`**: recorre todas las filas de la tabla principal y actualiza
   `item["path"]`, `item["name"]` e `item["first_file"]` para los ítems renombrados, usando
   el mapping `old_path → new_path` construido antes de ejecutar.
2. **`_update_rename_page()`**: reconstruye `_rename_selected_rows` desde los ítems actualizados
   (ya sin rutas obsoletas que causarían falsos "Destino ya existe").
3. **`_refresh_rename_preview()`**: reconstruye la tabla de rename con el estado actualizado.
4. **Restaura checkboxes**: por cada checkbox de la tabla de rename que existía antes, si su
   nuevo estado difiere del guardado, lo restaura llamando `chk.setChecked(was_checked)`, lo
   que dispara `_on_rename_chk_changed` y actualiza las celdas visualmente.

Los checkboxes de la **tabla principal** (`self._checkboxes`) no cambian.
Cuando el usuario vuelve a PAGE_MEDIA, `_rename_happened = True` dispara `_refresh_media_page()`
que re-escanea el disco y reconstruye la tabla principal con los nombres actualizados.

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
