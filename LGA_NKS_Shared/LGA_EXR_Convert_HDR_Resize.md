# HDR Resize — Pixeles Negativos en AP0

## El problema

Al hacer downscale de material ACES AP0 (ACES2065-1) con oiiotool, aparecen pixeles
negativos en zonas de alto contraste — típicamente bordes donde valores HDR extremos
(ej. 59 RGB) están junto a valores bajos (ej. 0.3 RGB). En el resultado quedan "agujeros"
visibles en la imagen.

**El problema NO es DWAA.** DWAA simplemente guarda los valores negativos que ya vienen
del resize. El causante es el filtro de resampling.

### Por qué sucede

Los filtros de resampling de alta calidad (Lanczos, Cubic, Blackman-Harris) tienen
"negative lobes" — partes del kernel con valores negativos que son parte del diseño
matemático para preservar frecuencias altas. En imágenes SDR (0–1) esto es invisible.
En material HDR AP0 con valores de 59, el lóbulo negativo puede producir un pixel en
−2 o −5. ACES AP0 empeora el problema porque tiene primarias extremadamente amplias,
lo que genera valores numéricos más extremos que ACEScg.

**Contexto AP0**: AP0/ACES2065-1 es el espacio de intercambio/archivo de ACES.
ACEScg/AP1 es el espacio de trabajo recomendado para procesamiento. AP0 genera
problemas numéricos más fácilmente al aplicar operaciones de filtering/resampling.

---

## Opciones descubiertas

### Opción A — `hdr_resize` (rangecompress + highlightcomp)
**Estado: [✅] FUNCIONA — probado 2026-05-08**

La recomendación de Larry Gritz (creador de OIIO) específicamente para material HDR.
Disponible en oiiotool 2.4+ (nuestra versión: 2.4.11.1 — ✓ confirmado).

Flujo:
```
input.exr → --rangecompress → --resize:highlightcomp=1 → --rangeexpand → dwaa
```

- `--rangecompress`: comprime valores >1.0 a escala logarítmica antes del resize.
- `highlightcomp=1`: mecanismo adicional de oiiotool específico para ringing HDR.
- `--rangeexpand`: restaura la escala lineal original.
- No requiere OCIO. Opera puramente a nivel matemático.
- Los valores negativos legítimos de AP0 (out-of-gamut) se preservan;
  solo se eliminan los negativos artificiales del ringing.

**Activación en manifest JSON:**
```json
{
  "hdr_resize": true,
  "resize": { "width": 2048, "height": 1152, "filter": "lanczos3" },
  ...
}
```

**Activación vía CLI:**
```
python LGA_EXR_Convert.py --manifest job.json --hdr-resize
```

**Comando oiiotool resultante** (para verificar con `--dry-run`):
```
oiiotool input.exr --rangecompress --resize 2048x1152:filter=lanczos3:highlightcomp=1 --rangeexpand --compression dwaa:quality=45 --nosoftwareattrib -o output.exr
```

---

### Opción B — AP0 → ACEScg → resize → AP0 (round-trip OCIO)
**Estado: [ ] sin probar**

Recomendación de ACESCentral (Thomas Mansencal y otros). ACEScg/AP1 tiene primarias
más razonables y genera menos problemas numéricos al filtrar.

Flujo:
```
AP0 input → colorconvert AP0→ACEScg → rangecompress → resize:highlightcomp=1 → rangeexpand → colorconvert ACEScg→AP0 → dwaa
```

#### OCIO config para esta opción

Se creó un config mínimo sin LUT, solo matrices:
```
LGA_NKS_Shared/OCIO/aces_ap0_ap1.ocio
```

- Solo 2 colorspaces: `"ACES - ACES2065-1"` y `"ACES - ACEScg"`
- Transformación puramente matricial (AP1→AP0: ACES TB-2014-004)
- Sin archivos LUT — completamente self-contained
- Compatible con oiiotool OCIO 2.1.2 ✅ (verificado)

**Por qué NO usar los configs de Nuke 17:**
Los configs `fn-nuke_*` de Nuke 17 son OCIO v2.4 — incompatibles con nuestro
oiiotool (OCIO 2.1.2). Error explícito al intentar cargarlos.

**Por qué NO copiar el ACES 1.2 de Nuke 15:**
La carpeta `aces_1.2` pesa 430 MB (LUTs de cámaras que no necesitamos).
`ACES - ACEScg` en ese config usa un shaper LUT `.spi1d`. Para AP0↔ACEScg
no necesitamos LUTs — es matriz pura. El config mínimo es la solución correcta.

Comando oiiotool completo:
```
oiiotool input.exr
  --colorconfig "LGA_NKS_Shared/OCIO/aces_ap0_ap1.ocio"
  --colorconvert "ACES - ACES2065-1" "ACES - ACEScg"
  --rangecompress
  --resize 2048x1152:filter=lanczos3:highlightcomp=1
  --rangeexpand
  --colorconvert "ACES - ACEScg" "ACES - ACES2065-1"
  --compression dwaa:quality=45 --nosoftwareattrib
  -o output.exr
```

**Nota sobre `--resize:hdr=1`** (ChatGPT lo menciona): este flag NO existe en
oiiotool. El correcto es `highlightcomp=1`, que ya probamos en Opción A.

**No implementado todavía** en LGA_EXR_Convert.py. Requiere agregar
`ocio_src_pre` / `ocio_dst_pre` separados del OCIO de salida actual.

---

### Opción C — Filtro sin negative lobes
**Estado: [ ] sin probar**

Cambiar el filtro a uno sin lóbulos negativos: `triangle` (bilinear) o `gaussian`.
Evita el ringing pero produce resultados más suaves/borrosos.

```json
{ "resize": { "width": 2048, "height": 1152, "filter": "gaussian" } }
```

Muchos labs prefieren esta opción por simplicidad aunque implique algo de sharpness loss.
No requiere cambios de código.

---

### Opción D — Clamp post-resize
**Estado: [ ] sin probar**

Clampa los valores negativos después del resize. Destruye información out-of-gamut.
No recomendado para material AP0 que puede tener negativos legítimos.
No implementado en LGA_EXR_Convert.py.

---

## Resultados de pruebas

| # | Opción | Fecha | Resultado | Notas |
|---|--------|-------|-----------|-------|
| 1 | A — rangecompress + highlightcomp=1 | 2026-05-08 | ✅ OK | Eliminó los pixeles negativos en material AP0 con highlights extremos |
| 2 | B — round-trip AP0→ACEScg (sin rangecompress) | 2026-05-08 | ❌ Peor que A | Flujo correcto confirmado por log, pero resultado visual inferior a Opción A |
| 3 | B+A — round-trip AP0→ACEScg + rangecompress | 2026-05-08 | ✅ OK | Similar a A. No supera claramente a A, mayor overhead (~23.5s vs ~21s) |
| 4 | C — filtro gaussian/triangle | — | pendiente | — |

---

## Archivos relacionados

| Archivo | Relevancia |
|---------|------------|
| `LGA_NKS_Shared/LGA_EXR_Convert.py` | `build_oiiotool_command()` — donde se aplica `hdr_resize`. `ConvertOptions.hdr_resize`. |
| `LGA_NKS_Shared/LGA_EXR_Convert.MD` | Documentación general de LGA_EXR_Convert |
| `LGA_NKS_Edit_Panel_py/LGA_import_shots_transcode.py` | `build_manifest_for_sequence()` — genera el JSON que pasa a LGA_EXR_Convert |

## Decisión final

**Opción A implementada como auto-detección en `LGA_EXR_Convert.py`.**

`hdr_resize` se activa automáticamente cuando:
1. El primer frame del job tiene chromaticities AP0 (`Rx≈0.7347, Ry≈0.2653`) o `acesImageContainerFlag`
2. Hay resize (`options.resize is not None`)

Nadie tiene que configurar nada. El manifest no necesita `hdr_resize`. La tool decide sola.

El log de stderr confirma la decisión frame a frame:
- `AUTO hdr_resize=ON: AP0 detectado + resize activo`
- `hdr_resize=OFF: material no es AP0`

Los flags `hdr_resize` y `ocio_round_trip` siguen existiendo para override manual vía manifest o CLI.

---

## Implementación actual (Opción A)

`hdr_resize` fue agregado en `LGA_EXR_Convert.py`:

- `ConvertOptions.hdr_resize: bool = False`
- Se lee de `manifest["hdr_resize"]` y de `--hdr-resize` CLI
- En `build_oiiotool_command`: si `hdr_resize` y hay `resize`, inserta
  `--rangecompress` antes del resize y `--rangeexpand` después;
  además fuerza `highlightcomp=1` en el sub-argumento del resize.
- Si `resize_filter` no está definido, usa `lanczos3` como default cuando `hdr_resize=True`.
