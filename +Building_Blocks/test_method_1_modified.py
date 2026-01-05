# =============================================================================
# PRUEBA DEL MÉTODO 1 MODIFICADO
# =============================================================================
# OBJETIVO: Probar el MÉTODO 1 (TimelineEditor widgets) de manera más detallada
# para identificar correctamente cuáles timelines están realmente "abiertos en UI"
# =============================================================================

import hiero.core
import hiero.ui

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def safe_window_property(window, property_name, default="N/A"):
    """Obtiene una propiedad del window de manera segura"""
    if not window:
        return default
    try:
        if hasattr(window, property_name):
            method = getattr(window, property_name)
            if callable(method):
                return method()
    except:
        pass
    return default

def detailed_timeline_analysis():
    """Análisis detallado de TODOS los widgets TimelineEditor encontrados"""

    debug_print("=" * 100)
    debug_print("🔬 ANÁLISIS DETALLADO: TODOS LOS WIDGETS TIMELINE EDITOR")
    debug_print("=" * 100)

    timeline_widgets = []

    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            debug_print("❌ No hay QApplication")
            return []

        all_widgets = app.allWidgets()

        debug_print(f"📊 Buscando en {len(all_widgets)} widgets totales...")

        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if "TimelineEditor" in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                    if obj_name and obj_name.strip():
                        # Recopilar TODAS las propiedades de visibilidad posibles
                        properties = {
                            'object_name': obj_name,
                            'window_title': window_title,
                            'class_name': class_name,
                            'isVisible': safe_window_property(widget, 'isVisible', False),
                            'isHidden': safe_window_property(widget, 'isHidden', True),
                            'isMinimized': safe_window_property(widget, 'isMinimized', False),
                            'isMaximized': safe_window_property(widget, 'isMaximized', False),
                            'isActiveWindow': safe_window_property(widget, 'isActiveWindow', False),
                            'isEnabled': safe_window_property(widget, 'isEnabled', True),
                            'width': safe_window_property(widget, 'width', 0),
                            'height': safe_window_property(widget, 'height', 0),
                            'x': safe_window_property(widget, 'x', 0),
                            'y': safe_window_property(widget, 'y', 0),
                        }

                        # Verificar si está en la jerarquía de widgets visibles
                        parent = widget.parent()
                        parent_info = ""
                        if parent:
                            parent_class = safe_window_property(parent, 'metaObject().className', 'N/A')
                            parent_visible = safe_window_property(parent, 'isVisible', False)
                            parent_info = f"Parent: {parent_class} (visible: {parent_visible})"

                        properties['parent_info'] = parent_info

                        # Calcular status basado en criterios (para el resumen final)
                        criterios_pasados = 0
                        if properties['isVisible'] and not properties['isHidden']:
                            criterios_pasados += 1
                        if properties['isActiveWindow']:
                            criterios_pasados += 1
                        if "visible: True" in properties['parent_info'] and properties['width'] > 100 and properties['height'] > 50:
                            criterios_pasados += 1

                        if criterios_pasados >= 2:
                            properties['status'] = 'CANDIDATO FUERTE'
                        elif criterios_pasados >= 1:
                            properties['status'] = 'CANDIDATO DÉBIL'
                        else:
                            properties['status'] = 'DESCARTADO'

                        timeline_widgets.append(properties)

            except Exception as e:
                debug_print(f"   ❌ Error analizando widget: {e}")
                continue

    except Exception as e:
        debug_print(f"❌ Error en búsqueda: {e}")
        return []

    debug_print(f"\n✅ ENCONTRADOS: {len(timeline_widgets)} widgets TimelineEditor")
    debug_print("-" * 100)

    # Mostrar cada timeline con TODA su información
    for i, tw in enumerate(timeline_widgets, 1):
        debug_print(f"\n🔍 TIMELINE {i}: {tw['object_name']}")
        debug_print(f"   📋 Título: '{tw['window_title']}'")
        debug_print(f"   📋 Clase: {tw['class_name']}")
        debug_print(f"   👁️  isVisible: {tw['isVisible']}")
        debug_print(f"   🙈 isHidden: {tw['isHidden']}")
        debug_print(f"   🪟 isActiveWindow: {tw['isActiveWindow']}")
        debug_print(f"   ✅ isEnabled: {tw['isEnabled']}")
        debug_print(f"   📏 Dimensiones: {tw['width']}x{tw['height']}")
        debug_print(f"   📍 Posición: ({tw['x']}, {tw['y']})")
        debug_print(f"   👨‍👩‍👧 Parent: {tw['parent_info']}")

        # Probar MÚLTIPLES CRITERIOS para determinar si está "abierto en UI"

        # CRITERIO 1: Solo isVisible=True (muy estricto)
        criterio_1 = tw['isVisible'] and not tw['isHidden']
        status_1 = "✅ ABIERTO" if criterio_1 else "❌ CERRADO"

        # CRITERIO 2: isActiveWindow=True (diferente enfoque)
        criterio_2 = tw['isActiveWindow']
        status_2 = "✅ ABIERTO" if criterio_2 else "❌ CERRADO"

        # CRITERIO 3: Parent visible + dimensiones razonables
        parent_visible = "visible: True" in tw['parent_info']
        good_size = tw['width'] > 100 and tw['height'] > 50
        criterio_3 = parent_visible and good_size
        status_3 = "✅ ABIERTO" if criterio_3 else "❌ CERRADO"

        # CRITERIO 4: Buscar en jerarquía de tabs/windows (nuevo enfoque)
        try:
            # Buscar si este widget está en alguna tab o window activa
            from LGA_QtAdapter_HieroTools import QtWidgets
            app = QtWidgets.QApplication.instance()
            if app:
                # Buscar windows principales
                main_windows = [w for w in app.allWidgets() if hasattr(w, 'windowTitle') and w.windowTitle()]
                criterio_4 = False
                for win in main_windows:
                    if hasattr(win, 'findChildren'):
                        # Buscar tabs o panels dentro de windows principales
                        tabs = win.findChildren(QtWidgets.QTabWidget)
                        for tab_widget in tabs:
                            if hasattr(tab_widget, 'tabText'):
                                for i in range(tab_widget.count()):
                                    tab_text = tab_widget.tabText(i)
                                    if tab_text == tw['window_title']:
                                        criterio_4 = True
                                        break
                        if criterio_4:
                            break
            status_4 = "✅ ABIERTO" if criterio_4 else "❌ CERRADO"
        except:
            criterio_4 = False
            status_4 = "❌ ERROR"

        debug_print(f"   🎯 CRITERIOS DE APERTURA:")
        debug_print(f"      1. Solo isVisible: {status_1}")
        debug_print(f"      2. isActiveWindow: {status_2}")
        debug_print(f"      3. Parent+Size: {status_3}")
        debug_print(f"      4. En tabs: {status_4}")

        # DETERMINAR EL MEJOR CANDIDATO
        # Contar cuántos criterios pasan
        criterios_pasados = sum([criterio_1, criterio_2, criterio_3, criterio_4])
        final_status = "🎯 CANDIDATO FUERTE" if criterios_pasados >= 2 else "⚠️ CANDIDATO DÉBIL" if criterios_pasados >= 1 else "❌ DESCARTADO"

        debug_print(f"   🏆 RESULTADO FINAL: {final_status} ({criterios_pasados}/4 criterios)")
        debug_print(f"   📊 Criterios pasados: {criterios_pasados}")
        debug_print("-" * 50)

    return timeline_widgets

def compare_with_active_sequence(timeline_widgets):
    """Comparar los timelines encontrados con la secuencia activa"""

    debug_print("\n" + "="*100)
    debug_print("🎯 COMPARACIÓN CON SECUENCIA ACTIVA")
    debug_print("="*100)

    try:
        active_seq = hiero.ui.activeSequence()
        if active_seq:
            active_seq_name = active_seq.name()
            debug_print(f"📋 Secuencia ACTIVA: {active_seq_name}")

            # Buscar cuál timeline corresponde a la secuencia activa
            active_timeline = None
            for tw in timeline_widgets:
                if tw['window_title'] == active_seq_name:
                    active_timeline = tw
                    break

            if active_timeline:
                debug_print(f"✅ TIMELINE ACTIVO encontrado: {active_timeline['object_name']}")
                debug_print(f"   📋 Título: '{active_timeline['window_title']}'")
                debug_print(f"   👁️  isVisible: {active_timeline['isVisible']}")
            else:
                debug_print("❌ No se encontró timeline correspondiente a la secuencia activa")
        else:
            debug_print("⚠️ No hay secuencia activa")

    except Exception as e:
        debug_print(f"❌ Error en comparación: {e}")

def analyze_tab_widgets():
    """Analizar widgets de tabs para encontrar timelines abiertos"""

    debug_print("\n" + "="*100)
    debug_print("📑 MÉTODO 5: ANÁLISIS DE WIDGETS DE TABS")
    debug_print("="*100)

    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            debug_print("❌ No hay QApplication")
            return

        # Buscar QTabWidget que contengan timelines
        tab_widgets = []
        for widget in app.allWidgets():
            try:
                if isinstance(widget, QtWidgets.QTabWidget):
                    tab_widgets.append(widget)
            except:
                pass

        debug_print(f"📊 Encontrados {len(tab_widgets)} widgets QTabWidget")

        timeline_tabs = []
        for tab_widget in tab_widgets:
            try:
                tab_count = tab_widget.count()
                debug_print(f"\n🔍 TabWidget con {tab_count} tabs:")

                for i in range(tab_count):
                    tab_text = tab_widget.tabText(i)
                    debug_print(f"   Tab {i+1}: '{tab_text}'")

                    # Si el tab text coincide con un nombre de secuencia, es un timeline
                    if tab_text and tab_text in ['360-700', '710-990', '010-350', 'z_EditRef_v1_6_20250725', 'z_EditRef_v.0.2']:
                        timeline_tabs.append({
                            'tab_widget': tab_widget,
                            'tab_index': i,
                            'tab_text': tab_text,
                            'is_current': tab_widget.currentIndex() == i
                        })
                        status = "🎯 ACTIVA" if tab_widget.currentIndex() == i else "📑 visible"
                        debug_print(f"      → TIMELINE {status}")

            except Exception as e:
                debug_print(f"   ❌ Error analizando tab: {e}")

        debug_print(f"\n📋 MÉTODO 5 RESULTADO: {len(timeline_tabs)} timelines encontrados en tabs")
        return timeline_tabs

    except Exception as e:
        debug_print(f"❌ Error en método 5: {e}")
        return []

def find_timelines_in_main_windows():
    """MÉTODO 6: Buscar timelines en windows principales de Hiero"""

    debug_print("\n" + "="*100)
    debug_print("🏠 MÉTODO 6: BUSCAR EN WINDOWS PRINCIPALES DE HIERO")
    debug_print("="*100)

    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            debug_print("❌ No hay QApplication")
            return []

        # Buscar windows principales (que tienen título)
        main_windows = []
        for widget in app.allWidgets():
            try:
                if (hasattr(widget, 'windowTitle') and
                    widget.windowTitle() and
                    hasattr(widget, 'isWindow') and
                    widget.isWindow()):
                    main_windows.append(widget)
            except:
                pass

        debug_print(f"📊 Encontradas {len(main_windows)} windows principales")

        timelines_in_windows = []
        for win in main_windows:
            try:
                win_title = win.windowTitle()
                debug_print(f"\n🔍 Window: '{win_title}'")

                # Buscar TimelineEditor dentro de esta window
                timeline_editors = win.findChildren(QtWidgets.QWidget)
                local_timelines = []

                for child in timeline_editors:
                    try:
                        class_name = child.metaObject().className() if hasattr(child, 'metaObject') else ""
                        if "TimelineEditor" in class_name:
                            obj_name = child.objectName() if hasattr(child, 'objectName') else ""
                            child_title = child.windowTitle() if hasattr(child, 'windowTitle') else ""

                            if obj_name and obj_name.strip():
                                local_timelines.append({
                                    'window_title': win_title,
                                    'timeline_obj': obj_name,
                                    'timeline_title': child_title,
                                    'is_visible': child.isVisible() if hasattr(child, 'isVisible') else False
                                })
                                status = "👁️ VISIBLE" if child.isVisible() else "🙈 OCULTO"
                                debug_print(f"   → Timeline: {obj_name} ({status})")
                    except:
                        pass

                if local_timelines:
                    timelines_in_windows.extend(local_timelines)
                    debug_print(f"   📊 Total timelines en esta window: {len(local_timelines)}")

            except Exception as e:
                debug_print(f"   ❌ Error analizando window: {e}")

        debug_print(f"\n📋 MÉTODO 6 RESULTADO: {len(timelines_in_windows)} timelines en windows principales")
        return timelines_in_windows

    except Exception as e:
        debug_print(f"❌ Error en método 6: {e}")
        return []

def find_timelines_via_hiero_api():
    """MÉTODO 7: Usar APIs específicas de Hiero para encontrar timelines"""

    debug_print("\n" + "="*100)
    debug_print("🎯 MÉTODO 7: APIs ESPECÍFICAS DE HIERO")
    debug_print("="*100)

    try:
        # Intentar usar hiero.ui para encontrar panels
        ui_attrs = dir(hiero.ui)

        # Buscar métodos relacionados con panels o windows
        panel_methods = [attr for attr in ui_attrs if any(keyword in attr.lower() for keyword in ['panel', 'window', 'tab', 'dock'])]

        debug_print(f"📋 APIs relacionadas con panels/windows: {len(panel_methods)}")
        for method in panel_methods:
            debug_print(f"   • {method}")

        # Probar algunos métodos específicos
        results = {}

        # Probar getTimelineEditor para cada secuencia (ya lo hicimos)
        debug_print("\n🔄 getTimelineEditor (repetido para comparación):")
        projects = hiero.core.projects()
        if projects:
            project = projects[0]
            for seq in project.sequences():
                try:
                    timeline = hiero.ui.getTimelineEditor(seq)
                    if timeline:
                        debug_print(f"   ✅ {seq.name()} → tiene timeline")
                    else:
                        debug_print(f"   ❌ {seq.name()} → sin timeline")
                except Exception as e:
                    debug_print(f"   ❌ {seq.name()} → error: {e}")

        debug_print(f"\n📋 MÉTODO 7 RESULTADO: Exploradas {len(panel_methods)} APIs de Hiero")
        return results

    except Exception as e:
        debug_print(f"❌ Error en método 7: {e}")
        return {}

def manual_verification_questions():
    """Preguntas para verificar manualmente cuáles timelines están abiertos"""

    debug_print("\n" + "="*100)
    debug_print("🔍 VERIFICACIÓN MANUAL - ¿CUÁLES ESTÁN REALMENTE ABIERTOS?")
    debug_print("="*100)

    debug_print("Para determinar correctamente cuáles timelines están 'abiertos en UI',")
    debug_print("necesito que mires en Hiero y me digas:")
    debug_print("")
    debug_print("1. ¿Cuántas pestañas de timeline ves en la interfaz?")
    debug_print("2. ¿Qué nombres aparecen en las pestañas de timeline?")
    debug_print("3. ¿Cuál es la secuencia activa (la que está seleccionada)?")
    debug_print("")
    debug_print("Con esta información podremos ajustar la lógica de detección.")
    debug_print("="*100)

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

debug_print("🚀 PRUEBA DEL MÉTODO 1 MODIFICADO")
debug_print("="*100)

try:
    # Ejecutar análisis detallado
    timeline_widgets = detailed_timeline_analysis()

    # Comparar con secuencia activa
    if timeline_widgets:
        compare_with_active_sequence(timeline_widgets)

    # MÉTODO 5: Analizar widgets de tabs
    debug_print("\n" + "="*100)
    tab_timelines = analyze_tab_widgets()

    # MÉTODO 6: Buscar en windows principales
    debug_print("\n" + "="*100)
    window_timelines = find_timelines_in_main_windows()

    # MÉTODO 7: APIs específicas de Hiero
    debug_print("\n" + "="*100)
    hiero_api_results = find_timelines_via_hiero_api()

    # RESUMEN FINAL COMPARATIVO
    debug_print("\n" + "="*100)
    debug_print("📊 RESUMEN COMPARATIVO FINAL - 7 MÉTODOS")
    debug_print("="*100)

    debug_print(f"🔍 MÉTODO 1 - Widgets TimelineEditor: {len(timeline_widgets)} encontrados")
    debug_print(f"📑 MÉTODO 5 - Timelines en tabs: {len(tab_timelines)} encontrados")
    debug_print(f"🏠 MÉTODO 6 - Timelines en windows: {len(window_timelines)} encontrados")
    debug_print(f"🎯 MÉTODO 7 - APIs Hiero: {len(hiero_api_results)} resultados")

    # Contar candidatos por criterios
    strong_candidates = [tw for tw in timeline_widgets if tw.get('status') == 'CANDIDATO FUERTE']
    weak_candidates = [tw for tw in timeline_widgets if tw.get('status') == 'CANDIDATO DÉBIL']
    discarded = [tw for tw in timeline_widgets if tw.get('status') == 'DESCARTADO']

    debug_print(f"\n🎯 CANDIDATOS FUERTES (≥2 criterios): {len(strong_candidates)}")
    for tw in strong_candidates:
        debug_print(f"   • {tw['object_name']} → {tw['window_title']}")

    debug_print(f"\n⚠️ CANDIDATOS DÉBILES (1 criterio): {len(weak_candidates)}")
    for tw in weak_candidates:
        debug_print(f"   • {tw['object_name']} → {tw['window_title']}")

    debug_print(f"\n❌ DESCARTADOS (0 criterios): {len(discarded)}")
    for tw in discarded:
        debug_print(f"   • {tw['object_name']} → {tw['window_title']}")

    # Preguntas para verificación manual
    manual_verification_questions()

    debug_print("\n✅ ANÁLISIS COMPLETADO - 7 MÉTODOS DIFERENTES")
    debug_print(f"📊 Resultados: M1={len(timeline_widgets)} | M5={len(tab_timelines)} | M6={len(window_timelines)} | M7={len(hiero_api_results)}")

except Exception as e:
    debug_print(f"\n❌ ERROR GENERAL: {e}")
    import traceback
    debug_print(traceback.format_exc())
