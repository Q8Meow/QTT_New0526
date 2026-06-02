"""PR162C formula source extraction facade."""

from __future__ import annotations

from .formula_test_vectors import formula_delta_records


def extracted_formula_records() -> list[dict[str, object]]:
    return formula_delta_records()
