"""
LGA Projects Panel - Switch Sequence Module
===========================================

Módulo auxiliar para cambiar de secuencia en Hiero con preservación completa de estado.

SOLUCIÓN GANADORA CONFIRMADA: V3 HÍBRIDA
- ✅ Velocidad óptima: 0.49s
- ✅ Ajustes completos preservados: Gain/Gamma/Saturation + Playhead
- ✅ Comportamiento nativo: Reemplaza viewer como Hiero nativo
- ✅ Sin duplicados: Lógica viewer-centric
- ✅ UI completa: Reduce panel + scroll automático

IMPORTANTE: Usa LGA_QtAdapter_HieroTools para compatibilidad Nuke 15/16
"""

import hiero.core
import hiero.ui
import time
import importlib.util
import os

# Qt import (según entorno) - usa el adapter para compatibilidad
try:
    from LGA_QtAdapter_HieroTools import QtCore
except ImportError:
    # Fallback si no está disponible
    try:
        from PySide2 import QtCore
    except Exception:
        try:
            from PySide6 import QtCore
        except Exception:
            QtCore = None

def _process_events():
    """Procesa eventos Qt para mantener la UI responsiva."""
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
            'gain': viewer.gain(),
            'gamma': viewer.gamma(),
            'saturation': viewer.saturation()
        }
    except Exception:
        return None

def _apply_viewer_settings(viewer, state):
    """Aplica ajustes del viewer (gain/gamma/saturation) - playhead lo maneja Hiero automáticamente."""
    if not viewer or not state:
        return
    try:
        # Aplicamos gain/gamma/saturation - el playhead lo preserva Hiero automáticamente
        if 'gain' in state:
            viewer.setGain(state['gain'])
        if 'gamma' in state:
            viewer.setGamma(state['gamma'])
        if 'saturation' in state:
            viewer.setSaturation(state['saturation'])
    except Exception:
        pass

def import_script(script_name):
    """Importa script desde LGA_NKS_ViewerTL."""
    startup_dir = r"C:\Users\leg4-pc\.nuke\Python\Startup"
    script_path = os.path.join(startup_dir, "LGA_NKS_ViewerTL", script_name + '.py')

    print(f"  🔍 Buscando script: {script_path}")
    if os.path.exists(script_path):
        print(f"  ✅ Script encontrado: {script_path}")
        try:
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"  ✅ Script importado exitosamente: {script_name}")
            return module
        except Exception as e:
            print(f"  ❌ Error importando script {script_name}: {e}")
            return None
    else:
        print(f"  ❌ Script NO encontrado: {script_path}")
        return None

def reduce_sequence_window():
    """Reduce panel izquierdo del timeline."""
    try:
        print("  🔧 Aplicando reducción de panel izquierdo...")
        print("  📋 Verificando que hay secuencia activa...")
        active_seq = hiero.ui.activeSequence()
        if not active_seq:
            print("  ❌ No hay secuencia activa")
            return False
        print(f"  ✅ Secuencia activa: {active_seq.name()}")

        reduce_module = import_script('LGA_NKS_Reduce_SeqWin')
        if reduce_module and hasattr(reduce_module, 'main'):
            print(f"  📋 Ejecutando reduce_module.main()...")
            reduce_module.main()
            print("  ✅ Panel izquierdo reducido exitosamente")
            return True
        else:
            print("  ❌ No se pudo importar LGA_NKS_Reduce_SeqWin o no tiene función main")
    except Exception as e:
        print(f"  ❌ Error aplicando reducción de panel: {e}")
        import traceback
        print(f"  📄 Traceback: {traceback.format_exc()}")
    return False

def scroll_to_top_track():
    """Hace scroll al track superior."""
    try:
        print("  🔧 Aplicando scroll al track superior...")
        print("  📋 Verificando que hay secuencia activa...")
        active_seq = hiero.ui.activeSequence()
        if not active_seq:
            print("  ❌ No hay secuencia activa")
            return False
        print(f"  ✅ Secuencia activa: {active_seq.name()}")

        scroll_module = import_script('LGA_NKS_ScrollTo_TopTrack')
        if scroll_module and hasattr(scroll_module, 'main'):
            print(f"  📋 Ejecutando scroll_module.main()...")
            scroll_module.main()
            print("  ✅ Scroll al track superior aplicado exitosamente")
            return True
        else:
            print("  ❌ No se pudo importar LGA_NKS_ScrollTo_TopTrack o no tiene función main")
    except Exception as e:
        print(f"  ❌ Error aplicando scroll: {e}")
        import traceback
        print(f"  📄 Traceback: {traceback.format_exc()}")
    return False

def switch_to_sequence_hybrid(target_sequence_name):
    """
    Switch HÍBRIDO V3 PERFECTO: Mejor que v4
    - Velocidad del v2 + Estado completo del v1
    - Sin duplicados + Mantiene viewer settings completos
    - ✅ Playhead: Preservado automáticamente por Hiero
    - ✅ Gain/Gamma/Saturation: Transferidos desde viewer anterior
    - ✅ UI: Redimensiona ventana + Scroll al top track

    Args:
        target_sequence_name (str): Nombre de la secuencia objetivo

    Returns:
        bool: True si el cambio fue exitoso, False en caso contrario
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

    # 3. Capturar ajustes del viewer ACTUAL (gain/gamma para transferir)
    step_start = time.time()
    current_viewer = hiero.ui.currentViewer()
    viewer_state = _get_viewer_state(current_viewer) if current_viewer else None
    viewer_capture_time = time.time() - step_start

    # 4. Buscar viewer existente para la secuencia OBJETIVO (como v2)
    existing_viewer = None
    try:
        # Intentar importar QtWidgets desde el adapter
        try:
            from LGA_QtAdapter_HieroTools import QtWidgets
        except ImportError:
            # Fallback a PySide directo
            try:
                from PySide2 import QtWidgets
            except ImportError:
                from PySide6 import QtWidgets

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

    # 5. Cerrar viewer existente si lo hay (como v2) - Hiero preservará playhead automáticamente
    viewer_close_time = 0
    if existing_viewer:
        step_start = time.time()
        try:
            existing_viewer.close()
            _process_events()
        except Exception:
            pass
        viewer_close_time = time.time() - step_start

    # 6. Abrir secuencia con openInTimeline (como v2) - playhead se preserva automáticamente
    step_start = time.time()
    try:
        hiero.ui.openInTimeline(target_seq)
        _process_events()

        # Dar tiempo extra para que la UI se actualice completamente
        import time as time_module
        print("  ⏱️ Esperando 200ms para que la UI se actualice...")
        time_module.sleep(0.2)  # 200ms delay
        _process_events()
        print("  ✅ UI actualizada, procediendo con optimizaciones...")

        # Verificar que cambió correctamente
        new_active = hiero.ui.activeSequence()
        if not (new_active and new_active.name() == target_sequence_name):
            print("❌ Error: Secuencia no cambió correctamente")
            return False

    except Exception as e:
        print(f"❌ Error abriendo secuencia: {e}")
        return False

    open_time = time.time() - step_start

    # 7. Aplicar ajustes del viewer anterior (gain/gamma) - playhead ya está correcto
    viewer_restore_time = 0
    if viewer_state:
        step_start = time.time()
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            _apply_viewer_settings(new_viewer, viewer_state)
        viewer_restore_time = time.time() - step_start

    # 8. Redimensionar ventana del timeline (como v4)
    step_start = time.time()
    reduce_success = reduce_sequence_window()
    reduce_time = time.time() - step_start

    # 9. Scrollear al top track (como v4)
    step_start = time.time()
    scroll_success = scroll_to_top_track()
    scroll_time = time.time() - step_start

    # 10. Verificar que las optimizaciones se aplicaron
    print("  🔍 Verificando optimizaciones aplicadas...")
    try:
        timeline_editor = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        if timeline_editor:
            window = timeline_editor.window()
            main_splitter = window.findChild(QtWidgets.QSplitter)
            if main_splitter:
                sizes = main_splitter.sizes()
                if len(sizes) >= 2:
                    print(f"  📐 Tamaños del splitter después de reducción: {sizes[0]}px | {sizes[1]}px")
                    if sizes[0] == 340:
                        print("  ✅ Panel izquierdo correctamente reducido a 340px")
                    else:
                        print(f"  ⚠️ Panel izquierdo no está en 340px (está en {sizes[0]}px)")
    except Exception as e:
        print(f"  ❌ Error verificando splitter: {e}")

    # 10. Resultado final
    total_time = time.time() - total_start
    print(f"✅ Switch híbrido perfecto completado en {total_time:.2f}s")
    print(f"   ├── Viewer capture: {viewer_capture_time:.3f}s")
    print(f"   ├── Existing viewer close: {viewer_close_time:.3f}s")
    print(f"   ├── Sequence open: {open_time:.3f}s")
    print(f"   ├── Viewer settings apply: {viewer_restore_time:.3f}s")
    print(f"   ├── UI reduce: {reduce_time:.3f}s")
    print(f"   ├── UI scroll: {scroll_time:.3f}s")
    print(f"   └── Total: {total_time:.2f}s")

    return True

# Función wrapper para compatibilidad con código existente
def switch_to_sequence(target_sequence_name):
    """
    Función principal para cambiar de secuencia.
    Wrapper para switch_to_sequence_hybrid con manejo de errores.
    """
    try:
        return switch_to_sequence_hybrid(target_sequence_name)
    except Exception as e:
        print(f"❌ Error inesperado en switch_to_sequence: {e}")
        import traceback
        print(traceback.format_exc())
        return False
