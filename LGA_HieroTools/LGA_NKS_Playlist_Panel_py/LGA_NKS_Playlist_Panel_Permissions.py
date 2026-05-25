"""
____________________________________________________________________

  LGA_NKS_Playlist_Panel_Permissions v0.01 | Lega

  Utilidades para detectar si el usuario actual de PipeSync tiene rol Master.

  v0.01: Lectura de config.secure y parsing de SpecialUsers.cpp.
____________________________________________________________________

"""

from pathlib import Path
import base64
import hashlib
import json
import os
import platform
import re
import uuid


PIPESYNC_ROOT = Path(r"C:\Portable\LGA_PipeSync_2")
SPECIAL_USERS_CPP = PIPESYNC_ROOT / "src" / "core" / "config" / "SpecialUsers.cpp"


def _get_config_path():
    if os.name == "nt":
        app_data = os.getenv("APPDATA", "")
        return Path(app_data) / "LGA" / "PipeSync" / "config.secure"
    if platform.system() == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "LGA"
            / "PipeSync"
            / "config.secure"
        )
    return Path.home() / ".config" / "LGA" / "PipeSync" / "config.secure"


def _get_key_path():
    if os.name == "nt":
        app_data = os.getenv("APPDATA", "")
        return Path(app_data) / "LGA" / "PipeSync" / ".key"
    if platform.system() == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "LGA"
            / "PipeSync"
            / ".key"
        )
    return Path.home() / ".config" / "LGA" / "PipeSync" / ".key"


def _get_system_identifier():
    system_info = platform.uname()
    identifier = f"{system_info.node}{system_info.system}{system_info.machine}"
    try:
        mac = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 8 * 6, 8)
            ][::-1]
        )
        identifier += mac
    except Exception:
        pass
    return identifier


def _generate_key():
    return hashlib.sha256(_get_system_identifier().encode()).digest()


def _get_encryption_key():
    key_path = _get_key_path()
    if key_path.exists():
        return key_path.read_bytes()
    return _generate_key()


def _decrypt(encrypted_text, key):
    if not encrypted_text:
        return ""

    encrypted_data = base64.b64decode(encrypted_text)
    decrypted_data = bytearray()
    for index, value in enumerate(encrypted_data):
        decrypted_data.append(value ^ key[index % len(key)])
    return decrypted_data.decode("utf-8")


def _load_secure_config():
    config_path = _get_config_path()
    if not config_path.exists():
        return {}

    key = _get_encryption_key()
    encrypted_data = config_path.read_text(encoding="utf-8")
    json_data = _decrypt(encrypted_data, key)
    if not json_data:
        return {}
    return json.loads(json_data)


def _parse_master_emails():
    if not SPECIAL_USERS_CPP.exists():
        return []

    text = SPECIAL_USERS_CPP.read_text(encoding="utf-8")
    pattern = re.compile(
        r'"([^"]+)"\s*,\s*//.*?\n\s*UserProfile\{\s*QSet<Role>\{([^}]*)\}\s*\}',
        re.DOTALL,
    )

    master_emails = []
    for email, roles_blob in pattern.findall(text):
        roles = {role.strip() for role in roles_blob.split(",")}
        if "Master" in roles:
            master_emails.append(email.strip().lower())
    return master_emails


def get_master_detection_details():
    config = _load_secure_config()
    flow_login = config.get("Flow", {}).get("Login", "").strip().lower()
    master_emails = _parse_master_emails()
    is_master = flow_login in master_emails

    return {
        "flow_login": flow_login,
        "master_emails": master_emails,
        "is_master": is_master,
    }


def is_current_user_master():
    return get_master_detection_details()["is_master"]
