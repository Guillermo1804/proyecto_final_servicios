from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Envía un correo de prueba para verificar la configuración SMTP (ISSUE-801).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            required=True,
            help='Dirección de correo destino (ej. tu@gmail.com)',
        )

    def handle(self, *args, **options):
        to_email = options['to'].strip()
        if not to_email or '@' not in to_email:
            raise CommandError('Proporciona un correo válido con --to')

        if not settings.EMAIL_HOST_USER:
            raise CommandError('EMAIL_HOST_USER no está configurado en el entorno')

        subject = 'AGM MS-6 — Correo de prueba SMTP'
        message = (
            'Este es un correo de prueba del microservicio de Notificaciones (MS-6).\n\n'
            'Si lo recibes, la configuración SMTP es correcta.'
        )
        from_email = settings.DEFAULT_FROM_EMAIL

        try:
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Error al enviar correo: {exc}') from exc

        if sent != 1:
            raise CommandError(f'send_mail devolvió {sent}; se esperaba 1')

        self.stdout.write(
            self.style.SUCCESS(
                f'Correo de prueba enviado a {to_email} (from: {from_email})'
            )
        )
