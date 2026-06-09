"""Input-consumption records for PR165-B."""

from __future__ import annotations

from typing import Any

from .artifact_discovery import ArtifactDiscovery, source_inputs_from_discovery
from .deterministic_ids import ordinal_ref


def build_input_consumption_records(discovery: ArtifactDiscovery) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, rel_path in enumerate(discovery.required_inputs, start=1):
        present = rel_path not in discovery.missing_required_inputs
        records.append(
            {
                "input_consumption_ref": ordinal_ref("PR165_B_INPUT", index),
                "input_path": rel_path,
                "required": True,
                "present": present,
                "consumption_status": "CONSUMED" if present else "INPUT_RECEIPT_REQUIRED",
                "validation_status": "PASS" if present else "FAIL",
            }
        )
    return records


def build_optional_context_receipts(discovery: ArtifactDiscovery) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    index = 0
    for group in sorted(discovery.optional_missing):
        for rel_path in discovery.optional_missing[group]:
            index += 1
            records.append(
                {
                    "optional_context_receipt_ref": ordinal_ref("PR165_B_OPTIONAL_CONTEXT", index),
                    "optional_context_group": group,
                    "input_path": rel_path,
                    "required": False,
                    "present": False,
                    "consumption_status": "OPTIONAL_CONTEXT_RECEIPT_RECORDED",
                    "execution_blocking": False,
                    "validation_status": "PASS",
                }
            )
    if not records:
        records.append(
            {
                "optional_context_receipt_ref": ordinal_ref("PR165_B_OPTIONAL_CONTEXT", 1),
                "optional_context_group": "all_optional_context",
                "input_path": "all_configured_optional_context_present",
                "required": False,
                "present": True,
                "consumption_status": "OPTIONAL_CONTEXT_CONSUMED",
                "execution_blocking": False,
                "validation_status": "PASS",
            }
        )
    return records


def source_inputs(discovery: ArtifactDiscovery) -> list[str]:
    return source_inputs_from_discovery(discovery)
