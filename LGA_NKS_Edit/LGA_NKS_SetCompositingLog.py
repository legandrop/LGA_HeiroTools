# _________________________________________________
#
#   LGA_NKS_SetCompositingLog v1.0 | Lega
#   Cambia el color transform de los clips seleccionados a compositing_log
# _________________________________________________

import hiero.ui
import hiero.core

def set_compositing_log():
    """
    Cambia el sourceMediaColourTransform de los clips seleccionados a 'compositing_log'
    """
    try:
        # Obtener la secuencia activa
        seq = hiero.ui.activeSequence()
        if not seq:
            print("ERROR: No hay secuencia activa")
            return

        # Obtener el timeline editor y los clips seleccionados
        te = hiero.ui.getTimelineEditor(seq)
        selected_clips = te.selection()

        if not selected_clips:
            print("ERROR: No hay clips seleccionados")
            return

        # Cambiar el color transform de cada clip seleccionado
        clips_cambiados = 0
        for clip in selected_clips:
            try:
                clip.setSourceMediaColourTransform("compositing_log")
                clips_cambiados += 1
                print(f"✓ Cambiado: {clip.name()}")
            except Exception as e:
                print(f"✗ Error cambiando {clip.name()}: {e}")

        print(f"\nCompletado: {clips_cambiados} clips cambiados a compositing_log")

    except Exception as e:
        print(f"ERROR general: {e}")
        import traceback
        traceback.print_exc()

# Ejecutar la función cuando se llama el script directamente
if __name__ == "__main__":
    set_compositing_log()
