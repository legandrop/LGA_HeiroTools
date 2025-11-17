"""
_______________________________________________________________________________________

  LGA_H-Clip_PrintName_from_Playhead v2 - Lega
  - Verifica si hay una secuencia activa.
  - Verifica si hay un track llamado "EXR".
  - Obtiene el tiempo actual del playhead.
  - Busca el clip ubicado en ese track y en ese tiempo.
  - Extrae e imprime el nombre del clip y la versión (_v###).
  - Imprime el frame actual del EXR.
_______________________________________________________________________________________

"""

import hiero.core
import hiero.ui
import os
import re


def parse_exr_name(file_name):
    version_match = re.search(r"_v(\d+)", file_name)
    version_number = version_match.group(1) if version_match else "Unknown"
    base_name = re.sub(r"_v\d+_%04d\.exr", "", file_name)
    return base_name, version_number


def print_clip_info_at_playhead_on_exr_track():
    sequence = hiero.ui.activeSequence()
    if not sequence:
        print("No se encontró una secuencia activa.")
        return

    viewer = hiero.ui.currentViewer()
    if not viewer:
        print("No se encontró un visor activo.")
        return

    current_time = viewer.time()
    print(f"Tiempo actual del playhead: {current_time}")

    exr_track = next((t for t in sequence.videoTracks() if t.name() == "EXR"), None)
    if not exr_track:
        print("No se encontró un track llamado 'EXR'.")
        return

    for clip in exr_track:
        if clip.timelineIn() <= current_time < clip.timelineOut():
            file_path = clip.source().mediaSource().fileinfos()[0].filename()
            fileinfo = clip.source().mediaSource().fileinfos()[0]
            exr_name = os.path.basename(file_path)
            base_name, version_number = parse_exr_name(exr_name)

            start_frame = fileinfo.startFrame()
            frame_offset = current_time - clip.timelineIn()
            frame_number = int(start_frame + frame_offset)

            print("Clip encontrado en 'EXR' track:")
            print("Nombre del archivo:", exr_name)
            print("Nombre base:", base_name)
            print("Versión:", version_number)
            print("--------- DEBUG ---------")
            print(f"timelineIn: {clip.timelineIn()}")
            print(f"current_time (playhead): {current_time}")
            print(f"startFrame (real del EXR): {start_frame}")
            print(f"frame_offset (diferencia): {frame_offset}")
            print(f"Frame dentro del clip (calculado): {frame_number:04d}")
            print("--------------------------")

            return

    print(
        "No se encontró un clip en el track 'EXR' en la posición actual del playhead."
    )


print_clip_info_at_playhead_on_exr_track()
