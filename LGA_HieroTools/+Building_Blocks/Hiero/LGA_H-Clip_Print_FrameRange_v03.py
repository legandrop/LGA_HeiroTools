"""
_______________________________________________________________________________________

  LGA_H-Clip_Print_FrameRange v0.4 | Lega
  - Imprime el frame range y la posición en el timeline de los clips seleccionados.
  - Calcula el TC In sumando timecodeStart() + sourceIn().
  - También imprime el FPS y la resolución.
_______________________________________________________________________________________
"""

import hiero.core
import hiero.ui
import os
import re


def parse_name_and_version(file_name):
    version_match = re.search(r"_v(\d+)", file_name)
    version_number = version_match.group(1) if version_match else "Unknown"
    base_name = re.sub(r"_v\d+(_%04d)?\.\w+$", "", file_name)
    return base_name, version_number


def frame_to_tc(frame, fps):
    frame = int(frame)
    fps = int(fps)
    h = frame // (3600 * fps)
    m = (frame // (60 * fps)) % 60
    s = (frame // fps) % 60
    f = frame % fps
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


seq = hiero.ui.activeSequence()
if seq:
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection()

    if selected_clips:
        for clip in selected_clips:
            fileinfos = clip.source().mediaSource().fileinfos()
            if not fileinfos:
                print("⚠️ No se encontraron fileinfos para el clip.")
                continue

            file_path = fileinfos[0].filename()
            print("🗂️ Original file path:", file_path)

            file_name = os.path.basename(file_path)
            print("📄 File name:", file_name)

            base_name, version_number = parse_name_and_version(file_name)
            print("📌 Base name:", base_name)
            print("🔢 Version number:", version_number)

            start_frame = fileinfos[0].startFrame()
            end_frame = fileinfos[0].endFrame()
            print(f"🎞️ Frame range del archivo: {start_frame} - {end_frame}")

            timeline_in = clip.timelineIn()
            timeline_out = clip.timelineOut()
            print(f"🕒 Posición en timeline: {timeline_in} - {timeline_out}")

            # FPS
            media_source = clip.source().mediaSource()
            metadata = media_source.metadata()
            try:
                fps = float(metadata["foundry.source.framerate"])
                print(f"🎚️ FPS: {fps:.3f}")
            except Exception:
                fps = 25.0
                print("🎚️ FPS: ❌ No disponible, usando default 25.0")

            # TC In desde timecodeStart + sourceIn
            try:
                tc_start = int(clip.source().timecodeStart())
                tc_in_frames = tc_start + int(clip.sourceIn())
                tc_str = frame_to_tc(tc_in_frames, fps)
                print(f"🎬 TC In: {tc_str}")
            except Exception as e:
                print(f"🎬 TC In: ❌ Error → {e}")

            # Resolución
            try:
                width = metadata["foundry.source.width"]
                height = metadata["foundry.source.height"]
                print(f"🖼️ Resolución: {width}x{height}")
            except Exception:
                print("🖼️ Resolución: ❌ No disponible")

            print("-" * 40)

    else:
        print("⚠️ No clips selected on the timeline.")
else:
    print("⚠️ No active sequence found.")
