import hiero
import time
from qt_compat import QtWidgets, QtCore

DEBUG = False

def debug_print(*message):
    if DEBUG:
        print(*message)


def obtener_scrollbar_robusto():
    """Método robusto para encontrar el scrollbar del timeline (compatible con Nuke 16)"""
    try:
        t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())
        if not t:
            return None

        # Estrategia específica para Nuke 16:
        # QSplitter -> QWidget -> QAbstractScrollArea (timelineView) -> qt_scrollarea_vcontainer -> scrollbar

        splitter = None
        for child in t.window().children():
            if isinstance(child, QtWidgets.QSplitter):
                splitter = child
                break

        if not splitter:
            return None

        for splitter_child in splitter.children():
            if isinstance(splitter_child, QtWidgets.QWidget):
                for subchild in splitter_child.children():
                    if isinstance(subchild, QtWidgets.QAbstractScrollArea):
                        # En Nuke 16, el scrollbar del timeline está en qt_scrollarea_vcontainer (no h_container)
                        for area_child in subchild.children():
                            if hasattr(area_child, 'objectName') and area_child.objectName() == "qt_scrollarea_vcontainer":
                                # El primer hijo del v_container es el scrollbar
                                if area_child.children():
                                    scrollbar = area_child.children()[0]
                                    if isinstance(scrollbar, QtWidgets.QScrollBar):
                                        # Verificar que tenga valores negativos (como en Nuke 15)
                                        if scrollbar.minimum() < 0 and scrollbar.maximum() < 0:
                                            return scrollbar
        return None

    except Exception as e:
        debug_print(f"Error en método robusto: {e}")
        return None


def obtener_limites_scrollbar():
    try:
        t = hiero.ui.getTimelineEditor(hiero.ui.activeSequence())

        # Primero intentar método original (Nuke 15)
        scrollbar = None
        try:
            scrollbar = t.window().children()[3].children()[0].children()[0].children()[7].children()[0]
            debug_print("Usando método original (Nuke 15)")
        except (IndexError, AttributeError):
            debug_print("Método original falló, intentando método robusto")
            scrollbar = obtener_scrollbar_robusto()

        if scrollbar is None:
            debug_print("No se pudo encontrar scrollbar con ningún método")
            return None, None, None

        limite_inferior = scrollbar.minimum()
        limite_superior = scrollbar.maximum()
        posicion_actual = scrollbar.value()

        # Verificación de sanidad: el scrollbar del timeline debería tener valores negativos en Nuke 15
        # Si encontramos valores positivos grandes, probablemente encontramos el scrollbar equivocado
        if limite_inferior == 0 and limite_superior > 1000 and posicion_actual == 0:
            debug_print("Scrollbar sospechoso encontrado (valores positivos), intentando método alternativo")

            # Intentar método robusto si el original dio valores sospechosos
            scrollbar_alt = obtener_scrollbar_robusto()
            if scrollbar_alt and scrollbar_alt != scrollbar:
                alt_min = scrollbar_alt.minimum()
                alt_max = scrollbar_alt.maximum()
                alt_val = scrollbar_alt.value()

                # Si el alternativo tiene valores más razonables (negativos), usarlo
                if alt_min < 0 and alt_max < 0 and alt_val < 0:
                    debug_print("Cambiando a scrollbar alternativo con valores negativos")
                    scrollbar = scrollbar_alt
                    limite_inferior = alt_min
                    limite_superior = alt_max
                    posicion_actual = alt_val

        debug_print(f"Posicion actual del scrollbar: {posicion_actual}")
        debug_print(f"Rango del scrollbar: {scrollbar.minimum()} a {scrollbar.maximum()}")
        debug_print(f"Tamano de pagina del scrollbar: {scrollbar.pageStep()}")

        return limite_inferior, limite_superior, scrollbar

    except Exception as e:
        debug_print(f"Ocurrio un error al obtener los limites: {e}")
        return None, None, None

def scroll_to_position(scrollbar, position):
    try:
        scrollbar.setValue(position)
        debug_print(f"Scrolled to position {position}.")
    except Exception as e:
        debug_print(f"Ocurrio un error al mover el scrollbar: {e}")


def main():
    # Obtener los limites y el scrollbar
    tiempo_inicio = time.time()
    limite_inferior, limite_superior, scrollbar = obtener_limites_scrollbar()
    tiempo_total = time.time() - tiempo_inicio

    if limite_inferior is not None and limite_superior is not None:
        debug_print(f"Limite inferior del scrollbar: {limite_inferior}")
        debug_print(f"Limite superior del scrollbar: {limite_superior}")
        debug_print(f"Tiempo de ejecucion: {tiempo_total:.2f} segundos")
        
        # Calcular la nueva posicion y mover el scrollbar
        nueva_posicion = limite_inferior + 70
        scroll_to_position(scrollbar, nueva_posicion)
        
        # Verificar la posicion final
        posicion_final = scrollbar.value()
        debug_print(f"Posicion final del scrollbar: {posicion_final}")

if __name__ == "__main__":
    main()