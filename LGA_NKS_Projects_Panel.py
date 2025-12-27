"""
________________________________________________________________

  LGA_Projects_Panel v1.0 | Lega
  Panel de prueba para testing de reimportación dinámica

  v1.0: Panel básico con botón ReImport y texto de prueba
________________________________________________________________

"""

import hiero.ui
import hiero.core
import os
import importlib
import sys
from LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore

# Variable global para activar o desactivar los prints
DEBUG = True

# Variable global para controlar si se debe crear panel automáticamente
# Se usa en smart reload para evitar creación duplicada
AUTO_CREATE_PANEL = True


def debug_print(*message):
    if DEBUG:
        print(*message)


class ProjectsPanel(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectsPanel, self).__init__()

        self.setObjectName("com.lega.ProjectsPanel")
        self.setWindowTitle("Projects")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

        # Texto de prueba
        self.test_label = QtWidgets.QLabel("Prueba 10")
        self.test_label.setAlignment(QtCore.Qt.AlignCenter)
        self.test_label.setStyleSheet("""
            QLabel {
                color: #d8d8d8;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        self.layout.addWidget(self.test_label)

        # Botón ReImport
        self.reimport_button = QtWidgets.QPushButton("ReImport")
        self.reimport_button.setStyleSheet("""
            QPushButton {
                background-color: #4c4350;
                border: 1px solid #666666;
                border-radius: 3px;
                color: #d8d8d8;
                padding: 8px 16px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #5a5060;
            }
            QPushButton:pressed {
                background-color: #4c4350aa;
            }
        """)
        self.reimport_button.clicked.connect(self.reimport_panel)
        self.reimport_button.setToolTip("Reimporta el panel y refresca la UI")
        self.layout.addWidget(self.reimport_button)

        # Spacer para empujar elementos hacia arriba
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout.addItem(spacer)

    def reimport_panel(self):
        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "LGA_Projects_Panel", "LGA_NKS_Projects_Panel_Smart_Reload.py"
            )
            if os.path.exists(script_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "LGA_NKS_Projects_Panel_Smart_Reload", script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Llamar a la función main del script de smart reload
                module.main()
                debug_print("Ejecutado LGA_NKS_Projects_Panel_Smart_Reload script.")
            else:
                debug_print(f"Script not found at path: {script_path}")
        except Exception as e:
            debug_print(f"Error durante reimportación: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Error durante reimportación:\n{str(e)}")


# Crear la instancia del widget y añadirlo al gestor de ventanas de Hiero
# SOLO si AUTO_CREATE_PANEL está activado (controlado por smart reload)
if AUTO_CREATE_PANEL:
    projectsPanel = ProjectsPanel()
    wm = hiero.ui.windowManager()
    wm.addWindow(projectsPanel)
