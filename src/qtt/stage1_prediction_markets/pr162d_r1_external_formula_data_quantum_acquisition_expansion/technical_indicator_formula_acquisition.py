"""Technical indicator formula acquisition facade."""

from __future__ import annotations

from typing import Any


def technical_indicator_formula_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in formulas if record["formula_category"] == "TECHNICAL_INDICATOR_FORMULA"]
