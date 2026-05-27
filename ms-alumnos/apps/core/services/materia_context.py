"""Contexto de materia/periodo/docente para payloads de eventos."""

from __future__ import annotations

from apps.core.models import Docente
from utils.periodos_ms2_client import get_materia_detail


def resolve_materia_context(
    materia_id: int,
    *,
    fallback_docente_email: str = "",
    fallback_periodo_id: int = 0,
) -> dict:
    """Enriquece datos de materia; tolera MS-2 no disponible."""
    base = {
        "materia_id": int(materia_id or 0),
        "periodo_id": int(fallback_periodo_id or 0),
        "docente_email": fallback_docente_email or "",
        "docente_nombre": "",
        "materia_nombre": "",
        "nrc": "",
        "docente_id": 0,
    }
    if materia_id <= 0:
        return base

    detail = get_materia_detail(materia_id)
    if not detail:
        return base

    docente_id = int(detail.get("docente_id") or 0)
    docente_email = (fallback_docente_email or "").strip()
    if docente_id:
        docente = Docente.objects.filter(usuario_id=docente_id).first()
        if docente and docente.email:
            docente_email = docente.email

    return {
        "materia_id": materia_id,
        "periodo_id": int(detail.get("periodo_id") or fallback_periodo_id or 0),
        "docente_email": docente_email,
        "docente_nombre": detail.get("docente_nombre") or "",
        "materia_nombre": detail.get("nombre") or "",
        "nrc": detail.get("nrc") or "",
        "horario": detail.get("horario") or "",
        "docente_id": docente_id,
    }
