# Panel de Proyectos LGA - Documentación

## Concepto rápido
- Panel `com.lega.ProjectsPanel` para Hiero/Nuke Studio que escanea `T:\` (`VFX-*/*_SUP`), detecta la última versión `.hrox`, y permite abrir proyectos y sus secuencias.
- Barra superior: `🔄 Refresh` reescanea en background; estado visible; `♻ Reimport` ejecuta el smart reload para redockear y aplicar cambios.
- Click en proyecto lo abre; click en secuencia la abre en timeline (cross-project) preservando ajustes de viewer.

## Archivos clave
- `LGA_NKS_Projects_Panel.py` — Panel definitivo. Clases `ProjectsPanel`, `ProjectItem`, `ScanWorker`. Se auto-registra en `hiero.ui.windowManager()` (AUTO_CREATE_PANEL).
- `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py` — `scan_projects_on_disk()`, `get_open_projects_info()`, `is_project_open()`, `get_project_sequences()`.
- `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py` — `switch_to_sequence_hybrid()` (V3 híbrida: preserva gain/gamma/saturation/playhead, optimiza UI y funciona cross-project).
- `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py` — `main()` recarga y redockea el panel (botón ♻).
- Qt adapter: `LGA_QtAdapter_HieroTools.py` (imports obligatorios). Doc ampliada en `Docu_LGA_QtAdapter.md`.

## Flujo y funcionalidades
- Escaneo automático al abrir y en cada Refresh (QRunnable + QThreadPool, no bloquea UI). Mensajes: “Escaneando… / Listo / Error”.
- Proyectos: se listan alfabéticamente con versión más alta. Click abre con `hiero.core.openProject()`.
- Secuencias: solo de proyectos abiertos. Click llama `switch_to_sequence_hybrid()` y usa `hiero.ui.openInTimeline()` con el objeto `Sequence` (cambio de proyecto automático si aplica).
- Contadores: etiqueta inferior muestra totales de proyectos encontrados y abiertos.
- Reimport: botón `♻` ejecuta el smart reload externo para probar cambios sin reiniciar Hiero.

## UI del panel
- Título centrado “Panel de Proyectos LGA”.
- Toolbar: `🔄 Refresh`, estado, stretch y `♻ Reimport` a la derecha.
- Lista con scroll: proyectos (📁 cerrados, 📂 abiertos). Secuencias indentadas `▶`.
- Etiqueta inferior con resumen de conteos.

## Compatibilidad Qt (Nuke 15/16)
Usar siempre el adapter:
```python
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt
```
No importar PySide2/PySide6 directamente. Helpers disponibles: `horizontal_advance`, `primary_screen_geometry`, `set_layout_margin`.
