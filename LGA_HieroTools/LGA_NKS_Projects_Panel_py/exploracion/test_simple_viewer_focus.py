"""
Test Simple: Cambiar foco a viewer de '010-350' - Estrategia Cerrar→Reabrir
===========================================================================

Script simple que prueba la estrategia definitiva: Si existe viewer → Cerrarlo → Reabrir
Esto evita duplicados porque siempre hay máximo 1 viewer por secuencia.

OBJETIVO: Confirmar que cerrar existente + openInTimeline funciona perfectamente
sin dejar duplicados.
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


TARGET_SEQUENCE = "010-350"


def _process_events():
    """Procesa eventos de Qt."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def _find_viewer_widgets():
    """Encuentra todos los widgets de viewer."""
    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets
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


def _debug_viewer_states(title="Estado de Viewers"):
    """Muestra estado de viewers."""
    print(f"🔍 {title}:")
    viewer_widgets = _find_viewer_widgets()

    if not viewer_widgets:
        print("  ❌ No viewers encontrados")
        return

    for i, viewer in enumerate(viewer_widgets):
        try:
            title = viewer.windowTitle() if hasattr(viewer, 'windowTitle') else "Sin título"
            visible = viewer.isVisible() if hasattr(viewer, 'isVisible') else "N/A"
            status = "🎯" if visible and title == TARGET_SEQUENCE else "  "
            print(f"  {status} {i+1}. '{title}' - Visible: {visible}")
        except Exception as e:
            print(f"  {i+1}. Error: {e}")
    print()


def test_focus_method_1_basic_show_hide():
    """Método 1: Básico show/hide."""
    print("🎯 MÉTODO 1: Básico show/hide")
    print("=" * 50)

    _debug_viewer_states("INICIAL")

    target_viewer = _find_viewer_for_sequence(TARGET_SEQUENCE)
    if not target_viewer:
        print(f"❌ Viewer para '{TARGET_SEQUENCE}' no encontrado")
        return False

    print(f"✅ Viewer encontrado: {target_viewer.windowTitle()}")

    # Ocultar todos menos el objetivo
    all_viewers = _find_viewer_widgets()
    for viewer in all_viewers:
        try:
            title = viewer.windowTitle() if hasattr(viewer, 'windowTitle') else ""
            if viewer != target_viewer and title != TARGET_SEQUENCE:
                if viewer.isVisible():
                    print(f"  👁️ Ocultando: '{title}'")
                    viewer.hide()
        except Exception:
            pass

    # Mostrar el objetivo
    print(f"  👁️ Mostrando: '{TARGET_SEQUENCE}'")
    target_viewer.show()
    target_viewer.raise_()

    _process_events()
    _debug_viewer_states("DESPUÉS show/hide")

    # Verificar
    new_active = hiero.ui.activeSequence()
    success = new_active and new_active.name() == TARGET_SEQUENCE
    print(f"  🎯 Secuencia activa: '{new_active.name() if new_active else 'Ninguna'}'")
    print(f"  {'✅' if success else '❌'} Éxito: {success}")
    print()

    return success


def test_focus_method_2_with_activate():
    """Método 2: Con activateWindow."""
    print("🎯 MÉTODO 2: Con activateWindow")
    print("=" * 50)

    _debug_viewer_states("INICIAL")

    target_viewer = _find_viewer_for_sequence(TARGET_SEQUENCE)
    if not target_viewer:
        print(f"❌ Viewer para '{TARGET_SEQUENCE}' no encontrado")
        return False

    print(f"✅ Viewer encontrado: {target_viewer.windowTitle()}")

    # Ocultar todos menos el objetivo
    all_viewers = _find_viewer_widgets()
    for viewer in all_viewers:
        try:
            title = viewer.windowTitle() if hasattr(viewer, 'windowTitle') else ""
            if viewer != target_viewer and title != TARGET_SEQUENCE:
                if viewer.isVisible():
                    print(f"  👁️ Ocultando: '{title}'")
                    viewer.hide()
        except Exception:
            pass

    # Mostrar y activar
    print(f"  👁️ Mostrando y activando: '{TARGET_SEQUENCE}'")
    target_viewer.show()
    target_viewer.raise_()
    target_viewer.activateWindow()

    _process_events()
    _debug_viewer_states("DESPUÉS activateWindow")

    # Verificar
    new_active = hiero.ui.activeSequence()
    success = new_active and new_active.name() == TARGET_SEQUENCE
    print(f"  🎯 Secuencia activa: '{new_active.name() if new_active else 'Ninguna'}'")
    print(f"  {'✅' if success else '❌'} Éxito: {success}")
    print()

    return success


def test_focus_method_3_find_and_click():
    """Método 3: Buscar y simular click."""
    print("🎯 MÉTODO 3: Buscar y simular click")
    print("=" * 50)

    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        _debug_viewer_states("INICIAL")

        # Buscar algún widget relacionado con la secuencia que sea clickeable
        all_widgets = QtWidgets.QApplication.instance().allWidgets()

        sequence_widgets = []
        for widget in all_widgets:
            try:
                text = ""
                if hasattr(widget, 'text'):
                    text = widget.text()
                elif hasattr(widget, 'windowTitle'):
                    text = widget.windowTitle()
                elif hasattr(widget, 'objectName'):
                    text = widget.objectName()

                if TARGET_SEQUENCE in text:
                    sequence_widgets.append((widget, text, type(widget).__name__))
            except Exception:
                continue

        print(f"  📋 Widgets con '{TARGET_SEQUENCE}': {len(sequence_widgets)}")
        for widget, text, class_name in sequence_widgets[:5]:  # Primeros 5
            print(f"    - {class_name}: '{text}'")

        # Intentar encontrar algo clickeable (como un tab o botón)
        clickable_found = False
        for widget, text, class_name in sequence_widgets:
            try:
                # Buscar widgets que podrían ser tabs o botones
                if 'Tab' in class_name or 'Button' in class_name or 'Item' in class_name:
                    if hasattr(widget, 'click'):
                        print(f"  🖱️ Click en {class_name}: '{text}'")
                        widget.click()
                        clickable_found = True
                        _process_events()
                        break
            except Exception as e:
                print(f"    Error clicking {class_name}: {e}")

        if not clickable_found:
            print("  ❌ No se encontró widget clickeable")
            return False

        _process_events()
        _debug_viewer_states("DESPUÉS de click")

        # Verificar
        new_active = hiero.ui.activeSequence()
        success = new_active and new_active.name() == TARGET_SEQUENCE
        print(f"  🎯 Secuencia activa: '{new_active.name() if new_active else 'Ninguna'}'")
        print(f"  {'✅' if success else '❌'} Éxito: {success}")
        print()

        return success

    except Exception as e:
        print(f"❌ Error en método 3: {e}")
        return False


def test_focus_method_4_force_sequence_activation():
    """Método 4: Forzar activación de secuencia sin crear viewer."""
    print("🎯 MÉTODO 4: Forzar activación de secuencia")
    print("=" * 50)

    _debug_viewer_states("INICIAL")

    # Verificar que el viewer objetivo existe
    target_viewer = _find_viewer_for_sequence(TARGET_SEQUENCE)
    if not target_viewer:
        print(f"❌ Viewer para '{TARGET_SEQUENCE}' no encontrado")
        return False

    print(f"✅ Viewer encontrado: {target_viewer.windowTitle()}")

    # Encontrar la secuencia correspondiente
    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos")
        return False

    project = projects[0]
    target_seq = None
    for seq in project.sequences():
        if seq.name() == TARGET_SEQUENCE:
            target_seq = seq
            break

    if not target_seq:
        print(f"❌ Secuencia '{TARGET_SEQUENCE}' no encontrada")
        return False

    # INTENTAR: Cambiar visibilidad Y forzar activación de secuencia
    print("  🔄 Cambiando visibilidad del viewer...")

    # Ocultar todos los demás
    all_viewers = _find_viewer_widgets()
    for viewer in all_viewers:
        try:
            title = viewer.windowTitle() if hasattr(viewer, 'windowTitle') else ""
            if viewer != target_viewer and title != TARGET_SEQUENCE:
                if viewer.isVisible():
                    viewer.hide()
        except Exception:
            pass

    # Mostrar el objetivo con todos los métodos
    target_viewer.show()
    target_viewer.raise_()
    target_viewer.activateWindow()

    # INTENTAR FORZAR ACTIVACIÓN DE SECUENCIA
    print("  🎯 Intentando forzar activación de secuencia...")

    # Método 1: Intentar setSequence en currentViewer
    current_viewer = hiero.ui.currentViewer()
    if current_viewer:
        print("  🔧 Intentando setSequence en currentViewer...")
        try:
            # Buscar método setSequence
            if hasattr(current_viewer, 'setSequence'):
                current_viewer.setSequence(target_seq)
                print("  ✅ setSequence ejecutado en currentViewer")
            else:
                print("  ❌ currentViewer no tiene setSequence")
        except Exception as e:
            print(f"  ❌ Error en setSequence: {e}")

    # Método 2: Buscar timeline editor y usar setSequence
    print("  🔧 Intentando setSequence en timeline editor...")
    try:
        timeline_ed = hiero.ui.getTimelineEditor(target_seq)
        if timeline_ed:
            # Buscar métodos de activación
            methods_to_try = ['setSequence', 'setActiveSequence', 'activate']
            for method in methods_to_try:
                if hasattr(timeline_ed, method):
                    try:
                        getattr(timeline_ed, method)(target_seq)
                        print(f"  ✅ {method} ejecutado en timeline editor")
                        break
                    except Exception as e:
                        print(f"  ❌ Error en {method}: {e}")
        else:
            print("  ❌ No se encontró timeline editor")
    except Exception as e:
        print(f"  ❌ Error accediendo timeline editor: {e}")

    _process_events()
    _debug_viewer_states("DESPUÉS de forzar activación")

    # Verificar resultado
    new_active = hiero.ui.activeSequence()
    success = new_active and new_active.name() == TARGET_SEQUENCE
    print(f"  🎯 Secuencia activa: '{new_active.name() if new_active else 'Ninguna'}'")
    print(f"  {'✅' if success else '❌'} Éxito: {success}")
    print()

    return success


def test_focus_method_5_close_and_reopen():
    """Método 5: Cerrar viewer existente y reabrir (evita duplicados)."""
    print("🎯 MÉTODO 5: Cerrar existente → Reabrir")
    print("=" * 50)

    _debug_viewer_states("INICIAL")

    # PASO 1: Buscar viewer existente
    existing_viewer = _find_viewer_for_sequence(TARGET_SEQUENCE)
    if existing_viewer:
        print(f"✅ Viewer existente encontrado: '{existing_viewer.windowTitle()}'")
        print("  🔒 Cerrando viewer existente para evitar duplicados...")

        # Intentar cerrar el viewer existente
        try:
            existing_viewer.close()
            _process_events()
            print("  ✅ Viewer existente cerrado")
        except Exception as e:
            print(f"  ⚠️ Error cerrando viewer: {e}")

        _debug_viewer_states("DESPUÉS de cerrar existente")

    else:
        print(f"ℹ️ No hay viewer existente para '{TARGET_SEQUENCE}'")

    # PASO 2: Abrir secuencia con openInTimeline (ahora no crea duplicado)
    print("  🚀 Abriendo secuencia con openInTimeline...")

    # Encontrar la secuencia
    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos")
        return False

    project = projects[0]
    target_seq = None
    for seq in project.sequences():
        if seq.name() == TARGET_SEQUENCE:
            target_seq = seq
            break

    if not target_seq:
        print(f"❌ Secuencia '{TARGET_SEQUENCE}' no encontrada")
        return False

    # Abrir con openInTimeline
    try:
        result = hiero.ui.openInTimeline(target_seq)
        _process_events()
        print("  ✅ openInTimeline ejecutado")

        _debug_viewer_states("DESPUÉS de openInTimeline")

        # Verificar resultado
        new_active = hiero.ui.activeSequence()
        success = new_active and new_active.name() == TARGET_SEQUENCE

        print(f"  🎯 Secuencia activa: '{new_active.name() if new_active else 'Ninguna'}'")
        print(f"  {'✅' if success else '❌'} Éxito: {success}")

        if success:
            print("  🎉 ¡MÉTODO PERFECTO! Cierra existente → Reabre → Sin duplicados")

        return success

    except Exception as e:
        print(f"  ❌ Error en openInTimeline: {e}")
        return False


def main():
    """Función principal - probar todos los métodos."""
    print("=" * 80)
    print(f"🧪 TEST SIMPLE: Cambiar foco a viewer '{TARGET_SEQUENCE}'")
    print("=" * 80)
    print()

    # Verificar estado inicial
    active_seq = hiero.ui.activeSequence()
    active_name = active_seq.name() if active_seq else "Ninguna"
    print(f"🎯 Secuencia activa inicial: '{active_name}'")
    print()

    # Probar métodos uno por uno
    results = []

    print("🔬 PROBANDO DIFERENTES MÉTODOS:")
    print("=" * 80)

    results.append(("Método 1 (show/hide)", test_focus_method_1_basic_show_hide()))
    results.append(("Método 2 (activateWindow)", test_focus_method_2_with_activate()))
    results.append(("Método 3 (buscar y click)", test_focus_method_3_find_and_click()))
    results.append(("Método 4 (forzar activación)", test_focus_method_4_force_sequence_activation()))
    results.append(("Método 5 (cerrar→reabrir)", test_focus_method_5_close_and_reopen()))

    print("=" * 80)
    print("📊 RESULTADOS FINALES:")
    print("=" * 80)

    for method_name, success in results:
        status = "✅ FUNCIONA" if success else "❌ FALLA"
        print(f"  {method_name}: {status}")

    successful_methods = sum(1 for _, success in results if success)
    print(f"\n🎯 MÉTODOS EXITOSOS: {successful_methods}/{len(results)}")

    if successful_methods == 0:
        print("❌ NINGÚN MÉTODO FUNCIONÓ - Necesitamos investigar más")
    elif successful_methods >= 1:
        working_methods = [name for name, success in results if success]
        print(f"✅ MÉTODOS QUE FUNCIONAN: {', '.join(working_methods)}")

        # El método 5 es el recomendado
        if results[4][1]:  # Método 5 funcionó
            print("🎯 MÉTODO 5 RECOMENDADO: Cierra existente → Reabre → Sin duplicados")
        elif any('openInTimeline' in name for name, _ in results if _):
            print("⚠️ ATENCIÓN: Algunos métodos pueden crear duplicados")
    else:
        print("🔍 Necesitamos encontrar el método correcto")

    print("=" * 80)


if __name__ == "__main__":
    main()
