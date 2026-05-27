from functools import wraps

from rest_framework.response import Response

from utils.jwt_local import validate_access_token


def validate_token(token: str, *, roles=None):
    """
    Valida JWT localmente vía JWKS de MS-1.

    Returns:
        AuthenticatedUser si el token es válido.

    Raises:
        ValueError: token vacío, inválido o rol no permitido.
    """
    token = (token or '').strip()
    if not token:
        raise ValueError('Token requerido')

    user = validate_access_token(token)
    if roles and user.rol not in roles:
        raise ValueError('Sin permisos')
    return user


def jwt_required(roles=None):
    """Decorador DRF: valida Bearer JWT vía JWKS e inyecta user_id, user_rol, user_email."""

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
                user = validate_token(token, roles=roles)
                request.user_id = user.user_id
                request.user_rol = user.rol
                request.user_email = user.email
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
            return fn(self, request, *args, **kwargs)

        return wrapper

    return decorator
