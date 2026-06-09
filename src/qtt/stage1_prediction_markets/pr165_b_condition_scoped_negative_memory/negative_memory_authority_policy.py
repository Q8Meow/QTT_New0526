"""PR165-B replay/paper-only authority boundary policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PR_ID = "PR165-B"
EXPECTED_BRANCH = "pr165-b-condition-scoped-negative-memory"
AUTHORITY_CLASS = "PR165_B_CONDITION_SCOPED_MEMORY_REPLAY_PAPER_ONLY"
POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr165_b_condition_scoped_negative_memory.negative_memory_authority_policy"
)

FILES_INTENTIONALLY_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "protected AtomicRows bundle artifacts",
    "AtomicRows bundle hash/SHA/checksum artifacts",
    "QTT integrity freeze, checksum, and global-digest authority files",
    "accepted source-evidence truth packets",
    "connector semantic binding truth packets",
    "private-state/runtime-cash/order/live artifacts",
    "quantum backend/runtime execution artifacts",
    "LLM hot-path/source-acceptance/order-release/result-rewrite artifacts",
    "profit evidence / profit guarantee artifacts",
)

BOUNDARY_COUNT_FIELDS = {
    "connector_binding_count": 0,
    "final_paper_result_packet_authority_count": 0,
    "final_replay_result_packet_authority_count": 0,
    "live_order_authority_count": 0,
    "live_promotion_ready_claim_count": 0,
    "llm_api_call_count": 0,
    "llm_browser_agent_count": 0,
    "llm_model_loading_count": 0,
    "llm_order_release_count": 0,
    "llm_prompt_execution_count": 0,
    "llm_result_rewrite_count": 0,
    "llm_runtime_inference_count": 0,
    "llm_source_acceptance_count": 0,
    "llm_tool_calling_agent_count": 0,
    "llm_trade_decision_count": 0,
    "order_ready_claim_count": 0,
    "paper_result_packet_count": 0,
    "private_state_fetch_count": 0,
    "profit_evidence_count": 0,
    "protected_atomicrows_bundle_checksum_mutation_count": 0,
    "qtt_freeze_checksum_global_digest_authority_count": 0,
    "qtt_generated_sha_authority_count": 0,
    "quantum_advantage_claim_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_simulator_execution_count": 0,
    "replay_result_packet_count": 0,
    "runtime_cash_receipt_count": 0,
    "source_acceptance_count": 0,
}

NO_AUTHORITY_FLAGS = {
    "calls_llm_api": False,
    "ci_requires_network": False,
    "creates_connector_binding": False,
    "creates_final_paper_result_packet_authority": False,
    "creates_final_replay_result_packet_authority": False,
    "creates_live_order_authority": False,
    "creates_live_promotion_ready_claim": False,
    "creates_order_ready_claim": False,
    "creates_paper_result_packets": False,
    "creates_profit_evidence": False,
    "creates_qtt_freeze_checksum_global_digest_authority": False,
    "creates_qtt_generated_sha_authority": False,
    "creates_quantum_advantage_claim": False,
    "creates_replay_result_packets": False,
    "creates_runtime_cash_receipt": False,
    "creates_source_acceptance": False,
    "executes_llm_prompt": False,
    "executes_quantum_backend": False,
    "executes_quantum_simulator": False,
    "fetches_private_state": False,
    "loads_llm_model": False,
    "mutates_protected_atomicrows_bundle_checksum_artifacts": False,
    "uses_llm_browser_agent": False,
    "uses_llm_order_release": False,
    "uses_llm_result_rewrite": False,
    "uses_llm_runtime_inference": False,
    "uses_llm_source_acceptance": False,
    "uses_llm_tool_calling_agent": False,
    "uses_llm_trade_decision": False,
}


def authority_boundary_record(subject_id: str) -> dict[str, Any]:
    return {
        "authority_boundary_ref": f"PR165_B_AUTHORITY_BOUNDARY::{subject_id}",
        "authority_class": AUTHORITY_CLASS,
        "replay_selection_allowed": True,
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "source_truth_conversion_allowed": False,
        "connector_binding_allowed": False,
        "runtime_cash_receipt_allowed": False,
        "live_order_authority_allowed": False,
        "quantum_backend_execution_allowed": False,
        "quantum_advantage_claim_allowed": False,
        "llm_hot_path_authority_allowed": False,
        "qtt_sha_freeze_checksum_authority_allowed": False,
        "atomicrows_bundle_hash_authority_allowed": False,
        "policy_module_ref": POLICY_MODULE_REF,
    }


def no_authority_record(record_ref: str, report_label: str) -> dict[str, Any]:
    return {
        "authority_audit_ref": record_ref,
        "report_label": report_label,
        "all_authority_counts_zero": True,
        "authority_counts": dict(BOUNDARY_COUNT_FIELDS),
        "authority_class": AUTHORITY_CLASS,
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
        "validation_status": "PASS",
    }


@dataclass(frozen=True)
class AuthorityValidation:
    failures: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.failures


def validate_record_authority(record: dict[str, Any]) -> AuthorityValidation:
    failures: list[str] = []
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        value = record.get(key)
        if value not in (None, expected):
            failures.append(f"authority count drift for {key}: {value!r}")
    boundary = record.get("authority_boundary") or record.get("authority_boundary_ref")
    if isinstance(boundary, dict):
        if boundary.get("live_selection_allowed") is not False:
            failures.append("authority boundary permits live selection")
        if boundary.get("source_truth_conversion_allowed") is not False:
            failures.append("authority boundary permits source truth conversion")
        if boundary.get("quantum_backend_execution_allowed") is not False:
            failures.append("authority boundary permits quantum backend execution")
    return AuthorityValidation(tuple(failures))
