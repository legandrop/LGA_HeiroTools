"""
______________________________________________________

  LGA_NKS_FrameNumber v0.51 | Lega
  Busca el clip 'Frame_Only' en el track 'BurnIn' y posiciona el box
  alineado a la izquierda con 30px de margen y centrado verticalmente
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
        debug_print(f"   Imagen del viewer: {qimage.width()} × {qimage.height()}")
    else:
        debug_print("⚠️ No se pudo obtener la imagen del viewer")
    
    # Obtener formato de la secuencia (ya tenemos seq desde el inicio)
    format_obj = seq.format()
    viewer_width = format_obj.width()
    viewer_height = format_obj.height()
    
    debug_print(f"\n📐 Información de la secuencia:")
    debug_print(f"   Formato de la secuencia: {viewer_width} × {viewer_height}")
    debug_print(f"   Centro del viewer: ({viewer_width/2}, {viewer_height/2})")
    
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
            
            # Configuración: alineado a la izquierda con 30px del borde, centrado en Y
            LEFT_MARGIN = 30
            
            # Calcular nuevos valores:
            # X: alineado a la izquierda con margen de 30px
            # Y: centrado verticalmente
            new_x = LEFT_MARGIN
            new_r = new_x + box_width  # Mantener el ancho
            
            # Centrar verticalmente: el centro Y del box debe estar en el centro Y del viewer
            new_box_center_y = viewer_center_y
            new_y = new_box_center_y - (box_height / 2)
            new_t = new_box_center_y + (box_height / 2)
            
            # Calcular desplazamiento para información de debug
            offset_x = new_x - x
            offset_y = new_y - y
            
            debug_print(f"\n📐 Configuración:")
            debug_print(f"   Margen izquierdo: {LEFT_MARGIN}px")
            debug_print(f"   Centrado verticalmente: Sí")
            debug_print(f"\n📐 Desplazamiento necesario:")
            debug_print(f"   Offset X: {offset_x}")
            debug_print(f"   Offset Y: {offset_y}")
            
            debug_print(f"\n" + "=" * 60)
            debug_print(f"Valores NUEVOS de 'box' (alineado izquierda, centrado Y):")
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
            debug_print(f"   Posición X: {new_x}px desde el borde izquierdo (objetivo: {LEFT_MARGIN}px)")
            debug_print(f"   Centrado verticalmente: {abs(new_box_center_y - viewer_center_y) < 0.01}")
            
            # Aplicar los nuevos valores
            try:
                new_box_value = (new_x, new_y, new_r, new_t)
                node['box'].setValue(new_box_value)
                debug_print(f"\n✅ Box posicionado y actualizado correctamente!")
                debug_print(f"   - Alineado a la izquierda con {LEFT_MARGIN}px de margen")
                debug_print(f"   - Centrado verticalmente en Y")
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

