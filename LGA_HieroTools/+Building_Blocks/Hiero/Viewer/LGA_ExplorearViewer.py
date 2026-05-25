"""
______________________________________________________

  LGA_ExplorearViewer v1.2 - Lega
  Script de exploracion para encontrar funciones del viewer de Hiero
  Especialmente buscando funciones de zoom como "Zoom to fill"
______________________________________________________

"""

import hiero.core
import hiero.ui
import inspect


def explorar_viewer_detallado():
    """Explora las funciones y metodos disponibles en el viewer actual con más detalle"""

    print("=" * 60)
    print("EXPLORANDO VIEWER DE HIERO - VERSIÓN DETALLADA")
    print("=" * 60)

    # Obtener el viewer actual
    viewer = hiero.ui.currentViewer()
    if not viewer:
        print("❌ No hay viewer activo")
        return None

    print(f"✅ Viewer encontrado: {type(viewer)}")
    print(f"Clase del viewer: {viewer.__class__}")
    print(f"MRO del viewer: {viewer.__class__.__mro__}")
    print()

    # Explorar todos los métodos con más detalle
    print("MÉTODOS Y ATRIBUTOS DEL VIEWER (DETALLADO):")
    print("-" * 50)

    metodos_zoom = []
    metodos_player = []
    metodos_layout = []
    metodos_otros = []

    for nombre in dir(viewer):
        if nombre.startswith("_"):
            continue

        try:
            atributo = getattr(viewer, nombre)
            tipo = type(atributo).__name__

            # Clasificar métodos más específicamente
            if any(
                keyword in nombre.lower()
                for keyword in ["zoom", "fit", "fill", "scale", "transform", "center"]
            ):
                metodos_zoom.append((nombre, tipo, atributo))
            elif any(
                keyword in nombre.lower()
                for keyword in ["player", "play", "mask", "overlay"]
            ):
                metodos_player.append((nombre, tipo, atributo))
            elif any(
                keyword in nombre.lower()
                for keyword in ["layout", "view", "display", "show", "widget"]
            ):
                metodos_layout.append((nombre, tipo, atributo))
            else:
                metodos_otros.append((nombre, tipo, atributo))

        except Exception as e:
            print(f"Error accediendo a {nombre}: {e}")

    # Mostrar métodos de zoom con más detalle
    if metodos_zoom:
        print("\n🔍 MÉTODOS RELACIONADOS CON ZOOM/FIT/FILL/SCALE/TRANSFORM/CENTER:")
        print("-" * 65)
        for nombre, tipo, atributo in metodos_zoom:
            print(f"  {nombre} ({tipo})")
            if callable(atributo):
                try:
                    sig = inspect.signature(atributo)
                    print(f"    Signature: {nombre}{sig}")
                except:
                    print(f"    Callable: {nombre}()")

                # Obtener docstring si existe
                if hasattr(atributo, "__doc__") and atributo.__doc__:
                    doc = atributo.__doc__.strip()
                    if doc:
                        print(f"    Doc: {doc[:150]}...")
            print()
    else:
        print("\n❌ NO SE ENCONTRARON MÉTODOS DE ZOOM DIRECTOS")

    # Mostrar métodos de player
    if metodos_player:
        print("\n🎮 MÉTODOS RELACIONADOS CON PLAYER/MASK/OVERLAY:")
        print("-" * 50)
        for nombre, tipo, atributo in metodos_player:
            print(f"  {nombre} ({tipo})")
            if callable(atributo):
                try:
                    sig = inspect.signature(atributo)
                    if len(str(sig)) < 100:
                        print(f"    {nombre}{sig}")
                except:
                    pass
            print()

    # Mostrar métodos de layout
    if metodos_layout:
        print("\n🎯 MÉTODOS RELACIONADOS CON LAYOUT/VIEW/DISPLAY:")
        print("-" * 50)
        for nombre, tipo, atributo in metodos_layout:
            print(f"  {nombre} ({tipo})")
            if callable(atributo):
                try:
                    sig = inspect.signature(atributo)
                    if len(str(sig)) < 100:
                        print(f"    {nombre}{sig}")
                except:
                    pass
            print()

    # Explorar el player del viewer si existe
    print("\n🎮 EXPLORANDO PLAYER DEL VIEWER:")
    print("-" * 40)

    try:
        if hasattr(viewer, "player"):
            player = viewer.player()
            if player:
                print(f"Player encontrado: {type(player)}")
                print(f"Clase del player: {player.__class__}")

                player_zoom_methods = []
                for nombre in dir(player):
                    if not nombre.startswith("_") and any(
                        keyword in nombre.lower()
                        for keyword in [
                            "zoom",
                            "fit",
                            "fill",
                            "scale",
                            "transform",
                            "center",
                        ]
                    ):
                        try:
                            attr = getattr(player, nombre)
                            player_zoom_methods.append(
                                (nombre, type(attr).__name__, attr)
                            )
                        except:
                            pass

                if player_zoom_methods:
                    print("\n🔍 Métodos de zoom en player:")
                    for nombre, tipo, attr in player_zoom_methods:
                        print(f"  player.{nombre} ({tipo})")
                        if callable(attr):
                            try:
                                sig = inspect.signature(attr)
                                print(f"    {nombre}{sig}")
                            except:
                                print(f"    {nombre}()")
                else:
                    print("No se encontraron métodos de zoom en el player")
            else:
                print("Player devolvió None")
        else:
            print("No se encontró método player() en el viewer")

    except Exception as e:
        print(f"Error explorando player: {e}")

    return viewer


def probar_metodos_viewer(viewer):
    """Prueba métodos específicos del viewer basándose en el ejemplo proporcionado"""

    print("\n🧪 PROBANDO MÉTODOS ESPECÍFICOS DEL VIEWER:")
    print("-" * 55)

    # Lista de métodos que podrían existir basándose en el patrón del ejemplo
    metodos_a_probar = [
        # Métodos de zoom/fit
        ("zoomToFill", []),
        ("zoomToFit", []),
        ("fitToWindow", []),
        ("centerImage", []),
        ("resetZoom", []),
        ("frameAll", []),
        # Métodos de escala
        ("setZoom", [1.0]),
        ("setScale", [1.0]),
        ("zoom", [1.0]),
        ("scale", [1.0]),
        # Métodos de layout que podrían afectar el zoom
        ("setLayoutMode", []),  # Sin parámetros primero para ver qué acepta
    ]

    metodos_exitosos = []

    for metodo_nombre, parametros in metodos_a_probar:
        if hasattr(viewer, metodo_nombre):
            try:
                metodo = getattr(viewer, metodo_nombre)
                print(f"✅ Encontrado: viewer.{metodo_nombre}")

                # Obtener información del método
                try:
                    sig = inspect.signature(metodo)
                    print(f"    Signature: {metodo_nombre}{sig}")
                except:
                    print(f"    Signature: No disponible")

                # Intentar ejecutar si hay parámetros
                if parametros:
                    try:
                        print(f"🔄 Probando {metodo_nombre}({parametros})...")
                        metodo(*parametros)
                        print(f"✅ ÉXITO: {metodo_nombre}({parametros}) ejecutado")
                        metodos_exitosos.append((metodo_nombre, parametros))
                    except Exception as e:
                        print(f"❌ Error ejecutando {metodo_nombre}({parametros}): {e}")
                else:
                    print(f"ℹ️  Método disponible pero sin probar ejecución")

            except Exception as e:
                print(f"❌ Error accediendo a {metodo_nombre}: {e}")
        else:
            print(f"❌ No encontrado: viewer.{metodo_nombre}")
        print()

    # Probar acceso al player como en el ejemplo
    print("\n🎮 PROBANDO ACCESO AL PLAYER (como en el ejemplo):")
    print("-" * 55)

    try:
        if hasattr(viewer, "player"):
            player = viewer.player()
            if player:
                print(f"✅ Player obtenido: {type(player)}")

                # Buscar métodos de zoom en el player
                player_methods = [
                    "zoom",
                    "setZoom",
                    "zoomToFill",
                    "zoomToFit",
                    "scale",
                    "setScale",
                ]
                for method_name in player_methods:
                    if hasattr(player, method_name):
                        try:
                            method = getattr(player, method_name)
                            sig = (
                                inspect.signature(method)
                                if hasattr(method, "__call__")
                                else "No callable"
                            )
                            print(f"✅ player.{method_name} disponible - {sig}")
                        except Exception as e:
                            print(f"❌ Error con player.{method_name}: {e}")
                    else:
                        print(f"❌ player.{method_name} no encontrado")
            else:
                print("❌ viewer.player() devolvió None")
        else:
            print("❌ viewer.player() no existe")

    except Exception as e:
        print(f"❌ Error general con player: {e}")

    return metodos_exitosos


# --- Main Execution ---
if __name__ == "__main__":
    try:
        viewer = explorar_viewer_detallado()
        if viewer:
            metodos_exitosos = probar_metodos_viewer(viewer)

            if metodos_exitosos:
                print(f"\n🎉 MÉTODOS EXITOSOS ENCONTRADOS:")
                for metodo, params in metodos_exitosos:
                    print(f"  - {metodo}({params})")
            else:
                print(f"\n❌ NO SE ENCONTRARON MÉTODOS FUNCIONALES DE ZOOM")

        print("\n" + "=" * 60)
        print("EXPLORACIÓN DETALLADA COMPLETADA")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error en la exploración: {e}")
        import traceback

        traceback.print_exc()
