import hiero.core
import hiero.ui

# Script de investigación para encontrar el default colorspace de clips
# Objetivo: Entender cómo determinar cuál es el colorspace "default" para cada clip/proyecto

seq = hiero.ui.activeSequence()
if seq:
    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection()

    if selected_clips:
        print("="*100)
        print("INVESTIGACIÓN: ¿CÓMO OBTENER EL DEFAULT COLORSPACE?")
        print("="*100)

        for clip in selected_clips:
            print(f"\n🔍 ANALIZANDO CLIP: {clip.name()}")
            print("-" * 60)

            # 1. Información básica del clip y su estado actual
            print("1. ESTADO ACTUAL:")
            try:
                current_colorspace = clip.sourceMediaColourTransform()
                print(f"   Colorspace actual: '{current_colorspace}'")

                source = clip.source()
                if source:
                    print(f"   Source name: {source.name()}")
                    print(f"   Source type: {type(source)}")

                    # Información del bin item
                    bin_item = source.binItem()
                    if bin_item:
                        print(f"   Bin item: {bin_item.name()}")
                        active_version = bin_item.activeVersion()
                        if active_version:
                            print(f"   Active version: {active_version.name()}")

            except Exception as e:
                print(f"   Error obteniendo estado actual: {e}")

            # 2. Investigar el read node del source
            print("\n2. READ NODE ANALYSIS:")
            try:
                source = clip.source()
                if source:
                    read_node = source.readNode()
                    if read_node:
                        print(f"   Read node found: {read_node.name()}")
                        print(f"   Read node type: {type(read_node)}")

                        # Explorar knobs del read node
                        knobs = read_node.knobs()
                        print(f"   Total knobs: {len(knobs)}")

                        # Knobs relacionados con color
                        color_knobs = {k: v for k, v in knobs.items() if 'color' in k.lower()}
                        if color_knobs:
                            print("   Color-related knobs:")
                            for knob_name, knob in color_knobs.items():
                                try:
                                    value = knob.value()
                                    print(f"     {knob_name}: {value} (type: {type(value)})")
                                except Exception as e:
                                    print(f"     {knob_name}: [Error getting value: {e}]")

                        # Buscar knobs que puedan indicar default
                        default_knobs = {k: v for k, v in knobs.items() if 'default' in k.lower()}
                        if default_knobs:
                            print("   Default-related knobs:")
                            for knob_name, knob in default_knobs.items():
                                try:
                                    value = knob.value()
                                    print(f"     {knob_name}: {value}")
                                except Exception as e:
                                    print(f"     {knob_name}: [Error: {e}]")

                        # Knob 'colorspace' específicamente
                        if 'colorspace' in knobs:
                            cs_knob = knobs['colorspace']
                            print(f"   Colorspace knob value: {cs_knob.value()}")
                            print(f"   Colorspace knob type: {type(cs_knob)}")

                            # Si es un knob de enumeración, ver opciones
                            if hasattr(cs_knob, 'values'):
                                try:
                                    values = cs_knob.values()
                                    print(f"   Available colorspace options: {values}")
                                except:
                                    pass

                    else:
                        print("   No read node found")

            except Exception as e:
                print(f"   Error analizando read node: {e}")

            # 3. Investigar propiedades del proyecto
            print("\n3. PROJECT ANALYSIS:")
            try:
                project = clip.project()
                if project:
                    print(f"   Project: {project.name()}")

                    # Buscar propiedades relacionadas con color/OCIO
                    project_attrs = dir(project)
                    color_attrs = [attr for attr in project_attrs if 'color' in attr.lower() or 'ocio' in attr.lower()]
                    if color_attrs:
                        print("   Project color/ocio attributes:")
                        for attr in color_attrs:
                            try:
                                value = getattr(project, attr)
                                if not callable(value):
                                    print(f"     {attr}: {value}")
                                else:
                                    print(f"     {attr}: [callable]")
                            except Exception as e:
                                print(f"     {attr}: [Error: {e}]")

                    # Verificar si hay configuración OCIO
                    ocio_attrs = [attr for attr in project_attrs if 'ocio' in attr.lower()]
                    if ocio_attrs:
                        print("   OCIO configuration:")
                        for attr in ocio_attrs:
                            try:
                                value = getattr(project, attr)
                                print(f"     {attr}: {value}")
                            except Exception as e:
                                print(f"     {attr}: [Error: {e}]")

            except Exception as e:
                print(f"   Error analizando proyecto: {e}")

            # 4. Comparar con otros clips del mismo tipo
            print("\n4. COMPARISON WITH OTHER CLIPS:")
            try:
                # Obtener todos los clips del timeline
                all_clips = []
                for track in seq:
                    if hasattr(track, 'items'):
                        for item in track.items():
                            if not isinstance(item, hiero.core.EffectTrackItem):
                                all_clips.append(item)

                print(f"   Total clips in timeline: {len(all_clips)}")

                # Agrupar por tipo de source o características similares
                similar_clips = []
                for other_clip in all_clips:
                    if other_clip != clip:
                        try:
                            other_colorspace = other_clip.sourceMediaColourTransform()
                            other_source = other_clip.source()
                            if other_source:
                                # Comparar por nombre de archivo o path similar
                                current_path = ""
                                other_path = ""

                                try:
                                    current_fileinfos = clip.source().mediaSource().fileinfos()
                                    if current_fileinfos:
                                        current_path = current_fileinfos[0].filename()
                                except:
                                    pass

                                try:
                                    other_fileinfos = other_source.mediaSource().fileinfos()
                                    if other_fileinfos:
                                        other_path = other_fileinfos[0].filename()
                                except:
                                    pass

                                # Si tienen paths similares, podrían ser del mismo tipo
                                if current_path and other_path:
                                    current_dir = "/".join(current_path.split("/")[:-1])
                                    other_dir = "/".join(other_path.split("/")[:-1])
                                    if current_dir == other_dir:
                                        similar_clips.append((other_clip, other_colorspace))

                        except Exception as e:
                            print(f"   Error comparando clip {other_clip.name()}: {e}")

                if similar_clips:
                    print(f"   Clips similares encontrados: {len(similar_clips)}")
                    colorspaces = {}
                    for sim_clip, cs in similar_clips:
                        colorspaces[cs] = colorspaces.get(cs, 0) + 1

                    print("   Colorspaces en clips similares:")
                    for cs, count in colorspaces.items():
                        marker = " ← POSIBLE DEFAULT" if count > len(similar_clips) // 2 else ""
                        print(f"     '{cs}': {count} clips{marker}")
                else:
                    print("   No se encontraron clips similares para comparar")

            except Exception as e:
                print(f"   Error en comparación: {e}")

            # 5. Intentar métodos alternativos para obtener default
            print("\n5. ALTERNATIVE METHODS:")
            try:
                # Intentar obtener información del media source
                source = clip.source()
                if source:
                    media_source = source.mediaSource()
                    if media_source:
                        print(f"   Media source type: {type(media_source)}")

                        # Ver si hay métodos relacionados con default/color
                        media_attrs = dir(media_source)
                        color_attrs = [attr for attr in media_attrs if 'color' in attr.lower() or 'default' in attr.lower()]
                        if color_attrs:
                            print("   Media source color/default methods:")
                            for attr in color_attrs:
                                try:
                                    value = getattr(media_source, attr)
                                    if not callable(value):
                                        print(f"     {attr}: {value}")
                                    else:
                                        print(f"     {attr}: [callable method]")
                                except Exception as e:
                                    print(f"     {attr}: [Error: {e}]")

            except Exception as e:
                print(f"   Error en métodos alternativos: {e}")

            # 6. Conclusiones y recomendaciones
            print("\n6. CONCLUSIONES:")
            current_cs = "desconocido"
            try:
                current_cs = clip.sourceMediaColourTransform()
            except:
                pass

            print(f"   Colorspace actual: '{current_cs}'")
            print("   Para determinar el 'default', considerar:")
            print("   - El colorspace más común entre clips similares")
            print("   - La configuración OCIO del proyecto")
            print("   - El knob 'colorspace' del read node")
            print("   - Comparar con otros proyectos")

            print("-" * 60)

        print("\n" + "="*100)
        print("FIN DE LA INVESTIGACIÓN")
        print("="*100)
        print("\nRecomendaciones:")
        print("1. El 'default' parece ser el colorspace más común en clips similares")
        print("2. Revisar la configuración OCIO del proyecto")
        print("3. Comparar con el knob 'colorspace' del read node en Nuke")
        print("4. Considerar crear un mapping por tipo de archivo/proyecto")

    else:
        print("No clips selected.")
else:
    print("No active sequence found.")
