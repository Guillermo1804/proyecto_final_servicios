"""Service for QR token generation and validation."""

import json
import base64
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.models import SesionAsistencia
from apps.core.utils import sign_qr_payload, qr_payload_hash
from apps.core.projection_access import (
    assert_alumno_inscrito,
    assert_materia_habilitada_para_asistencia,
    ProjectionRejection,
)
from apps.core.event_bus.publishers import publish_asistencia_rejected


class QRTokenService:
    """Service for generating and validating QR tokens."""

    QR_VALIDITY_SECONDS = 30

    @staticmethod
    def generar_token_qr(alumno_id: int, materia_id: int) -> dict:
        try:
            assert_materia_habilitada_para_asistencia(materia_id)
            assert_alumno_inscrito(alumno_id, materia_id)
        except ProjectionRejection as exc:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                motivo=str(exc),
                codigo=exc.codigo,
            )
            raise ValidationError(str(exc)) from exc

        sesion = SesionAsistencia.objects.filter(materia_id=materia_id, activa=True).first()
        if not sesion:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                motivo=f'No hay sesión activa para materia {materia_id}',
                codigo='sesion_inactiva',
            )
            raise ValidationError(
                f'No hay una sesión activa de asistencia para la materia {materia_id}. '
                f'El docente debe iniciar el pase de lista primero.'
            )

        if not sesion.esta_vigente():
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion.id,
                motivo='Sesión expirada (ventana 10 min)',
                codigo='sesion_inactiva',
            )
            raise ValidationError('La sesión de asistencia expiró (pasaron más de 10 minutos).')

        timestamp = timezone.now().timestamp()
        payload = {
            'alumno_id': alumno_id,
            'sesion_id': sesion.id,
            'materia_id': materia_id,
            'timestamp': timestamp,
        }
        signature = sign_qr_payload(payload)
        payload['signature'] = signature

        payload_json = json.dumps(payload, sort_keys=True)
        encoded_payload = base64.b64encode(payload_json.encode()).decode('utf-8')
        hash_value = qr_payload_hash(payload)

        return {
            'payload': payload,
            'encoded_payload': encoded_payload,
            'expires_in': QRTokenService.QR_VALIDITY_SECONDS,
            'qr_hash': hash_value,
            'sesion_id': sesion.id,
        }

    @staticmethod
    def validar_token_qr(token_payload: dict, current_timestamp: float = None) -> tuple[bool, str]:
        if current_timestamp is None:
            current_timestamp = timezone.now().timestamp()

        required_fields = ['alumno_id', 'sesion_id', 'timestamp', 'signature']
        missing = [f for f in required_fields if f not in token_payload]
        if missing:
            return False, f'Token incompleto: faltan {missing}'

        payload_for_verification = {k: v for k, v in token_payload.items() if k != 'signature'}
        from apps.core.utils import verify_qr_payload

        if not verify_qr_payload(payload_for_verification, token_payload['signature']):
            return False, 'Firma de QR inválida'

        age_seconds = current_timestamp - token_payload['timestamp']
        if age_seconds < 0:
            return False, 'Token con timestamp en el futuro'
        if age_seconds > QRTokenService.QR_VALIDITY_SECONDS:
            return False, f'Token expirado (>{QRTokenService.QR_VALIDITY_SECONDS}s)'

        return True, 'Token válido'
