# =============================================================================
# EXPLORACIÓN DE SECUENCIAS Y SUS TIMELINES/VIEWERS ABIERTOS (VERSION SEGURA)
# =============================================================================
# OBJETIVO: Explorar todas las secuencias del proyecto y determinar cuáles tienen
# timeline/viewer abierto vs cuáles están libres (disponibles para crear sin duplicar).
# ESTRATEGIA: Iterar por todas las secuencias del proyecto y verificar su estado.
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

def explore_sequences_and_open_panels():
    """Explora todas las secuencias del proyecto y verifica cuáles tienen timeline/viewer abierto"""

    debug_print("=" * 100)
    debug_print("EXPLORACIÓN: SECUENCIAS DEL PROYECTO Y SUS PANELS ABIERTOS")
    debug_print("=" * 100)

    try:
        # Obtener todas las secuencias del proyecto
        projects = hiero.core.projects()
        if not projects:
            debug_print("❌ No hay proyectos abiertos")
            return

        project = projects[0]
        all_sequences = project.sequences()

        debug_print(f"\n📋 TOTAL DE SECUENCIAS EN PROYECTO: {len(all_sequences)}")
        debug_print("-" * 80)

        sequences_with_panels = []
        sequences_free = []

        # PRIMERO: Obtener TODOS los viewers y timelines abiertos usando la lógica correcta
        all_open_viewers = []
        all_open_timelines = []

        # Usar la misma lógica que timelines_UI_activos.py para obtener timelines realmente abiertos en UI
        def find_timelines_in_main_windows():
            """Buscar timelines abiertos en la UI de Hiero (mismo método que timelines_UI_activos.py)"""
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
                        if (
                            hasattr(widget, "windowTitle")
                            and widget.windowTitle()
                            and hasattr(widget, "isWindow")
                            and widget.isWindow()
                        ):
                            main_windows.append(widget)
                    except:
                        pass

                timelines_in_windows = []
                for win in main_windows:
                    try:
                        win_title = win.windowTitle()

                        # Buscar TimelineEditor dentro de esta window
                        timeline_editors = win.findChildren(QtWidgets.QWidget)
                        local_timelines = []

                        for child in timeline_editors:
                            try:
                                class_name = (
                                    child.metaObject().className()
                                    if hasattr(child, "metaObject")
                                    else ""
                                )
                                if "TimelineEditor" in class_name:
                                    obj_name = (
                                        child.objectName()
                                        if hasattr(child, "objectName")
                                        else ""
                                    )
                                    child_title = (
                                        child.windowTitle()
                                        if hasattr(child, "windowTitle")
                                        else ""
                                    )

                                    if obj_name and obj_name.strip():
                                        local_timelines.append(
                                            {
                                                "window_title": win_title,
                                                "timeline_obj": obj_name,
                                                "timeline_title": child_title,
                                                "widget": child,  # guardar el widget para poder obtener la secuencia real
                                                "is_visible": (
                                                    child.isVisible()
                                                    if hasattr(child, "isVisible")
                                                    else False
                                                ),
                                            }
                                        )
                            except:
                                pass

                        if local_timelines:
                            timelines_in_windows.extend(local_timelines)

                    except Exception as e:
                        debug_print(f"   ❌ Error analizando window: {e}")

                return timelines_in_windows

            except Exception as e:
                debug_print(f"❌ Error en búsqueda de timelines: {e}")
                return []

        # Mapa auxiliar: objectName de timeline -> info de secuencia (usando la lógica antigua que sí devolvía el nombre)
        timeline_seq_lookup = {}
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
                            if obj_name and obj_name.strip():
                                seq_name = "Sin secuencia"
                                timeline_sequence = None

                                # MÉTODO 1: usar widget.sequence() (como en la versión previa)
                                try:
                                    if hasattr(widget, 'sequence') and widget.sequence():
                                        seq = widget.sequence()
                                        timeline_sequence = seq
                                        seq_name = seq.name() if hasattr(seq, 'name') else "Sin nombre"
                                except:
                                    pass

                                # MÉTODO 2: inferir de windowTitle
                                if seq_name == "Sin secuencia":
                                    try:
                                        title = window_title if window_title else ""
                                        projects = hiero.core.projects()
                                        if projects:
                                            project = projects[0]
                                            for seq in project.sequences():
                                                seq_name_in_title = seq.name()
                                                if seq_name_in_title in title:
                                                    seq_name = seq_name_in_title
                                                    timeline_sequence = seq
                                                    break
                                    except:
                                        pass

                                timeline_seq_lookup[obj_name] = {
                                    'seq_name': seq_name,
                                    'sequence': timeline_sequence,
                                    'window_title': window_title,
                                    'widget': widget,
                                }
                    except Exception:
                        continue
        except Exception as e:
            debug_print(f"❌ Error construyendo lookup de timelines: {e}")

        # Obtener viewers (mantener lógica existente por ahora)
        try:
            from LGA_QtAdapter_HieroTools import QtWidgets
            app = QtWidgets.QApplication.instance()
            if app:
                all_widgets = app.allWidgets()
                for widget in all_widgets:
                    try:
                        class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""

                        # Buscar viewers
                        if "Foundry::Storm::UI::Viewer" in class_name:
                            obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                            window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                            # Intentar obtener sequence name (MÉTODO ALTERNATIVO)
                            seq_name = "Sin secuencia"
                            viewer_sequence = None

                            # MÉTODO 1: Intentar usar player.sequence() (como antes)
                            try:
                                if hasattr(widget, 'player') and widget.player():
                                    player = widget.player()
                                    if hasattr(player, 'sequence') and player.sequence():
                                        seq = player.sequence()
                                        viewer_sequence = seq
                                        seq_name = seq.name() if hasattr(seq, 'name') else "Sin nombre"
                            except:
                                pass

                            # MÉTODO 2: Si no funcionó, intentar inferir de windowTitle
                            if seq_name == "Sin secuencia":
                                try:
                                    title = window_title if window_title else ""
                                    # Buscar nombres de secuencia conocidos en el título
                                    projects = hiero.core.projects()
                                    if projects:
                                        project = projects[0]
                                        for seq in project.sequences():
                                            seq_name_in_title = seq.name()
                                            if seq_name_in_title in title:
                                                seq_name = seq_name_in_title
                                                viewer_sequence = seq
                                                break
                                except:
                                    pass

                            # Solo incluir viewers con objectName válido (como en close_old_viewers_safe.py)
                            if obj_name and obj_name.strip():
                                all_open_viewers.append({
                                    'widget': widget,
                                    'object_name': obj_name,
                                    'window_title': window_title,
                                    'sequence_name': seq_name,
                                    'sequence': viewer_sequence,
                                    'viewer_id': hex(id(widget))
                                })

                    except Exception:
                        continue
        except Exception as e:
            debug_print(f"❌ Error obteniendo viewers: {e}")

        # Obtener timelines usando el método correcto
        all_open_timelines_data = find_timelines_in_main_windows()

        # Convertir el formato para mantener compatibilidad con el resto del código
        all_open_timelines = []
        for timeline_data in all_open_timelines_data:
            widget = timeline_data.get('widget')
            seq_name = "Sin secuencia"
            timeline_sequence = None

            # MÉTODO 1: usar widget.sequence() si está disponible
            if widget:
                try:
                    if hasattr(widget, 'sequence') and widget.sequence():
                        seq = widget.sequence()
                        timeline_sequence = seq
                        seq_name = seq.name() if hasattr(seq, 'name') else "Sin nombre"
                except:
                    pass

            # MÉTODO 2: inferir del windowTitle si aún no se obtuvo
            if seq_name == "Sin secuencia":
                try:
                    window_title = timeline_data['window_title'] if timeline_data['window_title'] else ""
                    projects = hiero.core.projects()
                    if projects:
                        project = projects[0]
                        for seq in project.sequences():
                            seq_name_in_title = seq.name()
                            if seq_name_in_title in window_title:
                                seq_name = seq_name_in_title
                                timeline_sequence = seq
                                break
                except:
                    pass

            # MÉTODO 3: inferir por objectName si sigue sin encontrarse
            if seq_name == "Sin secuencia":
                try:
                    obj_name = timeline_data['timeline_obj']
                    projects = hiero.core.projects()
                    if projects:
                        project = projects[0]
                        for seq in project.sequences():
                            seq_name_in_obj = seq.name()
                            if seq_name_in_obj in obj_name:
                                seq_name = seq_name_in_obj
                                timeline_sequence = seq
                                break
                except:
                    pass

            # MÉTODO 4: usar el lookup previo por objectName (que sí traía el nombre)
            if seq_name == "Sin secuencia":
                try:
                    obj_name = timeline_data['timeline_obj']
                    lookup = timeline_seq_lookup.get(obj_name)
                    if lookup:
                        seq_name = lookup['seq_name']
                        timeline_sequence = lookup['sequence']
                        # Si no tenemos widget porque vino de otra ventana, usar el del lookup para el id
                        if not widget:
                            widget = lookup.get('widget')
                except:
                    pass

            all_open_timelines.append({
                'object_name': timeline_data['timeline_obj'],
                'window_title': timeline_data['window_title'],
                'sequence_name': seq_name,
                'sequence': timeline_sequence,
                'timeline_id': hex(id(widget)) if widget else f"timeline_{len(all_open_timelines)}",
                'is_visible': timeline_data['is_visible']
            })

        debug_print(f"\n🔍 VIEWERS REALMENTE ABIERTOS EN LA UI: {len(all_open_viewers)}")
        for viewer in all_open_viewers:
            debug_print(f"  • {viewer['object_name']} → Secuencia: {viewer['sequence_name']}")

        debug_print(f"\n🔍 TIMELINES REALMENTE ABIERTOS EN LA UI: {len(all_open_timelines)}")
        for timeline in all_open_timelines:
            visibility_status = " (EN FOCO)" if timeline.get('is_visible', False) else " (visible)"
            debug_print(f"  • {timeline['object_name']} → Secuencia: {timeline['sequence_name']}{visibility_status}")

        # Verificar cada secuencia del proyecto
        for seq in all_sequences:
            seq_name = seq.name()
            seq_id = hex(id(seq))

            debug_print(f"\n🔍 VERIFICANDO SECUENCIA: {seq_name} (ID: {seq_id})")

            has_timeline = False
            has_viewer = False
            timeline_info = None
            viewer_info = None

            # 1. Verificar timeline comparando con la lista de timelines realmente abiertos en UI
            for timeline in all_open_timelines:
                if timeline['sequence'] and timeline['sequence'].name() == seq.name():
                    has_timeline = True
                    timeline_info = {
                        'timeline_obj_name': timeline['object_name'],
                        'timeline_id': timeline['timeline_id'],
                        'is_visible': timeline.get('is_visible', False)
                    }
                    visibility_status = " (EN FOCO)" if timeline.get('is_visible', False) else " (abierto)"
                    debug_print(f"  ✅ TIENE TIMELINE ABIERTO EN UI: {timeline['object_name']}{visibility_status}")
                    break

            if not has_timeline:
                debug_print("  ❌ NO TIENE TIMELINE ABIERTO EN UI")

            # 2. Verificar viewer comparando con la lista de viewers encontrados
            for viewer in all_open_viewers:
                if viewer['sequence'] and viewer['sequence'].name() == seq.name():
                    has_viewer = True
                    viewer_info = {
                        'viewer_obj_name': viewer['object_name'],
                        'viewer_id': viewer['viewer_id']
                    }
                    debug_print(f"  ✅ TIENE VIEWER ABIERTO: {viewer['object_name']} (ID: {viewer['viewer_id']})")
                    break

            if not has_viewer:
                debug_print("  ❌ NO TIENE VIEWER ABIERTO")

            # Clasificar la secuencia
            if has_timeline or has_viewer:
                panel_info = {
                    'sequence': seq,
                    'sequence_name': seq_name,
                    'sequence_id': seq_id,
                    'has_timeline': has_timeline,
                    'has_viewer': has_viewer,
                    'timeline_info': timeline_info,
                    'viewer_info': viewer_info
                }
                sequences_with_panels.append(panel_info)
            else:
                sequences_free.append({
                    'sequence': seq,
                    'sequence_name': seq_name,
                    'sequence_id': seq_id
                })

        # RESUMEN FINAL
        debug_print(f"\n{'='*100}")
        debug_print("RESUMEN FINAL - ESTADO ACTUAL DE PANELS")
        debug_print("=" * 100)

        debug_print(f"\n📊 ESTADÍSTICAS:")
        debug_print(f"   • Total secuencias en proyecto: {len(all_sequences)}")
        debug_print(f"   • Timelines realmente abiertos en UI: {len(all_open_timelines)}")
        debug_print(f"   • Viewers realmente abiertos en UI: {len(all_open_viewers)}")
        debug_print(f"   • Secuencias con timelines abiertos en UI: {len([s for s in sequences_with_panels if s['has_timeline']])}")
        debug_print(f"   • Secuencias con viewers abiertos: {len([s for s in sequences_with_panels if s['has_viewer']])}")
        debug_print(f"   • Secuencias completamente libres (sin panels): {len(sequences_free)}")

        # Identificar timeline activo/en foco usando la nueva lógica
        active_timeline_info = None
        try:
            # Buscar el timeline que está marcado como visible (is_visible=True)
            for timeline in all_open_timelines:
                if timeline.get('is_visible', False):
                    active_timeline_info = {
                        'sequence_name': timeline['sequence_name'],
                        'timeline_object_name': timeline['object_name'],
                        'timeline_window_title': timeline['window_title']
                    }
                    break
        except:
            pass

        debug_print(f"\n🎯 TIMELINE ACTIVO/EN FOCO: {active_timeline_info['sequence_name'] + ' (' + active_timeline_info['timeline_object_name'] + ')' if active_timeline_info else 'Ninguno'}")

        debug_print(f"\n🟢 SECUENCIAS SIN PANELS ABIERTOS (completamente libres):")
        if sequences_free:
            for i, seq_info in enumerate(sequences_free):
                debug_print(f"   {i+1}. {seq_info['sequence_name']} (ID: {seq_info['sequence_id']})")
        else:
            debug_print("   ❌ No hay secuencias libres")

        debug_print(f"\n🔴 SECUENCIAS CON PANELS ABIERTOS EN UI:")
        if sequences_with_panels:
            for i, seq_info in enumerate(sequences_with_panels):
                seq_name = seq_info['sequence_name']
                status_parts = []
                if seq_info['has_timeline']:
                    timeline_obj = seq_info['timeline_info']['timeline_obj_name']
                    is_active = seq_info['timeline_info'].get('is_visible', False)
                    status_parts.append(f"Timeline: {timeline_obj}{' (EN FOCO)' if is_active else ' (abierto)'}")
                if seq_info['has_viewer']:
                    viewer_obj = seq_info['viewer_info']['viewer_obj_name']
                    status_parts.append(f"Viewer: {viewer_obj}")
                status = " + ".join(status_parts)
                debug_print(f"   {i+1}. {seq_name} → {status}")
        else:
            debug_print("   ✅ Todas las secuencias están libres")

    except Exception as e:
        debug_print(f"❌ Error en exploración: {e}")
        import traceback
        debug_print(traceback.format_exc())

# =============================================================================
# EJECUCIÓN SENCILLA Y SEGURA
# =============================================================================

debug_print("🔍 EJECUTANDO EXPLORACIÓN SEGURA...")
debug_print("="*100)

# Solo ejecutar la función principal para evitar crashes
try:
    explore_sequences_and_open_panels()
    debug_print("\n✅ EXPLORACIÓN COMPLETADA EXITOSAMENTE")
except Exception as e:
    debug_print(f"\n❌ ERROR EN EXPLORACIÓN: {e}")
    import traceback
    debug_print(traceback.format_exc())

debug_print("\n" + "="*100)
debug_print("🎯 SECUENCIAS COMPLETAMENTE LIBRES:")
debug_print("Estas secuencias no tienen timeline ni viewer abierto en la UI")
debug_print("Puedes usarlas para crear nuevos panels sin conflictos")
debug_print("="*100)
