> **Regla de documentacion**: este archivo describe el plan de implementacion de la cola global de transcode. No es un historial de cambios ni reemplaza la especificacion funcional.
> **Regla de mantenimiento**: a medida que avance la implementacion, si aparecen decisiones nuevas, cambios de alcance o comportamientos no previstos, se debe actualizar tambien `LGA_import_shots_transcode_queue.md` para que la documentacion principal siga describiendo el sistema real.

# Plan - Cola global de Transcode Plates

Plan por etapas para implementar y testear el sistema descrito en
[`LGA_import_shots_transcode_queue.md`](LGA_import_shots_transcode_queue.md).

La prioridad es que cada etapa deje una version testeable. No se debe avanzar en UI
secundaria antes de validar que el manager global ejecuta los transcodes correctamente.

---

## Etapa 1 - Manager global minimo con una sola ventana {implementada y testeada en Hiero}

Objetivo: reemplazar la cola local por un manager global, manteniendo el caso de uso actual
con una sola ventana.

```text
{
  crear LGA_import_shots_transcode_queue.py,
  implementar TranscodeQueueManager singleton,
  implementar logging propio debugPy_ImportShotsTranscodeQueue.log,
  respetar docs/Docu_Logging_System.md - Sistema A,
  mantener logger sin salida a consola,
  encolar jobs desde una sola ventana,
  ejecutar un solo job activo por vez,
  generar manifest temporal por job activo,
  reutilizar TranscodeWorker actual,
  actualizar estados de filas: N en fila, Procesando, Listo, Error,
  mantener barra de progreso en la fila activa,
  finalizar cola y re-habilitar botones,
  escribir log detallado para analisis posterior
}
```

Resultado testeable:

```text
{
  abrir una ventana de Import Shot,
  seleccionar varios EXR,
  presionar Start Transcode,
  confirmar que se procesan uno por uno via manager,
  revisar debugPy_ImportShotsTranscodeQueue.log,
  revisar debugPy_ImportShots.log si hace falta
}
```

Resultado validado:

```text
{
  test manual en Hiero con una ventana,
  2 plates encolados,
  el primer plate corrio como job activo,
  el segundo plate mostro 1 en fila,
  ambos terminaron OK,
  log validado en debugPy_ImportShotsTranscodeQueue.log
}
```

No incluido en esta etapa:

```text
{
  multiples ventanas,
  footer global en todas las paginas,
  boton Open Queue,
  ventana de cola,
  cancelacion manual,
  reordenamiento de jobs
}
```

---

## Etapa 2 - Multiples ventanas compartiendo cola {implementada y testeada en Hiero}

Objetivo: permitir que varias ventanas encolen jobs en el mismo manager y que nunca corran
dos transcodes en paralelo dentro de la misma sesion.

```text
{
  no recargar LGA_import_shots_transcode_queue.py si ya hay ventanas Import Shot abiertas,
  mantener recarga de desarrollo del queue solo cuando no hay ventanas abiertas,
  mantener debugPy_ImportShots.log en append cuando ya hay ventanas abiertas,
  prefijar logs del script principal con [SHOT| despues de elegir carpeta,
  loguear apertura de ventanas en debugPy_ImportShotsTranscodeQueue.log,
  loguear cierre de ventanas antes de implementar remocion de jobs,
  registrar ventanas con window_id,
  desregistrar ventanas al cerrarse,
  encolar jobs desde multiples ventanas,
  conservar orden FIFO global,
  recalcular posiciones despues de cada cambio,
  mostrar N en fila entre ventanas,
  mostrar que shot/plate esta convirtiendo aunque sea de otra ventana,
  impedir ejecucion paralela de dos TranscodeWorker desde Import Shot
}
```

Resultado testeable:

```text
{
  abrir dos o tres ventanas de shots distintos,
  iniciar transcode en la primera,
  iniciar transcode en la segunda mientras la primera trabaja,
  confirmar que la segunda queda en fila,
  confirmar que la fila avanza al terminar cada plate
}
```

Resultado validado:

```text
{
  test manual en Hiero con dos ventanas,
  primera ventana encolo 2 jobs,
  segunda ventana encolo 2 jobs mientras la primera seguia activa,
  no hubo workers paralelos,
  la segunda ventana arranco despues de terminar la primera,
  los 4 jobs terminaron OK,
  queue_changed final size=0 active= pending=0,
  log validado en debugPy_ImportShotsTranscodeQueue.log
}
```

---

## Etapa 3 - Cierre de ventanas y limpieza de jobs {implementada y testeada en Hiero}

Objetivo: que cerrar una ventana no deje jobs huerfanos ni rompa updates de UI.

```text
{
  conectar closeEvent/destroyed con el manager,
  remover jobs pendientes de la ventana cerrada,
  recalcular posiciones globales,
  si el job activo pertenece a una ventana cerrada dejarlo terminar,
  no arrancar mas jobs pendientes de esa ventana,
  proteger updates contra widgets destruidos,
  registrar todo en el log del manager
}
```

Resultado testeable:

```text
{
  abrir tres ventanas,
  encolar jobs en todas,
  cerrar la segunda antes de que empiece,
  confirmar que la tercera sube en la fila,
  cerrar una ventana con job activo,
  confirmar que ese job termina y no siguen sus pendientes
}
```

Resultado validado:

```text
{
  test manual en Hiero con tres ventanas,
  ventana intermedia cerrada mientras tenia jobs pendientes,
  sus jobs pendientes fueron removidos de la cola,
  la ventana siguiente subio de posicion,
  el manager no arranco jobs pendientes de la ventana cerrada,
  log validado en debugPy_ImportShotsTranscodeQueue.log
}
```

---

## Etapa 4 - Estado global visible en todas las paginas {implementada y testeada en Hiero}

Objetivo: agregar una franja de estado global consistente en las paginas importantes del
dialogo.

```text
{
  agregar label global alineado a la izquierda en la fila inferior,
  mantener botones principales alineados a la derecha,
  cubrir PAGE_MEDIA,
  cubrir PAGE_RENAME,
  cubrir PAGE_CONVERT,
  cubrir PAGE_IMPORT,
  conectar el texto a senales del manager,
  mostrar idle/running/queued con texto claro,
  convertir el shot activo en boton plano con SHOTNAME_COLOR,
  al clickear el shot activo traer al frente su ventana de Import Shot
}
```

Resultado testeable:

```text
{
  navegar entre paginas mientras hay transcode activo,
  confirmar que todas muestran el mismo estado global,
  confirmar que no se rompe el layout de botones
}
```

---

## Etapa 4.5 - Guardas de filesystem para transcode {implementada y testeada en Hiero}

Objetivo: evitar que un bug de overwrite, restore o delete deje un plate sin EXR fuente
recuperable.

```text
{
  implementar preflight por job con conteos de EXR en item_path y Originals/<plate>,
  abortar antes de tocar archivos si no existe ninguna fuente EXR,
  impedir borrar la ultima copia conocida de un plate,
  restaurar Originals/<plate> a item_path antes de re-transcode y verificar conteo,
  validar rutas resueltas antes de cualquier delete/rmtree,
  borrar Originals/<plate> al terminar solo si el output final tiene EXR,
  registrar snapshots before/after en el log del worker y/o manager,
  documentar los resultados en LGA_import_shots_transcode.md
}
```

Resultado testeable:

```text
{
  correr re-transcode con Originals existente,
  correr overwrite con item_path convertido y Originals fuente,
  probar caso sin EXR en item_path ni Originals y confirmar que aborta sin borrar nada,
  probar Borrar /Originals al terminar y confirmar que solo borra despues de output OK,
  revisar logs con conteos y paths absolutos
}
```

---

## Etapa 5 - Boton Open Queue y ventana de cola {implementada, pendiente de test en Hiero}

Objetivo: dar visibilidad completa del orden global de jobs.

```text
{
  agregar boton pequeno Open Queue junto al estado global,
  crear LGA_import_shots_transcode_queue_ui.py,
  implementar recarga de desarrollo del modulo UI solo cuando no haya ventanas vivas,
  exponer show_queue_window(manager, parent=None, focus_window_callback=None),
  crear LGA_import_shots_transcode_queue_ui.md,
  usar estilo de botones pequenos existentes,
  respetar estetica visual de Import Shot,
  crear ventana flotante no bloqueante,
  traer al frente si ya esta abierta,
  mostrar tabla unica en orden global,
  columnas Shot, Plate, Duracion, Estado,
  mostrar Shot como boton plano clickeable,
  alternar color de Shot entre SHOTNAME_COLOR y SHOTNAME_COLOR_ALT cuando cambia el shot,
  click en Shot trae al frente la ventana existente,
  copiar/reutilizar la implementacion del boton de shot activo del estado global,
  si la ventana del shot ya no existe, registrar en log y no hacer nada en primera version,
  actualizar tabla por senales del manager,
  usar barra de progreso identica a la tabla de transcode para el job activo,
  mostrar N en fila en Estado para jobs pendientes,
  conservar historial visual de jobs terminados mientras la ventana este abierta,
  agregar boton Show All Import Windows,
  agregar boton Clear Completed,
  Clear Completed borra solo filas completadas del historial visual,
  agregar checkbox Keep this window on top alineado a la derecha de la fila inferior,
  persistir Keep this window on top en ImportShots.ini,
  implementar Keep this window on top con QtCore.Qt.WindowStaysOnTopHint,
  mantener la ventana no modal para no bloquear Hiero,
  mantener primera version solo lectura
}
```

Columnas iniciales:

```text
{
  Shot,
  Plate,
  Duracion,
  Estado
}
```

No incluido en esta etapa:

```text
{
  reordenar jobs,
  cancelar jobs desde la ventana,
  pausar cola
}
```

---

## Etapa 6 - Pulido, errores y documentacion final {pendiente}

Objetivo: cerrar casos borde y actualizar documentacion segun lo realmente implementado.

```text
{
  revisar errores por job sin bloquear la cola,
  revisar overwrite conflicts,
  validar re-transcode con _input/Originals/<plate>/ existente,
  revisar logs del manager y de ImportShots,
  limpiar estados visuales inconsistentes,
  asegurar que no quedan timers activos al terminar,
  asegurar que no hay updates a ventanas destruidas,
  actualizar LGA_import_shots_transcode_queue.md,
  actualizar LGA_import_shots.md,
  marcar secciones implementadas/testeadas donde corresponda
}
```

Resultado testeable:

```text
{
  correr pruebas manuales con una ventana,
  correr pruebas manuales con multiples ventanas,
  correr prueba de cierre de ventanas,
  revisar logs,
  documentar ajustes finales
}
```
