"""
____________________________________________________________________________________

  LGA_NKS_TaskSelectionDialog v1.0 | Lega
  Detección y selección de task entre los tracks EXR del playhead.

  Pensado como helper compartido para herramientas que actúan sobre una sola task
  por ejecución (Shot_info, Push, ReviewPic). Si en la posición del playhead hay
  clips de más de un track de task (`_comp_`, `_roto_`, `_cleanup_`), pide al
  usuario que elija; si hay solo una, la devuelve automáticamente.

  API pública:
  - get_tasks_at_playhead(seq) -> list[str]
  - track_for_task(task_name) -> str | None
  - prompt_task_selection(task_names, title="Select task") -> str | None
  - resolve_task_at_playhead(seq, title="Select task") -> str | None

  Convención de nombres de tracks: docs/Docu_Logica_Nombres_Tracks.md
____________________________________________________________________________________
"""

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore
from LGA_NKS_Shared.LGA_NKS_GetClip import (
    TASK_EXR_TRACKS,
    TRACK_comp_EXR,
    TRACK_roto_EXR,
    TRACK_cleanup_EXR,
    find_clip_at_playhead_in_track,
)


_TASK_TO_TRACK = {
    "comp": TRACK_comp_EXR,
    "roto": TRACK_roto_EXR,
    "cleanup": TRACK_cleanup_EXR,
}

_TRACK_TO_TASK = {v: k for k, v in _TASK_TO_TRACK.items()}


def track_for_task(task_name):
    """Devuelve el nombre de track EXR para una task ('comp'/'roto'/'cleanup')."""
    return _TASK_TO_TRACK.get(task_name.lower()) if task_name else None


def get_tasks_at_playhead(seq):
    """Lista las tasks (lowercase) que tienen un clip en el playhead.

    Recorre TASK_EXR_TRACKS en orden y devuelve solo las tasks cuyos tracks
    tienen un clip activo en la posición del playhead.
    """
    tasks = []
    for track_name in TASK_EXR_TRACKS:
        if find_clip_at_playhead_in_track(seq, track_name) is not None:
            task = _TRACK_TO_TASK.get(track_name)
            if task:
                tasks.append(task)
    return tasks


def prompt_task_selection(task_names, title="Select task"):
    """Muestra un diálogo modal con un botón por task y devuelve la elegida.

    Si la lista trae una sola task, la devuelve sin mostrar UI.
    Devuelve None si el usuario cierra el diálogo sin elegir.
    """
    if not task_names:
        return None
    if len(task_names) == 1:
        return task_names[0]

    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle(title)
    dialog.setModal(True)

    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setSpacing(8)
    layout.setContentsMargins(16, 16, 16, 16)

    label = QtWidgets.QLabel(title)
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setStyleSheet("font-weight: bold; font-size: 13px;")
    layout.addWidget(label)

    state = {"task": None}

    def make_handler(task):
        def handler():
            state["task"] = task
            dialog.accept()
        return handler

    for task in task_names:
        btn = QtWidgets.QPushButton(task)
        btn.setMinimumHeight(28)
        btn.clicked.connect(make_handler(task))
        layout.addWidget(btn)

    dialog.exec_()
    return state["task"]


def resolve_task_at_playhead(seq, title="Select task"):
    """Resuelve la task a usar en función del playhead.

    - 0 tasks bajo el playhead -> None
    - 1 task -> esa task
    - >1 tasks -> abre prompt y devuelve la elegida (o None si se canceló)
    """
    tasks = get_tasks_at_playhead(seq)
    if not tasks:
        return None
    if len(tasks) == 1:
        return tasks[0]
    return prompt_task_selection(tasks, title=title)
