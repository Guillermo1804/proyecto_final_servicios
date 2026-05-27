import logging
from concurrent import futures

import grpc
import jwt
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config

from apps.core.jwt_keys import get_rsa_public_key_pem
from apps.core.services import create_user_account
from proto_generated import agm_common_pb2, auth_pb2, auth_pb2_grpc

logger = logging.getLogger(__name__)
User = get_user_model()
VALID_ROLES = {'admin', 'docente', 'alumno'}


def _normalize_token(raw: str) -> str:
    token = (raw or '').strip()
    if token.startswith('Bearer '):
        return token[7:].strip()
    return token


def _invalid_token_response() -> auth_pb2.ValidateTokenResponse:
    return auth_pb2.ValidateTokenResponse(
        result=agm_common_pb2.TokenValidationResult(valid=False),
    )


def _build_user_profile(user) -> auth_pb2.UserProfile:
    return auth_pb2.UserProfile(
        claims=agm_common_pb2.UserClaims(
            user_id=user.id,
            email=user.email,
            nombre=user.nombre,
            rol=user.rol,
        ),
        activo=user.activo,
    )


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """Implementación gRPC alineada con RS256 (mismo criterio que REST + JWKS)."""

    def ValidateToken(self, request, context):
        try:
            from agm_events.jwt_revocation import is_jti_revoked

            credential = request.credential
            token = _normalize_token(
                credential.access_token if credential else '',
            )
            if not token:
                return _invalid_token_response()

            public_pem = get_rsa_public_key_pem()
            claims = jwt.decode(token, public_pem, algorithms=['RS256'])

            jti = claims.get('jti')
            if jti and is_jti_revoked(str(jti)):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details('Token revocado')
                return _invalid_token_response()

            user_id = claims.get('user_id') or claims.get('sub')
            return auth_pb2.ValidateTokenResponse(
                result=agm_common_pb2.TokenValidationResult(
                    valid=True,
                    user=agm_common_pb2.UserClaims(
                        user_id=int(user_id),
                        email=str(claims.get('email', '')),
                        nombre=str(claims.get('nombre', '')),
                        rol=str(claims.get('rol', '')),
                    ),
                    jti=str(jti or ''),
                    expires_at_unix=int(claims.get('exp', 0) or 0),
                ),
            )
        except jwt.ExpiredSignatureError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token expirado')
            return _invalid_token_response()
        except jwt.InvalidTokenError as exc:
            logger.warning('grpc_validate_token_failed', extra={'error': str(exc)})
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Token inválido')
            return _invalid_token_response()

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
                link_existing=True,
            )
            if error:
                return auth_pb2.CreateUserResponse(success=False, message=error, user_id=0)
            return auth_pb2.CreateUserResponse(
                success=True,
                message='Usuario creado exitosamente',
                user_id=user.id,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Error al crear usuario: {exc}')
            return auth_pb2.CreateUserResponse(success=False, message=str(exc), user_id=0)


class Command(BaseCommand):
    help = 'Inicia el servidor gRPC de autenticación'

    def handle(self, *args, **options):
        grpc_port = config('GRPC_PORT', default='50051')
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
        server.add_insecure_port(f'0.0.0.0:{grpc_port}')
        server.start()
        self.stdout.write(self.style.SUCCESS(f'Servidor gRPC iniciado en puerto {grpc_port}'))
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)
            self.stdout.write(self.style.SUCCESS('Servidor gRPC detenido'))
