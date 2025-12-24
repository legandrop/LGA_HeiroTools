# Plan de migración Nuke 15 → Nuke 16 (PySide2 → PySide6) - Hiero Panels

## Estrategia
- Crear capa de compatibilidad `qt_compat.py` similar a ToolPacks
- Reemplazar imports PySide2 → `qt_compat` en todos los paneles
- Mantener compatibilidad con Nuke 15 mediante try/except
- Actualizar APIs Qt5 deprecadas si es necesario

## Paneles Principales (requieren migración completa)

### Paneles de UI principales
- [x] `LGA_NKS_Color_Panel.py` — Panel de colores de clips (PySide2.QtWidgets, PySide2.QtGui)
- [x] `LGA_NKS_EditTools_Panel.py` — Panel de herramientas de edición (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_Flow_Assignee_Panel.py` — Panel de asignación de usuarios Flow (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_Flow_FlowProd_Panel.py` — Panel de producción Flow (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_Flow_Panel.py` — Panel principal Flow (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_Review_Panel.py` — Panel de revisión (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_ViewerPanel.py` — Panel de viewer (PySide2.QtWidgets, PySide2.QtGui, PySide2.QtCore)
- [x] `LGA_NKS_FlowNo_Panel.py` — Panel Flow alternativo (PySide2.QtWidgets, PySide2.QtGui)

### Archivos adicionales migrados (scripts auxiliares)
- [x] `LGA_NKS_Shortcuts.py` — Atajos de teclado (migrado a qt_compat)
- [x] `z_clear_outpoint_workaround.py` — Workaround para timeline viewer (migrado a qt_compat)
- [x] `z_version_everywhere.py` — Versionado de clips (migrado a qt_compat)

## Scripts de Funcionalidad (requieren migración Qt)

### LGA_NKS/ - Scripts básicos
- [x] `LGA_NKS_CheckProjectVersions.py` — Verificación de versiones (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [x] `LGA_NKS_OpenInNukeX.py` — Abrir en NukeX (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [x] `LGA_NKS_Compare_Versions.py` — Comparar versiones (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)

### LGA_NKS_Edit/ - Scripts de edición
- [ ] `LGA_NKS_Reconnect.py` — Reconexión de media (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [x] `LGA_NKS_SelfReplaceClip.py` — Reemplazo de clips (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_MatchVerToEXR.py` — Matching de versiones (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_CompareVerToEditref.py` — Comparación con EditRef (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_CompareEXR_to_aPlate.py` — Comparación EXR aPlate (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_CreateNewTrack.py` — Creación de tracks (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_mediaMissingFrames.py` — Frames faltantes (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_Trim_In.py` — Recorte IN (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_Trim_Out.py` — Recorte OUT (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_FixColorspaces.py` — Corrección de colorspaces (sin Qt directo)

### LGA_NKS_Flow/ - Scripts de Flow
- [ ] `LGA_NKS_Flow_Pull.py` — Pull de tasks Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QRunnable, QThreadPool)
- [ ] `LGA_NKS_Flow_Push.py` — Push de estados Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_Assign_Assignee.py` — Asignación de usuarios (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_Assignee.py` — Obtener asignados (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QRunnable, QThreadPool)
- [ ] `LGA_NKS_Flow_Clear_Assignees.py` — Limpiar asignados (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_Shot_info.py` — Información de shots (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_ReviewPic.py` — Captura de review (sin Qt directo)
- [ ] `LGA_NKS_Flow_NamingUtils.py` — Utilidades de naming (sin Qt)
- [ ] `LGA_NKS_Flow_CreateShot_Thumbs.py` — Creación de thumbnails (sin Qt directo)

### LGA_NKS_Flow_Prod/ - Scripts de producción Flow
- [ ] `LGA_NKS_Flow_CreateShot.py` — Crear shots Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_ModifyShot.py` — Modificar shots Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_Flow_ShowInFlow.py` — Mostrar en Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QRunnable, QThreadPool)
- [ ] `LGA_NKS_Flow_Thumbs.py` — Thumbnails Flow (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [ ] `LGA_NKS_Flow_ShotPriority.py` — Prioridad de shots (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_FileManager_Download.py` — Descarga FileManager (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_FileManager_Upload.py` — Subida FileManager (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_FileManager_OpenPath.py` — Abrir ruta FileManager (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)

### LGA_NKS_ViewerTL/ - Scripts de timeline/viewer
- [x] `LGA_NKS_Timeline_Refresh_Wrap.py` — Refresh timeline (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [ ] `LGA_NKS_FrameNumber.py` — Números de frame (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)
- [x] `LGA_NKS_PrevNext_Rev.py` — Navegación revisión (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [x] `LGA_NKS_InOut_Editref.py` — EditRef IN/OUT (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton)
- [x] `LGA_NKS_Reduce_SeqWin.py` — Reducir secuencia (sin Qt directo)
- [x] `LGA_NKS_SnapShot.py` — Captura de pantalla (sin Qt directo)

### LGA_NKS_Wasabi/ - Scripts de Wasabi
- [ ] `LGA_NKS_Wasabi_PolicyAssign.py` — Asignación de políticas Wasabi (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QRunnable, QThreadPool)
- [ ] `LGA_NKS_Wasabi_PolicyUnassign.py` — Eliminación de políticas Wasabi (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar)

## Archivos que NO necesitan migración

### Utilidades y configuración
- [x] `LGA_NKS_Shortcuts.py` — Atajos de teclado (migrado a qt_compat)
- [x] `LGA_NKS_Utils/LGA_NKS_StyleUtils.py` — Utilidades de estilos (sin Qt)
- [x] `LGA_NKS_Utils/LGA_NKS_GetClip.py` — Utilidades de clips (sin Qt)
- [x] `LGA_NKS_Utils/README_StyleUtils.md` — Documentación
- [x] `LGA_NKS_Flow_Task_Config.py` — Configuración de tasks Flow (sin Qt)
- [x] `LGA_NKS_Flow_Users.json` — Configuración de usuarios (JSON)
- [x] `LGA_NKS_Panel_Style_Guide.md` — Guía de estilos
- [x] `LGA_NKS_Hilos_Hiero.md` — Documentación de hilos

### Scripts sin Qt
- [x] `LGA_NKS_Flow_Prod/LGA_NKS_FileManager.md` — Documentación
- [x] `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.md` — Documentación
- [x] `LGA_NKS_Wasabi/LGA_NKS_Wasabi_README.md` — Documentación
- [x] `LGA_NKS_Wasabi/verify_policy_assign.py` — Script de verificación (sin Qt)
- [x] `LGA_NKS_Wasabi/verify_policy_created.py` — Script de verificación (sin Qt)
- [x] `LGA_NKS_Wasabi/verify_updated_policy.py` — Script de verificación (sin Qt)
- [x] `LGA_NKS_Wasabi/wasabi_policy_utils.py` — Utilidades Wasabi (sin Qt)
- [x] `LGA_NKS_Edit/LGA_NKS_MatchVerToEXR.md` — Documentación

### Building Blocks (archivos legacy)
- [x] Todos los archivos en `+Building_Blocks/` — Scripts antiguos no usados

### Dependencias externas
- [x] `shotgun_api3/` — API de ShotGrid (externa)
- [x] `LGA_NKS_Wasabi/boto3/` — AWS SDK (externa)
- [x] `LGA_NKS_Wasabi/botocore/` — AWS SDK core (externa)

## Pasos sugeridos para migración

1. **Crear `qt_compat.py`** en `Python/Startup/` (similar al de ToolPacks):
   ```python
   try:
       from PySide6 import QtWidgets, QtGui, QtCore
       from PySide6.QtGui import QAction, QGuiApplication
       PYSIDE_VERSION = 6
   except ImportError:
       from PySide2 import QtWidgets, QtGui, QtCore
       try:
           from PySide2.QtGui import QAction
       except ImportError:
           from PySide2.QtWidgets import QAction
       from PySide2.QtGui import QGuiApplication
       PYSIDE_VERSION = 2
   ```

2. **Migrar paneles principales** (orden recomendado):
   - Empezar con paneles simples como `LGA_NKS_Color_Panel.py`
   - Continuar con `LGA_NKS_ViewerPanel.py`
   - Luego paneles complejos como `LGA_NKS_Flow_Panel.py`

3. **Migrar scripts de funcionalidad**:
   - Reemplazar imports PySide2 → `qt_compat`
   - Revisar uso de APIs deprecated (QApplication, QThreadPool, etc.)
   - Los scripts que usan QRunnable/QThreadPool ya están preparados

4. **Probar en Nuke 15 y 16**:
   - Verificar que los paneles se cargan correctamente
   - Probar funcionalidades básicas
   - Revisar que los estilos y tooltips funcionan

## Consideraciones especiales

### QRunnable y QThreadPool
Los scripts que usan hilos (`LGA_NKS_Flow_Pull.py`, `LGA_NKS_Wasabi_PolicyAssign.py`, etc.) ya están preparados para ambas versiones ya que estas clases no cambiaron entre PySide2/6.

### QApplication global
Muchos scripts crean QApplication. En PySide6 puede haber cambios en el manejo de instancias globales.

### QFont y QFontMetrics
Algunos scripts pueden usar APIs de fuente que cambiaron.

### Cambios en jerarquía de widgets del Timeline
**Problema identificado:** La estructura interna de widgets del timeline cambió significativamente entre Nuke 15 y 16.

**Ejemplo con `LGA_NKS_ScrollTo_TopTrack.py`:**
- **Nuke 15:** Scrollbar horizontal en `QSplitter → QWidget → QAbstractScrollArea → qt_scrollarea_hcontainer`
- **Nuke 16:** Scrollbar vertical (¡no horizontal!) en `QSplitter → QWidget → QAbstractScrollArea → qt_scrollarea_vcontainer`

**Solución implementada:** Lógica híbrida que detecta automáticamente la versión y busca el scrollbar en la ubicación correcta:
- Detecta valores "sospechosos" (positivos cuando deberían ser negativos)
- Cambia automáticamente a método alternativo específico para cada versión
- En Nuke 16 busca en `vcontainer` en lugar de `hcontainer`

**Lección aprendida:** No asumir que la orientación del scrollbar (horizontal vs vertical) se mantiene entre versiones. Hacer pruebas exhaustivas de jerarquía de widgets.

## Estado actual
- [ ] Migración no iniciada
- [ ] `qt_compat.py` no existe
- [ ] Todos los paneles usan PySide2 directamente
- [ ] ~35 scripts requieren cambios de imports
