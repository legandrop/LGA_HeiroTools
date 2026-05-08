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

## Etapa 3 - Cierre de ventanas y limpieza de jobs {pendiente}

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

---

## Etapa 4 - Estado global visible en todas las paginas {pendiente}

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
  mostrar idle/running/queued con texto claro
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

## Etapa 5 - Boton Open Queue y ventana de cola {pendiente}

Objetivo: dar visibilidad completa del orden global de jobs.

```text
{
  agregar boton pequeno Open Queue junto al estado global,
  usar estilo de botones pequenos existentes,
  crear ventana flotante no bloqueante,
  traer al frente si ya esta abierta,
  mostrar tabla de jobs,
  actualizar tabla por senales del manager,
  mantener primera version solo lectura
}
```

Columnas iniciales:

```text
{
  Pos,
  Shot,
  Plate,
  Estado,
  Frames,
  Ventana
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
