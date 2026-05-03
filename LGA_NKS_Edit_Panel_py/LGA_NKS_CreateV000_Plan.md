# LGA_NKS Create v000 - Estado actual

Documento actualizado para reflejar la implementacion actual de:

`C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_NKS_CreateV000.py`

La herramienta sigue en fase de UI/validacion. Todavia no crea EXR reales.

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

Al presionar `Create v000`, por ahora solo imprime/loguea los parametros.

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

Y en fase futura debera escribir frames reales como:

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

Ejemplo de archivo futuro:

```text
T:/VFX-MOR/101/MOR_1003_020/Comp/4_publish/MOR_1003_020_comp_v000/MOR_1003_020_comp_v000_1001.exr
```

---

## Parametros recolectados

El stub imprime un diccionario con datos como:

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

- Crear EXR negros reales.
- Escribir archivos en disco.
- Detectar proxima version disponible.
- Crear `v001`, `v002`, etc.
- Sobrescribir una carpeta `v000` existente.
- Importar automaticamente la secuencia creada a Hiero.
- Agregar el clip resultante a tracks.
