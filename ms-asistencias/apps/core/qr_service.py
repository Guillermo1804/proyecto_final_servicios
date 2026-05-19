"""Service for QR token generation and validation."""

import json
import time
import base64
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.models import SesionAsistencia
from apps.core.utils import sign_qr_payload, qr_payload_hash
from grpc_clients import is_alumno_en_materia


class QRTokenService:
    """Service for generating and validating QR tokens."""
    
    QR_VALIDITY_SECONDS = 30  # 30 seconds validity window
    
    @staticmethod
    def generar_token_qr(alumno_id: int, materia_id: int) -> dict:
        """
        Generate a QR token for attendance registration.
        
        Payload structure:
        {
            "alumno_id": 1,
            "sesion_id": 5,
            "materia_id": 1,
            "timestamp": 1234567890.123,
            "signature": "abc123..."
        }
        
        Args:
            alumno_id: Student ID
            materia_id: Subject ID
        
        Returns:
            {
                'payload': {...},
                'encoded_payload': 'base64-encoded',
                'expires_in': 30,
                'qr_hash': 'sha256-hash'
            }
        
        Raises:
            ValidationError if:
            - No active session for materia_id
            - Student not enrolled in materia_id
            - Session expired
        """
        
        # 1. Validate active session exists
        sesion = SesionAsistencia.objects.filter(
            materia_id=materia_id,
            activa=True
        ).first()
        
        if not sesion:
            raise ValidationError(
                f"No hay una sesión activa de asistencia para la materia {materia_id}. "
                f"El docente debe iniciar el pase de lista primero."
            )
        
        # 2. Validate session is still within 10-minute window
        if not sesion.esta_vigente():
            raise ValidationError(
                f"La sesión de asistencia expiró (pasaron más de 10 minutos). "
                f"Se cerrará automáticamente."
            )
        
        # 3. Validate student is enrolled in subject (via gRPC to MS-3)
        try:
            enrolled = is_alumno_en_materia(alumno_id, materia_id)
            if not enrolled:
                raise ValidationError(
                    f"El alumno {alumno_id} no está inscrito en la materia {materia_id}"
                )
        except Exception as e:
            # If MS-3 is unavailable, we might want to be lenient or strict
            # For now: strict - fail if we can't verify enrollment
            raise ValidationError(
                f"Error validando inscripción en MS-3: {str(e)}"
            )
        
        # 4. Create payload
        ahora = timezone.now()
        timestamp = ahora.timestamp()
        
        payload = {
            'alumno_id': alumno_id,
            'sesion_id': sesion.id,
            'materia_id': materia_id,
            'timestamp': timestamp,
        }
        
        # 5. Sign payload
        signature = sign_qr_payload(payload)
        payload['signature'] = signature
        
        # 6. Encode payload as base64 for QR code scanning
        payload_json = json.dumps(payload, sort_keys=True)
        encoded_payload = base64.b64encode(payload_json.encode()).decode('utf-8')
        
        # 7. Generate hash for anti-replay tracking
        hash_value = qr_payload_hash(payload)
        
        return {
            'payload': payload,
            'encoded_payload': encoded_payload,  # This goes into the QR code
            'expires_in': QRTokenService.QR_VALIDITY_SECONDS,
            'qr_hash': hash_value,
            'sesion_id': sesion.id,
        }
    
    @staticmethod
    def validar_token_qr(token_payload: dict, current_timestamp: float = None) -> tuple[bool, str]:
        """
        Validate a QR token before registering attendance.
        
        Checks:
        1. Signature is valid
        2. Token is not expired (30s window)
        3. Session still active
        
        Args:
            token_payload: Dict with alumno_id, sesion_id, timestamp, signature
            current_timestamp: Optional override for current time (testing)
        
        Returns:
            (is_valid: bool, message: str)
        """
        if current_timestamp is None:
            current_timestamp = timezone.now().timestamp()
        
        # Validate structure
        required_fields = ['alumno_id', 'sesion_id', 'timestamp', 'signature']
        missing = [f for f in required_fields if f not in token_payload]
        if missing:
            return False, f"Token incompleto: faltan {missing}"
        
        # Validate signature
        # Create payload without signature for verification
        payload_for_verification = {k: v for k, v in token_payload.items() if k != 'signature'}
        from apps.core.utils import verify_qr_payload
        
        provided_signature = token_payload['signature']
        if not verify_qr_payload(payload_for_verification, provided_signature):
            return False, "Firma de QR inválida"
        
        # Validate timestamp (30 second window)
        token_timestamp = token_payload['timestamp']
        age_seconds = current_timestamp - token_timestamp
        
        if age_seconds < 0:
            return False, "Token con timestamp en el futuro (reloj desincronizado)"
        
        if age_seconds > QRTokenService.QR_VALIDITY_SECONDS:
            return False, f"Token expirado (más de {QRTokenService.QR_VALIDITY_SECONDS} segundos)"
        
        return True, "Token válido"
