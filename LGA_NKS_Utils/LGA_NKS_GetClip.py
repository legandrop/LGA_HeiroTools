"""
____________________________________________________________________________________

  LGA_NKS_GetClip v1.6 | Lega
  Utilidades para obtener clips del timeline de Hiero/Nuke Studio

  Método híbrido inteligente recomendado:
  1. LÓGICA INTELIGENTE: Si hay un clip seleccionado fuera del track objetivo pero del mismo shot,
     automáticamente usa el clip del track correcto (sin mostrar mensaje al usuario)
  2. Muestra advertencia solo cuando la lógica inteligente NO puede resolver automáticamente
  3. Intenta obtener el clip del track especificado en la posición del playhead
  4. Si no encuentra, usa el clip seleccionado como fallback

  v1.6 - LÓGICA INTELIGENTE MEJORADA: Ahora resuelve automáticamente selecciones erróneas
         sin mostrar mensaje informativo al usuario. La advertencia solo aparece cuando
         NO puede resolverse automáticamente. Función específica extract_shot_code_from_filename
         para evitar interferir con otros scripts.
  v1.5 - LÓGICA INTELIGENTE: Comparación automática de shots para selecciones simples.
         Si hay un clip seleccionado fuera del track objetivo pero del mismo shot,
         automáticamente usa el clip del track correcto
  v1.4 - Agrega advertencia automática cuando hay clips seleccionados en tracks que no son el objetivo
  v1.3 - Renombra variables: DEFAULT_TRACK_NAME → TRACK_comp_EXR, DEFAULT_REV_TRACK_NAME → TRACK_comp_REV
  v1.2 - Agrega DEFAULT_REV_TRACK_NAME para centralizar el nombre del track REV
  v1.1 - Agrega get_clips_to_process para obtener múltiples clips seleccionados en el track
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui

# Control interno del debug para este módulo (no se puede sobrescribir desde fuera)
_GETCLIP_DEBUG_ENABLED = True


def debug_print(*message):
    """Función para imprimir mensajes de debug del módulo GetClip."""
    if _GETCLIP_DEBUG_ENABLED:
        print("[GetClip]", *message)


# Variable configurable para el nombre del track por defecto
TRACK_comp_EXR = "_comp_"  # Es el track que contiene a los EXR con el render de COMP

# Variable configurable para el nombre del track REV por defecto
TRACK_comp_REV = "_rev_"  # Es el track que contiene a los MOV o MXF con el render de COMP

# Intentar importar funciones de naming para comparación inteligente de shots
try:
    from LGA_NKS_Flow_NamingUtils import extract_shot_code, clean_base_name, detect_shotname_format
    NAMING_UTILS_AVAILABLE = True
    debug_print("NamingUtils importado correctamente")
except ImportError as e:
    NAMING_UTILS_AVAILABLE = False
    debug_print(f"NamingUtils NO importado, usando fallback: {e}")
    def extract_shot_code(base_name):
        """Fallback básico si no hay módulo naming"""
        parts = base_name.split("_")
        return "_".join(parts[:3]) if len(parts) >= 3 else base_name

    def clean_base_name(file_name):
        """Fallback básico si no hay módulo naming"""
        import os
        return os.path.splitext(file_name)[0]

    def detect_shotname_format(base_name):
        """Fallback básico si no hay módulo naming"""
        parts = base_name.split("_")
        if len(parts) >= 5:
            field_5 = parts[4]
            return not (field_5.startswith('v') and field_5[1:].isdigit())
        return False


def extract_shot_code_from_filename(file_path):
    """
    Función específica para GetClip: extrae shot code de un filename completo (con ruta).
    Usa NamingUtils pero maneja correctamente filenames con rutas completas.

    Args:
        file_path (str): Ruta completa del archivo

    Returns:
        str: Shot code extraído o cadena vacía si error
    """
    if not file_path or not NAMING_UTILS_AVAILABLE:
        return ""

    try:
        # Limpiar el filename: remover ruta, extensión, versión
        import os
        filename_only = os.path.basename(file_path)  # Solo nombre del archivo sin ruta

        # Remover extensión de secuencia EXR y versión
        import re
        clean_name = re.sub(r"_%04d\.exr$", "", filename_only)
        clean_name = re.sub(r"_\d{4}\.exr$", "", clean_name)
        clean_name = re.sub(r"_v\d+$", "", clean_name)
        clean_name = os.path.splitext(clean_name)[0]

        debug_print(f"[GetClip] Filename limpio para shot code: {clean_name}")

        # Extraer shot code usando NamingUtils
        shot_code = extract_shot_code(clean_name)
        debug_print(f"[GetClip] Shot code extraído: {shot_code}")

        return shot_code

    except Exception as e:
        debug_print(f"[GetClip] Error extrayendo shot code de {file_path}: {e}")
        return ""


def extract_shot_code_from_clip(clip):
    """
    Extrae el shot code de un clip usando función específica de GetClip.
    Maneja errores gracefully si no hay media o el archivo no existe.

    Args:
        clip: Clip de Hiero

    Returns:
        str: Shot code extraído o cadena vacía si hay error
    """
    try:
        if not clip or not clip.source() or not clip.source().mediaSource():
            debug_print(f"[GetClip] Clip '{clip.name() if clip else 'None'}' no tiene source o mediaSource")
            return ""

        fileinfos = clip.source().mediaSource().fileinfos()
        if not fileinfos:
            debug_print(f"[GetClip] Clip '{clip.name()}' no tiene fileinfos")
            return ""

        filename = fileinfos[0].filename()
        debug_print(f"[GetClip] Procesando filename: {filename}")

        # Usar función específica de GetClip que maneja rutas completas correctamente
        shot_code = extract_shot_code_from_filename(filename)

        return shot_code

    except Exception as e:
        debug_print(f"[GetClip] Error extrayendo shot code del clip '{clip.name() if clip else 'None'}': {e}")
        return ""


def find_clip_at_playhead_in_track(seq, track_name=None):
    """
    Busca el clip en un track dado que coincide con la posicion del playhead.
    Evita efectos y devuelve el primer clip que cumpla la condicion o None.
    
    Args:
        seq: Secuencia activa de Hiero
        track_name (str, optional): Nombre del track a buscar. Si es None, usa TRACK_comp_EXR.
    
    Returns:
        Clip encontrado o None si no se encuentra.
    """
    if track_name is None:
        track_name = TRACK_comp_EXR
    
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
        track_name (str, optional): Nombre del track. Si es None, usa TRACK_comp_EXR.
    
    Returns:
        Lista de clips seleccionados en el track especificado (excluyendo efectos) o lista vacía.
    """
    if track_name is None:
        track_name = TRACK_comp_EXR
    
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
    Obtiene el clip a procesar usando el método híbrido inteligente:
    1. LÓGICA INTELIGENTE: Si hay un clip seleccionado fuera del track objetivo pero del mismo shot,
       automáticamente usa el clip del track correcto (sin mensaje informativo al usuario)
    2. Muestra advertencia automática SOLO cuando la lógica inteligente NO puede resolver automáticamente
    3. Si prioritize_multiple_selection=True y hay múltiples clips seleccionados en el track, devuelve lista
    4. Si no, primero intenta obtener el clip del track especificado en la posición del playhead
    5. Si no encuentra, usa el primer clip seleccionado como fallback

    Debe ejecutarse en el hilo principal de Hiero.

    Args:
        track_name (str, optional): Nombre del track a buscar. Si es None, usa TRACK_comp_EXR.
        prioritize_multiple_selection (bool): Si True y hay múltiples clips seleccionados en el track,
            devuelve lista de esos clips en lugar de usar playhead. Si False, usa playhead primero.

    Returns:
        Clip encontrado, lista de clips, o None si no se encuentra ningún clip.
        Si prioritize_multiple_selection=True y hay múltiples clips, siempre devuelve lista.
    """
    if track_name is None:
        track_name = TRACK_comp_EXR
    
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("No se encontro una secuencia activa en Hiero.")
        return None

    # Obtener información de selección
    all_selected_clips = get_selected_clips()
    selected_clips_in_track = get_selected_clips_in_track(seq, track_name=track_name)

    # LÓGICA INTELIGENTE PARA SELECCIONES:
    # Si hay un solo clip seleccionado que NO es del track objetivo, verificar si es del mismo shot
    # (se aplica tanto para prioritize_multiple_selection=True como False)
    intelligent_selection_applied = False
    if len(selected_clips_in_track) == 0 and len(all_selected_clips) == 1:
        debug_print("Activando lógica inteligente: un clip seleccionado fuera del track objetivo")
        selected_clip = all_selected_clips[0]

        # Obtener clip del playhead en el track objetivo
        playhead_clip = find_clip_at_playhead_in_track(seq, track_name=track_name)

        if playhead_clip:
            # Comparar shot codes
            selected_shot = extract_shot_code_from_clip(selected_clip)
            playhead_shot = extract_shot_code_from_clip(playhead_clip)

            debug_print(f"Comparando shots - seleccionado: '{selected_shot}', playhead: '{playhead_shot}'")

            if selected_shot and playhead_shot and selected_shot == playhead_shot:
                # 2a: Los shots coinciden, usar el clip del track correcto automáticamente
                debug_print(f"Shots coinciden ({selected_shot}). Usando clip del track '{track_name}' automáticamente.")
                intelligent_selection_applied = True
                if prioritize_multiple_selection:
                    return [playhead_clip]  # Devolver como lista
                else:
                    return playhead_clip
            else:
                # 2c: Los shots no coinciden, mostrar mensaje informativo
                debug_print(f"Shots diferentes - seleccionado: {selected_shot}, playhead: {playhead_shot}")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.warning(
                    None,
                    "Shots diferentes",
                    f"El clip seleccionado pertenece al shot '{selected_shot}',\n"
                    f"pero el playhead está posicionado sobre el shot '{playhead_shot}' en el track '{track_name}'.\n\n"
                    f"Se usará el clip del track '{track_name}' (playhead)."
                )
                if prioritize_multiple_selection:
                    return [playhead_clip]  # Devolver como lista
                else:
                    return playhead_clip

        # 2b: No hay clip en playhead del track objetivo, usar el seleccionado como fallback
        debug_print(f"No hay clip en playhead del track '{track_name}', usando clip seleccionado como fallback.")
        intelligent_selection_applied = True  # También cuenta como selección inteligente
        if prioritize_multiple_selection:
            return [selected_clip]  # Devolver como lista
        else:
            return selected_clip

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
        selected_clip = all_selected_clips[0]
        debug_print(f"Solo un clip seleccionado fuera del track '{track_name}': {selected_clip.name()}")

        # Obtener clip del playhead en el track objetivo
        playhead_clip = find_clip_at_playhead_in_track(seq, track_name=track_name)

        if playhead_clip:
            # Comparar shot codes
            selected_shot = extract_shot_code_from_clip(selected_clip)
            playhead_shot = extract_shot_code_from_clip(playhead_clip)

            if selected_shot and playhead_shot and selected_shot == playhead_shot:
                # 2a: Los shots coinciden, usar el clip del track correcto automáticamente
                debug_print(f"Shots coinciden ({selected_shot}). Usando clip del track '{track_name}' en lugar del seleccionado.")
                intelligent_selection_applied = True
                if prioritize_multiple_selection:
                    return [playhead_clip]  # Devolver como lista
                else:
                    return playhead_clip
            else:
                # 2c: Los shots no coinciden, mostrar mensaje informativo
                debug_print(f"Shots diferentes - seleccionado: {selected_shot}, playhead: {playhead_shot}")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.warning(
                    None,
                    "Shots diferentes",
                    f"El clip seleccionado pertenece al shot '{selected_shot}',\n"
                    f"pero el playhead está posicionado sobre el shot '{playhead_shot}' en el track '{track_name}'.\n\n"
                    f"Se usará el clip del track '{track_name}' (playhead)."
                )
                intelligent_selection_applied = True  # También resuelve automáticamente
                if prioritize_multiple_selection:
                    return [playhead_clip]  # Devolver como lista
                else:
                    return playhead_clip

        # 2b: No hay clip en playhead del track objetivo, usar el seleccionado como fallback
        debug_print(f"No hay clip en playhead del track '{track_name}', usando clip seleccionado como fallback.")
        intelligent_selection_applied = True  # También cuenta como selección inteligente
        if prioritize_multiple_selection:
            return [selected_clip]  # Devolver como lista
        else:
            return selected_clip

    # Verificar si hay clips seleccionados en otros tracks y mostrar advertencia
    # (solo si la lógica inteligente no resolvió el problema automáticamente)
    if not intelligent_selection_applied and len(all_selected_clips) > len(selected_clips_in_track):
        clips_in_other_tracks = len(all_selected_clips) - len(selected_clips_in_track)
        from PySide2.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Selección filtrada por track",
            f"Se detectaron {clips_in_other_tracks} clip(s) seleccionado(s) en tracks que no son '{track_name}'.\n\n"
            f"Solo se procesarán los clips seleccionados en el track '{track_name}'."
        )

    # Intentar obtener clip por playhead en el track especificado (lógica normal)
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
    Obtiene los clips a procesar usando el método híbrido inteligente.
    Siempre devuelve una lista (puede contener 0, 1 o más clips).

    Args:
        track_name (str, optional): Nombre del track a buscar. Si es None, usa TRACK_comp_EXR.
        prioritize_multiple_selection (bool): Si True y hay múltiples clips seleccionados en el track,
            prioriza esos clips sobre el playhead.

    Returns:
        Lista de clips encontrados (puede estar vacía).
    """
    debug_print(f"get_clips_to_process llamado con track_name={track_name}, prioritize_multiple_selection={prioritize_multiple_selection}")
    result = get_clip_to_process(track_name=track_name, prioritize_multiple_selection=prioritize_multiple_selection)

    # Si el resultado es una lista, devolverla directamente
    if isinstance(result, list):
        debug_print(f"Resultado es lista con {len(result)} clips")
        return result

    # Si es un clip único, devolverlo en una lista
    if result is not None:
        debug_print(f"Resultado es un clip único: {result.name() if hasattr(result, 'name') else result}")
        return [result]

    # Si es None, devolver lista vacía
    debug_print("Resultado es None, devolviendo lista vacía")
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
