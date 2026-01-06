# =============================================================================
# TEST TEORÍA 2: CREAR TIMELINE/VIEWER LIMPIO PARA SECUENCIA LIBRE
# =============================================================================
# 🎯 OBJETIVO PRINCIPAL:
#    Mostrar en la UI un timeline y viewer de una secuencia existente que
#    actualmente NO tiene timeline ni viewer visibles en la UI.
#
# 📋 ESTRATEGIA:
#    Probar diferentes "CAMINOS" para crear el timeline/viewer:
#    - CAMINO 1: openInTimeline() directo (como Projects Panel) ⭐ ACTUAL
#    - CAMINO 2: setActiveSequence() + openInTimeline()
#    - CAMINO 3: Solo openInNewViewer() (ventana flotante)
#    - Otros caminos según resultados...
#
# ✅ ÉXITO = Timeline y viewer aparecen en la UI sin crashes
# ❌ FALLO = Hiero crashea, o no aparecen en la UI, o aparecen duplicados
#
# 📊 COMPARACIÓN: Exploración ANTES vs DESPUÉS para verificar cambios
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
            (
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
                if hasattr(QtCore, "QEventLoop")
                else QtCore.QCoreApplication.processEvents()
            )
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
                                    if (
                                        hasattr(widget, "sequence")
                                        and widget.sequence()
                                    ):
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
                                    if (
                                        hasattr(player, "sequence")
                                        and player.sequence()
                                    ):
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
                    "timeline_id": (
                        hex(id(widget))
                        if widget
                        else f"timeline_{len(all_open_timelines)}"
                    ),
                    "is_visible": timeline_data["is_visible"],
                }
            )

        debug_print(
            f"\n🔍 VIEWERS REALMENTE ABIERTOS EN LA UI: {len(all_open_viewers)}"
        )
        for viewer in all_open_viewers:
            debug_print(
                f"  • {viewer['object_name']} → Secuencia: {viewer['sequence_name']}"
            )

        debug_print(
            f"\n🔍 TIMELINES REALMENTE ABIERTOS EN LA UI: {len(all_open_timelines)}"
        )
        for timeline in all_open_timelines:
            visibility_status = (
                " (EN FOCO)" if timeline.get("is_visible", False) else " (visible)"
            )
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
                        " (EN FOCO)"
                        if timeline.get("is_visible", False)
                        else " (abierto)"
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
        debug_print(
            f"   • Timelines realmente abiertos en UI: {len(all_open_timelines)}"
        )
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


def get_hiero_version():
    """Detecta la versión mayor de Hiero (15 o 16)."""
    try:
        version_tuple = hiero.core.applicationVersion()  # Returns (major, minor, patch)
        major_version = version_tuple[0]
        return major_version
    except Exception as e:
        debug_print(f"⚠️ Error detectando versión de Hiero: {e}")
        return None


def crear_timeline_y_viewer_para_libre(sequences_free, camino=2):
    """
    🎯 OBJETIVO: Mostrar en la UI un timeline y viewer de una secuencia que NO tiene ninguno abierto.
    
    CAMINOS DISPONIBLES:
    - CAMINO 1: openInTimeline() directo → ❌ CRASHEA EN H16, ✅ FUNCIONA EN H15
    - CAMINO 2: setActiveSequence() + openInTimeline() → 🔄 PROBANDO AHORA
    - CAMINO 3: Solo openInNewViewer() (ventana flotante) → ⏸️ Pendiente
    """
    if not sequences_free:
        debug_print("❌ No hay secuencias libres para probar TEORÍA 2.")
        return None

    # Preferir las dos secuencias indicadas; si no están, tomar la primera libre.
    preferidas = ["z_EditRef_v1_6_20250725", "z_EditRef_v.0.2"]
    target_info = None

    for nombre in preferidas:
        target_info = next(
            (s for s in sequences_free if s.get("sequence_name") == nombre), None
        )
        if target_info:
            break

    if not target_info:
        target_info = sequences_free[0]

    seq = target_info["sequence"]
    seq_name = target_info["sequence_name"]

    debug_print("\n" + "=" * 100)
    debug_print(f"🚀 CAMINO {camino}: Creando timeline/viewer para '{seq_name}'")
    debug_print("=" * 100)
    
    # Flush logs antes de la operación crítica
    flush_logs()

    new_timeline = None
    creation_error = None

    # ==========================================================================
    # CAMINO 1: openInTimeline() directo
    # ==========================================================================
    if camino == 1:
        debug_print("📋 ESTRATEGIA: openInTimeline() directo (como Projects Panel)")
        debug_print("   - Sin viewers temporales")
        debug_print("   - Sin cierres de widgets")
        debug_print("   - Solo: openInTimeline() + processEvents()")
        debug_print("")
        
        try:
            debug_print("🔧 Llamando hiero.ui.openInTimeline(seq)...")
            new_timeline = hiero.ui.openInTimeline(seq)
            debug_print("✅ openInTimeline() ejecutado sin excepciones")
            
            _process_events("post-openInTimeline")
            
            new_active = hiero.ui.activeSequence()
            if new_active and new_active.name() == seq_name:
                debug_print(f"✅ Secuencia activa confirmada: {seq_name}")
            else:
                debug_print(f"⚠️ Secuencia activa no coincide")
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR en openInTimeline(): {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    # ==========================================================================
    # CAMINO 2: setActiveSequence() + openInTimeline()
    # ==========================================================================
    elif camino == 2:
        debug_print("📋 ESTRATEGIA: setActiveSequence() ANTES de openInTimeline()")
        debug_print("   - Paso 1: setActiveSequence(seq) para 'preparar' la secuencia")
        debug_print("   - Paso 2: processEvents() para estabilizar")
        debug_print("   - Paso 3: openInTimeline(seq) para crear timeline/viewer")
        debug_print("")
        
        try:
            # PASO 1: Activar la secuencia primero
            if hasattr(hiero.ui, 'setActiveSequence'):
                debug_print("🔧 Paso 1: Llamando hiero.ui.setActiveSequence(seq)...")
                hiero.ui.setActiveSequence(seq)
                debug_print("✅ setActiveSequence() ejecutado sin excepciones")
                
                _process_events("post-setActiveSequence")
                
                # Verificar que se activó
                current_active = hiero.ui.activeSequence()
                if current_active and current_active.name() == seq_name:
                    debug_print(f"✅ Secuencia activada correctamente: {seq_name}")
                else:
                    debug_print(f"⚠️ Secuencia activa no coincide después de setActiveSequence")
            else:
                debug_print("⚠️ hiero.ui.setActiveSequence no disponible (Hiero muy antiguo?)")
            
            # PASO 2: Ahora crear timeline/viewer
            debug_print("")
            debug_print("🔧 Paso 2: Llamando hiero.ui.openInTimeline(seq)...")
            new_timeline = hiero.ui.openInTimeline(seq)
            debug_print("✅ openInTimeline() ejecutado sin excepciones")
            
            _process_events("post-openInTimeline")
            
            # Verificar resultado final
            new_active = hiero.ui.activeSequence()
            if new_active and new_active.name() == seq_name:
                debug_print(f"✅ Secuencia activa confirmada (final): {seq_name}")
            else:
                debug_print(f"⚠️ Secuencia activa no coincide (final)")
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR: {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    # ==========================================================================
    # CAMINO 3: Solo openInNewViewer() (ventana flotante)
    # ==========================================================================
    elif camino == 3:
        debug_print("📋 ESTRATEGIA: Solo openInNewViewer() (ventana flotante)")
        debug_print("   - NO crea timeline dockeado")
        debug_print("   - Solo crea viewer en ventana flotante")
        debug_print("   - Prueba diagnóstica para ver si openInTimeline es el problema")
        debug_print("")
        
        try:
            debug_print("🔧 Llamando hiero.ui.openInNewViewer(seq)...")
            new_viewer = hiero.ui.openInNewViewer(seq)
            debug_print("✅ openInNewViewer() ejecutado sin excepciones")
            
            _process_events("post-openInNewViewer")
            
            if new_viewer:
                debug_print("✅ Viewer flotante creado correctamente")
            else:
                debug_print("⚠️ openInNewViewer() devolvió None")
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR en openInNewViewer(): {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    # ==========================================================================
    # CAMINO 4: openInNewViewer() + getTimelineEditor() + show()
    # ==========================================================================
    elif camino == 4:
        debug_print("📋 ESTRATEGIA: openInNewViewer() + recuperar timeline oculto + show()")
        debug_print("   - Paso 1: openInNewViewer(seq) para crear viewer")
        debug_print("   - Paso 2: getTimelineEditor(seq) para recuperar timeline OCULTO que ya existe")
        debug_print("   - Paso 3: timeline.show() + raise_() + activateWindow() para hacerlo visible")
        debug_print("")
        
        try:
            # PASO 1: Crear viewer (funciona)
            debug_print("🔧 Paso 1: Llamando hiero.ui.openInNewViewer(seq)...")
            new_viewer = hiero.ui.openInNewViewer(seq)
            debug_print("✅ openInNewViewer() ejecutado sin excepciones")
            
            _process_events("post-openInNewViewer")
            
            if new_viewer:
                debug_print("✅ Viewer creado correctamente")
            else:
                debug_print("⚠️ openInNewViewer() devolvió None")
            
            # PASO 2: Recuperar timeline oculto que ya existe
            debug_print("")
            debug_print("🔧 Paso 2: Llamando hiero.ui.getTimelineEditor(seq)...")
            new_timeline = hiero.ui.getTimelineEditor(seq)
            
            if new_timeline:
                debug_print("✅ getTimelineEditor() devolvió timeline (estaba oculto)")
                
                # Obtener info del timeline
                tl_window = new_timeline.window() if hasattr(new_timeline, 'window') else None
                if tl_window:
                    tl_objname = tl_window.objectName() if hasattr(tl_window, 'objectName') else "N/A"
                    tl_title = tl_window.windowTitle() if hasattr(tl_window, 'windowTitle') else "N/A"
                    debug_print(f"   Timeline: objectName={tl_objname}, title={tl_title}")
                
                # PASO 3: Hacer timeline visible
                debug_print("")
                debug_print("🔧 Paso 3: Haciendo timeline visible...")
                
                try:
                    # Intentar diferentes métodos para hacer visible el timeline
                    if hasattr(new_timeline, 'show'):
                        new_timeline.show()
                        debug_print("   ✅ timeline.show() ejecutado")
                    
                    if tl_window:
                        if hasattr(tl_window, 'show'):
                            tl_window.show()
                            debug_print("   ✅ timeline.window().show() ejecutado")
                        if hasattr(tl_window, 'raise_'):
                            tl_window.raise_()
                            debug_print("   ✅ timeline.window().raise_() ejecutado")
                        if hasattr(tl_window, 'activateWindow'):
                            tl_window.activateWindow()
                            debug_print("   ✅ timeline.window().activateWindow() ejecutado")
                    
                    if hasattr(new_timeline, 'setFocus'):
                        new_timeline.setFocus()
                        debug_print("   ✅ timeline.setFocus() ejecutado")
                    
                    _process_events("post-timeline-show")
                    
                    debug_print("✅ Timeline debería estar visible ahora")
                    
                except Exception as e:
                    debug_print(f"⚠️ Error haciendo timeline visible: {e}")
                    debug_print(traceback.format_exc())
                
            else:
                debug_print("⚠️ getTimelineEditor() devolvió None (timeline no existe?)")
                debug_print("   Esto es extraño - los logs sugieren que debería existir oculto")
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR en CAMINO 4: {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    # ==========================================================================
    # CAMINO 5: Reutilizar timeline integrado existente + setSequence()
    # ==========================================================================
    elif camino == 5:
        debug_print("📋 ESTRATEGIA: Reutilizar timeline integrado de otra secuencia")
        debug_print("   - Paso 1: Buscar timeline INTEGRADO (dockeado) de cualquier secuencia")
        debug_print("   - Paso 2: Cambiar su secuencia con setSequence() o openInTimeline()")
        debug_print("   - Paso 3: Evita el bug de openInTimeline() en secuencias libres H16")
        debug_print("   - Objetivo: Timeline Y viewer dockeados, sin ventanas flotantes")
        debug_print("")
        
        try:
            # PASO 1: Buscar timeline integrado existente
            debug_print("🔧 Paso 1: Buscando timeline integrado existente...")
            
            active_seq = hiero.ui.activeSequence()
            if not active_seq:
                debug_print("❌ No hay secuencia activa - no hay timeline integrado disponible")
                debug_print("   CAMINO 5 requiere al menos una secuencia con timeline/viewer abiertos")
                flush_logs()
                return None
            
            debug_print(f"   Secuencia activa actual: {active_seq.name()}")
            
            existing_timeline = hiero.ui.getTimelineEditor(active_seq)
            if not existing_timeline:
                debug_print("❌ No se pudo obtener timeline de la secuencia activa")
                flush_logs()
                return None
            
            debug_print("✅ Timeline integrado encontrado")
            tl_window = existing_timeline.window() if hasattr(existing_timeline, 'window') else None
            if tl_window:
                tl_objname = tl_window.objectName() if hasattr(tl_window, 'objectName') else "N/A"
                tl_title = tl_window.windowTitle() if hasattr(tl_window, 'windowTitle') else "N/A"
                debug_print(f"   Timeline actual: objectName={tl_objname}, title={tl_title}")
            debug_print("")
            
            # PASO 2: Intentar cambiar la secuencia del timeline (sin crear nuevo)
            debug_print("🔧 Paso 2: Cambiando secuencia del timeline integrado...")
            debug_print(f"   De: {active_seq.name()} → A: {seq_name}")
            
            # Método 1: setSequence (si existe)
            if hasattr(existing_timeline, 'setSequence'):
                debug_print("   Usando timeline.setSequence(seq)...")
                existing_timeline.setSequence(seq)
                _process_events("post-setSequence")
                debug_print("✅ setSequence() ejecutado sin excepciones")
            else:
                # Método 2: openInTimeline (pero crashea en H16 - evitar)
                debug_print("   setSequence no disponible - fallback alternativo...")
                debug_print("   ⚠️ openInTimeline() crashea en H16 incluso con timeline existente")
                debug_print("   ❌ No se puede cambiar secuencia sin setSequence() en H16")
                flush_logs()
                return None
            
            # Verificar que cambió correctamente
            new_active = hiero.ui.activeSequence()
            if new_active and new_active.name() == seq_name:
                debug_print(f"✅ Secuencia activa confirmada: {seq_name}")
                debug_print("✅ Timeline/viewer ahora muestran la secuencia objetivo")
                debug_print("✅ Sin crear ventanas flotantes, todo integrado/dockeado")
            else:
                debug_print(f"⚠️ Secuencia no cambió correctamente")
                debug_print(f"   Esperado: {seq_name}")
                debug_print(f"   Actual: {new_active.name() if new_active else 'None'}")
            
            debug_print("")
            
            # Actualizar referencias (el timeline ES el mismo, solo cambió la secuencia)
            new_timeline = existing_timeline
            new_viewer = hiero.ui.currentViewer()
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR en CAMINO 5: {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    # ==========================================================================
    # CAMINO 6: Detección de versión + Método específico por versión
    # ==========================================================================
    elif camino == 6:
        debug_print("📋 ESTRATEGIA: Detección de versión + método específico")
        debug_print("   - Detectar si es Hiero 15 o 16")
        debug_print("   - H15: Usar openInTimeline() (funciona perfecto)")
        debug_print("   - H16: Usar setActiveSequence() SOLO (evita openInTimeline)")
        debug_print("")
        
        try:
            # PASO 1: Detectar versión
            hiero_version = get_hiero_version()
            if hiero_version is None:
                debug_print("❌ No se pudo detectar versión de Hiero - abortando")
                flush_logs()
                return None
            
            debug_print(f"✅ Versión detectada: Hiero {hiero_version}")
            debug_print("")
            
            # PASO 2: Estrategia según versión
            if hiero_version == 15:
                # HIERO 15: openInTimeline funciona perfecto
                debug_print("🔧 HIERO 15 detectado - usando openInTimeline()")
                hiero.ui.openInTimeline(seq)
                _process_events("post-openInTimeline")
                debug_print("✅ openInTimeline() ejecutado sin excepciones")
                
            elif hiero_version >= 16:
                # HIERO 16+: openInTimeline crashea - usar setActiveSequence
                debug_print("🔧 HIERO 16+ detectado - usando setActiveSequence()")
                debug_print("   (evitando openInTimeline que crashea en H16)")
                
                if hasattr(hiero.ui, 'setActiveSequence'):
                    hiero.ui.setActiveSequence(seq)
                    _process_events("post-setActiveSequence")
                    debug_print("✅ setActiveSequence() ejecutado sin excepciones")
                    debug_print("⚠️ Nota: Solo cambia secuencia activa, no crea timeline/viewer nuevos")
                else:
                    debug_print("❌ setActiveSequence no disponible")
                    flush_logs()
                    return None
            else:
                debug_print(f"⚠️ Versión desconocida: {hiero_version}")
                flush_logs()
                return None
            
            # Verificar que cambió correctamente
            new_active = hiero.ui.activeSequence()
            if new_active and new_active.name() == seq_name:
                debug_print(f"✅ Secuencia activa confirmada: {seq_name}")
            else:
                debug_print(f"⚠️ Secuencia no cambió correctamente")
                debug_print(f"   Esperado: {seq_name}")
                debug_print(f"   Actual: {new_active.name() if new_active else 'None'}")
            
            debug_print("")
            
            # Obtener referencias
            new_timeline = hiero.ui.getTimelineEditor(seq)
            new_viewer = hiero.ui.currentViewer()
                
        except Exception as e:
            creation_error = e
            debug_print(f"❌ CRASH/ERROR en CAMINO 6: {e}")
            debug_print(traceback.format_exc())
            flush_logs()
            return None

    flush_logs()

    # Obtener info del timeline creado
    timeline_obj = "N/A"
    timeline_window_title = "N/A"
    timeline_seq_name = "Desconocida"
    if new_timeline:
        try:
            tl_window = (
                new_timeline.window() if hasattr(new_timeline, "window") else None
            )
            if tl_window and hasattr(tl_window, "objectName"):
                timeline_obj = tl_window.objectName()
            if tl_window and hasattr(tl_window, "windowTitle"):
                timeline_window_title = tl_window.windowTitle()
            try:
                if hasattr(new_timeline, "sequence") and new_timeline.sequence():
                    timeline_seq = new_timeline.sequence()
                    timeline_seq_name = (
                        timeline_seq.name()
                        if hasattr(timeline_seq, "name")
                        else "Sin nombre"
                    )
            except Exception:
                pass
        except Exception:
            pass

    debug_print(
        f"🎯 TIMELINE CREADO: objectName={timeline_obj} | windowTitle={timeline_window_title} | sequence={timeline_seq_name}"
    )

    # Obtener info del viewer creado (currentViewer debería apuntar al nuevo)
    new_viewer = hiero.ui.currentViewer()
    viewer_obj = "N/A"
    viewer_seq_name = "Sin secuencia"
    if new_viewer:
        try:
            viewer_window = new_viewer.window()
            if viewer_window and hasattr(viewer_window, "objectName"):
                viewer_obj = viewer_window.objectName()
            if hasattr(new_viewer, "player") and new_viewer.player():
                seq_player = new_viewer.player().sequence()
                if seq_player and hasattr(seq_player, "name"):
                    viewer_seq_name = seq_player.name()
        except Exception:
            pass
        debug_print(
            f"🎯 VIEWER CREADO: objectName={viewer_obj} | sequence={viewer_seq_name}"
        )
    else:
        debug_print("❌ currentViewer() devolvió None (no se creó viewer)")

    debug_print("")
    debug_print("=" * 100)
    debug_print(f"✅ CAMINO {camino} COMPLETADO - Verificar resultados en exploración final")
    debug_print("=" * 100)
    
    flush_logs()

    return {
        "sequence_name": seq_name,
        "timeline_obj": timeline_obj,
        "timeline_window_title": timeline_window_title,
        "viewer_obj": viewer_obj,
        "viewer_seq_name": viewer_seq_name,
    }


def main():
    global debug_logger
    clear_debug_log()
    debug_logger = setup_debug_logging()

    debug_print("=" * 100)
    debug_print("🎯 TEST TEORÍA 2 - OBJETIVO:")
    debug_print("   Mostrar en UI: timeline + viewer de secuencia sin panels abiertos")
    debug_print("=" * 100)
    debug_print("")

    estado_inicial = explore_sequences_and_open_panels()
    sequences_free = estado_inicial.get("sequences_free", []) if estado_inicial else []

    if not sequences_free:
        debug_print(
            "\n❌ No hay secuencias libres; no se puede ejecutar la prueba TEORÍA 2."
        )
        return

    debug_print("")
    debug_print("⚠️ INICIANDO CAMINO 6: Detección de versión + método específico")
    debug_print("   Estrategia: Detectar H15 vs H16 y usar método correcto")
    debug_print("   - HIERO 15: openInTimeline() funciona perfecto")
    debug_print("   - HIERO 16: setActiveSequence() solo (evita openInTimeline crasheando)")
    debug_print("   - Descubrimiento: openInTimeline() crashea SIEMPRE en H16 (incluso con timeline previo)")
    debug_print("   Si funciona → ✅ SOLUCIÓN DEFINITIVA (compatible ambas versiones)")
    debug_print("")
    flush_logs()

    # Crear timeline/viewer para una secuencia libre
    # CAMINO 4: openInNewViewer + recuperar timeline oculto
    creacion_info = crear_timeline_y_viewer_para_libre(sequences_free, camino=6)
    if not creacion_info:
        debug_print(
            "\n❌ No se pudo crear timeline/viewer (openInTimeline falló o fue abortado)."
        )
        return

    debug_print(
        "\n✅ CREACIÓN COMPLETADA. RELANZANDO EXPLORACIÓN PARA COMPARAR ESTADO FINAL..."
    )
    debug_print("=" * 100)
    explore_sequences_and_open_panels()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        debug_print(f"\n❌ ERROR GENERAL EN TEST TEORÍA 2: {e}")
        debug_print(traceback.format_exc())
