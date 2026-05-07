"""
LGA_import_shots_timeline.py
Helpers de timeline para la importación real de shots.

Expone:
  push_clips_right       — empuja clips >= from_frame hacia la derecha
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


# ── helper privado ────────────────────────────────────────────────────────────

def _is_burnin_track(track_name: str) -> bool:
    return track_name.lower().strip() in _BURNIN_TRACK_NAMES


def _find_video_track(seq, track_name: str):
    for track in seq.videoTracks():
        if track.name() == track_name:
            return track
    return None


# ── funciones públicas ────────────────────────────────────────────────────────

def push_clips_right(seq, from_frame: int, amount: int) -> int:
    """
    Mueve todos los clips cuyo timelineIn >= from_frame hacia la derecha
    por 'amount' frames. Excluye tracks BurnIn y EffectTrackItems.

    Patrón basado en LGA_H-SelectFromPlayhead.py:
    - Recolecta items de todos los video tracks (excepto BurnIn).
    - Los selecciona en el Timeline Editor para visibilidad de debug.
    - Los ordena de derecha a izquierda para evitar colisiones.
    - Mueve con setTimelineOut() primero, luego setTimelineIn()
      (así el clip no se "colapsa" mientras se desplaza).

    Retorna el número de items movidos.
    """
    if not _HIERO_AVAILABLE or amount <= 0:
        _log("push_clips_right: amount=%d, saltando." % amount, level="warning")
        return 0

    items_to_move = []

    for track in seq.videoTracks():
        if _is_burnin_track(track.name()):
            continue
        for item in track.items():
            try:
                if isinstance(item, hiero.core.EffectTrackItem):
                    continue
                if int(item.timelineIn()) >= from_frame:
                    items_to_move.append(item)
            except Exception as exc:
                _log("push_clips_right: error leyendo item → %s" % exc, level="warning")

    # Seleccionar en el editor para visibilidad de debug
    try:
        te = hiero.ui.getTimelineEditor(seq)
        if te is not None:
            te.setSelection(items_to_move)
    except Exception as exc:
        _log("push_clips_right: no se pudo seleccionar en editor → %s" % exc, level="warning")

    # Ordenar de derecha a izquierda para evitar colisiones al expandir
    items_to_move.sort(key=lambda x: x.timelineIn(), reverse=True)

    moved = 0
    for item in items_to_move:
        try:
            new_out = item.timelineOut() + amount
            new_in  = item.timelineIn()  + amount
            # Mover out primero para que el clip no colapse al achicarse
            item.setTimelineOut(new_out)
            item.setTimelineIn(new_in)
            _log("  push: '%s' → tl_in=%d" % (item.name(), new_in))
            moved += 1
        except Exception as exc:
            _log("push_clips_right: error moviendo '%s' → %s" % (item.name(), exc),
                 level="warning")

    _log("push_clips_right: %d items movidos %d frames desde frame %d"
         % (moved, amount, from_frame))
    return moved


def place_clip_in_timeline(seq, clip, track_name: str,
                            tl_in: int, frame_count: int,
                            shot_name: str):
    """
    Coloca clip en el track indicado dentro de seq.

    Retorna (track_item, error_str). error_str es None si OK.

    Políticas:
    - El track debe existir; si no existe, retorna error (no crea tracks).
    - Source in/out: 0 .. frame_count-1 (el primer frame EXR mapea a source 0).
    - setVersionLinkedToBin(True) se llama al final, cuando el item ya está insertado.
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
        _log("place_clip_in_timeline: excepción → %s" % exc, level="error")
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
