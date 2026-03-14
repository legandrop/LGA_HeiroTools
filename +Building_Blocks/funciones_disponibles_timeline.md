> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.

# =============================================================================
# EJECUCIÓN AUTOMÁTICA CUANDO SE COPIA Y PEGA EN HIERO
# =============================================================================

debug_print("🔍 EJECUTANDO EXPLORACIÓN COMPLETA...")
debug_print("="*100)

# 1. Explorar secuencias y panels abiertos
explore_sequences_and_open_panels()

# 2. Explorar métodos disponibles para timelines
debug_print("\n" + "="*100)
explore_timeline_methods()

# 3. Instrucciones para TEORÍA 2
debug_print("\n" + "="*100)
debug_print("🎯 PRUEBA TEORÍA 2 - CREAR TIMELINE PARA SECUENCIA LIBRE")
debug_print("="*100)
debug_print("💡 Para probar TEORÍA 2, ejecuta en Hiero:")
debug_print("   test_sequence_creation()")

if __name__ == "__main__":
    main()
# Result: 🔍 EJECUTANDO EXPLORACIÓN COMPLETA...
====================================================================================================
====================================================================================================
EXPLORACIÓN: SECUENCIAS DEL PROYECTO Y SUS PANELS ABIERTOS
====================================================================================================

📋 TOTAL DE SECUENCIAS EN PROYECTO: 5
--------------------------------------------------------------------------------
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer uk.co.thefoundry.viewer.contactsheet.1 - windowTitle: 'Contact Sheet' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia

🔍 VIEWERS REALMENTE ABIERTOS EN LA UI: 4
  • uk.co.thefoundry.sequenceviewer.3 → Secuencia: 360-700
  • uk.co.thefoundry.sequenceviewer.25 → Secuencia: 710-990
  • uk.co.thefoundry.viewer.contactsheet.1 → Secuencia: Sin secuencia
  • uk.co.thefoundry.sequenceviewer.2 → Secuencia: 010-350

🔍 TIMELINES REALMENTE ABIERTOS EN LA UI: 1
  • uk.co.thefoundry.timeline.5 → Secuencia: 360-700

🔍 VERIFICANDO SECUENCIA: z_EditRef_v1_6_20250725 (ID: 0x1d245169280)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 710-990 (ID: 0x1d245169240)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 360-700 (ID: 0x1d2451c7980)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 010-350 (ID: 0x1d24519e8c0)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: z_EditRef_v.0.2 (ID: 0x1d24519e840)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

====================================================================================================
RESUMEN FINAL
====================================================================================================

📊 ESTADÍSTICAS:
   • Total secuencias: 5
   • Secuencias con timeline/viewer: 0
   • Secuencias libres: 5

🟢 SECUENCIAS LIBRES (sin timeline ni viewer - disponibles para crear):
   1. z_EditRef_v1_6_20250725 (ID: 0x1d245169280)
   2. 710-990 (ID: 0x1d245169240)
   3. 360-700 (ID: 0x1d2451c7980)
   4. 010-350 (ID: 0x1d24519e8c0)
   5. z_EditRef_v.0.2 (ID: 0x1d24519e840)

🔴 SECUENCIAS OCUPADAS (con timeline/viewer abierto):
   ✅ Todas las secuencias están libres

====================================================================================================
====================================================================================================
🔍 EXPLORACIÓN DE MÉTODOS DISPONIBLES PARA TIMELINE EDITOR
====================================================================================================
✅ Encontrado timeline de ejemplo: uk.co.thefoundry.timeline.5

🔧 MÉTODOS DISPONIBLES EN TIMELINE EDITOR (usando dir()):
   Total métodos públicos: 322

   📋 Lista completa de métodos:
       1. PaintDeviceMetric
       2. RenderFlag
       3. acceptDrops
       4. accessibleDescription
       5. accessibleName
       6. actionEvent
       7. actions
       8. activateWindow
       9. addAction
      10. addActions
      11. adjustSize
      12. autoFillBackground
      13. backgroundRole
      14. backingStore
      15. baseSize
      16. blockSignals
      17. changeEvent
      18. childAt
      19. childEvent
      20. children
      21. childrenRect
      22. childrenRegion
      23. clearFocus
      24. clearMask
      25. close
      26. closeEvent
      27. colorCount
      28. connect
      29. connectNotify
      30. contentsMargins
      31. contentsRect
      32. contextMenuEvent
      33. contextMenuPolicy
      34. create
      35. createWinId
      36. createWindowContainer
      37. cursor
      38. customContextMenuRequested
      39. customEvent
      40. deleteLater
      41. depth
      42. destroy
      43. destroyed
      44. devType
      45. devicePixelRatio
      46. devicePixelRatioF
      47. devicePixelRatioFScale
      48. disconnect
      49. disconnectNotify
      50. dragEnterEvent
      51. dragLeaveEvent
      52. dragMoveEvent
      53. dropEvent
      54. dumpObjectInfo
      55. dumpObjectTree
      56. dynamicPropertyNames
      57. effectiveWinId
      58. emit
      59. ensurePolished
      60. enterEvent
      61. event
      62. eventFilter
      63. find
      64. findChild
      65. findChildren
      66. focusInEvent
      67. focusNextChild
      68. focusNextPrevChild
      69. focusOutEvent
      70. focusPolicy
      71. focusPreviousChild
      72. focusProxy
      73. focusWidget
      74. font
      75. fontInfo
      76. fontMetrics
      77. foregroundRole
      78. frameGeometry
      79. frameSize
      80. geometry
      81. grab
      82. grabGesture
      83. grabKeyboard
      84. grabMouse
      85. grabShortcut
      86. graphicsEffect
      87. graphicsProxyWidget
      88. hasFocus
      89. hasHeightForWidth
      90. hasMouseTracking
      91. hasTabletTracking
      92. height
      93. heightForWidth
      94. heightMM
      95. hide
      96. hideEvent
      97. inherits
      98. initPainter
      99. inputMethodEvent
      100. inputMethodHints
      101. inputMethodQuery
      102. insertAction
      103. insertActions
      104. installEventFilter
      105. internalWinId
      106. isActiveWindow
      107. isAncestorOf
      108. isEnabled
      109. isEnabledTo
      110. isFullScreen
      111. isHidden
      112. isLeftToRight
      113. isMaximized
      114. isMinimized
      115. isModal
      116. isQuickItemType
      117. isRightToLeft
      118. isSignalConnected
      119. isTopLevel
      120. isVisible
      121. isVisibleTo
      122. isWidgetType
      123. isWindow
      124. isWindowModified
      125. isWindowType
      126. keyPressEvent
      127. keyReleaseEvent
      128. keyboardGrabber
      129. killTimer
      130. layout
      131. layoutDirection
      132. leaveEvent
      133. locale
      134. logicalDpiX
      135. logicalDpiY
      136. lower
      137. mapFrom
      138. mapFromGlobal
      139. mapFromParent
      140. mapTo
      141. mapToGlobal
      142. mapToParent
      143. mask
      144. maximumHeight
      145. maximumSize
      146. maximumWidth
      147. metaObject
      148. metric
      149. minimumHeight
      150. minimumSize
      151. minimumSizeHint
      152. minimumWidth
      153. mouseDoubleClickEvent
      154. mouseGrabber
      155. mouseMoveEvent
      156. mousePressEvent
      157. mouseReleaseEvent
      158. move
      159. moveEvent
      160. moveToThread
      161. nativeEvent
      162. nativeParentWidget
      163. nextInFocusChain
      164. normalGeometry
      165. objectName
      166. objectNameChanged
      167. overrideWindowFlags
      168. overrideWindowState
      169. paintEngine
      170. paintEvent
      171. painters
      172. paintingActive
      173. palette
      174. parent
      175. parentWidget
      176. physicalDpiX
      177. physicalDpiY
      178. pos
      179. previousInFocusChain
      180. property
      181. raise_
      182. receivers
      183. rect
      184. redirected
      185. releaseKeyboard
      186. releaseMouse
      187. releaseShortcut
      188. removeAction
      189. removeEventFilter
      190. render
      191. repaint
      192. resize
      193. resizeEvent
      194. restoreGeometry
      195. saveGeometry
      196. screen
      197. scroll
      198. sender
      199. senderSignalIndex
      200. setAcceptDrops
      201. setAccessibleDescription
      202. setAccessibleName
      203. setAttribute
      204. setAutoFillBackground
      205. setBackgroundRole
      206. setBaseSize
      207. setContentsMargins
      208. setContextMenuPolicy
      209. setCursor
      210. setDisabled
      211. setEnabled
      212. setFixedHeight
      213. setFixedSize
      214. setFixedWidth
      215. setFocus
      216. setFocusPolicy
      217. setFocusProxy
      218. setFont
      219. setForegroundRole
      220. setGeometry
      221. setGraphicsEffect
      222. setHidden
      223. setInputMethodHints
      224. setLayout
      225. setLayoutDirection
      226. setLocale
      227. setMask
      228. setMaximumHeight
      229. setMaximumSize
      230. setMaximumWidth
      231. setMinimumHeight
      232. setMinimumSize
      233. setMinimumWidth
      234. setMouseTracking
      235. setObjectName
      236. setPalette
      237. setParent
      238. setProperty
      239. setScreen
      240. setShortcutAutoRepeat
      241. setShortcutEnabled
      242. setSizeIncrement
      243. setSizePolicy
      244. setStatusTip
      245. setStyle
      246. setStyleSheet
      247. setTabOrder
      248. setTabletTracking
      249. setToolTip
      250. setToolTipDuration
      251. setUpdatesEnabled
      252. setVisible
      253. setWhatsThis
      254. setWindowFilePath
      255. setWindowFlag
      256. setWindowFlags
      257. setWindowIcon
      258. setWindowIconText
      259. setWindowModality
      260. setWindowModified
      261. setWindowOpacity
      262. setWindowRole
      263. setWindowState
      264. setWindowTitle
      265. sharedPainter
      266. show
      267. showEvent
      268. showFullScreen
      269. showMaximized
      270. showMinimized
      271. showNormal
      272. signalsBlocked
      273. size
      274. sizeHint
      275. sizeIncrement
      276. sizePolicy
      277. stackUnder
      278. startTimer
      279. staticMetaObject
      280. statusTip
      281. style
      282. styleSheet
      283. tabletEvent
      284. testAttribute
      285. thread
      286. timerEvent
      287. toolTip
      288. toolTipDuration
      289. topLevelWidget
      290. tr
      291. underMouse
      292. ungrabGesture
      293. unsetCursor
      294. unsetLayoutDirection
      295. unsetLocale
      296. update
      297. updateGeometry
      298. updateMicroFocus
      299. updatesEnabled
      300. visibleRegion
      301. whatsThis
      302. wheelEvent
      303. width
      304. widthMM
      305. winId
      306. window
      307. windowFilePath
      308. windowFlags
      309. windowHandle
      310. windowIcon
      311. windowIconChanged
      312. windowIconText
      313. windowIconTextChanged
      314. windowModality
      315. windowOpacity
      316. windowRole
      317. windowState
      318. windowTitle
      319. windowTitleChanged
      320. windowType
      321. x
      322. y

🔍 TODOS LOS ATRIBUTOS DISPONIBLES:
   Total atributos: 322
    1. PaintDeviceMetric() - método
    2. RenderFlag() - método
    3. acceptDrops() - método
    4. accessibleDescription() - método
    5. accessibleName() - método
    6. actionEvent() - método
    7. actions() - método
    8. activateWindow() - método
    9. addAction() - método
   10. addActions() - método
   11. adjustSize() - método
   12. autoFillBackground() - método
   13. backgroundRole() - método
   14. backingStore() - método
   15. baseSize() - método
   16. blockSignals() - método
   17. changeEvent() - método
   18. childAt() - método
   19. childEvent() - método
   20. children() - método
   ... y 302 más

🔍 ATRIBUTOS ESPECIALES QUE BUSCAMOS:
   ❌ sequence: No disponible
   ✅ window(): <PySide6.QtWidgets.QMainWindow(0x1cc9ba95440, name="NukeMainWindow") at 0x000001D1D50A5EC0>
   ✅ windowTitle(): 360-700
   ✅ objectName(): uk.co.thefoundry.timeline.5
   ❌ player: No disponible
   ❌ currentSequence: No disponible
   ❌ activeSequence: No disponible

🔧 TODOS LOS MÉTODOS DISPONIBLES EN HIERO.UI:
❌ Error explorando hiero.ui: cannot access local variable 'hiero' where it is not associated with a value

🔧 MÉTODOS ESTÁTICOS DE TIMELINE EDITOR:
   Clase: <class 'PySide6.QtWidgets.QWidget'>
   Módulo: PySide6.QtWidgets
   Métodos estáticos encontrados: 311
      • PaintDeviceMetric
      • RenderFlag
      • acceptDrops
      • accessibleDescription
      • accessibleName
      • actionEvent
      • actions
      • activateWindow
      • addAction
      • addActions
      • adjustSize
      • autoFillBackground
      • backgroundRole
      • backingStore
      • baseSize
      • blockSignals
      • changeEvent
      • childAt
      • childEvent
      • children
      • childrenRect
      • childrenRegion
      • clearFocus
      • clearMask
      • close
      • closeEvent
      • colorCount
      • connectNotify
      • contentsMargins
      • contentsRect
      • contextMenuEvent
      • contextMenuPolicy
      • create
      • createWinId
      • cursor
      • customContextMenuRequested
      • customEvent
      • deleteLater
      • depth
      • destroy
      • destroyed
      • devType
      • devicePixelRatio
      • devicePixelRatioF
      • disconnectNotify
      • dragEnterEvent
      • dragLeaveEvent
      • dragMoveEvent
      • dropEvent
      • dumpObjectInfo
      • dumpObjectTree
      • dynamicPropertyNames
      • effectiveWinId
      • emit
      • ensurePolished
      • enterEvent
      • event
      • eventFilter
      • findChild
      • findChildren
      • focusInEvent
      • focusNextChild
      • focusNextPrevChild
      • focusOutEvent
      • focusPolicy
      • focusPreviousChild
      • focusProxy
      • focusWidget
      • font
      • fontInfo
      • fontMetrics
      • foregroundRole
      • frameGeometry
      • frameSize
      • geometry
      • grab
      • grabGesture
      • grabKeyboard
      • grabMouse
      • grabShortcut
      • graphicsEffect
      • graphicsProxyWidget
      • hasFocus
      • hasHeightForWidth
      • hasMouseTracking
      • hasTabletTracking
      • height
      • heightForWidth
      • heightMM
      • hide
      • hideEvent
      • inherits
      • initPainter
      • inputMethodEvent
      • inputMethodHints
      • inputMethodQuery
      • insertAction
      • insertActions
      • installEventFilter
      • internalWinId
      • isActiveWindow
      • isAncestorOf
      • isEnabled
      • isEnabledTo
      • isFullScreen
      • isHidden
      • isLeftToRight
      • isMaximized
      • isMinimized
      • isModal
      • isQuickItemType
      • isRightToLeft
      • isSignalConnected
      • isTopLevel
      • isVisible
      • isVisibleTo
      • isWidgetType
      • isWindow
      • isWindowModified
      • isWindowType
      • keyPressEvent
      • keyReleaseEvent
      • killTimer
      • layout
      • layoutDirection
      • leaveEvent
      • locale
      • logicalDpiX
      • logicalDpiY
      • lower
      • mapFrom
      • mapFromGlobal
      • mapFromParent
      • mapTo
      • mapToGlobal
      • mapToParent
      • mask
      • maximumHeight
      • maximumSize
      • maximumWidth
      • metaObject
      • metric
      • minimumHeight
      • minimumSize
      • minimumSizeHint
      • minimumWidth
      • mouseDoubleClickEvent
      • mouseMoveEvent
      • mousePressEvent
      • mouseReleaseEvent
      • move
      • moveEvent
      • moveToThread
      • nativeEvent
      • nativeParentWidget
      • nextInFocusChain
      • normalGeometry
      • objectName
      • objectNameChanged
      • overrideWindowFlags
      • overrideWindowState
      • paintEngine
      • paintEvent
      • paintingActive
      • palette
      • parent
      • parentWidget
      • physicalDpiX
      • physicalDpiY
      • pos
      • previousInFocusChain
      • property
      • raise_
      • receivers
      • rect
      • redirected
      • releaseKeyboard
      • releaseMouse
      • releaseShortcut
      • removeAction
      • removeEventFilter
      • render
      • repaint
      • resize
      • resizeEvent
      • restoreGeometry
      • saveGeometry
      • screen
      • scroll
      • sender
      • senderSignalIndex
      • setAcceptDrops
      • setAccessibleDescription
      • setAccessibleName
      • setAttribute
      • setAutoFillBackground
      • setBackgroundRole
      • setBaseSize
      • setContentsMargins
      • setContextMenuPolicy
      • setCursor
      • setDisabled
      • setEnabled
      • setFixedHeight
      • setFixedSize
      • setFixedWidth
      • setFocus
      • setFocusPolicy
      • setFocusProxy
      • setFont
      • setForegroundRole
      • setGeometry
      • setGraphicsEffect
      • setHidden
      • setInputMethodHints
      • setLayout
      • setLayoutDirection
      • setLocale
      • setMask
      • setMaximumHeight
      • setMaximumSize
      • setMaximumWidth
      • setMinimumHeight
      • setMinimumSize
      • setMinimumWidth
      • setMouseTracking
      • setObjectName
      • setPalette
      • setParent
      • setProperty
      • setScreen
      • setShortcutAutoRepeat
      • setShortcutEnabled
      • setSizeIncrement
      • setSizePolicy
      • setStatusTip
      • setStyle
      • setStyleSheet
      • setTabletTracking
      • setToolTip
      • setToolTipDuration
      • setUpdatesEnabled
      • setVisible
      • setWhatsThis
      • setWindowFilePath
      • setWindowFlag
      • setWindowFlags
      • setWindowIcon
      • setWindowIconText
      • setWindowModality
      • setWindowModified
      • setWindowOpacity
      • setWindowRole
      • setWindowState
      • setWindowTitle
      • sharedPainter
      • show
      • showEvent
      • showFullScreen
      • showMaximized
      • showMinimized
      • showNormal
      • signalsBlocked
      • size
      • sizeHint
      • sizeIncrement
      • sizePolicy
      • stackUnder
      • startTimer
      • statusTip
      • style
      • styleSheet
      • tabletEvent
      • testAttribute
      • thread
      • timerEvent
      • toolTip
      • toolTipDuration
      • topLevelWidget
      • underMouse
      • ungrabGesture
      • unsetCursor
      • unsetLayoutDirection
      • unsetLocale
      • update
      • updateGeometry
      • updateMicroFocus
      • updatesEnabled
      • visibleRegion
      • whatsThis
      • wheelEvent
      • width
      • widthMM
      • winId
      • window
      • windowFilePath
      • windowFlags
      • windowHandle
      • windowIcon
      • windowIconChanged
      • windowIconText
      • windowIconTextChanged
      • windowModality
      • windowOpacity
      • windowRole
      • windowState
      • windowTitle
      • windowTitleChanged
      • windowType
      • x
      • y

====================================================================================================
🎯 PRUEBA TEORÍA 2 - CREAR TIMELINE PARA SECUENCIA LIBRE
====================================================================================================
💡 Para probar TEORÍA 2, ejecuta en Hiero:
   test_sequence_creation()
====================================================================================================
EXPLORACIÓN: SECUENCIAS DEL PROYECTO Y SUS PANELS ABIERTOS
====================================================================================================

📋 TOTAL DE SECUENCIAS EN PROYECTO: 5
--------------------------------------------------------------------------------
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer uk.co.thefoundry.viewer.contactsheet.1 - windowTitle: 'Contact Sheet' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia
🔍 Viewer  - windowTitle: '' - no se pudo determinar secuencia

🔍 VIEWERS REALMENTE ABIERTOS EN LA UI: 4
  • uk.co.thefoundry.sequenceviewer.3 → Secuencia: 360-700
  • uk.co.thefoundry.sequenceviewer.25 → Secuencia: 710-990
  • uk.co.thefoundry.viewer.contactsheet.1 → Secuencia: Sin secuencia
  • uk.co.thefoundry.sequenceviewer.2 → Secuencia: 010-350

🔍 TIMELINES REALMENTE ABIERTOS EN LA UI: 1
  • uk.co.thefoundry.timeline.5 → Secuencia: 360-700

🔍 VERIFICANDO SECUENCIA: z_EditRef_v1_6_20250725 (ID: 0x1d2451c06c0)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 710-990 (ID: 0x1d2451c0700)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 360-700 (ID: 0x1d2451c1140)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: 010-350 (ID: 0x1d272b0e3c0)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

🔍 VERIFICANDO SECUENCIA: z_EditRef_v.0.2 (ID: 0x1d272b0e480)
  ❌ NO TIENE TIMELINE ABIERTO
  ❌ NO TIENE VIEWER ABIERTO

====================================================================================================
RESUMEN FINAL
====================================================================================================

📊 ESTADÍSTICAS:
   • Total secuencias: 5
   • Secuencias con timeline/viewer: 0
   • Secuencias libres: 5

🟢 SECUENCIAS LIBRES (sin timeline ni viewer - disponibles para crear):
   1. z_EditRef_v1_6_20250725 (ID: 0x1d2451c06c0)
   2. 710-990 (ID: 0x1d2451c0700)
   3. 360-700 (ID: 0x1d2451c1140)
   4. 010-350 (ID: 0x1d272b0e3c0)
   5. z_EditRef_v.0.2 (ID: 0x1d272b0e480)

🔴 SECUENCIAS OCUPADAS (con timeline/viewer abierto):
   ✅ Todas las secuencias están libres
