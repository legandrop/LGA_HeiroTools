"""
_______________________________________________________

  LGA_NKS_Delete_ClipTags v1.1 | Lega
  Usado por runtime activo:
  - LGA_NKS_Edit_Panel.py
  - LGA_NKS_Flow_Panel.py
  Borra los tags del clip seleccionado
_______________________________________________________

"""

import hiero.core
import hiero.ui

def delete_tags_from_clip(clip):
    tags = clip.tags()
    if tags:
        for tag in list(tags):  # Usa list(tags) para evitar modificar la lista mientras se itera
            clip.removeTag(tag)
        #print(f"All tags removed from clip: {clip.name()}")

