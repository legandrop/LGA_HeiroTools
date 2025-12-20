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

**¿Necesitas más detalles?** Consulta `Docs/FM/Doc_FiMa_CLI.md` para documentación técnica completa.</contents>
</xai:function_call">**He creado una guía simple y clara para el CLI de FileManager:** `Docs/FM/GUIA_CLI_SIMPLE.md`

Esta guía incluye:

## ✅ **Lo esencial:**
- **¿Qué hace FileManager?** - Explicación breve
- **3 comandos principales** - `--path`, `--download`, `--upload`
- **Ejemplos concretos** - Copiar y pegar directo
- **Reglas de rutas** - Qué rutas funcionan y cuáles no
- **Estados visuales** - Significado de colores en la UI
- **Solución de problemas** - Errores comunes

## 🎯 **Características de la guía:**
- **Simple y directa** - Sin jerga técnica innecesaria
- **Ejemplos ejecutables** - Código listo para usar
- **Visual clara** - Emojis y formato fácil de seguir
- **Enfoque práctico** - Lo que alguien necesita saber para usar el CLI

La guía está basada en la documentación técnica existente pero adaptada para usuarios que solo quieren usar el CLI sin entender los detalles internos.

¿Quieres que agregue algún ejemplo específico o sección adicional? 🔧