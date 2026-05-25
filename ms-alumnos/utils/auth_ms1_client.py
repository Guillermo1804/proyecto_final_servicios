"""Cliente MS-1 Auth: HTTP (bus activo) o gRPC (legacy)."""

from __future__ import annotations

import json
import logging
import os
import sys
import urllib.error
import urllib.request

import grpc
from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


def _grpc_timeout() -> float:
    return float(config("GRPC_CLIENT_TIMEOUT", default=5))


def _http_timeout() -> float:
    return float(config("MS_AUTH_HTTP_TIMEOUT", default=10))


def create_user_in_auth(
    email: str,
    nombre: str,
    rol: str,
    password: str,
) -> tuple[int | None, str | None]:
    """
    Crea o vincula usuario en MS-1.
    Con USE_EVENT_BUS=true usa REST interno (no gRPC de negocio).
    """
    if _use_event_bus():
        return _create_user_via_http(email, nombre, rol, password)
    return _create_user_via_grpc(email, nombre, rol, password)


def _create_user_via_http(
    email: str,
    nombre: str,
    rol: str,
    password: str,
) -> tuple[int | None, str | None]:
    api_key = config("INTERNAL_API_KEY", default="").strip()
    if not api_key:
        return (
            None,
            "INTERNAL_API_KEY no configurada en MS-3. Debe coincidir con MS-1 Auth.",
        )

    base_url = config("MS_AUTH_HTTP_URL", default="http://ms-auth:8001").rstrip("/")
    url = f"{base_url}/usuarios"
    payload = {
        "email": email,
        "nombre": nombre,
        "rol": rol,
        "password": password,
        "send_email": False,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Internal-Api-Key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=_http_timeout()) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            raw = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw = {}
        message = raw.get("message")
        if isinstance(message, dict):
            message = str(message)
        return None, str(message or f"MS-1 respondio HTTP {exc.code}")
    except urllib.error.URLError as exc:
        logger.warning("MS-1 CreateUser HTTP fallo: %s", exc)
        return None, f"No se pudo contactar MS-1 Auth: {exc.reason}"
    except Exception as exc:
        logger.error("Error inesperado CreateUser HTTP MS-1: %s", exc)
        return None, str(exc)

    if raw.get("success") and isinstance(raw.get("data"), dict):
        user_id = raw["data"].get("id")
        if user_id:
            return int(user_id), None

    return None, str(raw.get("message") or "No se pudo crear el usuario en MS-1")


def _create_user_via_grpc(
    email: str,
    nombre: str,
    rol: str,
    password: str,
) -> tuple[int | None, str | None]:
    from proto_generated import auth_pb2
    from grpc_clients.auth_client import get_auth_stub

    try:
        stub = get_auth_stub()
        request = auth_pb2.CreateUserRequest(
            email=email,
            nombre=nombre,
            rol=rol,
            password=password,
        )
        response = stub.CreateUser(request, timeout=_grpc_timeout())
        if response.success and response.user_id:
            return response.user_id, None
        return None, response.message or "No se pudo crear el usuario en MS-1"
    except grpc.RpcError as exc:
        logger.warning("MS-1 CreateUser fallo por gRPC: %s", exc.code())
        return None, exc.details() or str(exc)
    except Exception as exc:
        logger.error("Error inesperado CreateUser MS-1: %s", exc)
        return None, str(exc)
