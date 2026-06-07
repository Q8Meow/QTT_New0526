"""Central authority policy for PR164."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PR_ID = "PR164"
EXPECTED_BRANCH = "pr164-review-provenance-qku-canonical-coverage-audit"
AUTHORITY_CLASS = "PR164_REVIEW_PROVENANCE_QKU_MATERIALIZATION_NONLIVE_CANDIDATE_ONLY"
POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr164_review_provenance_qku_canonical_coverage_audit.authority_policy"
)

NO_AUTHORITY_FLAGS: dict[str, bool] = {
    "creates_replay_result_packets": False,
    "creates_paper_result_packets": False,
    "creates_final_replay_result_packet_authority": False,
    "creates_final_paper_result_packet_authority": False,
    "creates_profit_evidence": False,
    "creates_live_order_authority": False,
    "creates_order_ready_claim": False,
    "creates_live_promotion_ready_claim": False,
    "creates_source_acceptance": False,
    "creates_connector_binding": False,
    "fetches_private_state": False,
    "creates_runtime_cash_receipt": False,
    "executes_quantum_backend": False,
    "executes_quantum_simulator": False,
    "creates_quantum_advantage_claim": False,
    "creates_qtt_freeze_checksum_global_digest_authority": False,
    "creates_qtt_generated_sha_authority": False,
    "mutates_protected_atomicrows_bundle_checksum_artifacts": False,
    "uses_llm_runtime_inference": False,
    "loads_llm_model": False,
    "calls_llm_api": False,
    "executes_llm_prompt": False,
    "uses_llm_tool_calling_agent": False,
    "uses_llm_browser_agent": False,
    "uses_llm_trade_decision": False,
    "uses_llm_order_release": False,
    "uses_llm_source_acceptance": False,
    "uses_llm_result_rewrite": False,
    "ci_requires_network": False,
}

BOUNDARY_COUNT_FIELDS: dict[str, int] = {
    "replay_result_packet_count": 0,
    "paper_result_packet_count": 0,
    "final_replay_result_packet_authority_count": 0,
    "final_paper_result_packet_authority_count": 0,
    "profit_evidence_count": 0,
    "live_order_authority_count": 0,
    "order_ready_claim_count": 0,
    "live_promotion_ready_claim_count": 0,
    "source_acceptance_count": 0,
    "connector_binding_count": 0,
    "private_state_fetch_count": 0,
    "runtime_cash_receipt_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_simulator_execution_count": 0,
    "quantum_advantage_claim_count": 0,
    "llm_runtime_inference_count": 0,
    "llm_model_loading_count": 0,
    "llm_api_call_count": 0,
    "llm_prompt_execution_count": 0,
    "llm_tool_calling_agent_count": 0,
    "llm_browser_agent_count": 0,
    "llm_trade_decision_count": 0,
    "llm_order_release_count": 0,
    "llm_source_acceptance_count": 0,
    "llm_result_rewrite_count": 0,
    "qtt_freeze_checksum_global_digest_authority_count": 0,
    "qtt_generated_sha_authority_count": 0,
    "protected_atomicrows_bundle_checksum_mutation_count": 0,
    "pr164_created_ref_integrity_authority_violation_count": 0,
}

ROW_NO_AUTHORITY_FIELDS: dict[str, Any] = {
    "live_allowed": False,
    "source_accepted": False,
    "connector_bound": False,
    "private_state_fetched": False,
    "runtime_cash_receipt_created": False,
    "replay_result_packet_created": False,
    "paper_result_packet_created": False,
    "final_result_packet_created": False,
    "profit_evidence_created": False,
    "live_authority_created": False,
    "order_ready_claim_created": False,
    "quantum_backend_executed": False,
    "quantum_simulator_executed": False,
    "quantum_advantage_claimed": False,
    "llm_runtime_inference_used": False,
    "llm_model_loaded": False,
    "llm_api_called": False,
    "llm_prompt_executed": False,
    "llm_order_release_used": False,
    "llm_source_acceptance_used": False,
    "llm_result_rewrite_used": False,
    "no_live_authority": True,
    "no_live_order_authority": True,
    "no_order_ready_claim": True,
    "no_live_promotion_ready_claim": True,
    "no_profit_evidence": True,
    "no_source_acceptance": True,
    "no_connector_binding": True,
    "no_private_state_fetch": True,
    "no_runtime_cash_receipt": True,
    "no_quantum_backend": True,
    "no_quantum_advantage_claim": True,
    "no_llm_runtime": True,
}

FILES_INTENTIONALLY_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "protected AtomicRows artifacts",
)


@dataclass(frozen=True)
class AuthorityCheck:
    ok: bool
    failures: tuple[str, ...]


def no_authority_fields() -> dict[str, Any]:
    return {**ROW_NO_AUTHORITY_FIELDS, **BOUNDARY_COUNT_FIELDS}


def no_authority_record(record_id: str, audit_family: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "audit_family": audit_family,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "central_policy_consumed_flag": True,
        "authority_decision": "NO_AUTHORITY_CREATED_BY_PR164",
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def validate_record_authority(record: dict[str, Any]) -> AuthorityCheck:
    failures: list[str] = []
    for key, expected in NO_AUTHORITY_FLAGS.items():
        if key in record and record[key] is not expected:
            failures.append(f"authority flag drift: {key}={record[key]!r}")
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        if key in record and record[key] != expected:
            failures.append(f"boundary count drift: {key}={record[key]!r}")
    for key in (
        "live_order_authority",
        "source_acceptance",
        "connector_binding",
        "private_state_fetch",
        "runtime_cash_receipt",
    ):
        if record.get(key) is True:
            failures.append(f"forbidden authority field true: {key}")
    return AuthorityCheck(not failures, tuple(failures))
