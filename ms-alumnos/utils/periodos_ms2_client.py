import logging
import os
import sys

import grpc
from django.conf import settings

# Dynamically add proto_generated to sys.path to avoid ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

from proto_generated import periodos_pb2
from grpc_clients.periodos_client import get_periodos_stub

logger = logging.getLogger(__name__)


def _detail_from_row(
    materia_id: int,
    *,
    nrc: str,
    nombre: str,
    seccion: str = "",
    clave: str = "",
    docente_nombre: str = "",
    docente_id: int = 0,
    horario: str = "",
    periodo_id: int = 0,
    periodo_nombre: str = "",
) -> dict:
    return {
        "id": materia_id,
        "nrc": nrc or "",
        "nombre": nombre or "",
        "seccion": seccion or "",
        "clave": clave or "",
        "docente_nombre": docente_nombre or "",
        "docente_id": int(docente_id or 0),
        "horario": horario or "",
        "periodo_id": int(periodo_id or 0),
        "periodo_nombre": periodo_nombre or "",
    }


def _detail_is_usable(detail: dict | None) -> bool:
    if not detail:
        return False
    return bool((detail.get("nombre") or "").strip() or (detail.get("nrc") or "").strip())


def _materia_detail_from_projection(materia_id: int) -> dict | None:
    from apps.core.models import MateriaProjection

    row = MateriaProjection.objects.filter(materia_id=materia_id).first()
    if row is None:
        return None
    return _detail_from_row(
        materia_id,
        nrc=row.nrc,
        nombre=row.nombre,
        seccion=row.seccion,
        clave=row.clave,
        docente_nombre=row.docente_nombre,
        docente_id=row.docente_id or 0,
        horario=row.horario,
        periodo_id=row.periodo_id,
        periodo_nombre=row.periodo_nombre,
    )


def _materia_detail_from_inscripcion(materia_id: int) -> dict | None:
    from apps.core.models import InscripcionMateria

    row = (
        InscripcionMateria.objects.filter(materia_id=materia_id)
        .order_by("-id")
        .first()
    )
    if row is None:
        return None
    return _detail_from_row(
        materia_id,
        nrc=row.nrc,
        nombre=row.nombre_materia,
        docente_nombre=row.docente_nombre,
        horario=row.horario,
    )


def _materia_detail_from_grpc(materia_id: int) -> dict | None:
    try:
        stub = get_periodos_stub()
        request = periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id)
        response = stub.GetMateriaById(request, timeout=3)
        return _detail_from_row(
            materia_id,
            nrc=response.nrc,
            nombre=response.nombre,
            seccion=response.seccion,
            clave=response.clave,
            docente_nombre=response.docente_nombre,
            docente_id=response.docente_id,
            horario=response.horario,
            periodo_id=response.periodo_id,
            periodo_nombre=response.periodo_nombre,
        )
    except grpc.RpcError as exc:
        logger.warning("MS-2 GetMateriaById falló por gRPC: %s", exc.code())
        return None
    except Exception as exc:
        logger.error("Error inesperado en GetMateriaById MS-2: %s", exc)
        return None


def get_materia_detail(materia_id: int) -> dict | None:
    """
    Detalle de materia: proyección local (event bus), inscripción desnormalizada o gRPC legacy.
    """
    materia_id = int(materia_id or 0)
    if materia_id <= 0:
        return None

    if getattr(settings, "USE_EVENT_BUS", False):
        detail = _materia_detail_from_projection(materia_id)
        if _detail_is_usable(detail):
            return detail
        detail = _materia_detail_from_inscripcion(materia_id)
        if _detail_is_usable(detail):
            return detail
        return None

    return _materia_detail_from_grpc(materia_id)


def refresh_inscripciones_from_detail(materia_id: int, detail: dict) -> int:
    """Rellena campos vacíos de inscripciones activas con datos de materia."""
    from apps.core.models import InscripcionMateria

    updated = 0
    for insc in InscripcionMateria.objects.filter(materia_id=materia_id, activa=True):
        fields = []
        if not (insc.nrc or "").strip() and detail.get("nrc"):
            insc.nrc = detail["nrc"]
            fields.append("nrc")
        if not (insc.nombre_materia or "").strip() and detail.get("nombre"):
            insc.nombre_materia = detail["nombre"]
            fields.append("nombre_materia")
        if not (insc.docente_nombre or "").strip() and detail.get("docente_nombre"):
            insc.docente_nombre = detail["docente_nombre"]
            fields.append("docente_nombre")
        if not (insc.horario or "").strip() and detail.get("horario"):
            insc.horario = detail["horario"]
            fields.append("horario")
        if fields:
            insc.save(update_fields=fields)
            updated += 1
    return updated
