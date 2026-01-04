# 🚨 **CRÍTICO: DoScan ES ESENCIAL - BinItem NO ES SOLUCIÓN**

## 🔥 **PROBLEMA PRINCIPAL**

El pull **DEBE usar doScan** porque es el **ÚNICO MÉTODO** que **ESCANEA VERSIONES DESDE EL DISCO**.

**BinItem NO SIRVE** - solo ve versiones ya cargadas en el proyecto.

## 🎯 **REQUISITO ABSOLUTO**

**MISMO RESULTADO en Hiero 15 y 16:**
- ✅ Encontrar TODAS las versiones disponibles
- ✅ Escanear activamente el sistema de archivos
- ✅ Resultados 100% idénticos

**NO ACEPTAMOS WORKAROUNDS** que den resultados diferentes o incompletos.

---

# 🔍 **INVESTIGACIÓN: Arreglar doScan para Hiero 16**

## 🚨 **¿Por qué se cuelga doScan en Hiero 16?**

- **Hiero 15**: PySide2 (Qt5) → doScan funciona
- **Hiero 16**: PySide6 (Qt6) → doScan se cuelga
- **Causa probable**: Incompatibilidad Qt5→Qt6 en threading/event loops

## 🛠️ **Scripts de Investigación**

### 1. `LGA_NKS_Flow_Pull_DoScan.py` - **MÉTODO CORRECTO**
**¿Qué hace?** `VersionScanner.doScan()` con timeout para evitar cuelgues infinitos.

**VENTAJAS CRÍTICAS:**
- ✅ **ESCANEA DESDE DISCO** - encuentra versiones nuevas
- ✅ **RESULTADO COMPLETO** - todas las versiones disponibles
- ✅ **MÉTODO OFICIAL** de Hiero para version scanning

**PROBLEMA ACTUAL:**
- ❌ Se cuelga en Hiero 16 por incompatibilidad PySide2→PySide6

---

### 2. `LGA_NKS_Flow_Pull_BinItem.py` - **NO ES SOLUCIÓN**
**¿Qué hace?** `binItem.items()` directo (sin escanear).

**¿POR QUÉ NO SIRVE?**
- ❌ **NO ESCANEA DISCO** - solo versiones ya cargadas
- ❌ **RESULTADOS INCOMPLETOS** - pierde versiones nuevas
- ❌ **DIFERENTE RESULTADO** - no es equivalente funcional

**SOLO PARA TESTING** - demuestra por qué no podemos usarlo.

---

## 📊 **DIFERENCIA CRÍTICA**

| Requisito | DoScan (CORRECTO) | BinItem (INCORRECTO) |
|-----------|-------------------|---------------------|
| **Escanea disco** | ✅ SÍ | ❌ NO |
| **Encuentra versiones nuevas** | ✅ SÍ | ❌ NO |
| **Mismo resultado H15/H16** | ✅ SÍ (cuando funcione) | ❌ NO |
| **Resultado completo** | ✅ SÍ | ❌ NO |

## 🎯 **OBJETIVO FINAL**

**ARREGLAR doScan para que funcione en Hiero 16** sin cambiar la funcionalidad.

**NO queremos:**
- ❌ Workarounds que den resultados diferentes
- ❌ Soluciones "buenas enough"
- ❌ Cambios que alteren el comportamiento correcto

**SÍ queremos:**
- ✅ doScan funcionando en ambas versiones
- ✅ Mismo resultado exacto
- ✅ Escaneo completo desde disco

## 🔧 **PRÓXIMOS PASOS**

1. **Diagnosticar exactamente** por qué doScan se cuelga en PySide6
2. **Encontrar solución compatible** Qt5/Qt6 para doScan
3. **Implementar fix** que mantenga funcionalidad completa
4. **Verificar** mismo resultado en Hiero 15 y 16

---

# 📋 **COSAS QUE YA PROBAMOS**

## ✅ **Confirmado: Problema NO es threading**

**Resultados de testing:**

1. **doScan con threading + timeout (10s)** → ❌ Se cuelga en Hiero 16
2. **doScan directo sin threading** → ❌ También se cuelga en Hiero 16
3. **BinItem sin doScan** → ✅ Funciona pero resultados incompletos

**Conclusión:** El problema es **inherente a doScan en Hiero 16**, no relacionado con threading.

---

# 🔬 **SIGUIENTES PRUEBAS PARA DIAGNOSTICAR**

## 🎯 **Opciones para simplificar y encontrar el motivo exacto:**

### 1. **Signal-based timeout** (sin threads)
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("doScan timeout")

# Setear alarm de 5 segundos
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)
try:
    vc.doScan(active_version)
    signal.alarm(0)  # Cancelar alarm si terminó
except TimeoutError:
    print("doScan se cuelga después de 5s")
```

### 2. **Multiprocessing en lugar de threading**
```python
from multiprocessing import Process, Queue

def do_scan_process(queue):
    try:
        vc.doScan(active_version)
        queue.put("SUCCESS")
    except Exception as e:
        queue.put(f"ERROR: {e}")

# Ejecutar en proceso separado
process = Process(target=do_scan_process, args=(queue,))
process.start()
process.join(timeout=5.0)
if process.is_alive():
    process.terminate()
    print("doScan se cuelga en proceso separado")
```

### 3. **Probar con diferentes VersionScanner instances**
- Crear múltiples VersionScanner
- Probar con diferentes parámetros
- Verificar si el problema es específico de cierto binItem

### 4. **API Alternatives**
Buscar en documentación de Hiero:
- `binItem.refresh()` o `binItem.rescan()`
- `hiero.core.scanVersions()` u otros métodos
- `project.scanForVersions()` si existe

### 5. **Context testing**
- Probar doScan desde diferentes puntos del código
- Antes/durante/durante el pull
- Con diferentes clips/binItems

### 6. **Minimal test case** ✅ **IMPLEMENTADO**
**Script:** `LGA_NKS_Flow_DoScan_Minimal.py`

**Propósito:** Aislar completamente doScan sin ninguna lógica extra. Solo prueba si `vc.doScan(active_version)` funciona en Hiero 16.

---

# 🎯 **OBJETIVO DE DIAGNÓSTICO**

**Simplificar hasta encontrar:**
- ❌ ¿Es específico del binItem?
- ❌ ¿Es específico de la versión activa?
- ❌ ¿Es problema general de VersionScanner en Hiero 16?
- ❌ ¿Hay alternativa en la API que funcione?

**Meta:** Encontrar exactamente **dónde** y **por qué** se cuelga para poder solucionarlo o encontrar workaround que mantenga funcionalidad completa.

---

# ⚠️ **RECORDATORIO IMPORTANTE**

**BinItem NO es una opción viable.** Es solo para demostrar que doScan es esencial.

**Necesitamos doScan funcionando.** Es el corazón del pull - sin él, los resultados son incorrectos e incompletos.

**El objetivo es ZERO compromiso en funcionalidad.** El pull debe trabajar exactamente igual en ambas versiones.
