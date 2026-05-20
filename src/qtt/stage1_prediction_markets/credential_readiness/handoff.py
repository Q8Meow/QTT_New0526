from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.credential_readiness import policy


def build_downstream_handoff(
    alias_records: list[Mapping[str, object]],
    readiness_receipts: list[Mapping[str, object]],
    scope_bindings: list[Mapping[str, object]],
) -> dict[str, object]:
    return {
        **policy.common_record_fields("CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF"),
        "handoff_id": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "downstream_prs": list(policy.DOWNSTREAM_PR_IDS),
        "venue_specific_scope": list(policy.STAGE1_VENUE_IDS),
        "shared_scope": list(policy.SHARED_SCOPE_IDS),
        "credential_alias_registry_refs": [
            record["credential_alias_id"] for record in alias_records
        ],
        "credential_alias_readiness_receipt_refs": [
            record["receipt_id"] for record in readiness_receipts
        ],
        "credential_scope_binding_refs": [
            record["binding_id"] for record in scope_bindings
        ],
        "contains_secrets": False,
        "contains_live_credentials": False,
        "contains_production_authority": False,
        "contains_private_state_payload": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
        "downstream_may_consume_metadata_only": True,
        "downstream_may_resolve_credentials": False,
        "downstream_may_call_provider": False,
        "downstream_may_call_venue_api_from_this_handoff": False,
        "future_atomicrows_parameter_row_refs": [],
        "future_atomicrows_family_refs": [],
        "future_atomicrows_credential_readiness_family_ref": (
            "FUTURE_ATOMICROWS_CREDENTIAL_READINESS_METADATA_ONLY"
        ),
        "future_quantum_optimizer_credential_readiness_ref": (
            "FUTURE_QUANTUM_OPTIMIZER_CREDENTIAL_READINESS_METADATA_ONLY"
        ),
        "quantum_backend_called": False,
        "quantum_simulator_called": False,
        "quantum_optimizer_called": False,
        "quantum_advantage_claim_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
    }
