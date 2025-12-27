# Módulo LGA_Projects_Panel_SwitchSequence

## Resumen

Módulo auxiliar que implementa la **solución ganadora V3 Híbrida** para cambiar de secuencia en Hiero con preservación completa de estado del viewer.

## Solución Implementada

### 🎯 **V3 HÍBRIDA - La Mejor Opción**
- ✅ **Velocidad óptima:** 0.49s (más rápido que v4)
- ✅ **Ajustes completos preservados:** Gain/Gamma/Saturation + Playhead automático
- ✅ **Comportamiento nativo:** Reemplaza viewer como Hiero nativo
- ✅ **Sin duplicados:** Lógica viewer-centric inteligente
- ✅ **UI completa:** Reduce panel + scroll automático

## API

### Función Principal

```python
switch_to_sequence(target_sequence_name)
```

**Parámetros:**
- `target_sequence_name` (str): Nombre de la secuencia objetivo

**Retorna:**
- `bool`: True si el cambio fue exitoso, False en caso contrario

**Características:**
- ✅ **Búsqueda inteligente:** Busca la secuencia en TODOS los proyectos abiertos
- ✅ **Cross-project:** Funciona perfectamente con secuencias de cualquier proyecto abierto
- ✅ **Cambio automático:** Cambia automáticamente al proyecto correcto cuando es necesario
- ✅ **Objetos Sequence directos:** Acepta objetos Sequence directamente (más eficiente y cross-project)
- ✅ **Detección de proyecto:** Identifica automáticamente a qué proyecto pertenece la secuencia
- ✅ **Preservación completa:** Gain/Gamma/Saturation + Playhead automático
- ✅ **Optimización UI:** Reduce panel + scroll al top track
- ✅ **Manejo de duplicados:** Cierra viewers existentes correctamente antes de abrir (evita duplicados)
- ✅ **Logging detallado:** Tiempos de ejecución y estado de operaciones

## Uso en Panel de Proyectos

### Importación
```python
from LGA_Projects_Panel_SwitchSequence import switch_to_sequence
```

### Integración
```python
def on_sequence_click(self, sequence_name):
    """Manejador de click en secuencia"""
    try:
        success = switch_to_sequence(sequence_name)
        if success:
            print(f"✅ Secuencia '{sequence_name}' cambiada exitosamente")
            # Actualizar UI si es necesario
        else:
            print(f"❌ Error cambiando a secuencia '{sequence_name}'")
    except Exception as e:
        print(f"❌ Error: {e}")
```

## Compatibilidad

- ✅ **Nuke 15/16:** Usa `LGA_QtAdapter_HieroTools` para compatibilidad Qt
- ✅ **Hiero APIs:** Funciona con todas las versiones de Hiero
- ✅ **Fallbacks:** Incluye fallbacks para imports de Qt si el adapter no está disponible

## Dependencias

### Requeridas
- `hiero.core` y `hiero.ui` (APIs de Hiero)
- Proyecto abierto en Hiero con secuencias

### Opcionales (para UI completa)
- `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py` - Reduce panel izquierdo
- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py` - Scroll al top track

## Testing

### Verificación de Funcionalidad
1. Abrir proyecto con múltiples secuencias en Hiero
2. Ajustar viewer: Gain=0.5, Gamma=1.2, posicionar playhead
3. Ejecutar: `switch_to_sequence("nombre_secuencia")`
4. Verificar: Ajustes preservados, playhead correcto, UI optimizada

### Casos de Testing
- ✅ Secuencia ya activa (debe ser no-op)
- ✅ Primer cambio de secuencia
- ✅ Cambios múltiples entre secuencias ya abiertas
- ✅ Proyectos con una sola secuencia
- ⚠️ **Limitación:** No funciona entre proyectos diferentes (busca solo en proyecto activo)

## Arquitectura

### Componentes
1. **Captura de Estado:** `_get_viewer_state()` - Gain/Gamma/Saturation
2. **Lógica Principal:** `switch_to_sequence_hybrid()` - Algoritmo completo
3. **Aplicación de Estado:** `_apply_viewer_settings()` - Restaura ajustes
4. **UI Helpers:** `reduce_sequence_window()`, `scroll_to_top_track()`

### Flujo de Ejecución
```
1. Verificar proyectos abiertos
2. Buscar secuencia objetivo
3. Verificar si ya está activa (optimización)
4. Capturar estado del viewer actual
5. Buscar/cerrar viewer existente duplicado
6. Abrir nueva secuencia (playhead automático)
7. Aplicar ajustes preservados
8. Optimizar UI (reduce + scroll)
```

## Logs y Debugging

### Output Normal (con debugging de UI)
```
🔄 Switch híbrido a '710-990'...
✅ Switch híbrido perfecto completado en 0.49s
   ├── Viewer capture: 0.000s
   ├── Existing viewer close: 0.000s
   ├── Sequence open: 0.470s
   ├── Viewer settings apply: 0.002s
   ├── UI reduce: 0.002s
   ├── UI scroll: 0.001s
   └── Total: 0.49s
  🔧 Aplicando reducción de panel izquierdo...
  📋 Verificando que hay secuencia activa...
  ✅ Secuencia activa: 710-990
  🔍 Buscando script: C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_ViewerTL\LGA_NKS_Reduce_SeqWin.py
  ✅ Script encontrado
  ✅ Script importado exitosamente: LGA_NKS_Reduce_SeqWin
  📋 Ejecutando reduce_module.main()...
  🔧 Aplicando scroll al track superior...
  📋 Verificando que hay secuencia activa...
  ✅ Secuencia activa: 710-990
  🔍 Buscando script: C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_ViewerTL\LGA_NKS_ScrollTo_TopTrack.py
  ✅ Script encontrado
  ✅ Script importado exitosamente: LGA_NKS_ScrollTo_TopTrack
  📋 Ejecutando scroll_module.main()...
  🔍 Verificando optimizaciones aplicadas...
  📐 Tamaños del splitter después de reducción: 340px | 1260px
  ✅ Panel izquierdo correctamente reducido a 340px
```

### Casos Especiales
- **Ya activa:** `✅ Ya activa - sin cambios`
- **Error:** `❌ Error: Secuencia 'nombre' no encontrada`
- **Proyecto diferente:** `❌ Error: Secuencia '000' no encontrada` (limitación conocida)

## Problemas Conocidos

### ✅ **RESUELTO: Cambio entre Proyectos Diferentes**

**Problema original:** La función buscaba secuencias únicamente en el proyecto activo.

**Error anterior:**
```
🔄 Switch híbrido a '000'...
❌ Error: Secuencia '000' no encontrada
```

**✅ Solución implementada y probada:**
- ✅ **Objetos Sequence directos:** La función ahora acepta objetos Sequence directamente
- ✅ **openInTimeline cross-project:** Descubrimos que `hiero.ui.openInTimeline(sequence_obj)` funciona automáticamente incluso cross-project
- ✅ **Cambio automático:** Hiero cambia el proyecto activo automáticamente cuando abres una secuencia de otro proyecto
- ✅ **Sin intervención manual:** Todo funciona automáticamente sin necesidad de cerrar/abrir proyectos

**Resultado actual (probado y funcionando):**
```
🎯 Usando objeto Sequence directamente para '000'
   Proyecto: 'ERSO_SUP_v011'
   📊 Cambiando de proyecto 'BRDA_SUP_v050' → 'ERSO_SUP_v011'
   ✅ openInTimeline maneja el cambio automáticamente
✅ Switch híbrido perfecto completado
```

**Estado:** ✅ **COMPLETAMENTE RESUELTO Y PROBADO EN PRODUCCIÓN** - Funciona perfectamente cross-project, sin duplicados, con cambio automático de proyecto

## Próximos Pasos

Una vez probado y funcionando en la ventana de testing:

1. ✅ **Integrar en panel final** (`LGA_Projects_Panel.py`) - PENDIENTE
2. ✅ **Probar en producción** con casos reales - ✅ COMPLETADO
3. ✅ **Documentar** en documentación completa del panel - ✅ COMPLETADO
4. ✅ **Resolver limitación entre proyectos** - ✅ COMPLETADO (usando objetos Sequence directamente)

## Referencias

- [`DOCUMENTACION_COMPLETA_SWITCH_SEQUENCE.md`](../exploracion/DOCUMENTACION_COMPLETA_SWITCH_SEQUENCE.md) - Documentación técnica completa
- [`test_sequence_switch_v3.py`](../exploracion/test_sequence_switch_v3.py) - Script de testing original
- [`LGA_QtAdapter_HieroTools.py`](../LGA_QtAdapter_HieroTools.py) - Adapter Qt para compatibilidad
