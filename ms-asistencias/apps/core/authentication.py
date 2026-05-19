"""JWT authentication via MS-1 gRPC (ValidateToken)."""

import grpc
from types import SimpleNamespace

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from grpc_clients import validate_token


class MsJwtAuthentication(BaseAuthentication):
    """Valida Bearer JWT contra MS-1 e inyecta request.user y request.user_id."""

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization") or ""
        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header.split(None, 1)[1].strip() if len(auth_header.split(None, 1)) > 1 else ""
        if not token:
            raise AuthenticationFailed("Token requerido")

        try:
            data = validate_token(token)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise AuthenticationFailed("Auth no disponible") from exc
            raise AuthenticationFailed("Token inválido") from exc

        user = SimpleNamespace(
            id=data.get("user_id"),
            pk=data.get("user_id"),
            is_authenticated=True,
            rol=data.get("role") or data.get("rol"),
            email=data.get("email"),
        )
        request.user_id = data.get("user_id")
        request.user_rol = user.rol
        request.user_email = data.get("email")
        return (user, token)
