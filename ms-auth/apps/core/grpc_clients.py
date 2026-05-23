"""
Cliente gRPC legacy MS-1 -> MS-6 (password reset).

DEPRECATED (Fase 9): con USE_EVENT_BUS=true use password.reset_requested.v1
via outbox. Este modulo solo se usa si USE_EVENT_BUS=false (rollback local).
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import grpc
from decouple import config

logger = logging.getLogger(__name__)

PROTO_GENERATED_DIR = Path(__file__).resolve().parents[2] / 'proto_generated'
if str(PROTO_GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(PROTO_GENERATED_DIR))


def send_reset_password_notification(email, token, reset_url, timeout_seconds=5):
    """Envia notificacion de reseteo via gRPC a MS-6 (ruta legacy)."""
    warnings.warn(
        'send_reset_password_notification gRPC esta deprecado; use el bus de eventos.',
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        import notificaciones_pb2
        import notificaciones_pb2_grpc
    except ImportError:
        logger.warning('Dependencias grpc/protobuf no disponibles para MS-6')
        return False, 'Dependencias grpc/protobuf no disponibles'

    host = config('MS_NOTIFICACIONES_GRPC_HOST', default='ms-notificaciones')
    port = config('MS_NOTIFICACIONES_GRPC_PORT', default='50056')
    target = f'{host}:{port}'
    timeout = float(config('GRPC_CLIENT_TIMEOUT', default=timeout_seconds))

    try:
        with grpc.insecure_channel(target) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            response = stub.SendResetPassword(
                notificaciones_pb2.SendResetPasswordRequest(
                    email=email,
                    token=token,
                    reset_url=reset_url,
                ),
                timeout=timeout,
            )
            if not response.success:
                return False, response.message or 'Error MS-6'
            return True, response.message or 'OK'
    except grpc.RpcError as exc:
        logger.warning('MS-6 gRPC reset password: %s', exc.details())
        return False, exc.details() or 'MS-6 no disponible'
