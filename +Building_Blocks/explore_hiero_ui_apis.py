"""
EXPLORACIÓN DE APIs DISPONIBLES EN HIERO.UI
===========================================

Objetivo: Confirmar qué métodos están disponibles en hiero.ui,
especialmente getTimelineEditor y otras APIs relacionadas con timelines.
"""

import hiero.core
import hiero.ui

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def explore_hiero_ui_methods():
    """Explora todos los métodos disponibles en hiero.ui"""
    debug_print("="*80)
    debug_print("EXPLORACIÓN: MÉTODOS DISPONIBLES EN HIERO.UI")
    debug_print("="*80)

    try:
        # Obtener todos los atributos de hiero.ui
        ui_attrs = dir(hiero.ui)

        debug_print(f"\n🔧 Total de atributos en hiero.ui: {len(ui_attrs)}")

        # Buscar métodos relacionados con timeline
        timeline_methods = [attr for attr in ui_attrs if 'timeline' in attr.lower()]
        debug_print(f"\n📋 MÉTODOS RELACIONADOS CON TIMELINE: {len(timeline_methods)}")
        for method in sorted(timeline_methods):
            debug_print(f"   • {method}")

        # Buscar métodos get*
        get_methods = [attr for attr in ui_attrs if attr.startswith('get')]
        debug_print(f"\n📋 MÉTODOS QUE EMPIEZAN CON 'get': {len(get_methods)}")
        for method in sorted(get_methods):
            debug_print(f"   • {method}")

        # Verificar específicamente getTimelineEditor
        debug_print(f"\n🎯 VERIFICACIÓN ESPECÍFICA:")
        if hasattr(hiero.ui, 'getTimelineEditor'):
            debug_print("   ✅ getTimelineEditor: EXISTE")
            try:
                # Intentar obtener la signatura
                method = getattr(hiero.ui, 'getTimelineEditor')
                debug_print(f"   📝 Tipo: {type(method)}")
                if callable(method):
                    debug_print("   📝 Es callable: SÍ")
                else:
                    debug_print("   📝 Es callable: NO")
            except Exception as e:
                debug_print(f"   ❌ Error al inspeccionar: {e}")
        else:
            debug_print("   ❌ getTimelineEditor: NO EXISTE")

        # Probar getTimelineEditor con una secuencia si existe
        try:
            projects = hiero.core.projects()
            if projects:
                project = projects[0]
                sequences = project.sequences()
                if sequences:
                    seq = sequences[0]
                    debug_print(f"\n🧪 PRUEBA CON SECUENCIA '{seq.name()}':")
                    try:
                        timeline = hiero.ui.getTimelineEditor(seq)
                        if timeline:
                            debug_print("   ✅ getTimelineEditor(secuencia): RETORNA TIMELINE")
                            debug_print(f"   📝 Tipo retornado: {type(timeline)}")
                            window = timeline.window()
                            if window and hasattr(window, 'objectName'):
                                debug_print(f"   📝 objectName: {window.objectName()}")
                        else:
                            debug_print("   ⚠️ getTimelineEditor(secuencia): RETORNA None (sin timeline)")
                    except Exception as e:
                        debug_print(f"   ❌ Error al llamar getTimelineEditor: {e}")
                else:
                    debug_print("   ⚠️ No hay secuencias para probar")
            else:
                debug_print("   ⚠️ No hay proyectos para probar")
        except Exception as e:
            debug_print(f"   ❌ Error en prueba: {e}")

        # Buscar otros métodos relacionados con secuencias
        seq_methods = [attr for attr in ui_attrs if 'sequence' in attr.lower()]
        debug_print(f"\n📋 MÉTODOS RELACIONADOS CON SEQUENCE: {len(seq_methods)}")
        for method in sorted(seq_methods):
            debug_print(f"   • {method}")

        # Verificar activeSequence
        if hasattr(hiero.ui, 'activeSequence'):
            debug_print("   ✅ activeSequence: EXISTE")
            try:
                active = hiero.ui.activeSequence()
                if active:
                    debug_print(f"   📝 Secuencia activa: {active.name()}")
                else:
                    debug_print("   📝 Secuencia activa: None")
            except Exception as e:
                debug_print(f"   ❌ Error al llamar activeSequence: {e}")
        else:
            debug_print("   ❌ activeSequence: NO EXISTE")

    except Exception as e:
        debug_print(f"❌ Error explorando hiero.ui: {e}")
        import traceback
        debug_print(traceback.format_exc())

def test_getTimelineEditor_for_all_sequences():
    """Prueba getTimelineEditor para todas las secuencias del proyecto"""
    debug_print("\n" + "="*80)
    debug_print("PRUEBA: getTimelineEditor PARA TODAS LAS SECUENCIAS")
    debug_print("="*80)

    try:
        projects = hiero.core.projects()
        if not projects:
            debug_print("❌ No hay proyectos")
            return

        project = projects[0]
        sequences = project.sequences()

        debug_print(f"📋 Total secuencias: {len(sequences)}")

        sequences_with_timelines = []
        sequences_without_timelines = []

        for seq in sequences:
            seq_name = seq.name()
            try:
                timeline = hiero.ui.getTimelineEditor(seq)
                if timeline:
                    window = timeline.window()
                    obj_name = window.objectName() if window and hasattr(window, 'objectName') else 'N/A'
                    debug_print(f"   ✅ {seq_name} → Timeline: {obj_name}")
                    sequences_with_timelines.append((seq_name, obj_name))
                else:
                    debug_print(f"   ❌ {seq_name} → Sin timeline")
                    sequences_without_timelines.append(seq_name)
            except Exception as e:
                debug_print(f"   ❌ {seq_name} → Error: {e}")

        debug_print(f"\n📊 RESULTADO:")
        debug_print(f"   • Con timeline: {len(sequences_with_timelines)}")
        debug_print(f"   • Sin timeline: {len(sequences_without_timelines)}")

        if sequences_with_timelines:
            debug_print("   🟢 Secuencias con timeline:")
            for seq_name, obj_name in sequences_with_timelines:
                debug_print(f"      • {seq_name} ({obj_name})")

        if sequences_without_timelines:
            debug_print("   🔴 Secuencias sin timeline:")
            for seq_name in sequences_without_timelines:
                debug_print(f"      • {seq_name}")

    except Exception as e:
        debug_print(f"❌ Error en prueba: {e}")
        import traceback
        debug_print(traceback.format_exc())

# EJECUCIÓN
debug_print("🚀 INICIANDO EXPLORACIÓN DE APIs HIERO.UI")
explore_hiero_ui_methods()
test_getTimelineEditor_for_all_sequences()

# PRUEBA ADICIONAL: Verificar isInAnyTimeline si existe
debug_print("\n" + "="*80)
debug_print("🔍 PRUEBA ADICIONAL: isInAnyTimeline")
debug_print("="*80)

try:
    if hasattr(hiero.ui, 'isInAnyTimeline'):
        debug_print("✅ hiero.ui.isInAnyTimeline: EXISTE")
        try:
            projects = hiero.core.projects()
            if projects:
                project = projects[0]
                sequences = project.sequences()
                if sequences:
                    for seq in sequences[:3]:  # Probar con las primeras 3
                        try:
                            result = hiero.ui.isInAnyTimeline(seq)
                            debug_print(f"   • {seq.name()}: isInAnyTimeline = {result}")
                        except Exception as e:
                            debug_print(f"   • {seq.name()}: Error = {e}")
        except Exception as e:
            debug_print(f"❌ Error probando isInAnyTimeline: {e}")
    else:
        debug_print("❌ hiero.ui.isInAnyTimeline: NO EXISTE")
except Exception as e:
    debug_print(f"❌ Error verificando isInAnyTimeline: {e}")

# PRUEBA ADICIONAL: Explorar métodos relacionados con panels/windows
debug_print("\n" + "="*80)
debug_print("🔍 EXPLORACIÓN: MÉTODOS DE GESTIÓN DE PANELS")
debug_print("="*80)

ui_methods = dir(hiero.ui)
panel_methods = [m for m in ui_methods if any(keyword in m.lower() for keyword in ['panel', 'window', 'close', 'open', 'show', 'hide'])]
debug_print(f"📋 Métodos relacionados con panels/ventanas: {len(panel_methods)}")
for method in sorted(panel_methods):
    debug_print(f"   • {method}")

# Verificar métodos específicos que podrían ser útiles
specific_methods_to_check = [
    'closeAllProjects', 'getAllPanels', 'panels', 'windows', 'getAllWindows',
    'closeAll', 'hideAll', 'showAll', 'minimizeAll', 'restoreAll'
]

debug_print(f"\n🎯 VERIFICACIÓN DE MÉTODOS ESPECÍFICOS:")
for method_name in specific_methods_to_check:
    if hasattr(hiero.ui, method_name):
        debug_print(f"   ✅ {method_name}: EXISTE")
        try:
            method = getattr(hiero.ui, method_name)
            if callable(method):
                debug_print(f"      📝 Es callable: SÍ")
            else:
                debug_print(f"      📝 Es callable: NO")
        except:
            debug_print(f"      ❌ Error inspeccionando")
    else:
        debug_print(f"   ❌ {method_name}: NO EXISTE")
