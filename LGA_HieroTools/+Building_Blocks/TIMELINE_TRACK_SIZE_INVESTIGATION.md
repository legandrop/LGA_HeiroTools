# Timeline Tracknames/Track Height Investigation

Fecha: 2026-05-13

Objetivo:

- Encontrar una forma por Python/Hiero/Nuke Studio de cambiar:
  - el ancho visual del area de tracknames dentro del timeline;
  - el alto visual de tracks, idealmente de un track puntual.
- Evitar soluciones basadas en mouse drag o cambios visuales equivocados.

## Contexto Importante

El cambio buscado NO es el splitter principal del TimelineEditor.

Ese splitter corresponde al panel izquierdo grande de propiedades/proyecto vs el panel derecho del timeline. Ya existe codigo que lo manipula:

- `LGA_NKS_Shared/LGA_NKS_Reduce_SeqWin.py`
- `PANEL_IZQUIERDO_TAMANO = 340`
- `main_splitter.setSizes([340, total - 340])`

Eso no cambia el ancho de tracknames dentro del `TimelineView`.

El area buscada esta dentro del viewport/render interno de:

- `Foundry::Storm::UI::TimelineView`
- Python wrapper: `QAbstractScrollArea`

## Scripts Descartados

Se crearon varios scripts exploratorios que luego fueron eliminados porque no aportaban para este problema:

- `explore_timeline_tracknames_area.py`
- `test_timeline_tracknames_resize.py`
- `test_timeline_internal_mouse_resize.py`
- `explore_timeline_size_api_candidates.py`
- `test_timeline_size_api_top10.py`
- `explore_timeline_viewer_widgets_to_txt.py`
- `explore_timeline_internal_state_to_txt.py`
- `test_timeline_header_widgets_geometry.py`

Motivos de descarte:

- Algunos listaban demasiados widgets sin revelar estado interno util.
- Uno cambio el ancho del zoom slider inferior, no los tracknames.
- Uno simulo mouse drag. Eso fue incorrecto para el objetivo y no debe repetirse.
- Uno movia la barra superior (`HieroTimeSlider`, disk cache button), pero eso no cambiaba los tracknames.

## Lo Que Se Probo y Se Descubrio

### 1. API directa del `TimelineEditor`

El objeto `TimelineEditor` Python mostro muy poca API util:

- `sequence()`
- `setTrackSelection()`
- `beginSelectionUpdate()`
- `endSelectionUpdate()`
- `selection()`
- `setSelection()`
- `window()`

No aparecio nada tipo:

- `setTrackHeight`
- `setTrackLabelWidth`
- `setTrackNameWidth`
- `setHeaderWidth`

### 2. API/metaObject del `TimelineView`

`TimelineView` es:

- C++ class: `Foundry::Storm::UI::TimelineView`
- Python/PySide wrapper: `QAbstractScrollArea`

Slots/metodos relevantes descubiertos:

- `refreshTimeline()`
- `updateViewport()`
- `zoom(float)`
- `zoomAboutTime(Foundry::Base::Time,float)`
- `zoomToFit()`
- `zoomToFill()`
- `zoomIn()`
- `zoomOut()`
- `zoomSliderChanged(int)`
- `setTimeRange(Foundry::Base::Time,Foundry::Base::Time)`
- `scrollToTime(Foundry::Base::Time)`
- `setTime(Foundry::Base::Time)`
- `adjustHorizontalScroll(int)`
- `adjustVerticalScroll(int)`
- `collapseTracks()`
- `splitViewsToTracks()`
- `finishNameEditing()`

No aparecio un setter publico para ancho/alto arbitrario de tracks.

### 3. Tracks (`VideoTrack`) tampoco exponen altura visual

Los objetos `VideoTrack` expusieron cosas como:

- `name()`
- `trackName()`
- `trackIndex()`
- `setName()`
- `setView()`
- `setAllViews()`
- `splitViewsToTracks()`
- `metadata()`
- `tags()`

Metadata vista:

- `foundry.track.enabled`
- `foundry.track.blendEnabled`

No aparecio metadata de alto visual ni ancho de label.

### 4. El test que cambio el zoom slider inferior

Un script infirio mal que el `QSlider` inferior representaba el ancho de tracknames.

Resultado real:

- Cambio el selector de zoom horizontal debajo de los tracknames.
- No cambio tracknames.
- No cambio alto de tracks.

Conclusion:

- No tocar `qt_scrollarea_hcontainer` / `QSlider` inferior para este objetivo.

### 5. Comparacion de snapshots de widgets (`final_2.txt` vs `final_3.txt`)

Se genero una comparacion entre:

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_2.txt`
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_3.txt`

Cambios reales detectados:

- `Hiero::HieroTimeSlider`: `x=185 -> 259`, `w=2115 -> 2041`
- `QFrame`: `x=140 -> 214`
- `QToolButton` disk cache: `x=140 -> 214`

Ese bloque se movio `+74px`.

Luego se probo mover esos widgets por script.

Resultado del usuario:

- Eso cambia una barra arriba de los tracknames.
- No cambia el area de tracknames.

Conclusion:

- Esos widgets son sintoma/acompanamiento del layout superior, no el control real del tracknames area.

### 6. Snapshot interno (`final_internal_1/2`)

Se genero un explorador mas amplio de QObject/meta properties.

Comparacion textual:

- No revelo propiedades o setters utiles.

Pero los PNG del viewport si cambiaron mucho:

- `final_internal_1_viewport.png`: tracknames angostos, tracks compactos.
- `final_internal_2_viewport.png`: tracknames mas anchos, `aPlate` mas alto, thumbnails visibles.

Conclusion:

- El cambio vive en el render interno del `TimelineView.viewport()`.
- No aparece como widget hijo ni propiedad Qt simple.

## Exploracion Actual Util

### `explore_timeline_render_metrics_to_txt.py`

Archivo:

- `+Building_Blocks/explore_timeline_render_metrics_to_txt.py`

Uso:

```python
exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_render_metrics_to_txt.py").read())
```

Guarda:

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_render_metrics_N.txt`
- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_render_metrics_N_viewport.png`

Que hace:

- Captura el viewport.
- Mide bordes verticales por pixeles para inferir limite tracknames/clips.
- Mide bordes horizontales por pixeles para inferir alturas de tracks.
- Lista meta-metodos/properties completos del `TimelineView`.

Resultados importantes:

Comparacion `final_render_metrics_3` vs `final_render_metrics_4`:

- Antes:
  - `inferred_label_clip_boundary_cluster={'range': (172, 306), 'center': 231, 'count': 16, 'score': 260047, 'strongest': (268, 99798)}`
- Despues:
  - `inferred_label_clip_boundary_cluster={'range': (282, 449), 'center': 355, 'count': 21, 'score': 326231, 'strongest': (375, 105432)}`

Interpretacion:

- El inicio de clips/fin de tracknames se corrio a la derecha.
- El ancho visual de tracknames aumento aprox. `+120/+140px`.

Altura de tracks:

- Antes, primeras lineas horizontales fuertes:
  - `y=123, 135, 146, 158...`
- Despues:
  - `y=67, 79, 90, 102...`

Interpretacion:

- El render vertical del timeline cambio y el track alto queda medible por pixeles.

Limitacion:

- Este script mide y confirma el estado visual.
- No setea el estado.

## Persistencia / Settings

### `explore_timeline_persistent_settings_to_txt.py`

Archivo:

- `+Building_Blocks/explore_timeline_persistent_settings_to_txt.py`

Uso:

```python
exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_persistent_settings_to_txt.py").read())
```

Guarda:

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_persistent_settings_N.txt`

Que revisa:

- `QSettings()` default.
- Variantes `Foundry / NukeStudio`, `The Foundry / Hiero`, etc.
- `C:\Users\leg4-pc\.nuke\uistate.ini`.
- `preferences*.nk`.
- configs Foundry en AppData.
- hashes, mtimes y lineas filtradas por timeline/track/header/height/width.

Hallazgos:

- `QSettings` via registro devolvio `totalKeys=0` para variantes relevantes.
- `uistate.ini` contiene seccion `[timeline]`, pero solo:
  - `timelineReformatType`
  - `timelineReformatResizeType`
  - `timelineReformatCenter`
  - `timelineAudioWaveformMemory`
  - `timelineDiskCacheEXRCompression`
  - `timelineShowFrameEndMarker`
  - `timelineFrameRangeFollowsPlayhead`
  - `timelineHalfAudioWaveforms`
  - `linkTrackItemVersions`
  - `currentTool`
  - `timelineHighlightClonesOfSelectedClones`
  - `timelineDragShiftInsertNewTrack`
  - `timelineDiskCacheSequenceAutoRecache`

No contiene:

- tracknames width
- track label width
- track height
- row height
- per-track expanded height

Comparacion `final_persistent_settings_2.txt` vs `final_persistent_settings_3.txt`:

- `diff blocks 0`

Conclusion:

- Cambiar manualmente ancho/alto no modifica archivos persistentes detectables.
- No parece guardarse en `uistate.ini`, `preferences*.nk`, `QSettings` o AppData escaneado.

## Introspeccion C++ Pendiente / Actual

### `explore_timeline_cpp_introspection_to_txt.py`

Archivo:

- `+Building_Blocks/explore_timeline_cpp_introspection_to_txt.py`

Uso:

```python
exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_cpp_introspection_to_txt.py").read())
```

Guarda:

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_cpp_introspection_N.txt`

Que hace:

- Obtiene punteros C++ con `shiboken2.getCppPointer`.
- Ejecuta `shiboken.dump()`.
- Lista `metaObject` completo, incluyendo herencia, enums, classInfo, methods y properties.
- Lista acciones asociadas al `TimelineView` y parents.
- Revisa referrers Python del wrapper.
- Inspecciona `hiero`, `hiero.ui`, `hiero.core`.
- Busca strings locales en `.dll`, `.pyd`, `.exe` de `C:\Program Files\Nuke15.1v6`.

Estado:

- Implementado.
- Analizado parcialmente.

Hallazgo importante:

Una busqueda dirigida en binarios de `C:\Program Files\Nuke15.1v6` encontro strings en:

- `C:\Program Files\Nuke15.1v6\studio-15.1.6.dll`

Clases C++ privadas relevantes:

- `.?AVTimelineToolTrackHeaderWidth@Hiero@@`
- `.?AVTimelineToolTrackHeight@Hiero@@`

Contexto encontrado alrededor:

```text
Foundry::Storm::UI::TimelineView
TrackHandler
TimelineToolTrackHeaderWidth
TimelineToolTrackMove
TimelineToolSelect
VideoTrackHandler
AudioTrackHandler
TransitionTrackHandler
SubTrackItemTrackHandler
TimelineViewDragEnterHandler
TimelineViewDragMoveHandler
TimelineViewTagDropHandler
TimelineViewContainer
```

Tambien aparecio:

```text
TimelineToolTrackHeight
```

junto a otras herramientas:

```text
TimelineToolMarqueeSelect
TimelineToolMove
TimelineMultiTool
TimelineToolRazor
TimelineToolRoll
TimelineToolSlide
TimelineToolSlip
TimelineToolTimeZoom
TimelineToolTrackHeight
TimelineToolTrim
```

Interpretacion:

- Foundry si tiene herramientas internas separadas para:
  - ancho del header/tracknames (`TimelineToolTrackHeaderWidth`);
  - alto de tracks (`TimelineToolTrackHeight`).
- Esas herramientas no aparecen como slots publicos ni propiedades Qt del `TimelineView`.
- Probablemente son clases C++ usadas por el sistema interno de tools/event handling del timeline.
- Esto explica por que el cambio manual funciona con drag, pero no aparece en Python como setter directo.

## Conclusiones Actuales

Confirmado:

- El cambio de ancho de tracknames y alto de tracks se ve y se puede medir en pixeles dentro del viewport.
- No aparece como widget hijo.
- No aparece como meta-property Qt.
- No aparece en `VideoTrack.metadata()`.
- No aparece en `QSettings`/registro.
- No aparece en archivos persistentes detectados.
- No hay setter publico evidente en `TimelineView.metaObject()`.
- Los binarios contienen tools C++ privadas con nombres exactos para este comportamiento:
  - `TimelineToolTrackHeaderWidth`
  - `TimelineToolTrackHeight`

Hipotesis actual:

- El ancho de tracknames y el alto de tracks viven como estado C++ interno del `Foundry::Storm::UI::TimelineView`.
- Ese estado se modifica por tools internas C++:
  - `Hiero::TimelineToolTrackHeaderWidth`
  - `Hiero::TimelineToolTrackHeight`
- No parece estar expuesto en Python de forma directa.

Proximos pasos razonables:

1. Buscar si esas tools privadas aparecen en algun factory/registry accesible desde Python.
2. Explorar acciones/tool groups y current tool para ver si se puede activar `TimelineToolTrackHeaderWidth` o `TimelineToolTrackHeight` por API.
3. Buscar simbolos/strings cercanos a esas clases para detectar metodos como `setHeight`, `setWidth`, `resize`, `mouseDrag`, etc.
4. Si aparecen slots/metodos no visibles en Python pero registrados por Qt, probar `QMetaObject.invokeMethod` solo si son seguros y no requieren eventos de mouse.
5. Si no aparece nada, asumir que el control directo requiere:
   - API privada C++ no vinculada a Qt metaObject;
   - hooking/event filter;
   - o automatizacion de UI, que ya se descarto como objetivo para esta etapa.

## Cosas Que NO Deben Repetirse

- No manipular el `QSlider` inferior del scrollbar: es el zoom slider, no tracknames.
- No simular mouse drag/click.
- No mover `Hiero::HieroTimeSlider`, `QFrame` o disk cache button: son la barra superior, no tracknames.
- No seguir explorando widgets hijos basicos esperando encontrar tracknames como `QWidget`; no existe como widget separado en lo observado.

## Exploracion de Tools Privadas

### `explore_timeline_private_tools_to_txt.py`

Archivo:

- `+Building_Blocks/explore_timeline_private_tools_to_txt.py`

Uso:

```python
exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_private_tools_to_txt.py").read())
```

Guarda:

- `C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout\final_private_tools_N.txt`

Que revisa:

- `uistate.ini` y `currentTool`.
- `hiero.ui.findMenuAction()` para acciones/timeline tool groups plausibles.
- Todas las `QAction` vivas relacionadas con timeline/tool.
- Widgets vivos relacionados con tool/timeline.
- Parent chain y children de `TimelineView`.
- Nombres en `hiero`, `hiero.ui`, `hiero.core`.
- Strings alrededor de:
  - `TimelineToolTrackHeaderWidth`
  - `TimelineToolTrackHeight`
  - `TimelineTool`
  - `TrackHeader`
  - `TrackHeight`
  - `HeaderWidth`
  - `foundry.timeline`

Objetivo:

- Detectar si esas tools privadas tienen action/factory/registry accesible desde Python.

Resultado de `final_private_tools_1.txt`:

- `uistate.ini` muestra:

```text
currentTool=foundry.timeline.selectMultiTool
```

- `hiero.ui.findMenuAction()` no encontro acciones directas para:

```text
foundry.timeline.trackHeaderWidth
foundry.timeline.trackHeight
foundry.timeline.selectMultiTool
foundry.timeline.timelineToolGroup1..5
```

- Pero las `QAction` vivas si muestran las tools normales del toolbar:

```text
foundry.timeline.selectMultiTool
foundry.timeline.selectSelectTool
foundry.timeline.selectTool
foundry.timeline.selectEffectsTool
foundry.timeline.selectSlipTool
foundry.timeline.selectSlideTool
foundry.timeline.selectRollTool
foundry.timeline.selectRippleTrimTool
foundry.timeline.selectRetimeTool
foundry.timeline.selectRazorTool
foundry.timeline.selectRazorAllTool
foundry.timeline.selectJoinTool
foundry.timeline.selectSelectLeftTool
foundry.timeline.selectSelectRightTool
foundry.timeline.selectSelectAllInTrackTool
foundry.timeline.selectSelectAllLeftTool
foundry.timeline.selectSelectAllRightTool
```

- En `studio-15.1.6.dll`, cerca de `foundry.timeline.timelineToolGroup`, aparecen los action ids normales y el texto:

```text
Timeline Tool Group
foundry.timeline.timelineToolGroup
```

- No aparecio ningun action id directo para:

```text
TimelineToolTrackHeaderWidth
TimelineToolTrackHeight
```

Interpretacion:

- Las tools privadas existen en C++.
- No estan registradas como `QAction`/menu action directa.
- Probablemente se activan internamente por el `TimelineMultiTool` cuando el cursor/hit-test cae sobre el borde correcto del viewport.
- Eso explica que el usuario pueda cambiar ancho/alto manualmente desde el Multi Tool, pero no exista una accion separada tipo `foundry.timeline.trackHeight`.
