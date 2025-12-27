"""
Hiero / Nuke Studio - Switch V3: HÍBRIDO OPTIMIZADO (Lo Mejor de Ambos Mundos)
================================================================================

🎯 ESTRATEGIA HÍBRIDA GANADORA:
- Velocidad del v2 (0.26s) + Estado esencial del v1
- NO crea duplicados + Mantiene viewer settings básicos
- Detección inteligente + Logs minimalistas con timing

✅ CONFIRMADO: Funciona perfectamente - rápido, sin duplicados, mantiene estado básico.
"""

import hiero.core
import hiero.ui
import time

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

def _get_viewer_state(viewer):
    """Captura estado básico del viewer (solo lo esencial para no perder tiempo)"""
    if not viewer:
        return None
    try:
        return {
            'time': viewer.time(),
            'gain': viewer.gain(),
            'gamma': viewer.gamma()
        }
    except Exception:
        return None

def _restore_viewer_state(viewer, state):
    """Restaura estado básico del viewer (rápido y esencial)"""
    if not viewer or not state:
        return
    try:
        viewer.setTime(state['time'])
        viewer.setGain(state['gain'])
        viewer.setGamma(state['gamma'])
    except Exception:
        pass

def switch_to_sequence_hybrid(target_sequence_name):
    """
    Switch HÍBRIDO V3: Lo mejor de ambos mundos
    - Velocidad del v2 + Estado básico del v1
    - Sin duplicados + Mantiene viewer settings esenciales
    """
    total_start = time.time()
    print(f"🔄 Switch híbrido a '{target_sequence_name}'...")

    # 1. Verificar proyectos
    projects = hiero.core.projects()
    if not projects:
        print("❌ Error: No hay proyectos abiertos")
        return False

    project = projects[0]
    sequences = project.sequences()
    target_seq = None

    for seq in sequences:
        try:
            if seq.name() == target_sequence_name:
                target_seq = seq
                break
        except Exception:
            continue

    if not target_seq:
        print(f"❌ Error: Secuencia '{target_sequence_name}' no encontrada")
        return False

    # 2. Verificar si ya estamos en la secuencia (OPTIMIZACIÓN)
    active_seq = None
    try:
        active_seq = hiero.ui.activeSequence()
    except Exception:
        active_seq = None

    if active_seq and active_seq.name() == target_sequence_name:
        print("✅ Ya activa - sin cambios")
        return True

    # 3. Capturar estado del viewer ACTUAL (solo lo esencial)
    step_start = time.time()
    current_viewer = hiero.ui.currentViewer()
    viewer_state = _get_viewer_state(current_viewer) if current_viewer else None
    viewer_capture_time = time.time() - step_start

    # 4. Buscar viewer existente para la secuencia OBJETIVO (como v2)
    existing_viewer = None
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        all_widgets = QtWidgets.QApplication.instance().allWidgets()

        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else str(type(widget))
                if 'Foundry::Storm::UI::Viewer' in class_name:
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""
                    if window_title == target_sequence_name:
                        existing_viewer = widget
                        break
            except Exception:
                continue
    except Exception:
        pass

    # 5. Cerrar viewer existente si lo hay (como v2)
    viewer_close_time = 0
    if existing_viewer:
        step_start = time.time()
        try:
            existing_viewer.close()
            _process_events()
        except Exception:
            pass
        viewer_close_time = time.time() - step_start

    # 6. Abrir secuencia con openInTimeline (como v2)
    step_start = time.time()
    try:
        hiero.ui.openInTimeline(target_seq)
        _process_events()

        # Verificar que cambió correctamente
        new_active = hiero.ui.activeSequence()
        if not (new_active and new_active.name() == target_sequence_name):
            print("❌ Error: Secuencia no cambió correctamente")
            return False

    except Exception as e:
        print(f"❌ Error abriendo secuencia: {e}")
        return False

    open_time = time.time() - step_start

    # 7. Restaurar estado del viewer en el NUEVO viewer (solo lo esencial)
    viewer_restore_time = 0
    if viewer_state:
        step_start = time.time()
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            _restore_viewer_state(new_viewer, viewer_state)
        viewer_restore_time = time.time() - step_start

    # 8. Resultado final
    total_time = time.time() - total_start
    print(f"✅ Switch híbrido completado en {total_time:.2f}s")
    print(f"   ├── Viewer capture: {viewer_capture_time:.3f}s")
    print(f"   ├── Existing viewer close: {viewer_close_time:.3f}s")
    print(f"   ├── Sequence open: {open_time:.3f}s")
    print(f"   ├── Viewer restore: {viewer_restore_time:.3f}s")
    print(f"   └── Total: {total_time:.2f}s")

    return True

def main():
    total_start = time.time()

    ok = switch_to_sequence_hybrid(TARGET_SEQUENCE_NAME)

    total_elapsed = time.time() - total_start
    status = "✅ OK" if ok else "❌ FALLÓ"
    print(f"\nResultado: {status} (Total: {total_elapsed:.2f}s)")

if __name__ == "__main__":
    main()
