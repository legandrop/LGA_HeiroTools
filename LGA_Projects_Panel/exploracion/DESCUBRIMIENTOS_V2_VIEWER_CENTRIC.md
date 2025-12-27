# 🎯 DESCUBRIMIENTOS V2: ESTRATEGIA VIEWER-CENTRIC

## Resumen Ejecutivo

Después de múltiples exploraciones, **descubrimos que Hiero mantiene múltiples viewers** (uno por secuencia abierta) pero solo uno está visible/activo a la vez. La estrategia VIEWER-CENTRIC detecta viewers existentes y cambia foco en lugar de crear duplicados.

## 🔍 Descubrimientos Clave

### 1. Arquitectura Real de Hiero

**ANTES (hipótesis errónea):**
- `getTimelineEditor()` devuelve editors para secuencias "abiertas"
- `openInTimeline()` crea nuevos timelines
- Problema: duplicados y ventanas flotantes

**DESPUÉS (descubrimiento real):**
- Hiero mantiene **`Foundry::Storm::UI::Viewer`** widgets (uno por secuencia abierta)
- Solo **uno está `Visible: True`** (activo)
- Los demás están **`Visible: False`** pero existen (abiertos pero no en foco)
- `getTimelineEditor()` y `window().isVisible()` NO detectan correctamente esto

### 2. Evidencia del Descubrimiento

**Logs del explorador viewer-centric:**
```
🎥 Widgets de viewer encontrados: 39

7. Foundry::Storm::UI::Viewer
   ObjectName: 'uk.co.thefoundry.sequenceviewer.19'
   Visible: False    ← ¡OCULTO!
   Window Title: '710-990'

11. Foundry::Storm::UI::Viewer
   ObjectName: 'uk.co.thefoundry.sequenceviewer.25'
   Visible: True     ← ¡ACTIVO!
   Window Title: '010-350'
```

**Conclusión:** ¡Dos viewers existen! Uno para cada secuencia abierta.

### 3. Métodos que NO Funcionan

- ❌ `getTimelineEditor().window().isVisible()` - Solo detecta el activo
- ❌ `isInAnyTimeline()` - "Invalid arguments"
- ❌ `currentViewer()` - No coincide con los widgets encontrados
- ❌ `getTimelineEditor()` flags - Crean ventanas flotantes

### 4. Método que SÍ Funciona

**Detección de viewers existentes:**
```python
def _find_viewer_for_sequence(sequence_name):
    viewer_widgets = _find_viewer_widgets()  # Foundry::Storm::UI::Viewer
    for widget in viewer_widgets:
        if widget.windowTitle() == sequence_name:
            return widget  # ¡Viewer existente encontrado!
    return None
```

**Cambio de foco:**
```python
def _switch_viewer_focus(target_viewer):
    # Ocultar todos los demás viewers
    for viewer in all_viewers:
        if viewer != target_viewer:
            viewer.hide()

    # Mostrar el viewer objetivo
    target_viewer.show()
    target_viewer.raise_()
    target_viewer.activateWindow()
```

## 🧪 Resultados de la Implementación

### Caso 1: Viewer NO existe → Crear nuevo ✅
```
🔍 ESTADO INICIAL de Viewers:
  1. '710-990' - Visible: True

🎯 ESTRATEGIA VIEWER-CENTRIC: Buscar viewer existente...
🆕 No hay viewer existente - creando nuevo...

🔍 ESTADO tras crear nuevo viewer:
  8. '010-350' - Visible: True  ← ¡Nuevo viewer creado!
```

### Caso 2: Viewer existe pero no en foco → Cambiar foco ⚠️
```
🔍 ESTADO INICIAL de Viewers:
  8. '010-350' - Visible: False  ← ¡Existe pero oculto!

✅ Viewer existente encontrado - cambiando foco...
🔄 Cambiando foco al viewer: '010-350'

🔍 DESPUÉS del cambio:
  8. '010-350' - Visible: True   ← ¡Ahora visible!

⚠️ Foco cambiado pero secuencia no se activó.
```

## 🎯 SOLUCIÓN DEFINITIVA ENCONTRADA ✅

### ¡MÉTODO 5 FUNCIONA PERFECTAMENTE!

**Resultado final:**
```
🎯 MÉTODO 5 (cerrar→reabrir): ✅ FUNCIONA
🎉 ¡MÉTODO PERFECTO! Cierra existente → Reabre → Sin duplicados
```

### 🔧 Estrategia Ganadora: Cerrar Existente → Reabrir

**Implementación definitiva:**
```python
def switch_to_sequence_final(sequence_name):
    # 1. Buscar viewer existente
    existing_viewer = _find_viewer_for_sequence(sequence_name)

    if existing_viewer:
        # 2. SI EXISTE → Cerrarlo para evitar duplicados
        existing_viewer.close()
        print("🔒 Viewer existente cerrado")

    # 3. SIEMPRE usar openInTimeline (funciona perfectamente)
    hiero.ui.openInTimeline(target_seq)
    print("✅ Secuencia activada correctamente")

    # Resultado: Sin duplicados, secuencia activa
```

### 📊 Evidencia del Éxito

**ANTES:**
```
🎯 Secuencia activa: '710-990'
8. '010-350' - Visible: False  ← Existe pero oculto
```

**DESPUÉS de aplicar solución:**
```
✅ Viewer existente encontrado: '010-350'
🔒 Cerrando viewer existente para evitar duplicados...
✅ Viewer existente cerrado

🚀 Abriendo secuencia con openInTimeline...
✅ openInTimeline ejecutado

🎯 Secuencia activa: '010-350'  ← ¡PERFECTO!
17. '010-350' - Visible: True   ← Sin duplicados
```

### 🎯 ¿Por qué funciona esta estrategia?

1. **`openInTimeline` es confiable:** Siempre activa la secuencia correctamente
2. **Cerrar primero evita duplicados:** Elimina el viewer existente antes de crear el nuevo
3. **Máximo 1 viewer por secuencia:** Nunca hay duplicados
4. **Simple y robusto:** No depende de APIs complejas que pueden fallar

### 📋 Comparación Final de Métodos

| Método | Resultado | Problema |
|--------|-----------|----------|
| Show/Hide básico | ❌ Falla | No activa secuencia |
| Con activateWindow | ❌ Falla | No activa secuencia |
| Buscar y click | ❌ Falla | No encuentra widgets clickeables |
| Forzar activación | ❌ Falla | APIs no funcionan |
| **Cerrar→Reabrir** | ✅ **PERFECTO** | **NINGUNO** |

## 📊 Arquitectura Final Comprendida

```
Hiero App
├── Proyecto
│   ├── Secuencia A (abierta) ← Activa
│   ├── Secuencia B (abierta) ← Inactiva
│   └── Secuencia C (cerrada)
│
├── UI Layer
│   ├── Foundry::Storm::UI::Viewer A (Visible: True) ← Único visible
│   ├── [Otros viewers cerrados/invisibles]
│   └── Timeline Editor (sincronizado con viewer visible)
│
└── Estado Interno
    ├── activeSequence: Secuencia A
    └── currentViewer: Viewer visible
```

**Conclusión:** La solución es **siempre usar `openInTimeline`** pero **cerrar viewers existentes primero** para evitar duplicados.

---

**Fecha:** Diciembre 2025
**Estado:** ✅ **SOLUCIÓN COMPLETA Y DEFINITIVA**
**Implementación:** Método 5 - Cerrar existente → Reabrir con openInTimeline
**Resultado:** Sin duplicados, secuencia activada correctamente, robusto y confiable
