"""Service for attendance registration via QR."""

import json
import base64
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError

from apps.core.models import SesionAsistencia, RegistroAsistencia
from apps.core.utils import (
    mark_qr_as_used,
    qr_payload_hash,
    verify_qr_payload,
    update_stats,
)
from apps.core.qr_service import QRTokenService


class AsistenciaRegistroService:
    """Service for registering attendance via QR token."""
    
    QR_ANTI_REPLAY_TTL = 120  # 2 minutes window for anti-replay
    
    @staticmethod
    @transaction.atomic
    def registrar_asistencia(encoded_payload: str, signature: str = None) -> dict:
        """
        Register attendance from QR token.
        
        Args:
            encoded_payload: Base64-encoded payload from QR scan
            signature: Optional separate signature (if payload is split)
        
        Returns:
            {
                'exitoso': True,
                'alumno_id': int,
                'sesion_id': int,
                'estado': 'presente' | 'retardo',
                'minuto_registro': int,
                'mensaje': str
            }
        
        Raises:
            ValidationError if:
            - Payload cannot be decoded
            - Signature invalid
            - Token expired
            - QR already used (anti-replay)
            - Session no longer active
            - Outside 10-minute window
        """
        
        # 1. Decode payload
        try:
            payload_json = base64.b64decode(encoded_payload).decode('utf-8')
            payload = json.loads(payload_json)
        except Exception as e:
            raise ValidationError(f"No se puede decodificar el payload QR: {str(e)}")
        
        # 2. Validate token structure
        required_fields = ['alumno_id', 'sesion_id', 'materia_id', 'timestamp', 'signature']
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise ValidationError(f"Payload incompleto: faltan {missing}")
        
        # 3. Verify HMAC signature
        payload_for_verification = {k: v for k, v in payload.items() if k != 'signature'}
        if not verify_qr_payload(payload_for_verification, payload['signature']):
            raise ValidationError("Firma de QR inválida (HMAC no coincide)")
        
        # 4. Validate token is not expired (30 second window)
        current_timestamp = timezone.now().timestamp()
        is_valid, message = QRTokenService.validar_token_qr(payload, current_timestamp)
        if not is_valid:
            raise ValidationError(f"Token QR inválido: {message}")
        
        # 5. Check anti-replay (mark as used)
        hash_payload = qr_payload_hash(payload_for_verification)
        already_used = not mark_qr_as_used(hash_payload, ttl=AsistenciaRegistroService.QR_ANTI_REPLAY_TTL)
        
        if already_used:
            raise ValidationError(
                "Este QR ya fue registrado (anti-replay). No se permite duplicado."
            )
        
        # 6. Fetch session from DB
        alumno_id = payload['alumno_id']
        sesion_id = payload['sesion_id']
        materia_id = payload['materia_id']
        
        try:
            sesion = SesionAsistencia.objects.get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            raise ValidationError(f"Sesión {sesion_id} no encontrada")
        
        # 7. Validate session is still active and within window
        if not sesion.activa:
            raise ValidationError(f"Sesión {sesion_id} ya está cerrada")
        
        if not sesion.esta_vigente():
            raise ValidationError(f"Sesión {sesion_id} expiró (ventana de 10 minutos)")
        
        # 8. Validate materia_id matches
        if sesion.materia_id != materia_id:
            raise ValidationError(
                f"Inconsistencia: QR es para materia {materia_id} pero sesión es para {sesion.materia_id}"
            )
        
        # 9. Calculate attendance state based on elapsed time
        minutos_transcurridos = sesion.minutos_transcurridos()
        
        if minutos_transcurridos <= 5:
            estado = 'presente'
        elif minutos_transcurridos <= 10:
            estado = 'retardo'
        else:
            raise ValidationError(
                f"Fuera de ventana: sesión pasó los 10 minutos ({minutos_transcurridos}m)"
            )
        
        # 10. Create or update attendance record
        try:
            registro, created = RegistroAsistencia.objects.get_or_create(
                sesion=sesion,
                alumno_id=alumno_id,
                defaults={
                    'estado': estado,
                    'minuto_registro': minutos_transcurridos,
                    'qr_payload_hash': hash_payload,
                }
            )
            
            if not created:
                # Record already exists - idempotent behavior
                # For idempotency: if it exists, return success with existing data
                registro.qr_payload_hash = hash_payload
                registro.save(update_fields=['qr_payload_hash'])
            else:
                # New record created - update stats
                update_stats(sesion_id, estado)
            
        except IntegrityError as e:
            # Should not happen due to get_or_create, but handle just in case
            raise ValidationError(f"Error registrando asistencia: {str(e)}")
        
        return {
            'exitoso': True,
            'alumno_id': alumno_id,
            'sesion_id': sesion_id,
            'estado': estado,
            'minuto_registro': minutos_transcurridos,
            'mensaje': f"Asistencia registrada: {estado.upper()} en minuto {minutos_transcurridos}"
        }
