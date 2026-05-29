"""Value-state classifier helper for PR161A."""

from __future__ import annotations

from typing import Mapping


def classify_value_state(record: Mapping[str, object]) -> str:
    return str(record.get("value_materialization_state") or "UNCLASSIFIED")

