"""
______________________________________________________________________

  LGA_NKS_Reconnect v1.17 | Lega
  Reconecta clips seleccionados a diferentes rutas, manteniendo el color original.

  v1.17: Fix en búsqueda de versiones superiores - corrige cálculo de prefijo
         (eliminaba doble guion bajo) y elimina completamente el límite de versiones
         para permitir detección de versiones con saltos grandes (ej. v16 -> v037).
  v1.16: Detecta media en versiones superiores buscando cualquier archivo *.exr
         en la carpeta, sin importar el nombre exacto (fix para versiones con
         nombres ajustados).
  v1.15: Escanea el publish para hallar la versión más alta con media,
         incluso si la base no existe (ej. salta de v00 a v005).
  v1.14: Maneja media de archivo único (mov, etc.) y sigue eligiendo
         la versión más alta con media; evita relinks si ya está en Mac.
  v1.13: Si el clip está offline y no se lee color,
         colorea por nombre de pista: "*plate*" -> 42616d, "*ref*" -> aa9e54.
  v1.12: Elige siempre la versión más alta disponible con media al relinkear
         de T: (Win) a /Volumes/T Viaja/T (Mac), preservando color y trims.
  v1.11: Agregado parámetro force_all_clips para procesar todos los clips del timeline
         o solo los seleccionados. Compatible con el botón Reconnect Win > Mac del Edit Panel.
______________________________________________________________________

"""

import hiero.core
import hiero.ui
import os
import re
from qt_compat import QtGui

# Eliminamos la importaci?n del SelfReplace
# import LGA_NKS_SelfReplaceClip as self_replace

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def print_clip_info(shot, prefix=""):
    """
    Imprime la informaci?n detallada del clip
    """
    debug_print(f"\n{prefix} Clip Info:")
    debug_print(f"Clip Name: {shot.name()}")
    
    # Informaci?n del clip en la timeline
    debug_print("\nTimeline Info:")
    debug_print(f"Source In: {shot.sourceIn()}")
    debug_print(f"Source Out: {shot.sourceOut()}")
    debug_print(f"Source Duration: {shot.sourceDuration()}")
    debug_print(f"Timeline In: {shot.timelineIn()}")
    debug_print(f"Timeline Out: {shot.timelineOut()}")
    debug_print(f"Timeline Duration: {shot.duration()}")
    
    # Informaci?n del Source
    source = shot.source()
    media_source = source.mediaSource()
    debug_print("\nSource Info:")
    debug_print(f"Source In: {source.sourceIn()}")
    debug_print(f"Source Out: {source.sourceOut()}")
    debug_print(f"Frame Rate: {source.framerate()}")
    
    # Informaci?n adicional del clip
    debug_print("\nAdditional Clip Info:")
    debug_print(f"Original Frame Rate: {shot.playbackSpeed()}")
    debug_print(f"Media Source Path: {media_source.fileinfos()[0].filename()}")
    
    # Informaci?n del formato
    format_obj = source.format()
    if format_obj:
        debug_print("\nFormat Info:")
        debug_print(f"Format: {format_obj.name()}")
        debug_print(f"Resolution: {format_obj.width()}x{format_obj.height()}")

def get_clip_color(clip):
    """
    Devuelve el color actual del BinItem asociado al clip.
    """
    try:
        bin_item = clip.source().binItem()
        return bin_item.color()
    except Exception as e:
        debug_print(f"No se pudo obtener el color del clip: {e}")
        return None

def set_clip_color(clip, color):
    """
    Asigna un color al BinItem asociado al clip.
    """
    try:
        bin_item = clip.source().binItem()
        if color:
            bin_item.setColor(color)
            debug_print(f"Color restaurado para el clip: {clip.name()}")
    except Exception as e:
        debug_print(f"No se pudo asignar el color al clip: {e}")


def fallback_color_from_track(clip):
    """
    Si no se pudo leer el color (clip offline), asigna color según nombre de pista.
    """
    try:
        track_name = clip.parentTrack().name().lower()
    except Exception:
        return None

    if "plate" in track_name:
        return QColor("#42616d")
    if "ref" in track_name:
        return QColor("#aa9e54")
    return None


def find_existing_frame(path_template):
    """
    Dado un path con %0Nd, devuelve el primer archivo existente que matchee.
    Si no encuentra coincidencias, retorna None.
    """
    directory = os.path.dirname(path_template)
    filename_tpl = os.path.basename(path_template)
    match = re.search(r"%0(\d+)d", filename_tpl, re.IGNORECASE)
    if not match or not os.path.exists(directory):
        return None

    digits = int(match.group(1))
    digits_tag = f"%0{digits}d"
    regex_str = re.escape(filename_tpl).replace(re.escape(digits_tag), rf"\\d{{{digits}}}")
    regex = re.compile(f"^{regex_str}$")

    try:
        for fname in os.listdir(directory):
            if regex.match(fname):
                return os.path.join(directory, fname)
    except Exception as e:
        debug_print(f"No se pudo listar {directory}: {e}")
    return None


def find_any_frame(directory, base_stub=None, exts=(".exr", ".dpx")):
    """
    Devuelve el primer archivo que coincida con el stub y extension.
    base_stub: si se provee, el archivo debe comenzar con ese stub.
    """
    if not os.path.exists(directory):
        return None
    try:
        for fname in os.listdir(directory):
            if base_stub and not fname.startswith(base_stub):
                continue
            if exts and not fname.lower().endswith(exts):
                continue
            return os.path.join(directory, fname)
    except Exception as e:
        debug_print(f"No se pudo listar {directory}: {e}")
    return None


def extract_frame_number(path):
    """
    Intenta extraer el número de frame desde el nombre de archivo.
    Retorna int o None.
    """
    fname = os.path.basename(path)
    m = re.search(r"(\d+)(?:\.[^.]+)?$", fname)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None

def main(force_all_clips=False):
    debug_print("\n==== INICIANDO SCRIPT DE RECONNECT ====")
    try:
        project = hiero.core.projects()[-1]
        with project.beginUndo("Reconnect T Win > Mac"):
            seq = hiero.ui.activeSequence()
            if not seq:
                debug_print("No active sequence found.")
                return

            te = hiero.ui.getTimelineEditor(seq)
            
            # Si force_all_clips es True, obtener todos los clips del timeline
            if force_all_clips:
                all_clips = []
                for track in seq.videoTracks():
                    for track_item in track:
                        if not isinstance(track_item, hiero.core.EffectTrackItem):
                            all_clips.append(track_item)
                selected_clips = all_clips
                debug_print(f"Procesando todos los clips del timeline ({len(selected_clips)} clips)...")
            else:
                selected_clips = te.selection()
                debug_print(f"Procesando clips seleccionados ({len(selected_clips)} clips)...")

            if len(selected_clips) == 0:
                debug_print("*** No clips selected on the track ***")
            else:
                valid_clips = [clip for clip in selected_clips if not isinstance(clip, hiero.core.EffectTrackItem)]
                skipped_clips = [clip.name() for clip in selected_clips if isinstance(clip, hiero.core.EffectTrackItem)]
                
                debug_print(f"Procesando {len(valid_clips)} clips v?lidos...")
                if skipped_clips:
                    debug_print(f"Salteando {len(skipped_clips)} efectos: {', '.join(skipped_clips)}")
                
                for shot in valid_clips:
                    # Leer color original antes de reconectar
                    original_color = get_clip_color(shot)
                    if original_color is None:
                        original_color = fallback_color_from_track(shot)
                    # Imprimir informaci?n del clip antes del reemplazo
                    print_clip_info(shot, "BEFORE")

                    # Guardar los valores originales antes de reconectar
                    original_source_in = shot.sourceIn()
                    original_source_out = shot.sourceOut()
                    original_duration = shot.sourceDuration()
                    # frame_offset = 997  # Offset para llevar a 1001 (comentado)

                    # Obtener el file path del clip seleccionado
                    file_path = shot.source().mediaSource().fileinfos()[0].filename()
                    debug_print("\nOriginal file path:", file_path)

                    # Inicializar new_file_path con el path original
                    new_file_path = file_path

                    # Primero intentar reemplazar "T:" si existe
                    if "T:" in file_path:
                        new_file_path = file_path.replace("T:", "/Volumes/T Viaja/T")
                    # Si no encontr? T:, buscar si comienza con /VFX-
                    elif file_path.upper().startswith("/VFX-"):
                        new_file_path = "/Volumes/T Viaja/T" + file_path

                    # Reemplazar las barras invertidas por barras normales
                    new_file_path = new_file_path.replace("\\", "/")
                    debug_print("Modified file path:", new_file_path)

                    # Obtener solo la ruta del directorio sin el nombre del archivo
                    directory_path = os.path.dirname(new_file_path)
                    debug_print(f"Directorio objetivo: {directory_path}")
                    debug_print(f"Existe directorio? {os.path.exists(directory_path)}")
                    filename_tpl = os.path.basename(new_file_path)
                    base_stub = filename_tpl.split("%")[0].rstrip("_")

                    # Armar lista de candidatos de versión (base hacia arriba, sin límite)
                    version_match = re.search(r"_v(\d+)", new_file_path, re.IGNORECASE)
                    if version_match:
                        digits_len = len(version_match.group(1))
                        base_version = int(version_match.group(1))
                        base_dir = os.path.dirname(new_file_path)
                        base_name = os.path.basename(new_file_path)
                        # Calcular prefijo correctamente - evitar doble guion bajo
                        prefix = re.sub(r'_v\d+.*', '_v', base_name)

                        # Escanear todas las carpetas del publish para hallar versiones superiores
                        parent_dir = os.path.dirname(base_dir)
                        candidates = []
                        try:
                            if os.path.exists(parent_dir):
                                for entry in os.listdir(parent_dir):
                                    if entry.startswith(prefix) and os.path.isdir(os.path.join(parent_dir, entry)):
                                        v_match = re.search(r"_v(\d+)", entry, re.IGNORECASE)
                                        if v_match:
                                            ver_num = int(v_match.group(1))
                                            candidates.append((ver_num, entry))
                        except Exception as e:
                            debug_print(f"No se pudo listar {parent_dir}: {e}")

                        # Ordenar por número de versión
                        candidates = sorted(candidates, key=lambda x: x[0])
                        candidates = [(f"_v{ver:0{digits_len}d}",
                                       os.path.join(parent_dir, entry, base_name),
                                       os.path.join(parent_dir, entry))
                                      for ver, entry in candidates
                                      if ver >= base_version]  # Solo mantener ver >= base_version, sin límite superior
                        # Ya no necesitamos fallback - el escaneo debería encontrar todas las versiones
                    else:
                        debug_print("No se pudo detectar versión en el path; se omite el reconnect.")
                        continue

                    def try_reconnect(path_for_frame, path_for_dir):
                        """
                        Intenta reconectar por archivo y luego por carpeta.
                        Retorna (reconnected_bool, current_path_after).
                        """
                        # Por archivo
                        if path_for_frame:
                            debug_print(f"Intentando reconnect con frame: {path_for_frame}")
                            try:
                                shot.reconnectMedia(path_for_frame)
                                current = shot.source().mediaSource().fileinfos()[0].filename()
                                return True, current
                            except Exception as e:
                                debug_print(f"Error reconnecting clip (archivo): {e}")
                        # Por carpeta
                        try:
                            shot.reconnectMedia(path_for_dir)
                            current = shot.source().mediaSource().fileinfos()[0].filename()
                            debug_print("\nClip reconnected successfully (por carpeta).")
                            return True, current
                        except Exception as e:
                            debug_print(f"\nError reconnecting clip (carpeta): {e}")
                        return False, shot.source().mediaSource().fileinfos()[0].filename()

                    # Seleccionar la versión más alta disponible con media
                    available_versions = []
                    for tag, candidate_file, candidate_dir in candidates:
                        # Caso secuencias (%0Nd)
                        candidate_stub = os.path.basename(candidate_file).split('%')[0].rstrip('_')
                        has_sequence_token = "%" in os.path.basename(candidate_file)

                        if not os.path.exists(candidate_dir):
                            debug_print(f"  Versión {tag}: carpeta no existe, se salta.")
                            continue

                        frame_path = None
                        if has_sequence_token:
                            # Para secuencias, buscar cualquier archivo *.exr en la carpeta
                            frame_path = find_any_frame(candidate_dir)
                        else:
                            # Archivo único (mov, etc.)
                            if os.path.exists(candidate_file):
                                frame_path = candidate_file

                        if not frame_path:
                            debug_print(f"  Versión {tag}: no hay media en carpeta/archivo.")
                            continue

                        available_versions.append((tag, candidate_file, candidate_dir, frame_path))

                    if not available_versions:
                        debug_print("No se encontró ninguna versión con media; se omite el reconnect.")
                        continue

                    # Tomar la versión más alta (última de la lista)
                    tag, candidate_file, candidate_dir, frame_path = available_versions[-1]
                    debug_print(f"Usando versión más alta disponible: {tag} con frame {frame_path}")

                    # Si ya estamos en esa versión y la ruta es Mac, no tocar nada
                    is_mac_path = file_path.startswith("/Volumes/T Viaja/T")
                    if is_mac_path and candidate_file == file_path:
                        debug_print("Path ya en Mac y en versión más alta; no se realiza reconnect.")
                        continue

                    # Intento A: replaceClips con frame específico (manteniendo source in/out)
                    reconnected = False
                    current_path = file_path
                    try:
                        shot.replaceClips(frame_path)
                        shot.setSourceIn(original_source_in)
                        shot.setSourceOut(original_source_out)
                        current_path = shot.source().mediaSource().fileinfos()[0].filename()
                        reconnected = True
                        debug_print(f"replaceClips aplicado con {frame_path}")
                    except Exception as e:
                        debug_print(f"Error en replaceClips ({tag}): {e}")

                    # Intento B: reconnect por archivo/carpeta si aún no cambió
                    if not reconnected or current_path == file_path:
                        reconnected, current_path = try_reconnect(frame_path, candidate_dir)

                    # Intento C: ruta completa si sigue igual
                    if not reconnected or current_path == file_path:
                        try:
                            shot.reconnectMedia(candidate_file)
                            current_path = shot.source().mediaSource().fileinfos()[0].filename()
                            reconnected = True
                            debug_print("Intento con ruta completa en versión más alta.")
                        except Exception as e:
                            debug_print(f"Error en reconnect con ruta completa ({tag}): {e}")

                    # Validar final
                    if current_path == file_path:
                        debug_print(f"Path final sin cambios (old/new): {file_path} -> {current_path}")
                        debug_print("El path no cambió; probable falta de media en destino.")
                        # Restaurar color si se perdió
                        set_clip_color(shot, original_color)
                        continue
                    else:
                        debug_print(f"Versión aplicada: {tag}")

                    # Restaurar el color original
                    set_clip_color(shot, original_color)
                    # Imprimir informaci?n del clip despu?s del reemplazo
                    print_clip_info(shot, "AFTER RECONNECT")

                debug_print("\n==== SCRIPT DE RECONNECT COMPLETADO ====")

    except Exception as e:
        debug_print(f"Error en script Reconnect: {e}")