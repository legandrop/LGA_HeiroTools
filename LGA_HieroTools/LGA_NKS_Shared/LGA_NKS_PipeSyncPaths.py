"""
Helpers de rutas de PipeSync para LGA_HieroTools.

Centraliza resolución de DB/cache por contexto (studio/project) evitando
hardcodes repetidos en paneles.
"""

import os
import sys
from pathlib import Path

from LGA_NKS_ContextProfile import get_db_path
from LGA_NKS_ContextProfile import is_project_context
from SecureConfig_Reader import read_secure_config


def _legacy_cache_candidates(filename):
    candidates = []

    if sys.platform == "win32":
        if is_project_context():
            candidates.append(Path("C:/Portable/LGA/PipeSyncProject/cache") / filename)
            candidates.append(Path("C:/Portable/LGA/PipeSync/cache/project") / filename)
        candidates.append(Path("C:/Portable/LGA/PipeSync/cache") / filename)
        return candidates

    if sys.platform == "darwin":
        if is_project_context():
            candidates.append(Path.home() / "Library" / "Caches" / "LGA" / "PipeSyncProject" / filename)
        candidates.append(Path.home() / "Library" / "Caches" / "LGA" / "PipeSync" / filename)
        return candidates

    if is_project_context():
        candidates.append(Path.home() / ".cache" / "LGA" / "PipeSyncProject" / filename)
    candidates.append(Path.home() / ".cache" / "LGA" / "PipeSync" / filename)
    return candidates


def _pick_existing_or_default(candidates, default_path):
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return default_path


def get_pipesync_db_path(filename="pipesync.db"):
    config = read_secure_config() or {}
    default_path = get_db_path(config, filename)
    candidates = [default_path]
    candidates.extend(_legacy_cache_candidates(filename))
    selected = _pick_existing_or_default(candidates, default_path)
    return os.path.normpath(str(selected))


def get_alt_work_root(default_root=None):
    if default_root is None:
        default_root = "N:\\" if is_project_context() else "T:\\"

    config = read_secure_config() or {}
    app_cfg = config.get("App", {}) if isinstance(config, dict) else {}
    raw_alt = str(app_cfg.get("AltTPath", "")).strip()
    if raw_alt:
        return os.path.normpath(raw_alt)
    return os.path.normpath(default_root)
