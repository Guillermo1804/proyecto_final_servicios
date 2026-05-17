from functools import wraps

from django.utils.crypto import constant_time_compare
from decouple import config
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from grpc_clients.auth_client import validate_token

_UNAUTHORIZED_MSG = (
    'No autorizado: requiere X-Internal-Api-Key válida o JWT de administrador'
)


def is_internal_api_key_valid(request) -> bool:
    expected = config('INTERNAL_API_KEY', default='')
    provided = request.headers.get('X-Internal-Api-Key', '')
    if not expected:
        return False
    return constant_time_compare(provided, expected)


def _authorize_admin_jwt(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        return None
    try:
        response = validate_token(token)
    except Exception:
        return None
    if not response.valid or response.rol != 'admin':
        return None
    request.user_id = response.user_id
    request.user_rol = response.rol
    request.user_email = response.email
    return True


def check_internal_or_admin(request) -> bool:
    if is_internal_api_key_valid(request):
        return True
    return _authorize_admin_jwt(request) is True


class InternalOrAdminAuthentication(BaseAuthentication):
    """API key interna o JWT admin; sin credenciales → 401 en permisos."""

    www_authenticate_realm = 'internal'

    def authenticate(self, request):
        if is_internal_api_key_valid(request):
            return (None, 'internal')
        if _authorize_admin_jwt(request):
            return (None, 'admin')
        return None

    def authenticate_header(self, request):
        return 'X-Internal-Api-Key'


class IsInternalOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.auth in ('internal', 'admin'):
            return True
        raise AuthenticationFailed(_UNAUTHORIZED_MSG)


def internal_or_admin(view_func):
    """Decorador para function-based views (usar con @api_view)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = InternalOrAdminAuthentication()
        user_auth = auth.authenticate(request)
        if not user_auth:
            raise AuthenticationFailed(_UNAUTHORIZED_MSG)
        request.auth = user_auth[1]
        return view_func(request, *args, **kwargs)

    return wrapper


class InternalOrAdminMixin:
    """Mixin para APIView: valida API key interna o JWT admin."""

    authentication_classes = [InternalOrAdminAuthentication]
    permission_classes = [IsInternalOrAdmin]
