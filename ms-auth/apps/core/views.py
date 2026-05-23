<<<<<<< HEAD
from uuid import uuid4
from datetime import timedelta
import secrets

from decouple import config
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
=======
>>>>>>> parent of 04b6ece (cambios de ms auth)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/login
    
    Body:
    {
        "email": "admin@agm.buap.mx",
        "password": "admin123"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "user": {
                "id": 1,
                "email": "admin@agm.buap.mx",
                "nombre": "Administrador",
                "rol": "admin",
                "activo": true
            }
        },
        "message": "Login exitoso"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            },
            'message': 'Login exitoso'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'data': None,
        'message': serializer.errors.get('non_field_errors', ['Error en la autenticación'])[0]
    }, status=status.HTTP_401_UNAUTHORIZED)
<<<<<<< HEAD


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    POST /auth/refresh-token
    
    Renueva el access token usando un refresh token válido.
    
    Body:
    {
        "refresh": "eyJ..."
    }
    
    Response 200:
    {
        "success": true,
        "data": {
            "access": "eyJ..."
        },
        "message": "Token renovado exitosamente"
    }
    
    Response 401:
    {
        "success": false,
        "data": null,
        "message": "Token de refresco inválido o expirado"
    }
    """
    serializer = CustomTokenRefreshSerializer(data=request.data)
    
    if serializer.is_valid():
        return Response({
            'success': True,
            'data': {
                'access': serializer.validated_data['access']
            },
            'message': 'Token renovado exitosamente'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'data': None,
        'message': 'Token de refresco inválido o expirado'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    """
    GET /auth/me
    
    Obtiene el perfil del usuario autenticado actual.
    
    Headers:
    Authorization: Bearer <access_token>
    
    Response 200:
    {
        "success": true,
        "data": {
            "id": 1,
            "email": "admin@agm.buap.mx",
            "nombre": "Administrador",
            "rol": "admin",
            "activo": true
        },
        "message": "Perfil obtenido exitosamente"
    }
    
    Response 401:
    {
        "success": false,
        "data": null,
        "message": "No autenticado"
    }
    """
    user = request.user
    return Response({
        'success': True,
        'data': UserSerializer(user).data,
        'message': 'Perfil obtenido exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """POST /auth/forgot-password

    Siempre responde 200 para evitar enumeración de usuarios.
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = getattr(request, 'user', None)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target_user = User.objects.filter(email=email, activo=True).first()

        if target_user:
            token_value = uuid4()
            reset_token = PasswordResetToken.objects.create(
                user=target_user,
                token=token_value,
                expira_en=timezone.now() + timedelta(hours=1),
            )

            frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
            reset_url = f'{frontend_url}/reset-password?token={reset_token.token}'
            send_reset_password_notification(target_user.email, str(reset_token.token), reset_url)

    return Response({
        'success': True,
        'data': None,
        'message': 'Si el correo está registrado, recibirás instrucciones para restablecer tu contraseña.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """POST /auth/reset-password

    Valida el token y cambia la contraseña si sigue vigente.
    """
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'data': None,
            'message': 'Token inválido o expirado'
        }, status=status.HTTP_400_BAD_REQUEST)

    reset_token = serializer.validated_data['reset_token']
    new_password = serializer.validated_data['password']

    with transaction.atomic():
        reset_token.user.set_password(new_password)
        reset_token.user.save(update_fields=['password'])
        reset_token.usado = True
        reset_token.save(update_fields=['usado'])

    return Response({
        'success': True,
        'data': None,
        'message': 'Contraseña actualizada exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    serializer = LogoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'data': None,
            'message': 'Refresh token requerido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(serializer.validated_data['refresh'])
        refresh.blacklist()
    except TokenError:
        return Response({
            'success': False,
            'data': None,
            'message': 'Refresh token inválido o expirado'
        }, status=status.HTTP_401_UNAUTHORIZED)

    return Response({
        'success': True,
        'data': None,
        'message': 'Sesión cerrada exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_only(request):
    return Response({
        'success': True,
        'data': {'role': 'admin'},
        'message': 'Acceso admin autorizado'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDocenteRole])
def docente_only(request):
    return Response({
        'success': True,
        'data': {'role': 'docente'},
        'message': 'Acceso docente autorizado'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumnoRole])
def alumno_only(request):
    return Response({
        'success': True,
        'data': {'role': 'alumno'},
        'message': 'Acceso alumno autorizado'
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def usuarios(request):
    if request.method == 'GET':
        if not request.user or not request.user.is_authenticated:
            return Response({
                'success': False,
                'data': None,
                'message': 'Token requerido',
            }, status=status.HTTP_401_UNAUTHORIZED)
        if request.user.rol != 'admin':
            return Response({
                'success': False,
                'data': None,
                'message': 'Sin permisos',
            }, status=status.HTTP_403_FORBIDDEN)

        page = max(int(request.query_params.get('page', 1)), 1)
        limit = max(int(request.query_params.get('limit', 10)), 1)
        queryset = User.objects.all().order_by('id')
        total = queryset.count()
        offset = (page - 1) * limit
        users = queryset[offset:offset + limit]

        return Response({
            'success': True,
            'data': {
                'items': AdminUserListSerializer(users, many=True).data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit if total else 0,
                },
            },
            'message': 'Usuarios obtenidos exitosamente'
        }, status=status.HTTP_200_OK)

    if not is_internal_api_key_valid(request) and not (request.user and request.user.is_authenticated and request.user.rol == 'admin'):
        return Response({
            'success': False,
            'data': None,
            'message': 'No autorizado'
        }, status=status.HTTP_401_UNAUTHORIZED)

    serializer = AdminUserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'data': None,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    password = serializer.validated_data.get('password') or secrets.token_urlsafe(12)
    user, error = create_user_account(
        email=serializer.validated_data['email'],
        nombre=serializer.validated_data['nombre'],
        rol=serializer.validated_data['rol'],
        password=password,
        activo=True,
    )
    if error:
        return Response({
            'success': False,
            'data': None,
            'message': error
        }, status=status.HTTP_400_BAD_REQUEST)

    if serializer.validated_data.get('send_email', True):
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=uuid4(),
            expira_en=timezone.now() + timedelta(hours=1),
        )
        reset_url = f'{frontend_url}/reset-password?token={reset_token.token}'
        send_reset_password_notification(user.email, str(reset_token.token), reset_url)

    return Response({
        'success': True,
        'data': AdminUserListSerializer(user).data,
        'message': 'Usuario creado exitosamente'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminRole])
def usuario_detail(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({
            'success': False,
            'data': None,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': _admin_user_payload(user),
            'message': 'Usuario obtenido exitosamente'
        }, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'data': None,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            'success': True,
            'data': _admin_user_payload(user),
            'message': 'Usuario actualizado exitosamente'
        }, status=status.HTTP_200_OK)

    user.activo = False
    user.save(update_fields=['activo'])
    return Response({
        'success': True,
        'data': _admin_user_payload(user),
        'message': 'Usuario eliminado lógicamente exitosamente'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def usuario_reset_password(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({
            'success': False,
            'data': None,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = AdminUserResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'data': None,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    _send_password_reset_email(user)

    return Response({
        'success': True,
        'data': None,
        'message': 'Se envió un enlace para restablecer la contraseña'
    }, status=status.HTTP_200_OK)
=======
>>>>>>> parent of 04b6ece (cambios de ms auth)
