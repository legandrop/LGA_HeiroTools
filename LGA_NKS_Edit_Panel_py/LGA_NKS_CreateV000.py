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
RANGE_SOURCE_EDITREF = "editref"
RANGE_SOURCE_PLATE = "plate"

CURRENT_DIR = Path(__file__).resolve().parent
STARTUP_DIR = CURRENT_DIR.parent
SHARED_DIR = STARTUP_DIR / "LGA_NKS_Shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(STARTUP_DIR))

from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtGui, QtCore
from LGA_NKS_Flow_NamingUtils import clean_base_name, extract_project_name, extract_shot_code
from LGA_NKS_GetClip import find_clip_at_playhead_in_track
from LGA_NKS_TaskSelectionDialog import track_for_task
from LGA_NKS_Flow_Task_Config import get_task_color


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


def _is_plate_track(track_name):
    return bool(re.search(r"plate$", track_name, flags=re.IGNORECASE))


def _is_editref_track(track_name):
    return bool(re.search(r"editref", track_name, flags=re.IGNORECASE))


def _range_source_from_clip(track_name, track_index, clip, source_type):
    media_path = _clip_media_path(clip)
    width, height = _plate_resolution(clip) if source_type == RANGE_SOURCE_PLATE else (None, None)
    return {
        "track_name": track_name,
        "track_index": track_index,
        "source_type": source_type,
        "clip": clip,
        "clip_name": clip.name(),
        "timeline_in": int(clip.timelineIn()),
        "timeline_out": int(clip.timelineOut()),
        "frame_count": _frame_count(clip.timelineIn(), clip.timelineOut()),
        "width": width,
        "height": height,
        "media_path": media_path,
    }


def _collect_range_sources(seq, current_time):
    tracks = list(seq.videoTracks())
    editrefs = []
    plates = []

    # Hiero usually exposes tracks bottom-to-top; reverse keeps the visual top first.
    for track_index, track in reversed(list(enumerate(tracks))):
        track_name = track.name()
        if _is_editref_track(track_name):
            source_type = RANGE_SOURCE_EDITREF
        elif _is_plate_track(track_name):
            source_type = RANGE_SOURCE_PLATE
        else:
            continue

        clip = _find_clip_at_time(track, current_time)
        if not clip:
            continue

        source = _range_source_from_clip(track_name, track_index, clip, source_type)
        if source_type == RANGE_SOURCE_EDITREF:
            editrefs.append(source)
        else:
            plates.append(source)

    return editrefs + plates, plates


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

    range_sources, plates = _collect_range_sources(seq, current_time)
    if not range_sources:
        return None, "No editref or plate tracks found."
    if not plates:
        return None, "No plate tracks found."

    default_plate = plates[0]
    shot_root = _derive_shot_root(default_plate["media_path"])
    shot_code = _derive_shot_code(default_plate["clip"], shot_root)
    if not shot_code:
        return None, "Could not detect shot."

    width, height = _timeline_resolution(seq)
    try:
        project_name = extract_project_name(clean_base_name(_clip_file_name(default_plate["clip"]))) or ""
    except Exception:
        project_name = ""
    return {
        "sequence": seq,
        "shot_code": shot_code,
        "project_name": project_name,
        "shot_root_path": shot_root,
        "range_sources": range_sources,
        "plates": plates,
        "timeline_resolution": (width, height),
        "existing_versions_by_task": _existing_versions_by_task(seq),
    }, None


class CreateV000Dialog(QtWidgets.QDialog):
    def __init__(self, context, parent=None):
        super(CreateV000Dialog, self).__init__(parent)
        self.context = context
        self.plate_checks = []
        self._syncing_range_checks = False
        self.resolution_buttons = {}
        self.task_buttons = {}
        self.selected_task = None
        self.selected_resolution = None

        self.setWindowTitle("Create v000 - %s" % context["shot_code"])
        self.setMinimumWidth(720)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2B2B2B;
                border: 1px solid #555555;
            }
            """
        )
        self._build_ui()
        self._select_default_task()
        self._update_state()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        project_name = self.context.get("project_name") or ""
        shot_code = self.context.get("shot_code") or ""
        if project_name:
            info_text = (
                "<span style='color:#6AB5CA;'>%s</span> / "
                "<span style='color:#B56AB5;'>%s</span>"
            ) % (project_name, shot_code)
        else:
            info_text = "<span style='color:#B56AB5;'>%s</span>" % shot_code

        header_row = QtWidgets.QHBoxLayout()
        info_label = QtWidgets.QLabel(info_text)
        info_label.setTextFormat(QtCore.Qt.RichText)
        info_label.setStyleSheet(
            "color: #CCCCCC; padding: 2px 5px 0px 5px; font-size: 14px; font-weight: bold;"
        )
        header_row.addWidget(info_label, 0, QtCore.Qt.AlignLeft)
        header_row.addStretch()
        title = QtWidgets.QLabel("Create v000")
        title.setStyleSheet(
            "color: #CCCCCC; padding: 2px 5px 0px 5px; font-size: 14px; font-weight: bold;"
        )
        header_row.addWidget(title, 0, QtCore.Qt.AlignRight)
        layout.addLayout(header_row)

        self.warning_label = QtWidgets.QLabel("")
        self.warning_label.setStyleSheet("color: #d9a441; padding: 2px 5px;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(16)

        frame_range_col = QtWidgets.QVBoxLayout()
        frame_range_col.addWidget(self._section_label("FRAME RANGE"))
        frame_range_col.addWidget(self._build_plates_table())
        frame_range_col.addStretch()
        top_row.addLayout(frame_range_col, 1)
        top_row.addWidget(self._build_separator("v"))

        resolution_col = QtWidgets.QVBoxLayout()
        resolution_col.addWidget(self._section_label("RESOLUTION"))
        resolution_col.addWidget(self._build_resolution_box())
        resolution_col.addStretch()
        top_row.addLayout(resolution_col, 1)
        layout.addLayout(top_row)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        middle_row = QtWidgets.QHBoxLayout()
        middle_row.setSpacing(16)

        handle_col = QtWidgets.QVBoxLayout()
        handle_col.addWidget(self._section_label("HANDLE"))
        handle_col.addWidget(self._build_handle_box())
        handle_col.addStretch()
        middle_row.addLayout(handle_col, 1)
        middle_row.addWidget(self._build_separator("v"))

        task_col = QtWidgets.QVBoxLayout()
        task_col.addWidget(self._section_label("TASK"))
        task_col.addWidget(self._build_task_box())
        task_col.addStretch()
        middle_row.addLayout(task_col, 1)
        layout.addLayout(middle_row)

        layout.addSpacing(5)
        layout.addWidget(self._build_separator())
        layout.addSpacing(5)

        layout.addWidget(self._section_label("OUTPUT"))
        self.output_text = QtWidgets.QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(128)
        self.output_text.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 5px;
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(self.output_text)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #CCCCCC;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #666666; }
            """
        )
        self.create_btn = QtWidgets.QPushButton("Create v000")
        self.create_btn.clicked.connect(self._create_v000)
        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #443a91;
                color: #b2b2b2;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #774dcb; color: #CCCCCC; }
            QPushButton:disabled { background-color: #2f2a5e; color: #6a6a6a; }
            """
        )
        buttons.addWidget(cancel_btn)
        buttons.addSpacing(10)
        buttons.addWidget(self.create_btn)
        layout.addLayout(buttons)

    def _section_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding-top: 5px;")
        return label

    def _build_separator(self, orientation="h"):
        sep = QtWidgets.QFrame()
        if orientation == "v":
            sep.setFrameShape(QtWidgets.QFrame.VLine)
        else:
            sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        sep.setStyleSheet("color: #444444; margin: 0px;")
        return sep

    def _build_plates_table(self):
        table = QtWidgets.QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Use", "Track", "TL IN", "TL OUT", "Frames"])
        table.setRowCount(len(self.context["range_sources"]))
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        table.setShowGrid(False)
        table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        table.setStyleSheet(
            """
            QTableWidget {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                gridline-color: #333333;
            }
            QHeaderView::section {
                background-color: #2B2B2B;
                color: #999999;
                padding: 4px 8px;
                border: 0px;
                border-bottom: 1px solid #444444;
                font-weight: bold;
            }
            QTableWidget::item { padding-left: 10px; padding-right: 10px; }
            """
        )

        for row, plate in enumerate(self.context["range_sources"]):
            check = QtWidgets.QCheckBox()
            check.setStyleSheet("color: #a7a7a7; padding: 2px;")
            check.setChecked(row == 0)
            check.stateChanged.connect(lambda state, changed_check=check: self._on_range_check_changed(changed_check))
            self.plate_checks.append((check, plate))
            check_container = QtWidgets.QWidget()
            check_layout = QtWidgets.QHBoxLayout(check_container)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(QtCore.Qt.AlignCenter)
            check_layout.addWidget(check)
            table.setCellWidget(row, 0, check_container)
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
        header.setStretchLastSection(False)
        for col in range(4):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)

        row_count = len(self.context["range_sources"])
        row_height = table.verticalHeader().defaultSectionSize()
        table.setMinimumHeight(header.height() + (row_count * row_height) + 2) # extra 2px de altura para que no aparezca el scrollbar (NO CAMBIAR!!)
        table.setMaximumHeight(header.height() + (row_count * row_height) + 2) # extra 2px de altura para que no aparezca el scrollbar (NO CAMBIAR!!)    
        return table

    def _build_resolution_box(self):
        box = QtWidgets.QVBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)

        tw, th = self.context["timeline_resolution"]
        timeline_text = "Timeline    %s x %s" % (tw or "N/A", th or "N/A")
        timeline_btn = QtWidgets.QRadioButton(timeline_text)
        timeline_btn.setStyleSheet("color: #a7a7a7; padding: 2px;")
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
            btn.setStyleSheet("color: #a7a7a7; padding: 2px;")
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

    def _build_handle_box(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)

        self.handle_value = 4
        handle_style = """
            QPushButton {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 2px 0px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
                color: #cfcfcf;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #232323;
                border: 1px solid #303030;
                color: #555555;
            }
        """

        self.handle_down_btn = QtWidgets.QPushButton("▼")
        self.handle_down_btn.setFixedSize(22, 24)
        self.handle_down_btn.setStyleSheet(
            handle_style
            + """
            QPushButton {
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-right: 0px;
            }
            """
        )
        self.handle_down_btn.clicked.connect(lambda: self._step_handle(-1))

        self.handle_value_label = QtWidgets.QLineEdit(str(self.handle_value))
        self.handle_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.handle_value_label.setReadOnly(True)
        self.handle_value_label.setFixedSize(30, 24)
        self.handle_value_label.setStyleSheet(
            """
            QLineEdit {
                background-color: #272727;
                border: 1px solid #333333;
                color: #a7a7a7;
                padding: 2px 0px;
                selection-background-color: #cfcfcf;
                selection-color: #2B2B2B;
            }
            QLineEdit:disabled {
                background-color: #232323;
                border: 1px solid #303030;
                color: #555555;
            }
            """
        )

        self.handle_up_btn = QtWidgets.QPushButton("▲")
        self.handle_up_btn.setFixedSize(22, 24)
        self.handle_up_btn.setStyleSheet(
            handle_style
            + """
            QPushButton {
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: 0px;
            }
            """
        )
        self.handle_up_btn.clicked.connect(lambda: self._step_handle(1))

        layout.addWidget(self.handle_down_btn)
        layout.addWidget(self.handle_value_label)
        layout.addWidget(self.handle_up_btn)
        layout.addStretch()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def _step_handle(self, delta):
        if not self.handle_up_btn.isEnabled():
            return
        self.handle_value = max(0, min(99, self.handle_value + delta))
        self.handle_value_label.setText(str(self.handle_value))
        self._update_state()

    def _build_task_box(self):
        layout = QtWidgets.QHBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        existing = self.context["existing_versions_by_task"]

        for task in TASKS:
            btn = QtWidgets.QPushButton(task)
            btn.setCheckable(True)
            btn.setMinimumWidth(90)
            task_color = get_task_color(task, fallback="#3B9ACA")
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #2B2B2B;
                    border: 1px solid #444444;
                    color: %(color)s;
                    padding: 6px 14px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover:!checked:!disabled {
                    background-color: #333333;
                }
                QPushButton:checked {
                    background-color: #3a3a3a;
                    color: %(color)s;
                    border: 1px solid %(color)s;
                }
                QPushButton:disabled {
                    background-color: #232323;
                    color: #555555;
                    border: 1px solid #333333;
                }
                """
                % {"color": task_color}
            )
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

    def _on_range_check_changed(self, changed_check):
        if self._syncing_range_checks:
            return

        changed_source = None
        for check, source in self.plate_checks:
            if check is changed_check:
                changed_source = source
                break

        if changed_check.isChecked() and changed_source:
            selected_type = changed_source["source_type"]
            self._syncing_range_checks = True
            try:
                for check, source in self.plate_checks:
                    if check is changed_check:
                        continue
                    if source["source_type"] != selected_type:
                        check.setChecked(False)
            finally:
                self._syncing_range_checks = False

        self._update_state()

    def _selected_plates(self):
        return [plate for check, plate in self.plate_checks if check.isChecked()]

    def _selected_range_uses_editref(self):
        return any(
            source["source_type"] == RANGE_SOURCE_EDITREF
            for check, source in self.plate_checks
            if check.isChecked()
        )

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

        base_timeline_in = min(p["timeline_in"] for p in plates)
        base_timeline_out = max(p["timeline_out"] for p in plates)
        handle = self.handle_value if self._selected_range_uses_editref() else 0
        timeline_in = base_timeline_in - handle
        timeline_out = base_timeline_out + handle
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
            "selected_range_sources": [
                {
                    "track_name": p["track_name"],
                    "source_type": p["source_type"],
                }
                for p in plates
            ],
            "selected_plates": [p["track_name"] for p in plates],
            "base_timeline_in": base_timeline_in,
            "base_timeline_out": base_timeline_out,
            "handle": handle,
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

    def _set_warning(self, message):
        if message:
            self.warning_label.setText(message)
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setText("")
            self.warning_label.setVisible(False)

    def _set_handle_enabled(self, enabled):
        self.handle_down_btn.setEnabled(enabled)
        self.handle_up_btn.setEnabled(enabled)
        self.handle_value_label.setEnabled(enabled)
        if not enabled and self.handle_value != 0:
            self.handle_value = 0
            self.handle_value_label.setText("0")

    def _update_state(self, *args):
        self._set_handle_enabled(self._selected_range_uses_editref())

        task = self._selected_task()
        if not task and all(not btn.isEnabled() for btn in self.task_buttons.values()):
            warning = "All tasks already have versions in timeline."
            self._set_warning(warning)
            self.create_btn.setEnabled(False)
            self.output_text.setPlainText(warning)
            return

        params, warning = self._build_output()
        if warning:
            self._set_warning(warning)
            self.create_btn.setEnabled(False)
            self.output_text.setPlainText(warning)
            return

        self._set_warning("")
        self.create_btn.setEnabled(True)
        self.output_text.setPlainText(
            "Path: {output_dir}\n"
            "Name: {output_name_pattern}\n"
            "Timeline: {timeline_in} - {timeline_out} (handle {handle})\n"
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
            self._set_warning(warning)
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
