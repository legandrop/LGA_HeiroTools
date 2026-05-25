#!/usr/bin/env python3
import sys
import os

# Añadir el directorio del proyecto al path para importar los módulos
sys.path.insert(0, '/Users/leg4/.nuke/Python/Startup')

print("=== PRUEBA SIMPLE DE RUTA ALTERNATIVA ===")

try:
    # Importar solo SecureConfig_Reader para probar la lógica
    from LGA_NKS_Flow.SecureConfig_Reader import read_secure_config

    print("✅ SecureConfig_Reader importado correctamente")

    # Leer configuración
    config = read_secure_config()
    if config:
        print("✅ Configuración leída correctamente")

        # Verificar si existe la sección App y AltTPath
        if 'App' in config and 'AltTPath' in config['App']:
            alt_path = config['App']['AltTPath']
            print(f"✅ AltTPath encontrado: {alt_path}")
            print(f"   Ruta existe: {os.path.exists(alt_path)}")

            # Simular la lógica de get_base_scan_path
            if alt_path and os.path.exists(alt_path):
                print(f"✅ Ruta alternativa válida: {alt_path}")
                print("✅ La lógica de get_base_scan_path funcionará correctamente")
            else:
                print(f"⚠️ Ruta alternativa configurada pero no existe: {alt_path}")
        else:
            print("❌ No se encontró AltTPath en la configuración")
    else:
        print("❌ No se pudo leer la configuración segura")

except Exception as e:
    print(f"❌ Error en la prueba: {e}")
    import traceback
    traceback.print_exc()
