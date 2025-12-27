# _________________________________________________
#
#   LGA_NKS_ColorTransforms v1.01 | Lega
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

        # Si se pide 'default', detectar dinámicamente cuál es el real
        if transform_type == 'default':
            debug_print("  Detectando default colorspace dinámicamente...")
            # Usar el primer clip para detectar el default del proyecto
            try:
                selected_clips = cls.get_selected_clips()
                if selected_clips:
                    real_default = cls.detect_real_default_colorspace(selected_clips[0])
                    if real_default:
                        debug_print(f"  ✓ Default real detectado: '{real_default}'")
                        transform_value = real_default
                        transform_type = f"default ({real_default})"
                    else:
                        debug_print("  ✗ No se pudo detectar el default real")
                        raise ValueError("No se pudo detectar el default colorspace real")
                else:
                    raise ValueError("No hay clips seleccionados")
            except Exception as e:
                debug_print(f"  ✗ Error detectando default: {e}")
                raise ValueError(f"No se pudo detectar el default colorspace: {e}")
        else:
            # Para otros transforms, usar el mapping fijo
            if transform_type not in cls.TRANSFORMS:
                debug_print(f"✗ Transform '{transform_type}' no soportada. Opciones: {list(cls.TRANSFORMS.keys())}")
                raise ValueError(f"Transform '{transform_type}' no soportada. Opciones: {list(cls.TRANSFORMS.keys())}")

            transform_value = cls.TRANSFORMS[transform_type]

        debug_print(f"✓ Transform value final: '{transform_value}'")
        selected_clips = cls.get_selected_clips()

        clips_cambiados = 0
        clips_ya_correctos = 0
        clips_con_error = 0

        for clip in selected_clips:
            try:
                # Verificar el colorspace actual del clip
                current_transform = clip.sourceMediaColourTransform()
                debug_print(f"  Clip '{clip.name()}': actual='{current_transform}', deseado='{transform_value}'")

                # Si ya tiene el transform correcto, saltarlo
                if current_transform == transform_value:
                    debug_print(f"  ✓ Ya tiene el transform correcto: {clip.name()}")
                    clips_ya_correctos += 1
                    continue

                # Verificar que el transform esté disponible antes de aplicarlo
                try:
                    available_transforms = clip.getAvailableOcioColourTransforms()
                    if transform_value not in available_transforms:
                        debug_print(f"  ✗ Transform '{transform_value}' no disponible para {clip.name()}. Disponibles: {available_transforms}")
                        clips_con_error += 1
                        continue
                except Exception as e:
                    debug_print(f"  ⚠️ No se pudo verificar transforms disponibles para {clip.name()}: {e}")

                # Aplicar el transform
                clip.setSourceMediaColourTransform(transform_value)
                clips_cambiados += 1
                debug_print(f"  ✓ Cambiado a {transform_type}: {clip.name()}")

            except Exception as e:
                debug_print(f"  ✗ Error cambiando {clip.name()}: {e}")
                clips_con_error += 1

        debug_print(f"\nCompletado:")
        debug_print(f"  • Cambiados: {clips_cambiados}")
        debug_print(f"  • Ya correctos: {clips_ya_correctos}")
        debug_print(f"  • Con error: {clips_con_error}")

        return clips_cambiados

    @classmethod
    def get_available_transforms(cls, clip=None):
        """Obtiene los transforms OCIO disponibles. Si no se pasa clip, usa el primer clip seleccionado"""
        if clip is None:
            try:
                selected_clips = cls.get_selected_clips()
                clip = selected_clips[0] if selected_clips else None
            except:
                return []

        if clip is None:
            return []

        try:
            available = clip.getAvailableOcioColourTransforms()
            debug_print(f"✓ Transforms OCIO disponibles: {available}")
            return available
        except Exception as e:
            debug_print(f"✗ Error obteniendo transforms disponibles: {e}")
            return []

    @classmethod
    def detect_real_default_colorspace(cls, clip):
        """Detecta dinámicamente cuál es el default colorspace real para este clip/proyecto"""
        debug_print(">>> Detectando default colorspace real...")

        try:
            # Obtener el source y read node
            source = clip.source()
            if not source:
                debug_print("✗ No se pudo obtener source del clip")
                return None

            read_node = source.readNode()
            if not read_node:
                debug_print("✗ No se pudo obtener read node")
                return None

            # Obtener el knob de colorspace
            if 'colorspace' not in read_node.knobs():
                debug_print("✗ Read node no tiene knob 'colorspace'")
                return None

            colorspace_knob = read_node.knobs()['colorspace']

            # Intentar obtener las opciones disponibles
            try:
                available_options = colorspace_knob.values()
                debug_print(f"✓ Opciones de colorspace disponibles: {len(available_options)}")

                if available_options:
                    first_option = available_options[0]
                    debug_print(f"✓ Primer opción: '{first_option}'")

                    # Caso 1: 'default (xxxxx)' - extraer xxxxx
                    if first_option.startswith('default (') and first_option.endswith(')'):
                        real_default = first_option.split('(')[1].rstrip(')')
                        debug_print(f"✓ Default detectado del primer elemento: '{real_default}'")
                        return real_default

                    # Caso 2: Solo 'default' - usar out_colorspace del read node
                    elif first_option == 'default':
                        if 'out_colorspace' in read_node.knobs():
                            out_colorspace = read_node['out_colorspace'].value()
                            debug_print(f"✓ Default detectado de out_colorspace: '{out_colorspace}'")
                            return out_colorspace
                        else:
                            debug_print("✗ No se encontró knob 'out_colorspace'")

            except Exception as e:
                debug_print(f"⚠️ Error obteniendo opciones del knob: {e}")

            # Fallback: usar out_colorspace directamente
            if 'out_colorspace' in read_node.knobs():
                out_colorspace = read_node['out_colorspace'].value()
                debug_print(f"✓ Default fallback usando out_colorspace: '{out_colorspace}'")
                return out_colorspace

            # Último fallback: scene_linear (común en ACES)
            debug_print("⚠️ Usando fallback: 'scene_linear'")
            return 'scene_linear'

        except Exception as e:
            debug_print(f"✗ Error detectando default colorspace: {e}")
            return None

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

def diagnose_colorspace_issues():
    """Diagnostica problemas de colorspace en clips seleccionados"""
    debug_print(">>> DIAGNOSTICANDO PROBLEMAS DE COLORSPACE...")

    try:
        selected_clips = ColorTransformManager.get_selected_clips()

        for clip in selected_clips:
            print(f"\n{'='*60}")
            print(f"DIAGNÓSTICO: {clip.name()}")
            print(f"{'='*60}")

            # Colorspace actual
            try:
                current = clip.sourceMediaColourTransform()
                print(f"Colorspace actual: '{current}'")
            except Exception as e:
                print(f"Error obteniendo colorspace actual: {e}")

            # Transforms disponibles
            try:
                available = ColorTransformManager.get_available_transforms(clip)
                print(f"Transforms OCIO disponibles: {available}")

                # Verificar si nuestros transforms están disponibles
                our_transforms = ColorTransformManager.TRANSFORMS.values()
                missing_transforms = []
                available_transforms = []

                for t in our_transforms:
                    if t in available:
                        available_transforms.append(t)
                    else:
                        missing_transforms.append(t)

                print(f"✓ Nuestros transforms disponibles: {available_transforms}")
                if missing_transforms:
                    print(f"✗ Nuestros transforms NO disponibles: {missing_transforms}")

            except Exception as e:
                print(f"Error obteniendo transforms disponibles: {e}")

            # Información del source y media
            try:
                source = clip.source()
                if source:
                    print(f"Source: {source.name()}")

                    media_source = source.mediaSource()
                    if media_source:
                        fileinfos = media_source.fileinfos()
                        if fileinfos:
                            print(f"Archivo: {fileinfos[0].filename()}")

                    # Intentar obtener read node
                    try:
                        read_node = source.readNode()
                        if read_node and "colorspace" in read_node.knobs():
                            nuke_colorspace = read_node["colorspace"].value()
                            print(f"Nuke colorspace: '{nuke_colorspace}'")
                    except Exception as e:
                        print(f"No se pudo obtener Nuke colorspace: {e}")

            except Exception as e:
                print(f"Error explorando source: {e}")

            # Detectar cuál sería el default para este clip
            try:
                detected_default = ColorTransformManager.detect_real_default_colorspace(clip)
                if detected_default:
                    print(f"🎯 Default detectado para este clip/proyecto: '{detected_default}'")
                    current = "desconocido"
                    try:
                        current = clip.sourceMediaColourTransform()
                    except:
                        pass

                    if current == detected_default:
                        print("✓ El clip YA está en su default")
                    else:
                        print("→ El clip NO está en default")
                else:
                    print("⚠️ No se pudo detectar el default")
            except Exception as e:
                print(f"⚠️ Error detectando default: {e}")

        print(f"\n{'='*60}")
        print("FIN DEL DIAGNÓSTICO")
        print(f"{'='*60}")

    except Exception as e:
        debug_print(f"Error en diagnóstico: {e}")

# Para ejecución directa
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "diagnose":
            diagnose_colorspace_issues()
        elif command in ColorTransformManager.TRANSFORMS:
            debug_print(f">>> Ejecutando desde línea de comandos: {command}")
            ColorTransformManager.apply_transform(command)
        else:
            debug_print(f"Comando desconocido: {command}")
            debug_print("Uso: python LGA_NKS_ColorTransforms.py <rec709|default|compositing_log|diagnose>")
    else:
        debug_print("Uso: python LGA_NKS_ColorTransforms.py <rec709|default|compositing_log|diagnose>")
