import logging
import os
import sys
import grpc

# Dynamically add proto_generated to sys.path to avoid ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

from proto_generated import periodos_pb2
from grpc_clients.periodos_client import get_periodos_stub

logger = logging.getLogger(__name__)


def get_materia_detail(materia_id: int) -> dict | None:
    """
    Llama a GetMateriaById gRPC de ms-periodos con timeout 3s.
    Retorna un diccionario con los datos o None en caso de fallo.
    """
    try:
        stub = get_periodos_stub()
        request = periodos_pb2.GetMateriaByIdRequest(materia_id=int(materia_id))
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
