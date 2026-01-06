# 🔄 **PROGRESO: Refresh Timeline en Hiero 16**

## 📊 **ESTADO ACTUAL**

**✅ Problema principal identificado**: Los scripts ahora usan APIs directas de Hiero para crear timelines/viewers duplicados sin cerrar los existentes, dejando el sistema en estado inconsistente.

**🔄 Próximo paso**: Ejecutar `test_teoria_2.py` para probar TEORÍA 2 y obtener resultados sobre ambas teorías.

---

## 🎯 **OBJETIVOS**

### **✅ Completado:**
- ✅ Identificar correctamente viewers/timelines abiertos en UI usando `metaObject().className()`
- ✅ Implementar cierre seguro con `deleteLater()` en lugar de `close()`
- ✅ Scripts modificados para trabajar en timeline/viewer nuevo

### **❌ Pendiente:**
- Ejecutar prueba experimental de TEORÍA 2
- Basado en resultados: confirmar cuál teoría explica los crashes en Hiero 16

---

## 🧪 **TEORÍAS SOBRE LA SOLUCIÓN**

### **TEORÍA 1: Los duplicados rompen Hiero**
- **Hipótesis**: Tener múltiples timelines/viewers para la misma secuencia YA rompe estabilidad
- **Evidencia**: Cerrar manualmente duplicados deja sistema roto (crash al borrar clips)
- **Implicación**: Nunca debemos llegar al estado de duplicados

### **TEORÍA 2: El problema son las APIs directas**
- **Hipótesis**: Usar `openInTimeline()` para crear panels rompe Hiero independientemente de duplicados
- **Prueba**: Crear timeline/viewer para secuencia libre (sin duplicar) y verificar estabilidad
- **Resultado esperado**: Si crashea → TEORÍA 2 confirmada, TEORÍA 1 descartada

---

## 🔍 **IDENTIFICACIÓN DE TIMELINES/VIEWERS ABIERTOS**

### **Script principal**: `+Building_Blocks/test_method_1_modified.py`
**Función clave**: `find_timelines_in_main_windows()` - Detecta correctamente timelines abiertos en UI

### **Resultados validados** (última ejecución):
- **6 widgets TimelineEditor encontrados** en aplicación
- **4 candidatos fuertes** (≥2 criterios de apertura): `360-700`, `010-350`, `710-990`
- **2 descartados** (0 criterios): `z_EditRef_v.0.2`, `z_EditRef_v1_6_20250725`
- **Método 6**: 4 timelines en windows principales (resultado más confiable)

### **Criterios de apertura** (widgets TimelineEditor):
1. `isVisible` + `not isHidden`
2. `isActiveWindow`
3. Parent visible + dimensiones > 100x50
4. Widget presente en tabs

---

## 📁 **ARCHIVOS CLAVE**

### **Scripts de identificación**:
- `+Building_Blocks/test_method_1_modified.py` - `find_timelines_in_main_windows()`
- `+Building_Blocks/explore_timeline_identification_SAFE.py` - Lógica completa de mapeo secuencias-panels

### **Script de prueba TEORÍA 2**:
- `+Building_Blocks/test_teoria_2.py` - Crear timeline/viewer para secuencia libre

### **Scripts de cierre seguro**:
- `+Building_Blocks/close_old_viewers_safe.py` - `deleteLater()` para viewers/timelines viejos

### **Scripts refresh modificados**:
- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` - Integración cierre automático
- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh.py` - Retorna info viewer viejo
- `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py` - Acepta `timeline_editor` opcional
- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py` - Acepta `timeline_editor` opcional

---

## 🎯 **SIGUIENTE PASO: EJECUTAR TEORÍA 2**

Comando a ejecutar dentro de Hiero:
```python
python +Building_Blocks/test_teoria_2.py
```

### **¿Qué probar?**
1. Script identifica secuencia libre usando lógica correcta
2. Crea timeline/viewer con `openInTimeline()`
3. Usuario prueba operaciones normales (borrar clips, zoom, etc.)
4. **Si crashea** → TEORÍA 2 confirmada (problema son APIs directas)
5. **Si funciona** → TEORÍA 1 cobra fuerza (problema son duplicados)

### **Resultado esperado**:
- Confirma cuál teoría explica los crashes en Hiero 16
- Define estrategia final para solucionar refresh timeline
