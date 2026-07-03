from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.build_pr169_dash1_owner_dashboard_ui import (
    MOBILE_TABS,
    PROVIDER_STAGES,
    SEMANTIC_COLORS,
    THEME_STORAGE_KEY,
    UI_ARTIFACT_FILES,
    build_ui,
)
from tools.validate_pr169_dash1_owner_dashboard_ui import validate


REPO_ROOT = Path(".")
BASE = Path("docs/master_plan/generated/pr169_dash1")
UI = BASE / "ui"


@pytest.fixture(scope="session", autouse=True)
def ui1_artifacts() -> Path:
    build_ui(BASE, REPO_ROOT)
    assert validate(BASE) == ()
    return BASE


def json_doc(path: str) -> dict[str, Any]:
    return json.loads((BASE / path).read_text(encoding="utf-8"))


def ui_doc(path: str) -> dict[str, Any]:
    return json.loads((UI / path).read_text(encoding="utf-8"))


def jsonl(path: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (BASE / path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def boot_data() -> dict[str, Any]:
    return ui_doc("owner_dashboard_review_data.generated.json")


def ui_text() -> str:
    return "\n".join(
        (UI / name).read_text(encoding="utf-8")
        for name in (
            "owner_dashboard_review_surface.html",
            "owner_dashboard_review_surface.css",
            "owner_dashboard_review_surface.js",
            "owner_dashboard_review_bootstrap.generated.js",
        )
    )


def walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(key)
            values.extend(walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(walk(child))
    return values
