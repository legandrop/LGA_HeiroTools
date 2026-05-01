# LGA_NKS_Flow_Shot_info

Muestra la informacion del shot y las versiones de la task seleccionada en el playhead, leyendo de `pipesync.db`.

Archivo: [LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py)

## Flujo general

1. Se resuelve la task del playhead (`comp` / `roto` / `cleanup`). Si hay varias tasks en el mismo frame, se abre `LGA_NKS_TaskSelectionDialog`.
2. Se parsea el nombre del clip para obtener `project_name` y `shot_code`.
3. Se consulta `pipesync.db` (`ShotGridManager`) y se arma una estructura `shot -> tasks -> versions -> comments`.
4. Si el timeline activo es un proyecto vendor (prefijo distinto al del clip) y el `Playlist Panel` esta registrado o el usuario es Master, se delega a `LGA_NKS_FlowPlaylist_Shot_info`.
5. La GUI (`GUIWindow`) lista cabecera del shot, descripcion, versiones y comentarios con thumbnails clickeables.

## Origen de los datos

Tablas usadas: `projects`, `shots`, `tasks`, `task_assignments`, `versions`, `version_notes`. Detalle en [Documentacion_DB PipeSync.md](../LGA_NKS_Flow_Panel_py/Documentacion_DB%20PipeSync.md).

Mapeo:

| Campo UI | Origen DB |
| --- | --- |
| `shot_code` | `shots.shot_name` |
| `description` | `tasks.task_description` (de la task resuelta) |
| `assignee` | `task_assignments.assigned_to` |
| Version `version_number` | `versions.version_number` (formateado `vNNN`) |
| Version `created_by` | `versions.created_by` |
| Version `version_description` | `versions.description` |
| Version `version_date` | `versions.created_on` |
| Comment `user` | `version_notes.created_by` |
| Comment `text` | `version_notes.content` |
| Comment `date` | `version_notes.created_on` |
| Comment `attachments` | `version_notes.local_attachment_paths` (separados por `;`) |

## Filtro de notas auto-generadas por upload de version

PipeSync, al subir una version, escribe en paralelo:

- `versions.description` con el mensaje del review.
- `version_notes` con un registro de mismo `content`, mismo `created_by` y `created_on` cercano al de la version.

Para no mostrar ese comentario duplicado, en `find_shot` se descarta toda `version_note` que cumpla:

1. `note.created_by == version.created_by` (mismo autor, comparado tras `strip()`).
2. `note.content.strip() == version.description.strip()` (mismo texto exacto).
3. `abs(note.created_on - version.created_on) <= VERSION_DUPLICATE_NOTE_WINDOW_SECONDS`.

La constante `VERSION_DUPLICATE_NOTE_WINDOW_SECONDS` (default `600`, 10 minutos) vive en el modulo y se puede ajustar. Si alguna fecha no se puede parsear pero el resto coincide, la nota se considera duplicada.

Helpers involucrados en `LGA_NKS_Flow_Shot_info.py`:

- `_parse_pipesync_datetime(value)`: parsea el formato `YYYY-MM-DD HH:MM:SS[+/-HH:MM]` que guarda SQLite a `datetime` con tzinfo.
- `_is_version_upload_duplicate_note(note, version_description, version_created_by, version_created_on)`: aplica las tres reglas anteriores.

## Vendor dispatch

`should_redirect_to_playlist_shot_info()` decide si la ejecucion se delega al Playlist Shot Info. Condicion: prefijo de proyecto != prefijo de clip Y (Playlist Panel registrado O usuario Master segun `LGA_NKS_Playlist_Panel_Permissions.is_current_user_master`).

## Prototipo standalone para iterar la UI

Para trabajar la UI sin tener que abrir Nuke, existe un script standalone:

- [LGA_NKS_Flow_Panel_py/_prototype_shot_info.py](../LGA_NKS_Flow_Panel_py/_prototype_shot_info.py)

Que hace:

- Replica la UI del `FlowNotesPopover` de PipeSync 2 (`src/features/shots/components/FlowNotesPopover.cpp` y `resources/styles/flow_notes.qss`).
- Usa **datos hardcodeados** del shot `ERSO_000_320` (task `Comp`), tomados de `pipesync.db`. No toca DB ni Nuke.
- Permite renderizar a PNG (`--screenshot preview.png`) o abrir la ventana interactiva.

Como ejecutar:

```
"C:/Users/leg4-pc/miniconda3/python.exe" _prototype_shot_info.py --screenshot preview.png
"C:/Users/leg4-pc/miniconda3/python.exe" _prototype_shot_info.py
```

### Dependencia temporal: PySide6

Para correr el prototipo se instalo `PySide6` en el python de miniconda con:

```
"C:/Users/leg4-pc/miniconda3/python.exe" -m pip install --user PySide6
```

> **TODO recordatorio**: cuando terminemos de iterar la UI y portemos los cambios al modulo productivo `LGA_NKS_Flow_Shot_info.py` (que usa el adapter `LGA_QtAdapter_HieroTools` para Hiero), **desinstalar `PySide6` del miniconda**:
>
> ```
> "C:/Users/leg4-pc/miniconda3/python.exe" -m pip uninstall -y PySide6 PySide6-Essentials PySide6-Addons shiboken6
> ```
>
> Y borrar tambien el script `_prototype_shot_info.py` y los `preview_*.png` generados.

### Notas sobre el rendering offscreen

El prototipo NO usa `QT_QPA_PLATFORM=offscreen` porque en Windows ese plugin no carga las fonts del sistema y todo aparece como cajitas. En su lugar, el modo screenshot mueve la ventana a `(-3000, -3000)` y la captura con `widget.grab()`.

## Pendiente

- Portar el resultado del prototipo al modulo productivo `LGA_NKS_Flow_Shot_info.py` una vez validada la UI.
- Sumar la consulta a `task_timelogs` para calcular `Time logged` por version (regex `v0*N` en `description`, sumar `duration` en minutos).
- Filtrar tambien notas duplicadas por `content` exacto (segun PipeSync hace en `displayedNoteContents`).
