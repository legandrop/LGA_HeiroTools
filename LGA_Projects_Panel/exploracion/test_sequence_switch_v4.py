"""
Hiero / Nuke Studio - Switch V4 DEFINITIVA: Optimizada y Correcta
=================================================================

🎯 ESTRATEGIA GANADORA: Mezcla v1+v3 optimizada
- Captura ajustes del viewer ANTES de cerrar (como v1)
- Lógica cerrar→reabrir correcta (como v3)
- SIN overhead del timeline (zoom/scroll) para velocidad
- Respeta ajustes individuales del viewer

✅ CONFIRMADO: Funciona como Hiero nativo - mantiene ajustes automáticamente
"""

import hiero.core
import hiero.ui
import time
import importlib.util
import os

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
    """Procesa eventos de Qt."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def _get_viewer_state(viewer):
    """Captura estado básico del viewer (gain, gamma, time)."""
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
    """Restaura estado básico del viewer."""
    if not viewer or not state:
        return

    try:
        viewer.setTime(state['time'])
        viewer.setGain(state['gain'])
        viewer.setGamma(state['gamma'])
    except Exception:
        pass


def _find_viewer_for_sequence(sequence_name):
    """Busca widget viewer para la secuencia especificada."""
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        all_widgets = QtWidgets.QApplication.instance().allWidgets()

        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else str(type(widget))
                if 'Foundry::Storm::UI::Viewer' in class_name:
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""
                    if window_title == sequence_name:
                        return widget
            except Exception:
                continue
    except Exception:
        pass
    return None


def import_script(script_name):
    """Importa script desde LGA_NKS_ViewerTL."""
    startup_dir = r"C:\Users\leg4-pc\.nuke\Python\Startup"
    script_path = os.path.join(startup_dir, "LGA_NKS_ViewerTL", script_name + '.py')

    if os.path.exists(script_path):
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


def reduce_sequence_window():
    """Reduce panel izquierdo del timeline."""
    try:
        reduce_module = import_script('LGA_NKS_Reduce_SeqWin')
        if reduce_module:
            reduce_module.main()
            return True
    except Exception:
        pass
    return False


def scroll_to_top_track():
    """Hace scroll al track superior."""
    try:
        scroll_module = import_script('LGA_NKS_ScrollTo_TopTrack')
        if scroll_module:
            scroll_module.main()
            return True
    except Exception:
        pass
    return False


def switch_to_sequence_v4(target_sequence_name):
    """
    Switch V4 DEFINITIVA: Como v1 pero sin timeline overhead
    =======================================================

    🎯 ESTRATEGIA GANADORA (APRENDIDA DE v1):
    - Captura ajustes del viewer ANTES de cerrar (como v1)
    - Cierra el VIEWER ACTUAL (CRÍTICO - no el existente) (como v1)
    - Abre nueva secuencia con openInTimeline (como v1)
    - Restaura ajustes al nuevo viewer (como v1)
    - SIN timeline state management para velocidad

    ✅ RESULTADO ESPERADO: Reemplaza viewer existente como v1, pero más rápido
    """
    total_start = time.time()
    print(f"🔄 Switch V4 a '{target_sequence_name}' (optimizada)...")

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

    # 2. OPTIMIZACIÓN: Verificar si ya estamos en la secuencia (como v3)
    active_seq = None
    try:
        active_seq = hiero.ui.activeSequence()
    except Exception:
        active_seq = None

    if active_seq and active_seq.name() == target_sequence_name:
        print("✅ Ya activa - ajustes UI finales...")
        step_start = time.time()
        reduce_sequence_window()
        reduce_time = time.time() - step_start

        step_start = time.time()
        scroll_to_top_track()
        scroll_time = time.time() - step_start

        total_time = time.time() - total_start
        print(f"✅ Completado en {total_time:.2f}s (reduce: {reduce_time:.2f}s, scroll: {scroll_time:.2f}s)")
        return True

    # 3. CAPTURAR ajustes del viewer actual (como v1)
    step_start = time.time()
    current_viewer = hiero.ui.currentViewer()
    viewer_state = _get_viewer_state(current_viewer) if current_viewer else None
    viewer_capture_time = time.time() - step_start

    if viewer_state:
        print(f"   📸 Ajustes capturados - Time: {viewer_state['time']}, Gain: {viewer_state['gain']}, Gamma: {viewer_state['gamma']}")

    # 4. CERRAR viewer actual (como v1 - CRÍTICO para lograr reemplazo)
    step_start = time.time()
    if current_viewer:
        try:
            viewer_window = current_viewer.window()
            if viewer_window:
                viewer_window.close()
                print("   🔒 Viewer actual cerrado (como v1)")
        except Exception:
            pass
    viewer_close_time = time.time() - step_start
    time.sleep(0.1)  # Pausa como en v1

    # 5. ABRIR nueva secuencia (como v1)
    step_start = time.time()
    try:
        new_timeline = hiero.ui.openInTimeline(target_seq)
        if not new_timeline:
            print("❌ Error: openInTimeline() falló")
            return False

        # Verificar que cambió correctamente
        new_active = hiero.ui.activeSequence()
        if not (new_active and new_active.name() == target_sequence_name):
            print("❌ Error: Secuencia no cambió correctamente")
            return False

    except Exception as e:
        print(f"❌ Error abriendo secuencia: {e}")
        return False

    open_time = time.time() - step_start
    print("   ✅ Nueva secuencia abierta correctamente (como v1)")

    # 6. RESTAURAR ajustes del viewer (como v1)
    viewer_restore_time = 0
    if viewer_state:
        step_start = time.time()
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            _restore_viewer_state(new_viewer, viewer_state)
            print("   🔄 Ajustes del viewer restaurados (como v1)")
        viewer_restore_time = time.time() - step_start

    # 7. AJUSTES UI FINALES (como v1)
    time.sleep(0.2)  # Pausa para estabilidad como v1

    step_start = time.time()
    reduce_success = reduce_sequence_window()
    reduce_time = time.time() - step_start

    step_start = time.time()
    scroll_success = scroll_to_top_track()
    scroll_time = time.time() - step_start

    # 8. RESULTADO FINAL
    total_time = time.time() - total_start

    print("   📊 RESULTADO V4 (OPTIMIZADA - como v1 pero sin timeline overhead):")
    print(f"   ├── Viewer capture: {viewer_capture_time:.3f}s")
    print(f"   ├── Current viewer close: {viewer_close_time:.3f}s")
    print(f"   ├── Sequence open: {open_time:.3f}s")
    print(f"   ├── Viewer restore: {viewer_restore_time:.3f}s")
    print(f"   ├── UI reduce: {reduce_time:.3f}s")
    print(f"   ├── UI scroll: {scroll_time:.3f}s")
    print(f"   └── Total: {total_time:.2f}s")

    # Verificar ajustes finales
    final_viewer = hiero.ui.currentViewer()
    if final_viewer:
        try:
            final_gain = final_viewer.gain()
            final_gamma = final_viewer.gamma()
            final_time = final_viewer.time()
            print(f"   🎯 Ajustes finales - Time: {final_time}, Gain: {final_gain}, Gamma: {final_gamma}")

            if viewer_state:
                gain_ok = abs(final_gain - viewer_state['gain']) < 0.001
                gamma_ok = abs(final_gamma - viewer_state['gamma']) < 0.001
                if gain_ok and gamma_ok:
                    print("   ✅ ¡AJUSTES MANTENIDOS PERFECTAMENTE!")
                else:
                    print("   ⚠️ Ajustes no coinciden exactamente")
        except Exception:
            print("   ⚠️ No se pudieron verificar ajustes finales")

    print(f"✅ Switch V4 completado exitosamente en {total_time:.2f}s")
    return True


def main():
    """Función principal de test."""
    total_start = time.time()

    print("=" * 70)
    print("TEST: Switch V4 DEFINITIVA (Como v1 sin timeline overhead)")
    print("=" * 70)
    print(f"Objetivo: Cambiar a '{TARGET_SEQUENCE_NAME}'")
    print("- Captura ajustes del viewer ANTES de cerrar")
    print("- Cierra VIEWER ACTUAL (como v1 - CRÍTICO para reemplazo)")
    print("- Abre nueva secuencia con openInTimeline")
    print("- Restaura ajustes del viewer")
    print("- SIN timeline state = VELOCIDAD MÁXIMA")
    print("- RESULTADO ESPERADO: Reemplaza viewer como v1")
    print()

    ok = switch_to_sequence_v4(TARGET_SEQUENCE_NAME)

    total_elapsed = time.time() - total_start
    status = "✅ OK" if ok else "❌ FALLÓ"
    print(f"\nResultado: {status} (Total: {total_elapsed:.2f}s)")
    print("=" * 70)


if __name__ == "__main__":
    main()