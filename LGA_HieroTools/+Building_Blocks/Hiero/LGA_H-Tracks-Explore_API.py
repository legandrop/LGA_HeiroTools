import hiero.core
import hiero.ui
import inspect

# Obtiene la secuencia activa
seq = hiero.ui.activeSequence()
if not seq:
    print("No hay secuencia activa.")
else:
    print("=" * 60)
    print("EXPLORACION DE API - TRACKS EN HIERO")
    print("=" * 60)

    # --- Metodos de hiero.core.Sequence relacionados con tracks ---
    print("\n[1] METODOS DE Sequence relacionados con 'track':")
    seq_methods = [m for m in dir(seq) if "track" in m.lower()]
    for m in seq_methods:
        try:
            attr = getattr(seq, m)
            sig = str(inspect.signature(attr)) if callable(attr) else "(property)"
            print(f"  seq.{m}{sig}")
        except Exception as e:
            print(f"  seq.{m}  -> error: {e}")

    # --- Todos los metodos de Sequence (sin underscore) ---
    print("\n[2] TODOS LOS METODOS PUBLICOS de Sequence:")
    all_seq = [m for m in dir(seq) if not m.startswith("_")]
    for m in all_seq:
        try:
            attr = getattr(seq, m)
            sig = str(inspect.signature(attr)) if callable(attr) else "(property)"
            print(f"  seq.{m}{sig}")
        except Exception:
            print(f"  seq.{m}")

    # --- Metodos de VideoTrack ---
    video_tracks = seq.videoTracks()
    if video_tracks:
        vt = video_tracks[0]
        print("\n[3] METODOS DE VideoTrack (primer track):")
        vt_methods = [m for m in dir(vt) if not m.startswith("_")]
        for m in vt_methods:
            try:
                attr = getattr(vt, m)
                sig = str(inspect.signature(attr)) if callable(attr) else "(property)"
                print(f"  track.{m}{sig}")
            except Exception:
                print(f"  track.{m}")

        # --- Info basica de tracks actuales ---
        print("\n[4] TRACKS ACTUALES EN LA SECUENCIA:")
        print(f"  Video tracks ({len(video_tracks)}):")
        for i, t in enumerate(video_tracks):
            print(f"    [{i}] '{t.name()}'  (index en seq: {t.trackIndex() if hasattr(t, 'trackIndex') else 'N/A'})")
        audio_tracks = seq.audioTracks()
        print(f"  Audio tracks ({len(audio_tracks)}):")
        for i, t in enumerate(audio_tracks):
            print(f"    [{i}] '{t.name()}'")

    # --- Metodos de hiero.core.Sequence en el modulo ---
    print("\n[5] METODOS EN hiero.core RELACIONADOS CON 'track' o 'sequence':")
    core_items = [m for m in dir(hiero.core) if "track" in m.lower() or "sequence" in m.lower()]
    for m in core_items:
        print(f"  hiero.core.{m}")

    print("\n" + "=" * 60)
    print("FIN DE EXPLORACION")
    print("=" * 60)
