"""
SCRIPT DE CIERRE SEGURO DE VIEWERS VIEJOS
================================================================

OBJETIVO: Cerrar viewers y timelines viejos de forma segura usando deleteLater()

ESTRATEGIA VALIDADA:
- Identificar viewers con metaObject().className()
- Comparar objectNames para distinguir activo vs viejos
- Filtrar Contact Sheet (no es viewer de secuencia)
- Cerrar con deleteLater() (diferido, seguro vs close() que crashea)

USO: Ejecutar después del refresh timeline para limpiar viewers duplicados
"""

import hiero.core
import hiero.ui

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def collect_and_analyze_viewers():
    """Recopila y analiza viewers actuales vs viejos."""
    viewers = []
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            return [], [], []

        # Buscar viewers con metaObject().className()
        for widget in app.allWidgets():
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if "Foundry::Storm::UI::Viewer" in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                    # Intentar obtener sequence name
                    seq_name = "Sin secuencia"
                    try:
                        if hasattr(widget, 'player') and widget.player():
                            player = widget.player()
                            if hasattr(player, 'sequence') and player.sequence():
                                seq = player.sequence()
                                seq_name = seq.name() if hasattr(seq, 'name') else "Sin nombre"
                    except:
                        seq_name = "Error obteniendo secuencia"

                    # Solo incluir viewers con objectName válido
                    if obj_name and obj_name.strip():
                        viewers.append({
                            'widget': widget,
                            'object_name': obj_name,
                            'window_title': window_title,
                            'sequence_name': seq_name,
                            'id': hex(id(widget))
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

    # Comparar con currentViewer()
    current_viewer = hiero.ui.currentViewer()
    current_obj_name = ""
    if current_viewer:
        try:
            current_window = current_viewer.window()
            if current_window and hasattr(current_window, 'objectName'):
                current_obj_name = current_window.objectName()
        except Exception as e:
            debug_print(f"Error obteniendo current objectName: {e}")

    # Separar activo vs viejos
    active_viewers = []
    old_viewers = []

    for viewer_info in viewers:
        obj_name = viewer_info.get('object_name', '')
        is_current = (obj_name == current_obj_name and obj_name != "")

        if is_current:
            active_viewers.append(viewer_info)
        else:
            old_viewers.append(viewer_info)

    return viewers, active_viewers, old_viewers

def collect_and_analyze_timelines():
    """Recopila y analiza timelines actuales vs viejos."""
    timelines = []
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            return [], [], []

        # Buscar timelines
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
                            'id': hex(id(widget))
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

    # MÉTODO NUEVO: Identificar timeline activo usando el método que funcionó ⭐
    current_timeline = None
    current_obj_name = ""

    try:
        # Usar el mismo método que funcionó en explore_timeline_identification.py
        # Método 7: Iterar por secuencias del proyecto y encontrar el timeline correspondiente
        projects = hiero.core.projects()
        if projects:
            project = projects[0]  # Proyecto actual
            sequences = project.sequences()

            # Obtener la secuencia del currentViewer
            current_viewer = hiero.ui.currentViewer()
            if current_viewer:
                viewer_sequence = current_viewer.player().sequence() if current_viewer.player() else None
                if viewer_sequence:
                    viewer_seq_name = viewer_sequence.name()

                    # Buscar el timeline que corresponde a esta secuencia
                    for seq in sequences:
                        try:
                            timeline = hiero.ui.getTimelineEditor(seq)
                            if timeline and seq.name() == viewer_seq_name:
                                current_timeline = timeline
                                break
                        except:
                            pass

        # Obtener el objectName del timeline activo encontrado
        if current_timeline:
            try:
                current_window = current_timeline.window()
                if current_window and hasattr(current_window, 'objectName'):
                    current_obj_name = current_window.objectName()
            except Exception as e:
                debug_print(f"Error obteniendo timeline objectName: {e}")
    except Exception as e:
        debug_print(f"Error en método nuevo de identificación de timeline: {e}")

    # Separar activo vs viejos
    active_timelines = []
    old_timelines = []

    for timeline_info in timelines:
        obj_name = timeline_info.get('object_name', '')
        is_current = (obj_name == current_obj_name and obj_name != "")

        if is_current:
            active_timelines.append(timeline_info)
        else:
            old_timelines.append(timeline_info)

    return timelines, active_timelines, old_timelines

def close_old_viewers_safe(old_viewers):
    """Cierra viewers viejos de forma segura usando deleteLater()."""
    closed_count = 0

    for viewer_info in old_viewers:
        obj_name = viewer_info.get('object_name', '')
        widget = viewer_info.get('widget')

        # Filtrar Contact Sheet - no es viewer de secuencia
        if 'contactsheet' in obj_name.lower():
            debug_print(f"⚠️  Saltando Contact Sheet: {obj_name}")
            continue

        # Usar deleteLater() en lugar de close()
        try:
            widget.deleteLater()
            closed_count += 1
            debug_print(f"✅ Cerrado (deleteLater): {obj_name}")
        except Exception as e:
            debug_print(f"❌ Error cerrando {obj_name}: {e}")

    return closed_count

def format_viewer_display_name(viewer_info):
    """Formatea el nombre para mostrar: objectName + windowTitle si es diferente."""
    obj_name = viewer_info.get('object_name', '')
    window_title = viewer_info.get('window_title', '')

    if window_title and window_title != obj_name and window_title.strip():
        return f"{obj_name} ({window_title})"
    else:
        return obj_name

def close_old_timelines_safe(old_timelines):
    """Cierra timelines viejos de forma segura."""
    closed_count = 0

    for timeline_info in old_timelines:
        obj_name = timeline_info.get('object_name', '')
        widget = timeline_info.get('widget')

        try:
            widget.deleteLater()
            closed_count += 1
            debug_print(f"✅ Timeline cerrado (deleteLater): {obj_name}")
        except Exception as e:
            debug_print(f"❌ Error cerrando timeline {obj_name}: {e}")

    return closed_count

def main():
    """Función principal: identificar y cerrar viewers/timelines viejos."""
    debug_print("🔒 CIERRE SEGURO DE VIEWERS VIEJOS")
    debug_print("   (Usando deleteLater() - método seguro)")
    debug_print("")

    try:
        # 1. ANALIZAR VIEWERS
        all_viewers, active_viewers, old_viewers = collect_and_analyze_viewers()

        # 2. ANALIZAR TIMELINES
        all_timelines, active_timelines, old_timelines = collect_and_analyze_timelines()

        # 3. MOSTRAR RESUMEN EJECUTIVO
        debug_print("=" * 80)
        debug_print("📋 RESUMEN EJECUTIVO")
        debug_print("=" * 80)

        # Viewer activo
        if active_viewers:
            active_display_name = format_viewer_display_name(active_viewers[0])
            debug_print(f"🎯 VIEWER ACTIVO: {active_display_name}")
        else:
            debug_print("❌ VIEWER ACTIVO: NO IDENTIFICADO")

        # Timeline activo
        if active_timelines:
            active_timeline_obj_name = active_timelines[0].get('object_name', 'Sin nombre')
            active_timeline_window_title = active_timelines[0].get('window_title', '')
            if active_timeline_window_title and active_timeline_window_title != active_timeline_obj_name:
                active_timeline_display_name = f"{active_timeline_obj_name} ({active_timeline_window_title})"
            else:
                active_timeline_display_name = active_timeline_obj_name
            debug_print(f"🎯 TIMELINE ACTIVO: {active_timeline_display_name}")
        else:
            debug_print("❌ TIMELINE ACTIVO: NO IDENTIFICADO")

        # Viewers a cerrar
        if old_viewers:
            old_viewer_names = []
            contact_sheet_skipped = []

            for v in old_viewers:
                obj_name = v.get('object_name', '')

                # Filtrar Contact Sheet
                if 'contactsheet' in obj_name.lower():
                    contact_sheet_skipped.append(obj_name)
                    continue

                display_name = format_viewer_display_name(v)
                old_viewer_names.append(display_name)

            # Mostrar viewers a cerrar
            if old_viewer_names:
                debug_print(f"📍 VIEWERS A CERRAR: {', '.join(old_viewer_names)}")
            else:
                debug_print("✅ NO HAY VIEWERS PARA CERRAR")

            # Mostrar Contact Sheet skipped
            if contact_sheet_skipped:
                for cs_name in contact_sheet_skipped:
                    debug_print(f"⚠️ SALTAR Contact Sheet: {cs_name}")

        else:
            debug_print("✅ NO HAY VIEWERS PARA CERRAR")

        # Timelines a cerrar
        if old_timelines:
            old_timeline_names = []
            for t in old_timelines:
                obj_name = t.get('object_name', '')
                window_title = t.get('window_title', '')

                if window_title and window_title != obj_name:
                    display_name = f"{obj_name} ({window_title})"
                else:
                    display_name = obj_name

                old_timeline_names.append(display_name)

            if old_timeline_names:
                debug_print(f"📍 TIMELINES A CERRAR: {', '.join(old_timeline_names)}")
            else:
                debug_print("✅ NO HAY TIMELINES PARA CERRAR")
        else:
            debug_print("✅ NO HAY TIMELINES PARA CERRAR")

        debug_print("")

        # 4. PROCEDER CON EL CIERRE SEGURO
        debug_print("🔒 PROCEDIENTO DE CIERRE SEGURO...")
        debug_print("   (Usando deleteLater() - diferido y seguro)")
        debug_print("")

        # VIEWERS DESACTIVADOS - SOLO TIMELINES CON FILTRO ESPECIAL
        debug_print("⚠️  CIERRE DE VIEWERS DESACTIVADO - SOLO TIMELINES")
        debug_print("   (Filtrando timelines que comparten nombre con viewer activo)")

        # Cerrar timelines viejos (con filtro especial)
        if old_timelines:
            # Filtro especial: NO cerrar timelines que tengan el mismo nombre que el viewer activo
            active_viewer_name = ""
            if active_viewers:
                active_display_name = format_viewer_display_name(active_viewers[0])
                debug_print(f"🔍 DEBUG FILTRO: active_display_name = '{active_display_name}'")
                # Extraer solo el nombre de secuencia (sin objectName)
                if " (" in active_display_name:
                    active_viewer_name = active_display_name.split(" (")[1].rstrip(")")
                debug_print(f"🔍 DEBUG FILTRO: active_viewer_name extraído = '{active_viewer_name}'")

            debug_print(f"🔍 DEBUG FILTRO: Procesando {len(old_timelines)} timelines viejos")

            filtered_old_timelines = []
            for timeline_info in old_timelines:
                timeline_window_title = timeline_info.get('window_title', '')
                timeline_obj_name = timeline_info.get('object_name', '')
                debug_print(f"🔍 DEBUG FILTRO: Timeline {timeline_obj_name} tiene window_title = '{timeline_window_title}'")

                # NO cerrar timelines que tengan el mismo nombre que el viewer activo
                # Usar window_title que contiene el nombre de la secuencia
                if timeline_window_title != active_viewer_name:
                    debug_print(f"✅ DEBUG FILTRO: Timeline {timeline_obj_name} PASA filtro (diferente window_title)")
                    filtered_old_timelines.append(timeline_info)
                else:
                    debug_print(f"⚠️  DEBUG FILTRO: SALTANDO timeline {timeline_obj_name} (mismo window_title que viewer activo: {timeline_window_title})")

            debug_print(f"🔍 DEBUG FILTRO: De {len(old_timelines)} timelines, {len(filtered_old_timelines)} pasan el filtro")

            if filtered_old_timelines:
                timelines_closed = close_old_timelines_safe(filtered_old_timelines)
                debug_print(f"✅ Timelines cerrados (filtrados): {timelines_closed}")
            else:
                debug_print("✅ No hay timelines para cerrar (todos filtrados)")
        else:
            debug_print("✅ No hay timelines para cerrar")

        debug_print("")
        debug_print("=" * 80)
        debug_print("✅ CIERRE SEGURO COMPLETADO")
        debug_print("   (deleteLater() es diferido - cierre sucederá pronto)")
        debug_print("=" * 80)

        return True

    except Exception as e:
        debug_print(f"❌ ERROR en cierre seguro: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()
