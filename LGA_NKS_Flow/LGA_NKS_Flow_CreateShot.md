# LGA_NKS_Flow_CreateShot v1.28

## Descripción General

Script para crear shots en ShotGrid/Flow Production Tracking basado en clips seleccionados en Hiero/Nuke Studio.

**Cambio importante en v1.2:** Ya no usa templates predefinidos. Crea shots y tasks manualmente para mayor control y flexibilidad.

**Cambio importante en v1.27:** Sistema modular y DRY para crear múltiples tasks. Agregar nuevas tasks es extremadamente fácil.

**Cambio importante en v1.28:** Todas las tasks del pipeline agregadas con sus colores específicos.

## Funcionalidades

### ✅ Sistema Modular de Tasks (NUEVO v1.27)
- Código completamente refactorizado para ser DRY (Don't Repeat Yourself)
- Agregar nuevas tasks es tan simple como agregar una línea a `AVAILABLE_TASKS`
- UI generada dinámicamente desde configuración
- Creación de tasks en ShotGrid completamente genérica
- Enable/disable dinámico de campos según checkbox de cada task

### ✅ Tasks Disponibles (v1.28)

Todas las tasks del pipeline están disponibles con sus colores específicos:

| # | Task | Color | Pipeline Step | Por Defecto |
|---|------|-------|---------------|-------------|
| 1 | **Comp** | 🔵 Azul | Comp | ✅ Habilitada |
| 2 | **Roto** | 🔵 Azul | Roto | ❌ Deshabilitada |
| 3 | **Cleanup** | 🔵 Cyan | Cleanup | ❌ Deshabilitada |
| 4 | **DMP** | 🟡 Amarillo | DMP | ❌ Deshabilitada |
| 5 | **Model** | 🟠 Naranja | Model | ❌ Deshabilitada |
| 6 | **Retopo** | 🟠 Naranja | Retopo | ❌ Deshabilitada |
| 7 | **Rigging** | 🟢 Verde | Rigging | ❌ Deshabilitada |
| 8 | **Shaders** | 🟢 Verde | Shaders | ❌ Deshabilitada |
| 9 | **Match Move** | 🟣 Morado | Match Move | ❌ Deshabilitada |
| 10 | **Animation** | 🟠 Naranja | Animation | ❌ Deshabilitada |
| 11 | **FX** | 🟣 Magenta | FX | ❌ Deshabilitada |
| 12 | **Lighting** | 🟢 Verde | Lighting | ❌ Deshabilitada |

**Nota importante:** El orden de las tasks en la UI coincide exactamente con el orden en ShotGrid. Los colores también son exactos según los pipeline steps configurados.

### ✅ Creación de Shots sin Templates
- Crea shots directamente sin depender de templates predefinidos
- Genera automáticamente las tasks habilitadas con estado "noread"
- Mayor control sobre la creación de tasks
- Compatible con cualquier proyecto

### ✅ Sistema de Nomenclatura Dual
- **Formato con descripción:** `PROYECTO_SEQ_SHOT_DESC1_DESC2`
- **Formato simplificado:** `PROYECTO_SEQ_SHOT`
- Detección automática del formato basado en el campo 5 del nombre

### ✅ Características Avanzadas
- Creación de thumbnails automática desde Hiero
- Configuración de estados de shot y task
- Copia de descripción del shot a la task Comp
- Interfaz gráfica intuitiva
- Procesamiento en segundo plano

## Investigación y Desarrollo

### Antecedentes del Proyecto

Este script fue desarrollado después de una investigación exhaustiva sobre cómo funcionan los templates en ShotGrid:

#### Templates Investigados

**Template "Template_comp" (Proyecto LC):**
- **task_count:** 1 (solo crea 1 task)
- **Descripción:** "Sólo Comp"
- **Entity Type:** Shot
- **Tasks creadas:** Solo "Comp" con estado inicial "noread"
- **Campos especiales:** Ninguno (no tiene task_defaults, tasks, etc.)

**Template "MNOC - Compo" (Proyecto EHQALPV):**
- Crea tasks: "Plate Online" + "Comp"
- Estado inicial: "noread" para Plate Online, "ready" para Comp

#### Problema Identificado
El script original usaba `"Template_comp"` hardcodeado, pero este template solo existe en el proyecto LC. Para EHQALPV se debería usar `"MNOC - Compo"`, causando inconsistencias.

### Solución Implementada

**v1.2 - Creación sin Templates:**
- Elimina dependencia de templates predefinidos
- Crea shots y tasks manualmente
- Mantiene compatibilidad con el workflow existente
- Funciona en cualquier proyecto

## Arquitectura del Código

### Estructura Principal

```
LGA_NKS_Flow_CreateShot.py
├── AVAILABLE_TASKS (configuración de tasks disponibles) ⭐ NUEVO
├── Conexión ShotGrid
├── Funciones de Thumbnail
├── Clases de UI (ShotConfigDialog, FlowStatusWindow)
├── ShotGridManager (lógica de negocio)
├── HieroOperations (operaciones en Hiero)
└── Worker (procesamiento en background)
```

### Cómo Agregar una Nueva Task ⭐

**¡Es súper fácil!** Solo necesitas agregar una entrada a `AVAILABLE_TASKS`:

```python
AVAILABLE_TASKS = [
    {
        "name": "Comp",
        "pipeline_step": "Comp",
        "enabled_by_default": True,
    },
    {
        "name": "Roto",
        "pipeline_step": "Roto",
        "enabled_by_default": False,
    },
    # ¡Agregar tu nueva task aquí! ⬇️
    {
        "name": "Animation",           # Nombre que aparecerá en UI y ShotGrid
        "pipeline_step": "Animation",   # Pipeline step en ShotGrid
        "enabled_by_default": False,    # Checkbox apagado por defecto
    },
]
```

**¡Eso es todo!** El resto del código se encarga automáticamente de:
- Generar la UI con todos los campos
- Aplicar el color específico de la task
- Habilitar/deshabilitar campos según el checkbox
- Crear la task en ShotGrid con el pipeline step correcto
- Asignar reviewers, descripción, días estimados, etc.

#### Ejemplo: Estado Actual de AVAILABLE_TASKS (v1.28)

```python
AVAILABLE_TASKS = [
    {"name": "Comp", "pipeline_step": "Comp", "enabled_by_default": True, "color": "#3B9ACA"},
    {"name": "Roto", "pipeline_step": "Roto", "enabled_by_default": False, "color": "#3B9ACA"},
    {"name": "Cleanup", "pipeline_step": "Cleanup", "enabled_by_default": False, "color": "#3BCACA"},
    {"name": "DMP", "pipeline_step": "DMP", "enabled_by_default": False, "color": "#CACA3B"},
    {"name": "Model", "pipeline_step": "Model", "enabled_by_default": False, "color": "#CA7A3B"},
    {"name": "Retopo", "pipeline_step": "Retopo", "enabled_by_default": False, "color": "#CA7A3B"},
    {"name": "Rigging", "pipeline_step": "Rigging", "enabled_by_default": False, "color": "#3BCA7A"},
    {"name": "Shaders", "pipeline_step": "Shaders", "enabled_by_default": False, "color": "#3BCA7A"},
    {"name": "Match Move", "pipeline_step": "Match Move", "enabled_by_default": False, "color": "#9A3BCA"},
    {"name": "Animation", "pipeline_step": "Animation", "enabled_by_default": False, "color": "#CA7A3B"},
    {"name": "FX", "pipeline_step": "FX", "enabled_by_default": False, "color": "#CA3B9A"},
    {"name": "Lighting", "pipeline_step": "Lighting", "enabled_by_default": False, "color": "#3BCA7A"},
]
```

#### Ejemplos Prácticos de Nuevas Tasks (Si necesitas agregar más)

**Agregar task personalizada:**
```python
{
    "name": "Custom Task",
    "pipeline_step": "Custom Task",
    "enabled_by_default": False,
    "color": "#FF5733",  # Color personalizado
},
```

**IMPORTANTE:** El `pipeline_step` debe coincidir exactamente con el código del Step en ShotGrid. Si no existe, se mostrará una advertencia pero la task se creará de todos modos (sin pipeline step asignado).

### Funciones Clave (Refactorizadas v1.27)

#### `create_task_row(task_config)` ⭐ NUEVO
- Genera dinámicamente una fila completa de UI para una task
- Crea todos los widgets (enable, est. days, status, description, reviewers)
- Conecta señales para enable/disable dinámico
- Totalmente genérico y reutilizable

#### `toggle_task_fields(task_name, enabled)` ⭐ NUEVO
- Habilita/deshabilita campos de una task según su checkbox
- Cambia colores de labels (gris cuando deshabilitado)
- Manejo centralizado del estado de UI

#### `create_task_for_shot(...)` ⭐ NUEVO
- Crea una task para un shot de forma completamente genérica
- Busca automáticamente el pipeline step correspondiente
- Aplica toda la configuración (status, descripción, días, reviewers)
- Reutilizable para cualquier tipo de task

#### `create_shot(project_id, shot_code, shot_config, thumbnail_path=None)`
- Crea shot sin template
- Itera sobre todas las tasks habilitadas y las crea dinámicamente ⭐
- Sube thumbnail si está disponible

#### `find_tasks_for_shot(shot_id, shot_config)`
- Busca tasks existentes del shot
- Actualiza estados según configuración
- Copia descripciones si está habilitado

## Configuración del Usuario

### Diálogo de Configuración

#### Configuración del Shot (3 columnas)
- **Sequence:** Campo de entrada limitado + **Shot status:** ☑️ Ready to start + **Priority:** ☑️ High

#### Configuración de Tasks (5 columnas por task) ⭐ NUEVO
Cada task tiene su propia fila con:
- **[NOMBRE TASK]:** ☑️ (habilitar/deshabilitar creación de esta task)
- **Est. Days:** Campo numérico para tiempo estimado (0-99.9)
- **Status:** ☑️ Ready to start (estado inicial de la task)
- **Description:** ☑️ copy from shot (copiar descripción del shot)
- **Reviewers:** Checkboxes horizontales (solo nombres en UI)
  - ☑️ Lega
  - ☑️ Sebas
  - ☑️ Javi

**Comportamiento:**
- **Comp:** Habilitada por defecto, todos los campos activos
- **Roto:** Deshabilitada por defecto, campos en gris hasta activar checkbox
- Cuando se deshabilita una task, todos sus campos se ponen en gris
- Cuando se habilita, todos los campos se activan

**Shot Description:** Campo de texto para descripción general del shot

#### Ejemplo Visual de la UI (v1.28)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Flow | Shot Creation                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Configuración del Shot (3 columnas):                                        │
│  [Thumbnail]  [Description]  │  [Sequence]  │  [Status + Priority]          │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔵 COMP ☑        │ Days [2] │ ☑ Ready │ ☑ copy │ ☑Lega ☑Sebas ☑Javi        │
│  (HABILITADA por defecto - campos activos)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔵 ROTO ☐        │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🔵 CLEANUP ☐     │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟡 DMP ☐         │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟠 MODEL ☐       │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟠 RETOPO ☐      │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟢 RIGGING ☐     │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟢 SHADERS ☐     │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟣 MATCH MOVE ☐  │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟠 ANIMATION ☐   │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟣 FX ☐          │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  🟢 LIGHTING ☐    │ Days [0] │ ☐ Ready │ ☐ copy │ ☐Lega ☐Sebas ☐Javi        │
│  (DESHABILITADAS por defecto - campos en gris hasta activar checkbox)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Nota:** Los colores en el nombre de cada task coinciden con los colores de pipeline steps en ShotGrid.

### Estados de Task

| Estado | Descripción |
|--------|-------------|
| `noread` | Estado inicial (creado por template) |
| `ready` | Listo para comenzar trabajo |
| `ip` | En progreso |
| `rev` | En revisión |
| `apr` | Aprobado |

## Uso del Script

### En Hiero/Nuke Studio

1. **Seleccionar clips** en el timeline
2. **Ejecutar script:** `LGA_NKS_Flow_CreateShot.py`
3. **Configurar opciones** en el diálogo
4. **Hacer clic en "Create Shots (No Template)"**
5. **Monitorear progreso** en la ventana de estado

### Resultado

Para cada clip seleccionado:
- Se crea un shot en ShotGrid (si no existe)
- Se crean todas las tasks habilitadas (ej: Comp, Roto) ⭐
- Cada task se crea con su pipeline step correspondiente ⭐
- Se asignan los reviewers seleccionados como `task_reviewers` (no como assignees)
- Se sube thumbnail desde Hiero
- Se actualizan estados según configuración
- Tasks deshabilitadas no se crean ⭐

## Campos ShotGrid Utilizados

### Entidad Shot
- `code`: Código del shot
- `description`: Descripción
- `sg_sequence`: Secuencia padre
- `sg_status_list`: Estado del shot
- `sg_prioridad`: Prioridad del shot ("high" si activado, opcional)
- `project`: Proyecto

### Entidad Task
- `content`: Nombre de la task ("Comp")
- `entity`: Shot padre
- `step`: Pipeline step (asignado automáticamente a "Comp")
- `sg_status_list`: Estado de la task
- `sg_description`: Descripción (opcional)
- `sg_estdias`: Tiempo estimado en días (opcional, solo si > 0)
- `task_reviewers`: Lista de usuarios asignados como reviewers
- `project`: Proyecto

### Entidad Step (Pipeline Steps)
- `code`: Código del step (ej: "Comp", "Animation", "Lighting")
- **Nota:** Los pipeline steps son entidades globales en ShotGrid y no están asociados a proyectos específicos

## Sistema de Logging

### Variables de Debug
```python
DEBUG = False  # Cambiar a True para debug detallado
```

### Sistema de Logging Seguro para Hilos
El script utiliza un sistema de logging seguro para entornos multi-hilo que evita conflictos con la GUI de Hiero:

- **Acumulación en memoria:** Los mensajes de debug se acumulan en una lista durante el procesamiento en hilos separados
- **Impresión diferida:** Los logs se imprimen solo al finalizar la operación, evitando crashes por acceso concurrente a la consola
- **Señales seguras:** Utiliza señales Qt para coordinar la impresión de logs entre hilos

### Niveles de Log
- **INFO:** Operaciones normales
- **DEBUG:** Detalles técnicos (solo con DEBUG=True, se imprime al final)
- **ERROR:** Errores críticos

## Compatibilidad

### Versiones Soportadas
- **ShotGrid/Flow:** Todas las versiones recientes
- **Hiero/Nuke Studio:** 12.0+
- **Python:** 3.6+

### Proyectos Soportados
- Funciona en cualquier proyecto ShotGrid
- No requiere configuración específica por proyecto
- Compatible con diferentes esquemas de tasks

## Mantenimiento y Troubleshooting

### Logs de Error Comunes

**"No se encontró la secuencia"**
- Verificar que la secuencia existe en ShotGrid
- Revisar permisos de acceso

**"Error al crear el shot"**
- Verificar permisos de creación en ShotGrid
- Revisar campos obligatorios

**"No se pudieron obtener credenciales"**
- Verificar archivo SecureConfig_Reader.py
- Revisar variables de entorno

### Archivos de Configuración

**SecureConfig_Reader.py**
```python
# Debe contener función get_flow_credentials()
# Retorna: sg_url, sg_login, sg_password
```

**LGA_NKS_Flow_NamingUtils.py**
- Funciones de parsing de nombres de archivo
- Detección automática de formato

## Historial de Versiones

### v1.28 - Pipeline Completo con Colores (Actual) ⭐
- ✅ **12 tasks del pipeline agregadas:** Comp, Roto, Cleanup, DMP, Model, Retopo, Rigging, Shaders, Match Move, Animation, FX, Lighting
- ✅ **Colores específicos por task:** Cada task muestra su color de pipeline step en la UI
- ✅ **Sistema de colores implementado:** 
  - 🔵 Azul: Comp, Roto
  - 🔵 Cyan: Cleanup
  - 🟡 Amarillo: DMP
  - 🟠 Naranja: Model, Retopo, Animation
  - 🟢 Verde: Rigging, Shaders, Lighting
  - 🟣 Morado: Match Move
  - 🟣 Magenta: FX
- ✅ **Orden respetado:** Mismo orden que en ShotGrid
- ✅ **Todo funcional:** Todas las tasks se crean con sus pipeline steps correctos

### v1.27 - Sistema Modular de Tasks ⭐
- ✅ **Refactorización completa a código DRY (Don't Repeat Yourself)**
- ✅ **Sistema modular:** Agregar nuevas tasks es tan fácil como agregar una línea
- ✅ **UI dinámica:** Generada automáticamente desde `AVAILABLE_TASKS`
- ✅ **Creación genérica de tasks en ShotGrid**
- ✅ **Task Roto agregada** (deshabilitada por defecto)
- ✅ **Enable/disable dinámico:** Campos se ponen en gris cuando task está deshabilitada
- ✅ **Estructura de datos mejorada:** `shot_config["tasks"]` con configuración por task
- ✅ **Método `create_task_row()`:** Genera UI dinámicamente
- ✅ **Método `toggle_task_fields()`:** Maneja enable/disable de campos
- ✅ **Método `create_task_for_shot()`:** Crea cualquier task de forma genérica
- ✅ **Preparado para el futuro:** Fácil agregar más tasks

### v1.26 - UI Reorganizada para Task Comp
- ✅ Layout reorganizado: 3 columnas para configuración del shot
- ✅ 5 columnas dedicadas para configuración de Task Comp
- ✅ Checkbox de habilitación para Task Comp
- ✅ Reviewers mostrados solo con nombres (sin apellidos) en UI

### v1.25 - Checkbox "High Priority"
- ✅ Agregado checkbox "High Priority" para asignar sg_prioridad="high"

### v1.24 - Mensajes Diferenciados para Shots
- ✅ Shots existentes muestran mensaje de error en rojo
- ✅ Solo shots recién creados cuentan como éxito
- ✅ Mejor feedback visual para el usuario
- ✅ Lógica clara: crear = verde, existente = rojo
- ✅ Task Comp asignada automáticamente al pipeline step "Comp"
- ✅ Checkbox "High Priority" para asignar sg_prioridad="high"

### v1.23 - Sistema de Logging Seguro para Hilos
- ✅ Sistema de logging multi-hilo seguro
- ✅ Impresión diferida de debug logs para evitar crashes
- ✅ Señalización Qt para coordinación entre hilos
- ✅ Compatible con procesamiento en background

### v1.22 - Campo de Tiempo Estimado
- ✅ Agregado campo numérico para tiempo estimado en días (0-99.9)
- ✅ Soporte para valores decimales (ej: 12.5)
- ✅ Campo sg_estdias solo se envía si el valor es mayor que 0
- ✅ Validación de entrada con decimales

### v1.21 - Asignación de Reviewers
- ✅ Asigna reviewers a la task usando el campo task_reviewers
- ✅ Eliminada dependencia de templates
- ✅ Creación manual de tasks
- ✅ Asignación automática de reviewers
- ✅ Mayor compatibilidad entre proyectos
- ✅ Documentación completa

### v1.1 - Sistema Dual de Nomenclatura
- ✅ Detección automática de formato
- ✅ Compatibilidad PROYECTO_SEQ_SHOT_DESC1_DESC2
- ✅ Compatibilidad PROYECTO_SEQ_SHOT

### v1.0 - Versión Inicial
- ✅ Creación básica de shots
- ✅ Template "Template_comp" hardcodeado
- ✅ Solo proyecto LC

## Quick Start: Agregar una Nueva Task

### Paso 1: Editar AVAILABLE_TASKS

Abre `LGA_NKS_Flow_CreateShot.py` y busca la sección `AVAILABLE_TASKS` (línea ~70):

```python
AVAILABLE_TASKS = [
    {
        "name": "Comp",
        "pipeline_step": "Comp",
        "enabled_by_default": True,
    },
    {
        "name": "Roto",
        "pipeline_step": "Roto",
        "enabled_by_default": False,
    },
    # ⬇️ AGREGAR AQUÍ TU NUEVA TASK ⬇️
    {
        "name": "TU_TASK",              # Ej: "Animation", "Lighting", "FX"
        "pipeline_step": "TU_STEP",     # Debe existir en ShotGrid
        "enabled_by_default": False,    # True o False
    },
]
```

### Paso 2: Guardar y Reiniciar Hiero

¡Listo! No necesitas modificar nada más. La nueva task aparecerá automáticamente en la UI con todos sus campos.

### Paso 3: Verificar Pipeline Step en ShotGrid

Asegúrate de que el pipeline step existe en ShotGrid con el mismo código (`code` field). Si no existe, la task se creará sin pipeline step (con advertencia en logs).

## Scripts Relacionados

- **LGA_NKS_Flow_Push.py:** Subida de versiones
- **LGA_NKS_Flow_Pull.py:** Descarga de datos
- **LGA_NKS_Flow_NamingUtils.py:** Utilidades de naming

## Conclusión

**v1.28** completa el pipeline con todas las tasks disponibles y sus colores específicos:

### Evolución del Script

#### Antes (v1.26)
- Código hardcodeado para cada task
- Solo task Comp disponible
- Agregar una nueva task requería duplicar ~200 líneas de código
- UI generada manualmente
- Propenso a errores y difícil de mantener

#### v1.27 ⭐
- **Código DRY y modular**
- **Agregar nueva task: 1 entrada en `AVAILABLE_TASKS` (~5 líneas)**
- **UI generada dinámicamente**
- **Todo el comportamiento es automático**
- 2 tasks: Comp, Roto

#### v1.28 ⭐⭐ (Actual)
- **12 tasks del pipeline completo**
- **Sistema de colores implementado**
- **Orden y colores respetan ShotGrid exactamente**
- **Listo para producción con cualquier tipo de shot**
- Tasks: Comp, Roto, Cleanup, DMP, Model, Retopo, Rigging, Shaders, Match Move, Animation, FX, Lighting

### Ventajas del Sistema Actual

✅ **Modularidad:** Agregar/modificar tasks es trivial  
✅ **Consistencia:** Colores y nombres coinciden con ShotGrid  
✅ **Escalabilidad:** 12 tasks funcionan igual que 2  
✅ **Mantenibilidad:** Código limpio y DRY  
✅ **Flexibilidad:** Habilitar solo las tasks necesarias por shot  
✅ **Sin templates:** Funciona en cualquier proyecto  

Esta versión del script representa una mejora significativa al eliminar dependencias de templates específicos, permitiendo que funcione de manera consistente en cualquier proyecto ShotGrid mientras mantiene toda la funcionalidad original.

La refactorización a código modular asegura que el script sea fácil de mantener y extender en el futuro, sin necesidad de duplicar lógica.

