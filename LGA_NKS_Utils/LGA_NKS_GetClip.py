"""
____________________________________________________________________________________

  LGA_NKS_GetClip v1.0 | Lega Pugliese
  Utilidades para obtener clips del timeline de Hiero/Nuke Studio
  
  Método híbrido recomendado:
  1. Intenta obtener el clip del track especificado en la posición del playhead
  2. Si no encuentra, usa el clip seleccionado como fallback
  
  Scripts que utilizan este módulo:
  - LGA_NKS_Flow_ShowInFlow.py
  - (otros scripts que necesiten obtener clips)
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui

# Variable global para controlar el debug
DEBUG = False  # Poner en True para activar los mensajes de debug

# Variable configurable para el nombre del track por defecto
DEFAULT_TRACK_NAME = "EXR"  # Puede cambiarse según el workflow


def debug_print(*message):
    """Función para imprimir mensajes de debug."""
    if DEBUG:
        print(*message)


def find_clip_at_playhead_in_track(seq, track_name=None):
    """
    Busca el clip en un track dado que coincide con la posicion del playhead.
    Evita efectos y devuelve el primer clip que cumpla la condicion o None.
    
    Args:
        seq: Secuencia activa de Hiero
        track_name (str, optional): Nombre del track a buscar. Si es None, usa DEFAULT_TRACK_NAME.
    
    Returns:
        Clip encontrado o None si no se encuentra.
    """
    if track_name is None:
        track_name = DEFAULT_TRACK_NAME
    
    try:
        viewer = hiero.ui.currentViewer()
        if not viewer:
            debug_print("No se encontró un viewer activo.")
            return None
        
        current_time = viewer.time()
        debug_print(f"Buscando clip en track '{track_name}' en posición {current_time}")
        
        for track in seq.videoTracks():
            if track.name().upper() == track_name.upper():
                for clip in track:
                    if isinstance(clip, hiero.core.EffectTrackItem):
                        continue
                    if clip.timelineIn() <= current_time < clip.timelineOut():
                        debug_print(
                            f">>> Clip encontrado en track {track_name} en posicion {current_time}: {clip.name()}"
                        )
                        return clip
                debug_print(f"No se encontró clip en track '{track_name}' en la posición del playhead.")
                return None
        
        debug_print(f"No se encontró el track '{track_name}' en la secuencia.")
        return None
        
    except Exception as e:
        debug_print(f"Error buscando clip por playhead en track {track_name}: {e}")
        return None


def get_clip_to_process(track_name=None):
    """
    Obtiene el clip a procesar usando el método híbrido:
    1. Primero intenta obtener el clip del track especificado en la posición del playhead
    2. Si no encuentra, usa el primer clip seleccionado como fallback
    
    Debe ejecutarse en el hilo principal de Hiero.
    
    Args:
        track_name (str, optional): Nombre del track a buscar. Si es None, usa DEFAULT_TRACK_NAME.
    
    Returns:
        Clip encontrado o None si no se encuentra ningún clip.
    """
    if track_name is None:
        track_name = DEFAULT_TRACK_NAME
    
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No se encontro una secuencia activa en Hiero.")
        return None

    # Intentar obtener clip por playhead en el track especificado
    playhead_clip = find_clip_at_playhead_in_track(seq, track_name=track_name)

    # Fallback a seleccion
    if not playhead_clip:
        te = hiero.ui.getTimelineEditor(seq)
        selected_clips = te.selection() if te else []
        if selected_clips:
            # Tomar el primer clip seleccionado que no sea un efecto
            for clip in selected_clips:
                if not isinstance(clip, hiero.core.EffectTrackItem):
                    debug_print(
                        f">>> No hay clip en playhead sobre track '{track_name}'; usando clip seleccionado como fallback: {clip.name()}"
                    )
                    return clip
        debug_print("No se encontró clip en playhead ni clips seleccionados.")
    else:
        debug_print(
            f">>> Usando clip del playhead en track '{track_name}': {playhead_clip.name()}"
        )

    return playhead_clip


def get_selected_clips():
    """
    Obtiene todos los clips seleccionados en el timeline.
    
    Returns:
        Lista de clips seleccionados (excluyendo efectos) o lista vacía.
    """
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No se encontro una secuencia activa en Hiero.")
        return []
    
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection() if te else []
    
    # Filtrar efectos
    valid_clips = [
        clip for clip in selected_clips 
        if not isinstance(clip, hiero.core.EffectTrackItem)
    ]
    
    return valid_clips

