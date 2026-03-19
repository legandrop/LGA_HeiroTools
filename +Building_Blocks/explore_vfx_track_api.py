"""
Exploracion puntual del track VFX/NukeVFX.

Estilo simple, parecido a explore_api.py y explore_offline_clips.py:
- mostrar tipo
- listar metodos disponibles
- probar algunos metodos concretos
- explorar tags asociados

No modifica nada.
"""

import hiero.core
import hiero.ui


TARGET_TRACK_NAME = "VFX-PHLDA 1"


def print_methods(obj, label):
    try:
        methods = [m for m in dir(obj) if not m.startswith("_")]
        print(f"\nMetodos/atributos disponibles en {label} ({len(methods)}):")
        print(methods)
    except Exception as e:
        print(f"Error obteniendo dir({label}): {e}")


def try_call(obj, method_name, label):
    if not hasattr(obj, method_name):
        print(f"  {label}.{method_name}(): NO EXISTE")
        return

    try:
        method = getattr(obj, method_name)
        if callable(method):
            result = method()
        else:
            result = method
        print(f"  {label}.{method_name}(): {result}")
    except Exception as e:
        print(f"  {label}.{method_name}(): ERROR -> {e}")


def explore_tag(tag, index):
    print("\n" + "-" * 80)
    print(f"TAG #{index}")
    print("-" * 80)
    print(f"Tipo: {type(tag)}")

    print_methods(tag, f"tag[{index}]")

    methods_to_test = [
        "name",
        "note",
        "icon",
        "visible",
        "metadata",
        "toString",
        "guid",
    ]

    for method_name in methods_to_test:
        try_call(tag, method_name, f"tag[{index}]")

    if hasattr(tag, "metadata"):
        try:
            metadata = tag.metadata()
            print(f"\n  Metadata del tag:")
            print(metadata)
        except Exception as e:
            print(f"  Error leyendo metadata del tag: {e}")


def explore_track(track):
    print("=" * 100)
    print("TRACK ENCONTRADO")
    print("=" * 100)
    print(f"Tipo: {type(track)}")

    print_methods(track, "track")

    methods_to_test = [
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

    print("\n" + "=" * 100)
    print("PRUEBA DE METODOS CONCRETOS")
    print("=" * 100)
    for method_name in methods_to_test:
        try_call(track, method_name, "track")

    print("\n" + "=" * 100)
    print("EXPLORACION DE TAGS")
    print("=" * 100)
    if hasattr(track, "tags"):
        try:
            tags = track.tags()
            print(f"Cantidad de tags: {len(tags)}")
            for index, tag in enumerate(tags):
                explore_tag(tag, index)
        except Exception as e:
            print(f"Error obteniendo tags: {e}")

    print("\n" + "=" * 100)
    print("COMPARACION CON OTROS TRACKS VACIOS")
    print("=" * 100)
    seq = hiero.ui.activeSequence()
    if not seq:
        print("No hay secuencia activa")
        return

    for other_track in seq.videoTracks():
        if other_track == track:
            continue

        try:
            items = other_track.items()
            subtracks = other_track.subTrackItems()
            tags = other_track.tags() if hasattr(other_track, "tags") else []

            if len(items) == 0 and len(subtracks) == 0:
                print(f"\nTrack vacio para comparar: {other_track.name()}")
                print(f"  Tipo: {type(other_track)}")
                print(f"  guid(): {other_track.guid() if hasattr(other_track, 'guid') else 'N/A'}")
                print(f"  toString(): {other_track.toString() if hasattr(other_track, 'toString') else 'N/A'}")
                print(f"  metadata(): {other_track.metadata() if hasattr(other_track, 'metadata') else 'N/A'}")
                print(f"  tags(): {tags}")
        except Exception as e:
            print(f"Error comparando track: {e}")


def main():
    print("=" * 100)
    print("EXPLORACION API DEL TRACK VFX")
    print("=" * 100)

    seq = hiero.ui.activeSequence()
    if not seq:
        print("No active sequence")
        return

    print(f"Secuencia activa: {seq.name()}")

    target_track = None
    for track in seq.videoTracks():
        try:
            if track.name() == TARGET_TRACK_NAME:
                target_track = track
                break
        except Exception:
            continue

    if not target_track:
        print(f"No se encontro el track '{TARGET_TRACK_NAME}'")
        print("\nTracks disponibles:")
        for track in seq.videoTracks():
            try:
                print(f"  - {track.name()}")
            except Exception as e:
                print(f"  - <error leyendo nombre>: {e}")
        return

    explore_track(target_track)


if __name__ == "__main__":
    main()
