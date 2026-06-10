"""Authority boundary for PR165-D selection-only artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .central_vocab import AUTHORITY_BOUNDARY_REF, AUTHORITY_CLASS

POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr165_d_scenario_qku_combination_selection.authority_policy"
)

AUTHORITY_COUNT_FIELDS = (
    "connector_runtime_binding_count",
    "live_order_authority_count",
    "live_promotion_claim_count",
    "llm_hot_path_or_order_release_count",
    "order_ready_claim_count",
    "private_state_fetch_count",
    "profit_evidence_claim_count",
    "protected_integrity_authority_count",
    "quantum_advantage_claim_count",
    "quantum_backend_execution_count",
    "runtime_cash_receipt_count",
    "source_truth_conversion_count",
    "fake_retest_result_count",
)

FILES_INTENTIONALLY_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "live order authority files",
    "source-truth packet files",
    "connector binding files",
    "private-state fetch files",
    "runtime cash receipt files",
    "profit evidence files",
    "quantum backend execution files",
    "QTT protected integrity digest authority files",
    "AtomicRows bundle SHA/hash/checksum authority files",
)


def authority_zero_counts() -> dict[str, int]:
    return {field: 0 for field in AUTHORITY_COUNT_FIELDS}


def authority_boundary_record() -> dict[str, Any]:
    return {
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "authority_class": AUTHORITY_CLASS,
        "policy_module_ref": POLICY_MODULE_REF,
        "scenario_selection_allowed": True,
        "retest_batch_queue_allowed": True,
        "repair_before_retest_queue_allowed": True,
        "dashboard_governance_commander_handoffs_allowed": True,
        "optional_candidate_input_consumption_allowed": True,
        "source_truth_conversion_allowed": False,
        "connector_runtime_binding_allowed": False,
        "live_order_authority_allowed": False,
        "live_promotion_claim_allowed": False,
        "order_ready_claim_allowed": False,
        "private_state_fetch_allowed": False,
        "profit_evidence_claim_allowed": False,
        "runtime_cash_receipt_allowed": False,
        "quantum_backend_execution_allowed": False,
        "quantum_advantage_claim_allowed": False,
        "llm_hot_path_or_order_release_allowed": False,
        "protected_integrity_authority_allowed": False,
    }


def authority_absence_confirmation() -> dict[str, bool]:
    return {
        "source_truth_conversion_absent": True,
        "connector_runtime_binding_absent": True,
        "live_order_authority_absent": True,
        "live_promotion_claim_absent": True,
        "order_ready_claim_absent": True,
        "private_state_fetch_absent": True,
        "profit_evidence_claim_absent": True,
        "runtime_cash_receipt_absent": True,
        "quantum_backend_execution_absent": True,
        "quantum_advantage_claim_absent": True,
        "llm_hot_path_or_order_release_absent": True,
        "protected_integrity_authority_absent": True,
        "fake_retest_result_absent": True,
    }


@dataclass(frozen=True)
class RecordAuthorityValidation:
    failures: tuple[str, ...]


def validate_record_authority(record: dict[str, Any]) -> RecordAuthorityValidation:
    failures = []
    for field in AUTHORITY_COUNT_FIELDS:
        if int(record.get(field, 0) or 0) != 0:
            failures.append(f"nonzero authority count {field}")
    if record.get("authority_boundary_ref") not in (None, "", AUTHORITY_BOUNDARY_REF):
        failures.append("authority boundary ref drift")
    return RecordAuthorityValidation(tuple(failures))
