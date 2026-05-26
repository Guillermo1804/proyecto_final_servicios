"""Validacion local de JWT via JWKS de MS-1 (sin gRPC en hot path)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import jwt
from django.conf import settings
from jwt import PyJWKClient, PyJWTError

logger = logging.getLogger(__name__)

_jwk_client: PyJWKClient | None = None
_jwk_client_url: str | None = None
_cached_signing_keys: list | None = None
_cached_signing_keys_at: float = 0.0


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    email: str
    nombre: str
    rol: str


def _get_signing_keys_cached(client: PyJWKClient) -> list:
    global _cached_signing_keys, _cached_signing_keys_at
    ttl = float(getattr(settings, 'JWT_JWKS_CACHE_TTL_SECONDS', 300))
    now = time.time()
    if _cached_signing_keys and (now - _cached_signing_keys_at) < ttl:
        return _cached_signing_keys
    try:
        keys = client.get_signing_keys()
        _cached_signing_keys = keys
        _cached_signing_keys_at = now
        return keys
    except Exception as exc:
        if _cached_signing_keys:
            logger.warning('jwks_stale_fallback', extra={'error': str(exc)})
            return _cached_signing_keys
        raise


def _resolve_signing_key(client: PyJWKClient, token: str):
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')
    keys = _get_signing_keys_cached(client)
    if kid:
        for key in keys:
            if getattr(key, 'key_id', None) == kid:
                return key
        raise ValueError(f'kid no encontrado en JWKS: {kid}')
    if not keys:
        raise ValueError('JWKS sin claves de firma')
    return keys[0]


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client, _jwk_client_url
    url = settings.JWT_JWKS_URL
    ttl = int(getattr(settings, 'JWT_JWKS_CACHE_TTL_SECONDS', 300))
    if _jwk_client is None or _jwk_client_url != url:
        _jwk_client = PyJWKClient(url, cache_keys=True, lifespan=ttl, timeout=10)
        _jwk_client_url = url
    return _jwk_client


def validate_access_token(token: str) -> AuthenticatedUser:
    client = _get_jwk_client()
    try:
        signing_key = _resolve_signing_key(client, token)
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            options={'verify_aud': False},
        )
    except PyJWTError as exc:
        raise ValueError('Token inválido') from exc

    jti = claims.get('jti')
    if jti:
        try:
            from agm_events.jwt_revocation import is_jti_revoked

            if is_jti_revoked(str(jti)):
                raise ValueError('Token revocado')
        except ImportError:
            pass

    user_id = claims.get('user_id') or claims.get('sub')
    if user_id is None:
        raise ValueError('Token sin user_id')
    rol = claims.get('rol', '')
    if not rol:
        raise ValueError('Token sin rol')

    return AuthenticatedUser(
        user_id=int(user_id),
        email=str(claims.get('email', '')),
        nombre=str(claims.get('nombre', '')),
        rol=str(rol),
    )
