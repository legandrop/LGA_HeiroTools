"""
________________________________________________________________
  LGA_NKS_Flow_GetUserProjects v1.1 | Lega
  Script temporal para obtener, desasignar y asignar proyectos a un usuario en Flow
  Mide el tiempo de cada operación para optimización
  Se ejecuta desde el Script Editor de Hiero
________________________________________________________________
"""

import os
import sys
import shotgun_api3
import time
from datetime import datetime

# Agregar la ruta de LGA_NKS_Flow al sys.path para importar SecureConfig_Reader
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Subir un nivel desde +Building_Blocks
flow_dir = os.path.join(parent_dir, "LGA_NKS_Flow")
sys.path.insert(0, flow_dir)

from SecureConfig_Reader import get_flow_credentials

# Variable global para debug
DEBUG = True


def get_timestamp():
    """Retorna un timestamp formateado para los logs"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def debug_print(message):
    if DEBUG:
        print(f"[{get_timestamp()}] {message}")


def get_user_projects(user_name):
    """
    Obtiene los proyectos asignados a un usuario en Flow Production Tracking.
    
    Args:
        user_name (str): Nombre del usuario en Flow
        
    Returns:
        list: Lista de proyectos asignados al usuario
    """
    debug_print(f"=== Iniciando obtención de proyectos para usuario: {user_name} ===")
    
    # Obtener credenciales de Flow
    sg_url, sg_login, sg_password = get_flow_credentials()
    if not all([sg_url, sg_login, sg_password]):
        print("ERROR: No se pudieron obtener las credenciales de Flow desde SecureConfig.")
        return []
    
    debug_print(f"Conectando a Flow: {sg_url}")
    
    try:
        # Conectar a ShotGrid/Flow
        sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)
        debug_print("Conexión a Flow establecida exitosamente")
        
        # Buscar el usuario por nombre
        debug_print(f"Buscando usuario: {user_name}")
        users = sg.find(
            "HumanUser",
            [["name", "is", user_name]],
            ["id", "name", "projects"]
        )
        
        if not users:
            print(f"ERROR: No se encontró el usuario '{user_name}' en Flow.")
            return []
        
        user = users[0]
        debug_print(f"Usuario encontrado: {user['name']} (ID: {user['id']})")
        
        # Obtener los proyectos asignados
        # El campo 'projects' puede ser una lista de referencias a proyectos
        projects = user.get("projects", [])
        
        if not projects:
            print(f"El usuario '{user_name}' no tiene proyectos asignados.")
            return []
        
        debug_print(f"Encontrados {len(projects)} proyecto(s) asignado(s)")
        
        # Obtener información detallada de cada proyecto
        project_list = []
        for project_ref in projects:
            # project_ref es un diccionario con 'type' y 'id'
            project_id = project_ref.get("id")
            if project_id:
                # Obtener información completa del proyecto
                project = sg.find_one(
                    "Project",
                    [["id", "is", project_id]],
                    ["id", "name", "code"]
                )
                if project:
                    project_info = {
                        "id": project["id"],
                        "name": project.get("name", "Sin nombre"),
                        "code": project.get("code", "Sin código")
                    }
                    project_list.append(project_info)
                    debug_print(f"  - Proyecto: {project_info['name']} (ID: {project_info['id']}, Code: {project_info['code']})")
        
        return project_list
        
    except Exception as e:
        print(f"ERROR al obtener proyectos del usuario: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return []


def unassign_project_from_user(user_name, project_name):
    """
    Desasigna un proyecto de un usuario en Flow Production Tracking.
    Mide el tiempo de cada operación.
    
    Args:
        user_name (str): Nombre del usuario en Flow
        project_name (str): Nombre del proyecto a desasignar
        
    Returns:
        tuple: (bool, str) - (True si se desasignó exitosamente, mensaje)
    """
    start_total = time.time()
    debug_print(f"=== Iniciando desasignación de proyecto ===")
    debug_print(f"Usuario: {user_name}")
    debug_print(f"Proyecto: {project_name}")
    
    # Obtener credenciales de Flow
    start_credentials = time.time()
    sg_url, sg_login, sg_password = get_flow_credentials()
    time_credentials = time.time() - start_credentials
    debug_print(f"[{time_credentials*1000:.2f}ms] Obtención de credenciales")
    
    if not all([sg_url, sg_login, sg_password]):
        return False, "ERROR: No se pudieron obtener las credenciales de Flow desde SecureConfig."
    
    try:
        # Conectar a ShotGrid/Flow
        start_connection = time.time()
        sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)
        time_connection = time.time() - start_connection
        debug_print(f"[{time_connection*1000:.2f}ms] Conexión a Flow establecida")
        
        # Buscar el usuario
        start_user_search = time.time()
        users = sg.find(
            "HumanUser",
            [["name", "is", user_name]],
            ["id", "name", "projects"]
        )
        time_user_search = time.time() - start_user_search
        debug_print(f"[{time_user_search*1000:.2f}ms] Búsqueda de usuario completada")
        
        if not users:
            return False, f"ERROR: No se encontró el usuario '{user_name}' en Flow."
        
        user = users[0]
        user_id = user["id"]
        debug_print(f"Usuario encontrado: {user['name']} (ID: {user_id})")
        
        # Buscar el proyecto
        start_project_search = time.time()
        projects = sg.find(
            "Project",
            [["name", "is", project_name]],
            ["id", "name"]
        )
        time_project_search = time.time() - start_project_search
        debug_print(f"[{time_project_search*1000:.2f}ms] Búsqueda de proyecto completada")
        
        if not projects:
            return False, f"ERROR: No se encontró el proyecto '{project_name}' en Flow."
        
        project = projects[0]
        project_id = project["id"]
        debug_print(f"Proyecto encontrado: {project['name']} (ID: {project_id})")
        
        # Obtener proyectos actuales del usuario
        current_projects = user.get("projects", [])
        debug_print(f"Proyectos actuales del usuario: {len(current_projects)}")
        
        # Verificar si el proyecto está asignado
        project_found = False
        new_projects = []
        for proj_ref in current_projects:
            if proj_ref.get("id") == project_id:
                project_found = True
                debug_print(f"Proyecto '{project_name}' encontrado en la lista del usuario")
            else:
                new_projects.append(proj_ref)
        
        if not project_found:
            return False, f"El proyecto '{project_name}' no está asignado al usuario '{user_name}'."
        
        # Actualizar el usuario removiendo el proyecto
        start_update = time.time()
        result = sg.update("HumanUser", user_id, {"projects": new_projects})
        time_update = time.time() - start_update
        debug_print(f"[{time_update*1000:.2f}ms] Actualización de usuario completada")
        
        if result:
            time_total = time.time() - start_total
            debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Desasignación exitosa")
            return True, f"Proyecto '{project_name}' desasignado exitosamente del usuario '{user_name}'."
        else:
            return False, "ERROR: No se pudo actualizar el usuario en Flow."
        
    except Exception as e:
        print(f"ERROR al desasignar proyecto: {e}")
        import traceback
        debug_print(traceback.format_exc())
        time_total = time.time() - start_total
        debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Error")
        return False, f"ERROR: {str(e)}"


def assign_project_to_user(user_name, project_name):
    """
    Asigna un proyecto a un usuario en Flow Production Tracking.
    Mide el tiempo de cada operación.
    
    Args:
        user_name (str): Nombre del usuario en Flow
        project_name (str): Nombre del proyecto a asignar
        
    Returns:
        tuple: (bool, str) - (True si se asignó exitosamente, mensaje)
    """
    start_total = time.time()
    debug_print(f"=== Iniciando asignación de proyecto ===")
    debug_print(f"Usuario: {user_name}")
    debug_print(f"Proyecto: {project_name}")
    
    # Obtener credenciales de Flow
    start_credentials = time.time()
    sg_url, sg_login, sg_password = get_flow_credentials()
    time_credentials = time.time() - start_credentials
    debug_print(f"[{time_credentials*1000:.2f}ms] Obtención de credenciales")
    
    if not all([sg_url, sg_login, sg_password]):
        return False, "ERROR: No se pudieron obtener las credenciales de Flow desde SecureConfig."
    
    try:
        # Conectar a ShotGrid/Flow
        start_connection = time.time()
        sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)
        time_connection = time.time() - start_connection
        debug_print(f"[{time_connection*1000:.2f}ms] Conexión a Flow establecida")
        
        # Buscar el usuario
        start_user_search = time.time()
        users = sg.find(
            "HumanUser",
            [["name", "is", user_name]],
            ["id", "name", "projects"]
        )
        time_user_search = time.time() - start_user_search
        debug_print(f"[{time_user_search*1000:.2f}ms] Búsqueda de usuario completada")
        
        if not users:
            return False, f"ERROR: No se encontró el usuario '{user_name}' en Flow."
        
        user = users[0]
        user_id = user["id"]
        debug_print(f"Usuario encontrado: {user['name']} (ID: {user_id})")
        
        # Buscar el proyecto
        start_project_search = time.time()
        projects = sg.find(
            "Project",
            [["name", "is", project_name]],
            ["id", "name"]
        )
        time_project_search = time.time() - start_project_search
        debug_print(f"[{time_project_search*1000:.2f}ms] Búsqueda de proyecto completada")
        
        if not projects:
            return False, f"ERROR: No se encontró el proyecto '{project_name}' en Flow."
        
        project = projects[0]
        project_id = project["id"]
        debug_print(f"Proyecto encontrado: {project['name']} (ID: {project_id})")
        
        # Obtener proyectos actuales del usuario
        current_projects = user.get("projects", [])
        debug_print(f"Proyectos actuales del usuario: {len(current_projects)}")
        
        # Verificar si el proyecto ya está asignado
        project_already_assigned = False
        for proj_ref in current_projects:
            if proj_ref.get("id") == project_id:
                project_already_assigned = True
                debug_print(f"El proyecto '{project_name}' ya está asignado al usuario")
                break
        
        if project_already_assigned:
            return False, f"El proyecto '{project_name}' ya está asignado al usuario '{user_name}'."
        
        # Agregar el proyecto a la lista
        new_project_ref = {"type": "Project", "id": project_id}
        new_projects = current_projects + [new_project_ref]
        
        # Actualizar el usuario agregando el proyecto
        start_update = time.time()
        result = sg.update("HumanUser", user_id, {"projects": new_projects})
        time_update = time.time() - start_update
        debug_print(f"[{time_update*1000:.2f}ms] Actualización de usuario completada")
        
        if result:
            time_total = time.time() - start_total
            debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Asignación exitosa")
            return True, f"Proyecto '{project_name}' asignado exitosamente al usuario '{user_name}'."
        else:
            return False, "ERROR: No se pudo actualizar el usuario en Flow."
        
    except Exception as e:
        print(f"ERROR al asignar proyecto: {e}")
        import traceback
        debug_print(traceback.format_exc())
        time_total = time.time() - start_total
        debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Error")
        return False, f"ERROR: {str(e)}"


def main():
    """Función principal que se ejecuta desde el Script Editor"""
    user_name = "Lega Pugliese"
    project_name = "EE"
    
    print(f"\n{'='*70}")
    print(f"PRUEBA DE DESASIGNACIÓN Y ASIGNACIÓN DE PROYECTO")
    print(f"{'='*70}")
    print(f"Usuario: {user_name}")
    print(f"Proyecto: {project_name}")
    print(f"{'='*70}\n")
    
    # Paso 1: Desasignar el proyecto
    print(f"\n{'='*70}")
    print(f"PASO 1: DESASIGNAR PROYECTO")
    print(f"{'='*70}\n")
    start_unassign = time.time()
    success_unassign, message_unassign = unassign_project_from_user(user_name, project_name)
    time_unassign = time.time() - start_unassign
    
    if success_unassign:
        print(f"✓ {message_unassign}")
    else:
        print(f"✗ {message_unassign}")
    print(f"Tiempo total de desasignación: {time_unassign*1000:.2f}ms ({time_unassign:.3f}s)")
    
    # Paso 2: Asignar el proyecto de nuevo
    print(f"\n{'='*70}")
    print(f"PASO 2: ASIGNAR PROYECTO")
    print(f"{'='*70}\n")
    start_assign = time.time()
    success_assign, message_assign = assign_project_to_user(user_name, project_name)
    time_assign = time.time() - start_assign
    
    if success_assign:
        print(f"✓ {message_assign}")
    else:
        print(f"✗ {message_assign}")
    print(f"Tiempo total de asignación: {time_assign*1000:.2f}ms ({time_assign:.3f}s)")
    
    # Resumen final
    print(f"\n{'='*70}")
    print(f"RESUMEN")
    print(f"{'='*70}")
    print(f"Desasignación: {time_unassign*1000:.2f}ms ({time_unassign:.3f}s)")
    print(f"Asignación:    {time_assign*1000:.2f}ms ({time_assign:.3f}s)")
    print(f"Total:         {(time_unassign + time_assign)*1000:.2f}ms ({(time_unassign + time_assign):.3f}s)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

