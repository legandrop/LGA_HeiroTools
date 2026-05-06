"""
Helper de transcode EXR para LGA_import_shots.

Proporciona:
  - TranscodeWorkerSignals  — QObject con señales Qt para comunicación entre hilos
  - TranscodeWorker         — QRunnable que ejecuta LGA_EXR_Convert.py via subprocess
  - build_manifest_for_sequence — construye el manifest dict para una secuencia EXR

El worker procesa las secuencias en serie (una tras otra); el paralelismo por frame
lo maneja internamente LGA_EXR_Convert.py con concurrent.futures.

Uso:
    worker = TranscodeWorker(job_sequences, global_opts, ...)
    worker.signals.log_message.connect(mi_funcion_log)
    worker.signals.sequence_done.connect(mi_funcion_done)
    worker.signals.all_done.connect(mi_funcion_all_done)
    QtCore.QThreadPool.globalInstance().start(worker)
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtCore

QObject    = QtCore.QObject
QRunnable  = QtCore.QRunnable
Signal     = QtCore.Signal
Slot       = QtCore.Slot


# ── Señales ───────────────────────────────────────────────────────────────────

class TranscodeWorkerSignals(QObject):
    """
    Señales emitidas por TranscodeWorker hacia el hilo principal de la UI.

    log_message      — línea de texto para el panel de log (plain text)
    sequence_started — (row_index, dst_dir_str, total_frames): archivos preparados,
                       subprocess a punto de arrancar — permite iniciar barra de progreso
    sequence_done    — (row_index, ok, stats_dict): la secuencia terminó
    all_done         — lista de dicts resultado por secuencia (worker terminó)
    error            — mensaje de error fatal (detiene el worker)
    """
    log_message      = Signal(str)
    sequence_started = Signal(int, str, int)   # row_i, dst_dir, total_frames
    sequence_done    = Signal(int, bool, dict)
    all_done         = Signal(list)
    error            = Signal(str)


# ── Manifest builder ──────────────────────────────────────────────────────────

def build_manifest_for_sequence(
    item: dict,
    src_dir: Path,
    dst_dir: Path,
    tw: int | None,
    th: int | None,
    compression: str,
    dwa_level: int,
    resize_filter: str,
    overwrite: bool = True,
) -> dict:
    """
    Construye el manifest dict para LGA_EXR_Convert.py para una sola secuencia EXR.

    Enumera todos los .exr en src_dir y mapea src→dst manteniendo el mismo filename.
    Si tw/th coinciden con las dimensiones originales del item, resize queda null.

    Args:
        item:           dict del item de _convert_rows (necesita 'width', 'height')
        src_dir:        directorio con los EXR fuente
        dst_dir:        directorio destino para los EXR convertidos
        tw, th:         resolución destino (None → no resize)
        compression:    "dwaa", "zip", etc.
        dwa_level:      nivel de compresión DWA (e.g. 45)
        resize_filter:  "lanczos3", "cubic", "box"
        overwrite:      si True, sobreescribe archivos existentes en dst

    Returns:
        manifest dict listo para json.dumps()
    """
    src_path = Path(src_dir)
    dst_path = Path(dst_dir)

    exr_files = sorted(src_path.glob("*.exr"))
    if not exr_files:
        exr_files = sorted(src_path.glob("**/*.exr"))

    tasks = [
        {"src": str(f), "dst": str(dst_path / f.name)}
        for f in exr_files
    ]

    # Solo incluir resize si hay cambio real de dimensiones
    sw, sh = item.get("width"), item.get("height")
    resize = None
    if tw and th and sw and sh and (tw != sw or th != sh):
        resize = {"width": tw, "height": th, "filter": resize_filter}

    return {
        "compression": compression,
        "dwa_level":   dwa_level,
        "resize":      resize,
        "workers":     6,
        "overwrite":   overwrite,
        "tasks":       tasks,
    }


# ── Worker ────────────────────────────────────────────────────────────────────

class TranscodeWorker(QRunnable):
    """
    Worker de transcode EXR. Diseñado para ejecutarse en QThreadPool.

    Itera las secuencias en serie. Por cada secuencia:
      1. Prepara paths de src/dst según modo (test / move_originals / temp)
      2. Construye el manifest JSON
      3. Llama a LGA_EXR_Convert.py via subprocess con el Python bundled de OIIO
      4. Parsea el resultado JSON y emite señales hacia la UI

    En caso de fallo (no test_mode), restaura los originales automáticamente.
    """

    def __init__(
        self,
        job_sequences: list[tuple[int, dict, int | None, int | None]],
        global_opts: dict,
        test_mode: bool,
        move_originals: bool,
        delete_originals: bool,
        shared_dir: str,
    ):
        """
        Args:
            job_sequences:    lista de (row_index, item_dict, target_w, target_h)
            global_opts:      dict con compression, dwa_level, resize_filter, workers
            test_mode:        si True, output a {seq}/test_transcode/ sin mover nada
            move_originals:   si True, mueve originales a {seq}/Originals/ antes de convertir
            delete_originals: si True (y move_originals), borra Originals/ tras éxito
            shared_dir:       path a LGA_NKS_Shared/ (str)
        """
        super(TranscodeWorker, self).__init__()
        self.job_sequences    = job_sequences
        self.global_opts      = global_opts
        self.test_mode        = test_mode
        self.move_originals   = move_originals
        self.delete_originals = delete_originals
        self.shared_dir       = Path(shared_dir)
        self.signals          = TranscodeWorkerSignals()

        self._convert_script = self.shared_dir / "LGA_EXR_Convert.py"
        # Python bundled con OIIO — garantiza stdlib completa + no depende de sys.executable
        self._python_exe = self.shared_dir / "OIIO_Win" / "bin" / "python" / "python.exe"
        self._start_time: float = 0.0

    # ── Helpers de tiempo ────────────────────────────────────────────────

    def _t(self) -> str:
        """Retorna el tiempo transcurrido desde el inicio del worker como '[N.Ns]'."""
        return "[%.1fs]" % (time.perf_counter() - self._start_time)

    # ── Entry point del hilo secundario ──────────────────────────────────

    @Slot()
    def run(self):
        self._start_time = time.perf_counter()
        total = len(self.job_sequences)
        self.signals.log_message.emit(
            "%s Iniciando transcode — %d secuencia%s" % (
                self._t(), total, "" if total == 1 else "s"
            )
        )

        all_results = []
        try:
            for idx, (row_i, item, tw, th) in enumerate(self.job_sequences, 1):
                seq_name = item.get("name", Path(item["path"]).name)
                self.signals.log_message.emit(
                    "%s [%d/%d] %s" % (self._t(), idx, total, seq_name)
                )
                result = self._transcode_sequence(row_i, item, tw, th, idx, total)
                all_results.append(result)

            ok_count = sum(1 for r in all_results if r.get("ok"))
            self.signals.log_message.emit(
                "%s Transcode completo: %d/%d OK" % (self._t(), ok_count, total)
            )
        except Exception as exc:
            self.signals.error.emit("Error inesperado en worker: %s" % str(exc))
            return

        self.signals.all_done.emit(all_results)

    # ── Proceso de una secuencia ──────────────────────────────────────────

    def _transcode_sequence(
        self,
        row_i: int,
        item: dict,
        tw: int | None,
        th: int | None,
        seq_idx: int,
        seq_total: int,
    ) -> dict:
        item_path = Path(item["path"])
        seq_name  = item.get("name", item_path.name)
        seq_start = time.perf_counter()

        originals_dir: Path | None = None
        temp_src_dir:  Path | None = None

        try:
            # ── 1. Preparar paths de src / dst ────────────────────────
            if self.test_mode:
                src_dir = item_path
                dst_dir = item_path / "test_transcode"
                dst_dir.mkdir(parents=True, exist_ok=True)

            elif self.move_originals:
                originals_dir = item_path / "Originals"
                originals_dir.mkdir(parents=True, exist_ok=True)
                moved = self._move_exrs(item_path, originals_dir)
                if moved == 0:
                    raise RuntimeError("No se encontraron EXR en: %s" % item_path)
                self.signals.log_message.emit(
                    "  %s %d EXR movidos a Originals/" % (self._t(), moved)
                )
                src_dir = originals_dir
                dst_dir = item_path

            else:
                # Sin move_originals: usar carpeta temporal como buffer
                temp_src_dir = item_path / "_tc_temp_src"
                temp_src_dir.mkdir(parents=True, exist_ok=True)
                moved = self._move_exrs(item_path, temp_src_dir)
                if moved == 0:
                    raise RuntimeError("No se encontraron EXR en: %s" % item_path)
                src_dir = temp_src_dir
                dst_dir = item_path

            # ── 2. Construir manifest ─────────────────────────────────
            compression   = self.global_opts.get("compression", "dwaa")
            dwa_level     = int(self.global_opts.get("dwa_level", 45))
            resize_filter = self.global_opts.get("resize_filter", "lanczos3")
            workers       = int(self.global_opts.get("workers", 6))

            manifest = build_manifest_for_sequence(
                item, src_dir, dst_dir, tw, th,
                compression, dwa_level, resize_filter,
                overwrite=True,
            )
            manifest["workers"] = workers

            frame_count = len(manifest["tasks"])
            if frame_count == 0:
                raise RuntimeError("No se encontraron frames EXR en: %s" % src_dir)

            # Emitir sequence_started DESPUÉS de preparar archivos y conocer frame_count.
            # La UI puede iniciar la barra de progreso sabiendo dst_dir y total de frames.
            self.signals.sequence_started.emit(row_i, str(dst_dir), frame_count)

            resize_info = (
                "%dx%d · %s" % (tw, th, resize_filter)
                if manifest["resize"] else "resolución original"
            )
            self.signals.log_message.emit(
                "  %s %d frames | %s | comp: %s%s | workers: %d" % (
                    self._t(), frame_count, resize_info,
                    compression,
                    (":%d" % dwa_level) if compression.lower().startswith("dwa") else "",
                    workers,
                )
            )

            # ── 3. Escribir manifest a archivo temporal ───────────────
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tf:
                json.dump(manifest, tf, indent=2)
                manifest_path = Path(tf.name)

            log_json_path = manifest_path.with_suffix(".result.json")

            # ── 4. Ejecutar LGA_EXR_Convert.py ───────────────────────
            python_exe = str(self._python_exe)
            if not self._python_exe.exists():
                # Fallback: Python del PATH (menos confiable en Nuke, pero mejor que nada)
                python_exe = "python"

            cmd = [
                python_exe,
                str(self._convert_script),
                "--manifest", str(manifest_path),
                "--log-json", str(log_json_path),
            ]

            extra = {}
            if platform.system() == "Windows":
                extra["creationflags"] = subprocess.CREATE_NO_WINDOW

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **extra,
            )

            # ── 5. Parsear resultado ──────────────────────────────────
            report = None
            if log_json_path.exists():
                try:
                    report = json.loads(log_json_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if report is None and proc.stdout.strip():
                try:
                    report = json.loads(proc.stdout)
                except Exception:
                    pass
            if report is None:
                stderr_snippet = (proc.stderr or "sin salida")[:300]
                report = {"ok": False, "error": stderr_snippet}

            elapsed   = time.perf_counter() - seq_start
            ok        = bool(report.get("ok", False))
            ok_count  = report.get("ok_count", 0)
            fps_rate  = report.get("fps", 0.0)

            if ok:
                self.signals.log_message.emit(
                    "  %s ✓ OK — %d/%d frames en %.1fs (%.1f fps)" % (
                        self._t(), ok_count, frame_count, elapsed, fps_rate
                    )
                )
            else:
                failed   = report.get("failed_count", frame_count - ok_count)
                err_msg  = report.get("error") or "fallo desconocido"
                self.signals.log_message.emit(
                    "  %s ✗ ERROR — %d frames fallaron: %s" % (
                        self._t(), failed, err_msg[:200]
                    )
                )

            # ── 6. Post-transcode: originales / restauración ──────────
            if ok and not self.test_mode:
                if originals_dir and self.delete_originals:
                    shutil.rmtree(str(originals_dir), ignore_errors=True)
                    self.signals.log_message.emit(
                        "  %s Originals/ eliminado." % self._t()
                    )
                elif temp_src_dir and temp_src_dir.exists():
                    shutil.rmtree(str(temp_src_dir), ignore_errors=True)

            elif not ok and not self.test_mode:
                # Restaurar originales en caso de fallo
                restore_from = originals_dir or temp_src_dir
                if restore_from and restore_from.exists():
                    restored = self._move_exrs(restore_from, item_path)
                    try:
                        restore_from.rmdir()
                    except Exception:
                        pass
                    self.signals.log_message.emit(
                        "  %s ↩ %d originales restaurados." % (self._t(), restored)
                    )

            # Limpiar archivos temporales del manifest
            try:
                manifest_path.unlink(missing_ok=True)
                log_json_path.unlink(missing_ok=True)
            except Exception:
                pass

            stats = {
                "ok":              ok,
                "frame_count":     frame_count,
                "ok_count":        ok_count,
                "elapsed_seconds": elapsed,
                "fps":             fps_rate,
            }
            self.signals.sequence_done.emit(row_i, ok, stats)

            return {"row_i": row_i, "ok": ok, "name": seq_name, **stats}

        except Exception as exc:
            elapsed  = time.perf_counter() - seq_start
            err_msg  = str(exc)
            self.signals.log_message.emit(
                "  %s ✗ EXCEPCIÓN: %s" % (self._t(), err_msg)
            )
            # Intentar restaurar si hay carpeta de buffer
            restore_from = originals_dir or temp_src_dir
            if restore_from and restore_from.exists() and not self.test_mode:
                restored = self._move_exrs(restore_from, item_path)
                try:
                    restore_from.rmdir()
                except Exception:
                    pass
                self.signals.log_message.emit(
                    "  %s ↩ %d originales restaurados (tras excepción)." % (
                        self._t(), restored
                    )
                )
            stats = {"ok": False, "error": err_msg, "elapsed_seconds": elapsed,
                     "frame_count": 0, "ok_count": 0, "fps": 0.0}
            self.signals.sequence_done.emit(row_i, False, stats)
            return {"row_i": row_i, "ok": False, "name": seq_name, **stats}

    # ── File helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _move_exrs(src_dir: Path, dst_dir: Path) -> int:
        """
        Mueve todos los .exr de src_dir a dst_dir.

        Usa os.rename() cuando es posible (misma unidad — operación atómica a nivel OS,
        libera el GIL). Si falla (e.g. unidades distintas), usa shutil.move() como
        fallback.

        Returns:
            Número de archivos movidos.
        """
        import os
        src_path = Path(src_dir)
        dst_path = Path(dst_dir)
        dst_path.mkdir(parents=True, exist_ok=True)
        moved = 0
        for f in sorted(src_path.glob("*.exr")):
            dst = dst_path / f.name
            try:
                os.rename(str(f), str(dst))
            except OSError:
                shutil.move(str(f), str(dst))
            moved += 1
        return moved
