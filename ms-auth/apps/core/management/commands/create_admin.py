import os
import secrets
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un usuario administrador inicial si no existe'

    def handle(self, *args, **options):
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@agm.buap.mx')
        admin_password = os.getenv('ADMIN_PASSWORD', None)
        
        # Si no hay contraseña en .env, generar una aleatoria
        if not admin_password:
            admin_password = secrets.token_urlsafe(12)
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  ADMIN_PASSWORD no definida en .env. Contraseña generada:'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'   📧 Email: {admin_email}\n   🔑 Contraseña: {admin_password}\n')
            )
        
        # Verificar si ya existe un admin
        if User.objects.filter(rol='admin').exists():
            self.stdout.write(
                self.style.SUCCESS('✓ Ya existe un usuario administrador en la base de datos.')
            )
            return
        
        # Crear el usuario admin
        try:
            admin_user = User.objects.create_user(
                email=admin_email,
                nombre='Administrador',
                rol='admin',
                password=admin_password
            )
            admin_user.activo = True
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Administrador creado exitosamente:\n'
                    f'   📧 Email: {admin_email}\n'
                    f'   🔑 Contraseña: {admin_password}\n'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error al crear administrador: {str(e)}')
            )
