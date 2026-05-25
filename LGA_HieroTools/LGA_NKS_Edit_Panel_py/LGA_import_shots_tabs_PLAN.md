> **Regla de documentación**: este archivo registra las decisiones de diseño tomadas antes de implementar el refactor de tabs (v1.07). Una vez implementado, las decisiones que afecten el estado final del código deben migrarse al MD principal (`LGA_import_shots.md`). Este archivo puede conservarse como referencia histórica.

# Plan: Refactor de navegación por tabs — v1.07

## Objetivo

Reemplazar el sistema de navegación por páginas (`QStackedWidget` con botones "Go Back") por un sistema de **tres tabs fijos** en la parte superior de la ventana.

---

## Decisiones de diseño (todas confirmadas)

### 1. Estructura de tabs

| Posición | Nombre del tab | Equivale a (antes) |
|----------|---------------|---------------------|
| 1 (izquierda) | **Rename** | PAGE_RENAME |
| 2 (centro) | **Transcode Plates** | PAGE_CONVERT |
| 3 (derecha) | **Import** | PAGE_MEDIA + PAGE_IMPORT |

- La tool **siempre abre en el tab Rename**.
- El título de sección que antes decía "MEDIA ENCONTRADA", "RENAME", etc. desaparece; su lugar lo ocupa el tab activo.

---

### 2. Estilo visual de los tabs

- Implementado con **QTabWidget + stylesheet CSS personalizado**.
- Estética: dark theme, texto uppercase, indicador de tab activo con color inferior (sin usar QPainter custom).
- El estilo sigue la paleta existente de la tool (`#2B2B2B`, `#272727`, `#CCCCCC`, etc.).
- Tabs deshabilitados durante transcode: greyed out visualmente + no clickeables (comportamiento estándar de QTabWidget con `setTabEnabled(False)`).

---

### 3. Footer compartido

El footer con **Open Queue + estado global + botones de acción** es **compartido en los tres tabs**.

Los botones de acción del footer cambian según el tab activo:

| Tab | Botones en el footer |
|-----|----------------------|
| Rename | `Run Rename` (igual que ahora, sin Go Back) |
| Transcode Plates | `Start Transcode` (igual que ahora, sin Go Back) |
| Import (vista tabla) | `Preview Timeline` (gris) · `Import Now` (primary) · `Import and Create V000` (primary) |
| Import (vista preview) | `← Go Back` (gris) · `Import Now` (primary) · `Import and Create V000` (primary) |

---

### 4. Independencia de las tablas

Las tres tablas son **completamente independientes**: los checkboxes de una tabla no afectan a las demás.

- Antes: Rename y Transcode mostraban solo los ítems chequeados en la tabla principal.
- Ahora: cada tabla tiene su propio estado de selección, sin filtro cruzado.

---

### 5. Estado inicial de checkboxes por tab

| Tab | Default al abrir la tool |
|-----|--------------------------|
| **Rename** | Todos los ítems chequeados |
| **Transcode Plates** | Todos los ítems chequeados |
| **Import** | Igual que la tabla principal actual: EXR de `_input` con `is_latest=True` → checked; resto → unchecked |

---

### 6. Contenido de cada tab

#### Tab Rename
- Tabla **idéntica a la actual** (mismas columnas, mismos section headers, todas las versiones).
- Se elimina únicamente el botón "Go Back".
- Muestra **todos los archivos** encontrados (PUBLISH + PLATES + REFERENCES), sin filtro de la tabla principal.

#### Tab Transcode Plates
- Tabla **idéntica a la actual**, sin botón "Go Back".
- Muestra **todos los plates EXR de `_input/`**, incluyendo todas las versiones (no solo la más alta).
- Sin filtro de la tabla principal.

#### Tab Import — vista tabla (sub-estado: `import_main`)
- **Idéntico a la tabla principal actual** (PAGE_MEDIA): mismas columnas, section headers, dropdowns de track, botones de selección rápida.
- Botones de selección rápida (Select All / Clear / Plates / References / Publish) se mantienen en este tab.
- Botones de footer: `Preview Timeline` · `Import Now` · `Import and Create V000`.
  - `Preview Timeline`: gris (estilo `_BTN_CANCEL`), siempre habilitado cuando hay ítems.
  - `Import Now`: primary (violeta `#443a91`), habilitado cuando hay al menos 1 ítem con track asignado y chequeado.
  - `Import and Create V000`: igual que `Import Now`.

#### Tab Import — vista preview (sub-estado: `import_preview`)
- **Idéntico a PAGE_IMPORT actual**: misma tabla de preview, mismo comportamiento.
- Se activa al clickear "Preview Timeline" desde la vista tabla del tab Import.
- El botón "← Go Back" en el footer vuelve a la vista tabla del tab Import (no cambia de tab).
- `Import Now` e `Import and Create V000` siguen apareciendo en esta vista (igual que en PAGE_IMPORT actual).
- El tab Import alterna entre `import_main` e `import_preview` con un `QStackedWidget` interno al tab.

---

### 7. Import Now directo (sin preview)

- El botón "Import Now" en la vista tabla del tab Import **importa directamente** sin pasar por el preview.
- El preview (Preview Timeline) es opcional para quien quiera verificar antes de importar.
- Este es un cambio deliberado respecto al flujo v1.06 donde Import siempre mostraba el preview primero.

---

### 8. Comportamiento durante transcode activo (esta ventana)

"Transcode activo" = el usuario presionó "Start Transcode" en **esta** ventana (no en otra).

- Tab **Transcode Plates**: único tab activo.
- Tabs **Rename** e **Import**: `setTabEnabled(False)` → greyed out + no clickeables.
- Al terminar el transcode: `setTabEnabled(True)` en ambos tabs.
- Esto reemplaza el comportamiento anterior de deshabilitar/renombrar el botón "Go Back".

> Los transcodes de otras ventanas (cola global) **no** deshabilitan los tabs de esta ventana.

---

### 9. Refresh inteligente entre tabs

#### Mecanismo
```python
self._needs_refresh: set  # conjunto de strings de tab: "rename", "transcode", "import"
```

#### Cuándo se setea el flag
| Acción | Flags que se activan |
|--------|----------------------|
| Rename ejecutado con éxito | `{"transcode", "import"}` |
| Transcode completado en esta ventana | `{"rename", "import"}` |

#### Cuándo se ejecuta el refresh
- Al activar un tab cuyo nombre está en `_needs_refresh`.
- Refresh = re-escaneo completo de carpeta + re-lectura de metadata (oiiotool/ffprobe).
- Tras el refresh, el flag se elimina del set.

#### Estado de checkboxes durante refresh
- Antes de reconstruir la tabla: guardar el conjunto de paths chequeados.
- Tras reconstruir: restaurar el estado checked para los ítems que sigan existiendo.
- Ítems nuevos detectados en el refresh: se suman con el default de ese tab (todos chequeados para Rename y Transcode; lógica `is_latest` para Import).

---

### 10. Eliminaciones respecto a v1.06

| Elemento eliminado | Motivo |
|--------------------|--------|
| Botón "Go Back" en Rename | Reemplazado por tabs |
| Botón "Go Back" en Transcode | Reemplazado por tabs |
| Botón "Import" en PAGE_MEDIA | Reemplazado por "Import Now" y "Preview Timeline" en tab Import |
| Botones "Rename" y "Transcode Plates" en PAGE_MEDIA | Reemplazados por los tabs |
| `_show_page()` con PAGE_MEDIA / PAGE_RENAME / PAGE_CONVERT | Reemplazado por `setCurrentIndex()` del QTabWidget |
| `_rename_happened` y `_transcode_happened` (flags bool) | Reemplazados por `_needs_refresh` (set) |

---

### 11. Versión

- El script sube de **v1.06 → v1.07**.
- Entrada en el docstring: `v1.07: Navegación por tabs (Rename / Transcode Plates / Import). Tablas independientes, refresh inteligente, Import Now directo sin preview obligatorio.`

---

### 12. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `LGA_import_shots.py` | Implementación completa |
| `LGA_import_shots.md` | Actualizar secciones afectadas: acceso, flujo general, botones, constantes |
| `LGA_import_shots_transcode.md` | Remover referencias a "Go Back" y al filtro de tabla principal |
| `LGA_import_shots_rename.md` | Remover referencias a "Go Back" y al filtro de tabla principal |

---

## Lo que NO cambia

- Toda la lógica interna de rename (`LGA_import_shots_rename.py`)
- Toda la lógica de transcode (`LGA_import_shots_transcode.py`, `LGA_import_shots_transcode_queue.py`)
- Toda la lógica de import real (`_do_import`, `_do_import_and_v000`)
- Toda la lógica de preview (`LGA_import_shots_preview.py`)
- Footer (Open Queue, estado global, botón de shot activo)
- Módulos auxiliares (bin, timeline, settings, rename_settings)
- Sistema de logging
- Dropdown de track con botón "Crear track"
- Sistema de presets de resolución en Transcode
