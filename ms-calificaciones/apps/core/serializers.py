from decimal import Decimal
from datetime import date

from rest_framework import serializers

from apps.core.models import Ponderacion, Actividad, Calificacion, EstadoMateria


class PonderacionItemSerializer(serializers.Serializer):
    nombre_categoria = serializers.CharField(max_length=100)
    porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.00'))

    def validate_nombre_categoria(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError('El nombre de la categoría es obligatorio.')
        return nombre


class PonderacionBatchSerializer(serializers.Serializer):
    ponderaciones = PonderacionItemSerializer(many=True)

    def validate(self, attrs):
        ponderaciones = attrs['ponderaciones']
        total = sum((item['porcentaje'] for item in ponderaciones), Decimal('0.00'))

        nombres_normalizados = [item['nombre_categoria'].strip().casefold() for item in ponderaciones]
        duplicados = sorted({nombre for nombre in nombres_normalizados if nombres_normalizados.count(nombre) > 1})
        if duplicados:
            raise serializers.ValidationError({
                'ponderaciones': [f'La categoría "{duplicados[0]}" está repetida.']
            })

        if total != Decimal('100.00'):
            raise serializers.ValidationError({
                'ponderaciones': [f'La suma de porcentajes debe ser 100.00 y actualmente es {total}.']
            })

        return attrs


class PonderacionOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ponderacion
        fields = ['id', 'materia_id', 'nombre_categoria', 'porcentaje']


class ActividadInputSerializer(serializers.Serializer):
    ponderacion_id = serializers.IntegerField()
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    fecha = serializers.DateField(required=False, allow_null=True)

    def validate_nombre(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError('El nombre de la actividad es obligatorio.')
        return nombre

    def validate_ponderacion_id(self, value):
        if not Ponderacion.objects.filter(id=value).exists():
            raise serializers.ValidationError('La ponderación especificada no existe.')
        return value


class ActividadOutputSerializer(serializers.ModelSerializer):
    ponderacion_id = serializers.IntegerField(source='ponderacion.id')
    categoria_nombre = serializers.CharField(source='ponderacion.nombre_categoria', read_only=True)
    categoria_porcentaje = serializers.DecimalField(
        source='ponderacion.porcentaje', max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Actividad
        fields = [
            'id', 'ponderacion_id', 'categoria_nombre', 'categoria_porcentaje',
            'nombre', 'descripcion', 'fecha',
        ]


class ActividadGroupedByCategoriaSerializer(serializers.Serializer):
    categoria_nombre = serializers.CharField()
    categoria_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2)
    actividades = ActividadOutputSerializer(many=True)


class CalificacionInputSerializer(serializers.Serializer):
    actividad_id = serializers.IntegerField()
    alumno_id = serializers.IntegerField()
    calificacion = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=Decimal('0.00'), max_value=Decimal('10.00'))

    def validate_actividad_id(self, value):
        if not Actividad.objects.filter(id=value).exists():
            raise serializers.ValidationError('La actividad especificada no existe.')
        return value

    def validate_alumno_id(self, value):
        if value <= 0:
            raise serializers.ValidationError('El alumno_id debe ser positivo.')
        return value


class CalificacionOutputSerializer(serializers.ModelSerializer):
    actividad_id = serializers.IntegerField(source='actividad.id')
    alumno_id = serializers.IntegerField()
    nombre_actividad = serializers.CharField(source='actividad.nombre', read_only=True)
    fecha_asignacion = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Calificacion
        fields = ['id', 'actividad_id', 'alumno_id', 'calificacion', 'nombre_actividad', 'fecha_asignacion']