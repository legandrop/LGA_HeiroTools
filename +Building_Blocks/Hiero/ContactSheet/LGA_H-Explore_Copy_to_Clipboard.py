"""
LGA_H-Explore_Copy_to_Clipboard.py  v0.02
Exploración de approaches para copiar clips del timeline al clipboard desde Python.

Ejecutar desde Script Editor de Nuke Studio con clips seleccionados en el timeline.
"""

import hiero.core
import hiero.ui
from PySide2 import QtWidgets, QtCore, QtGui
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_clipboard_formats():
    """Lee formatos MIME actuales. Mantiene referencia para evitar GC crash."""
    app = QtWidgets.QApplication.instance()
    if not app:
        return set()
    clipboard = app.clipboard()
    mime = clipboard.mimeData()
    if mime is None:
        return set()
    try:
        return set(list(mime.formats()))
    except RuntimeError:
        return set()


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def result_ok(msg):
    print(f"  [✓ EXITO] {msg}")


def result_fail(msg):
    print(f"  [✗ sin cambio] {msg}")


# ---------------------------------------------------------------------------
# Setup inicial
# ---------------------------------------------------------------------------

app = QtWidgets.QApplication.instance()
seq = hiero.ui.activeSequence()
te = hiero.ui.getTimelineEditor(seq) if seq else None
selected = te.selection() if te else []
clips = [x for x in selected if not isinstance(x, hiero.core.EffectTrackItem)]

print("\n" + "="*60)
print("  LGA Explore: Copy clips to clipboard  v0.02")
print("="*60)
print(f"  Secuencia activa: {seq.name() if seq else 'NINGUNA'}")
print(f"  Timeline editor tipo: {type(te)}")
print(f"  Clips seleccionados: {len(clips)}")

if not clips:
    print("  ATENCION: Selecciona al menos un clip antes de ejecutar.")

# Estado inicial del clipboard
fmt_inicial = get_clipboard_formats()
print(f"  Formatos clipboard iniciales: {fmt_inicial}")


# ---------------------------------------------------------------------------
# SECCION 0: Que metodos tiene el TimelineEditor wrapper?
# ---------------------------------------------------------------------------
section("0. Metodos disponibles en ui.TimelineEditor")

te_methods = [m for m in dir(te) if not m.startswith("__")]
print(f"  Todos los metodos ({len(te_methods)}):")
for m in te_methods:
    print(f"    {m}")


# ---------------------------------------------------------------------------
# SECCION 1: Encontrar el QWidget real del timeline editor
# ---------------------------------------------------------------------------
section("1. Buscar el QWidget real del timeline editor")

# te.window() devuelve la ventana principal (lo sabemos del building block existente)
main_window = te.window() if hasattr(te, "window") else None
print(f"  te.window(): {type(main_window).__name__ if main_window else 'no disponible'}")
print(f"  main_window isWidget: {isinstance(main_window, QtWidgets.QWidget)}")

# Buscar widgets con nombre de clase relacionado a timeline
timeline_widget = None
candidate_classes = []
if main_window:
    all_widgets = main_window.findChildren(QtWidgets.QWidget)
    print(f"  Total widgets hijos de main_window: {len(all_widgets)}")
    for w in all_widgets:
        class_name = type(w).__name__.lower()
        if "timeline" in class_name or "sequence" in class_name or "track" in class_name:
            candidate_classes.append((type(w).__name__, w.focusPolicy(), w.isVisible()))
            if timeline_widget is None and w.isVisible():
                timeline_widget = w

    if candidate_classes:
        print(f"  Candidatos con 'timeline/sequence/track' en el nombre:")
        for name, fp, vis in candidate_classes:
            print(f"    {name}  focusPolicy={fp}  visible={vis}")
    else:
        print("  No se encontraron widgets con 'timeline/sequence/track' en el nombre")

    # También buscar el widget que actualmente tiene foco
    focus_widget = app.focusWidget()
    print(f"\n  focusWidget actual: {type(focus_widget).__name__ if focus_widget else 'None'}")


# ---------------------------------------------------------------------------
# APPROACH A: Ctrl+C al main_window (la ventana principal de Hiero)
# ---------------------------------------------------------------------------
section("A. Ctrl+C sendEvent al main_window de Hiero")

if main_window and clips:
    main_window.raise_()
    main_window.activateWindow()
    app.processEvents()

    fmt_antes = get_clipboard_formats()
    print(f"  focusWidget antes de key event: {type(app.focusWidget()).__name__ if app.focusWidget() else 'None'}")

    key_press = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")
    key_release = QtGui.QKeyEvent(
        QtCore.QEvent.KeyRelease, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")

    app.sendEvent(main_window, key_press)
    app.sendEvent(main_window, key_release)
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()

    fmt_despues = get_clipboard_formats()
    if fmt_despues != fmt_antes:
        result_ok(f"clipboard cambio!")
        print(f"    Antes: {fmt_antes}")
        print(f"    Despues: {fmt_despues}")
    else:
        result_fail(f"sin cambio (antes={fmt_antes}  despues={fmt_despues})")
else:
    print("  SKIP")


# ---------------------------------------------------------------------------
# APPROACH B: Ctrl+C al focusWidget dentro de main_window
# ---------------------------------------------------------------------------
section("B. setFocus en main_window + Ctrl+C al focusWidget resultante")

if main_window and clips:
    main_window.raise_()
    main_window.activateWindow()
    main_window.setFocus()
    app.processEvents()

    focus_w = app.focusWidget()
    print(f"  focusWidget tras activateWindow: {type(focus_w).__name__ if focus_w else 'None'}")

    target = focus_w if focus_w else main_window
    fmt_antes = get_clipboard_formats()

    key_press = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")
    key_release = QtGui.QKeyEvent(
        QtCore.QEvent.KeyRelease, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")

    app.sendEvent(target, key_press)
    app.sendEvent(target, key_release)
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()

    fmt_despues = get_clipboard_formats()
    if fmt_despues != fmt_antes:
        result_ok(f"clipboard cambio! target={type(target).__name__}")
        print(f"    Antes: {fmt_antes}")
        print(f"    Despues: {fmt_despues}")
    else:
        result_fail(f"sin cambio  target={type(target).__name__}")
else:
    print("  SKIP")


# ---------------------------------------------------------------------------
# APPROACH C: Ctrl+C al candidato timeline widget encontrado
# ---------------------------------------------------------------------------
section("C. Ctrl+C al widget hijo con 'timeline/sequence/track' en el nombre")

if timeline_widget and clips:
    print(f"  Target widget: {type(timeline_widget).__name__}")
    timeline_widget.setFocus()
    app.processEvents()

    fmt_antes = get_clipboard_formats()

    key_press = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")
    key_release = QtGui.QKeyEvent(
        QtCore.QEvent.KeyRelease, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")

    app.sendEvent(timeline_widget, key_press)
    app.sendEvent(timeline_widget, key_release)
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()

    fmt_despues = get_clipboard_formats()
    if fmt_despues != fmt_antes:
        result_ok("clipboard cambio!")
        print(f"    Antes: {fmt_antes}")
        print(f"    Despues: {fmt_despues}")
    else:
        result_fail("sin cambio")
elif not timeline_widget:
    print("  SKIP: no se encontro timeline widget candidato")
else:
    print("  SKIP: no hay clips")


# ---------------------------------------------------------------------------
# APPROACH D: Iterar TODOS los hijos visibles y enviar Ctrl+C a cada uno
#             hasta que el clipboard cambie
# ---------------------------------------------------------------------------
section("D. Fuerza bruta: Ctrl+C a cada hijo visible hasta que clipboard cambie")

if main_window and clips:
    fmt_base = get_clipboard_formats()
    encontrado = False
    all_w = main_window.findChildren(QtWidgets.QWidget)
    visible_w = [w for w in all_w if w.isVisible() and w.focusPolicy() != QtCore.Qt.NoFocus]
    print(f"  Widgets visibles con focus policy != NoFocus: {len(visible_w)}")

    for i, w in enumerate(visible_w):
        w.setFocus()
        app.processEvents()

        kp = QtGui.QKeyEvent(
            QtCore.QEvent.KeyPress, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")
        kr = QtGui.QKeyEvent(
            QtCore.QEvent.KeyRelease, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier, "")

        app.sendEvent(w, kp)
        app.sendEvent(w, kr)
        app.processEvents()

        fmt_now = get_clipboard_formats()
        if fmt_now != fmt_base:
            result_ok(f"clipboard cambio con widget #{i}: {type(w).__name__}")
            print(f"    Antes: {fmt_base}")
            print(f"    Despues: {fmt_now}")
            encontrado = True
            break

    if not encontrado:
        result_fail(f"ningun widget de los {len(visible_w)} produjo cambio en clipboard")
else:
    print("  SKIP")


# ---------------------------------------------------------------------------
# APPROACH E: action.trigger() con isEnabled check desactivado
#             (para medir si con main_window activo cambia el estado)
# ---------------------------------------------------------------------------
section("E. action.trigger() con main_window activo")

action = hiero.ui.findMenuAction("foundry.application.copy")
if action is None:
    for a in hiero.ui.registeredActions():
        if a.objectName() == "foundry.application.copy":
            action = a
            break

if action and main_window and clips:
    main_window.raise_()
    main_window.activateWindow()
    app.processEvents()
    print(f"  isEnabled despues de activateWindow: {action.isEnabled()}")

    fmt_antes = get_clipboard_formats()
    action.trigger()
    app.processEvents()
    fmt_despues = get_clipboard_formats()

    if fmt_despues != fmt_antes:
        result_ok("clipboard cambio!")
    else:
        result_fail(f"sin cambio  isEnabled={action.isEnabled()}")
else:
    print("  SKIP")


# ---------------------------------------------------------------------------
# APPROACH F: hiero.core / hiero.ui - metodos copy/clipboard/paste
# ---------------------------------------------------------------------------
section("F. Inspeccion API: hiero.core y hiero.ui")

if clips:
    clip = clips[0]
    copy_methods = sorted([m for m in dir(clip) if any(k in m.lower() for k in ("copy", "serial", "paste", "clip"))])
    print(f"  TrackItem metodos: {copy_methods}")

seq_methods = sorted([m for m in dir(seq) if any(k in m.lower() for k in ("copy", "serial", "paste"))]) if seq else []
print(f"  Sequence metodos: {seq_methods}")

hcore = sorted([m for m in dir(hiero.core) if any(k in m.lower() for k in ("copy", "clipboard", "paste", "serial"))])
print(f"  hiero.core: {hcore}")

hui = sorted([m for m in dir(hiero.ui) if any(k in m.lower() for k in ("copy", "clipboard", "paste", "serial"))])
print(f"  hiero.ui: {hui}")


# ---------------------------------------------------------------------------
# RESUMEN
# ---------------------------------------------------------------------------
section("RESUMEN FINAL")

fmt_final = get_clipboard_formats()
print(f"  Clipboard al inicio:  {fmt_inicial}")
print(f"  Clipboard al final:   {fmt_final}")
cambio_total = fmt_final != fmt_inicial
print(f"  Clipboard cambio en algun momento: {cambio_total}")

print("\n" + "="*60)
print("  Fin exploracion")
print("="*60)
