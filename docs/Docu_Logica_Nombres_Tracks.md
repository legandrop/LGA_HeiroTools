> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Lógica de Nombres de Tracks del Timeline

Este documento centraliza la convención de nombres de tracks usada por las herramientas de Hiero / Nuke Studio en este repo.

## Objetivo

Separar claramente por dominio:

- tracks de **EXR por task** (renders publicados por cada task)
- tracks de **review MOV/MXF por task** (renders para revisar)
- tracks de **referencia editorial**
- tracks de **utilidad de viewer / timeline**

## Convención única para tasks

Para cada task hay dos tracks posibles:

| Tipo de track | Patrón del nombre | Ejemplos |
|---|---|---|
| EXR de la task | `_{task}_` | `_comp_`, `_roto_`, `_cleanup_` |
| Review MOV/MXF de la task | `_{task}Rev_` | `_compRev_`, `_rotoRev_`, `_cleanupRev_` |

El track `Rev` contiene archivos `.mov` o `.mxf` indistintamente según el proyecto. El sufijo `Rev` identifica la función (review), no el contenedor.

## Tasks vigentes

### Comp

| Dominio | Track | Variable |
|---|---|---|
| EXR | `_comp_` | `TRACK_comp_EXR` |
| Review MOV/MXF | `_compRev_` | `TRACK_comp_REV` |

### Roto

| Dominio | Track | Variable |
|---|---|---|
| EXR | `_roto_` | `TRACK_roto_EXR` |
| Review MOV/MXF | `_rotoRev_` | `TRACK_roto_REV` |

### Cleanup

| Dominio | Track | Variable |
|---|---|---|
| EXR | `_cleanup_` | `TRACK_cleanup_EXR` |
| Review MOV/MXF | `_cleanupRev_` | `TRACK_cleanup_REV` |

## Listas centralizadas

Cualquier script que opere sobre "todas las tasks" debe iterar las listas y no hardcodear nombres.

- `TASK_EXR_TRACKS = [TRACK_comp_EXR, TRACK_roto_EXR, TRACK_cleanup_EXR]`
- `TASK_REV_TRACKS = [TRACK_comp_REV, TRACK_roto_REV, TRACK_cleanup_REV]`

## Tracks editoriales y auxiliares

- **`EditRef`** — Referencia editorial para navegación, in/out y comparaciones.
- **`EditRefClean`** — Variante limpia de referencia editorial usada por algunos scripts.
- **`aPlate`** — Track de plate para comparaciones de rango o imagen contra comp.
- **`BurnIn`** — Track auxiliar para overlays de viewer.

## Semántica

El nombre del track importa:

- `_comp_` = **EXR de la task comp**, no "cualquier EXR"
- `_roto_` = **EXR de la task roto**
- `_compRev_` = **MOV/MXF de review de comp**
- `_rotoRev_` = **MOV/MXF de review de roto**

Por lo tanto:

- si el script trabaja solo con una task, usar la variable específica (`TRACK_comp_EXR`, `TRACK_roto_REV`, etc.)
- si el script trabaja con todas las tasks EXR, iterar `TASK_EXR_TRACKS`
- si el script trabaja con todas las reviews, iterar `TASK_REV_TRACKS`

## Agregar una nueva task

Los pasos para sumar una task nueva son:

1. Agregar las variables en [LGA_NKS_Shared/LGA_NKS_GetClip.py](../LGA_NKS_Shared/LGA_NKS_GetClip.py):
   ```python
   TRACK_nueva_EXR = "_nueva_"
   TRACK_nueva_REV = "_nuevaRev_"
   ```
2. Sumarlas a las listas centralizadas:
   ```python
   TASK_EXR_TRACKS = [..., TRACK_nueva_EXR]
   TASK_REV_TRACKS = [..., TRACK_nueva_REV]
   ```
3. Revisar filtros por nombre de archivo, regex y detección de task en los scripts que ya soportan multi-task.
4. Revisar UI donde hay acciones específicas por task (ej. botones on/off del Review Panel).
5. Actualizar la tabla de tasks vigentes de este documento.
6. Revisar el estado en [Docu_MultiTask.md](Docu_MultiTask.md).

## Reglas de implementación

- No hardcodear nombres de track si ya existe una variable centralizada.
- Para selección por track EXR principal, preferir `track_name=None` cuando el comportamiento deba respetar `TRACK_comp_EXR`.
- Para lógica multi-task, iterar `TASK_EXR_TRACKS` o `TASK_REV_TRACKS` según corresponda.
- Nombres históricos en desuso: `_rev_`, `REV`, `_compMov_`. Toda documentación o código que los nombre como vigentes está desactualizada.

## Referencias técnicas

- **Módulo central:** [LGA_NKS_Shared/LGA_NKS_GetClip.py](../LGA_NKS_Shared/LGA_NKS_GetClip.py)
  - Variables: `TRACK_comp_EXR`, `TRACK_comp_REV`, `TRACK_roto_EXR`, `TRACK_roto_REV`, `TRACK_cleanup_EXR`, `TRACK_cleanup_REV`, `TASK_EXR_TRACKS`, `TASK_REV_TRACKS`
  - Funciones: `get_clip_to_process()`, `get_clips_to_process()`, `find_clip_at_playhead_in_track()`

- **Estado multi-task por script:** [Docu_MultiTask.md](Docu_MultiTask.md)

- **Selección de clips:** [Docu_Metodos_Seleccion_Clip.md](Docu_Metodos_Seleccion_Clip.md)

- **Push multi-task:** [LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py)
  - Funciones: `push_from_selected_clips()`, `_show_task_selection_dialog()`

- **Pull multi-task:** [LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py](../LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py)
  - Métodos: `HieroOperations.process_selected_clips()`, `HieroOperations.change_to_highest_version()`

- **Review on/off por track:** [LGA_NKS_Review_Panel.py](../LGA_NKS_Review_Panel.py)
  - Métodos: `execute_DisableEXR()`, `execute_DisableRoto()`

- **Wrapper roto:** [LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py](../LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py)
  - Función: `main()`
