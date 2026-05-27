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


class EventOutbox(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PUBLISHED = 'published', 'Published'
        FAILED = 'failed', 'Failed'

    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128)
    event_version = models.PositiveIntegerField(default=1)
    aggregate_type = models.CharField(max_length=64)
    aggregate_id = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'event_outbox'
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_ms5_outbox_status'),
        ]


class EventInbox(models.Model):
    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128, db_index=True)
    handler = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_inbox'


class PeriodoProjection(models.Model):
    periodo_id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, default='')
    activo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'periodo_projection'


class MateriaProjection(models.Model):
    materia_id = models.IntegerField(primary_key=True)
    periodo_id = models.IntegerField(db_index=True)
    nrc = models.CharField(max_length=32, default='')
    nombre = models.CharField(max_length=255, default='')
    docente_id = models.IntegerField(null=True, blank=True)
    periodo_activo = models.BooleanField(default=True)
    cerrada_upstream = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materia_projection'


class AlumnoProjection(models.Model):
    """Inscripción alumno-materia para validación local en escaneo QR."""

    alumno_id = models.IntegerField(db_index=True)
    materia_id = models.IntegerField(db_index=True)
    matricula = models.CharField(max_length=32, default='')
    nombre = models.CharField(max_length=255, default='')
    email = models.EmailField(blank=True, default='')
    activa = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alumno_projection'
        constraints = [
            models.UniqueConstraint(
                fields=['alumno_id', 'materia_id'],
                name='uniq_alumno_projection_materia',
            ),
        ]
