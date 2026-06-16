# LGA_HieroTools - Context Profile

## Objetivo

Permitir que las tools de Hiero trabajen en modo `studio` o `project` sin cambiar código,
solo editando un INI.

## Archivo de control

Ubicación:

- `~/.nuke/Python/Startup/LGA_HieroTools_context.ini`

Formato:

```ini
[Context]
mode=studio
```

Valores válidos:

- `mode=studio`
- `mode=project`

## Qué cambia por contexto

- Lectura de `config.secure` y `.key` desde:
  - `%APPDATA%/LGA/PipeSync` (studio)
  - `%APPDATA%/LGA/PipeSyncProject` (project)
- Resolución de `pipesync.db` y `pipesync_playlists.db` mediante helper compartido
  (`LGA_NKS_Shared/LGA_NKS_PipeSyncPaths.py`) sin hardcodes fijos por script.
- Fallback de escaneo base en panel de proyectos:
  - `T:\` en studio
  - `N:\` en project (si no hay `AltTPath`)

## Módulos clave

- `LGA_NKS_Shared/LGA_NKS_ContextProfile.py`
- `LGA_NKS_Shared/SecureConfig_Reader.py`
- `LGA_NKS_Shared/LGA_NKS_PipeSyncPaths.py`
