"""
____________________________________________________________________

  explore_timeline_persistent_settings_to_txt.py | Lega

  Busca donde Hiero/Nuke Studio guarda estado persistente del TimelineView:

    - QSettings default y variantes de organizacion/aplicacion Foundry
    - ~/.nuke/uistate.ini, preferences*.nk y otros archivos recientes
    - AppData/Local/Roaming Foundry/NukeStudio
    - lineas filtradas por timeline/track/header/height/width/etc.
    - hashes y mtimes para comparar antes/despues de cambiar la UI

  Guarda snapshots numerados:

      C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/final_persistent_settings_1.txt

  Uso:
      exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_persistent_settings_to_txt.py").read())
____________________________________________________________________
"""

from __future__ import print_function

import hashlib
import os
import re
import sys
import time
import traceback

try:
    from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtCore
except Exception:
    try:
        from PySide6 import QtCore
    except Exception:
        from PySide2 import QtCore


OUT_DIR = r"C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout"
PREFIX = "final_persistent_settings"

HOME = os.path.expanduser("~")
NUKE_DIR = os.path.join(HOME, ".nuke")
APPDATA = os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))

ROOTS = [
    NUKE_DIR,
    os.path.join(LOCALAPPDATA, "Foundry"),
    os.path.join(LOCALAPPDATA, "The Foundry Visionmongers"),
    os.path.join(APPDATA, "Foundry"),
    os.path.join(APPDATA, "The Foundry Visionmongers"),
]

EXCLUDED_DIR_PARTS = (
    os.path.normcase(os.path.join(".nuke", "LGA_ToolPack-Layout")),
    os.path.normcase(os.path.join(".nuke", "Python", "Startup")),
    os.path.normcase(os.path.join(".nuke", ".git")),
    os.path.normcase(os.path.join(".nuke", ".venv")),
    os.path.normcase(os.path.join(".nuke", "__pycache__")),
)

EXCLUDED_FILE_NAMES = (
    "ScriptEditorHistory.xml",
)

KEYWORDS = (
    "timeline", "track", "tracks", "trackname", "tracknames",
    "header", "headers", "label", "labels", "namewidth",
    "height", "width", "row", "rows", "lane", "collapse",
    "collapsed", "expand", "expanded", "thumbnail", "thumb",
    "waveform", "zoom", "scroll", "split", "ruler", "sequence",
)

FILE_EXTS = (
    ".ini", ".conf", ".cfg", ".json", ".xml", ".txt", ".dat",
    ".pref", ".nk", ".plist", ".state", ".settings",
)

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_FILES_PER_ROOT = 2000
MAX_MATCHES_PER_FILE = 80
MAX_QSETTINGS_KEYS = 5000


def safe_str(value, limit=500):
    try:
        text = str(value)
    except Exception as exc:
        text = "<str error: %s>" % exc
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def section(lines, title):
    lines.append("")
    lines.append("=" * 100)
    lines.append(title)
    lines.append("=" * 100)


def next_output_path():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    idx = 1
    while True:
        path = os.path.join(OUT_DIR, "%s_%d.txt" % (PREFIX, idx))
        if not os.path.exists(path):
            return path, idx
        idx += 1


def matches_keyword(text):
    low = text.lower()
    return any(k in low for k in KEYWORDS)


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_lines(path):
    with open(path, "rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        return None, "<too large>"
    if b"\x00" in data[:4096]:
        # Some Qt blobs still contain readable strings, but line scanning is
        # noisy. Keep them in the manifest via hash/mtime only.
        return None, "<binary>"
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc, errors="replace").splitlines(), enc
        except Exception:
            pass
    return data.decode("utf-8", errors="replace").splitlines(), "utf-8-replace"


def iter_candidate_files(root):
    count = 0
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        norm_dirpath = os.path.normcase(dirpath)
        if any(part in norm_dirpath for part in EXCLUDED_DIR_PARTS):
            continue
        # Avoid huge browser/cache trees; we care about prefs/configs.
        lowered = dirpath.lower()
        if any(part in lowered for part in (
            "\\qtwebengine\\", "\\cache\\", "\\gpucache\\",
            "\\session storage\\", "\\local storage\\leveldb\\",
            "\\network\\", "\\crash", "\\logs\\",
        )):
            continue
        for name in filenames:
            if name in EXCLUDED_FILE_NAMES:
                continue
            if count >= MAX_FILES_PER_ROOT:
                return
            path = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in FILE_EXTS and not matches_keyword(name):
                continue
            try:
                size = os.path.getsize(path)
            except Exception:
                continue
            if size > MAX_FILE_BYTES:
                continue
            count += 1
            yield path


def dump_recent_files(lines):
    section(lines, "RECENT CANDIDATE FILES OUTSIDE OUTPUT/SCRIPTS")
    files = []
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for path in iter_candidate_files(root):
            try:
                stat = os.stat(path)
            except Exception:
                continue
            files.append((stat.st_mtime, stat.st_size, path))
    for mtime, size, path in sorted(files, reverse=True)[:120]:
        lines.append("%s size=%d path=%s" % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)), size, path
        ))


def dump_qsettings_instance(lines, label, settings):
    section(lines, "QSETTINGS: %s" % label)
    try:
        lines.append("fileName=%s" % settings.fileName())
    except Exception as exc:
        lines.append("fileName error=%s" % exc)
    try:
        lines.append("format=%s scope=%s status=%s" % (settings.format(), settings.scope(), settings.status()))
    except Exception as exc:
        lines.append("meta error=%s" % exc)
    try:
        keys = list(settings.allKeys())
    except Exception as exc:
        lines.append("allKeys error=%s" % exc)
        return
    matched = []
    for key in keys:
        if matches_keyword(key):
            try:
                value = settings.value(key)
            except Exception as exc:
                value = "<read error: %s>" % exc
            matched.append((key, value))
    lines.append("totalKeys=%d matchedKeys=%d" % (len(keys), len(matched)))
    for key, value in sorted(matched, key=lambda item: item[0].lower())[:MAX_QSETTINGS_KEYS]:
        lines.append("%s = %s" % (key, safe_str(value, 1200)))
    if len(matched) > MAX_QSETTINGS_KEYS:
        lines.append("<truncated %d matched keys>" % (len(matched) - MAX_QSETTINGS_KEYS))


def dump_qsettings(lines):
    section(lines, "QSETTINGS SUMMARY")
    variants = []
    try:
        variants.append(("default", QtCore.QSettings()))
    except Exception as exc:
        lines.append("default QSettings error=%s" % exc)

    orgs = [
        "Foundry",
        "The Foundry",
        "The Foundry Visionmongers",
        "The Foundry Visionmongers Ltd",
        "TheFoundry",
    ]
    apps = [
        "Nuke",
        "Nuke15.1",
        "Nuke Studio",
        "NukeStudio",
        "Hiero",
        "HieroPlayer",
        "Timeline",
    ]
    for org in orgs:
        for app in apps:
            try:
                variants.append(("%s / %s" % (org, app), QtCore.QSettings(org, app)))
            except Exception:
                pass
    for label, settings in variants:
        dump_qsettings_instance(lines, label, settings)


def dump_file_manifest_and_matches(lines):
    section(lines, "PERSISTENT FILE MANIFEST + KEYWORD MATCHES")
    seen = set()
    for root in ROOTS:
        lines.append("")
        lines.append("--- ROOT %s exists=%s ---" % (root, os.path.isdir(root)))
        for path in iter_candidate_files(root):
            norm = os.path.normcase(os.path.abspath(path))
            if norm in seen:
                continue
            seen.add(norm)
            try:
                stat = os.stat(path)
                sha1 = file_sha1(path)
            except Exception as exc:
                lines.append("FILE_ERROR path=%s error=%s" % (path, exc))
                continue
            rel = path
            lines.append("FILE path=%s size=%d mtime=%s sha1=%s" % (
                rel, stat.st_size, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)), sha1
            ))
            text_lines, encoding = read_text_lines(path)
            if text_lines is None:
                lines.append("  content=%s" % encoding)
                continue
            matches = []
            for idx, line in enumerate(text_lines, 1):
                if matches_keyword(line):
                    matches.append((idx, line))
                    if len(matches) >= MAX_MATCHES_PER_FILE:
                        break
            if matches:
                lines.append("  encoding=%s keywordMatches=%d%s" % (
                    encoding, len(matches), " (truncated)" if len(matches) >= MAX_MATCHES_PER_FILE else ""
                ))
                for idx, line in matches:
                    lines.append("  L%04d: %s" % (idx, safe_str(line, 1200)))


def dump_qstandardpaths(lines):
    section(lines, "QSTANDARDPATHS")
    candidates = [
        ("AppConfigLocation", getattr(QtCore.QStandardPaths, "AppConfigLocation", None)),
        ("AppDataLocation", getattr(QtCore.QStandardPaths, "AppDataLocation", None)),
        ("ConfigLocation", getattr(QtCore.QStandardPaths, "ConfigLocation", None)),
        ("DataLocation", getattr(QtCore.QStandardPaths, "DataLocation", None)),
        ("GenericConfigLocation", getattr(QtCore.QStandardPaths, "GenericConfigLocation", None)),
        ("GenericDataLocation", getattr(QtCore.QStandardPaths, "GenericDataLocation", None)),
    ]
    for name, enum_value in candidates:
        if enum_value is None:
            continue
        try:
            lines.append("%s writable=%s" % (name, QtCore.QStandardPaths.writableLocation(enum_value)))
            lines.append("%s locations=%s" % (name, safe_str(QtCore.QStandardPaths.standardLocations(enum_value), 1000)))
        except Exception as exc:
            lines.append("%s error=%s" % (name, exc))


def main():
    out_path, idx = next_output_path()
    lines = []
    lines.append("TIMELINE PERSISTENT SETTINGS EXPLORATION")
    lines.append("time=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("outputPath=%s" % out_path)
    lines.append("python=%s" % sys.version.replace("\n", " "))
    lines.append("HOME=%s" % HOME)
    lines.append("NUKE_DIR=%s" % NUKE_DIR)
    lines.append("APPDATA=%s" % APPDATA)
    lines.append("LOCALAPPDATA=%s" % LOCALAPPDATA)

    dump_qstandardpaths(lines)
    dump_qsettings(lines)
    dump_recent_files(lines)
    dump_file_manifest_and_matches(lines)

    lines.append("")
    lines.append("END explore_timeline_persistent_settings_to_txt")
    with open(out_path, "w", encoding="utf-8", errors="replace") as handle:
        handle.write("\n".join(lines))
    print("# Result: saved %s" % out_path)


try:
    main()
except Exception:
    print("# Result: TRACEBACK")
    print(traceback.format_exc())
