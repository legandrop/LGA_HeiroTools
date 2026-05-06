"""
LGA_import_shots_preview.py
Lógica de datos para la página de preview de importación.

Expone:
  build_import_preview_data  — construye la estructura de datos del preview timeline
  classify_track_type        — clasifica un nombre de track en plate/editref/comp/other
"""

from __future__ import annotations

import re

try:
    import hiero.core
    _HIERO_AVAILABLE = True
except ImportError:
    _HIERO_AVAILABLE = False


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
        (before, after)  — cada uno es dict|None con keys: name, tl_in, tl_out
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

        # Clip que termina antes del punto de inserción → candidato "before"
        if tl_out < insert_frame:
            if before is None or tl_out > before["tl_out"]:
                before = {"name": name, "tl_in": tl_in, "tl_out": tl_out}

        # Clip que empieza en o después del punto de inserción → candidato "after"
        elif tl_in >= insert_frame:
            if after is None or tl_in < after["tl_in"]:
                after = {"name": name, "tl_in": tl_in, "tl_out": tl_out}

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
        shot_name:       nombre del shot que se está importando
        insert_frame:    frame de inserción calculado por _find_insert_frame()
        items_by_track:  dict track_name → [item_dict] de los ítems chequeados
        unassigned_items: ítems chequeados sin track asignado

    Retorna:
        {
          "tracks": [
            {
              "track_name": str,
              "track_type": "plate"|"editref"|"comp"|"roto"|"cleanup"|"other",
              "before_clip": {"name": str, "tl_in": int, "tl_out": int} | None,
              "new_items":   [item_dict],
              "after_clip":  {"name": str, "tl_in": int, "tl_out": int} | None,
            },
            ...
          ],
          "unassigned": [item_dict],
        }

    Reglas de inclusión de tracks:
    - Se excluyen los tracks de burn-in.
    - Se incluye un track si tiene ítems nuevos asignados O si tiene clips
      before/after relevantes (al menos uno de los dos), indicando que el
      timeline ya tiene contenido adyacente al shot a insertar.
    - El orden respeta el orden de videoTracks() del timeline (de arriba a abajo).
    """
    tracks_result = []

    if not _HIERO_AVAILABLE or seq is None:
        return {
            "tracks": tracks_result,
            "unassigned": list(unassigned_items),
        }

    try:
        video_tracks = list(seq.videoTracks())
    except Exception:
        video_tracks = []

    for track in video_tracks:
        try:
            tname = track.name()
        except Exception:
            continue

        if _is_burnin(tname):
            continue

        before, after = _find_adjacent_clips(track, insert_frame)
        new_items     = items_by_track.get(tname, [])

        # Incluir solo si hay contenido relevante: ítems nuevos o contexto adyacente
        if not new_items and before is None and after is None:
            continue

        tracks_result.append({
            "track_name": tname,
            "track_type": classify_track_type(tname),
            "before_clip": before,
            "new_items":   list(new_items),
            "after_clip":  after,
        })

    # Tracks con ítems nuevos que NO existen aún en el timeline
    # (se asignaron a un track que todavía no existe en la secuencia)
    existing_track_names = {t["track_name"] for t in tracks_result}
    for tname, items in items_by_track.items():
        if tname in existing_track_names:
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
