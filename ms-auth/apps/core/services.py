from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import constant_time_compare
from decouple import config

User = get_user_model()

VALID_ROLES = {'admin', 'docente', 'alumno'}


def is_internal_api_key_valid(request):
    expected_key = config('INTERNAL_API_KEY', default='')
    provided_key = request.headers.get('X-Internal-Api-Key', '')
    if not expected_key:
        return False
    return constant_time_compare(provided_key, expected_key)


def create_user_account(*, email, nombre, rol, password, activo=True):
    if rol not in VALID_ROLES:
        return None, 'Rol inválido'

    if not email or not nombre or not password:
        return None, 'Email, nombre y password son obligatorios'

    if User.objects.filter(email=email).exists():
        return None, 'El email ya está registrado'

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            nombre=nombre,
            rol=rol,
            password=password,
        )
        user.activo = activo
        user.save(update_fields=['activo'])

    return user, None