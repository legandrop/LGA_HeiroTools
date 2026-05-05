> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_import_shots

Herramienta para importar un shot completo al timeline de Hiero/Nuke Studio.
Analiza la carpeta del shot, detecta plates/editrefs y versiones en publish,
y los coloca automaticamente en el timeline en la posicion alfabeticamente correcta.

## Descripcion

Abre un file browser para elegir la carpeta raiz del shot. Luego presenta una
ventana de tres fases (stepper) que guia al usuario a traves del analisis,
el procesamiento opcional de media (Prep Media), y la importacion final al
timeline y al bin del proyecto.

La posicion de insercion en el timeline se calcula automaticamente escaneando
los shots existentes y determinando la posicion alfabeticamente correcta,
sin depender del playhead.

## Archivos principales

- **Script principal:** `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots.py`
- **Boton:** Edit Panel → "Import shot" (verde `#2a4d3a`)
- **Plan de desarrollo:** `C:\Users\leg4-pc\.nuke\Python\Startup\docs\LGA_import_shots_PLAN.md`

### Modulos auxiliares (a extraer a medida que el script crece)

| Archivo | Contenido previsto |
|---------|-------------------|
| `LGA_import_shots_scan.py` | Helpers de escaneo de carpetas y metadata |
| `LGA_import_shots_timeline.py` | Helpers de timeline (push, stretch, posicionamiento) |
| `LGA_import_shots_bin.py` | Helpers de bin (find/create, import) |
| `LGA_import_shots_ui.py` | Estilos CSS, widgets helpers (stepper, separator) |

---

## Acceso

**Boton del panel:** "Import shot" en el Edit Panel (verde, posicion: antes de "Set Shot Name").

Llama a `main()` al ejecutarse como script externo desde el panel.

---

## Logging

Usa el sistema de logging dual estandar del proyecto (Sistema A — timer + limpieza por ejecucion).

### Variables de control

```python
DEBUG = True           # Master switch
DEBUG_CONSOLE = False  # Salida a consola (off por defecto)
DEBUG_LOG = True       # Escritura al archivo .log
```

### Archivo de log

`C:\Users\leg4-pc\.nuke\Python\Startup\logs\debugPy_ImportShots.log`

Formato: `[0.123s] mensaje`
El archivo se borra y recrea en cada ejecucion con encabezado `Fecha: YYYY-MM-DD HH:MM:SS`.

### Funciones del sistema

| Funcion | Descripcion |
|---------|-------------|
| `RelativeTimeFormatter` | Formatter con tiempo relativo desde inicio |
| `setup_debug_logging(script_name)` | Configura `QueueHandler + QueueListener`, `propagate=False` |
| `debug_print(*message, level="info")` | Funcion de logging publica, acepta multiples argumentos |
| `cleanup_logging()` | Detiene el listener; registrado con `atexit` |

Logger name: `importshots_logger`

### Como agregar debug prints

Usar `debug_print()` (argumentos variadicos, igual que `print`):

```python
debug_print("=== Iniciando escaneo ===")
debug_print("Shot root:", shot_root, "name:", shot_name)
debug_print("Track no existe:", track_name, level="warning")
debug_print("Error critico:", e, level="error")
```

Puntos clave donde ya hay instrumentacion:
- `main()`: inicio, carpeta elegida, deteccion de duplicado
- `_scan_input_folder()` / `_scan_publish_folders()`: cantidad de items encontrados
- `_find_insert_frame()`: insert_frame, frames_to_push, duracion
- `_push_clips_right()`: frame de insercion y cantidad desplazada
- `_place_clip_in_timeline()`: nombre del clip, track, frame de colocacion
- `_import_clip_to_bin()`: nombre del clip importado al bin
- `_stretch_burnin()`: frame final del burnin
- Errores de movimiento de clips y stretch

---

## Flujo general

```
main()
    |
    ├── hiero.ui.activeSequence()           -> sequence activa
    ├── QFileDialog.getExistingDirectory()  -> shot_root elegido por usuario
    ├── _shot_exists_in_timeline()          -> verificacion de duplicado (aborta si existe)
    ├── _scan_input_folder()                -> lista de media en _input/
    ├── _scan_publish_folders()             -> versiones en {Task}/4_publish/
    ├── _find_insert_frame()                -> posicion alfabetica en el timeline
    └── ImportShotDialog(...)
            |
            ├── Fase 2: tabla de media (PHASE_MEDIA)
            │       └── _build_media_table()
            ├── Sub-vista: Prep Media (PHASE_PREP)
            │       └── rename / convert (conversion pendiente herramienta externa)
            └── Fase 3: preview placement (PHASE_IMPORT)
                    └── _do_import()
                            ├── _push_clips_right()
                            ├── _import_clip_to_bin()
                            ├── _place_clip_in_timeline()
                            ├── _stretch_burnin()
                            └── LGA_NKS_SetShotName (llamada externa)
```

---

## Estructura de carpetas del shot (asumida)

```
T:/VFX-PROYECTO/101/MOR_1012C_010/          <- shot root
│
├── _input/                                  <- nivel raiz del shot
│   ├── MOR_1012C_010_aPlate_v01/            <- subcarpeta por secuencia EXR
│   │   └── MOR_1012C_010_aPlate_v01_1001.exr
│   ├── MOR_1012C_010_EditRefComp_v01.mov    <- editref: va al track EditRef
│   └── MOR_1012C_010_SeqRef_v01.mov         <- seqref: solo al bin, no al timeline
│
├── Comp/
│   └── 4_publish/
│       └── MOR_1012C_010_comp_v00/
└── Roto/
    └── 4_publish/
        └── MOR_1012C_010_roto_v002/
```

---

## Fase 2 — Tabla de media

### Fuentes analizadas

| Carpeta | Contenido | Track destino |
|---------|-----------|---------------|
| `{shot}/_input/*/` | Subcarpetas con EXR sequences | `aPlate`, `bPlate`, etc. |
| `{shot}/_input/` | `.mov`/`.mxf` con keyword `editref` | `EditRef` |
| `{shot}/_input/` | `.mov`/`.mxf` con keyword `seqref` | *(solo bin)* |
| `{shot}/_input/` | Archivos sueltos (jpg, etc.) | *(listados, sin track)* |
| `{shot}/{Task}/4_publish/` | EXR seq version mas alta | `_{task}_` |

### Comportamiento de checkboxes

- EXR de `_input` version mas alta (★) → checked por defecto
- Versiones anteriores → unchecked
- MOV, publish, sueltos → unchecked
- Hacer click en cualquier celda de la fila (excepto la columna del checkbox) tambien
  togglea el checkbox. Click directo sobre el checkbox funciona independientemente.

### Deteccion de track por nombre de carpeta (case-insensitive)

| Keyword | Track |
|---------|-------|
| `seqref` | *(solo bin)* |
| `editrefclean` | `EditRefClean` |
| `editref` | `EditRef` |
| `fgplate` | `fgPlate` |
| `bgplate` | `bgPlate` |
| `aplate` | `aPlate` |
| `bplate` | `bPlate` |
| `cplate` | `cPlate` |
| `dplate` | `dPlate` |

Fallback: EXR sin coincidencia se asignan alfabeticamente (`aPlate`, `bPlate`...).
MOV/MXF sin coincidencia → `EditRef`.

---

## Sub-vista Prep Media

Permite renombrar y/o convertir los items marcados antes de importar.

- **Rename:** estilo PowerRename (find/replace con preview en tiempo real)
- **Convert:** checkbox DWAA, selector de resolucion con presets, opciones de Originals
- **Log panel:** 3 lineas visibles, expandible con boton ▲/▼

> La conversion real esta pendiente de integracion con la herramienta externa `.py`
> que se agregara a `LGA_NKS_Edit_Panel_py/` cuando este lista.

---

## Fase 3 — Placement

### Logica de posicionamiento en el timeline

Los shots en el timeline estan siempre ordenados alfabeticamente de izquierda a derecha.
La herramienta escanea los tracks `aPlate` y `EditRef`, obtiene el listado de shots existentes
con sus posiciones, y calcula el `insert_frame` correcto para el nuevo shot.

Si hay shots que deben moverse a la derecha, se llama a `_push_clips_right()` que mueve
todos los clips de todos los tracks (excepto `BurnIn`) desde el punto de insercion.

El track `BurnIn` se **estira** con `_stretch_burnin()` para cubrir el nuevo largo total.

### Colocacion en timeline

```python
track_item.setTimes(tl_in, tl_out, 0, frame_count - 1)
track_item.setVersionLinkedToBin(True)   # siempre al final
```

Los EXR fisicos empiezan en frame `1001`. El source en Hiero empieza en `0`;
Hiero mapea internamente el rango fisico.

### Bin destino

```
project.clipsBin() / F <grupo> / <shot_name>
```

Ejemplo: `F 101/MOR_1012C_010`

El grupo se extrae de la penultima parte del path del shot root.
Si el bin ya existe se reutiliza; si no, se crea.

### Deteccion de shot existente (criterio doble)

1. Nombre del `TrackItem` coincide exactamente con `shot_name` (case-insensitive)
2. El path de la media del clip contiene el `shot_root` normalizado

Si cualquiera de los dos se cumple → error, el script se cancela.

### SeqRef

El SeqRef se importa al bin del shot (si no estaba ya). No se coloca en el timeline.
Se muestra con icono ⚠ en la tabla de Fase 2 y en el preview de Fase 3.

---

## Validaciones

| Condicion | Resultado |
|-----------|-----------|
| No hay sequence activa | Warning y salida |
| Usuario cancela el file browser | Salida silenciosa |
| El shot ya existe en el timeline | Error critico, solo opcion Cancelar |
| No hay EXR en `_input/` | `max_frames` fallback a 100, continua |
| Track destino no existe en timeline | Error por clip, continua con los demas |

---

## Constantes relevantes

```python
BURNIN_TRACK_NAMES = {"burnin", "burn in", "burn_in"}

PLATE_KEYWORDS = [
    ("seqref",       None),
    ("editrefclean", "EditRefClean"),
    ("editref",      "EditRef"),
    ("fgplate",      "fgPlate"),
    ("bgplate",      "bgPlate"),
    ("aplate",       "aPlate"),
    ("bplate",       "bPlate"),
    ("cplate",       "cPlate"),
    ("dplate",       "dPlate"),
    ("eplate",       "ePlate"),
]

TASK_FOLDERS = {
    "comp":    ("Comp",    "_comp_"),
    "roto":    ("Roto",    "_roto_"),
    "cleanup": ("Cleanup", "_cleanup_"),
    "dmp":     ("DMP",     "_dmp_"),
}
```

---

## Estilo de la UI

Basado en `LGA_NKS_CreateV000.py`:

- Fondo: `#2B2B2B`, texto principal: `#CCCCCC`, texto secundario: `#a7a7a7`
- Tablas: fondo `#272727`, borde `#333333`, headers `#999999`
- Boton primario (Import/Continuar): `#2a4d3a` con borde `#3a7a55`
- Boton secundario (Prep Media): `#3a3a3a` con borde `#555555`
- Boton cancelar/volver: `#555555` con borde `#666666`
- Ancho minimo del dialogo: `820px`
- SeqRef y warnings: `#d9a441` (amarillo dorado)

---

## Herramientas externas (LGA_NKS_Shared)

Las siguientes tools binarias estan disponibles en `LGA_NKS_Shared/` y se referencian
siempre con rutas **relativas a SHARED_DIR** para que funcionen en cualquier maquina
donde se distribuya la repo.

| Tool | Ruta relativa | Plataforma | Uso |
|------|---------------|------------|-----|
| oiiotool | `OIIO_Win/oiiotool.exe` | Windows | Lectura de metadata EXR (res, compresion) |
| ffprobe | `FFmpeg_Win/bin/ffprobe.exe` | Windows | Lectura de metadata MOV/MXF (res, fps, codec) |

> **Mac/Linux pendiente:** las rutas para macOS y Linux aun no estan implementadas.
> Cuando se agreguen las carpetas `OIIO_Mac/` y `FFmpeg_Mac/` en Shared, hay que
> agregar la rama `elif _OS == "Darwin":` en la seccion de constantes del script.

### Metadata leida

| Columna | EXR (oiiotool) | MOV/MXF (ffprobe) |
|---------|---------------|-------------------|
| Res | `W x H` de la primera linea de `--info -v` | `width` / `height` del video stream |
| FPS | `—` (no aplica para secuencias) | `r_frame_rate` del video stream |
| Compresion | `compression:` de la salida verbose | `codec_name` del video stream |

---

## Pendiente de implementacion

- **Prep Media — Convert:** logica real de conversion (pendiente herramienta externa)
- **Prep Media — Presets:** guardado de presets de rename y resolucion en `.ini`
- **SetShotName:** llamada correcta al script externo post-importacion
- **CreateV000:** trigger correcto para tasks sin versiones
- **Modularizacion:** extraer helpers a `LGA_import_shots_scan.py`,
  `LGA_import_shots_timeline.py`, `LGA_import_shots_bin.py`, `LGA_import_shots_ui.py`

---

## Referencias tecnicas

| Archivo | Funciones / clases clave |
|---------|--------------------------|
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `main()`, `ImportShotDialog`, `_scan_input_folder()`, `_scan_publish_folders()`, `_read_exr_metadata()`, `_read_mov_metadata()`, `_find_insert_frame()`, `_push_clips_right()`, `_stretch_burnin()`, `_shot_exists_in_timeline()`, `_import_clip_to_bin()`, `_place_clip_in_timeline()`, `_find_or_create_bin()` |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_CreateV000.py` | Referencia de UI, bin import, timeline placement, colorize path |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_SetShotName.py` | Renombrado de clips post-importacion |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_OrganizeProject.py` | Estructura de bins `F <grupo>/<shot>` |
| `LGA_NKS_Shared/LGA_NKS_Flow_NamingUtils.py` | `clean_base_name()`, `extract_shot_code()` |
| `LGA_NKS_Shared/LGA_QtAdapter_HieroTools.py` | Qt adapter (PyQt5/PySide2) |
| `LGA_NKS_Shared/OIIO_Win/oiiotool.exe` | Lectura metadata EXR (Windows). Llamado con `--info -v` |
| `LGA_NKS_Shared/FFmpeg_Win/bin/ffprobe.exe` | Lectura metadata MOV/MXF (Windows). Salida JSON |
| `docs/LGA_import_shots_PLAN.md` | Plan de desarrollo, decisiones de diseno, preguntas resueltas |
