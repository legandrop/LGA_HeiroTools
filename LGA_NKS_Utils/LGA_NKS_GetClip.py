"""
____________________________________________________________________________________

  LGA_NKS_GetClip v1.1 | Lega Pugliese
  Utilidades para obtener clips del timeline de Hiero/Nuke Studio
  
  Método híbrido recomendado:
  1. Intenta obtener el clip del track especificado en la posición del playhead
  2. Si no encuentra, usa el clip seleccionado como fallback
  
  Scripts que utilizan este módulo:
  - LGA_NKS_Flow_ShowInFlow.py
  - (otros scripts que necesiten obtener clips)

  v1.1 - Agrega get_clips_to_process para obtener múltiples clips seleccionados en el track EXR
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


def get_selected_clips_in_track(seq, track_name=None):
    """
    Obtiene todos los clips seleccionados que pertenecen al track especificado.
    
    Args:
        seq: Secuencia activa de Hiero
        track_name (str, optional): Nombre del track. Si es None, usa DEFAULT_TRACK_NAME.
    
    Returns:
        Lista de clips seleccionados en el track especificado (excluyendo efectos) o lista vacía.
    """
    if track_name is None:
        track_name = DEFAULT_TRACK_NAME
    
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection() if te else []
    
    # Encontrar el track especificado
    target_track = None
    for track in seq.videoTracks():
        if track.name().upper() == track_name.upper():
            target_track = track
            break
    
    if not target_track:
        debug_print(f"No se encontró el track '{track_name}' en la secuencia.")
        return []
    
    # Filtrar clips seleccionados que pertenecen al track especificado
    clips_in_track = []
    for clip in selected_clips:
        if isinstance(clip, hiero.core.EffectTrackItem):
            continue
        # Verificar si el clip pertenece al track especificado
        if clip.parentTrack() == target_track:
            clips_in_track.append(clip)
    
    return clips_in_track


def get_clip_to_process(track_name=None, prioritize_multiple_selection=False):
    """
    Obtiene el clip a procesar usando el método híbrido:
    1. Si prioritize_multiple_selection=True y hay múltiples clips seleccionados en el track, devuelve lista
    2. Si no, primero intenta obtener el clip del track especificado en la posición del playhead
    3. Si no encuentra, usa el primer clip seleccionado como fallback
    
    Debe ejecutarse en el hilo principal de Hiero.
    
    Args:
        track_name (str, optional): Nombre del track a buscar. Si es None, usa DEFAULT_TRACK_NAME.
        prioritize_multiple_selection (bool): Si True y hay múltiples clips seleccionados en el track,
            devuelve lista de esos clips en lugar de usar playhead. Si False, usa playhead primero.
    
    Returns:
        Clip encontrado, lista de clips, o None si no se encuentra ningún clip.
        Si prioritize_multiple_selection=True y hay múltiples clips, siempre devuelve lista.
    """
    if track_name is None:
        track_name = DEFAULT_TRACK_NAME
    
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No se encontro una secuencia activa en Hiero.")
        return None

    # Si prioritize_multiple_selection=True, verificar primero si hay múltiples clips seleccionados en el track
    if prioritize_multiple_selection:
        selected_clips_in_track = get_selected_clips_in_track(seq, track_name=track_name)
        if len(selected_clips_in_track) > 1:
            debug_print(
                f">>> Múltiples clips seleccionados en track '{track_name}' ({len(selected_clips_in_track)} clips). Priorizando selección sobre playhead."
            )
            return selected_clips_in_track
        elif len(selected_clips_in_track) == 1:
            debug_print(
                f">>> Un solo clip seleccionado en track '{track_name}'. Usando playhead primero."
            )
        # Si no hay clips seleccionados en el track, continuar con lógica normal

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


def get_clips_to_process(track_name=None, prioritize_multiple_selection=False):
    """
    Obtiene los clips a procesar usando el método híbrido.
    Siempre devuelve una lista (puede contener 0, 1 o más clips).
    
    Args:
        track_name (str, optional): Nombre del track a buscar. Si es None, usa DEFAULT_TRACK_NAME.
        prioritize_multiple_selection (bool): Si True y hay múltiples clips seleccionados en el track,
            prioriza esos clips sobre el playhead.
    
    Returns:
        Lista de clips encontrados (puede estar vacía).
    """
    result = get_clip_to_process(track_name=track_name, prioritize_multiple_selection=prioritize_multiple_selection)
    
    # Si el resultado es una lista, devolverla directamente
    if isinstance(result, list):
        return result
    
    # Si es un clip único, devolverlo en una lista
    if result is not None:
        return [result]
    
    # Si es None, devolver lista vacía
    return []


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

