#!/usr/bin/env python3
"""
LGA_analizar_logs_xyplorer.py

Analiza el tiempo aproximado de operaciones XYplorer en debugPy.log.
Empareja el inicio del thread con el primer fin detectado (error o resultado).
"""

import argparse
import os
import re
from collections import deque

LOG_RE = re.compile(r"^\[(\d+\.\d{3})s\]\s*(.*)$")
START_RE = re.compile(r"^tag_shot_folder_thread started")
END_RES = [
    re.compile(r"^Error applying tag in XYplorer"),
    re.compile(r"^Send_WM_COPYDATA result"),
]


def parse_log(path):
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = LOG_RE.match(line.strip())
            if not m:
                continue
            entries.append({"ts": float(m.group(1)), "msg": m.group(2)})
    return entries


def compute_xyplorer_durations(entries):
    starts = deque()
    durations = []
    for entry in entries:
        msg = entry["msg"]
        if START_RE.match(msg):
            starts.append(entry["ts"])
            continue
        if any(end_re.match(msg) for end_re in END_RES):
            if starts:
                start_ts = starts.popleft()
                durations.append(entry["ts"] - start_ts)
    return durations, len(starts)


def summarize(durations):
    if not durations:
        return None
    total = sum(durations)
    return {
        "count": len(durations),
        "avg": total / len(durations),
        "max": max(durations),
        "min": min(durations),
        "total": total,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analiza tiempo de operaciones XYplorer en debugPy.log"
    )
    parser.add_argument(
        "--log-file",
        "-f",
        default="logs/debugPy.log",
        help="Ruta del log",
    )
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"ERROR: no existe el log: {args.log_file}")
        return 1

    entries = parse_log(args.log_file)
    if not entries:
        print("ERROR: no se encontraron entradas con timestamp.")
        return 1

    durations, pending = compute_xyplorer_durations(entries)
    stats = summarize(durations)

    print("ANALISIS XYPLORER")
    print("-" * 60)
    print(f"Archivo: {os.path.basename(args.log_file)}")
    if not stats:
        print("No se detectaron intervalos de XYplorer.")
        return 0

    print(f"Conteo: {stats['count']}")
    print(f"Total: {stats['total']:.3f}s")
    print(
        f"Avg: {stats['avg']:.4f}s | Max: {stats['max']:.4f}s | Min: {stats['min']:.4f}s"
    )
    if pending:
        print(f"Advertencia: {pending} inicios sin fin detectado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
