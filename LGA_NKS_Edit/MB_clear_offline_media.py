# -*- coding: utf-8 -*-

"""
This script scans the entire bin structure of the current Nuke Studio / Hiero
project to find and delete all clips that are offline.

It recursively navigates through all bins, identifies items with an offline
media source, and then removes them from the project. The process is logged
to the Script Editor console for review. This is useful for project
maintenance and cleanup.

USAGE:
This script is intended to be triggered from a menu item (via menu.py).

MIT License
Copyright (c) 2025 Marek Bires
"""

import hiero.core
import hiero.ui


def is_item_offline(bin_item):
    """
    Checks if a given BinItem is offline.

    Args:
        bin_item (hiero.core.BinItem): The bin item to check.

    Returns:
        bool: True if the item is offline, otherwise False.
    """
    if not isinstance(bin_item, hiero.core.BinItem):
        return False

    try:
        # Get the active item (Clip or Sequence) from the BinItem
        active_item = bin_item.activeItem()

        # Get the MediaSource from the active item
        media_source = active_item.mediaSource()

        # The isOffline() method directly tells us the status
        if media_source.isOffline():
            return True

    except AttributeError:
        # Some items (e.g., empty sequences) might not have a mediaSource.
        # We are not interested in these, so we skip them.
        return False

    return False


def scan_bin_recursively(current_bin, found_offline_items):
    """
    Recursively scans the given bin and all its sub-bins.
    Collects all offline BinItems into the provided list.

    Args:
        current_bin (hiero.core.Bin): The bin to scan.
        found_offline_items (list): The list to which found offline items will be added.
    """
    # Iterate through all items in the current bin
    for item in current_bin.items():
        # If the item is another Bin, call this function recursively
        if isinstance(item, hiero.core.Bin):
            scan_bin_recursively(item, found_offline_items)
        # If it's a BinItem, check if it's offline
        elif isinstance(item, hiero.core.BinItem):
            if is_item_offline(item):
                print(f"Found offline media: {item.name()}")
                found_offline_items.append(item)


def delete_offline_items(list_to_delete):
    """
    Deletes all BinItems from the given list.

    No special "unlinking" step is necessary before deletion,
    as the removeItem() method properly handles the removal
    of the item from its parent bin.

    Args:
        list_to_delete (list): A list of BinItem objects to be deleted.
    """
    count_to_delete = len(list_to_delete)

    if count_to_delete == 0:
        print("No offline media found to delete.")
        return

    print(f"\nAbout to delete {count_to_delete} offline items.")

    # Iterate through the list and delete each item
    for item in list_to_delete:
        try:
            # Get the item's parent bin
            parent_bin = item.parentBin()
            if parent_bin:
                print(f"Deleting '{item.name()}' from bin '{parent_bin.name()}'...")
                # Remove the item from the bin
                parent_bin.removeItem(item)
        except Exception as e:
            print(f"Failed to delete item '{item.name()}'. Error: {e}")

    print(f"\nDone. Successfully deleted {count_to_delete} offline items.")


def find_and_delete_offline_media():
    """
    Main function to be called from menu.py.
    It initiates the process of finding and deleting offline media in the active project.
    """
    print("=" * 50)
    print("Running script to find and delete offline media...")

    # Get the currently active project
    try:
        project = hiero.core.projects()[-1]
    except IndexError:
        print("Error: No project is open.")
        hiero.ui.showError("Error", "No project is open.")
        return

    print(f"Scanning project: '{project.name()}'")

    # A list where we will store the found offline items
    offline_items = []

    # Get the project's root bin (Clips Bin)
    root_bin = project.clipsBin()

    # Start the recursive search
    scan_bin_recursively(root_bin, offline_items)

    # Start the deletion of the found items
    delete_offline_items(offline_items)

    print("=" * 50)

# --- Example Usage (for testing directly in the Nuke Studio Script Editor) ---
# To test the script, uncomment the last line and execute it.
# In a production environment, this function would be called via menu.py.
#
# find_and_delete_offline_media()
