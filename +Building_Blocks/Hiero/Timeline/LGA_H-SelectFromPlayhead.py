#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
____________________________________________________________________

  LGA_H-SelectFromPlayhead | Lega

  Selecciona todos los clips y soft effects en todos los tracks
  desde la posicion del playhead hasta el final de la secuencia,
  y los mueve a la derecha por MOVE_OFFSET frames.
  Todo el movimiento queda como un solo undo.
____________________________________________________________________

"""

import hiero.core
import hiero.ui

MOVE_OFFSET = 100  # Frames a mover hacia la derecha


def collect_items_from_playhead(seq, playhead_frame):
    """Recolecta TrackItems y EffectTrackItems desde el playhead en adelante."""
    track_items = []
    effect_items = []

    all_tracks = list(seq.videoTracks()) + list(seq.audioTracks())

    for track in all_tracks:
        # Clips normales
        for item in track.items():
            if isinstance(item, hiero.core.TrackItem):
                if item.timelineIn() >= playhead_frame:
                    track_items.append(item)

        # Soft effects en el track
        for group in track.subTrackItems():
            for effect in group:
                if isinstance(effect, hiero.core.EffectTrackItem):
                    if effect.timelineIn() >= playhead_frame:
                        effect_items.append(effect)

    return track_items, effect_items


def move_items_right(track_items, effect_items, offset):
    """Mueve todos los items hacia la derecha por offset frames (rightmost first)."""
    all_items = track_items + effect_items
    all_items.sort(key=lambda x: x.timelineIn(), reverse=True)

    for item in all_items:
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

        track_items, effect_items = collect_items_from_playhead(seq, playhead_frame)

        te.setSelection(track_items)
        print(f"Seleccionados {len(track_items)} clips y {len(effect_items)} soft effects desde frame {playhead_frame} en adelante.")

        project = seq.project()
        with project.beginUndo("Move From Playhead"):
            print(f"Moviendo {MOVE_OFFSET} frames a la derecha...")
            move_items_right(track_items, effect_items, MOVE_OFFSET)
        print("Listo.")
