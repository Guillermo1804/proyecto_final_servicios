import grpc
from functools import wraps

from rest_framework.response import Response

from grpc_clients import auth_client
from grpc_clients.exceptions import UpstreamUnavailable


def validate_token(token: str, *, roles=None):
    """
    Valida JWT contra MS-1 (ValidateToken).

    Returns:
        auth_pb2.ValidateTokenResponse si el token es válido.

    Raises:
        ValueError: token vacío, inválido o rol no permitido.
        UpstreamUnavailable: MS-1 no disponible.
    """
    token = (token or '').strip()
    if not token:
        raise ValueError('Token requerido')

    try:
        response = auth_client.validate_token(token)
    except UpstreamUnavailable:
        raise
    except grpc.RpcError as exc:
        raise UpstreamUnavailable('ms-auth', exc.details() or '') from exc

    if not response.valid:
        raise ValueError('Token inválido')
    if roles and response.rol not in roles:
        raise ValueError('Sin permisos')
    return response


def jwt_required(roles=None):
    """Decorador DRF: valida Bearer JWT vía MS-1 e inyecta user_id, user_rol, user_email."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(self, request, *args, **kwargs):
            token = (
                request.headers.get('Authorization', '')
                .replace('Bearer ', '')
                .strip()
            )
            if not token:
                return Response(
                    {
                        'success': False,
                        'data': None,
                        'message': 'Token requerido',
                        'errors': {},
                    },
                    status=401,
                )
            try:
                response = validate_token(token, roles=roles)
                request.user_id = response.user_id
                request.user_rol = response.rol
                request.user_email = response.email
            except ValueError as exc:
                message = str(exc)
                status_code = 403 if message == 'Sin permisos' else 401
                return Response(
                    {
                        'success': False,
                        'data': None,
                        'message': message,
                        'errors': {},
                    },
                    status=status_code,
                )
            except UpstreamUnavailable:
                return Response(
                    {
                        'success': False,
                        'data': None,
                        'message': 'Auth no disponible',
                        'errors': {},
                    },
                    status=503,
                )
            return fn(self, request, *args, **kwargs)

        return wrapper

    return decorator
