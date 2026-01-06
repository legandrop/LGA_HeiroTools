# =============================================================================
# TEST SIMPLE: Abrir secuencia "010-350" - EXACTAMENTE como Projects Panel
# =============================================================================

import hiero.core
import hiero.ui
from LGA_QtAdapter_HieroTools import QtCore

def _process_events():
    """EXACTAMENTE como Projects Panel."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def main():
    print("=" * 80)
    print("TEST SIMPLE: Abriendo secuencia '010-350'")
    print("=" * 80)
    
    # 1. Buscar la secuencia "010-350"
    projects = hiero.core.projects()
    if not projects:
        print("❌ No hay proyectos abiertos")
        return
    
    target_seq = None
    for proj in projects:
        for seq in proj.sequences():
            if seq.name() == "010-350":
                target_seq = seq
                break
        if target_seq:
            break
    
    if not target_seq:
        print("❌ No se encontró secuencia '010-350'")
        print("Secuencias disponibles:")
        for proj in projects:
            for seq in proj.sequences():
                print(f"  - {seq.name()}")
        return
    
    print(f"✅ Secuencia encontrada: {target_seq.name()}")
    
    # 2. Abrir en timeline - EXACTAMENTE como Projects Panel
    print("🔧 Llamando hiero.ui.openInTimeline(seq)...")
    
    try:
        hiero.ui.openInTimeline(target_seq)
        _process_events()
        print("✅ openInTimeline() completado")
        
        # Verificar
        active = hiero.ui.activeSequence()
        if active and active.name() == "010-350":
            print(f"✅ Secuencia activa: {active.name()}")
            print("✅ TODO FUNCIONÓ PERFECTO")
        else:
            print(f"⚠️ Secuencia activa: {active.name() if active else 'None'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

