> **Regla de documentacion**: este archivo describe el plan vigente del tema. No es un changelog ni una bitacora temporal.
> **Regla de documentacion**: este archivo debe mantenerse alineado con el estado real del codigo y con las decisiones arquitectonicas ya tomadas.

# LGA NKS Playlist Panel Plan

## Objetivo general

Crear un panel de Hiero/Nuke Studio para trabajar reviews de playlists vendor desde el timeline, con una experiencia parecida al `Flow Panel`, pero usando como fuente principal la base `pipesync_playlists.db`.

El panel debe permitir:

- pull visual desde la DB local de playlists;
- consulta de info del shot;
- creacion de imagenes de review;
- envio de notas a la playlist a la que pertenece la version actual;
- aprobacion y desaprobacion de la version desde el timeline.

## Relacion con Flow Panel y PipeSync

- `PipeSync` sigue siendo la fuente de sincronizacion local.
- `pipesync.db` se usara solo para resolver la info del shot en el boton `Shot Info`.
- `pipesync_playlists.db` sera la fuente para:
  - detectar playlists;
  - obtener mensajes/notas/replies/attachments;
  - resolver aprobacion de version;
  - identificar la playlist elegida por el usuario cuando una version pertenezca a varias playlists.
- El `Playlist Panel` sera equivalente funcional al `Flow Panel`, pero orientado al dominio playlist/vendor en lugar del dominio task/shot del flujo normal.

## Reglas ya definidas

### Regla 1: el panel solo existe para usuarios Master

- El script del panel debe chequear al inicio si el usuario actual tiene permiso `Master` en PipeSync.
- Si no tiene permiso `Master`, el panel no debe cargarse.
- El script termina en ese punto, sin registrar el panel ni exponer UI parcial.

### Regla 2: el panel solo se usara para vendor playlists

- Por ahora el `Playlist Panel` se usara solo para playlists vendor.
- Esto debe quedar explicitado en el codigo y en la documentacion.
- Mas adelante se podra evaluar si conviene abrirlo tambien a playlists no vendor.

### Regla 3: deteccion de timeline vendor

- La deteccion debe seguir el mismo criterio funcional ya adoptado en PipeSync.
- Se compara `shot_code` contra el `project_name` del timeline.
- Si no coinciden, se considera que estamos en un timeline vendor.
- Esta logica debe usarse para habilitar o validar el flujo del panel.

### Regla 4: separacion de bases

- `pipesync.db` solo se usa para `Shot Info`.
- `pipesync_playlists.db` se usa para todo el resto del panel.
- No mezclar logica runtime de playlist con joins improvisados a `pipesync.db`, salvo la excepcion explicita del boton `Shot Info`.

### Regla 5: si una version pertenece a varias playlists, el usuario elige

- Cuando una version este presente en mas de una playlist, el panel debe pedir al usuario que elija.
- La eleccion debe mostrarse con:
  - nombre de playlist;
  - fecha de creacion de la playlist.
- La eleccion vale solo para la accion actual.
- No debe persistirse como contexto global del clip.

## Confirmaciones sobre el Flow Panel actual

Queda confirmado que el `Flow Panel` ya maneja comentarios y attachments de forma no lineal en `Shot Info`.

En `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Flow_Panel_py\LGA_NKS_Flow_Shot_info.py`:

- se consultan notas desde `version_notes`;
- se cargan `local_attachment_paths`;
- se renderizan thumbnails por comentario;
- no se filtran las notas con `from_playlist`, por lo que tambien se muestran comentarios provenientes de playlists cuando existen en `pipesync.db`.

Esto sirve como referencia UX para el nuevo panel, pero no implica reutilizar exactamente la misma fuente de datos.

## Fuente de datos prevista

### Desde `pipesync.db`

Solo para `Shot Info`:

- datos generales del shot;
- informacion historica ya visible hoy en el `Flow Panel`.

### Desde `pipesync_playlists.db`

Para el resto del panel:

- playlists asociadas a la version;
- notas de playlist;
- replies;
- attachments;
- estado de aprobacion;
- metadata de version dentro de playlist.

## Botones previstos del panel

La lista de botones debe respetar, en orden y color, una logica lo mas parecida posible al `Flow Panel`.

Orden actual acordado:

1. `Playlist Pull`
2. `Shot Info`
3. `Review Pic`
4. `Corrections`
5. `Send Note`
6. `Rev Dir`
7. `Approve`
8. `Show Playlist`

### 1. Playlist Pull

Funcion esperada:

- leer desde `pipesync_playlists.db` la informacion de la version actual;
- determinar si la version pertenece a una o varias playlists;
- si hay mas de una, pedir eleccion al usuario;
- reflejar en el timeline el estado correspondiente del contexto playlist elegido.

Decision tomada:

- cuando el pull detecta cambios sobre clips, esos clips se pintan siempre con el color `Rev Lega`.

Pendiente:

- definir todas las fuentes que participa del `pull` cuando exista informacion cruzada entre `pipesync.db` y `pipesync_playlists.db`;
- definir si el pull afecta solo al clip actual o si tambien podra operar sobre multiples clips o timeline completo.

### 2. Shot Info

Funcion esperada:

- usar la misma fuente que el `Flow Panel` actual para mostrar informacion del shot;
- esta es la unica parte del panel que consultara `pipesync.db`.

Pendiente:

- definir si la ventana sera reutilizada tal cual o si habra una variante adaptada al panel playlist.

### 3. Review Pic

Funcion esperada:

- crear snapshots del viewer con numero de frame;
- dejarlos listos para adjuntarse luego a una nota de playlist.

Decision tomada:

- el `Playlist Panel` tendra una cache de imagenes separada del `Flow Panel`;
- el funcionamiento sera el mismo que en `Flow Panel`.

### 4. Send Note

Funcion esperada:

- abrir un dialogo para escribir una nota;
- adjuntar las review pics guardadas;
- enviar la nota a la playlist elegida a la que pertenece la version actual.

Flujo acordado:

- antes de abrir el editor de nota, el boton debe analizar si ya existen notas para esa version dentro de la playlist elegida;
- si existen, debe abrirse primero una ventana visualmente equivalente a `Shot Info`;
- esa ventana debe permitir elegir entre:
  - responder a una nota existente;
  - crear una nota nueva al final del thread, sin ser reply.
- luego de esa eleccion, se abre la ventana de notas identica a la del `Flow Panel`.
- el sistema de imagenes debe ser igual al de `Flow Panel`, pero usando cache separada del `Playlist Panel`.

Pendiente:

- validar contra Flow real el endpoint/campo exacto para crear una nota nueva en contexto playlist;
- validar contra Flow real el endpoint/campo exacto para responder a una nota existente;
- definir exactamente como se selecciona una nota previa cuando hay multiples notas y replies;
- definir si el usuario puede borrar individualmente imagenes antes del envio, igual que en `Flow Push`.

### 5. Corrections

Funcion esperada:

- cambiar el color del clip al mismo azul que `Corrections` en el `Flow Panel`;
- escribir estado en DB local;
- escribir estado en Flow;
- si el plano estaba aprobado, al ejecutar `Corrections` debe salir del estado aprobado.

Decision tomada:

- no existira un boton `Unapprove` separado;
- `Corrections` asume tambien el comportamiento operativo de sacar al plano de aprobado cuando corresponda.

Decision pendiente importante:

- definir si `Corrections` debe escribirse:
  - solo en `pipesync_playlists.db`;
  - en `pipesync_playlists.db` y tambien en `pipesync.db`;
  - y como se prioriza cada fuente luego en los pulls.

### 6. Rev Dir

Funcion esperada:

- por ahora no hace nada.

Decision tomada:

- el boton existe desde el arranque para mantener la estructura del panel alineada al `Flow Panel`;
- la logica compleja se agregara mas adelante.

### 7. Approve

Funcion esperada:

- aprobar la version;
- cambiar el color del clip a verde.

Decision tomada:

- `Approve` no requiere confirmacion previa.

Pendiente:

- validar contra Flow real cual es la operacion remota exacta de aprobacion;
- definir si la aprobacion se hace sobre la version global o sobre el contexto de version dentro de playlist.

### 8. Show Playlist

Funcion esperada:

- si la version pertenece a mas de una playlist, pedir al usuario cual abrir;
- abrir la playlist elegida en el browser.

Pendiente:

- validar la URL exacta a construir/abrir;
- definir si la seleccion de playlist usa exactamente el mismo selector que `Send Note` y `Playlist Pull`.

### Boton descartado: Unapprove

- `Unapprove` no existira como boton separado.
- Su efecto operativo queda absorbido por `Corrections` cuando el plano este aprobado.

## Diferencias importantes respecto del Flow Panel

### 1. Dominio playlist en vez de task

El `Flow Panel` trabaja principalmente contra task/version del flujo normal.

El `Playlist Panel` debe trabajar contra:

- `version_sg_id`;
- una playlist elegida;
- el contexto de review de esa version dentro de esa playlist.

Eso obliga a resolver el contexto antes de permitir acciones de escritura.

### 2. Una version puede estar en varias playlists

Esto no suele ser un problema equivalente en el `Flow Panel`.

En el `Playlist Panel` si una misma version aparece en varias playlists:

- el usuario debe elegir explicitamente;
- todas las acciones posteriores deben quedar atadas a esa eleccion;
- hay que definir si la eleccion vale solo para esa accion o para toda la sesion del panel mientras el clip siga activo.

### 3. Vendor-only

El panel arranca con un scope mas acotado:

- solo para usuarios `Master`;
- solo para playlists vendor;
- solo en timelines detectados como vendor.

### 4. Aprobacion con significado funcional propio

En este panel la aprobacion no es solo "poner color verde".

Debe existir una correspondencia entre:

- estado real en Flow;
- estado reflejado en `pipesync_playlists.db`;
- color del clip en Hiero.

### 5. Validacion previa de timeline vendor por accion

- Antes de ejecutar cualquier accion, se correra un script Python que valide si el timeline actual es vendor.
- Si no lo es:
  - se muestra un mensaje;
  - la accion no se ejecuta.
- Esta validacion es independiente del chequeo de permiso `Master` al cargar el panel.
- La implementacion puede vivir como una funcion corta dentro del mismo Python del panel, no hace falta que sea un script externo.

### 6. Probes obligatorios antes de implementar escrituras reales

- Antes de implementar de forma productiva cualquier escritura sobre Flow para playlists, se deben hacer pruebas reales con `.py` temporales.
- El flujo obligatorio de validacion sera:
  - escribir;
  - leer para comprobar;
  - borrar lo escrito de prueba.
- Esto aplica a:
  - crear notas nuevas;
  - responder notas;
  - adjuntar imagenes;
  - subir imagenes con numero de frame;
  - aprobar;
  - sacar de aprobado si corresponde.
- Estos probes temporales deben hacerse antes de tocar el codigo definitivo del panel.

## Riesgos ya detectados

### Riesgo 1: escribir en la playlist equivocada

Si una version pertenece a varias playlists y no se fija bien el contexto, una nota o una aprobacion pueden terminar en la playlist incorrecta.

### Riesgo 2: asumir una API de aprobacion que no este validada

La DB ya guarda `client_approved_at` y `client_approved_by`, pero aun no esta validado el mecanismo exacto para escribir ese estado desde el panel.

### Riesgo 3: mezclar demasiado con la logica del Flow Panel

Aunque la UX sea parecida, el dominio es distinto. Reutilizar componentes visuales es razonable; reutilizar sin revisar la logica de push puede generar errores conceptuales.

### Riesgo 4: depender de datos que no esten en `pipesync_playlists.db`

Si el panel necesita informacion adicional para operar, lo correcto sera extender:

- `create_database_playlists.py`;
- `get_Flow_playlists.py`;
- la documentacion de schema.

No resolverlo con dependencias ocultas a otras fuentes en runtime.

## Puntos pendientes de definir

### Contexto y seleccion

- que pasa si no hay playlists asociadas a la version.

### Pull visual

- si el pull debe leer aprobacion, correcciones, descripcion de version, o una combinacion de esos estados.
- como se resuelven conflictos si `pipesync.db` y `pipesync_playlists.db` contienen informacion util pero no identica.

### Notas

- si se permiten multiples imagenes como hoy.
- si al enviar nota se limpian automaticamente las imagenes cacheadas.
- si la respuesta puede apuntar solo a una nota principal o tambien a un reply existente.
- como se numeran visualmente las notas y replies para la seleccion.

### Aprobacion

- si `Approve` puede convivir con una nota opcional.
- como se representa en DB el hecho de que `Corrections` saco al plano de aprobado.

### UX y validaciones

- el mensaje cuando el timeline actual no es vendor debe incluir contexto.
- que mensaje se muestra si el usuario es `Master` pero la version no pertenece a ninguna playlist vendor.
- si el panel debe ocultar o deshabilitar botones segun contexto.

### Persistencia y refresh

- aunque por ahora no se implementara, queda pendiente definir como refrescar `pipesync_playlists.db` o la UI luego de escribir notas/aprobaciones para no quedar con estado stale.

### Shot Info del Playlist Panel

- la ventana tendra estetica y UI identicas a la existente en `Flow Panel`;
- el bloque superior debe mostrar:
  - `Descripcion Tarea: ...` leida desde `pipesync.db`;
  - `Descripcion Version: ...` leida desde `pipesync_playlists.db`.
- debajo de eso:
  - notas;
  - replies;
  - attachments;
  - todo leido desde `pipesync_playlists.db`.
- visualmente debe ser identica a la ventana del `Flow Panel`, salvo por esa adaptacion del bloque de descripcion.

Pendiente:

- definir si en esa vista se mostraran todas las playlists asociadas a la version o solo la playlist elegida para la accion actual.

### Seleccion de notas/replies para Send Note

- la ventana previa a `Send Note` debe mostrar todo:
  - descripcion;
  - notas;
  - replies;
  - attachments.
- se numeraran las notas y replies para que el usuario pueda elegir facilmente el target.
- abajo habra una opcion para:
  - `New Note`;
  - `Reply to #N`.
- sigue pendiente definir si `#N` puede ser tanto una nota como un reply, o solo una nota principal.

## Referencias tecnicas

- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Flow_Panel.py`
- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Flow_Panel_py\LGA_NKS_Flow_Shot_info.py`
- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Flow_Panel_py\LGA_NKS_Flow_Push.py`
- `C:\Portable\LGA_PipeSync_2\Docs\Doc_DB_Playlist.md`
- `C:\Portable\LGA_PipeSync_2\Docs\Doc_Tab_Playlist.md`
- `C:\Portable\LGA_PipeSync_2\Docs\Doc_Tab_Playlist_Plan.md`
- `C:\Portable\LGA_PipeSync_2\Docs\Doc_User_Permisos.md`
- `C:\Portable\LGA_PipeSync_2\Docs\Doc_Flow_Sync.md`
