"""Usuarios demo AGM (admin, docente, alumnos) con contraseñas conocidas."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

DEMO_USERS = [
    {
        'email': 'admin@agm.buap.mx',
        'nombre': 'Administrador AGM',
        'rol': 'admin',
        'password': 'admin123',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'docente.demo@agm.buap.mx',
        'nombre': 'María Docente Demo',
        'rol': 'docente',
        'password': 'Docente123!',
    },
    {
        'email': 'alumno.demo@agm.buap.mx',
        'nombre': 'Ana Alumno Demo',
        'rol': 'alumno',
        'password': 'Alumno123!',
    },
    {
        'email': 'alumno2.demo@agm.buap.mx',
        'nombre': 'Luis Alumno Demo',
        'rol': 'alumno',
        'password': 'Alumno123!',
    },
    {
        'email': 'alumno3.demo@agm.buap.mx',
        'nombre': 'Sofía Alumno Demo',
        'rol': 'alumno',
        'password': 'Alumno123!',
    },
]


class Command(BaseCommand):
    help = 'Crea o actualiza usuarios demo MS-1 (idempotente)'

    def handle(self, *args, **options):
        ids = {}
        for spec in DEMO_USERS:
            user, created = User.objects.update_or_create(
                email=spec['email'],
                defaults={
                    'nombre': spec['nombre'],
                    'rol': spec['rol'],
                    'activo': True,
                    'is_active': True,
                    'is_staff': spec.get('is_staff', False),
                    'is_superuser': spec.get('is_superuser', False),
                },
            )
            user.set_password(spec['password'])
            user.save()
            ids[spec['email']] = user.id
            verb = 'Creado' if created else 'Actualizado'
            self.stdout.write(f'{verb}: {spec["email"]} (id={user.id}, rol={spec["rol"]})')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Credenciales demo MS-1 ==='))
        for spec in DEMO_USERS:
            self.stdout.write(f'  {spec["email"]} / {spec["password"]}')
        self.stdout.write('')
        self.stdout.write(f'SEED_ADMIN_USUARIO_ID={ids["admin@agm.buap.mx"]}')
        self.stdout.write(f'SEED_DOCENTE_USUARIO_ID={ids["docente.demo@agm.buap.mx"]}')
        self.stdout.write(f'SEED_ALUMNO_USUARIO_ID={ids["alumno.demo@agm.buap.mx"]}')
        self.stdout.write(f'SEED_ALUMNO2_USUARIO_ID={ids["alumno2.demo@agm.buap.mx"]}')
        self.stdout.write(f'SEED_ALUMNO3_USUARIO_ID={ids["alumno3.demo@agm.buap.mx"]}')
