"""
SCRIPT DE IDENTIFICACIÓN DE VIEWERS/TIMELINES PARA REFRESH
================================================================

OBJETIVO: Identificar correctamente qué viewers y timelines existen actualmente
         y cuáles deberían cerrarse después del refresh.

ESTRATEGIA:
- Usar metaObject().className() para encontrar viewers (como el panel)
- Comparar con currentViewer() para identificar qué mantener
- MOSTRAR información clara sin modificar nada
- Preparar para cierre seguro con deleteLater()

USO: Ejecutar este script para ver el estado actual antes de refresh
"""

import hiero.core
import hiero.ui

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def collect_viewers_real():
    """Recopila viewers reales - solo los que tienen objectName válido."""
    viewers = []

    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            return viewers

        # ÚNICA ESTRATEGIA: metaObject().className() + objectName válido
        for widget in app.allWidgets():
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if "Foundry::Storm::UI::Viewer" in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                    # Intentar obtener nombre de secuencia asociada
                    seq_name = "Sin secuencia"
                    try:
                        # Los viewers de Hiero tienen una secuencia asociada
                        if hasattr(widget, 'player') and widget.player():
                            player = widget.player()
                            if hasattr(player, 'sequence') and player.sequence():
                                seq = player.sequence()
                                seq_name = seq.name() if hasattr(seq, 'name') else "Sin nombre"
                    except:
                        seq_name = "Error obteniendo secuencia"

                    # SOLO incluir viewers con objectName válido (evitar widgets basura)
                    if obj_name and obj_name.strip():
                        viewers.append({
                            'viewer': widget,
                            'object_name': obj_name,
                            'window_title': window_title,
                            'sequence_name': seq_name,
                            'id': hex(id(widget)),
                            'method': 'metaObject().className()'
                        })
            except Exception:
                continue

        # Eliminar duplicados por objectName
        unique_viewers = []
        seen_names = set()
        for viewer in viewers:
            obj_name = viewer['object_name']
            if obj_name not in seen_names:
                unique_viewers.append(viewer)
                seen_names.add(obj_name)

        viewers = unique_viewers

    except Exception as e:
        debug_print(f"❌ Error collecting viewers: {e}")

    return viewers

def explore_viewer_names(viewer_widget):
    """Explora todas las formas posibles de obtener nombres descriptivos de un viewer."""
    debug_print(f"\n🔍 EXPLORANDO NOMBRES PARA VIEWER {hex(id(viewer_widget))}:")

    # Propiedades básicas
    obj_name = viewer_widget.objectName() if hasattr(viewer_widget, 'objectName') else "N/A"
    debug_print(f"   objectName(): '{obj_name}'")

    window_title = viewer_widget.windowTitle() if hasattr(viewer_widget, 'windowTitle') else "N/A"
    debug_print(f"   windowTitle(): '{window_title}'")

    # Intentar acceder a la secuencia a través del player
    seq_name = "N/A"
    try:
        if hasattr(viewer_widget, 'player') and viewer_widget.player():
            player = viewer_widget.player()
            if hasattr(player, 'sequence') and player.sequence():
                seq = player.sequence()
                seq_name = seq.name() if hasattr(seq, 'name') else "Sin name()"
    except Exception as e:
        seq_name = f"Error: {e}"

    debug_print(f"   sequence.name(): '{seq_name}'")

    # Buscar otras propiedades que puedan tener nombres
    interesting_attrs = ['title', 'name', 'label', 'text', 'displayName']
    for attr in interesting_attrs:
        if hasattr(viewer_widget, attr):
            try:
                value = getattr(viewer_widget, attr)()
                if value and str(value).strip():
                    debug_print(f"   {attr}(): '{value}'")
            except:
                try:
                    value = getattr(viewer_widget, attr)
                    if value and str(value).strip():
                        debug_print(f"   {attr}: '{value}'")
                except:
                    pass

    # Buscar en hijos/widgets hijos
    try:
        if hasattr(viewer_widget, 'children'):
            for child in viewer_widget.children():
                if hasattr(child, 'objectName'):
                    child_obj = child.objectName()
                    if child_obj and ('title' in child_obj.lower() or 'name' in child_obj.lower()):
                        debug_print(f"   child objectName: '{child_obj}'")
                        if hasattr(child, 'text'):
                            try:
                                child_text = child.text()
                                if child_text and str(child_text).strip():
                                    debug_print(f"   child.text(): '{child_text}'")
                            except:
                                pass
    except:
        pass

def collect_timelines():
    """Recopila timelines abiertos con objectName válido."""
    timelines = []
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            return timelines

        for widget in app.allWidgets():
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if "TimelineEditor" in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                    # Solo incluir timelines con objectName válido
                    if obj_name and obj_name.strip():
                        seq_name = "Sin secuencia"
                        try:
                            seq = widget.sequence() if hasattr(widget, 'sequence') else None
                            if seq:
                                seq_name = seq.name()
                        except:
                            seq_name = "Error obteniendo secuencia"

                        timelines.append({
                            'widget': widget,
                            'object_name': obj_name,
                            'window_title': window_title,
                            'sequence_name': seq_name,
                            'id': hex(id(widget)),
                            'method': 'metaObject().className()'
                        })
            except Exception:
                continue

        # Eliminar duplicados por objectName
        unique_timelines = []
        seen_names = set()
        for timeline in timelines:
            obj_name = timeline['object_name']
            if obj_name not in seen_names:
                unique_timelines.append(timeline)
                seen_names.add(obj_name)

        timelines = unique_timelines

    except Exception as e:
        debug_print(f"❌ Error collecting timelines: {e}")

    return timelines

def analyze_current_state():
    """Analiza el estado actual de viewers y timelines."""
    debug_print("=" * 80)
    debug_print("ANÁLISIS DE ESTADO ACTUAL - VIEWERS Y TIMELINES")
    debug_print("=" * 80)

    # 1. Viewer actual
    debug_print("\n🎯 VIEWER ACTUAL:")
    current_viewer = hiero.ui.currentViewer()
    if current_viewer:
        window = current_viewer.window()
        obj_name = window.objectName() if window and hasattr(window, 'objectName') else "N/A"
        debug_print(f"   ✅ currentViewer(): {obj_name} (ID: {hex(id(current_viewer))})")
        current_viewer_id = hex(id(current_viewer))
    else:
        debug_print("   ❌ No hay viewer actual")
        current_viewer_id = None

    # 2. Secuencia actual
    debug_print("\n🎯 SECUENCIA ACTUAL:")
    active_seq = hiero.ui.activeSequence()
    if active_seq:
        debug_print(f"   ✅ activeSequence(): '{active_seq.name()}' (ID: {hex(id(active_seq))})")
        active_seq_name = active_seq.name()
    else:
        debug_print("   ❌ No hay secuencia activa")
        active_seq_name = None

    # 3. Timeline actual
    debug_print("\n🎯 TIMELINE ACTUAL:")
    if active_seq:
        current_timeline = hiero.ui.getTimelineEditor(active_seq)
        if current_timeline:
            window = current_timeline.window()
            obj_name = window.objectName() if window and hasattr(window, 'objectName') else "N/A"
            debug_print(f"   ✅ getTimelineEditor(): {obj_name} (ID: {hex(id(current_timeline))})")
            current_timeline_id = hex(id(current_timeline))
        else:
            debug_print("   ❌ No hay timeline para la secuencia activa")
            current_timeline_id = None
    else:
        current_timeline_id = None

    # 4. TODOS los viewers encontrados con múltiples métodos
    debug_print("\n🔍 TODOS LOS VIEWERS ENCONTRADOS:")
    all_viewers = collect_viewers_real()

    debug_print(f"   Total viewers encontrados: {len(all_viewers)}")
    for i, viewer in enumerate(all_viewers, 1):
        obj_name = viewer.get('object_name', 'N/A')
        window_title = viewer.get('window_title', '')
        seq_name = viewer.get('sequence_name', 'N/A')
        method = viewer.get('method', 'unknown')

        # Mostrar nombre más descriptivo disponible
        display_name = window_title or seq_name or obj_name
        debug_print(f"   {i}. {display_name} (obj: {obj_name}, seq: {seq_name}) [método: {method}]")

    # INTENTO DE IDENTIFICACIÓN: Comparar objectNames de ventanas
    active_viewers = []
    old_viewers = []

    debug_print(f"\n🔍 INTENTANDO IDENTIFICAR VIEWER ACTIVO:")
    debug_print(f"   currentViewer() ID: {current_viewer_id}")

    # Obtener el objectName del viewer actual
    current_obj_name = "N/A"
    if current_viewer:
        try:
            current_window = current_viewer.window()
            if current_window and hasattr(current_window, 'objectName'):
                current_obj_name = current_window.objectName()
        except Exception as e:
            debug_print(f"   Error obteniendo objectName del currentViewer: {e}")

    debug_print(f"   currentViewer objectName: '{current_obj_name}'")

    for viewer_info in all_viewers:
        obj_name = viewer_info.get('object_name', '')
        viewer_id = viewer_info['id']
        method = viewer_info.get('method', 'unknown')

        # Comparar objectNames - esta debería ser la forma correcta
        is_current = (obj_name == current_obj_name and obj_name != "N/A")

        window_title = viewer_info.get('window_title', '')
        seq_name = viewer_info.get('sequence_name', 'N/A')

        # Mostrar nombre más descriptivo
        display_name = window_title or seq_name or obj_name
        status = "🎯 ACTIVO" if is_current else "📍 VIEJO"
        debug_print(f"   {status}: '{display_name}' (obj: {obj_name}, seq: {seq_name}) [método: {method}]")

        if is_current:
            active_viewers.append(viewer_info)
        else:
            old_viewers.append(viewer_info)

    # Verificar resultados
    if len(active_viewers) == 0:
        debug_print(f"\n❌ PROBLEMA CRÍTICO:")
        debug_print(f"   - currentViewer existe: {current_viewer is not None}")
        debug_print(f"   - currentViewer objectName: '{current_obj_name}'")
        debug_print(f"   - Viewers encontrados: {len(all_viewers)}")
        debug_print(f"   - objectNames encontrados: {[v.get('object_name', 'N/A') for v in all_viewers]}")
        debug_print(f"   - CONCLUSIÓN: metaObject() NO encuentra el mismo widget que currentViewer()")

    elif len(active_viewers) > 1:
        debug_print(f"\n⚠️  MÚLTIPLES VIEWERS IDENTIFICADOS COMO ACTIVOS: {len(active_viewers)}")
        for v in active_viewers:
            debug_print(f"     - {v.get('object_name', 'N/A')} (ID: {v['id']})")

    else:
        debug_print(f"\n✅ IDENTIFICACIÓN EXITOSA:")
        debug_print(f"   - 1 viewer activo identificado correctamente")
        debug_print(f"   - {len(old_viewers)} viewers viejos para cerrar")

    # 5. TODOS los timelines encontrados
    debug_print("\n🔍 TODOS LOS TIMELINES ENCONTRADOS:")
    all_timelines = collect_timelines()
    debug_print(f"   Total timelines encontrados: {len(all_timelines)}")

    for i, timeline in enumerate(all_timelines, 1):
        obj_name = timeline.get('object_name', 'N/A')
        window_title = timeline.get('window_title', '')
        seq_name = timeline.get('sequence_name', 'N/A')
        method = timeline.get('method', 'unknown')

        # Mostrar nombre más descriptivo disponible
        display_name = window_title or seq_name or obj_name
        debug_print(f"   {i}. {display_name} (obj: {obj_name}, seq: {seq_name}) [método: {method}]")

    active_timelines = []
    old_timelines = []

    # Comparar por objectName como hicimos con viewers
    debug_print(f"\n🔍 COMPARACIÓN DE TIMELINES:")
    current_timeline_obj_name = "N/A"
    if current_timeline:
        try:
            current_window = current_timeline.window()
            if current_window and hasattr(current_window, 'objectName'):
                current_timeline_obj_name = current_window.objectName()
        except Exception as e:
            debug_print(f"   Error obteniendo objectName del timeline actual: {e}")

    debug_print(f"   getTimelineEditor() objectName: '{current_timeline_obj_name}'")

    for timeline_info in all_timelines:
        obj_name = timeline_info.get('object_name', '')
        window_title = timeline_info.get('window_title', '')
        seq_name = timeline_info.get('sequence_name', 'N/A')
        timeline_id = timeline_info['id']
        method = timeline_info.get('method', 'unknown')

        # Comparar objectNames
        is_current = (obj_name == current_timeline_obj_name and obj_name != "N/A")

        # Mostrar nombre más descriptivo
        display_name = window_title or seq_name or obj_name
        status = "🎯 ACTIVO" if is_current else "📍 VIEJO"
        debug_print(f"   {status}: '{display_name}' (obj: {obj_name}, seq: {seq_name}) [método: {method}]")

        if is_current:
            active_timelines.append(timeline_info)
        else:
            old_timelines.append(timeline_info)

    # 6. RESUMEN Y RECOMENDACIONES
    debug_print("\n" + "=" * 80)
    debug_print("📊 RESUMEN Y RECOMENDACIONES")
    debug_print("=" * 80)

    debug_print(f"\n🎯 ELEMENTOS ACTIVOS (MANTENER):")
    debug_print(f"   Viewers activos: {len(active_viewers)}")
    for v in active_viewers:
        debug_print(f"     - {v['object_name']}")

    debug_print(f"   Timelines activos: {len(active_timelines)}")
    for t in active_timelines:
        debug_print(f"     - {t['object_name']} ({t['sequence_name']})")

    debug_print(f"\n📍 ELEMENTOS VIEJOS (POSIBLEMENTE CERRAR):")
    debug_print(f"   Viewers viejos: {len(old_viewers)}")
    for v in old_viewers:
        debug_print(f"     - {v['object_name']} (deleteLater candidato)")

    debug_print(f"   Timelines viejos: {len(old_timelines)}")
    for t in old_timelines:
        debug_print(f"     - {t['object_name']} ({t['sequence_name']})")

    debug_print(f"\n💡 PARA REFRESH TIMELINE:")
    if old_viewers:
        debug_print(f"   🎯 Después de openInTimeline(), cerrar {len(old_viewers)} viewers viejos con deleteLater()")
        for v in old_viewers:
            debug_print(f"      - widget.deleteLater() para {v['object_name']}")
    else:
        debug_print("   ✅ No hay viewers viejos que cerrar")

    if old_timelines:
        debug_print(f"   ⚠️  También hay {len(old_timelines)} timelines viejos - considerar cerrar")
    else:
        debug_print("   ✅ No hay timelines viejos")

    # RESUMEN CLARO FINAL
    debug_print(f"\n" + "="*80)
    debug_print("📋 RESUMEN EJECUTIVO")
    debug_print("="*80)

    # Viewer activo
    if active_viewers:
        active_window_title = active_viewers[0].get('window_title', '')
        active_seq_name = active_viewers[0].get('sequence_name', 'N/A')
        active_obj_name = active_viewers[0].get('object_name', 'Sin nombre')
        # Usar el nombre más descriptivo disponible
        active_display_name = active_window_title or active_seq_name or active_obj_name
        debug_print(f"🎯 VIEWER ACTIVO: {active_display_name}")
    else:
        debug_print("❌ VIEWER ACTIVO: NO IDENTIFICADO")

    # Timeline activo
    if active_timelines:
        active_timeline_window_title = active_timelines[0].get('window_title', '')
        active_timeline_seq_name = active_timelines[0].get('sequence_name', 'N/A')
        active_timeline_obj_name = active_timelines[0].get('object_name', 'Sin nombre')
        # Usar el nombre más descriptivo disponible
        active_timeline_display_name = active_timeline_window_title or active_timeline_seq_name or active_timeline_obj_name
        debug_print(f"🎯 TIMELINE ACTIVO: {active_timeline_display_name}")
    else:
        debug_print("❌ TIMELINE ACTIVO: NO IDENTIFICADO")

    # Viewers a cerrar (filtrar Contact Sheet)
    if old_viewers:
        old_viewer_names = []
        for v in old_viewers:
            window_title = v.get('window_title', '')
            seq_name = v.get('sequence_name', 'N/A')
            obj_name = v.get('object_name', '')

            # Filtrar Contact Sheet - no es un viewer de secuencia
            if 'contactsheet' in obj_name.lower():
                continue

            # Usar el nombre más descriptivo disponible
            display_name = window_title or seq_name or obj_name
            if display_name and display_name != 'N/A':
                old_viewer_names.append(display_name)

        if old_viewer_names:
            debug_print(f"📍 VIEWERS A CERRAR: {', '.join(old_viewer_names)}")
        else:
            debug_print(f"📍 VIEWERS A CERRAR: {len([v for v in old_viewers if 'contactsheet' not in v.get('object_name', '').lower()])} sin nombre válido")
    else:
        debug_print("✅ NO HAY VIEWERS PARA CERRAR")

    # Timelines a cerrar
    if old_timelines:
        old_timeline_names = []
        for t in old_timelines:
            window_title = t.get('window_title', '')
            seq_name = t.get('sequence_name', 'N/A')
            obj_name = t.get('object_name', '')
            # Usar el nombre más descriptivo disponible
            display_name = window_title or seq_name or obj_name
            if display_name and display_name != 'N/A':
                old_timeline_names.append(display_name)

        if old_timeline_names:
            debug_print(f"📍 TIMELINES A CERRAR: {', '.join(old_timeline_names)}")
        else:
            debug_print(f"📍 TIMELINES A CERRAR: {len(old_timelines)} sin nombre válido")
    else:
        debug_print("✅ NO HAY TIMELINES PARA CERRAR")

    return {
        'active_viewer': current_viewer,
        'active_sequence': active_seq,
        'active_timeline': current_timeline if active_seq else None,
        'old_viewers': old_viewers,
        'old_timelines': old_timelines,
        'active_viewer_name': active_viewers[0]['object_name'] if active_viewers else None,
        'old_viewer_names': [v['object_name'] for v in old_viewers if v['object_name']]
    }

def main():
    """Función principal - SOLO IDENTIFICA, NO MODIFICA"""
    debug_print("🔍 IDENTIFICACIÓN DE VIEWERS/TIMELINES PARA REFRESH")
    debug_print("   (Este script SOLO analiza - NO modifica nada)")
    debug_print("")

    try:
        result = analyze_current_state()

        debug_print("\n" + "=" * 80)
        debug_print("✅ ANÁLISIS COMPLETADO - NADA MODIFICADO")
        debug_print("=" * 80)

        debug_print("\n📋 PRÓXIMOS PASOS:")
        debug_print("   1. Revisar si la identificación es correcta")
        debug_print("   2. Si sí, implementar cierre seguro con deleteLater()")
        debug_print("   3. Probar refresh timeline completo")

        return result

    except Exception as e:
        debug_print(f"❌ ERROR en identificación: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()
