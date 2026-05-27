"""Reconciliación idempotente de proyecciones MS-4 con BD fuente (MS-2 / MS-3)."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Alinea MateriaProjection, AlumnoMateriaProjection y UserProjection "
        "con las BD de MS-2 y MS-3 (no borra calificaciones locales)."
    )

    def handle(self, *args, **options):
        call_command("backfill_calificaciones_projections")
