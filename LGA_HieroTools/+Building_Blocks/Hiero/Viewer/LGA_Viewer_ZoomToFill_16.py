import hiero.ui


def zoom_to_fill_in_viewer():
    """
    Aplica zoom to fill al viewer actual (compatible con Nuke 15/16).
    En Nuke 16: viewer.zoomToFill()
    En Nuke 15: viewer.player().zoomToFill()
    """
    viewer = hiero.ui.currentViewer()
    if not viewer:
        print("❌ No hay viewer activo")
        return

    try:
        # Intentar método de Nuke 16 primero (viewer.zoomToFill)
        if hasattr(viewer, 'zoomToFill'):
            viewer.zoomToFill()
            print("✅ Zoom to Fill aplicado con éxito (Nuke 16)")
            return

        # Fallback a método de Nuke 15 (player.zoomToFill)
        player = viewer.player()
        if player and hasattr(player, 'zoomToFill'):
            player.zoomToFill()
            print("✅ Zoom to Fill aplicado con éxito (Nuke 15)")
            return

        # Si ninguno funciona, informar pero no fallar
        print("⚠️ zoomToFill no disponible - continuando sin zoom automático")

    except Exception as e:
        print(f"❌ Error aplicando zoom: {e}")


# Ejecutar la función
zoom_to_fill_in_viewer()
