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

## Análisis de Rendimiento (Basado en Logs v3.32)

### Estadísticas Generales
- **Tiempo total típico**: ~2.8 segundos para 15 clips
- **630 entradas de log** procesadas
- **Tiempo promedio por log**: ~0.004s

### Operaciones Más Lentas (Top Gaps)

1. **0.118s** - `doScan completado` (PHLDA_033_070_Chroma_LivingNoche)
2. **0.064s** - `doScan completado` (PHLDA_052_010_DMP_Binoculares_comp)
3. **0.062s** - Extracción de versión "No info"
4. **0.052s** - `doScan completado` (PHLDA_042_010_Add_CasaBouchard)
5. **0.042s** - Cálculo de ruta base de shot
6. **0.039s** - Búsqueda de task en shot
7. **0.037s** - Búsqueda de shot en SG
8. **0.032s** - Extracción de status de task

### Clips Más Lentos de Procesar

1. **0.458s** - PHLDA_052_010_DMP_Binoculares_comp
2. **0.396s** - PHLDA_033_070_Chroma_LivingNoche
3. **0.373s** - PHLDA_033_040_Chroma_LivingNoche
4. **0.288s** - PHLDA_042_010_Add_CasaBouchard
5. **0.154s** - PHLDA_033_050_Chroma_LivingNoche

### Análisis Detallado por Operación

#### doScan (ESCANEO DE VERSIONES)
- **Conteo**: 3 operaciones
- **Promedio**: 0.084s
- **Máximo**: 0.122s
- **Mínimo**: 0.057s
- **Total**: 0.252s
- **Porcentaje del tiempo total**: ~9%

#### XYplorer Send (TAGS EN EXPLORER)
- **Conteo**: 9 operaciones
- **Promedio**: 0.023s
- **Máximo**: 0.026s
- **Mínimo**: 0.018s
- **Total**: 0.207s
- **Porcentaje del tiempo total**: ~7.3%

#### SG Shot Lookup (CONSULTAS A BASE DE DATOS)
- **Conteo**: 15 operaciones
- **Promedio**: 0.004s
- **Máximo**: 0.006s
- **Mínimo**: 0.003s
- **Total**: 0.060s
- **Porcentaje del tiempo total**: ~2.1%

#### SG Task Lookup
- **Conteo**: 15 operaciones
- **Promedio**: 0.006s
- **Máximo**: 0.039s
- **Mínimo**: 0.002s
- **Total**: 0.090s
- **Porcentaje del tiempo total**: ~3.2%

#### setActiveVersion
- **Conteo**: 3 operaciones
- **Promedio**: 0.008s
- **Máximo**: 0.009s
- **Mínimo**: 0.008s
- **Total**: 0.024s
- **Porcentaje del tiempo total**: ~0.8%

## Diagnóstico de Cuellos de Botella

### Problema Principal: doScan
El análisis revela que **doScan es el mayor cuello de botella**, consumiendo ~9% del tiempo total del pull. Esta operación es inherentemente lenta ya que:
- Escanea el sistema de archivos en busca de versiones
- Puede tardar hasta 0.122s por clip
- Se ejecuta secuencialmente, bloqueando la UI

### Problema Secundario: XYplorer
Las operaciones de XYplorer consumen ~7.3% del tiempo total, aunque ya corren en un thread separado. Sin embargo, pueden interferir con otras operaciones.

### Conclusión
Las consultas a base de datos (SG) son **muy eficientes** (~5.3% del tiempo total) y no representan un problema. El foco debe estar en paralelizar las operaciones de escaneo y optimizar el manejo de threads.

## Mejoras Implementadas en v3.33

### 1. Paralelización de doScan
- **Objetivo**: Ejecutar operaciones de doScan en hilos separados y paralelos
- **Beneficio**: No bloquea la UI principal ni el procesamiento de otros clips
- **Implementación**:
  - Cada clip procesa su doScan en un thread dedicado
  - Múltiples doScan corren simultáneamente
  - Sincronización final para resultados completos

### 2. Optimización de Threads XYplorer
- **Objetivo**: Mejorar el aislamiento de operaciones XYplorer
- **Beneficio**: Reduce interferencias entre operaciones
- **Implementación**:
  - Mejor gestión de threads para XYplorer
  - Queue dedicada para operaciones de tagging
  - Timeouts mejorados para evitar bloqueos

### 3. Arquitectura Asíncrona Mejorada
- **Objetivo**: Mantener responsividad de UI durante procesamiento masivo
- **Beneficio**: Usuario puede continuar trabajando mientras se procesa
- **Implementación**:
  - Thread pool para operaciones pesadas
  - Callbacks para actualizar UI cuando terminan
  - Indicadores de progreso para operaciones largas

### 4. Sincronización Inteligente
- **Objetivo**: Garantizar resultados completos antes de mostrar ventana final
- **Beneficio**: Usuario obtiene resultados finales correctos
- **Implementación**:
  - Wait groups para operaciones paralelas
  - Validación de estado final
  - Rollback automático en caso de errores

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

## Historial de Versiones

### v3.33 (Próxima)
- Paralelización completa de doScan
- Arquitectura multithread mejorada
- Optimización de XYplorer threading
- UI responsiva durante procesamiento masivo

### v3.32
- Sistema de logging con timestamps
- Debug print mejorado
- Arreglos para Hiero 16 (PySide6)

### v3.31
- Soporte para versiones offline
- Reintentos automáticos de cambio de color

### v3.30
- Centralización de nombres de track
- Soporte para nomenclaturas múltiples

## Contribución

Para mejoras o reportes de bugs, contactar al equipo de desarrollo.

---
**Autor**: LGA Team
**Última actualización**: Enero 2026