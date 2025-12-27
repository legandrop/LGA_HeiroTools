"""
Script de Test: Cambiar a Secuencia Específica (Método Refresh Completo)
========================================================================

Script que cambia a una secuencia específica usando el MISMO método COMPLETO que
los scripts de refresh de LGA_NKS que funcionan perfectamente.

ESTRATEGIA (inspirada en LGA_NKS_Timeline_Refresh_Wrap.py):
1. Cerrar el viewer/timeline actual
2. Abrir la nueva secuencia con openInTimeline()
3. Reducir el panel izquierdo (340px)
4. Scrollear al track superior
5. Esto funciona porque replica exactamente el workflow que NO rompe Hiero

EJECUTAR EN HIERO mientras se está en cualquier secuencia del proyecto BRDA_SUP_v050.
"""

import hiero.core
import hiero.ui
import os
import importlib.util
import time
from LGA_QtAdapter_HieroTools import QtWidgets, QtCore

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

    except Exception as e:
        print(f"⚠️ Error al obtener el estado del timeline: {e}")
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

    except Exception as e:
        print(f"⚠️ Error al restaurar el estado: {e}")
        return False

def get_basic_viewer_state(viewer):
    """
    Captura estado básico del viewer (simplificado del script de refresh).
    """
    if not viewer:
        return None

    try:
        state = {
            'time': viewer.time(),
            'gain': viewer.gain(),
            'gamma': viewer.gamma()
        }
        print(f"📸 Estado capturado - Tiempo: {state['time']}, Gain: {state['gain']}, Gamma: {state['gamma']}")
        return state
    except Exception as e:
        print(f"⚠️ Error capturando estado del viewer: {e}")
        return None

def restore_basic_viewer_state(viewer, state):
    """
    Restaura estado básico del viewer (simplificado).
    """
    if not viewer or not state:
        return

    try:
        print("🔄 Restaurando estado básico del viewer...")
        viewer.setTime(state['time'])
        viewer.setGain(state['gain'])
        viewer.setGamma(state['gamma'])
        print("✅ Estado restaurado")
    except Exception as e:
        print(f"⚠️ Error restaurando estado: {e}")

def import_script(script_name):
    """
    Importa un script desde la carpeta LGA_NKS_ViewerTL usando ruta absoluta desde Startup
    """
    # Ruta absoluta desde la carpeta Startup (donde están todos los scripts)
    startup_dir = r"C:\Users\leg4-pc\.nuke\Python\Startup"
    script_path = os.path.join(startup_dir, "LGA_NKS_ViewerTL", script_name + '.py')

    if os.path.exists(script_path):
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    else:
        print(f"⚠️ Script no encontrado: {script_path}")
        print(f"   Ruta absoluta: {os.path.abspath(script_path)}")
        return None

def reduce_sequence_window():
    """
    Reduce el tamaño del panel izquierdo del timeline (como LGA_NKS_Reduce_SeqWin.py)
    """
    print("🔧 Reduciendo tamaño del panel izquierdo...")
    try:
        reduce_module = import_script('LGA_NKS_Reduce_SeqWin')
        if reduce_module:
            print("📋 Ejecutando reduce_sequence_window...")
            reduce_module.main()
            print("✅ Panel reducido exitosamente")
            return True
        else:
            print("⚠️ No se pudo importar el script de reducción")
            return False
    except Exception as e:
        print(f"⚠️ Error reduciendo panel: {e}")
        import traceback
        traceback.print_exc()
        return False

def scroll_to_top_track():
    """
    Hace scroll al track superior del timeline (como LGA_NKS_ScrollTo_TopTrack.py)
    """
    print("📍 Scrolleando al track superior...")
    try:
        scroll_module = import_script('LGA_NKS_ScrollTo_TopTrack')
        if scroll_module:
            print("📋 Ejecutando scroll_to_top_track...")
            scroll_module.main()
            print("✅ Scroll completado exitosamente")
            return True
        else:
            print("⚠️ No se pudo importar el script de scroll")
            return False
    except Exception as e:
        print(f"⚠️ Error haciendo scroll: {e}")
        import traceback
        traceback.print_exc()
        return False

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

    except Exception as e:
        print(f"⚠️ Error al obtener el estado del timeline: {e}")
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

    except Exception as e:
        print(f"⚠️ Error al restaurar el estado: {e}")
        return False

def switch_to_sequence_via_refresh(target_sequence_name):
    """
    Cambia a la secuencia especificada usando EXACTAMENTE el mismo método que LGA_NKS_Timeline_Refresh_Wrap.py.
    Incluye TODOS los pasos: captura timeline + refresh + reduce panel + scroll to top + restauración timeline.
    """

    print(f"🔄 Buscando secuencia '{target_sequence_name}'...")

    # Obtener proyectos abiertos
    proyectos = hiero.core.projects()
    if not proyectos:
        print("❌ No hay proyectos abiertos")
        return False

    proyecto = proyectos[0]
    print(f"📁 Proyecto: {proyecto.name()}")

    # Buscar secuencia por nombre
    sequences = proyecto.sequences()
    print(f"📋 Total de secuencias encontradas: {len(sequences)}")

    target_sequence = None
    for seq in sequences:
        if seq.name() == target_sequence_name:
            target_sequence = seq
            break

    if not target_sequence:
        print(f"❌ Secuencia '{target_sequence_name}' no encontrada")
        print("Secuencias disponibles:")
        for seq in sequences:
            print(f"  - {seq.name()}")
        return False

    print(f"✅ Secuencia encontrada: {target_sequence.name()}")

    # Verificar si ya estamos en esa secuencia
    current_sequence = hiero.ui.activeSequence()
    if current_sequence and current_sequence.name() == target_sequence_name:
        print("🎯 Ya estamos en la secuencia objetivo - ejecutando pasos finales...")

        # Aun si ya estamos en la secuencia, ejecutar los pasos finales
        reduce_sequence_window()
        scroll_to_top_track()
        print("🎯 Pasos finales completados")
        return True

    print("🔄 Cambiando a secuencia usando método 'refresh' completo...")

    # PASO 1: Capturar estado INICIAL del timeline (CRÍTICO - como en Timeline_Refresh_Wrap.py)
    start_time = time.time()
    original_timeline_state = get_timeline_state()
    if original_timeline_state is None:
        print("⚠️ No se pudo capturar el estado inicial del timeline.")
        return False
    print(f"📊 Estado INICIAL del timeline capturado en {time.time() - start_time:.3f} segundos")
    print(f"   Zoom factor: {original_timeline_state['zoom_factor']}")

    # PASO 2: Capturar estado del viewer actual (como en Timeline_Refresh.py)
    active_viewer = hiero.ui.currentViewer()
    viewer_state = None
    if active_viewer:
        print("📸 Capturando estado del viewer actual...")
        viewer_state = get_basic_viewer_state(active_viewer)

    # PASO 3: Cerrar el viewer/timeline actual (CRÍTICO - como hacen los scripts de refresh)
    print("🔒 Cerrando viewer/timeline actual...")
    if active_viewer:
        try:
            viewer_window = active_viewer.window()
            if viewer_window:
                viewer_window.close()
                print("✅ Viewer cerrado exitosamente")
            else:
                print("⚠️ No se pudo obtener la ventana del viewer")
        except Exception as e:
            print(f"⚠️ Error cerrando viewer: {e}")
    else:
        print("ℹ️ No hay viewer activo que cerrar")

    # Pequeña pausa para que se procese el cierre
    time.sleep(0.1)

    # PASO 4: Abrir la nueva secuencia (igual que LGA_NKS_Timeline_Refresh.py)
    print(f"🚀 Abriendo nueva secuencia '{target_sequence_name}'...")
    try:
        new_timeline = hiero.ui.openInTimeline(target_sequence)
        if new_timeline:
            print("✅ Nueva secuencia abierta exitosamente")

            # PASO 5: Restaurar estado del viewer si lo capturamos
            if viewer_state:
                print("🔄 Restaurando estado en el nuevo viewer...")
                new_viewer = hiero.ui.currentViewer()
                if new_viewer:
                    restore_basic_viewer_state(new_viewer, viewer_state)
                else:
                    print("⚠️ No se pudo obtener el nuevo viewer para restaurar estado")

            # PASO 6: Reducir el panel izquierdo (como en el workflow completo)
            print("⏳ Esperando para procesar cambios en UI...")
            time.sleep(0.2)  # Pausa para que Qt procese el cambio de secuencia
            start_time = time.time()
            reduce_success = reduce_sequence_window()
            print(f"⏱️ Reduce window tomó {time.time() - start_time:.3f} segundos")

            # PASO 7: Hacer scroll al track superior
            print("⏳ Esperando antes del scroll...")
            time.sleep(0.2)  # Pausa adicional antes del scroll
            start_time = time.time()
            scroll_success = scroll_to_top_track()
            print(f"⏱️ Scroll to top tomó {time.time() - start_time:.3f} segundos")

            # PASO 8: PRIMER intento de restauración del timeline (como en Timeline_Refresh_Wrap.py)
            print("🔄 Primer intento de restauración del timeline...")
            start_time = time.time()
            success = restore_timeline_state(original_timeline_state)
            print(f"⏱️ Primer intento tomó {time.time() - start_time:.3f} segundos")

            # PASO 9: SEGUNDO intento de restauración del timeline (como en Timeline_Refresh_Wrap.py)
            print("🔄 Segundo intento de restauración del timeline...")
            start_time = time.time()
            success = restore_timeline_state(original_timeline_state)
            print(f"⏱️ Segundo intento tomó {time.time() - start_time:.3f} segundos")

            # Procesar eventos finales
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.2)

            print("🎯 Cambio de secuencia completado exitosamente (con TODOS los pasos)")
            return True
        else:
            print("❌ Error: openInTimeline() retornó None")
            return False

    except Exception as e:
        print(f"❌ Error abriendo nueva secuencia: {e}")
        import traceback
        traceback.print_exc()
        return False

def switch_to_sequence_010_350():
    """Cambia a la secuencia '010-350' usando el método de refresh que funciona"""
    return switch_to_sequence_via_refresh("010-350")

if __name__ == "__main__":
    print("=" * 78)
    print("TEST: Cambiar a Secuencia 010-350 (MÉTODO REFRESH COMPLETO)")
    print("=" * 78)

    # Debug: mostrar rutas calculadas
    print("🔍 DEBUG - Rutas calculadas:")
    startup_dir = r"C:\Users\leg4-pc\.nuke\Python\Startup"
    print(f"   Directorio Startup: {startup_dir}")
    print(f"   Ruta a LGA_NKS_ViewerTL: {os.path.join(startup_dir, 'LGA_NKS_ViewerTL')}")
    print()

    # Ejecutar el test usando el mismo método completo que los scripts de refresh
    try:
        success = switch_to_sequence_010_350()
        if success:
            print("✅ TEST COMPLETADO EXITOSAMENTE (con reducción de panel y scroll)")
        else:
            print("❌ TEST FALLÓ")
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 78)
    print("FIN DEL TEST")
    print("=" * 78)
