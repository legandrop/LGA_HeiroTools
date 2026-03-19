"""
Exploracion de timeline para preparar futuras tareas de limpieza/refresco.

Objetivos:
1. Inspeccionar todos los video tracks para descubrir como identificar tracks
   especiales de proyectos creados desde Nuke Studio.
2. Calcular el ultimo TC con imagen del timeline ignorando efectos.
3. Inspeccionar el track BurnIn y reportar hasta donde llegan sus efectos.

Este script NO modifica nada. Solo imprime diagnostico.
"""

import hiero.core
import hiero.ui


DEBUG_SEPARATOR = "=" * 100
TRACK_SEPARATOR = "-" * 100
TARGET_PROJECT_TRACK_NAME = "VFX-PHLDA 1"
TARGET_BURNIN_TRACK_NAME = "BurnIn"


def safe_call(obj, attr_name, default=None):
    """Llama un metodo sin argumentos o devuelve un atributo simple."""
    try:
        attr = getattr(obj, attr_name)
    except Exception:
        return default


def summarize_value(value):
    """Resume valores complejos para imprimir sin inundar la consola."""
    if value is None:
        return "None"

    try:
        if isinstance(value, (str, int, float, bool)):
            return repr(value)
    except Exception:
        pass

    try:
        if isinstance(value, (tuple, list)):
            preview = ", ".join(summarize_value(v) for v in list(value)[:3])
            suffix = ", ..." if len(value) > 3 else ""
            return f"{type(value).__name__}(len={len(value)}): [{preview}{suffix}]"
    except Exception:
        pass

    try:
        if hasattr(value, "name") and callable(value.name):
            return f"{type(value).__name__}(name={value.name()!r})"
    except Exception:
        pass

    try:
        if hasattr(value, "toString") and callable(value.toString):
            return f"{type(value).__name__}: {value.toString()}"
    except Exception:
        pass

    try:
        return repr(value)
    except Exception:
        return f"<{type(value).__name__}>"


def metadata_to_lines(metadata):
    """Convierte metadata a lineas legibles."""
    if metadata is None:
        return ["None"]

    lines = []
    try:
        metadata_str = str(metadata)
        if metadata_str.strip():
            for line in metadata_str.splitlines():
                stripped = line.rstrip()
                if stripped:
                    lines.append(stripped)
    except Exception:
        pass

    return lines or ["<metadata vacia>"]


def call_method_for_exploration(obj, method_name):
    """
    Llama un metodo conocido de exploracion sin parametros.
    No intenta adivinar firmas dinamicamente porque los wrappers de Hiero/Shiboken
    no siempre son compatibles con inspect.signature().
    """
    try:
        method = getattr(obj, method_name)
    except Exception as exc:
        return f"<<getattr error: {exc}>>"

    if not callable(method):
        return f"<<atributo no callable: {summarize_value(method)}>>"

    try:
        return method()
    except Exception as exc:
        return f"<<call error: {exc}>>"

    try:
        return attr() if callable(attr) else attr
    except Exception:
        return default


def normalize_fps_int(fps):
    try:
        fps_int = int(round(float(fps)))
        return fps_int if fps_int > 0 else 24
    except Exception:
        return 24


def frames_to_tc(frame, fps):
    """Convierte frame a timecode HH:MM:SS:FF."""
    if frame is None:
        return "N/A"

    fps_int = normalize_fps_int(fps)

    sign = "-" if frame < 0 else ""
    total_frames = abs(int(frame))
    frames = total_frames % fps_int
    total_seconds = total_frames // fps_int
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def tc_to_frames(tc_value, fps):
    """Convierte un TC HH:MM:SS:FF a frames."""
    if tc_value is None:
        return None

    if isinstance(tc_value, int):
        return tc_value

    tc_str = str(tc_value).strip()
    if not tc_str:
        return None

    negative = tc_str.startswith("-")
    if negative:
        tc_str = tc_str[1:]

    parts = tc_str.split(":")
    if len(parts) != 4:
        return None

    try:
        hours, minutes, seconds, frames = [int(part) for part in parts]
    except Exception:
        return None

    fps_int = normalize_fps_int(fps)
    total = (((hours * 60) + minutes) * 60 + seconds) * fps_int + frames
    return -total if negative else total


def tc_label(frame, fps, seq_tc_start=0):
    """Devuelve frame y timecode de secuencia juntos."""
    tc_frame = None if frame is None else int(frame) + int(seq_tc_start)
    return f"{frames_to_tc(tc_frame, fps)} (frame {frame})"


def get_sequence_fps(seq):
    fps = safe_call(seq, "fps")
    if fps is not None:
        try:
            return float(fps)
        except Exception:
            pass

    fps = safe_call(seq, "framerate")
    if fps is not None:
        try:
            return float(fps)
        except Exception:
            pass

        # Algunas versiones devuelven core.TimeBase en vez de numero.
        for attr_name in ("toFloat", "asFloat", "fps", "value", "numerator"):
            value = safe_call(fps, attr_name)
            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

    fmt = safe_call(seq, "format")
    if fmt:
        fmt_fps = safe_call(fmt, "fps")
        if fmt_fps is not None:
            try:
                return float(fmt_fps)
            except Exception:
                pass

    return 24.0


def get_sequence_tc_start(seq, fps):
    """Obtiene el offset de timecode real de la secuencia."""
    candidates = [
        safe_call(seq, "timecodeStart"),
        safe_call(seq, "startTimecode"),
        safe_call(seq, "sourceTimecodeStart"),
    ]

    for candidate in candidates:
        if candidate is None:
            continue

        try:
            return int(candidate)
        except Exception:
            pass

        parsed = tc_to_frames(candidate, fps)
        if parsed is not None:
            return parsed

    # Fallback: usar el formato que ve el usuario en el viewer si existe el dato en metadata
    try:
        project = safe_call(seq, "project")
        metadata = safe_call(project, "metadata")
        if metadata:
            for key in ("foundry.sequence.startTC", "foundry.timeline.startTC"):
                value = safe_call(metadata, "value", None)
                if value:
                    parsed = tc_to_frames(value, fps)
                    if parsed is not None:
                        return parsed
    except Exception:
        pass

    return 0


def iter_subtrack_effects(track):
    """Itera soft effects de un track usando subTrackItems()."""
    items = safe_call(track, "subTrackItems", []) or []
    for group_index, group in enumerate(items):
        if not group:
            continue

        for item_index, item in enumerate(group):
            if isinstance(item, hiero.core.EffectTrackItem):
                yield {
                    "group_index": group_index,
                    "item_index": item_index,
                    "effect": item,
                }


def describe_track(track, fps, seq_tc_start=0):
    """Recolecta propiedades utiles para entender el tipo de track."""
    info = {
        "name": safe_call(track, "name", "<sin nombre>"),
        "class_name": track.__class__.__name__,
        "module_name": track.__class__.__module__,
        "media_type": safe_call(track, "mediaType"),
        "guid": safe_call(track, "guid"),
        "uuid": safe_call(track, "uuid"),
        "source": safe_call(track, "source"),
        "display_name": safe_call(track, "displayName"),
        "icon": safe_call(track, "icon"),
        "icon_name": safe_call(track, "iconName"),
        "item_type": safe_call(track, "itemType"),
        "track_type": safe_call(track, "trackType"),
        "metadata": safe_call(track, "metadata"),
        "items_count": None,
        "subtrack_groups": None,
        "effects_count": 0,
        "clips_count": 0,
    }

    try:
        items = list(track.items())
        info["items_count"] = len(items)
        for item in items:
            if isinstance(item, hiero.core.EffectTrackItem):
                info["effects_count"] += 1
            else:
                info["clips_count"] += 1
    except Exception:
        items = []

    try:
        subtrack_groups = safe_call(track, "subTrackItems", []) or []
        info["subtrack_groups"] = len(subtrack_groups)
        for group in subtrack_groups:
            for item in group:
                if isinstance(item, hiero.core.EffectTrackItem):
                    info["effects_count"] += 1
    except Exception:
        pass

    print(TRACK_SEPARATOR)
    print(f"Track: {info['name']}")
    print(f"  Clase: {info['module_name']}.{info['class_name']}")
    print(f"  mediaType(): {info['media_type']}")
    print(f"  guid(): {info['guid']}")
    print(f"  uuid(): {info['uuid']}")
    print(f"  source(): {info['source']}")
    print(f"  displayName(): {info['display_name']}")
    print(f"  icon(): {info['icon']}")
    print(f"  iconName(): {info['icon_name']}")
    print(f"  itemType(): {info['item_type']}")
    print(f"  trackType(): {info['track_type']}")
    print("  metadata():")
    for metadata_line in metadata_to_lines(info["metadata"]):
        print(f"    {metadata_line}")
    print(f"  items(): {info['items_count']}")
    print(f"  clips normales detectados: {info['clips_count']}")
    print(f"  effects detectados: {info['effects_count']}")
    print(f"  subTrackItems(): {info['subtrack_groups']}")

    interesting_methods = [
        method_name
        for method_name in dir(track)
        if any(token in method_name.lower() for token in ("icon", "meta", "type", "nuke", "vfx"))
        and not method_name.startswith("_")
    ]
    if interesting_methods:
        print(f"  metodos interesantes: {', '.join(sorted(interesting_methods)[:20])}")

    # Exploracion profunda basada en la API oficial de VideoTrack/TrackBase.
    # Lista explicita para evitar rompernos con metodos C++ no introspectables.
    api_query_methods = [
        "name",
        "guid",
        "metadata",
        "toString",
        "parent",
        "trackIndex",
        "view",
        "blendMode",
        "isBlendEnabled",
        "isBlendMaskEnabled",
        "isEnabled",
        "isLocked",
        "items",
        "subTrackItems",
        "tags",
        "mediaType",
        "source",
        "displayName",
        "uuid",
    ]

    available_api_methods = [method_name for method_name in api_query_methods if hasattr(track, method_name)]
    print(f"  metodos API explorados: {len(available_api_methods)}")
    print(f"    {', '.join(available_api_methods)}")

    for method_name in available_api_methods:
        result = call_method_for_exploration(track, method_name)
        print(f"    {method_name}() -> {summarize_value(result)}")

    preview_items = 0
    for item in items:
        if preview_items >= 5:
            break
        item_name = safe_call(item, "name", "<sin nombre>")
        item_in = safe_call(item, "timelineIn")
        item_out = safe_call(item, "timelineOut")
        item_class = item.__class__.__name__
        print(
            f"    item[{preview_items}] {item_class}: {item_name} | "
            f"in={tc_label(item_in, fps, seq_tc_start)} | out={tc_label(item_out, fps, seq_tc_start)}"
        )
        preview_items += 1

    preview_effects = 0
    for effect_data in iter_subtrack_effects(track):
        if preview_effects >= 5:
            break
        effect = effect_data["effect"]
        effect_name = safe_call(effect, "name", "<sin nombre>")
        effect_in = safe_call(effect, "timelineIn")
        effect_out = safe_call(effect, "timelineOut")
        print(
            f"    softEffect[{effect_data['group_index']}:{effect_data['item_index']}] "
            f"{effect.__class__.__name__}: {effect_name} | "
            f"in={tc_label(effect_in, fps, seq_tc_start)} | out={tc_label(effect_out, fps, seq_tc_start)}"
        )
        preview_effects += 1


def clip_has_visible_media(item):
    """Determina si un item parece ser un clip visible y no un efecto."""
    if isinstance(item, hiero.core.EffectTrackItem):
        return False

    source = safe_call(item, "source")
    if not source:
        return False

    media_source = safe_call(source, "mediaSource")
    if not media_source:
        return False

    # Algunos items pueden existir pero no tener media real.
    media_present = safe_call(media_source, "isMediaPresent")
    if media_present is False:
        return False

    return True


def get_last_visible_clip(seq):
    """Busca el item no-efecto mas a la derecha del timeline."""
    last_item = None
    last_track = None
    last_out = None

    for track in seq.videoTracks():
        try:
            track_items = list(track.items())
        except Exception:
            continue

        for item in track_items:
            if not clip_has_visible_media(item):
                continue

            timeline_out = safe_call(item, "timelineOut")
            if timeline_out is None:
                continue

            if last_out is None or timeline_out > last_out:
                last_item = item
                last_track = track
                last_out = timeline_out

    return last_track, last_item, last_out


def inspect_project_track_candidate(seq, fps, seq_tc_start):
    """Imprime diagnostico del track que queremos aprender a detectar."""
    print(DEBUG_SEPARATOR)
    print("1. EXPLORACION DEL TRACK ESPECIAL DE PROYECTOS")
    print(DEBUG_SEPARATOR)

    candidate = None
    for track in seq.videoTracks():
        if safe_call(track, "name") == TARGET_PROJECT_TRACK_NAME:
            candidate = track
            break

    if not candidate:
        print(f"No se encontro el track candidato '{TARGET_PROJECT_TRACK_NAME}'.")
        print("Igual se listan todos los tracks para seguir explorando.")
        return

    print(
        f"Se encontro el track candidato '{TARGET_PROJECT_TRACK_NAME}'. "
        "A continuacion va su diagnostico para descubrir como identificarlo."
    )
    describe_track(candidate, fps, seq_tc_start)
    print(
        f"Resultado provisional: se detecto el track {TARGET_PROJECT_TRACK_NAME} "
        "como candidato al tipo que luego habria que borrar, pendiente de confirmar "
        "por clase/propiedades reales."
    )


def inspect_all_tracks(seq, fps, seq_tc_start):
    """Lista todos los tracks para comparar propiedades."""
    print(DEBUG_SEPARATOR)
    print("2. LISTADO DE TODOS LOS VIDEO TRACKS")
    print(DEBUG_SEPARATOR)
    for index, track in enumerate(seq.videoTracks()):
        print(f"Indice de track: {index}")
        describe_track(track, fps, seq_tc_start)


def inspect_last_visible_tc(seq, fps, seq_tc_start):
    """Calcula e imprime el ultimo TC con imagen."""
    print(DEBUG_SEPARATOR)
    print("3. ULTIMO TC CON IMAGEN")
    print(DEBUG_SEPARATOR)

    track, item, timeline_out = get_last_visible_clip(seq)
    if not item:
        print("No se encontro ningun clip visible con media en el timeline.")
        return None

    last_visible_frame = timeline_out - 1 if timeline_out is not None else None
    item_name = safe_call(item, "name", "<sin nombre>")
    track_name = safe_call(track, "name", "<sin track>")

    print(f"Track del clip mas a la derecha: {track_name}")
    print(f"Clip mas a la derecha: {item_name}")
    print(f"timelineOut del clip mas a la derecha: {tc_label(timeline_out, fps, seq_tc_start)}")
    print(f"Ultimo frame visible de imagen: {tc_label(last_visible_frame, fps, seq_tc_start)}")
    print(
        f"Resultado resumido: el ultimo TC con imagen dentro del timeline es "
        f"{frames_to_tc(last_visible_frame + seq_tc_start, fps)}"
    )

    return {
        "track": track,
        "item": item,
        "timeline_out": timeline_out,
        "last_visible_frame": last_visible_frame,
    }


def inspect_burnin_track(seq, fps, seq_tc_start, last_visible_data):
    """Inspecciona el track BurnIn y compara sus efectos contra el ultimo TC con imagen."""
    print(DEBUG_SEPARATOR)
    print("4. ANALISIS DEL TRACK BURNIN")
    print(DEBUG_SEPARATOR)

    burnin_track = None
    for track in seq.videoTracks():
        if safe_call(track, "name") == TARGET_BURNIN_TRACK_NAME:
            burnin_track = track
            break

    if not burnin_track:
        print(f"No se encontro el track '{TARGET_BURNIN_TRACK_NAME}'.")
        return

    effects = []
    for effect_data in iter_subtrack_effects(burnin_track):
        effect = effect_data["effect"]
        effect_in = safe_call(effect, "timelineIn")
        effect_out = safe_call(effect, "timelineOut")
        effects.append(
            {
                "name": safe_call(effect, "name", "<sin nombre>"),
                "timeline_in": effect_in,
                "timeline_out": effect_out,
                "duration_frames": (
                    effect_out - effect_in
                    if effect_in is not None and effect_out is not None
                    else None
                ),
            }
        )

    if not effects:
        print("El track BurnIn existe pero no se detectaron soft effects en subTrackItems().")
        describe_track(burnin_track, fps)
        return

    print(f"Se detectaron {len(effects)} efectos en el track BurnIn:")
    for index, effect in enumerate(effects, start=1):
        print(
            f"  {index}. {effect['name']} | "
            f"in={tc_label(effect['timeline_in'], fps, seq_tc_start)} | "
            f"out={tc_label(effect['timeline_out'], fps, seq_tc_start)} | "
            f"duracion={effect['duration_frames']} frames"
        )

    if not last_visible_data:
        print("No se pudo comparar BurnIn porque no se pudo calcular el ultimo TC con imagen.")
        return

    target_out = last_visible_data["timeline_out"]
    target_last_visible = last_visible_data["last_visible_frame"]

    unique_outs = sorted({effect["timeline_out"] for effect in effects if effect["timeline_out"] is not None})
    max_effect_out = max(unique_outs) if unique_outs else None

    print("")
    print(f"Referencia de ajuste esperada para BurnIn:")
    print(f"  timelineOut objetivo: {tc_label(target_out, fps, seq_tc_start)}")
    print(f"  ultimo TC con imagen: {tc_label(target_last_visible, fps, seq_tc_start)}")

    if len(unique_outs) == 1:
        only_out = unique_outs[0]
        delta_frames = target_out - only_out
        delta_seconds = float(delta_frames) / float(fps) if fps else 0.0
        print(
            f"Todos los efectos llegan hasta el mismo out: {tc_label(only_out, fps, seq_tc_start)}"
        )
        if delta_frames == 0:
            print("Resultado resumido: todos los efectos de BurnIn ya llegan exactamente hasta el final esperado.")
        elif delta_frames > 0:
            print(
                "Resultado resumido: se detecto que en el track BurnIn los efectos "
                f"llegan hasta {frames_to_tc((only_out - 1) + seq_tc_start, fps)} y faltan "
                f"{delta_frames} frames ({delta_seconds:.2f} s) para llegar hasta el ultimo TC con imagen."
            )
        else:
            print(
                "Resultado resumido: los efectos de BurnIn se pasan del final esperado por "
                f"{abs(delta_frames)} frames ({abs(delta_seconds):.2f} s)."
            )
    else:
        print("Hay discrepancias entre los outs de los efectos de BurnIn:")
        for effect in effects:
            delta_frames = target_out - effect["timeline_out"]
            delta_seconds = float(delta_frames) / float(fps) if fps else 0.0
            if delta_frames == 0:
                status = "OK, llega exacto"
            elif delta_frames > 0:
                status = f"faltan {delta_frames} frames ({delta_seconds:.2f} s)"
            else:
                status = f"se pasa {abs(delta_frames)} frames ({abs(delta_seconds):.2f} s)"

            print(
                f"  - {effect['name']}: llega hasta {tc_label(effect['timeline_out'], fps, seq_tc_start)} | {status}"
            )

        print(
            f"El efecto que mas lejos llega termina en {tc_label(max_effect_out, fps, seq_tc_start)}."
        )


def main():
    print(DEBUG_SEPARATOR)
    print("LGA_NKS_Explore_Timeline_Cleanup")
    print(DEBUG_SEPARATOR)

    seq = hiero.ui.activeSequence()
    if not seq:
        print("No hay una secuencia activa.")
        return

    fps = get_sequence_fps(seq)
    seq_tc_start = get_sequence_tc_start(seq, fps)
    seq_name = safe_call(seq, "name", "<sin nombre>")
    seq_in = safe_call(seq, "inTime")
    seq_out = safe_call(seq, "outTime")

    print(f"Secuencia activa: {seq_name}")
    print(f"FPS detectado: {fps}")
    print(f"Timecode start de secuencia: {frames_to_tc(seq_tc_start, fps)} (offset {seq_tc_start} frames)")
    print(f"In actual de secuencia: {tc_label(seq_in, fps, seq_tc_start)}")
    print(f"Out actual de secuencia: {tc_label(seq_out, fps, seq_tc_start)}")
    print("")

    inspect_project_track_candidate(seq, fps, seq_tc_start)
    print("")
    inspect_all_tracks(seq, fps, seq_tc_start)
    print("")
    last_visible_data = inspect_last_visible_tc(seq, fps, seq_tc_start)
    print("")
    inspect_burnin_track(seq, fps, seq_tc_start, last_visible_data)

    print("")
    print(DEBUG_SEPARATOR)
    print("Fin de la exploracion. No se modifico nada.")
    print(DEBUG_SEPARATOR)


if __name__ == "__main__":
    main()
