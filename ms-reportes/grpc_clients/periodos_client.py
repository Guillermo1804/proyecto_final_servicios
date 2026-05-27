import grpc

from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.exceptions import map_rpc_error
from proto_generated import periodos_pb2, periodos_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc


def get_periodos_stub() -> periodos_pb2_grpc.PeriodosServiceStub:
    block_business_grpc('periodos_client.py.get_periodos_stub')
    channel = get_channel(
        'periodos',
        'MS_PERIODOS_GRPC_HOST',
        'MS_PERIODOS_GRPC_PORT',
        'ms-periodos',
        '50052',
    )
    return periodos_pb2_grpc.PeriodosServiceStub(channel)


def get_materia_by_id(materia_id: int) -> periodos_pb2.MateriaInfo:
    block_business_grpc('periodos_client.py.get_materia_by_id')
    try:
        return get_periodos_stub().GetMateriaById(
            periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-periodos', entity='materia', entity_id=materia_id)


def get_materias_by_docente(docente_id: int) -> periodos_pb2.MateriasListResponse:
    block_business_grpc('periodos_client.py.get_materias_by_docente')
    try:
        return get_periodos_stub().GetMateriasByDocente(
            periodos_pb2.GetMateriasByDocenteRequest(docente_id=docente_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-periodos', entity='materia', entity_id=docente_id)


def get_periodo_activo() -> periodos_pb2.PeriodoInfo:
    block_business_grpc('periodos_client.py.get_periodo_activo')
    try:
        return get_periodos_stub().GetPeriodoActivo(
            periodos_pb2.GetPeriodoActivoRequest(),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-periodos', entity='materia', entity_id=0)
