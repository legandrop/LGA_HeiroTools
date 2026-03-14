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
- Wrapper recomendado: `LGA_NKS_Flow_Prod/fm_cli_mac.sh` (usa `open -na`)

**Lógica de selección automática**:
- Si `Desarrollo = True` y el archivo existe en la carpeta build → usa desarrollo
- Si `Desarrollo = True` pero el archivo NO existe → usa producción como fallback
- Si `Desarrollo = False` → usa producción

Los scripts incluyen una variable `Desarrollo = True` para alternar entre rutas con verificación automática.

Los comandos se ejecutan de forma asíncrona (subprocess.Popen) para no bloquear la interfaz de Hiero/Nuke Studio.

---

