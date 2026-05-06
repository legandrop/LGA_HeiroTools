"""
____________________________________________________________________

  LGA_NKS_Clip_DisableComp v1.00 | Lega

  Habilita o deshabilita el clip en el track _comp_ con fallback al track de review.
  Wrapper de LGA_NKS_Clip_DisableEXR con enable_rev_fallback=True.

  Si el track _comp_ está vacío en el playhead o tiene un clip v00/v000, busca un track
  similar (_compRev_, _compMOV_, _compMXF_, etc.) y opera sobre el clip de ese track.
  Si el track encontrado no coincide con TRACK_comp_REV, ofrece renombrarlo al nombre
  canónico antes de operar.

  v1.00: Versión inicial
____________________________________________________________________

"""

import sys
from pathlib import Path

# Importar main de DisableEXR (mismo directorio)
panel_py_path = Path(__file__).parent
if str(panel_py_path) not in sys.path:
    sys.path.insert(0, str(panel_py_path))
from LGA_NKS_Clip_DisableEXR import main as disable_main


def main():
    disable_main(enable_rev_fallback=True)


if __name__ == "__main__":
    main()
