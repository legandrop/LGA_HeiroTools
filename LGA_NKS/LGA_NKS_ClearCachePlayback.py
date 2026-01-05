"""
__________________________________________________________

  LGA_NKS_ClearCachePlayback v1.0 | Lega
  Limpia el cache de reproduccion del viewer activo en Hiero
__________________________________________________________

"""

import hiero.core
import hiero.ui

DEBUG = True

def debug_print(*message):
    if DEBUG:
        print(*message)

def main():
    """
    Funcion principal que limpia el cache de reproduccion del viewer activo.
    """
    # Obtener el viewer activo
    viewer = hiero.ui.currentViewer()
    
    if viewer is None:
        debug_print("No se encontro un viewer activo.")
        return
        
    try:
        # Limpiar el cache de reproduccion del viewer activo
        viewer.flushCache()
        
        # Limpiar el cache de todos los viewers y pausar el caching
        hiero.ui.flushAllViewersCache()
        
        debug_print("Cache de reproduccion limpiado exitosamente.")
    except Exception as e:
        debug_print(f"Error al limpiar el cache de reproduccion: {e}")


if __name__ == "__main__":
    main()
