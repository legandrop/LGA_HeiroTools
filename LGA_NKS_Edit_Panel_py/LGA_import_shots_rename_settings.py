"""
____________________________________________________________________

  LGA_import_shots_rename_settings v1.00 | Lega

  Persistencia de configuracion para la seccion Rename.
  INI: %APPDATA%\\LGA\\HieroTools\\ImportShotsRename.ini

____________________________________________________________________
"""

import configparser
import os
import sys
from pathlib import Path

CONFIG_DIR_NAME = "LGA"
CONFIG_SUBDIR_NAME = "HieroTools"
CONFIG_FILE_NAME = "ImportShotsRename.ini"

SEC_SR1 = "SearchReplace1"
SEC_SR2 = "SearchReplace2"
SEC_DELIM = "Delimiter"
SEC_PADDING = "Padding"

DEFAULTS_SR = {
    "search": "",
    "replace": "",
    "case_sensitive": "false",
}
DEFAULTS_DELIM = {
    "char": "_",
}
DEFAULTS_PADDING = {
    "digits": "4",
}


def _user_config_root():
    if sys.platform.startswith("win"):
        v = os.getenv("APPDATA")
        if v:
            return v
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.path.expanduser("~/.config")


def get_settings_path():
    return (
        Path(_user_config_root())
        / CONFIG_DIR_NAME
        / CONFIG_SUBDIR_NAME
        / CONFIG_FILE_NAME
    )


def _ensure_dir(path_obj):
    path_obj.parent.mkdir(parents=True, exist_ok=True)


def _read_cfg(path_obj):
    cfg = configparser.ConfigParser()
    if path_obj.exists():
        cfg.read(str(path_obj), encoding="utf-8")
    return cfg


def _write_cfg(cfg, path_obj):
    _ensure_dir(path_obj)
    with open(str(path_obj), "w", encoding="utf-8") as fh:
        cfg.write(fh)


def load_settings():
    cfg = _read_cfg(get_settings_path())

    def _section(sec, defaults):
        out = dict(defaults)
        if cfg.has_section(sec):
            for k, v in cfg[sec].items():
                out[k] = v
        return out

    return {
        "sr1": _section(SEC_SR1, DEFAULTS_SR),
        "sr2": _section(SEC_SR2, DEFAULTS_SR),
        "delimiter": _section(SEC_DELIM, DEFAULTS_DELIM),
        "padding": _section(SEC_PADDING, DEFAULTS_PADDING),
    }


def save_settings(data):
    cfg_path = get_settings_path()
    cfg = _read_cfg(cfg_path)

    mapping = {
        "sr1": SEC_SR1,
        "sr2": SEC_SR2,
        "delimiter": SEC_DELIM,
        "padding": SEC_PADDING,
    }
    for key, sec_name in mapping.items():
        if key not in data:
            continue
        if not cfg.has_section(sec_name):
            cfg.add_section(sec_name)
        for k, v in data[key].items():
            cfg.set(sec_name, str(k), str(v))

    _write_cfg(cfg, cfg_path)
