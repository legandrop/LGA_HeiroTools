import hiero.ui
import inspect


def explorar_clip_seleccionado():
    seq = hiero.ui.activeSequence()
    if not seq:
        print("❌ No hay secuencia activa.")
        return

    te = hiero.ui.getTimelineEditor(seq)
    selected_clips = te.selection()
    if not selected_clips:
        print("❌ No hay clips seleccionados.")
        return

    clip = selected_clips[0]
    print(f"✅ Clip seleccionado: {clip}")
    print("=" * 60)
    print("📌 ATRIBUTOS DEL CLIP:")
    for attr in dir(clip):
        if not attr.startswith("_"):
            try:
                valor = getattr(clip, attr)
                if not inspect.ismethod(valor) and not inspect.isfunction(valor):
                    print(f"• {attr}: {valor}")
            except Exception as e:
                print(f"• {attr}: ⚠️ Error al acceder ({e})")

    print("\n📌 MÉTODOS DEL CLIP:")
    for name, method in inspect.getmembers(clip, predicate=inspect.ismethod):
        if not name.startswith("_"):
            try:
                sig = str(inspect.signature(method))
            except:
                sig = "()"
            print(f"• {name}{sig}")


explorar_clip_seleccionado()
