import grpc

from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.errors import map_rpc_error
from proto_generated import periodos_pb2, periodos_pb2_grpc


def get_periodos_stub() -> periodos_pb2_grpc.PeriodosServiceStub:
    channel = get_channel(
        'periodos',
        'MS_PERIODOS_GRPC_HOST',
        'MS_PERIODOS_GRPC_PORT',
        'ms-periodos',
        '50052',
    )
    return periodos_pb2_grpc.PeriodosServiceStub(channel)


def get_materia_by_id(materia_id: int) -> periodos_pb2.MateriaInfo:
    try:
        return get_periodos_stub().GetMateriaById(
            periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-periodos', entity='materia', entity_id=materia_id)
        raise
