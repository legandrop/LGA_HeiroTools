---
name: Transcode EXR implementation
overview: Implementar el botón "Start Transcode" en la sub-vista Convert de LGA_import_shots, usando LGA_EXR_Convert.py via manifest JSON y el patrón QRunnable + QThreadPool para no bloquear la UI.
todos:
  - id: todo-1778037627526-5e82gkf6o
    content: revisar LGA_NKS_Flow_CreateShot.md y el .py para ver como manejan perfectamente la ui separada del thread
    status: completed
  - id: create-transcode-module
    content: Crear LGA_import_shots_transcode.py con TranscodeWorkerSignals, TranscodeWorker y build_manifest_for_sequence
    status: completed
  - id: wire-ui
    content: "En LGA_import_shots.py: conectar _start_transcode_btn, implementar _run_transcode(), _update_transcode_btn_state() y handlers de señales"
    status: completed
  - id: save-go-back-ref
    content: Guardar referencia a go_back_btn en _build_page_convert() para poder deshabilitarlo durante el transcode
    status: completed
  - id: update-md
    content: "Actualizar LGA_import_shots.md: documentar módulo nuevo, limitaciones channels/bitdepth como pendiente explícito"
    status: completed
isProject: false
---

# Implementación del Transcode EXR

## Limitaciones documentadas (UI presente, converter no soporta)

Las siguientes opciones de la UI existen pero **no se pasan al manifest** en esta versión. Se documentan como pendiente en el `.md`:

- **Bit depth** (`half`/`float`): requiere agregar `--bit-depth` a `LGA_EXR_Convert.py` + `--type half/float` en oiiotool
- **Channels** (`RGBA→RGB`): requiere agregar `--channels` a `LGA_EXR_Convert.py` + `--ch R,G,B` en oiiotool
- **Transcode de MOV**: checkbox disabled en la tabla, estado "No soportado" — sin cambios

Las opciones que SÍ se implementan: DWAA on/off, DWAA level, resize + filtro, no-upscale flag (omite resize para esas filas), move_originals, delete_originals.

---

## Archivos a crear / modificar

- **NEW** [`LGA_NKS_Edit_Panel_py/LGA_import_shots_transcode.py`](LGA_NKS_Edit_Panel_py/LGA_import_shots_transcode.py) — módulo helper de transcode
- **MODIFY** [`LGA_NKS_Edit_Panel_py/LGA_import_shots.py`](LGA_NKS_Edit_Panel_py/LGA_import_shots.py) — conectar botón + handlers UI
- **MODIFY** [`LGA_NKS_Edit_Panel_py/LGA_import_shots.md`](LGA_NKS_Edit_Panel_py/LGA_import_shots.md) — documentar limitaciones + nuevo módulo

---

## Módulo helper: `LGA_import_shots_transcode.py`

### Clases y funciones

**`TranscodeWorkerSignals(QObject)`** — señales:
```python
log_message      = Signal(str)
sequence_started = Signal(int)           # row_index
sequence_done    = Signal(int, bool, dict)  # row_index, ok, stats
all_done         = Signal(list)          # [per-sequence results]
error            = Signal(str)
```

**`build_manifest_for_sequence(item, tw, th, compression, dwa_level, resize_filter, overwrite)`** → `dict`

Construye el manifest JSON para una sola secuencia EXR. Enumera todos los `.exr` en `item["path"]` con `sorted(Path(item["path"]).glob("*.exr"))`, mapea `src→dst`:

- **TEST mode**: `dst = {item_path}/test_transcode/{filename}`
- **Normal + move_originals ON**: `src = {item_path}/Originals/{filename}`, `dst = {item_path}/{filename}`
- **Normal + move_originals OFF**: `src = {item_path}/_tc_temp_src/{filename}` (archivos movidos ahí temporalmente), `dst = {item_path}/{filename}`

Si `tw == item["width"] and th == item["height"]` → `resize = null` en el manifest (no escala inútil).

**`TranscodeWorker(QRunnable)`**

Constructor recibe:
```python
def __init__(self, job_sequences, global_opts, test_mode, move_originals, delete_originals, shared_dir):
```

`job_sequences` = lista de `(row_i, item, tw, th)`.

`run()` itera secuencias **en serie** (el paralelismo lo hace el converter internamente por frame):

```
para cada (row_i, item, tw, th):
    1. emit sequence_started(row_i)
    2. Si test_mode:
         dst_dir = item_path / "test_transcode"
         no mover nada
       Elif move_originals:
         crear Originals/, mover *.exr allí
         src = Originals/, dst = item_path/
       Else:
         crear _tc_temp_src/, mover *.exr allí
         src = _tc_temp_src/, dst = item_path/
    3. build_manifest → escribir a temp .json
    4. subprocess: python LGA_EXR_Convert.py --manifest ... --log-json ...
    5. parsear JSON de stdout
    6. emit sequence_done(row_i, ok, stats)
    7. Si ok and delete_originals and move_originals:
         shutil.rmtree(Originals/)
       Si ok and not move_originals:
         shutil.rmtree(_tc_temp_src/)
       Si not ok and not test_mode:
         restaurar archivos (mover de vuelta de Originals/ o _tc_temp_src/)
emit all_done(results)
```

---

## Cambios en `LGA_import_shots.py`

### 1. Import del nuevo módulo

```python
from LGA_NKS_Edit_Panel_py.LGA_import_shots_transcode import (
    TranscodeWorker, TranscodeWorkerSignals
)
```

### 2. Habilitar Start Transcode

En `_update_convert_page()`, reemplazar el `setEnabled(False)` hardcodeado por llamada a `_update_transcode_btn_state()`.

En `_on_convert_row_clicked()`, agregar llamada a `_update_transcode_btn_state()` al final.

```python
def _update_transcode_btn_state(self):
    has_exr = any(
        chk.isChecked() and chk.isEnabled()
        for chk in self._convert_checkboxes.values()
    )
    self._start_transcode_btn.setEnabled(has_exr)
    self._start_transcode_btn.setToolTip(
        "" if has_exr else "Selecciona al menos un EXR"
    )
```

### 3. Conectar el botón

En `_build_page_convert()`:
```python
self._start_transcode_btn.clicked.connect(self._run_transcode)
```

### 4. `_run_transcode()`

```python
def _run_transcode(self):
    # Recolectar items checked (solo EXR habilitados)
    job_sequences = []
    for row_i, chk in self._convert_checkboxes.items():
        if not chk.isChecked() or not chk.isEnabled():
            continue
        item = self._convert_rows[row_i]
        tw, th = self._current_target_res(item["width"], item["height"])
        # no-upscale: si tw>sw o th>sh, usar dimensiones originales
        if self._convert_no_upscale.isChecked():
            if (item["width"] and tw > item["width"]) or (item["height"] and th > item["height"]):
                tw, th = item["width"], item["height"]
        job_sequences.append((row_i, item, tw, th))

    if not job_sequences:
        return

    # Deshabilitar botones durante el proceso
    self._start_transcode_btn.setEnabled(False)
    self._go_back_btn.setEnabled(False)  # referencia guardada en build
    self._convert_log.clear()

    global_opts = {
        "compression": self._target_compression(None),
        "dwa_level": self._convert_dwaa_level.value(),
        "resize_filter": self._convert_filter.currentText(),
        "workers": 6,
    }

    worker = TranscodeWorker(
        job_sequences, global_opts,
        test_mode=Transcode_TEST_Mode,
        move_originals=self._move_originals_chk.isChecked(),
        delete_originals=self._delete_originals_chk.isChecked(),
        shared_dir=str(SHARED_DIR),
    )
    worker.signals.log_message.connect(self._on_transcode_log)
    worker.signals.sequence_started.connect(self._on_sequence_started)
    worker.signals.sequence_done.connect(self._on_sequence_done)
    worker.signals.all_done.connect(self._on_transcode_all_done)
    worker.signals.error.connect(self._on_transcode_error)
    QThreadPool.globalInstance().start(worker)
```

### 5. Handlers de señales

```python
def _on_transcode_log(self, msg):
    self._convert_log.appendPlainText(msg)

def _on_sequence_started(self, row_i):
    # Estado → "Convirtiendo..."
    html = "<span style='color:#d9a441;'>Convirtiendo...</span>"
    self._convert_table.setCellWidget(row_i, 7, _cell_html_label(html))

def _on_sequence_done(self, row_i, ok, stats):
    # Estado → "✓ Listo" o "✗ Error"
    if ok:
        txt = "✓ Listo"
        clr = _CLR_STATUS_DONE
    else:
        txt = "✗ Error"
        clr = _CLR_STATUS_ERROR
    self._convert_table.setCellWidget(row_i, 7, _cell_html_label(
        "<span style='color:%s;'>%s</span>" % (clr, txt)
    ))

def _on_transcode_all_done(self, results):
    total_ok = sum(1 for r in results if r.get("ok"))
    self._on_transcode_log("Transcode completo: %d/%d OK" % (total_ok, len(results)))
    self._start_transcode_btn.setEnabled(True)
    self._go_back_btn.setEnabled(True)

def _on_transcode_error(self, msg):
    self._on_transcode_log("ERROR: " + msg)
    self._start_transcode_btn.setEnabled(True)
    self._go_back_btn.setEnabled(True)
```

---

## Flujo completo en el worker (secuencia)

```
[Worker hilo secundario]
  ↓ para cada (row_i, item, tw, th)
  ↓ emit sequence_started(row_i)          → UI: "Convirtiendo..."
  ↓ preparar paths (test / move / temp)
  ↓ escribir manifest JSON a temp file
  ↓ subprocess(python LGA_EXR_Convert.py --manifest X --log-json Y)
  ↓ parsear resultado JSON
  ↓ emit sequence_done(row_i, ok, stats)  → UI: "✓ Listo" o "✗ Error"
  ↓ emit log_message(...)                → UI: log panel
  ↓ post: delete_originals / restaurar
↓ emit all_done(results)                 → UI: re-enable botones
```

---

## Pendientes documentados en el .md

Agregar en la sección "Pendiente de implementación":

- **Convert — Channels (RGBA→RGB)**: opción presente en UI pero ignorada en el manifest. Requiere agregar `--channels` a `LGA_EXR_Convert.py` y pasarlo como `--ch R,G,B` a oiiotool.
- **Convert — Bit depth**: opción presente en UI pero ignorada en el manifest. Requiere agregar `--bit-depth half/float` a `LGA_EXR_Convert.py` y pasarlo como `--type half/float` a oiiotool.
