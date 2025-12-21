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

**Cálculo de ruta del shot**: Los scripts extraen la carpeta del shot tomando las primeras 4 partes de la ruta:

**Estructura**: `unidad/proyecto/grupo/shot/...`

**Algoritmo**:
1. Normaliza la ruta para manejar separadores mixtos (`/` y `\`)
2. Divide la ruta en partes usando `/` como separador universal
3. Toma las primeras 4 partes: `[unidad, proyecto, grupo, shot]`
4. Une las partes para formar la ruta del shot

**Ejemplo**:
- Ruta completa: `T:/VFX-LC/101/LC_1021_050_Beauty_Senora/Comp/4_publish/LC_1021_050_Beauty_Senora_comp_v014/LC_1021_050_Beauty_Senora_comp_v014_%04d.exr`
- Partes: `['T:', 'VFX-LC', '101', 'LC_1021_050_Beauty_Senora', 'Comp', '4_publish', 'LC_1021_050_Beauty_Senora_comp_v014', 'LC_1021_050_Beauty_Senora_comp_v014_%04d.exr']`
- Toma primeras 4: `['T:', 'VFX-LC', '101', 'LC_1021_050_Beauty_Senora']`
- Extrae: `T:/VFX-LC/101/LC_1021_050_Beauty_Senora` ← **Esta es la carpeta del shot**

**Rutas del ejecutable**:
- **Producción**: `C:\Portable\LGA\FileManager\FileManager.exe`
- **Desarrollo**: `C:\Portable\LGA_FileManager\build\FileManager.exe` (cuando `Desarrollo = True`)

**Lógica de selección automática**:
- Si `Desarrollo = True` y el archivo existe en la carpeta build → usa desarrollo
- Si `Desarrollo = True` pero el archivo NO existe → usa producción como fallback
- Si `Desarrollo = False` → usa producción

Los scripts incluyen una variable `Desarrollo = True` para alternar entre rutas con verificación automática.

Los comandos se ejecutan de forma asíncrona (subprocess.Popen) para no bloquear la interfaz de Hiero/Nuke Studio.

---

