"""Critical execution gap classifier for PR162R-A."""

from __future__ import annotations

from typing import Any

from .candidate_loader import agent_refs, candidate_type, route_refs


def critical_missing_info(record: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not record.get("source_locator"):
        missing.append("SOURCE_LOCATOR_MISSING")
    if not record.get("qku_refs"):
        missing.append("QKU_MAPPING_MISSING")
    if not agent_refs(record):
        missing.append("AGENT_ROUTE_MISSING")
    if not route_refs(record):
        missing.append("REPLAY_PAPER_ROUTE_MISSING")
    if record.get("metadata_only_flag") or record.get("quantum_metadata_only_flag"):
        missing.append("METADATA_ONLY_NOT_EXECUTABLE")
    if not _has_compute_path(record):
        missing.append("FORMULA_OR_ALGORITHM_MISSING")
    if not record.get("input_fields"):
        missing.append("INPUT_FIELD_UNDEFINED")
    if not record.get("output_fields"):
        missing.append("OUTPUT_FIELD_UNDEFINED")
    if not record.get("units"):
        missing.append("UNIT_SCALE_MISSING")
    if not _has_dataset_binding(record):
        missing.append("DATASET_BINDING_MISSING")
    if candidate_type(record) == "QUANTUM" and not _has_quantum_mapping(record):
        missing.append("QUANTUM_MAPPING_MISSING")
    if _requires_private_or_live_state(record):
        missing.append("AUTHENTICATED_LIVE_CONNECTOR_STATE_REQUIRED")
    return sorted(set(missing))


def _has_compute_path(record: dict[str, Any]) -> bool:
    return bool(
        record.get("expression")
        or record.get("deterministic_steps")
        or record.get("field_mapping")
        or record.get("mathematical_objective")
        or record.get("default_value_candidate") is not None
    )


def _has_dataset_binding(record: dict[str, Any]) -> bool:
    if record.get("field_mapping") and record.get("locator_schema_fields"):
        return True
    return bool(record.get("source_locator") and record.get("input_fields") and route_refs(record))


def _has_quantum_mapping(record: dict[str, Any]) -> bool:
    mappings = (
        record.get("qubo_mapping"),
        record.get("ising_mapping"),
        record.get("bqm_cqm_mapping"),
        record.get("qaoa_vqe_samplingvqe_annealing_mapping"),
    )
    return bool(
        record.get("mathematical_objective")
        and record.get("variable_definitions")
        and record.get("coefficient_definitions")
        and any(mappings)
    )


def _requires_private_or_live_state(record: dict[str, Any]) -> bool:
    text = " ".join(str(value).lower() for value in record.values())
    forbidden = ("credential-only", "private secret", "authenticated live", "live connector state")
    return any(token in text for token in forbidden)
