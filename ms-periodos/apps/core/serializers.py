from rest_framework import serializers

from apps.core.models import Materia, Periodo


class PeriodoSerializer(serializers.ModelSerializer):
    """Serializer para Periodo con validación de fechas."""

    materias_count = serializers.SerializerMethodField()

    class Meta:
        model = Periodo
        fields = [
            "id",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
            "plan_estudios",
            "activo",
            "materias_count",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "activo",
            "materias_count",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_materias_count(self, obj: Periodo) -> int:
        return obj.materias.count()

    def validate(self, attrs):
        fecha_inicio = attrs.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fecha_fin = attrs.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError(
                {"fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio."}
            )
        return attrs


class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para Materia."""

    class Meta:
        model = Materia
        fields = [
            "id",
            "periodo",
            "nrc",
            "nombre",
            "seccion",
            "clave",
            "docente_nombre",
            "docente_id",
            "horario",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "fecha_creacion"]
