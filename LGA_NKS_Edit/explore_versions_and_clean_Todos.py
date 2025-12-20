# Version Cleaner - Process ALL clips in project
# Detects online/offline versions and safely removes offline ones from ALL BinItems

import hiero
import hiero.core.find_items
import os


def cleanOfflineVersions():
    """Detect online/offline versions and remove offline ones safely"""

    projects = hiero.core.projects()
    if not projects:
        print("ERROR: No active project found.")
        return

    proj = projects[0]
    print(f"🧽 LIMPIANDO VERSIONES OFFLINE - TODO EL PROYECTO")
    print(f"📂 Proyecto: {proj.name()}")
    print(f"🎯 Procesando TODOS los clips del proyecto")
    print(f"🔍 Buscando BinItems...")
    print()

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
        print(f"⚠️ No se encontraron BinItems con versiones en el proyecto")
        return

    print(f"📋 Encontrados {len(all_bin_items)} BinItem(s) para procesar:")
    print()

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
                if hasattr(version, "name") and version.name().startswith(bin_item_name):
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
                print(
                    f"⏭️  {main_bin_item.name()} ({file_type}): 1 versión - No procesado"
                )
            elif online_count == 0:
                print(
                    f"⚠️  {main_bin_item.name()} ({file_type}): {total_versions} versiones offline - No procesado (todas offline)"
                )
            else:
                # Safe to remove offline versions
                versions_to_remove = []
                for version in versions:
                    if hasattr(version, "name") and version.name().startswith(bin_item_name):
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
                    print(
                        f"🗑️  {main_bin_item.name()} ({file_type}): Eliminadas {removed_count} offline, conservadas {remaining} online"
                    )
                    total_versions_removed += removed_count
                else:
                    print(
                        f"✅ {main_bin_item.name()} ({file_type}): {total_versions} versiones - No hay offline para eliminar"
                    )

            total_processed += 1

        except Exception as e:
            print(f"❌ Error procesando {main_bin_item.name()}: {e}")
            total_processed += 1

    # Final summary
    print(f"\n📊 LIMPIEZA COMPLETADA - TODO EL PROYECTO:")
    print(f"   • BinItems procesados: {total_processed}")
    print(f"   • Versiones offline eliminadas: {total_versions_removed}")
    print(f"   • Proyecto optimizado ✅")


# Execute the cleaning
if __name__ == "__main__":
    cleanOfflineVersions()
