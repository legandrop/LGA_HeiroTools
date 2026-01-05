# =============================================================================
# INVESTIGACIÓN COMPLETA DE TODAS LAS APIs DE TIMELINES EN HIERO
# =============================================================================
# OBJETIVO: Probar sistemáticamente TODAS las funciones relacionadas con timelines
# para encontrar cuál nos da la información correcta sobre qué timelines están abiertos.
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

# =============================================================================
# MÉTODO 1: Buscar widgets TimelineEditor directamente
# =============================================================================

def method_1_find_timeline_widgets():
    """Método 1: Buscar todos los widgets TimelineEditor en QApplication.allWidgets()"""
    debug_print("\n" + "="*80)
    debug_print("🔍 MÉTODO 1: QApplication.allWidgets() - TimelineEditor widgets")
    debug_print("="*80)

    timeline_widgets = []
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app:
            all_widgets = app.allWidgets()
            for widget in all_widgets:
                try:
                    class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                    if "TimelineEditor" in class_name:
                        obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                        window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""
                        is_visible = widget.isVisible() if hasattr(widget, 'isVisible') else False
                        is_hidden = widget.isHidden() if hasattr(widget, 'isHidden') else False

                        if obj_name and obj_name.strip():
                            timeline_widgets.append({
                                'widget': widget,
                                'object_name': obj_name,
                                'window_title': window_title,
                                'is_visible': is_visible,
                                'is_hidden': is_hidden,
                                'class_name': class_name
                            })
                except:
                    pass
    except Exception as e:
        debug_print(f"❌ Error en método 1: {e}")

    debug_print(f"📊 ENCONTRADOS: {len(timeline_widgets)} widgets TimelineEditor")
    for i, tw in enumerate(timeline_widgets):
        status = "ABIERTO" if tw['is_visible'] else "OCULTO"
        debug_print(f"   {i+1}. {tw['object_name']} → '{tw['window_title']}' [{status}]")

    return timeline_widgets

# =============================================================================
# MÉTODO 2: Usar getTimelineEditor() para cada secuencia
# =============================================================================

def method_2_getTimelineEditor_per_sequence():
    """Método 2: getTimelineEditor(sequence) para cada secuencia del proyecto"""
    debug_print("\n" + "="*80)
    debug_print("🔍 MÉTODO 2: getTimelineEditor(sequence) por secuencia")
    debug_print("="*80)

    try:
        projects = hiero.core.projects()
        if not projects:
            debug_print("❌ No hay proyectos")
            return []

        project = projects[0]
        all_sequences = project.sequences()

        timeline_editors = []
        for seq in all_sequences:
            seq_name = seq.name()
            try:
                timeline_editor = hiero.ui.getTimelineEditor(seq)
                if timeline_editor:
                    window = timeline_editor.window()
                    obj_name = safe_window_property(window, 'objectName', 'N/A')
                    window_title = safe_window_property(window, 'windowTitle', 'N/A')
                    is_visible = safe_window_property(window, 'isVisible', False)

                    timeline_editors.append({
                        'sequence_name': seq_name,
                        'timeline_editor': timeline_editor,
                        'object_name': obj_name,
                        'window_title': window_title,
                        'is_visible': is_visible,
                        'sequence': seq
                    })

                    status = "ABIERTO" if is_visible else "EXISTE PERO NO VISIBLE"
                    debug_print(f"   ✅ {seq_name} → {obj_name} [{status}]")
                else:
                    debug_print(f"   ❌ {seq_name} → None")
            except Exception as e:
                debug_print(f"   ❌ {seq_name} → Error: {e}")

        debug_print(f"\n📊 TOTAL: {len(timeline_editors)} timeline editors devueltos por getTimelineEditor()")
        return timeline_editors

    except Exception as e:
        debug_print(f"❌ Error en método 2: {e}")
        return []

# =============================================================================
# MÉTODO 3: Explorar APIs en hiero.ui relacionadas con timelines
# =============================================================================

def method_3_explore_hiero_ui_timeline_apis():
    """Método 3: Explorar todas las APIs de hiero.ui relacionadas con timelines"""
    debug_print("\n" + "="*80)
    debug_print("🔍 MÉTODO 3: Explorar APIs hiero.ui para timelines")
    debug_print("="*80)

    ui_attrs = dir(hiero.ui)
    timeline_related = [attr for attr in ui_attrs if 'timeline' in attr.lower()]

    debug_print(f"📋 APIs relacionadas con timeline en hiero.ui: {len(timeline_related)}")
    for api in sorted(timeline_related):
        debug_print(f"   • {api}")

    # Probar cada API
    results = {}
    for api_name in timeline_related:
        try:
            api = getattr(hiero.ui, api_name)
            if callable(api):
                debug_print(f"\n🧪 Probando {api_name}():")

                # Probar con diferentes parámetros
                try:
                    # Sin parámetros
                    result = api()
                    debug_print(f"   ✅ {api_name}() → {type(result)}")
                    if hasattr(result, '__len__') and len(result) < 10:
                        debug_print(f"      Contenido: {result}")
                    results[api_name] = result
                except Exception as e:
                    debug_print(f"   ❌ {api_name}() → Error: {e}")

                # Probar con activeSequence si es aplicable
                if 'sequence' in api_name.lower():
                    try:
                        active_seq = hiero.ui.activeSequence()
                        if active_seq:
                            result = api(active_seq)
                            debug_print(f"   ✅ {api_name}(activeSequence) → {type(result)}")
                            results[f"{api_name}_active"] = result
                    except Exception as e:
                        debug_print(f"   ❌ {api_name}(activeSequence) → Error: {e}")

            else:
                debug_print(f"⚠️ {api_name} no es callable")
                results[api_name] = api

        except Exception as e:
            debug_print(f"❌ Error probando {api_name}: {e}")

    return results

# =============================================================================
# MÉTODO 4: Buscar timelines usando diferentes estrategias de filtrado
# =============================================================================

def method_4_filtered_timeline_search():
    """Método 4: Buscar timelines con diferentes criterios de filtrado"""
    debug_print("\n" + "="*80)
    debug_print("🔍 MÉTODO 4: Búsqueda filtrada de timelines")
    debug_print("="*80)

    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            debug_print("❌ No hay QApplication")
            return {}

        all_widgets = app.allWidgets()
        debug_print(f"📊 Total widgets en aplicación: {len(all_widgets)}")

        # Filtrar por diferentes criterios
        filters = {
            'TimelineEditor_visible': lambda w: ("TimelineEditor" in safe_window_property(w, 'metaObject().className', "")) and safe_window_property(w, 'isVisible', False),
            'TimelineEditor_all': lambda w: "TimelineEditor" in safe_window_property(w, 'metaObject().className', ""),
            'windowTitle_not_empty': lambda w: safe_window_property(w, 'windowTitle', "").strip() != "",
            'objectName_not_empty': lambda w: safe_window_property(w, 'objectName', "").strip() != "",
        }

        results = {}

        for filter_name, filter_func in filters.items():
            matching_widgets = [w for w in all_widgets if filter_func(w)]
            results[filter_name] = []

            debug_print(f"\n🔍 Filtro '{filter_name}': {len(matching_widgets)} widgets")

            for i, widget in enumerate(matching_widgets):
                try:
                    obj_name = safe_window_property(widget, 'objectName', 'N/A')
                    window_title = safe_window_property(widget, 'windowTitle', 'N/A')
                    class_name = safe_window_property(widget, 'metaObject().className', 'N/A')
                    is_visible = safe_window_property(widget, 'isVisible', False)

                    widget_info = {
                        'index': i+1,
                        'object_name': obj_name,
                        'window_title': window_title,
                        'class_name': class_name,
                        'is_visible': is_visible
                    }

                    results[filter_name].append(widget_info)

                    status = "ABIERTO" if is_visible else "OCULTO"
                    debug_print(f"   {i+1}. {obj_name} → '{window_title}' [{status}]")

                except Exception as e:
                    debug_print(f"   {i+1}. Error: {e}")

        return results

    except Exception as e:
        debug_print(f"❌ Error en método 4: {e}")
        return {}

# =============================================================================
# MÉTODO 5: Comparación cruzada de todos los métodos
# =============================================================================

def method_5_cross_comparison():
    """Método 5: Comparar resultados de todos los métodos"""
    debug_print("\n" + "="*80)
    debug_print("🔍 MÉTODO 5: COMPARACIÓN CRUZADA DE TODOS LOS MÉTODOS")
    debug_print("="*80)

    # Ejecutar todos los métodos
    results = {
        'method_1': method_1_find_timeline_widgets(),
        'method_2': method_2_getTimelineEditor_per_sequence(),
        'method_4': method_4_filtered_timeline_search(),
    }

    # Intentar method_3 (puede fallar)
    try:
        results['method_3'] = method_3_explore_hiero_ui_timeline_apis()
    except:
        results['method_3'] = {}

    # Extraer object_names de cada método
    object_names_by_method = {}

    # Method 1: widgets encontrados
    object_names_by_method['method_1'] = [tw['object_name'] for tw in results['method_1']]

    # Method 2: getTimelineEditor results
    object_names_by_method['method_2'] = [te['object_name'] for te in results['method_2'] if te['object_name'] != 'N/A']

    # Method 4: diferentes filtros
    for filter_name, widgets in results['method_4'].items():
        object_names_by_method[f'method_4_{filter_name}'] = [w['object_name'] for w in widgets if w['object_name'] != 'N/A']

    # Comparar
    debug_print("\n📊 COMPARACIÓN DE OBJECT NAMES POR MÉTODO:")
    for method_name, obj_names in object_names_by_method.items():
        debug_print(f"   {method_name}: {len(obj_names)} objetos → {sorted(obj_names)}")

    # Encontrar intersecciones
    debug_print("\n🎯 ANÁLISIS DE INTERSECCIONES:")

    all_methods = list(object_names_by_method.keys())
    for i, method1 in enumerate(all_methods):
        for j, method2 in enumerate(all_methods):
            if i < j:  # Evitar duplicados
                set1 = set(object_names_by_method[method1])
                set2 = set(object_names_by_method[method2])
                intersection = set1 & set2
                union = set1 | set2
                jaccard = len(intersection) / len(union) if union else 0

                debug_print(f"   {method1} ∩ {method2}: {len(intersection)} objetos")
                if intersection:
                    debug_print(f"      Coinciden: {sorted(intersection)}")
                debug_print(".2f")

    # Determinar cuál método parece más correcto
    debug_print("\n🎯 ANÁLISIS DE CUAL MÉTODO ES CORRECTO:")
    debug_print("   (Basado en que sabemos que hay aproximadamente 3-4 timelines realmente abiertos)")

    for method_name, obj_names in object_names_by_method.items():
        count = len(obj_names)
        assessment = ""
        if count == 4:  # Basado en resultados anteriores
            assessment = "⭐ POSIBLEMENTE CORRECTO"
        elif count < 4:
            assessment = "⚠️ POCO (puede estar filtrando demasiado)"
        else:
            assessment = "⚠️ MUCHO (puede incluir widgets fantasma)"

        debug_print(f"   {method_name}: {count} timelines {assessment}")

    return results

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

debug_print("🚀 INICIANDO INVESTIGACIÓN COMPLETA DE APIs DE TIMELINES")
debug_print("="*80)

try:
    # Ejecutar comparación cruzada que incluye todos los métodos
    all_results = method_5_cross_comparison()

    debug_print("\n" + "="*80)
    debug_print("📋 RESUMEN EJECUTIVO")
    debug_print("="*80)
    debug_print("Hemos probado 5 métodos diferentes para encontrar timelines abiertos:")
    debug_print("1. Buscar widgets TimelineEditor en QApplication")
    debug_print("2. getTimelineEditor() para cada secuencia")
    debug_print("3. Explorar APIs relacionadas con timeline en hiero.ui")
    debug_print("4. Búsqueda con diferentes filtros")
    debug_print("5. Comparación cruzada de todos los métodos")
    debug_print("\nEl método que devuelva exactamente los timelines que sabes que están")
    debug_print("abiertos (aprox 3-4) es el correcto para usar.")

    debug_print("\n✅ INVESTIGACIÓN COMPLETADA")

except Exception as e:
    debug_print(f"\n❌ ERROR EN INVESTIGACIÓN: {e}")
    import traceback
    debug_print(traceback.format_exc())
