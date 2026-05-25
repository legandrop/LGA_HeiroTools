"""
Script de exploración para entender cómo usar track.createEffect()
"""

import hiero.core
import hiero.ui
import inspect

def explore_create_effect():
    """Explora cómo usar track.createEffect()"""
    
    print("=" * 80)
    print("🔍 EXPLORACIÓN: track.createEffect()")
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
    
    # Analizar la signatura de createEffect
    print(f"\n📚 ANÁLISIS DE createEffect():")
    if hasattr(track, 'createEffect'):
        try:
            sig = inspect.signature(track.createEffect)
            print(f"  Signatura: {sig}")
            
            # Obtener información de los parámetros
            params = sig.parameters
            print(f"\n  Parámetros:")
            for param_name, param in params.items():
                print(f"    - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'sin tipo'}")
                if param.default != inspect.Parameter.empty:
                    print(f"      Valor por defecto: {param.default}")
        except Exception as e:
            print(f"  ⚠️ Error obteniendo signatura: {e}")
    
    # Buscar un efecto existente para clonar
    items = track.subTrackItems()
    existing_effect = None
    if items:
        for item in items:
            effect_item = item[0] if isinstance(item, (tuple, list)) else item
            if isinstance(effect_item, hiero.core.EffectTrackItem):
                existing_effect = effect_item
                break
    
    if existing_effect:
        print(f"\n📋 Efecto existente encontrado: '{existing_effect.name()}'")
        node = existing_effect.node()
        if node:
            print(f"  Clase del nodo: {node.Class()}")
    
    # Probar diferentes formas de usar createEffect
    print(f"\n🧪 PRUEBAS DE createEffect():")
    
    # Lista para guardar efectos creados y eliminarlos al final
    effects_to_remove = []
    
    # Obtener la duración del efecto existente para usar en las pruebas
    existing_timeline_in = 0
    existing_timeline_out = 100
    if existing_effect:
        try:
            existing_timeline_in = existing_effect.timelineIn()
            existing_timeline_out = existing_effect.timelineOut()
            print(f"\n📏 Duración del efecto existente: In={existing_timeline_in}, Out={existing_timeline_out}")
        except:
            pass
    
    # Prueba 1: effectType con nombre de clase (usando duración del efecto existente)
    print(f"\n  PRUEBA 1: createEffect(effectType='Text2', timelineIn={existing_timeline_in}, timelineOut={existing_timeline_out})")
    try:
        effect1 = track.createEffect(effectType='Text2', timelineIn=existing_timeline_in, timelineOut=existing_timeline_out)
        print(f"    ✅ Éxito: {effect1}")
        print(f"    Nombre: {effect1.name() if effect1 else 'None'}")
        if effect1:
            print(f"    Timeline: In={effect1.timelineIn()}, Out={effect1.timelineOut()}")
            effects_to_remove.append(effect1)
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Prueba 2: cloneFrom con efecto existente (usa la misma duración automáticamente)
    if existing_effect:
        print(f"\n  PRUEBA 2: createEffect(cloneFrom=existing_effect, timelineIn={existing_timeline_in}, timelineOut={existing_timeline_out})")
        try:
            effect2 = track.createEffect(cloneFrom=existing_effect, timelineIn=existing_timeline_in, timelineOut=existing_timeline_out)
            print(f"    ✅ Éxito: {effect2}")
            print(f"    Nombre: {effect2.name() if effect2 else 'None'}")
            if effect2:
                print(f"    Timeline: In={effect2.timelineIn()}, Out={effect2.timelineOut()}")
                effects_to_remove.append(effect2)
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Prueba 3: copyFrom con efecto existente (usa la misma duración automáticamente)
    if existing_effect:
        print(f"\n  PRUEBA 3: createEffect(copyFrom=existing_effect, timelineIn={existing_timeline_in}, timelineOut={existing_timeline_out})")
        try:
            effect3 = track.createEffect(copyFrom=existing_effect, timelineIn=existing_timeline_in, timelineOut=existing_timeline_out)
            print(f"    ✅ Éxito: {effect3}")
            print(f"    Nombre: {effect3.name() if effect3 else 'None'}")
            if effect3:
                print(f"    Timeline: In={effect3.timelineIn()}, Out={effect3.timelineOut()}")
                effects_to_remove.append(effect3)
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Eliminar todos los efectos de prueba al final
    if effects_to_remove:
        print(f"\n🗑️ Eliminando {len(effects_to_remove)} efectos de prueba...")
        project = seq.project()
        if project:
            project.beginUndo("Remove test effects")
        try:
            for effect in effects_to_remove:
                try:
                    # Los soft effects se eliminan usando el método del track
                    # Intentar obtener el SubTrackItem primero
                    items = track.subTrackItems()
                    for item in items:
                        effect_item = item[0] if isinstance(item, (tuple, list)) else item
                        if effect_item == effect:
                            # Eliminar usando el SubTrackItem completo
                            if hasattr(track, 'removeSubTrackItem'):
                                track.removeSubTrackItem(item)
                                print(f"    ✅ Eliminado: {effect.name()}")
                                break
                            # Alternativa: usar el método del proyecto
                            elif project:
                                # Los efectos pueden eliminarse a través del proyecto
                                try:
                                    # Buscar método de eliminación en el proyecto
                                    if hasattr(project, 'removeItem'):
                                        project.removeItem(effect)
                                        print(f"    ✅ Eliminado: {effect.name()}")
                                        break
                                except:
                                    pass
                except Exception as e:
                    print(f"    ⚠️ No se pudo eliminar {effect.name()}: {e}")
                    import traceback
                    traceback.print_exc()
        finally:
            if project:
                project.endUndo()
        
        print(f"\n⚠️ NOTA: Si algunos efectos no se eliminaron, elimínalos manualmente desde la UI")

if __name__ == "__main__":
    explore_create_effect()

