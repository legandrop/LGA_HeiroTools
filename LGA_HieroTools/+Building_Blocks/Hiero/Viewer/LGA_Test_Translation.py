"""
______________________________________________________

  LGA_Test_Translation v1.0 - Lega
  Prueba específicamente el método translation() del player
  que podría devolver el pan/offset del viewer
______________________________________________________

"""

import hiero.core
import hiero.ui
import inspect


def debug_print(*message):
    """Función de debug que siempre imprime"""
    print(*message)


def test_translation():
    """
    Prueba específicamente el método translation() del player
    """
    debug_print("=" * 80)
    debug_print("PRUEBA ESPECÍFICA: player.translation()")
    debug_print("=" * 80)
    debug_print()
    
    viewer = hiero.ui.currentViewer()
    if not viewer:
        debug_print("❌ No hay viewer activo")
        return
    
    player = viewer.player()
    if not player:
        debug_print("❌ No hay player")
        return
    
    seq = hiero.ui.activeSequence()
    if not seq:
        debug_print("❌ No hay secuencia activa")
        return
    
    format_obj = seq.format()
    image_width = format_obj.width()
    image_height = format_obj.height()
    
    qimage = viewer.image()
    viewer_width = qimage.width() if qimage else 0
    viewer_height = qimage.height() if qimage else 0
    
    zoom = player.zoom()
    
    debug_print("📐 INFORMACIÓN BÁSICA:")
    debug_print(f"   Imagen completa: {image_width} × {image_height}")
    debug_print(f"   Viewer widget: {viewer_width} × {viewer_height}")
    debug_print(f"   Zoom: {zoom:.6f}")
    debug_print()
    
    # Calcular área visible esperada
    expected_visible_width = viewer_width / zoom if zoom > 0 else viewer_width
    expected_visible_height = viewer_height / zoom if zoom > 0 else viewer_height
    
    debug_print(f"📐 ÁREA VISIBLE ESPERADA:")
    debug_print(f"   Ancho: {expected_visible_width:.2f}px")
    debug_print(f"   Alto: {expected_visible_height:.2f}px")
    debug_print()
    
    # ========================================================================
    # PROBAR player.translation()
    # ========================================================================
    debug_print("=" * 80)
    debug_print("PROBANDO player.translation()")
    debug_print("=" * 80)
    debug_print()
    
    if hasattr(player, "translation"):
        try:
            translation_method = getattr(player, "translation")
            
            if callable(translation_method):
                try:
                    sig = inspect.signature(translation_method)
                    debug_print(f"✅ player.translation{sig}")
                    debug_print()
                    
                    # Intentar llamar sin parámetros
                    if len(sig.parameters) == 0:
                        try:
                            result = translation_method()
                            debug_print(f"✅ player.translation() = {result}")
                            debug_print(f"   Tipo: {type(result).__name__}")
                            
                            # Si es una tupla o lista
                            if isinstance(result, (tuple, list)):
                                if len(result) >= 2:
                                    pan_x = result[0]
                                    pan_y = result[1]
                                    debug_print(f"   ✅ Pan X: {pan_x}")
                                    debug_print(f"   ✅ Pan Y: {pan_y}")
                                    
                                    # Calcular área visible usando el pan
                                    visible_x = pan_x
                                    visible_y = pan_y
                                    
                                    debug_print(f"\n📐 ÁREA VISIBLE CALCULADA:")
                                    debug_print(f"   x: {visible_x:.2f}")
                                    debug_print(f"   y: {visible_y:.2f}")
                                    debug_print(f"   width: {expected_visible_width:.2f}")
                                    debug_print(f"   height: {expected_visible_height:.2f}")
                                    
                                    debug_print(f"\n✅ ¡ÉXITO! player.translation() devuelve el pan")
                                    debug_print(f"✅ PAN X: {pan_x}")
                                    debug_print(f"✅ PAN Y: {pan_y}")
                                else:
                                    debug_print(f"   ⚠️ Resultado tiene menos de 2 elementos: {result}")
                            
                            # Si es un QPoint o similar
                            elif hasattr(result, 'x') and hasattr(result, 'y'):
                                pan_x = result.x()
                                pan_y = result.y()
                                debug_print(f"   ✅ Pan X: {pan_x}")
                                debug_print(f"   ✅ Pan Y: {pan_y}")
                                
                                # Calcular área visible usando el pan
                                visible_x = pan_x
                                visible_y = pan_y
                                
                                debug_print(f"\n📐 ÁREA VISIBLE CALCULADA:")
                                debug_print(f"   x: {visible_x:.2f}")
                                debug_print(f"   y: {visible_y:.2f}")
                                debug_print(f"   width: {expected_visible_width:.2f}")
                                debug_print(f"   height: {expected_visible_height:.2f}")
                                
                                debug_print(f"\n✅ ¡ÉXITO! player.translation() devuelve el pan")
                                debug_print(f"✅ PAN X: {pan_x}")
                                debug_print(f"✅ PAN Y: {pan_y}")
                            
                            # Si es un número
                            elif isinstance(result, (int, float)):
                                debug_print(f"   ⚠️ Resultado es un número: {result}")
                                debug_print(f"   ⚠️ Podría ser solo una componente del pan")
                            
                            else:
                                debug_print(f"   ⚠️ Tipo de resultado inesperado: {type(result)}")
                                debug_print(f"   Valor: {result}")
                        except Exception as e:
                            debug_print(f"❌ Error ejecutando translation(): {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        # Intentar con diferentes parámetros
                        debug_print(f"⚠️ translation() requiere parámetros: {sig}")
                        debug_print()
                        debug_print("Probando con diferentes argumentos...")
                        
                        # Intentar con None, 0, valores por defecto
                        test_cases = [
                            (None, None),
                            (0, 0),
                            (-1, -1),
                            (True, True),
                        ]
                        
                        for args in test_cases:
                            try:
                                if len(args) <= len(sig.parameters):
                                    result = translation_method(*args)
                                    debug_print(f"   player.translation{args} = {result}")
                                    if result is not None:
                                        debug_print(f"      ✅ ¡Devuelve algo! Tipo: {type(result).__name__}")
                                        if isinstance(result, (tuple, list)) and len(result) >= 2:
                                            debug_print(f"      ✅ Pan X: {result[0]}, Pan Y: {result[1]}")
                            except Exception as e:
                                debug_print(f"   player.translation{args} error: {e}")
                except Exception as e:
                    debug_print(f"⚠️ No se pudo obtener signature (built-in method): {e}")
                    debug_print()
                    debug_print("Probando llamarlo directamente con diferentes argumentos...")
                    
                    # Intentar llamarlo sin parámetros primero
                    try:
                        result = translation_method()
                        debug_print(f"✅ player.translation() = {result}")
                        debug_print(f"   Tipo: {type(result).__name__}")
                        
                        # Si es una tupla o lista
                        if isinstance(result, (tuple, list)):
                            if len(result) >= 2:
                                pan_x = result[0]
                                pan_y = result[1]
                                debug_print(f"   ✅ Pan X: {pan_x}")
                                debug_print(f"   ✅ Pan Y: {pan_y}")
                                
                                # Calcular área visible usando el pan
                                visible_x = pan_x
                                visible_y = pan_y
                                
                                debug_print(f"\n📐 ÁREA VISIBLE CALCULADA:")
                                debug_print(f"   x: {visible_x:.2f}")
                                debug_print(f"   y: {visible_y:.2f}")
                                debug_print(f"   width: {expected_visible_width:.2f}")
                                debug_print(f"   height: {expected_visible_height:.2f}")
                                
                                debug_print(f"\n✅ ¡ÉXITO! player.translation() devuelve el pan")
                                debug_print(f"✅ PAN X: {pan_x}")
                                debug_print(f"✅ PAN Y: {pan_y}")
                            else:
                                debug_print(f"   ⚠️ Resultado tiene menos de 2 elementos: {result}")
                        
                        # Si es un QPoint o similar
                        elif hasattr(result, 'x') and hasattr(result, 'y'):
                            pan_x = result.x()
                            pan_y = result.y()
                            debug_print(f"   ✅ Pan X: {pan_x}")
                            debug_print(f"   ✅ Pan Y: {pan_y}")
                            
                            # Calcular área visible usando el pan
                            visible_x = pan_x
                            visible_y = pan_y
                            
                            debug_print(f"\n📐 ÁREA VISIBLE CALCULADA:")
                            debug_print(f"   x: {visible_x:.2f}")
                            debug_print(f"   y: {visible_y:.2f}")
                            debug_print(f"   width: {expected_visible_width:.2f}")
                            debug_print(f"   height: {expected_visible_height:.2f}")
                            
                            debug_print(f"\n✅ ¡ÉXITO! player.translation() devuelve el pan")
                            debug_print(f"✅ PAN X: {pan_x}")
                            debug_print(f"✅ PAN Y: {pan_y}")
                        
                        # Si es un número
                        elif isinstance(result, (int, float)):
                            debug_print(f"   ⚠️ Resultado es un número: {result}")
                            debug_print(f"   ⚠️ Podría ser solo una componente del pan")
                        
                        else:
                            debug_print(f"   ⚠️ Tipo de resultado: {type(result)}")
                            debug_print(f"   Valor: {result}")
                    except TypeError:
                        # Requiere parámetros, probar diferentes combinaciones
                        debug_print("⚠️ translation() requiere parámetros")
                        debug_print()
                        debug_print("Probando con diferentes argumentos...")
                        
                        test_cases = [
                            (None, None),
                            (0, 0),
                            (-1, -1),
                            (True, True),
                            (0,),
                            (None,),
                        ]
                        
                        for args in test_cases:
                            try:
                                result = translation_method(*args)
                                debug_print(f"   player.translation{args} = {result}")
                                if result is not None:
                                    debug_print(f"      ✅ ¡Devuelve algo! Tipo: {type(result).__name__}")
                                    if isinstance(result, (tuple, list)) and len(result) >= 2:
                                        debug_print(f"      ✅ Pan X: {result[0]}, Pan Y: {result[1]}")
                                        debug_print(f"\n✅ ¡ÉXITO! player.translation{args} devuelve el pan")
                                        debug_print(f"✅ PAN X: {result[0]}")
                                        debug_print(f"✅ PAN Y: {result[1]}")
                            except Exception as e:
                                debug_print(f"   player.translation{args} error: {e}")
                    except Exception as e:
                        debug_print(f"❌ Error ejecutando translation(): {e}")
                        import traceback
                        traceback.print_exc()
            else:
                debug_print(f"⚠️ translation no es callable: {type(translation_method)}")
                debug_print(f"   Valor: {translation_method}")
        except Exception as e:
            debug_print(f"❌ Error accediendo a translation: {e}")
            import traceback
            traceback.print_exc()
    else:
        debug_print("❌ player no tiene método translation()")
    
    debug_print()
    debug_print("=" * 80)
    debug_print("PRUEBA COMPLETADA")
    debug_print("=" * 80)


# Ejecutar
if __name__ == "__main__":
    test_translation()

