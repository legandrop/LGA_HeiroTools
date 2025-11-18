"""
______________________________________________________

  LGA_NKS_FrameNumber_Create v0.2 | Lega
  Script para crear el soft effect 'Frame_Only' en el track 'BurnIn'
  con todas las propiedades capturadas de un efecto existente.
  
  Este script puede ejecutarse de forma independiente para pruebas,
  pero está diseñado para ser usado como función auxiliar desde
  el script maestro LGA_NKS_FrameNumber.py

______________________________________________________

"""

import hiero.core
import hiero.ui
import nuke

# ============================
# Configuración
# ============================

TRACK_NAME = "BurnIn"
EFFECT_NAME = "Frame_Only"
DEBUG = True

# ============================
# Funciones Auxiliares
# ============================

def debug_print(*message):
    if DEBUG:
        print(*message)

def safe_set_knob(node, knob_name, value):
    """Intenta establecer un valor de knob de forma segura."""
    try:
        if knob_name not in node.knobs():
            debug_print(f"  ⚠️ Knob '{knob_name}' no existe en el nodo, saltando...")
            return False
        
        knob = node[knob_name]
        
        # Manejar el knob 'font' de forma especial (FreeType_Knob)
        if knob_name == 'font':
            # El font knob es un FreeType_Knob que requiere setValue(nombre_fuente, estilo)
            # Según la exploración: getValue() retorna ['Arial', 'Regular']
            # y setValue() requiere exactamente 2 argumentos: nombre y estilo
            try:
                font_name = 'Arial'
                font_style = 'Regular'  # Estilo por defecto para Arial
                
                # Usar setValue con nombre y estilo
                knob.setValue(font_name, font_style)
                debug_print(f"  ✅ Font configurado: '{font_name}' estilo '{font_style}'")
                
                # Verificar que se configuró correctamente
                try:
                    current_font = knob.getValue()
                    if isinstance(current_font, list) and len(current_font) >= 2:
                        debug_print(f"  ✅ Verificación: getValue() = {current_font}")
                except:
                    pass
                
                return True
            except Exception as e:
                debug_print(f"  ⚠️ Error configurando knob 'font': {e}")
                debug_print(f"     Intentando método alternativo...")
                
                # Método alternativo: intentar obtener el valor actual y usar ese estilo
                try:
                    current_value = knob.getValue()
                    if isinstance(current_value, list) and len(current_value) >= 2:
                        # Usar el estilo actual pero cambiar solo el nombre
                        knob.setValue(font_name, current_value[1])
                        debug_print(f"  ✅ Font configurado usando estilo existente: '{font_name}' estilo '{current_value[1]}'")
                        return True
                except:
                    pass
                
                debug_print(f"  ❌ No se pudo configurar el font '{font_name}'")
                return False
        
        # Manejar diferentes tipos de valores para otros knobs
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                knob.setValue(value)
        elif value is not None:
            knob.setValue(value)
        
        return True
    except Exception as e:
        debug_print(f"  ⚠️ Error estableciendo '{knob_name}': {e}")
        return False

def get_track_duration_from_other_effects(track):
    """
    Obtiene la duración (timeline_in, timeline_out) basándose en otros
    soft effects en el track. Retorna (timeline_in, timeline_out) o None.
    """
    items = track.subTrackItems()
    if not items:
        return None
    
    for item in items:
        effect_item = item[0]
        if isinstance(effect_item, hiero.core.EffectTrackItem):
            try:
                timeline_in = effect_item.timelineIn()
                timeline_out = effect_item.timelineOut()
                if timeline_in is not None and timeline_out is not None:
                    debug_print(f"  📏 Duración obtenida de '{effect_item.name()}': In={timeline_in}, Out={timeline_out}")
                    return (timeline_in, timeline_out)
            except:
                continue
    
    return None

# ============================
# Propiedades del Efecto (Capturadas de la exploración)
# ============================

# Propiedades principales del nodo Text2
EFFECT_PROPERTIES = {
    # Texto y mensaje
    'message': 'Frame: [metadata input/frame]',
    # Box aumentado 100px de ancho para mejor compatibilidad
    # Formato: (x1, y1, x2, y2) - aumentamos x2 (derecha) en 100px
    'box': (280.5599795074472, 372.4884323840888, 867.5303935074476, 436.68261568408855),
    'xjustify': 'left',
    'yjustify': 'top',
    
    # Fuente
    'font': 'Arial',
    'font_size': 91.0,
    'font_width': 97.0,
    'font_height': 85.0,
    'global_font_scale': 0.9,
    'kerning': 0.0,
    'tracking': 0.0,
    'baseline_shift': 0.0,
    'leading': 0.0,
    
    # Color del texto
    'color': [1.0, 0.7991074323654175, 0.0, 1.0],  # Amarillo/naranja
    
    # Fondo
    'enable_background': True,
    'background_color': [0.0, 0.0, 0.0, 1.0],  # Negro
    'background_opacity': 0.94,
    'background_border_x': 10.0,
    'background_border_y': 5.0,
    
    # Sombras
    'enable_shadows': True,
    'shadow_color': [0.0, 0.0, 0.0, 1.0],  # Negro
    'shadow_opacity': 1.0,
    'shadow_angle': 270.0,
    'shadow_distance': 1.0,
    'shadow_softness': 0.0,
    'shadow_size': 1.0,
    'shadow_inherit_input_color': False,
    
    # Transformaciones
    'translate': (0.0, 0.0),
    'rotate': 0.0,
    'scale': [1.0, 1.0],
    'center': (0.0, 0.0),
    'invert_matrix': False,
    
    # Canales y mezcla
    'output': 'rgba',
    'channel': 'rgba',
    'premult': 'none',
    'cliptype': 'format',
    'replace': False,
    'invert': False,
    'opacity': 1.0,
    'mix': 1.0,
    'enable': 1.0,
    
    # Lifetime (se configurará según la duración del track)
    'useLifetime': True,
}

# ============================
# Función Principal
# ============================

def create_frame_only_effect(seq=None, track=None):
    """
    Crea el soft effect 'Frame_Only' en el track 'BurnIn' con todas las propiedades.
    
    Args:
        seq: Secuencia activa (opcional, se obtiene automáticamente si no se proporciona)
        track: Track objetivo (opcional, se busca automáticamente si no se proporciona)
    
    Returns:
        EffectTrackItem creado o None si falla
    """
    debug_print("=" * 80)
    debug_print("🔧 CREACIÓN DEL SOFT EFFECT 'Frame_Only'")
    debug_print("=" * 80)
    
    # Obtener secuencia si no se proporciona
    if not seq:
        seq = hiero.ui.activeSequence()
        if not seq:
            debug_print("❌ No se encontró una secuencia activa.")
            return None
    
    # Buscar el track si no se proporciona
    if not track:
        for t in seq.videoTracks():
            if t.name() == TRACK_NAME:
                track = t
                break
    
    if not track:
        debug_print(f"❌ No se encontró el track '{TRACK_NAME}'.")
        return None
    
    debug_print(f"✅ Track '{TRACK_NAME}' encontrado.")
    
    # Verificar si el soft effect ya existe
    # Buscar en subTrackItems (soft effects)
    items = track.subTrackItems()
    if items:
        for item in items:
            # Cada item es una tupla/lista, tomar el primer elemento
            effect_item = item[0] if isinstance(item, (tuple, list)) else item
            if isinstance(effect_item, hiero.core.EffectTrackItem):
                try:
                    if effect_item.name() == EFFECT_NAME:
                        debug_print(f"ℹ️ El soft effect '{EFFECT_NAME}' ya existe en el track.")
                        return effect_item
                except:
                    continue
    
    # Obtener duración de otros soft effects en el track
    duration_info = get_track_duration_from_other_effects(track)
    if not duration_info:
        debug_print("⚠️ No se encontraron otros soft effects para obtener la duración.")
        debug_print("   Usando duración por defecto: In=0, Out=461")
        timeline_in = 0
        timeline_out = 461
    else:
        timeline_in, timeline_out = duration_info
        debug_print(f"✅ Duración configurada: In={timeline_in}, Out={timeline_out}")
    
    # Nota: Ya no creamos el nodo aquí porque createEffect() lo crea automáticamente
    # El nodo se creará dentro de createEffect() usando effectType o cloneFrom
    
    # Agregar el efecto al track usando createEffect()
    debug_print(f"\n🔗 Agregando nodo como soft effect al track...")
    try:
        project = seq.project()
        
        # Usar undo para operaciones seguras
        if project:
            project.beginUndo(f"Create {EFFECT_NAME} effect")
        
        try:
            # Usar track.createEffect() que es el método correcto según la exploración
            # createEffect requiere effectType, cloneFrom o copyFrom (no acepta nodo directamente)
            # IMPORTANTE: Siempre crear un efecto NUEVO, NO clonar otros efectos existentes
            if hasattr(track, 'createEffect'):
                try:
                    debug_print(f"🔧 Creando nuevo efecto usando track.createEffect()...")
                    
                    # Crear nuevo efecto usando effectType (NO clonar)
                    # Esto crea un efecto completamente nuevo e independiente
                    effect_item = track.createEffect(
                        effectType='Text2',
                        timelineIn=timeline_in,
                        timelineOut=timeline_out
                    )
                    debug_print(f"✅ Soft effect creado usando effectType='Text2'")
                    
                    if not effect_item:
                        raise Exception("createEffect() retornó None")
                    
                    # Configurar nombre del efecto
                    effect_item.setName(EFFECT_NAME)
                    
                    # Obtener el nodo y configurar todas las propiedades
                    effect_node = effect_item.node()
                    if not effect_node:
                        raise Exception("No se pudo obtener el nodo del efecto creado")
                    
                    effect_node['name'].setValue(EFFECT_NAME)
                    
                    # Configurar todas las propiedades
                    debug_print(f"⚙️ Configurando propiedades del efecto creado...")
                    configured_count = 0
                    skipped_count = 0
                    for knob_name, value in EFFECT_PROPERTIES.items():
                        if safe_set_knob(effect_node, knob_name, value):
                            configured_count += 1
                        else:
                            skipped_count += 1
                    debug_print(f"✅ Propiedades configuradas: {configured_count} exitosas, {skipped_count} omitidas")
                    
                    # Configurar lifetime
                    try:
                        effect_node['lifetimeStart'].setValue(float(timeline_in))
                        effect_node['lifetimeEnd'].setValue(float(timeline_out))
                        effect_node['useLifetime'].setValue(True)
                        debug_print(f"✅ Lifetime configurado: {timeline_in} - {timeline_out}")
                    except Exception as e:
                        debug_print(f"⚠️ Error configurando lifetime: {e}")
                    
                    debug_print(f"✅ Soft effect '{EFFECT_NAME}' creado y configurado exitosamente")
                    if project:
                        project.endUndo()
                    return effect_item
                        
                except Exception as e:
                    debug_print(f"❌ Error usando track.createEffect(): {e}")
                    import traceback
                    debug_print(traceback.format_exc())
                    raise
            
            # Fallback: Si createEffect no está disponible
            debug_print(f"❌ track.createEffect() no está disponible")
            debug_print(f"   Timeline requerido: {timeline_in} - {timeline_out}")
            debug_print(f"   NOTA: Puede ser necesario crear el efecto manualmente desde la UI")
            
            if project:
                project.endUndo()
            
            return None
            
        except Exception as e:
            if project:
                project.endUndo()
            raise e
        
    except Exception as e:
        debug_print(f"❌ Error agregando el efecto al track: {e}")
        import traceback
        debug_print(traceback.format_exc())
        # Intentar hacer undo si hay un proyecto activo
        try:
            project = seq.project()
            if project:
                project.endUndo()
        except:
            pass
        return None

# ============================
# Función para ejecución independiente
# ============================

def main():
    """Función principal para ejecución independiente del script."""
    result = create_frame_only_effect()
    if result:
        debug_print("\n✅ Script completado exitosamente.")
        debug_print(f"   Soft effect '{EFFECT_NAME}' creado en track '{TRACK_NAME}'")
    else:
        debug_print("\n❌ Script completado con errores.")

# Ejecutar si se llama directamente
if __name__ == "__main__":
    main()

