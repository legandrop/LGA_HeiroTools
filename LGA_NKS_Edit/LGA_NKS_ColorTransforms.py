# _________________________________________________
#
#   LGA_NKS_ColorTransforms v1.0 | Lega
#   Módulo unificado para transformaciones de color de clips
#   Soporta: Rec.709, Default, Compositing Log
# _________________________________________________

import hiero.ui
import hiero.core

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

class ColorTransformManager:
    """Gestor centralizado para transformaciones de color de clips"""

    TRANSFORMS = {
        'rec709': 'Output - Rec.709',
        'default': 'default',
        'compositing_log': 'compositing_log'
    }

    @staticmethod
    def get_selected_clips():
        """Obtiene los clips seleccionados de la secuencia activa"""
        debug_print(">>> Obteniendo clips seleccionados...")
        seq = hiero.ui.activeSequence()
        if not seq:
            debug_print("✗ No hay secuencia activa")
            raise ValueError("No hay secuencia activa")

        te = hiero.ui.getTimelineEditor(seq)
        selected_clips = te.selection()

        if not selected_clips:
            debug_print("✗ No hay clips seleccionados")
            raise ValueError("No hay clips seleccionados")

        debug_print(f"✓ Encontrados {len(selected_clips)} clips seleccionados")
        return selected_clips

    @classmethod
    def apply_transform(cls, transform_type):
        """Aplica una transformación de color específica"""
        debug_print(f">>> Aplicando transform '{transform_type}'...")

        if transform_type not in cls.TRANSFORMS:
            debug_print(f"✗ Transform '{transform_type}' no soportada. Opciones: {list(cls.TRANSFORMS.keys())}")
            raise ValueError(f"Transform '{transform_type}' no soportada. Opciones: {list(cls.TRANSFORMS.keys())}")

        transform_value = cls.TRANSFORMS[transform_type]
        debug_print(f"✓ Transform value: '{transform_value}'")

        selected_clips = cls.get_selected_clips()

        clips_cambiados = 0
        for clip in selected_clips:
            try:
                clip.setSourceMediaColourTransform(transform_value)
                clips_cambiados += 1
                debug_print(f"✓ Cambiado a {transform_type}: {clip.name()}")
            except Exception as e:
                debug_print(f"✗ Error cambiando {clip.name()}: {e}")

        debug_print(f"\nCompletado: {clips_cambiados} clips cambiados a {transform_type}")
        return clips_cambiados

# Funciones de conveniencia para uso directo
def set_rec709():
    """Cambia clips seleccionados a Rec.709"""
    debug_print(">>> Ejecutando set_rec709...")
    return ColorTransformManager.apply_transform('rec709')

def set_default():
    """Cambia clips seleccionados a default"""
    debug_print(">>> Ejecutando set_default...")
    return ColorTransformManager.apply_transform('default')

def set_compositing_log():
    """Cambia clips seleccionados a compositing_log"""
    debug_print(">>> Ejecutando set_compositing_log...")
    return ColorTransformManager.apply_transform('compositing_log')

# Para ejecución directa
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transform_type = sys.argv[1]
        debug_print(f">>> Ejecutando desde línea de comandos: {transform_type}")
        ColorTransformManager.apply_transform(transform_type)
    else:
        debug_print("Uso: python LGA_NKS_ColorTransforms.py <rec709|default|compositing_log>")
