"""
____________________________________________________________________

  explore_timeline_render_metrics_to_txt.py | Lega

  Exploracion enfocada en lo que SI cambio: el render interno del
  TimelineView.viewport().

  La exploracion por widgets mostro que el ancho de tracknames y el alto
  de tracks no aparecen como widgets ni propiedades Qt visibles. Este
  script toma una captura del viewport y calcula metricas por pixeles:

    - bordes verticales fuertes, para inferir el limite tracknames/clips
    - bordes horizontales fuertes, para inferir alturas de tracks
    - resumen de columnas/filas relevantes
    - meta-metodos completos del TimelineView, sin filtro de keywords

  Guarda snapshots numerados:

      C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/final_render_metrics_1.txt
      C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/final_render_metrics_1_viewport.png

  Uso:
      exec(open(r"C:/Users/leg4-pc/.nuke/Python/Startup/+Building_Blocks/explore_timeline_render_metrics_to_txt.py").read())
____________________________________________________________________
"""

from __future__ import print_function

import os
import sys
import time
import traceback

import hiero.ui

try:
    from LGA_NKS_Shared.LGA_QtAdapter_HieroTools import QtWidgets, QtCore
except Exception:
    try:
        from PySide6 import QtWidgets, QtCore
    except Exception:
        from PySide2 import QtWidgets, QtCore


OUT_DIR = r"C:\Users\leg4-pc\.nuke\LGA_ToolPack-Layout"
PREFIX = "final_render_metrics"

MAX_METHODS = 500
MAX_PROPERTIES = 300
MAX_PEAKS = 120


def safe_str(value, limit=300):
    try:
        text = str(value)
    except Exception as exc:
        text = "<str error: %s>" % exc
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def class_name(obj):
    try:
        if hasattr(obj, "metaObject"):
            return obj.metaObject().className()
    except Exception:
        pass
    return type(obj).__name__


def next_output_path():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    idx = 1
    while True:
        txt = os.path.join(OUT_DIR, "%s_%d.txt" % (PREFIX, idx))
        if not os.path.exists(txt):
            return txt, idx
        idx += 1


def section(lines, title):
    lines.append("")
    lines.append("=" * 100)
    lines.append(title)
    lines.append("=" * 100)


def find_timeline_editor():
    try:
        seq = hiero.ui.activeSequence()
        return hiero.ui.getTimelineEditor(seq)
    except Exception:
        return None


def find_timeline_view(window):
    if not window:
        return None
    for widget in window.findChildren(QtWidgets.QWidget):
        if class_name(widget) == "Foundry::Storm::UI::TimelineView":
            return widget
    return None


def geom_text(widget):
    if not widget:
        return "<none>"
    try:
        g = widget.geometry()
        return "x=%d y=%d w=%d h=%d" % (g.x(), g.y(), g.width(), g.height())
    except Exception as exc:
        return "<geometry error: %s>" % exc


def process_events():
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.12)
    QtCore.QCoreApplication.processEvents()


def qimage_rgb_matrix(qimage):
    image = qimage.convertToFormat(qimage.Format_RGB32)
    w = image.width()
    h = image.height()
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = image.pixelColor(x, y)
            row.append((c.red(), c.green(), c.blue()))
        rows.append(row)
    return w, h, rows


def color_diff(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def edge_scores_vertical(rows, w, h):
    scores = []
    for x in range(1, w):
        score = 0
        for y in range(h):
            score += color_diff(rows[y][x - 1], rows[y][x])
        scores.append((x, score))
    return scores


def edge_scores_horizontal(rows, w, h):
    scores = []
    for y in range(1, h):
        score = 0
        prev = rows[y - 1]
        cur = rows[y]
        for x in range(w):
            score += color_diff(prev[x], cur[x])
        scores.append((y, score))
    return scores


def top_peaks(scores, max_items=MAX_PEAKS, min_distance=3):
    ordered = sorted(scores, key=lambda item: item[1], reverse=True)
    chosen = []
    for pos, score in ordered:
        if all(abs(pos - prev_pos) >= min_distance for prev_pos, _ in chosen):
            chosen.append((pos, score))
            if len(chosen) >= max_items:
                break
    return sorted(chosen)


def local_peaks(scores, threshold_ratio=0.18):
    if not scores:
        return []
    max_score = max(score for _, score in scores)
    threshold = max_score * threshold_ratio
    peaks = []
    for i in range(1, len(scores) - 1):
        pos, score = scores[i]
        if score >= threshold and score >= scores[i - 1][1] and score >= scores[i + 1][1]:
            peaks.append((pos, score))
    return peaks


def ranges_from_positions(positions, gap=2):
    if not positions:
        return []
    ranges = []
    start = prev = positions[0]
    for pos in positions[1:]:
        if pos <= prev + gap:
            prev = pos
        else:
            ranges.append((start, prev))
            start = prev = pos
    ranges.append((start, prev))
    return ranges


def avg_rgb_for_column(rows, x):
    h = len(rows)
    if h == 0:
        return (0, 0, 0)
    r = g = b = 0
    for row in rows:
        c = row[x]
        r += c[0]
        g += c[1]
        b += c[2]
    return (r // h, g // h, b // h)


def avg_rgb_for_row(rows, y):
    row = rows[y]
    w = len(row)
    if w == 0:
        return (0, 0, 0)
    r = g = b = 0
    for c in row:
        r += c[0]
        g += c[1]
        b += c[2]
    return (r // w, g // w, b // w)


def infer_label_boundary(vertical_scores, w):
    # The label/clip boundary appears as a small cluster of strong vertical
    # edges after the icon/name area. Individual clip edges can be stronger,
    # so report a candidate cluster instead of blindly taking the max score.
    left_limit = max(120, int(w * 0.25))
    candidates = [(x, s) for x, s in vertical_scores if 20 <= x <= left_limit]
    peaks = top_peaks(candidates, max_items=30, min_distance=6)
    if not peaks:
        return None, [], []

    # Ignore the left border/icons and build contiguous-ish clusters of peaks.
    usable = [(x, s) for x, s in peaks if x >= 120]
    clusters = []
    current = []
    for item in usable:
        if not current or item[0] <= current[-1][0] + 28:
            current.append(item)
        else:
            clusters.append(current)
            current = [item]
    if current:
        clusters.append(current)

    cluster_summaries = []
    for cluster in clusters:
        xs = [x for x, _ in cluster]
        score = sum(s for _, s in cluster)
        strongest = max(cluster, key=lambda item: item[1])
        center = int(round(sum(xs) / float(len(xs))))
        cluster_summaries.append({
            "range": (min(xs), max(xs)),
            "center": center,
            "count": len(cluster),
            "score": score,
            "strongest": strongest,
        })

    # Prefer the earliest substantial cluster. That is the track header/clip
    # split in the viewport captures; later strong peaks are clip boundaries.
    substantial = [c for c in cluster_summaries if c["count"] >= 2]
    picked = substantial[0] if substantial else (cluster_summaries[0] if cluster_summaries else None)
    return picked, peaks, cluster_summaries


def dump_pixel_metrics(lines, timeline_view, png_path):
    section(lines, "VIEWPORT PIXEL METRICS")
    if not timeline_view:
        lines.append("<no TimelineView>")
        return
    try:
        viewport = timeline_view.viewport()
        pixmap = viewport.grab()
        ok = pixmap.save(png_path)
        lines.append("viewport_grab_saved=%s path=%s size=%dx%d" % (ok, png_path, pixmap.width(), pixmap.height()))
        qimage = pixmap.toImage()
    except Exception as exc:
        lines.append("<viewport grab error: %s>" % exc)
        return

    try:
        w, h, rows = qimage_rgb_matrix(qimage)
    except Exception as exc:
        lines.append("<qimage read error: %s>" % exc)
        return

    v_scores = edge_scores_vertical(rows, w, h)
    h_scores = edge_scores_horizontal(rows, w, h)
    v_peak, v_left_peaks, label_clusters = infer_label_boundary(v_scores, w)
    h_peaks = top_peaks(h_scores, max_items=MAX_PEAKS, min_distance=3)
    h_local = local_peaks(h_scores, threshold_ratio=0.16)
    v_local = local_peaks(v_scores, threshold_ratio=0.16)

    lines.append("image_size=%dx%d" % (w, h))
    lines.append("inferred_label_clip_boundary_cluster=%s" % (safe_str(v_peak) if v_peak else "<none>"))
    lines.append("label_clip_boundary_candidate_clusters=%s" % safe_str(label_clusters, 3000))
    lines.append("left_side_vertical_peaks=%s" % safe_str(v_left_peaks, 2000))
    lines.append("top_vertical_peaks=%s" % safe_str(top_peaks(v_scores, max_items=MAX_PEAKS, min_distance=4), 4000))
    lines.append("top_horizontal_peaks=%s" % safe_str(h_peaks, 4000))
    lines.append("vertical_local_peak_ranges=%s" % safe_str(ranges_from_positions([x for x, _ in v_local]), 3000))
    lines.append("horizontal_local_peak_ranges=%s" % safe_str(ranges_from_positions([y for y, _ in h_local]), 3000))

    sample_columns = sorted(set([0, 1, 20, 36, 60, 90, 120, 135, 152, 185, 214, 259, 300, 315, 342, 387, w - 2, w - 1]))
    sample_columns = [x for x in sample_columns if 0 <= x < w]
    lines.append("sample_column_avg_rgb:")
    for x in sample_columns:
        lines.append("  x=%04d avgRGB=%s" % (x, avg_rgb_for_column(rows, x)))

    sample_rows = sorted(set([0, 1, 20, 35, 50, 70, 90, 105, 120, 145, 170, 200, 225, 250, 275, 300, h - 2, h - 1]))
    sample_rows = [y for y in sample_rows if 0 <= y < h]
    lines.append("sample_row_avg_rgb:")
    for y in sample_rows:
        lines.append("  y=%04d avgRGB=%s" % (y, avg_rgb_for_row(rows, y)))


def dump_timeline_methods(lines, timeline_view):
    section(lines, "TIMELINEVIEW FULL META METHODS")
    if not timeline_view:
        lines.append("<no TimelineView>")
        return
    try:
        mo = timeline_view.metaObject()
    except Exception as exc:
        lines.append("<metaObject error: %s>" % exc)
        return
    lines.append("className=%s methodOffset=%d methodCount=%d" % (mo.className(), mo.methodOffset(), mo.methodCount()))
    count = 0
    for i in range(mo.methodOffset(), mo.methodCount()):
        if count >= MAX_METHODS:
            lines.append("<truncated at %d methods>" % MAX_METHODS)
            break
        method = mo.method(i)
        try:
            signature = bytes(method.methodSignature()).decode("utf-8", "replace")
        except Exception:
            signature = safe_str(method.methodSignature())
        lines.append("%03d type=%s access=%s signature=%s" % (i, method.methodType(), method.access(), signature))
        count += 1


def dump_timeline_properties(lines, timeline_view):
    section(lines, "TIMELINEVIEW FULL META PROPERTIES")
    if not timeline_view:
        lines.append("<no TimelineView>")
        return
    try:
        mo = timeline_view.metaObject()
    except Exception as exc:
        lines.append("<metaObject error: %s>" % exc)
        return
    lines.append("className=%s propertyOffset=%d propertyCount=%d" % (mo.className(), mo.propertyOffset(), mo.propertyCount()))
    count = 0
    for i in range(mo.propertyOffset(), mo.propertyCount()):
        if count >= MAX_PROPERTIES:
            lines.append("<truncated at %d properties>" % MAX_PROPERTIES)
            break
        prop = mo.property(i)
        try:
            value = prop.read(timeline_view)
        except Exception as exc:
            value = "<read error: %s>" % exc
        lines.append("%03d name=%s type=%s writable=%s value=%s" % (
            i, prop.name(), prop.typeName(), prop.isWritable(), safe_str(value)
        ))
        count += 1


def dump_runtime_summary(lines, editor, timeline_view):
    section(lines, "RUNTIME SUMMARY")
    try:
        seq = hiero.ui.activeSequence()
    except Exception:
        seq = None
    lines.append("activeSequence=%r" % (seq.name() if seq else None))
    lines.append("TimelineEditor=%s class=%s" % (safe_str(repr(editor)), type(editor).__name__ if editor else None))
    lines.append("TimelineView=%s class=%s geometry=%s" % (safe_str(repr(timeline_view)), class_name(timeline_view) if timeline_view else None, geom_text(timeline_view)))
    try:
        lines.append("Viewport geometry=%s" % geom_text(timeline_view.viewport()))
    except Exception:
        lines.append("Viewport geometry=<none>")
    if timeline_view:
        for name in ("horizontalScrollBar", "verticalScrollBar"):
            try:
                sb = getattr(timeline_view, name)()
                lines.append("%s geometry=%s value=%s range=(%s,%s) pageStep=%s" % (
                    name, geom_text(sb), sb.value(), sb.minimum(), sb.maximum(), sb.pageStep()
                ))
            except Exception as exc:
                lines.append("%s error=%s" % (name, exc))

    if seq:
        try:
            tracks = list(seq.videoTracks())
            lines.append("videoTracks=%s" % ", ".join("%d:%s" % (i, t.name()) for i, t in enumerate(tracks)))
        except Exception as exc:
            lines.append("videoTracks error=%s" % exc)


def main():
    txt_path, idx = next_output_path()
    png_path = os.path.join(OUT_DIR, "%s_%d_viewport.png" % (PREFIX, idx))

    process_events()

    editor = find_timeline_editor()
    window = None
    try:
        window = editor.window() if editor else None
    except Exception:
        window = None
    timeline_view = find_timeline_view(window)

    lines = []
    lines.append("TIMELINE RENDER METRICS EXPLORATION")
    lines.append("time=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("outputPath=%s" % txt_path)
    lines.append("python=%s" % sys.version.replace("\n", " "))

    dump_runtime_summary(lines, editor, timeline_view)
    dump_pixel_metrics(lines, timeline_view, png_path)
    dump_timeline_methods(lines, timeline_view)
    dump_timeline_properties(lines, timeline_view)

    lines.append("")
    lines.append("END explore_timeline_render_metrics_to_txt")

    with open(txt_path, "w", encoding="utf-8", errors="replace") as handle:
        handle.write("\n".join(lines))

    print("# Result: saved %s" % txt_path)
    print("# Result: saved %s" % png_path)


try:
    main()
except Exception:
    print("# Result: TRACEBACK")
    print(traceback.format_exc())
