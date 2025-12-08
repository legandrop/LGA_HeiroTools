"""
_______________________________________________________________________________________

LGA_NKS_CleanProject v1.01 | Lega

v1.01: Maneja clips con múltiples BinItems/huérfanos y numera cada eliminación
v1.00: Script extraído desde el panel Clean Project
_______________________________________________________________________________________
"""

import hiero.core
import PySide2.QtWidgets as QtWidgets

# Activar/desactivar logs de depuracion desde este flag
DEBUG = False


def debug_print(*message):
    if DEBUG:
        print(*message)


def get_active_project():
    """Obtiene el primer proyecto activo en Hiero."""
    projects = hiero.core.projects()
    return projects[0] if projects else None


def _clip_info(clip):
    """Devuelve nombre y path para logs amigables."""
    try:
        path = clip.mediaSource().fileinfos()[0].filename()
    except Exception:
        path = "<path desconocido>"
    return clip.name(), path


def _remove_clips(project, clips, start_idx, total_target):
    """Elimina los clips especificados dentro de un bloque de undo.

    Args:
        start_idx (int): indice inicial para numerar logs (1-based).
        total_target (int): total esperado a eliminar (para logs).

    Returns:
        tuple[int, int, int]: (eliminados_ok, eliminados_fallidos, next_idx)
    """
    removed_ok = 0
    removed_fail = 0
    current_idx = start_idx
    debug_print(
        f"[CleanProject] Iniciando batch de eliminación: {len(clips)} items, start_idx={start_idx}, total={total_target}"
    )
    with project.beginUndo("Clean Unused Clips"):
        for clip in list(clips):
            name, path = _clip_info(clip)
            removed_here = 0
            failed_here = 0

            # Algunos clips pueden tener múltiples BinItems; preferimos items() sobre binItem()
            bin_items = []
            try:
                if hasattr(clip, "items"):
                    bin_items = list(clip.items())
            except Exception:
                bin_items = []

            if not bin_items:
                try:
                    single_item = clip.binItem()
                    if single_item:
                        bin_items = [single_item]
                except Exception:
                    bin_items = []

            if not bin_items:
                removed_fail += 1
                debug_print(
                    f"Unable to remove (sin BinItems asociados): {name} | {path}"
                )
                current_idx += 1
                continue

            for idx_in_clip, bin_item in enumerate(bin_items, start=1):
                parent_bin = None
                try:
                    parent_bin = bin_item.parentBin()
                except Exception:
                    parent_bin = None

                if not parent_bin:
                    failed_here += 1
                    debug_print(
                        f"Unable to remove (sin parent_bin) [{idx_in_clip}/{len(bin_items)}]: {name} | {path}"
                    )
                    continue

                debug_print(
                    f"[Removing {current_idx}/{total_target}] {name} | {path} (binItem {idx_in_clip}/{len(bin_items)})"
                )
                try:
                    parent_bin.removeItem(bin_item)
                    removed_here += 1
                except Exception as e:
                    failed_here += 1
                    debug_print(
                        f"Unable to remove: {name} | {path} | binItem {idx_in_clip}/{len(bin_items)} | err={e}"
                    )

            removed_ok += removed_here
            removed_fail += failed_here
            current_idx += 1

    debug_print(
        f"[CleanProject] Batch completado: ok={removed_ok}, fail={removed_fail}, next_idx={current_idx}"
    )
    return removed_ok, removed_fail, current_idx


def _confirm(message, extra_log=None):
    """Muestra un dialogo de confirmacion y devuelve el resultado."""
    if extra_log:
        debug_print(extra_log)
    msg_box = QtWidgets.QMessageBox()
    msg_box.setText("Clean Unused Clips")
    msg_box.setInformativeText(message)
    msg_box.setStandardButtons(
        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
    )
    msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
    return msg_box.exec_()


def _clean_unused_clips(project):
    """Replica la logica original de CleanUnusedAction.CleanUnused con logs y loop."""
    sequences = hiero.core.findItems(project, "Sequences")

    def compute_candidates():
        all_clips = hiero.core.findItems(project, "Clips")
        in_use_count = 0
        candidates = list(all_clips)

        for seq in sequences:
            for track in seq:
                for track_item in track:
                    source = track_item.source()
                    if source in candidates:
                        name, path = _clip_info(source)
                        debug_print(f"[In use] {name} | {path}")
                        candidates.remove(source)
                        in_use_count += 1
        return in_use_count, candidates

    try:
        debug_print(
            f"[CleanProject] Sequences: {len(sequences)} | Clips totales: {len(hiero.core.findItems(project, 'Clips'))}"
        )

        if len(sequences) == 0:
            # Caso sin secuencias: se limpia todo en una sola confirmación
            clips_to_remove = hiero.core.findItems(project, "Clips")
            message = (
                "You have no Sequences in this Project. Do you want to remove all "
                "Clips (%i) from Project: %s?" % (len(clips_to_remove), project.name())
            )
            ret = _confirm(
                message,
                extra_log="[CleanProject] No hay secuencias; todos los clips quedan marcados para eliminar.",
            )
            if ret == QtWidgets.QMessageBox.Cancel:
                debug_print("Cancel")
                return
            removed_ok, removed_fail, _ = _remove_clips(
                project, clips_to_remove, start_idx=1, total_target=len(clips_to_remove)
            )
            debug_print(
                f"[CleanProject] Resumen: eliminados={removed_ok}, fallidos={removed_fail}, restantes=0"
            )
            return

        # Con secuencias: bucle hasta que no haya candidatos o no haya progreso
        in_use, clips_to_remove = compute_candidates()
        debug_print(f"[CleanProject] Clips en uso detectados: {in_use}")

        if clips_to_remove:
            debug_print("[CleanProject] Clips marcados como NO usados:")
            for clip in clips_to_remove:
                name, path = _clip_info(clip)
                debug_print(f"  - {name} | {path}")
        else:
            debug_print("[CleanProject] No se encontraron clips sin uso.")

        message = "Remove %i unused Clips from Project %s?" % (
            len(clips_to_remove),
            project.name(),
        )
        ret = _confirm(
            message,
            extra_log=f"[CleanProject] Clips candidatos a eliminar: {len(clips_to_remove)} (se procesarán en un solo corrido)",
        )
        if ret == QtWidgets.QMessageBox.Cancel:
            debug_print("Cancel")
            return

        total_removed = 0
        total_failed = 0
        total_target = len(clips_to_remove)
        next_idx = 1
        max_loops = 200  # seguridad alta para evitar bucles infinitos

        for loop_idx in range(max_loops):
            if not clips_to_remove:
                break
            removed_ok, removed_fail, next_idx = _remove_clips(
                project,
                clips_to_remove,
                start_idx=next_idx,
                total_target=total_target,
            )
            total_removed += removed_ok
            total_failed += removed_fail

            # Recalcular por si quedaron referencias cruzadas
            in_use, clips_to_remove = compute_candidates()
            debug_print(
                f"[CleanProject] Iteración {loop_idx+1}: in_use={in_use}, pendientes={len(clips_to_remove)}, "
                f"acumulado_eliminados={total_removed}, acumulado_fallidos={total_failed}"
            )

            # Si no hubo progreso, avisar y cortar para no ciclar eternamente
            if removed_ok == 0 and removed_fail == 0:
                debug_print(
                    "[CleanProject] Sin progreso en esta iteración; deteniendo para evitar bucle. "
                    f"Pendientes: {len(clips_to_remove)}"
                )
                break

        debug_print(
            f"[CleanProject] Resumen final: eliminados={total_removed}, fallidos={total_failed}, restantes={len(clips_to_remove)}"
        )
    except Exception as e:
        import traceback

        debug_print(f"[CleanProject] ERROR inesperado: {e}")
        debug_print(traceback.format_exc())


def main(force_all_clips=None):
    """
    Punto de entrada para el panel. El parametro force_all_clips se ignora,
    se deja para compatibilidad con otros scripts del panel.
    """
    debug_print("[CleanProject] Inicio")
    project = get_active_project()
    if not project:
        debug_print("No active project found for cleaning.")
        return False

    _clean_unused_clips(project)
    debug_print("[CleanProject] Fin")
    return True


if __name__ == "__main__":
    main()
