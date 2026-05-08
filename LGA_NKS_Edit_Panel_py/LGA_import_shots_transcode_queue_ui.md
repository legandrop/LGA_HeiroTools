> **Regla de documentacion**: este archivo describe la UI prevista para `LGA_import_shots_transcode_queue_ui.py`. No es un historial de cambios.
> **Estado general**: pendiente de implementacion y test en Hiero.

# UI - Open Queue

Ventana flotante no modal para visualizar la cola global de transcode de `Import Shot`.

Modulo previsto:

```text
LGA_NKS_Edit_Panel_py/LGA_import_shots_transcode_queue_ui.py
```

Clase principal prevista:

```python
TranscodeQueueWindow
```

Funcion publica prevista:

```python
show_queue_window(manager, parent=None, focus_window_callback=None)
```

`Open Queue` en `LGA_import_shots.py` debe llamar a esta funcion. La UI recibe el manager
global existente; no crea otro manager ni decide el orden de la cola.

---

## Proposito

Mostrar al usuario que conversion esta corriendo ahora, que plates siguen en fila y que
jobs terminaron mientras la ventana estuvo abierta.

La ventana debe ser solo lectura en la primera version:

- No reordenar jobs.
- No cancelar jobs.
- No pausar la cola.
- No tocar archivos.
- No ejecutar transcodes.

---

## Layout

Estructura general:

```text
Open Queue
────────────────────────────────────────────────────────
Shot          Plate                  Duracion      Estado
TEST_014_010  TEST_014_010_aPlate... 184f - 7.7s  [barra progreso]
TEST_014_010  TEST_014_010_bPlate... 184f - 7.7s  1 en fila
TEST_014_020  TEST_014_020_aPlate... 78f - 3.3s   2 en fila
TEST_014_020  TEST_014_020_bPlate... 484f - 20.2s Terminado
────────────────────────────────────────────────────────
[Show Windows] [Clear Completed]
☐ Keep on top
```

La tabla debe usar una estetica similar a la tabla de la seccion Convert:

- Fondo oscuro `#272727`.
- Headers sobrios.
- Sin grid visible.
- Bordes y separadores compatibles con `Import Shot`.
- Tipografia y tamanos similares a la tabla de transcode.

---

## Columnas

| Columna | Contenido |
|---------|-----------|
| Shot | Nombre del shot como boton plano clickeable |
| Plate | Nombre de secuencia |
| Duracion | Frames y segundos, por ejemplo `484f - 20.2s` |
| Estado | Barra de progreso, `N en fila`, `Terminado`, `Error` o `Cancelado` |

No se agrega columna `Pos`: la posicion global se comunica dentro de `Estado` con
`N en fila`. El job activo se identifica por la barra de progreso.

---

## Columna Shot

El texto de `Shot` funciona como boton plano:

- Sin fondo.
- Sin borde.
- Color principal `SHOTNAME_COLOR`.
- Hover con mas brillo, sin subrayado.
- Click trae al frente la ventana de `Import Shot` si todavia existe.
- Si la ventana fue cerrada, no hace nada visible y registra el evento en log.

Se agrega una segunda constante para esta UI:

```python
SHOTNAME_COLOR_ALT = "..."
```

La tabla alterna entre `SHOTNAME_COLOR` y `SHOTNAME_COLOR_ALT` cuando cambia el shot en la
lista ordenada global:

```text
TEST_014_010  SHOTNAME_COLOR
TEST_014_010  SHOTNAME_COLOR
TEST_014_020  SHOTNAME_COLOR_ALT
TEST_014_020  SHOTNAME_COLOR_ALT
TEST_014_030  SHOTNAME_COLOR
```

La alternancia es por bloque de shot consecutivo, no por fila.

---

## Columna Plate

Muestra el nombre de la secuencia usando el mismo criterio visual que la columna `Nombre`
de la tabla Convert:

- Si el plate comienza con `shot_name`, ese prefijo puede colorearse con el color del shot
  usado en la fila.
- El resto del nombre mantiene el color base `#cccccc`.

---

## Columna Duracion

Formato:

```text
484f - 20.2s
```

Debe usar el mismo color de frames/segundos que en la tabla Convert.

La duracion se calcula con:

- `frame_count` del job si existe.
- FPS del item si existe.
- Si no hay FPS confiable, mostrar solo frames.

---

## Columna Estado

Estados previstos:

| Estado logico | UI |
|---------------|----|
| running / starting | Barra de progreso identica a la tabla Convert |
| queued | `N en fila`, mismo estilo que la tabla Convert |
| done | `Terminado`, verde como estado listo |
| error | `Error`, rojo |
| cancelled | `Cancelado`, rojo/gris segun convenga visualmente |

La barra de progreso debe reutilizar la logica visual de la tabla Convert todo lo posible.

---

## Historial Visual

El manager global provee activo y pendientes. Para mostrar `Terminado`, `Error` y
`Cancelado`, la primera version puede mantener un historial visual dentro de la ventana UI.

Reglas:

- Los jobs activos y pendientes siempre vienen del snapshot del manager.
- Los completados se agregan al historial de la UI cuando llegan senales del manager.
- `Clear Completed` borra solo ese historial visual.
- `Clear Completed` no modifica el manager ni la cola real.

---

## Botones Inferiores

```text
[Show Windows] [Clear Completed]
☐ Keep on top
```

`Show Windows`:

- Reutiliza la logica ya implementada en `ImportShotDialog`.
- Trae al frente todas las ventanas `Import Shot` abiertas.

`Clear Completed`:

- Borra filas con estado `Terminado`, `Error` o `Cancelado`.
- No borra jobs activos ni pendientes.

`Keep on top`:

- Persistente entre sesiones.
- Usa `QtCore.Qt.WindowStaysOnTopHint`.
- No debe volver modal la ventana.
- Texto visible: `Keep on top`.

Persistencia propuesta en `ImportShots.ini`:

```ini
[TranscodeQueueWindow]
keep_on_top = true
```

---

## Recarga de Desarrollo

`LGA_import_shots.py` puede recargar este modulo durante desarrollo solo si no hay ventanas
vivas:

- No hay ventanas `Import Shot` visibles.
- No hay ventana `Open Queue` visible.

Si alguna existe, debe reutilizar el modulo ya cargado para evitar widgets creados por una
clase vieja, senales duplicadas o una ventana desconectada del manager actual.

---

## Referencias Tecnicas

| Archivo | Funciones / clases clave |
|---------|--------------------------|
| `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots.py` | `_make_footer_pair()`, `_focus_import_shot_window()`, `_show_import_shot_windows()`, boton `Open Queue` |
| `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots_transcode_queue.py` | `TranscodeQueueManager`, `snapshot()`, `queue_changed`, `sequence_started`, `sequence_done`, `job_cancelled` |
| `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots_transcode_queue.md` | Especificacion funcional de la cola global |
| `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Edit_Panel_py\LGA_import_shots_transcode_queue_PLAN.md` | Plan de implementacion por etapas |
