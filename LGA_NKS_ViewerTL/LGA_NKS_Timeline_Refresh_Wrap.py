"""
____________________________________________________________________________________________________________________

  LGA_NKS_Timeline_Refresh_Wrap v1.3 | Lega
  
  Wrapper que ejecuta una secuencia de scripts para refrescar el timeline manteniendo el nivel de zoom original:
  
  1. Captura el estado actual del timeline (zoom y scroll)
  2. Limpia el cache de reproducción (deshabiliado por el momento)
  3. Refresca el timeline
  4. Ajusta el tamaño de la ventana
  5. Scrollea al track superior
  6. Restaura el estado original (dos intentos) usando los valores exactos del slider y scrollbar
____________________________________________________________________________________________________________________
"""

import hiero.core
import hiero.ui
import os
import importlib.util
from LGA_QtAdapter_HieroTools import QtWidgets, QtCore
import time

# Variable global para activar o desactivar los prints
DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def get_timeline_state(timeline_editor=None):
    """
    Obtiene el estado actual del timeline.
    Si timeline_editor es None, usa activeSequence() como fallback.
    """
    try:
        if timeline_editor is None:
            t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        else:
            t = timeline_editor
        if not t:
            return None
            
        # Buscar el QSplitter primero
        splitter = None
        for child in t.window().children():
            if isinstance(child, QtWidgets.QSplitter):
                splitter = child
                break
                
        if not splitter:
            debug_print("No se pudo encontrar el QSplitter")
            return None
            
        # Buscar el TimelineView dentro del primer widget del QSplitter
        timeline_view = None
        for child in splitter.children():
            if isinstance(child, QtWidgets.QWidget):
                for subchild in child.children():
                    if isinstance(subchild, QtWidgets.QAbstractScrollArea):
                        timeline_view = subchild
                        break
                if timeline_view:
                    break
                    
        if not timeline_view:
            debug_print("No se pudo encontrar el TimelineView")
            return None
            
        # Buscar viewport y h_container por nombre
        viewport = None
        h_container = None
        for child in timeline_view.children():
            if hasattr(child, 'objectName'):
                if child.objectName() == "qt_scrollarea_viewport":
                    viewport = child
                elif child.objectName() == "qt_scrollarea_hcontainer":
                    h_container = child
        
        if not all([viewport, h_container]):
            debug_print("No se pudieron encontrar todos los widgets necesarios")
            return None
            
        # Obtener scrollbar y slider
        h_scrollbar = h_container.children()[0]  # QScrollBar
        h_slider = h_container.children()[2]     # QSlider
        
        viewport_width = viewport.width()
        scrollbar_range = h_scrollbar.maximum() - h_scrollbar.minimum() + h_scrollbar.pageStep()
        zoom_factor = viewport_width / scrollbar_range
        
        state = {
            'scroll_value': h_scrollbar.value(),
            'scroll_min': h_scrollbar.minimum(),
            'scroll_max': h_scrollbar.maximum(),
            'page_step': h_scrollbar.pageStep(),
            'viewport_width': viewport_width,
            'zoom_factor': zoom_factor,
            'slider_value': h_slider.value() if hasattr(h_slider, 'value') else None
        }
        
        return state
            
    except Exception as e:
        debug_print(f"Error al obtener el estado del timeline: {e}")
        if DEBUG:
            import traceback
            debug_print(traceback.format_exc())
        
    return None

def restore_timeline_state(state, timeline_editor=None):
    """
    Restaura el estado del timeline usando acceso directo al scrollbar y slider.
    Si timeline_editor es None, usa activeSequence() como fallback.
    """
    try:
        if timeline_editor is None:
            t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        else:
            t = timeline_editor
        if not t:
            return False
            
        # Buscar el QSplitter primero
        splitter = None
        for child in t.window().children():
            if isinstance(child, QtWidgets.QSplitter):
                splitter = child
                break
                
        if not splitter:
            debug_print("No se pudo encontrar el QSplitter")
            return False
            
        # Buscar el TimelineView dentro del primer widget del QSplitter
        timeline_view = None
        for child in splitter.children():
            if isinstance(child, QtWidgets.QWidget):
                for subchild in child.children():
                    if isinstance(subchild, QtWidgets.QAbstractScrollArea):
                        timeline_view = subchild
                        break
                if timeline_view:
                    break
                    
        if not timeline_view:
            debug_print("No se pudo encontrar el TimelineView")
            return False
            
        # Buscar viewport y h_container por nombre
        viewport = None
        h_container = None
        for child in timeline_view.children():
            if hasattr(child, 'objectName'):
                if child.objectName() == "qt_scrollarea_viewport":
                    viewport = child
                elif child.objectName() == "qt_scrollarea_hcontainer":
                    h_container = child
        
        if not all([viewport, h_container]):
            debug_print("No se pudieron encontrar todos los widgets necesarios")
            return False
            
        # Obtener scrollbar y slider
        h_scrollbar = h_container.children()[0]  # QScrollBar
        h_slider = h_container.children()[2]     # QSlider
        
        debug_print("\nRestaurando estado del timeline...")
        debug_print(f"Usando scrollbar y slider para restaurar zoom_factor: {state['zoom_factor']}")
        
        # 1. Primero restaurar el valor del slider
        if state['slider_value'] is not None:
            debug_print(f"Restaurando valor del slider: {state['slider_value']}")
            h_slider.setValue(state['slider_value'])
            QtCore.QCoreApplication.processEvents()
            
            # Verificar estado intermedio
            intermediate_state = get_timeline_state()
            debug_print("\nEstado después de restaurar slider:")
            debug_print(intermediate_state)
        
        # 2. Luego restaurar valores del scrollbar
        debug_print("\nRestaurando valores del scrollbar...")
        h_scrollbar.setPageStep(state['page_step'])
        h_scrollbar.setMaximum(state['scroll_max'])
        h_scrollbar.setMinimum(state['scroll_min'])
        h_scrollbar.setValue(state['scroll_value'])
        
        QtCore.QCoreApplication.processEvents()
        
        # Verificar el estado final
        final_state = get_timeline_state()
        debug_print("\nEstado FINAL después de restaurar:")
        debug_print(final_state)
        
        return True
            
    except Exception as e:
        debug_print(f"Error al restaurar el estado: {e}")
        return False

def find_and_close_old_viewers():
    """
    Cierra todos los viewers que NO sean el currentViewer().
    Estrategia: después de openInTimeline(), currentViewer() devuelve el nuevo,
    así que todos los demás viewers son viejos y pueden cerrarse.
    """
    try:
        # Obtener el viewer actualmente activo (el nuevo)
        current_viewer = hiero.ui.currentViewer()
        if not current_viewer:
            debug_print("⚠️ No hay viewer actualmente activo")
            return False

        debug_print(f"\n🔍 Buscando viewers viejos (todos excepto currentViewer: {hex(id(current_viewer))})")

        # Buscar TODOS los viewers en la aplicación
        from LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            debug_print("No se pudo obtener la instancia de QApplication")
            return False

        all_widgets = app.allWidgets()
        old_viewers_found = 0
        old_viewers_closed = 0

        for widget in all_widgets:
            if isinstance(widget, hiero.ui.Viewer) and widget != current_viewer:
                old_viewers_found += 1
                try:
                    # Obtener info del viewer viejo antes de cerrarlo
                    old_window = widget.window()
                    old_obj_name = old_window.objectName() if (old_window and hasattr(old_window, 'objectName')) else 'N/A'
                    debug_print(f"  📍 Encontrado viewer viejo: {old_obj_name} (ID: {hex(id(widget))})")

                    # Intentar cerrar el viewer viejo
                    old_window.close()
                    QtCore.QCoreApplication.processEvents()

                    old_viewers_closed += 1
                    debug_print(f"  ✅ Cerrado viewer viejo: {old_obj_name}")

                except Exception as e:
                    debug_print(f"  ❌ Error cerrando viewer viejo {old_obj_name}: {e}")

        debug_print(f"\n📊 Resumen: {old_viewers_found} viewers viejos encontrados, {old_viewers_closed} cerrados")
        return old_viewers_closed > 0

    except Exception as e:
        debug_print(f"❌ Error en find_and_close_old_viewers: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return False

def import_script(script_name):
    """
    Importa un script desde la carpeta LGA_NKS
    """
    script_path = os.path.join(os.path.dirname(__file__), script_name + '.py')
    if os.path.exists(script_path):
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    else:
        debug_print(f"Script no encontrado: {script_path}")
        return None

def main():
    """
    Función principal que coordina la ejecución de todos los scripts
    """
    try:
        start_total = time.time()
        
        # 1. Capturar estado inicial
        start_time = time.time()
        original_state = get_timeline_state()
        if original_state is None:
            debug_print("No se pudo capturar el estado inicial del timeline.")
            return
        debug_print("\nEstado INICIAL:")
        debug_print(original_state)
        debug_print(f"Tiempo capturando estado inicial: {time.time() - start_time:.3f} segundos")

        # 2. Ejecutar Clear Cache Playback
        """
        start_time = time.time()
        cache_module = import_script('LGA_NKS_ClearCachePlayback')
        if cache_module:
            cache_module.main()
            QtCore.QThread.msleep(10)
            QtCore.QCoreApplication.processEvents()
        debug_print(f"Tiempo ejecutando clear cache: {time.time() - start_time:.3f} segundos")
        """

        # 3. Ejecutar refresh y obtener timeline/viewer nuevo
        start_time = time.time()
        refresh_module = import_script('LGA_NKS_Timeline_Refresh')
        new_timeline = None
        new_viewer = None
        if refresh_module:
            result = refresh_module.main()
            if result and len(result) >= 2:
                new_timeline, new_viewer = result[:2]  # Solo necesitamos timeline y viewer nuevos
                debug_print(f"Timeline nuevo recibido: {hex(id(new_timeline)) if new_timeline else None}")
                debug_print(f"Viewer nuevo recibido: {hex(id(new_viewer)) if new_viewer else None}")
                if len(result) >= 4:
                    debug_print(f"Viewer viejo objectName: {result[2]}")
                    debug_print(f"Timeline viejo objectName: {result[3]}")
            QtCore.QThread.msleep(10)
            QtCore.QCoreApplication.processEvents()
        debug_print(f"Tiempo ejecutando refresh timeline: {time.time() - start_time:.3f} segundos")

        # Si no obtuvimos el timeline nuevo, usar activeSequence() como fallback
        if not new_timeline:
            debug_print("⚠️ No se obtuvo timeline nuevo, usando activeSequence() como fallback")
            active_seq = hiero.ui.activeSequence()
            if active_seq:
                new_timeline = hiero.ui.getTimelineEditor(active_seq)

        start_time = time.time()
        reduce_module = import_script('LGA_NKS_Reduce_SeqWin')
        if reduce_module:
            reduce_module.main(new_timeline)  # Pasar el timeline nuevo
            QtCore.QThread.msleep(10)
            QtCore.QCoreApplication.processEvents()
        debug_print(f"Tiempo ejecutando reduce window: {time.time() - start_time:.3f} segundos")

        start_time = time.time()
        scroll_module = import_script('LGA_NKS_ScrollTo_TopTrack')
        if scroll_module:
            scroll_module.main(new_timeline)  # Pasar el timeline nuevo
            QtCore.QThread.msleep(10)
            QtCore.QCoreApplication.processEvents()
        debug_print(f"Tiempo ejecutando scroll to top: {time.time() - start_time:.3f} segundos")

        # 4. Primer intento de restauración usando el timeline nuevo
        start_time = time.time()
        debug_print("\nPrimer intento de restauración...")
        success = restore_timeline_state(original_state, new_timeline)
        debug_print(f"Tiempo primera restauración: {time.time() - start_time:.3f} segundos")
        
        # 5. Segundo intento de restauración usando el timeline nuevo
        start_time = time.time()
        debug_print("\nSegundo intento de restauración...")
        success = restore_timeline_state(original_state, new_timeline)
        debug_print(f"Tiempo segunda restauración: {time.time() - start_time:.3f} segundos")

        # 6. Procesar eventos finales
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.2)

        # 7. ANALIZAR viewers/timelines para cierre (SIN CERRAR AÚN)
        debug_print(f"\n--- ANÁLISIS DE VIEWERS/TIMELINES PARA CIERRE ---")
        debug_print(f"   (Solo análisis - NO se cierra nada aún)")

        try:
            # Recopilar viewers actuales
            from LGA_QtAdapter_HieroTools import QtWidgets
            app = QtWidgets.QApplication.instance()
            if not app:
                debug_print("❌ No QApplication")
                return

            # Buscar viewers con metaObject().className()
            viewers = []
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

            # Recopilar timelines
            timelines = []
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

            # Comparar con getTimelineEditor()
            active_seq = hiero.ui.activeSequence()
            current_timeline = hiero.ui.getTimelineEditor(active_seq) if active_seq else None
            current_timeline_obj_name = ""
            if current_timeline:
                try:
                    current_window = current_timeline.window()
                    if current_window and hasattr(current_window, 'objectName'):
                        current_timeline_obj_name = current_window.objectName()
                except Exception as e:
                    debug_print(f"Error obteniendo timeline objectName: {e}")

            # MOSTRAR ANÁLISIS DETALLADO
            debug_print(f"\n🔍 VIEWERS ENCONTRADOS ({len(viewers)}):")
            for i, viewer in enumerate(viewers, 1):
                obj_name = viewer.get('object_name', 'N/A')
                window_title = viewer.get('window_title', '')
                seq_name = viewer.get('sequence_name', 'N/A')

                display_name = window_title or seq_name or obj_name
                is_current = (obj_name == current_obj_name and obj_name != "")
                status = "🎯 ACTIVO" if is_current else "📍 VIEJO"

                debug_print(f"   {i}. {status}: {display_name} (obj: {obj_name}, seq: {seq_name})")

            debug_print(f"\n🔍 TIMELINES ENCONTRADOS ({len(timelines)}):")
            for i, timeline in enumerate(timelines, 1):
                obj_name = timeline.get('object_name', 'N/A')
                window_title = timeline.get('window_title', '')
                seq_name = timeline.get('sequence_name', 'N/A')

                display_name = window_title or seq_name or obj_name
                is_current = (obj_name == current_timeline_obj_name and obj_name != "")
                status = "🎯 ACTIVO" if is_current else "📍 VIEJO"

                debug_print(f"   {i}. {status}: {display_name} (obj: {obj_name}, seq: {seq_name})")

            # RESUMEN EJECUTIVO
            debug_print(f"\n" + "="*80)
            debug_print("📋 RESUMEN EJECUTIVO - QUÉ CERRAR")
            debug_print("="*80)

            if current_viewer:
                current_window_title = ""
                try:
                    current_window = current_viewer.window()
                    if current_window and hasattr(current_window, 'windowTitle'):
                        current_window_title = current_window.windowTitle() or ""
                except:
                    pass
                active_display = current_window_title or "Sin título"
                debug_print(f"🎯 VIEWER ACTIVO: {active_display} (obj: {current_obj_name})")
            else:
                debug_print("❌ VIEWER ACTIVO: NO IDENTIFICADO")

            if active_seq:
                timeline_active_display = active_seq.name() if hasattr(active_seq, 'name') else "Sin nombre"
                debug_print(f"🎯 TIMELINE ACTIVO: {timeline_active_display} (obj: {current_timeline_obj_name})")
            else:
                debug_print("❌ TIMELINE ACTIVO: NO IDENTIFICADO")

            # Viewers a cerrar
            old_viewers = [v for v in viewers if v.get('object_name', '') != current_obj_name or not v.get('object_name', '').strip()]
            if old_viewers:
                debug_print("📍 VIEWERS A CERRAR:")
                for v in old_viewers:
                    obj_name = v.get('object_name', '')
                    window_title = v.get('window_title', '')
                    seq_name = v.get('sequence_name', 'N/A')

                    # Filtrar Contact Sheet
                    if 'contactsheet' in obj_name.lower():
                        debug_print(f"   ⚠️ SALTAR Contact Sheet: {obj_name}")
                        continue

                    display_name = window_title or seq_name or obj_name
                    debug_print(f"   📍 {display_name} (obj: {obj_name}, seq: {seq_name})")
            else:
                debug_print("✅ NO HAY VIEWERS PARA CERRAR")

            # Timelines a cerrar
            old_timelines = [t for t in timelines if t.get('object_name', '') != current_timeline_obj_name or not t.get('object_name', '').strip()]
            if old_timelines:
                debug_print("📍 TIMELINES A CERRAR:")
                for t in old_timelines:
                    obj_name = t.get('object_name', '')
                    window_title = t.get('window_title', '')
                    seq_name = t.get('sequence_name', 'N/A')

                    display_name = window_title or seq_name or obj_name
                    debug_print(f"   📍 {display_name} (obj: {obj_name}, seq: {seq_name})")
            else:
                debug_print("✅ NO HAY TIMELINES PARA CERRAR")

            debug_print(f"\n📊 TOTAL: {len(old_viewers)} viewers y {len(old_timelines)} timelines para cerrar")
            debug_print(f"   ✅ Análisis completado (SIN cerrar nada)")

        except Exception as e:
            debug_print(f"❌ Error en análisis: {e}")
            import traceback
            debug_print(traceback.format_exc())

        debug_print(f"\nTiempo total de operación: {time.time() - start_total:.3f} segundos")

    except Exception as e:
        debug_print(f"Error en Timeline Refresh Wrap: {e}")
        import traceback
        debug_print(traceback.format_exc())

if __name__ == "__main__":
    main()
