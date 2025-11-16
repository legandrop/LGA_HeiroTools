# LGA_NKS_MatchVerToEXR

Herramienta para sincronizar versiones entre tracks `_comp_` y `_rev_` en Hiero/Nuke Studio.

## Descripción

Busca la versión actual de los clips del track `_comp_` (configurado en `DEFAULT_TRACK_NAME`) e intenta subir la versión de los clips correspondientes del track `_rev_` (configurado en `DEFAULT_REV_TRACK_NAME`) a la misma versión. Solo procesa clips que contengan "_comp_" en su nombre.

## Archivos principales

- **Script principal:** `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit\LGA_NKS_MatchVerToEXR.py`
- **Panel de control:** `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_EditTools_Panel.py`

## Acceso

**Botón del panel:** "Match Rev Ver" en EditTools Panel
- **Click normal:** Procesa clips usando método híbrido (prioriza selecciones múltiples, luego playhead, luego fallback a selección)
- **Shift + Click:** Fuerza procesamiento de todos los clips independientemente de la selección

## Funcionamiento

### Requisitos
- Secuencia activa con tracks `_comp_` (configurado en `DEFAULT_TRACK_NAME`) y `_rev_` (configurado en `DEFAULT_REV_TRACK_NAME`)
- Clips con "_comp_" en el nombre del archivo

### Proceso
1. Analiza versiones de clips del track `_comp_` (usando método híbrido: selecciones múltiples > playhead > selección)
2. Busca clips correspondientes en el track `_rev_` por nombre base
3. Actualiza clips del track `_rev_` a la versión más alta disponible
4. Si la versión del track `_comp_` no está disponible, agrega tag rojo "Version Mismatch"
5. Muestra ventana con resultados del proceso

### Estados de resultado
- **Updated:** Clip del track `_rev_` actualizado exitosamente
- **Already Matched:** Las versiones ya coincidían
- **Version Not Available:** La versión del track `_comp_` no existe para el clip del track `_rev_`

## Funciones principales

### `match_exr_to_rev(force_all_clips=False)`
Función principal que inicializa la GUI y ejecuta el proceso.

### `HieroOperations.process_tracks()`
Lógica principal que:
- Detecta tracks `_comp_` y `_rev_` usando variables centralizadas (`DEFAULT_TRACK_NAME` y `DEFAULT_REV_TRACK_NAME`)
- Procesa clips usando método híbrido (selecciones múltiples > playhead > selección) o todos si `force_all_clips=True`
- Actualiza versiones y agrega tags según resultado

### `VersionMatcherGUI`
Interfaz que muestra resultados en tabla con:
- Nombre del shot
- Versión del track `_comp_`
- Versión anterior del track `_rev_`
- Estado del proceso

## Notas técnicas

- Utiliza expresiones regulares para extraer números de versión
- Maneja archivos EXR con secuencias (%04d) y archivos de video
- Implementa sistema de undo para reversión de cambios
- Compatible con selección múltiple y procesamiento masivo
- Usa módulo centralizado `LGA_NKS_GetClip` para obtener clips (método híbrido)
- Los nombres de tracks son configurables mediante variables centralizadas en `LGA_NKS_GetClip.py`:
  - `DEFAULT_TRACK_NAME = "_comp_"` (track que contiene los EXR con el render de COMP)
  - `DEFAULT_REV_TRACK_NAME = "_rev_"` (track que contiene los MOV o MXF con el render de COMP)
