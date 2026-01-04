"""
LGA_NKS_Flow_DoScan_Minimal v1.0
Test case MÍNIMO: Solo probar doScan en clip seleccionado
Sin lógica extra, solo para diagnosticar si doScan funciona
"""

import hiero.core
import hiero.ui

def main():
    # Obtener clip seleccionado en timeline
    seq = hiero.ui.activeSequence()
    if not seq:
        print("No active sequence")
        return

    te = hiero.ui.getTimelineEditor(seq)
    if not te:
        print("No timeline editor")
        return

    selected_clips = te.selection()
    if not selected_clips:
        print("No clips selected")
        return

    # Tomar el primer clip seleccionado
    clip = selected_clips[0]
    print(f"Testing doScan on clip: {clip.name()}")

    # Obtener binItem
    bin_item = clip.source().binItem()
    if not bin_item:
        print("No binItem found")
        return

    # Obtener versión activa
    active_version = bin_item.activeVersion()
    if not active_version:
        print("No active version found")
        return

    print(f"Active version: {active_version.name()}")

    # TEST MÍNIMO: Solo doScan
    print("Creating VersionScanner...")
    vc = hiero.core.VersionScanner()
    print("Calling doScan...")

    try:
        vc.doScan(active_version)
        print("doScan COMPLETED successfully!")

        # Ver qué versiones encontró
        versions = bin_item.items()
        print(f"Versions found after doScan: {len(versions)}")
        for v in versions:
            print(f"  - {v.name()}")

    except Exception as e:
        print(f"doScan FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
