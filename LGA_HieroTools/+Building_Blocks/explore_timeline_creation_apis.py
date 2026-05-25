# =============================================================================
# EXPLORACIÓN EXHAUSTIVA: APIs de creación/manipulación de timelines
# =============================================================================
# 🎯 OBJETIVO: Descubrir TODOS los métodos disponibles para crear/mostrar timelines
# 
# Exploramos:
# 1. Métodos específicos de TimelineEditor (no solo Qt)
# 2. TODAS las APIs en hiero.ui relacionadas con timelines
# 3. WindowManager y métodos de gestión de ventanas
# 4. Diferencias entre timeline oculto vs visible
# =============================================================================

import hiero.core
import hiero.ui


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
# EXPLORACIÓN 1: Métodos ESPECÍFICOS de TimelineEditor (no Qt genérico)
# =============================================================================
def explore_timeline_editor_specific_methods():
    """
    Explorar métodos que NO sean de Qt, sino específicos de Hiero.
    """
    print("=" * 100)
    print("EXPLORACIÓN 1: Métodos ESPECÍFICOS de TimelineEditor de Hiero")
    print("=" * 100)
    
    seq = find_sequence("010-350")
    if not seq:
        print("❌ Secuencia no encontrada")
        return
    
    timeline = hiero.ui.getTimelineEditor(seq)
    if not timeline:
        print("❌ No se pudo obtener timeline")
        return
    
    print(f"✅ Timeline obtenido: {timeline}")
    print(f"   Tipo: {type(timeline)}")
    print(f"   Clase: {timeline.__class__.__name__}")
    
    # Filtrar SOLO métodos que NO sean de Qt (probablemente de Hiero)
    all_methods = dir(timeline)
    
    # Métodos Qt comunes a filtrar
    qt_common_methods = {
        'acceptDrops', 'accessibleDescription', 'accessibleName', 'actionEvent', 'actions',
        'activateWindow', 'addAction', 'addActions', 'adjustSize', 'autoFillBackground',
        'backgroundRole', 'baseSize', 'blockSignals', 'changeEvent', 'childAt', 'childEvent',
        'children', 'childrenRect', 'childrenRegion', 'clearFocus', 'clearMask', 'close',
        'closeEvent', 'colorCount', 'connect', 'connectNotify', 'contentsMargins', 'contentsRect',
        'contextMenuEvent', 'contextMenuPolicy', 'create', 'createWinId', 'cursor', 'deleteLater',
        'depth', 'destroy', 'destroyed', 'devType', 'disconnect', 'disconnectNotify', 'dragEnterEvent',
        'dragLeaveEvent', 'dragMoveEvent', 'dropEvent', 'dumpObjectInfo', 'dumpObjectTree',
        'dynamicPropertyNames', 'effectiveWinId', 'emit', 'ensurePolished', 'enterEvent', 'event',
        'eventFilter', 'find', 'findChild', 'findChildren', 'focusInEvent', 'focusNextChild',
        'focusNextPrevChild', 'focusOutEvent', 'focusPolicy', 'focusPreviousChild', 'focusProxy',
        'focusWidget', 'font', 'fontInfo', 'fontMetrics', 'foregroundRole', 'frameGeometry',
        'frameSize', 'geometry', 'grab', 'grabGesture', 'grabKeyboard', 'grabMouse', 'grabShortcut',
        'graphicsEffect', 'graphicsProxyWidget', 'hasFocus', 'hasHeightForWidth', 'hasMouseTracking',
        'hasTabletTracking', 'height', 'heightForWidth', 'heightMM', 'hide', 'hideEvent', 'inherits',
        'initPainter', 'inputMethodEvent', 'inputMethodHints', 'inputMethodQuery', 'insertAction',
        'insertActions', 'installEventFilter', 'internalWinId', 'isActiveWindow', 'isAncestorOf',
        'isEnabled', 'isEnabledTo', 'isFullScreen', 'isHidden', 'isLeftToRight', 'isMaximized',
        'isMinimized', 'isModal', 'isRightToLeft', 'isSignalConnected', 'isTopLevel', 'isVisible',
        'isVisibleTo', 'isWidgetType', 'isWindow', 'isWindowModified', 'isWindowType', 'keyPressEvent',
        'keyReleaseEvent', 'keyboardGrabber', 'killTimer', 'layout', 'layoutDirection', 'leaveEvent',
        'locale', 'logicalDpiX', 'logicalDpiY', 'lower', 'mapFrom', 'mapFromGlobal', 'mapFromParent',
        'mapTo', 'mapToGlobal', 'mapToParent', 'mask', 'maximumHeight', 'maximumSize', 'maximumWidth',
        'metaObject', 'metric', 'minimumHeight', 'minimumSize', 'minimumSizeHint', 'minimumWidth',
        'mouseDoubleClickEvent', 'mouseGrabber', 'mouseMoveEvent', 'mousePressEvent', 'mouseReleaseEvent',
        'move', 'moveEvent', 'moveToThread', 'nativeEvent', 'nativeParentWidget', 'nextInFocusChain',
        'normalGeometry', 'objectName', 'objectNameChanged', 'overrideWindowFlags', 'overrideWindowState',
        'paintEngine', 'paintEvent', 'painters', 'paintingActive', 'palette', 'parent', 'parentWidget',
        'physicalDpiX', 'physicalDpiY', 'pos', 'previousInFocusChain', 'property', 'raise_', 'receivers',
        'rect', 'redirected', 'releaseKeyboard', 'releaseMouse', 'releaseShortcut', 'removeAction',
        'removeEventFilter', 'render', 'repaint', 'resize', 'resizeEvent', 'restoreGeometry',
        'saveGeometry', 'screen', 'scroll', 'sender', 'senderSignalIndex', 'setAcceptDrops',
        'setAccessibleDescription', 'setAccessibleName', 'setAttribute', 'setAutoFillBackground',
        'setBackgroundRole', 'setBaseSize', 'setContentsMargins', 'setContextMenuPolicy', 'setCursor',
        'setDisabled', 'setEnabled', 'setFixedHeight', 'setFixedSize', 'setFixedWidth', 'setFocus',
        'setFocusPolicy', 'setFocusProxy', 'setFont', 'setForegroundRole', 'setGeometry',
        'setGraphicsEffect', 'setHidden', 'setInputMethodHints', 'setLayout', 'setLayoutDirection',
        'setLocale', 'setMask', 'setMaximumHeight', 'setMaximumSize', 'setMaximumWidth',
        'setMinimumHeight', 'setMinimumSize', 'setMinimumWidth', 'setMouseTracking', 'setObjectName',
        'setPalette', 'setParent', 'setProperty', 'setScreen', 'setShortcutAutoRepeat',
        'setShortcutEnabled', 'setSizeIncrement', 'setSizePolicy', 'setStatusTip', 'setStyle',
        'setStyleSheet', 'setTabOrder', 'setTabletTracking', 'setToolTip', 'setToolTipDuration',
        'setUpdatesEnabled', 'setVisible', 'setWhatsThis', 'setWindowFilePath', 'setWindowFlag',
        'setWindowFlags', 'setWindowIcon', 'setWindowIconText', 'setWindowModality', 'setWindowModified',
        'setWindowOpacity', 'setWindowRole', 'setWindowState', 'setWindowTitle', 'sharedPainter',
        'show', 'showEvent', 'showFullScreen', 'showMaximized', 'showMinimized', 'showNormal',
        'signalsBlocked', 'size', 'sizeHint', 'sizeIncrement', 'sizePolicy', 'stackUnder', 'startTimer',
        'staticMetaObject', 'statusTip', 'style', 'styleSheet', 'tabletEvent', 'testAttribute',
        'thread', 'timerEvent', 'toolTip', 'toolTipDuration', 'topLevelWidget', 'tr', 'underMouse',
        'ungrabGesture', 'unsetCursor', 'unsetLayoutDirection', 'unsetLocale', 'update',
        'updateGeometry', 'updateMicroFocus', 'updatesEnabled', 'visibleRegion', 'whatsThis',
        'wheelEvent', 'width', 'widthMM', 'winId', 'window', 'windowFilePath', 'windowFlags',
        'windowHandle', 'windowIcon', 'windowIconChanged', 'windowIconText', 'windowIconTextChanged',
        'windowModality', 'windowOpacity', 'windowRole', 'windowState', 'windowTitle',
        'windowTitleChanged', 'windowType', 'x', 'y'
    }
    
    # Métodos que probablemente SON de Hiero
    hiero_specific_methods = [m for m in all_methods if m not in qt_common_methods and not m.startswith('_')]
    
    print(f"\n🔍 MÉTODOS ESPECÍFICOS DE HIERO (no Qt estándar): {len(hiero_specific_methods)}")
    for i, method in enumerate(hiero_specific_methods, 1):
        # Ver si es callable
        try:
            attr = getattr(timeline, method)
            is_callable = callable(attr)
            type_info = "método" if is_callable else "propiedad"
            print(f"   {i:2d}. {method:30s} [{type_info}]")
            
            # Si es propiedad, mostrar valor
            if not is_callable:
                try:
                    value = attr
                    print(f"       └─ Valor: {value}")
                except:
                    pass
        except:
            print(f"   {i:2d}. {method:30s} [error]")
    
    # Intentar llamar métodos que suenen prometedores
    print("\n🔧 PROBANDO métodos prometedores:")
    
    promising_methods = [m for m in hiero_specific_methods if any(x in m.lower() for x in 
                        ['sequence', 'viewer', 'player', 'track', 'item', 'selection', 'time', 'frame'])]
    
    for method in promising_methods:
        try:
            attr = getattr(timeline, method)
            if callable(attr):
                # Intentar llamar sin parámetros
                try:
                    result = attr()
                    print(f"   ✅ {method}() → {result}")
                except TypeError as e:
                    print(f"   ⚠️ {method}() requiere parámetros: {e}")
                except Exception as e:
                    print(f"   ❌ {method}() error: {e}")
            else:
                # Propiedad
                print(f"   📋 {method} = {attr}")
        except Exception as e:
            print(f"   ❌ Error con {method}: {e}")


# =============================================================================
# EXPLORACIÓN 2: TODAS las APIs en hiero.ui
# =============================================================================
def explore_all_hiero_ui_apis():
    """
    Listar TODAS las APIs en hiero.ui relacionadas con timelines/viewers.
    """
    print("\n" + "=" * 100)
    print("EXPLORACIÓN 2: TODAS las APIs en hiero.ui")
    print("=" * 100)
    
    all_apis = dir(hiero.ui)
    
    # Filtrar las relacionadas con timeline/viewer/window
    categories = {
        'timeline': [],
        'viewer': [],
        'window': [],
        'sequence': [],
        'editor': [],
        'other': []
    }
    
    for api in all_apis:
        if api.startswith('_'):
            continue
        
        api_lower = api.lower()
        categorized = False
        
        for category in categories.keys():
            if category in api_lower:
                categories[category].append(api)
                categorized = True
                break
        
        if not categorized:
            categories['other'].append(api)
    
    # Mostrar por categoría
    for category, apis in categories.items():
        if not apis:
            continue
        
        print(f"\n📋 Categoría '{category.upper()}': {len(apis)} APIs")
        for api in sorted(apis):
            try:
                obj = getattr(hiero.ui, api)
                is_callable = callable(obj)
                type_str = "función" if is_callable else "clase/constante"
                print(f"   • {api:40s} [{type_str}]")
                
                # Si es función, ver su firma
                if is_callable:
                    try:
                        import inspect
                        sig = inspect.signature(obj)
                        print(f"     └─ {api}{sig}")
                    except:
                        pass
            except:
                print(f"   • {api:40s} [error]")


# =============================================================================
# EXPLORACIÓN 3: WindowManager - Métodos de gestión de ventanas
# =============================================================================
def explore_window_manager():
    """
    Explorar hiero.ui.windowManager() y sus métodos.
    """
    print("\n" + "=" * 100)
    print("EXPLORACIÓN 3: WindowManager")
    print("=" * 100)
    
    try:
        wm = hiero.ui.windowManager()
        print(f"✅ WindowManager obtenido: {wm}")
        print(f"   Tipo: {type(wm)}")
        
        print("\n📋 Métodos disponibles en WindowManager:")
        wm_methods = [m for m in dir(wm) if not m.startswith('_')]
        
        for i, method in enumerate(wm_methods, 1):
            try:
                attr = getattr(wm, method)
                is_callable = callable(attr)
                type_info = "método" if is_callable else "propiedad"
                print(f"   {i:2d}. {method:30s} [{type_info}]")
                
                # Si es método, intentar llamar sin parámetros para ver qué hace
                if is_callable and method in ['windows', 'activeWindow']:
                    try:
                        result = attr()
                        print(f"       └─ {method}() → {type(result).__name__}")
                        if method == 'windows':
                            print(f"          Total ventanas: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                    except:
                        pass
            except:
                print(f"   {i:2d}. {method:30s} [error]")
        
        # ¿Tiene método para abrir/mostrar timeline?
        print("\n🔍 Buscando métodos relacionados con timeline/viewer:")
        timeline_methods = [m for m in wm_methods if any(x in m.lower() for x in ['timeline', 'viewer', 'sequence', 'show', 'open'])]
        for method in timeline_methods:
            print(f"   ⭐ {method}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# =============================================================================
# EXPLORACIÓN 4: Comparar timeline OCULTO vs VISIBLE
# =============================================================================
def compare_hidden_vs_visible_timeline():
    """
    Comparar propiedades de timeline oculto vs uno visible.
    """
    print("\n" + "=" * 100)
    print("EXPLORACIÓN 4: Comparar timeline OCULTO vs VISIBLE")
    print("=" * 100)
    
    # Timeline oculto (010-350)
    seq_hidden = find_sequence("010-350")
    timeline_hidden = hiero.ui.getTimelineEditor(seq_hidden) if seq_hidden else None
    
    # Timeline visible (buscar uno que esté abierto)
    seq_visible = find_sequence("360-700")  # Ajustar según tu proyecto
    timeline_visible = hiero.ui.getTimelineEditor(seq_visible) if seq_visible else None
    
    if not timeline_hidden:
        print("❌ No se pudo obtener timeline oculto")
        return
    
    if not timeline_visible:
        print("⚠️ No se pudo obtener timeline visible para comparar")
        print("   (Comparación solo con timeline oculto)")
    
    print(f"\n🔍 TIMELINE OCULTO (010-350):")
    analyze_timeline_properties(timeline_hidden)
    
    if timeline_visible:
        print(f"\n🔍 TIMELINE VISIBLE (360-700):")
        analyze_timeline_properties(timeline_visible)
        
        print(f"\n📊 DIFERENCIAS CLAVE:")
        compare_properties(timeline_hidden, timeline_visible)


def analyze_timeline_properties(timeline):
    """Analiza propiedades clave de un timeline."""
    props = {
        'isVisible()': timeline.isVisible() if hasattr(timeline, 'isVisible') else None,
        'isHidden()': timeline.isHidden() if hasattr(timeline, 'isHidden') else None,
        'isWindow()': timeline.isWindow() if hasattr(timeline, 'isWindow') else None,
        'isTopLevel()': timeline.isTopLevel() if hasattr(timeline, 'isTopLevel') else None,
        'parent()': type(timeline.parent()).__name__ if hasattr(timeline, 'parent') and timeline.parent() else None,
        'window()': type(timeline.window()).__name__ if hasattr(timeline, 'window') and timeline.window() else None,
        'objectName()': timeline.objectName() if hasattr(timeline, 'objectName') else None,
        'windowTitle()': timeline.windowTitle() if hasattr(timeline, 'windowTitle') else None,
    }
    
    for key, value in props.items():
        print(f"   {key:20s} = {value}")


def compare_properties(timeline_hidden, timeline_visible):
    """Compara propiedades entre dos timelines."""
    props_to_compare = ['isVisible', 'isHidden', 'isWindow', 'isTopLevel', 'parent', 'window']
    
    for prop in props_to_compare:
        try:
            hidden_val = getattr(timeline_hidden, prop)() if hasattr(timeline_hidden, prop) else None
            visible_val = getattr(timeline_visible, prop)() if hasattr(timeline_visible, prop) else None
            
            if hidden_val != visible_val:
                print(f"   ❗ {prop:20s} → Oculto: {hidden_val}, Visible: {visible_val}")
            else:
                print(f"   ✓ {prop:20s} → Ambos: {hidden_val}")
        except:
            pass


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("🚀 EXPLORACIÓN EXHAUSTIVA DE APIs DE TIMELINE")
    print("Objetivo: Descubrir métodos alternativos para crear/mostrar timelines")
    print("")
    
    # EXPLORACIÓN 1: Métodos específicos de Hiero en TimelineEditor
    explore_timeline_editor_specific_methods()
    
    # EXPLORACIÓN 2: Todas las APIs en hiero.ui
    explore_all_hiero_ui_apis()
    
    # EXPLORACIÓN 3: WindowManager
    explore_window_manager()
    
    # EXPLORACIÓN 4: Comparar oculto vs visible
    compare_hidden_vs_visible_timeline()
    
    print("\n" + "=" * 100)
    print("✅ EXPLORACIÓN COMPLETADA")
    print("📝 Revisar output para identificar APIs prometedoras")
    print("=" * 100)


if __name__ == "__main__":
    main()

