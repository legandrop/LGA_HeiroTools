#!/usr/bin/env python3
import sys
import os

# Añadir el directorio del proyecto al path para importar los módulos
sys.path.insert(0, '/Users/leg4/.nuke/Python/Startup')

try:
    from LGA_NKS_Flow.SecureConfig_Reader import read_secure_config, get_config_path, DEBUG

    # Activar debug para ver más información
    DEBUG = True

    print("=== VERIFICANDO CONFIGURACIÓN SEGURA DE PIPESYNC ===")
    print(f"Ruta del archivo de configuración: {get_config_path()}")
    print(f"Archivo existe: {get_config_path().exists()}")
    print()

    # Leer la configuración
    config = read_secure_config()

    if config:
        print("✅ Configuración leída exitosamente")
        print("Contenido de la configuración:")
        print("=" * 50)

        # Mostrar todas las claves principales
        for key in config.keys():
            print(f"\n🔑 Sección: {key}")
            if isinstance(config[key], dict):
                for subkey in config[key].keys():
                    value = config[key][subkey]
                    # Ocultar contraseñas
                    if 'password' in subkey.lower() or 'secret' in subkey.lower():
                        value = "*" * len(str(value)) if value else "No configurado"
                    print(f"   {subkey}: {value}")
            else:
                print(f"   Valor: {config[key]}")

        # Buscar específicamente parámetros relacionados con rutas
        print("\n" + "=" * 50)
        print("🔍 BUSCANDO PARÁMETROS DE RUTA:")
        print("=" * 50)

        def buscar_rutas(d, prefix=""):
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    buscar_rutas(value, full_key)
                else:
                    key_lower = key.lower()
                    value_str = str(value).lower() if value else ""
                    if ('ruta' in key_lower or 'path' in key_lower or 'dir' in key_lower or
                        'alternativa' in key_lower or 'volume' in value_str or
                        'viaja' in value_str or '/t' in value_str):
                        print(f"   📂 Posible ruta encontrada: {full_key} = {value}")

        buscar_rutas(config)

    else:
        print("❌ No se pudo leer la configuración segura")
        print("Posibles causas:")
        print("- El archivo config.secure no existe")
        print("- Error de desencriptación")
        print("- Permisos insuficientes")

except Exception as e:
    print(f"❌ Error al ejecutar el script: {e}")
    import traceback
    traceback.print_exc()
