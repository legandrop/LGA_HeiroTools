"""
____________________________________________________________________________________

  LGA_NKS_Flow_ExploreSequence v1.0 | Lega Pugliese
  Script de exploración para entender cómo obtener información de secuencias en Hiero
____________________________________________________________________________________
"""

import hiero.core
import hiero.ui


def getDstIn(trackItem):
    """Obtiene la posición de entrada del clip en el timeline"""
    return trackItem.timelineIn()


def getDstOut(trackItem):
    """Obtiene la posición de salida del clip en el timeline"""
    return trackItem.timelineOut()


def explore_sequence_info():
    """
    Función de exploración para entender la estructura de secuencias en Hiero
    """
    print("=== LGA_NKS_Flow_ExploreSequence ===")
    print("Explorando información de secuencias y clips...")

    # Obtener la secuencia activa y el editor de línea de tiempo
    seq = hiero.ui.activeSequence()
    if seq:  # Asegurarse de que hay una secuencia activa
        print(f"\n--- INFORMACIÓN DE LA SECUENCIA ---")
        print(f"Nombre de la secuencia: {seq.name()}")
        print(f"Tipo de objeto: {type(seq)}")
        print(f"Duración: {seq.duration()} frames")
        print(f"Frame rate: {seq.framerate()}")

        # Intentar obtener más información de la secuencia
        try:
            print(f"Path del proyecto: {seq.project().path()}")
            print(f"Nombre del proyecto: {seq.project().name()}")
        except Exception as e:
            print(f"Error obteniendo info del proyecto: {e}")

        # Obtener información del timeline editor
        te = hiero.ui.getTimelineEditor(seq)
        selected_clips = te.selection()

        print(f"\n--- INFORMACIÓN DEL TIMELINE EDITOR ---")
        print(f"Clips seleccionados: {len(selected_clips)}")

        # Obtener la instancia del reproductor y la posición del playhead
        current_viewer = hiero.ui.currentViewer()
        player = current_viewer.player() if current_viewer else None
        playhead_frame = player.time() if player else "No player available"

        print(f"Playhead en frame: {playhead_frame}")

        # Iterar sobre los clips seleccionados para imprimir la información deseada
        print(f"\n--- INFORMACIÓN DE CLIPS SELECCIONADOS ---")
        for i, shot in enumerate(selected_clips):
            print(f"\nClip #{i+1}:")
            if isinstance(shot, hiero.core.TrackItem):
                dstIn = getDstIn(shot)
                dstOut = getDstOut(shot)

                print(f"  Nombre: {shot.name()}")
                print(f"  Tipo: {type(shot)}")
                print(f"  DST In: {dstIn}")
                print(f"  DST Out: {dstOut}")
                print(f"  Duración: {dstOut - dstIn + 1} frames")
                print(f"  Playhead: {playhead_frame}")

                # Obtener información del source
                try:
                    source = shot.source()
                    if source:
                        print(f"  Source name: {source.name()}")
                        print(f"  Source type: {type(source)}")

                        # Obtener información del media source
                        media_source = source.mediaSource()
                        if media_source:
                            print(f"  Media source type: {type(media_source)}")
                            file_infos = media_source.fileinfos()
                            if file_infos:
                                print(f"  File path: {file_infos[0].filename()}")
                except Exception as e:
                    print(f"  Error obteniendo source info: {e}")

                # Obtener información del track
                try:
                    track = shot.parentTrack()
                    if track:
                        print(f"  Track name: {track.name()}")
                        print(f"  Track type: {type(track)}")
                except Exception as e:
                    print(f"  Error obteniendo track info: {e}")

            else:
                print(f"  El item seleccionado no es un track item: {type(shot)}")

        # Explorar información adicional de la secuencia
        print(f"\n--- INFORMACIÓN ADICIONAL DE LA SECUENCIA ---")
        try:
            # Intentar obtener todos los tracks
            video_tracks = seq.videoTracks()
            audio_tracks = seq.audioTracks()

            print(f"Video tracks: {len(video_tracks)}")
            for i, track in enumerate(video_tracks):
                print(f"  Video Track #{i+1}: {track.name()}")

            print(f"Audio tracks: {len(audio_tracks)}")
            for i, track in enumerate(audio_tracks):
                print(f"  Audio Track #{i+1}: {track.name()}")

        except Exception as e:
            print(f"Error explorando tracks: {e}")

        # Explorar métodos disponibles en la secuencia
        print(f"\n--- MÉTODOS DISPONIBLES EN LA SECUENCIA ---")
        seq_methods = [method for method in dir(seq) if not method.startswith("_")]
        print(
            f"Métodos disponibles ({len(seq_methods)}): {', '.join(seq_methods[:10])}..."
        )

        # Algunos métodos interesantes para probar
        interesting_methods = ["name", "project", "framerate", "format", "tracks"]
        for method in interesting_methods:
            if hasattr(seq, method):
                try:
                    result = getattr(seq, method)()
                    print(f"  {method}(): {result}")
                except Exception as e:
                    print(f"  {method}(): Error - {e}")

    else:
        print("No se encontró una secuencia activa.")

    print("\n=== Fin de la exploración ===")


def main():
    """Función principal"""
    explore_sequence_info()


if __name__ == "__main__":
    main()
