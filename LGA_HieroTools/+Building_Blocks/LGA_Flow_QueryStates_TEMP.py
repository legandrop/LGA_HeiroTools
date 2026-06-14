"""
TEMP / investigacion: consulta a Flow (ShotGrid) los estados validos de
sg_status_list para Shot y Task, sus nombres visibles y colores, y los valores
de sg_prioridad. Solo lectura (schema + Status entity). No escribe nada.

Correr con el Python runtime de PipeSync:
  C:/Portable/LGA/PipeSync/python_runtime/windows/python.exe este_script.py
"""

import sys
from pathlib import Path

shared = Path(__file__).parent.parent / "LGA_NKS_Shared"
sys.path.insert(0, str(shared))

import shotgun_api3
from SecureConfig_Reader import get_flow_credentials


def dump_status_field(sg, entity, field):
    try:
        schema = sg.schema_field_read(entity, field)
        props = schema[field]["properties"]
        valid = props.get("valid_values", {}).get("value", [])
        display = props.get("display_values", {}).get("value", {})
        print(f"\n=== {entity}.{field} valid_values ({len(valid)}) ===")
        for code in valid:
            print(f"  {code:10s} -> {display.get(code, '?')}")
        return valid
    except Exception as e:
        print(f"ERROR leyendo {entity}.{field}: {e}")
        return []


def main():
    url, login, password = get_flow_credentials()
    if not all([url, login, password]):
        print("ERROR: no se pudieron obtener credenciales de Flow")
        return
    print(f"Conectando a: {url}")
    sg = shotgun_api3.Shotgun(url, login=login, password=password)

    shot_codes = dump_status_field(sg, "Shot", "sg_status_list")
    task_codes = dump_status_field(sg, "Task", "sg_status_list")
    dump_status_field(sg, "Shot", "sg_prioridad")

    # Status entity global: code | name | bg_color (RGB "r,g,b")
    try:
        statuses = sg.find("Status", [], ["code", "name", "bg_color"])
        by_code = {s.get("code"): s for s in statuses}

        def rgb_to_hex(rgb):
            if not rgb:
                return None
            try:
                r, g, b = [int(x) for x in rgb.split(",")[:3]]
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                return rgb

        def print_table(title, codes):
            print(f"\n=== {title} (code | name | bg_color hex) ===")
            for c in codes:
                s = by_code.get(c, {})
                print(f"  {c:10s} | {str(s.get('name')):28s} | {rgb_to_hex(s.get('bg_color'))}")

        print_table("SHOT statuses", shot_codes)
        print_table("TASK statuses", task_codes)
    except Exception as e:
        print(f"ERROR leyendo Status entity: {e}")


if __name__ == "__main__":
    main()
