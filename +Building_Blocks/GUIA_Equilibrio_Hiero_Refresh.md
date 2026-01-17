# 🔄 **GUÍA: Equilibrio Delicado de Hiero - Refresh Timeline Seguro**

## 📋 **Índice**
1. [Problema Original](#problema-original)
2. [Descubrimiento del Equilibrio Delicado](#descubrimiento-del-equilibrio-delicado)
3. [Solución Implementada](#solución-implementada)
4. [Métodos Técnicos Utilizados](#métodos-técnicos-utilizados)
5. [Cómo Aplicar a Otros Scripts](#cómo-aplicar-a-otros-scripts)
6. [Casos de Uso](#casos-de-uso)
7. [Verificación y Testing](#verificación-y-testing)

---

## 🐛 **Problema Original**

### **Síntomas:**
- ✅ Refresh timeline funcionaba sin crashes inmediatos
- ❌ Quedaban **timelines duplicados** abiertos
- ❌ Solo se cerraban **viewers viejos**, no timelines
- ❌ Estado inconsistente del sistema Hiero

### **Código Problemático (v1.3):**
```python
# ❌ PROBLEMA: Solo cerraba viewers
find_and_close_old_viewers_safe(old_viewer_object_name=viewer_obj)
# Resultado: Timelines duplicados permanecían abiertos
```

---

## 🔍 **Descubrimiento del Equilibrio Delicado**

### **Investigación Documentada:**

Basado en **`FIX_Problemas_RefreshTimeline_1.md`**, se descubrió que Hiero tiene un **"equilibrio delicado"** entre viewers y timelines:

```
❌ Cerrar SOLO viewers → CRASHEA (estado inconsistente)
❌ Cerrar SOLO timelines → CRASHEA (estado inconsistente)
✅ Cerrar VIEWERS + TIMELINES JUNTOS → SIN CRASHES
```

### **Por Qué Es Importante:**

Hiero mantiene una **sincronización interna** entre viewers y timelines. Si se rompe este equilibrio cerrando solo un tipo de widget, el sistema queda en estado corrupto que causa crashes posteriores.

---

## ✅ **Solución Implementada**

### **Enfoque: Cierre Simultáneo**

```python
# ✅ SOLUCIÓN: Cerrar ambos simultáneamente
find_and_close_old_viewers_and_timelines_safe(
    old_viewer_object_name=viewer_obj,
    old_timeline_object_name=timeline_obj
)
```

### **Resultado:**
- ✅ Sin crashes
- ✅ Sin duplicados
- ✅ Equilibrio mantenido
- ✅ Compatible con Hiero 15/16

---

## 🔧 **Métodos Técnicos Utilizados**

### **1. Identificación de Widgets por Tipo**

#### **Viewers:**
```python
class_name = widget.metaObject().className()
if "Foundry::Storm::UI::Viewer" in class_name:
    # Es un viewer válido
```

#### **Timelines:**
```python
class_name = widget.metaObject().className()
if "TimelineEditor" in class_name:
    # Es un timeline válido
```

#### **Filtros de Exclusión:**
```python
# Excluir Contact Sheet y otros viewers no-secuencia
if 'contactsheet' in obj_name.lower():
    continue
```

### **2. Identificación de Widgets Activos**

#### **Viewer Activo:**
```python
current_viewer = hiero.ui.currentViewer()
current_obj_name = current_viewer.window().objectName()
```

#### **Timeline Activo:**
```python
active_seq = hiero.ui.activeSequence()
current_timeline = hiero.ui.getTimelineEditor(active_seq)
current_timeline_obj = current_timeline.window().objectName()
```

### **3. Cierre Seguro (Compatible con Hiero 16)**

```python
# ✅ deleteLater() - Seguro, diferido
widget.deleteLater()

# ❌ close() - Problemático en H16
# widget.close()  # → CRASHEA
```

### **4. Algoritmo de Cierre Simultáneo**

```python
# PRIMERA PASADA: Identificar qué cerrar
widgets_to_close = []
for widget in all_widgets:
    # Identificar tipo y determinar si debe cerrarse
    # Agregar a lista de widgets a cerrar

# SEGUNDA PASADA: Cerrar simultáneamente
for widget_info in widgets_to_close:
    widget_info['widget'].deleteLater()

# Procesar eventos para que se ejecuten los deleteLater()
QtCore.QCoreApplication.processEvents()
```

---

## 📝 **Cómo Aplicar a Otros Scripts**

### **Patrón General de Implementación:**

```python
def refresh_con_equilibrio():
    # 1. CAPTURAR widgets activos ANTES del refresh
    old_viewer_obj = None
    old_timeline_obj = None

    active_viewer = hiero.ui.currentViewer()
    if active_viewer:
        old_viewer_obj = active_viewer.window().objectName()

    active_seq = hiero.ui.activeSequence()
    if active_seq:
        old_timeline = hiero.ui.getTimelineEditor(active_seq)
        if old_timeline:
            old_timeline_obj = old_timeline.window().objectName()

    # 2. HACER EL REFRESH (crear duplicados)
    # ... código que crea nuevos timeline/viewer ...

    # 3. CERRAR SIMULTÁNEAMENTE los widgets identificados
    from LGA_NKS_Timeline_Refresh_Wrap import find_and_close_old_viewers_and_timelines_safe

    find_and_close_old_viewers_and_timelines_safe(
        old_viewer_object_name=old_viewer_obj,
        old_timeline_object_name=old_timeline_obj
    )
```

### **Scripts que Necesitan Esta Solución:**

1. **`LGA_Projects_Panel_SwitchSequence.py`**
   - Problema: Cambia entre secuencias pero deja duplicados
   - Solución: Aplicar patrón de cierre simultáneo

2. **Cualquier script que use `openInTimeline()`**
   - Problema: Crea nuevos panels sin limpiar viejos
   - Solución: Capturar + cerrar simultáneamente

---

## 🎯 **Casos de Uso**

### **Caso 1: Refresh Timeline (YA IMPLEMENTADO)**
- **Antes:** Solo cerraba viewers → duplicados
- **Después:** Cierra viewers + timelines → limpio

### **Caso 2: Cambio de Secuencia**
- **Problema:** `LGA_Projects_Panel_SwitchSequence.py` crashea en H16
- **Solución:** Aplicar cierre simultáneo después de `openInTimeline()`

### **Caso 3: Scripts Legacy**
- **Problema:** `Hiero/GUI/LGA_H-Close_Reopen_TimelineViewer.py`
- **Solución:** Reemplazar `close()` con `deleteLater()` simultáneo

---

## 🧪 **Verificación y Testing**

### **Script de Prueba:**
```python
# Ejecutar: +Building_Blocks/test_close_viewer_safe.py
# Opción 3: "Cerrar VIEWERS + TIMELINES simultáneamente"
```

### **Verificación Manual:**
1. ✅ Refresh funciona sin crash inmediato
2. ✅ No quedan viewers duplicados
3. ✅ No quedan timelines duplicados
4. ✅ Operaciones normales funcionan (borrar clips, zoom, etc.)

### **Verificación en Hiero 16:**
- ✅ No crashea al cerrar widgets
- ✅ Sistema permanece estable
- ✅ Equilibrio mantenido

---

## 📚 **Referencias**

- **`FIX_Problemas_RefreshTimeline_1.md`** - Descubrimiento del equilibrio delicado
- **`LGA_NKS_Timeline_Refresh_Wrap.py`** - Implementación completa
- **`test_close_viewer_safe.py`** - Script de testing

---

## 🎉 **Resumen Ejecutivo**

**Problema:** Cerrar solo viewers dejaba timelines duplicados y causaba inestabilidad.

**Solución:** Cerrar viewers Y timelines simultáneamente manteniendo el equilibrio delicado de Hiero.

**Resultado:** Refresh limpio, sin duplicados, sin crashes, compatible con Hiero 15/16.

**Aplicabilidad:** Patrón reusable para cualquier script que refresque timelines en Hiero.