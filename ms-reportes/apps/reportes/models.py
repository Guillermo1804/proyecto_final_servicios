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


class EventInbox(models.Model):
    """Idempotencia de consumo — PK event_id (agm_events)."""

    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128, db_index=True)
    handler = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'event_inbox'


class ReportAnalyticsState(models.Model):
    """Cursor global de consistencia eventual para respuestas API."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    data_as_of = models.DateTimeField(null=True, blank=True)
    events_processed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_analytics_state'


class ReportePeriodoProjection(models.Model):
    periodo_id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=128, default='')
    activo = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reporte_periodo_projection'


class ReporteMateriaProjection(models.Model):
    materia_id = models.IntegerField(primary_key=True)
    periodo_id = models.IntegerField(db_index=True)
    periodo_nombre = models.CharField(max_length=128, default='')
    nrc = models.CharField(max_length=32, default='', db_index=True)
    nombre = models.CharField(max_length=255, default='')
    seccion = models.CharField(max_length=32, default='')
    clave = models.CharField(max_length=32, default='')
    docente_id = models.IntegerField(null=True, blank=True, db_index=True)
    docente_nombre = models.CharField(max_length=255, default='')
    horario = models.CharField(max_length=128, default='')
    cerrada = models.BooleanField(default=False, db_index=True)
    total_alumnos = models.PositiveIntegerField(default=0)
    aprobados = models.PositiveIntegerField(default=0)
    reprobados = models.PositiveIntegerField(default=0)
    promedio_grupal = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_sesiones_qr = models.PositiveIntegerField(default=0)
    porcentaje_asistencia_grupal = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reporte_materia_projection'
        indexes = [
            models.Index(fields=['docente_id', 'periodo_id'], name='idx_rep_mat_doc_per'),
        ]


class ReporteAlumnoProjection(models.Model):
    alumno_id = models.IntegerField(db_index=True)
    materia_id = models.IntegerField(db_index=True)
    usuario_id = models.IntegerField(null=True, blank=True, db_index=True)
    matricula = models.CharField(max_length=32, default='')
    nombre = models.CharField(max_length=255, default='')
    email = models.EmailField(default='')
    activa = models.BooleanField(default=True, db_index=True)
    promedio_real = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    promedio_redondeado = models.SmallIntegerField(default=0)
    presentes = models.PositiveIntegerField(default=0)
    retardos = models.PositiveIntegerField(default=0)
    ausentes = models.PositiveIntegerField(default=0)
    porcentaje_asistencia = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reporte_alumno_projection'
        constraints = [
            models.UniqueConstraint(
                fields=['alumno_id', 'materia_id'],
                name='uniq_reporte_alumno_materia',
            ),
        ]
        indexes = [
            models.Index(fields=['materia_id', 'activa'], name='idx_rep_alu_mat_act'),
            models.Index(fields=['alumno_id', 'activa'], name='idx_rep_alu_alu_act'),
        ]


class ReporteCalificacionProjection(models.Model):
    actividad_id = models.IntegerField(db_index=True)
    alumno_id = models.IntegerField(db_index=True)
    materia_id = models.IntegerField(db_index=True)
    calificacion_id = models.IntegerField(null=True, blank=True)
    categoria = models.CharField(max_length=128, default='')
    porcentaje_categoria = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    actividad_nombre = models.CharField(max_length=255, default='')
    calificacion = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reporte_calificacion_projection'
        constraints = [
            models.UniqueConstraint(
                fields=['actividad_id', 'alumno_id'],
                name='uniq_reporte_calif_act_alu',
            ),
        ]
        indexes = [
            models.Index(fields=['materia_id', 'categoria'], name='idx_rep_cal_mat_cat'),
        ]


class ReporteAsistenciaProjection(models.Model):
    sesion_id = models.IntegerField()
    materia_id = models.IntegerField(db_index=True)
    alumno_id = models.IntegerField(db_index=True)
    estado = models.CharField(max_length=16)
    minuto_registro = models.SmallIntegerField(default=0)
    registro_id = models.IntegerField(null=True, blank=True)
    registrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reporte_asistencia_projection'
        constraints = [
            models.UniqueConstraint(
                fields=['sesion_id', 'alumno_id'],
                name='uniq_reporte_asist_ses_alu',
            ),
        ]
