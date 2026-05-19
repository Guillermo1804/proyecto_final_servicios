from django.db import models


class TipoCorreo(models.TextChoices):
    BIENVENIDA = 'bienvenida', 'Bienvenida'
    BAJA = 'baja', 'Baja'
    CIERRE_MATERIA = 'cierre_materia', 'Cierre de materia'
    RESET_PASSWORD = 'reset_password', 'Reset de contraseña'


class HistorialCorreo(models.Model):
    tipo = models.CharField(max_length=32, choices=TipoCorreo.choices)
    destinatario_email = models.EmailField()
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    enviado_en = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField(default=False)
    error_msg = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'historial_correo'
        indexes = [
            models.Index(fields=['tipo', 'enviado_en'], name='idx_historial_tipo_enviado'),
        ]
        ordering = ['-enviado_en']

    def __str__(self):
        return f'{self.tipo} → {self.destinatario_email} ({self.enviado_en:%Y-%m-%d %H:%M})'
