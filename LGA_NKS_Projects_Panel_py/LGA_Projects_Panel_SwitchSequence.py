"""
____________________________________________________________________________________

  LGA_NKS_Projects_Panel_SwitchSequence v2.26 | Lega
  Hiero / Nuke Studio - Switch V3: HÍBRIDO OPTIMIZADO + LIMPIEZA TOTAL + CROSS-PROJECT

  🎯 SOLUCIÓN GANADORA FINAL:
  - Velocidad optimizada + Estado completo del viewer
  - NO crea duplicados + Mantiene viewer settings completos
  - ✅ Playhead: Preservado automáticamente por Hiero
  - ✅ Gain/Gamma/Saturation: Transferidos desde viewer anterior
  - ✅ UI: Redimensiona ventana + Scroll al top track
  - ✅ CIERRE EQUILIBRADO: Cierra viewer + timeline originales (método refresh)
  - ✅ CROSS-PROJECT: Cambia entre proyectos automáticamente

  ✅ CONFIRMADO: Funciona perfectamente - velocidad 0.63s con cierre equilibrado + cross-project.

  v2.26: Reinicia el log en cada cambio de timeline e inyecta el logger del Projects Panel en scripts shared
  v2.25: Agregado timeline pre-cleanup sobre la secuencia nueva.
         Elimina tracks NukeVFX y extiende BurnIn antes de los ajustes finales de UI.
  v2.24: Flag opcional para cerrar viewers + timelines viejos (deja solo el nuevo)
  v2.23: Flag opcional para cerrar TODOS los timelines viejos (deja solo el nuevo)
  v2.22: Apertura con duplicado y cierre simultáneo de viewer + timeline originales (método refresh)
  v2.21: Mejorada lógica de versiones: búsqueda en anteúltimo bloque y priorización de sufijos (_Mac)

  INTEGRACIÓN EN PANEL DE PROYECTOS:
  from switch_sequence_v3_final import switch_to_sequence_hybrid
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui
import time
import importlib.util
import os
from LGA_NKS_Projects_Panel_py.LGA_NKS_ProjectsPanel_Logging import (
    DEBUG,
    DEBUG_CONSOLE,
    DEBUG_LOG,
    debug_print,
    reset_debug_log,
)

# Si True, cierra TODOS los viewers + timelines viejos y deja solo el nuevo
CLOSE_ALL_TIMELINES = True

# Qt import (según entorno)
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt


def _process_events():
    """Procesa eventos de Qt para estabilidad."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def _get_viewer_state(viewer):
    """Captura estado del viewer (gain/gamma/saturation para transferir, sin time)."""
    if not viewer:
        return None
    try:
        return {
            "gain": viewer.gain(),
            "gamma": viewer.gamma(),
            "saturation": viewer.saturation(),
        }
    except Exception:
        return None


def _apply_viewer_settings(viewer, state):
    """Aplica ajustes del viewer (gain/gamma/saturation) - playhead lo maneja Hiero automáticamente."""
    if not viewer or not state:
        return
    try:
        # Aplicamos gain/gamma/saturation - el playhead lo preserva Hiero automáticamente
        if "gain" in state:
            viewer.setGain(state["gain"])
        if "gamma" in state:
            viewer.setGamma(state["gamma"])
        if "saturation" in state:
            viewer.setSaturation(state["saturation"])
    except Exception:
        pass


def _get_available_luts(player):
    """Devuelve lista de LUTs disponibles si el player lo soporta."""
    if not player:
        return None
    try:
        if hasattr(player, "LUTs"):
            luts = player.LUTs()
            if isinstance(luts, (list, tuple, set)):
                return list(luts)
    except Exception:
        return None
    return None


def _apply_rec709_if_available(viewer):
    """
    Aplica LUT ACES/Rec.709 solo si existe.
    Si no se puede verificar disponibilidad, intenta setearlo y valida.
    """
    if not viewer:
        return False
    try:
        player = viewer.player()
        if not player:
            return False

        target_lut = "ACES/Rec.709"
        available_luts = _get_available_luts(player)
        if available_luts is not None and target_lut not in available_luts:
            debug_print(f"   ├── LUT '{target_lut}' no disponible, se mantiene actual")
            return False

        previous_lut = None
        try:
            previous_lut = player.LUT()
        except Exception:
            previous_lut = None

        try:
            player.setLUT(target_lut)
        except Exception as e:
            debug_print(f"   ├── Error al setear LUT '{target_lut}': {e}")
            return False

        try:
            current_lut = player.LUT()
        except Exception:
            current_lut = None

        if current_lut and current_lut != target_lut:
            if previous_lut:
                try:
                    player.setLUT(previous_lut)
                except Exception:
                    pass
            debug_print(
                f"   ├── LUT '{target_lut}' no aplicado (actual: {current_lut})"
            )
            return False

        debug_print(f"   ├── LUT aplicado: {target_lut}")
        return True
    except Exception as e:
        debug_print(f"   ├── Error aplicando LUT Rec.709: {e}")
        return False


def _get_current_viewer_object_name():
    """Obtiene objectName del viewer activo actual."""
    try:
        current_viewer = hiero.ui.currentViewer()
        if not current_viewer:
            return None
        current_window = current_viewer.window()
        if current_window and hasattr(current_window, "objectName"):
            return current_window.objectName()
    except Exception:
        return None
    return None


def _get_current_timeline_object_name():
    """Obtiene objectName del timeline activo actual."""
    try:
        active_seq = hiero.ui.activeSequence()
        if not active_seq:
            return None
        current_timeline = hiero.ui.getTimelineEditor(active_seq)
        if not current_timeline:
            return None
        current_window = current_timeline.window()
        if current_window and hasattr(current_window, "objectName"):
            return current_window.objectName()
    except Exception:
        return None
    return None


def _close_old_viewer_and_timeline_safe(old_viewer_object_name, old_timeline_object_name):
    """
    Cierra viewer + timeline originales de forma SEGURA usando deleteLater().
    Mantiene el equilibrio delicado de Hiero cerrando ambos simultáneamente.
    """
    if not old_viewer_object_name and not old_timeline_object_name:
        return 0, 0

    closed_viewers = 0
    closed_timelines = 0

    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        app = QtWidgets.QApplication.instance()
        if not app:
            return 0, 0

        widgets_to_close = []

        for widget in app.allWidgets():
            try:
                obj_name = widget.objectName() if hasattr(widget, "objectName") else ""
                if not obj_name:
                    continue

                class_name = (
                    widget.metaObject().className()
                    if hasattr(widget, "metaObject")
                    else ""
                )

                if (
                    old_viewer_object_name
                    and obj_name == old_viewer_object_name
                    and "Foundry::Storm::UI::Viewer" in class_name
                ):
                    widgets_to_close.append(("viewer", widget))

                if (
                    old_timeline_object_name
                    and obj_name == old_timeline_object_name
                    and "TimelineEditor" in class_name
                ):
                    widgets_to_close.append(("timeline", widget))

            except Exception:
                continue

        # Cierre simultáneo para mantener equilibrio
        for widget_type, widget in widgets_to_close:
            try:
                widget.deleteLater()
                if widget_type == "viewer":
                    closed_viewers += 1
                elif widget_type == "timeline":
                    closed_timelines += 1
            except Exception:
                continue

        _process_events()

    except Exception:
        return closed_viewers, closed_timelines

    return closed_viewers, closed_timelines


def _close_all_other_viewers_and_timelines_safe(
    current_viewer_object_name, current_timeline_object_name
):
    """
    Cierra TODOS los viewers + timelines viejos dejando solo los actuales.
    Usa deleteLater() para evitar crashes en Hiero 16 y mantener equilibrio delicado.
    """
    if not current_viewer_object_name and not current_timeline_object_name:
        return 0, 0

    closed_viewers = 0
    closed_timelines = 0

    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        app = QtWidgets.QApplication.instance()
        if not app:
            return 0, 0

        widgets_to_close = []

        for widget in app.allWidgets():
            try:
                obj_name = widget.objectName() if hasattr(widget, "objectName") else ""
                if not obj_name:
                    continue

                class_name = (
                    widget.metaObject().className()
                    if hasattr(widget, "metaObject")
                    else ""
                )

                if "Foundry::Storm::UI::Viewer" in class_name:
                    if "contactsheet" in obj_name.lower():
                        continue
                    if current_viewer_object_name and obj_name != current_viewer_object_name:
                        widgets_to_close.append(("viewer", widget))

                if "TimelineEditor" in class_name:
                    if current_timeline_object_name and obj_name != current_timeline_object_name:
                        widgets_to_close.append(("timeline", widget))

            except Exception:
                continue

        for widget_type, widget in widgets_to_close:
            try:
                widget.deleteLater()
                if widget_type == "viewer":
                    closed_viewers += 1
                elif widget_type == "timeline":
                    closed_timelines += 1
            except Exception:
                continue

        _process_events()

    except Exception:
        return closed_viewers, closed_timelines

    return closed_viewers, closed_timelines


def _collect_viewers():
    """Devuelve lista de viewers Qt (Foundry::Storm::UI::Viewer) con título y visibilidad."""
    viewers = []
    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        all_widgets = QtWidgets.QApplication.instance().allWidgets()
        for widget in all_widgets:
            try:
                class_name = (
                    widget.metaObject().className()
                    if hasattr(widget, "metaObject")
                    else str(type(widget))
                )
                if "Foundry::Storm::UI::Viewer" in class_name:
                    title = (
                        widget.windowTitle() if hasattr(widget, "windowTitle") else ""
                    )
                    visible = (
                        widget.isVisible() if hasattr(widget, "isVisible") else False
                    )
                    viewers.append(
                        {"widget": widget, "title": title, "visible": visible}
                    )
            except Exception:
                continue
    except Exception:
        pass
    return viewers


def _pick_target_by_title(items, target_sequence_name):
    """Selecciona un item cuyo título coincida, priorizando los visibles."""
    visible_matches = [
        v for v in items if v.get("title") == target_sequence_name and v.get("visible")
    ]
    if visible_matches:
        return visible_matches[0]
    name_matches = [v for v in items if v.get("title") == target_sequence_name]
    if name_matches:
        return name_matches[0]
    return None


def _pick_target_viewer(viewers, target_sequence_name):
    return _pick_target_by_title(viewers, target_sequence_name)


def _collect_timelines():
    """Devuelve lista de timelines Qt (TimelineEditor) con título, visibilidad y secuencia asociada (si disponible)."""
    timelines = []
    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        all_widgets = QtWidgets.QApplication.instance().allWidgets()
        for widget in all_widgets:
            try:
                class_name = (
                    widget.metaObject().className()
                    if hasattr(widget, "metaObject")
                    else str(type(widget))
                )
                # Distintos nombres observados para timelines
                if "TimelineEditor" in class_name or "Timeline" in class_name:
                    title = (
                        widget.windowTitle() if hasattr(widget, "windowTitle") else ""
                    )
                    visible = (
                        widget.isVisible() if hasattr(widget, "isVisible") else False
                    )
                    seq_name = None
                    try:
                        seq = widget.sequence() if hasattr(widget, "sequence") else None
                        if seq:
                            seq_name = seq.name()
                    except Exception:
                        seq_name = None
                    timelines.append(
                        {
                            "widget": widget,
                            "title": title,
                            "visible": visible,
                            "seq_name": seq_name,
                        }
                    )
            except Exception:
                continue
    except Exception:
        pass
    return timelines


def _cleanup_viewers_aggressive(target_sequence_name):
    """
    Cierra TODOS los viewers excepto el correspondiente a la secuencia objetivo.
    - Mantiene únicamente el primer viewer con windowTitle == target_sequence_name (el activo).
    - Cierra duplicados y cualquier otro viewer/timeline residual.
    - Loggea estado antes/después para diagnóstico.
    """
    viewers = _collect_viewers()
    closed = []
    kept = []
    target_viewer = _pick_target_viewer(viewers, target_sequence_name)

    for entry in viewers:
        widget = entry["widget"]
        title = entry.get("title", "") or "<sin título>"
        visible = entry.get("visible", False)

        if target_viewer and widget == target_viewer["widget"]:
            kept.append(title)
            continue

        try:
            widget.deleteLater()
            _process_events()
            closed.append(title)
        except Exception:
            continue

    debug_print(
        f"   ├── Viewers antes: {len(viewers)} | cerrados: {len(closed)} | mantenidos: {len(kept)}"
    )
    if kept:
        debug_print(f"   │   Mantenidos: {kept}")
    if closed:
        debug_print(f"   │   Cerrados: {closed}")

    return len(closed), len(kept), kept, closed


def _cleanup_timelines_aggressive(target_sequence_name, target_seq_obj=None):
    """
    Cierra timelines (TimelineEditor) que no correspondan a la secuencia objetivo.
    Mantiene los timelines cuya secuencia asociada o título coincida con la secuencia objetivo.
    No cierra timelines de secuencia desconocida (para evitar dejar la UI sin timeline si no podemos determinar).
    """
    timelines = _collect_timelines()
    target_timeline = _pick_target_by_title(timelines, target_sequence_name)
    closed = []
    kept = []
    skipped = []

    for entry in timelines:
        widget = entry["widget"]
        title = entry.get("title", "") or "<sin título>"
        seq_name = entry.get("seq_name")

        # Mantener timelines que correspondan a la secuencia objetivo (por nombre de secuencia o por título)
        if (target_timeline and widget == target_timeline["widget"]) or (
            seq_name == target_sequence_name
        ):
            kept.append(title)
            continue

        # Si no podemos determinar la secuencia, no lo cerramos para no dejar la UI en gris
        if seq_name is None:
            skipped.append(title)
            continue

        try:
            widget.deleteLater()
            _process_events()
            closed.append(title)
        except Exception:
            continue

    debug_print(
        f"   ├── Timelines antes: {len(timelines)} | cerrados: {len(closed)} | mantenidos: {len(kept)} | omitidos (desconocidos): {len(skipped)}"
    )
    if kept:
        debug_print(f"   │   Timelines mantenidos: {kept}")
    if closed:
        debug_print(f"   │   Timelines cerrados: {closed}")
    if skipped:
        debug_print(f"   │   Timelines omitidos (seq desconocida): {skipped}")

    return len(closed), len(kept), kept, closed, skipped


def _focus_target_viewer(target_sequence_name):
    """Intenta enfocar el viewer de la secuencia objetivo después de la limpieza."""
    viewers = _collect_viewers()
    target = _pick_target_viewer(viewers, target_sequence_name)
    if not target:
        debug_print(
            f"   ├── No se encontró viewer para '{target_sequence_name}' tras limpieza"
        )
        return
    widget = target["widget"]
    try:
        widget.show()
        widget.raise_()
        widget.activateWindow()
        _process_events()
        debug_print(f"   ├── Viewer enfocado: {target_sequence_name}")
    except Exception:
        debug_print(f"   ├── No se pudo enfocar viewer '{target_sequence_name}'")


def import_script(script_name):
    """Importa script shared usado por Switch Sequence."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "LGA_NKS_Shared", script_name + ".py")

    if os.path.exists(script_path):
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "set_debug_handler"):
            module.set_debug_handler(debug_print)
        elif hasattr(module, "debug_print"):
            module.debug_print = debug_print
        if hasattr(module, "DEBUG"):
            module.DEBUG = DEBUG
        return module
    return None


def reduce_sequence_window(timeline_editor=None):
    """Reduce panel izquierdo del timeline."""
    try:
        reduce_module = import_script("LGA_NKS_Reduce_SeqWin")
        if reduce_module:
            reduce_module.main(timeline_editor)
            return True
    except Exception:
        pass
    return False


def scroll_to_top_track(timeline_editor=None):
    """Hace scroll al track superior."""
    try:
        scroll_module = import_script("LGA_NKS_ScrollTo_TopTrack")
        if scroll_module:
            scroll_module.main(timeline_editor)
            return True
    except Exception:
        pass
    return False


def switch_to_sequence_hybrid(target_sequence_name, target_project=None):
    """
    Switch HÍBRIDO V3 PERFECTO: Mejor que v4 + LIMPIEZA TOTAL + CROSS-PROJECT
    - Velocidad del v2 + Estado completo del v1
    - Sin duplicados + Mantiene viewer settings completos
    - ✅ Playhead: Preservado automáticamente por Hiero
    - ✅ Gain/Gamma/Saturation: Transferidos desde viewer anterior
    - ✅ UI: Redimensiona ventana + Scroll al top track
    - ✅ CIERRE EQUILIBRADO: Cierra viewer + timeline originales (método refresh)
    - ✅ OPCIONAL: Cierra TODOS los timelines viejos (flag CLOSE_ALL_TIMELINES)
    - ✅ CROSS-PROJECT: Cambia entre proyectos automáticamente
    """
    reset_debug_log()
    total_start = time.time()
    debug_print(f"🔄 Switch híbrido a '{target_sequence_name}'...")

    # 1. Verificar proyectos
    projects = hiero.core.projects()
    if not projects:
        debug_print("❌ Error: No hay proyectos abiertos")
        return False

    # 2. Buscar la secuencia en el proyecto especificado o en todos los proyectos
    target_seq = None

    if target_project:
        # Buscar en el proyecto específico
        try:
            sequences = target_project.sequences()
            for seq in sequences:
                try:
                    if seq.name() == target_sequence_name:
                        target_seq = seq
                        debug_print(
                            f"   ├── Secuencia encontrada en proyecto: {target_project.name()}"
                        )
                        break
                except Exception:
                    continue
        except Exception:
            pass
    else:
        # Búsqueda legacy: buscar en todos los proyectos disponibles
        for proj in projects:
            try:
                sequences = proj.sequences()
                for seq in sequences:
                    try:
                        if seq.name() == target_sequence_name:
                            target_seq = seq
                            if proj != projects[0]:
                                debug_print(
                                    f"   ├── Secuencia encontrada en proyecto: {proj.name()}"
                                )
                            break
                    except Exception:
                        continue
                if target_seq:
                    break
            except Exception:
                continue

    if not target_seq:
        debug_print(f"❌ Error: Secuencia '{target_sequence_name}' no encontrada")
        return False

    # 2. Verificar si ya estamos en la secuencia (OPTIMIZACIÓN)
    active_seq = None
    try:
        active_seq = hiero.ui.activeSequence()
    except Exception:
        active_seq = None

    if active_seq and active_seq.name() == target_sequence_name:
        debug_print("✅ Ya activa - sin cambios")
        return True

    # 3. Capturar ajustes del viewer ACTUAL (gain/gamma para transferir)
    step_start = time.time()
    current_viewer = hiero.ui.currentViewer()
    viewer_state = _get_viewer_state(current_viewer) if current_viewer else None
    viewer_capture_time = time.time() - step_start

    # 4. Capturar viewer + timeline actuales ANTES de duplicar (método refresh)
    old_viewer_object_name = _get_current_viewer_object_name()
    old_timeline_object_name = _get_current_timeline_object_name()

    # 5. Abrir secuencia con openInTimeline (como v2) - playhead se preserva automáticamente
    step_start = time.time()
    try:
        hiero.ui.openInTimeline(target_seq)
        _process_events()

        # Verificar que cambió correctamente
        new_active = hiero.ui.activeSequence()
        if not (new_active and new_active.name() == target_sequence_name):
            debug_print("❌ Error: Secuencia no cambió correctamente")
            return False

    except Exception as e:
        debug_print(f"❌ Error abriendo secuencia: {e}")
        return False

    open_time = time.time() - step_start
    new_timeline = hiero.ui.getTimelineEditor(new_active) if new_active else None

    # 6. CERRAR viewer + timeline ORIGINALES simultáneamente (método refresh)
    step_start = time.time()
    try:
        closed_viewers, closed_timelines = _close_old_viewer_and_timeline_safe(
            old_viewer_object_name, old_timeline_object_name
        )
        debug_print(
            f"   ├── Cerrados originales: viewers={closed_viewers}, timelines={closed_timelines}"
        )
    except Exception as e:
        debug_print(f"   ├── Error cerrando viewer/timeline originales: {e}")
        closed_viewers, closed_timelines = 0, 0
    close_time = time.time() - step_start

    # 7. Ejecutar pre-cleanup sobre la secuencia nueva antes de ajustes finales de UI
    step_start = time.time()
    try:
        precleanup_module = import_script("LGA_NKS_Timeline_PreCleanup")
        if precleanup_module:
            precleanup_result = precleanup_module.main()
            debug_print(f"   ├── Timeline pre-cleanup: {precleanup_result}")
        else:
            debug_print("   ├── No se pudo importar LGA_NKS_Timeline_PreCleanup")
    except Exception as e:
        debug_print(f"   ├── Error ejecutando timeline pre-cleanup: {e}")
    precleanup_time = time.time() - step_start

    # 8. Aplicar ajustes del viewer anterior (gain/gamma) - playhead ya está correcto
    viewer_restore_time = 0
    if viewer_state:
        step_start = time.time()
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            _apply_viewer_settings(new_viewer, viewer_state)
        viewer_restore_time = time.time() - step_start

    # 9. Enfocar viewer objetivo tras cierre (para evitar pantallas grises)
    _focus_target_viewer(target_sequence_name)

    # 10. Redimensionar ventana del timeline (como v4)
    step_start = time.time()
    reduce_success = reduce_sequence_window(new_timeline)
    reduce_time = time.time() - step_start

    # 11. Scrollear al top track (como v4)
    step_start = time.time()
    scroll_success = scroll_to_top_track(new_timeline)
    scroll_time = time.time() - step_start

    # 12. Cerrar TODOS los viewers + timelines viejos si el flag está activo
    close_all_widgets_time = 0
    if CLOSE_ALL_TIMELINES:
        step_start = time.time()
        current_viewer_object_name = _get_current_viewer_object_name()
        current_timeline_object_name = _get_current_timeline_object_name()
        closed_extra_viewers, closed_extra_timelines = (
            _close_all_other_viewers_and_timelines_safe(
                current_viewer_object_name, current_timeline_object_name
            )
        )
        close_all_widgets_time = time.time() - step_start
        debug_print(
            f"   ├── Close ALL old viewers: {closed_extra_viewers} cerrados"
        )
        debug_print(
            f"   ├── Close ALL old timelines: {closed_extra_timelines} cerrados"
        )

    # 13. Aplicar LUT Rec.709 si existe (evita reset a sRGB)
    rec709_time = 0
    rec709_applied = False
    step_start = time.time()
    try:
        rec709_applied = _apply_rec709_if_available(hiero.ui.currentViewer())
    except Exception as e:
        debug_print(f"   ├── Error aplicando LUT Rec.709: {e}")
    rec709_time = time.time() - step_start

    # 14. Resultado final
    total_time = time.time() - total_start
    debug_print(f"✅ Switch híbrido perfecto completado en {total_time:.2f}s")
    debug_print(f"   ├── Viewer capture: {viewer_capture_time:.3f}s")
    debug_print(f"   ├── Sequence open: {open_time:.3f}s")
    debug_print(f"   ├── Close originals (viewer+timeline): {close_time:.3f}s")
    debug_print(f"   ├── Timeline pre-cleanup: {precleanup_time:.3f}s")
    debug_print(f"   ├── Viewer settings apply: {viewer_restore_time:.3f}s")
    debug_print(f"   ├── UI reduce: {reduce_time:.3f}s")
    debug_print(f"   ├── UI scroll: {scroll_time:.3f}s")
    debug_print(
        f"   ├── Rec.709 apply: {rec709_time:.3f}s | applied={rec709_applied}"
    )
    if CLOSE_ALL_TIMELINES:
        debug_print(
            f"   ├── Close ALL old viewers+timelines: {close_all_widgets_time:.3f}s"
        )
    debug_print(f"   └── Total: {total_time:.2f}s")

    return True
