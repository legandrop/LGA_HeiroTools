> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.

# LGA_NKS_Wasabi_PolicyUnassign_CompletedShots

## Objetivo
Este script permite limpiar en lote líneas de policies de Wasabi que siguen dando acceso a shots ya terminados en PipeSync.

Se considera "terminado" cuando el shot está en alguno de estos estados:
- `approved`
- `delivery_checked`

Para compatibilidad con valores internos de la DB también toma:
- `apr` -> `approved`
- `check` -> `delivery_checked`

## Flujo
1. Lee `pipesync.db` y arma un mapa de shots terminados.
2. Lista policies locales de Wasabi (`*_policy`).
3. Lee cada policy y extrae shots desde statements `s3:*`.
4. Cruza los shots de policy con los shots terminados de DB.
5. Muestra una ventana con filas:
   - `Nombre de policy | Nombre de shot | Estado del shot`
6. Todas las filas arrancan seleccionadas.
7. Al presionar **Limpiar policies**, elimina referencias del shot en:
   - Prefijos de `s3:ListBucket`
   - Recursos de `s3:*`
8. Guarda una nueva versión de cada policy modificada y la deja como default.

## Integración en panel
Se ejecuta con:
- **Shift+Click** en el botón `Clear Assignees` del panel `LGA_NKS_Flow_Assignee_Panel`.

## Archivo DB
- Windows: `C:/Portable/LGA/PipeSync/cache/pipesync.db`
- macOS: `~/Library/Caches/LGA/PipeSync/pipesync.db`

## Script relacionado
- Implementación: `LGA_NKS_Wasabi_PolicyUnassign_CompletedShots.py`
