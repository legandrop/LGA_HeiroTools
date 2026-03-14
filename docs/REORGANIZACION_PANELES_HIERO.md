# Reorganizacion de Paneles Hiero

## Objetivo

Documentar:

- La ubicacion actual de los paneles y scripts relacionados.
- Que scripts son privados de un panel y cuales son compartidos.
- Una propuesta de reorganizacion basada en ownership real.

El criterio usado es:

- Si un script/tool lo usa un solo panel, debe vivir en la carpeta privada de ese panel.
- Si lo usan tools de varios paneles, debe vivir en una carpeta compartida.
- Los renombres y movimientos futuros deberian hacerse con `git mv`.

## Estructura actual

### Paneles raiz

- `LGA_NKS_Flow_Panel.py`
- `LGA_NKS_Flow_Assignee_Panel.py`
- `LGA_NKS_Flow_FlowProd_Panel.py`
- `LGA_NKS_ViewerPanel.py`
- `LGA_NKS_EditTools_Panel.py`
- `LGA_NKS_Review_Panel.py`
- `LGA_NKS_Projects_Panel.py`
- `LGA_NKS_Color_Panel.py`
- `LGA_NKS_FlowNo_Panel.py`

### Carpetas actuales relacionadas

- `LGA_NKS/`
- `LGA_NKS_Edit/`
- `LGA_NKS_Flow/`
- `LGA_NKS_Flow_Prod/`
- `LGA_NKS_Utils/`
- `LGA_NKS_ViewerTL/`
- `LGA_NKS_Wasabi/`
- `LGA_Projects_Panel/`

### Shareds actuales sueltos en raiz

- `LGA_QtAdapter_HieroTools.py`
- `LGA_NKS_Flow_Task_Config.py`
- `LGA_NKS_Flow_Users.json`
- `LGA_NKS_Projects_Panel.ini`
- `LGA_NKS_Shortcuts.py`

## Mapa actual por panel

### 1. Flow Panel

Panel:

- `LGA_NKS_Flow_Panel.py`

Hoy carga scripts desde:

- `LGA_NKS_Flow/LGA_NKS_Flow_Pull.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Push.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`
- `LGA_NKS_Flow/LGA_NKS_ReviewPic.py`
- `LGA_NKS_Flow/LGA_NKS_Delete_ClipTags.py`

Tambien usa shareds:

- `LGA_NKS_Flow_NamingUtils.py`
- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Utils/LGA_NKS_GetClip.py`

### 2. Flow Assignee Panel

Panel:

- `LGA_NKS_Flow_Assignee_Panel.py`

Hoy carga scripts desde:

- `LGA_NKS_Flow/LGA_NKS_Flow_Assignee.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Assign_Assignee.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Clear_Assignees.py`
- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyAssign.py`
- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyUnassign.py`
- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyUnassign_CompletedShots.py`

Tambien usa shareds:

- `LGA_NKS_Flow_NamingUtils.py`
- `LGA_NKS_Utils/LGA_NKS_GetClip.py`
- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Flow_Users.json`
- `LGA_NKS_Flow_Task_Config.py`

### 3. FlowProd Panel

Panel:

- `LGA_NKS_Flow_FlowProd_Panel.py`

Hoy carga scripts desde:

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShowInFlow.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_Thumbs.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ModifyShot.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShotPriority.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_OpenPath.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Download.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Upload.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CheckTimelineShots.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_OpenPath.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_CreatePsync.py`

Tambien usa shareds:

- `LGA_NKS_Flow_NamingUtils.py`
- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Flow_Task_Config.py` indirectamente via `LGA_NKS_Flow_CreateShot.py`

### 4. Viewer Panel

Panel:

- `LGA_NKS_ViewerPanel.py`

Hoy carga scripts desde:

- `LGA_NKS_ViewerTL/LGA_NKS_Viewer_Mask.py`
- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py`
- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py`
- `LGA_NKS_ViewerTL/LGA_NKS_InOut_Editref.py`
- `LGA_NKS_ViewerTL/LGA_NKS_PrevNext_Rev.py`
- `LGA_NKS_ViewerTL/LGA_NKS_SnapShot.py`
- `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber.py`

Tambien usa shareds:

- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Flow/SecureConfig_Reader.py`

### 5. EditTools Panel

Panel:

- `LGA_NKS_EditTools_Panel.py`

Hoy carga scripts desde:

- `LGA_NKS_Edit/LGA_NKS_ColorTransforms.py`
- `LGA_NKS_Edit/LGA_NKS_FixColorspaces.py`
- `LGA_NKS_Edit/LGA_NKS_CreateNewTrack.py`
- `LGA_NKS_Edit/LGA_NKS_OrganizeProject.py`
- `LGA_NKS_Edit/LGA_NKS_SetShotName.py`
- `LGA_NKS_Edit/LGA_NKS_Trim_In.py`
- `LGA_NKS_Edit/LGA_NKS_Trim_Out.py`
- `LGA_NKS_Edit/LGA_NKS_Reconnect.py`
- `LGA_NKS_Edit/LGA_NKS_CleanProject.py`
- `LGA_NKS_Edit/LGA_NKS_mediaMissingFrames.py`
- `LGA_NKS_Edit/LGA_NKS_MatchVerToEXR.py`
- `LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`
- `LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`

Tambien carga shareds fuera de esa carpeta:

- `LGA_NKS_Flow/LGA_NKS_Delete_ClipTags.py`
- `LGA_NKS_Edit/LGA_NKS_SelfReplaceClip.py`

Tambien usa shareds:

- `LGA_NKS_Flow_NamingUtils.py`
- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`

### 6. Review Panel

Panel:

- `LGA_NKS_Review_Panel.py`

Hoy carga scripts desde:

- `LGA_NKS/LGA_NKS_ON_Clips_OFF_v00-Clips.py`
- `LGA_NKS/LGA_NKS_EXRTrack_Difference.py`
- `LGA_NKS/LGA_NKS_Compare_Versions.py`
- `LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`
- `LGA_NKS/LGA_NKS_RevealInExplorer.py`
- `LGA_NKS/LGA_NKS_RevealNKS_Project.py`
- `LGA_NKS/LGA_NKS_RevealNK_Script.py`
- `LGA_NKS/LGA_NKS_OpenInNukeX.py`
- `LGA_NKS/LGA_NKS_Clip_DisableEXR.py`

Tambien carga:

- `LGA_NKS_Edit/LGA_NKS_SelfReplaceClip.py`

Tambien usa shareds:

- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`

### 7. Projects Panel

Panel:

- `LGA_NKS_Projects_Panel.py`

Hoy carga scripts y recursos desde:

- `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py`
- `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py`
- `LGA_Projects_Panel/LGA_NKS_ProjectItem.py`
- `LGA_Projects_Panel/LGA_NKS_Workers.py`
- `LGA_Projects_Panel/LGA_NKS_UIManager.py`
- `LGA_Projects_Panel/LGA_NKS_ScanManager.py`
- `LGA_Projects_Panel/LGA_NKS_ProjectHandler.py`
- `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py`
- `LGA_Projects_Panel/*.svg`

Tambien usa shareds:

- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Projects_Panel.ini`

### 8. Color Panel

Panel:

- `LGA_NKS_Color_Panel.py`

Hoy usa shareds:

- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`

No depende de una carpeta privada propia.

### 9. FlowNo Panel

Panel:

- `LGA_NKS_FlowNo_Panel.py`

Problema actual:

- Intenta cargar `LGA_FPT-Hiero/LGA_FPT-Hiero_Push.py`
- Intenta cargar `LGA_FPT-Hiero/LGA_H-DeleteClipTags.py`

Esa carpeta no existe actualmente en el repo.

Conclusion:

- `LGA_NKS_FlowNo_Panel.py` esta referenciando nombres y ubicaciones legacy.

## Scripts compartidos detectados

### Shared generales

- `LGA_QtAdapter_HieroTools.py`
- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
- `LGA_NKS_Utils/LGA_NKS_GetClip.py`

### Shared de dominio Flow

- `LGA_NKS_Flow_NamingUtils.py`
- `LGA_NKS_Flow_Task_Config.py`
- `LGA_NKS_Flow_Users.json`
- `LGA_NKS_Flow/SecureConfig_Reader.py`

### Shared de acciones

- `LGA_NKS_Flow/LGA_NKS_Delete_ClipTags.py`
  - Usado por `Flow Panel`
  - Usado por `EditTools Panel`
  - `FlowNo Panel` intenta usar su variante legacy

- `LGA_NKS_Edit/LGA_NKS_SelfReplaceClip.py`
  - Usado por `EditTools Panel`
  - Usado por `Review Panel`

## Scripts privados de un solo panel

### Flow Panel

- `LGA_NKS_Flow/LGA_NKS_Flow_Pull.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Push.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`
- `LGA_NKS_Flow/LGA_NKS_ReviewPic.py`

### Flow Assignee Panel

- `LGA_NKS_Flow/LGA_NKS_Flow_Assignee.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Assign_Assignee.py`
- `LGA_NKS_Flow/LGA_NKS_Flow_Clear_Assignees.py`

### FlowProd Panel

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShowInFlow.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_Thumbs.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ModifyShot.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShotPriority.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_OpenPath.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Download.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Upload.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CheckTimelineShots.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_OpenPath.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_CreatePsync.py`
- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot_Folders.py`

### Viewer Panel

- `LGA_NKS_ViewerTL/LGA_NKS_Viewer_Mask.py`
- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py`
- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py`
- `LGA_NKS_ViewerTL/LGA_NKS_InOut_Editref.py`
- `LGA_NKS_ViewerTL/LGA_NKS_PrevNext_Rev.py`
- `LGA_NKS_ViewerTL/LGA_NKS_SnapShot.py`
- `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber.py`
- `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber_Create.py`

### EditTools Panel

- `LGA_NKS_Edit/LGA_NKS_ColorTransforms.py`
- `LGA_NKS_Edit/LGA_NKS_FixColorspaces.py`
- `LGA_NKS_Edit/LGA_NKS_CreateNewTrack.py`
- `LGA_NKS_Edit/LGA_NKS_OrganizeProject.py`
- `LGA_NKS_Edit/LGA_NKS_SetShotName.py`
- `LGA_NKS_Edit/LGA_NKS_Trim_In.py`
- `LGA_NKS_Edit/LGA_NKS_Trim_Out.py`
- `LGA_NKS_Edit/LGA_NKS_Reconnect.py`
- `LGA_NKS_Edit/LGA_NKS_CleanProject.py`
- `LGA_NKS_Edit/LGA_NKS_mediaMissingFrames.py`
- `LGA_NKS_Edit/LGA_NKS_MatchVerToEXR.py`
- `LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`
- `LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`

### Review Panel

- `LGA_NKS/LGA_NKS_ON_Clips_OFF_v00-Clips.py`
- `LGA_NKS/LGA_NKS_EXRTrack_Difference.py`
- `LGA_NKS/LGA_NKS_Compare_Versions.py`
- `LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`
- `LGA_NKS/LGA_NKS_RevealInExplorer.py`
- `LGA_NKS/LGA_NKS_RevealNKS_Project.py`
- `LGA_NKS/LGA_NKS_RevealNK_Script.py`
- `LGA_NKS/LGA_NKS_OpenInNukeX.py`
- `LGA_NKS/LGA_NKS_Clip_DisableEXR.py`

### Projects Panel

- `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py`
- `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py`
- `LGA_Projects_Panel/LGA_NKS_ProjectItem.py`
- `LGA_Projects_Panel/LGA_NKS_Workers.py`
- `LGA_Projects_Panel/LGA_NKS_UIManager.py`
- `LGA_Projects_Panel/LGA_NKS_ScanManager.py`
- `LGA_Projects_Panel/LGA_NKS_ProjectHandler.py`
- `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py`
- `LGA_Projects_Panel/*.svg`

## Problemas detectados

### Naming inconsistente entre panel y carpeta

- `LGA_NKS_Projects_Panel.py` usa carpeta `LGA_Projects_Panel/`
- `LGA_NKS_ViewerPanel.py` usa carpeta `LGA_NKS_ViewerTL/`
- `LGA_NKS_Flow_FlowProd_Panel.py` usa carpeta `LGA_NKS_Flow_Prod/`
- `LGA_NKS_Review_Panel.py` usa carpeta generica `LGA_NKS/`

### Carpetas que parecen privadas pero no lo son

- `LGA_NKS_Flow/` contiene privados del Flow Panel, privados del Assignee Panel y shareds de dominio Flow.
- `LGA_NKS_Edit/` contiene mayormente privados de EditTools, pero tambien `LGA_NKS_SelfReplaceClip.py` que lo usa Review.

### Legacy roto

- `LGA_NKS_FlowNo_Panel.py` referencia una carpeta inexistente: `LGA_FPT-Hiero/`

### Helpers internos que tambien hay que contemplar

- `LGA_NKS_Flow/LGA_NKS_Flow_Push_connector.py`
  - No lo llama un panel directo.
  - Lo usa `LGA_NKS_Flow/LGA_NKS_Flow_Push.py` del `Flow Panel`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot_Folders.py`
  - No lo llama un panel directo.
  - Lo usan:
    - `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py` del `FlowProd Panel`
    - `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ModifyShot.py` del `FlowProd Panel`

- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh.py`
  - No lo llama un panel directo.
  - Lo usa `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` del `Viewer Panel`.

- `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py`
  - No lo llama un panel directo.
  - Lo usan:
    - `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` del `Viewer Panel`
    - `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py` del `Projects Panel`

## Propuesta de reorganizacion

## Criterio de destino

- Carpeta privada del panel si lo usa un solo panel.
- Carpeta shared si lo usan varios paneles.
- Mantener paneles raiz visibles en `Startup/`.

### Estructura propuesta

```text
Startup/
  LGA_NKS_Flow_Panel.py
  LGA_NKS_Flow_Assignee_Panel.py
  LGA_NKS_Flow_FlowProd_Panel.py
  LGA_NKS_ViewerPanel.py
  LGA_NKS_EditTools_Panel.py
  LGA_NKS_Review_Panel.py
  LGA_NKS_Projects_Panel.py
  LGA_NKS_Color_Panel.py
  LGA_NKS_FlowNo_Panel.py

  LGA_NKS_Shared/
    LGA_QtAdapter_HieroTools.py
    LGA_NKS_StyleUtils.py
    LGA_NKS_GetClip.py

  LGA_NKS_Flow_Shared/
    LGA_NKS_Flow_NamingUtils.py
    LGA_NKS_Flow_Task_Config.py
    LGA_NKS_Flow_Users.json
    SecureConfig_Reader.py

  LGA_NKS_Flow_Panel_scripts/
    LGA_NKS_Flow_Pull.py
    LGA_NKS_Flow_Push.py
    LGA_NKS_Flow_Shot_info.py
    LGA_NKS_ReviewPic.py

  LGA_NKS_Flow_Assignee_Panel_scripts/
    LGA_NKS_Flow_Assignee.py
    LGA_NKS_Flow_Assign_Assignee.py
    LGA_NKS_Flow_Clear_Assignees.py

  LGA_NKS_Flow_FlowProd_Panel_scripts/
    LGA_NKS_Flow_ShowInFlow.py
    LGA_NKS_Flow_Thumbs.py
    LGA_NKS_Flow_CreateShot.py
    LGA_NKS_Flow_ModifyShot.py
    LGA_NKS_Flow_ShotPriority.py
    LGA_NKS_FileManager_OpenPath.py
    LGA_NKS_FileManager_Download.py
    LGA_NKS_FileManager_Upload.py
    LGA_NKS_Flow_CheckTimelineShots.py
    LGA_NKS_PipeSync_OpenPath.py
    LGA_NKS_PipeSync_CreatePsync.py
    LGA_NKS_Flow_CreateShot_Folders.py

  LGA_NKS_ViewerPanel_scripts/
    LGA_NKS_Viewer_Mask.py
    LGA_NKS_Timeline_Refresh_Wrap.py
    LGA_NKS_ScrollTo_TopTrack.py
    LGA_NKS_InOut_Editref.py
    LGA_NKS_PrevNext_Rev.py
    LGA_NKS_SnapShot.py
    LGA_NKS_FrameNumber.py
    LGA_NKS_FrameNumber_Create.py

  LGA_NKS_EditTools_Panel_scripts/
    LGA_NKS_ColorTransforms.py
    LGA_NKS_FixColorspaces.py
    LGA_NKS_CreateNewTrack.py
    LGA_NKS_OrganizeProject.py
    LGA_NKS_SetShotName.py
    LGA_NKS_Trim_In.py
    LGA_NKS_Trim_Out.py
    LGA_NKS_Reconnect.py
    LGA_NKS_CleanProject.py
    LGA_NKS_mediaMissingFrames.py
    LGA_NKS_MatchVerToEXR.py
    LGA_NKS_CompareVerToEditref.py
    LGA_NKS_CompareEXR_to_aPlate.py

  LGA_NKS_Review_Panel_scripts/
    LGA_NKS_ON_Clips_OFF_v00-Clips.py
    LGA_NKS_EXRTrack_Difference.py
    LGA_NKS_Compare_Versions.py
    LGA_NKS_Compare_Versions_OFF.py
    LGA_NKS_RevealInExplorer.py
    LGA_NKS_RevealNKS_Project.py
    LGA_NKS_RevealNK_Script.py
    LGA_NKS_OpenInNukeX.py
    LGA_NKS_Clip_DisableEXR.py

  LGA_NKS_SharedActions/
    LGA_NKS_Delete_ClipTags.py
    LGA_NKS_SelfReplaceClip.py

  LGA_NKS_Projects_Panel_scripts/
    LGA_Projects_Panel_ScanProjects.py
    LGA_Projects_Panel_SwitchSequence.py
    LGA_NKS_ProjectItem.py
    LGA_NKS_Workers.py
    LGA_NKS_UIManager.py
    LGA_NKS_ScanManager.py
    LGA_NKS_ProjectHandler.py
    LGA_NKS_Projects_Panel_Smart_Reload.py
    *.svg
```

## Notas de criterio

### Por que `LGA_NKS_Flow_Task_Config.py` va a shared

Porque no pertenece solo al Flow Panel:

- Lo usan tools del Assignee Panel.
- Lo usan tools del FlowProd Panel.

No deberia quedar en la carpeta privada de `Flow Panel`.

### Por que `LGA_NKS_Flow_Pull.py` y `LGA_NKS_Flow_Push.py` van a `Flow_Panel_scripts`

Porque hoy los invoca directamente solo `LGA_NKS_Flow_Panel.py`.

### Por que `LGA_NKS_Delete_ClipTags.py` no deberia quedar dentro de `LGA_NKS_Flow/`

Porque ya no es privado de Flow:

- Lo usa `Flow Panel`
- Lo usa `EditTools Panel`
- `FlowNo Panel` intenta usar su equivalente legacy

### Por que `LGA_NKS_SelfReplaceClip.py` no deberia quedar dentro de `LGA_NKS_Edit/`

Porque hoy ya no es privado de EditTools:

- Lo usa `EditTools Panel`
- Lo usa `Review Panel`

## Matriz archivo -> quien lo usa

Esta seccion agrega el nivel fino: para cada `.py` relevante se indica si lo llama un panel directo o si lo usa otro `.py`, indicando de que panel es ese `.py`.

### Shared de dominio Flow

- `LGA_NKS_Flow_Task_Config.py`
  - Lo usan:
    - `LGA_NKS_Flow/LGA_NKS_Flow_Assignee.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow/LGA_NKS_Flow_Assign_Assignee.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow/LGA_NKS_Flow_Clear_Assignees.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py` del `FlowProd Panel`

- `LGA_NKS_Flow_Users.json`
  - Lo usan:
    - `LGA_NKS_Flow_Assignee_Panel.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow/LGA_NKS_Flow_Assignee.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow/LGA_NKS_Flow_Assign_Assignee.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow/LGA_NKS_Flow_Clear_Assignees.py` del `Flow Assignee Panel`
    - `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyAssign.py` usado por `Flow Assignee Panel`
    - `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyUnassign.py` usado por `Flow Assignee Panel`

- `LGA_NKS_Flow/LGA_NKS_Flow_NamingUtils.py`
  - Lo usan:
    - `LGA_NKS_Flow_Panel.py` del `Flow Panel`
    - `LGA_NKS_Flow_Assignee_Panel.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow_FlowProd_Panel.py` del `FlowProd Panel`
    - `LGA_NKS_EditTools_Panel.py` del `EditTools Panel`
    - varios scripts de `LGA_NKS_Edit/`

- `LGA_NKS_Flow/SecureConfig_Reader.py`
  - Lo usan:
    - `LGA_NKS_ViewerPanel.py` del `Viewer Panel`
    - scripts de `LGA_NKS_Flow/`
    - scripts de `LGA_NKS_Wasabi/`

### Shared generales

- `LGA_QtAdapter_HieroTools.py`
  - Lo usan todos los paneles principales y la mayoria de los scripts auxiliares.

- `LGA_NKS_Utils/LGA_NKS_StyleUtils.py`
  - Lo usan:
    - `LGA_NKS_Color_Panel.py` del `Color Panel`
    - `LGA_NKS_Projects_Panel.py` del `Projects Panel`
    - `LGA_NKS_Review_Panel.py` del `Review Panel`
    - `LGA_NKS_ViewerPanel.py` del `Viewer Panel`
    - `LGA_NKS_Flow_Panel.py` del `Flow Panel`
    - `LGA_NKS_Flow_Assignee_Panel.py` del `Flow Assignee Panel`
    - `LGA_NKS_Flow_FlowProd_Panel.py` del `FlowProd Panel`
    - `LGA_NKS_EditTools_Panel.py` del `EditTools Panel`

- `LGA_NKS_Utils/LGA_NKS_GetClip.py`
  - Lo usan:
    - `LGA_NKS_Flow_Panel.py` del `Flow Panel`
    - `LGA_NKS_Flow_Assignee_Panel.py` del `Flow Assignee Panel`
    - varios scripts de `LGA_NKS_Edit/`
    - varios scripts de `LGA_NKS_Flow_Prod/`
    - algunos scripts de `LGA_NKS/`

### Shared actions

- `LGA_NKS_Flow/LGA_NKS_Delete_ClipTags.py`
  - Lo usan:
    - `LGA_NKS_Flow_Panel.py` del `Flow Panel`
    - `LGA_NKS_EditTools_Panel.py` del `EditTools Panel`
    - `LGA_NKS_FlowNo_Panel.py` lo intenta usar con nombre legacy

- `LGA_NKS_Edit/LGA_NKS_SelfReplaceClip.py`
  - Lo usan:
    - `LGA_NKS_EditTools_Panel.py` del `EditTools Panel`
    - `LGA_NKS_Review_Panel.py` del `Review Panel`

### Flow Panel

- `LGA_NKS_Flow/LGA_NKS_Flow_Pull.py`
  - Lo usa `LGA_NKS_Flow_Panel.py`.

- `LGA_NKS_Flow/LGA_NKS_Flow_Push.py`
  - Lo usa `LGA_NKS_Flow_Panel.py`.
  - A su vez usa `LGA_NKS_Flow/LGA_NKS_Flow_Push_connector.py`.

- `LGA_NKS_Flow/LGA_NKS_Flow_Push_connector.py`
  - Lo usa `LGA_NKS_Flow/LGA_NKS_Flow_Push.py` del `Flow Panel`.

- `LGA_NKS_Flow/LGA_NKS_Flow_Shot_info.py`
  - Lo usa `LGA_NKS_Flow_Panel.py`.

- `LGA_NKS_Flow/LGA_NKS_ReviewPic.py`
  - Lo usa `LGA_NKS_Flow_Panel.py`.

### Flow Assignee Panel

- `LGA_NKS_Flow/LGA_NKS_Flow_Assignee.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

- `LGA_NKS_Flow/LGA_NKS_Flow_Assign_Assignee.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

- `LGA_NKS_Flow/LGA_NKS_Flow_Clear_Assignees.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyAssign.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyUnassign.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

- `LGA_NKS_Wasabi/LGA_NKS_Wasabi_PolicyUnassign_CompletedShots.py`
  - Lo usa `LGA_NKS_Flow_Assignee_Panel.py`.

### FlowProd Panel

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShowInFlow.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_Thumbs.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.
  - A su vez usa `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot_Folders.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ModifyShot.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.
  - A su vez usa `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot_Folders.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot_Folders.py`
  - Lo usan:
    - `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CreateShot.py` del `FlowProd Panel`
    - `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ModifyShot.py` del `FlowProd Panel`

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_ShotPriority.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_OpenPath.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Download.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_FileManager_Upload.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_Flow_CheckTimelineShots.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_OpenPath.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

- `LGA_NKS_Flow_Prod/LGA_NKS_PipeSync_CreatePsync.py`
  - Lo usa `LGA_NKS_Flow_FlowProd_Panel.py`.

### Viewer Panel

- `LGA_NKS_ViewerTL/LGA_NKS_Viewer_Mask.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.
  - A su vez usa:
    - `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh.py`
    - `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py`

- `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh.py`
  - Lo usa `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` del `Viewer Panel`.

- `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py`
  - Lo usan:
    - `LGA_NKS_ViewerTL/LGA_NKS_Timeline_Refresh_Wrap.py` del `Viewer Panel`
    - `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py` del `Projects Panel`

- `LGA_NKS_ViewerTL/LGA_NKS_ScrollTo_TopTrack.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_InOut_Editref.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_PrevNext_Rev.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_SnapShot.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber.py`
  - Lo usa `LGA_NKS_ViewerPanel.py`.
  - A su vez usa `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber_Create.py`.

- `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber_Create.py`
  - Lo usa `LGA_NKS_ViewerTL/LGA_NKS_FrameNumber.py` del `Viewer Panel`.

### EditTools Panel

- `LGA_NKS_Edit/LGA_NKS_ColorTransforms.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_FixColorspaces.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_CreateNewTrack.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_OrganizeProject.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_SetShotName.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_Trim_In.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_Trim_Out.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_Reconnect.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_CleanProject.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_mediaMissingFrames.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_MatchVerToEXR.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_CompareVerToEditref.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

- `LGA_NKS_Edit/LGA_NKS_CompareEXR_to_aPlate.py`
  - Lo usa `LGA_NKS_EditTools_Panel.py`.

### Review Panel

- `LGA_NKS/LGA_NKS_ON_Clips_OFF_v00-Clips.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_EXRTrack_Difference.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_Compare_Versions.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_Compare_Versions_OFF.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_RevealInExplorer.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_RevealNKS_Project.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_RevealNK_Script.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_OpenInNukeX.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

- `LGA_NKS/LGA_NKS_Clip_DisableEXR.py`
  - Lo usa `LGA_NKS_Review_Panel.py`.

### Projects Panel

- `LGA_Projects_Panel/LGA_Projects_Panel_ScanProjects.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_Projects_Panel_SwitchSequence.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.
  - A su vez usa `LGA_NKS_ViewerTL/LGA_NKS_Reduce_SeqWin.py`.

- `LGA_Projects_Panel/LGA_NKS_ProjectItem.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_NKS_Workers.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_NKS_UIManager.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_NKS_ScanManager.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_NKS_ProjectHandler.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

- `LGA_Projects_Panel/LGA_NKS_Projects_Panel_Smart_Reload.py`
  - Lo usa `LGA_NKS_Projects_Panel.py`.

## Prioridad sugerida para implementar despues

1. Resolver el legacy roto de `LGA_NKS_FlowNo_Panel.py`
2. Separar shareds reales de `LGA_NKS_Flow/`
3. Renombrar carpetas privadas para que coincidan con el panel
4. Separar `LGA_NKS/` en `Review_Panel_scripts` y `SharedActions`
5. Mover `StyleUtils`, `GetClip` y `QtAdapter` a una carpeta shared unica

## Regla para ejecucion

Todos los movimientos y renombres deberian hacerse con:

```bash
git mv origen destino
```

Y luego actualizar imports y rutas en los paneles.
