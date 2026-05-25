"""
____________________________________________________________________

  LGA_NKS_TaskMismatchDialog v1.00 | Lega

  Ventana de advertencia compartida para cuando la task detectada en
  el filename de un clip NO coincide con el nombre del track donde
  está ubicado. La función principal es show_task_mismatch_warning().
  No bloquea ni modifica el procesamiento: solo informa al usuario.

  Usado por runtime activo:
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Pull.py
  - LGA_NKS_Flow_Panel_py/LGA_NKS_Flow_Push.py

  Convención de nombres de tracks: docs/Docu_Logica_Nombres_Tracks.md

  v1.00: Versión inicial
____________________________________________________________________
"""

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore, Qt


def collect_task_mismatches(selected_clips, seq, task_exr_tracks, extract_task_name, clean_base_name, debug_log=None):
    """
    Recorre los clips y devuelve los que tienen inconsistencia entre la task del
    filename y el nombre del track donde están ubicados.

    Args:
        selected_clips: lista de TrackItems a chequear.
        seq: Sequence activa (para resolver el track de cada clip).
        task_exr_tracks: lista de nombres de tracks de task (TASK_EXR_TRACKS).
        extract_task_name: función que extrae la task del base_name (del módulo NamingUtils).
        clean_base_name: función que limpia el filename (del módulo NamingUtils).

    Returns:
        Lista de dicts con claves: 'clip', 'task', 'track'. Puede estar vacía.
    """
    import os
    import hiero.core

    def _dlog(msg):
        if debug_log:
            try:
                debug_log(msg)
            except Exception:
                pass

    _dlog(f"[MismatchFn] version=v1.1 guid-matching selected={len(selected_clips)}")

    # Mapa identidad -> nombre del track. Usamos guid() cuando existe
    # porque Hiero puede devolver wrappers distintos (id() cambia) para el mismo TrackItem.
    def _key(item):
        try:
            g = item.guid()
            if g:
                return ("guid", g)
        except Exception:
            pass
        return ("id", id(item))

    clip_track_map = {}
    for track in seq.videoTracks():
        for item in track.items():
            clip_track_map[_key(item)] = track.name()

    mismatches = []
    seen_keys = set()  # evita reportar el mismo clip dos veces
    for clip in selected_clips:
        if isinstance(clip, hiero.core.EffectTrackItem):
            continue
        k = _key(clip)
        if k in seen_keys:
            continue
        seen_keys.add(k)

        track_name = clip_track_map.get(k)
        if track_name is None:
            # Fallback: intentar via parentTrack()
            try:
                parent = clip.parentTrack()
                if parent is not None:
                    track_name = parent.name()
            except Exception:
                track_name = None
        _dlog(f"[MismatchFn] clip='{clip.name()}' track_resuelto='{track_name}'")
        if track_name is None or track_name not in task_exr_tracks:
            _dlog(f"[MismatchFn]   -> skip (track None o fuera de TASK_EXR_TRACKS)")
            continue  # solo nos interesan clips en tracks de task

        try:
            fileinfos = clip.source().mediaSource().fileinfos()
            if not fileinfos:
                _dlog(f"[MismatchFn]   -> skip (sin fileinfos)")
                continue
            filename = os.path.basename(fileinfos[0].filename())
            base_name = clean_base_name(filename)
            task_from_name = extract_task_name(base_name)
            _dlog(f"[MismatchFn]   filename='{filename}' task_from_name='{task_from_name}'")
            if not task_from_name:
                continue
            task_from_name = task_from_name.lower()
            expected_track = f"_{task_from_name}_"
            _dlog(f"[MismatchFn]   expected_track='{expected_track}' vs track='{track_name}' -> match={expected_track == track_name}")
            if expected_track != track_name:
                mismatches.append({
                    "clip": clip.name(),
                    "task": task_from_name,
                    "track": track_name,
                })
        except Exception as _e:
            _dlog(f"[MismatchFn]   -> excepcion: {_e}")
            continue

    return mismatches


def show_task_mismatch_warning(mismatches, parent=None):
    """
    Muestra una ventana modal listando los clips donde la task del filename
    no coincide con el track. Si la lista está vacía, no hace nada.
    """
    if not mismatches:
        return

    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Task / Track Mismatch")
    dialog.setModal(True)

    layout = QtWidgets.QVBoxLayout(dialog)

    header = QtWidgets.QLabel(
        "Se encontraron clips donde la <b>task del filename</b> no coincide con el "
        "<b>nombre del track</b> donde el clip está ubicado.<br>"
        "Revisá si hay que renombrar el clip o moverlo de track."
    )
    header.setWordWrap(True)
    layout.addWidget(header)

    table = QtWidgets.QTableWidget(len(mismatches), 3, dialog)
    table.setHorizontalHeaderLabels(["Clip", "Task (filename)", "Track"])
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    for row, m in enumerate(mismatches):
        table.setItem(row, 0, QtWidgets.QTableWidgetItem(m.get("clip", "")))
        task_item = QtWidgets.QTableWidgetItem(f"_{m.get('task', '')}_")
        task_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 1, task_item)
        track_item = QtWidgets.QTableWidgetItem(m.get("track", ""))
        track_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 2, track_item)

    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
    btn_box.rejected.connect(dialog.reject)
    btn_box.accepted.connect(dialog.accept)
    layout.addWidget(btn_box)

    # Tamaño inicial razonable
    header_w = table.verticalHeader().width() + 40
    for i in range(table.columnCount()):
        header_w += table.columnWidth(i) + 20
    rows_h = table.horizontalHeader().height() + 20
    for i in range(table.rowCount()):
        rows_h += table.rowHeight(i) + 4
    dialog.resize(min(header_w, 900), min(rows_h + 160, 600))

    dialog.exec_() if hasattr(dialog, "exec_") else dialog.exec()
