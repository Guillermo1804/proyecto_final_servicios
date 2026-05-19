import grpc

from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.errors import map_rpc_error
from proto_generated import auth_pb2, auth_pb2_grpc


def get_auth_stub() -> auth_pb2_grpc.AuthServiceStub:
    channel = get_channel(
        'auth',
        'MS_AUTH_GRPC_HOST',
        'MS_AUTH_GRPC_PORT',
        'ms-auth',
        '50051',
    )
    return auth_pb2_grpc.AuthServiceStub(channel)


def validate_token(token: str) -> auth_pb2.ValidateTokenResponse:
    """
    Valida JWT contra MS-1 (AuthService.ValidateToken).
    """
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
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            from apps.notificaciones.exceptions import UpstreamUnavailable
            raise UpstreamUnavailable('ms-auth', 'Timeout al validar token') from exc
        from apps.notificaciones.exceptions import UpstreamGrpcError
        raise UpstreamGrpcError('ms-auth', code.name, exc.details() or '') from exc
