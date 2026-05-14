"""
____________________________________________________________________

  explore_timeline_private_tools_to_txt.py | Lega

  Exploracion enfocada en las tools privadas encontradas en studio-15.1.6.dll:

    - Hiero::TimelineToolTrackHeaderWidth
    - Hiero::TimelineToolTrackHeight

  Objetivo:
    Encontrar si esas tools se pueden activar/consultar desde Python sin mouse:

    - QAction / registered action
    - tool group
    - currentTool en uistate.ini
    - QObject vivo relacionado
    - factory/registry en hiero.ui o QApplication
    - strings cercanos en studio-15.1.6.dll

  No modifica la UI, no dispara acciones y no invoca slots de cambio.

  Uso:
      exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_private_tools_to_txt.py").read())
____________________________________________________________________
"""

from __future__ import print_function

import os
import re
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
PREFIX = "final_private_tools"
STUDIO_DLL = r"C:\Program Files\Nuke15.1v6\studio-15.1.6.dll"
UISTATE = r"C:\Users\leg4-pc\.nuke\uistate.ini"

KEYWORDS = (
    "TimelineToolTrackHeaderWidth",
    "TimelineToolTrackHeight",
    "TrackHeaderWidth",
    "TrackHeight",
    "TrackHeader",
    "HeaderWidth",
    "trackHeader",
    "trackHeight",
    "timelineTool",
    "timelineToolGroup",
    "currentTool",
    "foundry.timeline",
    "ToolGroup",
    "Toolbox",
    "TimelineTool",
)

MAX_VALUE = 900
MAX_ACTIONS = 1200
MAX_WIDGETS = 1000


def safe_str(value, limit=MAX_VALUE):
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
            return path
        idx += 1


def class_name(obj):
    try:
        if hasattr(obj, "metaObject"):
            return obj.metaObject().className()
    except Exception:
        pass
    return type(obj).__name__


def geom_text(widget):
    if not isinstance(widget, QtWidgets.QWidget):
        return ""
    try:
        g = widget.geometry()
        return " geometry=(%d,%d,%d,%d)" % (g.x(), g.y(), g.width(), g.height())
    except Exception:
        return ""


def matches(text):
    low = text.lower()
    return any(k.lower() in low for k in KEYWORDS)


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


def dump_uistate(lines):
    section(lines, "UISTATE TIMELINE CURRENT TOOL")
    if not os.path.exists(UISTATE):
        lines.append("<missing %s>" % UISTATE)
        return
    try:
        raw = open(UISTATE, "r", encoding="utf-8", errors="replace").read().splitlines()
    except Exception as exc:
        lines.append("<read error: %s>" % exc)
        return
    in_timeline = False
    for idx, line in enumerate(raw, 1):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_timeline = stripped.lower() == "[timeline]"
        if in_timeline or matches(line):
            lines.append("L%04d: %s" % (idx, line))


def dump_registered_actions(lines):
    section(lines, "HIERO REGISTERED ACTION LOOKUP")
    names = [
        "foundry.timeline.timelineToolGroup1",
        "foundry.timeline.timelineToolGroup2",
        "foundry.timeline.timelineToolGroup3",
        "foundry.timeline.timelineToolGroup4",
        "foundry.timeline.timelineToolGroup5",
        "foundry.timeline.selectMultiTool",
        "foundry.timeline.selectTool",
        "foundry.timeline.trackHeaderWidth",
        "foundry.timeline.trackHeight",
        "foundry.timeline.collapseTracks",
        "foundry.timeline.splitViews",
    ]
    for name in names:
        try:
            action = hiero.ui.findMenuAction(name)
        except Exception as exc:
            lines.append("%s -> ERROR %s" % (name, exc))
            continue
        if action is None:
            lines.append("%s -> <none>" % name)
            continue
        lines.append("%s -> objectName=%r text=%r tooltip=%r shortcut=%r enabled=%s checkable=%s checked=%s" % (
            name, action.objectName(), action.text(), safe_str(action.toolTip(), 250),
            action.shortcut().toString(), action.isEnabled(), action.isCheckable(),
            action.isChecked() if action.isCheckable() else ""
        ))


def dump_all_actions(lines):
    section(lines, "ALL QAPPLICATION ACTIONS MATCHING TOOL/TIMELINE KEYWORDS")
    app = QtWidgets.QApplication.instance()
    if not app:
        lines.append("<no QApplication>")
        return
    found = []
    for widget in app.allWidgets():
        try:
            actions = widget.actions()
        except Exception:
            continue
        for action in actions:
            try:
                blob = " ".join([
                    action.objectName() or "",
                    action.text() or "",
                    action.toolTip() or "",
                    action.statusTip() or "",
                    action.shortcut().toString() or "",
                    class_name(widget),
                ])
            except Exception:
                continue
            if matches(blob):
                found.append((widget, action, blob))
    seen = set()
    for widget, action, blob in found[:MAX_ACTIONS]:
        key = (id(action), action.objectName(), action.text())
        if key in seen:
            continue
        seen.add(key)
        lines.append("ownerClass=%s ownerObject=%r%s actionObject=%r text=%r tooltip=%r status=%r shortcut=%r enabled=%s checkable=%s checked=%s" % (
            class_name(widget), getattr(widget, "objectName", lambda: "")(), geom_text(widget),
            action.objectName(), action.text(), safe_str(action.toolTip(), 250),
            safe_str(action.statusTip(), 250), action.shortcut().toString(),
            action.isEnabled(), action.isCheckable(),
            action.isChecked() if action.isCheckable() else ""
        ))
    lines.append("uniqueMatched=%d rawMatched=%d" % (len(seen), len(found)))


def dump_tool_widgets(lines):
    section(lines, "LIVE WIDGETS/QOBJECTS MATCHING TOOL KEYWORDS")
    app = QtWidgets.QApplication.instance()
    if not app:
        lines.append("<no QApplication>")
        return
    count = 0
    for widget in app.allWidgets():
        if count >= MAX_WIDGETS:
            lines.append("<truncated>")
            break
        bits = []
        for attr in ("objectName", "windowTitle", "toolTip", "statusTip", "whatsThis"):
            try:
                bits.append(getattr(widget, attr)() or "")
            except Exception:
                pass
        bits.append(class_name(widget))
        try:
            if isinstance(widget, QtWidgets.QAbstractButton):
                bits.append(widget.text() or "")
        except Exception:
            pass
        blob = " ".join(bits)
        if not matches(blob):
            continue
        count += 1
        lines.append("class=%s py=%s objectName=%r title=%r text=%r tooltip=%r%s" % (
            class_name(widget), type(widget).__name__,
            getattr(widget, "objectName", lambda: "")(),
            getattr(widget, "windowTitle", lambda: "")(),
            widget.text() if isinstance(widget, QtWidgets.QAbstractButton) else "",
            safe_str(getattr(widget, "toolTip", lambda: "")(), 250),
            geom_text(widget),
        ))
        try:
            for prop in widget.dynamicPropertyNames():
                try:
                    pname = bytes(prop).decode("utf-8", "replace")
                except Exception:
                    pname = safe_str(prop)
                if matches(pname):
                    lines.append("  dynamic %s=%s" % (pname, safe_str(widget.property(pname))))
        except Exception:
            pass
    lines.append("matchedWidgets=%d" % count)


def dump_timeline_children_and_parents(lines):
    section(lines, "TIMELINE VIEW/PARENT CONTEXT")
    editor = find_timeline_editor()
    window = editor.window() if editor else None
    view = find_timeline_view(window)
    lines.append("TimelineEditor=%s class=%s" % (safe_str(repr(editor)), type(editor).__name__ if editor else None))
    lines.append("TimelineWindow=%s class=%s%s" % (safe_str(repr(window)), class_name(window) if window else None, geom_text(window)))
    lines.append("TimelineView=%s class=%s%s" % (safe_str(repr(view)), class_name(view) if view else None, geom_text(view)))
    cur = view
    depth = 0
    while cur is not None:
        lines.append("parentDepth=%d class=%s objectName=%r%s" % (
            depth, class_name(cur), getattr(cur, "objectName", lambda: "")(), geom_text(cur)
        ))
        try:
            cur = cur.parentWidget()
        except Exception:
            cur = None
        depth += 1
    if view:
        lines.append("TimelineView children:")
        for child in view.children():
            lines.append("  class=%s py=%s objectName=%r%s" % (
                class_name(child), type(child).__name__,
                getattr(child, "objectName", lambda: "")(), geom_text(child)
            ))


def ascii_strings_with_offsets(data, min_len=4):
    cur = []
    start = None
    for i, b in enumerate(data):
        if 32 <= b <= 126:
            if start is None:
                start = i
            cur.append(chr(b))
        else:
            if start is not None and len(cur) >= min_len:
                yield start, "".join(cur)
            cur = []
            start = None
    if start is not None and len(cur) >= min_len:
        yield start, "".join(cur)


def dump_nearby_dll_strings(lines):
    section(lines, "STUDIO DLL STRINGS AROUND PRIVATE TOOL CLASSES")
    if not os.path.exists(STUDIO_DLL):
        lines.append("<missing %s>" % STUDIO_DLL)
        return
    try:
        data = open(STUDIO_DLL, "rb").read()
    except Exception as exc:
        lines.append("<read error: %s>" % exc)
        return
    strings = list(ascii_strings_with_offsets(data, 4))
    targets = [
        "TimelineToolTrackHeaderWidth",
        "TimelineToolTrackHeight",
        "TimelineTool",
        "TrackHeader",
        "TrackHeight",
        "HeaderWidth",
        "foundry.timeline.timelineToolGroup",
        "foundry.timeline",
    ]
    for target in targets:
        section(lines, "STRINGS NEAR: %s" % target)
        positions = [i for i, (_, s) in enumerate(strings) if target.lower() in s.lower()]
        lines.append("matches=%d" % len(positions))
        for idx in positions[:20]:
            lines.append("-- matchIndex=%d offset=0x%X text=%s" % (idx, strings[idx][0], safe_str(strings[idx][1], 1400)))
            for j in range(max(0, idx - 18), min(len(strings), idx + 19)):
                mark = ">>" if j == idx else "  "
                off, s = strings[j]
                lines.append("%s 0x%08X %s" % (mark, off, safe_str(s, 1400)))


def dump_hiero_ui_names(lines):
    section(lines, "HIERO.UI / MODULE NAMES MATCHING TOOL KEYWORDS")
    modules = []
    for mod_name in ("hiero", "hiero.ui", "hiero.core"):
        try:
            modules.append((mod_name, __import__(mod_name, fromlist=["*"])))
        except Exception as exc:
            lines.append("%s import error=%s" % (mod_name, exc))
    for mod_name, mod in modules:
        lines.append("-- module %s file=%s" % (mod_name, getattr(mod, "__file__", "")))
        for name in dir(mod):
            if not matches(name):
                continue
            try:
                obj = getattr(mod, name)
            except Exception as exc:
                lines.append("  %s error=%s" % (name, exc))
                continue
            lines.append("  %s type=%s repr=%s" % (name, type(obj).__name__, safe_str(repr(obj), 700)))


def main():
    out = next_output_path()
    lines = []
    lines.append("TIMELINE PRIVATE TOOL EXPLORATION")
    lines.append("time=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("outputPath=%s" % out)
    lines.append("python=%s" % sys.version.replace("\n", " "))

    dump_uistate(lines)
    dump_registered_actions(lines)
    dump_all_actions(lines)
    dump_tool_widgets(lines)
    dump_timeline_children_and_parents(lines)
    dump_hiero_ui_names(lines)
    dump_nearby_dll_strings(lines)

    lines.append("")
    lines.append("END explore_timeline_private_tools_to_txt")
    with open(out, "w", encoding="utf-8", errors="replace") as handle:
        handle.write("\n".join(lines))
    print("# Result: saved %s" % out)


try:
    main()
except Exception:
    print("# Result: TRACEBACK")
    print(traceback.format_exc())

