import hiero.core
import hiero.ui
import os
import re


# Función para extraer el nombre base del archivo y el número de versión
def parse_name_and_version(file_name):
    version_match = re.search(r"_v(\d+)", file_name)
    version_number = version_match.group(1) if version_match else "Unknown"
    base_name = re.sub(r"_v\d+(_%04d)?\.\w+$", "", file_name)
    return base_name, version_number


# Obtener la secuencia activa y el editor de línea de tiempo
seq = hiero.ui.activeSequence()
if seq:
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection()

    if selected_clips:
        for clip in selected_clips:
            # Obtener el path del archivo
            fileinfos = clip.source().mediaSource().fileinfos()
            if not fileinfos:
                print("⚠️ No se encontraron fileinfos para el clip.")
                continue

            file_path = fileinfos[0].filename()
            print("🗂️ Original file path:", file_path)

            # Obtener nombre y versión del archivo
            file_name = os.path.basename(file_path)
            print("📄 File name:", file_name)

            base_name, version_number = parse_name_and_version(file_name)
            print("📌 Base name:", base_name)
            print("🔢 Version number:", version_number)

            # Obtener frame range real del archivo
            start_frame = fileinfos[0].startFrame()
            end_frame = fileinfos[0].endFrame()
            print(f"🎞️ Frame range del archivo: {start_frame} - {end_frame}")
            print("-" * 40)

    else:
        print("⚠️ No clips selected on the timeline.")
else:
    print("⚠️ No active sequence found.")
