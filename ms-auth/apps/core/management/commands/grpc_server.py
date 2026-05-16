import grpc
from concurrent import futures
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from proto_generated import auth_pb2, auth_pb2_grpc
import jwt
from decouple import config
from django.db import transaction

from apps.core.services import create_user_account

User = get_user_model()


VALID_ROLES = {'admin', 'docente', 'alumno'}


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


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """Implementación del servicio gRPC de autenticación."""

    def ValidateToken(self, request, context):
        """Valida un JWT y retorna los claims del usuario."""
        try:
            token = _normalize_token(request.token)
            secret_key = config('SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])

            return auth_pb2.ValidateTokenResponse(
                valid=True,
                user_id=payload.get('user_id'),
                email=payload.get('email'),
                rol=payload.get('rol'),
                nombre=payload.get('nombre'),
            )
        except jwt.ExpiredSignatureError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token expirado')
            return auth_pb2.ValidateTokenResponse(valid=False)
        except jwt.InvalidTokenError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token inválido')
            return auth_pb2.ValidateTokenResponse(valid=False)

    def GetUserById(self, request, context):
        """Obtiene el perfil de un usuario por su ID."""
        try:
            user = User.objects.get(id=request.user_id, activo=True)
            return _build_user_profile(user)
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Usuario no encontrado o inactivo')
            return auth_pb2.UserProfile()

    def CheckRole(self, request, context):
        """Verifica si un usuario tiene un rol específico."""
        try:
            user = User.objects.get(id=request.user_id, activo=True)
            has_role = user.rol == request.role
            return auth_pb2.CheckRoleResponse(has_role=has_role)
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Usuario no encontrado')
            return auth_pb2.CheckRoleResponse(has_role=False)

    def CreateUser(self, request, context):
        """Crea un nuevo usuario."""
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
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Error al crear usuario: {str(e)}')
            return auth_pb2.CreateUserResponse(
                success=False,
                message=str(e),
                user_id=0,
            )


class Command(BaseCommand):
    help = 'Inicia el servidor gRPC de autenticación'

    def handle(self, *args, **options):
        grpc_port = config('GRPC_PORT', default='50051')

        # Crear servidor gRPC
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        auth_pb2_grpc.add_AuthServiceServicer_to_server(
            AuthServiceServicer(), server
        )

        # Configurar puerto
        server.add_insecure_port(f'0.0.0.0:{grpc_port}')
        server.start()

        self.stdout.write(
            self.style.SUCCESS(f'✓ Servidor gRPC iniciado en puerto {grpc_port}')
        )

        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)
            self.stdout.write(self.style.SUCCESS('✓ Servidor gRPC detenido'))
