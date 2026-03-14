> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.

# Acceso al Usuario Actual de PipeSync

## Descripción
Esta documentación explica cómo acceder al usuario actual configurado en PipeSync desde scripts de Python en Nuke/Hiero. PipeSync almacena la información del usuario en dos lugares: configuración segura y base de datos SQLite.

## Ubicaciones por Sistema Operativo

### Windows
- **Configuración segura**: `%APPDATA%\LGA\PipeSync\config.secure`
- **Base de datos**: `C:/Portable/LGA/PipeSync/cache/pipesync.db`

### macOS
- **Configuración segura**: `~/Library/Application Support/LGA/PipeSync/config.secure`
- **Base de datos**: `~/Library/Caches/LGA/PipeSync/pipesync.db`

## Métodos para Obtener el Usuario Actual

### Método 1: Desde Configuración Segura (Recomendado)

```python
import sys
import os

# Añadir el directorio padre al path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

from LGA_NKS_Flow.SecureConfig_Reader import get_flow_credentials

def obtener_usuario_actual():
    """Obtiene el usuario actual desde la configuración segura de PipeSync."""
    try:
        url, login, password = get_flow_credentials()

        if not login:
            print("No se pudo obtener el usuario de PipeSync")
            return None

        return login  # Retorna el email/login del usuario

    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None

# Uso
usuario = obtener_usuario_actual()
if usuario:
    print(f"Usuario actual: {usuario}")
```

### Método 2: Desde Base de Datos SQLite

```python
import sqlite3
import platform
import os

def get_db_path():
    """Obtiene la ruta de la base de datos según el sistema operativo."""
    if platform.system() == "Windows":
        return r"C:/Portable/LGA/PipeSync/cache/pipesync.db"
    elif platform.system() == "Darwin":
        return "/Users/leg4/Library/Caches/LGA/PipeSync/pipesync.db"
    else:
        return os.path.expanduser("~/Library/Caches/LGA/PipeSync/pipesync.db")

def obtener_usuario_desde_db():
    """Obtiene información del usuario desde la base de datos."""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print("Base de datos no encontrada")
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Obtener user_login (email)
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_login'"
        )
        login_row = cursor.fetchone()

        # Obtener user_name (nombre completo)
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_name'"
        )
        name_row = cursor.fetchone()

        # Obtener user_id
        cursor.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = 'user_id'"
        )
        id_row = cursor.fetchone()

        conn.close()

        return {
            'login': login_row[0] if login_row and login_row[0] else None,
            'name': name_row[0] if name_row and name_row[0] else None,
            'id': id_row[0] if id_row and id_row[0] else None
        }

    except Exception as e:
        print(f"Error al acceder a la base de datos: {e}")
        return None

# Uso
usuario_info = obtener_usuario_desde_db()
if usuario_info:
    print(f"Login: {usuario_info['login']}")
    print(f"Nombre: {usuario_info['name']}")
    print(f"ID: {usuario_info['id']}")
```

## Función Combinada (Recomendada)

Para mayor robustez, puedes combinar ambos métodos:

```python
def obtener_usuario_pipesync():
    """
    Obtiene el usuario actual de PipeSync usando el método más confiable disponible.

    Retorna:
        str: Login/email del usuario actual, o None si no se puede determinar
    """
    # Intentar primero con configuración segura
    try:
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        sys.path.insert(0, parent_dir)
        from LGA_NKS_Flow.SecureConfig_Reader import get_flow_credentials

        url, login, password = get_flow_credentials()
        if login:
            return login
    except:
        pass

    # Si falla, intentar con base de datos
    try:
        usuario_info = obtener_usuario_desde_db()
        if usuario_info and usuario_info['login']:
            return usuario_info['login']
    except:
        pass

    return None

# Uso
usuario_actual = obtener_usuario_pipesync()
if usuario_actual:
    print(f"Usuario actual de PipeSync: {usuario_actual}")
else:
    print("No se pudo determinar el usuario actual de PipeSync")
```

## Información Disponible

### Desde Configuración Segura
- **Login/Email**: Dirección de email del usuario (ej: `lega@wanka.tv`)
- **URL**: URL de ShotGrid/Flow
- **Password**: Contraseña (encriptada)

### Desde Base de Datos
- **user_login**: Login/email del usuario
- **user_name**: Nombre completo del usuario
- **user_id**: ID numérico del usuario en ShotGrid

## Script de Prueba

Se incluye un script de prueba `temp_get_pipesync_user.py` que demuestra ambos métodos:

```bash
cd "+Building_Blocks"
python temp_get_pipesync_user.py
```

## Ejemplo de Uso en Panel de Viewer

Para implementar la lógica de mostrar solo los botones del usuario actual:

```python
def mostrar_botones_usuario_actual():
    """Muestra solo los botones de navegación para el usuario actual."""

    # Obtener usuario actual
    usuario_actual = obtener_usuario_pipesync()

    # Usuarios disponibles
    usuarios = {
        "lega": "Lega Pugliese",
        "javi": "Javi Bravo",
        "sebas": "Sebas Romano"
    }

    # Mostrar botones solo para el usuario actual
    if usuario_actual:
        # Extraer nombre de usuario del email (parte antes del @)
        nombre_usuario = usuario_actual.split('@')[0].lower()

        if nombre_usuario in usuarios:
            print(f"Mostrando botones para: {usuarios[nombre_usuario]}")
            # Aquí iría la lógica para mostrar botones prev/next
        else:
            print("Usuario no reconocido en la lista de usuarios")
    else:
        print("No se pudo determinar el usuario actual")

# Llamar en la inicialización del panel
mostrar_botones_usuario_actual()
```

## Consideraciones de Seguridad

- La configuración segura (`config.secure`) contiene credenciales encriptadas
- La base de datos SQLite contiene información del usuario pero no credenciales
- Ambos métodos requieren acceso a archivos del sistema
- El método de configuración segura es más confiable ya que se actualiza automáticamente

## Troubleshooting

### Error: "No module named 'LGA_NKS_Flow'"
- Asegurarse de que el script esté en la estructura correcta de carpetas
- Verificar que el path al directorio padre sea correcto

### Error: Archivo no encontrado
- Verificar que PipeSync esté instalado y configurado
- Comprobar rutas específicas del sistema operativo

### Usuario vacío
- Verificar que el usuario haya iniciado sesión en PipeSync al menos una vez
- Comprobar que la configuración de PipeSync esté completa

## Archivos Relacionados

- `temp_get_pipesync_user.py`: Script de prueba
- `LGA_NKS_Flow/SecureConfig_Reader.py`: Módulo para acceder a configuración segura
- `LGA_NKS_Flow/Documentacion_DB PipeSync.md`: Documentación completa de la base de datos