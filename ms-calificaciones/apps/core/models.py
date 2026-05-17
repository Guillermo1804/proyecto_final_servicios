from django.db import models


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
