"""Service for real-time attendance statistics."""

from typing import Dict, Optional
from django.core.exceptions import ValidationError

from apps.core.models import SesionAsistencia, RegistroAsistencia
from apps.core.utils import get_stats, initialize_stats
from apps.core.models import AlumnoProjection


class EstadisticasService:
    """Service for computing and managing attendance statistics."""
    
    @staticmethod
    def obtener_stats_sesion(sesion_id: int) -> Dict:
        """
        Get real-time statistics for a session.
        
        Fetches live data from database with Redis as backup.
        
        Args:
            sesion_id: Session ID
        
        Returns:
            {
                'sesion_id': int,
                'materia_id': int,
                'docente_id': int,
                'presentes': int,
                'retardos': int,
                'ausentes': int,
                'total_registrados': int,
                'estado_sesion': 'activa' | 'cerrada' | 'confirmada',
                'vigente': bool,
                'minutos_transcurridos': int,
            }
        
        Raises:
            ValidationError if session not found
        """
        try:
            sesion = SesionAsistencia.objects.get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            raise ValidationError(f"Sesión {sesion_id} no encontrada")
        
        # Get live counts from database
        registros = RegistroAsistencia.objects.filter(sesion=sesion)
        presentes = registros.filter(estado='presente').count()
        retardos = registros.filter(estado='retardo').count()
        ausentes = registros.filter(estado='ausente').count()
        total_registrados = registros.count()
        
        # If stats exist in Redis, use them as backup for "ausentes" calculation
        # but trust the database for present/late counts
        redis_stats = get_stats(sesion_id)
        
        # Calculate minutos_transcurridos
        minutos = sesion.minutos_transcurridos()
        
        return {
            'sesion_id': sesion.id,
            'materia_id': sesion.materia_id,
            'docente_id': sesion.docente_id,
            'presentes': presentes,
            'retardos': retardos,
            'ausentes': ausentes,
            'total_registrados': total_registrados,
            'estado_sesion': sesion.estado,
            'vigente': sesion.esta_vigente(),
            'minutos_transcurridos': minutos,
            'fecha_inicio': sesion.fecha_inicio.isoformat() if sesion.fecha_inicio else None,
            'fecha_fin_teorica': sesion.fecha_fin_teorica.isoformat() if sesion.fecha_fin_teorica else None,
        }
    
    @staticmethod
    def obtener_stats_alumno_materia(alumno_id: int, materia_id: int) -> Dict:
        """
        Get attendance statistics for a student in a subject.
        
        Args:
            alumno_id: Student ID
            materia_id: Subject ID
        
        Returns:
            {
                'alumno_id': int,
                'materia_id': int,
                'total_registros': int,
                'presentes': int,
                'retardos': int,
                'ausentes': int,
                'porcentaje_asistencia': float,
                'porcentaje_retardo': float,
            }
        """
        registros = RegistroAsistencia.objects.filter(
            alumno_id=alumno_id,
            sesion__materia_id=materia_id
        )
        
        total = registros.count()
        presentes = registros.filter(estado='presente').count()
        retardos = registros.filter(estado='retardo').count()
        ausentes = registros.filter(estado='ausente').count()
        
        porcentaje_asistencia = (presentes / total * 100) if total > 0 else 0
        porcentaje_retardo = (retardos / total * 100) if total > 0 else 0
        
        return {
            'alumno_id': alumno_id,
            'materia_id': materia_id,
            'total_registros': total,
            'presentes': presentes,
            'retardos': retardos,
            'ausentes': ausentes,
            'porcentaje_asistencia': round(porcentaje_asistencia, 2),
            'porcentaje_retardo': round(porcentaje_retardo, 2),
        }
    
    @staticmethod
    def obtener_stats_materia_resumen(materia_id: int) -> Dict:
        """
        Get aggregate statistics for a subject (all sessions).
        
        Args:
            materia_id: Subject ID
        
        Returns:
            {
                'materia_id': int,
                'total_registros': int,
                'presentes': int,
                'retardos': int,
                'ausentes': int,
                'total_alumnos_unicos': int,
                'total_sesiones': int,
                'promedio_asistencia': float,
            }
        """
        registros = RegistroAsistencia.objects.filter(sesion__materia_id=materia_id)
        sesiones = SesionAsistencia.objects.filter(materia_id=materia_id)
        
        total = registros.count()
        presentes = registros.filter(estado='presente').count()
        retardos = registros.filter(estado='retardo').count()
        ausentes = registros.filter(estado='ausente').count()
        alumnos_unicos = registros.values('alumno_id').distinct().count()
        total_sesiones = sesiones.count()
        
        promedio_asistencia = (presentes / total * 100) if total > 0 else 0
        
        return {
            'materia_id': materia_id,
            'total_registros': total,
            'presentes': presentes,
            'retardos': retardos,
            'ausentes': ausentes,
            'total_alumnos_unicos': alumnos_unicos,
            'total_sesiones': total_sesiones,
            'promedio_asistencia': round(promedio_asistencia, 2),
        }
    
    @staticmethod
    def obtener_detalle_sesion_completo(sesion_id: int) -> Dict:
        """
        Get complete session details with all attendance records.
        
        Args:
            sesion_id: Session ID
        
        Returns:
            {
                'sesion': {...stats completos...},
                'registros': [...list of attendance records...],
                'resumen_por_estado': {'presente': 10, 'retardo': 2, 'ausente': 0}
            }
        """
        stats = EstadisticasService.obtener_stats_sesion(sesion_id)
        
        registros_qs = RegistroAsistencia.objects.filter(sesion_id=sesion_id).values(
            'id', 'alumno_id', 'estado', 'minuto_registro', 'fecha_registro'
        ).order_by('-fecha_registro')
        
        return {
            'sesion': stats,
            'registros': list(registros_qs),
            'resumen_por_estado': {
                'presente': stats['presentes'],
                'retardo': stats['retardos'],
                'ausente': stats['ausentes'],
            }
        }
