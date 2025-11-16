"""
____________________________________________________________________________________

  LGA_NKS_Flow_NamingUtils v1.0 | Lega
  Utilidades para detectar y extraer información de nombres de archivos/shots
  Compatible con ambos sistemas de nomenclatura:
  - PROYECTO_SEQ_SHOT_DESC1_DESC2 (5 bloques con descripción)
  - PROYECTO_SEQ_SHOT (3 bloques simplificado)
  
  Scripts que utilizan este módulo:
  - LGA_NKS_Flow_Push.py
  - LGA_NKS_Flow_Push_connector.py
  - LGA_NKS_Flow_Pull.py
  - LGA_NKS_Flow_Thumbs.py
  - LGA_NKS_Flow_CreateShot_Thumbs.py
  - LGA_NKS_Flow_Shot_info.py
  - LGA_NKS_Flow_CreateShot.py
  - LGA_NKS_Flow_Panel.py
  - LGA_NKS_Flow_Assign_Assignee.py
  - LGA_NKS_Flow_Assignee.py
  - LGA_NKS_Flow_Clear_Assignees.py
  - LGA_NKS_CompareEXR_to_aPlate.py
  - LGA_NKS_CompareVerToEditref.py
  - LGA_NKS_MatchVerToEXR.py
____________________________________________________________________________________
"""

import re
import os


def detect_shotname_format(base_name):
    """
    Detecta el formato del shotname basado en el nombre base del archivo.
    
    Técnica de detección por Campo 5:
    - Si el campo 5 (índice 4) empieza con 'v' seguido de números → formato simplificado (3 bloques)
    - Si no → formato con descripción (5 bloques)
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        bool: True si es formato con descripción (5 bloques), False si es simplificado (3 bloques)
    """
    if not base_name:
        return False  # Por defecto, formato simplificado
    
    parts = base_name.split("_")
    
    # Verificar si el campo 5 (índice 4) es una versión
    if len(parts) >= 5:
        field_5 = parts[4]
        # Si campo 5 empieza con 'v' seguido de números, es formato simplificado
        if field_5.startswith('v') and len(field_5) > 1 and field_5[1:].isdigit():
            return False  # Formato simplificado (3 bloques)
        else:
            return True  # Formato con descripción (5 bloques)
    else:
        # Menos de 5 campos → formato simplificado
        return False


def extract_shot_code(base_name):
    """
    Extrae el shot_code de un nombre base de archivo.
    Detecta automáticamente el formato y extrae el shot_code correcto.
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        str: Shot code extraído (PROYECTO_SEQ_SHOT o PROYECTO_SEQ_SHOT_DESC1_DESC2)
    """
    if not base_name:
        return ""
    
    parts = base_name.split("_")
    
    # Detectar formato
    has_description = detect_shotname_format(base_name)
    
    if has_description:
        # Formato con descripción: tomar primeros 5 campos
        if len(parts) >= 5:
            shot_code = "_".join(parts[:5])
        else:
            # Fallback: usar todos los campos disponibles
            shot_code = "_".join(parts)
    else:
        # Formato simplificado: tomar primeros 3 campos
        if len(parts) >= 3:
            shot_code = "_".join(parts[:3])
        else:
            # Fallback: usar todos los campos disponibles
            shot_code = "_".join(parts)
    
    return shot_code


def extract_project_name(base_name):
    """
    Extrae el nombre del proyecto del nombre base del archivo.
    
    Args:
        base_name (str): Nombre base del archivo
        
    Returns:
        str: Nombre del proyecto (primer campo)
    """
    if not base_name:
        return ""
    
    parts = base_name.split("_")
    return parts[0] if parts else ""


def clean_base_name(file_name):
    """
    Limpia el nombre de archivo removiendo extensiones y versiones.
    
    Args:
        file_name (str): Nombre completo del archivo
        
    Returns:
        str: Nombre base limpio sin extensión ni versión
    """
    if not file_name:
        return ""
    
    # Remover extensión de secuencia EXR
    base_name = re.sub(r"_%04d\.exr$", "", file_name)
    base_name = re.sub(r"_\d{4}\.exr$", "", base_name)  # También formato sin %04d
    
    # Remover versión al final (_v19, _v001, etc.)
    base_name = re.sub(r"_v\d+$", "", base_name)
    
    # Remover extensión común
    base_name = os.path.splitext(base_name)[0]
    
    return base_name


def extract_task_name(base_name):
    """
    Extrae el nombre de la tarea del nombre base del archivo.
    
    Args:
        base_name (str): Nombre base del archivo sin extensión ni versión
        
    Returns:
        str: Nombre de la tarea o None si no se encuentra
    """
    if not base_name:
        return None
    
    parts = base_name.split("_")
    
    # Detectar formato
    has_description = detect_shotname_format(base_name)
    
    if has_description:
        # Formato con descripción: task está en el campo 6 (índice 5)
        # Estructura: PROYECTO_SEQ_SHOT_DESC1_DESC2_TASK_vVERSION
        if len(parts) >= 6:
            return parts[5]
    else:
        # Formato simplificado: task está en el campo 4 (índice 3)
        # Estructura: PROYECTO_SEQ_SHOT_TASK_vVERSION
        if len(parts) >= 4:
            return parts[3]
    
    return None

