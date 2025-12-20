# 🎯 OBJETIVOS DEL SCRIPT LGA_NKS_CleanProject.py

## 📋 **OBJETIVOS PRINCIPALES**

### **1. Limpieza de Clips No Utilizados**
Eliminar automáticamente todos los clips que **NO estén siendo usados en ninguna secuencia**, incluyendo:
- ✅ Clips de cualquier formato (.exr, .mov, .nk, etc.)
- ✅ Clips .nk (composiciones de Nuke) - **detectarlos por separado**
- ✅ Eliminación completa del BinItem (no solo versiones)

### **2. Limpieza de Versiones Offline** ✅ **COMPLETADO**
Eliminar las versiones offline de clips que cumplan estas condiciones:
- ✅ Tengan **múltiples versiones**
- ✅ Tengan **al menos una versión online** disponible
- ❌ **NO eliminar** si todas las versiones están offline
- ✅ Solo eliminar versiones offline no activas

**Scripts implementados:**
- `explore_versions_and_clean_UNCLIP.py` - Para limpiar un clip específico
- `explore_versions_and_clean_Todos.py` - Para limpiar TODO el proyecto

## 🔒 **CRITERIOS DE SEGURIDAD**

### **Para Eliminación de Clips Completos:**
- ❌ **NO eliminar** clips usados en secuencias
- ✅ **SÍ eliminar** clips completamente no utilizados

### **Para Eliminación de Versiones:**
- ❌ **NO eliminar** la versión activa del BinItem
- ❌ **NO eliminar** versiones usadas en secuencias
- ❌ **NO eliminar** versiones con archivos existentes
- ❌ **NO eliminar** si todas las versiones están offline
- ✅ **SÍ eliminar** versiones offline no usadas no activas (cuando hay otras versiones online)

## 🛠️ **IMPLEMENTACIÓN TÉCNICA**

### **Detección de Uso en Secuencias:**
- Verificar si clips aparecen en timelines de secuencias
- Para clips .nk: verificar referencias en composiciones

### **Detección de Estado Online/Offline:**
- Usar API nativa de Hiero: `version.item().mediaSource().isMediaPresent()`
- Compatible con todos los formatos (.exr, .mov, .nk, etc.)

### **Métodos de Eliminación:**
- Clips completos: `bin.removeItem(binItem)` (cuando no se usan)
- Versiones específicas: `binItem.removeVersion(version)` (solo offline no usadas)