"""Servicer gRPC Auth (compartido entre comando manage.py y tests)."""

import grpc
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from proto_generated import auth_pb2, auth_pb2_grpc
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenBackendError

from apps.core.services import create_user_account

User = get_user_model()


def _normalize_token(token):
    if token.startswith('Bearer '):
        return token[7:]
    return token


def _build_user_profile(user):
    return auth_pb2.UserProfile(
        id=user.id,
        email=user.email,
        nombre=user.nombre,
        rol=user.rol,
        activo=user.activo,
    )


def _token_backend() -> TokenBackend:
    return TokenBackend(
        algorithm=settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        signing_key=settings.SIMPLE_JWT['SIGNING_KEY'],
    )


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def ValidateToken(self, request, context):
        try:
            token = _normalize_token(request.token)
            payload = _token_backend().decode(token, verify=True)
            user_id = payload.get('user_id')
            if user_id is None and payload.get('sub') is not None:
                user_id = int(payload['sub'])
            return auth_pb2.ValidateTokenResponse(
                valid=True,
                user_id=user_id,
                email=payload.get('email', ''),
                rol=payload.get('rol', ''),
                nombre=payload.get('nombre', ''),
            )
        except jwt.ExpiredSignatureError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token expirado')
            return auth_pb2.ValidateTokenResponse(valid=False)
        except (jwt.InvalidTokenError, TokenBackendError):
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token inválido')
            return auth_pb2.ValidateTokenResponse(valid=False)

    def GetUserById(self, request, context):
        try:
            user = User.objects.get(id=request.user_id, activo=True)
            return _build_user_profile(user)
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Usuario no encontrado o inactivo')
            return auth_pb2.UserProfile()

    def CheckRole(self, request, context):
        try:
            user = User.objects.get(id=request.user_id, activo=True)
            return auth_pb2.CheckRoleResponse(has_role=user.rol == request.role)
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Usuario no encontrado')
            return auth_pb2.CheckRoleResponse(has_role=False)

    def CreateUser(self, request, context):
        try:
            user, error = create_user_account(
                email=request.email,
                nombre=request.nombre,
                rol=request.rol,
                password=request.password,
                activo=True,
            )
            if error:
                return auth_pb2.CreateUserResponse(
                    success=False,
                    message=error,
                    user_id=0,
                )
            return auth_pb2.CreateUserResponse(
                success=True,
                message='Usuario creado exitosamente',
                user_id=user.id,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Error al crear usuario: {exc}')
            return auth_pb2.CreateUserResponse(
                success=False,
                message=str(exc),
                user_id=0,
            )
