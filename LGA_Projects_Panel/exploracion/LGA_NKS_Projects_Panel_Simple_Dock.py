"""
________________________________________________________________

  LGA_Projects_Panel_Simple_Dock | Lega
  Script simple para dockear el panel Projects donde estaba antes

________________________________________________________________
"""

import hiero.ui
import hiero.core
import sys
import os
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

# Variable global para activar o desactivar los prints
DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)

def analyze_panel_docking(panel):
    """Analiza el estado de docking de un panel (versión simplificada)"""
    print(f"\n{'='*50}")
    print(f"ANÁLISIS DE DOCKING: {panel.objectName()}")
    print(f"{'='*50}")

    # Información básica
    print(f"Título: {panel.windowTitle()}")
    print(f"Visible: {panel.isVisible()}")
    print(f"Geometry: {panel.geometry()}")

    # Verificar jerarquía de parents
    has_stacked_widget = False
    current = panel
    depth = 0
    while current and depth < 10:
        if isinstance(current, QtWidgets.QStackedWidget):
            has_stacked_widget = True
            print(f"✓ TIENE QStackedWidget en profundidad {depth}")
            print(f"  Count: {current.count()}")
            print(f"  Current Index: {current.currentIndex()}")

            # Encontrar el índice de nuestro panel
            panel_index = -1
            for i in range(current.count()):
                widget = current.widget(i)
                if widget == panel:
                    panel_index = i
                    break
            print(f"  Nuestro panel está en índice: {panel_index}")
            break
        current = current.parent()
        depth += 1

    if not has_stacked_widget:
        print("❌ NO tiene QStackedWidget - NO ESTÁ DOCKEADO")

    print(f"{'='*50} FIN ANÁLISIS {'='*50}")
    return has_stacked_widget

def dock_panel_with_window_manager(panel):
    """Dockea el panel usando los métodos del WindowManager de Hiero"""
    print(f"\n{'='*50}")
    print(f"DOCKEANDO PANEL CON WINDOW MANAGER")
    print(f"{'='*50}")

    wm = hiero.ui.windowManager()

    # Explorar métodos disponibles del WindowManager
    wm_methods = [method for method in dir(wm) if not method.startswith('_')]
    print(f"Métodos disponibles en WindowManager: {wm_methods}")

    # Intentar usar showWindow() si existe
    if hasattr(wm, 'showWindow'):
        print("✓ WindowManager tiene método showWindow")
        try:
            result = wm.showWindow(panel)
            print(f"wm.showWindow() retornó: {result}")
            return True
        except Exception as e:
            print(f"✗ Error llamando wm.showWindow(): {e}")
            return False
    else:
        print("✗ WindowManager NO tiene método showWindow")
        return False

def dock_panel_manually(panel):
    """Dockea el panel manualmente reconstruyendo la jerarquía"""
    print(f"\n{'='*50}")
    print(f"DOCKEANDO PANEL MANUALMENTE")
    print(f"{'='*50}")

    wm = hiero.ui.windowManager()

    # Buscar el QStackedWidget del panel Project (que comparte espacio con Projects)
    project_panel = None
    for window in wm.windows():
        if window.objectName() == "uk.co.thefoundry.project.2":  # Panel Project
            project_panel = window
            break

    if not project_panel:
        print("❌ No se encontró el panel Project")
        return False

    print("✓ Encontrado panel Project")

    # Buscar el QStackedWidget del panel Project
    stacked_widget = None
    current = project_panel
    depth = 0
    while current and depth < 10:
        if isinstance(current, QtWidgets.QStackedWidget):
            stacked_widget = current
            print(f"✓ Encontrado QStackedWidget del panel Project: count={current.count()}")
            break
        current = current.parent()
        depth += 1

    if not stacked_widget:
        print("❌ No se encontró QStackedWidget del panel Project")
        return False

    # Ver qué panels están actualmente en el QStackedWidget
    print("Panels actualmente en el QStackedWidget:")
    for i in range(stacked_widget.count()):
        widget = stacked_widget.widget(i)
        name = getattr(widget, 'objectName', lambda: 'N/A')()
        title = getattr(widget, 'windowTitle', lambda: 'N/A')()
        current_marker = " ← CURRENT" if i == stacked_widget.currentIndex() else ""
        print(f"  [{i}] {name}: '{title}'{current_marker}")

    # Insertar nuestro panel en el índice 1 (donde estaba antes)
    print("Insertando panel Projects en índice 1...")
    result = stacked_widget.insertWidget(1, panel)
    print(f"insertWidget() retornó: {result}")

    # Activar nuestro panel
    stacked_widget.setCurrentIndex(1)
    final_index = stacked_widget.currentIndex()
    print(f"Current index después: {final_index}")

    if final_index == 1:
        print("✅ DOCKING MANUAL EXITOSO")
        return True
    else:
        print("❌ DOCKING MANUAL FALLÓ")
        return False

def dock_panel_at_index(panel, target_index=1):
    """Dockea el panel usando la mejor estrategia disponible"""
    print(f"Intentando dockear panel en índice {target_index}...")

    # Primero intentar con WindowManager (método correcto de Hiero)
    if dock_panel_with_window_manager(panel):
        print("✓ Docking exitoso con WindowManager")
        return True

    # Si falla, intentar manualmente
    print("Intentando docking manual...")
    if dock_panel_manually(panel):
        print("✓ Docking manual exitoso")
        return True

    print("❌ Todas las estrategias de docking fallaron")
    return False

def main():
    """Función principal"""
    print("=" * 80)
    print("SCRIPT SIMPLE DE DOCKING DEL PANEL PROJECTS")
    print("=" * 80)

    wm = hiero.ui.windowManager()
    target_object_name = "com.lega.ProjectsPanel"

    # Buscar panel
    panel = None
    for window in wm.windows():
        if window.objectName() == target_object_name:
            panel = window
            break

    if not panel:
        print("❌ Panel Projects no encontrado")
        return

    print("✓ Panel encontrado")

    # 1. Estado ANTES del docking
    print("\n" + "="*30 + " ESTADO ANTES " + "="*30)
    is_docked_before = analyze_panel_docking(panel)

    # 2. Intentar dockear
    print("\n" + "="*30 + " DOCKEANDO... " + "="*30)
    docking_success = dock_panel_at_index(panel, target_index=1)

    # Pequeño delay para que se apliquen los cambios
    QtCore.QTimer.singleShot(100, lambda: show_final_status(panel, is_docked_before, docking_success))

def show_final_status(panel, was_docked_before, docking_attempted):
    """Muestra el estado final después del docking con análisis detallado"""
    print("\n" + "="*30 + " ESTADO DESPUÉS " + "="*30)

    is_docked_after = analyze_panel_docking(panel)

    print("\n" + "="*30 + " RESULTADO " + "="*30)
    print(f"¿Estaba dockeado antes? {was_docked_before}")
    print(f"¿Está dockeado ahora? {is_docked_after}")

    if not was_docked_before and is_docked_after:
        print("🎉 ÉXITO: Panel dockeado correctamente")
    elif was_docked_before and is_docked_after:
        print("ℹ️  Panel ya estaba dockeado")
    else:
        print("❌ FRACASO: Panel no se dockeó")

    # Análisis detallado final como el script de exploración
    if is_docked_after:
        print("\n" + "="*30 + " ANÁLISIS DETALLADO FINAL " + "="*30)

        # Buscar el QStackedWidget donde está dockeado
        stacked_widget = None
        current = panel
        depth = 0
        while current and depth < 10:
            if isinstance(current, QtWidgets.QStackedWidget):
                stacked_widget = current
                break
            current = current.parent()
            depth += 1

        if stacked_widget:
            print("📋 PANEL DOCKEADO - Comparte espacio con:")
            for i in range(stacked_widget.count()):
                widget = stacked_widget.widget(i)
                name = getattr(widget, 'objectName', lambda: 'N/A')()
                title = getattr(widget, 'windowTitle', lambda: 'N/A')()
                current_marker = " ← CURRENT" if i == stacked_widget.currentIndex() else ""
                our_panel_marker = " ← NUESTRO PANEL" if widget == panel else ""
                print(f"  [{i}] {name}: '{title}'{current_marker}{our_panel_marker}")

    print("=" * 80)

if __name__ == "__main__":
    main()
