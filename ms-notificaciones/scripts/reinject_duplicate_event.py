"""Reinyecta un evento duplicado en agm.domain (prueba Fase 5 escenario c)."""
from __future__ import annotations

from agm_events.config import EventBusConfig, load_env
from agm_events.envelope import EventEnvelope
from agm_events.publisher import EventPublisher

EVENT_ID = "b3edc7824c144898bf235a58cfad68d8"


def main() -> None:
    load_env()
    cfg = EventBusConfig.from_env()
    payload = {
        "nrc": "DEMO01",
        "email": "fase5.test@buap.mx",
        "nombre": "Luis Notif",
        "alumno_id": 14,
        "matricula": "FASE5-001",
        "materia_id": 1,
        "periodo_id": 1,
        "clave_acceso": "Pass-F5-99",
        "docente_email": "docente.demo@agm.buap.mx",
        "docente_nombre": "Docente Demo",
        "materia_nombre": "Materia Demo AGM",
    }
    envelope = EventEnvelope(
        event_id=EVENT_ID,
        event_name="alumno.imported.v1",
        event_version=1,
        aggregate_type="alumno",
        aggregate_id="14",
        source_service="ms-alumnos",
        correlation_id="e0e94626-9edb-417b-a26e-822899f8d83e",
        causation_id="e0e94626-9edb-417b-a26e-822899f8d83e",
        occurred_at="2026-05-22T12:00:00Z",
        payload=payload,
    )
    pub = EventPublisher(cfg)
    pub.connect()
    pub.publish(envelope)
    pub.close()
    print(f"REPUBLISHED event_id={EVENT_ID}")


if __name__ == "__main__":
    main()
