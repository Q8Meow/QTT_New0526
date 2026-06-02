"""PR162C input-field coverage helpers."""

from __future__ import annotations

from typing import Iterable


def strict_field_coverage_status(
    required_fields: Iterable[str],
    provided_fields: Iterable[str],
) -> dict[str, object]:
    missing = sorted(set(required_fields) - set(provided_fields))
    return {
        "missing_input_fields": missing,
        "coverage_status": "STRICT_COVERED_REPO_LOCAL"
        if not missing
        else "BLOCKED_REQUIRED_FIELDS_MISSING",
    }
