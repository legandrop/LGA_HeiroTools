"""
EXPLORACIÓN VIEWER-CENTRIC: Detectando Timelines Abiertos en Hiero
===================================================================

Script que explora desde el lado del VIEWER para encontrar timelines
abiertos pero no activos. En Hiero, viewers y timelines están
completamente relacionados.

OBJETIVO: Encontrar viewers "ocultos" o "en background" que
correspondan a secuencias con timeline abierto pero no visible.
"""

import hiero.core
import hiero.ui

def explore_viewer_sequence_relationship():
    """Explora la relación entre viewers y secuencias."""
    print("=" * 80)
    print("🔍 EXPLORACIÓN: VIEWERS vs SECUENCIAS")
    print("=" * 80)

    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos abiertos.")
        return

    project = projects[0]
    all_sequences = project.sequences()

    print(f"📁 Proyecto: {project.name()}")
    print(f"📋 Total secuencias: {len(all_sequences)}")
    print()

    # Obtener secuencia activa
    active_seq = hiero.ui.activeSequence()
    active_name = active_seq.name() if active_seq else "Ninguna"
    print(f"🎯 Secuencia activa: '{active_name}'")
    print()

    # Explorar currentViewer
    print("🔍 CURRENT VIEWER:")
    try:
        current_viewer = hiero.ui.currentViewer()
        if current_viewer:
            print(f"✅ Current viewer encontrado: {type(current_viewer)}")

            # Explorar propiedades del viewer
            viewer_props = [attr for attr in dir(current_viewer) if not attr.startswith('_')]
            sequence_related = [p for p in viewer_props if 'sequence' in p.lower() or 'seq' in p.lower()]

            print(f"📋 Propiedades del viewer: {len(viewer_props)}")
            print(f"🎬 Propiedades relacionadas con secuencia: {len(sequence_related)}")

            for prop in sorted(sequence_related):
                try:
                    value = getattr(current_viewer, prop)
                    if callable(value):
                        print(f"  ✅ {prop}: callable")
                        # Intentar llamar métodos seguros
                        if prop in ['sequence', 'getSequence']:
                            try:
                                seq_result = value()
                                if seq_result:
                                    print(f"     → Secuencia: '{seq_result.name()}'")
                                else:
                                    print(f"     → Secuencia: None")
                            except Exception as e:
                                print(f"     → Error llamando: {e}")
                    else:
                        print(f"  📄 {prop}: {value}")
                except Exception as e:
                    print(f"  ❌ {prop}: Error - {e}")

        else:
            print("❌ No current viewer")

    except Exception as e:
        print(f"❌ Error explorando current viewer: {e}")

    print()


def explore_all_viewers():
    """Busca todos los viewers disponibles en Hiero."""
    print("=" * 80)
    print("🔍 EXPLORACIÓN: TODOS LOS VIEWERS")
    print("=" * 80)

    try:
        # Buscar métodos relacionados con viewers en hiero.ui
        ui_methods = [attr for attr in dir(hiero.ui) if not attr.startswith('_')]
        viewer_methods = [m for m in ui_methods if 'viewer' in m.lower()]

        print(f"📋 Métodos relacionados con viewer: {len(viewer_methods)}")
        for method in sorted(viewer_methods):
            print(f"  - {method}")

        print()

        # Explorar métodos de viewer
        viewer_method_tests = [
            ('currentViewer', 'Devuelve el viewer actual'),
            ('getViewer', 'Podría devolver viewer específico'),
            ('viewers', 'Podría listar todos los viewers'),
            ('allViewers', 'Podría listar todos los viewers'),
        ]

        for method_name, description in viewer_method_tests:
            if hasattr(hiero.ui, method_name):
                print(f"🔧 Probando {method_name}: {description}")
                try:
                    method = getattr(hiero.ui, method_name)
                    if callable(method):
                        # Intentar llamar sin parámetros
                        try:
                            result = method()
                            print(f"  ✅ Llamada exitosa: {type(result)}")
                            if isinstance(result, list):
                                print(f"     → Lista con {len(result)} elementos")
                                for i, item in enumerate(result[:3]):  # Mostrar primeros 3
                                    print(f"       [{i}] {type(item)} - {item}")
                            elif result:
                                print(f"     → Resultado: {result}")
                            else:
                                print("     → Resultado: None")
                        except Exception as e:
                            print(f"  ❌ Error llamando: {e}")
                    else:
                        print(f"  📄 Propiedad: {method}")
                except Exception as e:
                    print(f"  ❌ Error accediendo: {e}")
            else:
                print(f"❌ {method_name}: no disponible")

            print()

    except Exception as e:
        print(f"❌ Error general en exploración de viewers: {e}")
        import traceback
        traceback.print_exc()

    print()


def explore_viewer_sequence_correlation():
    """Explora la correlación entre viewers y secuencias."""
    print("=" * 80)
    print("🔍 CORRELACIÓN: VIEWERS ↔ SECUENCIAS")
    print("=" * 80)

    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos.")
        return

    project = projects[0]
    all_sequences = project.sequences()

    print(f"📁 Proyecto: {project.name()}")
    print(f"📋 Secuencias: {len(all_sequences)}")
    print()

    # Obtener current viewer y explorar su secuencia
    print("🔍 CURRENT VIEWER ANALYSIS:")
    try:
        current_viewer = hiero.ui.currentViewer()
        if current_viewer:
            print("✅ Current viewer encontrado")

            # Buscar métodos que puedan dar info sobre secuencia
            viewer_methods = [m for m in dir(current_viewer) if not m.startswith('_')]
            seq_methods = [m for m in viewer_methods if 'seq' in m.lower() or 'sequence' in m.lower()]

            print(f"📊 Métodos de secuencia en viewer: {len(seq_methods)}")

            for method in seq_methods:
                try:
                    attr = getattr(current_viewer, method)
                    if callable(attr):
                        print(f"  🔧 {method}: callable")
                        # Intentar llamar métodos seguros
                        if method in ['sequence', 'getSequence', 'currentSequence']:
                            try:
                                seq = attr()
                                if seq:
                                    print(f"     → Secuencia conectada: '{seq.name()}'")
                                else:
                                    print("     → Sin secuencia conectada")
                            except Exception as e:
                                print(f"     → Error: {e}")
                    else:
                        print(f"  📄 {method}: {attr}")
                except Exception as e:
                    print(f"  ❌ {method}: Error - {e}")

        else:
            print("❌ No current viewer")

    except Exception as e:
        print(f"❌ Error analizando current viewer: {e}")

    print()


def explore_sequence_viewer_connection():
    """Explora cómo conectar secuencias con viewers específicos."""
    print("=" * 80)
    print("🔍 CONEXIÓN: SECUENCIAS → VIEWERS")
    print("=" * 80)

    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos.")
        return

    project = projects[0]
    all_sequences = project.sequences()

    print(f"📁 Proyecto: {project.name()}")
    print(f"📋 Secuencias: {len(all_sequences)}")
    print()

    # Probar diferentes formas de conectar secuencia con viewer
    print("🔍 PROBANDO CONEXIONES SECUENCIA-VIEWER:")

    for seq in all_sequences:
        try:
            seq_name = seq.name()
            print(f"\n📝 Secuencia: '{seq_name}'")

            # Método 1: getTimelineEditor y buscar viewer asociado
            ed = hiero.ui.getTimelineEditor(seq)
            if ed:
                print("  ✅ Tiene timeline editor")

                # Buscar propiedades de viewer en el editor
                editor_attrs = [attr for attr in dir(ed) if not attr.startswith('_')]
                viewer_attrs = [a for a in editor_attrs if 'viewer' in a.lower()]

                if viewer_attrs:
                    print(f"  🎥 Propiedades de viewer en editor: {viewer_attrs}")

                    for attr in viewer_attrs:
                        try:
                            value = getattr(ed, attr)
                            if callable(value):
                                print(f"    🔧 {attr}: callable")
                                # Intentar llamar métodos seguros
                                if attr in ['viewer', 'getViewer']:
                                    try:
                                        viewer_result = value()
                                        if viewer_result:
                                            print(f"       → Viewer obtenido: {type(viewer_result)}")
                                            # Verificar si es el mismo que currentViewer
                                            current_viewer = hiero.ui.currentViewer()
                                            is_current = (viewer_result == current_viewer)
                                            print(f"       → Es current viewer: {is_current}")
                                        else:
                                            print("       → Viewer: None")
                                    except Exception as e:
                                        print(f"       → Error obteniendo viewer: {e}")
                            else:
                                print(f"    📄 {attr}: {value}")
                        except Exception as e:
                            print(f"    ❌ {attr}: Error - {e}")
                else:
                    print("  ❌ No hay propiedades de viewer en el editor")

            else:
                print("  ❌ No tiene timeline editor")

        except Exception as e:
            print(f"❌ Error procesando secuencia: {e}")

    print()


def explore_hidden_viewers():
    """Busca viewers ocultos o en background que puedan corresponder a timelines abiertos."""
    print("=" * 80)
    print("🔍 BÚSQUEDA DE VIEWERS OCULTOS")
    print("=" * 80)

    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets

        # Buscar todos los widgets de viewer
        all_widgets = QtWidgets.QApplication.instance().allWidgets()
        viewer_widgets = []

        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else str(type(widget))
                object_name = widget.objectName() if hasattr(widget, 'objectName') else ""

                # Buscar widgets de viewer
                if 'viewer' in class_name.lower() or 'Viewer' in class_name:
                    viewer_widgets.append((widget, class_name, object_name))

            except Exception:
                continue

        print(f"🎥 Widgets de viewer encontrados: {len(viewer_widgets)}")
        print()

        for i, (widget, class_name, object_name) in enumerate(viewer_widgets):
            visible = widget.isVisible() if hasattr(widget, 'isVisible') else "N/A"
            print(f"  {i+1}. {class_name}")
            print(f"     ObjectName: '{object_name}'")
            print(f"     Visible: {visible}")
            print(f"     Widget ID: {id(widget)}")

            # Información adicional
            if hasattr(widget, 'windowTitle'):
                try:
                    title = widget.windowTitle()
                    print(f"     Window Title: '{title}'")
                except:
                    pass

            print()

        # Comparar con current viewer
        current_viewer = hiero.ui.currentViewer()
        if current_viewer:
            print("🔍 COMPARACIÓN CON CURRENT VIEWER:")
            print(f"  Current viewer ID: {id(current_viewer)}")

            # Ver si alguno de los widgets encontrados corresponde al current viewer
            matching_widgets = [w for w, _, _ in viewer_widgets if id(w) == id(current_viewer)]
            if matching_widgets:
                print("  ✅ Current viewer encontrado en la lista de widgets")
            else:
                print("  ⚠️ Current viewer NO encontrado en la lista de widgets")

        print()

    except Exception as e:
        print(f"❌ Error buscando viewers ocultos: {e}")
        import traceback
        traceback.print_exc()

    print()


def main():
    """Función principal - Enfoque VIEWER-CENTRIC."""
    print("🚀 EXPLORACIÓN VIEWER-CENTRIC: TIMELINES ABIERTOS EN HIERO")
    print("OBJETIVO: Encontrar viewers ocultos que correspondan a timelines abiertos")
    print()

    try:
        explore_viewer_sequence_relationship()
        explore_all_viewers()
        explore_viewer_sequence_correlation()
        explore_sequence_viewer_connection()
        explore_hidden_viewers()

        print("=" * 80)
        print("✅ EXPLORACIÓN VIEWER-CENTRIC COMPLETADA")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
