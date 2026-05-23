from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nombre', 'rol', 'activo']
        read_only_fields = ['id', 'activo']


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


class AuthResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.SerializerMethodField()
    message = serializers.CharField()

    def get_data(self, obj):
        user = obj.get('user')
        refresh = RefreshToken.for_user(user)
        
        return {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }
