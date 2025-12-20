# Reorganización de Scripts de Edición

## Scripts a mover de `LGA_NKS` a `LGA_NKS_Edit`

- [x] **LGA_NKS_FixColorspaces.py** - Corrige colorspaces rec709 y gamma2.2 en clips
- [x] **LGA_NKS_CreateNewTrack.py** - Crea nuevos tracks de video
- [x] **LGA_NKS_Trim_In.py** - Recorta material antes del playhead
- [x] **LGA_NKS_Trim_Out.py** - Recorta material después del playhead
- [x] **LGA_NKS_Reconnect.py** - Maneja reconexión de rutas (Win ↔ Mac)
- [x] **LGA_NKS_SelfReplaceClip.py** - Reemplaza clips manteniendo propiedades
- [x] **LGA_NKS_mediaMissingFrames.py** - Verifica frames faltantes en clips

## Scripts a mover de otras carpetas

- [ ] **LGA_NKS_Flow/LGA_NKS_Delete_ClipTags.py** → `LGA_NKS_Edit/LGA_NKS_Delete_ClipTags.py` - Elimina tags de clips

## Funcionalidades embebidas a extraer como scripts

- [ ] **Extraer `set_shot_name()`** - Crear `LGA_NKS_SetShotName.py` con la lógica del método `set_shot_name()` (líneas 377-439)
- [ ] **Extraer `OrganizeProject`** - Crear `LGA_NKS_OrganizeProject.py` con la clase `OrganizeProject` completa (líneas 1052-1116)

## Verificación final

- [ ] Actualizar rutas en `LGA_NKS_EditTools_Panel.py` para apuntar a `LGA_NKS_Edit` en lugar de `LGA_NKS`
- [ ] Probar que todos los botones del panel funcionen correctamente después de la reorganización
- [ ] Verificar que no queden referencias rotas a los scripts movidos