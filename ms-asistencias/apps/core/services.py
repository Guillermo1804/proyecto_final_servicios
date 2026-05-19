"""Business logic for MS-5 session management.

Handles session lifecycle: creation, validation, closure, and cleanup.
"""

import json
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.core.models import SesionAsistencia
from apps.core.utils import (
    store_sesion_in_redis,
    get_sesion_from_redis,
    get_active_sesion_id_by_materia,
    delete_sesion_from_redis,
    initialize_stats,
)


class SesionAsistenciaService:
    """Service for managing attendance sessions."""
    
    @staticmethod
    @transaction.atomic
    def crear_sesion(materia_id: int, docente_id: int) -> tuple[SesionAsistencia, str]:
        """
        Create a new attendance session.
        
        Rules:
        - Only ONE active session per materia_id (checked in Redis + MySQL)
        - Session duration: 10 minutes (600 seconds)
        - Persisted in MySQL, cached in Redis
        
        Args:
            materia_id: Subject ID
            docente_id: Teacher ID
        
        Returns:
            (SesionAsistencia instance, message)
        
        Raises:
            ValidationError if duplicate session exists
        """
        # Check if already active in Redis (fast path)
        existing_redis = get_active_sesion_id_by_materia(materia_id)
        if existing_redis:
            raise ValidationError(
                f"Ya existe una sesión activa para la materia {materia_id}. "
                f"Ciérrala antes de iniciar una nueva."
            )
        
        # Check MySQL for any active session
        existing_db = SesionAsistencia.objects.filter(
            materia_id=materia_id,
            activa=True
        ).first()
        if existing_db:
            raise ValidationError(
                f"Ya existe una sesión activa en BD para materia {materia_id} "
                f"(sesión {existing_db.id}). Contacta a administrador si persiste."
            )
        
        # Create session
        ahora = timezone.now()
        fecha_fin = ahora + timedelta(seconds=600)  # 10 minutes
        
        sesion = SesionAsistencia.objects.create(
            materia_id=materia_id,
            docente_id=docente_id,
            fecha_fin_teorica=fecha_fin,
            estado='activa',
            activa=True,
        )
        
        # Store in Redis (TTL 600s)
        inicio_epoch = ahora.timestamp()
        success = store_sesion_in_redis(
            sesion_id=sesion.id,
            materia_id=materia_id,
            docente_id=docente_id,
            inicio_timestamp=inicio_epoch,
            ttl=600
        )
        
        if not success:
            # Rollback session creation if Redis fails
            sesion.delete()
            raise ValidationError("Error al guardar sesión en Redis. Intenta de nuevo.")
        
        # Initialize stats
        initialize_stats(sesion.id)
        
        return sesion, f"Sesión {sesion.id} iniciada para materia {materia_id}"
    
    @staticmethod
    @transaction.atomic
    def cerrar_sesion(sesion_id: int) -> tuple[bool, str]:
        """
        Close an active session.
        
        Actions:
        - Mark as inactive in MySQL (activa=False)
        - Clean up Redis keys
        - Freeze further registrations
        
        Args:
            sesion_id: Session ID to close
        
        Returns:
            (success: bool, message: str)
        """
        try:
            sesion = SesionAsistencia.objects.get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            return False, f"Sesión {sesion_id} no encontrada"
        
        if not sesion.activa:
            return False, f"Sesión {sesion_id} ya está cerrada"
        
        # Mark as closed
        sesion.activa = False
        sesion.estado = 'cerrada'
        sesion.save(update_fields=['activa', 'estado', 'updated_at'])
        
        # Clean up Redis
        delete_sesion_from_redis(sesion.id, sesion.materia_id)
        
        return True, f"Sesión {sesion_id} cerrada exitosamente"

    @staticmethod
    @transaction.atomic
    def confirmar_sesion(sesion_id: int) -> tuple[bool, str]:
        """
        Confirm a session and freeze records.

        Business rule:
        - Session must exist and be active.
        - Marks state as 'confirmada' and active=False.
        - Clears Redis keys associated to the session.
        """
        try:
            sesion = SesionAsistencia.objects.select_for_update().get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            return False, f"Sesión {sesion_id} no encontrada"

        if not sesion.activa:
            if sesion.estado == 'confirmada':
                return False, f"Sesión {sesion_id} ya estaba confirmada"
            return False, f"Sesión {sesion_id} no está activa"

        sesion.estado = 'confirmada'
        sesion.activa = False
        sesion.save(update_fields=['estado', 'activa', 'updated_at'])

        delete_sesion_from_redis(sesion_id, sesion.materia_id)
        return True, f"Sesión {sesion_id} confirmada y congelada"

    @staticmethod
    @transaction.atomic
    def solicitar_nueva_lista(sesion_id: int) -> tuple[bool, str]:
        """
        Invalidate current session and allow creating a new one.

        Business rule:
        - Session must exist.
        - Marks state as 'cerrada' and active=False.
        - Clears Redis keys to unlock creating a fresh session via /sesiones/iniciar.
        """
        try:
            sesion = SesionAsistencia.objects.select_for_update().get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            return False, f"Sesión {sesion_id} no encontrada"

        if sesion.activa:
            sesion.estado = 'cerrada'
            sesion.activa = False
            sesion.save(update_fields=['estado', 'activa', 'updated_at'])

        delete_sesion_from_redis(sesion_id, sesion.materia_id)
        return True, (
            f"Sesión {sesion_id} invalidada. Ya puedes iniciar una nueva lista "
            f"para materia {sesion.materia_id}"
        )
    
    @staticmethod
    def obtener_sesion_activa(materia_id: int) -> SesionAsistencia | None:
        """
        Get the active session for a subject.
        
        Priority:
        1. Check Redis (fast)
        2. Check MySQL (fallback)
        
        Args:
            materia_id: Subject ID
        
        Returns:
            SesionAsistencia instance or None
        """
        # Try Redis first
        sesion_id = get_active_sesion_id_by_materia(materia_id)
        if sesion_id:
            try:
                return SesionAsistencia.objects.get(id=sesion_id, activa=True)
            except SesionAsistencia.DoesNotExist:
                # Redis stale, fallback to DB
                pass
        
        # Fallback: check MySQL
        return SesionAsistencia.objects.filter(
            materia_id=materia_id,
            activa=True
        ).first()
    
    @staticmethod
    def validar_sesion_vigente(sesion: SesionAsistencia) -> tuple[bool, str]:
        """
        Check if session is still within 10-minute window.
        
        Args:
            sesion: SesionAsistencia instance
        
        Returns:
            (is_valid: bool, message: str)
        """
        if not sesion.esta_vigente():
            return False, f"Sesión {sesion.id} expiró (ventana de 10 minutos)"
        return True, "Sesión vigente"
    
    @staticmethod
    def obtener_minutos_transcurridos(sesion: SesionAsistencia) -> int:
        """Get minutes elapsed since session start."""
        return sesion.minutos_transcurridos()
