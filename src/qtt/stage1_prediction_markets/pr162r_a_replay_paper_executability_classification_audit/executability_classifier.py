"""Primary replay/paper executability classifier."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type, route_refs
from .critical_missing_info_classifier import critical_missing_info
from .noncritical_missing_info_classifier import noncritical_tags


def classify_executability(record: dict[str, Any], micro_materialized: bool = False) -> dict[str, Any]:
    cid = candidate_id(record)
    critical = critical_missing_info(record)
    tags = noncritical_tags(record)
    if micro_materialized:
        tags.append("MICRO_MATERIALIZED_IN_PR162R_A")
    if critical:
        tags.append("TARGETED_CRITICAL_GAP_FOR_PR162D_R2")
    primary = _primary_state(record, critical, tags)
    return {
        "classification_id": f"PR162R_A_EXEC::{cid}",
        "candidate_id": cid,
        "candidate_type": candidate_type(record),
        "primary_executability_state": primary,
        "secondary_tags": sorted(set(tags)),
        "critical_missing_info": critical,
        "replay_route_ready_flag": "REPLAY_ENGINE_INPUT_PREP" in " ".join(route_refs(record)),
        "paper_route_ready_flag": "PAPER_ENGINE_INPUT_PREP" in " ".join(route_refs(record)),
        "candidate_or_provisional_flag": bool(record.get("candidate_or_provisional_flag", True)),
        "source_locator": record.get("source_locator"),
        "qku_refs": record.get("qku_refs") or [],
        "agent_refs": record.get("agent_refs") or record.get("agent_route_refs") or [],
        "replay_paper_route_refs": route_refs(record),
        "live_order_authority": False,
    }


def _primary_state(record: dict[str, Any], critical: list[str], tags: list[str]) -> str:
    if critical:
        if "SOURCE_LOCATOR_MISSING" in critical:
            return "NON_EXECUTABLE_SOURCE_LOCATOR_MISSING"
        if "QUANTUM_MAPPING_MISSING" in critical and candidate_type(record) == "QUANTUM":
            return "NON_EXECUTABLE_QUANTUM_MAPPING_MISSING"
        if "DATASET_BINDING_MISSING" in critical:
            return "NON_EXECUTABLE_DATASET_BINDING_MISSING"
        if "FORMULA_OR_ALGORITHM_MISSING" in critical:
            return "NON_EXECUTABLE_FORMULA_OR_ALGORITHM_MISSING"
        return "NON_EXECUTABLE_CRITICAL_INPUT_MISSING"
    partial_types = {"PARAMETER", "DATASET", "QUANTUM"}
    partial_tags = {
        "NON_OFFICIAL_SOURCE",
        "PROVISIONAL_SOURCE",
        "PARAMETER_CALIBRATION_NEEDED",
        "QUANTUM_BACKEND_OPTIONAL",
        "RISK_REVIEW_NEEDED",
        "CAPITAL_SIZING_REVIEW_NEEDED",
    }
    if candidate_type(record) in partial_types or any(tag in partial_tags for tag in tags):
        return "PARTIAL_EXECUTABLE_REPLAY_AND_PAPER_READY"
    return "EXECUTABLE_REPLAY_AND_PAPER_READY"
