"""Carga y validación de consumer_bindings.json (cobertura de handlers)."""

from __future__ import annotations

import json
from pathlib import Path


def default_bindings_path() -> Path:
    import os

    contracts_dir = os.environ.get("EVENT_CONTRACTS_DIR", "").strip()
    if contracts_dir:
        return Path(contracts_dir) / "consumer_bindings.json"

    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    return repo_root / "contracts" / "events" / "consumer_bindings.json"


def load_consumer_bindings(path: Path | None = None) -> dict[str, list[str]]:
    bindings_path = path or default_bindings_path()
    raw = json.loads(bindings_path.read_text(encoding="utf-8"))
    return {
        key: list(value)
        for key, value in raw.items()
        if not key.startswith("$") and isinstance(value, list)
    }


def missing_handlers(
    service_key: str,
    registered_handlers: dict[str, object],
    *,
    path: Path | None = None,
) -> list[str]:
    bindings = load_consumer_bindings(path)
    required = bindings.get(service_key, [])
    return [event for event in required if event not in registered_handlers]
