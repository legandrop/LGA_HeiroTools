"""
LGA_import_shots_preview.py
Lógica de datos para la página de preview de importación.

Expone:
  build_import_preview_data  — construye la estructura de datos del preview timeline
  classify_track_type        — clasifica un nombre de track en plate/editref/comp/other
  mix_colors                 — mezcla dos colores hex por interpolación lineal
"""

from __future__ import annotations

import re

try:
    import hiero.core
    _HIERO_AVAILABLE = True
except ImportError:
    _HIERO_AVAILABLE = False


# ── utilidad de color ─────────────────────────────────────────────────────────

def mix_colors(hex_color: str, base: str = "#1e1e1e", factor: float = 1.0) -> str:
    """
    Mezcla hex_color con base a la intensidad indicada por factor.

    factor=1.0  → hex_color puro
    factor=0.0  → base puro
    factor=0.35 → 35% hex_color + 65% base  (útil para fondos de chips)

    Retorna string hex "#rrggbb".
    """
    def _parse(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = _parse(hex_color)
    r2, g2, b2 = _parse(base)
    t = max(0.0, min(1.0, factor))
    r = int(r1 * t + r2 * (1 - t))
    g = int(g1 * t + g2 * (1 - t))
    b = int(b1 * t + b2 * (1 - t))
    return "#%02x%02x%02x" % (r, g, b)


# ── clasificación de track ────────────────────────────────────────────────────

def classify_track_type(track_name: str) -> str:
    """
    Clasifica el tipo de track por su nombre.

    Retorna uno de: "plate" | "editref" | "comp" | "roto" | "cleanup" | "other"
    """
    lower = str(track_name).strip().lower()
    if lower.endswith("plate"):
        return "plate"
    if "editref" in lower:
        return "editref"
    if lower == "_comp_" or lower.startswith("_comp_"):
        return "comp"
    if lower == "_roto_" or lower.startswith("_roto_"):
        return "roto"
    if lower == "_cleanup_" or lower.startswith("_cleanup_"):
        return "cleanup"
    return "other"


_BURNIN_NAMES = {"burnin", "burn in", "burn_in"}


def _is_burnin(track_name: str) -> bool:
    return str(track_name).strip().lower() in _BURNIN_NAMES


# ── helpers de búsqueda en track ─────────────────────────────────────────────

def _find_adjacent_clips(track, insert_frame: int):
    """
    Dado un track de Hiero y un frame de inserción, devuelve el clip
    inmediatamente anterior y el inmediatamente posterior.

    Retorna:
        (before, after)  — cada uno es dict|None con keys: name, tl_in, tl_out, duration
    """
    before = None
    after  = None

    for item in track.items():
        if not _HIERO_AVAILABLE:
            break
        try:
            if isinstance(item, hiero.core.EffectTrackItem):
                continue
            tl_in  = int(item.timelineIn())
            tl_out = int(item.timelineOut())
            name   = item.name()
        except Exception:
            continue

        duration = tl_out - tl_in + 1

        # Clip que termina antes del punto de inserción → candidato "before"
        if tl_out < insert_frame:
            if before is None or tl_out > before["tl_out"]:
                before = {"name": name, "tl_in": tl_in, "tl_out": tl_out, "duration": duration}

        # Clip que empieza en o después del punto de inserción → candidato "after"
        elif tl_in >= insert_frame:
            if after is None or tl_in < after["tl_in"]:
                after = {"name": name, "tl_in": tl_in, "tl_out": tl_out, "duration": duration}

    return before, after


# ── función principal ─────────────────────────────────────────────────────────

def build_import_preview_data(
    seq,
    shot_name: str,
    insert_frame: int,
    items_by_track: dict[str, list[dict]],
    unassigned_items: list[dict],
) -> dict:
    """
    Construye la estructura de datos para el preview de importación.

    Args:
        seq:             hiero.core.Sequence activa
        shot_name:       nombre del shot que se importa
        insert_frame:    frame de inserción calculado por _find_insert_frame()
        items_by_track:  dict track_name → [item_dict] de los ítems chequeados
                         (ya deduplicados: solo la última versión por track)
        unassigned_items: ítems chequeados sin track asignado, cada uno con
                          un campo extra "_color" con su color de barra

    Retorna:
        {
          "tracks": [
            {
              "track_name": str,
              "track_type": "plate"|"editref"|"comp"|"roto"|"cleanup"|"other",
              "before_clip": {"name": str, "tl_in": int, "tl_out": int, "duration": int} | None,
              "new_items":   [item_dict],
              "after_clip":  {"name": str, "tl_in": int, "tl_out": int, "duration": int} | None,
            },
            ...
          ],
          "unassigned": [item_dict],  # cada uno tiene "_color"
        }

    Reglas de inclusión de tracks:
    - Se incluyen TODOS los tracks del timeline excepto los de burn-in.
    - El orden respeta el orden de videoTracks() del timeline (de arriba a abajo).
    - Los tracks asignados a ítems nuevos que no existen en el timeline
      se añaden al final de la lista.
    """
    tracks_result = []

    if not _HIERO_AVAILABLE or seq is None:
        return {
            "tracks": tracks_result,
            "unassigned": list(unassigned_items),
        }

    try:
        # Hiero devuelve los tracks de abajo hacia arriba;
        # reversed() los da de arriba hacia abajo como se ven en el timeline.
        video_tracks = list(reversed(list(seq.videoTracks())))
    except Exception:
        video_tracks = []

    seen_track_names = set()

    for track in video_tracks:
        try:
            tname = track.name()
        except Exception:
            continue

        if _is_burnin(tname):
            continue

        seen_track_names.add(tname)
        before, after = _find_adjacent_clips(track, insert_frame)
        new_items     = items_by_track.get(tname, [])

        # Se incluyen TODOS los tracks del timeline (no se filtra por contenido vacío)
        tracks_result.append({
            "track_name": tname,
            "track_type": classify_track_type(tname),
            "before_clip": before,
            "new_items":   list(new_items),
            "after_clip":  after,
        })

    # Tracks asignados a ítems nuevos que NO existen en el timeline
    for tname, items in items_by_track.items():
        if tname in seen_track_names:
            continue
        tracks_result.append({
            "track_name": tname,
            "track_type": classify_track_type(tname),
            "before_clip": None,
            "new_items":   list(items),
            "after_clip":  None,
        })

    return {
        "tracks": tracks_result,
        "unassigned": list(unassigned_items),
    }
