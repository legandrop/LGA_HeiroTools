# _________________________________________________
#
#   LGA_BuscarRec709_EnTodosClips v1.0
#   Recorre TODOS los clips del proyecto,
#   no solo los del bin.
# _________________________________________________

import hiero.core


def extraer_colorspace_desde_read(clip):
    try:
        read_node = clip.readNode()
        if read_node and "colorspace" in read_node.knobs():
            return read_node["colorspace"].value()
    except:
        pass
    return None


def main():
    for proyecto in hiero.core.projects():
        print(f"\n📁 Explorando proyecto: {proyecto.name()}")
        encontrados = 0
        for clip in proyecto.clips():
            cs = extraer_colorspace_desde_read(clip)
            if cs and cs.lower() == "rec709":
                try:
                    path = clip.mediaSource().firstpath()
                except:
                    path = "(sin path)"
                print(f" 🎯 {clip.name()} → rec709\n    📍 {path}")
                encontrados += 1
        if not encontrados:
            print(" ✅ No se encontraron clips con colorspace 'rec709'.")


# Ejecutar
main()
