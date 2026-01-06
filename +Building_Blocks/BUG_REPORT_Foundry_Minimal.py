# =============================================================================
# BUG REPORT PARA FOUNDRY - HIERO 16 openInTimeline() INSTABILITY
# =============================================================================
# Script mínimo reproducible - 100% reproducible en Hiero 16
#
# BUG SUMMARY:
#   hiero.ui.openInTimeline() crea timeline/viewer correctamente,
#   pero los deja en estado CORRUPTO/INESTABLE.
#   Operaciones posteriores causan crash de Hiero.
#
# REPRODUCTION STEPS:
#   1. Open any project with sequences in Hiero 16
#   2. Run this script
#   3. Timeline/viewer are created successfully
#   4. Select any clip in the created timeline
#   5. Press DELETE key
#   6. Result: Hiero CRASHES (silent C++ crash)
#
# EXPECTED BEHAVIOR (Hiero 15):
#   - Timeline/viewer created
#   - Can delete clips normally
#   - Hiero remains stable
#
# ACTUAL BEHAVIOR (Hiero 16):
#   - Timeline/viewer created
#   - Deleting clips causes Hiero crash
#   - Instability is 100% reproducible
#
# VERSIONS TESTED:
#   - Hiero 15.x: ✅ Works perfectly
#   - Hiero 16.x: ❌ Bug reproducible 100%
#
# EVIDENCE:
#   - Tested with isolated function calls
#   - Problem occurs with:
#     • hiero.ui.openInTimeline()
#     • hiero.ui.openInViewer()
#   - Problem does NOT occur with:
#     • hiero.ui.getTimelineEditor() (if timeline not shown)
#   - Problem is NOT related to processEvents()
#   - Logs: logs/debugPy.log
# =============================================================================

import hiero.core
import hiero.ui


def reproduce_bug():
    """
    Minimal reproducible test case for Hiero 16 instability bug.
    """
    print("=" * 80)
    print("BUG REPORT: Hiero 16 - openInTimeline() Instability")
    print("=" * 80)
    print()
    
    # Get any sequence from project
    projects = hiero.core.projects()
    if not projects:
        print("ERROR: No projects open. Please open a project first.")
        return
    
    sequences = projects[0].sequences()
    if not sequences:
        print("ERROR: No sequences in project.")
        return
    
    seq = sequences[0]
    print(f"✓ Using sequence: {seq.name()}")
    print()
    
    # Call the problematic API
    print("Calling hiero.ui.openInTimeline(seq)...")
    try:
        hiero.ui.openInTimeline(seq)
        print("✓ openInTimeline() completed without immediate crash")
        print("✓ Timeline and viewer should be visible")
    except Exception as e:
        print(f"✗ Exception: {e}")
        return
    
    print()
    print("=" * 80)
    print("MANUAL VERIFICATION REQUIRED:")
    print("=" * 80)
    print("1. Timeline and viewer are visible (✓)")
    print("2. Select any clip in the timeline")
    print("3. Press DELETE key to delete the clip")
    print()
    print("EXPECTED (Hiero 15): Clip deleted, Hiero remains stable")
    print("ACTUAL (Hiero 16):   Hiero CRASHES (silent C++ crash)")
    print()
    print("This bug demonstrates that openInTimeline() in Hiero 16")
    print("leaves the application in an unstable/corrupted state.")
    print("=" * 80)
    print()
    print("Additional evidence:")
    print("  - Bug is 100% reproducible")
    print("  - Also occurs with hiero.ui.openInViewer()")
    print("  - NOT related to processEvents()")
    print("  - Affects ALL programmatic timeline/viewer creation")
    print("=" * 80)


if __name__ == "__main__":
    reproduce_bug()

