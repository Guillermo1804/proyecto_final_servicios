from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, TokenError
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
    """
    Renueva access (y refresh si ROTATE_REFRESH_TOKENS) con los mismos claims
    que el login (user_id, email, rol, nombre) para MS-2..MS-7.
    """

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except TokenError as exc:
            raise serializers.ValidationError('Token de refresco inválido o expirado') from exc

        access = AccessToken(data['access'])
        user_id = access.get('user_id')
        if user_id is None:
            raise serializers.ValidationError('Token de refresco inválido o expirado')

        try:
            user = User.objects.get(pk=int(user_id))
        except (User.DoesNotExist, TypeError, ValueError) as exc:
            raise serializers.ValidationError('Usuario no encontrado') from exc

        access['user_id'] = user.id
        access['email'] = user.email
        access['rol'] = user.rol
        access['nombre'] = user.nombre
        data['access'] = str(access)
        return data


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
