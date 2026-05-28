from rest_framework import status
from rest_framework.views import APIView

from apps.notificaciones.serializers import (
    BajaSerializer,
    BienvenidaSerializer,
    CierreMateriaSerializer,
    ResetPasswordSerializer,
)
from apps.notificaciones.services.email_service import EmailService
from apps.notificaciones.utils.internal_auth import InternalOrAdminMixin
from utils.responses import error_response, success_response


def _http_status_for_failure(message: str) -> int:
    lower = (message or '').lower()
    if 'no encontrado' in lower or 'not found' in lower:
        return status.HTTP_404_NOT_FOUND
    if 'no disponible' in lower or 'timeout' in lower or 'grpc' in lower:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_400_BAD_REQUEST


def _response_from_result(result: dict, *, success_status=status.HTTP_200_OK):
    if result.get('success'):
        data = {
            k: v
            for k, v in result.items()
            if k not in ('success', 'message')
        }
        return success_response(
            data,
            message=result.get('message', 'OK'),
            status=success_status,
        )
    return error_response(
        result.get('message', 'Error al enviar correo'),
        status=_http_status_for_failure(result.get('message', '')),
    )


def _response_cierre_materia(result: dict):
    data = {
        'enviados': result.get('enviados', 0),
        'fallidos': result.get('fallidos', 0),
    }
    if result.get('detalle') is not None:
        data['detalle'] = result['detalle']
    if result.get('historial_id') is not None:
        data['historial_id'] = result['historial_id']
    body_status = status.HTTP_200_OK
    if not result.get('success') and result.get('enviados', 0) == 0:
        body_status = _http_status_for_failure(result.get('message', ''))
    if result.get('success'):
        return success_response(data, message=result.get('message', 'OK'), status=body_status)
    return error_response(
        result.get('message', 'Error en envío masivo'),
        errors={'enviados': data.get('enviados'), 'fallidos': data.get('fallidos')},
        status=body_status if body_status != status.HTTP_200_OK else status.HTTP_400_BAD_REQUEST,
    )


class BienvenidaView(InternalOrAdminMixin, APIView):
    def post(self, request):
        serializer = BienvenidaSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Datos inválidos',
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        result = EmailService().send_bienvenida(
            data['alumno_id'],
            data['materia_id'],
            data['clave_acceso'],
        )
        return _response_from_result(result, success_status=status.HTTP_201_CREATED)


class BajaView(InternalOrAdminMixin, APIView):
    def post(self, request):
        serializer = BajaSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Datos inválidos',
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        result = EmailService().send_baja(
            data['alumno_id'],
            data['docente_id'],
            data['materia_id'],
        )
        return _response_from_result(result, success_status=status.HTTP_201_CREATED)


class CierreMateriaView(InternalOrAdminMixin, APIView):
    """Delega en EmailService (ThreadPoolExecutor vía EMAIL_MAX_WORKERS)."""

    def post(self, request):
        serializer = CierreMateriaSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Datos inválidos',
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = EmailService().send_cierre_materia(serializer.validated_data['materia_id'])
        return _response_cierre_materia(result)


class ResetPasswordView(InternalOrAdminMixin, APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Datos inválidos',
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        result = EmailService().send_reset_password(
            data['email'],
            data['reset_url'],
            nombre=data.get('nombre', ''),
        )
        return _response_from_result(result, success_status=status.HTTP_201_CREATED)
