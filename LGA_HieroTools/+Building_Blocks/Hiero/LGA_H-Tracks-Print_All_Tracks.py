import hiero.core
import hiero.ui


def safe_call(obj, method_name, default="N/A"):
    if not hasattr(obj, method_name):
        return default

    try:
        method = getattr(obj, method_name)
        return method() if callable(method) else method
    except Exception as e:
        return f"ERROR: {e}"


def print_track_list(label, tracks):
    tracks = list(tracks)
    print(f"\n--- {label} tracks ({len(tracks)}) ---")

    if not tracks:
        print(f"No hay tracks de {label.lower()}.")
        return

    # Hiero devuelve los tracks de abajo hacia arriba; invertimos la lista para
    # imprimirlos como se ven en el timeline, de arriba hacia abajo.
    for display_index, track in enumerate(reversed(tracks)):
        name = safe_call(track, "name", "<sin nombre>")
        native_index = len(tracks) - 1 - display_index
        track_index = safe_call(track, "trackIndex", native_index)
        enabled = safe_call(track, "isEnabled")
        locked = safe_call(track, "isLocked")

        item_count = "N/A"
        try:
            item_count = len(track.items())
        except Exception:
            pass

        subtrack_item_count = "N/A"
        try:
            subtrack_item_count = len(track.subTrackItems())
        except Exception:
            pass

        print(
            f"{display_index:02d} | name: {name} | nativeIndex: {native_index} | "
            f"trackIndex: {track_index} | "
            f"enabled: {enabled} | locked: {locked} | "
            f"items: {item_count} | subTrackItems: {subtrack_item_count}"
        )


def print_all_tracks_in_active_timeline():
    seq = hiero.ui.activeSequence()

    if not seq:
        print("No hay una secuencia activa.")
        return

    print("=" * 80)
    print("TRACKS DEL TIMELINE ACTIVO")
    print("=" * 80)
    print(f"Secuencia activa: {seq.name()}")
    print("Orden: de arriba hacia abajo, como se ve en el timeline.")

    try:
        print_track_list("Video", seq.videoTracks())
    except Exception as e:
        print(f"\nError leyendo video tracks: {e}")

    try:
        print_track_list("Audio", seq.audioTracks())
    except Exception as e:
        print(f"\nError leyendo audio tracks: {e}")


print_all_tracks_in_active_timeline()
