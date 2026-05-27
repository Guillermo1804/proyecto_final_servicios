"""Construccion de payloads de dominio para el bus."""

from __future__ import annotations

from apps.core.models import Alumno, Docente, InscripcionMateria


def alumno_display_name(alumno: Alumno) -> str:
    return f"{alumno.nombre} {alumno.apellido}".strip()


def alumno_imported_payload(
    alumno: Alumno,
    *,
    materia_id: int,
    periodo_id: int,
    docente_email: str,
    clave_acceso: str = "",
    docente_nombre: str = "",
    materia_nombre: str = "",
    nrc: str = "",
) -> dict:
    return {
        "alumno_id": alumno.id,
        "email": alumno.email,
        "nombre": alumno_display_name(alumno),
        "matricula": alumno.matricula,
        "materia_id": int(materia_id or 0),
        "docente_email": docente_email or "",
        "periodo_id": int(periodo_id or 0),
        "clave_acceso": clave_acceso or "",
        "docente_nombre": docente_nombre or "",
        "materia_nombre": materia_nombre or "",
        "nrc": nrc or "",
    }


def alumno_updated_payload(alumno: Alumno) -> dict:
    return {
        "alumno_id": alumno.id,
        "email": alumno.email,
        "nombre": alumno_display_name(alumno),
        "matricula": alumno.matricula,
        "carrera": alumno.carrera,
        "semestre": alumno.semestre,
        "activo": alumno.activo,
        "usuario_id": alumno.usuario_id,
    }


def alumno_withdrawn_payload(
    inscripcion: InscripcionMateria,
    *,
    periodo_id: int,
    docente_email: str,
    docente_id: int = 0,
) -> dict:
    alumno = inscripcion.alumno
    return {
        "alumno_id": alumno.id,
        "email": alumno.email,
        "nombre": alumno_display_name(alumno),
        "matricula": alumno.matricula,
        "materia_id": inscripcion.materia_id,
        "docente_email": docente_email or "",
        "periodo_id": int(periodo_id or 0),
        "docente_id": int(docente_id or 0),
        "docente_nombre": inscripcion.docente_nombre or "",
        "materia_nombre": inscripcion.nombre_materia or "",
        "nrc": inscripcion.nrc or "",
        "fecha_baja": inscripcion.fecha_baja.isoformat() if inscripcion.fecha_baja else None,
    }


def docente_imported_payload(
    docente: Docente,
    *,
    temporary_password: str,
) -> dict:
    return {
        "docente_id": docente.id,
        "email": docente.email,
        "nombre": docente.nombre,
        "apellido": docente.apellido,
        "departamento": docente.departamento or "",
        "temporary_password": temporary_password,
    }
