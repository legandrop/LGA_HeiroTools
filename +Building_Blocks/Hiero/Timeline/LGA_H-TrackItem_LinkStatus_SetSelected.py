"""
____________________________________________________________________

  LGA_H-TrackItem_LinkStatus_SetSelected | Lega

  Prueba minima para setear versionLinkedToBin=True en clips seleccionados.

  ADVERTENCIA:
  - Esta API ya crasheo Hiero cuando se llamo durante la creacion del TrackItem.
  - Usar solo con un proyecto de prueba o despues de guardar.
  - Seleccionar solo el clip creado por Python que tenga versionLinkedToBin=False.
____________________________________________________________________
"""

import traceback

import hiero.core
import hiero.ui


def log(message=""):
    print("[LinkStatus SetSelected] %s" % message)


def safe_call(obj, method_name, default=None):
    if obj is None:
        return default
    try:
        attr = getattr(obj, method_name)
    except Exception:
        return default
    try:
        return attr() if callable(attr) else attr
    except Exception as exc:
        return "<ERROR %s: %s>" % (method_name, exc)


def set_selected_link_status():
    seq = hiero.ui.activeSequence()
    if not seq:
        log("No active sequence.")
        return

    editor = hiero.ui.getTimelineEditor(seq)
    selection = editor.selection() if editor else []
    log("Seleccionados: %d" % len(selection))
    if not selection:
        log("Selecciona un TrackItem y corre de nuevo.")
        return

    project = seq.project()
    log("Project trackItemVersionsLinkedToBin: %s" % safe_call(project, "trackItemVersionsLinkedToBin", "<no disponible>"))

    for index, item in enumerate(selection, start=1):
        log("")
        log("Seleccion #%d" % index)
        if isinstance(item, hiero.core.EffectTrackItem):
            log("Es EffectTrackItem. Se omite.")
            continue
        if not isinstance(item, hiero.core.TrackItem):
            log("No es TrackItem. Se omite.")
            continue

        log("TrackItem: %s" % safe_call(item, "name", "<sin nombre>"))
        log("Track: %s" % safe_call(safe_call(item, "parentTrack"), "name", "<sin track>"))
        log("Antes versionLinkedToBin: %s" % safe_call(item, "versionLinkedToBin", "<no disponible>"))
        log("CurrentVersion: %s" % safe_call(item, "currentVersion", "<no disponible>"))

        try:
            item.setVersionLinkedToBin(True)
            log("setVersionLinkedToBin(True) ejecutado.")
        except Exception:
            log("ERROR ejecutando setVersionLinkedToBin(True):")
            log(traceback.format_exc())
            continue

        log("Despues versionLinkedToBin: %s" % safe_call(item, "versionLinkedToBin", "<no disponible>"))
        log("CurrentVersion despues: %s" % safe_call(item, "currentVersion", "<no disponible>"))


if __name__ == "__main__":
    set_selected_link_status()
