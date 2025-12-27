"""
Módulo de Escaneo de Proyectos - Panel de Proyectos LGA
========================================================

Este módulo contiene funciones reutilizables para:
- Escanear proyectos en disco T:
- Obtener información de proyectos abiertos en Hiero
- Verificar si un proyecto está abierto
- Obtener secuencias de un proyecto

IMPORTANTE: Este módulo usa LGA_QtAdapter_HieroTools para compatibilidad Nuke 15/16
"""

import hiero.core
import hiero.ui
import os
import glob
import re
import sys
from pathlib import Path

# Importar funciones de manejo de versiones desde código existente
lga_nks_path = None
for path_str in sys.path:
    try:
        path = Path(path_str)
        test_file = path / "LGA_NKS_CheckProjectVersions.py"
        if test_file.exists():
            lga_nks_path = path
            break
        if path.parent.exists():
            test_file_parent = path.parent / "LGA_NKS_CheckProjectVersions.py"
            if test_file_parent.exists():
                lga_nks_path = path.parent
                break
        if path.exists() and (path / "LGA_NKS" / "LGA_NKS_CheckProjectVersions.py").exists():
            lga_nks_path = path / "LGA_NKS"
            break
    except Exception:
        continue

if lga_nks_path is None or not lga_nks_path.exists():
    if '__file__' in globals() and __file__:
        try:
            script_dir = Path(__file__).resolve().parent
            potential_startup = script_dir.parent
            potential_lga_nks = potential_startup / "LGA_NKS"
            if (potential_lga_nks / "LGA_NKS_CheckProjectVersions.py").exists():
                lga_nks_path = potential_lga_nks
        except Exception:
            pass

if lga_nks_path is None or not lga_nks_path.exists():
    standard_paths = [
        Path.home() / ".nuke" / "Python" / "Startup" / "LGA_NKS",
        Path(os.path.expanduser("~")) / ".nuke" / "Python" / "Startup" / "LGA_NKS",
    ]
    for test_path in standard_paths:
        if (test_path / "LGA_NKS_CheckProjectVersions.py").exists():
            lga_nks_path = test_path
            break

if lga_nks_path and lga_nks_path.exists():
    if str(lga_nks_path) not in sys.path:
        sys.path.insert(0, str(lga_nks_path))

try:
    from LGA_NKS_CheckProjectVersions import (
        extraer_version,
        comparar_versiones,
        encontrar_version_mas_alta,
        obtener_nombre_base_proyecto,
    )
except ImportError as e:
    raise ImportError(f"No se pudo importar funciones de LGA_NKS_CheckProjectVersions: {e}")


def scan_projects_on_disk(base_path="T:\\"):
    """
    Escanea el disco buscando proyectos VFX y retorna información de cada uno.
    
    Busca carpetas que empiecen con 'VFX-' y dentro busca carpetas '*_SUP'.
    En cada carpeta SUP encuentra el archivo .hrox con la versión más alta.
    
    Args:
        base_path (str): Ruta base donde buscar proyectos (default: "T:\\")
        
    Returns:
        list: Lista de diccionarios con información de proyectos encontrados.
              Cada diccionario contiene:
              - nombre_base (str): Nombre base del proyecto (ej: "BRDA_SUP")
              - vfx_folder (str): Nombre de la carpeta VFX (ej: "VFX-BRDA")
              - sup_folder (str): Nombre de la carpeta SUP (ej: "BRDA_SUP")
              - ruta_hrox (str): Ruta completa del archivo .hrox con versión más alta
              - version (str): Versión extraída (ej: "v050")
              - ruta_proyecto (str): Ruta completa de la carpeta SUP
    """
    proyectos_encontrados = []
    
    if not os.path.exists(base_path):
        return proyectos_encontrados
    
    try:
        # Buscar carpetas que empiecen con VFX-
        items = os.listdir(base_path)
        vfx_folders = [
            item 
            for item in items 
            if os.path.isdir(os.path.join(base_path, item)) and item.startswith("VFX-")
        ]
        
        for vfx_folder in sorted(vfx_folders):
            vfx_path = os.path.join(base_path, vfx_folder)
            
            try:
                # Buscar carpetas que terminen con _SUP
                subitems = os.listdir(vfx_path)
                sup_folders = [
                    item
                    for item in subitems
                    if os.path.isdir(os.path.join(vfx_path, item)) and item.endswith("_SUP")
                ]
                
                for sup_folder in sup_folders:
                    sup_path = os.path.join(vfx_path, sup_folder)
                    
                    # Buscar archivos .hrox en la carpeta SUP
                    hrox_pattern = os.path.join(sup_path, "*.hrox")
                    hrox_files = glob.glob(hrox_pattern)
                    
                    if not hrox_files:
                        continue
                    
                    # Encontrar la versión más alta
                    if len(hrox_files) > 1:
                        # Usar el primer archivo como referencia
                        ruta_referencia = hrox_files[0]
                        version_mas_alta = encontrar_version_mas_alta(ruta_referencia)
                        
                        if version_mas_alta not in ["No detectada", "Error", "No disponible", "No hay otras versiones"]:
                            nombre_base = obtener_nombre_base_proyecto(version_mas_alta)
                            version = extraer_version(version_mas_alta)
                            
                            proyectos_encontrados.append({
                                "nombre_base": nombre_base if nombre_base else sup_folder,
                                "vfx_folder": vfx_folder,
                                "sup_folder": sup_folder,
                                "ruta_hrox": version_mas_alta,
                                "version": version,
                                "ruta_proyecto": sup_path,
                            })
                    elif len(hrox_files) == 1:
                        # Solo hay un archivo
                        hrox_file = hrox_files[0]
                        nombre_base = obtener_nombre_base_proyecto(hrox_file)
                        version = extraer_version(hrox_file)
                        
                        proyectos_encontrados.append({
                            "nombre_base": nombre_base if nombre_base else sup_folder,
                            "vfx_folder": vfx_folder,
                            "sup_folder": sup_folder,
                            "ruta_hrox": hrox_file,
                            "version": version,
                            "ruta_proyecto": sup_path,
                        })
                        
            except PermissionError:
                # Ignorar carpetas sin permisos
                continue
            except Exception:
                # Ignorar errores en carpetas individuales
                continue
                
    except Exception:
        # Retornar lista vacía si hay error general
        pass
    
    return proyectos_encontrados


def get_open_projects_info():
    """
    Obtiene información de todos los proyectos abiertos en Hiero.
    
    Agrupa proyectos por nombre base y extrae información de versión.
    
    Returns:
        dict: Diccionario agrupado por nombre base. Cada entrada contiene:
              nombre_base: [
                  {
                      "proyecto": proyecto_obj,
                      "ruta": str,
                      "version_num": int,
                      "version_str": str,
                      "nombre": str
                  },
                  ...
              ]
    """
    proyectos_abiertos_por_base = {}
    
    proyectos = hiero.core.projects()
    if not proyectos:
        return proyectos_abiertos_por_base
    
    for proyecto in proyectos:
        try:
            ruta_disco = proyecto.path()
            nombre_base = obtener_nombre_base_proyecto(ruta_disco)
            
            if nombre_base:
                if nombre_base not in proyectos_abiertos_por_base:
                    proyectos_abiertos_por_base[nombre_base] = []
                
                version_num = -1
                version_str = extraer_version(ruta_disco)
                if version_str not in ["No detectada", "Error"]:
                    match = re.search(r"v?(\d+)", version_str)
                    if match:
                        version_num = int(match.group(1))
                
                proyectos_abiertos_por_base[nombre_base].append({
                    "proyecto": proyecto,
                    "ruta": ruta_disco,
                    "version_num": version_num,
                    "version_str": version_str,
                    "nombre": proyecto.name(),
                })
        except Exception:
            # Ignorar proyectos con errores
            continue
    
    return proyectos_abiertos_por_base


def is_project_open(ruta_hrox, proyectos_abiertos_info):
    """
    Verifica si un proyecto (por su ruta .hrox) ya está abierto en Hiero.
    
    Compara por nombre base + número de versión.
    
    Args:
        ruta_hrox (str): Ruta completa del archivo .hrox del proyecto
        proyectos_abiertos_info (dict): Diccionario retornado por get_open_projects_info()
        
    Returns:
        bool: True si el proyecto está abierto, False si no
    """
    if not ruta_hrox or not os.path.exists(ruta_hrox):
        return False
    
    nombre_base = obtener_nombre_base_proyecto(ruta_hrox)
    if not nombre_base:
        return False
    
    version_str = extraer_version(ruta_hrox)
    if version_str in ["No detectada", "Error"]:
        return False
    
    match = re.search(r"v?(\d+)", version_str)
    if not match:
        return False
    
    version_num = int(match.group(1))
    
    # Verificar si hay un proyecto abierto con el mismo nombre base y versión
    if nombre_base in proyectos_abiertos_info:
        for proyecto_abierto in proyectos_abiertos_info[nombre_base]:
            if proyecto_abierto["version_num"] == version_num:
                return True
    
    return False


def get_project_sequences(proyecto):
    """
    Obtiene lista de nombres de secuencias de un proyecto.
    
    Args:
        proyecto: Objeto proyecto de Hiero (hiero.core.Project)
        
    Returns:
        list: Lista de nombres de secuencias (strings)
    """
    sequences_names = []
    
    try:
        sequences = proyecto.sequences()
        sequences_names = [seq.name() for seq in sequences if hasattr(seq, 'name')]
    except Exception:
        # Retornar lista vacía si hay error
        pass
    
    return sequences_names

