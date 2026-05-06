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
| A | `combo.setView(QtWidgets.QListView())` | ✅ Popup limpio |
| B | `combo.setItemDelegate(QtWidgets.QStyledItemDelegate(combo))` | ✅ Popup limpio (visualmente igual a A) |
| Fallback | `combo.setStyle(QStyleFactory.create("Fusion"))` | ✅ Popup limpio (pero cambia look del combo entero) |

#### Solucion ganadora

**`setView(QListView)`** (opcion A). `QListView` no incluye check indicators
y es la solucion mas limpia. Se llama una vez despues de crear el combo:

```python
combo = _ArrowComboBox()
combo.setView(QtWidgets.QListView())
```

---

### Problema 3 — El item en hover del popup tiene texto negro sobre fondo gris

Al hacer hover sobre un item del popup desplegado, el texto pasa a negro
(heredado del sistema) sobre un fondo de seleccion del OS. La combinacion
es ilegible sobre fondos oscuros.

#### Solucion

Agregar `selection-color` y usar `selection-background-color` explicito en
el stylesheet del `QAbstractItemView`:

```css
QComboBox QAbstractItemView {
    background-color: #2B2B2B;
    color: #a7a7a7;
    selection-background-color: #272727;
    selection-color: #a7a7a7;
    outline: 0;
}
```

---

### Receta canonica — `_ArrowComboBox` completo

Combo styled con flecha custom, popup sin checkboxes y hover legible:

```python
combo = _ArrowComboBox()
combo.setView(QtWidgets.QListView())
combo.setStyleSheet(
    "QComboBox { background-color:#272727; border:1px solid #444; "
    "color:#a7a7a7; padding:3px 6px; }"
    "QComboBox::drop-down { border:0px; width:18px; }"
    "QComboBox::down-arrow { image:none; width:0px; height:0px; }"
    "QComboBox QAbstractItemView { background-color:#2B2B2B; color:#a7a7a7; "
    "selection-background-color:#272727; selection-color:#a7a7a7; outline:0; }"
)
```

Para version sin border (columna Track en tabla):

```python
combo = _ArrowComboBox()
combo.setView(QtWidgets.QListView())
combo.setStyleSheet(
    "QComboBox { background-color:#272727; border:0px; "
    "color:#a7a7a7; padding:1px 4px; }"
    "QComboBox::drop-down { border:0px; width:14px; }"
    "QComboBox::down-arrow { image:none; width:0px; height:0px; }"
    "QComboBox QAbstractItemView { background-color:#2B2B2B; "
    "border:1px solid #444444; color:#a7a7a7; "
    "selection-background-color:#272727; selection-color:#a7a7a7; outline:none; }"
)
```

---

## SpinBox (`QSpinBox` / `QDoubleSpinBox`)

### Problema — Los botones arriba/abajo desaparecen con stylesheet custom

Cuando se aplica un stylesheet custom a `QSpinBox`, los botones up/down pueden
desaparecer o quedar invisibles si no se definen los sub-controles
`::up-button`, `::down-button`, `::up-arrow` y `::down-arrow`.

A diferencia de `QComboBox`, **el CSS triangle (border trick) SÍ funciona** en
`QSpinBox` para renderear las flechas.

#### Solucion ganadora

```css
QSpinBox {
    background-color: #272727; border: 1px solid #444;
    color: #a7a7a7; padding: 2px 20px 2px 4px;
}
QSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right;
    width: 18px; border-left: 1px solid #444; background-color: #2e2e2e;
}
QSpinBox::up-button:hover { background-color: #3a3a3a; }
QSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 4px solid #888; width: 0px; height: 0px;
}
QSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 18px; border-left: 1px solid #444; background-color: #2e2e2e;
}
QSpinBox::down-button:hover { background-color: #3a3a3a; }
QSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 4px solid #888; width: 0px; height: 0px;
}
```

El padding derecho `2px 20px 2px 4px` deja espacio para los botones.
Aplicar el mismo patron a `QDoubleSpinBox` (mismos sub-controles).

---

## Referencias

- [LGA_import_shots.py](../LGA_NKS_Edit_Panel_py/LGA_import_shots.py) — clase
  `_ArrowComboBox`, constantes `_COMBO_BASE`, `_COMBO_STYLE_VARIANT_A`.
- [LGA_NKS_Panel_Style_Guide.md](LGA_NKS_Panel_Style_Guide.md) — guia general
  de estilos de paneles (colores, fuentes, bordes).
- [GUI_Windows_Reference.md](GUI_Windows_Reference.md) — referencias de
  ventanas y widgets utilizados en el proyecto.
