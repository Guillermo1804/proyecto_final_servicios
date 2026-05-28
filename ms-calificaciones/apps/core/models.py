from django.db import models


class Ponderacion(models.Model):
    materia_id = models.IntegerField(db_index=True)
    nombre_categoria = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = 'Ponderación'
        verbose_name_plural = 'Ponderaciones'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['materia_id', 'nombre_categoria'],
                name='uniq_ponderacion_materia_categoria',
            ),
        ]

    def __str__(self):
        return f'{self.materia_id} - {self.nombre_categoria} ({self.porcentaje}%)'


class Actividad(models.Model):
    ponderacion = models.ForeignKey(Ponderacion, on_delete=models.CASCADE, related_name='actividades')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return self.nombre


class Calificacion(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='calificaciones')
    alumno_id = models.IntegerField(db_index=True)
    calificacion = models.DecimalField(max_digits=4, decimal_places=2)
    fecha_asignacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'alumno_id'],
                name='uniq_calificacion_actividad_alumno',
            ),
        ]

    def __str__(self):
        return f'Alumno {self.alumno_id} - {self.calificacion}'


class EstadoMateria(models.Model):
    """Estado de cierre de una materia (referencia lógica a MS-2)."""

    materia_id = models.IntegerField(unique=True)
    cerrada = models.BooleanField(default=False)
    lista_impresa = models.BooleanField(default=False)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    notificacion_enviada = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Estado de materia'
        verbose_name_plural = 'Estados de materias'

    def __str__(self):
        return f'Materia {self.materia_id} cerrada={self.cerrada}'


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
            models.Index(fields=['status', 'created_at'], name='idx_ms4_outbox_status'),
        ]


class EventInbox(models.Model):
    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128, db_index=True)
    handler = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_inbox'


class UserProjection(models.Model):
    """Identidades/roles sincronizados desde MS-1 (event bus)."""

    user_id = models.IntegerField(primary_key=True)
    email = models.EmailField()
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=32)
    activo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_projection'


class MateriaProjection(models.Model):
    """Read model local de materias (MS-2 / eventos)."""

    materia_id = models.IntegerField(primary_key=True)
    periodo_id = models.IntegerField(db_index=True)
    nrc = models.CharField(max_length=32, default='')
    nombre = models.CharField(max_length=255, default='')
    seccion = models.CharField(max_length=16, blank=True, default='')
    clave = models.CharField(max_length=32, blank=True, default='')
    horario = models.CharField(max_length=255, blank=True, default='')
    docente_id = models.IntegerField(null=True, blank=True, db_index=True)
    docente_nombre = models.CharField(max_length=255, blank=True, default='')
    docente_email = models.EmailField(blank=True, default='')
    periodo_nombre = models.CharField(max_length=100, blank=True, default='')
    periodo_activo = models.BooleanField(default=True)
    materia_cerrada_upstream = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materia_projection'


class AlumnoMateriaProjection(models.Model):
    """Inscripción alumno-materia para validaciones locales."""

    alumno_id = models.IntegerField(db_index=True)
    materia_id = models.IntegerField(db_index=True)
    matricula = models.CharField(max_length=32, default='')
    nombre = models.CharField(max_length=255, default='')
    email = models.EmailField(blank=True, default='')
    activa = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alumno_materia_projection'
        constraints = [
            models.UniqueConstraint(
                fields=['alumno_id', 'materia_id'],
                name='uniq_alumno_materia_projection',
            ),
        ]
