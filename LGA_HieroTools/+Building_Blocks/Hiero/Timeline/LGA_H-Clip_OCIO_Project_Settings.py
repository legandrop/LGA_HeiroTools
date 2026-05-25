import hiero.core
import hiero.ui

# Script de exploración exhaustiva de settings OCIO del proyecto
# Basado en la configuración mostrada por el usuario

seq = hiero.ui.activeSequence()
if seq:
    project = seq.project()
    if project:
        print("="*100)
        print("EXPLORACIÓN EXHAUSTIVA: SETTINGS OCIO DEL PROYECTO")
        print("="*100)

        print(f"Proyecto: {project.name()}")
        print(f"Proyecto type: {type(project)}")
        print("-" * 80)

        # 1. EXPLORACIÓN GENERAL DE MÉTODOS OCIO
        print("1. MÉTODOS OCIO DISPONIBLES:")
        all_methods = dir(project)
        ocio_methods = [m for m in all_methods if 'ocio' in m.lower() or 'color' in m.lower()]

        for method in sorted(ocio_methods):
            try:
                attr = getattr(project, method)
                if callable(attr):
                    print(f"  {method}(): [callable method]")
                else:
                    print(f"  {method}: {attr}")
            except Exception as e:
                print(f"  {method}: [Error accessing: {e}]")

        print("\n" + "-" * 80)

        # 2. INTENTAR EJECUTAR MÉTODOS OCIO Y VER RESULTADOS
        print("2. EJECUCIÓN DE MÉTODOS OCIO:")
        methods_to_try = [
            'ocioConfigName', 'ocioConfigPath', 'lutUseOCIOForExport',
            'useOCIOEnvironmentOverride', 'showViewColors', 'viewsAndColors'
        ]

        for method_name in methods_to_try:
            if hasattr(project, method_name):
                try:
                    method = getattr(project, method_name)
                    if callable(method):
                        result = method()
                        print(f"  {method_name}(): {result}")
                    else:
                        print(f"  {method_name}: {method} [not callable]")
                except Exception as e:
                    print(f"  {method_name}(): [Error: {e}]")
            else:
                print(f"  {method_name}: [Method not found]")

        print("\n" + "-" * 80)

        # 3. EXPLORACIÓN DE OCIO CONFIG SPECÍFICA
        print("3. OCIO CONFIG SPECÍFICA:")
        try:
            # Intentar acceder a propiedades específicas de OCIO
            ocio_props = {}

            # Buscar cualquier propiedad que pueda contener la config
            for attr_name in dir(project):
                if not attr_name.startswith('_'):  # Evitar métodos privados
                    try:
                        attr_value = getattr(project, attr_name)
                        if not callable(attr_value):
                            attr_str = str(attr_value).lower()
                            # Buscar referencias a OCIO, config, working space, etc.
                            if any(keyword in attr_str for keyword in ['ocio', 'config', 'working', 'space', 'aces', 'rec709']):
                                ocio_props[attr_name] = attr_value
                    except:
                        pass

            if ocio_props:
                print("Propiedades relacionadas con OCIO encontradas:")
                for prop, value in ocio_props.items():
                    print(f"  {prop}: {value}")
            else:
                print("No se encontraron propiedades relacionadas con OCIO")

        except Exception as e:
            print(f"Error explorando OCIO config: {e}")

        print("\n" + "-" * 80)

        # 4. INTENTAR ACCEDER A SETTINGS POR DEFECTO
        print("4. SETTINGS POR DEFECTO (DEFAULT COLOR TRANSFORMS):")

        # Basado en lo que mostró el usuario, buscar estos settings específicos
        settings_to_find = {
            'Working Space': ['aces_interchange', 'working_space', 'default_working_space'],
            'Viewer': ['rec1886', 'rec.1886', 'rec709', 'viewer_transform', 'display_transform'],
            'Thumbnails': ['thumbnail', 'thumb', 'bin_transform'],
            'Monitor Out': ['monitor', 'output_transform'],
            '8 Bit Files': ['8bit', '8_bit', 'matte_paint', 'srgb'],
            '16 Bit Files': ['16bit', '16_bit'],
            'Log Files': ['log', 'log_files'],
            'Floating Point Files': ['float', 'floating_point', 'exr']
        }

        for category, keywords in settings_to_find.items():
            print(f"\n{category}:")
            found = False

            # Buscar en métodos
            for method_name in dir(project):
                if any(keyword.lower() in method_name.lower() for keyword in keywords):
                    try:
                        method = getattr(project, method_name)
                        if callable(method):
                            result = method()
                            print(f"  ✓ {method_name}(): {result}")
                            found = True
                        else:
                            print(f"  ? {method_name}: {method}")
                            found = True
                    except Exception as e:
                        print(f"  ✗ {method_name}(): Error: {e}")

            # Buscar en propiedades
            for attr_name in dir(project):
                try:
                    if not callable(getattr(project, attr_name)):
                        attr_value = str(getattr(project, attr_name))
                        if any(keyword.lower() in attr_value.lower() for keyword in keywords):
                            print(f"  ✓ {attr_name}: {attr_value}")
                            found = True
                except:
                    pass

            if not found:
                print("  ✗ No encontrado")

        print("\n" + "-" * 80)

        # 5. EXPLORACIÓN PROFUNDA DE PROPIEDADES
        print("5. EXPLORACIÓN PROFUNDA DE TODAS LAS PROPIEDADES:")

        # Obtener todas las propiedades no-callable
        all_properties = {}
        for attr_name in dir(project):
            try:
                attr_value = getattr(project, attr_name)
                if not callable(attr_value) and not attr_name.startswith('_'):
                    all_properties[attr_name] = attr_value
            except:
                pass

        # Mostrar propiedades que podrían contener settings OCIO
        ocio_related_props = {}
        for prop_name, prop_value in all_properties.items():
            prop_str = str(prop_value).lower()
            if any(keyword in prop_str for keyword in ['ocio', 'color', 'aces', 'rec709', 'working', 'space', 'transform', 'config']):
                ocio_related_props[prop_name] = prop_value

        if ocio_related_props:
            print("Propiedades que pueden contener settings OCIO:")
            for prop, value in sorted(ocio_related_props.items()):
                print(f"  {prop}: {value}")
        else:
            print("No se encontraron propiedades con contenido OCIO")

        print("\n" + "-" * 80)

        # 6. INTENTAR ACCEDER A LA CONFIGURACIÓN INTERNA
        print("6. INTENTO DE ACCESO A CONFIGURACIÓN INTERNA:")

        # Algunos proyectos pueden tener acceso interno a la config OCIO
        internal_config_attempts = [
            '_ocioConfig', '_ocio_config', '_config', '_ocioSettings',
            'ocioSettings', 'colorSettings', '_color_management'
        ]

        for attempt in internal_config_attempts:
            if hasattr(project, attempt):
                try:
                    value = getattr(project, attempt)
                    if not callable(value):
                        print(f"  ✓ {attempt}: {value}")
                    else:
                        print(f"  ? {attempt}: [callable]")
                except Exception as e:
                    print(f"  ✗ {attempt}: Error: {e}")
            else:
                print(f"  ✗ {attempt}: [Not found]")

        print("\n" + "-" * 80)

        # 7. VERIFICACIÓN FINAL
        print("7. VERIFICACIÓN FINAL:")
        print("Basado en la configuración que mostraste:")
        print("  - Working Space debería ser: aces_interchange (ACES2065-1)")
        print("  - 8 Bit Files debería ser: matte_paint (sRGB - Texture)")
        print("  - 16 Bit/Log/Float Files debería ser: aces_interchange (ACES2065-1)")
        print("")
        print("¿Encontramos alguna forma de acceder a estos valores?")
        print("¿Hay algún método que devuelva estos settings específicos?")

        print("\n" + "="*100)
        print("FIN DE LA EXPLORACIÓN OCIO")
        print("="*100)

    else:
        print("No se pudo obtener el proyecto")
else:
    print("No active sequence found.")
