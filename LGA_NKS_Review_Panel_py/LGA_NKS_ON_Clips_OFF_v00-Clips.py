"""
____________________________________________________________________

  LGA_NKS_ON_Clips_OFF_v00-Clips v1.20 | Lega

  Activa todos los clips y desactiva clips v00/v000

  v1.20: Soporta versiones de 2 y 3 dígitos
____________________________________________________________________

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
    Activa todos los clips y desactiva clips v00/v000 (versión cero)
    Soporta versiones de 2 dígitos (v00-v99) y 3 dígitos (v000-v999)

    Args:
        force_all_clips (bool): Si es True, procesa todos los clips de todos los tracks
                               del timeline, no solo los seleccionados.
    """
    # Mensaje inicial mejorado
    if force_all_clips:
        debug_print("Ejecutando sobre todos los clips del timeline")
    else:
        debug_print("Ejecutando solo en los clips seleccionados")

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
                debug_print(
                    f"Procesando todos los clips del timeline ({len(selected_items)} clips)"
                )
            else:
                # Usar solo los clips seleccionados
                selected_items = te.selection()
                debug_print(
                    f"Procesando clips seleccionados ({len(selected_items)} clips)"
                )

            # Patrón regex para detectar versiones de 2 o 3 dígitos: _comp_v00, _comp_v000, _comp_v01, _comp_v001, etc.
            version_pattern = re.compile(r"_comp_v(\d{2,3})", re.IGNORECASE)

            if selected_items:
                for item in selected_items:
                    if not isinstance(item, hiero.core.EffectTrackItem):
                        file_path = (
                            item.source().mediaSource().fileinfos()[0].filename()
                            if item.source().mediaSource().fileinfos()
                            else None
                        )
                        if file_path:
                            filename = os.path.basename(file_path)
                            # Buscar versión en el nombre del archivo
                            version_match = version_pattern.search(filename.lower())

                            if version_match:
                                version_number = version_match.group(1)
                                # Desactivar solo si es v00 o v000 (versión cero)
                                if version_number == "00" or version_number == "000":
                                    item.setEnabled(False)
                                    debug_print(
                                        f"Clip '{item.name()}' desactivado (versión v{version_number})."
                                    )
                                else:
                                    item.setEnabled(True)
                                    debug_print(
                                        f"Clip '{item.name()}' activado (versión v{version_number})."
                                    )
                            else:
                                # No tiene patrón de versión _comp_vXX, activar
                                item.setEnabled(True)
                                debug_print(
                                    f"Clip '{item.name()}' activado (sin versión detectada)."
                                )
                        else:
                            item.setEnabled(True)
                            debug_print(
                                f"Clip '{item.name()}' activado (sin ruta de archivo)."
                            )
            else:
                debug_print("No hay clips para procesar en la linea de tiempo.")
        else:
            debug_print("No se encontro una secuencia activa en Hiero.")
    except Exception as e:
        debug_print(f"Error durante la operacion: {e}")
