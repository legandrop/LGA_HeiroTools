> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Lógica de Nombres de Tracks del Timeline

Este documento centraliza la convención de nombres de tracks usada por las herramientas de Hiero / Nuke Studio en este repo.

## Objetivo

La idea es separar claramente:

- tracks de **tasks EXR** que representan renders publicados por task
- tracks de **review MOV/MXF**
- tracks de **referencia editorial**
- tracks de **utilidad de viewer o timeline**

Cuando se agrega una nueva task, la convención debe quedar definida aquí y en `LGA_NKS_Shared/LGA_NKS_GetClip.py`.

## Tracks vigentes

### Tasks EXR

- **`_comp_`**
  - Variable: `TRACK_comp_EXR`
  - Significado: track con los renders EXR de la task **comp**
  - Uso típico: selección principal de clips, comparación contra aPlate, push/pull de estados, on/off de EXR

- **`_roto_`**
  - Variable: `TRACK_roto_EXR`
  - Significado: track con los renders EXR de la task **roto**
  - Uso típico: push/pull multi-task, on/off de roto, futuros flujos equivalentes a comp cuando corresponda

- **Lista centralizada**
  - Variable: `TASK_EXR_TRACKS`
  - Valor actual: `[TRACK_comp_EXR, TRACK_roto_EXR]`
  - Regla: cualquier script que opere sobre "todas las tasks EXR" debe iterar esta lista y no hardcodear `_comp_` ni `_roto_`

### Review MOV/MXF

- **`_compMov_`**
  - Variable: `TRACK_comp_REV`
  - Significado: track con renders MOV/MXF de review de la task **comp**
  - Reemplaza los nombres históricos `_rev_` y `REV`

### Tracks editoriales y auxiliares

- **`EditRef`**
  - Referencia editorial para navegación, in/out y comparaciones

- **`EditRefClean`**
  - Variante limpia de referencia editorial usada por algunos scripts

- **`aPlate`**
  - Track de plate usado para comparaciones de rango o imagen contra comp

- **`BurnIn`**
  - Track auxiliar para overlays de viewer

## Regla funcional

La semántica del nombre del track importa:

- `_comp_` no significa "cualquier EXR"; significa **EXR de la task comp**
- `_roto_` no significa "otro track cualquiera"; significa **EXR de la task roto**
- `_compMov_` significa **MOV/MXF de review de comp**

Por lo tanto:

- si el script trabaja solo con comp, debe usar `TRACK_comp_EXR`
- si el script trabaja solo con roto, debe usar `TRACK_roto_EXR`
- si el script trabaja con todas las tasks EXR, debe usar `TASK_EXR_TRACKS`
- si el script trabaja con review MOV/MXF de comp, debe usar `TRACK_comp_REV`

## Próxima expansión: `_cleanup_`

La próxima task prevista es **cleanup**.

Cuando se incorpore, la expansión correcta es:

1. Agregar `TRACK_cleanup_EXR = "_cleanup_"` en `LGA_NKS_Shared/LGA_NKS_GetClip.py`
2. Incluirla en `TASK_EXR_TRACKS`
3. Revisar filtros por nombre de archivo, regex y detección de task
4. Revisar UI donde hoy existen acciones específicas para `_comp_` o `_roto_`
5. Actualizar esta documentación y los `.md` funcionales relacionados

## Reglas de implementación

- No hardcodear nombres de track si ya existe una variable centralizada.
- Para selección por track EXR principal, preferir `track_name=None` cuando el comportamiento deba respetar `TRACK_comp_EXR`.
- Para lógica multi-task, iterar `TASK_EXR_TRACKS`.
- Toda documentación que nombre `_rev_` como track actual está desactualizada; el nombre vigente es `_compMov_`.

## Referencias técnicas

- **Módulo central:** `/Users/leg4/.nuke/Python/Startup/LGA_NKS_Shared/LGA_NKS_GetClip.py`
  - Variables: `TRACK_comp_EXR`, `TRACK_comp_REV`, `TRACK_roto_EXR`, `TASK_EXR_TRACKS`
  - Funciones: `get_clip_to_process()`, `get_clips_to_process()`, `find_clip_at_playhead_in_track()`

- **Selección de clips:** `/Users/leg4/.nuke/Python/Startup/docs/Docu_Metodos_Seleccion_Clip.md`
  - Secciones: método híbrido, configuración, uso del módulo centralizado

- **Push multi-task:** `/Users/leg4/.nuke/Python/Startup/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py`
  - Funciones: `push_from_selected_clips()`, `_show_task_selection_dialog()`

- **Pull multi-task:** `/Users/leg4/.nuke/Python/Startup/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py`
  - Métodos: `HieroOperations.process_selected_clips()`, `HieroOperations.change_to_highest_version()`

- **Review on/off por track:** `/Users/leg4/.nuke/Python/Startup/LGA_NKS_Review_Panel.py`
  - Métodos: `execute_DisableEXR()`, `execute_DisableRoto()`

- **Wrapper roto:** `/Users/leg4/.nuke/Python/Startup/LGA_NKS_Review_Panel_py/LGA_NKS_Clip_DisableRoto.py`
  - Función: `main()`
