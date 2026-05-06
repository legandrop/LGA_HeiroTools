> **Regla de documentacion**: este archivo recopila aprendizajes y soluciones a
> problemas recurrentes de UI con PySide/PyQt en Hiero/Nuke Studio. No es un
> historial ni changelog; cada seccion describe un problema concreto, las
> opciones probadas y la solucion ganadora.

# Aprendizajes UI — PySide / PyQt en Hiero/Nuke

Bitacora de problemas de styling y rendering de widgets que se repitieron en
multiples herramientas del proyecto. La idea es no volver a perder tiempo
reinventando la rueda cuando aparezca el mismo sintoma.

---

## Dropdowns (`QComboBox`)

### Problema 1 — La flecha `▼` se ve como un cuadradito

Cuando se aplica un stylesheet custom a `QComboBox`, la flecha del drop-down
aparece como un pequeño cuadrado solido en vez del triangulo `▼` esperado.
Sintoma comun cuando se usa el truco de los borders CSS para "dibujar" el
triangulo.

#### Opciones probadas

| # | Estrategia | Resultado |
|---|-----------|-----------|
| 1 | CSS triangle (`border-left/right transparent + border-top solido`, `width:0; height:0`) | ❌ Aparece un cuadrado en vez del triangulo |
| 2 | SVG inline via `image: url("data:image/svg+xml;...")` | ❌ No renderea el SVG en este Qt build |
| 3 | Sin custom drop-down (solo styling de `QComboBox`) | ❌ Mantiene el cuadrado heredado del style |
| 4 | `image: none` con drop-down area visible | ❌ Mismo cuadrado |
| 5 | Subclase con `paintEvent` dibujando el triangulo via `QPainter` | ✅ Flecha perfecta |
| 6 | Sin stylesheet (default puro de Qt) | ❌ Estetica inconsistente con el resto de la UI |
| 7 | `setStyle(QStyleFactory.create("Fusion"))` | ⚠ Flecha mas fea pero el popup no muestra checkboxes |

#### Solucion ganadora

**Subclase con `paintEvent`** (opcion 5). Se oculta la flecha nativa via
stylesheet y se pinta el triangulo manualmente:

```python
class _ArrowComboBox(QtWidgets.QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        cx = rect.right() - 10
        cy = rect.center().y() + 1
        path = QtGui.QPainterPath()
        path.moveTo(cx - 4, cy - 2)
        path.lineTo(cx + 4, cy - 2)
        path.lineTo(cx, cy + 3)
        path.closeSubpath()
        p.fillPath(path, QtGui.QColor("#999999"))
        p.end()
```

Stylesheet acompañante para ocultar la flecha nativa:

```css
QComboBox::drop-down { border: 0px; width: 18px; }
QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
```

---

### Problema 2 — El popup desplegado muestra checkboxes a la izquierda de cada item

Al desplegar el `QComboBox`, los items aparecen con un check indicator (caja
vacia) a la izquierda. Es el delegate nativo del style de Windows.

#### Opciones probadas

| # | Estrategia | Resultado |
|---|-----------|-----------|
| A | `combo.setView(QtWidgets.QListView())` | (a confirmar) |
| B | `combo.setItemDelegate(QtWidgets.QStyledItemDelegate(combo))` | (a confirmar) |
| Fallback | `combo.setStyle(QStyleFactory.create("Fusion"))` | ✅ Popup limpio (pero cambia look del combo entero) |

#### Solucion ganadora

**Pendiente** — actualmente bajo test en
[LGA_import_shots.py](../LGA_NKS_Edit_Panel_py/LGA_import_shots.py) en la
seccion de tests de la pagina de Convert. Se actualiza este archivo cuando
quede confirmado.

---

### Combo final recomendado

Cuando se confirme la solucion al Problema 2, la receta canonica para crear
un combo styled con flecha custom y popup limpio quedara documentada aqui.
Por ahora ver [`_ArrowComboBox`](../LGA_NKS_Edit_Panel_py/LGA_import_shots.py)
y los stylesheets `_COMBO_BASE` / `_COMBO_STYLE_VARIANT_A` / `_COMBO_STYLE_VARIANT_B`.

---

## Referencias

- [LGA_import_shots.py](../LGA_NKS_Edit_Panel_py/LGA_import_shots.py) — clase
  `_ArrowComboBox`, constantes `_COMBO_BASE`, `_COMBO_STYLE_VARIANT_A/B`.
- [LGA_NKS_Panel_Style_Guide.md](LGA_NKS_Panel_Style_Guide.md) — guia general
  de estilos de paneles (colores, fuentes, bordes).
- [GUI_Windows_Reference.md](GUI_Windows_Reference.md) — referencias de
  ventanas y widgets utilizados en el proyecto.
