> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Soporte Multi-Task en las herramientas de Hiero / Nuke Studio

Este documento describe el **objetivo** del soporte multi-task del pipeline, la **convención de nombres** que lo hace posible, y el **estado actual** de cada herramienta respecto de las tres tasks vigentes: **comp**, **roto**, **cleanup**.

Complementa a [Docu_Logica_Nombres_Tracks.md](Docu_Logica_Nombres_Tracks.md), que define la convención de nombres. Este documento se enfoca en **qué scripts ya soportan multi-task y cuáles todavía no**.

## 1. Objetivo

Históricamente las herramientas trabajaban únicamente con la task **comp** (un único track EXR `_comp_` y un único track de review). El pipeline hoy necesita operar con varias tasks en paralelo, cada una con su propio track de EXR y su propio track de review.

El objetivo es que **toda herramienta que toque tracks de task**:

1. Sepa recorrer todos los tracks de task disponibles (no solo comp).
2. Detecte a qué task pertenece cada clip por su nombre de track y/o su filename.
3. Actualice o consulte la task correcta en Flow/SG.
4. Nunca hardcodee el string `_comp_` como si fuera sinónimo de "cualquier task".

## 2. Convención de nombres (resumen)

Regla única:

- **EXR** de una task → `_{task}_` (ej: `_comp_`, `_roto_`, `_cleanup_`)
- **Review MOV/MXF** de una task → `_{task}Rev_` (ej: `_compRev_`, `_rotoRev_`, `_cleanupRev_`)

El track Rev puede contener `.mov` o `.mxf` según el proyecto; el nombre del track es siempre `_{task}Rev_`.

Todo está centralizado en [LGA_NKS_Shared/LGA_NKS_GetClip.py](../LGA_NKS_Shared/LGA_NKS_GetClip.py):

```python
TRACK_comp_EXR    = "_comp_"
TRACK_roto_EXR    = "_roto_"
TRACK_cleanup_EXR = "_cleanup_"

TRACK_comp_REV    = "_compRev_"
TRACK_roto_REV    = "_rotoRev_"
TRACK_cleanup_REV = "_cleanupRev_"

TASK_EXR_TRACKS = [TRACK_comp_EXR, TRACK_roto_EXR, TRACK_cleanup_EXR]
TASK_REV_TRACKS = [TRACK_comp_REV, TRACK_roto_REV, TRACK_cleanup_REV]
```

Los scripts deben importar estas variables o las listas y no hardcodear los strings.

## 3. Tasks y su estado en Flow / SG

Las tres tasks (**comp**, **roto**, **cleanup**) tienen en Flow/SG **sus propios status, versiones y assignee**. Es decir: un shot puede tener simultáneamente una task `comp` con status "Review Lega" y una task `roto` con status "In Progress", cada una con su propia historia de versiones.

## 4. Estado actual por herramienta

Leyenda:

- ✅ Soporta la task completamente
- 🟡 Soporta de forma parcial (ver nota)
- ❌ No soporta (hardcodeado a comp, o no existe)
- — No aplica

### 4.1. Módulo central — `LGA_NKS_Shared/LGA_NKS_GetClip.py`

| Dominio | comp | roto | cleanup |
|---|---|---|---|
| Variables `TRACK_*_EXR` | ✅ | ✅ | ✅ |
| Variables `TRACK_*_REV` | ✅ | ✅ | ✅ |
| Lista `TASK_EXR_TRACKS` | ✅ | ✅ | ✅ |
| Lista `TASK_REV_TRACKS` | ✅ | ✅ | ✅ |

Nada pendiente.

### 4.2. Flow Panel

| Script | comp EXR | roto EXR | cleanup EXR | comp Rev | roto Rev | cleanup Rev |
|---|---|---|---|---|---|---|
| [LGA_NKS_Flow_Pull.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py) | ✅ | ✅ | ✅ | — | — | — |
| [LGA_NKS_Flow_Push.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py) | ✅ | ✅ | 🟡 | — | — | — |
| [LGA_NKS_Flow_Shot_info.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py) | ✅ | ❓ | ❓ | — | — | — |
| [LGA_NKS_ReviewPic.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_ReviewPic.py) | ✅ | ❓ | ❓ | — | — | — |

**Flow Pull — notas:**
- Multi-task completo (v3.41). El filtro de filename acepta cualquier task de `TASK_EXR_TRACKS` (`_comp_`, `_roto_`, `_cleanup_`); antes hardcodeaba `_comp_` y descartaba roto/cleanup.
- Comparación de versión SG vs NKS por task: `find_highest_version_for_task(shot, task, task_name)` ([Flow_Pull.py:312](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py:312)) recorre solo `task["versions"]` de la task detectada y devuelve el string como `_{task}_v{n}`. Antes mezclaba todas las tasks del shot y rotulaba como `_comp_`, lo que producía falsos mismatches (ej: comp v9 en NKS comparado contra roto v33 en SG).
- Tabla de cambios incluye columna `Task` (la detectada del filename), para distinguir a qué task corresponden la versión y el status mostrados.

**Flow Push — notas:**
- v3.97 implementó multi-task correctamente: itera `TASK_EXR_TRACKS`, detecta la task del filename y, cuando hay clips de varias tasks seleccionadas, muestra un diálogo para elegir a cuál aplicar el status (`_show_task_selection_dialog`, [Flow_Push.py:2325](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py:2325)).
- Para cleanup: apenas se agregue a `TASK_EXR_TRACKS` (ya hecho), Push lo detecta automáticamente. Pendiente validar con timeline real.
- [Flow_Push.py:839](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py:839) tiene `get_comp_assignee()` que busca siempre la task "comp" del shot para decidir el assignee. → **Pendiente revisar:** definir si el assignee del shot debe venir siempre de comp o depender de la task activa.

**Flow Shot_info y ReviewPic:** no auditados en detalle. Posibles hardcodes a revisar.

### 4.3. Review Panel

| Script | comp | roto | cleanup | Notas |
|---|---|---|---|---|
| [LGA_NKS_Clip_DisableEXR.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableEXR.py) | ✅ | ✅ | ✅ | Parametrizado con `track_name=TRACK_*_EXR` |
| [LGA_NKS_Clip_DisableRoto.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py) | — | ✅ | — | Wrapper de DisableEXR con `TRACK_roto_EXR` |
| **Wrapper cleanup** | — | — | ❌ | **Pendiente crear** `LGA_NKS_Clip_DisableCleanup.py` |
| [LGA_NKS_EXRTrack_Difference.py](../LGA_NKS_Review_Panel_py/LGA_NKS_EXRTrack_Difference.py) | ✅ | ❌ | ❌ | Hardcodeado a `TRACK_comp_EXR` |
| [LGA_NKS_Compare_Versions.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Compare_Versions.py) | ✅ | ❌ | ❌ | Hardcodeado a `TRACK_comp_EXR` |
| [LGA_NKS_Compare_Versions_OFF.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Compare_Versions_OFF.py) | ✅ | ❌ | ❌ | Hardcodeado a `TRACK_comp_EXR` |
| [LGA_NKS_ON_Clips_OFF_v00-Clips.py](../LGA_NKS_Review_Panel_py/LGA_NKS_ON_Clips_OFF_v00-Clips.py) | ✅ | ❌ | ❌ | Regex `_comp_v(\d{2,3})` hardcodeado; no detecta roto/cleanup |

**Pendiente en Review Panel:**
- Agregar botón y wrapper `ON OFF _cleanup_` análogo a los de comp y roto.
- Decidir si las herramientas de diferencia/comparación deben operar por task o solo sobre comp.
- Reemplazar regex hardcodeados por patrón que use `TASK_EXR_TRACKS`.

### 4.4. Edit Panel

| Script | comp EXR | roto EXR | cleanup EXR | comp Rev | roto Rev | cleanup Rev |
|---|---|---|---|---|---|---|
| [LGA_NKS_MatchVerToEXR.py](../LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py) | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| [LGA_NKS_CompareVerToEditref.py](../LGA_NKS_Edit_Panel_py/LGA_NKS_CompareVerToEditref.py) | — | — | — | ✅ | ❌ | ❌ |
| [LGA_NKS_CompareEXR_to_aPlate.py](../LGA_NKS_Edit_Panel_py/LGA_NKS_CompareEXR_to_aPlate.py) | ✅ | ❌ | ❌ | — | — | — |

**Pendiente en Edit Panel:**
- MatchVerToEXR: hoy matchea la versión de `_comp_` con `_compRev_`. Cuando roto/cleanup tengan review, extender para operar por task iterando las listas.
- CompareVerToEditref: hoy compara rangos solo del track `_compRev_` contra EditRef. Evaluar si debe operar también sobre `_rotoRev_` y `_cleanupRev_`.

### 4.5. Coordination, Assignee, ViewerTL

No auditados en detalle para este documento. El assignee por task ya funciona en parte porque Flow/SG devuelve assignees por task, pero hay lugares (ej. el `get_comp_assignee` del Push) donde la task está hardcoded a comp. Revisar caso por caso.

## 5. Advertencia de Task / Track Mismatch

Cuando la **task detectada en el filename** de un clip no coincide con el **nombre del track** donde el clip está ubicado, las herramientas muestran una ventana informativa al finalizar la operación.

Ejemplo: un clip llamado `SHOW_SEQ_SHOT_comp_v003.exr` ubicado en el track `_roto_`.

### Política

- **Solo informa**, no bloquea ni modifica el procesamiento.
- El procesamiento real sigue usando la task **del filename** (comportamiento histórico): en el ejemplo anterior, se actualiza la task `comp` en SG.
- El usuario decide si renombra el clip, lo mueve de track, o ignora el aviso.

### Dónde aplica

| Herramienta | Cuándo aparece la ventana |
|---|---|
| Flow Pull | Al finalizar, después de procesar todos los clips |
| Flow Push | Al iniciar, antes del diálogo de selección de task |

### Formato

Una fila por clip con tres columnas: **Clip**, **Task (filename)**, **Track**.

### Implementación

- Helper compartido: [LGA_NKS_Shared/LGA_NKS_TaskMismatchDialog.py](../LGA_NKS_Shared/LGA_NKS_TaskMismatchDialog.py)
  - `collect_task_mismatches(...)`: arma la lista de mismatches.
  - `show_task_mismatch_warning(...)`: muestra la ventana modal.
- Usado por [Flow_Pull.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py) y [Flow_Push.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py).

## 6. Roadmap resumido

Lista de pendientes concretos, en orden sugerido:

1. **Review Panel** — crear wrapper y botón para `ON OFF _cleanup_`.
2. **Review Panel** — revisar regex hardcoded de `_comp_v` en `LGA_NKS_ON_Clips_OFF_v00-Clips.py`.
3. **Flow Push** — decidir política del assignee del shot (`get_comp_assignee`) y ajustar si corresponde.
4. **Edit Panel** — extender MatchVerToEXR y CompareVerToEditref a operar por task iterando `TASK_EXR_TRACKS` / `TASK_REV_TRACKS`.
5. **Review Panel** — evaluar si EXRTrack_Difference y Compare_Versions deben trabajar por task o seguir siendo comp-only.
6. **Scripts no auditados** — pasar el filtro de hardcodes por Coordination, Assignee, ViewerTL, Shot_info, ReviewPic.

## 7. Tests manuales sugeridos

Con un timeline que tenga un shot con clips en `_comp_`, `_roto_`, `_cleanup_`, `_compRev_`, `_rotoRev_`, `_cleanupRev_`:

- Flow Pull (Shift+Click = solo shot seleccionado):
  - El clip `_comp_` debe recibir color del status de la task comp.
  - El clip `_roto_` debe recibir color del status de la task roto.
  - El clip `_cleanup_` debe recibir color del status de la task cleanup.
  - La tabla de cambios debe mostrar la columna `Task` con `comp`/`roto`/`cleanup` según el filename del clip.
- Flow Push con un status:
  - Seleccionar clips de varias tasks → debe mostrar el diálogo preguntando a cuál aplicar.
  - Aplicar a una sola task → el status debe escribirse únicamente en esa task en SG.
- Review Panel:
  - `ON OFF _comp_` (Shift+D) alterna el clip de `_comp_`.
  - `ON OFF _roto_` (Ctrl+Shift+D) alterna el clip de `_roto_`.
  - `ON OFF _cleanup_` todavía no existe (pendiente).

## 8. Referencias técnicas

- **Convención de nombres:** [Docu_Logica_Nombres_Tracks.md](Docu_Logica_Nombres_Tracks.md)
- **Selección de clips:** [Docu_Metodos_Seleccion_Clip.md](Docu_Metodos_Seleccion_Clip.md)
- **Módulo central:** [LGA_NKS_Shared/LGA_NKS_GetClip.py](../LGA_NKS_Shared/LGA_NKS_GetClip.py)
  - Variables: `TRACK_comp_EXR`, `TRACK_roto_EXR`, `TRACK_cleanup_EXR`, `TRACK_comp_REV`, `TRACK_roto_REV`, `TRACK_cleanup_REV`, `TASK_EXR_TRACKS`, `TASK_REV_TRACKS`
- **Flow Pull:** [LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py)
  - Métodos: `HieroOperations.process_selected_clips()`, `HieroOperations.enable_or_disable_clips()`, `SGManager.find_highest_version_for_task()`
- **Flow Push:** [LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py)
  - Funciones: `push_from_selected_clips()`, `_show_task_selection_dialog()`, `get_comp_assignee()`
- **Review Panel (panel):** [LGA_NKS_Review_Panel.py](../LGA_NKS_Review_Panel.py)
  - Métodos: `execute_DisableEXR()`, `execute_DisableRoto()`
- **Review Panel (wrappers):** [LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableEXR.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableEXR.py), [LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py)
- **Edit Panel:** [LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py](../LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py), [LGA_NKS_Edit_Panel_py/LGA_NKS_CompareVerToEditref.py](../LGA_NKS_Edit_Panel_py/LGA_NKS_CompareVerToEditref.py)
- **Advertencia Task/Track Mismatch:** [LGA_NKS_Shared/LGA_NKS_TaskMismatchDialog.py](../LGA_NKS_Shared/LGA_NKS_TaskMismatchDialog.py)
  - Funciones: `collect_task_mismatches()`, `show_task_mismatch_warning()`
