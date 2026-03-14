# =============================================================================
# TEST ALTERNATIVO: Métodos alternativos para abrir secuencia "010-350"
# =============================================================================
# 🎯 OBJETIVO: Encontrar método que NO deje a Hiero 16 inestable
# 
# TEORÍA 2 CONFIRMADA: openInTimeline() deja H16 inestable
# Probamos métodos alternativos:
#   - OPCIÓN A: getTimelineEditor() + hacerlo visible sin .show()
#   - OPCIÓN B: TimelineEditor() constructor
#   - OPCIÓN C: openInTimeline() con flags
# =============================================================================

import hiero.core
import hiero.ui
from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtCore

def _process_events():
    """EXACTAMENTE como Projects Panel."""
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
# OPCIÓN A: Recuperar timeline oculto + hacerlo visible (SIN .show())
# =============================================================================
def test_option_a_get_timeline_and_show():
    """
    Estrategia: El timeline YA EXISTE oculto.
    En lugar de crear nuevo (openInTimeline), recuperarlo y hacerlo visible.
    """
    print("=" * 80)
    print("OPCIÓN A: getTimelineEditor() + hacerlo visible")
    print("=" * 80)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ No se encontró secuencia '010-350'")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    # 1. Recuperar timeline oculto existente
    print("🔧 Paso 1: Recuperando timeline oculto con getTimelineEditor()...")
    timeline = hiero.ui.getTimelineEditor(seq)
    
    if not timeline:
        print("❌ No se pudo obtener timeline")
        return
    
    print(f"✅ Timeline obtenido: {timeline}")
    
    # 2. Explorar métodos disponibles
    print("\n🔍 Explorando métodos disponibles en timeline:")
    timeline_methods = [m for m in dir(timeline) if not m.startswith('_')]
    
    # Buscar métodos relacionados con visibilidad/docking
    visibility_methods = [m for m in timeline_methods if any(x in m.lower() for x in ['visible', 'show', 'hide', 'dock', 'float', 'raise', 'activate'])]
    print(f"📋 Métodos de visibilidad/docking encontrados: {len(visibility_methods)}")
    for m in visibility_methods:
        print(f"   - {m}")
    
    # 3. Intentar hacerlo visible SIN usar .show() (que crea flotante)
    print("\n🔧 Paso 2: Intentando hacerlo visible (SIN .show() que crea flotante)...")
    
    try:
        # Método 1: setVisible(True) - ¿Diferente de .show()?
        if hasattr(timeline, 'setVisible'):
            print("   Probando: timeline.setVisible(True)...")
            timeline.setVisible(True)
            _process_events()
            print("   ✅ setVisible(True) ejecutado")
        
        # Método 2: raise_() - Traer al frente
        if hasattr(timeline, 'raise_'):
            print("   Probando: timeline.raise_()...")
            timeline.raise_()
            _process_events()
            print("   ✅ raise_() ejecutado")
        
        # Método 3: activateWindow() - Activar ventana
        if hasattr(timeline, 'activateWindow'):
            print("   Probando: timeline.activateWindow()...")
            timeline.activateWindow()
            _process_events()
            print("   ✅ activateWindow() ejecutado")
        
        # Método 4: setFocus() - Dar foco
        if hasattr(timeline, 'setFocus'):
            print("   Probando: timeline.setFocus()...")
            timeline.setFocus()
            _process_events()
            print("   ✅ setFocus() ejecutado")
        
        print("\n✅ Métodos de visibilidad ejecutados")
        print("👁️ Verificar manualmente si timeline aparece dockeado (no flotante)")
        
        # Verificar secuencia activa
        active = hiero.ui.activeSequence()
        if active and active.name() == "010-350":
            print(f"✅ Secuencia activa confirmada: {active.name()}")
        else:
            print(f"⚠️ Secuencia activa: {active.name() if active else 'None'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# =============================================================================
# OPCIÓN B: Constructor TimelineEditor() directo
# =============================================================================
def test_option_b_timeline_constructor():
    """
    Estrategia: Crear timeline desde constructor vacío.
    ¿Podemos configurarlo manualmente y evitar bug de openInTimeline?
    """
    print("\n" + "=" * 80)
    print("OPCIÓN B: TimelineEditor() constructor directo")
    print("=" * 80)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ No se encontró secuencia '010-350'")
        return
    
    print(f"✅ Secuencia encontrada: {seq.name()}")
    
    try:
        # 1. Crear timeline vacío
        print("🔧 Intentando crear timeline con constructor...")
        timeline = hiero.ui.TimelineEditor()
        print(f"✅ Timeline creado: {timeline}")
        
        # 2. Explorar métodos
        print("\n🔍 Explorando métodos del timeline creado:")
        timeline_methods = [m for m in dir(timeline) if not m.startswith('_')]
        
        # Buscar setSequence u otros métodos de configuración
        config_methods = [m for m in timeline_methods if any(x in m.lower() for x in ['sequence', 'set', 'init', 'config'])]
        print(f"📋 Métodos de configuración encontrados: {len(config_methods)}")
        for m in config_methods[:20]:  # Primeros 20
            print(f"   - {m}")
        
        # 3. ¿Tiene setSequence?
        if hasattr(timeline, 'setSequence'):
            print("\n🔧 ¡Encontrado! timeline.setSequence()")
            print("   Intentando asignar secuencia...")
            timeline.setSequence(seq)
            _process_events()
            print("   ✅ setSequence() ejecutado")
        else:
            print("\n❌ No tiene método setSequence()")
            print("   Métodos alternativos a explorar:")
            for m in config_methods:
                print(f"      - {m}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# =============================================================================
# OPCIÓN C: Explorar TimelineEditorCreationFlag
# =============================================================================
def test_option_c_creation_flags():
    """
    Estrategia: ¿openInTimeline() acepta flags que controlen la creación?
    """
    print("\n" + "=" * 80)
    print("OPCIÓN C: Explorar TimelineEditorCreationFlag")
    print("=" * 80)
    
    try:
        # 1. Ver qué es TimelineEditorCreationFlag
        print("🔍 Explorando hiero.ui.TimelineEditorCreationFlag...")
        flag_obj = hiero.ui.TimelineEditorCreationFlag
        print(f"✅ Objeto encontrado: {flag_obj}")
        print(f"   Tipo: {type(flag_obj)}")
        
        # 2. Ver qué atributos/valores tiene
        print("\n📋 Atributos disponibles:")
        flag_attrs = [a for a in dir(flag_obj) if not a.startswith('_')]
        for attr in flag_attrs:
            try:
                value = getattr(flag_obj, attr)
                print(f"   - {attr}: {value}")
            except:
                print(f"   - {attr}: (error al obtener)")
        
        # 3. ¿Se puede pasar a openInTimeline?
        print("\n🔧 Intentando llamar openInTimeline con flag...")
        print("   (Esto es experimental - puede fallar)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# =============================================================================
# OPCIÓN D: Análisis comparativo (solo logging, no modifica)
# =============================================================================
def test_option_d_analyze_existing():
    """
    Estrategia: Analizar timeline existente funcional para ver cómo está configurado.
    """
    print("\n" + "=" * 80)
    print("OPCIÓN D: Análisis de timeline existente funcional")
    print("=" * 80)
    
    # Buscar timeline que YA esté funcionando (de otra secuencia)
    print("🔍 Buscando timelines existentes y funcionales...")
    
    try:
        from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets
        app = QtWidgets.QApplication.instance()
        if not app:
            print("❌ No hay QApplication")
            return
        
        all_widgets = app.allWidgets()
        timelines_found = []
        
        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if 'TimelineEditor' in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    is_visible = widget.isVisible() if hasattr(widget, 'isVisible') else False
                    
                    if is_visible:  # Solo los visibles/funcionales
                        timelines_found.append({
                            'widget': widget,
                            'object_name': obj_name,
                            'visible': is_visible
                        })
            except:
                continue
        
        print(f"✅ Timelines visibles/funcionales encontrados: {len(timelines_found)}")
        
        if not timelines_found:
            print("⚠️ No hay timelines visibles para analizar")
            return
        
        # Analizar el primero funcional
        timeline = timelines_found[0]['widget']
        print(f"\n🔬 Analizando timeline: {timelines_found[0]['object_name']}")
        
        # Propiedades Qt relevantes
        print("📋 Propiedades Qt:")
        props = {
            'isVisible': timeline.isVisible() if hasattr(timeline, 'isVisible') else None,
            'isWindow': timeline.isWindow() if hasattr(timeline, 'isWindow') else None,
            'parent': type(timeline.parent()).__name__ if hasattr(timeline, 'parent') and timeline.parent() else None,
            'windowFlags': timeline.windowFlags() if hasattr(timeline, 'windowFlags') else None,
        }
        for key, value in props.items():
            print(f"   {key}: {value}")
        
        print("\n💡 Comparar estas propiedades con timeline creado por openInTimeline()")
        print("   para identificar diferencias que causan inestabilidad")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# =============================================================================
# MAIN: Ejecutar todas las opciones
# =============================================================================
def main():
    print("🚀 INICIANDO TESTS DE MÉTODOS ALTERNATIVOS")
    print("Objetivo: Encontrar método que NO deje Hiero 16 inestable")
    print("")
    
    # OPCIÓN A: Recuperar timeline oculto (MÁS PROMETEDOR)
    test_option_a_get_timeline_and_show()
    
    # OPCIÓN B: Constructor directo
    # test_option_b_timeline_constructor()
    
    # OPCIÓN C: Explorar flags
    # test_option_c_creation_flags()
    
    # OPCIÓN D: Análisis comparativo
    # test_option_d_analyze_existing()
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("📝 Verificar manualmente:")
    print("   1. ¿Timeline aparece dockeado (no flotante)?")
    print("   2. ¿Hiero permanece estable después?")
    print("   3. ¿Puedes borrar un clip sin crash?")
    print("=" * 80)


if __name__ == "__main__":
    main()
