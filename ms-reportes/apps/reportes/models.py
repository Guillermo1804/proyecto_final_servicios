from django.db import models


class TipoReporte(models.TextChoices):
    CALIFICACIONES = 'calificaciones', 'Calificaciones'
    ASISTENCIAS = 'asistencias', 'Asistencias'


class FormatoReporte(models.TextChoices):
    XLSX = 'xlsx', 'Excel'
    PDF = 'pdf', 'PDF'


class ReporteGenerado(models.Model):
    """Auditoría de reportes generados por MS-7."""

    tipo = models.CharField(max_length=20, choices=TipoReporte.choices)
    usuario_id = models.IntegerField(help_text='usuario_id del solicitante (MS-1)')
    formato = models.CharField(max_length=10, choices=FormatoReporte.choices)
    generado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reporte_generado'
        ordering = ['-generado_en']
        indexes = [
            models.Index(fields=['usuario_id', 'generado_en'], name='idx_reporte_usuario_fecha'),
            models.Index(fields=['tipo', 'generado_en'], name='idx_reporte_tipo_fecha'),
        ]

    def __str__(self):
        return f'{self.tipo} ({self.formato}) — usuario {self.usuario_id} @ {self.generado_en:%Y-%m-%d %H:%M}'
