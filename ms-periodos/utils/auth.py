import grpc
from functools import wraps
from rest_framework.response import Response

from grpc_clients.auth_client import get_auth_stub
from proto_generated import auth_pb2


def jwt_required(roles=None):
    """
    Decorador que valida JWT vía gRPC a MS-1 (AuthService.ValidateToken).
    Inyecta request.user_id, request.user_rol, request.user_email.
    5s timeout → DEADLINE_EXCEEDED → 503.
    Mock en tests: @patch("utils.auth.get_auth_stub")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(self, request, *args, **kwargs):
            token = (
                request.headers.get("Authorization", "")
                .replace("Bearer ", "")
                .strip()
            )
            if not token:
                return Response(
                    {
                        "success": False,
                        "data": None,
                        "message": "Token requerido",
                        "errors": {},
                    },
                    status=401,
                )
            try:
                response = get_auth_stub().ValidateToken(
                    auth_pb2.ValidateTokenRequest(token=token), timeout=5
                )
                if not response.valid:
                    return Response(
                        {
                            "success": False,
                            "data": None,
                            "message": "Token inválido",
                            "errors": {},
                        },
                        status=401,
                    )
                if roles and response.rol not in roles:
                    return Response(
                        {
                            "success": False,
                            "data": None,
                            "message": "Sin permisos",
                            "errors": {},
                        },
                        status=403,
                    )
                request.user_id = response.user_id
                request.user_rol = response.rol
                request.user_email = response.email
            except grpc.RpcError as e:
                status_code = (
                    503
                    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED
                    else 401
                )
                message = (
                    "Auth no disponible"
                    if status_code == 503
                    else "Error auth"
                )
                return Response(
                    {
                        "success": False,
                        "data": None,
                        "message": message,
                        "errors": {},
                    },
                    status=status_code,
                )
            return fn(self, request, *args, **kwargs)
        return wrapper
    return decorator
