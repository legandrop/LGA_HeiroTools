"""
______________________________________________________

  LGA_H-Explore_Font_Knob | Lega
  Script de exploración para entender cómo funciona el knob 'font'
  en un nodo Text2 y cómo establecer correctamente la fuente Arial

______________________________________________________

"""

import hiero.core
import hiero.ui
import nuke

def explore_font_knob():
    """Explora el knob 'font' del efecto Frame_Only para entender su configuración."""
    
    print("=" * 80)
    print("🔍 EXPLORACIÓN DEL KNOB 'font' EN EL EFECTO 'Frame_Only'")
    print("=" * 80)
    
    # Obtener secuencia activa
    seq = hiero.ui.activeSequence()
    if not seq:
        print("❌ No se encontró una secuencia activa.")
        return
    
    # Buscar el track 'BurnIn'
    track = None
    for t in seq.videoTracks():
        if t.name() == "BurnIn":
            track = t
            break
    
    if not track:
        print("❌ No se encontró el track 'BurnIn'.")
        return
    
    print(f"✅ Track 'BurnIn' encontrado")
    
    # Buscar el efecto 'Frame_Only'
    effect_item = None
    items = track.subTrackItems()
    if items:
        for item in items:
            effect = item[0] if isinstance(item, (tuple, list)) else item
            if isinstance(effect, hiero.core.EffectTrackItem):
                try:
                    if effect.name() == "Frame_Only":
                        effect_item = effect
                        break
                except:
                    continue
    
    if not effect_item:
        print("❌ No se encontró el efecto 'Frame_Only'.")
        print("   Buscando cualquier efecto Text2 para explorar...")
        
        # Buscar cualquier efecto Text2
        items = track.subTrackItems()
        if items:
            for item in items:
                effect = item[0] if isinstance(item, (tuple, list)) else item
                if isinstance(effect, hiero.core.EffectTrackItem):
                    try:
                        node = effect.node()
                        if node and node.Class() == 'Text2':
                            effect_item = effect
                            print(f"   ✅ Usando efecto '{effect.name()}' para explorar")
                            break
                    except:
                        continue
        
        if not effect_item:
            print("❌ No se encontró ningún efecto Text2 para explorar.")
            return
    
    print(f"✅ Efecto encontrado: '{effect_item.name()}'")
    
    # Obtener el nodo
    node = effect_item.node()
    if not node:
        print("❌ No se pudo obtener el nodo del efecto.")
        return
    
    print(f"✅ Nodo obtenido: {node.name()} ({node.Class()})")
    
    # Analizar el knob 'font'
    if 'font' not in node.knobs():
        print("❌ El nodo no tiene un knob 'font'.")
        return
    
    font_knob = node['font']
    
    print("\n" + "=" * 80)
    print("📋 INFORMACIÓN DEL KNOB 'font':")
    print("=" * 80)
    
    # Información básica
    print(f"\n🔹 Tipo del objeto: {type(font_knob)}")
    print(f"🔹 Clase: {font_knob.__class__.__name__}")
    print(f"🔹 Nombre: {font_knob.name()}")
    print(f"🔹 Label: {font_knob.label()}")
    
    # Valor actual
    try:
        current_value = font_knob.value()
        print(f"🔹 Valor actual: {current_value} (Tipo: {type(current_value)})")
    except Exception as e:
        print(f"⚠️ Error obteniendo valor: {e}")
    
    # Métodos disponibles
    print(f"\n📚 MÉTODOS DISPONIBLES EN EL KNOB:")
    methods = [m for m in dir(font_knob) if not m.startswith('_')]
    font_related_methods = [m for m in methods if 'font' in m.lower() or 'set' in m.lower() or 'get' in m.lower()]
    for method in sorted(font_related_methods):
        try:
            attr = getattr(font_knob, method)
            if callable(attr):
                print(f"  - {method}()")
        except:
            pass
    
    # Intentar obtener fuentes disponibles
    print(f"\n🔤 FUENTES DISPONIBLES:")
    try:
        if hasattr(font_knob, 'getFontNames'):
            fonts = font_knob.getFontNames()
            print(f"  ✅ getFontNames() disponible")
            print(f"  Total de fuentes: {len(fonts)}")
            if 'Arial' in fonts:
                arial_index = fonts.index('Arial')
                print(f"  ✅ 'Arial' encontrada en índice: {arial_index}")
            else:
                print(f"  ⚠️ 'Arial' NO encontrada en la lista")
                # Buscar variaciones
                arial_variants = [f for f in fonts if 'arial' in f.lower()]
                if arial_variants:
                    print(f"  📋 Variantes encontradas: {arial_variants}")
            print(f"  Primeras 10 fuentes: {fonts[:10]}")
        else:
            print(f"  ⚠️ getFontNames() no disponible")
    except Exception as e:
        print(f"  ❌ Error obteniendo fuentes: {e}")
    
    # Intentar obtener el nombre de la fuente actual
    print(f"\n🔍 NOMBRE DE LA FUENTE ACTUAL:")
    try:
        if hasattr(font_knob, 'getFontName'):
            current_font_name = font_knob.getFontName()
            print(f"  ✅ getFontName() = '{current_font_name}'")
    except Exception as e:
        print(f"  ⚠️ getFontName() no disponible o error: {e}")
    
    try:
        if hasattr(font_knob, 'value'):
            val = font_knob.value()
            if isinstance(val, str):
                print(f"  ✅ value() retorna string: '{val}'")
            elif isinstance(val, (int, float)):
                print(f"  ✅ value() retorna número: {val}")
                # Intentar obtener el nombre desde el índice
                try:
                    if hasattr(font_knob, 'getFontNames'):
                        fonts = font_knob.getFontNames()
                        if int(val) < len(fonts):
                            font_name = fonts[int(val)]
                            print(f"     → Nombre de fuente en índice {int(val)}: '{font_name}'")
                except:
                    pass
    except Exception as e:
        print(f"  ⚠️ Error obteniendo valor: {e}")
    
    # Probar diferentes métodos de setValue
    print(f"\n🧪 PRUEBAS DE setValue():")
    print("-" * 80)
    
    # Guardar valor original para restaurar después
    original_value = None
    try:
        original_value = font_knob.value()
        print(f"📌 Valor original guardado: {original_value}")
    except:
        pass
    
    # Prueba 1: setValue con string 'Arial'
    print(f"\n  PRUEBA 1: setValue('Arial')")
    try:
        font_knob.setValue('Arial')
        new_value = font_knob.value()
        print(f"    ✅ Éxito! Nuevo valor: {new_value}")
        # Verificar si realmente cambió
        if hasattr(font_knob, 'getFontName'):
            try:
                font_name = font_knob.getFontName()
                print(f"    ✅ Nombre de fuente actual: '{font_name}'")
            except:
                pass
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Restaurar valor original
    if original_value is not None:
        try:
            font_knob.setValue(original_value)
            print(f"    🔄 Valor restaurado a: {original_value}")
        except:
            pass
    
    # Prueba 2: setValue con string y estilo 'Regular'
    print(f"\n  PRUEBA 2: setValue('Arial', 'Regular')")
    try:
        font_knob.setValue('Arial', 'Regular')
        new_value = font_knob.value()
        get_value = font_knob.getValue()
        print(f"    ✅ Éxito! Nuevo valor: {new_value}")
        print(f"    ✅ getValue(): {get_value}")
        to_script = font_knob.toScript()
        print(f"    ✅ toScript(): {to_script}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Restaurar valor original
    if original_value is not None:
        try:
            # Restaurar usando getValue() que retorna ['Arial', 'Regular']
            original_get_value = font_knob.getValue()
            if isinstance(original_get_value, list) and len(original_get_value) >= 2:
                font_knob.setValue(original_get_value[0], original_get_value[1])
                print(f"    🔄 Valor restaurado usando getValue(): {original_get_value}")
            else:
                font_knob.setValue(original_value)
                print(f"    🔄 Valor restaurado a: {original_value}")
        except Exception as e:
            print(f"    ⚠️ Error restaurando: {e}")
    
    # Prueba 2b: setValue con string e índice 0 (por si acaso)
    print(f"\n  PRUEBA 2b: setValue('Arial', 0)")
    try:
        font_knob.setValue('Arial', 0)
        new_value = font_knob.value()
        print(f"    ✅ Éxito! Nuevo valor: {new_value}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Restaurar valor original
    if original_value is not None:
        try:
            original_get_value = font_knob.getValue()
            if isinstance(original_get_value, list) and len(original_get_value) >= 2:
                font_knob.setValue(original_get_value[0], original_get_value[1])
        except:
            pass
    
    # Prueba 3: setValue con índice numérico (si encontramos Arial)
    print(f"\n  PRUEBA 3: setValue con índice numérico")
    try:
        if hasattr(font_knob, 'getFontNames'):
            fonts = font_knob.getFontNames()
            if 'Arial' in fonts:
                arial_index = fonts.index('Arial')
                font_knob.setValue(arial_index)
                new_value = font_knob.value()
                print(f"    ✅ Éxito con índice {arial_index}! Nuevo valor: {new_value}")
                if hasattr(font_knob, 'getFontName'):
                    try:
                        font_name = font_knob.getFontName()
                        print(f"    ✅ Nombre de fuente actual: '{font_name}'")
                    except:
                        pass
            else:
                print(f"    ⚠️ 'Arial' no encontrada en la lista de fuentes")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Restaurar valor original
    if original_value is not None:
        try:
            font_knob.setValue(original_value)
            print(f"    🔄 Valor restaurado a: {original_value}")
        except:
            pass
    
    # Prueba 4: Analizar la signatura de setValue
    print(f"\n📝 SIGNATURA DE setValue():")
    try:
        import inspect
        sig = inspect.signature(font_knob.setValue)
        print(f"  {sig}")
    except Exception as e:
        print(f"  ⚠️ No se pudo obtener signatura: {e}")
    
    # Información adicional sobre el knob
    print(f"\n📋 INFORMACIÓN ADICIONAL:")
    try:
        # Verificar si tiene métodos específicos de FreeType_Knob
        if hasattr(font_knob, 'toScript'):
            script_value = font_knob.toScript()
            print(f"  toScript(): {script_value}")
    except:
        pass
    
    try:
        if hasattr(font_knob, 'getValue'):
            val = font_knob.getValue()
            print(f"  getValue(): {val} (Tipo: {type(val)})")
    except:
        pass
    
    print("\n" + "=" * 80)
    print("✅ EXPLORACIÓN COMPLETA")
    print("=" * 80)

if __name__ == "__main__":
    explore_font_knob()

