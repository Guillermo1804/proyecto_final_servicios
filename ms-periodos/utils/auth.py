"""Autenticacion HTTP — JWT local (Fase 3, sin gRPC a MS-1)."""

from functools import wraps

from rest_framework.response import Response

from utils.jwt_local import validate_access_token


def jwt_required(roles=None):
    """
    Valida JWT localmente contra JWKS de MS-1 (cache en memoria).
    Inyecta request.user_id, request.user_rol, request.user_email, request.user_nombre.
  Mock en tests: @patch("utils.jwt_local.validate_access_token")
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
                user = validate_access_token(token)
            except ValueError as exc:
                return Response(
                    {
                        "success": False,
                        "data": None,
                        "message": str(exc),
                        "errors": {},
                    },
                    status=401,
                )
            if roles and user.rol not in roles:
                return Response(
                    {
                        "success": False,
                        "data": None,
                        "message": "Sin permisos",
                        "errors": {},
                    },
                    status=403,
                )
            request.user_id = user.user_id
            request.user_rol = user.rol
            request.user_email = user.email
            request.user_nombre = user.nombre
            return fn(self, request, *args, **kwargs)

        return wrapper

    return decorator
