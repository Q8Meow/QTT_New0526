"""QKU/formula/algorithm/agent routing for PR163 paper mode."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref
from .paper_contracts import DOWNSTREAM_AGENT_ROUTES


def build_qku_route(index: int, row_resolution: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_qku_route_ref": plain_ref("QKU_AGENT_ROUTE", index),
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "formulation_refs": [row_resolution.get("formulation_ref")] if row_resolution.get("formulation_ref") else [],
        "formula_refs": [row_resolution.get("callable_ref")] if row_resolution.get("callable_ref") else [],
        "algorithm_refs": ["PR163_PAPER_DECISION_ALGORITHM_V1"],
        "agent_refs": row_resolution.get("agent_refs", []),
        "upstream_refs": row_resolution.get("upstream_refs", []),
        "downstream_refs": list(DOWNSTREAM_AGENT_ROUTES),
        "paper_binding_refs": row_resolution.get("paper_binding_refs", []),
        "quantum_binding_refs": row_resolution.get("quantum_binding_refs", []),
        "orphan_flag": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
