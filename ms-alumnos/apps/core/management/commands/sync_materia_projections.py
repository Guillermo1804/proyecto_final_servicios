"""Sincroniza materia_projection desde MS-2 (gRPC lectura puntual, solo mantenimiento)."""

from __future__ import annotations

from unittest.mock import patch

from django.core.management.base import BaseCommand

from apps.core.event_bus import projection_service as proj
from apps.core.models import InscripcionMateria, MateriaProjection
from utils.periodos_ms2_client import (
    _materia_detail_from_grpc,
    refresh_inscripciones_from_detail,
)


class Command(BaseCommand):
    help = "Pobla materia_projection e inscripciones desde MS-2 (tras import sin eventos historicos)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--materia-id",
            type=int,
            default=0,
            help="Solo una materia (0 = todas las inscritas)",
        )

    def handle(self, *args, **options):
        materia_filter = int(options["materia_id"] or 0)
        qs = InscripcionMateria.objects.all()
        if materia_filter > 0:
            qs = qs.filter(materia_id=materia_filter)
        materia_ids = sorted({int(mid) for mid in qs.values_list("materia_id", flat=True) if mid})

        synced = 0
        with patch("grpc_clients.periodos_client.block_business_grpc"):
            for materia_id in materia_ids:
                detail = _materia_detail_from_grpc(materia_id)
                if not detail:
                    self.stdout.write(self.style.WARNING(f"Sin datos MS-2 para materia {materia_id}"))
                    continue
                proj.upsert_materia(
                    {
                        "materia_id": materia_id,
                        "periodo_id": detail.get("periodo_id", 0),
                        "periodo_nombre": detail.get("periodo_nombre", ""),
                        "nrc": detail.get("nrc", ""),
                        "nombre": detail.get("nombre", ""),
                        "seccion": detail.get("seccion", ""),
                        "clave": detail.get("clave", ""),
                        "horario": detail.get("horario", ""),
                        "docente_nombre": detail.get("docente_nombre", ""),
                        "docente_id": detail.get("docente_id"),
                    }
                )
                refresh_inscripciones_from_detail(materia_id, detail)
                synced += 1

        total = MateriaProjection.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {synced} materia(s) sincronizada(s); filas en materia_projection: {total}"
            )
        )
