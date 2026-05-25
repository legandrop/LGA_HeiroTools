"""
________________________________________________________________
  LGA_NKS_Flow_CheckUserProject v1.0 | Lega
  Script temporal para verificar si un usuario tiene asignado un proyecto específico en Flow
  Mide el tiempo de cada operación para optimización
  Se ejecuta desde el Script Editor de Hiero
________________________________________________________________
"""

import os
import sys
import shotgun_api3
import time
from datetime import datetime

# Agregar la ruta actual al sys.path para importar SecureConfig_Reader
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from SecureConfig_Reader import get_flow_credentials

# Variable global para debug
DEBUG = False


def get_timestamp():
    """Retorna un timestamp formateado para los logs"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def debug_print(message):
    if DEBUG:
        print(f"[{get_timestamp()}] {message}")


def check_user_has_project(user_name, project_name):
    """
    Verifica si un usuario tiene asignado un proyecto específico en Flow Production Tracking.
    Mide el tiempo de cada operación.

    Args:
        user_name (str): Nombre del usuario en Flow
        project_name (str): Nombre del proyecto a verificar

    Returns:
        tuple: (bool, dict) - (True si tiene el proyecto asignado, información del proyecto)
    """
    start_total = time.time()
    debug_print(f"=== Iniciando verificación de proyecto para usuario: {user_name} ===")
    debug_print(f"Proyecto a verificar: {project_name}")

    # Obtener credenciales de Flow
    start_credentials = time.time()
    sg_url, sg_login, sg_password = get_flow_credentials()
    time_credentials = time.time() - start_credentials
    debug_print(f"[{time_credentials*1000:.2f}ms] Obtención de credenciales")

    if not all([sg_url, sg_login, sg_password]):
        print(
            f"ERROR: No se pudieron obtener las credenciales de Flow desde SecureConfig."
        )
        return False, None

    debug_print(f"Conectando a Flow: {sg_url}")

    try:
        # Conectar a ShotGrid/Flow
        start_connection = time.time()
        sg = shotgun_api3.Shotgun(sg_url, login=sg_login, password=sg_password)
        time_connection = time.time() - start_connection
        debug_print(f"[{time_connection*1000:.2f}ms] Conexión a Flow establecida")

        # Buscar el usuario por nombre
        start_user_search = time.time()
        debug_print(f"Buscando usuario: {user_name}")
        users = sg.find(
            "HumanUser", [["name", "is", user_name]], ["id", "name", "projects"]
        )
        time_user_search = time.time() - start_user_search
        debug_print(f"[{time_user_search*1000:.2f}ms] Búsqueda de usuario completada")

        if not users:
            print(f"ERROR: No se encontró el usuario '{user_name}' en Flow.")
            return False, None

        user = users[0]
        debug_print(f"Usuario encontrado: {user['name']} (ID: {user['id']})")

        # Obtener los proyectos asignados
        projects = user.get("projects", [])
        debug_print(f"Proyectos asignados encontrados: {len(projects)}")

        if not projects:
            debug_print(f"El usuario '{user_name}' no tiene proyectos asignados.")
            time_total = time.time() - start_total
            debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Usuario sin proyectos")
            return False, None

        # Verificar si el proyecto específico está en la lista
        start_project_check = time.time()
        project_found = None

        # Primero, buscar el proyecto por nombre para obtener su ID
        start_project_search = time.time()
        project_results = sg.find(
            "Project", [["name", "is", project_name]], ["id", "name", "code"]
        )
        time_project_search = time.time() - start_project_search
        debug_print(
            f"[{time_project_search*1000:.2f}ms] Búsqueda del proyecto '{project_name}' completada"
        )

        if not project_results:
            debug_print(f"El proyecto '{project_name}' no existe en Flow.")
            time_total = time.time() - start_total
            debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Proyecto no existe")
            return False, None

        project_to_check = project_results[0]
        project_id_to_check = project_to_check["id"]
        debug_print(
            f"Proyecto encontrado: {project_to_check['name']} (ID: {project_id_to_check})"
        )

        # Verificar si el ID del proyecto está en la lista de proyectos del usuario
        start_id_check = time.time()
        for project_ref in projects:
            project_id = project_ref.get("id")
            if project_id == project_id_to_check:
                project_found = project_to_check
                break
        time_id_check = time.time() - start_id_check
        debug_print(f"[{time_id_check*1000:.2f}ms] Verificación de IDs completada")

        time_project_check = time.time() - start_project_check
        debug_print(
            f"[{time_project_check*1000:.2f}ms] Verificación completa de proyecto"
        )

        time_total = time.time() - start_total
        debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Operación completada")

        if project_found:
            return True, project_found
        else:
            return False, project_to_check

    except Exception as e:
        print(f"ERROR al verificar proyecto del usuario: {e}")
        import traceback

        debug_print(traceback.format_exc())
        time_total = time.time() - start_total
        debug_print(f"[{time_total*1000:.2f}ms] TOTAL - Error")
        return False, None


def main():
    """Función principal que se ejecuta desde el Script Editor"""
    user_name = "Lega Pugliese"
    project_name = "EE"

    print(f"\n{'='*70}")
    print(f"Verificando si '{user_name}' tiene asignado el proyecto '{project_name}'")
    print(f"{'='*70}\n")

    start_main = time.time()
    has_project, project_info = check_user_has_project(user_name, project_name)
    time_main = time.time() - start_main

    print(f"\n{'='*70}")
    if has_project:
        print(
            f"RESULTADO: ✓ SÍ - El usuario '{user_name}' TIENE asignado el proyecto '{project_name}'"
        )
        if project_info:
            print(f"  Proyecto ID: {project_info.get('id')}")
            print(f"  Proyecto Name: {project_info.get('name')}")
            print(f"  Proyecto Code: {project_info.get('code', 'None')}")
    else:
        print(
            f"RESULTADO: ✗ NO - El usuario '{user_name}' NO tiene asignado el proyecto '{project_name}'"
        )
        if project_info:
            print(f"  (El proyecto existe en Flow con ID: {project_info.get('id')})")
    print(f"{'='*70}")
    print(f"Tiempo total de ejecución: {time_main*1000:.2f}ms ({time_main:.3f}s)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
