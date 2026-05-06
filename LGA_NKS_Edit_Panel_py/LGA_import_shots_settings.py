"""
LGA_import_shots_settings.py
Persistencia de configuración y presets del Import Shots tool.

INI: %APPDATA%\\LGA\\HieroTools\\ImportShots.ini

Secciones del INI:
  [Codec]       — dwaa, dwaa_level, channels, filter
  [Resolution]  — preset_index, custom_w/h, keep_ar, match_dim, no_upscale, deana, deana_par
  [Originals]   — move, delete
  [ResPreset_N] — name + (w, h) ó special="original"|"custom"
"""

import configparser
import os
import sys
from pathlib import Path

# ── Constantes de ruta ────────────────────────────────────────────────────────

CONFIG_DIR_NAME    = "LGA"
CONFIG_SUBDIR_NAME = "HieroTools"
CONFIG_FILE_NAME   = "ImportShots.ini"

SEC_CODEC = "Codec"
SEC_RES   = "Resolution"
SEC_ORIG  = "Originals"

DEFAULTS_CODEC = {
    "dwaa":       "true",
    "dwaa_level": "45",
    "channels":   "all",
    "filter":     "lanczos3",
}
DEFAULTS_RES = {
    "preset_index": "0",
    "custom_w":     "2048",
    "custom_h":     "1152",
    "keep_ar":      "true",
    "match_dim":    "0",
    "no_upscale":   "true",
    "deana":        "false",
    "deana_par":    "2.0",
}
DEFAULTS_ORIG = {
    "move":   "false",
    "delete": "false",
}

# Presets built-in (primera vez que se abre la herramienta)
DEFAULT_PRESETS = [
    {"name": "Original",         "special": "original"},
    {"name": "2K — 2048×1152",  "w": 2048, "h": 1152},
    {"name": "UHD — 3840×2160", "w": 3840, "h": 2160},
    {"name": "4K — 4096×2304",  "w": 4096, "h": 2304},
    {"name": "Custom...",        "special": "custom"},
]


# ── Rutas ─────────────────────────────────────────────────────────────────────

def _user_config_root():
    if sys.platform.startswith("win"):
        v = os.getenv("APPDATA")
        if v:
            return v
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.path.expanduser("~/.config")


def get_settings_path():
    """Retorna el Path al archivo ImportShots.ini."""
    return (Path(_user_config_root()) / CONFIG_DIR_NAME
            / CONFIG_SUBDIR_NAME / CONFIG_FILE_NAME)


def _ensure_dir(p):
    p.parent.mkdir(parents=True, exist_ok=True)


def _read_cfg(p):
    """Lee el INI si existe y retorna un ConfigParser."""
    cfg = configparser.ConfigParser()
    if p.exists():
        cfg.read(str(p), encoding="utf-8")
    return cfg


def _write_cfg(cfg, p):
    """Escribe el ConfigParser al disco."""
    _ensure_dir(p)
    with open(str(p), "w", encoding="utf-8") as f:
        cfg.write(f)


# ── Settings generales ────────────────────────────────────────────────────────

def load_all_settings():
    """Retorna dict con claves 'codec', 'res', 'originals'."""
    cfg = _read_cfg(get_settings_path())

    def _sec(name, defaults):
        d = dict(defaults)
        if cfg.has_section(name):
            for k, v in cfg[name].items():
                d[k] = v
        return d

    return {
        "codec":     _sec(SEC_CODEC, DEFAULTS_CODEC),
        "res":       _sec(SEC_RES,   DEFAULTS_RES),
        "originals": _sec(SEC_ORIG,  DEFAULTS_ORIG),
    }


def save_all_settings(s):
    """Guarda el dict de settings.  Solo modifica las secciones presentes en s."""
    p = get_settings_path()
    cfg = _read_cfg(p)

    mapping = {"codec": SEC_CODEC, "res": SEC_RES, "originals": SEC_ORIG}
    for key, sec_name in mapping.items():
        if key not in s:
            continue
        if not cfg.has_section(sec_name):
            cfg.add_section(sec_name)
        for k, v in s[key].items():
            cfg.set(sec_name, str(k), str(v))

    _write_cfg(cfg, p)


# ── Presets de resolución ─────────────────────────────────────────────────────

def load_res_presets():
    """Retorna la lista de presets de resolución.

    Cada preset es un dict:
      {"name": str, "special": "original"|"custom"}   — preset especial
      {"name": str, "w": int, "h": int}               — preset con dimensiones
    """
    p = get_settings_path()
    cfg = _read_cfg(p)

    presets = []
    i = 0
    while cfg.has_section("ResPreset_%d" % i):
        sec = "ResPreset_%d" % i
        d = {}
        for k, v in cfg[sec].items():
            d[k] = v
        for k in ("w", "h"):
            if k in d:
                try:
                    d[k] = int(d[k])
                except ValueError:
                    pass
        presets.append(d)
        i += 1

    if not presets:
        presets = [dict(pr) for pr in DEFAULT_PRESETS]
        save_res_presets(presets)

    return presets


def save_res_presets(presets):
    """Guarda la lista de presets al INI (sobrescribe secciones ResPreset_N)."""
    p = get_settings_path()
    cfg = _read_cfg(p)

    for sec in list(cfg.sections()):
        if sec.lower().startswith("respreset_"):
            cfg.remove_section(sec)

    for i, preset in enumerate(presets):
        sec = "ResPreset_%d" % i
        cfg.add_section(sec)
        for k, v in preset.items():
            cfg.set(sec, k, str(v))

    _write_cfg(cfg, p)


def preset_to_tuple(p):
    """Convierte un dict de preset a la tupla (name, preset_val).

    preset_val:
      None       — "Original" (mantener resolución fuente)
      "custom"   — resolución custom (spinboxes)
      (w, h)     — dimensiones fijas
    """
    if "special" in p:
        spec = p["special"]
        return (p["name"], None if spec == "original" else spec)
    return (p["name"], (int(p["w"]), int(p["h"])))


# ── Diálogo "Guardar preset" ──────────────────────────────────────────────────

def show_save_preset_dialog(w, h, parent=None):
    """Abre un diálogo para nombrar un preset de resolución.

    Returns:
        str — nombre introducido por el usuario.
        None — el usuario canceló.
    """
    from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore

    _STYLE = """
        QDialog {
            background-color: #1e1e2e;
            border: 1px solid #444;
        }
        QLabel {
            color: #cccccc;
            font-size: 12px;
        }
        QLabel#title_lbl {
            font-size: 13px;
            font-weight: bold;
            color: #e8c97a;
        }
        QLabel#res_lbl {
            color: #888888;
            font-size: 11px;
        }
        QLineEdit {
            background-color: #2a2a3a;
            border: 1px solid #555;
            color: #cccccc;
            padding: 4px 6px;
            font-size: 12px;
            border-radius: 3px;
        }
        QLineEdit:focus { border: 1px solid #7070b0; }
        QPushButton {
            background-color: #2a2a3a;
            border: 1px solid #555;
            color: #cccccc;
            padding: 5px 14px;
            font-size: 12px;
            border-radius: 3px;
            min-width: 80px;
        }
        QPushButton:hover { background-color: #3a3a4a; }
        QPushButton#btn_save {
            background-color: #443a91;
            border: 1px solid #5040aa;
            color: #e0e0e0;
        }
        QPushButton#btn_save:hover  { background-color: #5448a8; }
        QPushButton#btn_save:disabled { background-color: #2a2a4a; color: #666; }
    """

    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Guardar preset de resolución")
    dlg.setModal(True)
    dlg.setFixedWidth(340)
    dlg.setStyleSheet(_STYLE)
    dlg.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    vbox = QtWidgets.QVBoxLayout(dlg)
    vbox.setContentsMargins(20, 16, 20, 16)
    vbox.setSpacing(10)

    title = QtWidgets.QLabel("Guardar preset de resolución")
    title.setObjectName("title_lbl")
    vbox.addWidget(title)

    res_lbl = QtWidgets.QLabel("%d × %d" % (w, h))
    res_lbl.setObjectName("res_lbl")
    vbox.addWidget(res_lbl)

    vbox.addSpacing(4)
    vbox.addWidget(QtWidgets.QLabel("Nombre:"))

    line = QtWidgets.QLineEdit()
    line.setPlaceholderText("Ej: DI 2K")
    vbox.addWidget(line)

    vbox.addSpacing(4)
    btn_row = QtWidgets.QHBoxLayout()
    btn_row.addStretch()
    btn_cancel = QtWidgets.QPushButton("Cancelar")
    btn_save   = QtWidgets.QPushButton("Guardar")
    btn_save.setObjectName("btn_save")
    btn_save.setEnabled(False)
    btn_row.addWidget(btn_cancel)
    btn_row.addWidget(btn_save)
    vbox.addLayout(btn_row)

    line.textChanged.connect(lambda t: btn_save.setEnabled(bool(t.strip())))

    result = [None]

    def _do_save():
        result[0] = line.text().strip()
        dlg.accept()

    btn_cancel.clicked.connect(dlg.reject)
    btn_save.clicked.connect(_do_save)
    line.returnPressed.connect(lambda: _do_save() if btn_save.isEnabled() else None)

    dlg.exec_()
    return result[0]
