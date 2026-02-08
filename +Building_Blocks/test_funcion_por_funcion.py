# =============================================================================
# TEST CIENTÍFICO - UNA FUNCIÓN A LA VEZ
# =============================================================================
# Objetivo: Identificar EXACTAMENTE qué función causa EXACTAMENTE qué problema
#
# Metodología:
# 1. Probar CADA función de forma AISLADA
# 2. Logs escriben en tiempo real a debugPy.log
# 3. Si Hiero crashea, logs nos dirán EXACTAMENTE dónde
# 4. Ejecutar tests comentados/descomentados UNO A LA VEZ
# =============================================================================

import hiero.core
import hiero.ui
import os
import logging
import time
from LGA_QtAdapter_HieroTools import QtCore

# Secuencia hardcodeada para tests consistentes
TARGET_SEQUENCE_NAME = "010-350"


# =============================================================================
# LOGGING - Escribir a archivo en tiempo real
# =============================================================================
def setup_debug_logging():
    """Configura el logging para escribir en tiempo real a debugPy.log."""
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'debugPy.log')
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger('debug_logger')
    logger.setLevel(logging.DEBUG)
    # 🔑 CLAVE: Desactivar propagación al logger root (consola CMD)
    logger.propagate = False
    
    # Limpiar handlers existentes
    if logger.handlers:
        logger.handlers.clear()
    
    # Handler para archivo con escritura inmediata
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Formato simple
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger


def clear_debug_log():
    """Limpia el archivo de log al iniciar cada ejecución."""
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'debugPy.log')
    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"Warning: No se pudo limpiar el archivo de log: {e}")


# Flags de consola (por defecto apagada)
DEBUG_CONSOLE = False

# Inicializar logger
debug_logger = setup_debug_logging()


def debug_print(*message):
    """Función de debug que escribe a archivo (con consola opcional)."""
    msg = ' '.join(str(arg) for arg in message)
    if DEBUG_CONSOLE:
        print(msg)  # Consola
    debug_logger.info(msg)  # Archivo (escritura inmediata)


def _process_events():
    """Process Qt events."""
    if QtCore:
        try:
            QtCore.QCoreApplication.processEvents()
        except Exception:
            pass


def find_sequence(name):
    """Busca secuencia por nombre."""
    projects = hiero.core.projects()
    if not projects:
        return None
    
    for proj in projects:
        for seq in proj.sequences():
            if seq.name() == name:
                return seq
    return None


# =============================================================================
# TEST 1: SOLO setActiveSequence()
# =============================================================================
def test_1_solo_setActiveSequence():
    """
    TEST 1: Probar SOLO setActiveSequence() sin nada más.
    
    Pregunta: ¿Esta función SOLA causa inestabilidad?
    """
    debug_print("\n" + "=" * 100)
    debug_print("TEST 1: SOLO setActiveSequence()")
    debug_print("=" * 100)
    debug_print("Función bajo prueba: hiero.ui.setActiveSequence(seq)")
    debug_print("Hipótesis: Esta función NO debería causar inestabilidad")
    debug_print("")
    
    seq = find_sequence(TARGET_SEQUENCE_NAME)
    if not seq:
        debug_print(f"❌ Secuencia '{TARGET_SEQUENCE_NAME}' no encontrada")
        return
    
    debug_print(f"✅ Secuencia encontrada: {seq.name()}")
    debug_print("")
    
    # Estado ANTES
    debug_print("Estado ANTES de setActiveSequence():")
    active_before = hiero.ui.activeSequence()
    debug_print(f"  Secuencia activa: {active_before.name() if active_before else 'None'}")
    debug_print("")
    
    # EJECUTAR LA FUNCIÓN
    debug_print("🔧 Ejecutando: hiero.ui.setActiveSequence(seq)")
    try:
        hiero.ui.setActiveSequence(seq)
        debug_print("✅ setActiveSequence() completado sin excepciones")
    except Exception as e:
        debug_print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return
    
    _process_events()
    
    # Estado DESPUÉS
    debug_print("")
    debug_print("Estado DESPUÉS de setActiveSequence():")
    active_after = hiero.ui.activeSequence()
    debug_print(f"  Secuencia activa: {active_after.name() if active_after else 'None'}")
    debug_print("")
    
    debug_print("👁️ VERIFICACIÓN MANUAL REQUERIDA:")
    debug_print("   1. ¿Se creó/cambió algo en la UI?")
    debug_print("   2. ¿Hiero sigue respondiendo?")
    debug_print("   3. PRUEBA DE ESTABILIDAD: Selecciona clip y presiona DELETE")
    debug_print("")
    
    debug_print("✅ TEST 1 COMPLETADO - Verificar manualmente estabilidad")
    debug_print("=" * 100)


# =============================================================================
# TEST 2: SOLO openInTimeline() - SIN ProcessEvents
# =============================================================================
def test_2_solo_openInTimeline_sin_processEvents():
    """
    TEST 2: Probar openInTimeline() SIN processEvents().
    
    Pregunta: ¿El problema es openInTimeline() o processEvents()?
    """
    debug_print("\n" + "=" * 100)
    debug_print("TEST 2: SOLO openInTimeline() - SIN processEvents()")
    debug_print("=" * 100)
    debug_print("Función bajo prueba: hiero.ui.openInTimeline(seq)")
    debug_print("SIN llamar a processEvents() después")
    debug_print("")
    
    seq = find_sequence(TARGET_SEQUENCE_NAME)
    if not seq:
        debug_print(f"❌ Secuencia '{TARGET_SEQUENCE_NAME}' no encontrada")
        return
    
    debug_print(f"✅ Secuencia encontrada: {seq.name()}")
    debug_print("")
    
    # EJECUTAR LA FUNCIÓN (SIN processEvents)
    debug_print("🔧 Ejecutando: hiero.ui.openInTimeline(seq)")
    debug_print("   (SIN processEvents después)")
    try:
        hiero.ui.openInTimeline(seq)
        debug_print("✅ openInTimeline() completado sin excepciones")
    except Exception as e:
        debug_print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return
    
    # NO llamamos processEvents() - ese es el punto del test
    
    debug_print("")
    debug_print("📊 Observación: ¿Se creó timeline/viewer?")
    active = hiero.ui.activeSequence()
    debug_print(f"  Secuencia activa: {active.name() if active else 'None'}")
    debug_print("")
    
    debug_print("👁️ VERIFICACIÓN MANUAL REQUERIDA:")
    debug_print("   Prueba de estabilidad: Borrar clip")
    debug_print("")
    
    debug_print("✅ TEST 2 COMPLETADO - Verificar manualmente estabilidad")
    debug_print("=" * 100)


# =============================================================================
# TEST 3: SOLO openInTimeline() - CON ProcessEvents
# =============================================================================
def test_3_solo_openInTimeline_con_processEvents():
    """
    TEST 3: Probar openInTimeline() CON processEvents().
    
    Pregunta: ¿processEvents() DESPUÉS de openInTimeline() causa el problema?
    """
    debug_print("\n" + "=" * 100)
    debug_print("TEST 3: SOLO openInTimeline() - CON processEvents()")
    debug_print("=" * 100)
    debug_print("Función bajo prueba: hiero.ui.openInTimeline(seq) + processEvents()")
    debug_print("")
    
    seq = find_sequence(TARGET_SEQUENCE_NAME)
    if not seq:
        debug_print(f"❌ Secuencia '{TARGET_SEQUENCE_NAME}' no encontrada")
        return
    
    debug_print(f"✅ Secuencia encontrada: {seq.name()}")
    debug_print("")
    
    # EJECUTAR LA FUNCIÓN
    debug_print("🔧 Ejecutando: hiero.ui.openInTimeline(seq)")
    try:
        hiero.ui.openInTimeline(seq)
        debug_print("✅ openInTimeline() completado sin excepciones")
    except Exception as e:
        debug_print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return
    
    # AHORA SÍ processEvents
    debug_print("🔧 Ejecutando: processEvents()")
    _process_events()
    debug_print("✅ processEvents() completado")
    
    debug_print("")
    debug_print("📊 Observación: ¿Se creó timeline/viewer?")
    active = hiero.ui.activeSequence()
    debug_print(f"  Secuencia activa: {active.name() if active else 'None'}")
    debug_print("")
    
    debug_print("👁️ VERIFICACIÓN MANUAL REQUERIDA:")
    debug_print("   Prueba de estabilidad: Borrar clip")
    debug_print("")
    
    debug_print("✅ TEST 3 COMPLETADO - Verificar manualmente estabilidad")
    debug_print("=" * 100)


# =============================================================================
# TEST 4: SOLO openInViewer()
# =============================================================================
def test_4_solo_openInViewer():
    """
    TEST 4: Probar SOLO openInViewer().
    
    Pregunta: ¿Esta función causa inestabilidad?
    """
    debug_print("\n" + "=" * 100)
    debug_print("TEST 4: SOLO openInViewer()")
    debug_print("=" * 100)
    debug_print("Función bajo prueba: hiero.ui.openInViewer(seq)")
    debug_print("")
    
    seq = find_sequence(TARGET_SEQUENCE_NAME)
    if not seq:
        debug_print(f"❌ Secuencia '{TARGET_SEQUENCE_NAME}' no encontrada")
        return
    
    debug_print(f"✅ Secuencia encontrada: {seq.name()}")
    debug_print("")
    
    # EJECUTAR LA FUNCIÓN
    debug_print("🔧 Ejecutando: hiero.ui.openInViewer(seq)")
    try:
        viewer = hiero.ui.openInViewer(seq)
        debug_print(f"✅ openInViewer() completado sin excepciones")
        debug_print(f"   Retornó: {viewer}")
    except Exception as e:
        debug_print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return
    
    _process_events()
    
    debug_print("")
    debug_print("📊 Observación:")
    debug_print(f"  Current viewer: {hiero.ui.currentViewer()}")
    debug_print(f"  Secuencia activa: {hiero.ui.activeSequence().name() if hiero.ui.activeSequence() else 'None'}")
    debug_print("")
    
    debug_print("👁️ VERIFICACIÓN MANUAL REQUERIDA:")
    debug_print("   Prueba de estabilidad: Borrar clip")
    debug_print("")
    
    debug_print("✅ TEST 4 COMPLETADO - Verificar manualmente estabilidad")
    debug_print("=" * 100)


# =============================================================================
# TEST 5: getTimelineEditor() - Solo obtener, NO mostrar
# =============================================================================
def test_5_solo_getTimelineEditor():
    """
    TEST 5: Probar SOLO getTimelineEditor() sin hacer nada con él.
    
    Pregunta: ¿Obtener el timeline causa algún problema?
    """
    debug_print("\n" + "=" * 100)
    debug_print("TEST 5: SOLO getTimelineEditor() - Sin mostrar")
    debug_print("=" * 100)
    debug_print("Función bajo prueba: hiero.ui.getTimelineEditor(seq)")
    debug_print("Solo OBTENER el timeline, NO mostrarlo")
    debug_print("")
    
    seq = find_sequence(TARGET_SEQUENCE_NAME)
    if not seq:
        debug_print(f"❌ Secuencia '{TARGET_SEQUENCE_NAME}' no encontrada")
        return
    
    debug_print(f"✅ Secuencia encontrada: {seq.name()}")
    debug_print("")
    
    # EJECUTAR LA FUNCIÓN
    debug_print("🔧 Ejecutando: hiero.ui.getTimelineEditor(seq)")
    try:
        timeline = hiero.ui.getTimelineEditor(seq)
        debug_print(f"✅ getTimelineEditor() completado sin excepciones")
        debug_print(f"   Retornó: {timeline}")
        
        if timeline:
            debug_print(f"   Timeline.sequence(): {timeline.sequence().name() if timeline.sequence() else 'None'}")
    except Exception as e:
        debug_print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return
    
    _process_events()
    
    debug_print("")
    debug_print("📊 Observación: NO hicimos nada con el timeline obtenido")
    debug_print("   Solo lo obtuvimos y lo guardamos en una variable")
    debug_print("")
    
    debug_print("👁️ VERIFICACIÓN MANUAL REQUERIDA:")
    debug_print("   Prueba de estabilidad: Borrar clip")
    debug_print("")
    
    debug_print("✅ TEST 5 COMPLETADO - Verificar manualmente estabilidad")
    debug_print("=" * 100)


# =============================================================================
# MAIN: Ejecutar tests en orden
# =============================================================================
def main():
    # Limpiar log al inicio
    clear_debug_log()
    
    debug_print("🔬 TESTS CIENTÍFICOS - UNA FUNCIÓN A LA VEZ")
    debug_print("Objetivo: Identificar EXACTAMENTE qué función causa qué problema")
    debug_print("")
    debug_print("METODOLOGÍA:")
    debug_print("  • Cada test es INDEPENDIENTE y escribe logs a debugPy.log")
    debug_print("  • Si Hiero crashea, logs dirán EXACTAMENTE dónde")
    debug_print("  • Descomentar/ejecutar tests UNO A LA VEZ")
    debug_print("  • Verificar estabilidad después de cada test (borrar clip)")
    debug_print("")
    debug_print("=" * 100)
    debug_print("")
    
    # =========================================================================
    # INSTRUCCIONES: Descomentar UN test a la vez para probar
    # =========================================================================
    
    # Test 1: setActiveSequence (el más seguro, probar primero)
    # test_1_solo_setActiveSequence()
    
    # Test 2: openInTimeline SIN processEvents (descomentar para probar)
    # test_2_solo_openInTimeline_sin_processEvents()
    
    # Test 3: openInTimeline CON processEvents (descomentar para probar)
    # test_3_solo_openInTimeline_con_processEvents()
    
    # Test 4: openInViewer (descomentar para probar)
    # test_4_solo_openInViewer()
    
    # Test 5: getTimelineEditor solo obtener (descomentar para probar)
    test_5_solo_getTimelineEditor()
    
    debug_print("")
    debug_print("=" * 100)
    debug_print("📊 EJECUCIÓN COMPLETADA")
    debug_print("=" * 100)
    debug_print("PRÓXIMO PASO:")
    debug_print("  1. Verifica estabilidad: Selecciona clip y presiona DELETE")
    debug_print("  2. Si crashea o queda inestable: ANOTA QUÉ TEST LO CAUSÓ")
    debug_print("  3. Si es estable: Descomentar siguiente test y repetir")
    debug_print("")
    debug_print("Logs guardados en: logs/debugPy.log")
    debug_print("=" * 100)


if __name__ == "__main__":
    main()

