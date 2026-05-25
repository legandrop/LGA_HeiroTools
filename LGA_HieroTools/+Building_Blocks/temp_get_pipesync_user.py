#!/usr/bin/env python3
"""
Script temporal para obtener el usuario actual de PipeSync.
Prueba dos métodos:
1. Desde la configuración segura (SecureConfig)
2. Desde la base de datos SQLite (app_settings)
"""

import sys
import os
import platform
import sqlite3
from pathlib import Path

# Añadir el directorio padre al path para importar los módulos desde LGA_NKS_Flow
parent_dir = os.path.dirname(os.path.dirname(__file__))  # Ir al directorio padre
sys.path.insert(0, parent_dir)

try:
    from LGA_NKS_Flow.SecureConfig_Reader import get_flow_credentials, get_config_path
except ImportError as e:
    print(f"Error al importar SecureConfig_Reader: {e}")
    sys.exit(1)


def get_db_path():
    """Obtiene la ruta de la base de datos según el sistema operativo."""
    if platform.system() == "Windows":
        db_path = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
    elif platform.system() == "Darwin":
        db_path = "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
    else:
        # Linux u otro sistema
        db_path = os.path.expanduser("~/Library/Caches/LGA/PipeSync/pipesync.db")
    return db_path


def get_user_from_config():
    """Obtiene el usuario desde la configuración segura."""
    print("\n" + "=" * 60)
    print("MÉTODO 1: Obtener usuario desde SecureConfig")
    print("=" * 60)
    
    try:
        config_path = get_config_path()
        print(f"Ruta de configuración: {config_path}")
        print(f"Archivo existe: {config_path.exists()}")
        
        if not config_path.exists():
            print("[ERROR] El archivo de configuración no existe")
            return None
        
        # Obtener credenciales
        url, login, password = get_flow_credentials()
        
        if not url or not login or not password:
            print("[ERROR] No se pudieron obtener las credenciales")
            return None
        
        print(f"[OK] Credenciales obtenidas exitosamente")
        print(f"   URL: {url}")
        print(f"   Login (usuario): {login}")
        print(f"   Password: {'*' * len(password) if password else 'No disponible'}")
        
        return {
            'method': 'SecureConfig',
            'login': login,
            'url': url
        }
        
    except Exception as e:
        print(f"[ERROR] Error al obtener usuario desde SecureConfig: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_user_from_database():
    """Obtiene el usuario desde la base de datos SQLite."""
    print("\n" + "=" * 60)
    print("MÉTODO 2: Obtener usuario desde Base de Datos SQLite")
    print("=" * 60)
    
    try:
        db_path = get_db_path()
        print(f"Ruta de base de datos: {db_path}")
        print(f"Archivo existe: {os.path.exists(db_path)}")
        
        if not os.path.exists(db_path):
            print("[ERROR] La base de datos no existe")
            return None
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consultar app_settings para obtener información del usuario
        user_info = {}
        
        # Obtener user_login
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_login'"
        )
        row = cursor.fetchone()
        if row and row[0]:
            user_info['login'] = row[0]
            print(f"[OK] user_login encontrado: {row[0]}")
        else:
            print("[WARN] user_login no encontrado en app_settings")
        
        # Obtener user_name
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_name'"
        )
        row = cursor.fetchone()
        if row and row[0]:
            user_info['name'] = row[0]
            print(f"[OK] user_name encontrado: {row[0]}")
        else:
            print("[WARN] user_name no encontrado en app_settings")
        
        # Obtener user_id
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_id'"
        )
        row = cursor.fetchone()
        if row and row[0]:
            user_info['id'] = row[0]
            print(f"[OK] user_id encontrado: {row[0]}")
        else:
            print("[WARN] user_id no encontrado en app_settings")
        
        conn.close()
        
        if not user_info:
            print("[ERROR] No se encontró información del usuario en app_settings")
            return None
        
        print(f"[OK] Información del usuario obtenida desde la base de datos")
        return {
            'method': 'Database',
            **user_info
        }
        
    except Exception as e:
        print(f"[ERROR] Error al obtener usuario desde la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Función principal."""
    print("=" * 60)
    print("SCRIPT TEMPORAL: Obtener Usuario Actual de PipeSync")
    print("=" * 60)
    print(f"Sistema operativo: {platform.system()}")
    print(f"Plataforma: {platform.platform()}")
    
    # Método 1: Desde SecureConfig
    config_user = get_user_from_config()
    
    # Método 2: Desde Base de Datos
    db_user = get_user_from_database()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if config_user:
        print(f"\n[OK] Método 1 (SecureConfig):")
        print(f"   Usuario (login): {config_user.get('login', 'N/A')}")
        print(f"   URL: {config_user.get('url', 'N/A')}")
    else:
        print("\n[ERROR] Método 1 (SecureConfig): No disponible")
    
    if db_user:
        print(f"\n[OK] Método 2 (Base de Datos):")
        if 'login' in db_user:
            print(f"   Login: {db_user.get('login', 'N/A')}")
        if 'name' in db_user:
            print(f"   Nombre: {db_user.get('name', 'N/A')}")
        if 'id' in db_user:
            print(f"   ID: {db_user.get('id', 'N/A')}")
    else:
        print("\n[ERROR] Método 2 (Base de Datos): No disponible")
    
    # Determinar usuario actual
    print("\n" + "=" * 60)
    print("USUARIO ACTUAL DETECTADO")
    print("=" * 60)
    
    if config_user and config_user.get('login'):
        print(f"\n[RESULTADO] Usuario actual (desde SecureConfig): {config_user['login']}")
        return config_user['login']
    elif db_user and db_user.get('login'):
        print(f"\n[RESULTADO] Usuario actual (desde Base de Datos): {db_user['login']}")
        return db_user['login']
    elif db_user and db_user.get('name'):
        print(f"\n[RESULTADO] Usuario actual (desde Base de Datos - nombre): {db_user['name']}")
        return db_user['name']
    else:
        print("\n[ERROR] No se pudo determinar el usuario actual")
        return None


if __name__ == "__main__":
    usuario = main()
    if usuario:
        print(f"\n[OK] Usuario encontrado: {usuario}")
    else:
        print("\n[ERROR] No se pudo obtener el usuario")
        sys.exit(1)
