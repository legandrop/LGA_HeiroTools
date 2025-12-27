# Panel Projects - Objetivo Actual

## 🎯 Objetivo
Crear un panel integrado en Hiero llamado "Projects" que permita hacer **ReImport inteligente** preservando su estado dockeado usando el método nativo `WindowManager.showWindow()`.

## 📁 Estructura de Scripts

### Panel Principal
**Ubicación:** `LGA_NKS_Projects_Panel.py` (raíz)
- Clase `ProjectsPanel` con botón "ReImport"
- Registrado como `"com.lega.ProjectsPanel"`

### Script Smart Reload
**Ubicación:** `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py`
- Función: `smart_reload_panel()`
- Guarda estado básico (visible, geometry)
- Destruye panel actual con `deleteLater()`
- Crea nuevo panel con `importlib`
- **Usa `wm.showWindow()` para dockear** (método nativo de Hiero)

### Script de Exploración
**Ubicación:** `LGA_Projects_Panel/exploracion/`
- `LGA_Projects_Panel_Exploracion_Reimport.py` - Análisis completo de docking
- `LGA_NKS_Projects_Panel_Simple_Dock.py` - Script de testing simple

## 🔑 Descubrimientos Críticos

### 🎯 Cómo Funciona el Docking en Hiero
- **Panel dockeado:** Está en QStackedWidget, comparte espacio con otros panels
- **Panel cerrado:** Removido completamente de jerarquía, Visible=False, sin parents
- **Para redockear:** NO usar `insertWidget()` (duplica), usar `wm.showWindow()` (método nativo)

### 📊 Ejemplo Real de Docking
```
📋 PANEL DOCKEADO - Comparte espacio con:
  [0] uk.co.thefoundry.project.2: 'Project'
  [1] com.lega.ProjectsPanel: 'Projects' ← CURRENT ← NUESTRO PANEL
```

### ✅ Método Correcto Encontrado
- **`wm.showWindow(panel)`** - Método nativo de Hiero para mostrar panels dockeados
- Retorna `None` pero funciona perfectamente
- Restaura automáticamente la posición dockeada correcta

## 🔄 Funcionamiento ReImport (Versión Final)

1. **Usuario hace click en "ReImport"** → `reimport_panel()`
2. **Se llama script externo** → `LGA_NKS_Projects_Panel_Smart_Reload.py`
3. **Destruye panel actual** → `hide() + setParent(None) + deleteLater()`
4. **Crea nuevo panel** → importa módulo y crea instancia
5. **Dockea automáticamente** → `wm.showWindow(new_panel)` ✨

## ✅ Estado Actual - ¡FUNCIONANDO!
- ✅ Panel básico creado y funcional
- ✅ Smart reload implementado con método nativo
- ✅ Preserva posición dockeada perfectamente
- ✅ Usa `wm.showWindow()` - método correcto de Hiero
- ✅ Testing exitoso - panel se redockea automáticamente

## 🧪 Para Probar
1. Cambiar texto en panel (ej: "Prueba 4" → "Prueba 5")
2. Click "ReImport"
3. Verificar que panel reaparece dockeado en mismo lugar con nuevo texto
4. Debe compartir espacio con panel "Project"

## 🎉 Resultado del Testing
```
🎉 ÉXITO: Panel dockeado correctamente
📋 PANEL DOCKEADO - Comparte espacio con:
  [0] uk.co.thefoundry.project.2: 'Project'
  [1] com.lega.ProjectsPanel: 'Projects' ← CURRENT ← NUESTRO PANEL
```
