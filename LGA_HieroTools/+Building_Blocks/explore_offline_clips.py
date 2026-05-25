"""
Script de exploración para entender cómo manejar clips offline en Hiero.
Escribe el resultado a logs/explore_offline_clips.txt en la raíz de Startup.
"""

import os
import time
import hiero.core
import hiero.ui


def _open_output():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    out_path = os.path.join(logs_dir, "explore_offline_clips.txt")
    f = open(out_path, "w", encoding="utf-8")
    f.write(f"Explore Offline Clips - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Output: {out_path}\n\n")
    return f, out_path


def explore_clip_offline_api():
    """Explorar la API de clips offline (escribe a .txt en logs/)."""
    f, out_path = _open_output()
    print(f"[explore_offline_clips] escribiendo a: {out_path}")

    def w(line=""):
        f.write(str(line) + "\n")

    try:
        seq = hiero.ui.activeSequence()
        if not seq:
            w("No active sequence")
            return

        w(f"Active sequence: {seq.name()}")

        for track in seq.videoTracks():
            for item in track.items():
                if isinstance(item, hiero.core.EffectTrackItem):
                    continue

                clip = item
                try:
                    media_source = clip.source().mediaSource()
                except Exception as e:
                    w(f"\n=== Clip: {clip.name()} === (error obteniendo mediaSource: {e})")
                    continue

                w(f"\n=== Clip: {clip.name()} ===")
                try:
                    w(f"isMediaPresent(): {media_source.isMediaPresent()}")
                except Exception as e:
                    w(f"isMediaPresent() error: {e}")

                methods = [m for m in dir(media_source) if not m.startswith('_')]
                w(f"Métodos mediaSource: {methods}")

                source_methods = [m for m in dir(clip.source()) if not m.startswith('_')]
                w(f"Métodos source: {source_methods}")

                try:
                    is_present = media_source.isMediaPresent()
                except Exception:
                    is_present = True

                if not is_present:
                    w("Clip offline - intentando métodos:")

                    if hasattr(media_source, 'refresh'):
                        try:
                            media_source.refresh()
                            w(f"Después de refresh(): {media_source.isMediaPresent()}")
                        except Exception as e:
                            w(f"Error en refresh(): {e}")

                    if hasattr(media_source, 'recheck'):
                        try:
                            media_source.recheck()
                            w(f"Después de recheck(): {media_source.isMediaPresent()}")
                        except Exception as e:
                            w(f"Error en recheck(): {e}")

                    try:
                        fileinfos = media_source.fileinfos()
                        if fileinfos:
                            file_path = fileinfos[0].filename()
                            w(f"File path: {file_path}")
                            if os.path.exists(file_path):
                                w("File exists on disk")
                            else:
                                w("File does not exist on disk")
                    except Exception as e:
                        w(f"Error leyendo fileinfos: {e}")
    finally:
        f.flush()
        f.close()
        print(f"[explore_offline_clips] listo: {out_path}")


explore_clip_offline_api()
