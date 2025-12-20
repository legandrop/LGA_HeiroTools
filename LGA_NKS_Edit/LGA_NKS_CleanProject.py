# LGA_NKS_CleanProject.py - Limpieza Segura de Clips en Hiero/Nuke
# Script principal de producción para limpiar clips no utilizados y versiones offline

import hiero
import hiero.core.find_items
import os

def get_all_sequences(project):
    """Obtiene todas las secuencias del proyecto para verificar uso de clips"""
    sequences = []
    try:
        sequences = hiero.core.findItems(project, "Sequences")
        print(f"📋 Encontradas {len(sequences)} secuencias en el proyecto")
    except Exception as e:
        print(f"⚠️ Error obteniendo secuencias: {e}")
    return sequences

def is_clip_used_in_sequences(clip_item, sequences):
    """
    Verifica si un clip está siendo usado en alguna secuencia
    Retorna True si se usa, False si no se usa
    """
    if not sequences:
        return False

    try:
        # Para clips normales, verificar si aparecen en timelines
        for sequence in sequences:
            if hasattr(sequence, 'videoTracks'):
                for track in sequence.videoTracks():
                    for track_item in track.items():
                        if hasattr(track_item, 'source'):
                            source_clip = track_item.source()
                            if source_clip and source_clip == clip_item:
                                return True

        # Para clips .nk (composiciones), verificar referencias adicionales
        clip_name = clip_item.name() if hasattr(clip_item, 'name') else ""
        if clip_name.endswith('.nk'):
            # Verificar si el archivo .nk existe y es referenciado
            try:
                if hasattr(clip_item, 'mediaSource') and clip_item.mediaSource():
                    media_source = clip_item.mediaSource()
                    if hasattr(media_source, 'isMediaPresent') and media_source.isMediaPresent():
                        # Si el archivo .nk existe, asumir que puede estar siendo usado
                        # (más conservador para composiciones)
                        return True
            except:
                pass

    except Exception as e:
        print(f"⚠️ Error verificando uso del clip: {e}")

    return False

def is_version_used_in_sequences(version, sequences):
    """
    Verifica si una versión específica está siendo usada en secuencias
    """
    if not sequences:
        return False

    try:
        # Obtener el clip real de la versión
        if hasattr(version, 'item'):
            clip_item = version.item()
            return is_clip_used_in_sequences(clip_item, sequences)
    except Exception as e:
        print(f"⚠️ Error verificando uso de versión: {e}")

    return False

def check_version_status(version):
    """
    Verifica el estado online/offline de una versión usando la API nativa de Hiero
    Retorna: (status, details)
    """
    status = "UNKNOWN"
    details = ""

    try:
        # Usar API nativa de Hiero: version.item().mediaSource().isMediaPresent()
        if hasattr(version, "item"):
            clip_item = version.item()
            if clip_item and hasattr(clip_item, "mediaSource"):
                media_source = clip_item.mediaSource()
                if media_source and hasattr(media_source, "isMediaPresent"):
                    if media_source.isMediaPresent():
                        status = "ONLINE"
                        details = "Media present (Hiero API)"
                    else:
                        status = "OFFLINE"
                        details = "Media not present (Hiero API)"

                    # Información adicional
                    if hasattr(media_source, "isOffline"):
                        is_offline = media_source.isOffline()
                        details += f" | isOffline: {is_offline}"

                    # Intentar obtener path del archivo
                    if hasattr(media_source, "fileinfos") and media_source.fileinfos():
                        try:
                            file_info = media_source.fileinfos()[0]
                            if hasattr(file_info, "filename"):
                                file_path = file_info.filename()
                                details += f" | Path: {file_path}"
                        except:
                            pass
                else:
                    status = "OFFLINE"
                    details = "No MediaSource disponible"
            else:
                status = "OFFLINE"
                details = "No clip item disponible"
        else:
            status = "OFFLINE"
            details = "No item() method disponible"

    except Exception as e:
        status = "ERROR"
        details = f"Exception: {e}"

    return status, details

def clean_unused_clips(project):
    """
    OBJETIVO 1: Eliminar todos los clips que NO estén siendo usados en ninguna secuencia
    Incluyendo clips .nk (composiciones) - detectados por separado
    """
    print("🧹 OBJETIVO 1: LIMPIANDO CLIPS NO UTILIZADOS")
    print("=" * 60)

    sequences = get_all_sequences(project)
    removed_clips = 0
    processed_clips = 0

    # Procesar todos los BinItems del proyecto
    for bin_item in hiero.core.findItems(project, "BinItems"):
        if not bin_item or not hasattr(bin_item, "name"):
            continue

        bin_name = bin_item.name()
        processed_clips += 1

        print(f"\n🔍 Verificando clip: {bin_name}")

        # Verificar si es una composición .nk
        is_nuke_comp = bin_name.endswith('.nk')

        # Verificar si el clip está siendo usado
        is_used = False

        # Para BinItems con versiones, verificar si alguna versión se usa
        if hasattr(bin_item, 'items'):
            try:
                versions = bin_item.items()
                if versions:
                    # Verificar si alguna versión del clip se usa en secuencias
                    for version in versions:
                        if is_version_used_in_sequences(version, sequences):
                            is_used = True
                            break
                else:
                    # BinItem sin versiones, verificar directamente
                    is_used = is_clip_used_in_sequences(bin_item, sequences)
            except:
                is_used = is_clip_used_in_sequences(bin_item, sequences)
        else:
            # BinItem sin método items
            is_used = is_clip_used_in_sequences(bin_item, sequences)

        # Reporte del resultado
        if is_used:
            if is_nuke_comp:
                print(f"  ✅ Conservando composición .nk (en uso): {bin_name}")
            else:
                print(f"  ✅ Conservando clip (en uso): {bin_name}")
        else:
            # ELIMINAR CLIP NO UTILIZADO
            try:
                # Obtener el bin contenedor para eliminar el item
                parent_bin = None
                for bin_container in hiero.core.findItems(project, "Bins"):
                    if hasattr(bin_container, 'items') and bin_item in bin_container.items():
                        parent_bin = bin_container
                        break

                if parent_bin:
                    parent_bin.removeItem(bin_item)
                    removed_clips += 1
                    if is_nuke_comp:
                        print(f"  🗑️ Eliminada composición .nk no utilizada: {bin_name}")
                    else:
                        print(f"  🗑️ Eliminado clip no utilizado: {bin_name}")
                else:
                    print(f"  ⚠️ No se pudo encontrar contenedor para eliminar: {bin_name}")

            except Exception as e:
                print(f"  ❌ Error eliminando clip {bin_name}: {e}")

    print(f"\n📊 RESULTADO OBJETIVO 1:")
    print(f"  • Clips procesados: {processed_clips}")
    print(f"  • Clips eliminados: {removed_clips}")
    print(f"  • Clips conservados: {processed_clips - removed_clips}")

    return removed_clips

def clean_offline_versions(project):
    """
    OBJETIVO 2: Eliminar versiones offline de clips que tengan múltiples versiones
    Solo si tienen al menos una versión online. Si todas están offline, no eliminar ninguna.
    """
    print("\n🧽 OBJETIVO 2: LIMPIANDO VERSIONES OFFLINE")
    print("=" * 60)

    sequences = get_all_sequences(project)
    total_versions_removed = 0
    processed_bin_items = 0

    # Procesar todos los BinItems que tienen versiones
    for bin_item in hiero.core.findItems(project, "BinItems"):
        if not bin_item or not hasattr(bin_item, "name"):
            continue

        if not hasattr(bin_item, 'items'):
            continue

        bin_name = bin_item.name()
        processed_bin_items += 1

        print(f"\n🔍 Analizando versiones del clip: {bin_name}")

        try:
            versions = bin_item.items()
            if len(versions) <= 1:
                print(f"  ⏭️ Saltando (solo {len(versions)} versión)")
                continue

            # Obtener versión activa
            active_version = None
            try:
                active_version = bin_item.activeVersion()
            except:
                pass

            # Analizar estado de todas las versiones
            online_versions = []
            offline_versions = []
            versions_to_remove = []

            print(f"  📋 Analizando {len(versions)} versiones:")

            for version in versions:
                if not hasattr(version, "name"):
                    continue

                version_name = version.name()
                is_active = (active_version and version == active_version)
                is_used = is_version_used_in_sequences(version, sequences)

                # Verificar estado online/offline
                status, details = check_version_status(version)

                # Categorizar versión
                if status == "ONLINE":
                    online_versions.append(version)
                    print(f"    🟢 {version_name}: ONLINE - {details}")
                elif status == "OFFLINE":
                    offline_versions.append(version)
                    print(f"    🔴 {version_name}: OFFLINE - {details}")

                    # Candidata para eliminación si cumple criterios
                    if not is_active and not is_used:
                        versions_to_remove.append((version_name, version, details))
                else:
                    print(f"    ❓ {version_name}: {status} - {details}")

            # VALIDACIÓN DE SEGURIDAD: Solo eliminar si hay al menos una versión online
            if len(online_versions) == 0:
                print(f"  ⚠️ NO SE ELIMINA NADA: Todas las versiones están offline")
                continue

            # Eliminar versiones offline candidatas
            if versions_to_remove:
                print(f"  🗑️ Eliminando {len(versions_to_remove)} versiones offline:")

                removed_count = 0
                for version_name, version, details in versions_to_remove:
                    try:
                        bin_item.removeVersion(version)
                        print(f"    ✓ Eliminada: {version_name}")
                        removed_count += 1
                    except Exception as e:
                        print(f"    ✗ Error eliminando {version_name}: {e}")

                total_versions_removed += removed_count

                # Verificar versiones restantes
                try:
                    remaining_versions = bin_item.items()
                    print(f"  📊 Versiones restantes: {len(remaining_versions)}")
                except:
                    print(f"  📊 Versiones restantes: desconocido")
            else:
                print(f"  ✅ No hay versiones offline para eliminar")

        except Exception as e:
            print(f"  ❌ Error procesando {bin_name}: {e}")

    print(f"\n📊 RESULTADO OBJETIVO 2:")
    print(f"  • BinItems procesados: {processed_bin_items}")
    print(f"  • Versiones eliminadas: {total_versions_removed}")

    return total_versions_removed

def main():
    """
    Función principal: Ejecuta la limpieza completa del proyecto
    """
    print("🚀 LGA_NKS_CleanProject.py - Limpieza Segura de Clips en Hiero/Nuke")
    print("=" * 80)

    # Verificar proyecto activo
    projects = hiero.core.projects()
    if not projects:
        print("❌ ERROR: No hay proyecto activo en Hiero")
        return

    project = projects[0]
    print(f"📂 Proyecto: {project.name()}")
    print(f"🎯 Ejecutando limpieza completa...")
    print()

    total_clips_removed = 0
    total_versions_removed = 0

    try:
        # OBJETIVO 1: Eliminar clips no utilizados
        total_clips_removed = clean_unused_clips(project)

        # OBJETIVO 2: Eliminar versiones offline
        total_versions_removed = clean_offline_versions(project)

        # RESUMEN FINAL
        print("\n" + "=" * 80)
        print("🎉 LIMPIEZA COMPLETA FINALIZADA")
        print("=" * 80)
        print(f"📊 RESUMEN:")
        print(f"  • Clips eliminados (no utilizados): {total_clips_removed}")
        print(f"  • Versiones offline eliminadas: {total_versions_removed}")
        print(f"  • Total elementos limpiados: {total_clips_removed + total_versions_removed}")

        if total_clips_removed + total_versions_removed > 0:
            print("\n✅ Limpieza exitosa - Proyecto optimizado")
        else:
            print("\nℹ️ No se encontraron elementos para limpiar")

    except Exception as e:
        print(f"\n❌ ERROR durante la limpieza: {e}")
        print("🔄 Se recomienda verificar el estado del proyecto")

# Ejecutar la limpieza
if __name__ == "__main__":
    main()