"""
________________________________________________________________

  Exploración: Docking State de Paneles en Hiero
  Script para analizar el estado de docking del panel Projects

________________________________________________________________
"""

import hiero.ui
import hiero.core
import sys
import os
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

print("=" * 80)
print("EXPLORACIÓN: Estado de Docking del Panel Projects")
print("=" * 80)

def analyze_panel_docking(panel):
    """Analiza el estado de docking de un panel"""
    print(f"\n{'='*50}")
    print(f"ANÁLISIS DE DOCKING: {panel.objectName()}")
    print(f"{'='*50}")

    # Información básica
    print(f"Título: {panel.windowTitle()}")
    print(f"Visible: {panel.isVisible()}")
    print(f"Geometry: {panel.geometry()}")
    print(f"Size: {panel.size()}")
    print(f"Pos: {panel.pos()}")

    # Estado de ventana
    print(f"Is Floating: {getattr(panel, 'isFloating', lambda: 'N/A')()}")
    print(f"Is Minimized: {getattr(panel, 'isMinimized', lambda: 'N/A')()}")
    print(f"Is Maximized: {getattr(panel, 'isMaximized', lambda: 'N/A')()}")
    print(f"Window State: {panel.windowState()}")

    # Análisis de jerarquía de parents
    print("\nJERARQUÍA DE PARENTS:")
    current = panel
    depth = 0
    while current and depth < 10:  # Límite para evitar loops
        parent_info = f"  [{'  '*depth}] {type(current).__name__}"
        if hasattr(current, 'objectName') and current.objectName():
            parent_info += f" ({current.objectName()})"
        if hasattr(current, 'windowTitle') and current.windowTitle():
            parent_info += f" '{current.windowTitle()}'"
        print(parent_info)

        # Información adicional del widget
        if hasattr(current, 'size'):
            print(f"  [{'  '*depth}]   Size: {current.size()}")
        if hasattr(current, 'geometry'):
            print(f"  [{'  '*depth}]   Geometry: {current.geometry()}")

        current = current.parent()
        depth += 1

    # Buscar QMainWindow o QStackedWidget (contenedores típicos)
    main_window = panel
    while main_window and not isinstance(main_window, QtWidgets.QMainWindow):
        main_window = main_window.parent()

    if main_window:
        print("\n✓ ENCONTRADO QMainWindow:")
        print(f"  Type: {type(main_window)}")
        print(f"  Title: {getattr(main_window, 'windowTitle', lambda: 'N/A')()}")
        print(f"  ObjectName: {getattr(main_window, 'objectName', lambda: 'N/A')()}")
    else:
        print("\n✗ NO se encontró QMainWindow en la jerarquía")

    # Buscar QStackedWidget (donde están los panels dockeados)
    stacked_widget = panel
    while stacked_widget and not isinstance(stacked_widget, QtWidgets.QStackedWidget):
        stacked_widget = stacked_widget.parent()

    if stacked_widget:
        print("\n✓ ENCONTRADO QStackedWidget (CONTENEDOR DE PANELS):")
        print(f"  Type: {type(stacked_widget)}")
        print(f"  ObjectName: {getattr(stacked_widget, 'objectName', lambda: 'N/A')()}")
        print(f"  Count: {stacked_widget.count()}")
        print(f"  Current Index: {stacked_widget.currentIndex()}")

        # Encontrar el índice de nuestro panel
        panel_index = -1
        for i in range(stacked_widget.count()):
            widget = stacked_widget.widget(i)
            if widget == panel:
                panel_index = i
                break

        print(f"  Nuestro panel está en índice: {panel_index}")

        # Ver TODOS los panels en el mismo contenedor (incluyendo el nuestro)
        print("  📋 TODOS los panels en este contenedor:")
        for i in range(stacked_widget.count()):
            widget = stacked_widget.widget(i)
            name = getattr(widget, 'objectName', lambda: 'N/A')() or 'Sin nombre'
            title = getattr(widget, 'windowTitle', lambda: 'N/A')() or 'Sin título'
            marker = " ← CURRENT" if i == stacked_widget.currentIndex() else ""
            our_panel_marker = " ← NUESTRO PANEL" if widget == panel else ""
            print(f"    [{i}] {name}: '{title}'{marker}{our_panel_marker}")

        # Información adicional del contenedor
        print("\n  🔍 INFORMACIÓN DETALLADA DEL CONTENEDOR:")
        print(f"  Parent del QStackedWidget: {type(stacked_widget.parent())}")
        if stacked_widget.parent():
            print(f"  Parent objectName: {getattr(stacked_widget.parent(), 'objectName', lambda: 'N/A')()}")

        # Verificar si hay algún tab widget o similar
        tab_parent = stacked_widget.parent()
        while tab_parent:
            if hasattr(tab_parent, 'tabText') or 'tab' in type(tab_parent).__name__.lower():
                print(f"  🚨 ENCONTRADO TAB WIDGET: {type(tab_parent)} - {getattr(tab_parent, 'objectName', lambda: 'N/A')()}")
                break
            tab_parent = tab_parent.parent()

    else:
        print("\n✗ NO se encontró QStackedWidget en la jerarquía")
        print("  💡 Esto significa que el panel NO está dockeado en Hiero")

    # Métodos relacionados con docking/layout
    docking_methods = [method for method in dir(panel) if any(x in method.lower() for x in ['dock', 'layout', 'tab', 'float', 'embed'])]
    if docking_methods:
        print("\nMÉTODOS DE DOCKING/LAYOUT:")
        for method in docking_methods:
            print(f"  - {method}")

    print(f"\n{'='*50} FIN ANÁLISIS {'='*50}")


# Análisis principal
print("\nINICIANDO ANÁLISIS DEL PANEL PROJECTS...")
print("=" * 80)

wm = hiero.ui.windowManager()

# Buscar el panel Projects
projects_panel = None
for window in wm.windows():
    if window.objectName() == "com.lega.ProjectsPanel":
        projects_panel = window
        break

if projects_panel:
    print("✓ Panel Projects encontrado")
    analyze_panel_docking(projects_panel)
else:
    print("✗ Panel Projects NO encontrado")
    print("Paneles disponibles:")
    for window in wm.windows():
        print(f"  - {window.objectName()}: {window.windowTitle()}")

print("\n" + "=" * 80)
print("ANÁLISIS COMPARATIVO: DOCKEADO vs NO DOCKEADO")
print("=" * 80)

print("\n🎯 DIFERENCIAS CLAVE ENTRE PANEL DOCKEADO Y NO DOCKEADO:")
print("✅ PANEL DOCKEADO: Tiene jerarquía completa, está en QStackedWidget, comparte espacio")
print("❌ PANEL NO DOCKEADO: Sin parents, no en QStackedWidget, no forma parte del layout")
print("🔍 PARA REDOCKEAR: NO usar insertWidget (duplica), encontrar cómo Hiero 'abre' panels")
print("📋 PRÓXIMOS PASOS: Ejecutar en ambos estados y comparar")

print("=" * 80)
print("FIN DE EXPLORACIÓN DE DOCKING")
print("=" * 80)
