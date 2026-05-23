# Extracción de Project Name — Patrón Canónico

**Fecha:** 2026-05-22  
**Afecta a:** todos los scripts que busquen shots/tasks en la DB de PipeSync usando `project_name`.

---

## El problema

El método histórico extraía el nombre del proyecto del primer bloque del filename:

```
MOR_1048_060_Compo_v012.%04d.exr  →  "MOR"
```

Esto falla cuando el proyecto tiene nombre largo en la DB pero un prefijo corto en los shots:

| Folder en disco  | En DB      | Desde filename |
|------------------|------------|----------------|
| `VFX-MORLASP`    | `MORLASP`  | `MOR` ❌        |
| `VFX-BRDA`       | `BRDA`     | `BRDA` ✓ (coincide de casualidad) |
| `VFX-PHLDA`      | `PHLDA`    | `PHLDA` ✓      |

El resultado: `find_shot("MOR", ...)` no encuentra nada aunque el shot exista en la DB como proyecto `MORLASP`.

---

## La solución

Los proyectos **siempre** viven en una carpeta raíz con el patrón `VFX-NOMBRE`:

```
T:/VFX-MORLASP/101/MOR_1048_060/Comp/4_publish/...
     ^^^^^^^^^^
     segmento con prefijo "VFX-"
```

El nombre del proyecto en la DB es el segmento **sin el prefijo `VFX-`**:

```
"VFX-MORLASP"  →  "MORLASP"
"VFX-BRDA"     →  "BRDA"
"VFX-KTCE"     →  "KTCE"
```

---

## Funciones disponibles en `LGA_NKS_Flow_NamingUtils`

```python
from LGA_NKS_Flow_NamingUtils import extract_project_name_from_path, extract_project_name

# Primario: desde la ruta del archivo
project_name = extract_project_name_from_path(file_path)

# Fallback: desde el nombre base del archivo (comportamiento histórico)
if not project_name:
    project_name = extract_project_name(base_name)
```

### `extract_project_name_from_path(file_path)`
- Recorre los segmentos de la ruta normalizada.
- Devuelve el texto después del primer `VFX-` (case-insensitive).
- Devuelve `None` si no encuentra el patrón → usar fallback.

### `extract_project_name(base_name)` _(fallback)_
- Devuelve el primer bloque del nombre base antes del primer `_`.
- Comportamiento original, sin cambios.

---

## Patrón de implementación

Buscar en cada script el bloque donde se extrae `project_name` y reemplazarlo:

### Antes
```python
project_name = extract_project_name(base_name)
debug_print(f"Project name: {project_name}")
```

### Después
```python
project_name = extract_project_name_from_path(file_path)
if project_name:
    debug_print(f"Project name (from path): {project_name}")
else:
    project_name = extract_project_name(base_name)
    debug_print(f"Project name (from filename fallback): {project_name}")
```

> `file_path` es la ruta completa del archivo del clip (obtenida antes de este punto en todos los scripts existentes).

---

## Scripts — estado de análisis

Leyenda:
- ✅ **Analizado · necesitaba cambio → aplicado**
- 🔵 **Analizado · no necesitaba cambio**
- ⬜ **Sin analizar todavía**

---

### Flow Pull / Push / Info

| Script | Estado |
|--------|--------|
| `LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py` | ✅ Actualizado v3.44 |
| `LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py` | ✅ Actualizado v4.01 |
| `LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push_connector.py` | ✅ Actualizado v1.01 — proceso separado; recibe file_path vía JSON |
| `LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py` | ⬜ |

### Assignee Panel

| Script | Estado |
|--------|--------|
| `LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assignee.py` | ⬜ |
| `LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Assign_Assignee.py` | ⬜ |
| `LGA_NKS_Assignee_Panel_py/LGA_NKS_Flow_Clear_Assignees.py` | ⬜ |

### Coordination Panel

| Script | Estado |
|--------|--------|
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShowInFlow.py` | ✅ Actualizado v1.29 — 3 call sites: `HieroOperations.process_clip()`, `ShowInFlowWorker.run()`, `ShowShotInFlowWorker.run()` |
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_Thumbs.py` | ✅ Actualizado v1.02 — fix en `get_project_name_from_clip()` |
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_CreateShot.py` | ✅ Actualizado v1.36 — fix en `get_selected_clips_info()` |
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ModifyShot.py` | 🔵 Analizado · hereda `get_selected_clips_info()` de CreateShot — fix automático con v1.36 |
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_CheckTimelineShots.py` | ✅ Actualizado v1.01 — fix en `_collect_shots_from_track()` |
| `LGA_NKS_Coordination_Panel_py/LGA_NKS_Flow_ShotPriority.py` | ⬜ |

### Edit Panel

| Script | Estado |
|--------|--------|
| `LGA_NKS_Edit_Panel_py/LGA_NKS_MatchVerToEXR.py` | ⬜ |

---

## Proyectos confirmados en DB (al 2026-05-22)

```
BRDA, ERSO, KTCE, MOR, MORLASP, PHLDA, TEST, VLLF
```

> Nota: `MOR` existe en la DB como proyecto separado. No confundir con el prefijo
> de los shot codes del proyecto `MORLASP` (cuyos shots empiezan con `MOR_`).
