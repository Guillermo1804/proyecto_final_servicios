from django.db import models
from django.db.models import Q, UniqueConstraint

class Docente(models.Model):
    """Modelo para docentes vinculado lógicamente a MS-1 Auth."""
    usuario_id = models.IntegerField(unique=True, help_text="ID en MS-1 Auth")
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
    usuario_id = models.IntegerField(unique=True, help_text="ID en MS-1 Auth")
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
