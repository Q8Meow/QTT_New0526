#!/usr/bin/env python3
"""Formula registry loader for PR168-GFP2R."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.pr168_gfp2r_config import GENERATED_ROOT


FORMULA_REGISTRY_PATHS = [
    GENERATED_ROOT / "PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
    GENERATED_ROOT / "PR168_GFP_MasterPlanFormulaCatalog.report.json",
    GENERATED_ROOT / "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
]


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        records = value.get("records", value)
        if isinstance(records, list):
            return [row for row in records if isinstance(row, dict)]
        if isinstance(records, dict):
            for key in ("rows", "formulas", "formula_rows"):
                rows = records.get(key)
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]
    return []


def load_formula_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in FORMULA_REGISTRY_PATHS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        for row in _rows(payload):
            formula_id = row.get("formula_id")
            if formula_id and formula_id not in registry:
                registry[str(formula_id)] = dict(row)
    return registry
