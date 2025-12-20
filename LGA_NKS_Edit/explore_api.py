# EXPLORACIÓN PROFUNDA DE LA API DE HIERO/NUKE

import hiero
import inspect

def explore_object(obj, name="obj", max_depth=2, current_depth=0):
    """Explora recursivamente un objeto y sus propiedades"""
    if current_depth > max_depth:
        return

    indent = "  " * current_depth

    print(f"{indent}🔍 {name}: {type(obj).__name__}")

    # Mostrar atributos principales
    try:
        if hasattr(obj, '__dict__'):
            attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
            print(f"{indent}  📋 Atributos: {len(attrs)} - {attrs[:10]}{'...' if len(attrs) > 10 else ''}")
    except:
        pass

    # Mostrar métodos principales
    try:
        methods = [method for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith('_')]
        print(f"{indent}  ⚙️  Métodos: {len(methods)} - {methods[:10]}{'...' if len(methods) > 10 else ''}")
    except:
        pass

    # Propiedades específicas de Hiero
    try:
        if hasattr(obj, 'name') and callable(getattr(obj, 'name')):
            print(f"{indent}  🏷️  Nombre: '{obj.name()}'")
    except:
        pass

    try:
        if hasattr(obj, 'guid') and callable(getattr(obj, 'guid')):
            print(f"{indent}  🆔 GUID: {obj.guid()}")
    except:
        pass

    # Explorar jerarquía si es posible
    if current_depth < max_depth:
        print(f"{indent}  📂 Explorando sub-elementos...")

        # Si es un proyecto, explorar bins
        if hasattr(obj, 'clipsBin') and callable(getattr(obj, 'clipsBin')):
            try:
                clips_bin = obj.clipsBin()
                if clips_bin:
                    explore_object(clips_bin, "clipsBin", max_depth, current_depth + 1)
            except:
                pass

        # Si tiene items, explorar algunos
        if hasattr(obj, 'items') and callable(getattr(obj, 'items')):
            try:
                items = obj.items()
                if items and len(items) > 0:
                    print(f"{indent}  📦 Tiene {len(items)} items")
                    # Explorar solo los primeros 3 items
                    for i, item in enumerate(items[:3]):
                        explore_object(item, f"item[{i}]", max_depth, current_depth + 1)
            except:
                pass

        # Si tiene videoTracks, explorar algunas
        if hasattr(obj, 'videoTracks') and callable(getattr(obj, 'videoTracks')):
            try:
                tracks = obj.videoTracks()
                if tracks and len(tracks) > 0:
                    print(f"{indent}  🎬 Tiene {len(tracks)} videoTracks")
                    for i, track in enumerate(tracks[:2]):
                        explore_object(track, f"videoTrack[{i}]", max_depth, current_depth + 1)
            except:
                pass

def explore_hiero_api():
    """Exploración completa de la API de Hiero"""

    print("🚀 EXPLORACIÓN PROFUNDA DE LA API DE HIERO/NUKE")
    print("=" * 80)

    # 1. EXPLORAR PROYECTOS
    print("\n📂 PROYECTOS:")
    projects = hiero.core.projects()
    if projects:
        proj = projects[0]
        explore_object(proj, "Proyecto Actual", max_depth=1)
    else:
        print("  ❌ No hay proyectos activos")

    # 2. EXPLORAR FUNCIONES DISPONIBLES EN hiero.core
    print("\n🔧 FUNCIONES EN hiero.core:")
    core_functions = [attr for attr in dir(hiero.core) if not attr.startswith('_')]
    print(f"  📋 Funciones disponibles: {len(core_functions)}")
    print(f"  📝 Lista: {core_functions}")

    # 3. EXPLORAR MÉTODOS DE BÚSQUEDA
    print("\n🔍 MÉTODOS DE BÚSQUEDA DISPONIBLES:")
    search_methods = [method for method in dir(hiero.core) if 'find' in method.lower()]
    print(f"  🔎 Métodos find: {search_methods}")

    # 4. PROBAR DIFERENTES BÚSQUEDAS
    if projects:
        proj = projects[0]
        print("\n🧪 PROBANDO DIFERENTES BÚSQUEDAS:")
        print(f"  📂 Proyecto: {proj.name()}")

        # Buscar secuencias
        try:
            sequences = hiero.core.findItems(proj, "Sequences")
            print(f"  🎬 findItems(proj, 'Sequences'): {len(sequences)} items")
            if sequences:
                seq = sequences[0]
                print(f"    📋 Primer secuencia - Tipo: {type(seq).__name__}")
                if hasattr(seq, 'name'):
                    print(f"    🏷️  Nombre: {seq.name()}")
                if hasattr(seq, 'videoTracks'):
                    tracks = seq.videoTracks()
                    print(f"    🎬 VideoTracks: {len(tracks)}")
        except Exception as e:
            print(f"  ❌ Error en Sequences: {e}")

        # Buscar BinItems
        try:
            bin_items = hiero.core.findItems(proj, "BinItems")
            print(f"  📦 findItems(proj, 'BinItems'): {len(bin_items)} items")
            if bin_items:
                item = bin_items[0]
                print(f"    📋 Primer BinItem - Tipo: {type(item).__name__}")
                if hasattr(item, 'name'):
                    print(f"    🏷️  Nombre: {item.name()}")
                if hasattr(item, 'items'):
                    try:
                        versions = item.items()
                        print(f"    📋 Versiones: {len(versions)}")
                    except:
                        print("    📋 Error al contar versiones")
        except Exception as e:
            print(f"  ❌ Error en BinItems: {e}")

        # Buscar Bins
        try:
            bins = hiero.core.findItems(proj, "Bins")
            print(f"  📁 findItems(proj, 'Bins'): {len(bins)} items")
            if bins:
                bin_obj = bins[0]
                print(f"    📋 Primer Bin - Tipo: {type(bin_obj).__name__}")
                if hasattr(bin_obj, 'name'):
                    print(f"    🏷️  Nombre: {bin_obj.name()}")
        except Exception as e:
            print(f"  ❌ Error en Bins: {e}")

    # 5. EXPLORAR CLASES DISPONIBLES
    print("\n🏗️  CLASES DISPONIBLES EN hiero:")
    hiero_classes = []
    for attr_name in dir(hiero):
        attr = getattr(hiero, attr_name)
        if inspect.isclass(attr):
            hiero_classes.append(attr_name)

    print(f"  🏛️  Clases en hiero: {len(hiero_classes)}")
    print(f"  📝 Lista: {sorted(hiero_classes)}")

    # 6. EXPLORAR MÓDULOS
    print("\n📚 MÓDULOS DISPONIBLES:")
    modules = ['hiero.core', 'hiero.ui', 'hiero.api']
    for mod_name in modules:
        try:
            mod = eval(mod_name)
            attrs = [attr for attr in dir(mod) if not attr.startswith('_')]
            print(f"  📖 {mod_name}: {len(attrs)} elementos")
        except:
            print(f"  ❌ {mod_name}: No disponible")

    # 7. EXPLORAR OBJETOS GLOBALES
    print("\n🌍 OBJETOS GLOBALES:")
    try:
        import nuke
        print(f"  🎬 Nuke disponible: Sí")
        print(f"  📊 Version: {nuke.NUKE_VERSION_STRING if hasattr(nuke, 'NUKE_VERSION_STRING') else 'Unknown'}")
    except:
        print(f"  🎬 Nuke disponible: No")

    try:
        import nukescripts
        print(f"  🛠️  NukeScripts disponible: Sí")
    except:
        print(f"  🛠️  NukeScripts disponible: No")

    print("\n✅ EXPLORACIÓN COMPLETADA")
    print("💡 Usa esta información para entender mejor cómo trabajar con la API de Hiero/Nuke")

# Ejecutar exploración
if __name__ == "__main__":
    explore_hiero_api()