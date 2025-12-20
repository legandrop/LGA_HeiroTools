# Simple File Existence Check - Dynamic clip processing
# Just checks if expected files exist on disk

import hiero
import hiero.core.find_items
import os

# CONFIGURATION - Change this variable to check different clips
TARGET_CLIP_NAME = "PHLDA_013_050_Chroma_AutoDia_EditRef"  # Change this to any clip name

def checkFileExistence():
    """Simple check of file existence for versions"""

    projects = hiero.core.projects()
    if not projects:
        print('No active project found.')
        return

    proj = projects[0]
    print(f'CHECKING FILE EXISTENCE in project: {proj.name()}')
    print(f'Target clip: {TARGET_CLIP_NAME}')
    print('=' * 80)

    # Debug: List all BinItems to understand the structure
    print('ALL BIN ITEMS FOUND:')
    print('-' * 50)
    all_bin_items = []
    for bin_item in hiero.core.findItems(proj, 'BinItems'):
        if bin_item and hasattr(bin_item, 'name'):
            bin_name = bin_item.name()
            if hasattr(bin_item, 'items'):
                try:
                    versions = bin_item.items()
                    version_count = len(versions)
                    print(f'  {bin_name}: {version_count} versions')
                    all_bin_items.append((bin_item, version_count))

                    # Show version names for debugging
                    if version_count > 0:
                        version_names = [v.name() if hasattr(v, 'name') else 'unnamed' for v in versions[:5]]  # Show first 5
                        if version_count > 5:
                            version_names.append("...")
                        print(f'    Versions: {version_names}')

                except Exception as e:
                    print(f'  {bin_name}: ERROR getting versions - {e}')
            else:
                print(f'  {bin_name}: No items method')
    print()

    # Find the specific bin item for the target clip
    target_bin_item = None

    for bin_item in hiero.core.findItems(proj, 'BinItems'):
        if bin_item and hasattr(bin_item, 'name') and bin_item.name() == TARGET_CLIP_NAME:
            if hasattr(bin_item, 'items'):
                try:
                    versions = bin_item.items()
                    if len(versions) >= 1:  # Allow single versions too
                        target_bin_item = bin_item
                        print(f'FOUND TARGET BIN ITEM: {bin_item.name()} with {len(versions)} versions')
                        version_names = [v.name() if hasattr(v, 'name') else 'unnamed' for v in versions]
                        print(f'Versions: {version_names}')
                        if len(versions) == 1:
                            print(f'WARNING: This BinItem has only 1 version. Usually version cleaning is done on clips with multiple versions.')
                        print()
                        break
                except Exception as e:
                    print(f'Error checking versions for {bin_item.name()}: {e}')

    if not target_bin_item:
        print(f'ERROR: Target BinItem {TARGET_CLIP_NAME} not found or has no versions')
        print(f'Hint: Check the list above to see available BinItems and their version counts')
        return

    main_bin_item = target_bin_item

    # Check each version's file existence
    try:
        versions = main_bin_item.items()
        online_versions = []
        offline_versions = []

        for version in versions:
            if hasattr(version, 'name'):
                version_name = version.name()

                # USE HIERO'S NATIVE API: Check mediaSource for each version
                status = "UNKNOWN"
                details = ""

                try:
                    # METHOD 1: Access mediaSource through version.item() - this should work!
                    # version.item() returns the Clip object that contains mediaSource
                    status = "UNKNOWN"
                    details = ""

                    if hasattr(version, 'item'):
                        try:
                            clip_item = version.item()
                            if clip_item and hasattr(clip_item, 'mediaSource'):
                                media_source = clip_item.mediaSource()
                                if media_source:
                                    # Check if media is present using Hiero's native API
                                    if hasattr(media_source, 'isMediaPresent') and media_source.isMediaPresent():
                                        status = "ONLINE"
                                        details = "Media present (Hiero API)"
                                    else:
                                        status = "OFFLINE"
                                        details = "Media not present (Hiero API)"

                                    # Additional info from Hiero
                                    if hasattr(media_source, 'isOffline'):
                                        is_offline = media_source.isOffline()
                                        details += f" | isOffline: {is_offline}"

                                    # Try to get file path if available
                                    if hasattr(media_source, 'fileinfos') and media_source.fileinfos():
                                        file_info = media_source.fileinfos()[0]
                                        if hasattr(file_info, 'filename'):
                                            details += f" | Path: {file_info.filename()}"
                                else:
                                    status = "OFFLINE"
                                    details = "No MediaSource on clip"
                            else:
                                status = "OFFLINE"
                                details = "No clip item or no mediaSource"
                        except Exception as e:
                            status = "ERROR"
                            details = f"item().mediaSource() failed: {e}"
                    else:
                        status = "OFFLINE"
                        details = "No item() method on version"

                    # METHOD 2: Fallback - try to verify file existence if we have a path from Hiero
                    if status == "UNKNOWN" or status == "ERROR":
                        # If we got a path from Hiero's API, try to verify it exists
                        if hasattr(media_source, 'fileinfos') and media_source.fileinfos():
                            try:
                                file_info = media_source.fileinfos()[0]
                                if hasattr(file_info, 'filename'):
                                    file_path = str(file_info.filename())
                                    if os.path.exists(file_path):
                                        status = "ONLINE (fallback)"
                                        details = f"Files exist on disk: {file_path}"
                                    else:
                                        status = "OFFLINE (fallback)"
                                        details = f"Files not found: {file_path}"
                                else:
                                    status = "OFFLINE (fallback)"
                                    details = "No filename in fileinfo"
                            except Exception as e:
                                status = "OFFLINE (fallback)"
                                details = f"File check failed: {e}"
                        else:
                            status = "OFFLINE (fallback)"
                            details = "No file path available from Hiero"

                except Exception as e:
                    status = f"ERROR: {e}"
                    details = "Exception occurred"

                if status == "ONLINE" or status == "ONLINE (fallback)":
                    online_versions.append(version_name)
                elif status == "OFFLINE" or status == "OFFLINE (fallback)":
                    offline_versions.append(version_name)

                print(f'{version_name}: {status} - {details}')

        print()
        print(f'ONLINE versions ({len(online_versions)}): {online_versions}')
        print(f'OFFLINE versions ({len(offline_versions)}): {offline_versions}')

    except Exception as e:
        print(f'Error checking files: {e}')

# Execute the check
if __name__ == "__main__":
    checkFileExistence()