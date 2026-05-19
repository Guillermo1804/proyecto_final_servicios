import logging

import grpc
from decouple import config
from proto_generated import periodos_pb2, periodos_pb2_grpc

logger = logging.getLogger(__name__)


def _periodos_target() -> str:
    host = config('MS_PERIODOS_GRPC_HOST', default='ms-periodos')
    port = config('MS_PERIODOS_GRPC_PORT', default='50052')
    return f'{host}:{port}'


def _grpc_timeout() -> float:
    return float(config('GRPC_CLIENT_TIMEOUT', default=5))


def get_materia_docente_id(materia_id: int) -> int | None:
    """Obtiene usuario_id del docente titular desde MS-2."""
    if materia_id <= 0:
        return None
    try:
        with grpc.insecure_channel(_periodos_target()) as channel:
            stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
            info = stub.GetMateriaById(
                periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id),
                timeout=_grpc_timeout(),
            )
            if info.id and info.docente_id:
                return info.docente_id
            return None
    except grpc.RpcError as exc:
        logger.warning(
            'MS-2 GetMateriaById falló para materia %s: %s',
            materia_id,
            exc.code(),
        )
        return None
    except Exception as exc:
        logger.error('Error inesperado consultando materia %s: %s', materia_id, exc)
        return None
