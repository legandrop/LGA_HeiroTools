#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
____________________________________________________________________

  LGA_H-SelectFromPlayhead | Lega

  Selecciona todos los clips en todos los tracks (video y audio)
  desde la posicion del playhead hasta el final de la secuencia,
  y los mueve a la derecha por MOVE_OFFSET frames.
____________________________________________________________________

"""

import hiero.core
import hiero.ui

MOVE_OFFSET = 100  # Frames a mover hacia la derecha


def move_items_right(items, offset):
    # Procesar de derecha a izquierda para evitar colisiones al expandir
    sorted_items = sorted(items, key=lambda x: x.timelineIn(), reverse=True)
    for item in sorted_items:
        new_out = item.timelineOut() + offset
        new_in = item.timelineIn() + offset
        item.setTimelineOut(new_out)
        item.setTimelineIn(new_in)
        print(f"  Movido: {item.name()} -> frame {new_in}")


seq = hiero.ui.activeSequence()
if not seq:
    print("No hay una secuencia activa.")
else:
    te = hiero.ui.getTimelineEditor(seq)

    current_viewer = hiero.ui.currentViewer()
    player = current_viewer.player() if current_viewer else None
    playhead_frame = player.time() if player else None

    if playhead_frame is None:
        print("No se pudo obtener la posicion del playhead.")
    else:
        print(f"Playhead en frame: {playhead_frame}")

        items_to_select = []

        all_tracks = list(seq.videoTracks()) + list(seq.audioTracks())

        for track in all_tracks:
            for item in track.items():
                if isinstance(item, hiero.core.TrackItem):
                    if item.timelineIn() >= playhead_frame:
                        items_to_select.append(item)

        te.setSelection(items_to_select)
        print(f"Seleccionados {len(items_to_select)} clips desde frame {playhead_frame} en adelante.")

        print(f"Moviendo {MOVE_OFFSET} frames a la derecha...")
        move_items_right(items_to_select, MOVE_OFFSET)
        print("Listo.")
