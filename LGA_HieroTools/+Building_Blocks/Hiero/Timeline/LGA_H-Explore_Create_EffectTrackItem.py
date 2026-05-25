"""
Script de exploración para entender cómo crear EffectTrackItem en Hiero
"""

import hiero.core
import hiero.ui
import nuke

def explore_effect_creation():
    """Explora diferentes formas de crear EffectTrackItem"""
    
    print("=" * 80)
    print("🔍 EXPLORACIÓN: Creación de EffectTrackItem")
    print("=" * 80)
    
    # Obtener secuencia activa
    seq = hiero.ui.activeSequence()
    if not seq:
        print("❌ No hay secuencia activa")
        return
    
    # Buscar track BurnIn
    track = None
    for t in seq.videoTracks():
        if t.name() == "BurnIn":
            track = t
            break
    
    if not track:
        print("❌ No se encontró track BurnIn")
        return
    
    print(f"✅ Track 'BurnIn' encontrado")
    
    # Obtener un EffectTrackItem existente para analizar
    items = track.subTrackItems()
    existing_effect = None
    if items:
        for item in items:
            effect_item = item[0]
            if isinstance(effect_item, hiero.core.EffectTrackItem):
                existing_effect = effect_item
                break
    
    if not existing_effect:
        print("⚠️ No hay efectos existentes para analizar")
        return
    
    print(f"\n📋 Analizando EffectTrackItem existente: '{existing_effect.name()}'")
    
    # Analizar el EffectTrackItem existente
    print("\n" + "-" * 80)
    print("PROPIEDADES DEL EffectTrackItem:")
    print("-" * 80)
    
    # Obtener el nodo
    node = existing_effect.node()
    print(f"  Nodo: {node.name() if node else 'None'}")
    print(f"  Clase del nodo: {node.Class() if node else 'None'}")
    
    # Analizar métodos disponibles
    print(f"\n📚 MÉTODOS DISPONIBLES EN EffectTrackItem:")
    methods = [m for m in dir(existing_effect) if not m.startswith('_')]
    for method in sorted(methods):
        print(f"  - {method}")
    
    # Analizar cómo se creó (mirar el tipo y constructor)
    print(f"\n🔧 CONSTRUCTOR DE EffectTrackItem:")
    print(f"  Tipo: {type(existing_effect)}")
    print(f"  Módulo: {type(existing_effect).__module__}")
    
    # Intentar crear un nodo Text2
    print(f"\n🧪 PRUEBA: Crear nodo Text2...")
    try:
        test_node = nuke.createNode('Text2', inpanel=False)
        if test_node:
            print(f"  ✅ Nodo creado: {test_node.name()}")
            
            # Probar diferentes formas de crear EffectTrackItem
            print(f"\n🧪 PRUEBA 1: EffectTrackItem(node)")
            try:
                effect1 = hiero.core.EffectTrackItem(test_node)
                print(f"  ✅ Éxito: {effect1}")
                print(f"  Tipo: {type(effect1)}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print(f"\n🧪 PRUEBA 2: EffectTrackItem(node, timeline_in, timeline_out)")
            try:
                effect2 = hiero.core.EffectTrackItem(test_node, 0, 100)
                print(f"  ✅ Éxito: {effect2}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print(f"\n🧪 PRUEBA 3: Buscar otros constructores...")
            # Buscar métodos de creación en el módulo
            import inspect
            if hasattr(hiero.core, 'EffectTrackItem'):
                sig = inspect.signature(hiero.core.EffectTrackItem.__init__)
                print(f"  Signatura del constructor: {sig}")
            
            # Limpiar nodo de prueba
            nuke.delete(test_node)
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Analizar cómo se agrega al track
    print(f"\n📚 MÉTODOS DISPONIBLES EN TRACK para agregar efectos:")
    track_methods = [m for m in dir(track) if 'effect' in m.lower() or 'add' in m.lower()]
    for method in sorted(track_methods):
        print(f"  - {method}")
    
    # Analizar el knob 'font'
    if node and 'font' in node.knobs():
        print(f"\n🔤 ANÁLISIS DEL KNOB 'font':")
        font_knob = node['font']
        print(f"  Tipo: {type(font_knob)}")
        print(f"  Clase: {font_knob.__class__.__name__}")
        print(f"  Valor actual: {font_knob.value()}")
        
        # Probar diferentes formas de establecer el valor
        print(f"\n🧪 PRUEBA: Establecer valor del font...")
        try:
            # Método 1: setValue con índice
            font_knob.setValue(0, 0)  # índice 0, valor 0
            print(f"  ✅ setValue(0, 0) funcionó")
        except Exception as e:
            print(f"  ❌ setValue(0, 0) falló: {e}")
        
        try:
            # Método 2: setValue con string
            font_knob.setValue('Arial')
            print(f"  ✅ setValue('Arial') funcionó")
        except Exception as e:
            print(f"  ❌ setValue('Arial') falló: {e}")

if __name__ == "__main__":
    explore_effect_creation()

