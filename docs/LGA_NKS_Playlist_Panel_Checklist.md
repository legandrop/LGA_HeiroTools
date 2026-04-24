> **Regla de documentacion**: este archivo es un checklist vivo de implementacion. No describe intenciones generales; describe entregables concretos y su estado.
> **Regla de documentacion**: cada item completado debe reflejar codigo real existente y probado. Si algo cambia, este checklist debe actualizarse.

# LGA NKS Playlist Panel Checklist

## Etapa 1 - Esqueleto y permisos

- [x] Crear el documento de checklist de implementacion.
- [x] Crear la subcarpeta `LGA_NKS_Playlist_Panel_py`.
- [x] Crear el archivo principal `LGA_NKS_Playlist_Panel.py`.
- [x] Mantener la convencion de encabezado con nombre, version y notas de version.
- [x] Implementar una utilidad de deteccion de `Master` basada en:
  - `config.secure` via `SecureConfig_Reader.py`
  - roles declarados en `SpecialUsers.cpp`
- [x] Probar con un `.py` temporario que el usuario actual se detecta correctamente como `Master`.
- [x] Borrar el `.py` temporario luego de la prueba.
- [x] Hacer que el panel no se cargue si el usuario actual no es `Master`.
- [x] Crear la UI base del panel con los botones en el orden acordado.
- [x] Respetar colores y look general alineados al `Flow Panel`.
- [x] Dejar botones con comportamiento placeholder por ahora.
- [x] Dejar `Rev Dir` mostrando mensaje `todavia no implementado`.

## Etapa 2 - Vendor check por accion

- [ ] Implementar la funcion corta de validacion de timeline vendor dentro del panel.
- [ ] Hacer que todas las acciones pasen primero por ese chequeo.
- [ ] Mostrar mensaje con contexto si el timeline actual no es vendor.

## Etapa 3 - Playlist Pull

- [ ] Implementar seleccion de clips/timeline igual que `Flow Pull`.
- [ ] Resolver estado base desde `pipesync.db`.
- [ ] Calcular `ultima_actividad_playlist`.
- [ ] Definir y persistir el modelo de estado local en `pipesync_playlists.db`.
- [ ] Aplicar la regla final de colores:
  - `Corrections`
  - `Rev Lega`
  - `Approved`

## Etapa 4 - Shot Info

- [ ] Reutilizar la UI del `Shot Info` del `Flow Panel`.
- [ ] Mostrar `Descripcion Tarea` desde `pipesync.db`.
- [ ] Mostrar `Descripcion Version` desde `pipesync_playlists.db`.
- [ ] Mostrar notas, replies y attachments desde `pipesync_playlists.db`.
- [ ] Mostrar multiples apariciones de la misma version si pertenece a playlists distintas.

## Etapa 5 - Review Pic y Send Note

- [ ] Crear cache propia de imagenes para el `Playlist Panel`.
- [ ] Reutilizar la logica funcional de `Review Pic`.
- [ ] Implementar la ventana previa de seleccion entre `New Note` y `Reply to #N`.
- [ ] Numerar notas y replies para seleccion visual.
- [ ] Reutilizar el dialogo de notas del `Flow Panel`.
- [ ] Reutilizar el checkbox para borrar imagenes cacheadas tras envio exitoso.

## Etapa 6 - Escrituras reales en Flow

- [ ] Hacer probes temporales para crear nota nueva.
- [ ] Hacer probes temporales para responder una nota.
- [ ] Hacer probes temporales para adjuntar imagenes.
- [ ] Validar conservacion de frame number.
- [ ] Leer lo escrito para verificarlo.
- [ ] Borrar lo escrito de prueba.
- [ ] Recién despues implementar codigo productivo.

## Etapa 7 - Corrections y Approve

- [ ] Implementar `Corrections` escribiendo en DB y en Flow.
- [ ] Hacer que `Corrections` saque de aprobado si corresponde.
- [ ] Guardar timestamp local del cambio de estado en playlist.
- [ ] Implementar `Approve` escribiendo en DB y en Flow.
- [ ] Reflejar el estado en task comp y en playlist.

## Etapa 8 - Show Playlist

- [ ] Investigar la URL correcta de apertura de playlist en browser.
- [ ] Implementar apertura directa si hay una sola playlist.
- [ ] Implementar selector si hay varias playlists.

## Etapa 9 - Refresh y pulido

- [ ] Analizar y copiar el flujo de refresh post escritura del `Flow Panel`.
- [ ] Revisar formato amigable de fechas/horas usando como referencia `Playlist Tab` de PipeSync.
- [ ] Verificar que el checklist y el plan sigan alineados.
