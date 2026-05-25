# =============================================================================
# TEST CANDIDATOS PROMETEDORES - Métodos alternativos basados en exploración
# =============================================================================
# 🎯 OBJETIVO: Probar candidatos identificados en exploración exhaustiva
# 
# CANDIDATOS:
# 1. WindowManager.showWindow(timeline.window()) ⭐⭐⭐ MÁS PROMETEDOR
# 2. openInViewer() vs openInNewViewer()
# 3. Crear viewer PRIMERO, luego timeline
# 4. addWindow() + showWindow()
# =============================================================================

import hiero.core
import hiero.ui
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtCore

def _process_events():
    """Process Qt events."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def find_sequence(name):
    """Busca secuencia por nombre."""
    projects = hiero.core.projects()
    if not projects:
        return None
    
    for proj in projects:
        for seq in proj.sequences():
            if seq.name() == name:
                return seq
    return None


# =============================================================================
# CANDIDATO 1: WindowManager.showWindow(timeline.window()) ⭐⭐⭐
# =============================================================================
def test_candidato_1_windowmanager_showwindow():
    """
    CANDIDATO 1: Usar WindowManager.showWindow() con timeline.window()
    
    Fundamento:
    - Projects Panel usa wm.showWindow() para panels personalizados
    - Timeline tiene .window() que devuelve QWidget
    - ¿WindowManager puede mostrar widgets nativos de Hiero?
    """
    print("=" * 100)
    print("CANDIDATO 1: WindowManager.showWindow(timeline.window())")
    print("=" * 100)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ Secuencia no encontrada")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    try:
        # 1. Obtener timeline oculto
        print("\n🔧 Paso 1: Obteniendo timeline oculto...")
        timeline = hiero.ui.getTimelineEditor(seq)
        if not timeline:
            print("❌ No se pudo obtener timeline")
            return
        
        print(f"✅ Timeline obtenido: {timeline}")
        
        # 2. Obtener window del timeline
        print("\n🔧 Paso 2: Obteniendo window del timeline...")
        timeline_window = timeline.window()
        if not timeline_window:
            print("❌ Timeline no tiene window")
            return
        
        print(f"✅ Timeline window: {timeline_window}")
        print(f"   Tipo: {type(timeline_window)}")
        print(f"   ObjectName: {timeline_window.objectName() if hasattr(timeline_window, 'objectName') else 'N/A'}")
        
        # 3. Usar WindowManager.showWindow()
        print("\n🔧 Paso 3: Llamando WindowManager.showWindow()...")
        wm = hiero.ui.windowManager()
        print(f"✅ WindowManager: {wm}")
        
        result = wm.showWindow(timeline_window)
        print(f"✅ showWindow() ejecutado, retornó: {result}")
        
        _process_events()
        
        # 4. Verificar
        print("\n📊 Verificación:")
        active = hiero.ui.activeSequence()
        print(f"   Secuencia activa: {active.name() if active else 'None'}")
        
        print("\n👁️ Verificar manualmente:")
        print("   1. ¿Timeline aparece dockeado?")
        print("   2. ¿Viewer aparece?")
        print("   3. ¿Hiero permanece estable?")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# CANDIDATO 2: openInViewer() vs openInNewViewer()
# =============================================================================
def test_candidato_2_openinviewer():
    """
    CANDIDATO 2: Probar openInViewer() (diferente de openInNewViewer)
    
    Fundamento:
    - openInViewer() vs openInNewViewer() - APIs diferentes
    - Posiblemente openInViewer() use viewer existente integrado
    """
    print("\n" + "=" * 100)
    print("CANDIDATO 2: hiero.ui.openInViewer()")
    print("=" * 100)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ Secuencia no encontrada")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    try:
        print("\n🔧 Llamando hiero.ui.openInViewer(seq)...")
        print("   (Diferente de openInNewViewer que crea flotante)")
        
        result = hiero.ui.openInViewer(seq)
        print(f"✅ openInViewer() ejecutado, retornó: {result}")
        
        _process_events()
        
        # Verificar
        print("\n📊 Verificación:")
        active = hiero.ui.activeSequence()
        print(f"   Secuencia activa: {active.name() if active else 'None'}")
        
        current_viewer = hiero.ui.currentViewer()
        print(f"   Current viewer: {current_viewer}")
        
        print("\n👁️ Verificar manualmente:")
        print("   1. ¿Qué se creó/abrió?")
        print("   2. ¿Timeline dockeado o flotante?")
        print("   3. ¿Viewer dockeado o flotante?")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# CANDIDATO 3: Crear viewer PRIMERO, luego timeline
# =============================================================================
def test_candidato_3_viewer_first():
    """
    CANDIDATO 3: Crear viewer primero, LUEGO timeline
    
    Fundamento:
    - Hipótesis: openInTimeline() crashea porque intenta crear viewer también
    - Si viewer ya existe, tal vez no crashea
    """
    print("\n" + "=" * 100)
    print("CANDIDATO 3: Crear viewer PRIMERO, luego timeline")
    print("=" * 100)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ Secuencia no encontrada")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    try:
        # Paso 1: Crear viewer primero
        print("\n🔧 Paso 1: Creando viewer primero con openInViewer()...")
        viewer = hiero.ui.openInViewer(seq)
        print(f"✅ Viewer creado: {viewer}")
        _process_events()
        
        # Paso 2: LUEGO crear timeline
        print("\n🔧 Paso 2: Ahora llamando openInTimeline()...")
        print("   (Hipótesis: No crashea porque viewer ya existe)")
        
        timeline = hiero.ui.openInTimeline(seq)
        print(f"✅ openInTimeline() ejecutado, retornó: {timeline}")
        _process_events()
        
        # Verificar
        print("\n📊 Verificación:")
        active = hiero.ui.activeSequence()
        print(f"   Secuencia activa: {active.name() if active else 'None'}")
        
        print("\n👁️ Verificar manualmente:")
        print("   1. ¿Ambos creados correctamente?")
        print("   2. ¿Hiero permanece estable?")
        print("   3. ¿Puedes borrar clip sin crash?")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# CANDIDATO 4: addWindow() + showWindow()
# =============================================================================
def test_candidato_4_addwindow_showwindow():
    """
    CANDIDATO 4: Registrar con addWindow() ANTES de showWindow()
    
    Fundamento:
    - Tal vez timeline.window() necesita estar registrado en WindowManager
    - addWindow() primero, luego showWindow()
    """
    print("\n" + "=" * 100)
    print("CANDIDATO 4: WindowManager.addWindow() + showWindow()")
    print("=" * 100)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ Secuencia no encontrada")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    try:
        # 1. Obtener timeline y window
        print("\n🔧 Paso 1: Obteniendo timeline y window...")
        timeline = hiero.ui.getTimelineEditor(seq)
        timeline_window = timeline.window()
        
        print(f"✅ Timeline: {timeline}")
        print(f"✅ Window: {timeline_window}")
        
        # 2. WindowManager
        print("\n🔧 Paso 2: Obteniendo WindowManager...")
        wm = hiero.ui.windowManager()
        print(f"✅ WindowManager: {wm}")
        
        # 3. addWindow() primero
        print("\n🔧 Paso 3: Registrando con addWindow()...")
        try:
            wm.addWindow(timeline_window)
            print("✅ addWindow() ejecutado")
        except Exception as e:
            print(f"⚠️ addWindow() falló: {e}")
            print("   (Continuando con showWindow()...)")
        
        _process_events()
        
        # 4. showWindow() después
        print("\n🔧 Paso 4: Mostrando con showWindow()...")
        result = wm.showWindow(timeline_window)
        print(f"✅ showWindow() ejecutado, retornó: {result}")
        
        _process_events()
        
        # Verificar
        print("\n📊 Verificación:")
        active = hiero.ui.activeSequence()
        print(f"   Secuencia activa: {active.name() if active else 'None'}")
        
        print("\n👁️ Verificar manualmente:")
        print("   1. ¿Timeline aparece dockeado?")
        print("   2. ¿Funciona correctamente?")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN: Ejecutar candidatos en orden de prioridad
# =============================================================================
def main():
    print("🚀 PROBANDO CANDIDATOS PROMETEDORES")
    print("Basado en exploración exhaustiva de APIs")
    print("")
    
    results = {}
    
    # CANDIDATO 1 (más prometedor)
    print("\n🌟 PROBANDO CANDIDATO 1 (MÁS PROMETEDOR)...")
    results['candidato_1'] = test_candidato_1_windowmanager_showwindow()
    
    # CANDIDATO 2
    print("\n🌟 PROBANDO CANDIDATO 2...")
    results['candidato_2'] = test_candidato_2_openinviewer()
    
    # CANDIDATO 3
    print("\n🌟 PROBANDO CANDIDATO 3...")
    results['candidato_3'] = test_candidato_3_viewer_first()
    
    # CANDIDATO 4
    # print("\n🌟 PROBANDO CANDIDATO 4...")
    # results['candidato_4'] = test_candidato_4_addwindow_showwindow()
    
    # Resumen
    print("\n" + "=" * 100)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 100)
    for candidato, success in results.items():
        status = "✅ Sin errores" if success else "❌ Error"
        print(f"   {candidato}: {status}")
    
    print("\n📝 IMPORTANTE:")
    print("   - 'Sin errores' NO significa que funcionó correctamente")
    print("   - Verificar MANUALMENTE si timeline/viewer aparecen dockeados")
    print("   - Probar estabilidad: borrar clip, hacer operaciones")
    print("=" * 100)


if __name__ == "__main__":
    main()

