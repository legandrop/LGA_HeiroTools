"""
Hiero / Nuke Studio - Switch DEFINITIVO: Cerrar→Reabrir (SOLUCIÓN PERFECTA)
===============================================================================

🎯 ESTRATEGIA DEFINITIVA GANADORA (LIMPIA Y OPTIMIZADA):
- Busca viewer existente por windowTitle()
- Si existe → CIERRALO para evitar duplicados
- Siempre usa openInTimeline() que funciona perfectamente
- Resultado: Sin duplicados, secuencia activada correctamente, con timer

✅ CONFIRMADO: Funciona perfectamente - sin prints innecesarios, con medición de tiempo.

Hardcodeado a: "010-350"
"""

import hiero.core
import hiero.ui

# Qt import (según entorno)
try:
    from PySide2 import QtCore
except Exception:
    try:
        from PySide6 import QtCore
    except Exception:
        QtCore = None


TARGET_SEQUENCE_NAME = "010-350"


def _process_events():
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def _is_timeline_integrated(ed):
    """Verifica si el timeline editor está integrado en la UI principal o es flotante."""
    if not ed:
        return False

    try:
        w = ed.window()
        if not w:
            print("🔍 Editor sin ventana accesible - probablemente integrado.")
            return True  # Sin ventana accesible = probablemente integrado

        # Verificar si es una ventana principal o flotante
        window_title = w.windowTitle() if hasattr(w, 'windowTitle') else "Sin título"
        is_main_window = w.isWindow() and not w.parent()

        print(f"🔍 Ventana del editor: '{window_title}' - Main window: {is_main_window}")

        # Si tiene título de "Timeline" o similar, puede ser flotante
        if "timeline" in window_title.lower() or "editor" in window_title.lower():
            print("⚠️ Detectada ventana flotante de timeline.")
            return False

        return True

    except Exception as e:
        print(f"⚠️ Error verificando integración: {e}")
        return True  # Asumir integrado si no podemos verificar


def _focus_timeline_editor(ed):
    """Intenta traer al frente la ventana del TimelineEditor."""
    if not ed:
        return False

    try:
        # Primero verificar si está integrado
        if not _is_timeline_integrated(ed):
            print("⚠️ Timeline parece estar en ventana flotante.")
            return False

        w = ed.window()
        if not w:
            print("✅ Editor integrado (sin ventana separada).")
            return True  # Ya está integrado, no necesita focus

        # traer al frente (Qt)
        try:
            w.show()
        except Exception:
            pass
        try:
            w.raise_()
        except Exception:
            pass
        try:
            w.activateWindow()
        except Exception:
            pass
        try:
            w.setFocus()
        except Exception:
            pass

        _process_events()
        return True

    except Exception as e:
        print(f"⚠️ Error en focus: {e}")
        return False


def _get_first_open_project():
    projects = hiero.core.projects()
    if not projects:
        return None
    return projects[0]


def _find_sequence_by_name(project, name):
    if not project:
        return None
    for seq in project.sequences():
        try:
            if seq.name() == name:
                return seq
        except Exception:
            pass
    return None


def _find_integrated_timeline_editor():
    """
    Busca el timeline editor integrado en la UI principal de Hiero.
    Retorna el editor si lo encuentra, None si no.
    """
    try:
        # Obtener la secuencia activa actual
        active_seq = hiero.ui.activeSequence()
        if not active_seq:
            return None

        # Obtener el timeline editor para la secuencia activa
        ed = hiero.ui.getTimelineEditor(active_seq)
        if not ed:
            return None

        # Verificar si está integrado (sin ventana separada)
        w = ed.window()
        if w:
            # Si tiene ventana pero no es flotante, puede estar integrado
            window_title = w.windowTitle() if hasattr(w, 'windowTitle') else ""
            # Si el título contiene el nombre de la secuencia, puede ser flotante
            if active_seq.name() in window_title and "010-350" not in window_title:
                print(f"🔍 Timeline con título '{window_title}' - parece flotante.")
                return None

        print("✅ Timeline integrado encontrado.")
        return ed

    except Exception as e:
        print(f"⚠️ Error buscando timeline integrado: {e}")
        return None


def _change_sequence_in_existing_timeline(target_seq):
    """
    Intenta cambiar la secuencia en el timeline integrado existente.
    """
    print("🔄 Intentando cambiar secuencia en timeline existente...")

    try:
        # Buscar el timeline integrado
        existing_ed = _find_integrated_timeline_editor()
        if not existing_ed:
            print("⚠️ No se encontró timeline integrado.")
            return False

        # Intentar métodos directos en el editor
        methods_to_try = ['setSequence', 'setActiveSequence', 'switchToSequence']

        for method_name in methods_to_try:
            if hasattr(existing_ed, method_name):
                print(f"🔧 Intentando {method_name}...")
                try:
                    getattr(existing_ed, method_name)(target_seq)
                    _process_events()

                    # Verificar si cambió
                    new_active = hiero.ui.activeSequence()
                    if new_active and new_active.name() == target_seq.name():
                        print(f"✅ {method_name} funcionó!")
                        return True
                    else:
                        print(f"⚠️ {method_name} ejecutado pero secuencia no cambió.")
                except Exception as e:
                    print(f"⚠️ {method_name} falló: {e}")

        print("❌ Ningún método directo funcionó.")
        return False

    except Exception as e:
        print(f"❌ Error cambiando secuencia en timeline existente: {e}")
        return False


def _find_viewer_widgets():
    """Encuentra todos los widgets de viewer en la aplicación."""
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        all_widgets = QtWidgets.QApplication.instance().allWidgets()

        viewer_widgets = []
        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else str(type(widget))
                if 'Foundry::Storm::UI::Viewer' in class_name:
                    viewer_widgets.append(widget)
            except Exception:
                continue

        return viewer_widgets
    except Exception as e:
        print(f"❌ Error buscando viewer widgets: {e}")
        return []


def _find_viewer_for_sequence(sequence_name):
    """Busca si ya existe un viewer para la secuencia especificada."""
    viewer_widgets = _find_viewer_widgets()

    for widget in viewer_widgets:
        try:
            window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""
            if window_title == sequence_name:
                return widget
        except Exception:
            continue

    return None


def _debug_viewer_states(title="Estado de Viewers"):
    """Muestra el estado actual de todos los viewers para debugging."""
    # Silenciado - solo mostrar si hay errores críticos
    pass


def _switch_viewer_focus(target_viewer):
    """Cambia el foco al viewer especificado."""
    try:
        # Buscar todos los viewers
        all_viewers = _find_viewer_widgets()

        # Ocultar todos los viewers primero (excepto el objetivo)
        for viewer in all_viewers:
            try:
                if viewer != target_viewer and hasattr(viewer, 'hide'):
                    if viewer.isVisible() if hasattr(viewer, 'isVisible') else False:
                        viewer.hide()
            except Exception:
                pass

        # Mostrar el viewer objetivo
        if hasattr(target_viewer, 'show'):
            target_viewer.show()

        if hasattr(target_viewer, 'raise_'):
            target_viewer.raise_()

        if hasattr(target_viewer, 'activateWindow'):
            target_viewer.activateWindow()

        _process_events()
        return True

    except Exception as e:
        return False


def switch_to_sequence_fast_by_name(sequence_name):
    """
    Switch DEFINITIVO a una secuencia usando estrategia Cerrar→Reabrir.
    Solución perfecta: Si existe viewer → cerrarlo → openInTimeline → Sin duplicados.
    """
    import time
    start_time = time.time()

    print(f"🔄 Switch a '{sequence_name}'...")

    project = _get_first_open_project()
    if not project:
        print("❌ Error: No hay proyectos abiertos.")
        return False

    target_seq = _find_sequence_by_name(project, sequence_name)
    if not target_seq:
        print(f"❌ Error: Secuencia '{sequence_name}' no encontrada.")
        return False

    # Verificar si ya es la secuencia activa
    active_seq = None
    try:
        active_seq = hiero.ui.activeSequence()
    except Exception:
        active_seq = None

    if active_seq and active_seq.name() == sequence_name:
        print("✅ Ya activa - sin cambios.")
        return True

    # 🎯 ESTRATEGIA DEFINITIVA: Cerrar Existente → Reabrir
    existing_viewer = _find_viewer_for_sequence(sequence_name)
    if existing_viewer:
        try:
            existing_viewer.close()
            _process_events()
        except Exception as e:
            print(f"⚠️ Advertencia cerrando viewer: {e}")

    # PASO 2: Abrir secuencia con openInTimeline (siempre funciona)
    try:
        hiero.ui.openInTimeline(target_seq)
        _process_events()

        # Verificar resultado
        new_active = hiero.ui.activeSequence()
        success = new_active and new_active.name() == sequence_name

        elapsed_time = time.time() - start_time

        if success:
            print(f"✅ Switch completado en {elapsed_time:.2f}s")
        else:
            print(f"❌ Switch fallido en {elapsed_time:.2f}s")

        return success

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Error en switch ({elapsed_time:.2f}s): {e}")
        return False


def main():
    import time
    total_start = time.time()

    ok = switch_to_sequence_fast_by_name(TARGET_SEQUENCE_NAME)

    total_elapsed = time.time() - total_start
    status = "✅ OK" if ok else "❌ FALLÓ"
    print(f"Resultado: {status} (Total: {total_elapsed:.2f}s)")


if __name__ == "__main__":
    main()
