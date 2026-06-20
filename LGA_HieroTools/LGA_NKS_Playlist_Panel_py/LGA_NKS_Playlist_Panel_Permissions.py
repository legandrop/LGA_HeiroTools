"""
____________________________________________________________________

  LGA_NKS_Playlist_Panel_Permissions v0.01 | Lega

  Utilidades para detectar si el usuario actual de PipeSync tiene rol Master.

  v0.01: Lectura de config.secure y parsing de SpecialUsers.cpp.
____________________________________________________________________

"""

from pathlib import Path
import re

from LGA_NKS_Shared.LGA_NKS_ContextProfile import get_pipesync_profile_folder
from LGA_NKS_Shared.SecureConfig_Reader import get_flow_login_for_profile


PIPESYNC_ROOT = Path(r"C:\Portable\LGA_PipeSync_2")
SPECIAL_USERS_CPP = PIPESYNC_ROOT / "src" / "core" / "config" / "SpecialUsers.cpp"

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
    profile_folder = get_pipesync_profile_folder()
    flow_login = get_flow_login_for_profile(profile_folder).strip().lower()
    master_emails = _parse_master_emails()
    is_master = flow_login in master_emails

    return {
        "profile_folder": profile_folder,
        "flow_login": flow_login,
        "master_emails": master_emails,
        "is_master": is_master,
    }


def is_current_user_master():
    return get_master_detection_details()["is_master"]
