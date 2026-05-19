"""Serializers for MS-5 Asistencias QR."""

from rest_framework import serializers
from django.utils import timezone

from apps.core.models import SesionAsistencia, RegistroAsistencia


class SesionAsistenciaSerializer(serializers.ModelSerializer):
    """Serializer for SesionAsistencia model."""
    
    minutos_transcurridos = serializers.SerializerMethodField()
    vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = SesionAsistencia
        fields = [
            'id',
            'materia_id',
            'docente_id',
            'fecha_inicio',
            'fecha_fin_teorica',
            'estado',
            'activa',
            'minutos_transcurridos',
            'vigente',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'fecha_inicio',
            'created_at',
            'updated_at',
            'minutos_transcurridos',
            'vigente',
        ]
    
    def get_minutos_transcurridos(self, obj):
        """Calculate elapsed minutes."""
        return obj.minutos_transcurridos()
    
    def get_vigente(self, obj):
        """Check if session is still valid."""
        return obj.esta_vigente()


class IniciarSesionSerializer(serializers.Serializer):
    """Input serializer for POST /sesiones/iniciar."""
    
    materia_id = serializers.IntegerField(
        min_value=1,
        help_text="ID de la materia para la que se inicia sesión"
    )
    docente_id = serializers.IntegerField(
        min_value=1,
        help_text="ID del docente (debe ser validado con token)"
    )


class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    """Serializer for RegistroAsistencia model."""
    
    class Meta:
        model = RegistroAsistencia
        fields = [
            'id',
            'sesion',
            'alumno_id',
            'estado',
            'minuto_registro',
            'fecha_registro',
            'qr_payload_hash',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'fecha_registro',
            'created_at',
        ]


class RegistroAsistenciaListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing attendance records."""
    
    class Meta:
        model = RegistroAsistencia
        fields = [
            'id',
            'alumno_id',
            'estado',
            'minuto_registro',
            'fecha_registro',
        ]


class EstadisticasAsistenciaSerializer(serializers.Serializer):
    """Response serializer for session statistics."""
    
    sesion_id = serializers.IntegerField()
    materia_id = serializers.IntegerField()
    presentes = serializers.IntegerField()
    retardos = serializers.IntegerField()
    ausentes = serializers.IntegerField()
    total_registrados = serializers.IntegerField()


class GenerarQRSerializer(serializers.Serializer):
    """Input serializer for GET /qr/generate?materia_id=1&alumno_id=1."""
    
    materia_id = serializers.IntegerField(
        min_value=1,
        help_text="ID de la materia"
    )
    alumno_id = serializers.IntegerField(
        min_value=1,
        help_text="ID del alumno (del token o query)"
    )


class QRTokenResponseSerializer(serializers.Serializer):
    """Response serializer for QR token generation."""
    
    payload = serializers.JSONField(
        help_text="Payload sin firmar (para debug/logging)"
    )
    encoded_payload = serializers.CharField(
        help_text="Base64-encoded payload para escanear con QR code"
    )
    expires_in = serializers.IntegerField(
        help_text="Segundos de validez del token (30)"
    )
    qr_hash = serializers.CharField(
        help_text="SHA256 hash del payload para anti-replay"
    )
    sesion_id = serializers.IntegerField(
        help_text="ID de la sesión vigente"
    )


class RegistrarAsistenciaSerializer(serializers.Serializer):
    """Input serializer for POST /asistencias/registrar/."""
    
    encoded_payload = serializers.CharField(
        help_text="Base64-encoded QR payload (from QR scan)"
    )


class RegistroAsistenciaResponseSerializer(serializers.Serializer):
    """Response serializer for attendance registration."""
    
    exitoso = serializers.BooleanField()
    alumno_id = serializers.IntegerField()
    sesion_id = serializers.IntegerField()
    estado = serializers.CharField()
    minuto_registro = serializers.IntegerField()
    mensaje = serializers.CharField()

