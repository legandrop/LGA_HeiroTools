# LGA_NKS Create v000 - Estado actual

Documento actualizado para reflejar la implementacion actual de:

`C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CreateV000.py`

La herramienta ya crea la secuencia EXR v000 en Windows usando `oiiotool`
vendorizado dentro de `LGA_NKS_Shared`.

La implementacion para macOS queda pendiente para una etapa posterior, cuando
este cerrada la implementacion de Windows.

---

## Objetivo

`Create v000` abre un dialogo en Hiero para preparar una secuencia negra `v000` para el shot activo.

El dialogo recolecta y previsualiza:

- frame range del v000
- task (`comp`, `roto`, `cleanup`)
- resolucion
- output path
- nombre de secuencia
- handle, solo cuando el frame range viene de `editref`

Al presionar `Create v000`, crea la carpeta de salida y escribe la secuencia
EXR negra.

Cuando termina correctamente, cierra el dialogo sin mostrar un mensaje extra.

Si la carpeta de salida ya existe y contiene EXR, muestra una confirmacion con:

- `Cancel`
- `Replace`

`Replace` borra la carpeta v000 existente y crea una secuencia nueva desde cero.

---

## Integracion con Edit Panel

Archivo:

`C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel.py`

Estado:

- El boton `Create v000` ya esta agregado despues de `Set Shot Name`.
- Usa el mismo color de boton que `Set Shot Name`.
- Llama al script externo `LGA_NKS_CreateV000.py` mediante el patron existente del panel.

---

## UI actual

Layout del dialogo:

```text
Header

FRAME RANGE                         RESOLUTION
[tabla editref/plates]              ( ) Timeline
                                    ( ) aPlate
                                    ( ) cPlate

HANDLE                              TASK
[ v ][ 4 ][ ^ ]                     [ comp ] [ roto ] [ cleanup ]

OUTPUT
Path: ...
Name: ...
Timeline: ...
Frames: ...
Resolution: ...

[ Cancel ] [ Create v000 ]
```

Notas:

- La ventana usa un ancho minimo de `720`.
- El estilo actual usa fondo oscuro, textos `#a7a7a7`/`#CCCCCC`, separadores y botones custom.
- La tabla no muestra grid.
- La tabla no muestra scroll vertical.
- El alto de la tabla usa este calculo y no se debe cambiar sin probar en Hiero:

```python
header.height() + (row_count * row_height) + 2
```

---

## Frame Range

La tabla de `FRAME RANGE` lista fuentes de rango en este orden:

1. Tracks cuyo nombre contiene `editref`, case-insensitive.
2. Tracks cuyo nombre termina en `plate`, case-insensitive.

Ejemplos:

- `EditRef`
- `editref`
- `editref_2`
- `aPlate`
- `cPlate`

Cada fila muestra:

- checkbox `Use`
- nombre del track
- `TL IN`
- `TL OUT`
- `Frames`

Reglas:

- Si hay clips en tracks `editref`, aparecen primeros.
- `editref` y `plate` no son combinables entre si.
- Si se selecciona un `editref`, se deseleccionan todos los plates.
- Si se selecciona un plate, se deseleccionan todos los `editref`.
- Varios `editref` pueden combinarse entre si.
- Varios plates pueden combinarse entre si.
- El rango base se calcula con:
  - `base_timeline_in = min(timelineIn)`
  - `base_timeline_out = max(timelineOut)`

---

## Handle

El control `HANDLE` es custom. No usa `QSpinBox`.

UI:

```text
[ v ][ 4 ][ ^ ]
```

Implementacion:

- Boton izquierdo: baja el valor.
- Campo central: `QLineEdit` read-only.
- Boton derecho: sube el valor.
- Valor inicial: `4`.
- Rango permitido: `0` a `99`.

Reglas:

- Solo se puede editar si la seleccion actual del frame range contiene al menos un `editref`.
- Si la seleccion actual no contiene `editref`, el handle:
  - se pone en `0`
  - queda deshabilitado/greyed out
- Si el handle esta en `4`, el rango efectivo se expande:
  - `timeline_in = base_timeline_in - 4`
  - `timeline_out = base_timeline_out + 4`
  - el total suma `8` frames respecto del rango base
- El handle recalcula el preview de `OUTPUT` en vivo.

---

## Resolution

Default:

- `Timeline`

Opciones:

- `Timeline`
- resolucion de cada plate detectado

Notas:

- `editref` no se usa como fuente de resolucion.
- Si un plate no devuelve resolucion valida, su radio button queda deshabilitado.
- La resolucion no afecta el frame range ni el path.

---

## Task

Tasks disponibles:

- `comp`
- `roto`
- `cleanup`

Reglas:

- Si ya existe una version en el track de una task, esa task queda deshabilitada.
- Tracks de task:
  - `comp -> _comp_`
  - `roto -> _roto_`
  - `cleanup -> _cleanup_`
- Si `comp` esta deshabilitado, se selecciona la primera task disponible.
- Si todas las tasks estan deshabilitadas, `Create v000` queda deshabilitado.

---

## Output

El output preview muestra:

- `Path`
- `Name`
- `Timeline`
- `Frames`
- `Resolution`

Ejemplo:

```text
Path: T:/VFX-MOR/101/MOR_1003_020/Roto/4_publish/MOR_1003_020_roto_v000
Name: MOR_1003_020_roto_v000_####.exr
Timeline: 3813 - 4242 (handle 4)
Frames: 1001 - 1429 (429 frames)
Resolution: 4168 x 1612 (Timeline)
```

El frame inicial de salida siempre es:

```text
1001
```

La version siempre es:

```text
v000
```

El naming de salida usa:

```text
SHOT_task_v000_####.exr
```

La implementacion actual escribe frames reales como:

```text
SHOT_task_v000_1001.exr
SHOT_task_v000_1002.exr
...
```

---

## Path de salida

Los plates viven dentro de:

```text
RutaProyecto/Secuencia/Shotname/_input
```

El output se deriva desde el path de un plate real, no desde `editref`.

Ejemplo para comp:

```text
T:/VFX-MOR/101/MOR_1003_020/Comp/4_publish/MOR_1003_020_comp_v000
```

Ejemplo de archivo generado:

```text
T:/VFX-MOR/101/MOR_1003_020/Comp/4_publish/MOR_1003_020_comp_v000/MOR_1003_020_comp_v000_1001.exr
```

---

## Parametros recolectados

La herramienta arma un diccionario de parametros como:

```python
{
    "shot_code": "MOR_1003_020",
    "task": "roto",
    "selected_range_sources": [
        {"track_name": "EditRef", "source_type": "editref"},
    ],
    "selected_plates": ["EditRef"],
    "base_timeline_in": 3817,
    "base_timeline_out": 4238,
    "handle": 4,
    "timeline_in": 3813,
    "timeline_out": 4242,
    "frame_count": 429,
    "source_first_frame": 1001,
    "source_last_frame": 1429,
    "resolution": (4168, 1612),
    "resolution_source": "Timeline",
    "output_dir": "T:/VFX-MOR/101/MOR_1003_020/Roto/4_publish/MOR_1003_020_roto_v000",
    "output_name_pattern": "MOR_1003_020_roto_v000_####.exr",
}
```

Nota: `selected_plates` conserva el nombre historico de la key, pero actualmente puede contener `editref` porque representa las fuentes seleccionadas para frame range.

---

## Creacion de EXR en Windows

Backend actual:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\OIIO_Win\oiiotool.exe
```

Flujo:

1. Resolver `oiiotool.exe` relativo a `LGA_NKS_Shared`.
2. Crear la carpeta `output_dir` si no existe.
3. Si la carpeta ya existe y contiene `.exr`, pedir confirmacion.
4. Si el usuario elige `Replace`, borrar la carpeta v000 existente y recrearla desde cero.
5. Crear el primer frame negro a la resolucion seleccionada.
6. Duplicar ese primer EXR para todos los frames restantes.
7. Validar que la cantidad de EXR escritos coincida con `frame_count`.
8. Cerrar el dialogo al finalizar correctamente.

Comando base usado:

```text
oiiotool --create WIDTHxHEIGHT 3 --chnames R,G,B -d half --compression zip -o FIRST_FRAME.exr
```

Formato actual:

- canales: `R,G,B`
- data type: `half`
- compression: `zip`
- primer frame: `1001`
- version: `v000`

macOS:

- Pendiente.
- No se implementa hasta terminar/cerrar la version Windows.
- La futura version macOS debera tener su propia carpeta vendorizada, por ejemplo `LGA_NKS_Shared/OIIO_Mac`.

---

## Fuentes de codigo reutilizadas

Archivos relevantes:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_GetClip.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_TaskSelectionDialog.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Shared\LGA_NKS_Flow_NamingUtils.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_SetShotName.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_Trim_In.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_Trim_Out.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CompareEXR_to_aPlate.py
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_MatchVerToEXR.py
```

---

## Validaciones actuales

`Create v000` queda deshabilitado o muestra warning si:

- no hay sequence activa
- no hay viewer/playhead activo
- no hay `editref` ni `plate` detectado
- no hay plate real para derivar path/resolucion
- no se puede detectar shot
- no hay seleccion en frame range
- no se puede derivar shot root desde `_input`
- la resolucion seleccionada no es valida
- todas las tasks ya tienen version

---

## Fuera de scope actual

- Detectar proxima version disponible.
- Crear `v001`, `v002`, etc.
- Importar automaticamente la secuencia creada a Hiero.
- Agregar el clip resultante a tracks.
- Implementacion macOS.

---

## Proximo paso: importar y colocar la v000 en Hiero

Despues de crear correctamente la secuencia EXR `v000` en disco, el siguiente bloque de trabajo sera investigar e implementar su integracion dentro del proyecto/timeline actual de Hiero.

Este paso se hara en fases. Antes de modificar `LGA_NKS_CreateV000.py`, hay que explorar y validar con scripts de prueba en `+Building_Blocks`.

### Objetivos

1. Importar via Python la secuencia EXR creada al proyecto actual.
2. Ubicar el clip importado dentro del bin correcto del proyecto.
3. Asignarle al clip importado el shot name correcto, con la misma logica de `Set Shot Name`.
4. Insertar/colocar el clip en el timeline, en el lugar correcto.
5. Hacerlo respetando la organizacion existente del proyecto y los patrones ya usados por el Edit Panel.

### Investigacion requerida

Antes de implementar, hay que confirmar con documentacion y pruebas:

- Como importar una secuencia EXR via Python en Hiero/Nuke Studio.
- Como agregar esa secuencia importada a un bin especifico.
- Como crear/obtener el `BinItem` resultante.
- Como crear un clip/track item desde ese media importado.
- Como ubicarlo en el timeline en un track especifico y con el `timelineIn`/`timelineOut` correspondiente.
- Que metodos exactos existen en la version de Hiero/Nuke Studio usada localmente.

### Scripts locales que hay que revisar

Para bins/organizacion:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_OrganizeProject.py
```

Ese script organiza clips en bins segun la ruta del archivo. La v000 importada deberia seguir esa misma estructura, por ejemplo:

```text
F <Secuencia>/<ShotName>
```

o la estructura exacta que use `Organize Project` para el material existente.

Para naming del clip:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_SetShotName.py
```

La v000 importada deberia recibir el shot name correcto como si se ejecutara `Set Shot Name` sobre ese nuevo clip importado.

### Script de exploracion a crear

Crear un script de prueba en `+Building_Blocks`, no en el script final todavia.

Ubicacion sugerida:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-CreateV000_ImportExplore.py
```

Este script de exploracion primero deberia comprobar que existen y funcionan los metodos necesarios, sin hacer todavia la importacion definitiva.

Primera version del script exploratorio:

- Detectar proyecto activo.
- Detectar sequence activa.
- Imprimir root bin / clips bin.
- Imprimir metodos relevantes disponibles en:
  - `hiero.core.Project`
  - `hiero.core.Bin`
  - `hiero.core.BinItem`
  - `hiero.core.Clip`
  - `hiero.core.Sequence`
  - tracks del timeline
- Confirmar si se puede crear un `hiero.core.Clip` desde el path de una secuencia EXR.
- Confirmar si ese clip puede agregarse a un bin.
- Confirmar si existe un metodo para crear un track item desde ese clip.
- Confirmar como setear:
  - nombre del clip
  - timeline in
  - timeline out
  - source in/out si aplica
  - track destino

En esta primera exploracion, el script puede imprimir resultados y no deberia modificar el proyecto salvo que se decida explicitamente en el siguiente paso.

### Preguntas tecnicas a resolver antes de implementar

- En que bin exacto debe quedar la v000 importada.
- Si hay que crear un sub-bin especial para publish/v000 o usar la misma estructura de `Organize Project`.
- En que track debe insertarse cada task:
  - `comp -> _comp_`
  - `roto -> _roto_`
  - `cleanup -> _cleanup_`
- Si el track no existe, si debe crearse automaticamente o avisar al usuario.
- Si hay un clip previo en ese rango/track, si debe reemplazarse, moverse, cortarse o cancelar.
- Si el clip en timeline debe ocupar el rango con handle ya calculado o el rango base.
- Si el nombre visible del timeline item debe ser solo `SHOT` o `SHOT_task_v000`.

### Orden propuesto

1. Documentar este plan en el MD.
2. Buscar documentacion oficial de Hiero/Nuke Studio sobre importacion de media y colocacion en timeline.
3. Crear el script exploratorio en `+Building_Blocks`.
4. Ejecutarlo manualmente dentro de Hiero para validar que los metodos existen.
5. Ajustar el script exploratorio hasta confirmar el flujo correcto.
6. Recien entonces integrar el flujo en `LGA_NKS_CreateV000.py`.

---

## Resultado validado: importar y colocar v000 en Hiero

Fecha: 2026-05-03

Scripts de exploracion usados:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-CreateV000_ImportExplore.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-TrackItem_LinkStatus_Explore.py
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-TrackItem_LinkStatus_SetSelected.py
```

### Media EXR

Funciona crear un `hiero.core.Clip` desde el primer frame real de la secuencia:

```python
clip = hiero.core.Clip("T:/.../MOR_1003_020_roto_v000_1001.exr")
```

Hiero detecta la secuencia completa y normaliza internamente el path a `%04d`:

```text
MOR_1003_020_roto_v000_%04d.exr
```

Validado en la v000 de prueba:

```text
sourceIn/sourceOut: 1001 - 1429
duration: 429
media startTime: 1001
media duration: 429
resolution: 4168 x 1612
hasVideo: True
hasAudio: False
```

Tambien funcionan como input `####`, `%04d` y `######`, pero el primer frame real es el path mas simple y confiable.

### Bin destino

Segun `LGA_NKS_OrganizeProject.py`, la v000 debe importarse como `BinItem` directo dentro del shot bin:

```text
project.clipsBin()/F <Secuencia>/<ShotName>
```

Ejemplo validado:

```text
Sequences/F 101/MOR_1003_020
```

No debe importarse en sub-bins `Comp`, `Roto`, `Cleanup`, `4_publish` ni `v000` si se quiere respetar la logica actual de `Organize Project`.

### Track destino

Tracks confirmados para task:

```text
comp    -> _comp_
roto    -> _roto_
cleanup -> _cleanup_
```

Si el track destino no existe, la integracion deberia cancelar y avisar. No crear tracks automaticamente en esta etapa.

Antes de insertar, hay que chequear overlaps en el rango destino. `VideoTrack.addTrackItem` puede cortar o borrar clips superpuestos, asi que no debe llamarse sin validar conflicto.

### Timing correcto del TrackItem

El source del `TrackItem` debe setearse relativo al clip, no con frames absolutos de archivo.

Correcto para una secuencia `1001-1429` de 429 frames:

```python
source_in = 0
source_out = 428
timeline_in = 3813
timeline_out = 4241
track_item.setTimes(timeline_in, timeline_out, source_in, source_out)
```

Resultado validado:

```text
Timeline: 3813 - 4241
Source: 0.0 - 428.0
Duration: 429
Source duration: 429.0
Playback speed: 1.0
```

Incorrecto:

```python
track_item.setTimes(3813, 4242, 1001, 1429)
```

Ese flujo genera offset interno y retime porque Hiero interpreta el source del `TrackItem` relativo al clip. Resultado observado:

```text
Speed: 99.8%
Src Duration: 428
Dst Duration: 430
```

### Flujo validado de creacion

Flujo que funciona:

```python
clip = hiero.core.Clip(first_frame_path)
bin_item = hiero.core.BinItem(clip)
target_bin.addItem(bin_item)

track_item = target_track.addTrackItem(clip, timeline_in)
track_item.setName(shot_name)
track_item.setTimes(timeline_in, timeline_out - 1, 0, frame_count - 1)
track_item.setVersionLinkedToBin(True)
```

Notas:

- `timeline_out` de los parametros de `Create v000` es exclusivo.
- `TrackItem.setTimes()` debe recibir `timeline_out - 1`.
- `source_out` debe ser `frame_count - 1`.
- `setVersionLinkedToBin(True)` debe llamarse despues de que el `TrackItem` ya fue creado/agregado por `addTrackItem` y despues de ajustar tiempos.

### Link Status

El icono de la columna `Link Status` corresponde a:

```python
track_item.versionLinkedToBin()
```

Validado:

```text
Clip creado por Python antes del fix: versionLinkedToBin = False
Clip arrastrado manualmente desde bin: versionLinkedToBin = True
Clip creado por Python despues del fix: versionLinkedToBin = True
```

`linkedItems()` no explica ese icono: manual y Python devuelven `linkedItems count: 0`.

El proyecto tiene el default activo:

```text
project.trackItemVersionsLinkedToBin() == True
```

pero ese default no se aplica automaticamente al flujo Python probado. Hay que llamar `setVersionLinkedToBin(True)` explicitamente al final del flujo.

### No usar

No usar este orden, porque crashea Hiero:

```python
track_item = target_track.createTrackItem(name)
track_item.setSource(clip)
track_item.setTimes(...)
track_item.setVersionLinkedToBin(True)
target_track.addItem(track_item)
```

Tampoco usar la variante de dos argumentos:

```python
track_item.setVersionLinkedToBin(True, True)
```

El crash se produjo al llamar `setVersionLinkedToBin` sobre un `TrackItem` todavia no agregado/registrado completamente en timeline. La llamada si funciono sobre un item ya existente y tambien al final del flujo con `addTrackItem`.

### Integracion implementada

Implementado y probado en:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CreateV000.py
```

Funciona:

- Importar al bin `F <Secuencia>/<ShotName>`.
- Insertar en `_comp_`, `_roto_` o `_cleanup_` segun task.
- Cancelar si el track destino no existe.
- Chequear overlap en el track destino antes de insertar.
- Si hay overlap, permitir crear solo EXRs, crear+importar al bin, o crear+importar al timeline reemplazando los clips solapados.
- `Create + Import to Bin & Timeline` borra solo clips reales del track destino y luego coloca la v000.
- Usar source relativo `0..frame_count-1`.
- Usar timeline out inclusivo para `TrackItem`: `params["timeline_out"] - 1`.
- Setear nombre visible con la logica de `Set Shot Name` (`SHOT`, no `SHOT_task_v000`).
- Llamar `setVersionLinkedToBin(True)` al final, despues de crear/agregar el TrackItem y ajustar tiempos.

### Politica propuesta para overlaps

Al clickear `Create v000`, el flujo debe:

1. Chequear si ya existen EXRs `v000` en disco.
   - Si existen, mostrar el dialogo actual `Cancel / Replace`.
   - Si el usuario cancela, no hacer nada.
   - Si el usuario elige `Replace`, borrar y recrear los EXRs.
2. Antes de insertar en timeline, chequear si el rango destino se solapa con clips existentes en el track de la task.
   - Ejemplo: `roto -> _roto_`, rango `3813-4242`.
   - El chequeo debe mirar solo el track destino.
   - Ignorar `EffectTrackItem`.

Si hay overlap, mostrar un dialogo informando:

```text
Existing clip: <clip_name>
Track: <track_name>
Range: <timeline_in> - <timeline_out>
```

Opciones propuestas:

- `Cancel`: cancelar toda la operacion.
- `Create EXRs Only`: crear/reemplazar EXRs en disco, sin importar a Hiero.
- `Create + Import to Bin`: crear/reemplazar EXRs e importar al bin correcto, sin poner en timeline.
- `Create + Import to Bin & Timeline`: crear/reemplazar EXRs, importar al bin, borrar el/los clips solapados del track destino y colocar la v000.

Estado de implementacion:

1. Primera integracion: implementada y funcionando.
   - Sin overlap: crear EXRs, importar al bin y colocar en timeline.
   - Con overlap: ofrecer solo `Cancel`, `Create EXRs Only`, `Create + Import to Bin`.
2. Segunda integracion: implementada y funcionando.
   - Agregar `Create + Import to Bin & Timeline`.

Notas de seguridad:

- `VideoTrack.addTrackItem()` puede modificar items superpuestos; por eso el chequeo de overlap debe hacerse antes.
- `Create + Import to Bin & Timeline` debe borrar solo clips reales del track destino, no efectos ni clips de otros tracks.
- Si hay multiples overlaps, el dialogo debe listarlos o indicar claramente cuantos son.
- El borrado debe ocurrir dentro de `project.beginUndo(...)`.
- No borrar nada del timeline si la creacion EXR o la importacion al bin falla.

Exploracion de borrado validada:

```text
C:\Users\leg4-pc\.nuke\Python\Startup\+Building_Blocks\Hiero\Timeline\LGA_H-CreateV000_RemoveOverlap_Explore.py
```

Resultado:

- Detecta correctamente uno o multiples clips con overlap en `_roto_`.
- `track.removeItem(item)` elimina los clips detectados sin tocar otros tracks.
- Despues del borrado, el mismo rango devuelve `0` overlaps.
