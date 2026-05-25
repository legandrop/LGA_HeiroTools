> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA_Contact_Sheet_OpenInNukeX

## Objetivo

`LGA_Contact_Sheet_OpenInNukeX.py` envia los clips seleccionados del timeline de Hiero/Nuke Studio al NukeX abierto, usando el servidor TCP existente de `LGA_OpenInNukeX`.

El comportamiento actual no cierra el proyecto abierto en NukeX y no crea todavia una plantilla completa de contact sheet. Por ahora replica el flujo manual de copiar clips seleccionados en Hiero y pegarlos en NukeX, lo que permite que Nuke genere los `Read` con la informacion que ya conserva ese paste: ruta, trims, rango y datos asociados al clip.

## Flujo actual

1. El boton `Contact Sheet` del Review Panel ejecuta `LGA_Contact_Sheet_OpenInNukeX.py`.
2. El script valida que exista una secuencia activa.
3. Obtiene la seleccion explicita del timeline con `hiero.ui.getTimelineEditor(seq).selection()`.
4. Ignora items de efecto (`hiero.core.EffectTrackItem`).
5. Dispara la accion registrada de Hiero `foundry.application.copy`.
6. Verifica que el servidor de `LGA_OpenInNukeX` responda con `ping`/`pong` en `localhost:54325`.
7. Envia el comando TCP `paste_clipboard`.
8. NukeX ejecuta `nuke.nodePaste("%clipboard%")` en el proyecto actualmente abierto.

## Metodo de seleccion

Este script usa seleccion explicita (`te.selection()`), no playhead.

La razon es que `Contact Sheet` es una operacion batch sobre varios clips elegidos por el usuario. La posicion del playhead no debe cambiar el conjunto de clips enviados a NukeX.

## Protocolo con OpenInNukeX

El servidor de `LGA_OpenInNukeX` mantiene el comando existente:

- `run_script||<path>`: cierra el proyecto actual y abre el `.nk` indicado.

Y suma el comando:

- `paste_clipboard`: pega el contenido actual del clipboard en NukeX sin llamar a `nuke.scriptClose()` ni a `nuke.scriptOpen()`.

El comando `paste_clipboard` debe ejecutarse con NukeX ya abierto y con el servidor de `OpenInNukeX` activo.

## Hallazgos

- El paste manual desde Hiero a NukeX ya genera `Read` nodes con caracteristicas del clip de Hiero. Por eso se aprovecha el clipboard en lugar de reconstruir manualmente los `Read`.
- `OpenInNukeX` originalmente solo aceptaba `ping` y `run_script||<path>`. Se agrego `paste_clipboard` para cubrir este caso sin cerrar el proyecto abierto.
- La automatizacion depende de que la accion registrada `foundry.application.copy` copie correctamente la seleccion activa de Hiero al clipboard.

## Referencias tecnicas

- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Review_Panel.py`
  - `ReviewPanel.buttons`: define el boton `Contact Sheet`.
  - `ReviewPanel.execute_ContactSheet()`: ejecuta el script externo.
  - `ReviewPanel.execute_external_script()`: carga y llama `main()` en scripts del folder `LGA_NKS_Review_Panel_py`.

- `C:\Users\leg4-pc\.nuke\Python\Startup\LGA_NKS_Review_Panel_py\LGA_Contact_Sheet_OpenInNukeX.py`
  - `get_selected_clips()`: obtiene la seleccion explicita del timeline y filtra efectos.
  - `trigger_hiero_copy()`: dispara `foundry.application.copy`.
  - `send_paste_clipboard_to_nukex()`: valida `ping` y envia `paste_clipboard`.
  - `main()`: orquesta seleccion, copy y paste remoto.

- `C:\Users\leg4-pc\.nuke\LGA_OpenInNukeX\init.py`
  - `handle_client()`: recibe `paste_clipboard` por TCP.
  - `paste_clipboard_with_logging()`: ejecuta `nuke.nodePaste("%clipboard%")` sin cerrar ni abrir scripts.
  - `nuke_server()`: escucha en `localhost:54325`.

- `C:\Users\leg4-pc\.nuke\Python\Startup\docs\Docu_Metodos_Seleccion_Clip.md`
  - Documenta `te.selection()` como metodo de seleccion explicita independiente del playhead.
