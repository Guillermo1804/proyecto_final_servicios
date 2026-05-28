"""Service for attendance registration via QR."""

import json
import base64
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError

from apps.core.models import SesionAsistencia, RegistroAsistencia
from apps.core.utils import mark_qr_as_used, qr_payload_hash, verify_qr_payload, update_stats
from apps.core.qr_service import QRTokenService
from apps.core.projection_access import (
    assert_alumno_inscrito,
    assert_materia_habilitada_para_asistencia,
    ProjectionRejection,
)
from apps.core.event_bus.publishers import (
    publish_asistencia_registered,
    publish_asistencia_rejected,
)


class AsistenciaRegistroService:
    """Service for registering attendance via QR token."""

    QR_ANTI_REPLAY_TTL = 120

    @staticmethod
    @transaction.atomic
    def registrar_asistencia(encoded_payload: str, signature: str = None) -> dict:
        try:
            payload_json = base64.b64decode(encoded_payload).decode('utf-8')
            payload = json.loads(payload_json)
        except Exception as exc:
            publish_asistencia_rejected(
                materia_id=0,
                alumno_id=0,
                motivo=str(exc),
                codigo='qr_invalido',
            )
            raise ValidationError(f'No se puede decodificar el payload QR: {exc}') from exc

        required_fields = ['alumno_id', 'sesion_id', 'materia_id', 'timestamp', 'signature']
        missing = [f for f in required_fields if f not in payload]
        if missing:
            publish_asistencia_rejected(
                materia_id=payload.get('materia_id', 0),
                alumno_id=payload.get('alumno_id', 0),
                motivo=f'Payload incompleto: {missing}',
                codigo='qr_invalido',
            )
            raise ValidationError(f'Payload incompleto: faltan {missing}')

        alumno_id = payload['alumno_id']
        sesion_id = payload['sesion_id']
        materia_id = payload['materia_id']

        payload_for_verification = {k: v for k, v in payload.items() if k != 'signature'}
        if not verify_qr_payload(payload_for_verification, payload['signature']):
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo='Firma HMAC inválida',
                codigo='qr_invalido',
            )
            raise ValidationError('Firma de QR inválida (HMAC no coincide)')

        current_timestamp = timezone.now().timestamp()
        is_valid, message = QRTokenService.validar_token_qr(payload, current_timestamp)
        if not is_valid:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo=message,
                codigo='qr_invalido',
            )
            raise ValidationError(f'Token QR inválido: {message}')

        hash_payload = qr_payload_hash(payload_for_verification)
        already_used = not mark_qr_as_used(
            hash_payload, ttl=AsistenciaRegistroService.QR_ANTI_REPLAY_TTL
        )
        if already_used:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo='QR ya utilizado (anti-replay)',
                codigo='qr_replay',
            )
            raise ValidationError('Este QR ya fue registrado (anti-replay).')

        try:
            assert_materia_habilitada_para_asistencia(materia_id)
            assert_alumno_inscrito(alumno_id, materia_id)
        except ProjectionRejection as exc:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo=str(exc),
                codigo=exc.codigo,
            )
            raise ValidationError(str(exc)) from exc

        try:
            sesion = SesionAsistencia.objects.get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo=f'Sesión {sesion_id} no encontrada',
                codigo='sesion_inactiva',
            )
            raise ValidationError(f'Sesión {sesion_id} no encontrada')

        if not sesion.activa:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo='Sesión cerrada',
                codigo='sesion_inactiva',
            )
            raise ValidationError(f'Sesión {sesion_id} ya está cerrada')

        if not sesion.esta_vigente():
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo='Sesión fuera de ventana 10 min',
                codigo='sesion_inactiva',
            )
            raise ValidationError(f'Sesión {sesion_id} expiró')

        if sesion.materia_id != materia_id:
            raise ValidationError('Inconsistencia materia_id en QR vs sesión')

        minutos_transcurridos = sesion.minutos_transcurridos()
        if minutos_transcurridos <= 5:
            estado = 'presente'
        elif minutos_transcurridos <= 10:
            estado = 'retardo'
        else:
            publish_asistencia_rejected(
                materia_id=materia_id,
                alumno_id=alumno_id,
                sesion_id=sesion_id,
                motivo='Fuera de ventana de registro',
                codigo='sesion_inactiva',
            )
            raise ValidationError('Fuera de ventana de 10 minutos')

        try:
            registro, created = RegistroAsistencia.objects.get_or_create(
                sesion=sesion,
                alumno_id=alumno_id,
                defaults={
                    'estado': estado,
                    'minuto_registro': minutos_transcurridos,
                    'qr_payload_hash': hash_payload,
                },
            )
            if not created:
                registro.qr_payload_hash = hash_payload
                registro.save(update_fields=['qr_payload_hash'])
            else:
                update_stats(sesion_id, estado)
                publish_asistencia_registered(
                    sesion_id=sesion_id,
                    materia_id=materia_id,
                    alumno_id=alumno_id,
                    estado=estado,
                    minuto_registro=minutos_transcurridos,
                    registro_id=registro.id,
                )
        except IntegrityError as exc:
            raise ValidationError(f'Error registrando asistencia: {exc}') from exc

        return {
            'exitoso': True,
            'alumno_id': alumno_id,
            'sesion_id': sesion_id,
            'estado': estado,
            'minuto_registro': minutos_transcurridos,
            'mensaje': f'Asistencia registrada: {estado.upper()} en minuto {minutos_transcurridos}',
        }
