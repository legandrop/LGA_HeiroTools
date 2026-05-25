import hiero.ui


def zoom_to_fill_in_viewer():
    viewer = hiero.ui.currentViewer()
    if not viewer:
        print("❌ No hay viewer activo")
        return

    try:
        player = viewer.player()
        if not player:
            print("❌ No se encontró el player del viewer")
            return

        player.zoomToFill()
        print("✅ Zoom to Fill aplicado con éxito")
    except Exception as e:
        print(f"❌ Error aplicando zoomToFill: {e}")


# Ejecutar la función
zoom_to_fill_in_viewer()
