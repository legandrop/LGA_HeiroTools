# TEST CIENTÍFICO - RESULTADOS POR FUNCIÓN

**Fecha:** 5 Enero 2026  
**Metodología:** Probar UNA función a la vez, verificar estabilidad inmediatamente  
**Objetivo:** Identificar EXACTAMENTE qué función causa EXACTAMENTE qué problema

---

## 🔬 PROTOCOLO DE TESTING

### **Para cada test:**
1. ✅ Ejecutar la función bajo prueba
2. ✅ Verificar que NO crashee inmediatamente
3. ✅ Verificar estado de la UI (timeline/viewer creados?)
4. ✅ **PRUEBA DE ESTABILIDAD:** Borrar un clip del timeline
5. ✅ Documentar resultado preciso

### **Clasificación de resultados:**
- ✅ **ESTABLE:** Función ejecuta OK, Hiero permanece estable, puedo borrar clips
- ⚠️ **INESTABLE:** Función ejecuta OK, pero Hiero crashea al borrar clips
- ❌ **CRASH:** Hiero crashea inmediatamente al ejecutar la función
- 🔵 **PARCIAL:** Función ejecuta OK, algo se crea, pero no todo

---

## 📊 RESULTADOS - HIERO 16

### **TEST 1: setActiveSequence(seq)**

**Script:** `test_funcion_por_funcion.py` - TEST 1

**Función probada:**
```python
hiero.ui.setActiveSequence(seq)
```

**Resultado:**
- [ ] ✅ ESTABLE
- [ ] ⚠️ INESTABLE
- [x] ❌ CRASH
- [ ] 🔵 PARCIAL

**Observaciones:**
```
❌ ERROR: La función NO EXISTE
AttributeError: module 'hiero.ui' has no attribute 'setActiveSequence'

- NO crasheó Hiero
- Simplemente la función no existe en hiero.ui
- UI no cambió
```

**Conclusión:**
```
La función setActiveSequence() NO EXISTE en hiero.ui.
Era una suposición incorrecta sobre la API de Hiero.
```

---

### **TEST 2: openInTimeline(seq) SIN processEvents()**

**Script:** `test_funcion_por_funcion.py` - TEST 2

**Función probada:**
```python
hiero.ui.openInTimeline(seq)
# NO se llama processEvents() después
```

**Resultado:**
- [ ] ✅ ESTABLE
- [x] ⚠️ INESTABLE
- [ ] ❌ CRASH
- [ ] 🔵 PARCIAL

**Observaciones:**
```
✅ NO crasheó inmediatamente
✅ Creó timeline Y viewer para 010-350
✅ Secuencia activa cambió a 010-350
❌ Timeline/Viewer quedan en ESTADO INESTABLE

Pruebas de estabilidad:
  • Si timeline/viewer ya existían → Crea DUPLICADOS
  • Si cierro duplicado nuevo → Timeline original crashea al borrar clip
  • Si borro clip de timeline creado por este test → Hiero CRASHEA
  • Si borro clip de OTRO timeline → NO crashea
```

**Conclusión:**
```
⚠️⚠️⚠️ FUNCIÓN PROBLEMÁTICA IDENTIFICADA ⚠️⚠️⚠️

openInTimeline() ejecuta correctamente PERO deja el timeline/viewer
creado en un estado CORRUPTO/INESTABLE.

El problema NO requiere processEvents() para manifestarse.
El problema es INHERENTE a openInTimeline() en Hiero 16.
```

---

### **TEST 3: openInTimeline(seq) CON processEvents()**

**Script:** `test_funcion_por_funcion.py` - TEST 3

**Función probada:**
```python
hiero.ui.openInTimeline(seq)
processEvents()  # ← Llamado DESPUÉS
```

**Resultado:**
- [ ] ✅ ESTABLE
- [x] ⚠️ INESTABLE
- [ ] ❌ CRASH
- [ ] 🔵 PARCIAL

**Observaciones:**
```
✅ NO crasheó inmediatamente
✅ Creó timeline Y viewer para 010-350
✅ Secuencia activa cambió a 010-350
❌ Timeline/Viewer quedan en ESTADO INESTABLE

Comportamiento IDÉNTICO a TEST 2.

Pruebas de estabilidad:
  • Borro clip de timeline creado → Hiero CRASHEA
  • Borro clip de otro timeline → NO crashea
```

**Conclusión:**
```
processEvents() NO CAMBIA NADA.

TEST 2 (sin processEvents) = TEST 3 (con processEvents)
Mismo resultado: INESTABILIDAD

Esto confirma que el problema NO es processEvents().
El problema ES openInTimeline() mismo.
```

---

### **TEST 4: openInViewer(seq)**

**Script:** `test_funcion_por_funcion.py` - TEST 4

**Función probada:**
```python
hiero.ui.openInViewer(seq)
```

**Resultado:**
- [ ] ✅ ESTABLE
- [x] ⚠️ INESTABLE
- [ ] ❌ CRASH
- [ ] 🔵 PARCIAL

**Observaciones:**
```
✅ NO crasheó inmediatamente
✅ Creó viewer
✅ Retornó objeto Viewer válido
✅ Secuencia activa cambió a 010-350
❌ Viewer queda en ESTADO INESTABLE

Igual comportamiento que openInTimeline().

Pruebas de estabilidad:
  • Crea timeline Y viewer (no solo viewer)
  • Borro clip → Hiero CRASHEA
```

**Conclusión:**
```
openInViewer() también causa INESTABILIDAD.

No es exclusivo de openInTimeline().
Parece ser un problema sistémico con la creación
de timelines/viewers en Hiero 16.
```

---

### **TEST 5: getTimelineEditor(seq) - Solo obtener**

**Script:** `test_funcion_por_funcion.py` - TEST 5

**Función probada:**
```python
timeline = hiero.ui.getTimelineEditor(seq)
# Solo OBTENER, NO mostrar ni modificar
```

**Resultado:**
- [x] ✅ ESTABLE
- [ ] ⚠️ INESTABLE
- [ ] ❌ CRASH
- [ ] 🔵 PARCIAL

**Observaciones:**
```
✅ NO crasheó inmediatamente
✅ Devolvió objeto TimelineEditor válido
✅ Timeline.sequence() devuelve "010-350" correctamente
✅ NO cambió nada en la UI (timeline sigue oculto)
✅ Hiero permanece ESTABLE

Pruebas de estabilidad:
  • Borro clips de otros timelines → NO crashea
  • Hiero funciona normalmente
  • NO se creó nada visible
```

**Conclusión:**
```
✅ getTimelineEditor() es SEGURO.

Solo OBTENER el timeline (sin mostrarlo) NO causa problemas.
El timeline devuelto existe pero está oculto.

El problema NO es obtener el timeline.
El problema ES cuando se MUESTRA/CREA en la UI.
```

---

## 🎯 ANÁLISIS FINAL

### **Funciones SEGURAS (estables):**
```
✅ hiero.ui.getTimelineEditor(seq)
   - Solo OBTENER el timeline (sin mostrarlo)
   - NO causa inestabilidad
   - Hiero permanece completamente estable
```

### **Funciones PELIGROSAS (inestables):**
```
⚠️ hiero.ui.openInTimeline(seq)
   - Crea timeline/viewer pero quedan INESTABLES
   - Crash al borrar clips del timeline creado
   - Problema NO depende de processEvents()

⚠️ hiero.ui.openInViewer(seq)
   - También causa INESTABILIDAD
   - Mismo comportamiento que openInTimeline()
```

### **Funciones que NO EXISTEN:**
```
❌ hiero.ui.setActiveSequence(seq)
   - Esta función NO existe en la API de Hiero
   - Era una suposición incorrecta
```

### **Función ESPECÍFICA que causa el problema:**
```
╔═══════════════════════════════════════════════════════════════╗
║  FUNCIÓN CULPABLE IDENTIFICADA CON EVIDENCIA CIENTÍFICA      ║
╠═══════════════════════════════════════════════════════════════╣
║  hiero.ui.openInTimeline()                                    ║
║  hiero.ui.openInViewer()                                      ║
║                                                               ║
║  Ambas funciones causan INESTABILIDAD en Hiero 16           ║
║  cuando crean/muestran timelines/viewers.                    ║
║                                                               ║
║  El problema NO es:                                           ║
║    • processEvents() (TEST 2 vs TEST 3 - mismo resultado)   ║
║    • Obtener timeline (TEST 5 - funciona OK)                 ║
║    • Nuestro código                                           ║
║                                                               ║
║  El problema ES:                                              ║
║    • La CREACIÓN/VISUALIZACIÓN de timeline/viewer en UI      ║
║    • Bug SISTÉMICO en Hiero 16                               ║
║    • Afecta TODAS las APIs que crean/muestran timelines      ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🔬 PRUEBAS ADICIONALES (si es necesario)

### **TEST 6: [Descripción]**
```
[Si necesitamos más tests granulares]
```

---

## 📋 CONCLUSIÓN CIENTÍFICA

**Basado en evidencia experimental rigurosa:**

### 1. **Funciones problemáticas identificadas:**
```
• hiero.ui.openInTimeline(seq)  ← CULPABLE PRINCIPAL
• hiero.ui.openInViewer(seq)    ← TAMBIÉN CULPABLE
```

### 2. **Tipo de problema:**
```
[x] Inestabilidad post-ejecución
[x] Corrupción de estado interno de Hiero
[ ] Crash inmediato (NO crashea al ejecutar, crashea después)
```

**Descripción precisa:**
- Funciones ejecutan sin errores Python
- Crean timeline/viewer correctamente
- PERO dejan objetos en estado corrupto
- Operaciones posteriores (borrar clip) causan crash

### 3. **Reproducibilidad:**
```
[x] 100% reproducible en Hiero 16
    - TEST 2, 3, 4 reproducen el problema consistentemente
    - Crash ocurre SIEMPRE al borrar clip del timeline creado
```

### 4. **Workaround posible:**
```
❌ NO EXISTE workaround funcional desde Python.

Opciones exploradas (todas fallaron):
  • openInTimeline() sin processEvents() → INESTABLE (TEST 2)
  • openInTimeline() con processEvents() → INESTABLE (TEST 3)
  • openInViewer() → INESTABLE (TEST 4)
  • getTimelineEditor() + showWindow() → INESTABLE (tests previos)

Única función estable:
  • getTimelineEditor() → ESTABLE (TEST 5)
    PERO solo obtiene timeline oculto, NO lo muestra en UI

Conclusión: NO hay forma de crear/mostrar timeline/viewer
            de forma programática en Hiero 16 sin causar inestabilidad.
```

### 5. **Evidencia para reportar a Foundry:**
```
Script mínimo reproducible:
  import hiero.core
  import hiero.ui
  
  # Obtener cualquier secuencia
  seq = hiero.core.projects()[0].sequences()[0]
  
  # Ejecutar API problemática
  hiero.ui.openInTimeline(seq)
  
  # Resultado: Timeline/viewer creados
  # Problema: Seleccionar clip → presionar DELETE → Hiero CRASHEA

Versiones:
  • Hiero 15.x → Funciona perfectamente
  • Hiero 16.x → Bug reproducible 100%

Logs completos: logs/debugPy.log
```

---

## 📝 NOTAS ADICIONALES

```
[Cualquier observación relevante durante los tests]
```

