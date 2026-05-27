"""Cache en memoria de JTI revocados (evento token.revoked.v1 de MS-1)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_revoked_jti: dict[str, float] = {}
DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 8  # 8 dias


def _purge_expired(now: Optional[float] = None) -> None:
    ts = now if now is not None else time.time()
    expired = [jti for jti, exp in _revoked_jti.items() if exp <= ts]
    for jti in expired:
        del _revoked_jti[jti]


def revoke_jti(jti: str, *, ttl_seconds: Optional[int] = None) -> None:
    if not jti:
        return
    exp = time.time() + (ttl_seconds or DEFAULT_TTL_SECONDS)
    with _lock:
        _revoked_jti[jti] = exp
        _purge_expired()
    logger.info("jwt_jti_revoked", extra={"jti": jti})


def is_jti_revoked(jti: str) -> bool:
    if not jti:
        return False
    now = time.time()
    with _lock:
        _purge_expired(now)
        exp = _revoked_jti.get(jti)
    return exp is not None and exp > now


def apply_token_revoked_payload(payload: Mapping[str, Any]) -> None:
    """Procesa payload token.revoked.v1 (alineado con agm.common.TokenRevocationPayload)."""
    jti = str(payload.get("jti") or "").strip()
    if jti:
        revoke_jti(jti)


def clear_revocation_cache() -> None:
    with _lock:
        _revoked_jti.clear()
