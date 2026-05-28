from django.core.management.base import BaseCommand

from apps.core.jwt_keys import ensure_rsa_keypair


class Command(BaseCommand):
    help = "Genera el par RSA para JWT (RS256) si no existe."

    def handle(self, *args, **options):
        ensure_rsa_keypair()
        self.stdout.write(self.style.SUCCESS("Claves JWT RSA listas en ms-auth/keys/"))
