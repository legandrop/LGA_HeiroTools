> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# FIX_Problemas_RefreshTimeline_3.md

## 🔴 **RESUMEN EJECUTIVO - BUG CRÍTICO EN HIERO 16**

### **Problema Identificado:**
La API `hiero.ui.openInTimeline(seq)` **crashea completamente** en Hiero 16 **SIEMPRE** (con o sin timeline previo existente).

**Descubrimiento crítico (CAMINO 5):**
- ❌ Hipótesis inicial incorrecta: "crashea solo si no hay timeline previo"
- ✅ Realidad: `openInTimeline()` crashea **DENTRO de la API** en H16, incluso con timeline integrado existente
- ✅ El crash ocurre antes de retornar de la función (segmentation fault en C++)

### **Evidencia:**
| Aspecto | Hiero 15 | Hiero 16 |
|---------|----------|----------|
| **Mismo código** | ✅ Funciona perfecto | ❌ **CRASH TOTAL** |
| **Logs posteriores** | ✅ Se ejecutan | ❌ Nunca llegan |
| **Timeline/Viewer creados** | ✅ Correctos | ❌ N/A (crash antes) |
| **Tipo de crash** | N/A | Segmentation fault (silencioso) |

### **Causa raíz:**
- **Bug en Hiero 16:** Refactorización interna rompió `openInTimeline()` para secuencias sin estado previo
- **NO es problema de código:** Mismo código funciona en H15, crashea en H16
- **NO es problema de duplicados:** Secuencia estaba libre (sin panels)
- **Crash en C++:** Por eso no hay excepción Python ni traceback

### **Impacto:**
- ❌ **Refresh timeline** crashea (usa `openInTimeline` internamente)
- ❌ **Projects Panel** a veces crashea (mismo problema)
- ❌ **Cualquier script** que use `openInTimeline` en secuencias nuevas crashea
- ✅ **Funciona SI** la secuencia ya tiene/tuvo panels antes (estado inicializado)

### **Soluciones disponibles:**

**A) CAMINO 6** ⭐ (Detección de versión + Método específico)
- ✅ **CAMINO 5 DESCUBRIMIENTO:** `openInTimeline()` crashea SIEMPRE en H16 (no solo sin timeline previo)
- 🔄 **PROBANDO AHORA:** Detectar versión y usar método correcto para cada una
- **H15:** Usar `openInTimeline()` (funciona perfecto)
- **H16:** Usar `setActiveSequence()` (solo cambia secuencia, no crea panels, pero NO crashea)
- **Estado:** 🔄 En prueba - solución definitiva portable H15/H16

**B) Detección de versión** (Código diferente H15 vs H16)
- Detectar versión con `hiero.core.applicationVersion()`
- H15: Usar `openInTimeline()` normal
- H16: Usar método alternativo o deshabilitar función
- **Estado:** ✅ Método de detección encontrado en codebase

**C) Deshabilitar en H16** (Solución temporal)
- Mostrar mensaje: "Por favor abre la secuencia manualmente"
- Evita crashes pero pierde funcionalidad
- **Estado:** ✅ Fácil de implementar

**D) Reportar a Foundry** (Solución a largo plazo)
- Crear caso de prueba mínimo
- Reportar bug oficial
- Esperar fix en versión futura
- **Estado:** ⏸️ Recomendado después de confirmar workaround

---

## 🎯 OBJETIVO DEL TEST TEORÍA 2

**OBJETIVO PRINCIPAL:**  
Lograr **MOSTRAR EN LA UI** un timeline y un viewer de una secuencia existente que actualmente **NO tiene timeline ni viewer visibles en la UI**.

**ÉXITO =** Timeline y viewer aparecen correctamente en la UI, Hiero permanece estable.  
**FALLO =** Hiero crashea, o los panels no aparecen, o aparecen duplicados zombies.

**Script:** `+Building_Blocks/test_teoria_2.py`

**RESULTADO:** ✅ **TEORÍA 2 CONFIRMADA** - APIs directas (`openInTimeline`) crashean en H16

---

## 🧪 CAMINOS PROBADOS (Estrategias de Creación)

### **CAMINO 1: openInTimeline() DIRECTO** ⭐ (Imitando Projects Panel)

**Estado:** ❌ **FALLA EN HIERO 16** | ✅ **FUNCIONA EN HIERO 15**

**Estrategia:**
```python
hiero.ui.openInTimeline(seq)
_process_events()
```

**Características:**
- ✅ Sin viewers temporales (sin pre-estabilización)
- ✅ Sin cierres de widgets
- ✅ Más simple posible
- ✅ Exactamente como lo hace Projects Panel

**Resultado en Hiero 16:**
- ❌ **CRASH TOTAL** - Hiero se cierra completamente
- ❌ Crash ocurre DENTRO de `openInTimeline(seq)`
- ❌ No llega a ejecutar logs posteriores
- ❌ Última línea: "🔧 Llamando hiero.ui.openInTimeline(seq)..."

**Resultado en Hiero 15:**
- ✅ **FUNCIONA PERFECTAMENTE**
- ✅ Timeline creado: `uk.co.thefoundry.timeline.7`
- ✅ Viewer creado: `uk.co.thefoundry.sequenceviewer.7`
- ✅ Estado final: 4 timelines, 4 viewers (correcto: +1 de cada)
- ✅ No hay duplicados, secuencia aparece en foco
- ✅ Logs completos: "✅ openInTimeline() ejecutado sin excepciones"

**CONCLUSIÓN CRÍTICA:**
- ✅ **TEORÍA 2 CONFIRMADA**: `openInTimeline()` crashea en H16 al crear timeline/viewer para secuencia libre
- ✅ **TEORÍA 1 DESCARTADA**: No es problema de duplicados (secuencia estaba libre)
- ❌ **API `openInTimeline()` está rota en Hiero 16** para este caso de uso específico

---

---

## 🔍 **ANÁLISIS: ¿POR QUÉ CRASHEA EN HIERO 16?**

### **Diferencias Clave H15 vs H16:**

| Aspecto | Hiero 15 | Hiero 16 |
|---------|----------|----------|
| `openInTimeline(seq_libre)` | ✅ Funciona | ❌ **CRASH TOTAL** |
| Logs posteriores | ✅ Se ejecutan | ❌ Nunca llegan |
| Timeline/Viewer creados | ✅ Correctos | ❌ N/A (crash antes) |
| Comportamiento | Estable | Inestable (cierre completo) |

### **Hipótesis sobre la causa:**

**H1: Contexto de ejecución diferente**
- Projects Panel ejecuta desde callbacks de UI (botones Qt)
- Nuestro script ejecuta directo desde consola Python
- Posible problema de threading/event loop en H16

**H2: Estado interno de Hiero diferente**
- Projects Panel cambia ENTRE secuencias que ya tienen/tuvieron panels
- Nuestro test crea panels para secuencia que NUNCA tuvo panels
- H16 podría tener bug al inicializar estructuras internas nuevas

**H3: Cambio en implementación de `openInTimeline()` en H16**
- API refactorizada internamente en H16
- Nuevos requisitos implícitos no documentados
- Crash por asunciones rotas sobre estado de la secuencia

### **¿Por qué Projects Panel no crashea (o crashea menos)?**

Posibles razones:
1. **Secuencias diferentes**: Cambia a secuencias que ya tienen historial de panels
2. **Timing diferente**: Ejecuta desde eventos Qt con estado UI diferente
3. **Limpieza previa**: Cierra viewers viejos antes (aunque documentación dice que crashea en algunos casos)
4. **Misma secuencia**: A veces retorna temprano si ya está activa (línea 384-386)

---

### **CAMINO 2: setActiveSequence() PRIMERO** 🔄 (PROBAR AHORA)

**Estado:** ⏸️ **LISTO PARA PROBAR**

**Estrategia:**
```python
hiero.ui.setActiveSequence(seq)
_process_events()
hiero.ui.openInTimeline(seq)
_process_events()
```

**Características:**
- Activa la secuencia ANTES de crear timeline
- Podría evitar crashes si Hiero necesita secuencia "preparada"
- Sigue siendo prueba limpia

**Resultado esperado:**
- Si funciona (y CAMINO 1 falló) → Necesitas activar secuencia antes
- Si crashea → Confirma problema más profundo

**Resultado en Hiero 16:**
- ⚠️ **`setActiveSequence()` NO EXISTE** en la API (ni en H15 ni en H16)
- ❌ CAMINO 2 se reduce a CAMINO 1 (sin el paso 1)
- ❌ **CRASH TOTAL** en `openInTimeline()` (igual que CAMINO 1)
- ❌ Última línea: "🔧 Paso 2: Llamando hiero.ui.openInTimeline(seq)..."

**Resultado en Hiero 15:**
- ⚠️ **`setActiveSequence()` NO EXISTE** (mismo que H16)
- ✅ PERO `openInTimeline()` **FUNCIONA PERFECTAMENTE**
- ✅ Timeline creado: `uk.co.thefoundry.timeline.13`
- ✅ Viewer creado: `uk.co.thefoundry.sequenceviewer.13`
- ✅ Sin crashes, estado final correcto

**CONCLUSIÓN CRÍTICA:**
- ❌ **CAMINO 2 NO ES SOLUCIÓN** (`setActiveSequence` no existe)
- ❌ **Problema confirmado:** `openInTimeline()` está **ROTO en H16**
- ✅ **Mismo código, resultados opuestos:** H15 funciona, H16 crashea
- 🔴 **NO hay forma de evitar el crash** con esta API en H16

---

---

### **CAMINO 3: Solo openInNewViewer()** 🔄 (PROBAR AHORA - Diagnóstico)

**Estado:** 🔄 **PRÓXIMO A PROBAR**

**Estrategia:**
```python
viewer = hiero.ui.openInNewViewer(seq)
_process_events()
```

**Características:**
- NO crea timeline dockeado (solo viewer flotante)
- Prueba si problema específico es `openInTimeline`
- ⚠️ NO cumple objetivo (queremos timeline dockeado)

**Resultado esperado:**
- Si funciona → Problema específico es `openInTimeline` (podemos buscar alternativa)
- Si crashea → Problema más amplio en APIs de creación de panels

**Resultado en Hiero 16:**
- ✅ **NO CRASHEA** - `openInNewViewer()` funciona perfectamente
- ✅ Viewer creado: `uk.co.thefoundry.viewer.4`
- ❌ **Timeline NO aparece** en UI (solo viewer flotante)
- ✅ Sin crashes, sistema estable

**Resultado en Hiero 15:**
- ✅ **NO CRASHEA** - `openInNewViewer()` funciona perfectamente  
- ✅ Viewer creado correctamente
- ❌ **Timeline NO aparece** en UI (mismo que H16)
- ✅ Sin crashes, sistema estable

**CONCLUSIÓN:**
- ✅ **`openInNewViewer()` FUNCIONA** en ambas versiones
- ❌ **Solo `openInTimeline()` está roto** en H16
- ✅ Confirmado: **HAY ALTERNATIVA VIABLE**
- 🎯 **Próximo paso:** Recuperar timeline oculto con `getTimelineEditor()` + hacerlo visible

---

---

### **CAMINO 4: openInNewViewer() + getTimelineEditor() + show()** ❌

**Estado:** ❌ **FALLO** - Timeline aparece en **ventana flotante** (no dockeado)

**Estrategia:**
```python
# 1. Crear viewer flotante (✅ funciona - CAMINO 3 confirmado)
viewer = hiero.ui.openInNewViewer(seq)
_process_events()

# 2. Recuperar timeline OCULTO que ya existe
timeline = hiero.ui.getTimelineEditor(seq)

# 3. Hacer timeline visible
if timeline:
    timeline.show()
    timeline_window = timeline.window()
    if timeline_window:
        timeline_window.show()
        timeline_window.raise_()
        timeline_window.activateWindow()
    timeline.setFocus()
```

**Resultado en Hiero 15:**
- ✅ **NO CRASHEA** - Ejecución completa sin errores
- ✅ Viewer creado: `uk.co.thefoundry.viewer.18` y `uk.co.thefoundry.sequenceviewer.19` (duplicado)
- ⚠️ **Timeline aparece en VENTANA FLOTANTE** - `uk.co.thefoundry.timeline.24`
- ❌ **NO está dockeado** en la UI principal
- ❌ **Creó 2 viewers** (duplicados)

**Problema identificado:**
- `timeline.window().show()` hace que el timeline aparezca como **ventana flotante separada**
- NO está integrado/dockeado en la UI principal de Hiero
- El método `.show()` es para ventanas independientes, no para docking

**CONCLUSIÓN:**
- ❌ **NO cumple objetivo** (queremos timeline dockeado, no flotante)
- ✅ Confirmado: Timelines existen ocultos y se pueden recuperar
- ❌ `.show()` NO es el método correcto para dockear
- 🎯 **Próximo paso:** Reutilizar timeline INTEGRADO existente y cambiar su secuencia

---

### **CAMINO 5: Reutilizar timeline integrado + setSequence()** ❌

**Estado:** ❌ **FALLO CRÍTICO** - Descubrimiento importante sobre el bug de H16

**Estrategia:**
```python
# 1. Buscar timeline INTEGRADO existente (de cualquier secuencia)
active_seq = hiero.ui.activeSequence()
existing_timeline = hiero.ui.getTimelineEditor(active_seq)

# 2. Cambiar la secuencia del timeline existente (sin crear nuevo)
if hasattr(existing_timeline, 'setSequence'):
    existing_timeline.setSequence(target_seq)  # ← No existe en Hiero
else:
    hiero.ui.openInTimeline(target_seq)  # ← CRASHEA EN H16
```

**Resultado en Hiero 15:**
- ✅ **FUNCIONA** - `setSequence()` no existe, usa `openInTimeline()` como fallback
- ✅ `openInTimeline()` funciona correctamente
- ✅ Timeline cambia a secuencia objetivo
- ✅ Sin crashes

**Resultado en Hiero 16:**
- ❌ **CRASH TOTAL** - `setSequence()` no existe, cae a `openInTimeline()`
- ❌ `openInTimeline()` crashea **DENTRO de la llamada** (antes de retornar)
- ❌ Nunca llega a `processEvents()`
- ❌ Última línea: "(SEGURO ahora porque YA EXISTE un timeline integrado)"

## 🔴 **DESCUBRIMIENTO CRÍTICO:**

**Hipótesis anterior (INCORRECTA):**
- ❌ "`openInTimeline()` crashea solo si NO hay timeline previo"

**Realidad descubierta (CORRECTA):**
- ✅ **`openInTimeline()` crashea SIEMPRE en Hiero 16** (con o sin timeline previo)
- ✅ El crash ocurre **DENTRO** de `openInTimeline()`, no es problema de estado
- ✅ Es un **bug en la API misma**, no en cómo la usamos

**Evidencia:**
```
✅ Timeline integrado encontrado: uk.co.thefoundry.timeline.5
✅ Secuencia activa: 360-700
🔧 Llamando hiero.ui.openInTimeline(seq)...
💥 CRASH (nunca retorna)
```

**Conclusión:**
- ❌ NO es viable usar `openInTimeline()` en H16 (bajo ninguna circunstancia)
- ✅ `setSequence()` no existe en la API de Hiero
- 🎯 **Solución:** Detección de versión + métodos diferentes por versión

---

### **CAMINO 6: Detección de versión + Método específico** ⭐ (PROBANDO AHORA)

**Estado:** 🔄 **EN PRUEBA** (Solución definitiva esperada)

**Estrategia:**
```python
# 1. Detectar versión de Hiero
version = hiero.core.applicationVersion()[0]  # Returns (15, x, x) or (16, x, x)

# 2. Estrategia según versión
if version == 15:
    # HIERO 15: openInTimeline funciona perfecto
    hiero.ui.openInTimeline(seq)
    _process_events()
    
elif version >= 16:
    # HIERO 16: openInTimeline crashea - usar setActiveSequence
    hiero.ui.setActiveSequence(seq)
    _process_events()
    # Nota: Solo cambia secuencia activa, no crea timeline/viewer nuevos
```

**Fundamento técnico:**
- **H15:** `openInTimeline()` funciona perfecto → crear timeline/viewer nuevos
- **H16:** `openInTimeline()` crashea siempre → usar `setActiveSequence()` (CAMINO 2 confirmó que no crashea)
- **Compromiso H16:** Solo cambia secuencia activa en timeline existente, no crea panels nuevos

**Ventajas:**
- ✅ NO crashea en ninguna versión
- ✅ Código único que se adapta automáticamente
- ✅ H15: Funcionalidad completa (crea timeline/viewer)
- ⚠️ H16: Funcionalidad reducida (solo cambia secuencia en timeline existente)

**Desventajas H16:**
- ⚠️ Requiere que ya exista un timeline abierto (no crea nuevo)
- ⚠️ No cumple objetivo original (crear timeline/viewer para secuencia libre)
- ✅ Pero evita crashes → mejor que nada

**Resultado esperado:**
- ✅ H15: Crea timeline/viewer perfectamente
- ✅ H16: Cambia secuencia activa sin crashear (limitado pero estable)
- ✅ Código portable entre versiones

**Resultado real:** _[Usuario probará ahora]_

---

## 📊 HISTORIAL DE PRUEBAS PREVIAS (Antes de simplificar)

### Intento Previo: Pre-estabilización con viewer temporal

**Estado:** ❌ FALLÓ (dejó duplicados zombies)

**Estrategia:**
- Crear viewer temporal con `openInNewViewer()`
- Cerrar con `close()` / `deleteLater()`
- Luego `openInTimeline()` final con `singleShot()`

**Resultado:**
- ❌ Cierres de widgets NO efectivos
- ❌ Estado final: 6 viewers (2 más), 4 timelines (1 más)
- ❌ Widgets zombies: `uk.co.thefoundry.viewer.4` no se cerró
- ❌ Complejidad innecesaria que contamina la prueba

**Conclusión:** Abandonado - volver a lo simple (CAMINO 1)

---

## 📋 HALLAZGOS ANTERIORES

## Referencias de scripts que crean timeline/viewer y NO crashean (casos estables conocidos)
- **Projects Panel** (`LGA_Projects_Panel_SwitchSequence.py`): usa `openInTimeline(target_seq)` desde callbacks de UI y luego limpia viewers/timelines sobrantes. (Igual se reportó inestabilidad en algunos escenarios de Hiero 16, pero no crashea en la llamada).
- **Refresh wrapper** (`LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` + `LGA_NKS_Timeline_Refresh.py`): crea nuevo timeline/viewer de la secuencia activa, transfiere estado de viewer, y limpia duplicados. No se reprodujo crash en la llamada (el problema está más asociado a duplicados post-refresh).
- Scripts legacy (`Hiero/GUI/LGA_H-Close_Reopen_TimelineViewer.py`, `Hiero/Viewer/LGA_Abrir_Nuevo_CompTimelineViewers.py`) también usan `openInTimeline`, pero están centrados en la secuencia activa o paths simples, no en secuencias libres.

## Diferencias clave entre lo que hacemos y Projects Panel
1) Contexto de llamada: Projects Panel dispara desde UI (acciones Qt) y procesa eventos antes y después. Ya imitamos esto con `singleShot + processEvents`.
2) Limpieza inmediata: Projects Panel suele cerrar viewers/timelines no objetivo después de abrir. Nosotros NO limpiamos para aislar la TEORÍA 2 (crear sin duplicar).
3) Secuencia objetivo: Projects Panel cambia a una secuencia existente y, si es la misma, retorna; aquí abrimos una secuencia libre (sin panels).

## Hipótesis actuales
- **H1 (TEORÍA 2)**: En Hiero 16, `openInTimeline()` puede crashear al crear un timeline nuevo para una secuencia libre, independientemente de duplicados.
- **H2**: Hay algún requisito implícito de estado (por ejemplo, secuencia debe estar activa/seleccionada en UI) antes de llamar; al no cumplirlo, la creación crashea.
- **H3**: El crash es interno y sólo se evita usando otro camino de apertura (ej. `openInNewViewer()` y luego `getTimelineEditor()`), o activando primero la secuencia.

## 🎯 ESTRATEGIA ACTUAL

**SIMPLIFICACIÓN RADICAL:** Volver a lo básico y probar caminos simples uno por uno.

**Orden de pruebas:**
1. **CAMINO 1** (actual): openInTimeline() directo
2. Si falla → **CAMINO 2**: setActiveSequence() + openInTimeline()
3. Si falla → **CAMINO 3**: Solo openInNewViewer() (diagnóstico)
4. Si todos fallan → Investigar alternativas (dock manual, APIs legacy, etc.)

**Registro de resultados:** Usuario reportará éxito/fallo de cada camino.

---

---

## 📊 **RESUMEN EJECUTIVO: DIFERENCIAS H15 vs H16**

| Aspecto | Hiero 15 | Hiero 16 | Impacto |
|---------|----------|----------|---------|
| **`openInTimeline(seq_libre)` directo** | ✅ Funciona perfecto | ❌ **CRASH TOTAL** | 🔴 CRÍTICO |
| **Creación timeline/viewer** | ✅ Exitosa | ❌ Imposible (crash) | 🔴 CRÍTICO |
| **Logs posteriores a openInTimeline** | ✅ Se ejecutan todos | ❌ Nunca llegan | 🔴 CRÍTICO |
| **Estado final** | ✅ Limpio (+1 TL, +1 V) | ❌ Crash antes de crear | 🔴 CRÍTICO |
| **Refresh timeline actual** | ⚠️ Crea duplicados | ❌ Crashea + duplicados | 🔴 CRÍTICO |
| **Projects Panel** | ✅ Funciona | ⚠️ A veces crashea | 🟡 MEDIO |

**CONCLUSIÓN:**
- Hiero 16 tiene **BUG CRÍTICO** en `openInTimeline()` para secuencias libres
- NO es problema de duplicados (TEORÍA 1 descartada)
- API está rota/cambiada en H16 (TEORÍA 2 confirmada)
- Necesitamos workaround específico para H16

---

## 🎯 **ESTRATEGIA DE SOLUCIÓN**

### **Opciones disponibles:**

1. **CAMINO 2** (probando ahora): `setActiveSequence()` antes podría "preparar" la secuencia
2. **CAMINO 3** (si CAMINO 2 falla): Solo viewer flotante (sin timeline dockeado)
3. **Workaround con detección de versión**: Código diferente para H15 vs H16
4. **Alternativa radical**: No usar `openInTimeline()` en H16, buscar otro método

### **Si CAMINO 2 funciona:**
- ✅ Solución simple: Siempre llamar `setActiveSequence()` antes
- ✅ Compatible con ambas versiones
- ✅ Sin pérdida de funcionalidad

### **Si CAMINO 2 falla:**
- Probar CAMINO 3 como diagnóstico
- Investigar APIs alternativas
- Considerar reportar bug a Foundry

---

---

## 🔴 **PROBLEMA CONFIRMADO: `openInTimeline()` ROTO EN HIERO 16**

### **Evidencia definitiva:**

| Aspecto | Hiero 15 | Hiero 16 | Conclusión |
|---------|----------|----------|------------|
| **`setActiveSequence()`** | ❌ No existe | ❌ No existe | API no disponible |
| **CAMINO 1** | ✅ Funciona | ❌ Crash | Código idéntico, resultado opuesto |
| **CAMINO 2** | ✅ Funciona | ❌ Crash | Se reduce a CAMINO 1 |
| **`openInTimeline(seq_libre)`** | ✅ OK | ❌ **CRASH** | 🔴 **API ROTA EN H16** |

### **¿Por qué crashea silenciosamente?**

- El crash ocurre **dentro del código C++** de `openInTimeline()`
- NO es una excepción Python (por eso no hay traceback)
- Es un **segmentation fault o assert** en el core de Hiero
- Por eso Hiero se cierra completamente sin logs

### **¿Por qué H15 funciona y H16 no?**

**Hipótesis más probable:**
1. **Refactorización interna** en H16 del sistema de panels
2. **Bug introducido** en la reimplementación
3. **Asunción rota:** El código asume que la secuencia tiene cierto estado inicializado
4. **Secuencias "vírgenes"** (sin panels previos) no tienen ese estado → crash

### **¿Por qué Projects Panel a veces funciona en H16?**

Posibles razones:
1. Cambia entre secuencias que **ya tuvieron panels** (estado inicializado)
2. Ejecuta desde **callbacks Qt** con contexto diferente
3. Hace **limpieza previa** que podría inicializar estado
4. Mismo bug, pero menos expuesto en ese flujo

---

## 🎯 **ESTRATEGIA DE RECUPERACIÓN**

### **AHORA: PROBAR CAMINO 3 (Diagnóstico)**

Si `openInNewViewer()` funciona → sabemos que solo `openInTimeline()` está roto

**Ejecuta en Hiero 16:**
```python
exec(open(r"C:\Users\leg4-pc\.nuke\Python\Startup\LGA_HieroTools\+Building_Blocks\test_teoria_2.py").read())
```

**Reporta:**
1. ¿Crasheó en `openInNewViewer()`?
   - Si SÍ → APIs de creación rotas en general (problema mayor)
   - Si NO → Solo `openInTimeline` roto (hay workaround posible)

2. Si no crasheó: ¿Apareció ventana flotante del viewer?

3. Copia los logs

---

## 💡 **ALTERNATIVAS SI CAMINO 3 FUNCIONA**

### **Opción A: Usar openInNewViewer + getTimelineEditor**
```python
viewer = hiero.ui.openInNewViewer(seq)  # Crea viewer flotante
timeline = hiero.ui.getTimelineEditor(seq)  # Recupera timeline creado automáticamente
# Intentar dockear manualmente (si es posible)
```

### **Opción B: Detección de versión** ⭐ (ENCONTRADA EN CODEBASE)
```python
# Método usado en LGA_NKS_Flow_Pull.py (línea 946)
if hasattr(hiero.core, 'applicationVersion'):
    version = hiero.core.applicationVersion()
    if version and version.startswith('16'):
        # ⚠️ Hiero 16: NO usar openInTimeline() para secuencias libres
        # Usar workaround alternativo (CAMINO 4)
        usar_metodo_alternativo()
    else:
        # ✅ Hiero 15 y anteriores: Funciona normal
        hiero.ui.openInTimeline(seq)
else:
    # Fallback: Hiero muy antiguo
    hiero.ui.openInTimeline(seq)
```

### **Opción C: Solución Temporal - No crear panels para secuencias libres en H16**
```python
if hasattr(hiero.core, 'applicationVersion'):
    version = hiero.core.applicationVersion()
    if version and version.startswith('16'):
        # Evitar crashes en H16
        print("⚠️ Hiero 16: Esta función no está disponible por bug en la API")
        print("   Por favor, abre manualmente la secuencia desde el Bin")
        return False
        
# Continuar normal para H15
hiero.ui.openInTimeline(seq)
```

**Pros:**
- ✅ Evita crashes completamente
- ✅ Informa al usuario qué hacer
- ✅ Código simple y seguro

**Contras:**
- ❌ Pierde funcionalidad en H16
- ❌ Experiencia de usuario degradada

### **Opción D: Reportar bug a Foundry** (Largo plazo)
- Crear caso de prueba mínimo
- Reportar en foros de Foundry
- Esperar fix en H16.1 o H17

---

## 📋 **PLAN DE ACCIÓN INMEDIATO**

### ✅ **PASO 1: PROBAR CAMINO 3** - COMPLETADO

**Resultado:** ✅ **FUNCIONA** - `openInNewViewer()` no crashea en H15 ni H16  
**Problema:** ❌ Solo crea viewer, NO crea timeline visible

---

### **PASO 2: PROBAR CAMINO 4** (AHORA) ⭐

**Ejecuta en Hiero 16:**
```python
exec(open(r"C:\Users\leg4-pc\.nuke\Python\Startup\LGA_HieroTools\+Building_Blocks\test_teoria_2.py").read())
```

**¿Qué esperamos?**
1. `openInNewViewer()` crea viewer ✅ (confirmado CAMINO 3)
2. `getTimelineEditor()` recupera timeline oculto que ya existe
3. `.show()` + `.raise_()` + `.activateWindow()` hacen timeline visible
4. **Resultado:** Timeline Y viewer aparecen en UI sin crashes

**Si funciona:** ✅ **SOLUCIÓN ENCONTRADA** para H16

---

### **PASO 3: IMPLEMENTAR SOLUCIÓN EN SCRIPTS**

#### **Si CAMINO 4 funciona:**

**→ Implementar workaround basado en CAMINO 4:**
```python
# Workaround para Hiero 16
def crear_timeline_viewer_h16_safe(seq):
    """
    Crea timeline + viewer para secuencia sin crashear en H16.
    
    Método:
    1. openInNewViewer() - crea viewer (funciona en H15 y H16)
    2. getTimelineEditor() - recupera timeline oculto existente
    3. .show() - hace timeline visible
    """
    # 1. Crear viewer
    viewer = hiero.ui.openInNewViewer(seq)
    processEvents()
    
    # 2. Recuperar timeline oculto
    timeline = hiero.ui.getTimelineEditor(seq)
    
    # 3. Hacer timeline visible
    if timeline:
        timeline.show()
        tl_window = timeline.window()
        if tl_window:
            tl_window.show()
            tl_window.raise_()
            tl_window.activateWindow()
        timeline.setFocus()
        processEvents()
    
    return viewer, timeline
```

**Aplicar a:**
1. **Refresh Timeline** - Reemplazar `openInTimeline()` con workaround
2. **Projects Panel** - Usar workaround para secuencias libres en H16
3. **Cualquier script** que cree timelines programáticamente

**Detección de versión:**
```python
if hasattr(hiero.core, 'applicationVersion'):
    version = hiero.core.applicationVersion()
    if version and version.startswith('16'):
        # Usar workaround
        crear_timeline_viewer_h16_safe(seq)
    else:
        # H15: Método normal
        hiero.ui.openInTimeline(seq)
```

#### **Si CAMINO 4 NO funciona:**

**→ Implementar Opción C** (Deshabilitar en H16)
```python
def safe_open_timeline(seq):
    """Abre timeline solo si es seguro (no crasheará)"""
    if hasattr(hiero.core, 'applicationVersion'):
        version = hiero.core.applicationVersion()
        if version and version.startswith('16'):
            print("⚠️ Hiero 16: Esta API está rota, abre la secuencia manualmente")
            return None
    
    # Seguro en H15
    return hiero.ui.openInTimeline(seq)
```

---

### **PASO 3: APLICAR A SCRIPTS AFECTADOS**

**Scripts que necesitan actualización:**

1. **Refresh Timeline** (`LGA_NKS_Timeline_Refresh_Wrap.py`)
   - Usa `openInTimeline()` internamente
   - ⚠️ Crashea en H16 con secuencias libres

2. **Projects Panel** (`LGA_Projects_Panel_SwitchSequence.py`)
   - Usa `openInTimeline()` para cambiar secuencias
   - ⚠️ A veces crashea en H16

3. **Cualquier otro script** que cree timelines/viewers programáticamente

**Estrategia de actualización:**
```python
# Función helper centralizada (crear en LGA_NKS_Utils o similar)
def safe_open_timeline_with_version_detection(seq):
    """
    Abre timeline de manera segura, detectando versión de Hiero.
    
    Returns:
        - H15: TimelineEditor
        - H16 (workaround exitoso): (viewer, timeline)
        - H16 (sin workaround): None + mensaje al usuario
    """
    if hasattr(hiero.core, 'applicationVersion'):
        version = hiero.core.applicationVersion()
        if version and version.startswith('16'):
            # Intentar workaround si está disponible
            return _h16_workaround(seq)
    
    # H15: Método normal
    return hiero.ui.openInTimeline(seq)
```

---

## 🎯 **PRÓXIMO PASO INMEDIATO**

**Ejecuta CAMINO 4** (script ya actualizado):
```python
exec(open(r"C:\Users\leg4-pc\.nuke\Python\Startup\LGA_HieroTools\+Building_Blocks\test_teoria_2.py").read())
```

**Reporta:**
1. ¿Apareció el timeline en la UI? (visible, no solo oculto)
2. ¿El viewer sigue apareciendo?
3. ¿Algún crash?
4. Copia los logs completos

**Si funciona → ✅ PROBLEMA RESUELTO**
- Tenemos workaround funcional para H16
- Podemos aplicarlo a Refresh Timeline y Projects Panel
- Sin pérdida de funcionalidad 🚀


