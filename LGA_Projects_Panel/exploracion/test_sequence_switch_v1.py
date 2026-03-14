"""
Script de Test: Cambiar a Secuencia Específica (Método Refresh Completo)
========================================================================

Script optimizado que cambia a una secuencia específica usando el MISMO método COMPLETO que
los scripts de refresh de LGA_NKS. Mide tiempo de cada paso para comparación.

ESTRATEGIA (inspirada en LGA_NKS_Timeline_Refresh_Wrap.py):
1. Cerrar el viewer/timeline actual
2. Abrir la nueva secuencia con openInTimeline()
3. Reducir el panel izquierdo (340px)
4. Scrollear al track superior
5. Esto funciona porque replica exactamente el workflow que NO rompe Hiero
"""

import hiero.core
import hiero.ui
import os
import importlib.util
import time
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore

def get_timeline_state():
    """
    Obtiene el estado actual del timeline (zoom, scroll, etc.)
    Copiado exactamente de LGA_NKS_Timeline_Refresh_Wrap.py
    """
    try:
        t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        if not t:
            return None

        # Buscar el QSplitter primero
        splitter = None
        for child in t.window().children():
            if isinstance(child, QtWidgets.QSplitter):
                splitter = child
                break

        if not splitter:
            return None

        # Buscar el TimelineView dentro del primer widget del QSplitter
        timeline_view = None
        for child in splitter.children():
            if isinstance(child, QtWidgets.QWidget):
                for subchild in child.children():
                    if isinstance(subchild, QtWidgets.QAbstractScrollArea):
                        timeline_view = subchild
                        break
                if timeline_view:
                    break

        if not timeline_view:
            return None

        # Buscar viewport y h_container por nombre
        viewport = None
        h_container = None
        for child in timeline_view.children():
            if hasattr(child, 'objectName'):
                if child.objectName() == "qt_scrollarea_viewport":
                    viewport = child
                elif child.objectName() == "qt_scrollarea_hcontainer":
                    h_container = child

        if not all([viewport, h_container]):
            return None

        # Obtener scrollbar y slider
        h_scrollbar = h_container.children()[0]  # QScrollBar
        h_slider = h_container.children()[2]     # QSlider

        viewport_width = viewport.width()
        scrollbar_range = h_scrollbar.maximum() - h_scrollbar.minimum() + h_scrollbar.pageStep()
        zoom_factor = viewport_width / scrollbar_range

        state = {
            'scroll_value': h_scrollbar.value(),
            'scroll_min': h_scrollbar.minimum(),
            'scroll_max': h_scrollbar.maximum(),
            'page_step': h_scrollbar.pageStep(),
            'viewport_width': viewport_width,
            'zoom_factor': zoom_factor,
            'slider_value': h_slider.value() if hasattr(h_slider, 'value') else None
        }

        return state

    except Exception:
        return None

def restore_timeline_state(state):
    """
    Restaura el estado del timeline usando acceso directo al scrollbar y slider.
    Copiado exactamente de LGA_NKS_Timeline_Refresh_Wrap.py
    """
    try:
        t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        if not t:
            return False

        # Buscar el QSplitter primero
        splitter = None
        for child in t.window().children():
            if isinstance(child, QtWidgets.QSplitter):
                splitter = child
                break

        if not splitter:
            return False

        # Buscar el TimelineView dentro del primer widget del QSplitter
        timeline_view = None
        for child in splitter.children():
            if isinstance(child, QtWidgets.QWidget):
                for subchild in child.children():
                    if isinstance(subchild, QtWidgets.QAbstractScrollArea):
                        timeline_view = subchild
                        break
                if timeline_view:
                    break

        if not timeline_view:
            return False

        # Buscar viewport y h_container por nombre
        viewport = None
        h_container = None
        for child in timeline_view.children():
            if hasattr(child, 'objectName'):
                if child.objectName() == "qt_scrollarea_viewport":
                    viewport = child
                elif child.objectName() == "qt_scrollarea_hcontainer":
                    h_container = child

        if not all([viewport, h_container]):
            return False

        # Obtener scrollbar y slider
        h_scrollbar = h_container.children()[0]  # QScrollBar
        h_slider = h_container.children()[2]     # QSlider

        print("🔄 Restaurando estado del timeline...")

        # 1. Primero restaurar el valor del slider
        if state['slider_value'] is not None:
            h_slider.setValue(state['slider_value'])
            QtCore.QCoreApplication.processEvents()

        # 2. Luego restaurar valores del scrollbar
        h_scrollbar.setPageStep(state['page_step'])
        h_scrollbar.setMaximum(state['scroll_max'])
        h_scrollbar.setMinimum(state['scroll_min'])
        h_scrollbar.setValue(state['scroll_value'])

        QtCore.QCoreApplication.processEvents()

        return True

    except Exception:
        return False

def get_basic_viewer_state(viewer):
    """Captura estado básico del viewer (simplificado del script de refresh)."""
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

def restore_basic_viewer_state(viewer, state):
    """Restaura estado básico del viewer (simplificado)."""
    if not viewer or not state:
        return

    try:
        viewer.setTime(state['time'])
        viewer.setGain(state['gain'])
        viewer.setGamma(state['gamma'])
    except Exception:
        pass

def import_script(script_name):
    """Importa un script desde la carpeta LGA_NKS_ViewerTL usando ruta absoluta desde Startup"""
    startup_dir = r"C:\Users\leg4-pc\.nuke\Python\Startup"
    script_path = os.path.join(startup_dir, "LGA_NKS_ViewerTL", script_name + '.py')

    if os.path.exists(script_path):
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None

def reduce_sequence_window():
    """Reduce el tamaño del panel izquierdo del timeline (como LGA_NKS_Reduce_SeqWin.py)"""
    try:
        reduce_module = import_script('LGA_NKS_Reduce_SeqWin')
        if reduce_module:
            reduce_module.main()
            return True
    except Exception:
        pass
    return False

def scroll_to_top_track():
    """Hace scroll al track superior del timeline (como LGA_NKS_ScrollTo_TopTrack.py)"""
    try:
        scroll_module = import_script('LGA_NKS_ScrollTo_TopTrack')
        if scroll_module:
            scroll_module.main()
            return True
    except Exception:
        pass
    return False

def switch_to_sequence_via_refresh(target_sequence_name):
    """
    Cambia a la secuencia especificada usando EXACTAMENTE el mismo método que LGA_NKS_Timeline_Refresh_Wrap.py.
    Versión optimizada con logs minimalistas y medición de tiempos.
    """
    total_start = time.time()
    print(f"🔄 Switch a '{target_sequence_name}' (método refresh completo)...")

    # Obtener proyectos y secuencia
    proyectos = hiero.core.projects()
    if not proyectos:
        print("❌ Error: No hay proyectos abiertos")
        return False

    proyecto = proyectos[0]
    sequences = proyecto.sequences()
    target_sequence = None
    for seq in sequences:
        if seq.name() == target_sequence_name:
            target_sequence = seq
            break

    if not target_sequence:
        print(f"❌ Error: Secuencia '{target_sequence_name}' no encontrada")
        return False

    # Verificar si ya estamos en esa secuencia
    current_sequence = hiero.ui.activeSequence()
    if current_sequence and current_sequence.name() == target_sequence_name:
        print("✅ Ya activa - ejecutando pasos finales...")

        step_start = time.time()
        reduce_sequence_window()
        reduce_time = time.time() - step_start

        step_start = time.time()
        scroll_to_top_track()
        scroll_time = time.time() - step_start

        total_time = time.time() - total_start
        print(f"✅ Completado en {total_time:.2f}s (reduce: {reduce_time:.2f}s, scroll: {scroll_time:.2f}s)")
        return True

    # PASO 1: Capturar estado del timeline
    step_start = time.time()
    original_timeline_state = get_timeline_state()
    timeline_capture_time = time.time() - step_start
    if original_timeline_state is None:
        print("❌ Error: No se pudo capturar estado del timeline")
        return False

    # PASO 2: Capturar estado del viewer
    active_viewer = hiero.ui.currentViewer()
    viewer_state = get_basic_viewer_state(active_viewer) if active_viewer else None

    # PASO 3: Cerrar viewer actual
    step_start = time.time()
    if active_viewer:
        try:
            viewer_window = active_viewer.window()
            if viewer_window:
                viewer_window.close()
        except Exception:
            pass
    viewer_close_time = time.time() - step_start
    time.sleep(0.1)

    # PASO 4: Abrir nueva secuencia
    step_start = time.time()
    try:
        new_timeline = hiero.ui.openInTimeline(target_sequence)
        open_time = time.time() - step_start
        if not new_timeline:
            print("❌ Error: openInTimeline() falló")
            return False
    except Exception as e:
        print(f"❌ Error abriendo secuencia: {e}")
        return False

    # PASO 5: Restaurar estado del viewer
    if viewer_state:
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            restore_basic_viewer_state(new_viewer, viewer_state)

    # PASO 6: Reducir panel izquierdo
    time.sleep(0.2)
    step_start = time.time()
    reduce_success = reduce_sequence_window()
    reduce_time = time.time() - step_start

    # PASO 7: Scroll al track superior
    time.sleep(0.2)
    step_start = time.time()
    scroll_success = scroll_to_top_track()
    scroll_time = time.time() - step_start

    # PASO 8: Restaurar timeline (dos intentos)
    step_start = time.time()
    restore_timeline_state(original_timeline_state)
    first_restore_time = time.time() - step_start

    step_start = time.time()
    restore_timeline_state(original_timeline_state)
    second_restore_time = time.time() - step_start

    # Procesar eventos finales
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.2)

    # Resultado final
    total_time = time.time() - total_start
    print(f"✅ Switch completado en {total_time:.2f}s")
    print(f"   ├── Timeline capture: {timeline_capture_time:.3f}s")
    print(f"   ├── Viewer close: {viewer_close_time:.3f}s")
    print(f"   ├── Sequence open: {open_time:.3f}s")
    print(f"   ├── Reduce window: {reduce_time:.3f}s")
    print(f"   ├── Scroll to top: {scroll_time:.3f}s")
    print(f"   ├── Timeline restore x2: {first_restore_time:.3f}s + {second_restore_time:.3f}s")
    print(f"   └── Total: {total_time:.2f}s")

    return True

def switch_to_sequence_010_350():
    """Cambia a la secuencia '010-350' usando el método de refresh que funciona"""
    return switch_to_sequence_via_refresh("010-350")

if __name__ == "__main__":
    print("=" * 70)
    print("TEST: Switch a '010-350' (MÉTODO REFRESH COMPLETO CON TIMING)")
    print("=" * 70)

    total_start = time.time()
    try:
        success = switch_to_sequence_010_350()
        total_elapsed = time.time() - total_start

        status = "✅ OK" if success else "❌ FALLÓ"
        print(f"\nResultado: {status} (Total: {total_elapsed:.2f}s)")

    except Exception as e:
        total_elapsed = time.time() - total_start
        print(f"\n❌ Error general ({total_elapsed:.2f}s): {e}")

    print("=" * 70)
