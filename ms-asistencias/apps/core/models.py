"""
Models for MS-5 Asistencias QR.

SesionAsistencia: Represents a 10-minute attendance session for a class/subject.
RegistroAsistencia: Represents a single student's attendance record in a session.
"""

from django.db import models
from django.utils import timezone


class SesionAsistencia(models.Model):
    """
    Sesión de asistencia por QR (10 minutos por materia).
    
    - Solo una sesión activa por materia_id en MySQL + Redis.
    - TTL en Redis: 600 segundos (10 minutos).
    - Persistida en MySQL para recuperación ante fallos de Redis.
    """
    
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cerrada', 'Cerrada'),
        ('confirmada', 'Confirmada'),
    ]
    
    materia_id = models.IntegerField(
        help_text="ID de la materia (desde MS-3)",
        db_index=True
    )
    docente_id = models.IntegerField(
        help_text="ID del docente titular que inicia la sesión"
    )
    
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de inicio de la sesión (en UTC)"
    )
    fecha_fin_teorica = models.DateTimeField(
        help_text="Fecha teórica de fin = inicio + 10 minutos"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa',
        help_text="Estado de la sesión: activa, cerrada, confirmada"
    )
    
    activa = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag para Query rápida de sesiones activas"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sesion_asistencia'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['materia_id', 'activa']),
            models.Index(fields=['docente_id', 'activa']),
            models.Index(fields=['fecha_inicio']),
        ]
        verbose_name = 'Sesión de Asistencia'
        verbose_name_plural = 'Sesiones de Asistencia'
    
    def __str__(self):
        return f"Sesión Materia {self.materia_id} ({self.get_estado_display()}) - {self.fecha_inicio.strftime('%Y-%m-%d %H:%M')}"
    
    def tiempo_transcurrido_segundos(self):
        """Calcula segundos transcurridos desde el inicio de la sesión."""
        elapsed = timezone.now() - self.fecha_inicio
        return int(elapsed.total_seconds())
    
    def minutos_transcurridos(self):
        """Calcula minutos transcurridos desde el inicio."""
        return self.tiempo_transcurrido_segundos() // 60
    
    def esta_vigente(self):
        """Verifica si la sesión aún está dentro de la ventana de 10 minutos."""
        return self.tiempo_transcurrido_segundos() <= 600  # 10 minutos


class RegistroAsistencia(models.Model):
    """
    Registro individual de asistencia de un alumno en una sesión.
    
    - unique_together(sesion, alumno_id): evita duplicados por anti-replay.
    - estados: 'presente' (≤5 min), 'retardo' (5-10 min), 'ausente' (no registrado).
    """
    
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('retardo', 'Retardo'),
        ('ausente', 'Ausente'),
    ]
    
    sesion = models.ForeignKey(
        SesionAsistencia,
        on_delete=models.CASCADE,
        related_name='registros',
        help_text="Referencia a la sesión de asistencia"
    )
    
    alumno_id = models.IntegerField(
        help_text="ID del alumno (desde MS-3)",
        db_index=True
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ausente',
        help_text="Clasificación: presente, retardo, ausente"
    )
    
    minuto_registro = models.IntegerField(
        help_text="Minuto dentro de la sesión (0-10) en que se registró"
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp exacto del registro"
    )
    
    qr_payload_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Hash SHA256 del payload QR para traceabilidad"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'registro_asistencia'
        ordering = ['fecha_registro']
        unique_together = [('sesion', 'alumno_id')]
        indexes = [
            models.Index(fields=['sesion', 'alumno_id']),
            models.Index(fields=['alumno_id', 'estado']),
            models.Index(fields=['sesion', 'estado']),
            models.Index(fields=['fecha_registro']),
        ]
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
    
    def __str__(self):
        return f"Alumno {self.alumno_id} - {self.get_estado_display()} (Sesión {self.sesion.id})"
    
    def save(self, *args, **kwargs):
        """
        Override save para validaciones adicionales si es necesario.
        """
        if self.minuto_registro < 0 or self.minuto_registro > 10:
            raise ValueError("minuto_registro debe estar entre 0 y 10")
        super().save(*args, **kwargs)
