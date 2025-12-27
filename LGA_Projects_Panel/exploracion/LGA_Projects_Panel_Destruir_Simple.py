"""
________________________________________________________________

  DESTRUCCIÓN SIMPLE DEL PANEL PROJECTS
  Script directo que destruye el panel usando hide() + deleteLater()

________________________________________________________________
"""

import hiero.ui
import hiero.core
import sys
import os
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

print("=" * 50)
print("DESTRUCCIÓN SIMPLE DEL PANEL PROJECTS")
print("=" * 50)

def destroy_projects_panel():
    """Destruye el panel Projects usando la estrategia que funciona"""
    wm = hiero.ui.windowManager()

    # Buscar el panel Projects
    projects_panel = None
    for window in wm.windows():
        if window.objectName() == "com.lega.ProjectsPanel":
            projects_panel = window
            break

    if not projects_panel:
        print("❌ No se encontró el panel Projects")
        return False

    print(f"✅ Panel encontrado: {projects_panel.windowTitle()}")

    try:
        # Estrategia que funciona: hide() + deleteLater()
        print("🔨 Destruyendo panel...")
        projects_panel.hide()
        projects_panel.deleteLater()

        # Verificar después de 100ms
        QtCore.QTimer.singleShot(100, lambda: verify_destruction(projects_panel))

        print("✅ Comando enviado")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_destruction(panel):
    """Verifica que el panel fue destruido"""
    wm = hiero.ui.windowManager()

    # Contar panels Projects restantes
    projects_count = len([w for w in wm.windows() if w.objectName() == "com.lega.ProjectsPanel"])

    # Verificar si el objeto específico existe
    panel_exists = any(w == panel for w in wm.windows())

    print("\n⏱️  VERIFICACIÓN:")
    print(f"Panels Projects restantes: {projects_count}")
    print(f"Panel objeto existe: {'SÍ' if panel_exists else 'NO'}")

    if projects_count == 0 and not panel_exists:
        print("✅ ¡PANEL DESTRUIDO EXITOSAMENTE!")
    else:
        print("❌ Panel no destruido")

# Ejecutar
if __name__ == "__main__":
    destroy_projects_panel()
    print("\n" + "="*50)
    print("ESPERANDO VERIFICACIÓN...")
    print("="*50)
