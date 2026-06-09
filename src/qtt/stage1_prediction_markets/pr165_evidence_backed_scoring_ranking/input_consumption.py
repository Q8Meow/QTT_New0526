"""Input consumption audit builders for PR165."""

from __future__ import annotations

from typing import Any

from .artifact_discovery import Discovery


def source_inputs_from_discovery(discovery: Discovery) -> list[str]:
    return discovery.source_inputs


def build_optional_context_receipts(discovery: Discovery) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for group, missing in sorted(discovery.optional_missing.items()):
        for rel_path in missing:
            rows.append(
                {
                    "optional_context_receipt_ref": f"PR165_OPTIONAL_CONTEXT::{index:06d}",
                    "input_group": group,
                    "missing_input_path": rel_path,
                    "scoring_blocked": False,
                    "receipt_reason": "OPTIONAL_CONTEXT_ABSENT_REQUIRED_INPUTS_PRESENT",
                    "fallback_context_used": discovery.optional_present.get(group, []),
                    "validation_status": "PASS",
                }
            )
            index += 1
    return rows
