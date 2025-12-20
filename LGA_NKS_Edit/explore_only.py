# EXPLORATION ONLY - No elimina nada, solo muestra información

import hiero
import hiero.core.find_items
import os

def exploreProject():
    """Solo explora y muestra información del proyecto SIN eliminar nada"""

    projects = hiero.core.projects()
    if not projects:
        print("❌ ERROR: No hay proyecto activo")
        return

    proj = projects[0]
    print(f"🔍 EXPLORACIÓN DEL PROYECTO")
    print(f"📂 Proyecto: {proj.name()}")
    print("=" * 80)

    # 1. EXPLORAR SECUENCIAS
    print("\n🎬 SECUENCIAS ENCONTRADAS:")
    sequences = []
    for seq in hiero.core.findItems(proj, "Sequences"):
        if seq and hasattr(seq, 'name'):
            seq_name = seq.name()
            sequences.append(seq)
            print(f"   • {seq_name}")

            # Mostrar clips usados en esta secuencia
            if hasattr(seq, 'videoTracks'):
                clips_in_sequence = []
                for track in seq.videoTracks():
                    for track_item in track.items():
                        if hasattr(track_item, 'source'):
                            source = track_item.source()
                            if source and hasattr(source, 'name'):
                                clip_name = source.name()
                                if clip_name not in clips_in_sequence:
                                    clips_in_sequence.append(clip_name)

                if clips_in_sequence:
                    print(f"     📎 Clips usados: {', '.join(clips_in_sequence[:5])}")
                    if len(clips_in_sequence) > 5:
                        print(f"         ... y {len(clips_in_sequence) - 5} más")
                else:
                    print("     📎 Sin clips")

    print(f"\n📊 Total secuencias: {len(sequences)}")

    # 2. CREAR LISTA NEGRA DE SECUENCIAS CONOCIDAS
    print("\n🚫 CREANDO LISTA NEGRA DE SECUENCIAS:")
    known_sequences = set()
    for seq in sequences:
        if hasattr(seq, 'name'):
            seq_name = seq.name()
            known_sequences.add(seq_name)
            print(f"   • '{seq_name}' → EN LISTA NEGRA")

    print(f"\n📋 Total secuencias en lista negra: {len(known_sequences)}")

    # 3. EXPLORAR TODOS LOS ITEMS ENCONTRADOS EN "BinItems"
    print("\n🔍 EXPLORACIÓN DETALLADA DE findItems(proj, 'BinItems'):")
    all_items_found = []
    for item in hiero.core.findItems(proj, "BinItems"):
        all_items_found.append(item)
        item_name = item.name() if hasattr(item, 'name') else "SIN_NOMBRE"

        # Verificar si está en lista negra
        is_sequence = item_name in known_sequences

        # Analizar propiedades del item
        has_video_tracks = hasattr(item, 'videoTracks')
        has_items = hasattr(item, 'items')
        item_type = type(item).__name__

        print(f"   📋 Item: '{item_name}'")
        print(f"      • Tipo Python: {item_type}")
        print(f"      • Tiene videoTracks: {has_video_tracks}")
        print(f"      • Tiene items(): {has_items}")
        print(f"      • Está en lista negra: {is_sequence}")

        if is_sequence:
            print("      • ES UNA SECUENCIA CONOCIDA! ❌ (filtrada)")
        elif has_video_tracks:
            print("      • TIENE videoTracks (secuencia) ❌")
        elif has_items:
            try:
                versions_count = len(item.items())
                print(f"      • Versiones: {versions_count} ✅ (BinItem válido)")
            except:
                print("      • Error al contar versiones ⚠️")
        else:
            print("      • Tipo desconocido ❓")

        print()

    # Filtrar solo BinItems reales (excluyendo secuencias conocidas)
    print("\n📁 BIN ITEMS FILTRADOS (excluyendo secuencias):")
    bin_items = []
    for item in all_items_found:
        if item and hasattr(item, "name"):
            item_name = item.name()
            # NO es una secuencia conocida Y NO tiene videoTracks
            if item_name not in known_sequences and not hasattr(item, 'videoTracks'):
                # Es un BinItem real
                bin_items.append(item)

                # Determinar tipo
                file_type = "unknown"
                try:
                    if hasattr(item, 'items'):
                        versions = item.items()
                        if versions and hasattr(versions[0], "item"):
                            clip_item = versions[0].item()
                            if hasattr(clip_item, "mediaSource"):
                                media_source = clip_item.mediaSource()
                                if hasattr(media_source, "fileinfos") and media_source.fileinfos():
                                    file_info = media_source.fileinfos()[0]
                                    if hasattr(file_info, "filename"):
                                        path = file_info.filename()
                                        if path.endswith('.nk'):
                                            file_type = ".nk"
                                        elif path.endswith('.exr'):
                                            file_type = ".exr"
                                        elif path.endswith('.mov'):
                                            file_type = ".mov"
                except:
                    pass

                print(f"   • {item_name} ({file_type})")

    print(f"\n✅ BinItems reales encontrados: {len(bin_items)} (excluyendo {len(known_sequences)} secuencias)")

    print(f"\n📊 Total BinItems: {len(bin_items)}")

    # 3. ANÁLISIS CRUZADO
    print("\n🔍 ANÁLISIS CRUZADO:")
    print("Verificando qué BinItems se usan en secuencias...")

    used_clips = []
    unused_clips = []

    for bin_item in bin_items:
        bin_name = bin_item.name()
        is_used = False

        # Verificar si se usa en alguna secuencia
        for seq in sequences:
            if hasattr(seq, 'videoTracks'):
                for track in seq.videoTracks():
                    for track_item in track.items():
                        if hasattr(track_item, 'source'):
                            source = track_item.source()
                            if source and hasattr(source, 'name') and source.name() == bin_name:
                                is_used = True
                                break
                    if is_used:
                        break
            if is_used:
                break

        if is_used:
            used_clips.append(bin_name)
            print(f"   ✅ {bin_name}: USADO")
        else:
            unused_clips.append(bin_name)
            print(f"   🗑️  {bin_name}: NO USADO")

    print("\n📊 RESUMEN:")
    print(f"   • Secuencias: {len(sequences)}")
    print(f"   • BinItems totales: {len(bin_items)}")
    print(f"   • BinItems usados: {len(used_clips)}")
    print(f"   • BinItems no usados: {len(unused_clips)}")

    print("\n💡 Los BinItems marcados como 'NO USADO' son candidatos para eliminación")
    print("🔒 Este script SOLO EXPLORA - no elimina nada")


# Execute exploration
if __name__ == "__main__":
    exploreProject()