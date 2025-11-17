"""
______________________________________________________

  LGA_NKS_FrameNumber v0.54 | Lega
  Busca el clip 'Frame_Only' en el track 'BurnIn' y posiciona el box
  alineado a la izquierda y al bottom con 30px de margen
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
    
    debug_print(f"✅ Track '{TRACK_NAME}' encontrado.")
    
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
    
    debug_print(f"✅ Clip '{CLIP_NAME}' encontrado.")
    debug_print(f"   Tipo: {type(target_clip).__name__}")
    
    # Obtener el nodo asociado al clip
    # Los clips normales y los efectos tienen el método node()
    node = None
    try:
        node = target_clip.node()
        if node:
            debug_print(f"✅ Nodo obtenido con node(): {node.name()}")
    except Exception as e:
        debug_print(f"⚠️ Error al obtener nodo con node(): {e}")
        # Intentar otros métodos si node() no funciona
        if hasattr(target_clip, 'node'):
            try:
                node = target_clip.node
                if node:
                    debug_print(f"✅ Nodo obtenido con atributo node: {node.name()}")
            except Exception as e2:
                debug_print(f"⚠️ Error al obtener nodo con atributo: {e2}")
    
    if not node:
        debug_print("❌ No se pudo obtener el nodo asociado al clip.")
        debug_print("   Métodos disponibles del clip:")
        import inspect
        for name, method in inspect.getmembers(target_clip, predicate=inspect.ismethod):
            if not name.startswith("_") and 'node' in name.lower():
                debug_print(f"     - {name}")
        return
    
    debug_print(f"✅ Nodo encontrado: {node.name()}")
    
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
    if qimage:
        debug_print(f"\n📐 Información del viewer:")
        debug_print(f"   Imagen visible del viewer: {qimage.width()} × {qimage.height()}")
    else:
        debug_print("⚠️ No se pudo obtener la imagen del viewer")
    
    # Obtener formato de la secuencia (ya tenemos seq desde el inicio)
    format_obj = seq.format()
    image_width = format_obj.width()  # Ancho completo de la imagen
    image_height = format_obj.height()  # Alto completo de la imagen
    
    debug_print(f"\n📐 Información de la secuencia:")
    debug_print(f"   Formato completo de la imagen: {image_width} × {image_height}")
    
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
                    
                    debug_print(f"   Área visible inicial (sin considerar aspect ratio):")
                    debug_print(f"      Ancho: {visible_width_raw:.2f}px")
                    debug_print(f"      Alto: {visible_height_raw:.2f}px")
                    
                    # Determinar qué dimensión limita el área visible basándose en el aspect ratio
                    # Si el viewer es más ancho que la imagen (proporcionalmente), la altura limita
                    # Si el viewer es más alto que la imagen (proporcionalmente), el ancho limita
                    if viewer_aspect > image_aspect:
                        # Viewer más ancho: la altura limita el área visible
                        # El área visible mantiene el aspect ratio de la imagen
                        visible_height_in_image = visible_height_raw
                        visible_height_in_image = min(visible_height_in_image, image_height)
                        visible_width_in_image = visible_height_in_image * image_aspect
                        visible_width_in_image = min(visible_width_in_image, image_width)
                        debug_print(f"   Viewer más ancho: altura limita ({visible_height_in_image:.2f}px)")
                    else:
                        # Viewer más alto o igual: el ancho limita el área visible
                        # El área visible mantiene el aspect ratio de la imagen
                        visible_width_in_image = visible_width_raw
                        visible_width_in_image = min(visible_width_in_image, image_width)
                        visible_height_in_image = visible_width_in_image / image_aspect
                        visible_height_in_image = min(visible_height_in_image, image_height)
                        debug_print(f"   Viewer más alto o igual: ancho limita ({visible_width_in_image:.2f}px)")
                    
                    # Limitar el área visible al tamaño máximo de la imagen (por seguridad)
                    visible_width_in_image = min(visible_width_in_image, image_width)
                    visible_height_in_image = min(visible_height_in_image, image_height)
                    
                    debug_print(f"   Área visible en coordenadas de imagen:")
                    debug_print(f"      Ancho visible: {visible_width_in_image:.2f}px")
                    debug_print(f"      Alto visible: {visible_height_in_image:.2f}px")
                    
                    # Obtener el pan usando player.translation()
                    try:
                        translation = player.translation()  # Devuelve QPointF(x, y)
                        pan_x_viewer = translation.x()
                        pan_y_viewer = translation.y()
                        
                        debug_print(f"   ✅ Pan obtenido de player.translation():")
                        debug_print(f"      Pan X (viewer): {pan_x_viewer:.2f}")
                        debug_print(f"      Pan Y (viewer): {pan_y_viewer:.2f}")
                        
                        # Convertir pan del viewer a coordenadas de imagen
                        # CORRECCIÓN CRÍTICA: El viewer usa coordenadas Qt (Y=0 arriba) pero Hiero/Nuke usa Y=0 abajo
                        # 
                        # Para X: ambos sistemas coinciden (X=0 izquierda) -> pan_x_image = pan_x_viewer / zoom
                        # Para Y: los sistemas están invertidos -> pan_y_image = -pan_y_viewer / zoom
                        # 
                        # Cuando pan Y del viewer es negativo (pan hacia arriba en Qt), 
                        # en Hiero (Y=0 abajo) significa que vemos la parte superior (Y más alto)
                        # Por eso necesitamos invertir el signo ANTES de escalar por zoom
                        
                        # Escalar el pan por el zoom para convertir a coordenadas de imagen
                        pan_x_image = pan_x_viewer / zoom if zoom > 0 else pan_x_viewer
                        pan_y_image = -pan_y_viewer / zoom if zoom > 0 else -pan_y_viewer  # INVERTIR para convertir de Qt a Hiero
                        
                        if abs(zoom - 1.0) < 0.0001:
                            debug_print(f"   📐 Zoom = 1.0: escalando pan por zoom (factor 1.0)")
                        else:
                            debug_print(f"   📐 Zoom != 1.0 ({zoom:.6f}): escalando pan por zoom")
                        
                        debug_print(f"      Pan X (viewer): {pan_x_viewer:.2f} -> (imagen): {pan_x_image:.2f}")
                        debug_print(f"      Pan Y (viewer): {pan_y_viewer:.2f} -> (imagen INVERTIDO): {pan_y_image:.2f}")
                        
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
                        
                        # Calcular el offset del área visible (esquina inferior izquierda en Hiero: bottom-left)
                        visible_x_offset = visible_center_x - (visible_width_in_image / 2)
                        visible_y_offset = visible_center_y - (visible_height_in_image / 2)
                        
                        # DEBUG: Verificar el cálculo
                        debug_print(f"   🔍 Debug cálculo área visible:")
                        debug_print(f"      Centro imagen Y: {image_center_y:.2f}")
                        debug_print(f"      Pan Y (imagen, ya invertido Qt->Hiero): {pan_y_image:.2f}")
                        debug_print(f"      Centro área visible Y: {visible_center_y:.2f}")
                        debug_print(f"      Alto visible: {visible_height_in_image:.2f}")
                        debug_print(f"      Offset Y calculado: {visible_y_offset:.2f}")
                        debug_print(f"      Bottom calculado: {visible_y_offset + visible_height_in_image:.2f}")
                        
                        debug_print(f"   📐 Conversión a coordenadas de imagen:")
                        debug_print(f"      Centro imagen: ({image_center_x:.2f}, {image_center_y:.2f})")
                        debug_print(f"      Centro área visible: ({visible_center_x:.2f}, {visible_center_y:.2f})")
                        debug_print(f"      Offset X (área visible): {visible_x_offset:.2f}")
                        debug_print(f"      Offset Y (área visible): {visible_y_offset:.2f}")
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
                        
                        debug_print(f"   ⚠️ Usando aproximación centrada como fallback:")
                        debug_print(f"      Offset X: {visible_x_offset:.2f}")
                        debug_print(f"      Offset Y: {visible_y_offset:.2f}")
                    
                    # Actualizar las dimensiones visibles
                    visible_width = visible_width_in_image
                    visible_height = visible_height_in_image
                    
                    # Asegurar que el área visible no exceda las dimensiones de la imagen
                    if visible_width > image_width:
                        visible_width = image_width
                    if visible_height > image_height:
                        visible_height = image_height
                    
                    # Limitar el offset para que el área visible no se salga de la imagen
                    # Pero permitir valores negativos si el área visible es más grande que la imagen
                    if visible_x_offset < 0:
                        visible_x_offset = 0
                    if visible_y_offset < 0:
                        visible_y_offset = 0
                    
                    # Asegurar que el área visible no se salga de la imagen por la derecha/abajo
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
    
    debug_print(f"\n📐 Área visible del viewer:")
    debug_print(f"   Offset X: {visible_x_offset}")
    debug_print(f"   Offset Y: {visible_y_offset}")
    debug_print(f"   Ancho visible: {visible_width}")
    debug_print(f"   Alto visible: {visible_height}")
    
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
            
            debug_print("\n" + "=" * 60)
            debug_print(f"Valores ACTUALES de 'box' para el clip '{CLIP_NAME}':")
            debug_print("=" * 60)
            debug_print(f"x: {x}")
            debug_print(f"y: {y}")
            debug_print(f"r: {r}")
            debug_print(f"t: {t}")
            
            # Calcular dimensiones del box
            box_width = r - x
            box_height = t - y
            box_center_x = (x + r) / 2
            box_center_y = (y + t) / 2
            
            debug_print(f"\n📏 Dimensiones del box:")
            debug_print(f"   Ancho: {box_width}")
            debug_print(f"   Alto: {box_height}")
            debug_print(f"   Centro actual: ({box_center_x}, {box_center_y})")
            
            # Calcular centro del viewer
            viewer_center_x = viewer_width / 2
            viewer_center_y = viewer_height / 2
            
            debug_print(f"\n🎯 Centro del viewer:")
            debug_print(f"   Centro: ({viewer_center_x}, {viewer_center_y})")
            
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
                
                # CORRECCIÓN CRÍTICA: En Hiero/Nuke, Y=0 es el BOTTOM de la imagen, no el TOP
                # Por lo tanto, para alinear al bottom con margen, necesitamos:
                # - El BOTTOM del box (Y) debe estar a BOTTOM_MARGIN del bottom del área visible
                # - El TOP del box (T) debe estar a Y + box_height
                # Alinear al bottom del área visible con margen
                new_y = visible_y_offset + BOTTOM_MARGIN  # Bottom del box a 30px del bottom del área visible
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
            
            debug_print(f"\n📐 Configuración:")
            debug_print(f"   Modo: {'ABSOLUTO' if USE_ABSOLUTE_POSITION else 'RELATIVO'}")
            debug_print(f"   Margen izquierdo: {LEFT_MARGIN}px")
            debug_print(f"   Margen inferior: {BOTTOM_MARGIN}px")
            debug_print(f"   Alineado al bottom: Sí")
            if not USE_ABSOLUTE_POSITION:
                debug_print(f"   Punto cero: pixel más a la izquierda visible ({visible_x_offset})")
                debug_print(f"   Bottom del área visible: {visible_y_offset + visible_height:.2f}")
            debug_print(f"\n📐 Desplazamiento necesario:")
            debug_print(f"   Offset X: {offset_x}")
            debug_print(f"   Offset Y: {offset_y}")
            
            debug_print(f"\n" + "=" * 60)
            debug_print(f"Valores NUEVOS de 'box' (alineado izquierda y bottom):")
            debug_print("=" * 60)
            debug_print(f"x: {new_x}")
            debug_print(f"y: {new_y}")
            debug_print(f"r: {new_r}")
            debug_print(f"t: {new_t}")
            debug_print("=" * 60)
            
            # Verificar que las dimensiones se mantienen
            new_box_width = new_r - new_x
            new_box_height = new_t - new_y
            new_box_center_x = (new_x + new_r) / 2
            new_box_center_y = (new_y + new_t) / 2
            
            debug_print(f"\n✅ Verificación:")
            debug_print(f"   Ancho mantenido: {abs(new_box_width - box_width) < 0.01}")
            debug_print(f"   Alto mantenido: {abs(new_box_height - box_height) < 0.01}")
            debug_print(f"   Nuevo centro: ({new_box_center_x}, {new_box_center_y})")
            if USE_ABSOLUTE_POSITION:
                debug_print(f"   Posición X: {new_x}px desde el borde izquierdo de la imagen (objetivo: {LEFT_MARGIN}px)")
                debug_print(f"   Posición Y (bottom del box): {new_y}px desde el bottom de la imagen (objetivo: {BOTTOM_MARGIN}px)")
                debug_print(f"   Posición T (top del box): {new_t}px")
            else:
                debug_print(f"   Posición X: {new_x}px desde el origen de la imagen ({new_x - visible_x_offset:.2f}px desde el borde visible)")
                debug_print(f"   Posición Y (bottom del box): {new_y}px desde el bottom del área visible (offset: {visible_y_offset}, margen: {BOTTOM_MARGIN}, objetivo: {visible_y_offset + BOTTOM_MARGIN:.2f}px)")
                debug_print(f"   Posición T (top del box): {new_t}px")
            debug_print(f"   Alineado al bottom: {abs(new_y - (visible_y_offset + BOTTOM_MARGIN if not USE_ABSOLUTE_POSITION else BOTTOM_MARGIN)) < 0.01}")
            debug_print(f"   Dentro de límites de imagen: {new_x >= 0 and new_y >= 0 and new_r <= image_width and new_t <= image_height}")
            
            # Aplicar los nuevos valores
            try:
                new_box_value = (new_x, new_y, new_r, new_t)
                node['box'].setValue(new_box_value)
                debug_print(f"\n✅ Box posicionado y actualizado correctamente!")
                debug_print(f"   - Alineado a la izquierda con {LEFT_MARGIN}px de margen")
                debug_print(f"   - Alineado al bottom con {BOTTOM_MARGIN}px de margen")
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

