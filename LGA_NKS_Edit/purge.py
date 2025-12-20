# Purge Unused Clips - VERSION-SAFE REMOVAL MODE
# Usage: Run directly in Hiero/Nuke
# Demonstrates the use of hiero.core.find_items module.
# Result: Safely removes specific offline versions without breaking clips
# TEMPORARY: Only processes clips starting with "PHLDA_013_050_"
# Compatible with Hiero/Nuke 11+ (PySide2) and Nuke 15
# Version 2.7 - Safe removal of offline unused versions

import hiero
import hiero.core.find_items
from collections import Counter

def purgeUnusedClips():
    """Remove unused clips from the active project"""

    # Get active project
    projects = hiero.core.projects()
    if not projects:
        print('No active project found.')
        return

    proj = projects[0]  # Use the first active project
  
    print('PURGING unused clip versions from project:', proj.name(), '(SAFE REMOVAL - OFFLINE VERSIONS ONLY)') 
    
    # Build a list of Projects
    SEQS = hiero.core.findItems(proj,"Sequences")

    # Build a list of BinItems (which contain clips and versions)
    all_bin_items = []
    for bin_item in hiero.core.findItems(proj, "BinItems"):
        if bin_item and hasattr(bin_item, 'name') and bin_item.name().startswith("PHLDA_013_050_"):
            all_bin_items.append(bin_item)

    print(f'TEMPORARY FILTER: Working only with {len(all_bin_items)} bin items starting with "PHLDA_013_050_"')

    if len(SEQS)==0:
        print('No sequences found in project - removing offline versions from filtered bin items')
        removed_count = 0
        for bin_item in all_bin_items:
            print(f'\n=== PROCESSING BIN ITEM: {bin_item.name()} ===')

            # Process versions of this bin item
            if hasattr(bin_item, 'versions'):
                versions = bin_item.versions()
                print(f'  - Has {len(versions)} versions')

                for version in versions:
                    # Check if version file exists
                    media_exists = True
                    file_path = None
                    try:
                        if hasattr(version, 'mediaSource') and version.mediaSource():
                            media_source = version.mediaSource()
                            if hasattr(media_source, 'fileinfos') and media_source.fileinfos():
                                file_path = str(media_source.fileinfos()[0].filename())
                                import os
                                media_exists = os.path.exists(file_path)
                    except Exception as e:
                        print(f'  - Version media check error: {e}')
                        continue

                    print(f'    - Version: {version.name()} - File exists: {media_exists}')

                    if media_exists:
                        print('    - DECISION: KEEP - File exists')
                        continue

                    # Safe to remove this offline version
                    try:
                        print('    - DECISION: REMOVE - File offline')
                        with proj.beginUndo('Safe Purge Unused Clip Versions'):
                            bin_item.removeVersion(version)
                        removed_count += 1
                        print('    - REMOVAL: SUCCESS')
                    except Exception as e:
                        print(f'    - REMOVAL: FAILED - {str(e)}')

        print(f'Removed {removed_count} offline versions from project with no sequences')
        return

    # SAFE REMOVAL MODE - Only remove offline versions that are not used
    print(f'Processing {len(all_bin_items)} filtered bin items for safe version removal...')

    removed_count = 0

    for bin_item in all_bin_items:
        bin_item_name = bin_item.name()
        print(f'\n=== PROCESSING BIN ITEM: {bin_item_name} ===')

        # Check if this bin item has versions
        if not hasattr(bin_item, 'versions'):
            print('  - No versions available')
            continue

        versions = bin_item.versions()
        print(f'  - Has {len(versions)} versions')

        # Process each version
        for version in versions:
            version_name = version.name() if hasattr(version, 'name') else str(version)
            print(f'\n  --- VERSION: {version_name} ---')

            # Check if this version is used in any sequence
            used_in_sequences = []
            for seq in SEQS:
                for track in seq:
                    for trackitem in track:
                        source = trackitem.source()
                        if source and source == version:  # Direct object comparison
                            used_in_sequences.append(f'{seq.name()}/Track_{track.name()}/Item_{trackitem.name()}')

            # Check if this version is the active one
            is_active = False
            try:
                active_version = bin_item.activeVersion()
                if active_version and active_version == version:
                    is_active = True
            except:
                pass

            # Check if media file exists
            media_exists = True
            file_path = None
            try:
                if hasattr(version, 'mediaSource') and version.mediaSource():
                    media_source = version.mediaSource()
                    if hasattr(media_source, 'fileinfos') and media_source.fileinfos():
                        file_path = str(media_source.fileinfos()[0].filename())
                        import os
                        media_exists = os.path.exists(file_path)
                        print(f'    - Media file: {file_path}')
                        print(f'    - File exists: {media_exists}')
                    else:
                        print('    - Media file: No file path available')
                else:
                    print('    - Media file: No media source')
            except Exception as e:
                print(f'    - Media file check error: {e}')

            print(f'    - Used in sequences: {len(used_in_sequences)} times')
            print(f'    - Is active version: {is_active}')

            # DECISION LOGIC - Only remove offline versions that are not used and not active
            if used_in_sequences:
                print(f'    - USAGE LOCATIONS: {used_in_sequences[:3]}' + ('...' if len(used_in_sequences) > 3 else ''))
                print('    - DECISION: KEEP - Used in sequences')
            elif is_active:
                print('    - DECISION: KEEP - Is active version')
            elif media_exists:
                print('    - DECISION: KEEP - File exists')
            else:
                print('    - DECISION: REMOVE - Not used, not active, file offline')
                try:
                    with proj.beginUndo('Safe Purge Unused Clip Versions'):
                        bin_item.removeVersion(version)
                    removed_count += 1
                    print('    - REMOVAL: SUCCESS')
                except Exception as e:
                    print(f'    - REMOVAL: FAILED - {str(e)}')

    print(f'\n=== PURGE COMPLETE ===')
    print(f'Removed {removed_count} offline versions safely (not used, not active)')
    if removed_count > 0:
        print('NOTE: Changes can be undone with Ctrl+Z in Hiero')

# Execute the purge when script is run
if __name__ == "__main__":
    purgeUnusedClips()
