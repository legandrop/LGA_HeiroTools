# LGA_NKS Create v000 - Plan de implementacion

Ubicacion de este documento:

`C:\Users\leg4-pc\.nuke\LGA_NKS_CreateV000_Plan.md`

Este MD queda fuera de `C:\Users\leg4-pc\.nuke\Python\Startup` porque esa carpeta esta siendo modificada y no se debe pisar durante esta etapa.

---

## 1. Objetivo

Agregar al Edit Panel de Hiero un boton llamado `Create v000`.

El boton abrira una ventana de validacion/configuracion para crear, en una fase posterior, una secuencia de EXR negros para el shot activo.

La secuencia se nombrara segun el shot y la task elegida:

- `SHOT_comp_v000`
- `SHOT_roto_v000`
- `SHOT_cleanup_v000`

En esta primera etapa no se implementa la creacion real de EXR. El boton `Create v000` dentro del dialogo queda como stub: valida y muestra/imprime los parametros recolectados.

---

## 2. Decisiones confirmadas

| Tema | Decision |
| --- | --- |
| Boton en el panel | Agregar `Create v000` inmediatamente despues de `Set Shot Name` |
| Color del boton | Mismo color que `Set Shot Name`: `#453434` |
| Tracks de plate | Cualquier track cuyo nombre matchee `*plate`, case-insensitive |
| Default de plates | Solo el primer plate de la lista, entendido como el track `*plate` mas alto |
| Default de task | `comp` |
| Tasks disponibles | `comp`, `roto`, `cleanup` |
| Task ya existente | Si ya existe version en el track de esa task (`_comp_`, `_roto_`, `_cleanup_`), esa task debe aparecer deshabilitada |
| Default de resolucion | Resolucion del timeline |
| Version | Siempre `v000` fija |
| Primer frame de salida | Siempre `1001`, sin importar el `timelineIn()` |
| Naming de frames | Sin punto antes del frame: `SHOT_task_v000_1001.exr` |
| Scope actual | Solo UI + recoleccion de datos + preview; no renderizar EXR todavia |

---

## 3. Path y naming

Los plates viven siempre dentro de:

```text
RutaProyecto/Secuencia/Shotname/_input
```

Las secuencias v000 deben publicarse en:

```text
RutaProyecto/Secuencia/Shotname/Comp/4_publish/SHOT_comp_v000/SHOT_comp_v000_1001.exr
RutaProyecto/Secuencia/Shotname/Roto/4_publish/SHOT_roto_v000/SHOT_roto_v000_1001.exr
RutaProyecto/Secuencia/Shotname/Cleanup/4_publish/SHOT_cleanup_v000/SHOT_cleanup_v000_1001.exr
```

Ejemplo dado:

```text
T:\VFX-MOR\101\MOR_1001C_010\Comp\4_publish\MOR_1001C_010_comp_v005\MOR_1001C_010_comp_v005_1001.exr
```

Para `v000`, la salida esperada seria:

```text
T:\VFX-MOR\101\MOR_1001C_010\Comp\4_publish\MOR_1001C_010_comp_v000\MOR_1001C_010_comp_v000_1001.exr
```

Regla para calcular el path:

1. Tomar el path de un plate del shot, idealmente el plate default.
2. Encontrar el directorio `_input`.
3. Subir un nivel para obtener el root del shot.
4. Agregar la carpeta de task:
   - `Comp`
   - `Roto`
   - `Cleanup`
5. Agregar `4_publish`.
6. Agregar carpeta/version:
   - `SHOT_comp_v000`
   - `SHOT_roto_v000`
   - `SHOT_cleanup_v000`
7. Armar el patron de nombre:
   - `SHOT_task_v000_####.exr` para preview
   - `SHOT_task_v000_1001.exr`, `1002`, etc. para los frames reales en fase 2

---

## 4. UI propuesta

Ventana modal:

```text
+--------------------------------------------------------------+
| Create v000 - MOR_1001C_010                                  |
+--------------------------------------------------------------+
|                                                              |
| FRAME RANGE                                                  |
| Multi-select: define el IN/OUT del v000                      |
|                                                              |
| [x] aPlate      TL IN 1015   TL OUT 1112   98 frames         |
| [ ] bPlate      TL IN 1020   TL OUT 1080   61 frames         |
| [ ] cPlate      TL IN 1015   TL OUT 1100   86 frames         |
|                                                              |
| v000 timeline range: 1015 - 1112 (98 frames)                 |
| v000 source range:   1001 - 1098                             |
|                                                              |
| RESOLUTION                                                   |
| Single-select                                                |
|                                                              |
| ( ) aPlate       2048 x 858                                  |
| ( ) bPlate       3840 x 2160                                 |
| (*) Timeline     1920 x 1080                                 |
|                                                              |
| TASK                                                         |
|                                                              |
| [ comp ]    [ roto ]    [ cleanup ]                          |
|                                                              |
| Si una task ya tiene version en su track, aparece disabled.  |
| Ejemplo: comp disabled - existing _comp_ v003                |
|                                                              |
| OUTPUT                                                       |
| Path: T:\VFX-MOR\101\MOR_1001C_010\Roto\4_publish\           |
|       MOR_1001C_010_roto_v000\                               |
| Name: MOR_1001C_010_roto_v000_####.exr                       |
| Frames: 1001 - 1098 (98 frames)                              |
| Resolution: 1920 x 1080 (Timeline)                           |
|                                                              |
|                                      [ Cancel ] [ Create v000 ]|
+--------------------------------------------------------------+
```

### 4.1 Seccion Frame Range

Debe listar todos los clips `*plate` correspondientes al shot.

Por cada plate mostrar:

- checkbox
- nombre del track
- `timelineIn()`
- `timelineOut()`
- cantidad de frames
- opcionalmente path corto o nombre del clip si entra limpio en la UI

Comportamiento:

- Solo el primer plate de la lista aparece tildado por defecto.
- Al tildar varios plates:
  - `timeline_in` del v000 = el menor `timelineIn()` de los plates seleccionados
  - `timeline_out` del v000 = el mayor `timelineOut()` de los plates seleccionados
  - `frame_count` = cantidad total de frames resultante
- Si no hay ningun plate seleccionado:
  - `Create v000` disabled
  - mostrar warning: `Select at least one plate`

Nota de implementacion:

- Confirmar en Hiero si el orden de `seq.videoTracks()` coincide con el orden visual esperado para "track mas alto".
- Si no coincide, invertir/ordenar segun el indice real del track para que el default sea efectivamente el plate visualmente mas alto.

### 4.2 Seccion Resolution

Debe ser single-select, preferentemente con radio buttons o `QButtonGroup` exclusivo.

Opciones:

- una opcion por cada plate listado
- una opcion `Timeline`

Default:

- `Timeline`

Datos a mostrar:

- `width x height`
- nombre de la fuente de resolucion (`aPlate`, `bPlate`, `Timeline`, etc.)

Comportamiento:

- Cambiar resolucion no cambia el range ni el path.
- Solo actualiza el resumen de salida.

### 4.3 Seccion Task

Tres toggles exclusivos:

- `comp`
- `roto`
- `cleanup`

Default:

- `comp`, salvo que este deshabilitado por version existente.

Regla de disabled:

- Analizar los tracks EXR de task:
  - `_comp_`
  - `_roto_`
  - `_cleanup_`
- Si ya existe un clip/version de esa task para el shot, el toggle queda disabled.
- El usuario no debe poder crear una `v000` para una task que ya tiene version en timeline.

Si `comp` esta disabled:

- elegir automaticamente la primera task disponible en orden `roto`, `cleanup`.
- si las tres estan disabled, deshabilitar `Create v000` y mostrar un mensaje claro.

Mensaje sugerido:

```text
All tasks already have versions in timeline.
```

O por task:

```text
comp disabled - existing _comp_ v003
```

### 4.4 Seccion Output

Preview read-only con:

- directorio destino
- patron de nombre
- source frame range resultante
- cantidad de frames
- resolucion elegida
- task elegida

Debe actualizarse en vivo cuando cambian:

- plates seleccionados
- task
- resolucion

Preview de nombre:

```text
MOR_1001C_010_comp_v000_####.exr
```

Aunque el render real, en fase 2, escriba:

```text
MOR_1001C_010_comp_v000_1001.exr
MOR_1001C_010_comp_v000_1002.exr
...
```

### 4.5 Botones inferiores

`Cancel`

- Cierra sin hacer nada.

`Create v000`

- En esta fase no genera EXR.
- Debe recolectar el estado final y hacer `print()` o log de un diccionario con parametros.
- Luego puede cerrar el dialogo.

---

## 5. Informacion a obtener y donde ya existe

Regla general: no redescubrir. Buscar y copiar/adaptar patrones existentes.

### 5.1 Boton e integracion con Edit Panel

Archivo:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel.py
```

Referencias verificadas:

- Lista de botones: `self.buttons`
- Boton actual:
  - `("Set Shot Name", self.set_shot_name, "#453434", None, ...)`
- El nuevo boton va inmediatamente despues.
- Reusar color `#453434`.
- Patron de ejecucion externa:
  - `execute_external_script("LGA_NKS_SetShotName.py")`
  - `importlib.util.spec_from_file_location(...)`
  - `importlib.util.module_from_spec(...)`
  - `spec.loader.exec_module(module)`

Handler futuro sugerido:

```python
def create_v000(self):
    result = self.execute_external_script("LGA_NKS_CreateV000.py")
```

O, si el script necesita llamar una funcion especifica:

```python
module.open_create_v000_dialog()
```

Siguiendo el patron existente del panel.

### 5.2 Shot activo / seleccion inteligente

Archivo:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_GetClip.py
```

Referencias verificadas:

- `get_clip_to_process(track_name=None, prioritize_multiple_selection=False)`
- `find_clip_at_playhead_in_track(seq, track_name=None)`
- `TRACK_comp_EXR = "_comp_"`
- `TRACK_roto_EXR = "_roto_"`
- `TRACK_cleanup_EXR = "_cleanup_"`
- `TASK_EXR_TRACKS = [TRACK_comp_EXR, TRACK_roto_EXR, TRACK_cleanup_EXR]`

Uso recomendado:

- Usar `hiero.ui.activeSequence()` para obtener sequence.
- Usar playhead y/o seleccion con el mismo criterio de los scripts existentes.
- Para la task existente, usar `find_clip_at_playhead_in_track()` sobre cada track de task.

### 5.3 Task bajo playhead

Archivo:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_TaskSelectionDialog.py
```

Referencias verificadas:

- `get_tasks_at_playhead(seq)`
- `resolve_task_at_playhead(seq, title="Select task")`
- `track_for_task(task_name)`

Nota:

- Para este feature, el default confirmado es `comp`, no "task bajo playhead".
- Aun asi, este archivo sirve para copiar el mapeo task/track y el patron de dialogo modal simple.

### 5.4 Timeline IN/OUT y playhead

Archivos:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_Trim_In.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_Trim_Out.py
```

Referencias verificadas:

- `clip.timelineIn()`
- `clip.timelineOut()`
- `clip.sourceIn()`
- `clip.sourceOut()`
- `hiero.ui.activeSequence()`
- `hiero.ui.currentViewer()`
- `player.time()`

Uso recomendado:

- Copiar el tratamiento de `timelineIn()` / `timelineOut()`.
- Mantener la misma interpretacion de rangos que usan esos scripts para evitar off-by-one.

Punto a cuidar:

- En Hiero, segun la API y el uso local, confirmar si `timelineOut()` se trata como frame incluido o limite de salida.
- El calculo de `frame_count` debe seguir la convencion usada en `Trim_In`, `Trim_Out` y comparadores existentes.

### 5.5 Path del media y nombre del shot

Archivo:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_SetShotName.py
```

Referencias verificadas:

- `shot.source().mediaSource().fileinfos()[0].filename()`
- `hiero.ui.activeSequence()`
- fallback de nombre de shot desde path

Archivo adicional:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_Flow_NamingUtils.py
```

Referencias verificadas:

- `extract_shot_code(base_name)`
- `clean_base_name(file_name)`
- `extract_task_name(base_name)`

Uso recomendado:

- Obtener filename del plate.
- Limpiar basename.
- Extraer shot code con `extract_shot_code()` cuando sea posible.
- Mantener compatibilidad con la spec de naming existente.

Docs relacionadas:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\docs\Docu_Naming_Compatibility_Specification.md
```

### 5.6 Listar plates

Archivos de referencia:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CompareEXR_to_aPlate.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_SetShotName.py
```

Referencias verificadas en `CompareEXR_to_aPlate.py`:

- busqueda de track `aPlate`
- iteracion de `seq.videoTracks()`
- `track.items()`
- ignorar `hiero.core.EffectTrackItem`
- acceso a `clip.source().mediaSource().fileinfos()`

Para este script:

- No limitar a `aPlate`.
- Filtrar cualquier track cuyo nombre termine o matchee `plate` de forma case-insensitive.
- Ejemplos esperados:
  - `aPlate`
  - `bPlate`
  - `cPlate`
  - cualquier otro `*plate`

### 5.7 Resolucion de plates

Archivo principal de referencia:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CompareEXR_to_aPlate.py
```

Referencias utiles:

- `clip.source().mediaSource()`
- `mediaSource().fileinfos()`
- `mediaSource().metadata()`

Implementacion probable:

- Intentar obtener resolucion desde metadata/mediaSource/fileinfo segun patron local.
- Si un plate no devuelve resolucion, mostrar `N/A` y no permitir elegirlo como fuente de resolucion.
- Mantener siempre disponible `Timeline`.

### 5.8 Resolucion del timeline

Uso esperado:

```python
fmt = seq.format()
width = fmt.width()
height = fmt.height()
```

Default confirmado:

- `Timeline`

### 5.9 Deteccion de versiones existentes por task

Archivos:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_GetClip.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_MatchVerToEXR.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-Clip_ScanVersions.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-Clip_ScanVersions_v2.py
```

Referencias verificadas:

- `find_clip_at_playhead_in_track(seq, track_name)`
- `extract_version_number(version_str)`
- regex: `r"_v(\d+)(?:[-\(][^)]+)?"`
- version scanner:
  - `hiero.core.VersionScanner()`
  - `binItem.items()`
  - `binItem.activeVersion()`

Logica para este feature:

1. Para cada task:
   - `comp -> _comp_`
   - `roto -> _roto_`
   - `cleanup -> _cleanup_`
2. Buscar si hay clip de esa task en el rango/playhead del shot.
3. Si existe:
   - extraer version desde filename o bin item.
   - marcar task como disabled.
4. Si no existe:
   - task habilitada.

Decision funcional:

- No detectar "proxima version".
- No crear `v001`, `v002`, etc.
- Si ya existe cualquier version de esa task, no se ofrece crear `v000` para esa task.

### 5.10 Building Blocks utiles

Rutas verificadas dentro de `Python\Startup`:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Bin\LGA_H-Bin-GetClipPath_FromObject.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-Clip_ScanVersions.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-Clip_ScanVersions_v2.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\LGA_H-Clip_ScanVersions.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\LGA_H-Clip_ScanVersions_v2.py
```

Nota:

- Existe tambien `C:\Users\leg4-pc\.nuke\+Building_Blocks`, pero los scripts relevantes encontrados estan en `C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks`.

### 5.11 Estilo UI

Archivos:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_StyleUtils.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\README_StyleUtils.md
C:\Users\leg4-pc\.nuke\Python\Startup\docs\LGA_NKS_Panel_Style_Guide.md
C:\Users\leg4-pc\.nuke\Python\Startup\docs\GUI_Windows_Reference.md
```

Referencias verificadas:

- `calculate_dynamic_border(style)`
- `calculate_dynamic_hover(style)`
- `create_tooltip_stylesheet(style)`
- texto de botones: `#d8d8d8`

UI recomendada:

- `QDialog`
- `QVBoxLayout` principal
- secciones con labels compactos
- `QTableWidget` o filas custom para plates
- `QButtonGroup` para resoluciones
- `QButtonGroup` exclusivo para task toggles
- boton final disabled cuando falten datos o la task no este permitida

---

## 6. Archivos a crear o modificar en la implementacion futura

No tocar ahora. Esto es para la fase de implementacion.

### Crear

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CreateV000.py
```

Contenido esperado:

- `CreateV000Dialog(QtWidgets.QDialog)`
- `open_create_v000_dialog()`
- helpers internos para:
  - obtener sequence activa
  - detectar shot activo
  - listar plates `*plate`
  - obtener range por plate
  - obtener resolucion por plate
  - obtener resolucion timeline
  - detectar versiones existentes por task
  - construir output preview
  - devolver/imprimir parametros finales

### Crear mas adelante, fase 2

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CreateV000_renderer.py
```

Responsabilidad futura:

- Crear EXR negros reales.
- Recibir parametros ya validados.
- Escribir secuencia desde frame `1001`.
- Usar rango/cantidad de frames calculado por la UI.

### Modificar mas adelante

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel.py
```

Cambios esperados:

- Agregar tupla de boton despues de `Set Shot Name`.
- Agregar handler `create_v000`.
- Mantener mismo estilo y patron de carga externa que el resto del panel.

---

## 7. Modelo interno sugerido

Al abrir el dialogo:

```python
shot_info = {
    "shot_code": "MOR_1001C_010",
    "shot_root_path": Path("T:/VFX-MOR/101/MOR_1001C_010"),
    "plates": [
        {
            "track_name": "aPlate",
            "track_index": 5,
            "timeline_in": 1015,
            "timeline_out": 1112,
            "frame_count": 98,
            "width": 2048,
            "height": 858,
            "media_path": "T:/VFX-MOR/101/MOR_1001C_010/_input/...",
            "checked_default": True,
        },
    ],
    "timeline_resolution": (1920, 1080),
    "existing_versions_by_task": {
        "comp": "v003",
        "roto": None,
        "cleanup": None,
    },
}
```

Al apretar `Create v000` en esta fase:

```python
params = {
    "shot_code": "MOR_1001C_010",
    "task": "roto",
    "selected_plates": ["aPlate", "cPlate"],
    "timeline_in": 1015,
    "timeline_out": 1112,
    "frame_count": 98,
    "source_first_frame": 1001,
    "source_last_frame": 1098,
    "resolution": (1920, 1080),
    "resolution_source": "Timeline",
    "output_dir": "T:/VFX-MOR/101/MOR_1001C_010/Roto/4_publish/MOR_1001C_010_roto_v000",
    "output_name_pattern": "MOR_1001C_010_roto_v000_####.exr",
}
```

---

## 8. Validaciones

`Create v000` debe estar disabled si:

- no hay sequence activa
- no se detecta shot activo
- no se detecta ningun track `*plate`
- no hay ningun plate seleccionado
- no se puede calcular path desde `_input`
- no hay task habilitada
- no hay resolucion valida seleccionada

Warnings sugeridos:

```text
No active sequence.
No plate tracks found.
Select at least one plate.
Could not derive shot root from _input path.
All tasks already have versions in timeline.
Selected resolution is unavailable.
```

---

## 9. Checklist de implementacion futura

1. Leer `LGA_NKS_Edit_Panel.py` y ubicar `Set Shot Name` en `self.buttons`.
2. Leer `LGA_NKS_SetShotName.py` para copiar acceso a sequence, media path y fallback de shot name.
3. Leer `LGA_NKS_Trim_In.py` y `LGA_NKS_Trim_Out.py` para copiar el criterio de `timelineIn()` / `timelineOut()`.
4. Leer `LGA_NKS_CompareEXR_to_aPlate.py` para copiar acceso a tracks, clips, fileinfos y mediaSource.
5. Leer `LGA_NKS_GetClip.py` para usar tracks centralizados y busqueda por playhead.
6. Leer `LGA_NKS_TaskSelectionDialog.py` para copiar mapeo task/track y patron de dialogo Qt.
7. Leer `LGA_NKS_MatchVerToEXR.py` y `LGA_H-Clip_ScanVersions*.py` para extraer versiones existentes.
8. Leer `LGA_NKS_StyleUtils.py` para aplicar el estilo visual del panel.
9. Crear `LGA_NKS_CreateV000.py` con UI estatica.
10. Conectar deteccion real de plates.
11. Conectar calculo dinamico de range.
12. Conectar resoluciones.
13. Conectar deteccion de tasks deshabilitadas.
14. Conectar output preview.
15. Agregar boton al panel.
16. Probar en shots con:
    - solo aPlate
    - aPlate + bPlate
    - plates con diferentes rangos
    - timeline resolution distinta al plate
    - task comp ya existente
    - las tres tasks existentes

---

## 10. Dudas / puntos a validar al implementar

No bloquean el plan, pero conviene confirmarlos con pruebas reales en Hiero:

1. Orden real de tracks: asegurar que "track mas alto" corresponda al primer item elegido por default.
2. Inclusividad de `timelineOut()`: confirmar si el calculo correcto de frames es `out - in + 1` o `out - in`, segun la convencion local de los scripts actuales.
3. Resolucion de plate: confirmar el metodo mas confiable disponible en Hiero para obtener `width/height` del mediaSource en todos los formatos usados.
4. Deteccion de version existente: decidir si alcanza con clip bajo playhead en `_comp_`/`_roto_`/`_cleanup_`, o si debe buscar cualquier clip de la misma task que solape el rango completo del shot.
5. Si ya existe carpeta fisica `SHOT_task_v000` pero no hay clip en timeline: el plan actual solo deshabilita por version en track, no por carpeta existente. Esto queda fuera de scope salvo que se decida lo contrario.

---

## 11. Out of scope

- Crear EXR negros reales.
- Escribir archivos en disco.
- Detectar proxima version disponible.
- Crear `v001`, `v002`, etc.
- Sobrescribir una carpeta `v000` existente.
- Importar automaticamente la secuencia creada a Hiero.
- Agregar el clip resultante a tracks.
- Modificar `Python/Startup` durante esta etapa.

