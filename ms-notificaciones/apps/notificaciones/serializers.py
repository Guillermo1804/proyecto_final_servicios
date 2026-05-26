from rest_framework import serializers


class BienvenidaSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField(min_value=1)
    materia_id = serializers.IntegerField(min_value=0)
    clave_acceso = serializers.CharField(max_length=255)


class BajaSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField(min_value=1)
    docente_id = serializers.IntegerField(min_value=1)
    materia_id = serializers.IntegerField(min_value=1)


class CierreMateriaSerializer(serializers.Serializer):
    materia_id = serializers.IntegerField(min_value=1)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_url = serializers.URLField()
    nombre = serializers.CharField(max_length=255, required=False, allow_blank=True)
