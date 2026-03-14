"""
Script de exploración para entender cómo manejar clips offline en Hiero
Ejecutar en Hiero para ver qué métodos están disponibles
"""

import hiero.core
import hiero.ui

def explore_clip_offline_api():
    """Explorar la API de clips offline"""
    seq = hiero.ui.activeSequence()
    if not seq:
        print("No active sequence")
        return

    for track in seq.videoTracks():
        for item in track.items():
            if isinstance(item, hiero.core.EffectTrackItem):
                continue

            clip = item
            media_source = clip.source().mediaSource()

            print(f"\n=== Clip: {clip.name()} ===")
            print(f"isMediaPresent(): {media_source.isMediaPresent()}")

            # Explorar métodos disponibles en mediaSource
            methods = [m for m in dir(media_source) if not m.startswith('_')]
            print(f"Métodos mediaSource: {methods}")

            # Explorar métodos disponibles en el clip source
            source_methods = [m for m in dir(clip.source()) if not m.startswith('_')]
            print(f"Métodos source: {source_methods}")

            # Si está offline, intentar diferentes formas de ponerlo online
            if not media_source.isMediaPresent():
                print("Clip offline - intentando métodos:")

                # Método 1: refresh()
                if hasattr(media_source, 'refresh'):
                    try:
                        media_source.refresh()
                        print(f"Después de refresh(): {media_source.isMediaPresent()}")
                    except Exception as e:
                        print(f"Error en refresh(): {e}")

                # Método 2: recheck() si existe
                if hasattr(media_source, 'recheck'):
                    try:
                        media_source.recheck()
                        print(f"Después de recheck(): {media_source.isMediaPresent()}")
                    except Exception as e:
                        print(f"Error en recheck(): {e}")

                # Método 3: Verificar file paths
                fileinfos = media_source.fileinfos()
                if fileinfos:
                    print(f"File path: {fileinfos[0].filename()}")
                    import os
                    if os.path.exists(fileinfos[0].filename()):
                        print("File exists on disk")
                    else:
                        print("File does not exist on disk")

# Ejecutar exploración
explore_clip_offline_api()
