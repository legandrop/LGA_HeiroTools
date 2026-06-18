# LGA_NKS_OrganizeProject

Documentacion del boton **Organize Project** del **Edit Panel**.

## Resumen

El boton ejecuta `LGA_NKS_OrganizeProject.py`. Su funcion es reorganizar clips dentro del `clipsBin()` del proyecto activo de Hiero/Nuke Studio, moviendolos a una estructura de bins derivada del path del archivo de media.

La estructura final que busca generar es:

```text
Clips
+-- F <parts[2]>
    +-- <parts[3]>
        +-- clip
```

Donde `parts` sale de dividir el path de media con `/`.

Ejemplo:

```text
Path: /show/SEQ001/SHOT010/Comp/v001/render.exr
parts[2]: SEQ001
parts[3]: SHOT010

Bin destino:
Clips/F SEQ001/SHOT010/
```

## Como se ejecuta

1. El boton del Edit Panel llama a `organize_project()` en `LGA_NKS_Edit_Panel.py`.
2. Ese metodo ejecuta el script externo `LGA_NKS_OrganizeProject.py`.
3. El script toma el primer proyecto abierto devuelto por `hiero.core.projects()`.
4. Si hay proyecto activo, abre un bloque de undo llamado `Reorganize Clips Based on Path`.
5. Recorre los bins existentes dentro de `project.clipsBin()`.
6. Mueve clips a bins calculados desde su path de media.
7. Elimina bins vacios al terminar.

## Reglas de organizacion

- Solo procesa items que esten dentro de bins del `clipsBin()` del proyecto.
- Recorre bins de forma recursiva.
- Si encuentra un bin llamado exactamente `Published`, lo ignora completo, incluyendo todos sus sub-bins y clips.
- Solo mueve items que sean `hiero.core.BinItem` cuyo `activeItem()` sea un `hiero.core.Clip`.
- Para cada clip, lee `clip.mediaSource().fileinfos()[0].filename()`.
- Usa solamente el primer `fileinfo()` del media source.
- Divide el path usando `/`.
- Solo organiza clips cuyo path tenga mas de 3 partes (`len(parts) > 3`).
- Crea o reutiliza un bin de secuencia en la raiz de `clipsBin()` con el nombre `F <parts[2]>`.
- Crea o reutiliza un sub-bin de shot dentro del bin de secuencia con el nombre `<parts[3]>`.
- Mueve el `clip.binItem()` al bin destino `Clips/F <parts[2]>/<parts[3]>`.
- Si el clip ya esta en ese bin destino, no lo mueve.
- No renombra clips.
- No modifica el path de media.
- No cambia tracks, timeline items, versiones, tags ni metadata.
- Al final elimina bins vacios, de forma recursiva.
- La limpieza tambien ignora cualquier bin llamado exactamente `Published`.
- No elimina bins que todavia contengan items.

## Reglas implicitas y limitaciones

- El script asume paths separados por `/`. Si un path viniera con `\`, la regla de `parts[2]` y `parts[3]` no funcionaria como se espera.
- Los clips que esten directamente en la raiz de `clipsBin()` no se procesan, porque el recorrido inicial solo entra en items que sean bins.
- Los clips sin `mediaSource()`, sin `fileinfos()`, o con path demasiado corto no se mueven.
- Si existen varios bins con el mismo nombre en distintos lugares, el destino siempre se busca o crea bajo `clipsBin()/F <parts[2]>`.
- Si hay dos clips de distintos origenes que resuelven al mismo `parts[2]` y `parts[3]`, ambos terminan en el mismo bin.

## Archivo principal

- Script: `LGA_HieroTools/LGA_NKS_Edit_Panel_py/LGA_NKS_OrganizeProject.py`
- Boton: `LGA_HieroTools/LGA_NKS_Edit_Panel.py`
