"""Validacion JSON Schema del sobre y payloads."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from agm_events.envelope import EventEnvelope
from agm_events.exceptions import EventValidationError


def _contracts_dir() -> Path:
    override = os.getenv("EVENT_CONTRACTS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "contracts" / "events"


def _load_schema(filename: str) -> dict[str, Any]:
    path = _contracts_dir() / filename
    if not path.is_file():
        raise EventValidationError(f"Schema file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_envelope_dict(data: dict[str, Any]) -> None:
    schema = _load_schema("_envelope.schema.json")
    validator = Draft202012Validator(schema)
    try:
        validator.validate(data)
    except JsonSchemaValidationError as exc:
        raise EventValidationError(f"Envelope validation failed: {exc.message}") from exc


def validate_envelope(envelope: EventEnvelope) -> None:
    validate_envelope_dict(envelope.to_dict())


def validate_event_payload(event_name: str, payload: dict[str, Any]) -> None:
    schema_file = f"{event_name}.schema.json"
    schema_path = _contracts_dir() / schema_file
    if not schema_path.is_file():
        return
    schema = _load_schema(schema_file)
    validator = Draft202012Validator(schema)
    try:
        validator.validate(payload)
    except JsonSchemaValidationError as exc:
        raise EventValidationError(
            f"Payload validation failed for {event_name}: {exc.message}"
        ) from exc


def validate_full_event(envelope: EventEnvelope) -> None:
    validate_envelope(envelope)
    validate_event_payload(envelope.event_name, envelope.payload)
