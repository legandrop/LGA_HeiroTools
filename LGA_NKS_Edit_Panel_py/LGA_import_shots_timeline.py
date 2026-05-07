"""
LGA_import_shots_timeline.py
Helpers de timeline para la importación real de shots.

Expone:
  push_clips_right       — empuja clips que ocupan from_frame o posterior
  place_clip_in_timeline — coloca un clip en el track indicado
  stretch_burnin         — estira el clip BurnIn hasta new_end_frame
  set_debug_print        — inyecta la función debug_print del módulo principal
"""

from __future__ import annotations

try:
    import hiero.core
    import hiero.ui
    _HIERO_AVAILABLE = True
except ImportError:
    _HIERO_AVAILABLE = False


# ── constantes ────────────────────────────────────────────────────────────────

_BURNIN_TRACK_NAMES = {"burnin", "burn in", "burn_in"}


# ── logging inyectable ────────────────────────────────────────────────────────

_debug_print = None


def set_debug_print(fn):
    """Inyecta la función debug_print del módulo principal."""
    global _debug_print
    _debug_print = fn


def _log(*args, level="info"):
    if _debug_print is not None:
        try:
            _debug_print(*args, level=level)
        except Exception:
            pass


# ── helpers privados ──────────────────────────────────────────────────────────

def _is_burnin_track(track_name: str) -> bool:
    return track_name.lower().strip() in _BURNIN_TRACK_NAMES


def _find_video_track(seq, track_name: str):
    for track in seq.videoTracks():
        if track.name() == track_name:
            return track
    return None


# ── funciones públicas ────────────────────────────────────────────────────────

def push_clips_right(seq, from_frame: int, amount: int):
    """
    Empuja hacia la derecha todos los clips que tienen contenido en from_frame
    o en cualquier frame posterior. Excluye tracks BurnIn y EffectTrackItems.

    Criterio de seleccion: tl_out >= from_frame
    Captura clips que EMPIEZAN en from_frame o despues (tl_in >= from_frame)
    Y clips que CRUZAN from_frame (tl_in < from_frame, tl_out >= from_frame),
    que son los del shot siguiente con inicio desalineado entre tracks.

    Patron basado en LGA_H-SelectFromPlayhead.py:
    - Selecciona los clips en el Timeline Editor para visibilidad de debug.
    - Ordena de derecha a izquierda para evitar colisiones al expandir.
    - Mueve: setTimelineOut(out + amount) primero, luego setTimelineIn(in + amount).

    Retorna (moved_count, effective_insert_frame) donde:
      moved_count           — numero de clips movidos
      effective_insert_frame — min(tl_in de todos los clips seleccionados) ANTES
                               de moverlos. Es el frame real donde debe empezar
                               el nuevo shot para quedar adyacente al siguiente.
                               Si no hay clips que mover, retorna from_frame.
    """
    if not _HIERO_AVAILABLE or amount <= 0:
        _log("push_clips_right: amount=%d <= 0, saltando." % amount, level="warning")
        return 0, from_frame

    _log("push_clips_right: buscando clips con tl_out >= %d para mover %d frames"
         % (from_frame, amount))

    items_to_move = []

    for track in seq.videoTracks():
        track_name = track.name()
        if _is_burnin_track(track_name):
            _log("push_clips_right: track '%s' es BurnIn, saltado" % track_name)
            continue

        track_total = 0
        track_selected = 0
        for item in track.items():
            try:
                if isinstance(item, hiero.core.EffectTrackItem):
                    continue
                track_total += 1
                tl_in  = int(item.timelineIn())
                tl_out = int(item.timelineOut())

                if tl_out >= from_frame:
                    items_to_move.append(item)
                    track_selected += 1
                    _log("  track='%s' clip='%s' tl=%d-%d → INCLUIDO"
                         " (tl_out=%d >= from_frame=%d)"
                         % (track_name, item.name(), tl_in, tl_out,
                            tl_out, from_frame))
                else:
                    _log("  track='%s' clip='%s' tl=%d-%d → omitido"
                         " (tl_out=%d < from_frame=%d)"
                         % (track_name, item.name(), tl_in, tl_out,
                            tl_out, from_frame))
            except Exception as exc:
                _log("push_clips_right: error leyendo item en track '%s' → %s"
                     % (track_name, exc), level="warning")

        _log("push_clips_right: track='%s' → %d/%d clips seleccionados"
             % (track_name, track_selected, track_total))

    _log("push_clips_right: total %d clips seleccionados para mover %d frames"
         % (len(items_to_move), amount))

    if not items_to_move:
        _log("push_clips_right: sin clips que mover, effective_insert_frame=%d"
             % from_frame, level="warning")
        return 0, from_frame

    # Calcular el effective_insert_frame ANTES de mover:
    # es el tl_in mas pequenio de todos los clips seleccionados.
    # El nuevo shot debe empezar aqui para quedar pegado al shot siguiente.
    effective_insert_frame = min(int(item.timelineIn()) for item in items_to_move)
    _log("push_clips_right: effective_insert_frame=%d (min tl_in de %d clips)"
         % (effective_insert_frame, len(items_to_move)))

    # Seleccionar en el editor para visibilidad de debug
    try:
        te = hiero.ui.getTimelineEditor(seq)
        if te is not None:
            te.setSelection(items_to_move)
            _log("push_clips_right: seleccion aplicada en Timeline Editor")
    except Exception as exc:
        _log("push_clips_right: no se pudo seleccionar en editor → %s" % exc,
             level="warning")

    # Ordenar de derecha a izquierda para evitar colisiones al expandir
    items_to_move.sort(key=lambda x: x.timelineIn(), reverse=True)

    moved = 0
    for item in items_to_move:
        try:
            old_in  = int(item.timelineIn())
            old_out = int(item.timelineOut())
            new_out = old_out + amount
            new_in  = old_in  + amount
            # Mover out primero para que el clip no colapse antes de ajustar in
            item.setTimelineOut(new_out)
            item.setTimelineIn(new_in)
            _log("  movido: '%s' (track='%s') tl %d-%d -> %d-%d"
                 % (item.name(), item.parent().name(),
                    old_in, old_out, new_in, new_out))
            moved += 1
        except Exception as exc:
            _log("push_clips_right: error moviendo '%s' → %s" % (item.name(), exc),
                 level="warning")

    _log("push_clips_right: resultado: %d/%d clips movidos %d frames"
         " | effective_insert_frame=%d"
         % (moved, len(items_to_move), amount, effective_insert_frame))
    return moved, effective_insert_frame


def place_clip_in_timeline(seq, clip, track_name: str,
                            tl_in: int, frame_count: int,
                            shot_name: str):
    """
    Coloca clip en el track indicado dentro de seq.

    Retorna (track_item, error_str). error_str es None si OK.

    Politicas:
    - El track debe existir; si no existe, retorna error (no crea tracks).
    - Source in/out: 0 .. frame_count-1 (el primer frame EXR mapea a source 0).
    - setVersionLinkedToBin(True) se llama al final, cuando el item ya esta insertado.
    """
    target_track = _find_video_track(seq, track_name)
    if target_track is None:
        msg = "Track no encontrado: '%s'" % track_name
        _log("place_clip_in_timeline: %s" % msg, level="error")
        return None, msg

    tl_out = tl_in + frame_count - 1
    try:
        track_item = target_track.addTrackItem(clip, tl_in)
        track_item.setName(shot_name)
        track_item.setTimes(tl_in, tl_out, 0, frame_count - 1)
        track_item.setVersionLinkedToBin(True)
        _log("place_clip_in_timeline: '%s' → track='%s' tl=%d-%d (%df)"
             % (shot_name, track_name, tl_in, tl_out, frame_count))
        return track_item, None
    except Exception as exc:
        _log("place_clip_in_timeline: excepcion → %s" % exc, level="error")
        return None, str(exc)


def stretch_burnin(seq, new_end_frame: int):
    """
    Estira el clip BurnIn para cubrir hasta new_end_frame (inclusive).
    Opera sobre el primer clip del primer track BurnIn encontrado.
    """
    if not _HIERO_AVAILABLE:
        return

    for track in seq.videoTracks():
        if not _is_burnin_track(track.name()):
            continue
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            try:
                tl_in   = int(item.timelineIn())
                src_in  = int(item.sourceIn())
                new_out = max(int(item.timelineOut()), new_end_frame)
                new_src_out = src_in + (new_out - tl_in)
                item.setTimes(tl_in, new_out, src_in, new_src_out)
                _log("stretch_burnin: estirado hasta frame %d" % new_out)
            except Exception as exc:
                _log("stretch_burnin: error → %s" % exc, level="warning")
        break  # solo el primer track BurnIn
