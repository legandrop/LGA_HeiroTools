# LGA_NKS_Flow_CreateShot v1.2

## Descripción General

Script para crear shots en ShotGrid/Flow Production Tracking basado en clips seleccionados en Hiero/Nuke Studio.

**Cambio importante en v1.2:** Ya no usa templates predefinidos. Crea shots y tasks manualmente para mayor control y flexibilidad.

## Funcionalidades

### ✅ Creación de Shots sin Templates
- Crea shots directamente sin depender de templates predefinidos
- Genera automáticamente la task "Comp" con estado "noread"
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
├── Conexión ShotGrid
├── Funciones de Thumbnail
├── Clases de UI (ShotConfigDialog, FlowStatusWindow)
├── ShotGridManager (lógica de negocio)
├── HieroOperations (operaciones en Hiero)
└── Worker (procesamiento en background)
```

### Funciones Clave

#### `create_shot(project_id, shot_code, shot_config, thumbnail_path=None)`
- Crea shot sin template
- Genera task "Comp" manualmente con estado "noread"
- Asigna reviewers usando el campo `task_reviewers` de la task
- Sube thumbnail si está disponible

#### `find_tasks_for_shot(shot_id, shot_config)`
- Busca tasks existentes del shot
- Actualiza estados según configuración
- Copia descripciones si está habilitado

## Configuración del Usuario

### Diálogo de Configuración

**Campos disponibles:**
- **Shot Description:** Descripción del shot
- **Sequence:** Nombre de la secuencia
- **Opciones:**
  - ☑️ Copy shot description to Comp Description
  - ☑️ Shot status Ready to start
  - ☑️ Task Comp status Ready to start
- **Reviewers:** (Todos activados por defecto)
  - ☑️ Lega Pugliese
  - ☑️ Sebas Romano
  - ☑️ Javi Bravo

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
- Se crea la task "Comp" con estado "noread"
- Se asignan los reviewers seleccionados como `task_reviewers` (no como assignees)
- Se sube thumbnail desde Hiero
- Se actualizan estados según configuración

## Campos ShotGrid Utilizados

### Entidad Shot
- `code`: Código del shot
- `description`: Descripción
- `sg_sequence`: Secuencia padre
- `sg_status_list`: Estado del shot
- `project`: Proyecto

### Entidad Task
- `content`: Nombre de la task ("Comp")
- `entity`: Shot padre
- `sg_status_list`: Estado de la task
- `sg_description`: Descripción (opcional)
- `task_reviewers`: Lista de usuarios asignados como reviewers
- `project`: Proyecto

## Sistema de Logging

### Variables de Debug
```python
DEBUG = False  # Cambiar a True para debug detallado
```

### Niveles de Log
- **INFO:** Operaciones normales
- **DEBUG:** Detalles técnicos (solo con DEBUG=True)
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

### v1.2 - Creación sin Templates (Actual)
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

## Scripts Relacionados

- **LGA_NKS_Flow_Push.py:** Subida de versiones
- **LGA_NKS_Flow_Pull.py:** Descarga de datos
- **LGA_NKS_Flow_NamingUtils.py:** Utilidades de naming

## Conclusión

Esta versión del script representa una mejora significativa al eliminar dependencias de templates específicos, permitiendo que funcione de manera consistente en cualquier proyecto ShotGrid mientras mantiene toda la funcionalidad original.

La investigación exhaustiva realizada asegura que la implementación manual replica exactamente el comportamiento de los templates investigados, pero con mayor flexibilidad y control.

