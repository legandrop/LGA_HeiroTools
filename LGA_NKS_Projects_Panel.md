# Panel de Proyectos LGA - Documentación

## Concepto rápido
- Panel `com.lega.ProjectsPanel` para Hiero/Nuke Studio que escanea `T:\` (`VFX-*/*_SUP`), detecta la última versión `.hrox`, y permite abrir proyectos y sus secuencias.
- Barra superior: `🔄 Refresh` reescanea en background; estado visible; `♻ Reimport` ejecuta el smart reload para redockear y aplicar cambios.
- Click en proyecto lo abre; click en secuencia la abre en timeline (cross-project) preservando ajustes de viewer.
- **Botón 🔼 Update**: aparece al lado de proyectos abiertos cuando existe versión más nueva en disco, permite actualizar automáticamente.

## Archivos clave
- `LGA_NKS_Projects_Panel.py` — Panel definitivo. Clase `ProjectsPanel`. Se auto-registra en `hiero.ui.windowManager()` (AUTO_CREATE_PANEL).
- `LGA_Projects_Panel/LGA_NKS_ProjectItem.py` — Clase `ProjectItem` para widgets de proyecto y secuencias. Gestiona botón 🔼 update.
- `LGA_Projects_Panel/LGA_NKS_Workers.py` — Clases `WorkerSignals`, `ScanWorker` para operaciones en background.
- `LGA_Projects_Panel/LGA_NKS_UIManager.py` — Clase `UIManager` para configuración y gestión de interfaz de usuario.
- `LGA_Projects_Panel/LGA_NKS_ScanManager.py` — Clase `ScanManager` para gestión de operaciones de escaneo.
- `LGA_Projects_Panel/LGA_NKS_ProjectHandler.py` — Clase `ProjectHandler` para manejo de proyectos y apertura. `on_update_project_click()` actualiza proyectos.
- `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py` — `scan_projects_on_disk()`, `get_open_projects_info()`, `is_project_open()`, `get_project_sequences()`, `get_projects_with_newer_versions()`.
- `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py` — `switch_to_sequence_hybrid()` (V3 híbrida: preserva gain/gamma/saturation/playhead, optimiza UI y funciona cross-project).
- `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py` — `main()` recarga y redockea el panel (botón ♻).
- `LGA_NKS_Projects_Panel.ini` — Configuración (colores por proyecto y auto-refresh interval para re-escaneos periódicos).
- Qt adapter: `LGA_QtAdapter_HieroTools.py` (imports obligatorios). Doc ampliada en `Docu_LGA_QtAdapter.md`.

## Flujo y funcionalidades
- Escaneo automático al abrir y en cada Refresh (QRunnable + QThreadPool, no bloquea UI). Mensajes: "Escaneando… / Listo / Error".
- **Nuke 16: Delay de inicialización** - Se usa `QTimer.singleShot(500ms)` para esperar que Qt esté completamente inicializado antes de ejecutar threads.
- Proyectos: se listan alfabéticamente con versión más alta. Click abre con `hiero.core.openProject()`.
- **Update automático**: proyectos abiertos muestran botón 🔼 cuando existe versión más nueva en disco. Click actualiza automáticamente.
- Secuencias: solo de proyectos abiertos. Click llama `switch_to_sequence_hybrid()` y usa `hiero.ui.openInTimeline()` con el objeto `Sequence` (cambio de proyecto automático si aplica).
- Contadores: etiqueta inferior muestra totales de proyectos encontrados y abiertos.
- Reimport: botón `♻` ejecuta el smart reload externo para probar cambios sin reiniciar Hiero.

## UI del panel
- Título centrado "Panel de Proyectos LGA".
- Toolbar derecha: `🔄 Refresh`, `⚙ Settings`, estado, `♻ Reimport` (opcional).
- Lista con scroll: proyectos (▶ cerrados, ▼ abiertos). **Botón 🔼 update** al lado de proyectos abiertos con versión más nueva.
- Etiqueta inferior con resumen de conteos.
- Vista de Settings (sustituye la lista al pulsar ⚙):
  - Dropdown `Auto-refresh interval`: never / 5min / 10min / 15min / 30min / 1h / 2h (lanza el mismo escaneo que el botón Refresh).
  - Lista editable de proyectos desde el `.ini`: nombre y botón de color (selector HSV). Botón ✕ para eliminar, y `+ Add project` para añadir.
  - Botones `Cancel` y `Save`: vuelven a la vista principal; `Save` escribe en `.ini`, recarga colores y relanza el escaneo.

## Compatibilidad Qt (Nuke 15/16)
Usar siempre el adapter:
```python
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt
```
No importar PySide2/PySide6 directamente. Helpers disponibles: `horizontal_advance`, `primary_screen_geometry`, `set_layout_margin`.

**Consideraciones específicas de Nuke 16:**
- Threading requiere delay de inicialización: `QTimer.singleShot(500ms)` antes de usar `QThreadPool`
- `QFontMetrics.width()` → usar `horizontal_advance()` del adapter
