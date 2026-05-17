from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .models import PasswordResetToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nombre', 'rol', 'activo']
        read_only_fields = ['id', 'activo']


class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nombre', 'rol', 'activo', 'fecha_creacion', 'fecha_actualizacion']


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nombre', 'activo']


class AdminUserResetPasswordSerializer(serializers.Serializer):
    send_email = serializers.BooleanField(required=False, default=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class AdminUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nombre = serializers.CharField(max_length=255)
    rol = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    send_email = serializers.BooleanField(required=False, default=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email y contraseña son requeridos')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Credenciales inválidas')

        if not user.check_password(password):
            raise serializers.ValidationError('Credenciales inválidas')

        if not user.activo:
            raise serializers.ValidationError('Usuario inactivo')

        attrs['user'] = user
        return attrs


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Serializer para refresh token que valida y retorna nuevo access."""
    
    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            return {'access': str(refresh.access_token)}
        except TokenError:
            raise serializers.ValidationError('Token de refresco inválido o expirado')


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        token = attrs.get('token')
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=token, usado=False)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Token inválido o expirado')

        if reset_token.expira_en <= timezone.now():
            raise serializers.ValidationError('Token inválido o expirado')

        if not reset_token.user.activo:
            raise serializers.ValidationError('Token inválido o expirado')

        attrs['reset_token'] = reset_token
        return attrs


class AuthResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.SerializerMethodField()
    message = serializers.CharField()

    def get_data(self, obj):
        user = obj.get('user')
        refresh = RefreshToken.for_user(user)
        
        # Agregar claims custom al token de acceso
        access = refresh.access_token
        access['user_id'] = user.id
        access['email'] = user.email
        access['rol'] = user.rol
        access['nombre'] = user.nombre
        
        return {
            'access_token': str(access),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }
