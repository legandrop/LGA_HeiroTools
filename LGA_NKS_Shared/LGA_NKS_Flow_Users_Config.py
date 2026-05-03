"""
____________________________________________________________________

  LGA_NKS_Flow_Users_Config v1.00 | Lega

  Carga y gestiona la configuración de usuarios para Flow.

  Usado por runtime activo:
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py

  v1.00: Versión inicial
____________________________________________________________________

"""

import json
import os


LOCAL_USERS_FILENAME = "LGA_NKS_Flow_Users.json"
DIST_USERS_FILENAME = "LGA_NKS_Flow_Users_dist.json"


def get_flow_users_config_paths(startup_dir):
    startup_dir = os.path.abspath(startup_dir)
    local_path = os.path.join(startup_dir, LOCAL_USERS_FILENAME)
    dist_path = os.path.join(startup_dir, DIST_USERS_FILENAME)
    return local_path, dist_path


def get_flow_users_config_path(startup_dir):
    local_path, dist_path = get_flow_users_config_paths(startup_dir)
    if os.path.exists(local_path):
        return local_path
    if os.path.exists(dist_path):
        return dist_path
    return local_path


def load_flow_users_config(startup_dir):
    config_path = get_flow_users_config_path(startup_dir)
    if not os.path.exists(config_path):
        return None, config_path

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f), config_path
