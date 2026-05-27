"""Reconciliación idempotente de proyecciones MS-3 (materias desde MS-2)."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sincroniza materia_projection e inscripciones desde MS-2 (lectura puntual de mantenimiento)."

    def handle(self, *args, **options):
        call_command("sync_materia_projections")
