"""
Create v000 dialog for Hiero/Nuke Studio.

Phase 1 only: validates context, previews output params and prints the collected
dictionary. It does not write EXR files.
"""

import os
import re
import sys
from pathlib import Path

import hiero.core
import hiero.ui

START_FRAME = 1001
VERSION = "v000"
TASKS = ("comp", "roto", "cleanup")
TASK_FOLDER = {
    "comp": "Comp",
    "roto": "Roto",
    "cleanup": "Cleanup",
}

CURRENT_DIR = Path(__file__).resolve().parent
STARTUP_DIR = CURRENT_DIR.parent
SHARED_DIR = STARTUP_DIR / "LGA_NKS_Shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(STARTUP_DIR))

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore
from LGA_NKS_Flow_NamingUtils import clean_base_name, extract_shot_code
from LGA_NKS_GetClip import find_clip_at_playhead_in_track
from LGA_NKS_TaskSelectionDialog import track_for_task


def debug_print(*message):
    print("[Create v000]", *message)


def _current_time():
    viewer = hiero.ui.currentViewer()
    if not viewer:
        return None
    try:
        return viewer.time()
    except Exception:
        player = viewer.player() if hasattr(viewer, "player") else None
        return player.time() if player else None


def _clip_media_path(clip):
    try:
        fileinfos = clip.source().mediaSource().fileinfos()
        if fileinfos:
            return fileinfos[0].filename()
    except Exception:
        pass
    return ""


def _clip_file_name(clip):
    return os.path.basename(_clip_media_path(clip).replace("\\", "/"))


def _frame_count(timeline_in, timeline_out):
    return max(0, int(timeline_out) - int(timeline_in))


def _extract_version_label(value):
    if not value:
        return None
    match = re.search(r"_v(\d+)(?:[-_(.]|$)", value, flags=re.IGNORECASE)
    if match:
        return "v%s" % match.group(1).zfill(3)
    match = re.search(r"\bv(\d+)\b", value, flags=re.IGNORECASE)
    if match:
        return "v%s" % match.group(1).zfill(3)
    return None


def _clip_version_label(clip):
    candidates = []
    for getter in (
        lambda: _clip_file_name(clip),
        lambda: clip.name(),
        lambda: clip.source().binItem().activeVersion().name(),
    ):
        try:
            value = getter()
            if value:
                candidates.append(value)
        except Exception:
            pass

    for value in candidates:
        version = _extract_version_label(value)
        if version:
            return version
    return "existing"


def _timeline_resolution(seq):
    try:
        fmt = seq.format()
        return int(fmt.width()), int(fmt.height())
    except Exception:
        return None, None


def _call_int_method(obj, names):
    for name in names:
        if not hasattr(obj, name):
            continue
        try:
            value = getattr(obj, name)()
            if value:
                return int(value)
        except Exception:
            pass
    return None


def _metadata_resolution(metadata):
    if not metadata:
        return None, None

    width_keys = (
        "foundry.source.width",
        "input/width",
        "exr/displayWindow/width",
        "exr/dataWindow/width",
        "width",
    )
    height_keys = (
        "foundry.source.height",
        "input/height",
        "exr/displayWindow/height",
        "exr/dataWindow/height",
        "height",
    )

    def read(keys):
        for key in keys:
            try:
                value = metadata.get(key)
            except Exception:
                value = metadata[key] if key in metadata else None
            if value:
                try:
                    return int(float(value))
                except Exception:
                    pass
        return None

    return read(width_keys), read(height_keys)


def _plate_resolution(clip):
    try:
        source = clip.source()
        media_source = source.mediaSource()
    except Exception:
        return None, None

    for obj in (source, media_source):
        width = _call_int_method(obj, ("width",))
        height = _call_int_method(obj, ("height",))
        if width and height:
            return width, height

    try:
        metadata = media_source.metadata()
        width, height = _metadata_resolution(metadata)
        if width and height:
            return width, height
    except Exception:
        pass

    try:
        fileinfos = media_source.fileinfos()
        for fileinfo in fileinfos:
            width = _call_int_method(fileinfo, ("width",))
            height = _call_int_method(fileinfo, ("height",))
            if width and height:
                return width, height
    except Exception:
        pass

    return None, None


def _derive_shot_root(media_path):
    normalized = media_path.replace("\\", "/")
    parts = normalized.split("/")
    input_index = None
    for index, part in enumerate(parts):
        if part.lower() == "_input":
            input_index = index
            break
    if input_index is None or input_index == 0:
        return None
    return "/".join(parts[:input_index])


def _derive_shot_code(clip, shot_root):
    file_name = _clip_file_name(clip)
    base_name = clean_base_name(file_name)
    shot_code = extract_shot_code(base_name)
    if shot_code:
        return shot_code
    if shot_root:
        return os.path.basename(shot_root.rstrip("/\\"))
    try:
        return clip.name()
    except Exception:
        return ""


def _find_clip_at_time(track, current_time):
    if current_time is None:
        return None
    for item in track.items():
        if isinstance(item, hiero.core.EffectTrackItem):
            continue
        try:
            if item.timelineIn() <= current_time < item.timelineOut():
                return item
        except Exception:
            pass
    return None


def _collect_plates(seq, current_time):
    tracks = list(seq.videoTracks())
    plates = []

    # Hiero usually exposes tracks bottom-to-top; reverse keeps the visual top first.
    for track_index, track in reversed(list(enumerate(tracks))):
        track_name = track.name()
        if not re.search(r"plate$", track_name, flags=re.IGNORECASE):
            continue
        clip = _find_clip_at_time(track, current_time)
        if not clip:
            continue
        media_path = _clip_media_path(clip)
        width, height = _plate_resolution(clip)
        plates.append(
            {
                "track_name": track_name,
                "track_index": track_index,
                "clip": clip,
                "clip_name": clip.name(),
                "timeline_in": int(clip.timelineIn()),
                "timeline_out": int(clip.timelineOut()),
                "frame_count": _frame_count(clip.timelineIn(), clip.timelineOut()),
                "width": width,
                "height": height,
                "media_path": media_path,
            }
        )
    return plates


def _existing_versions_by_task(seq):
    versions = {}
    for task in TASKS:
        clip = find_clip_at_playhead_in_track(seq, track_for_task(task))
        versions[task] = _clip_version_label(clip) if clip else None
    return versions


def _collect_context():
    seq = hiero.ui.activeSequence()
    if not seq:
        return None, "No active sequence."

    current_time = _current_time()
    if current_time is None:
        return None, "No active viewer/playhead."

    plates = _collect_plates(seq, current_time)
    if not plates:
        return None, "No plate tracks found."

    default_plate = plates[0]
    shot_root = _derive_shot_root(default_plate["media_path"])
    shot_code = _derive_shot_code(default_plate["clip"], shot_root)
    if not shot_code:
        return None, "Could not detect shot."

    width, height = _timeline_resolution(seq)
    return {
        "sequence": seq,
        "shot_code": shot_code,
        "shot_root_path": shot_root,
        "plates": plates,
        "timeline_resolution": (width, height),
        "existing_versions_by_task": _existing_versions_by_task(seq),
    }, None


class CreateV000Dialog(QtWidgets.QDialog):
    def __init__(self, context, parent=None):
        super(CreateV000Dialog, self).__init__(parent)
        self.context = context
        self.plate_checks = []
        self.resolution_buttons = {}
        self.task_buttons = {}
        self.selected_task = None
        self.selected_resolution = None

        self.setWindowTitle("Create v000 - %s" % context["shot_code"])
        self.setMinimumWidth(620)
        self._build_ui()
        self._select_default_task()
        self._update_state()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Create v000 - %s" % self.context["shot_code"])
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #e6e6e6;")
        layout.addWidget(title)

        self.warning_label = QtWidgets.QLabel("")
        self.warning_label.setStyleSheet("color: #d9a441;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        layout.addWidget(self._section_label("FRAME RANGE"))
        layout.addWidget(self._build_plates_table())
        self.range_label = QtWidgets.QLabel("")
        layout.addWidget(self.range_label)

        layout.addWidget(self._section_label("RESOLUTION"))
        layout.addWidget(self._build_resolution_box())

        layout.addWidget(self._section_label("TASK"))
        layout.addWidget(self._build_task_box())

        layout.addWidget(self._section_label("OUTPUT"))
        self.output_text = QtWidgets.QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(128)
        self.output_text.setStyleSheet(
            "QPlainTextEdit { background: #1f1f1f; color: #d8d8d8; border: 1px solid #3c3c3c; }"
        )
        layout.addWidget(self.output_text)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self.create_btn = QtWidgets.QPushButton("Create v000")
        self.create_btn.clicked.connect(self._create_v000)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self.create_btn)
        layout.addLayout(buttons)

    def _section_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #c9c9c9;")
        return label

    def _build_plates_table(self):
        table = QtWidgets.QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Use", "Track", "TL IN", "TL OUT", "Frames"])
        table.setRowCount(len(self.context["plates"]))
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setMaximumHeight(34 + (len(self.context["plates"]) * 26))

        for row, plate in enumerate(self.context["plates"]):
            check = QtWidgets.QCheckBox()
            check.setChecked(row == 0)
            check.stateChanged.connect(self._update_state)
            self.plate_checks.append((check, plate))
            table.setCellWidget(row, 0, check)
            values = (
                plate["track_name"],
                str(plate["timeline_in"]),
                str(plate["timeline_out"]),
                str(plate["frame_count"]),
            )
            for col, value in enumerate(values, start=1):
                item = QtWidgets.QTableWidgetItem(value)
                table.setItem(row, col, item)

        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        for col in range(4):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        return table

    def _build_resolution_box(self):
        box = QtWidgets.QVBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)

        tw, th = self.context["timeline_resolution"]
        timeline_text = "Timeline    %s x %s" % (tw or "N/A", th or "N/A")
        timeline_btn = QtWidgets.QRadioButton(timeline_text)
        timeline_btn.setChecked(True)
        timeline_btn.toggled.connect(self._update_state)
        group.addButton(timeline_btn)
        self.resolution_buttons[timeline_btn] = {
            "source": "Timeline",
            "width": tw,
            "height": th,
        }
        box.addWidget(timeline_btn)

        for plate in self.context["plates"]:
            width, height = plate["width"], plate["height"]
            text = "%s    %s x %s" % (
                plate["track_name"],
                width or "N/A",
                height or "N/A",
            )
            btn = QtWidgets.QRadioButton(text)
            btn.setEnabled(bool(width and height))
            btn.toggled.connect(self._update_state)
            group.addButton(btn)
            self.resolution_buttons[btn] = {
                "source": plate["track_name"],
                "width": width,
                "height": height,
            }
            box.addWidget(btn)

        container = QtWidgets.QWidget()
        container.setLayout(box)
        return container

    def _build_task_box(self):
        layout = QtWidgets.QHBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        existing = self.context["existing_versions_by_task"]

        for task in TASKS:
            btn = QtWidgets.QPushButton(task)
            btn.setCheckable(True)
            btn.setMinimumWidth(90)
            if existing.get(task):
                btn.setEnabled(False)
                btn.setToolTip("%s disabled - existing %s" % (task, existing[task]))
            btn.toggled.connect(self._update_state)
            group.addButton(btn)
            self.task_buttons[task] = btn
            layout.addWidget(btn)
        layout.addStretch()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def _select_default_task(self):
        for task in TASKS:
            btn = self.task_buttons[task]
            if btn.isEnabled():
                btn.setChecked(True)
                return

    def _selected_plates(self):
        return [plate for check, plate in self.plate_checks if check.isChecked()]

    def _selected_task(self):
        for task, btn in self.task_buttons.items():
            if btn.isChecked():
                return task
        return None

    def _selected_resolution_info(self):
        for btn, info in self.resolution_buttons.items():
            if btn.isChecked():
                return info
        return None

    def _build_output(self):
        plates = self._selected_plates()
        task = self._selected_task()
        resolution = self._selected_resolution_info()
        shot_root = self.context["shot_root_path"]
        shot_code = self.context["shot_code"]

        if not plates or not task or not resolution:
            return None, "Select at least one plate."
        if not shot_root:
            return None, "Could not derive shot root from _input path."
        if not resolution.get("width") or not resolution.get("height"):
            return None, "Selected resolution is unavailable."

        timeline_in = min(p["timeline_in"] for p in plates)
        timeline_out = max(p["timeline_out"] for p in plates)
        frame_count = _frame_count(timeline_in, timeline_out)
        if frame_count <= 0:
            return None, "Invalid frame range."

        source_first = START_FRAME
        source_last = START_FRAME + frame_count - 1
        version_name = "%s_%s_%s" % (shot_code, task, VERSION)
        output_dir = "/".join(
            [
                shot_root.rstrip("/\\"),
                TASK_FOLDER[task],
                "4_publish",
                version_name,
            ]
        )

        return {
            "shot_code": shot_code,
            "task": task,
            "selected_plates": [p["track_name"] for p in plates],
            "timeline_in": timeline_in,
            "timeline_out": timeline_out,
            "frame_count": frame_count,
            "source_first_frame": source_first,
            "source_last_frame": source_last,
            "resolution": (resolution["width"], resolution["height"]),
            "resolution_source": resolution["source"],
            "output_dir": output_dir,
            "output_name_pattern": "%s_####.exr" % version_name,
        }, None

    def _update_state(self, *args):
        task = self._selected_task()
        if not task and all(not btn.isEnabled() for btn in self.task_buttons.values()):
            warning = "All tasks already have versions in timeline."
            self.warning_label.setText(warning)
            self.create_btn.setEnabled(False)
            self.output_text.setPlainText(warning)
            return

        params, warning = self._build_output()
        if warning:
            self.warning_label.setText(warning)
            self.create_btn.setEnabled(False)
            self.output_text.setPlainText(warning)
            self.range_label.setText("")
            return

        self.warning_label.setText("")
        self.create_btn.setEnabled(True)
        self.range_label.setText(
            "v000 timeline range: {timeline_in} - {timeline_out} ({frame_count} frames)\n"
            "v000 source range:   {source_first_frame} - {source_last_frame}".format(**params)
        )
        self.output_text.setPlainText(
            "Path: {output_dir}\n"
            "Name: {output_name_pattern}\n"
            "Frames: {source_first_frame} - {source_last_frame} ({frame_count} frames)\n"
            "Resolution: {0} x {1} ({resolution_source})".format(
                params["resolution"][0],
                params["resolution"][1],
                **params
            )
        )

    def _create_v000(self):
        params, warning = self._build_output()
        if warning:
            self.warning_label.setText(warning)
            return
        debug_print("params:", params)
        self.accept()


def open_create_v000_dialog():
    context, error = _collect_context()
    if error:
        QtWidgets.QMessageBox.warning(None, "Create v000", error)
        debug_print(error)
        return None

    dialog = CreateV000Dialog(context)
    result = dialog.exec_()
    return result


def main():
    return open_create_v000_dialog()


if __name__ == "__main__":
    main()
