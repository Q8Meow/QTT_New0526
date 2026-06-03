"""Formula equivalence and dedupe ledger."""

from __future__ import annotations

from typing import Any


def formula_equivalence_dedup_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for formula in formulas:
        dedupe_key = str(formula["dedupe_key"])
        duplicate = dedupe_key in seen
        seen.add(dedupe_key)
        rows.append(
            {
                "formula_id": formula["formula_id"],
                "formula_equivalence_family_id": formula["formula_equivalence_family_id"],
                "dedupe_key": dedupe_key,
                "duplicate_count_inflation_flag": duplicate,
                "dedupe_status": "UNIQUE_COUNTABLE_CANDIDATE" if not duplicate else "DUPLICATE_NOT_COUNTED",
                "live_order_authority": False,
            }
        )
    return rows
