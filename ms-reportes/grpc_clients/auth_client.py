import grpc

from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.exceptions import UpstreamGrpcError, UpstreamUnavailable
from proto_generated import auth_pb2, auth_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc


def get_auth_stub() -> auth_pb2_grpc.AuthServiceStub:
    block_business_grpc('auth_client.py.get_auth_stub')
    channel = get_channel(
        'auth',
        'MS_AUTH_GRPC_HOST',
        'MS_AUTH_GRPC_PORT',
        'ms-auth',
        '50051',
    )
    return auth_pb2_grpc.AuthServiceStub(channel)


def validate_token(token: str) -> auth_pb2.ValidateTokenResponse:
    block_business_grpc('auth_client.py.validate_token')
    """Valida JWT contra MS-1 (AuthService.ValidateToken)."""
    normalized = (token or '').replace('Bearer ', '').strip()
    if not normalized:
        return auth_pb2.ValidateTokenResponse(valid=False)
    try:
        return get_auth_stub().ValidateToken(
            auth_pb2.ValidateTokenRequest(token=normalized),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        code = exc.code()
        if code in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
            raise UpstreamUnavailable('ms-auth', 'Timeout o MS-1 no disponible') from exc
        raise UpstreamGrpcError('ms-auth', code.name, exc.details() or '') from exc
