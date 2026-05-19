"""Utilities for MS-5 Asistencias QR.

Redis key patterns and helpers for session/QR management.
"""

import hashlib
import hmac
import json
import time
from typing import Optional, Dict, Any

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone


# ===== REDIS KEY PATTERNS =====

def sesion_redis_key(sesion_id: int) -> str:
    """Key: sesion:{sesion_id} — TTL 600s (10 minutos)."""
    return f"sesion:{sesion_id}"


def qr_used_redis_key(qr_payload_hash: str) -> str:
    """Key: qr_used:{hash} — TTL 60-120s (anti-replay)."""
    return f"qr_used:{qr_payload_hash}"


def active_sesion_by_materia_key(materia_id: int) -> str:
    """Key: active_sesion:materia:{materia_id} — points to sesion_id."""
    return f"active_sesion:materia:{materia_id}"


def stats_key(sesion_id: int) -> str:
    """Key: stats:{sesion_id} — real-time stats (presentes, retardos, etc.)."""
    return f"stats:{sesion_id}"


# ===== SESION REDIS OPERATIONS =====

def store_sesion_in_redis(sesion_id: int, materia_id: int, docente_id: int, 
                          inicio_timestamp: float, ttl: int = 600) -> bool:
    """
    Store session state in Redis for fast lookup.
    
    Args:
        sesion_id: DB session ID
        materia_id: Subject/class ID
        docente_id: Teacher ID
        inicio_timestamp: Unix timestamp of session start (server time)
        ttl: Time-to-live in seconds (default 600s = 10 minutes)
    
    Returns:
        True if stored, False otherwise
    """
    key = sesion_redis_key(sesion_id)
    data = {
        'sesion_id': sesion_id,
        'materia_id': materia_id,
        'docente_id': docente_id,
        'inicio_timestamp': inicio_timestamp,
    }
    
    try:
        cache.set(key, json.dumps(data), timeout=ttl)
        # Also store a pointer: active_sesion:materia:{materia_id} -> sesion_id
        cache.set(active_sesion_by_materia_key(materia_id), sesion_id, timeout=ttl)
        return True
    except Exception as e:
        print(f"Error storing session in Redis: {e}")
        return False


def get_sesion_from_redis(sesion_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve session data from Redis."""
    key = sesion_redis_key(sesion_id)
    try:
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Error retrieving session from Redis: {e}")
        return None


def get_active_sesion_id_by_materia(materia_id: int) -> Optional[int]:
    """Get currently active session ID for a subject."""
    key = active_sesion_by_materia_key(materia_id)
    try:
        sesion_id = cache.get(key)
        return sesion_id if sesion_id else None
    except Exception as e:
        print(f"Error getting active session: {e}")
        return None


def delete_sesion_from_redis(sesion_id: int, materia_id: int) -> bool:
    """Delete session data from Redis."""
    try:
        cache.delete(sesion_redis_key(sesion_id))
        cache.delete(active_sesion_by_materia_key(materia_id))
        # Also delete any stats key for this session
        cache.delete(stats_key(sesion_id))
        return True
    except Exception as e:
        print(f"Error deleting session from Redis: {e}")
        return False


# ===== QR ANTI-REPLAY =====

def mark_qr_as_used(qr_payload_hash: str, ttl: int = 120) -> bool:
    """
    Mark a QR payload as used (anti-replay).
    
    Uses SET key 1 NX EX ttl pattern.
    Returns True if newly set, False if already existed (replay detected).
    """
    key = qr_used_redis_key(qr_payload_hash)
    try:
        # Use add() which is atomic SET...NX
        result = cache.add(key, "1", timeout=ttl)
        return result  # True = newly added (safe), False = already existed (replay)
    except Exception as e:
        print(f"Error marking QR as used: {e}")
        return True  # Conservative: assume safe on error


def qr_payload_hash(payload: Dict[str, Any]) -> str:
    """Generate SHA256 hash of QR payload (for anti-replay tracking)."""
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()


# ===== HMAC SIGNING & VERIFICATION =====

def sign_qr_payload(payload: Dict[str, Any]) -> str:
    """
    Generate HMAC-SHA256 signature for QR payload.
    
    Returns hex digest.
    """
    secret = settings.QR_HMAC_SECRET.encode()
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(secret, payload_str.encode(), hashlib.sha256).hexdigest()
    return signature


def verify_qr_payload(payload: Dict[str, Any], provided_signature: str) -> bool:
    """Verify HMAC signature of QR payload."""
    expected_signature = sign_qr_payload(payload)
    return hmac.compare_digest(expected_signature, provided_signature)


# ===== REAL-TIME STATS =====

def initialize_stats(sesion_id: int) -> bool:
    """Initialize empty stats for a session."""
    key = stats_key(sesion_id)
    stats = {
        'presentes': 0,
        'retardos': 0,
        'ausentes': 0,
    }
    try:
        cache.set(key, json.dumps(stats), timeout=600)  # TTL 10 min
        return True
    except Exception as e:
        print(f"Error initializing stats: {e}")
        return False


def get_stats(sesion_id: int) -> Optional[Dict[str, int]]:
    """Get current stats for a session."""
    key = stats_key(sesion_id)
    try:
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None


def update_stats(sesion_id: int, estado: str) -> bool:
    """
    Increment stats counter for a given attendance state.
    
    Args:
        sesion_id: Session ID
        estado: 'presente', 'retardo', or 'ausente'
    """
    key = stats_key(sesion_id)
    try:
        data = cache.get(key)
        if not data:
            # Initialize if missing
            initialize_stats(sesion_id)
            data = cache.get(key)
        
        stats = json.loads(data) if data else {'presentes': 0, 'retardos': 0, 'ausentes': 0}
        
        if estado in stats:
            stats[estado] += 1
        
        cache.set(key, json.dumps(stats), timeout=600)
        return True
    except Exception as e:
        print(f"Error updating stats: {e}")
        return False
