import uuid

from django.db import models


class TipoCorreo(models.TextChoices):
    BIENVENIDA = 'bienvenida', 'Bienvenida'
    BAJA = 'baja', 'Baja'
    CIERRE_MATERIA = 'cierre_materia', 'Cierre de materia'
    RESET_PASSWORD = 'reset_password', 'Reset de contraseña'


class EstadoEnvioCorreo(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    RETRYING = 'retrying', 'Retrying'
    DEAD_LETTER = 'dead_letter', 'Dead letter'


class EventInbox(models.Model):
    """Idempotencia de consumo — PK event_id."""

    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128, db_index=True)
    handler = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_inbox'


class HistorialCorreo(models.Model):
    tipo = models.CharField(max_length=32, choices=TipoCorreo.choices)
    destinatario_email = models.EmailField()
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    enviado_en = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField(default=False)
    error_msg = models.TextField(null=True, blank=True)
    event_id = models.UUIDField(null=True, blank=True, db_index=True)
    estado_envio = models.CharField(
        max_length=16,
        choices=EstadoEnvioCorreo.choices,
        default=EstadoEnvioCorreo.PENDING,
        db_index=True,
    )

    class Meta:
        db_table = 'historial_correo'
        indexes = [
            models.Index(fields=['tipo', 'enviado_en'], name='idx_historial_tipo_enviado'),
            models.Index(fields=['event_id', 'destinatario_email'], name='idx_historial_event_dest'),
        ]
        ordering = ['-enviado_en']

    def __str__(self):
        return f'{self.tipo} → {self.destinatario_email} ({self.enviado_en:%Y-%m-%d %H:%M})'
