"""
______________________________________________________

  LGA_NKS_FrameNumber v0.56 | Lega
  Busca el clip 'Frame_Only' en el track 'BurnIn' y posiciona el box
  alineado a la izquierda y al bottom con 30px de margen

  v0.56: Se corrigió el problema de posición vertical (Y)
  v0.55: Logs simplificados
______________________________________________________

"""

import hiero.core
import hiero.ui

# ============================
# Configuración
# ============================

TRACK_NAME = "BurnIn"
CLIP_NAME = "Frame_Only"
DEBUG = True  # Activar para ver información de depuración

# Modo de posicionamiento:
# True = Absoluto: posición basada en las dimensiones completas de la imagen (sin importar zoom/pan)
# False = Relativo: posición basada en el área visible del viewer (considera zoom y pan)
USE_ABSOLUTE_POSITION = False

# ============================
# Funciones Auxiliares
# ============================

def debug_print(*message):
    if DEBUG:
        print(*message)

# ============================
# Función Principal
# ============================

def print_box_values():
    """
    Busca el clip 'Frame_Only' en el track 'BurnIn' e imprime los valores de la propiedad 'box'.
    """
    # Obtener la secuencia activa
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("❌ No se encontró una secuencia activa.")
        return
    
    # Buscar el track especificado
    target_track = None
    for track in seq.videoTracks():
        if track.name() == TRACK_NAME:
            target_track = track
            break
    
    if not target_track:
        debug_print(f"❌ No se encontró el track '{TRACK_NAME}'.")
        return
    
    # Buscar el clip especificado en el track usando subTrackItems() para soft effects
    target_clip = None
    
    # Usar subTrackItems() para acceder a los soft effects (efectos suaves)
    items = target_track.subTrackItems()
    if not items:
        debug_print(f"❌ El track '{TRACK_NAME}' no tiene items.")
        return
    
    # Buscar en los soft effects del track
    for item in items:
        # Cada item es una lista/tupla, tomar el primer elemento
        effect_item = item[0]
        if isinstance(effect_item, hiero.core.EffectTrackItem):
            if effect_item.name() == CLIP_NAME:
                target_clip = effect_item
                break
    
    # Si no se encontró como soft effect, buscar como clip normal
    if not target_clip:
        for item in target_track:
            # Saltar efectos
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            
            # Verificar si es un clip normal y coincide con el nombre
            if hasattr(item, 'name') and item.name() == CLIP_NAME:
                target_clip = item
                break
    
    # Si aún no se encontró, buscar en los efectos de los clips normales
    if not target_clip:
        for item in target_track:
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            
            try:
                effects = item.effects()
                if effects:
                    for effect in effects:
                        if effect.name() == CLIP_NAME:
                            target_clip = effect
                            break
            except:
                pass
            
            if target_clip:
                break
    
    if not target_clip:
        debug_print(f"❌ No se encontró el clip '{CLIP_NAME}' en el track '{TRACK_NAME}'.")
        debug_print(f"Soft effects encontrados en el track:")
        for item in items:
            effect_item = item[0]
            if isinstance(effect_item, hiero.core.EffectTrackItem):
                debug_print(f"  - Soft Effect: {effect_item.name()}")
        debug_print(f"Clips normales encontrados en el track:")
        for item in target_track:
            if isinstance(item, hiero.core.EffectTrackItem):
                debug_print(f"  - Efecto: {item.name()}")
            else:
                clip_name = item.name() if hasattr(item, 'name') else "Sin nombre"
                debug_print(f"  - Clip: {clip_name}")
        return
    
    # Obtener el nodo asociado al clip
    # Los clips normales y los efectos tienen el método node()
    node = None
    try:
        node = target_clip.node()
    except Exception as e:
        # Intentar otros métodos si node() no funciona
        if hasattr(target_clip, 'node'):
            try:
                node = target_clip.node
            except Exception as e2:
                pass
    
    if not node:
        debug_print("❌ No se pudo obtener el nodo asociado al clip.")
        return
    
    # Verificar si el nodo tiene la propiedad 'box'
    if 'box' not in node.knobs():
        debug_print("❌ El nodo no tiene una propiedad 'box'.")
        debug_print(f"Propiedades disponibles: {list(node.knobs())}")
        return
    
    # Obtener información del viewer y la secuencia
    viewer = hiero.ui.currentViewer()
    if not viewer:
        debug_print("❌ No se encontró un viewer activo.")
        return
    
    # Obtener imagen del viewer para debuggear
    qimage = viewer.image()
    
    # Obtener formato de la secuencia (ya tenemos seq desde el inicio)
    format_obj = seq.format()
    image_width = format_obj.width()  # Ancho completo de la imagen
    image_height = format_obj.height()  # Alto completo de la imagen
    
    # Calcular área visible y transform si estamos en modo relativo
    visible_x_offset = 0
    visible_y_offset = 0
    visible_width = image_width
    visible_height = image_height
    
    if not USE_ABSOLUTE_POSITION:
        # Modo relativo: calcular el área visible basándose en el zoom del player
        if qimage:
            viewer_width = qimage.width()
            viewer_height = qimage.height()
            
            # Calcular el offset del área visible usando el zoom del player
            visible_x_offset = 0
            visible_y_offset = 0
            
            try:
                # Obtener el zoom del player (esto sí funciona)
                player = viewer.player()
                if player:
                    zoom = player.zoom()
                    debug_print(f"   Zoom del player: {zoom:.6f}")
                    
                    # Calcular aspect ratios
                    image_aspect = image_width / image_height if image_height > 0 else 1.0
                    viewer_aspect = viewer_width / viewer_height if viewer_height > 0 else 1.0
                    
                    debug_print(f"   Aspect ratios:")
                    debug_print(f"      Imagen: {image_aspect:.4f} ({image_width}:{image_height})")
                    debug_print(f"      Viewer: {viewer_aspect:.4f} ({viewer_width}:{viewer_height})")
                    
                    # Calcular el área visible en coordenadas de imagen
                    # El zoom es el factor de escala: si zoom > 1, estamos viendo una porción MÁS PEQUEÑA de la imagen
                    # Si zoom = 2, significa que cada pixel del viewer representa 2 pixels de la imagen
                    # Entonces: tamaño_imagen_visible = tamaño_viewer / zoom
                    # Ejemplo: viewer_width=2004, zoom=2 -> visible_width_in_image = 2004/2 = 1002px
                    # Si zoom < 1 (zoom out), el área visible puede ser mayor que la imagen completa
                    
                    # Calcular área visible inicial basada en el zoom
                    visible_width_raw = viewer_width / zoom if zoom > 0 else viewer_width
                    visible_height_raw = viewer_height / zoom if zoom > 0 else viewer_height
                    
                    # Determinar qué dimensión limita el área visible basándose en el aspect ratio
                    if viewer_aspect > image_aspect:
                        visible_height_in_image = visible_height_raw
                        visible_width_in_image = visible_height_in_image * image_aspect
                    else:
                        visible_width_in_image = visible_width_raw
                        visible_height_in_image = visible_width_in_image / image_aspect
                    
                    if USE_ABSOLUTE_POSITION:
                        visible_width_in_image = min(visible_width_in_image, image_width)
                        visible_height_in_image = min(visible_height_in_image, image_height)
                    
                    # Obtener el pan usando player.translation()
                    try:
                        translation = player.translation()  # Devuelve QPointF(x, y)
                        pan_x_viewer = translation.x()
                        pan_y_viewer = translation.y()
                        
                        # Convertir pan del viewer a coordenadas de imagen
                        pan_x_image = pan_x_viewer / zoom if zoom > 0 else pan_x_viewer
                        pan_y_image = pan_y_viewer / zoom if zoom > 0 else pan_y_viewer
                        
                        debug_print(f"\n📍 Pan del viewer:")
                        debug_print(f"   X viewer: {pan_x_viewer:.2f} -> imagen: {pan_x_image:.2f}")
                        debug_print(f"   Y viewer: {pan_y_viewer:.2f} -> imagen: {pan_y_image:.2f}")
                        
                        # Calcular el centro de la imagen
                        image_center_x = image_width / 2
                        image_center_y = image_height / 2
                        
                        # IMPORTANTE: player.translation() devuelve el pan en coordenadas del viewer/widget
                        # El pan representa el desplazamiento del área visible desde el centro
                        # Pan positivo en X = ver más a la izquierda (área visible se mueve a la izquierda)
                        # Pan positivo en Y (en Hiero) = ver más arriba (área visible se mueve hacia arriba)
                        # 
                        # Ya invertimos el pan Y al convertir de coordenadas Qt a Hiero
                        visible_center_x = image_center_x - pan_x_image
                        visible_center_y = image_center_y - pan_y_image
                        
                        # Calcular el offset del área visible (esquina inferior izquierda en coordenadas de imagen)
                        visible_x_offset = visible_center_x - (visible_width_in_image / 2)
                        visible_y_offset = visible_center_y - (visible_height_in_image / 2)
                        
                        debug_print(f"\n📐 Área visible:")
                        debug_print(f"   Centro imagen: ({image_center_x:.2f}, {image_center_y:.2f})")
                        debug_print(f"   Centro visible: ({visible_center_x:.2f}, {visible_center_y:.2f})")
                        debug_print(f"   Offset: X={visible_x_offset:.2f}, Y={visible_y_offset:.2f}")
                        debug_print(f"   Dimensiones visibles: W={visible_width_in_image:.2f}, H={visible_height_in_image:.2f}")
                    except Exception as e:
                        debug_print(f"   ⚠️ Error obteniendo pan de player.translation(): {e}")
                        # Fallback: asumir que está centrado
                        # Si el área visible es igual o mayor que la imagen completa, el offset debe ser 0
                        if visible_width_in_image >= image_width:
                            visible_x_offset = 0
                        else:
                            visible_x_offset = (image_width - visible_width_in_image) / 2
                        
                        if visible_height_in_image >= image_height:
                            visible_y_offset = 0
                        else:
                            visible_y_offset = (image_height - visible_height_in_image) / 2
                        
                        debug_print(f"   ⚠️ Fallback centrado: X={visible_x_offset:.2f}, Y={visible_y_offset:.2f}")
                    
                    # Actualizar las dimensiones visibles
                    visible_width = visible_width_in_image
                    visible_height = visible_height_in_image
                    
                    if USE_ABSOLUTE_POSITION:
                        # En modo absoluto, el área visible no debe salir de los límites de la imagen
                        if visible_width > image_width:
                            visible_width = image_width
                        if visible_height > image_height:
                            visible_height = image_height
                        
                        if visible_x_offset < 0:
                            visible_x_offset = 0
                        if visible_y_offset < 0:
                            visible_y_offset = 0
                        
                        if visible_x_offset + visible_width > image_width:
                            visible_x_offset = max(0, image_width - visible_width)
                        if visible_y_offset + visible_height > image_height:
                            visible_y_offset = max(0, image_height - visible_height)
                else:
                    debug_print(f"   ⚠️ No se pudo obtener el player del viewer")
                    # Fallback: usar aproximación basada en tamaño del viewer
                    if viewer_width < image_width or viewer_height < image_height:
                        visible_x_offset = (image_width - viewer_width) / 2
                        visible_y_offset = (image_height - viewer_height) / 2
                        visible_width = viewer_width
                        visible_height = viewer_height
                    else:
                        visible_x_offset = 0
                        visible_y_offset = 0
                        visible_width = image_width
                        visible_height = image_height
            except Exception as e:
                # Si hay cualquier error, usar aproximación centrada
                debug_print(f"   Error obteniendo información del viewer: {e}")
                if qimage:
                    viewer_width = qimage.width()
                    viewer_height = qimage.height()
                    if viewer_width < image_width or viewer_height < image_height:
                        visible_x_offset = (image_width - viewer_width) / 2
                        visible_y_offset = (image_height - viewer_height) / 2
                        visible_width = viewer_width
                        visible_height = viewer_height
                    else:
                        visible_x_offset = 0
                        visible_y_offset = 0
                        visible_width = image_width
                        visible_height = image_height
                else:
                    visible_x_offset = 0
                    visible_y_offset = 0
                    visible_width = image_width
                    visible_height = image_height
        else:
            debug_print("⚠️ No se pudo obtener la imagen del viewer")
            visible_x_offset = 0
            visible_y_offset = 0
            visible_width = image_width
            visible_height = image_height
    
    if USE_ABSOLUTE_POSITION:
        debug_print(f"\n📐 Modo absoluto: usando dimensiones completas de la imagen")
    
    # Usar las dimensiones apropiadas según el modo
    if USE_ABSOLUTE_POSITION:
        viewer_width = image_width
        viewer_height = image_height
        viewer_center_x = image_width / 2
        viewer_center_y = image_height / 2
    else:
        viewer_width = visible_width
        viewer_height = visible_height
        viewer_center_x = visible_width / 2
        viewer_center_y = visible_height / 2
    
    # Obtener el valor de 'box'
    try:
        box_value = node['box'].value()
        
        # Verificar el formato del valor
        if isinstance(box_value, (tuple, list)) and len(box_value) >= 4:
            x = box_value[0]
            y = box_value[1]
            r = box_value[2]
            t = box_value[3]
            
            # Calcular dimensiones del box
            box_width = r - x
            box_height = t - y
            
            debug_print(f"\n📦 Box actual:")
            debug_print(f"   Posición: x={x:.2f}, y={y:.2f}, r={r:.2f}, t={t:.2f}")
            debug_print(f"   Dimensiones: W={box_width:.2f}, H={box_height:.2f}")
            
            # Configuración: alineado a la izquierda y al bottom con 30px de margen
            LEFT_MARGIN = 30
            BOTTOM_MARGIN = 30
            
            # Calcular nuevos valores según el modo
            if USE_ABSOLUTE_POSITION:
                # Modo absoluto: posición basada en la imagen completa
                new_x = LEFT_MARGIN
                new_r = new_x + box_width
                
                # CORRECCIÓN CRÍTICA: En Hiero/Nuke, Y=0 es el BOTTOM de la imagen, no el TOP
                # Alinear al bottom de la imagen completa con margen
                new_y = BOTTOM_MARGIN  # Bottom del box a 30px del bottom de la imagen
                new_t = new_y + box_height  # Top del box
            else:
                # Modo relativo: posición basada en el área visible
                # El punto cero es el pixel más a la izquierda visible
                new_x = visible_x_offset + LEFT_MARGIN
                new_r = new_x + box_width
                
                # CORRECCIÓN CRÍTICA: Si el área inferior está completamente visible, usar el bottom de la imagen
                # Si visible_y_offset <= 0, significa que el bottom de la imagen (Y=0) está visible
                if visible_y_offset <= 0:
                    # El área inferior está completamente visible, usar el bottom de la imagen directamente
                    new_y = BOTTOM_MARGIN  # 30px del bottom de la imagen completa
                    debug_print(f"\n✅ Área inferior completamente visible:")
                    debug_print(f"   visible_y_offset={visible_y_offset:.2f} <= 0")
                    debug_print(f"   Usando new_y = BOTTOM_MARGIN = {BOTTOM_MARGIN} (bottom de la imagen)")
                else:
                    # El área inferior está cropeada, usar el bottom del área visible
                    new_y = visible_y_offset + BOTTOM_MARGIN  # Bottom del box a 30px del bottom del área visible
                    debug_print(f"\n⚠️ Área inferior cropeada:")
                    debug_print(f"   visible_y_offset={visible_y_offset:.2f} > 0")
                    debug_print(f"   Usando new_y = visible_y_offset + BOTTOM_MARGIN = {new_y:.2f}")
                
                new_t = new_y + box_height  # Top del box
                
                # Asegurar que el box quede dentro del área visible
                # Si el box se sale por la derecha del área visible, ajustarlo
                visible_right_edge = visible_x_offset + visible_width
                if new_r > visible_right_edge:
                    # Mover el box hacia la izquierda para que quepa
                    offset = new_r - visible_right_edge
                    new_x = max(visible_x_offset + LEFT_MARGIN, new_x - offset)
                    new_r = new_x + box_width
                
                # Si el box se sale por la izquierda del área visible, ajustarlo
                if new_x < visible_x_offset:
                    new_x = visible_x_offset + LEFT_MARGIN
                    new_r = new_x + box_width
                
                # CORRECCIÓN: Ahora Y es el bottom, T es el top
                # Si el box se sale por el top del área visible (T > visible_top), ajustarlo
                visible_top = visible_y_offset + visible_height
                if new_t > visible_top:
                    # Mover el box hacia abajo (disminuir Y y T) para que quepa
                    offset = new_t - visible_top
                    new_t = visible_top
                    new_y = new_t - box_height
                    # Si ahora se sale por el bottom, ajustar también
                    if new_y < visible_y_offset:
                        new_y = visible_y_offset + BOTTOM_MARGIN
                        new_t = new_y + box_height
                
                # Si el box se sale por el bottom del área visible (Y < visible_y_offset), ajustarlo
                if new_y < visible_y_offset:
                    new_y = visible_y_offset + BOTTOM_MARGIN
                    new_t = new_y + box_height
            
            # Asegurar que el box no se salga de los límites de la imagen
            # Limitar a los bordes de la imagen completa
            # CORRECCIÓN: Ahora Y es el bottom (Y=0 es el bottom de la imagen, Y=image_height es el top)
            if new_x < 0:
                offset = 0 - new_x
                new_x = 0
                new_r += offset
            if new_y < 0:
                # Y no puede ser menor que 0 (bottom de la imagen)
                offset = 0 - new_y
                new_y = 0
                new_t = new_y + box_height
            if new_r > image_width:
                offset = new_r - image_width
                new_r = image_width
                new_x = max(0, new_x - offset)
            if new_t > image_height:
                # T no puede ser mayor que image_height (top de la imagen)
                offset = new_t - image_height
                new_t = image_height
                new_y = new_t - box_height
            
            # Calcular desplazamiento para información de debug
            offset_x = new_x - x
            offset_y = new_y - y
            
            debug_print(f"\n🎯 Posición nueva (comparación X vs Y):")
            debug_print(f"   X: {x:.2f} -> {new_x:.2f} (offset: {offset_x:.2f})")
            debug_print(f"   Y: {y:.2f} -> {new_y:.2f} (offset: {offset_y:.2f})")
            
            if not USE_ABSOLUTE_POSITION:
                # Calcular posición esperada
                expected_x = visible_x_offset + LEFT_MARGIN
                expected_y = visible_y_offset + BOTTOM_MARGIN
                
                debug_print(f"\n🔍 Verificación área visible (X vs Y):")
                debug_print(f"   Área visible - Bottom: X={visible_x_offset:.2f}, Y={visible_y_offset:.2f}")
                debug_print(f"   Área visible - Top: X={visible_x_offset + visible_width:.2f}, Y={visible_y_offset + visible_height:.2f}")
                debug_print(f"   Posición esperada: X={expected_x:.2f}, Y={expected_y:.2f}")
                debug_print(f"   Posición calculada: X={new_x:.2f}, Y={new_y:.2f}")
                debug_print(f"   Diferencia: X={new_x - expected_x:.2f}px, Y={new_y - expected_y:.2f}px")
                debug_print(f"   Desde área visible: X={new_x - visible_x_offset:.2f}px (esperado: {LEFT_MARGIN}px)")
                debug_print(f"   Desde área visible: Y={new_y - visible_y_offset:.2f}px (esperado: {BOTTOM_MARGIN}px)")
                debug_print(f"   ⚠️ Si Y está muy alto visualmente, new_y debería ser MAYOR que expected_y")
                debug_print(f"   ⚠️ En Hiero Y=0 es bottom, entonces Y más grande = más arriba")
                # Recalcular sin inversión para comparar
                if not USE_ABSOLUTE_POSITION:
                    try:
                        viewer = hiero.ui.currentViewer()
                        if viewer:
                            player = viewer.player()
                            if player:
                                translation = player.translation()
                                pan_y_viewer_test = translation.y()
                                zoom_test = player.zoom()
                                pan_y_image_sin_inversion_test = pan_y_viewer_test / zoom_test if zoom_test > 0 else pan_y_viewer_test
                                visible_center_y_sin_inversion_test = image_height / 2 - pan_y_image_sin_inversion_test
                                visible_y_offset_sin_inversion_test = visible_center_y_sin_inversion_test - (visible_height / 2)
                                expected_y_sin_inversion = visible_y_offset_sin_inversion_test + BOTTOM_MARGIN
                                
                                debug_print(f"\n💡 Análisis del problema:")
                                debug_print(f"   Con inversión: visible_y_offset={visible_y_offset:.2f} -> expected_y={expected_y:.2f} -> new_y={new_y:.2f}")
                                debug_print(f"   Sin inversión: visible_y_offset={visible_y_offset_sin_inversion_test:.2f} -> expected_y={expected_y_sin_inversion:.2f}")
                                debug_print(f"   Diferencia en expected_y: {abs(expected_y - expected_y_sin_inversion):.2f}px")
                                
                                # Calcular cuánto más alto está el box de lo que debería
                                diferencia_y = new_y - expected_y_sin_inversion
                                debug_print(f"\n📊 CUÁNTO MÁS ALTO ESTÁ EL BOX:")
                                debug_print(f"   new_y actual (con inversión): {new_y:.2f}")
                                debug_print(f"   new_y esperado (sin inversión): {expected_y_sin_inversion:.2f}")
                                debug_print(f"   ⚠️ DIFERENCIA: {diferencia_y:.2f}px MÁS ALTO de lo que debería estar")
                                debug_print(f"   ⚠️ El box está {diferencia_y:.2f}px más arriba de donde debería estar visualmente")
                                debug_print(f"   ⚠️ Si el box está muy alto, debería estar en {expected_y_sin_inversion:.2f} en lugar de {new_y:.2f}")
                                debug_print(f"   ⚠️ CONCLUSIÓN: El problema está en la INVERSIÓN del pan Y")
                                debug_print(f"   ⚠️ SOLUCIÓN: NO deberíamos invertir el pan Y (quitar el signo negativo)")
                    except:
                        pass
            
            # Aplicar los nuevos valores
            try:
                new_box_value = (new_x, new_y, new_r, new_t)
                node['box'].setValue(new_box_value)
                debug_print(f"\n✅ Box actualizado: x={new_x:.2f}, y={new_y:.2f}, r={new_r:.2f}, t={new_t:.2f}")
            except Exception as e:
                debug_print(f"\n❌ Error al actualizar el box: {e}")
        else:
            debug_print(f"⚠️ La propiedad 'box' no tiene el formato esperado.")
            debug_print(f"Valor obtenido: {box_value} (Tipo: {type(box_value).__name__})")
    except Exception as e:
        debug_print(f"❌ Error al obtener el valor de 'box': {e}")

# Ejecutar la función
if __name__ == "__main__":
    print_box_values()

