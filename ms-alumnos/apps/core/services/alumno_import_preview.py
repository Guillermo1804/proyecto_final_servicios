"""Vista previa de importacion PDF (sin persistir)."""

from __future__ import annotations

from apps.core.models import Alumno, InscripcionMateria


def build_alumno_import_preview(
    rows: list[dict],
    materia_id: int,
) -> tuple[list[dict], dict]:
    """
    Enriquece filas parseadas del PDF con accion esperada (nuevo/actualizar/inscripcion).
    No escribe en BD.
    """
    if not rows:
        return [], {
            "total": 0,
            "nuevos": 0,
            "actualizados": 0,
            "inscripciones_nuevas": 0,
            "ya_inscritos": 0,
            "con_email": 0,
            "sin_email": 0,
        }

    matriculas = [str(row.get("matricula") or "").strip() for row in rows if row.get("matricula")]
    existing_by_mat = {
        alumno.matricula: alumno
        for alumno in Alumno.objects.filter(matricula__in=matriculas)
    }

    insc_activas = set(
        InscripcionMateria.objects.filter(
            materia_id=materia_id,
            alumno__matricula__in=matriculas,
            activa=True,
        ).values_list("alumno__matricula", flat=True)
    )
    insc_inactivas = set(
        InscripcionMateria.objects.filter(
            materia_id=materia_id,
            alumno__matricula__in=matriculas,
            activa=False,
        ).values_list("alumno__matricula", flat=True)
    )

    preview_rows: list[dict] = []
    nuevos = 0
    actualizados = 0
    inscripciones_nuevas = 0
    ya_inscritos = 0
    con_email = 0

    for row in rows:
        matricula = str(row.get("matricula") or "").strip()
        if not matricula:
            continue

        existing = existing_by_mat.get(matricula)
        if existing:
            accion = "actualizar"
            actualizados += 1
        else:
            accion = "nuevo"
            nuevos += 1

        if matricula in insc_activas:
            inscripcion = "ya_inscrito"
            ya_inscritos += 1
        elif matricula in insc_inactivas:
            inscripcion = "reactivar"
            inscripciones_nuevas += 1
        else:
            inscripcion = "nueva"
            inscripciones_nuevas += 1

        email = (row.get("email") or "").strip().lower()
        if email:
            con_email += 1

        apellido = row.get("apellido") or ""
        nombre = row.get("nombre") or ""
        nombre_completo = f"{apellido}, {nombre}".strip().strip(",")

        preview_rows.append(
            {
                **row,
                "accion": accion,
                "inscripcion": inscripcion,
                "nombre_completo": nombre_completo,
                "email_actual": (existing.email if existing else "") or "",
                "tiene_usuario_ms1": bool(existing and existing.usuario_id),
            }
        )

    resumen = {
        "total": len(preview_rows),
        "nuevos": nuevos,
        "actualizados": actualizados,
        "inscripciones_nuevas": inscripciones_nuevas,
        "ya_inscritos": ya_inscritos,
        "con_email": con_email,
        "sin_email": len(preview_rows) - con_email,
    }
    return preview_rows, resumen
