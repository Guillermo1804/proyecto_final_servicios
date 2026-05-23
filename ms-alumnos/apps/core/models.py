import uuid

from django.db import models
from django.db.models import Q, UniqueConstraint


class Docente(models.Model):
    """Modelo para docentes vinculado lógicamente a MS-1 Auth."""
    usuario_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID en MS-1 Auth (null mientras pending_user_creation)",
    )
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    departamento = models.CharField(max_length=255, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"

class Alumno(models.Model):
    """Modelo para alumnos vinculado lógicamente a MS-1 Auth."""
    usuario_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID en MS-1 Auth (null mientras pending_user_creation)",
    )
    matricula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    email = models.EmailField()
    carrera = models.CharField(max_length=100, blank=True)
    semestre = models.IntegerField(default=1)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.matricula} - {self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

class InscripcionMateria(models.Model):
    """Inscripción de un alumno en una materia de MS-2."""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="inscripciones")
    materia_id = models.IntegerField(help_text="ID en MS-2 Periodos")
    
    # Datos desnormalizados de la materia para rendimiento
    nrc = models.CharField(max_length=20)
    nombre_materia = models.CharField(max_length=255)
    docente_nombre = models.CharField(max_length=255)
    horario = models.CharField(max_length=255, blank=True)
    
    activa = models.BooleanField(default=True)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["alumno", "materia_id"],
                condition=Q(activa=True),
                name="unique_inscripcion_activa"
            )
        ]
        verbose_name = "Inscripción de Materia"
        verbose_name_plural = "Inscripciones de Materias"

    def __str__(self):
        return f"{self.alumno.matricula} en {self.nombre_materia} ({self.nrc})"


class PendingUserCreation(models.Model):
    """Seguimiento de credenciales solicitadas a MS-1 via bus."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class EntityType(models.TextChoices):
        ALUMNO = "alumno", "Alumno"
        DOCENTE = "docente", "Docente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=16, choices=EntityType.choices)
    entity_id = models.PositiveIntegerField()
    email = models.EmailField()
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=32)
    temporary_password = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    ms1_user_id = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pending_user_creation"
        indexes = [
            models.Index(
                fields=["entity_type", "entity_id"],
                name="idx_pending_entity",
            ),
        ]


class EventOutbox(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

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
        db_table = "event_outbox"
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="idx_outbox_status_created",
            ),
        ]
