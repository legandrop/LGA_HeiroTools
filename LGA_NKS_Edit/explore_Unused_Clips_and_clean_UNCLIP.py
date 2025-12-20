# Version Cleaner - Dynamic clip processing
# Detects online/offline versions and safely removes offline ones

import hiero
import hiero.core.find_items
import os

# CONFIGURATION - Change this variable to process different clips
TARGET_CLIP_NAME = "PHLDA_013_010_Chroma_AutoDia_comp"  # Change this to any clip name


def cleanOfflineVersions():
    """Detect online/offline versions and remove offline ones safely"""

    projects = hiero.core.projects()
    if not projects:
        print("ERROR: No active project found.")
        return

    proj = projects[0]
    print(f"🧽 LIMPIANDO VERSIONES OFFLINE")
    print(f"📂 Proyecto: {proj.name()}")
    print(f"🎯 Clip objetivo: {TARGET_CLIP_NAME}")
    print(f"🔍 Buscando BinItems...")
    print()


    # Find ALL bin items for the target clip (there might be multiple with same name)
    target_bin_items = []

    for bin_item in hiero.core.findItems(proj, "BinItems"):
        if bin_item and hasattr(bin_item, "name") and bin_item.name() == TARGET_CLIP_NAME:
            if hasattr(bin_item, "items"):
                try:
                    versions = bin_item.items()
                    if len(versions) >= 1:  # Allow single versions too
                        target_bin_items.append(bin_item)
                except:
                    pass

    if not target_bin_items:
        print(f"ERROR: No BinItems '{TARGET_CLIP_NAME}' found or have no versions")
        return

    print(f"📋 Encontrados {len(target_bin_items)} BinItem(s) con nombre '{TARGET_CLIP_NAME}':")
    print()

    # Process each BinItem found
    total_processed = 0
    total_versions_removed = 0

    for bin_item_index, main_bin_item in enumerate(target_bin_items):
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

            for version in versions:
                if hasattr(version, "name") and version.name().startswith(TARGET_CLIP_NAME):
                    # Check if this version is active
                    is_active = (active_version and version == active_version)

                    # Check online/offline status
                    try:
                        if hasattr(version, "item"):
                            clip_item = version.item()
                            if clip_item and hasattr(clip_item, "mediaSource"):
                                media_source = clip_item.mediaSource()
                                if media_source and hasattr(media_source, "isMediaPresent"):
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

            # Process based on conditions
            if total_versions <= 1:
                print(f"⏭️  {main_bin_item.name()} ({file_type}): 1 versión - No procesado")
            elif online_count == 0:
                print(f"⚠️  {main_bin_item.name()} ({file_type}): {total_versions} versiones offline - No procesado (todas offline)")
            else:
                # Safe to remove offline versions
                versions_to_remove = []
                for version in versions:
                    if hasattr(version, "name") and version.name().startswith(TARGET_CLIP_NAME):
                        is_active = (active_version and version == active_version)
                        if not is_active:
                            try:
                                clip_item = version.item()
                                if clip_item and hasattr(clip_item, "mediaSource"):
                                    media_source = clip_item.mediaSource()
                                    if media_source and hasattr(media_source, "isMediaPresent") and not media_source.isMediaPresent():
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
                    print(f"🗑️  {main_bin_item.name()} ({file_type}): Eliminadas {removed_count} offline, conservadas {remaining} online")
                    total_versions_removed += removed_count
                else:
                    print(f"✅ {main_bin_item.name()} ({file_type}): {total_versions} versiones - No hay offline para eliminar")

            total_processed += 1

        except Exception as e:
            print(f"❌ Error procesando {main_bin_item.name()}: {e}")
            total_processed += 1

        except Exception as e:
            print(f"ERROR during processing: {e}")

    # Final summary
    print(f"\n📊 PROCESO COMPLETADO:")
    print(f"   • BinItems procesados: {total_processed}")
    print(f"   • Versiones offline eliminadas: {total_versions_removed}")

# Execute the cleaning
if __name__ == "__main__":
    cleanOfflineVersions()
