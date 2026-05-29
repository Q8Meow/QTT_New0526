"""PR154 universe loader for PR161A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import as_list, as_mapping, read_json


def load_pr154_universe(root: Path) -> list[dict[str, Any]]:
    payload = as_mapping(read_json(root / c.PR157_PR154_REGISTRY_PATH))
    return sorted(
        [dict(record) for record in as_list(payload.get("records"))],
        key=lambda item: str(item.get("target_id")),
    )


def pr154_target_id(record: dict[str, Any]) -> str:
    return str(record.get("target_id"))

