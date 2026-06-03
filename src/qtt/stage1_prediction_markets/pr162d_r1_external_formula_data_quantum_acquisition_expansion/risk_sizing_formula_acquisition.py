"""Risk and sizing formula acquisition facade."""

from __future__ import annotations

from typing import Any


def risk_sizing_formula_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in formulas if record["formula_category"] == "RISK_SIZING_FORMULA"]
