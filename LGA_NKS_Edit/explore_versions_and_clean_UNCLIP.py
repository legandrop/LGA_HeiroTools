# Version Cleaner - Dynamic clip processing
# Detects online/offline versions and safely removes offline ones

import hiero
import hiero.core.find_items
import os

# CONFIGURATION - Change this variable to process different clips
TARGET_CLIP_NAME = "PHLDA_013_050_Chroma_AutoDia_comp"  # Change this to any clip name


def cleanOfflineVersions():
    """Detect online/offline versions and remove offline ones safely"""

    projects = hiero.core.projects()
    if not projects:
        print("ERROR: No active project found.")
        return

    proj = projects[0]
    print(f"CLEANING OFFLINE VERSIONS in project: {proj.name()}")
    print(f"Target clip: {TARGET_CLIP_NAME}")
    print("=" * 80)


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

    print(f"Found {len(target_bin_items)} BinItem(s) with name '{TARGET_CLIP_NAME}'")
    print()

    # Process each BinItem found
    total_processed = 0
    total_versions_removed = 0

    for bin_item_index, main_bin_item in enumerate(target_bin_items):
        print(f"{'='*60}")
        print(f"PROCESSING BINITEM {bin_item_index + 1}/{len(target_bin_items)}")
        print(f"{'='*60}")

        print(f"BinItem: {main_bin_item.name()}")
        try:
            total_versions = len(main_bin_item.items())
            print(f"Total versions: {total_versions}")
        except:
            print("Total versions: Unknown")

        # Get active version
        active_version = None
        try:
            active_version = main_bin_item.activeVersion()
        except:
            pass

        active_name = active_version.name() if active_version and hasattr(active_version, 'name') else 'unknown'
        print(f"Active version: {active_name}")
        print()

        # Check each version's file existence and categorize
        try:
            versions = main_bin_item.items()
            online_versions = []
            offline_versions = []
            versions_to_remove = []

            print("DETECTING VERSION STATUS:")
            print("-" * 40)

            for version in versions:
                if hasattr(version, "name"):
                    version_name = version.name()

                    # Skip if not matching our target clip pattern
                    if not version_name.startswith(TARGET_CLIP_NAME):
                        continue

                    # Check if this version is active
                    is_active = (active_version and version == active_version)

                    # USE HIERO'S NATIVE API: Check mediaSource for each version
                    status = "UNKNOWN"
                    details = ""

                    try:
                        # METHOD 1: Access mediaSource through version.item()
                        if hasattr(version, "item"):
                            clip_item = version.item()
                            if clip_item and hasattr(clip_item, "mediaSource"):
                                media_source = clip_item.mediaSource()
                                if media_source and hasattr(media_source, "isMediaPresent"):
                                    # Check if media is present using Hiero's native API
                                    if media_source.isMediaPresent():
                                        status = "ONLINE"
                                        details = "Media present (Hiero API)"
                                    else:
                                        status = "OFFLINE"
                                        details = "Media not present (Hiero API)"

                                    # Additional info from Hiero
                                    if hasattr(media_source, "isOffline"):
                                        is_offline = media_source.isOffline()
                                        details += f" | isOffline: {is_offline}"

                                    # Try to get file path if available
                                    if (
                                        hasattr(media_source, "fileinfos")
                                        and media_source.fileinfos()
                                    ):
                                        try:
                                            file_info = media_source.fileinfos()[0]
                                            if hasattr(file_info, "filename"):
                                                details += f" | Path: {file_info.filename()}"
                                        except:
                                            pass
                                else:
                                    status = "OFFLINE"
                                    details = "No MediaSource disponible"
                            else:
                                status = "OFFLINE"
                                details = "No clip item disponible"
                        else:
                            status = "OFFLINE"
                            details = "No item() method disponible"

                    except Exception as e:
                        status = f"ERROR: {e}"
                        details = "Exception occurred"

                    # Categorize versions
                    if status == "ONLINE" or status == "ONLINE (fallback)":
                        online_versions.append(version_name)
                        print(f"  {version_name}: ONLINE - {details}")
                    elif status == "OFFLINE" or status == "OFFLINE (fallback)":
                        offline_versions.append(version_name)
                        # Only add to removal list if not active
                        if not is_active:
                            versions_to_remove.append((version_name, version, details))
                        print(f"  {version_name}: OFFLINE - {details}")
                    else:
                        print(f"  {version_name}: {status} - {details}")

            print()
            print(f"ONLINE versions ({len(online_versions)}): {online_versions}")
            print(f"OFFLINE versions ({len(offline_versions)}): {offline_versions}")
            print(f"Versions to remove ({len(versions_to_remove)}): {[v[0] for v in versions_to_remove]}")
            print()

            # Safety check - ensure we keep at least one online version
            if len(online_versions) == 0:
                print("ERROR: No online versions found! Aborting to prevent breaking the clip.")
                continue

            if len(online_versions) == 1 and active_version and active_version.name() in offline_versions:
                print("ERROR: Active version is offline and it's the only online version! Aborting.")
                continue

            # Proceed with removal
            if versions_to_remove:
                print("REMOVING OFFLINE VERSIONS:")
                print("-" * 40)

                removed_count = 0
                for version_name, version, details in versions_to_remove:
                    try:
                        main_bin_item.removeVersion(version)
                        print(f"  ✓ Removed: {version_name}")
                        removed_count += 1
                    except Exception as e:
                        print(f"  ✗ Failed to remove {version_name}: {e}")

                print(f"\nREMOVAL COMPLETE: {removed_count}/{len(versions_to_remove)} versions removed")
                total_versions_removed += removed_count

                # Verify remaining versions
                try:
                    remaining_versions = main_bin_item.items()
                    remaining_filtered = [v.name() for v in remaining_versions if hasattr(v, 'name') and v.name().startswith(TARGET_CLIP_NAME)]
                    print(f"Remaining versions: {len(remaining_filtered)}")
                    for v_name in sorted(remaining_filtered):
                        print(f"  * {v_name}")
                except Exception as e:
                    print(f"Error verifying remaining versions: {e}")
            else:
                print("No offline versions to remove.")

            total_processed += 1
            print()

        except Exception as e:
            print(f"ERROR during processing: {e}")

    # Final summary
    print(f"{'='*80}")
    print("SUMMARY - ALL BINITEMS PROCESSED")
    print(f"{'='*80}")
    print(f"BinItems processed: {total_processed}")
    print(f"Total versions removed: {total_versions_removed}")

# Execute the cleaning
if __name__ == "__main__":
    cleanOfflineVersions()
