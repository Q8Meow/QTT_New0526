from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.qtt.dashboard.owner_dashboard_projection_builder import build_all
from src.qtt.dashboard.owner_dashboard_validator import validate_artifacts


BASE = Path("docs/master_plan/generated/pr169_dash1")


@pytest.fixture(scope="session", autouse=True)
def dash1_artifacts() -> Path:
    if not (BASE / "owner_dashboard_surface_registry.jsonl").exists():
        build_all(BASE)
    failures = validate_artifacts(BASE)
    assert failures == ()
    return BASE


def jsonl(name: str) -> list[dict[str, Any]]:
    path = BASE / name
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def json_doc(name: str) -> dict[str, Any]:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def registry() -> list[dict[str, Any]]:
    return jsonl("owner_dashboard_surface_registry.jsonl")


def registry_ids() -> set[str]:
    return {row["feature_id"] for row in registry()}
