import hiero.core
import hiero.ui

# =============================================================
# HALLAZGOS: Insertar un track en posicion especifica en Hiero
# =============================================================
#
# La API de Hiero NO tiene insertTrack() ni addTrack(track, index).
# El unico metodo disponible es:
#   seq.addTrack(track)   -> siempre agrega al tope (indice maximo)
#   seq.removeTrack(track)
#
# WORKAROUND (unica solucion):
#   1. Obtener la lista actual: video_tracks = list(seq.videoTracks())
#      -> videoTracks() devuelve de abajo hacia arriba (index 0 = fondo)
#
#   2. Determinar insert_at = trackIndex() del track de referencia
#      El nuevo track va en ese indice, empujando los demas hacia arriba.
#
#      Ejemplo: insertar dPlate debajo de bPlate
#        bPlate esta en idx 1
#        insert_at = 1
#        new_list = tracks[:1] + [dPlate] + tracks[1:]
#        resultado: [EditRef(0), dPlate(1), bPlate(2), aPlate(3), ...]
#
#   3. Remover todos los tracks y re-agregar en el nuevo orden:
#        for t in video_tracks: seq.removeTrack(t)
#        for t in new_list:     seq.addTrack(t)
#      addTrack apila de abajo hacia arriba: el primero queda en idx 0.
#
# ORDEN ALFABETICO DE PLATES (bottom to top en Hiero panel):
#   Los plates se leen de arriba hacia abajo en el panel (aPlate arriba).
#   Por eso el orden alfabetico en videoTracks() es DESCENDENTE:
#     [N]   aPlate   <- mayor indice (mas alto en el panel)
#     [N-1] bPlate
#     [N-2] cPlate
#     [N-3] dPlate   <- menor indice entre los plates (mas bajo en el panel)
#
#   Para insertar un nuevo plate hay que releer videoTracks() en ese momento
#   ya que el stack puede haber cambiado. No reutilizar indices anteriores.
#
# IMPORTANTE: Envolver siempre en project.beginUndo() / endUndo()
# para que el usuario pueda deshacer con Ctrl+Z.
# =============================================================

NEW_TRACK_NAME = "dPlate"
# dPlate va justo debajo de bPlate (entre EditRef y bPlate)
INSERT_BELOW = "bPlate"  # el nuevo track va debajo de este

def print_track_order(seq, label=""):
    tracks = seq.videoTracks()
    print(f"\n  --- {label} ---")
    for t in tracks:
        marker = " <-- NUEVO" if t.name() == NEW_TRACK_NAME else ""
        print(f"  [{t.trackIndex()}] {t.name()}{marker}")

def get_track_by_name(seq, name):
    for t in seq.videoTracks():
        if t.name() == name:
            return t
    return None

def remove_test_track(seq, project):
    t = get_track_by_name(seq, NEW_TRACK_NAME)
    if t:
        with project.beginUndo("Remove test track"):
            seq.removeTrack(t)
        print(f"  -> '{NEW_TRACK_NAME}' removido")

# -------------------------------------------------------

seq = hiero.ui.activeSequence()
if not seq:
    print("No hay secuencia activa.")
else:
    project = seq.project()

    ref_track = get_track_by_name(seq, INSERT_BELOW)
    if not ref_track:
        print(f"No se encontro el track '{INSERT_BELOW}'.")
    else:
        # dPlate va en el indice de bPlate, empujando bPlate y aPlate hacia arriba
        insert_at = ref_track.trackIndex()

        print("=" * 55)
        print(f"Insertando '{NEW_TRACK_NAME}' en indice {insert_at}")
        print(f"(justo debajo de '{INSERT_BELOW}' que esta en idx {ref_track.trackIndex()})")
        print("=" * 55)

        print_track_order(seq, "ORDEN ORIGINAL")

        # Workaround: remove all + reinsert con nuevo track en posicion correcta
        video_tracks = list(seq.videoTracks())
        new_list = video_tracks[:insert_at] + [hiero.core.VideoTrack(NEW_TRACK_NAME)] + video_tracks[insert_at:]

        with project.beginUndo("Test insert dPlate"):
            for t in video_tracks:
                seq.removeTrack(t)
            for t in new_list:
                seq.addTrack(t)

        result = get_track_by_name(seq, NEW_TRACK_NAME)
        landed = result.trackIndex() if result else "?"
        ok = "OK" if landed == insert_at else f"FALLO (esperado {insert_at}, obtuvo {landed})"
        print(f"\n  Resultado: '{NEW_TRACK_NAME}' en indice {landed}  -> {ok}")
        print_track_order(seq, "ORDEN TRAS INSERCION")

        remove_test_track(seq, project)
        print_track_order(seq, "ORDEN FINAL (debe ser igual al original)")
        print("\n" + "=" * 55)
