"""Autenticacion DRF con JWT local (JWKS MS-1)."""

from __future__ import annotations

from types import SimpleNamespace

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from utils.jwt_local import validate_access_token


class AGMJwtUser(SimpleNamespace):
    @property
    def is_authenticated(self):
        return True


class AGMJwtAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith(f'{self.keyword} '):
            return None
        token = auth[len(self.keyword) + 1 :].strip()
        if not token:
            return None
        try:
            user_data = validate_access_token(token)
        except ValueError as exc:
            raise AuthenticationFailed(str(exc)) from exc
        user = AGMJwtUser(
            pk=user_data.user_id,
            user_id=user_data.user_id,
            email=user_data.email,
            nombre=user_data.nombre,
            rol=user_data.rol,
        )
        request.user_id = user_data.user_id
        request.user_rol = user_data.rol
        request.user_email = user_data.email
        request.user_nombre = user_data.nombre
        return (user, token)
