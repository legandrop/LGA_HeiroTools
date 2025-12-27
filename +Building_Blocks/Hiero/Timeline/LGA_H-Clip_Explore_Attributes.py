import hiero.core
import hiero.ui

# Obtener la secuencia activa y el editor de linea de tiempo
seq = hiero.ui.activeSequence()
if seq:  # Asegurarse de que hay una secuencia activa
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection()

    # Iterar sobre los clips seleccionados
    if selected_clips:
        for clip in selected_clips:
            # Verificar si es un clip válido (no un efecto)
            if not isinstance(clip, hiero.core.EffectTrackItem):
                print(f"\n{'='*80}")
                print(f"EXPLORACIÓN COMPLETA DEL CLIP: {clip.name()}")
                print(f"{'='*80}")

                # Información básica del objeto
                print(f"\n--- INFORMACIÓN BÁSICA ---")
                print(f"Type: {type(clip)}")
                print(f"Class: {clip.__class__}")
                print(f"Module: {clip.__class__.__module__}")
                print(f"ID: {id(clip)}")
                print(f"Repr: {repr(clip)}")

                # Todos los atributos y métodos disponibles
                print(f"\n--- TODOS LOS ATRIBUTOS Y MÉTODOS (dir()) ---")
                all_attributes = dir(clip)
                print(f"Total de atributos/métodos: {len(all_attributes)}")

                # Separar en métodos y atributos
                methods = []
                attributes = []
                special_methods = []

                for attr in all_attributes:
                    if attr.startswith('_'):
                        special_methods.append(attr)
                    elif callable(getattr(clip, attr, None)):
                        methods.append(attr)
                    else:
                        attributes.append(attr)

                print(f"Métodos públicos: {len(methods)}")
                print(f"Atributos públicos: {len(attributes)}")
                print(f"Métodos especiales: {len(special_methods)}")

                # Mostrar métodos públicos
                print(f"\n--- MÉTODOS PÚBLICOS ---")
                for method in sorted(methods):
                    try:
                        attr_value = getattr(clip, method)
                        if callable(attr_value):
                            print(f"  {method}() -> {type(attr_value)}")
                    except:
                        print(f"  {method}() -> [Error accessing]")

                # Mostrar atributos públicos con sus valores
                print(f"\n--- ATRIBUTOS PÚBLICOS ---")
                for attr in sorted(attributes):
                    try:
                        value = getattr(clip, attr)
                        print(f"  {attr} = {value} ({type(value).__name__})")
                    except Exception as e:
                        print(f"  {attr} = [Error: {e}]")

                # Explorar propiedades específicas que podrían ser útiles
                print(f"\n--- PROPIEDADES ESPECÍFICAS DE COLOR Y MEDIA ---")

                # Probar métodos relacionados con color
                color_methods = [m for m in methods if 'color' in m.lower()]
                if color_methods:
                    print("Métodos relacionados con color:")
                    for method in color_methods:
                        try:
                            result = getattr(clip, method)()
                            print(f"  clip.{method}() = {result}")
                        except Exception as e:
                            print(f"  clip.{method}() -> Error: {e}")

                # Probar métodos relacionados con media/source
                media_methods = [m for m in methods if any(x in m.lower() for x in ['media', 'source', 'read'])]
                if media_methods:
                    print("Métodos relacionados con media/source:")
                    for method in media_methods:
                        try:
                            result = getattr(clip, method)()
                            print(f"  clip.{method}() = {result}")
                        except Exception as e:
                            print(f"  clip.{method}() -> Error: {e}")

                # Intentar acceder a propiedades comunes que podrían existir
                print("\n--- PROPIEDADES COMUNES (intentando acceso directo) ---")
                common_props = [
                    'sourceMediaColourTransform', 'colourTransform', 'colorTransform',
                    'mediaSource', 'source', 'binItem', 'readNode', 'node',
                    'name', 'duration', 'timelineIn', 'timelineOut',
                    'track', 'parentTrack', 'parent'
                ]

                for prop in common_props:
                    if hasattr(clip, prop):
                        try:
                            value = getattr(clip, prop)
                            if callable(value):
                                try:
                                    result = value()
                                    print(f"  clip.{prop}() = {result}")
                                except Exception as e:
                                    print(f"  clip.{prop}() -> Error calling: {e}")
                            else:
                                print(f"  clip.{prop} = {value}")
                        except Exception as e:
                            print(f"  clip.{prop} -> Error accessing: {e}")
                    else:
                        print(f"  clip.{prop} -> [No existe]")

                # Explorar el source si existe
                print(f"\n--- EXPLORACIÓN DEL SOURCE ---")
                try:
                    source = clip.source()
                    if source:
                        print(f"Source type: {type(source)}")
                        print(f"Source class: {source.__class__}")
                        print(f"Source attributes: {len(dir(source))}")

                        # Mostrar algunos métodos comunes del source
                        source_methods = ['name', 'mediaSource', 'binItem', 'readNode']
                        for method in source_methods:
                            if hasattr(source, method):
                                try:
                                    result = getattr(source, method)()
                                    print(f"  source.{method}() = {result}")
                                except Exception as e:
                                    print(f"  source.{method}() -> Error: {e}")
                    else:
                        print("No source available")
                except Exception as e:
                    print(f"Error exploring source: {e}")

                print(f"\n{'='*80}")

    else:
        print("No clips selected.")
else:
    print("No active sequence found.")
