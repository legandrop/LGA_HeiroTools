# LGA_NKS_Flow_Pull v3.33

## Descripción

Script de integración entre Hiero y Flow Production Tracker. Compara los estados de tareas Comp de los shots del timeline de Hiero con los estados registrados en Flow PT y aplica cambios automáticamente.

## Funcionalidades Principales

- **Comparación automática**: Compara versiones y estados entre Hiero y Flow Production
- **Cambio de versiones**: Actualiza automáticamente clips a la versión más alta disponible
- **Aplicación de colores**: Aplica colores de estado de Flow PT en los clips de Hiero
- **Tags XYplorer**: Aplica tags automáticos en XYplorer según estado de tareas
- **Procesamiento masivo**: Puede procesar múltiples clips seleccionados simultáneamente

## Modo de Uso

### Ejecución Básica
1. Seleccionar clips en el timeline de Hiero
2. Ejecutar el script desde el menú de Hiero
3. Revisar la tabla de cambios (si los hay)

### Modo Force All Clips
- Procesa automáticamente todos los clips del track `_comp_EXR`
- Útil para sincronización completa de secuencias

## Rendimiento actual

- El tiempo total se reparte en micro‑operaciones por clip (parseo, SG lookup, colores, versionado).
- Los clips más lentos suelen ser **offline** o con **mismatch** de versión, porque ejecutan `doScan`, `setActiveVersion` y reconexión de media.
- En macOS, XYplorer no aporta tiempo relevante (no existe); en Windows sigue activo y en thread.

## Optimizaciones actuales (implementadas en el código)

- **Logging asíncrono** en `LGA_NKS_Flow/LGA_NKS_Flow_Pull.py` → `setup_debug_logging()` usa `QueueHandler/QueueListener` para evitar bloqueos al escribir `logs/debugPy.log`.
- **Consola opcional** → `debug_print()` solo imprime si `LGA_DEBUG_CONSOLE=1` (por defecto escribe solo en archivo).
- **XYplorer en macOS** → `tag_shot_folder()` retorna sin crear threads porque XYplorer no existe en macOS. En Windows se mantiene el comportamiento original.
- **Parser de nombres robusto** → `LGA_NKS_Flow/LGA_NKS_Flow_NamingUtils.py::clean_base_name()` limpia EXR/DPX con secuencias, evitando códigos de shot corruptos.

## Arquitectura Técnica

### Flujo de Procesamiento
1. **Parse inicial**: Extrae metadatos de clips seleccionados
2. **Consultas SG**: Obtiene estados desde Flow Production (rápido)
3. **doScan paralelo**: Busca versiones en hilos separados (ahora paralelo)
4. **Aplicación de cambios**: Colores, versiones, tags (parcialmente paralelo)
5. **Sincronización final**: Muestra resultados completos

### Manejo de Estados
- **Offline clips**: Manejo especial para clips sin media presente
- **Version mismatches**: Detección y corrección automática
- **Error recovery**: Reintentos automáticos en operaciones críticas

## Configuración y Dependencias

### Base de Datos
- **Windows**: `C:/Portable/LGA/PipeSync/cache/pipesync.db`
- **macOS**: `~/Library/Caches/LGA/PipeSync/pipesync.db`

### Requisitos del Sistema
- Hiero 15+ (PySide2) o 16+ (PySide6)
- SQLite3
- Acceso a sistema de archivos de producción
- XYplorer (opcional, para tagging automático)

## Troubleshooting

### Problemas Comunes
1. **doScan lento**: Verificar permisos de acceso a archivos
2. **XYplorer no responde**: Verificar instalación y configuración
3. **Base de datos inaccesible**: Verificar paths y permisos
4. **UI congelada**: Indica problema de threading (mejorado en v3.33)

### Debug
- Logs disponibles en: `../logs/debugPy.log`
- Timestamps relativos para análisis de rendimiento
- Usar script analizador: `+Building_Blocks/LGA_analizar_logs_pull.py`
- XYplorer: `+Building_Blocks/LGA_analizar_logs_xyplorer.py`

## Historial de Versiones

### v3.34
- **Simplificación completa**: Eliminada lógica condicional innecesaria entre Hiero 15/16
- doScan funciona correctamente en todas las versiones de Hiero
- Código más simple y mantenible

### v3.32
- Sistema de logging con timestamps
- Debug print mejorado
- Arreglos para Hiero 16 (PySide6): omitir doScan problemático

### v3.31
- Soporte para versiones offline
- Reintentos automáticos de cambio de color

### v3.30
- Centralización de nombres de track
- Soporte para nomenclaturas múltiples

## Contribución

Para mejoras o reportes de bugs, contactar al equipo de desarrollo.

## Optimizacion aplicada (10s -> <1s)

- **Cuello principal:** el costo de logging en tiempo real (muchas escrituras por clip).
- **Solucion:** logging asíncrono + consola opcional (se mantiene el archivo completo en `logs/debugPy.log`).
- **XYplorer:** en macOS se evita crear threads fallidos; en Windows se conserva la funcionalidad completa.
- **Resultado:** en el mismo timeline, el pull pasa de ~10s a <1s sin perder funcionalidad.

---
**Autor**: LGA Team
**Última actualización**: Enero 2026