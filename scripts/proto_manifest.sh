#!/bin/bash
# Manifest: agm_common.proto (base) + exposicion del MS + clientes que invoca.

proto_files_for_ms() {
  local ms="$1"
  case "${ms}" in
    ms-auth)
      echo "agm_common.proto auth.proto notificaciones.proto"
      ;;
    ms-periodos)
      echo "agm_common.proto periodos.proto"
      ;;
    ms-alumnos)
      echo "agm_common.proto alumnos.proto auth.proto periodos.proto notificaciones.proto"
      ;;
    ms-calificaciones)
      echo "agm_common.proto calificaciones.proto auth.proto alumnos.proto periodos.proto notificaciones.proto"
      ;;
    ms-asistencias)
      echo "agm_common.proto asistencias.proto auth.proto alumnos.proto"
      ;;
    ms-notificaciones)
      echo "agm_common.proto notificaciones.proto auth.proto alumnos.proto periodos.proto"
      ;;
    ms-reportes)
      echo "agm_common.proto reportes.proto auth.proto alumnos.proto periodos.proto calificaciones.proto asistencias.proto"
      ;;
    *)
      echo "ERROR: MS desconocido: ${ms}" >&2
      return 1
      ;;
  esac
}
