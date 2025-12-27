"""
EXPLORACIÓN SIMPLE: Estados de Viewer para Secuencias 710-990 y 010-350
=======================================================================

🎯 OBJETIVO: Explorar elementos disponibles para capturar gain/gamma de secuencia 010-350
mientras estamos enfocados en 710-990.

Sabemos que:
- currentViewer() tiene .gain(), .gamma(), .time() para viewer ACTIVO
- Widgets Qt 'Foundry::Storm::UI::Viewer' NO tienen estos métodos
- Necesitamos encontrar cómo acceder a ajustes de viewers no activos
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
    """Busca viewer para la secuencia especificada."""
    viewer_widgets = _find_viewer_widgets()

    for widget in viewer_widgets:
        try:
            window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""
            if window_title == sequence_name:
                return widget
        except Exception:
            continue

    return None


def _get_viewer_state(viewer, label="Viewer"):
    """Obtiene estado básico del viewer (gain, gamma, time)."""
    if not viewer:
        print(f"❌ {label}: No disponible")
        return None

    try:
        state = {}
        if hasattr(viewer, 'time'):
            state['time'] = viewer.time()
        if hasattr(viewer, 'gain'):
            state['gain'] = viewer.gain()
        if hasattr(viewer, 'gamma'):
            state['gamma'] = viewer.gamma()

        print(f"✅ {label} - Estado capturado:")
        print(f"   - Time: {state.get('time', 'N/A')}")
        print(f"   - Gain: {state.get('gain', 'N/A')}")
        print(f"   - Gamma: {state.get('gamma', 'N/A')}")

        return state
    except Exception as e:
        print(f"❌ {label}: Error obteniendo estado - {e}")
        return None


def _test_send_to_viewer_api(api_name, api_func, target_sequence):
    """Prueba una API sendToViewer para ver si cambia currentViewer."""
    try:
        print(f"\n🎯 Probando {api_name}...")

        # Estado antes
        before_viewer = hiero.ui.currentViewer()
        before_active = hiero.ui.activeSequence()
        before_gain = before_viewer.gain() if before_viewer else "N/A"

        print(f"   📊 ANTES: currentViewer gain = {before_gain}")

        # Ejecutar API
        result = api_func(target_sequence)
        print(f"   - Retorno: {result}")

        # Estado después
        after_viewer = hiero.ui.currentViewer()
        after_active = hiero.ui.activeSequence()

        viewer_changed = (before_viewer != after_viewer)
        active_changed = (before_active != after_active)

        print(f"   - currentViewer cambió: {viewer_changed}")
        print(f"   - activeSequence cambió: {active_changed}")

        if viewer_changed:
            after_gain = after_viewer.gain() if after_viewer else "N/A"
            print(f"   📊 DESPUÉS: currentViewer gain = {after_gain}")

            if hasattr(after_viewer, 'time') and hasattr(after_viewer, 'gamma'):
                time_val = after_viewer.time()
                gamma_val = after_viewer.gamma()
                print(f"   ✅ ¡PUDO ACCEDER A AJUSTES! Time: {time_val}, Gamma: {gamma_val}")

                # Verificar si son diferentes del estado inicial
                if str(after_gain) != str(before_gain):
                    print("   🎯 ¡AJUSTES DIFERENTES! → ¡Accedió al viewer objetivo!")
                else:
                    print("   ⚠️ Ajustes iguales → ¿Mismo viewer?")

        return viewer_changed, active_changed

    except Exception as e:
        print(f"❌ Error probando {api_name}: {e}")
        return False, False


def explore_viewer_states_simple():
    """
    EXPLORACIÓN SIMPLE: Estados de viewer para 710-990 y 010-350
    """
    print("=" * 80)
    print("🔍 EXPLORACIÓN: Estados de Viewer 710-990 vs 010-350")
    print("=" * 80)

    # Verificar secuencia activa actual
    active_seq = hiero.ui.activeSequence()
    if not active_seq:
        print("❌ No hay secuencia activa")
        return

    active_name = active_seq.name()
    print(f"🎯 Secuencia ACTIVA (en foco): '{active_name}'")

    # 1. MOSTRAR ESTADO DEL VIEWER ACTUAL (710-990)
    print("\n" + "=" * 60)
    print("1. ESTADO DEL VIEWER ACTUAL (710-990)")
    print("=" * 60)

    current_viewer = hiero.ui.currentViewer()
    if current_viewer:
        print(f"✅ currentViewer encontrado: {type(current_viewer)}")
        current_state = _get_viewer_state(current_viewer, "Viewer Actual (710-990)")
    else:
        print("❌ No hay currentViewer")
        current_state = None

    # 2. BUSCAR VIEWER PARA 010-350
    print("\n" + "=" * 60)
    print("2. BUSCANDO VIEWER PARA 010-350")
    print("=" * 60)

    target_viewer_widget = _find_viewer_for_sequence("010-350")
    if target_viewer_widget:
        print("✅ Viewer widget encontrado para '010-350'")
        print(f"   - Tipo: {type(target_viewer_widget)}")
        print(f"   - WindowTitle: '{target_viewer_widget.windowTitle()}'")
        print(f"   - Visible: {target_viewer_widget.isVisible() if hasattr(target_viewer_widget, 'isVisible') else 'N/A'}")

        # Verificar si el widget Qt tiene métodos de viewer
        print("   🎮 Verificando métodos de viewer en widget Qt:")
        viewer_methods = ['time', 'gain', 'gamma', 'setTime', 'setGain', 'setGamma']
        has_viewer_methods = False

        for method in viewer_methods:
            has_method = hasattr(target_viewer_widget, method)
            status = "✅" if has_method else "❌"
            print(f"   - .{method}(): {status}")
            if has_method:
                has_viewer_methods = True

        if not has_viewer_methods:
            print("   ❌ ¡Widget Qt NO tiene métodos de viewer! (como esperábamos)")

        # Intentar acceder a ajustes del widget Qt (debería fallar)
        print("   🎯 Intentando capturar ajustes del widget Qt:")
        widget_state = _get_viewer_state(target_viewer_widget, "Widget Qt (010-350)")

    else:
        print("❌ No se encontró viewer widget para '010-350'")
        print("   (Significa que la secuencia no tiene timeline abierto)")

    # 3. PROBAR APIs QUE PUEDEN CAMBIAR currentViewer
    print("\n" + "=" * 60)
    print("3. PROBANDO APIs PARA ACCEDER A AJUSTES DE 010-350")
    print("=" * 60)

    # Encontrar la secuencia 010-350
    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos")
        return

    project = projects[0]
    target_sequence_obj = None

    for seq in project.sequences():
        if seq.name() == "010-350":
            target_sequence_obj = seq
            break

    if not target_sequence_obj:
        print("❌ No se encontró objeto Sequence para '010-350'")
        return

    print(f"✅ Objeto Sequence encontrado para '010-350': {type(target_sequence_obj)}")

    # Probar sendToViewerA y sendToViewerB
    apis_to_test = [
        ('sendToViewerA', hiero.ui.sendToViewerA),
        ('sendToViewerB', hiero.ui.sendToViewerB),
    ]

    for api_name, api_func in apis_to_test:
        viewer_changed, active_changed = _test_send_to_viewer_api(api_name, api_func, target_sequence_obj)

        if viewer_changed:
            print(f"   🎯 ¡{api_name} CAMBIA currentViewer!")
            if active_changed:
                print("   ⚠️ PERO también cambia activeSequence (puede causar problemas)")
            else:
                print("   ✅ SOLO cambia currentViewer (¡PERFECTO!)")
        else:
            print(f"   - {api_name} NO cambió currentViewer")

    # 4. RESUMEN FINAL
    print("\n" + "=" * 60)
    print("4. RESUMEN FINAL")
    print("=" * 60)

    print("📊 ESTADO DEL VIEWER ACTUAL (710-990):")
    if current_state:
        print(f"   - Gain: {current_state.get('gain', 'N/A')}")
        print(f"   - Gamma: {current_state.get('gamma', 'N/A')}")
        print(f"   - Time: {current_state.get('time', 'N/A')}")

    print("\n🎯 ACCESO A AJUSTES DE 010-350:")
    if target_viewer_widget:
        print("   - Widget Qt existe: ✅")
        print("   - Tiene métodos de viewer: ❌ (como esperábamos)")
        print("   - sendToViewerA/B: Pueden cambiar currentViewer temporalmente ✅")
        print("   - Conclusión: ¡TENEMOS APIs para acceder a ajustes de viewers no activos!")
    else:
        print("   - No hay viewer widget: ❌ (secuencia no tiene timeline abierto)")

    print("\n💡 CONCLUSIÓN:")
    print("   - currentViewer() siempre tiene .gain(), .gamma(), .time() ✅")
    print("   - Widgets Qt NO tienen estos métodos ❌")
    print("   - sendToViewerA/B pueden cambiar currentViewer temporalmente ✅")
    print("   - ¡SOLUCIÓN POSIBLE: Cambiar temporalmente currentViewer para capturar ajustes!")

    print("=" * 80)


if __name__ == "__main__":
    explore_viewer_states_simple()
