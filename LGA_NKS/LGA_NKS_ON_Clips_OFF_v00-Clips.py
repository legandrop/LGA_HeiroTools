"""
______________________________________________________

  LGA_NKS_ON_Clips_OFF_v00-Clips v1.1 | Lega
  Activa todos los clips y desactiva clips v00
______________________________________________________

"""

import hiero.core
import hiero.ui
import os
import re

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

def main(force_all_clips=False):
    """
    Activa todos los clips y desactiva clips v00
    
    Args:
        force_all_clips (bool): Si es True, procesa todos los clips de todos los tracks
                               del timeline, no solo los seleccionados.
    """
    debug_print(f"Iniciando main() con force_all_clips={force_all_clips}")
    try:
        seq = hiero.ui.activeSequence()
        if seq:
            te = hiero.ui.getTimelineEditor(seq)
            
            # Determinar qué clips procesar
            if force_all_clips:
                # Obtener todos los clips de todos los tracks del timeline
                all_tracks = seq.videoTracks()
                selected_items = []
                for track in all_tracks:
                    selected_items.extend(track.items())
                debug_print(f"Procesando todos los clips del timeline ({len(selected_items)} clips)")
            else:
                # Usar solo los clips seleccionados
                selected_items = te.selection()
                debug_print(f"Procesando clips seleccionados ({len(selected_items)} clips)")
            
            if selected_items:
                for item in selected_items:
                    if not isinstance(item, hiero.core.EffectTrackItem):
                        file_path = item.source().mediaSource().fileinfos()[0].filename() if item.source().mediaSource().fileinfos() else None
                        if file_path and '_comp_' in os.path.basename(file_path).lower():
                            if re.search(r'_comp_v00', os.path.basename(file_path).lower()):
                                item.setEnabled(False)
                                debug_print(f"Clip '{item.name()}' desactivado.")
                            else:
                                item.setEnabled(True)
                                debug_print(f"Clip '{item.name()}' activado.")
                        else:
                            item.setEnabled(True)
                            debug_print(f"Clip '{item.name()}' activado.")
            else:
                debug_print("No hay clips para procesar en la linea de tiempo.")
        else:
            debug_print("No se encontro una secuencia activa en Hiero.")
    except Exception as e:
        debug_print(f"Error durante la operacion: {e}")
