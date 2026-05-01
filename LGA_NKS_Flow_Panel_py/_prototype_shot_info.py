"""
Prototipo standalone de Shot Info imitando la UI de PipeSync (FlowNotesPopover).

Uso:
    set QT_QPA_PLATFORM=offscreen
    python _prototype_shot_info.py --screenshot preview.png
    python _prototype_shot_info.py            # modo interactivo

Datos hardcodeados del shot ERSO_000_320 (Comp), tomados de pipesync.db.
NO usar en produccion. Es solo para iterar visualmente la UI fuera de Nuke.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt


# --------------------------------------------------------------------------- #
# Paleta y constantes (sacadas de PipeSync mainwindow.cpp y flow_notes.qss)
# --------------------------------------------------------------------------- #
COLORS = {
    "bg_principal": "#161616",
    "bg_popover": "#232323",
    "bg_version_container": "#1e1e1e",
    "bg_version_header": "#3C3764",
    "border_principal": "#303030",
    "txt_principal": "#B2B2B2",
    "txt_principal_strong": "#dddddd",
    "txt_secundario": "#929292",
    "txt_subtle": "#cccccc",
    "txt_desc_title": "#d8d8d8",
    "txt_desc_meta": "#b8b8b8",
    "txt_body": "#909090",
    "attachment_label_bg": "#2D2A26",
    "attachment_label_fg": "#8B7355",
}


# --------------------------------------------------------------------------- #
# DateUtils.formatFriendlyDate (port directo del C++ de PipeSync)
# --------------------------------------------------------------------------- #
# -*- coding: utf-8 -*-
_MONTHS_SHORT = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def parse_pipesync_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    iso = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        try:
            dt = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_friendly_date(dt, include_time=False, today=None):
    """Reproduce DateUtils::formatFriendlyDate de PipeSync."""
    if dt is None:
        return "Fecha desconocida"
    if today is None:
        today = datetime.now(dt.tzinfo).date() if dt.tzinfo else datetime.now().date()

    date_day = dt.date()
    days_diff = (today - date_day).days

    if days_diff > 0:
        if days_diff == 1:
            out = "Ayer"
        elif days_diff <= 15:
            out = f"Hace {days_diff} dias"
        else:
            if date_day.year == today.year:
                out = f"{date_day.day} {_MONTHS_SHORT[date_day.month]}"
            else:
                out = f"{date_day.day} {_MONTHS_SHORT[date_day.month]} {date_day.year % 100}"
    elif days_diff == 0:
        out = "Hoy"
    else:
        d = -days_diff
        if d == 1:
            out = "Manana"
        elif d == 2:
            out = "Pasado manana"
        elif d <= 15:
            out = f"Dentro de {d} dias"
        else:
            if date_day.year == today.year:
                out = f"{date_day.day} {_MONTHS_SHORT[date_day.month]}"
            else:
                out = f"{date_day.day} {_MONTHS_SHORT[date_day.month]} {date_day.year % 100}"

    if include_time:
        out += f" a las {dt.strftime('%H:%M')}"
    return out


def format_logged_time(minutes):
    if not minutes or minutes <= 0:
        return ""
    days = minutes / (8.0 * 60.0)
    if days >= 1.0:
        return f"{days:.1f}d"
    hours = minutes / 60.0
    return f"{hours:.1f}h"


# --------------------------------------------------------------------------- #
# Datos hardcodeados (ERSO_000_320 / Comp)
# --------------------------------------------------------------------------- #
TODAY_OVERRIDE = datetime(2026, 4, 30).date()  # para que las fechas se rendericen como en la captura

THUMB_DIR = r"C:\Portable\LGA\PipeSync\cache\notes\ERSO_000_320_Comp_v6"

SHOT_DATA = {
    "shot_code": "ERSO_000_320",
    "task_type": "Comp",
    "assignee": "Ignacio Jamilis",
    "versions": [
        {
            "version_number": 7,
            "created_by": "Ignacio Jamilis",
            "created_on": "2026-03-27 13:41:53-03:00",
            "description": (
                "levantado el matte de las ventanas para recuperar más reflejo y "
                "suciedad, hace más opaco al BG, sobre todo en la ventana de atrás "
                "que estaba con valor 0. virado a frio y un cachito desaturado el "
                "BG. MB al BG."
            ),
            "logged_minutes": 210,
            "notes": [],
        },
        {
            "version_number": 6,
            "created_by": "Ignacio Jamilis",
            "created_on": "2026-03-19 11:41:27-03:00",
            "description": "nuevo BG. el exr anterior salió cropeado o desplazado un par de pixeles",
            "logged_minutes": 40,
            "notes": [
                {
                    "content": (
                        "nachin! agregemos MB al fondo y en la ventana de atras hay "
                        "unos cambios de color medio extraños"
                    ),
                    "created_by": "Juan Olivares",
                    "created_on": "2026-03-20 17:52:19-03:00",
                    "attachment_info": "[]",
                    "local_attachment_paths": "",
                },
                {
                    "content": (
                        "nacho te dejo unas notitas para este shot.\n"
                        "aumentemos un poco la presencia de los reflejos de las "
                        "ventanas y ajustemos el color del fondo para que este un "
                        "poco mas nublado y neutral y no tan calido. esta nota es "
                        "valida para todos los shots. La idea es que todos tengan "
                        "el mismo color."
                    ),
                    "created_by": "Juan Olivares",
                    "created_on": "2026-03-27 08:44:25-03:00",
                    "attachment_info": json.dumps([
                        {"frame": 1080},
                        {"frame": 1080},
                        {"frame": 1080},
                    ]),
                    "local_attachment_paths": ";".join([
                        os.path.join(THUMB_DIR, "ERSO_000_320_Comp_v6_1080.jpg"),
                        os.path.join(THUMB_DIR, "ERSO_000_320_Comp_v6_1080_2.jpg"),
                        os.path.join(THUMB_DIR, "ERSO_000_320_Comp_v6_1080_3.jpg"),
                    ]),
                },
            ],
        },
    ],
}


# --------------------------------------------------------------------------- #
# Widgets
# --------------------------------------------------------------------------- #
class ThumbnailButton(QtWidgets.QPushButton):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setObjectName("flowVersionCommentThumbnail")
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)

        pix = QtGui.QPixmap(image_path)
        if pix.isNull():
            pix = QtGui.QPixmap(150, 80)
            pix.fill(QtGui.QColor("#3a3a3a"))
        else:
            pix = pix.scaledToWidth(150, Qt.SmoothTransformation)
        self.setIcon(QtGui.QIcon(pix))
        self.setIconSize(pix.size())
        self.setFixedSize(pix.size())
        self.setToolTip(f"Clic para abrir: {os.path.basename(image_path)}")


class ShotInfoWindow(QtWidgets.QWidget):
    def __init__(self, shot_data):
        super().__init__()
        self.shot_data = shot_data
        self.setObjectName("flowNotesContentWidget")
        self.setMinimumSize(900, 760)
        self._build_ui()

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QtWidgets.QWidget()
        header.setObjectName("flowNotesHeaderWidget")
        h_layout = QtWidgets.QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 12, 12)

        title_text = (
            f"{self.shot_data['shot_code']}"
            f"  |  {self.shot_data['task_type']}"
            f"  |  {self.shot_data['assignee']}"
        )
        title = QtWidgets.QLabel(title_text)
        title.setObjectName("flowNotesTitle")
        h_layout.addWidget(title, 1)

        close_btn = QtWidgets.QPushButton("X")
        close_btn.setObjectName("flowNotesCloseButton")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)

        outer.addWidget(header)

        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("flowNotesScrollArea")
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)

        scroll_content = QtWidgets.QWidget()
        scroll_content.setObjectName("flowNotesScrollContent")
        scroll.setWidget(scroll_content)

        v_layout = QtWidgets.QVBoxLayout(scroll_content)
        v_layout.setContentsMargins(16, 12, 16, 12)
        v_layout.setSpacing(16)

        for version in self.shot_data["versions"]:
            v_layout.addWidget(self._build_version_widget(version))

        v_layout.addStretch(1)

    # ----- version block -----
    def _build_version_widget(self, version):
        container = QtWidgets.QWidget()
        container.setObjectName("flowVersionContainer")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        c_layout = QtWidgets.QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 12)
        c_layout.setSpacing(0)

        c_layout.addWidget(self._build_version_header(version))
        c_layout.addWidget(self._build_description_section(version))

        # Notes (filtradas)
        visible_notes = self._filter_notes(version)
        if visible_notes:
            c_layout.addWidget(self._build_comments_section(visible_notes))

        return container

    def _build_version_header(self, version):
        header = QtWidgets.QWidget()
        header.setObjectName("flowVersionHeader")
        header.setFixedHeight(40)

        hl = QtWidgets.QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 16, 8)

        version_dt = parse_pipesync_dt(version["created_on"])
        date_text = format_friendly_date(version_dt, include_time=False, today=TODAY_OVERRIDE)

        info_html = (
            f"<span style='color: {COLORS['txt_principal_strong']}; font-weight: 800;'>v{version['version_number']:03d}</span>"
            f"<span style='color: {COLORS['txt_secundario']};'> &nbsp;&nbsp; | &nbsp;&nbsp; subida </span>"
            f"<span style='color: {COLORS['txt_subtle']};'>{date_text}</span>"
            f"<span style='color: {COLORS['txt_secundario']};'> &nbsp;&nbsp; por </span>"
            f"<span style='color: {COLORS['txt_subtle']};'>{version['created_by']}</span>"
        )
        info_label = QtWidgets.QLabel(info_html)
        info_label.setObjectName("flowVersionInfo")
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hl.addWidget(info_label)
        hl.addStretch(1)

        time_text = format_logged_time(version.get("logged_minutes", 0))
        if time_text:
            time_html = (
                f"<span style='color: {COLORS['txt_secundario']};'>Time logged: </span>"
                f"<span style='color: {COLORS['txt_subtle']};'>{time_text}</span>"
            )
            time_label = QtWidgets.QLabel(time_html)
            time_label.setObjectName("flowVersionTimeLogged")
            time_label.setTextFormat(Qt.RichText)
            time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            hl.addWidget(time_label)

        return header

    def _build_description_section(self, version):
        section = QtWidgets.QWidget()
        section.setObjectName("flowVersionDescriptionSection")
        sl = QtWidgets.QVBoxLayout(section)
        sl.setContentsMargins(16, 8, 12, 8)
        sl.setSpacing(0)

        author = (version.get("created_by") or "").strip()
        title_html = (
            f"<span style='color: {COLORS['txt_desc_title']}; font-weight: 700; font-size: 15px;'>Descripción:</span>"
        )
        if author:
            title_html += (
                f"<span style='color: {COLORS['txt_desc_meta']}; font-size: 14px;'>"
                f"&nbsp;(por {author})</span>"
            )
        title_label = QtWidgets.QLabel(title_html)
        title_label.setObjectName("flowVersionDescriptionTitle")
        title_label.setTextFormat(Qt.RichText)
        title_label.setWordWrap(True)
        sl.addWidget(title_label)

        sl.addSpacing(2)

        desc = (version.get("description") or "").strip()
        if not desc:
            content_html = f"<span style='color: {COLORS['txt_body']};'>Sin descripción</span>"
        else:
            esc = QtGui.QTextDocumentFragment.fromPlainText(desc).toHtml()
            # toHtml envuelve mucho — usar replace simple en su lugar:
            esc = (
                desc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            content_html = f"<span style='color: {COLORS['txt_body']};'>{esc}</span>"
        content_label = QtWidgets.QLabel(content_html)
        content_label.setObjectName("flowVersionDescriptionContent")
        content_label.setTextFormat(Qt.RichText)
        content_label.setWordWrap(True)
        content_label.setContentsMargins(16, 0, 0, 0)
        sl.addWidget(content_label)

        return section

    def _filter_notes(self, version):
        """Filtra: notas espejo de descripcion + duplicados de content (igual que C++)."""
        seen = set()
        out = []
        v_desc = (version.get("description") or "").strip()
        v_user = (version.get("created_by") or "").strip()
        v_dt = parse_pipesync_dt(version.get("created_on"))
        for note in version.get("notes", []):
            n_content = (note.get("content") or "").strip()
            n_user = (note.get("created_by") or "").strip()
            # mirror filter
            if v_desc and n_content == v_desc and n_user == v_user:
                n_dt = parse_pipesync_dt(note.get("created_on"))
                if v_dt and n_dt:
                    delta = (n_dt - v_dt).total_seconds()
                    if 0 <= delta <= 300:
                        continue
                else:
                    continue
            if n_content in seen:
                continue
            seen.add(n_content)
            out.append(note)
        return out

    def _build_comments_section(self, notes):
        section = QtWidgets.QWidget()
        section.setObjectName("flowVersionCommentsContainer")
        sl = QtWidgets.QVBoxLayout(section)
        sl.setContentsMargins(8, 0, 8, 0)
        sl.setSpacing(4)

        for note in notes:
            sep = QtWidgets.QFrame()
            sep.setObjectName("flowCommentSeparator")
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setFixedHeight(1)
            sl.addWidget(sep)
            sl.addWidget(self._build_comment_widget(note))

        return section

    def _build_comment_widget(self, note):
        w = QtWidgets.QWidget()
        w.setObjectName("flowVersionComment")
        wl = QtWidgets.QVBoxLayout(w)
        wl.setContentsMargins(0, 0, 0, 8)
        wl.setSpacing(0)

        author = (note.get("created_by") or "").strip()
        n_dt = parse_pipesync_dt(note.get("created_on"))
        date_str = format_friendly_date(n_dt, include_time=True, today=TODAY_OVERRIDE)

        header_html = (
            f"<span style='color: {COLORS['txt_desc_title']}; font-size: 15px; font-weight: 700;'>Comentario:</span>"
            f"<span style='color: {COLORS['txt_desc_meta']}; font-size: 14px;'>&nbsp;(por {author}, {date_str})</span>"
        )
        header_label = QtWidgets.QLabel(header_html)
        header_label.setObjectName("flowVersionCommentHeader")
        header_label.setTextFormat(Qt.RichText)
        header_label.setWordWrap(True)
        header_label.setContentsMargins(8, 8, 0, 0)
        wl.addWidget(header_label)
        wl.addSpacing(6)

        content = (note.get("content") or "").strip()
        esc = (
            content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        content_html = f"<span style='color: {COLORS['txt_body']};'>{esc}</span>"
        content_label = QtWidgets.QLabel(content_html)
        content_label.setObjectName("flowVersionCommentContent")
        content_label.setTextFormat(Qt.RichText)
        content_label.setWordWrap(True)
        content_label.setContentsMargins(32, 0, 0, 0)
        wl.addWidget(content_label)

        # Attachments
        att_info = note.get("attachment_info") or ""
        local_paths = (note.get("local_attachment_paths") or "").split(";")
        local_paths = [p.strip() for p in local_paths if p.strip()]

        frame_texts = []
        try:
            data = json.loads(att_info) if att_info else []
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and entry.get("frame") is not None:
                        frame_texts.append(f"Frame {entry['frame']}")
                    else:
                        frame_texts.append("Sin Frame Number")
        except Exception:
            pass

        if local_paths:
            thumbs_w = QtWidgets.QWidget()
            thumbs_w.setObjectName("flowVersionCommentThumbnails")
            tl = QtWidgets.QHBoxLayout(thumbs_w)
            tl.setContentsMargins(32, 8, 0, 8)
            tl.setSpacing(8)

            for i, path in enumerate(local_paths):
                if not os.path.exists(path):
                    continue
                col = QtWidgets.QWidget()
                col.setObjectName("flowVersionCommentThumbnailContainer")
                cl = QtWidgets.QVBoxLayout(col)
                cl.setContentsMargins(0, 0, 0, 0)
                cl.setSpacing(4)
                cl.addWidget(ThumbnailButton(path))
                frame_text = frame_texts[i] if i < len(frame_texts) else "Sin Frame Number"
                lab = QtWidgets.QLabel(frame_text)
                lab.setObjectName("flowVersionCommentAttachment")
                lab.setFixedWidth(150)
                lab.setAlignment(Qt.AlignCenter)
                cl.addWidget(lab)
                tl.addWidget(col)
            tl.addStretch(1)
            wl.addWidget(thumbs_w)

        return w


# --------------------------------------------------------------------------- #
# QSS (port directo de flow_notes.qss con variables resueltas)
# --------------------------------------------------------------------------- #
QSS = """
QWidget#flowNotesContentWidget {
    background-color: %(bg_popover)s;
    border: 1px solid %(border_principal)s;
    border-radius: 8px;
}

QWidget#flowNotesHeaderWidget {
    background-color: %(bg_popover)s;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom: 1px solid rgba(48, 48, 48, 0.7);
}

QLabel#flowNotesTitle {
    color: %(txt_principal)s;
    font-family: "Inter", "Segoe UI", Arial, Helvetica, sans-serif;
    font-weight: 500;
    font-size: 18px;
    background-color: transparent;
}

QPushButton#flowNotesCloseButton {
    background-color: transparent;
    border: none;
    color: %(txt_principal)s;
    font-size: 14px;
}
QPushButton#flowNotesCloseButton:hover {
    background-color: #2E2E2E;
    border-radius: 12px;
}

QScrollArea#flowNotesScrollArea {
    background-color: transparent;
    border: none;
}
QWidget#flowNotesScrollContent {
    background-color: transparent;
}

QScrollArea#flowNotesScrollArea QScrollBar:vertical {
    background-color: #252525;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollArea#flowNotesScrollArea QScrollBar::handle:vertical {
    background-color: #2E2E2E;
    min-height: 30px;
    border-radius: 4px;
}
QScrollArea#flowNotesScrollArea QScrollBar::handle:vertical:hover { background-color: #3D3D3D; }
QScrollArea#flowNotesScrollArea QScrollBar::add-line:vertical,
QScrollArea#flowNotesScrollArea QScrollBar::sub-line:vertical { height: 0px; background: none; }

QWidget#flowVersionContainer {
    background-color: %(bg_version_container)s;
    border: 1px solid rgba(48, 48, 48, 0.6);
    border-radius: 6px;
}

QWidget#flowVersionHeader {
    background-color: %(bg_version_header)s;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QLabel#flowVersionInfo {
    background-color: transparent;
    font-size: 14px;
    font-weight: 500;
}
QLabel#flowVersionTimeLogged {
    background-color: transparent;
    font-size: 13px;
    font-weight: 400;
}

QLabel#flowVersionDescriptionTitle,
QLabel#flowVersionDescriptionContent {
    background-color: transparent;
    font-size: 14px;
    border: none;
    padding: 4px 0px;
}

QWidget#flowVersionCommentsContainer {
    background-color: transparent;
    border-radius: 4px;
}
QWidget#flowVersionComment {
    background-color: transparent;
}

QFrame#flowCommentSeparator {
    color: %(border_principal)s;
    background-color: %(border_principal)s;
    border: none;
    max-height: 1px;
}

QLabel#flowVersionCommentHeader {
    background-color: transparent;
    padding-top: 4px;
    font-size: 14px;
    font-weight: 400;
}

QLabel#flowVersionCommentContent {
    background-color: transparent;
    color: #909090;
    font-size: 14px;
    border: none;
    padding: 0;
    margin: 0;
}

QLabel#flowVersionCommentAttachment {
    color: %(attachment_label_fg)s;
    background-color: %(attachment_label_bg)s;
    border-radius: 0px;
    font-size: 13px;
}

QPushButton#flowVersionCommentThumbnail {
    border: 2px solid #404040;
    border-radius: 8px;
    background-color: transparent;
    padding: 2px;
}
QPushButton#flowVersionCommentThumbnail:hover {
    border-color: #606060;
    background-color: rgba(255, 255, 255, 0.05);
}
""" % COLORS


# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot", help="ruta a PNG; si se da, no abre ventana")
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=820)
    args = parser.parse_args()

    # NOTA: NO usamos QT_QPA_PLATFORM=offscreen porque en Windows no carga
    # las fonts del sistema y todo se ve como cajitas. Usamos el plugin
    # nativo y, en modo screenshot, ocultamos la ventana fuera de pantalla.
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    # Asegurar una font del sistema (offscreen no resuelve "Inter" automaticamente).
    fdb_families = set(QtGui.QFontDatabase.families())
    for candidate in ("Segoe UI", "Arial", "Helvetica", "DejaVu Sans"):
        if candidate in fdb_families:
            app.setFont(QtGui.QFont(candidate, 10))
            break

    app.setStyleSheet(QSS)

    win = ShotInfoWindow(SHOT_DATA)
    win.resize(args.width, args.height)

    if args.screenshot:
        # Mostrar la ventana fuera del escritorio para forzar layout sin molestar.
        win.move(-3000, -3000)
        win.show()
        for _ in range(5):
            app.processEvents()
        win.repaint()
        app.processEvents()
        pix = win.grab()
        pix.save(args.screenshot, "PNG")
        win.close()
        print(f"[ok] screenshot guardado en {args.screenshot}")
        return 0

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
