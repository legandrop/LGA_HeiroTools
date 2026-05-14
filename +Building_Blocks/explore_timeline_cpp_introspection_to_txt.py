"""
____________________________________________________________________

  explore_timeline_cpp_introspection_to_txt.py | Lega

  Introspeccion agresiva, de solo lectura, para el TimelineView C++.

  Objetivo:
    Buscar pistas para controlar por Python:
      - ancho visual de tracknames
      - alto visual de tracks

  Que hace:
    - obtiene punteros C++ con shiboken
    - dump de wrapper PySide/Shiboken
    - metaObject completo, incluyendo herencia, classInfo, enums, properties
    - metodos/slots completos del TimelineView y parents
    - acciones asociadas al TimelineView
    - introspeccion de modulos hiero/ui encontrados
    - busqueda local de strings en DLL/PYD/EXE de Nuke relacionados con
      TimelineView, track height/header/label width

  No modifica la UI, no invoca slots de cambio, no simula mouse.

  Guarda:
      C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/final_cpp_introspection_1.txt

  Uso:
      exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_cpp_introspection_to_txt.py").read())
____________________________________________________________________
"""

from __future__ import print_function

import gc
import inspect
import os
import re
import subprocess
import sys
import time
import traceback

import hiero.ui

try:
    from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore
except Exception:
    try:
        from PySide6 import QtWidgets, QtCore
    except Exception:
        from PySide2 import QtWidgets, QtCore


OUT_DIR = r"C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout"
PREFIX = "final_cpp_introspection"
NUKE_ROOT = r"C:\Program Files\Nuke15.1v6"

KEYWORDS = (
    "TimelineView", "TimelineEditor", "Timeline", "TrackName", "TrackNames",
    "TrackHeader", "TrackHeaders", "HeaderWidth", "LabelWidth",
    "TrackHeight", "TrackSize", "RowHeight", "LaneHeight",
    "setTrack", "trackWidth", "trackHeight", "trackName", "trackLabel",
    "collapseTracks", "splitViewsToTracks", "ResizeTrack", "TrackResize",
)

MAX_TEXT = 1000
MAX_DIR = 1500
MAX_REFS = 120
MAX_SYMBOL_FILES = 120
MAX_SYMBOL_MATCHES_PER_FILE = 80


def safe_str(value, limit=MAX_TEXT):
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


def class_name(obj):
    try:
        if hasattr(obj, "metaObject"):
            return obj.metaObject().className()
    except Exception:
        pass
    return type(obj).__name__


def object_name(obj):
    try:
        return obj.objectName()
    except Exception:
        return ""


def geom_text(widget):
    if not isinstance(widget, QtWidgets.QWidget):
        return ""
    try:
        g = widget.geometry()
        return " geometry=(%d,%d,%d,%d)" % (g.x(), g.y(), g.width(), g.height())
    except Exception:
        return ""


def find_timeline_editor():
    try:
        return hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
    except Exception:
        return None


def find_timeline_view(window):
    if not window:
        return None
    for widget in window.findChildren(QtWidgets.QWidget):
        if class_name(widget) == "Foundry::Storm::UI::TimelineView":
            return widget
    return None


def get_shiboken():
    for name in ("shiboken2", "shiboken6"):
        try:
            return name, __import__(name)
        except Exception:
            pass
    return None, None


def dump_shiboken(lines, label, obj):
    section(lines, "SHIBOKEN: %s" % label)
    if obj is None:
        lines.append("<none>")
        return
    mod_name, shiboken = get_shiboken()
    lines.append("module=%s" % mod_name)
    if not shiboken:
        lines.append("<no shiboken module>")
        return
    for fn_name in ("getCppPointer", "isValid", "ownedByPython", "createdByPython"):
        try:
            fn = getattr(shiboken, fn_name)
            lines.append("%s=%s" % (fn_name, safe_str(fn(obj))))
        except Exception as exc:
            lines.append("%s error=%s" % (fn_name, safe_str(exc)))
    try:
        dump = shiboken.dump(obj)
        lines.append("dump=%s" % safe_str(dump, 5000))
    except Exception as exc:
        lines.append("dump error=%s" % safe_str(exc))


def dump_python_object(lines, label, obj):
    section(lines, "PYTHON OBJECT: %s" % label)
    if obj is None:
        lines.append("<none>")
        return
    lines.append("repr=%s" % safe_str(repr(obj)))
    lines.append("type=%s module=%s" % (type(obj).__name__, getattr(type(obj), "__module__", "")))
    lines.append("className=%s objectName=%r%s" % (class_name(obj), object_name(obj), geom_text(obj)))
    try:
        lines.append("mro=%s" % safe_str(inspect.getmro(type(obj)), 3000))
    except Exception as exc:
        lines.append("mro error=%s" % exc)
    try:
        names = dir(obj)
    except Exception as exc:
        lines.append("dir error=%s" % exc)
        return
    lines.append("dirCount=%d" % len(names))
    for name in names[:MAX_DIR]:
        if name.startswith("__") and name.endswith("__"):
            continue
        try:
            attr = getattr(obj, name)
            marker = "callable" if callable(attr) else type(attr).__name__
        except Exception as exc:
            marker = "<getattr error: %s>" % safe_str(exc, 120)
        lines.append("  %s : %s" % (name, marker))
    if len(names) > MAX_DIR:
        lines.append("<dir truncated %d>" % (len(names) - MAX_DIR))


def method_type_name(method):
    try:
        return str(method.methodType()).split(".")[-1]
    except Exception:
        return safe_str(method.methodType())


def method_access_name(method):
    try:
        return str(method.access()).split(".")[-1]
    except Exception:
        return safe_str(method.access())


def dump_meta_chain(lines, label, obj):
    section(lines, "METAOBJECT CHAIN: %s" % label)
    if obj is None:
        lines.append("<none>")
        return
    try:
        mo = obj.metaObject()
    except Exception as exc:
        lines.append("metaObject error=%s" % exc)
        return
    chain = []
    while mo:
        chain.append(mo)
        mo = mo.superClass()
    for depth, meta in enumerate(chain):
        lines.append("")
        lines.append("-- depth=%d className=%s methodOffset=%d methodCount=%d propertyOffset=%d propertyCount=%d enumeratorOffset=%d enumeratorCount=%d classInfoOffset=%d classInfoCount=%d --" % (
            depth, meta.className(), meta.methodOffset(), meta.methodCount(),
            meta.propertyOffset(), meta.propertyCount(), meta.enumeratorOffset(),
            meta.enumeratorCount(), meta.classInfoOffset(), meta.classInfoCount()
        ))
        lines.append("CLASSINFO:")
        for i in range(meta.classInfoOffset(), meta.classInfoCount()):
            try:
                ci = meta.classInfo(i)
                lines.append("  %03d %s=%s" % (i, ci.name(), ci.value()))
            except Exception as exc:
                lines.append("  %03d error=%s" % (i, exc))
        lines.append("ENUMS:")
        for i in range(meta.enumeratorOffset(), meta.enumeratorCount()):
            try:
                en = meta.enumerator(i)
                vals = []
                for k in range(en.keyCount()):
                    vals.append("%s=%s" % (en.key(k), en.value(k)))
                lines.append("  %03d name=%s scoped=%s flags=%s values=%s" % (
                    i, en.name(), en.isScoped(), en.isFlag(), safe_str(", ".join(vals), 2500)
                ))
            except Exception as exc:
                lines.append("  %03d error=%s" % (i, exc))
        lines.append("PROPERTIES:")
        for i in range(meta.propertyOffset(), meta.propertyCount()):
            try:
                prop = meta.property(i)
                try:
                    value = prop.read(obj)
                except Exception as exc:
                    value = "<read error: %s>" % exc
                lines.append("  %03d name=%s type=%s writable=%s resettable=%s stored=%s designable=%s user=%s value=%s" % (
                    i, prop.name(), prop.typeName(), prop.isWritable(), prop.isResettable(),
                    prop.isStored(obj), prop.isDesignable(obj), prop.isUser(obj), safe_str(value)
                ))
            except Exception as exc:
                lines.append("  %03d error=%s" % (i, exc))
        lines.append("METHODS:")
        for i in range(meta.methodOffset(), meta.methodCount()):
            try:
                method = meta.method(i)
                try:
                    signature = bytes(method.methodSignature()).decode("utf-8", "replace")
                except Exception:
                    signature = safe_str(method.methodSignature())
                try:
                    name = bytes(method.name()).decode("utf-8", "replace")
                except Exception:
                    name = safe_str(method.name())
                try:
                    params = [bytes(p).decode("utf-8", "replace") for p in method.parameterNames()]
                except Exception:
                    params = []
                lines.append("  %03d type=%s access=%s name=%s signature=%s params=%s return=%s" % (
                    i, method_type_name(method), method_access_name(method), name, signature,
                    safe_str(params), safe_str(method.typeName())
                ))
            except Exception as exc:
                lines.append("  %03d error=%s" % (i, exc))


def dump_actions(lines, label, widget):
    section(lines, "ACTIONS: %s" % label)
    if widget is None:
        lines.append("<none>")
        return
    widgets = []
    cur = widget
    while cur:
        widgets.append(cur)
        try:
            cur = cur.parentWidget()
        except Exception:
            cur = None
    seen = set()
    for owner in widgets:
        try:
            actions = owner.actions()
        except Exception:
            actions = []
        lines.append("-- owner class=%s objectName=%r%s actionCount=%d" % (
            class_name(owner), object_name(owner), geom_text(owner), len(actions)
        ))
        for action in actions:
            key = id(action)
            if key in seen:
                continue
            seen.add(key)
            try:
                lines.append("  action objectName=%r text=%r toolTip=%r statusTip=%r shortcut=%r enabled=%s checkable=%s checked=%s" % (
                    action.objectName(), action.text(), safe_str(action.toolTip(), 200),
                    safe_str(action.statusTip(), 200), action.shortcut().toString(),
                    action.isEnabled(), action.isCheckable(),
                    action.isChecked() if action.isCheckable() else ""
                ))
            except Exception as exc:
                lines.append("  action error=%s" % exc)


def dump_gc_refs(lines, obj):
    section(lines, "GC REFERRERS TO TIMELINEVIEW WRAPPER")
    if obj is None:
        lines.append("<none>")
        return
    try:
        refs = gc.get_referrers(obj)
    except Exception as exc:
        lines.append("gc.get_referrers error=%s" % exc)
        return
    lines.append("referrerCount=%d" % len(refs))
    for idx, ref in enumerate(refs[:MAX_REFS]):
        lines.append("%03d type=%s repr=%s" % (idx, type(ref).__name__, safe_str(repr(ref), 800)))
    if len(refs) > MAX_REFS:
        lines.append("<truncated %d>" % (len(refs) - MAX_REFS))


def dump_hiero_modules(lines):
    section(lines, "HIERO/UI MODULE INTROSPECTION")
    modules = []
    for mod_name in ("hiero", "hiero.ui", "hiero.core"):
        try:
            modules.append((mod_name, __import__(mod_name, fromlist=["*"])))
        except Exception as exc:
            lines.append("%s import error=%s" % (mod_name, exc))
    for mod_name, mod in modules:
        lines.append("")
        lines.append("-- module %s file=%s --" % (mod_name, getattr(mod, "__file__", "")))
        try:
            names = dir(mod)
        except Exception as exc:
            lines.append("dir error=%s" % exc)
            continue
        for name in names:
            blob = name
            if not any(k.lower() in blob.lower() for k in KEYWORDS):
                continue
            try:
                attr = getattr(mod, name)
            except Exception as exc:
                lines.append("  %s <getattr error=%s>" % (name, exc))
                continue
            lines.append("  %s type=%s repr=%s" % (name, type(attr).__name__, safe_str(repr(attr), 600)))


def iter_binary_candidates(root):
    if not os.path.isdir(root):
        return
    exts = (".dll", ".pyd", ".exe")
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        low = dirpath.lower()
        if any(skip in low for skip in ("\\qtwebengine", "\\documentation", "\\plugins\\platforms")):
            continue
        for name in filenames:
            if not name.lower().endswith(exts):
                continue
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except Exception:
                continue
            if size <= 0 or size > 250 * 1024 * 1024:
                continue
            count += 1
            if count > MAX_SYMBOL_FILES:
                return
            yield full


def ascii_strings_from_bytes(data, min_len=5):
    cur = []
    for b in data:
        if 32 <= b <= 126:
            cur.append(chr(b))
        else:
            if len(cur) >= min_len:
                yield "".join(cur)
            cur = []
    if len(cur) >= min_len:
        yield "".join(cur)


def dump_binary_string_search(lines):
    section(lines, "LOCAL BINARY STRING SEARCH")
    lines.append("NUKE_ROOT=%s exists=%s" % (NUKE_ROOT, os.path.isdir(NUKE_ROOT)))
    keyword_lows = [k.lower() for k in KEYWORDS]
    for path in iter_binary_candidates(NUKE_ROOT):
        matches = []
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except Exception as exc:
            lines.append("FILE_ERROR %s %s" % (path, exc))
            continue
        for text in ascii_strings_from_bytes(data):
            low = text.lower()
            if any(k in low for k in keyword_lows):
                matches.append(text)
                if len(matches) >= MAX_SYMBOL_MATCHES_PER_FILE:
                    break
        if matches:
            try:
                rel = os.path.relpath(path, NUKE_ROOT)
            except Exception:
                rel = path
            lines.append("")
            lines.append("FILE %s matches=%d" % (rel, len(matches)))
            for match in matches:
                lines.append("  %s" % safe_str(match, 1200))


def main():
    out_path, _ = next_output_path()
    lines = []
    lines.append("TIMELINE CPP INTROSPECTION")
    lines.append("time=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("outputPath=%s" % out_path)
    lines.append("python=%s" % sys.version.replace("\n", " "))

    editor = find_timeline_editor()
    window = None
    try:
        window = editor.window() if editor else None
    except Exception:
        window = None
    timeline_view = find_timeline_view(window)
    viewport = None
    try:
        viewport = timeline_view.viewport() if timeline_view else None
    except Exception:
        viewport = None

    dump_python_object(lines, "TimelineEditor", editor)
    dump_python_object(lines, "TimelineEditor.window()", window)
    dump_python_object(lines, "TimelineView", timeline_view)
    dump_python_object(lines, "TimelineView.viewport()", viewport)
    dump_shiboken(lines, "TimelineView", timeline_view)
    dump_shiboken(lines, "TimelineView.viewport()", viewport)
    dump_meta_chain(lines, "TimelineView", timeline_view)
    dump_meta_chain(lines, "TimelineView.viewport()", viewport)
    dump_actions(lines, "TimelineView and parents", timeline_view)
    dump_gc_refs(lines, timeline_view)
    dump_hiero_modules(lines)
    dump_binary_string_search(lines)

    lines.append("")
    lines.append("END explore_timeline_cpp_introspection_to_txt")
    with open(out_path, "w", encoding="utf-8", errors="replace") as handle:
        handle.write("\n".join(lines))
    print("# Result: saved %s" % out_path)


try:
    main()
except Exception:
    print("# Result: TRACEBACK")
    print(traceback.format_exc())

