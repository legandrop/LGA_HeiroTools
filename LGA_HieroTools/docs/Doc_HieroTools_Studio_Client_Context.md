# LGA_HieroTools - Contexto Studio/Client (integración con PipeSync)

## Referencia principal

Este documento complementa a:

- `C:/Portable/LGA_PipeSync_2/Docs/Doc_Studio_Client_Context.md`

PipeSync define la arquitectura de contexto. Este MD documenta cómo se aplica en
HieroTools, qué scripts quedaron adaptados y cuáles requieren revisión adicional.

## Estado actual

- Control de contexto por INI: `LGA_HieroTools_context.ini` (`mode=studio|client`).
- Resolución de `config.secure/.key` por contexto activo.
- Resolución de cache/DB por contexto activo (con fallback portable histórico).
- Preflight bloqueante en Pull/Push con mensajes UI cuando faltan prerequisitos.
- Projects Panel con switch Studio/Client visible solo para `lega@wanka.tv`
  (leyendo PipeSync normal).

## Reglas operativas

- Si falta `config.secure` o `pipesync.db`, Pull y Push muestran error claro.
- Push además valida `Flow.Url`, `Flow.Login`, `Flow.Password`.
- En client no se debe caer en DB studio como fallback funcional.
- El switch Studio/Client actualiza INI y fuerza recarga del Projects Panel.

## Archivos adaptados (confirmados)

### Núcleo de contexto

- `LGA_HieroTools_context.ini`
- `LGA_HieroTools/LGA_NKS_Shared/LGA_NKS_ContextProfile.py`
- `LGA_HieroTools/LGA_NKS_Shared/SecureConfig_Reader.py`
- `LGA_HieroTools/LGA_NKS_Shared/LGA_NKS_PipeSyncPaths.py`
- `LGA_HieroTools/LGA_NKS_Shared/LGA_NKS_PipeSyncPreflight.py`
- `LGA_HieroTools/docs/Docu_Context_Profile.md`

### Flow Pull / Push

- `LGA_HieroTools/LGA_NKS_Flow_Panel.py`
- `LGA_HieroTools/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py`
- `LGA_HieroTools/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py`
- `LGA_HieroTools/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Shot_info.py`

### Playlist / permisos

- `LGA_HieroTools/LGA_NKS_Playlist_Panel_py/LGA_NKS_FlowPlaylist_Pull.py`
- `LGA_HieroTools/LGA_NKS_Playlist_Panel_py/LGA_NKS_FlowPlaylist_Push.py`
- `LGA_HieroTools/LGA_NKS_Playlist_Panel_py/LGA_NKS_FlowPlaylist_Shot_info.py`
- `LGA_HieroTools/LGA_NKS_Playlist_Panel_py/LGA_NKS_Playlist_Panel_Permissions.py`

### Projects

- `LGA_HieroTools/LGA_NKS_Projects_Panel.py`
- `LGA_HieroTools/LGA_NKS_Projects_Panel_py/LGA_Projects_Panel_ScanProjects.py`
- `LGA_HieroTools/LGA_NKS_Projects_Panel_py/LGA_Projects_Panel_SwitchSequence.py`

## Archivos revisados que siguen parciales o con deuda

- `LGA_HieroTools/LGA_NKS_Coordination_Panel_py/LGA_NKS_PipeSync_OpenPath.py`
  - usa rutas hardcodeadas de instalación (no completamente context-aware).
- `LGA_HieroTools/LGA_NKS_Coordination_Panel_py/LGA_NKS_PipeSync_CreatePsync.py`
  - requiere confirmar matriz Studio/Client en entorno deploy.
- `LGA_HieroTools/+Building_Blocks/PipeSync_Usuario_Actual.md`
  - documentación desactualizada respecto a estructura actual shared/contexto.
- `LGA_HieroTools/LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull_README.md`
  - referencias históricas y ejemplos con paths legacy.

## Decisiones de diseño implementadas

- Switch en Projects Panel:
  - persistencia en `LGA_HieroTools_context.ini`;
  - override de sesión vía `LGA_HIEROTOOLS_CONTEXT_INI` y `PIPESYNC_CONTEXT`;
  - recarga de panel/proyectos sin reinicio obligatorio.
- Visibilidad del switch:
  - solo si `Flow.Login` de `%APPDATA%/LGA/PipeSync/config.secure` es
    `lega@wanka.tv`.
- Preflight:
  - validación común para Pull/Push con mensajes de error accionables.

## Gaps detectados (seguimiento)

- Unificar paths de runtime/ejecutable de PipeSync en módulos de Coordination.
- Revisar documentación auxiliar para eliminar ejemplos studio-only.
- Validar en QA que todos los paneles abiertos en sesión refrescan contexto sin
  reinicio en escenarios edge.
