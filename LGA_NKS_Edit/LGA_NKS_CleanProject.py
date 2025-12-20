"""
______________________________________________________________________

  LGA_NKS_CleanProject v2.01 | Sistema de Limpieza Segura de Hiero

  Script principal de limpieza automática que combina ambos objetivos:
  1. Eliminación de clips no utilizados en secuencias
  2. Limpieza de versiones offline en clips con múltiples versiones

  v2.01: Agregado mensaje final al usuario con resumen de limpieza
         Script principal que integra ambas funcionalidades de limpieza
         Implementa protección anti-secuencias con lista negra
         Compatible con todos los formatos (.exr, .mov, .nk)
         Logging detallado con debug_print para control de salida
  v2.0: Script principal que integra ambas funcionalidades de limpieza
        Implementa protección anti-secuencias con lista negra
        Compatible con todos los formatos (.exr, .mov, .nk)
        Logging detallado con debug_print para control de salida
______________________________________________________________________

"""

import hiero
import hiero.core.find_items
import nuke
import os

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)


def get_all_sequences(project):
    """Obtiene todas las secuencias del proyecto para verificar uso de clips"""
    sequences = []
    try:
        sequences = hiero.core.findItems(project, "Sequences")
        debug_print(f"📋 Encontradas {len(sequences)} secuencias para verificar uso")
    except Exception as e:
        debug_print(f"⚠️ Error obteniendo secuencias: {e}")
    return sequences


def is_bin_item_used_in_sequences(bin_item, sequences):
    """
    Verifica si un BinItem está siendo usado en alguna secuencia
    Retorna True si se usa, False si no se usa
    """
    if not sequences:
        return False

    try:
        bin_name = bin_item.name() if hasattr(bin_item, "name") else ""

        # Verificar si el BinItem completo se usa en secuencias
        for sequence in sequences:
            if hasattr(sequence, "videoTracks"):
                for track in sequence.videoTracks():
                    for track_item in track.items():
                        if hasattr(track_item, "source"):
                            source = track_item.source()
                            if source:
                                # Comparar por nombre del BinItem (más confiable)
                                if (
                                    hasattr(source, "name")
                                    and source.name() == bin_name
                                ):
                                    return True

                                # También verificar si es el mismo objeto
                                if source == bin_item:
                                    return True

        # Para BinItems con versiones, verificar si alguna versión se usa
        if hasattr(bin_item, "items"):
            versions = bin_item.items()
            for version in versions:
                if hasattr(version, "name"):
                    version_name = version.name()

                    # Verificar si esta versión aparece en secuencias
                    for sequence in sequences:
                        if hasattr(sequence, "videoTracks"):
                            for track in sequence.videoTracks():
                                for track_item in track.items():
                                    if hasattr(track_item, "source"):
                                        source = track_item.source()
                                        if (
                                            source
                                            and hasattr(source, "name")
                                            and source.name() == version_name
                                        ):
                                            return True

        # Para clips .nk (composiciones), ser más conservador
        if bin_name.endswith(".nk"):
            # Si el archivo existe, asumir que podría estar en uso
            try:
                if hasattr(bin_item, "mediaSource") and bin_item.mediaSource():
                    media_source = bin_item.mediaSource()
                    if (
                        hasattr(media_source, "isMediaPresent")
                        and media_source.isMediaPresent()
                    ):
                        # Ser conservador con .nk - si existe, no eliminar
                        return True
            except:
                pass

    except Exception as e:
        bin_name = bin_item.name() if hasattr(bin_item, "name") else "unknown"
        debug_print(f"⚠️ Error verificando uso del BinItem {bin_name}: {e}")
        # En caso de error, ser conservador y asumir que se usa
        return True

    return False


def cleanAllUnusedClips():
    """OBJETIVO 1: Elimina TODOS los clips del proyecto que NO se usan en secuencias"""

    projects = hiero.core.projects()
    if not projects:
        debug_print("❌ ERROR: No hay proyecto activo")
        return 0, 0, 0

    proj = projects[0]
    debug_print(f"🧹 ELIMINANDO TODOS LOS CLIPS NO UTILIZADOS - OBJETIVO 1")
    debug_print(f"📂 Proyecto: {proj.name()}")
    debug_print(f"🎯 Procesando TODOS los clips del proyecto")
    debug_print(f"📋 Buscando BinItems y verificando uso en secuencias...")
    debug_print()

    # Obtener todas las secuencias para verificación de uso
    sequences = get_all_sequences(proj)

    # DEBUG: Mostrar nombres de secuencias y crear lista negra
    known_sequences = set()
    if sequences:
        debug_print("📋 Nombres de secuencias encontradas (lista negra):")
        for seq in sequences:
            if hasattr(seq, "name"):
                seq_name = seq.name()
                known_sequences.add(seq_name)
                debug_print(f"   • '{seq_name}' → EN LISTA NEGRA")
        debug_print()

    # Find ALL bin items in the project (SOLO BinItems, no Sequences)
    all_bin_items = []

    for item in hiero.core.findItems(proj, "BinItems"):
        if item and hasattr(item, "name"):
            item_name = item.name()
            # Excluir secuencias conocidas Y items con videoTracks
            if item_name not in known_sequences and not hasattr(item, "videoTracks"):
                # Es un BinItem real
                all_bin_items.append(item)

    if not all_bin_items:
        debug_print(f"❌ No se encontraron BinItems en el proyecto")
        return 0, 0, 0

    debug_print(
        f"📋 Encontrados {len(all_bin_items)} BinItem(s) reales en el proyecto (excluyendo {len(known_sequences)} secuencias):"
    )
    debug_print()

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
                if hasattr(bin_item, "items"):
                    versions = bin_item.items()
                    if versions and hasattr(versions[0], "item"):
                        clip_item = versions[0].item()
                        if hasattr(clip_item, "mediaSource"):
                            media_source = clip_item.mediaSource()
                            if (
                                hasattr(media_source, "fileinfos")
                                and media_source.fileinfos()
                            ):
                                file_info = media_source.fileinfos()[0]
                                if hasattr(file_info, "filename"):
                                    path = file_info.filename()
                                    if path.endswith(".nk"):
                                        file_type = ".nk"
                                    elif path.endswith(".exr"):
                                        file_type = ".exr"
                                    elif path.endswith(".mov"):
                                        file_type = ".mov"
            except:
                pass

            # VERIFICAR SI EL CLIP SE USA EN SECUENCIAS
            is_used = is_bin_item_used_in_sequences(bin_item, sequences)

            if is_used:
                debug_print(f"✅ {bin_name} ({file_type}): CONSERVADO (usado en secuencias)")
                used_clips += 1
            else:
                # ELIMINAR CLIP NO UTILIZADO
                try:
                    # Obtener el bin contenedor para eliminar el item
                    parent_bin = None
                    for bin_container in hiero.core.findItems(proj, "Bins"):
                        if (
                            hasattr(bin_container, "items")
                            and bin_item in bin_container.items()
                        ):
                            parent_bin = bin_container
                            break

                    if parent_bin:
                        parent_bin.removeItem(bin_item)
                        debug_print(
                            f"🗑️  {bin_name} ({file_type}): ELIMINADO (no usado en secuencias)"
                        )
                        deleted_clips += 1
                    else:
                        debug_print(
                            f"⚠️  {bin_name} ({file_type}): No se pudo eliminar (contenedor no encontrado)"
                        )

                except Exception as e:
                    debug_print(f"❌ {bin_name} ({file_type}): Error eliminando - {e}")

            total_processed += 1

        except Exception as e:
            debug_print(f"❌ Error procesando {bin_item.name()}: {e}")
            total_processed += 1

    # Final summary
    debug_print(f"\n📊 LIMPIEZA COMPLETADA - OBJETIVO 1:")
    debug_print(f"   • BinItems procesados: {total_processed}")
    debug_print(f"   • Clips conservados: {used_clips}")
    debug_print(f"   • Clips eliminados: {deleted_clips}")
    debug_print(f"\n✅ Proyecto optimizado - Clips no utilizados eliminados")

    return total_processed, used_clips, deleted_clips


# Version Cleaner - Process ALL clips in project
# Detects online/offline versions and safely removes offline ones from ALL BinItems

import hiero
import hiero.core.find_items
import os


def cleanOfflineVersions():
    """Detect online/offline versions and remove offline ones safely"""

    projects = hiero.core.projects()
    if not projects:
        debug_print("ERROR: No active project found.")
        return 0, 0

    proj = projects[0]
    debug_print(f"🧽 LIMPIANDO VERSIONES OFFLINE - TODO EL PROYECTO")
    debug_print(f"📂 Proyecto: {proj.name()}")
    debug_print(f"🎯 Procesando TODOS los clips del proyecto")
    debug_print(f"🔍 Buscando BinItems...")
    debug_print()

    # Find ALL bin items in the project
    all_bin_items = []

    for bin_item in hiero.core.findItems(proj, "BinItems"):
        if bin_item and hasattr(bin_item, "name"):
            if hasattr(bin_item, "items"):
                try:
                    versions = bin_item.items()
                    if len(versions) >= 1:  # Only process BinItems that have versions
                        all_bin_items.append(bin_item)
                except:
                    pass

    if not all_bin_items:
        debug_print(f"⚠️ No se encontraron BinItems con versiones en el proyecto")
        return 0, 0

    debug_print(f"📋 Encontrados {len(all_bin_items)} BinItem(s) para procesar:")
    debug_print()

    # Process each BinItem found
    total_processed = 0
    total_versions_removed = 0

    for bin_item_index, main_bin_item in enumerate(all_bin_items):
        try:
            versions = main_bin_item.items()
            total_versions = len(versions)

            # Quick analysis without verbose logging
            online_count = 0
            offline_count = 0
            offline_to_remove = 0

            # Get active version
            active_version = None
            try:
                active_version = main_bin_item.activeVersion()
            except:
                pass

            bin_item_name = main_bin_item.name()

            for version in versions:
                if hasattr(version, "name") and version.name().startswith(
                    bin_item_name
                ):
                    # Check if this version is active
                    is_active = active_version and version == active_version

                    # Check online/offline status
                    try:
                        if hasattr(version, "item"):
                            clip_item = version.item()
                            if clip_item and hasattr(clip_item, "mediaSource"):
                                media_source = clip_item.mediaSource()
                                if media_source and hasattr(
                                    media_source, "isMediaPresent"
                                ):
                                    if media_source.isMediaPresent():
                                        online_count += 1
                                    else:
                                        offline_count += 1
                                        if not is_active:
                                            offline_to_remove += 1
                    except:
                        offline_count += 1

            # Determine file type from first version path
            file_type = "unknown"
            try:
                if versions and hasattr(versions[0], "item"):
                    clip_item = versions[0].item()
                    if hasattr(clip_item, "mediaSource"):
                        media_source = clip_item.mediaSource()
                        if (
                            hasattr(media_source, "fileinfos")
                            and media_source.fileinfos()
                        ):
                            file_info = media_source.fileinfos()[0]
                            if hasattr(file_info, "filename"):
                                path = file_info.filename()
                                if path.endswith(".nk"):
                                    file_type = ".nk"
                                elif path.endswith(".exr"):
                                    file_type = ".exr"
                                elif path.endswith(".mov"):
                                    file_type = ".mov"
            except:
                pass

            # Process based on conditions
            if total_versions <= 1:
                debug_print(
                    f"⏭️  {main_bin_item.name()} ({file_type}): 1 versión - No procesado"
                )
            elif online_count == 0:
                debug_print(
                    f"⚠️  {main_bin_item.name()} ({file_type}): {total_versions} versiones offline - No procesado (todas offline)"
                )
            else:
                # Safe to remove offline versions
                versions_to_remove = []
                for version in versions:
                    if hasattr(version, "name") and version.name().startswith(
                        bin_item_name
                    ):
                        is_active = active_version and version == active_version
                        if not is_active:
                            try:
                                clip_item = version.item()
                                if clip_item and hasattr(clip_item, "mediaSource"):
                                    media_source = clip_item.mediaSource()
                                    if (
                                        media_source
                                        and hasattr(media_source, "isMediaPresent")
                                        and not media_source.isMediaPresent()
                                    ):
                                        versions_to_remove.append(version)
                            except:
                                pass

                if versions_to_remove:
                    # Remove offline versions
                    removed_count = 0
                    for version in versions_to_remove:
                        try:
                            main_bin_item.removeVersion(version)
                            removed_count += 1
                        except:
                            pass

                    remaining = total_versions - removed_count
                    debug_print(
                        f"🗑️  {main_bin_item.name()} ({file_type}): Eliminadas {removed_count} offline, conservadas {remaining} online"
                    )
                    total_versions_removed += removed_count
                else:
                    debug_print(
                        f"✅ {main_bin_item.name()} ({file_type}): {total_versions} versiones - No hay offline para eliminar"
                    )

            total_processed += 1

        except Exception as e:
            debug_print(f"❌ Error procesando {main_bin_item.name()}: {e}")
            total_processed += 1

    # Final summary
    debug_print(f"\n📊 LIMPIEZA COMPLETADA - TODO EL PROYECTO:")
    debug_print(f"   • BinItems procesados: {total_processed}")
    debug_print(f"   • Versiones offline eliminadas: {total_versions_removed}")
    debug_print(f"   • Proyecto optimizado ✅")

    return total_processed, total_versions_removed


def cleanProjectComplete():
    """Ejecuta la limpieza completa del proyecto: clips no utilizados + versiones offline"""

    debug_print("🚀 INICIANDO LIMPIEZA COMPLETA DEL PROYECTO")
    debug_print("=" * 60)

    # Ejecutar limpieza de clips no utilizados
    processed_clips, used_clips, deleted_clips = cleanAllUnusedClips()

    debug_print()
    debug_print("-" * 60)
    debug_print()

    # Ejecutar limpieza de versiones offline
    processed_versions, deleted_versions = cleanOfflineVersions()

    debug_print()
    debug_print("=" * 60)
    debug_print("🎉 LIMPIEZA COMPLETA FINALIZADA")
    debug_print()

    # Mostrar mensaje al usuario con resultados
    message = f"""🧹 LIMPIEZA COMPLETA DEL PROYECTO FINALIZADA

📊 RESULTADOS:

• Clips procesados: {processed_clips}
• Clips eliminados (no utilizados): {deleted_clips}

• BinItems procesados (versiones): {processed_versions}
• Versiones offline eliminadas: {deleted_versions}

✅ Proyecto optimizado exitosamente"""

    try:
        nuke.message(message)
    except:
        # Fallback si nuke.message no está disponible
        print(message)


# Execute the cleaning
if __name__ == "__main__":
    cleanProjectComplete()
