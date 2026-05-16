> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# 🚀 Guía Rápida CLI - FileManager

## 🎯 ¿Qué hace FileManager?

FileManager es una aplicación para sincronizar archivos entre carpetas locales y Wasabi S3. Funciona completamente portable sin instalación.

## 📋 Comandos CLI Disponibles

### 1. **Abrir FileManager en una ruta específica**
```bash
FileManager.exe --path "T:\VFX-TOC\From_Wanka\20250909\Probando"
```

- Abre la interfaz gráfica apuntando directamente a esa carpeta
- Escanea automáticamente la contraparte en Wasabi S3
- Muestra archivos locales vs remotos lado a lado

### 2. **Descargar desde Wasabi S3**
```bash
FileManager.exe --download "T:\VFX-TOC\From_Wanka\20250909\Probando"
```

- Abre la interfaz gráfica
- Muestra diálogo para resolver conflictos (Sobrescribir/Saltar/Cancelar)
- Descarga archivos desde Wasabi hacia la carpeta local
- Muestra progreso en tiempo real

### 3. **Subir a Wasabi S3**
```bash
FileManager.exe --upload "T:\VFX-TOC\From_Wanka\20250909\Probando"
```

- Abre la interfaz gráfica
- Muestra diálogo para resolver conflictos remotos
- Sube archivos desde carpeta local hacia Wasabi S3
- Muestra progreso en tiempo real

### 4. **Descargar un archivo individual desde Wasabi S3**
```bash
FileManager.exe --download-file "T:\VFX-MOR\102\MOR_2015_010\_input\MOR_2015_010_EditRef_v01.mov"
```

- Descarga **un único archivo** (no una carpeta) desde Wasabi
- Crea solo la carpeta padre del archivo, no una carpeta con el nombre del archivo
- Resuelve el tamaño real del objeto en S3 antes de encolar la descarga
- Se descarga con `overwrite` activado
- `--download` y `--download-file` aceptan **múltiples rutas** y pueden combinarse en una sola invocación:
  ```bash
  FileManager.exe --download "T:\VFX-MOR\102\SHOT\_input\seq_v01" --download-file "T:\VFX-MOR\102\SHOT\_input\ref.mov"
  ```

### 5. **Notificar a Hiero al terminar la descarga**
```bash
FileManager.exe --download-file "T:\VFX-MOR\102\SHOT\_input\ref.mov" --notify-completion "C:\Users\...\Startup\logs\download_clip_done"
```

- `--notify-completion "<carpeta>"` hace que FileManager escriba un marcador `.json` en `<carpeta>` cuando cada tarea de descarga termina
- El valor es la **carpeta de salida** de los marcadores (Hiero le pasa su propia ruta, así no hay rutas hardcodeadas entre repos)
- Solo afecta a las descargas de esa invocación; lo usa el botón **Download Clip** para disparar la reconexión automática

## 🔧 Cómo usar desde compilar.bat

```bash
# Compilar y ejecutar con CLI
.\compilar.bat --path "T:\VFX-TOC\From_Wanka\20250909\Probando"
.\compilar.bat --download "T:\VFX-TOC\From_Wanka\20250909\Probando"
.\compilar.bat --upload "T:\VFX-TOC\From_Wanka\20250909\Probando"
```

## 🍎 macOS: uso recomendado (app abierta o cerrada)

En macOS, `open -a ... --args` puede ignorar argumentos si la app ya está abierta.
Para garantizar que el CLI funcione siempre, usar el wrapper:

```bash
./fm_cli_mac.sh --path "/Volumes/T Viaja/T/VFX-BRDA/010-350/BRDA_040_010"
./fm_cli_mac.sh --download "/Volumes/T Viaja/T/VFX-BRDA/010-350/BRDA_040_010"
./fm_cli_mac.sh --upload "/Volumes/T Viaja/T/VFX-BRDA/010-350/BRDA_040_010"
```

Alternativa directa sin wrapper:

```bash
open -na /Users/leg4/Desktop/Codin/LGA_FileManager/build/FileManager.app --args --path "/Volumes/T Viaja/T/VFX-BRDA/010-350/BRDA_040_010"
```

Notas:
- `fm_cli_mac.sh` usa por defecto `build/FileManager.app` (dev) o `/Applications/FileManager.app` (prod).
- Para deploy, podés definir `FILEMANAGER_APP_PATH` con la ruta del `.app`.

## 📝 Reglas importantes

### ✅ Rutas válidas
- Deben empezar con `VFX-` (ej: `VFX-TOC`, `VFX-PHLDA`)
- Pueden tener barras `/` o `\`
- Usar comillas `"` si hay espacios

### ✅ Ejemplos válidos
```bash
--path "T:\VFX-TOC\From_Wanka\20250909\Probando"
--path "T:/VFX-PHLDA/022-055/PHLDA_030_010_Stab_Auto"
--download "T:\VFX-TOC\From_Wanka\20250909\TOC_067_010_HdMkup_Fabric_comp_v13"
```

### ❌ Ejemplos inválidos
```bash
--path "C:\Users\MiUsuario\Desktop"  # No es VFX-
--path "T:\MiProyecto\Archivos"      # No es VFX-
```

## 🎮 Comportamiento

- **Primera ejecución**: Abre interfaz gráfica y ejecuta la operación
- **App ya abierta**: Reutiliza la instancia existente (no abre nueva ventana)
- **Sin argumentos**: Abre interfaz normal (todos los tabs disponibles)

## 📊 Estados de archivos

- 🟢 **Verde**: Archivo existe local y remotamente (igual)
- 🔴 **Rojo**: Solo existe remotamente (se puede descargar)
- 🔵 **Azul**: Solo existe localmente (se puede subir)
- 🟡 **Amarillo**: Existe en ambos pero diferente (conflicto)

## 🚨 Solución de problemas

### "Bucket no encontrado"
- Verificar que la ruta empiece con `VFX-*`
- Revisar configuración de credenciales Wasabi

### "Carpeta no existe"
- Para `--download`: La carpeta se crea automáticamente
- Para `--upload`: Verificar que la ruta local exista

### "Conflicto de archivos"
- El diálogo muestra opciones: Sobrescribir/Saltar/Cancelar
- Elegir según necesites mantener o reemplazar archivos

---

## 🤖 Integración con Panel FlowProd

### Botones FileManager en Hiero/Nuke Studio

Los siguientes botones están disponibles en el panel **Flow Production** de Hiero:

#### 🎯 **Open in FileManager**
- **Función**: Abre la carpeta del shot seleccionado en FileManager
- **Comando**: `FileManager.exe --path "ruta_del_shot"`
- **Uso**: Explorar y gestionar archivos del shot local vs Wasabi S3
- **Color**: Marrón (#8e6c17)

#### ⬇️ **Download Shot**
- **Función**: Descarga el shot completo desde Wasabi S3
- **Comando**: `FileManager.exe --download "ruta_del_shot"`
- **Uso**: Sincronizar archivos remotos hacia local
- **Color**: Marrón (#8e6c17)

#### ⬆️ **Upload Shot**
- **Función**: Sube el shot completo a Wasabi S3
- **Comando**: `FileManager.exe --upload "ruta_del_shot"`
- **Uso**: Sincronizar archivos locales hacia remoto
- **Color**: Marrón (#8e6c17)

#### 🎬 **Download Clip**
- **Función**: Descarga **solo el/los clip(s) seleccionado(s)** desde Wasabi S3, no el shot completo
- **Diferencia con Download Shot**: `Download Shot` descarga la carpeta entera del shot (unidad/proyecto/grupo/shot). `Download Clip` descarga únicamente el media del clip seleccionado.
- **Selección de clip**: usa el **Método 1 (selección pura)** — opera sobre los clips realmente seleccionados en el timeline, **ignorando el playhead**. Soporta seleccionar y descargar **uno o varios clips a la vez**, de cualquier track.
- **Lógica de ruta a descargar** (según `mediaSource().singleFile()`):
  - **Archivo de video único** (`.mov`, `.mp4` → `singleFile() == True`): se descarga ese archivo con `--download-file`.
  - **Secuencia de imágenes** (`..._%04d.exr` → `singleFile() == False`): se descarga la **carpeta** que contiene la secuencia con `--download`.
- **Comando**: arma **una sola llamada** combinando todos los clips seleccionados:
  `FileManager.exe --download "<carpeta_seq1>" "<carpeta_seq2>" --download-file "<archivo1>" "<archivo2>" --notify-completion "<carpeta_marcadores>"`
- **Overwrite**: los archivos individuales se descargan con `overwrite=true` (un clip online se puede re-descargar).
- **Tabs**: a diferencia de los botones de shot, Download Clip **no abre ningún tab** en FileManager — solo dispara la descarga y FileManager cambia a la pestaña *Activity*.
- **Reconexión automática**: el comando incluye `--notify-completion "<Startup>/logs/download_clip_done"`. FileManager escribe un marcador `.json` al terminar cada descarga; el watcher `LGA_NKS_DownloadClip_Watcher.py` lo detecta y reconecta el clip offline en Hiero automáticamente (ver sección **Reconexión automática** más abajo).
- **Logging**: el script imprime via `debug_print`, por cada clip: nombre (`clip.name()`), ruta (`mediaSource().fileinfos()[0].filename()`), tipo (archivo/secuencia) y estado online/offline (`mediaSource().isMediaPresent()`).
- **Color**: Gradiente magenta/violeta (`gradient_magenta_violet`)

### 📂 Estructura de Rutas

Los botones operan sobre la **ruta del shot**, no del archivo individual:
```
Unidad:/VFX-PROJECTO/GRUPO/SHOT_NAME
Ejemplo: T:/VFX-LC/101/LC_1010_010_Beauty_Senora
```

**Nota**: La ruta se extrae automáticamente del clip seleccionado usando lógica inteligente (playhead primero, selección como fallback).

### 🔧 Implementación Técnica

Los scripts ejecutan comandos CLI reales de FileManager:
- **OpenPath**: `FileManager.exe --path "ruta_del_shot"`
- **Download**: `FileManager.exe --download "ruta_del_shot"`
- **Upload**: `FileManager.exe --upload "ruta_del_shot"`
- **DownloadClip**: `FileManager.exe --download "<carpeta_secuencia>" ... --download-file "<archivo>" ... --notify-completion "<carpeta_marcadores>"` (una sola llamada combinada para todos los clips seleccionados, con notificación de finalización)

**Cálculo de ruta del shot**: Los scripts detectan la carpeta del shot con lógica inteligente:

**Algoritmo**:
1. Normaliza la ruta para manejar separadores mixtos (`/` y `\`)
2. Busca primero un patrón de shot (ej: `BRDA_050_010`) y corta la ruta hasta esa carpeta
3. Si no encuentra patrón, usa una estructura de ruta dependiendo del OS:
   - macOS: `/Volumes/<volumen>/<drive>/<proyecto>/<grupo>/<shot>`
   - Windows: `T:/<proyecto>/<grupo>/<shot>`
4. Si la ruta es corta, usa fallback subiendo carpetas desde el archivo

**Ejemplo**:
- Ruta completa: `T:/VFX-LC/101/LC_1021_050_Beauty_Senora/Comp/4_publish/LC_1021_050_Beauty_Senora_comp_v014/LC_1021_050_Beauty_Senora_comp_v014_%04d.exr`
- Detecta `LC_1021_050_Beauty_Senora` y corta en: `T:/VFX-LC/101/LC_1021_050_Beauty_Senora`

**Rutas del ejecutable**:
- **Producción**: `C:\Portable\LGA\FileManager\FileManager.exe`
- **Desarrollo**: `C:\Portable\LGA_FileManager\build\FileManager.exe` (cuando `Desarrollo = True`)

**macOS**:
- Wrapper recomendado: `LGA_NKS_Coordination_Panel_py/fm_cli_mac.sh` (usa `open -na`)

**Lógica de selección automática**:
- Si `Desarrollo = True` y el archivo existe en la carpeta build → usa desarrollo
- Si `Desarrollo = True` pero el archivo NO existe → usa producción como fallback
- Si `Desarrollo = False` → usa producción

Los scripts incluyen una variable `Desarrollo = True` para alternar entre rutas con verificación automática.

Los comandos se ejecutan de forma asíncrona (subprocess.Popen) para no bloquear la interfaz de Hiero/Nuke Studio.

---

## 🔄 Reconexión automática (Download Clip)

Cuando se usa **Download Clip**, al terminar la descarga el clip se reconecta solo en Hiero, sin intervención del usuario. El mecanismo es **archivo marcador** (FileManager escribe, Hiero vigila):

### Flujo

1. **Download Clip** arma el comando agregando `--notify-completion "<Startup>/logs/download_clip_done"`.
2. **FileManager** descarga normalmente. Al recibir la señal `celeryTaskCompleted` de una tarea lanzada con `--notify-completion`, escribe un marcador `.json` (de forma atómica: `.tmp` + rename) en esa carpeta:
   ```json
   { "task_id": "...", "success": true, "items": [ { "path": "T:/.../ref.mov", "kind": "file" } ] }
   ```
   `kind` es `"file"` (archivo único) o `"folder"` (carpeta de la secuencia).
3. **El watcher** `LGA_NKS_Coordination_Panel_py/LGA_NKS_DownloadClip_Watcher.py` (lo arranca el Coordination Panel al iniciar Hiero) revisa esa carpeta cada ~5 s con un `QTimer`. Por cada marcador:
   - Si `success` es `false` → no reconecta, descarta el marcador.
   - Si `success` es `true` → busca el/los clip(s) cuyo media coincide (`file` = ruta exacta; `folder` = `dirname` del media de la secuencia), ejecuta `reconnectMedia()` con fallback `refresh()`, y borra el marcador.

### Garantías de robustez

- El watcher corre en el **hilo principal** de Hiero (la reconexión toca la API de Hiero). El `QTimer` no bloquea: el callback es trabajo de milisegundos.
- Es **stateless** entre ticks: si la descarga se cancela, FileManager se cierra o crashea, **no se escribe marcador** → el watcher sigue idle y el clip queda offline (correcto).
- Cada marcador se **borra siempre** tras procesarlo (haya match o no).
- Marcadores sin clip que matchee (proyecto no cargado aún) se reintentan hasta un **TTL de 30 min** y luego se descartan → sin huérfanos eternos.
- Escritura atómica del marcador (`.tmp` + rename) → el watcher nunca lee un `.json` a medio escribir.

---

## 📚 Referencias Técnicas

- **`LGA_NKS_Coordination_Panel.py`** (raíz de Startup)
  - Clase `FlowProdPanel`: define los botones del panel en `self.fixed_buttons`.
  - `download_shot_from_filemanager()`: lanza `LGA_NKS_FileManager_Download.py`.
  - `upload_shot_to_filemanager()`: lanza `LGA_NKS_FileManager_Upload.py`.
  - `open_shot_in_filemanager()`: lanza `LGA_NKS_FileManager_OpenPath.py`.
  - `download_clip_from_filemanager()`: lanza `LGA_NKS_FileManager_DownloadClip.py`.

- **`LGA_NKS_Coordination_Panel_py/LGA_NKS_FileManager_OpenPath.py`**
  - `main()`, `get_shot_path()`, `build_filemanager_cmd()`: abre la carpeta del shot.

- **`LGA_NKS_Coordination_Panel_py/LGA_NKS_FileManager_Download.py`**
  - `main()`, `get_shot_path()`, `build_filemanager_cmd()`: descarga el shot completo.

- **`LGA_NKS_Coordination_Panel_py/LGA_NKS_FileManager_Upload.py`**
  - `main()`, `get_shot_path()`, `build_filemanager_cmd()`: sube el shot completo.

- **`LGA_NKS_Coordination_Panel_py/LGA_NKS_FileManager_DownloadClip.py`**
  - `main()`: itera los clips seleccionados, los clasifica en secuencias/archivos y dispara la descarga.
  - `_get_selected_clips()`: obtiene los clips seleccionados (Método 1, sin playhead).
  - `_inspect_clip()`: extrae nombre, ruta, tipo (`singleFile()`) y estado online/offline.
  - `_path_has_vfx_root()`: valida que la ruta tenga raíz `VFX-` (requisito del CLI).
  - `get_filemanager_exe()`, `build_filemanager_cmd()`: resuelven el ejecutable y arman la llamada combinada `--download` / `--download-file` / `--notify-completion`.
  - `get_notify_dir()`: devuelve la carpeta de marcadores (`logs/download_clip_done`).
  - `setup_debug_logging()`, `debug_print()`: sistema de logging a archivo.

- **`LGA_NKS_Coordination_Panel_py/LGA_NKS_DownloadClip_Watcher.py`** (lo arranca el Coordination Panel al iniciar Hiero)
  - `DownloadClipWatcher`: `QObject` con un `QTimer` que vigila la carpeta de marcadores.
  - `start_watcher()`: crea la instancia del watcher (se llama al cargarse el módulo).
  - `_scan_markers()`, `_process_marker()`: leen y procesan los marcadores `.json`.
  - `_find_and_reconnect()`: matchea la ruta del marcador con los clips de las secuencias.
  - `_reconnect_clip()`: ejecuta `reconnectMedia()` con fallback `refresh()`.
  - `get_marker_dir()`: carpeta vigilada (debe coincidir con `get_notify_dir()` del script anterior).

- **`LGA_NKS_Coordination_Panel.py`**
  - Al final del módulo carga e inicia `LGA_NKS_DownloadClip_Watcher.py` (mantiene la referencia en `download_clip_watcher_module`).

- **`LGA_NKS_Shared/LGA_NKS_GetClip.py`**
  - `get_selected_clips()`: devuelve los clips seleccionados en el timeline (excluye efectos), usado por DownloadClip.
  - `get_clip_to_process()`: método híbrido playhead+selección, usado por Download/Upload/OpenPath.

- **`C:\Portable\LGA_FileManager\src\main.cpp`** (repo de FileManager)
  - `startCliDownloadFile()`: descarga un archivo individual (resuelve tamaño en S3, encola 1 objeto).
  - `startCliDownload()`: descarga una carpeta completa (shots / secuencias).
  - `registerCliNotifyTask()`, `writeCliCompletionMarker()`: registran la tarea y escriben el marcador `.json` al completarse (señal `celeryTaskCompleted`).
  - Parseo CLI de `--download`, `--download-file` (ambos multi-ruta) y `--notify-completion`; transporte por IPC (`CliCommandPayload`).

---

