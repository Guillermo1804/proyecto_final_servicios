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
_cache_stats = {"jwks_fetch": 0, "signing_key_cache_hit": 0, "jwks_stale_fallback": 0}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    email: str
    nombre: str
    rol: str


def _get_signing_keys_cached(client: PyJWKClient) -> list:
    global _cached_signing_keys, _cached_signing_keys_at
    ttl = float(getattr(settings, "JWT_JWKS_CACHE_TTL_SECONDS", 300))
    now = time.time()
    if _cached_signing_keys and (now - _cached_signing_keys_at) < ttl:
        return _cached_signing_keys
    try:
        keys = client.get_signing_keys()
        _cached_signing_keys = keys
        _cached_signing_keys_at = now
        _cache_stats["jwks_fetch"] += 1
        logger.info(
            "jwks_keys_refreshed",
            extra={"key_count": len(keys), "cache_ttl_seconds": ttl},
        )
        return keys
    except Exception as exc:
        if _cached_signing_keys:
            _cache_stats["jwks_stale_fallback"] += 1
            logger.warning(
                "jwks_refresh_failed_using_stale_cache",
                extra={"error": str(exc)},
            )
            return _cached_signing_keys
        raise


def _resolve_signing_key(client: PyJWKClient, token: str):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    keys = _get_signing_keys_cached(client)
    if kid:
        for key in keys:
            if getattr(key, "key_id", None) == kid:
                return key
        raise ValueError(f"kid no encontrado en JWKS: {kid}")
    if not keys:
        raise ValueError("JWKS sin claves de firma")
    if len(keys) == 1:
        return keys[0]
    alg = header.get("alg", "RS256")
    for key in keys:
        if getattr(key, "key_id", None) and getattr(key, "_jwk_data", {}).get("alg") == alg:
            return key
    return keys[0]


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client, _jwk_client_url
    url = settings.JWT_JWKS_URL
    ttl = int(getattr(settings, "JWT_JWKS_CACHE_TTL_SECONDS", 300))
    if _jwk_client is None or _jwk_client_url != url:
        logger.info(
            "jwks_client_init",
            extra={"jwks_url": url, "cache_ttl_seconds": ttl},
        )
        _jwk_client = PyJWKClient(
            url,
            cache_keys=True,
            lifespan=ttl,
            timeout=10,
        )
        _jwk_client_url = url
    return _jwk_client


def validate_access_token(token: str) -> AuthenticatedUser:
    client = _get_jwk_client()
    started = time.perf_counter()
    try:
        signing_key = _resolve_signing_key(client, token)
        _cache_stats["signing_key_cache_hit"] += 1
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except PyJWTError as exc:
        logger.warning("jwt_validation_failed", extra={"error": str(exc)})
        raise ValueError("Token inválido") from exc

    user_id = claims.get("user_id") or claims.get("sub")
    if user_id is None:
        raise ValueError("Token sin user_id")

    email = claims.get("email", "")
    nombre = claims.get("nombre", "")
    rol = claims.get("rol", "")
    if not rol:
        raise ValueError("Token sin rol")

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "jwt_validated_local",
        extra={
            "user_id": int(user_id),
            "rol": rol,
            "elapsed_ms": elapsed_ms,
            "jwks_url": settings.JWT_JWKS_URL,
            "validation_mode": "offline_jwks",
            "signing_key_resolutions": _cache_stats["signing_key_cache_hit"],
            "jwks_stale_fallback": _cache_stats["jwks_stale_fallback"],
        },
    )
    return AuthenticatedUser(
        user_id=int(user_id),
        email=str(email),
        nombre=str(nombre),
        rol=str(rol),
    )
