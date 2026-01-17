"""
Test script para probar el cierre seguro de viewers en Hiero 16.
Este script permite probar la función find_and_close_old_viewers_safe()
sin necesidad de ejecutar todo el refresh.
"""

import sys
import os

# Agregar el directorio padre al path para importar módulos de Hiero
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

# Importar módulos necesarios
import hiero.ui
import hiero.core
from LGA_QtAdapter_HieroTools import QtWidgets, QtCore

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def test_close_viewer_safe():
    """
    Prueba la función de cierre seguro de viewers.
    """
    try:
        print("🧪 TEST: Cierre seguro de viewers en Hiero 16")
        print("="*50)

        # 1. Mostrar estado inicial
        current_viewer = hiero.ui.currentViewer()
        if current_viewer:
            try:
                current_window = current_viewer.window()
                if current_window and hasattr(current_window, 'objectName'):
                    current_obj_name = current_window.objectName()
                    print(f"📍 Viewer activo actual: {current_obj_name}")
                else:
                    print("⚠️ No se pudo obtener objectName del viewer actual")
            except Exception as e:
                print(f"⚠️ Error obteniendo viewer actual: {e}")
        else:
            print("⚠️ No hay viewer activo actualmente")

        # 2. Mostrar todos los viewers encontrados
        app = QtWidgets.QApplication.instance()
        if not app:
            print("❌ No se pudo obtener QApplication")
            return

        print("\n🔍 VIEWERS ENCONTRADOS:")
        all_widgets = app.allWidgets()
        viewers_found = []

        for widget in all_widgets:
            try:
                class_name = widget.metaObject().className() if hasattr(widget, 'metaObject') else ""
                if "Foundry::Storm::UI::Viewer" in class_name:
                    obj_name = widget.objectName() if hasattr(widget, 'objectName') else ""
                    window_title = widget.windowTitle() if hasattr(widget, 'windowTitle') else ""

                    if obj_name and obj_name.strip():
                        viewers_found.append({
                            'object_name': obj_name,
                            'window_title': window_title
                        })
                        print(f"   📺 {window_title or obj_name} (obj: {obj_name})")
            except:
                continue

        if not viewers_found:
            print("   ⚠️ No se encontraron viewers")
            return

        # 3. Preguntar qué hacer
        print(f"\n📊 Encontrados {len(viewers_found)} viewers")

        print("\n¿Que acción deseas probar?")
        print("1. Cerrar viewer específico (proporcionar objectName)")
        print("2. Cerrar todos los viewers que NO sean currentViewer")
        print("3. ⚖️ Cerrar VIEWERS + TIMELINES simultáneamente (EQUILIBRIO)")
        print("4. Solo analizar (no cerrar)")
        action = input("Opción: ")

        if action == "1":
            obj_name = input("Ingresa el objectName del viewer a cerrar: ")
            if obj_name.strip():
                print(f"\n🔧 Cerrando viewer específico: {obj_name}")
                # Importar la función del wrapper
                sys.path.insert(0, os.path.join(parent_dir, "LGA_NKS_ViewerTL"))
                from LGA_NKS_Timeline_Refresh_Wrap import find_and_close_old_viewers_and_timelines_safe

                result = find_and_close_old_viewers_and_timelines_safe(old_viewer_object_name=obj_name)
                if result:
                    print("✅ Viewer cerrado exitosamente")
                else:
                    print("⚠️ No se pudo cerrar el viewer")
            else:
                print("⚠️ objectName vacío")

        elif action == "2":
            print(f"\n🔧 Cerrando todos los viewers que NO sean currentViewer")
            # Importar la función del wrapper
            sys.path.insert(0, os.path.join(parent_dir, "LGA_NKS_ViewerTL"))
            from LGA_NKS_Timeline_Refresh_Wrap import find_and_close_old_viewers_and_timelines_safe

            result = find_and_close_old_viewers_and_timelines_safe(old_viewer_object_name=None)
            if result:
                print("✅ Viewers cerrados exitosamente")
            else:
                print("⚠️ No se pudieron cerrar viewers")

        elif action == "3":
            print(f"\n⚖️ Cerrar VIEWERS + TIMELINES simultáneamente (EQUILIBRIO)")
            print(f"   Manteniendo el equilibrio delicado de Hiero")

            # Importar la función del wrapper
            sys.path.insert(0, os.path.join(parent_dir, "LGA_NKS_ViewerTL"))
            from LGA_NKS_Timeline_Refresh_Wrap import find_and_close_old_viewers_and_timelines_safe

            result = find_and_close_old_viewers_and_timelines_safe(
                old_viewer_object_name=None,
                old_timeline_object_name=None
            )
            if result:
                print("✅ Viewers + Timelines cerrados simultáneamente - Equilibrio mantenido")
            else:
                print("⚠️ No se pudieron cerrar widgets")

        elif action == "4":
            print("ℹ️ Solo análisis completado")

        else:
            print("⚠️ Opción no válida")

        print("\n✅ Test completado")

    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_close_viewer_safe()