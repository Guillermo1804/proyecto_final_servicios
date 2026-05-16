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
