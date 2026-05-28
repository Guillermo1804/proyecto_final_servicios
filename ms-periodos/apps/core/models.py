from django.db import models
from django.db.models import Q, UniqueConstraint


class Periodo(models.Model):
    """Periodo académico. Solo uno puede estar activo a la vez."""

    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    plan_estudios = models.CharField(max_length=100, blank=True, default="")
    activo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "periodos"
        constraints = [
            UniqueConstraint(
                fields=["activo"],
                condition=Q(activo=True),
                name="unique_periodo_activo",
            )
        ]

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    """Materia asociada a un periodo académico."""

    periodo = models.ForeignKey(
        Periodo, on_delete=models.CASCADE, related_name="materias"
    )
    nrc = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    seccion = models.CharField(max_length=10)
    clave = models.CharField(max_length=20)
    docente_nombre = models.CharField(max_length=255, blank=True, default="")
    docente_id = models.IntegerField(null=True, blank=True)
    horario = models.CharField(max_length=255, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "materias"
        unique_together = [["periodo", "nrc"]]

    def __str__(self):
        return f"{self.nrc} - {self.nombre}"


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
            models.Index(fields=["status", "created_at"], name="idx_outbox_status_created"),
        ]
