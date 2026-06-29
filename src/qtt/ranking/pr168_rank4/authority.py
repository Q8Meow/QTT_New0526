"""Authority-boundary helpers for PR168-RANK4."""

from __future__ import annotations

from .models import FALSE_AUTHORITY_FIELDS


def false_authority_payload() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORITY_FIELDS}

