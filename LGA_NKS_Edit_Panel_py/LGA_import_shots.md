> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

> ⚠ **PENDIENTE — Transcode de MOV no implementado**: la pagina
> "Transcode Plates" acepta plates en cualquier formato (EXR o MOV), pero el
> motor de transcode (`TranscodeWorker`) solo procesa EXR sequences via `LGA_EXR_Convert.py`.
> Los plates MOV aparecen en la tabla con checkbox deshabilitado y estado
> "No soportado". Implementar cuando haya herramienta de transcode MOV disponible.

# LGA_import_shots

Herramienta para importar un shot completo al timeline de Hiero/Nuke Studio.
Analiza la carpeta del shot, detecta plates/editrefs y versiones en publish,
y los coloca automaticamente en el timeline en la posicion alfabeticamente correcta.

## Descripcion

Abre un file browser para elegir la carpeta raiz del shot. Luego presenta
una ventana principal con la tabla de media detectada y tres botones de accion.

La posicion de insercion en el timeline se calcula automaticamente escaneando
los shots existentes y determinando la posicion alfabeticamente correcta,
sin depender del playhead.

## Archivos principales

- **Script principal:** `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots.py`
- **Boton:** Edit Panel → "Import shot" (verde `#2a4d3a`)
- **Plan de desarrollo:** `C:\Users\leg4-pc\.nuke\Python\Startup\docs\LGA_import_shots_PLAN.md`

### Modulos auxiliares (a extraer a medida que el script crece)

| Archivo | Contenido previsto | Estado |
|---------|-------------------|--------|
| `LGA_import_shots_transcode.py` | `TranscodeWorkerSignals`, `TranscodeWorker`, `build_manifest_for_sequence`, `check_existing_outputs`, `delete_existing_outputs`, `show_overwrite_warning` | **implementado** |
| `LGA_import_shots_settings.py` | Persistencia de settings e INI de presets de resolución. `load_all_settings`, `save_all_settings`, `load_res_presets`, `save_res_presets`, `preset_to_tuple`, `show_save_preset_dialog` | **implementado** |
| `LGA_import_shots_scan.py` | Helpers de escaneo de carpetas y metadata | pendiente |
| `LGA_import_shots_timeline.py` | Helpers de timeline (push, stretch, posicionamiento) | pendiente |
| `LGA_import_shots_bin.py` | Helpers de bin (find/create, import) | pendiente |
| `LGA_import_shots_ui.py` | Estilos CSS, widgets helpers, separadores | pendiente |

---

## Acceso

**Boton del panel:** "Import shot" en el Edit Panel (verde, posicion: antes de "Set Shot Name").

Llama a `main()` al ejecutarse como script externo desde el panel.

---

## Logging

Usa el sistema de logging dual estandar del proyecto (Sistema A — timer + limpieza por ejecucion).

### Variables de control

```python
DEBUG = True                  # Master switch
DEBUG_CONSOLE = False         # Salida a consola (off por defecto)
DEBUG_LOG = True              # Escritura al archivo .log
Transcode_TEST_Mode = True    # Output a /test_transcode; checkboxes de
                              # originals quedan inertes
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
    └── ImportShotDialog(...)               -> ventana principal con tabla + 3 botones
            |
            ├── [Rename]  -> sub-vista de renombrado para items marcados
            │                (stub: ventana temporal con Rename / Cancel)
            ├── [Convert] -> sub-vista de conversion EXR para items marcados
            │                Solo opera sobre EXR sequences. Si hay MOVs marcados,
            │                muestra advertencia por cada uno y los excluye.
            │                Si no hay ningun EXR marcado, no abre la sub-vista.
            └── [Import]  -> _do_import() sobre items marcados
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

## Ventana principal — Tabla de media

La tabla esta organizada en **secciones**, no como un file browser plano.
Solo se muestran las secciones que contienen media.

### Orden de secciones (de arriba a abajo)

1. **PUBLISH** — EXR sequences en `{Task}/4_publish/`
2. **PLATES** — EXR sequences en `_input/`
3. **REFERENCES** — MOVs de `_input/` (editref, seqref)

### Sistema de colores por fila

Cada fila tiene una barra de color de 4 px en el borde izquierdo que indica su tipo:

| Tipo | Color |
|------|-------|
| comp (publish) | `#3381e0` azul |
| roto (publish) | `#2abf7e` verde |
| cleanup (publish) | `#27c8c3` cyan |
| dmp (publish) | `#e08033` naranja |
| plates (input EXR) | `#42616d` azul petróleo |
| references (editref/seqref) | `#aa9e54` dorado |

Los mismos colores se usan en los titulos de las secciones.

### Fuentes analizadas

| Carpeta | Contenido | Seccion | Track destino |
|---------|-----------|---------|---------------|
| `{shot}/_input/*/` | Subcarpetas con EXR sequences | PLATES | `aPlate`, `bPlate`, etc. |
| `{shot}/_input/` | `.mov`/`.mxf` con keyword `editref` | REFERENCES | `EditRef` |
| `{shot}/_input/` | `.mov`/`.mxf` con keyword `seqref` | REFERENCES | *(solo bin)* |
| `{shot}/{Task}/4_publish/` | **Todas** las versiones EXR | PUBLISH | `_{task}_` |

### Comportamiento de la seccion PUBLISH

- Se listan **todas las versiones** encontradas (no solo la mas alta).
- Ordenadas: por task (`comp → roto → cleanup → dmp`), luego por version descendente.
- La version mas alta de cada task aparece primera y con texto mas claro (`#CCCCCC`).
- Versiones anteriores en gris oscuro (`#777777`).

### Comportamiento de checkboxes

- EXR de `_input` con `is_latest=True` → checked por defecto.
- Todo lo demas (publish, versiones anteriores, MOVs) → unchecked por defecto.
- Click en cualquier celda de la fila (excepto la barra de color y el checkbox) togglea el checkbox.

### Columnas

| Col | Contenido | Formato / color |
|-----|-----------|-----------------|
| (barra) | Color indicator | 4 px, sin header |
| (checkbox) | Seleccion | 28 px, sin header |
| Nombre | Nombre del clip/version | — |
| Tipo | `EXR seq`, `MOV`, etc. | — |
| Res | Resolucion + AR | `2048×1152` en gris, `(16:9)` en dorado `#a89060` (muted si row greyed out) |
| FPS | Frames por segundo | `23.976` |
| Compresion | Codec | `dwaa` → verde `#6a9960`, `zip`/`piz` → rojo `#a06060`, resto → gris |
| Frames | Rango y duracion | `1001–1480  (480f - 20.0s)` — count+secs en ámbar `#b09040` |
| Track | Asignacion de track | dropdown editable para inputs, label para publish |

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

### Botones de seleccion rapida

Fila de botones pequenos encima de los botones de accion:

| Boton | Accion |
|-------|--------|
| Select All | marca todos los checkboxes |
| Clear | desmarca todos |
| Plates | marca solo los items de la seccion PLATES |
| References | marca solo los items de la seccion REFERENCES |
| Publish | marca solo los items de la seccion PUBLISH |

### Botones de accion

Los tres botones operan sobre los items que tienen el checkbox marcado.

| Boton | Color | Habilitado cuando | Accion |
|-------|-------|-------------------|--------|
| Rename | secundario `#3a3a3a` | hay al menos 1 item marcado | abre sub-vista de renombrado |
| Transcode Plates | secundario `#3a3a3a` | hay al menos 1 EXR seq de input marcado | abre sub-vista de conversion |
| Create Tasks | secundario `#3a3a3a` | hay al menos 1 item marcado | **PENDIENTE** — abrirá `LGA_import_shots_createtasks.py`; hoy muestra un placeholder |
| Import | primario `#2a4d3a` | hay al menos 1 item marcado | ejecuta import (ver logica abajo) |

### Logica de Import (comportamiento previsto)

> **Estado actual:** Import cierra el dialogo sin importar nada (stub).

Cuando se implemente:
- **Plates / References:** se importan exactamente los items que tienen checkbox marcado.
- **Publish:** para cada task que tenga al menos una version chequeada, se importa
  **siempre la version mas alta** de esa task, independientemente de cual version
  este chequeada. Esto previene importar accidentalmente una version obsoleta.
- La seleccion de versiones anteriores de publish sirve exclusivamente para Rename o Convert.

---

## Sub-vista Rename

Estilo PowerRename: find/replace con preview en tiempo real sobre los nombres
de los items marcados.

> **Estado actual:** stub. Muestra una ventana temporal con botones Rename y Cancel.
> Cancel vuelve a la ventana principal sin cambios.

---

## Sub-vista Convert

Conversion de EXR sequences para los items marcados.

- Solo opera sobre `exr_seq`. Los MOVs marcados se listan con un aviso
  `"<nombre>.mov no sera convertido"` y se excluyen del proceso.
- Si no hay ningun EXR marcado (solo MOVs u otros), el boton no hace nada.

### Layout

```
┌─ EXR CONVERT ─────────────────────────────────────────┐
│  [⚠ avisos por MOVs excluidos]                        │
├───────────────────────────────────────────────────────┤
│  TABLA DE EXRs A CONVERTIR                            │
├───────────────────────────────────────────────────────┤
│  Codec / Calidad     │  Resolucion                    │
│  (col izquierda)     │  (col derecha)                 │
├───────────────────────────────────────────────────────┤
│  Manejo de originales                                 │
├───────────────────────────────────────────────────────┤
│  RESUMEN  (totales en disco)                          │
├───────────────────────────────────────────────────────┤
│  LOG (3 lineas, expandible ▲/▼)                       │
├───────────────────────────────────────────────────────┤
│  [← Go Back]                  [Start Transcode]       │
└───────────────────────────────────────────────────────┘
```

### Tabla de EXRs a convertir

| Col | Contenido | Formato / color |
|-----|-----------|-----------------|
| (barra) | Color `#42616d` (plates) | 4 px, sin header |
| Nombre | Nombre de la secuencia | `#cccccc` |
| Origen | `WxH (AR) (PAR) · bitdepth · Nch · compresion · #f - Xs` | AR dorado `#a89060`, PAR rosa `#c4787a` entre paréntesis, comp coloreada, count+secs ámbar `#b09040`. Ancho: 375 px |
| → | Flecha separadora | centrada, `#666` |
| Destino | `WxH (AR) (PAR) · bitdepth · Nch · compresion` | mismo coloring; PAR destino = `(1)` si desanamorfizar activo, sino mismo PAR fuente; `—` gris oscuro si checkbox off |
| Tamaño | Tamaño actual en disco | escaneado al abrir la pagina (`_folder_size_bytes`) |
| Estado | `Pendiente` / `⚠ Upscale` / `—` / barra de progreso / `✓ Listo` / `✗ Error` | ancho fijo 130px. Ver detalle abajo. |

**Estados de la columna Estado:**

| Estado | Descripción | Color/widget |
|--------|-------------|--------------|
| `Pendiente` | EXR chequeado, listo para convertir | cian `#5a9ab5` |
| `⚠ Upscale` | Resize bloqueado por "no upscale" | rojo `#a06060` |
| `—` | Checkbox desactivado (fila no se convertirá) | gris oscuro `#444444` |
| Barra de progreso | Convirtiendo — polling QTimer cada 300ms de archivos en dst | fondo vacío `#393959`, relleno `#443a91`, texto `#cccccc`, bordes redondeados |
| `✓ Listo` | Conversión completada exitosamente | verde `#6a9960` |
| `✗ Error` | Conversión fallida | rojo `#a06060` |

La columna Destino y la columna Estado se recalculan en vivo cuando cambian:
DWAA on/off, DWAA level, channels, preset de resolucion, custom W×H, "no upscale", **checkbox de la fila**.

**Upscale bloqueado:** cuando el resize resultaría en upscale y "Aplicar solo si origen es mayor"
está activo, la fila muestra `⚠ Upscale` en rojo y la columna Destino se grísea. No se modifica
la lógica de cálculo; es solo comunicación visual al usuario.

El bit depth y channels se leen via `oiiotool --info -v` parseando la linea
`"WxH, N channel, half openexr"` y se guardan en cada item como `bitdepth` y
`channels` (int) en `_scan_input_folder()` y `_scan_publish_folders()`.

### Opciones — Codec / Calidad (columna izquierda)

| Control | Default | Notas |
|---------|---------|-------|
| ☑ Convertir a DWAA | on | Si off, mantiene compresion original; oculta el control de nivel |
| DWAA level (`QSpinBox` editable + `QSlider`) | `45` | Visible solo si DWAA activo. Rango `30–60`. Spin y slider two-way bound. |
| Channels (`QComboBox`) | `Mantener` | `Mantener` o `Reducir a RGB` (elimina canal alpha; pasa `channels: "rgb"` al manifest) |

> Todos los valores de Codec / Calidad son **persistentes**: se guardan en el INI al cambiar
> y se restauran en la próxima apertura de la herramienta.

### Opciones — Resolucion (columna derecha)

| Control | Default | Notas |
|---------|---------|-------|
| Destino (`QComboBox`) | `Original` | Presets cargados desde INI. Secciones `[AR]` en dorado. Ícono 🗑 a la derecha en presets borrables; click en ícono borra el preset del INI. Presets por defecto: `Original`, `2K — 2048×1152 [16:9]`, `UHD — 3840×2160 [16:9]`, `4K — 4096×2304 [16:9]`, `Custom...`. Con source disponible: muestra `→ WxH [AR_real]` calculado según PAR y match_dim |
| Custom W × H + `[Save preset]` | `2048 × 1152` | Solo visible si preset = `Custom...`. El botón "Save preset" abre un diálogo para nombrar y guardar el preset al INI. |
| ☑ Preserve aspect ratio | on | **Comportamiento según preset:** |
| | | — **Presets fijos** (2K/UHD/4K): muestra "Dimensión que manda" (match width/height) |
| | | — **Custom:** oculta "Dimensión que manda"; vincula W↔H dinámicamente. La última dimensión editada es el "master"; la otra se recalcula por ítem según su AR de source |
| Dimensión que manda | `Match target width` | Solo visible cuando PAR activo Y preset NO es Custom |
| ☑ Desanamorfizar (Pixel Aspect Ratio) | off | Si activo, aparece el selector de PAR fuente (`1.3`, `1.5`, `1.8`, `2.0`). El ancho destino = `src_w × PAR`. El `PixelAspectRatio` de salida se fuerza a `1.0` en el manifest. La columna Destino muestra PAR `(1)`. |
| PAR fuente (`QComboBox`) | `2.0` | Visible solo si Desanamorfizar activo |
| Filtro resampling | `lanczos3` | `cubic`, `box` (solo aplica si hay resize) |
| ☑ Aplicar solo si origen es mayor | on | Evita upscale accidental; filas con upscale → Estado `⚠ Upscale` |

> Todos los valores de Resolución son **persistentes**: se guardan en el INI al cambiar
> y se restauran en la próxima apertura.

#### Presets de resolución — formato INI

Los presets se almacenan en secciones `[ResPreset_N]` del mismo INI (`ImportShots.ini`):

```ini
[ResPreset_0]
name = Original
special = original

[ResPreset_1]
name = 2K — 2048×1152
w = 2048
h = 1152

[ResPreset_4]
name = Custom...
special = custom
```

- `special = original` → mantiene resolución fuente  
- `special = custom` → muestra spinboxes  
- `w` + `h` → preset fijo (permite trash icon y borrado)  
- Los presets `original` y `custom` son invariables (sin trash icon)

#### Lógica Custom + Preserve AR

```
_custom_master: "w" | "h"  — última dimensión editada por el usuario
_custom_ar_updating: bool  — flag para evitar recursión en valueChanged

_on_custom_w_changed() → si PAR on: calcula H = W * src_h/src_w (primer EXR)
_on_custom_h_changed() → si PAR on: calcula W = H * src_w/src_h (primer EXR)

_current_target_res(src_w, src_h) con preset=custom y PAR on:
    if _custom_master == "w": tw = spinner_w; th = round(tw * src_h/src_w)
    if _custom_master == "h": th = spinner_h; tw = round(th * src_w/src_h)
    → resultado diferente por ítem (cada plate mantiene su propio AR)
```

### Opciones — Manejo de originales (fila inferior)

| Control | Default |
|---------|---------|
| ☑ Mover originales a `/Originals` | on (off si `Transcode_TEST_Mode`) |
| ☑ Borrar `/Originals` al terminar | off |

> Los valores de Manejo de originales son **persistentes** (se guardan en el INI al cambiar),
> excepto cuando `Transcode_TEST_Mode = True` (los checkboxes quedan bloqueados).

Cuando el flag global `Transcode_TEST_Mode = True` está activo:
- Aparece un aviso `🧪 TEST MODE` en la sección.
- Ambos checkboxes quedan deshabilitados.
- El output del transcode (cuando se implemente) se escribirá en
  `{seq_path}/test_transcode/` en vez de reemplazar la secuencia original.

### Solución QSpinBox — `_ArrowSpinBox` (ganadora, implementada)

Clase de módulo definida en `LGA_import_shots.py` (junto a `_ArrowComboBox`).
Usada en los spinboxes W y H del panel Custom de resolución.

**Ronda 1 FALLADA**: CSS triangle, `subcontrol-origin:border/padding`, arrows nativos del SO
→ flechas invisibles en este build.

**Ronda 2 ganadora**: Subclase con `paintEvent` (Opción 7) — mismo patrón que `_ArrowComboBox`.
Opciones 5 (▲▼ externos) y 6 ([−] valor [+]) también funcionales como workaround.

Ver receta completa en `docs/Docu_PySide_UI_Aprendizajes.md — SpinBox`.

### Resumen

Una linea de texto sobre el log con totales (sin estimaciones):

```
3 secuencias · 1842 frames · 14.21 GB en disco
```

### Botones inferiores

| Boton | Estilo | Habilitado | Accion |
|-------|--------|------------|--------|
| ← Go Back | `_BTN_SECONDARY` | siempre (deshabilitado durante transcode activo) | vuelve a `PAGE_MEDIA` (preserva opciones) |
| Start Transcode | `_BTN_PRIMARY` | cuando hay ≥1 EXR chequeado | llama a `_run_transcode()` → lanza `TranscodeWorker` via `QThreadPool` |

### Log panel

3 lineas visibles, expandible con boton ▲/▼ a `setMaximumHeight(16777215)`.

> **Estado actual:** Implementado. El transcode corre via `LGA_EXR_Convert.py`
> (manifest JSON + subprocess) en un `QRunnable` separado para no bloquear la UI.

---

## Placement (Import)

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
Se muestra con icono ⚠ en la tabla principal.

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
# Colores para anotaciones en tabla / dropdowns
# Derivados de la paleta PATH_LEVEL_COLORS, desaturados ~40 %
_CLR_AR            = "#a89060"   # aspect ratio          — dorado suave
_CLR_PAR           = "#c4787a"   # pixel aspect ratio    — rosa suave
_CLR_FRAMES        = "#b09040"   # cantidad de frames    — ámbar cálido
_CLR_COMP_ZIP      = "#a06060"   # compresión zip/piz    — rojo suave
_CLR_COMP_DWAA     = "#6a9960"   # compresión dwaa/dwab  — verde suave
_CLR_STATUS_PENDING  = "#5a9ab5" # estado Pendiente      — cian suave
_CLR_STATUS_DONE     = "#6a9960" # estado Terminado      — verde suave
_CLR_STATUS_ERROR    = "#a06060" # estado Error          — rojo suave
_CLR_STATUS_UPSCALE  = "#a06060" # estado Upscale (bloq) — rojo suave

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

# Colores de borde izquierdo por tipo de fila (tabla de media)
_CLR_COMP    = "#3381e0"   # comp publish    (= TASK_COLORS["comp"]    en CreateV000)
_CLR_ROTO    = "#2abf7e"   # roto publish    (= TASK_COLORS["roto"]    en CreateV000)
_CLR_CLEANUP = "#27c8c3"   # cleanup publish (= TASK_COLORS["cleanup"] en CreateV000)
_CLR_DMP     = "#e08033"   # dmp publish
_CLR_PLATES  = "#42616d"   # plates input (EXR)
_CLR_REFS    = "#aa9e54"   # references (editref / seqref)
_TASK_ORDER  = {"comp": 0, "roto": 1, "cleanup": 2, "dmp": 3}
```

---

## Estilo de la UI

Basado en `LGA_NKS_CreateV000.py`:

- Fondo: `#2B2B2B`, texto principal: `#CCCCCC`, texto secundario: `#a7a7a7`
- Tablas: fondo `#272727`, borde `#333333`, headers `#999999`
- Boton primario (Import): `#2a4d3a` con borde `#3a7a55`
- Botones secundarios (Rename, Transcode EXR): `#3a3a3a` con borde `#555555`
- Botones pequenos (seleccion): `#2e2e2e` con borde `#444444`, texto `#999999`
- Boton cancelar/volver: `#555555` con borde `#666666`
- Ancho minimo del dialogo: `1275px` (requiere espacio para la tabla de transcode con Origen 375 px + Destino amplio)
- Titulos de seccion de tabla: color de la seccion sobre fondo `#313131`
- Referencias (seqref en bin): texto color `#aa9e54`

---

## Settings persistentes

Los settings de la sub-vista Convert se guardan en:

| Sistema | Ruta |
|---------|------|
| Windows | `%APPDATA%\LGA\HieroTools\ImportShots.ini` |
| macOS   | `~/Library/Application Support/LGA/HieroTools/ImportShots.ini` |
| Fallback | `~/.config/LGA/HieroTools/ImportShots.ini` |

El módulo `LGA_import_shots_settings.py` es el único responsable de leer y escribir este archivo.

### Secciones del INI

```ini
[Codec]
dwaa = true
dwaa_level = 45
channels = all          ; "all" | "rgb"
filter = lanczos3

[Resolution]
preset_index = 0
custom_w = 2048
custom_h = 1152
keep_ar = true
match_dim = 0           ; 0 = "Match target width", 1 = "Match target height"
no_upscale = true
deana = false
deana_par = 2.0

[Originals]
move = false
delete = false

[ResPreset_0]
name = Original
special = original

[ResPreset_1]
name = 2K — 2048×1152
w = 2048
h = 1152

[ResPreset_2]
name = UHD — 3840×2160
w = 3840
h = 2160

[ResPreset_3]
name = 4K — 4096×2304
w = 4096
h = 2304

[ResPreset_4]
name = Custom...
special = custom
```

### Flujo de carga / guardado

1. **Apertura de la herramienta:** `load_all_settings()` y `load_res_presets()` se llaman en
   `ImportShotDialog.__init__` **antes** de construir la UI.
2. **Construccion de la UI:** los widgets se crean con sus defaults internos, luego
   `_load_settings_to_ui()` aplica los valores guardados (sin activar auto-save).
3. **Auto-save:** al final de `_build_page_convert` se conecta `_save_all_settings` a
   todas las señales `stateChanged` / `valueChanged` / `currentIndexChanged` de los
   widgets de settings. Cualquier cambio del usuario dispara `save_all_settings()`.
4. **Presets de resolución:** al borrar un preset (`_on_delete_preset`) o guardar uno nuevo
   (`_on_save_preset_clicked`), se llama `save_res_presets()` y se reconstruye el combo
   con `_rebuild_res_combo()`.

### Iconos de la UI

Los iconos SVG para el trash del dropdown de presets viven en:

```
LGA_NKS_Shared/icons/trash.svg        — estado normal
LGA_NKS_Shared/icons/trash_hover.svg  — estado hover
```

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
| FPS | `framesPerSecond` (si el archivo lo tiene embebido) | `r_frame_rate` del video stream |
| Compresion | `compression:` de la salida verbose | `codec_name` del video stream |
| Frames | rango escaneado de la secuencia EXR | `nb_frames` del video stream (fallback: `duration × fps`) |
| Tipo | `EXR seq` | extension real del archivo: `MOV`, `MXF`, `MP4` |

---

## Pendiente de implementacion

- **Sub-vista Rename:** implementacion real del find/replace con preview (hoy es stub)
- **Convert — Transcode de MOV:** plates MOV aparecen en la tabla con checkbox deshabilitado
  y estado "No soportado". Implementar cuando haya herramienta de transcode MOV disponible.
- **Create Tasks:** el botón existe en la pantalla principal pero abre un placeholder.
  El archivo `LGA_import_shots_createtasks.py` es una copia de `LGA_NKS_CreateV000.py`
  que sirve como base. Pendiente: adaptar la lógica de CreateV000 al contexto de este
  import (multi-shot, sin Hiero sequence object propio, etc.).
- **SetShotName:** llamada correcta al script externo post-importacion
- **CreateV000:** trigger correcto para tasks sin versiones
- **Modularizacion:** extraer helpers a `LGA_import_shots_scan.py`,
  `LGA_import_shots_timeline.py`, `LGA_import_shots_bin.py`, `LGA_import_shots_ui.py`

---

## Referencias tecnicas

| Archivo | Funciones / clases clave |
|---------|--------------------------|
| `LGA_NKS_Edit_Panel_py/LGA_import_shots.py` | `main()`, `ImportShotDialog`, `_show_page()`, `_build_page_media()`, `_build_page_convert()`, `_update_convert_page()`, `_on_res_preset_changed()`, `_on_keep_ar_changed()`, `_update_match_dim_visibility()`, `_get_representative_res()`, `_on_custom_w_changed()`, `_on_custom_h_changed()`, `_current_target_res()`, `_target_compression()`, `_refresh_convert_destinos()`, `_update_res_combo_labels()`, `_on_dwaa_chk_changed()`, `_on_deana_chk_changed()`, `_apply_deana_if_active()`, `_load_settings_to_ui()`, `_save_all_settings()`, `_rebuild_res_combo()`, `_on_delete_preset()`, `_on_save_preset_clicked()`, `_run_transcode()`, `_start_next_sequence()`, `_on_sequence_started()`, `_poll_transcode_progress()`, `_on_sequence_done()`, `_on_worker_batch_done()`, `_finalize_transcode()`, `_on_transcode_error()`, `_fmt_bd()`, `_fmt_par()`, `_ar_str()`, `_read_exr_metadata()`, `_read_mov_metadata()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_transcode.py` | `TranscodeWorkerSignals` (señales: `log_message`, `sequence_started(row_i, dst_dir, total_frames)`, `sequence_done`, `all_done`, `error`), `TranscodeWorker`, `build_manifest_for_sequence(channels, pixel_aspect_ratio)`, `check_existing_outputs()`, `delete_existing_outputs()`, `show_overwrite_warning()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_settings.py` | `get_settings_path()`, `load_all_settings()`, `save_all_settings()`, `load_res_presets()`, `save_res_presets()`, `preset_to_tuple()`, `show_save_preset_dialog()` |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_createtasks.py` | Copia de `LGA_NKS_CreateV000.py`. Base para la futura ventana "Create Tasks". **Pendiente de adaptación.** |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_CreateV000.py` | Referencia de UI, bin import, timeline placement, colorize path, patrón de settings persistentes |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_SetShotName.py` | Renombrado de clips post-importacion |
| `LGA_NKS_Edit_Panel_py/LGA_NKS_OrganizeProject.py` | Estructura de bins `F <grupo>/<shot>` |
| `LGA_NKS_Shared/LGA_EXR_Convert.py` | Motor de transcode EXR. Llamado via subprocess con `--manifest` JSON. Soporta DWAA, resize, channels, pixel_aspect_ratio, OCIO, workers paralelos. |
| `LGA_NKS_Shared/LGA_NKS_Flow_NamingUtils.py` | `clean_base_name()`, `extract_shot_code()` |
| `LGA_NKS_Shared/LGA_QtAdapter_HieroTools.py` | Qt adapter (PyQt5/PySide2) |
| `LGA_NKS_Shared/icons/trash.svg` | Ícono de papelera para borrar presets (estado normal) |
| `LGA_NKS_Shared/icons/trash_hover.svg` | Ícono de papelera (estado hover) |
| `LGA_NKS_Shared/OIIO_Win/oiiotool.exe` | Lectura metadata EXR (Windows). Llamado con `--info -v` |
| `LGA_NKS_Shared/OIIO_Win/bin/python/python.exe` | Python bundled usado por `TranscodeWorker` para invocar `LGA_EXR_Convert.py` |
| `LGA_NKS_Shared/FFmpeg_Win/bin/ffprobe.exe` | Lectura metadata MOV/MXF (Windows). Salida JSON |
| `docs/LGA_import_shots_PLAN.md` | Plan de desarrollo, decisiones de diseno, preguntas resueltas |
