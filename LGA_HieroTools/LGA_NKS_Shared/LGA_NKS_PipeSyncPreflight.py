"""
Preflight checks para integración HieroTools <-> PipeSync.

Centraliza validaciones visibles para Pull/Push y utilidades de identidad
del usuario en el perfil normal de PipeSync.
"""

from pathlib import Path

from LGA_NKS_ContextProfile import get_context_mode
from LGA_NKS_ContextProfile import get_secure_config_path
from LGA_NKS_PipeSyncPaths import get_pipesync_db_path
from SecureConfig_Reader import get_flow_credentials
from SecureConfig_Reader import get_flow_login_for_profile


def _build_state(require_flow_credentials=False):
    context_mode = get_context_mode()
    config_path = Path(get_secure_config_path())
    db_path = Path(get_pipesync_db_path("pipesync.db"))

    has_config = config_path.exists()
    has_db = db_path.exists()

    has_flow_credentials = True
    missing_flow_fields = []
    if require_flow_credentials:
        sg_url, sg_login, sg_password = get_flow_credentials()
        if not sg_url:
            missing_flow_fields.append("Flow.Url")
        if not sg_login:
            missing_flow_fields.append("Flow.Login")
        if not sg_password:
            missing_flow_fields.append("Flow.Password")
        has_flow_credentials = len(missing_flow_fields) == 0

    return {
        "mode": context_mode,
        "config_path": str(config_path),
        "db_path": str(db_path),
        "has_config": has_config,
        "has_db": has_db,
        "has_flow_credentials": has_flow_credentials,
        "missing_flow_fields": missing_flow_fields,
    }


def _build_error_text(action_name, state, require_flow_credentials=False):
    missing = []
    if not state["has_config"]:
        missing.append(f"- config.secure no encontrado:\n  {state['config_path']}")
    if not state["has_db"]:
        missing.append(f"- pipesync.db no encontrado:\n  {state['db_path']}")
    if require_flow_credentials and not state["has_flow_credentials"]:
        missing_fields = ", ".join(state["missing_flow_fields"])
        missing.append(
            "- Credenciales de Flow incompletas en config.secure:\n"
            f"  faltan: {missing_fields}"
        )

    if not missing:
        return ""

    lines = [
        f"No se puede ejecutar {action_name} en modo '{state['mode']}'.",
        "",
        "Faltan los siguientes prerequisitos de PipeSync:",
        *missing,
        "",
        "Abrí PipeSync, configurá Flow y sincronizá para generar cache/DB local.",
    ]
    return "\n".join(lines)


def validate_pull_preflight():
    state = _build_state(require_flow_credentials=False)
    message = _build_error_text("Flow Pull", state, require_flow_credentials=False)
    return message == "", message, state


def validate_push_preflight():
    state = _build_state(require_flow_credentials=True)
    message = _build_error_text("Flow Push", state, require_flow_credentials=True)
    return message == "", message, state


def get_normal_pipesync_flow_login():
    """
    Devuelve Flow.Login del perfil normal (%APPDATA%/LGA/PipeSync/config.secure).
    Independiente del contexto activo de HieroTools.
    """
    return get_flow_login_for_profile("PipeSync")

