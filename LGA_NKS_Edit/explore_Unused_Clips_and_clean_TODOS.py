# All Unused Clips Cleaner - OBJETIVO 1
# Detects and removes ALL clips in project that are NOT used in any sequences

import hiero
import hiero.core.find_items
import os

# No configuration needed - processes ALL clips in project


def get_all_sequences(project):
    """Obtiene todas las secuencias del proyecto para verificar uso de clips"""
    sequences = []
    try:
        sequences = hiero.core.findItems(project, "Sequences")
        print(f"📋 Encontradas {len(sequences)} secuencias para verificar uso")
    except Exception as e:
        print(f"⚠️ Error obteniendo secuencias: {e}")
    return sequences


def is_bin_item_used_in_sequences(bin_item, sequences):
    """
    Verifica si un BinItem está siendo usado en alguna secuencia
    Retorna True si se usa, False si no se usa
    """
    if not sequences:
        return False

    try:
        bin_name = bin_item.name() if hasattr(bin_item, 'name') else ""

        # Verificar si el BinItem completo se usa en secuencias
        for sequence in sequences:
            if hasattr(sequence, 'videoTracks'):
                for track in sequence.videoTracks():
                    for track_item in track.items():
                        if hasattr(track_item, 'source'):
                            source = track_item.source()
                            if source:
                                # Comparar por nombre del BinItem (más confiable)
                                if hasattr(source, 'name') and source.name() == bin_name:
                                    return True

                                # También verificar si es el mismo objeto
                                if source == bin_item:
                                    return True

        # Para BinItems con versiones, verificar si alguna versión se usa
        if hasattr(bin_item, 'items'):
            versions = bin_item.items()
            for version in versions:
                if hasattr(version, 'name'):
                    version_name = version.name()

                    # Verificar si esta versión aparece en secuencias
                    for sequence in sequences:
                        if hasattr(sequence, 'videoTracks'):
                            for track in sequence.videoTracks():
                                for track_item in track.items():
                                    if hasattr(track_item, 'source'):
                                        source = track_item.source()
                                        if source and hasattr(source, 'name') and source.name() == version_name:
                                            return True

        # Para clips .nk (composiciones), ser más conservador
        if bin_name.endswith('.nk'):
            # Si el archivo existe, asumir que podría estar en uso
            try:
                if hasattr(bin_item, 'mediaSource') and bin_item.mediaSource():
                    media_source = bin_item.mediaSource()
                    if hasattr(media_source, 'isMediaPresent') and media_source.isMediaPresent():
                        # Ser conservador con .nk - si existe, no eliminar
                        return True
            except:
                pass

    except Exception as e:
        bin_name = bin_item.name() if hasattr(bin_item, 'name') else "unknown"
        print(f"⚠️ Error verificando uso del BinItem {bin_name}: {e}")
        # En caso de error, ser conservador y asumir que se usa
        return True

    return False


def cleanAllUnusedClips():
    """OBJETIVO 1: Elimina TODOS los clips del proyecto que NO se usan en secuencias"""

    projects = hiero.core.projects()
    if not projects:
        print("❌ ERROR: No hay proyecto activo")
        return

    proj = projects[0]
    print(f"🧹 ELIMINANDO TODOS LOS CLIPS NO UTILIZADOS - OBJETIVO 1")
    print(f"📂 Proyecto: {proj.name()}")
    print(f"🎯 Procesando TODOS los clips del proyecto")
    print(f"📋 Buscando BinItems y verificando uso en secuencias...")
    print()

    # Obtener todas las secuencias para verificación de uso
    sequences = get_all_sequences(proj)

    # DEBUG: Mostrar nombres de secuencias y crear lista negra
    known_sequences = set()
    if sequences:
        print("📋 Nombres de secuencias encontradas (lista negra):")
        for seq in sequences:
            if hasattr(seq, 'name'):
                seq_name = seq.name()
                known_sequences.add(seq_name)
                print(f"   • '{seq_name}' → EN LISTA NEGRA")
        print()

    # Find ALL bin items in the project (SOLO BinItems, no Sequences)
    all_bin_items = []

    for item in hiero.core.findItems(proj, "BinItems"):
        if item and hasattr(item, "name"):
            item_name = item.name()
            # Excluir secuencias conocidas Y items con videoTracks
            if item_name not in known_sequences and not hasattr(item, 'videoTracks'):
                # Es un BinItem real
                all_bin_items.append(item)

    if not all_bin_items:
        print(f"❌ No se encontraron BinItems en el proyecto")
        return

    print(f"📋 Encontrados {len(all_bin_items)} BinItem(s) reales en el proyecto (excluyendo {len(known_sequences)} secuencias):")
    print()

    # Process each BinItem found - DETECTAR Y ELIMINAR SI NO SE USA
    total_processed = 0
    used_clips = 0
    deleted_clips = 0

    for bin_item_index, bin_item in enumerate(all_bin_items):
        try:
            bin_name = bin_item.name()

            # Determinar tipo de archivo
            file_type = "unknown"
            try:
                if hasattr(bin_item, 'items'):
                    versions = bin_item.items()
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

            # VERIFICAR SI EL CLIP SE USA EN SECUENCIAS
            is_used = is_bin_item_used_in_sequences(bin_item, sequences)

            if is_used:
                print(f"✅ {bin_name} ({file_type}): CONSERVADO (usado en secuencias)")
                used_clips += 1
            else:
                # ELIMINAR CLIP NO UTILIZADO
                try:
                    # Obtener el bin contenedor para eliminar el item
                    parent_bin = None
                    for bin_container in hiero.core.findItems(proj, "Bins"):
                        if hasattr(bin_container, 'items') and bin_item in bin_container.items():
                            parent_bin = bin_container
                            break

                    if parent_bin:
                        parent_bin.removeItem(bin_item)
                        print(f"🗑️  {bin_name} ({file_type}): ELIMINADO (no usado en secuencias)")
                        deleted_clips += 1
                    else:
                        print(f"⚠️  {bin_name} ({file_type}): No se pudo eliminar (contenedor no encontrado)")

                except Exception as e:
                    print(f"❌ {bin_name} ({file_type}): Error eliminando - {e}")

            total_processed += 1

        except Exception as e:
            print(f"❌ Error procesando {bin_item.name()}: {e}")
            total_processed += 1

    # Final summary
    print(f"\n📊 LIMPIEZA COMPLETADA - OBJETIVO 1:")
    print(f"   • BinItems procesados: {total_processed}")
    print(f"   • Clips conservados: {used_clips}")
    print(f"   • Clips eliminados: {deleted_clips}")
    print(f"\n✅ Proyecto optimizado - Clips no utilizados eliminados")

# Execute the cleaning
if __name__ == "__main__":
    cleanAllUnusedClips()
