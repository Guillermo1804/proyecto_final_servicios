from uuid import uuid4
from datetime import timedelta
import secrets

from decouple import config
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django.conf import settings

from .event_bus.password_events import enqueue_password_reset_requested
from .grpc_clients import send_reset_password_notification
from .models import PasswordResetToken
from .permissions import IsAdminRole, IsDocenteRole, IsAlumnoRole
from .event_bus.token_events import enqueue_token_revoked
from .services import create_user_account, is_internal_api_key_valid
from .serializers import (
    LoginSerializer,
    UserSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    AdminUserResetPasswordSerializer,
    AdminUserCreateSerializer,
    LogoutSerializer,
    CustomTokenRefreshSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)

User = get_user_model()


def _admin_user_payload(user):
    return AdminUserListSerializer(user).data


def _dispatch_password_reset_notification(
    *, email: str, reset_url: str, token: str, nombre: str = ''
) -> None:
    if getattr(settings, 'USE_EVENT_BUS', True):
        enqueue_password_reset_requested(
            email=email,
            reset_url=reset_url,
            token=token,
            nombre=nombre,
        )
    else:
        send_reset_password_notification(email, token, reset_url)


def _send_password_reset_email(user):
    token_value = uuid4()
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=token_value,
        expira_en=timezone.now() + timedelta(hours=1),
    )

    frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
    reset_url = f'{frontend_url}/reset-password?token={reset_token.token}'
    transaction.on_commit(
        lambda: _dispatch_password_reset_notification(
            email=user.email,
            reset_url=reset_url,
            token=str(reset_token.token),
            nombre=user.nombre or '',
        )
    )
    return reset_token


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/login
    
    Autentica un usuario con email y contraseña, retorna JWT (access + refresh).
    
    Body:
    {
        "email": "admin@agm.buap.mx",
        "password": "admin123"
    }
    
    Response 200:
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
    
    Response 401:
    {
        "success": false,
        "data": null,
        "message": "Credenciales inválidas"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Agregar claims custom
        access['user_id'] = user.id
        access['email'] = user.email
        access['rol'] = user.rol
        access['nombre'] = user.nombre
        
        return Response({
            'success': True,
            'data': {
                'access_token': str(access),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            },
            'message': 'Login exitoso'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'data': None,
        'message': serializer.errors.get('non_field_errors', ['Credenciales inválidas'])[0]
    }, status=status.HTTP_401_UNAUTHORIZED)


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
        payload = {'access': serializer.validated_data['access']}
        if serializer.validated_data.get('refresh'):
            payload['refresh'] = serializer.validated_data['refresh']
        return Response({
            'success': True,
            'data': payload,
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
            transaction.on_commit(
                lambda u=target_user, r=reset_url, t=str(reset_token.token): (
                    _dispatch_password_reset_notification(
                        email=u.email,
                        reset_url=r,
                        token=t,
                        nombre=u.nombre or '',
                    )
                )
            )

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
        jti = refresh.get('jti')
        user_id = refresh.get('user_id') or getattr(request.user, 'id', None)
        refresh.blacklist()
        if jti and user_id:
            enqueue_token_revoked(user_id=int(user_id), jti=str(jti))
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
        if not (request.user and request.user.is_authenticated and request.user.rol == 'admin'):
            return Response({
                'success': False,
                'data': None,
                'message': 'No autorizado'
            }, status=status.HTTP_401_UNAUTHORIZED)

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
        link_existing=is_internal_api_key_valid(request),
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
        transaction.on_commit(
            lambda: _dispatch_password_reset_notification(
                email=user.email,
                reset_url=reset_url,
                token=str(reset_token.token),
                nombre=user.nombre or '',
            )
        )

    return Response({
        'success': True,
        'data': AdminUserListSerializer(user).data,
        'message': 'Usuario creado exitosamente'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def usuario_detail(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({
            'success': False,
            'data': None,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    is_admin = request.user and request.user.is_authenticated and request.user.rol == 'admin'
    is_internal = is_internal_api_key_valid(request)

    if request.method == 'GET':
        if not is_admin and not is_internal:
            return Response({
                'success': False,
                'data': None,
                'message': 'No autorizado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'success': True,
            'data': _admin_user_payload(user),
            'message': 'Usuario obtenido exitosamente'
        }, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        if not is_admin and not is_internal:
            return Response({
                'success': False,
                'data': None,
                'message': 'No autorizado'
            }, status=status.HTTP_401_UNAUTHORIZED)
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

    if not is_admin and not is_internal:
        return Response({
            'success': False,
            'data': None,
            'message': 'No autorizado'
        }, status=status.HTTP_401_UNAUTHORIZED)

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
