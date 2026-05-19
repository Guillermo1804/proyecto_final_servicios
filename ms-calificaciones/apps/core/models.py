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
