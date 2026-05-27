from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import constant_time_compare
from decouple import config

User = get_user_model()

VALID_ROLES = {'admin', 'docente', 'alumno'}


def is_internal_api_key_valid(request):
    expected_key = str(
        getattr(settings, 'INTERNAL_API_KEY', None) or config('INTERNAL_API_KEY', default='')
    ).strip()
    provided_key = request.headers.get('X-Internal-Api-Key', '').strip()
    if not expected_key:
        return False
    return constant_time_compare(provided_key, expected_key)


def create_user_account(*, email, nombre, rol, password, activo=True, link_existing=False):
    if rol not in VALID_ROLES:
        return None, 'Rol inválido'

    if not email or not nombre or not password:
        return None, 'Email, nombre y password son obligatorios'

    existing = User.objects.filter(email=email).first()
    if existing:
        if link_existing:
            if existing.rol != rol:
                return None, f'El email ya existe con rol {existing.rol}'
            return existing, None
        return None, 'El email ya está registrado'

    with transaction.atomic():
        user = User(
            email=email,
            nombre=nombre,
            rol=rol,
            activo=activo,
        )
        user.set_password(password)
        user.save()

    return user, None