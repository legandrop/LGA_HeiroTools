# LGA_NKS_Flow_Push

Este sistema consta de dos componentes principales que automatizan la gestión de estados de tareas y versiones en ShotGrid para proyectos de Nuke/Hiero:

* **`LGA_NKS_Flow/LGA_NKS_Flow_Push.py`** - Interfaz principal y lógica de UI (corre en Hiero/Nuke)
* **`LGA_NKS_Flow/LGA_NKS_Flow_Push_connector.py`** - Operaciones de red optimizadas (corre con Python personalizado)

Su propósito principal es mantener sincronizada la información entre ShotGrid y una base de datos SQLite local (`pipesync.db`), optimizando el rendimiento mediante arquitectura distribuida.

## Funcionalidades Principales:

*   **Arquitectura Optimizada:** Separa UI (Hiero/Nuke) de operaciones de red (Python personalizado) para evitar conflictos de dependencias y mejorar rendimiento.
*   **Actualización de Estados en ShotGrid:** Permite cambiar el estado de las tareas de Nuke/Hiero en ShotGrid mediante operaciones optimizadas que minimizan llamadas de red.
*   **Selección de Clips Centralizada:** Usa el módulo utilitario `LGA_NKS_GetClip` (Método 2 híbrido: playhead primero, luego selección como fallback) para obtener clips del track configurado (por defecto `_comp_`). Soporta selecciones múltiples cuando se usa `push_from_selected_clips()`.
*   **Sincronización con Base de Datos Local:** Mantiene una base de datos SQLite local (`pipesync.db`) sincronizada con los cambios realizados en ShotGrid.
*   **Verificación de Versiones del Timeline:** Antes de abrir el diálogo de notas, verifica si la versión actual del clip seleccionado es la más alta disponible en el timeline. Si no lo es, muestra un diálogo de advertencia permitiendo continuar o cancelar la operación.
*   **Gestión de Versiones Asíncrona:** Identifica versiones y realiza verificaciones sin congelar la interfaz de usuario.
*   **Notas para Versiones:** En ciertos estados específicos, abre un diálogo para introducir comentarios que se envían a ShotGrid con adjuntos visuales.
*   **Integración con ReviewPic:** El diálogo incluye thumbnails de imágenes capturadas, adjuntándolas automáticamente a las notas en ShotGrid.
*   **Procesamiento de Múltiples Clips:** La función `push_from_selected_clips()` permite procesar múltiples clips en una sola operación, con limitación de 4 clips con confirmación para evitar operaciones accidentales.

## Búsqueda de Versiones en Flow:

El sistema **NO compara nombres completos de versiones**. Utiliza una estrategia basada en relaciones de ShotGrid:

1. **Extracción del Shot Code:** Del nombre del clip extrae `project_name` y `shot_code`.
2. **Búsqueda del Shot:** Busca el shot usando `shot_code` en el proyecto correspondiente y obtiene el `shot_id`.
3. **Búsqueda de Versiones:** Busca **TODAS las versiones** asociadas a ese `shot_id`, incluyendo EXRs, MOVs renombrados y cualquier otro tipo de versión vinculada al mismo shot.
4. **Filtrado:** Filtra versiones que contengan `_comp_` o `_cmp_` en su código.
5. **Selección de Versión:**
   - **Para comentarios:** Selecciona la versión específica correspondiente al número de versión del clip actual.
   - **Para otras operaciones:** Selecciona la versión numérica más alta entre todas las encontradas.

**Ejemplo:** Si el clip es `LC_1021_050_Beauty_Senora_comp_v013` y en Flow existe un MOV renombrado como `LC_101_WAN_021_050_comp_v013` vinculado al mismo shot, el sistema encontrará y usará la versión correcta aunque los nombres no coincidan completamente.

## Verificación de Versiones del Timeline:

Antes de abrir el diálogo de notas, el sistema verifica automáticamente si la versión actual del clip seleccionado es la más alta disponible en el timeline:

1. **Obtención de Versiones:** Usa la API de Hiero para obtener todas las versiones disponibles del clip seleccionado mediante `binItem.items()`.
2. **Detección de Versión Actual:** Identifica la versión activa usando `activeVersion()` del binItem.
3. **Comparación:** Compara la versión actual con la versión más alta disponible.
4. **Diálogo de Advertencia:** Si la versión actual no es la más alta, muestra un diálogo (`PushVersionDialog`) que:
   - Muestra la versión actual y la versión más alta disponible
   - Lista todas las versiones disponibles en el timeline
   - Permite continuar con el push de la versión actual o cancelar la operación
   - Si el usuario cierra el diálogo sin confirmar, la operación se cancela completamente
5. **Prevención de Errores:** Esta verificación ocurre ANTES del diálogo de notas, evitando que el usuario escriba comentarios para luego descubrir que estaba trabajando con una versión antigua.

## Estados que Solicitan una Nota:

La ventana para introducir una nota se activa cuando el estado de la tarea se cambia a uno de los siguientes:

*   **"Corrections"** (se traduce a `corr` en ShotGrid)
*   **"Corrs_Lega"** (se traduce a `revleg` en ShotGrid)
*   **"Rev_Dir"** (se traduce a `rev_di` en ShotGrid)
*   **"Rev Lega"** (se traduce a `revleg` en ShotGrid)
*   **"Rev Javi"** (se traduce a `revjav` en ShotGrid)
*   **"Rev Hold"** (se traduce a `revhld` en ShotGrid)

## Arquitectura y Rendimiento:

El sistema utiliza una arquitectura distribuida optimizada:

* **Separación de responsabilidades:** UI corre en Hiero/Nuke, operaciones de red en Python personalizado
* **Operaciones asíncronas:** Todas las llamadas a ShotGrid se ejecutan en hilos separados para evitar congelamiento de UI
* **Operación completa optimizada:** Una sola llamada `execute_full_push` reemplaza múltiples operaciones individuales
* **Verificación de versiones asíncrona:** Se realiza en background sin bloquear la interfaz
* **Timeouts inteligentes:** 10 segundos para operaciones normales, 30 segundos para subida de imágenes

## Integración con ReviewPic:

Cuando se abre el diálogo para introducir notas, el script automáticamente:

1. **Busca Imágenes de Review:** Examina la carpeta `ReviewPic_Cache` (ubicada en el mismo directorio que el script) buscando imágenes correspondientes al shot y versión actual usando la función `find_review_images()`.

2. **Muestra Thumbnails:** Si encuentra imágenes, las muestra como thumbnails de 150px de ancho debajo del área de texto de notas, en un área scrolleable implementada en la clase `InputDialog`.

3. **Información de Frame:** Cada thumbnail muestra el número de frame correspondiente alineado a la izquierda debajo de la imagen, extraído mediante `extract_frame_number_from_filename()`. Antes del texto "Frame:" aparece un botón de tachito (×) que permite borrar esa imagen individualmente.

4. **Borrado Individual de Imágenes:** Cada thumbnail incluye un botón de tachito (×) que permite borrar imágenes individuales antes de enviar la nota. Al hacer clic, se muestra un diálogo de confirmación y, si se confirma, la imagen se borra del disco, se remueve de la lista de imágenes a subir, y desaparece inmediatamente del diálogo. Las imágenes borradas individualmente no se adjuntarán a la nota en ShotGrid.

5. **Ajuste Automático de Ventana:** El ancho de la ventana se ajusta automáticamente para acomodar los thumbnails, con un mínimo del tamaño actual y un máximo de 1500px usando `adjust_window_size()`. El tamaño se actualiza dinámicamente cuando se borran imágenes individuales.

6. **Referencia Visual:** Los thumbnails incluyen tooltips que muestran el nombre del archivo al pasar el mouse, proporcionando una referencia visual rápida de las imágenes capturadas durante el proceso de review.

7. **Adjuntar a ShotGrid:** Las imágenes restantes (que no fueron borradas individualmente) se adjuntan automáticamente a la nota en ShotGrid mediante `attach_images_to_note()` usando upload directo a Note con la convención de nombres `annot_version_<version_id>.<frame_number>.jpg` para que aparezcan con números de frame en la interfaz de ShotGrid.

8. **Opción de Limpieza:** Un checkbox "Delete all saved review images from disk" (marcado por defecto) permite al usuario elegir si borrar automáticamente toda la carpeta `ReviewPic_Cache` después de un envío exitoso únicamente.

9. **Organización Automática:** Las imágenes se organizan automáticamente por carpetas que siguen el patrón `{proyecto}_{secuencia}_{shot}_{task}_v{version}`, manteniéndose sincronizadas con el flujo de trabajo de revisión.

### Funciones Clave:

**En `LGA_NKS_Flow/LGA_NKS_Flow_Push.py`:**
- **`push_from_selected_clips()`**: **[NUEVO]** Función principal que usa el método centralizado para obtener clips del track `TRACK_comp_EXR` (Método 2 híbrido). Soporta selecciones múltiples, filtra clips de composición, y maneja el diálogo de notas apropiadamente. Incluye confirmación para más de 4 clips.
- **`Push_Task_Status()`**: Función legacy que procesa un clip individual cuando se proporciona `base_name`. Mantiene compatibilidad con paneles que llaman esta función directamente. Verifica versiones del timeline antes de abrir el diálogo de notas.
- **`get_clip_versions_from_timeline()`**: Obtiene todas las versiones disponibles del clip seleccionado usando la API de Hiero, detecta la versión actual y encuentra la versión más alta.
- **`extract_version_number_from_string()`**: Extrae el número de versión de nombres de archivos usando el patrón `_v\d+`.
- **`PushVersionDialog`**: Diálogo personalizado que muestra advertencia cuando la versión actual no es la más alta, permitiendo continuar o cancelar.
- **`call_flow_connector()`**: Puente que comunica con el conector externo de forma asíncrona
- **`handle_version_check_result()`**: Maneja confirmaciones de versión del usuario para verificaciones asíncronas con Flow
- **`find_review_images()`**: Localiza imágenes en `LGA_NKS_Flow/ReviewPic_Cache/`
- **`delete_single_image()`**: Borra una imagen individual del disco y la remueve de la UI y de la lista de imágenes a subir

**En `LGA_NKS_Flow/LGA_NKS_Flow_Push_connector.py`:**
- **`execute_full_push_operation()`**: Operación completa que actualiza estado, versión y comentarios en una sola llamada
- **`find_specific_version_for_shot()`**: Busca la versión específica correspondiente al número de versión del clip actual para agregar comentarios
- **`find_highest_version_for_shot()`**: Busca la versión más alta disponible para otras operaciones
- **`execute_flow_operation()`**: Dispatcher principal para todas las operaciones de red
- **`attach_images_to_note()`**: Sube imágenes a ShotGrid con números de frame

Esta integración permite a los usuarios revisar visualmente las imágenes capturadas previamente mientras escriben sus notas de revisión, seleccionar qué imágenes adjuntar mediante borrado individual antes del envío, adjuntarlas automáticamente a ShotGrid con información de frame, y opcionalmente limpiar el caché local después del envío exitoso.
