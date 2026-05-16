from rest_framework import serializers
from apps.core.models import Docente, Alumno, InscripcionMateria


class DocenteSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Docente."""

    class Meta:
        model = Docente
        fields = [
            "id",
            "usuario_id",
            "nombre",
            "apellido",
            "email",
            "departamento",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "usuario_id", "fecha_creacion"]


class AlumnoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Alumno."""

    class Meta:
        model = Alumno
        fields = [
            "id",
            "usuario_id",
            "matricula",
            "nombre",
            "apellido",
            "email",
            "carrera",
            "semestre",
            "activo",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "usuario_id", "fecha_creacion"]


class InscripcionMateriaSerializer(serializers.ModelSerializer):
    """Serializer para inscripciones con datos del alumno anidados."""
    alumno = AlumnoSerializer(read_only=True)

    class Meta:
        model = InscripcionMateria
        fields = [
            "id",
            "materia_id",
            "nrc",
            "nombre_materia",
            "docente_nombre",
            "horario",
            "activa",
            "fecha_inscripcion",
            "alumno",
        ]
