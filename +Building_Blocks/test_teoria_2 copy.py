# =============================================================================
# TEST TEORÍA 2: CREAR TIMELINE/VIEWER PARA UNA SECUENCIA LIBRE Y RELOGGEAR
# =============================================================================
# OBJETIVO:
# - Reutilizar la exploración segura para listar timelines/viewers abiertos.
# - Elegir una secuencia libre (sin timeline ni viewer) y abrirla con
#   hiero.ui.openInTimeline(), creando un timeline y viewer nuevos.
# - Volver a loggear el estado final para comparar antes vs después.
# =============================================================================

import hiero.core
import hiero.ui
import traceback
import os
import logging

try:
    from LGA_QtAdapter_HieroTools import QtCore  # para processEvents/flush UI
except Exception:
    QtCore = None

DEBUG = True


def setup_debug_logging():
    """Configura el logging para debug que escribe en tiempo real a debugPy.log."""
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "debugPy.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    logger = logging.getLogger("debug_logger_test_teoria_2")
    logger.setLevel(logging.DEBUG)

    # Limpiar handlers para evitar duplicados si se reimporta
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def clear_debug_log():
    """Limpia el archivo de log al iniciar cada ejecución."""
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "debugPy.log")
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Warning: No se pudo limpiar el archivo de log: {e}")


debug_logger = setup_debug_logging()


def debug_print(*message):
    if DEBUG:
        msg = " ".join(str(arg) for arg in message)
        print(msg)
        try:
            debug_logger.info(msg)
        except Exception:
            pass


def flush_logs():
    """Fuerza el flush de los handlers de logging para no perder trazas antes de un posible crash."""
    try:
        for handler in debug_logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass
    except Exception:
        pass


def _process_events(label=""):
    """ProcessEvents similar a Projects Panel para evitar cuelgues en openInTimeline."""
    if not QtCore:
        return
    try:
        for _ in range(3):
            QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents, 50
            ) if hasattr(QtCore, "QEventLoop") else QtCore.QCoreApplication.processEvents()
        if label:
            debug_print(f"🌀 processEvents() completado: {label}")
    except Exception as e:
        debug_print(f"⚠️ processEvents() falló ({label}): {e}")


def safe_window_property(window, property_name, default="N/A"):
    """Obtiene una propiedad del window de manera segura."""
    if not window:
        return default
    try:
        if hasattr(window, property_name):
            method = getattr(window, property_name)
            if callable(method):
                return method()
    except Exception:
        pass
    return default


def explore_sequences_and_open_panels():
    """
    Exploración completa (misma que explorar_seqs_timelines_viewers_del_proyecto.py)
    Devuelve diccionario con listas para reutilizar en la prueba.
    """

    debug_print("=" * 100)
    debug_print("EXPLORACIÓN: SECUENCIAS DEL PROYECTO Y SUS PANELS ABIERTOS")
    debug_print("=" * 100)

    try:
        # Obtener todas las secuencias del proyecto
        projects = hiero.core.projects()
        if not projects:
            debug_print("❌ No hay proyectos abiertos")
            return {}

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
                    except Exception:
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
                            except Exception:
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
                        class_name = (
                            widget.metaObject().className()
                            if hasattr(widget, "metaObject")
                            else ""
                        )
                        if "TimelineEditor" in class_name:
                            obj_name = (
                                widget.objectName()
                                if hasattr(widget, "objectName")
                                else ""
                            )
                            window_title = (
                                widget.windowTitle()
                                if hasattr(widget, "windowTitle")
                                else ""
                            )
                            if obj_name and obj_name.strip():
                                seq_name = "Sin secuencia"
                                timeline_sequence = None

                                # MÉTODO 1: usar widget.sequence() (como en la versión previa)
                                try:
                                    if hasattr(widget, "sequence") and widget.sequence():
                                        seq = widget.sequence()
                                        timeline_sequence = seq
                                        seq_name = (
                                            seq.name()
                                            if hasattr(seq, "name")
                                            else "Sin nombre"
                                        )
                                except Exception:
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
                                    except Exception:
                                        pass

                                timeline_seq_lookup[obj_name] = {
                                    "seq_name": seq_name,
                                    "sequence": timeline_sequence,
                                    "window_title": window_title,
                                    "widget": widget,
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
                        class_name = (
                            widget.metaObject().className()
                            if hasattr(widget, "metaObject")
                            else ""
                        )

                        # Buscar viewers
                        if "Foundry::Storm::UI::Viewer" in class_name:
                            obj_name = (
                                widget.objectName()
                                if hasattr(widget, "objectName")
                                else ""
                            )
                            window_title = (
                                widget.windowTitle()
                                if hasattr(widget, "windowTitle")
                                else ""
                            )

                            # Intentar obtener sequence name (MÉTODO ALTERNATIVO)
                            seq_name = "Sin secuencia"
                            viewer_sequence = None

                            # MÉTODO 1: Intentar usar player.sequence() (como antes)
                            try:
                                if hasattr(widget, "player") and widget.player():
                                    player = widget.player()
                                    if hasattr(player, "sequence") and player.sequence():
                                        seq = player.sequence()
                                        viewer_sequence = seq
                                        seq_name = (
                                            seq.name()
                                            if hasattr(seq, "name")
                                            else "Sin nombre"
                                        )
                            except Exception:
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
                                except Exception:
                                    pass

                            # Solo incluir viewers con objectName válido (como en close_old_viewers_safe.py)
                            if obj_name and obj_name.strip():
                                all_open_viewers.append(
                                    {
                                        "widget": widget,
                                        "object_name": obj_name,
                                        "window_title": window_title,
                                        "sequence_name": seq_name,
                                        "sequence": viewer_sequence,
                                        "viewer_id": hex(id(widget)),
                                    }
                                )

                    except Exception:
                        continue
        except Exception as e:
            debug_print(f"❌ Error obteniendo viewers: {e}")

        # Obtener timelines usando el método correcto
        all_open_timelines_data = find_timelines_in_main_windows()

        # Convertir el formato para mantener compatibilidad con el resto del código
        all_open_timelines = []
        for timeline_data in all_open_timelines_data:
            widget = timeline_data.get("widget")
            seq_name = "Sin secuencia"
            timeline_sequence = None

            # MÉTODO 1: usar widget.sequence() si está disponible
            if widget:
                try:
                    if hasattr(widget, "sequence") and widget.sequence():
                        seq = widget.sequence()
                        timeline_sequence = seq
                        seq_name = seq.name() if hasattr(seq, "name") else "Sin nombre"
                except Exception:
                    pass

            # MÉTODO 2: inferir del windowTitle si aún no se obtuvo
            if seq_name == "Sin secuencia":
                try:
                    window_title = (
                        timeline_data["window_title"]
                        if timeline_data["window_title"]
                        else ""
                    )
                    projects = hiero.core.projects()
                    if projects:
                        project = projects[0]
                        for seq in project.sequences():
                            seq_name_in_title = seq.name()
                            if seq_name_in_title in window_title:
                                seq_name = seq_name_in_title
                                timeline_sequence = seq
                                break
                except Exception:
                    pass

            # MÉTODO 3: inferir por objectName si sigue sin encontrarse
            if seq_name == "Sin secuencia":
                try:
                    obj_name = timeline_data["timeline_obj"]
                    projects = hiero.core.projects()
                    if projects:
                        project = projects[0]
                        for seq in project.sequences():
                            seq_name_in_obj = seq.name()
                            if seq_name_in_obj in obj_name:
                                seq_name = seq_name_in_obj
                                timeline_sequence = seq
                                break
                except Exception:
                    pass

            # MÉTODO 4: usar el lookup previo por objectName (que sí traía el nombre)
            if seq_name == "Sin secuencia":
                try:
                    obj_name = timeline_data["timeline_obj"]
                    lookup = timeline_seq_lookup.get(obj_name)
                    if lookup:
                        seq_name = lookup["seq_name"]
                        timeline_sequence = lookup["sequence"]
                        # Si no tenemos widget porque vino de otra ventana, usar el del lookup para el id
                        if not widget:
                            widget = lookup.get("widget")
                except Exception:
                    pass

            all_open_timelines.append(
                {
                    "object_name": timeline_data["timeline_obj"],
                    "window_title": timeline_data["window_title"],
                    "sequence_name": seq_name,
                    "sequence": timeline_sequence,
                    "timeline_id": hex(id(widget))
                    if widget
                    else f"timeline_{len(all_open_timelines)}",
                    "is_visible": timeline_data["is_visible"],
                }
            )

        debug_print(f"\n🔍 VIEWERS REALMENTE ABIERTOS EN LA UI: {len(all_open_viewers)}")
        for viewer in all_open_viewers:
            debug_print(f"  • {viewer['object_name']} → Secuencia: {viewer['sequence_name']}")

        debug_print(f"\n🔍 TIMELINES REALMENTE ABIERTOS EN LA UI: {len(all_open_timelines)}")
        for timeline in all_open_timelines:
            visibility_status = " (EN FOCO)" if timeline.get("is_visible", False) else " (visible)"
            debug_print(
                f"  • {timeline['object_name']} → Secuencia: {timeline['sequence_name']}{visibility_status}"
            )

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
                if timeline["sequence"] and timeline["sequence"].name() == seq.name():
                    has_timeline = True
                    timeline_info = {
                        "timeline_obj_name": timeline["object_name"],
                        "timeline_id": timeline["timeline_id"],
                        "is_visible": timeline.get("is_visible", False),
                    }
                    visibility_status = (
                        " (EN FOCO)" if timeline.get("is_visible", False) else " (abierto)"
                    )
                    debug_print(
                        f"  ✅ TIENE TIMELINE ABIERTO EN UI: {timeline['object_name']}{visibility_status}"
                    )
                    break

            if not has_timeline:
                debug_print("  ❌ NO TIENE TIMELINE ABIERTO EN UI")

            # 2. Verificar viewer comparando con la lista de viewers encontrados
            for viewer in all_open_viewers:
                if viewer["sequence"] and viewer["sequence"].name() == seq.name():
                    has_viewer = True
                    viewer_info = {
                        "viewer_obj_name": viewer["object_name"],
                        "viewer_id": viewer["viewer_id"],
                    }
                    debug_print(
                        f"  ✅ TIENE VIEWER ABIERTO: {viewer['object_name']} (ID: {viewer['viewer_id']})"
                    )
                    break

            if not has_viewer:
                debug_print("  ❌ NO TIENE VIEWER ABIERTO")

            # Clasificar la secuencia
            if has_timeline or has_viewer:
                panel_info = {
                    "sequence": seq,
                    "sequence_name": seq_name,
                    "sequence_id": seq_id,
                    "has_timeline": has_timeline,
                    "has_viewer": has_viewer,
                    "timeline_info": timeline_info,
                    "viewer_info": viewer_info,
                }
                sequences_with_panels.append(panel_info)
            else:
                sequences_free.append(
                    {
                        "sequence": seq,
                        "sequence_name": seq_name,
                        "sequence_id": seq_id,
                    }
                )

        # RESUMEN FINAL
        debug_print(f"\n{'='*100}")
        debug_print("RESUMEN FINAL - ESTADO ACTUAL DE PANELS")
        debug_print("=" * 100)

        debug_print(f"\n📊 ESTADÍSTICAS:")
        debug_print(f"   • Total secuencias en proyecto: {len(all_sequences)}")
        debug_print(f"   • Timelines realmente abiertos en UI: {len(all_open_timelines)}")
        debug_print(f"   • Viewers realmente abiertos en UI: {len(all_open_viewers)}")
        debug_print(
            f"   • Secuencias con timelines abiertos en UI: {len([s for s in sequences_with_panels if s['has_timeline']])}"
        )
        debug_print(
            f"   • Secuencias con viewers abiertos: {len([s for s in sequences_with_panels if s['has_viewer']])}"
        )
        debug_print(
            f"   • Secuencias completamente libres (sin panels): {len(sequences_free)}"
        )

        # Identificar timeline activo/en foco usando la nueva lógica
        active_timeline_info = None
        try:
            # Buscar el timeline que está marcado como visible (is_visible=True)
            for timeline in all_open_timelines:
                if timeline.get("is_visible", False):
                    active_timeline_info = {
                        "sequence_name": timeline["sequence_name"],
                        "timeline_object_name": timeline["object_name"],
                        "timeline_window_title": timeline["window_title"],
                    }
                    break
        except Exception:
            pass

        debug_print(
            f"\n🎯 TIMELINE ACTIVO/EN FOCO: {active_timeline_info['sequence_name'] + ' (' + active_timeline_info['timeline_object_name'] + ')' if active_timeline_info else 'Ninguno'}"
        )

        debug_print(f"\n🟢 SECUENCIAS SIN PANELS ABIERTOS (completamente libres):")
        if sequences_free:
            for i, seq_info in enumerate(sequences_free):
                debug_print(
                    f"   {i+1}. {seq_info['sequence_name']} (ID: {seq_info['sequence_id']})"
                )
        else:
            debug_print("   ❌ No hay secuencias libres")

        debug_print(f"\n🔴 SECUENCIAS CON PANELS ABIERTOS EN UI:")
        if sequences_with_panels:
            for i, seq_info in enumerate(sequences_with_panels):
                seq_name = seq_info["sequence_name"]
                status_parts = []
                if seq_info["has_timeline"]:
                    timeline_obj = seq_info["timeline_info"]["timeline_obj_name"]
                    is_active = seq_info["timeline_info"].get("is_visible", False)
                    status_parts.append(
                        f"Timeline: {timeline_obj}{' (EN FOCO)' if is_active else ' (abierto)'}"
                    )
                if seq_info["has_viewer"]:
                    viewer_obj = seq_info["viewer_info"]["viewer_obj_name"]
                    status_parts.append(f"Viewer: {viewer_obj}")
                status = " + ".join(status_parts)
                debug_print(f"   {i+1}. {seq_name} → {status}")
        else:
            debug_print("   ✅ Todas las secuencias están libres")

        debug_print("\n✅ EXPLORACIÓN COMPLETADA EXITOSAMENTE")
        debug_print("\n" + "=" * 100)
        debug_print("🎯 SECUENCIAS COMPLETAMENTE LIBRES:")
        debug_print("Estas secuencias no tienen timeline ni viewer abierto en la UI")
        debug_print("Puedes usarlas para crear nuevos panels sin conflictos")
        debug_print("=" * 100)

        return {
            "all_sequences": all_sequences,
            "all_open_viewers": all_open_viewers,
            "all_open_timelines": all_open_timelines,
            "sequences_with_panels": sequences_with_panels,
            "sequences_free": sequences_free,
            "active_timeline_info": active_timeline_info,
        }

    except Exception as e:
        debug_print(f"❌ Error en exploración: {e}")
        debug_print(traceback.format_exc())
        return {}


def crear_timeline_y_viewer_para_libre(estado_inicial):
    """Crea timeline/viewer para secuencia usando MÉTODO DEL PANEL (simplificado)."""
    sequences_free = estado_inicial.get("sequences_free", [])
    sequences_with_panels = estado_inicial.get("sequences_with_panels", [])

    # Verificar que haya secuencias para trabajar
    if not sequences_free and not sequences_with_panels:
        debug_print("❌ No hay secuencias disponibles para probar.")
        return None

    # SOLUCIÓN: Usar el método del REFRESH TIMELINE (recrear existente)
    debug_print("🎯 SOLUCIÓN: Usando método del REFRESH TIMELINE - recrear secuencia existente")

    # El refresh funciona porque recrea timelines para secuencias que YA TIENEN viewers
    # Vamos a hacer exactamente lo mismo: elegir una secuencia que tenga viewer abierto
    # y recrear su timeline/viewer (como hace el refresh)

    secuencias_con_viewer = [s for s in sequences_with_panels if s.get("has_viewer", False)]

    if secuencias_con_viewer:
        # Elegir la secuencia activa (como hace el refresh) o una con viewer
        active_seq = hiero.ui.activeSequence()
        active_seq_name = active_seq.name() if active_seq else None

        # Preferir la secuencia activa si existe, sino cualquier otra con viewer
        target_info = None
        if active_seq_name:
            # Buscar la secuencia activa en las que tienen viewer
            target_info = next(
                (s for s in secuencias_con_viewer if s.get("sequence_name") == active_seq_name),
                None
            )

        if not target_info and secuencias_con_viewer:
            # Si no está la activa, tomar la primera con viewer
            target_info = secuencias_con_viewer[0]

        if target_info:
            debug_print(f"✅ Recreando timeline para secuencia existente: {target_info['sequence_name']}")
            debug_print("   (como hace el refresh timeline - debería funcionar)")
        else:
            debug_print("❌ No se encontró secuencia para recrear")
            return None
    else:
        debug_print("❌ No hay secuencias con viewer abierto para recrear")
        return None

    # TEORÍA CONFIRMADA: No podemos crear desde cero, pero podemos RECREAR existente
    debug_print("🔍 TEORÍA: Las secuencias 'libres' ya tienen asignaciones ocultas")
    debug_print("   → Por eso crashea crear desde cero")
    debug_print("   → Pero funciona recrear secuencias que ya existen")

    seq = target_info["sequence"]
    seq_name = target_info["sequence_name"]

    debug_print("\n" + "=" * 100)
    debug_print(f"🚀 CREANDO NUEVO TIMELINE/VIEWER PARA: {seq_name} (MÉTODO PANEL)")
    debug_print("=" * 100)

    # LOGS DETALLADOS: Comparar con Panel de Proyectos
    debug_print("🔍 ANÁLISIS PREVIO - ESTILO PANEL:")
    try:
        active_seq_before = hiero.ui.activeSequence()
        active_seq_name = active_seq_before.name() if active_seq_before else "Ninguna"
        debug_print(f"   ├── Secuencia activa antes: {active_seq_name}")

        current_viewer_before = hiero.ui.currentViewer()
        viewer_info_before = "Ninguno"
        if current_viewer_before:
            try:
                viewer_win = current_viewer_before.window()
                if viewer_win and hasattr(viewer_win, "objectName"):
                    viewer_info_before = viewer_win.objectName()
            except Exception:
                pass
        debug_print(f"   ├── currentViewer() antes: {viewer_info_before}")

        # Verificar proyectos (como hace el Panel)
        projects = hiero.core.projects()
        debug_print(f"   ├── Proyectos abiertos: {len(projects)}")
        if projects:
            debug_print(f"   ├── Proyecto activo: {projects[0].name()}")

            # Verificar si ya estamos en la secuencia (optimización del Panel)
            if active_seq_before and active_seq_before.name() == seq_name:
                debug_print("   ├── ⚠️ Ya estamos en la secuencia objetivo - no hay cambios")
                return {
                    "sequence_name": seq_name,
                    "timeline_obj": "Ya activo",
                    "timeline_window_title": "Ya activo",
                    "viewer_obj": viewer_info_before,
                    "viewer_seq_name": seq_name,
                }

    except Exception as e:
        debug_print(f"   ├── Error en análisis previo: {e}")

    debug_print("🔒 Preparación - flush logs y processEvents (estilo Panel)")
    flush_logs()
    try:
        _process_events("pre-openInTimeline-panel-style")
    except Exception as e:
        debug_print(f"   ├── Error en processEvents inicial: {e}")

    # 📋 MÉTODO DEL PANEL: UNA SOLA LLAMADA (como en switch_to_sequence_hybrid)
    debug_print("🎯 MÉTODO PANEL: UNA SOLA LLAMADA A openInTimeline()")
    debug_print("   ├── Capturando estado viewer actual (gain/gamma/saturation)")

    # 1. Capturar estado del viewer actual (como hace el Panel)
    viewer_state = None
    current_viewer = hiero.ui.currentViewer()
    if current_viewer:
        viewer_state = _get_viewer_state(current_viewer)
        debug_print(f"   ├── Estado viewer capturado: {viewer_state is not None}")

    # 2. UNA SOLA LLAMADA: openInTimeline (exactamente como el Panel)
    debug_print("   ├── Ejecutando hiero.ui.openInTimeline(seq) [UNA SOLA VEZ]")
    creation_error = None
    new_timeline = None

    try:
        # Verificar secuencia objetivo (como hace el Panel)
        target_seq = seq  # Ya tenemos la secuencia validada

        # Llamada directa - como el Panel
        new_timeline = hiero.ui.openInTimeline(target_seq)
        debug_print("   ✅ openInTimeline() ejecutado exitosamente (estilo Panel)")

        # Procesar eventos (como hace el Panel)
        _process_events("post-openInTimeline-panel-style")

        # Verificar que cambió correctamente (como hace el Panel)
        new_active = hiero.ui.activeSequence()
        if not (new_active and new_active.name() == seq_name):
            debug_print("   ⚠️ Secuencia no cambió correctamente")
        else:
            debug_print("   ✅ Secuencia cambió correctamente")

    except Exception as e:
        creation_error = e
        debug_print(f"❌ ERROR en openInTimeline() estilo Panel: {e}")
        debug_print(traceback.format_exc())
        return None

    if creation_error:
        return None

    # 3. Aplicar estado del viewer anterior (como hace el Panel)
    if viewer_state:
        debug_print("   ├── Aplicando estado viewer anterior (gain/gamma/saturation)")
        new_viewer = hiero.ui.currentViewer()
        if new_viewer:
            _apply_viewer_settings(new_viewer, viewer_state)
            debug_print("   ✅ Estado viewer aplicado")

    # 4. Enfocar viewer (como hace el Panel)
    debug_print("   ├── Enfocando viewer objetivo")
    _focus_target_viewer_panel_style(seq_name)

    # LOGS DETALLADOS: Resultado final
    debug_print("🔍 RESULTADO FINAL:")

    # Info del timeline creado
    timeline_obj = "N/A"
    timeline_window_title = "N/A"
    timeline_seq_name = "Desconocida"
    if new_timeline:
        try:
            tl_window = new_timeline.window() if hasattr(new_timeline, "window") else None
            if tl_window and hasattr(tl_window, "objectName"):
                timeline_obj = tl_window.objectName()
            if tl_window and hasattr(tl_window, "windowTitle"):
                timeline_window_title = tl_window.windowTitle()
            try:
                if hasattr(new_timeline, "sequence") and new_timeline.sequence():
                    timeline_seq = new_timeline.sequence()
                    timeline_seq_name = (
                        timeline_seq.name() if hasattr(timeline_seq, "name") else "Sin nombre"
                    )
            except Exception:
                pass
        except Exception:
            pass

    debug_print(f"   ├── Timeline creado: objectName={timeline_obj} | title={timeline_window_title} | seq={timeline_seq_name}")

    # Info del viewer creado
    new_viewer_final = hiero.ui.currentViewer()
    viewer_obj = "N/A"
    viewer_seq_name = "Sin secuencia"
    if new_viewer_final:
        try:
            viewer_window = new_viewer_final.window()
            if viewer_window and hasattr(viewer_window, "objectName"):
                viewer_obj = viewer_window.objectName()
            if hasattr(new_viewer_final, "player") and new_viewer_final.player():
                seq_player = new_viewer_final.player().sequence()
                if seq_player and hasattr(seq_player, "name"):
                    viewer_seq_name = seq_player.name()
        except Exception:
            pass

    debug_print(f"   ├── Viewer actual: objectName={viewer_obj} | sequence={viewer_seq_name}")

    debug_print("🔒 Finalización - flush logs y processEvents")
    flush_logs()
    try:
        _process_events("post-creation-panel-style")
    except Exception:
        pass

    debug_print("✅ CREACIÓN COMPLETADA CON MÉTODO PANEL")

    return {
        "sequence_name": seq_name,
        "timeline_obj": timeline_obj,
        "timeline_window_title": timeline_window_title,
        "viewer_obj": viewer_obj,
        "viewer_seq_name": viewer_seq_name,
    }


def _focus_target_viewer_panel_style(target_sequence_name):
    """Enfocar viewer estilo Panel (simplificado, sin limpieza agresiva)."""
    try:
        viewers = _collect_viewers()
        target = _pick_target_viewer(viewers, target_sequence_name)
        if not target:
            debug_print(f"   ├── No se encontró viewer para '{target_sequence_name}'")
            return
        widget = target["widget"]
        widget.show()
        widget.raise_()
        widget.activateWindow()
        _process_events("focus-viewer-panel-style")
        debug_print(f"   ├── Viewer enfocado: {target_sequence_name}")
    except Exception as e:
        debug_print(f"   ├── Error enfocando viewer: {e}")


def _get_viewer_state(viewer):
    """Captura estado del viewer (gain/gamma/saturation)."""
    if not viewer:
        return None
    try:
        return {
            "gain": viewer.gain(),
            "gamma": viewer.gamma(),
            "saturation": viewer.saturation(),
        }
    except Exception:
        return None


def _apply_viewer_settings(viewer, state):
    """Aplica ajustes del viewer (gain/gamma/saturation)."""
    if not viewer or not state:
        return
    try:
        if "gain" in state:
            viewer.setGain(state["gain"])
        if "gamma" in state:
            viewer.setGamma(state["gamma"])
        if "saturation" in state:
            viewer.setSaturation(state["saturation"])
    except Exception:
        pass


def _collect_viewers():
    """Devuelve lista de viewers Qt (Foundry::Storm::UI::Viewer) con título y visibilidad."""
    viewers = []
    try:
        from LGA_QtAdapter_HieroTools import QtWidgets

        all_widgets = QtWidgets.QApplication.instance().allWidgets()
        for widget in all_widgets:
            try:
                class_name = (
                    widget.metaObject().className()
                    if hasattr(widget, "metaObject")
                    else str(type(widget))
                )
                if "Foundry::Storm::UI::Viewer" in class_name:
                    title = (
                        widget.windowTitle() if hasattr(widget, "windowTitle") else ""
                    )
                    visible = (
                        widget.isVisible() if hasattr(widget, "isVisible") else False
                    )
                    viewers.append(
                        {"widget": widget, "title": title, "visible": visible}
                    )
            except Exception:
                continue
    except Exception:
        pass
    return viewers


def _pick_target_viewer(viewers, target_sequence_name):
    """Selecciona un viewer cuyo título coincida, priorizando los visibles."""
    visible_matches = [
        v for v in viewers if v.get("title") == target_sequence_name and v.get("visible")
    ]
    if visible_matches:
        return visible_matches[0]
    name_matches = [v for v in viewers if v.get("title") == target_sequence_name]
    if name_matches:
        return name_matches[0]
    return None


def main():
    global debug_logger
    clear_debug_log()
    debug_logger = setup_debug_logging()

    debug_print("🔍 TEST TEORÍA 2 - ESTADO INICIAL (creación siguiendo patrón Projects Panel)")
    debug_print("=" * 100)

    estado_inicial = explore_sequences_and_open_panels()
    sequences_free = estado_inicial.get("sequences_free", []) if estado_inicial else []

    if not sequences_free:
        debug_print("\n❌ No hay secuencias libres; no se puede ejecutar la prueba TEORÍA 2.")
        return

    debug_print("   Si crashea, revisa logs/debugPy.log para ver el último paso registrado.")
    flush_logs()

    # Crear timeline/viewer para una secuencia
    creacion_info = crear_timeline_y_viewer_para_libre(estado_inicial)
    if not creacion_info:
        debug_print("\n❌ No se pudo crear timeline/viewer (openInTimeline falló o fue abortado).")
        return

    debug_print("\n✅ CREACIÓN COMPLETADA. RELANZANDO EXPLORACIÓN PARA COMPARAR ESTADO FINAL...")
    debug_print("=" * 100)
    explore_sequences_and_open_panels()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        debug_print(f"\n❌ ERROR GENERAL EN TEST TEORÍA 2: {e}")
        debug_print(traceback.format_exc())

