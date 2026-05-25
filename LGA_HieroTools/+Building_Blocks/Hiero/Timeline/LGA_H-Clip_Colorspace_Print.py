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
                print(f"\n=== CLIP: {clip.name()} ===")

                try:
                    # Obtener el espacio de color actual del clip
                    current_colorspace = clip.sourceMediaColourTransform()
                    print(f"Current Colorspace: {current_colorspace}")

                    # Obtener información del source
                    source = clip.source()
                    if source:
                        print(f"Source Name: {source.name()}")

                        # Intentar obtener información del media source
                        try:
                            media_source = source.mediaSource()
                            if media_source:
                                print(f"Media Source: {media_source}")

                                # Intentar obtener el colorspace desde el read node si existe
                                try:
                                    read_node = source.readNode()
                                    if read_node:
                                        print(f"Read Node encontrado: {read_node.name()}")
                                        if "colorspace" in read_node.knobs():
                                            nuke_colorspace = read_node["colorspace"].value()
                                            print(f"Nuke Colorspace (desde Read Node): {nuke_colorspace}")
                                        else:
                                            print("Read node no tiene knob 'colorspace'")
                                    else:
                                        print("No read node found")
                                except Exception as e:
                                    print(f"Could not get Nuke colorspace: {e}")

                                # Intentar obtener fileinfos
                                try:
                                    fileinfos = media_source.fileinfos()
                                    if fileinfos:
                                        print(f"File Path: {fileinfos[0].filename()}")
                                        print(f"Start Frame: {fileinfos[0].startFrame()}")
                                except Exception as e:
                                    print(f"Could not get file info: {e}")

                                # Obtener transforms OCIO disponibles
                                try:
                                    available_transforms = clip.getAvailableOcioColourTransforms()
                                    print(f"Available OCIO Transforms: {available_transforms}")
                                except Exception as e:
                                    print(f"Could not get available OCIO transforms: {e}")

                        except Exception as e:
                            print(f"Error accessing media source: {e}")

                    # Información adicional del bin item
                    try:
                        bin_item = source.binItem()
                        if bin_item:
                            print(f"Bin Item: {bin_item.name()}")
                            print(f"Active Version: {bin_item.activeVersion().name() if bin_item.activeVersion() else 'None'}")
                    except Exception as e:
                        print(f"Could not get bin item info: {e}")

                except Exception as e:
                    print(f"Error obteniendo colorspace: {e}")

                # Información adicional del clip
                try:
                    print(f"Clip Duration: {clip.duration()}")
                    print(f"Clip Timeline In: {clip.timelineIn()}")
                    print(f"Clip Timeline Out: {clip.timelineOut()}")

                except Exception as e:
                    print(f"Error obteniendo información adicional del clip: {e}")

                # Análisis y recomendaciones
                print(f"\n--- ANÁLISIS ---")
                try:
                    current = clip.sourceMediaColourTransform()
                    print(f"Colorspace actual: '{current}'")

                    # Comparar con nuestros transforms estándar
                    our_transforms = {
                        'rec709': 'Output - Rec.709',
                        'default': 'default',
                        'compositing_log': 'compositing_log'
                    }

                    print("Comparación con transforms estándar:")
                    for name, transform in our_transforms.items():
                        if current == transform:
                            print(f"  ✓ Ya tiene '{name}' ({transform})")
                        else:
                            print(f"  → Podría cambiarse a '{name}' ({transform})")

                    # Verificar si el transform actual está disponible
                    try:
                        available = clip.getAvailableOcioColourTransforms()
                        if current in available:
                            print(f"  ✓ El colorspace actual '{current}' está disponible en OCIO")
                        else:
                            print(f"  ⚠️ El colorspace actual '{current}' NO está disponible en OCIO")
                            print(f"     Transforms OCIO disponibles: {available}")
                    except Exception as e:
                        print(f"  ⚠️ No se pudo verificar disponibilidad en OCIO: {e}")

                except Exception as e:
                    print(f"Error en análisis: {e}")

    else:
        print("No clips selected.")
else:
    print("No active sequence found.")
