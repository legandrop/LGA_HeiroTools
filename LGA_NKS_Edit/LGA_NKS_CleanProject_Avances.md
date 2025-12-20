# Proyecto Purge - Limpieza Segura de Clips en Hiero

## 🎯 **OBJETIVO PRINCIPAL**
Crear un sistema seguro para eliminar clips no utilizados en proyectos de Hiero/Nuke sin romper la integridad del proyecto.

## 📜 **HISTORIA DEL PROYECTO**

### **Problema Inicial**
- Existía un script oficial llamado "Remove Unused Clips" que funcionaba bien
- Pero al actualizar a Nuke 15/Hiero más nuevo, el script dejó de funcionar
- Los usuarios reportaban que clips se rompían al intentar limpiarlos

### **Intento de Solución Inicial**
- Se intentó actualizar el script original para PySide2/Nuke 15
- Se agregaron validaciones de seguridad
- **PROBLEMA:** Seguía rompiendo clips al eliminarlos

## 🎯 **SCRIPT PRINCIPAL OBJETIVO**

### **`purge.py` - Script Oficial de Limpieza General**
**Propósito:** Limpiar TODOS los clips no utilizados del proyecto de manera segura
**Estado Actual:** ❌ **SIN IMPLEMENTAR** - versión antigua rota
**Problema:** La versión original eliminaba BinItems completos rompiendo clips
**Objetivo:** Reescribir completamente usando las lecciones aprendidas

---

## 🔬 **SCRIPTS DE DESARROLLO/EXPLORACIÓN**

### **1. `explore_versions.py` - Explorador Inicial**
**Propósito:** Entender la estructura básica de clips en el proyecto
**Estado:** ✅ Completado
**Descubrimientos:**
- Encontró 19 clips individuales con patrón `PHLDA_013_050_Chroma_AutoDia_comp_`
- Mostró que algunos clips están ONLINE, otros OFFLINE
- Reveló que algunos clips se usan en secuencias, otros no

### **2. `explore_versions_and_clean.py` - Script de Desarrollo Dinámico**
**Propósito:** Herramienta de desarrollo para limpiar clips específicos
**Estado:** ✅ Completado y probado
**Funciones:**
- ✅ Sistema dinámico: cambiar `TARGET_CLIP_NAME` para procesar cualquier clip
- ✅ Eliminación segura de versiones offline
- ✅ Funciona con .exr, .mov y cualquier formato
- ✅ API nativa de Hiero funcionando perfectamente
- **NOTA:** Script de desarrollo, NO el script principal de producción

### **3. `simple_file_check.py` - Verificador de Diagnóstico**
**Propósito:** Herramienta de debugging para verificar estado de versiones
**Estado:** ✅ Completado
**Funciones:**
- ✅ Lista todos los BinItems del proyecto
- ✅ Verifica estado online/offline de versiones
- ✅ Ayuda a identificar problemas de configuración
- **NOTA:** Herramienta de diagnóstico, NO para limpieza

## 🚀 **SISTEMA FINAL IMPLEMENTADO**

### **Scripts de Producción Funcionando:**

#### **1. `explore_versions_and_clean.py` - Script de Limpieza Dinámica**
**Propósito:** Eliminación automática y segura de versiones offline
**Características:**
- ✅ **Sistema dinámico:** Una sola variable `TARGET_CLIP_NAME` para cambiar entre clips
- ✅ **Detección automática:** Funciona con cualquier tipo de archivo (.exr, .mov, etc.)
- ✅ **Eliminación segura:** Solo versiones offline, no activas, no usadas en secuencias
- ✅ **Verificación nativa:** Usa API de Hiero `version.item().mediaSource().isMediaPresent()`
- ✅ **Reportes detallados:** Muestra qué se elimina y qué se conserva

#### **2. `simple_file_check.py` - Verificador de Estado**
**Propósito:** Diagnóstico rápido del estado online/offline de versiones
**Características:**
- ✅ **Vista completa del proyecto:** Lista todos los BinItems disponibles
- ✅ **Detección precisa:** Mismo algoritmo que el script de limpieza
- ✅ **Debugging tool:** Ayuda a identificar BinItems correctos cuando hay problemas

### **Uso del Sistema Dinámico:**

```python
# Para cambiar de clip, solo modifica esta línea:
TARGET_CLIP_NAME = "PHLDA_013_030_Chroma_AutoDia_comp"  # Cambia esto
```

**Ejemplos probados:**
- ✅ `PHLDA_013_030_Chroma_AutoDia_comp` (17 versiones, eliminó 15 offline)
- ✅ `PHLDA_013_050_Chroma_AutoDia_comp` (17 versiones, eliminó 13 offline)
- ⚠️ `PHLDA_013_050_Chroma_AutoDia_EditRef` (.mov con 1 versión offline)

## 🔍 **DESCUBRIMIENTOS CLAVE**

### **Estructura de Versiones en Hiero**
1. **NO son clips separados:** Las versiones están contenidas dentro de BinItems
2. **BinItem principal:** `PHLDA_013_050_Chroma_AutoDia_comp` contiene 17 versiones
3. **Versión activa:** `v22` - la que se usa en secuencias
4. **Acceso a versiones:** Se usa `bin_item.items()` no `bin_item.versions()`

### **Por Qué se Rompían los Clips**
1. **Eliminación incorrecta:** Estábamos eliminando BinItems completos (`bin.removeItem(binItem)`)
2. **Pérdida de versiones:** Al eliminar el contenedor, se perdían TODAS las versiones
3. **Referencias rotas:** Los clips en secuencias perdían su fuente

### **Método Correcto**
- **Eliminar versiones individuales:** `binItem.removeVersion(version)`
- **Conservar el BinItem:** Mantener el contenedor intacto
- **Solo versiones offline:** Que no se usen y no tengan archivos

### **Problema Actual**
- ✅ Estructura de versiones: ENTENDIDA
- ✅ Método de eliminación: IDENTIFICADO
- ❌ Verificación de archivos: NO FUNCIONA para versiones dentro de BinItems
- ❌ Detección offline/online: FALLANDO

## 🛠️ **MÉTODOS DE ELIMINACIÓN**

### **❌ Método Incorrecto (causaba problemas)**
```python
# Eliminaba TODO el BinItem - ROMPE TODO
bin.removeItem(binItem)
```

### **✅ Método Correcto (seguro)**
```python
# Elimina solo la versión específica - CONSERVA EL RESTO
binItem.removeVersion(version)
```

## 📋 **CRITERIOS PARA ELIMINACIÓN SEGURA**

Una versión puede eliminarse si cumple TODOS estos criterios:
- ✅ **Offline:** Los archivos NO existen en disco
- ✅ **No usada:** NO aparece en ninguna secuencia
- ✅ **No activa:** NO es la versión activa del BinItem
- ✅ **Método seguro:** Usar `removeVersion()` no `removeItem()`

## 🎯 **ESTADO ACTUAL**

### **✅ LOGRADO:**
- ✅ Entendida completamente la estructura de versiones en Hiero
- ✅ Identificado el método correcto de eliminación (`removeVersion()` vs `removeItem()`)
- ✅ API nativa de Hiero funcionando perfectamente
- ✅ Lógica de detección online/offline probada y validada
- ✅ Validaciones de seguridad implementadas y probadas

### **🔄 SCRIPTS DE DESARROLLO COMPLETADOS:**
- ✅ `explore_versions.py` - exploración inicial
- ✅ `simple_file_check.py` - diagnóstico de versiones
- ✅ `explore_versions_and_clean.py` - limpieza de clips específicos

### **❌ PENDIENTE - SCRIPT PRINCIPAL:**
- ❌ `purge.py` - Script oficial de limpieza general AÚN SIN IMPLEMENTAR

### **🔍 INVESTIGACIÓN RESUELTA:**

## 🚨 **DESCUBRIMIENTO CRUCIAL: ACCESO CORRECTO A LA API DE HIERO**

**✅ YA SABEMOS CÓMO ACCEDER A LA INFORMACIÓN NATIVA DE HIERO**

Las versiones dentro de BinItems **SÍ TIENEN ACCESO a la información de mediaSource**, pero a través del método correcto:

```python
# ✅ ACCESO CORRECTO A LA API NATIVA DE HIERO
clip_item = version.item()  # Obtiene el Clip real de la versión
media_source = clip_item.mediaSource()  # Accede a MediaSource del Clip

if media_source.isMediaPresent():
    # ✅ Archivos ONLINE (usando información nativa de Hiero)
    print("Media present (Hiero API)")
else:
    # ❌ Archivos OFFLINE (usando información nativa de Hiero)
    print("Media not present (Hiero API)")

# Información adicional disponible:
is_offline = media_source.isOffline()  # Confirma estado offline
file_path = media_source.fileinfos()[0].filename()  # Obtiene ruta real
```

**¿Por qué no funcionaba antes?**
- `version.mediaSource()` → ❌ No existe (las versiones no tienen este atributo directamente)
- `version.item().mediaSource()` → ✅ CORRECTO (accede al Clip real que contiene la información)

**Lección aprendida:**
- **Clips en timeline:** `clip.mediaSource().isMediaPresent()`
- **Versiones en BinItems:** `version.item().mediaSource().isMediaPresent()`
- **Ambos usan la API nativa de Hiero**, no verificación manual de archivos

---

## 📝 **LECCIONES APRENDIDAS**

1. **No asumir estructura:** Lo que parece clips separados son versiones dentro de contenedores
2. **Eliminar con cuidado:** `removeItem()` vs `removeVersion()` hace toda la diferencia
3. **Verificar archivos correctamente:** La API de Hiero funciona diferente según el contexto:
   - Clips en timeline: `clip.mediaSource().isMediaPresent()` ✅
   - Versiones en BinItems: verificación directa del sistema de archivos ✅
4. **Testing iterativo:** Crear scripts simples para validar cada paso del proceso

---

## 🔬 **INVESTIGACIÓN Y DESCUBRIMIENTOS DETALLADOS**

### **Problemas Encontrados y Solucionados:**

#### **1. Estructura de Versiones en Hiero**
- **Descubrimiento:** Las versiones NO son clips separados, son objetos dentro de BinItems
- **Acceso correcto:** `bin_item.items()` devuelve lista de versiones
- **Versión activa:** `bin_item.activeVersion()` identifica cuál está activa
- **Eliminación segura:** `bin_item.removeVersion(version)` elimina solo esa versión

#### **2. Detección de Archivos Offline**
- **API de Hiero no disponible:** Versiones dentro de BinItems no tienen acceso a `mediaSource()`
- **Solución definitiva:** Verificación directa del sistema de archivos con `os.path.exists()`
- **Patrón de paths corregido:** `T:/VFX-PHLDA/001-021/{bin_name_sin_comp}/Comp/4_publish/{version_name}/{version_name}_%04d.exr`

#### **3. Eliminación Incorrecta Anterior**
- **Problema:** `bin.removeItem(binItem)` eliminaba TODO el BinItem con todas sus versiones
- **Consecuencia:** Rompía clips completos cuando solo quería eliminar versiones específicas
- **Solución:** Usar `binItem.removeVersion(version)` para eliminación selectiva

### **Scripts Desarrollados y Probados:**

#### **1. `purge.py` - Script Principal Objetivo**
- **Estado:** ❌ **SIN IMPLEMENTAR** - versión antigua rota
- **Problema Actual:** Elimina BinItems completos rompiendo clips
- **Objetivo:** Reescribir completamente aplicando TODA la lógica descubierta
- **Requerimientos:**
  - ✅ Procesar TODOS los clips del proyecto automáticamente
  - ✅ Usar API nativa de Hiero: `version.item().mediaSource().isMediaPresent()`
  - ✅ Eliminar solo versiones offline con `binItem.removeVersion(version)`
  - ✅ Preservar versiones activas y usadas en secuencias
  - ✅ Compatible con cualquier formato (.exr, .mov, etc.)

#### **2. `explore_versions.py` - Explorador Inicial**
- **Estado:** ✅ Completado
- **Propósito:** Entender estructura básica de clips
- **Descubrimiento:** 19 clips individuales, algunos online/offline

#### **3. `explore_versions_and_clean.py` - Herramienta de Desarrollo**
- **Estado:** ✅ Completado y probado
- **Propósito:** Limpiar clips específicos durante desarrollo
- **Características:** Sistema dinámico con `TARGET_CLIP_NAME`

#### **4. `simple_file_check.py` - Herramienta de Diagnóstico**
- **Estado:** ✅ Completado
- **Propósito:** Debugging y verificación de estado de versiones
- **Características:** Lista todos los BinItems y verifica online/offline

### **Resultados de Testing Exitosos:**

#### **Clip 1: PHLDA_013_030_Chroma_AutoDia_comp (.exr)**
- **Versión activa:** `v24`
- **Total versiones:** 19
- **Eliminadas:** 15 versiones offline (v00, v06-v20)
- **Conservadas:** 4 versiones online (v21, v22, v23, v24)
- **Estado:** ✅ **EXITOSO** - Clip intacto, versiones offline eliminadas

#### **Clip 2: PHLDA_013_050_Chroma_AutoDia_comp (.exr)**
- **Versión activa:** `v22`
- **Total versiones:** 17
- **Eliminadas:** 13 versiones offline
- **Conservadas:** 4 versiones online
- **Estado:** ✅ **EXITOSO** - Segundo clip limpiado exitosamente

#### **Clip 3: PHLDA_013_050_Chroma_AutoDia_EditRef (.mov)**
- **Versión activa:** `v01`
- **Total versiones:** 1
- **Estado:** ⚠️ **NO APLICABLE** - Solo 1 versión offline (no hay qué limpiar)
- **Problema:** Archivo real existe como v02, pero Hiero tiene v01

#### **API Nativa de Hiero:**
- ✅ **CONFIRMADO FUNCIONANDO:** `version.item().mediaSource().isMediaPresent()`
- ✅ **Compatible con .exr y .mov:** Mismo método funciona para ambos formatos
- ✅ **Información completa:** Proporciona paths reales, estado offline, etc.

### **ESTADO ACTUAL DEL PROYECTO:**

#### **✅ INVESTIGACIÓN COMPLETADA:**
- ✅ **API nativa de Hiero dominada** - `version.item().mediaSource().isMediaPresent()`
- ✅ **Método de eliminación seguro identificado** - `binItem.removeVersion(version)`
- ✅ **Lógica de detección online/offline probada** - funciona con .exr, .mov y cualquier formato
- ✅ **Validaciones de seguridad implementadas** - no rompe clips ni pierde versiones activas

#### **✅ OBJETIVO 2 COMPLETADO - LIMPIEZA DE VERSIONES OFFLINE:**
- ✅ `explore_versions_and_clean_UNCLIP.py` - herramienta para limpiar un clip específico
- ✅ `explore_versions_and_clean_Todos.py` - herramienta para limpiar TODO el proyecto
- ✅ Lógica probada y validada en producción real
- ✅ Compatible con .exr, .mov, .nk y cualquier formato
- ✅ Validaciones de seguridad: no elimina si todas offline, preserva versión activa

#### **📋 SCRIPTS DE DESARROLLO COMPLETADOS:**
- ✅ `explore_versions_and_clean.py` - herramienta original para limpiar clips específicos
- ✅ `simple_file_check.py` - herramienta de diagnóstico

#### **✅ OBJETIVO 1 COMPLETADO:**
- ✅ `explore_Unused_Clips_and_clean_UNCLIP.py` - Script individual para limpiar clip específico
- ✅ `explore_Unused_Clips_and_clean_TODOS.py` - Script completo para limpiar TODO el proyecto
- ✅ **Problema solucionado:** Implementada lista negra de secuencias conocidas
- ✅ **Verificación robusta:** Excluye secuencias de la eliminación automática

## 🎉 **OBJETIVO 2 COMPLETADO - SISTEMA DE LIMPIEZA DE VERSIONES OFFLINE FUNCIONANDO**

### **✅ LOGROS ALCANZADOS:**

1. **API nativa de Hiero completamente dominada** - `version.item().mediaSource().isMediaPresent()`
2. **Método de eliminación seguro identificado** - `binItem.removeVersion(version)` vs `removeItem()`
3. **Scripts de producción implementados** - `explore_versions_and_clean_UNCLIP.py` y `explore_versions_and_clean_Todos.py`
4. **Compatibilidad total validada** - funciona con .exr, .mov, .nk y cualquier formato
5. **Validaciones de seguridad implementadas** - no elimina si todas offline, preserva versión activa
6. **Lógica probada en producción** - eliminadas cientos de versiones offline en proyectos reales

### **🎯 PRÓXIMO PASO - OBJETIVO 1:**

**Implementar el sistema para eliminar clips completos no utilizados en secuencias**

### **📋 INSTRUCCIONES PARA SCRIPTS DE PRODUCCIÓN:**

#### **Para limpiar un clip específico:**
```python
# Script: explore_versions_and_clean_UNCLIP.py
# 1. Cambiar esta línea:
TARGET_CLIP_NAME = "NOMBRE_DEL_CLIP_A_LIMPIAR"

# 2. Ejecutar el script en Hiero
# 3. Limpia versiones offline de ese clip específico
```

#### **Para limpiar TODO el proyecto:**
```python
# Script: explore_versions_and_clean_Todos.py
# 1. Ejecutar directamente (no requiere configuración)
# 2. Procesa TODOS los clips del proyecto
# 3. Elimina versiones offline donde sea seguro hacerlo
```

#### **Para diagnosticar un clip:**
```python
# Script: simple_file_check.py (herramienta de diagnóstico)
# 1. Cambiar TARGET_CLIP_NAME al clip deseado
# 2. Ejecutar para ver estado online/offline de versiones
```

### **🎯 OBJETIVO FINAL - SCRIPT PRINCIPAL:**

**`purge.py` debe ser reescrito para:**
- ✅ Aplicar la lógica de limpieza a **TODOS** los clips del proyecto
- ✅ Usar la API nativa de Hiero descubierta
- ✅ Implementar eliminación segura con `removeVersion()`
- ✅ Ser compatible con cualquier formato de archivo
- ✅ Reemplazar el script oficial roto

### **⚠️ NOTAS IMPORTANTES SOBRE SEGURIDAD:**
- Los scripts **NUNCA** eliminan la versión activa de un BinItem
- Los scripts **NUNCA** eliminan versiones que se usan en secuencias
- Los scripts **SOLO** eliminan versiones offline que no se usan
- Si un clip tiene solo 1 versión offline, se informa pero no se elimina

## 🛠️ **SOLUCIÓN FINAL PROPUESTA**

### **Script de Eliminación Segura:**
```python
# Para cada BinItem con versiones:
for version in bin_item.items():
    if (not version_is_active(version) and
        not version_is_used_in_sequences(version) and
        not file_exists_for_version(version)):
        bin_item.removeVersion(version)  # ✅ Seguro - no rompe el clip
```

### **Criterios de Seguridad:**
- ❌ **NO eliminar** versión activa (`bin_item.activeVersion()`)
- ❌ **NO eliminar** versiones usadas en secuencias
- ❌ **NO eliminar** versiones con archivos existentes
- ✅ **SÍ eliminar** versiones offline no usadas no activas

### **Estado del Proyecto:**
**🔬 INVESTIGACIÓN COMPLETADA - LISTO PARA IMPLEMENTACIÓN FINAL**

- ✅ **API nativa de Hiero completamente dominada** - detección online/offline precisa
- ✅ **Método de eliminación seguro identificado** - `binItem.removeVersion(version)`
- ✅ **Scripts de desarrollo probados** - herramientas funcionales para clips específicos
- ✅ **Conocimiento completo adquirido** - lógica validada y documentada
- ✅ **Seguridad garantizada** - validaciones evitan romper clips

**Falta implementar `purge.py` - el script oficial de limpieza general.** 🎯

---

## 🎯 **RESUMEN EJECUTIVO - INVESTIGACIÓN COMPLETADA**

### **Problema Original:**
- Script oficial "Remove Unused Clips" dejó de funcionar en Nuke 15/Hiero nuevo
- Los intentos de actualización rompían clips al eliminar versiones

### **Investigación Completada:**
- ✅ **API nativa de Hiero completamente entendida** - `version.item().mediaSource().isMediaPresent()`
- ✅ **Método de eliminación seguro identificado** - `binItem.removeVersion(version)` vs `removeItem()`
- ✅ **Scripts de desarrollo funcionales** - herramientas probadas para clips específicos
- ✅ **Compatibilidad total validada** - funciona con .exr, .mov y cualquier formato

### **Resultados de Testing en Desarrollo:**
- **Clip 1:** 19 versiones → 4 conservadas (eliminadas 15 offline) ✅
- **Clip 2:** 17 versiones → 4 conservadas (eliminadas 13 offline) ✅
- **Estado:** ✅ **LÓGICA PROBADA** - clips intactos, almacenamiento liberado

### **Archivos Desarrollados:**
- `explore_versions_and_clean.py` - Herramienta de desarrollo para clips específicos
- `simple_file_check.py` - Herramienta de diagnóstico y debugging
- `PURGE_PROJECT_DOCUMENTATION.md` - Documentación completa del proceso
- `purge.py` - ❌ **PENDIENTE** - Script oficial de limpieza general

### **🎯 PRÓXIMO PASO CRÍTICO:**

## **IMPLEMENTACIÓN FINAL: `purge.py`**

### **Especificaciones del Script Final:**

```python
# Estructura del script purge.py final:

def purge_unused_clips():
    """
    Limpia TODOS los clips no utilizados del proyecto de manera segura.
    Versión corregida del script oficial roto.
    """

    # 1. Obtener todas las secuencias para verificar uso
    sequences = hiero.core.findItems(proj, "Sequences")

    # 2. Procesar TODOS los BinItems del proyecto
    for bin_item in hiero.core.findItems(proj, "BinItems"):

        # 3. Para cada BinItem con versiones
        if hasattr(bin_item, 'items'):
            versions = bin_item.items()

            # 4. Identificar versión activa
            active_version = bin_item.activeVersion()

            # 5. Para cada versión en el BinItem
            for version in versions:

                # 6. Verificar si está usada en secuencias
                used_in_sequences = check_if_used_in_sequences(version, sequences)

                # 7. Verificar si archivos existen (API nativa de Hiero)
                files_exist = version.item().mediaSource().isMediaPresent()

                # 8. Aplicar criterios de eliminación segura
                if (version != active_version and     # No es versión activa
                    not used_in_sequences and         # No se usa en secuencias
                    not files_exist):                 # Archivos no existen

                    # ✅ ELIMINACIÓN SEGURA
                    bin_item.removeVersion(version)
```

### **Scripts de Producción Implementados:**
- ✅ `explore_versions_and_clean_UNCLIP.py` - Limpieza de clip específico
- ✅ `explore_versions_and_clean_Todos.py` - Limpieza de TODO el proyecto
- ✅ **Procesamiento automático** - no requiere configuración manual
- ✅ **Cobertura completa** - procesa todos los clips del proyecto
- ✅ **API nativa de Hiero** - detección online/offline precisa
- ✅ **Eliminación selectiva** - solo `removeVersion()`, nunca `removeItem()`
- ✅ **Validaciones robustas** - preserva versiones activas y offline seguras

## 🎉 **PROYECTO COMPLETADO - AMBOS OBJETIVOS IMPLEMENTADOS**

**OBJETIVO 1 COMPLETADO** ✅ - Sistema de eliminación de clips no utilizados funcionando perfectamente

**OBJETIVO 2 COMPLETADO** ✅ - Sistema de limpieza de versiones offline funcionando perfectamente

### **SCRIPTS DE PRODUCCIÓN DISPONIBLES:**

**Script Principal Integrado:**
- `LGA_NKS_CleanProject.py` - **Script completo v2.0** que ejecuta ambos objetivos automáticamente

**Scripts Individuales - Limpieza de Versiones Offline:**
- `explore_versions_and_clean_UNCLIP.py` - Clip específico
- `explore_versions_and_clean_Todos.py` - Todo el proyecto

**Scripts Individuales - Eliminación de Clips No Utilizados:**
- `explore_Unused_Clips_and_clean_UNCLIP.py` - Clip específico
- `explore_Unused_Clips_and_clean_TODOS.py` - Todo el proyecto

**Proyecto 100% operativo.** 🎯✨