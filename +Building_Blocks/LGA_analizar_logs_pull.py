#!/usr/bin/env python3
"""
LGA_analizar_logs_pull.py

Analiza el archivo debugPy.log para responder con claridad:
- Que operaciones tardan mas
- Que clips tardan mas
- Tiempos de doScan, busquedas en SG, XYplorer y cambios de version
"""

import argparse
import os
import re

DEFAULT_LOG = r"C:\Users\leg4-pc\.nuke\Python\Startup\logs\debugPy.log"
LOG_RE = re.compile(r"^\[(\d+\.\d{3})s\]\s*(.*)$")


def parse_log(path):
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            m = LOG_RE.match(line.strip())
            if not m:
                continue
            entries.append(
                {"ts": float(m.group(1)), "msg": m.group(2), "line": line_num}
            )
    return entries


def compute_gaps(entries):
    gaps = []
    for i in range(1, len(entries)):
        gaps.append(
            {
                "dt": entries[i]["ts"] - entries[i - 1]["ts"],
                "from_msg": entries[i - 1]["msg"],
                "to_msg": entries[i]["msg"],
            }
        )
    return gaps


def compute_clip_durations(entries):
    clips = []
    current = None
    for entry in entries:
        msg = entry["msg"]
        if msg.startswith("Procesando clip:"):
            clip_name = msg.split("Procesando clip:", 1)[1].strip()
            if current:
                current["end_ts"] = entry["ts"]
                current["duration"] = current["end_ts"] - current["start_ts"]
                clips.append(current)
            current = {"clip": clip_name, "start_ts": entry["ts"]}
    if current:
        current["end_ts"] = entries[-1]["ts"]
        current["duration"] = current["end_ts"] - current["start_ts"]
        clips.append(current)
    return clips


def pair_by_key(entries, start_re, end_res, start_key_index=1, end_key_index=1):
    starts = {}
    durations = []
    for entry in entries:
        msg = entry["msg"]
        m = start_re.match(msg)
        if m:
            key = m.group(start_key_index)
            starts[key] = entry["ts"]
            continue
        for end_re in end_res:
            m_end = end_re.match(msg)
            if m_end:
                key = m_end.group(end_key_index)
                if key in starts:
                    durations.append({"dt": entry["ts"] - starts[key], "key": key})
                    del starts[key]
                break
    return durations


def pair_sequential(entries, start_re, end_res):
    durations = []
    start_ts = None
    start_label = None
    for entry in entries:
        msg = entry["msg"]
        m = start_re.match(msg)
        if m:
            start_ts = entry["ts"]
            start_label = m.group(1) if m.groups() else None
            continue
        if start_ts is not None:
            for end_re in end_res:
                if end_re.match(msg):
                    durations.append({"dt": entry["ts"] - start_ts, "key": start_label})
                    start_ts = None
                    start_label = None
                    break
    return durations


def summarize(durations):
    if not durations:
        return None
    vals = [d["dt"] for d in durations]
    return {
        "count": len(vals),
        "avg": sum(vals) / len(vals),
        "max": max(vals),
        "min": min(vals),
        "total": sum(vals),
    }


def format_seconds(value):
    return f"{value:.3f}s"


def build_report(entries, log_path, top, min_gap):
    total_time = entries[-1]["ts"] if entries else 0.0
    report = []

    report.append("ANALISIS DE LOG PULL")
    report.append("-" * 60)
    report.append(f"Archivo: {os.path.basename(log_path)}")
    report.append(f"Entradas: {len(entries)}")
    report.append(f"Tiempo total: {format_seconds(total_time)}")
    report.append("")
    report.append("Nota: los gaps son el tiempo entre logs consecutivos.")
    report.append("Nota: XYplorer corre en thread, puede mezclar tiempos.")
    report.append("")

    # Top gaps
    gaps = compute_gaps(entries)
    gaps = [g for g in gaps if g["dt"] >= min_gap]
    gaps.sort(key=lambda g: g["dt"], reverse=True)

    report.append("TOP GAPS (tiempo entre logs consecutivos)")
    report.append("-" * 60)
    if gaps:
        for i, gap in enumerate(gaps[:top], 1):
            report.append(
                f"{i:02d}. {format_seconds(gap['dt'])} | {gap['from_msg']} -> {gap['to_msg']}"
            )
    else:
        report.append("No hay gaps mayores al umbral.")

    # Clip durations
    report.append("")
    report.append("TOP CLIPS POR DURACION (de 'Procesando clip' al siguiente)")
    report.append("-" * 60)
    clips = compute_clip_durations(entries)
    clips.sort(key=lambda c: c["duration"], reverse=True)
    if clips:
        for i, clip in enumerate(clips[:top], 1):
            report.append(f"{i:02d}. {format_seconds(clip['duration'])} | {clip['clip']}")
    else:
        report.append("No se detectaron clips.")

    # doScan durations
    report.append("")
    report.append("DURACIONES POR OPERACION (medidas con inicio/fin)")
    report.append("-" * 60)

    re_scan_start = re.compile(r"^Creando VersionScanner para clip: (.+)$")
    re_scan_end = re.compile(r"^doScan completado para clip: (.+)$")
    scan_durs = pair_by_key(entries, re_scan_start, [re_scan_end], 1, 1)

    re_shot_start = re.compile(
        r"^Buscando shot en SG: project='([^']+)', shot='([^']+)'$"
    )
    re_shot_ok = re.compile(r"^Shot encontrado: (.+)$")
    re_shot_no = re.compile(
        r"^No se encontro shot '([^']+)' en el proyecto '([^']+)'$"
    )
    shot_durs = pair_by_key(entries, re_shot_start, [re_shot_ok, re_shot_no], 2, 1)

    re_task_start = re.compile(r"^Buscando task '(.+)' en el shot$")
    re_task_ok = re.compile(r"^Task encontrada: (.+)$")
    re_task_no = re.compile(r"^No se encontro task '(.+)' para el shot '(.+)'$")
    task_durs = pair_sequential(entries, re_task_start, [re_task_ok, re_task_no])

    re_set_start = re.compile(r"^Ejecutando setActiveVersion para clip: (.+)$")
    re_set_end = re.compile(r"^setActiveVersion completado exitosamente para clip: (.+)$")
    set_durs = pair_by_key(entries, re_set_start, [re_set_end], 1, 1)

    re_xy_send = re.compile(r"^Sending command to XYplorer:")
    re_xy_end = re.compile(r"^Send_WM_COPYDATA result:")
    xy_durs = pair_sequential(entries, re_xy_send, [re_xy_end])

    for name, durs in [
        ("doScan", scan_durs),
        ("SG shot lookup", shot_durs),
        ("SG task lookup", task_durs),
        ("setActiveVersion", set_durs),
        ("XYplorer send", xy_durs),
    ]:
        stats = summarize(durs)
        if not stats:
            report.append(f"{name}: sin datos")
            continue
        report.append(
            f"{name}: count={stats['count']} avg={format_seconds(stats['avg'])} "
            f"max={format_seconds(stats['max'])} min={format_seconds(stats['min'])}"
        )

    # Top doScan list
    if scan_durs:
        report.append("")
        report.append("TOP doScan por clip")
        report.append("-" * 60)
        scan_durs.sort(key=lambda d: d["dt"], reverse=True)
        for i, item in enumerate(scan_durs[:top], 1):
            report.append(f"{i:02d}. {format_seconds(item['dt'])} | {item['key']}")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Analizar logs de debugPy.log y mostrar operaciones mas lentas"
    )
    parser.add_argument("--log-file", "-f", default=DEFAULT_LOG, help="Ruta del log")
    parser.add_argument("--top", "-t", type=int, default=10, help="Cantidad de items")
    parser.add_argument(
        "--min-gap",
        type=float,
        default=0.02,
        help="Umbral de gap minimo en segundos",
    )
    parser.add_argument("--out", "-o", help="Archivo de salida para el reporte")

    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"ERROR: no existe el log: {args.log_file}")
        return 1

    entries = parse_log(args.log_file)
    if not entries:
        print("ERROR: no se encontraron entradas con timestamp.")
        return 1

    report = build_report(entries, args.log_file, args.top, args.min_gap)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print("")
        print(f"Reporte guardado en: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())