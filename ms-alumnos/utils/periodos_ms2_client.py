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


def _materia_detail_from_inscripcion(materia_id: int) -> dict | None:
    """Datos desnormalizados en inscripciones (sin gRPC cuando USE_EVENT_BUS=true)."""
    from apps.core.models import InscripcionMateria

    row = (
        InscripcionMateria.objects.filter(materia_id=materia_id)
        .order_by("-id")
        .first()
    )
    if row is None:
        return None
    return {
        "id": materia_id,
        "nrc": row.nrc or "",
        "nombre": row.nombre_materia or "",
        "seccion": "",
        "clave": "",
        "docente_nombre": row.docente_nombre or "",
        "docente_id": 0,
        "horario": row.horario or "",
        "periodo_id": 0,
        "periodo_nombre": "",
    }


def get_materia_detail(materia_id: int) -> dict | None:
    """
    Detalle de materia: proyección local (event bus) o GetMateriaById gRPC (legacy).
    """
    materia_id = int(materia_id or 0)
    if materia_id <= 0:
        return None

    if getattr(settings, "USE_EVENT_BUS", False):
        return _materia_detail_from_inscripcion(materia_id)

    try:
        stub = get_periodos_stub()
        request = periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id)
        response = stub.GetMateriaById(request, timeout=3)
        return {
            "id": response.id,
            "nrc": response.nrc,
            "nombre": response.nombre,
            "seccion": response.seccion,
            "clave": response.clave,
            "docente_nombre": response.docente_nombre,
            "docente_id": response.docente_id,
            "horario": response.horario,
            "periodo_id": response.periodo_id,
            "periodo_nombre": response.periodo_nombre,
        }
    except grpc.RpcError as exc:
        logger.warning("MS-2 GetMateriaById falló por gRPC: %s", exc.code())
        return None
    except Exception as exc:
        logger.error("Error inesperado en GetMateriaById MS-2: %s", exc)
        return None
