"""Authority boundary policy for PR166-S artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .central_vocab import AUTHORITY_BOUNDARY_REF


ZERO_AUTHORITY_KEYS = (
    "live_authority_rows",
    "live_order_authority_count",
    "live_promotion_claim_count",
    "source_truth_acceptance_count",
    "source_truth_conversion_count",
    "connector_runtime_binding_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_count",
    "profit_evidence_count",
    "profit_evidence_claim_count",
    "fake_live_result_count",
    "quantum_backend_execution_count",
    "quantum_backend_execution_rows",
    "quantum_advantage_claim_count",
    "quantum_advantage_claim_rows",
    "llm_hot_path_or_order_release_count",
    "protected_integrity_authority_count",
)

FILES_INTENTIONALLY_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "AtomicRows protected bundle files",
    "live connector binding files",
    "runtime/live order-routing files",
)


@dataclass(frozen=True)
class AuthorityValidationResult:
    failures: tuple[str, ...]


def authority_zero_counts() -> dict[str, int]:
    return {key: 0 for key in ZERO_AUTHORITY_KEYS}


def authority_boundary_record() -> dict[str, Any]:
    return {
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "authority_scope": "DETERMINISTIC_REPLAY_PAPER_SCENARIO_RETEST_EXECUTION_ONLY",
        "no_live_execution": True,
        "no_live_order_authority": True,
        "no_live_order_routing": True,
        "no_connector_semantic_binding": True,
        "no_private_state_fetch": True,
        "no_source_truth_acceptance": True,
        "no_profit_evidence": True,
        "no_quantum_backend_execution": True,
        "no_quantum_advantage_claim": True,
        "paper_adapter_scope": "SIMULATED_ADAPTER_ONLY",
    }


def authority_absence_confirmation() -> dict[str, Any]:
    return {
        "forbidden_live_execution_created": False,
        "forbidden_live_order_authority_created": False,
        "forbidden_connector_binding_created": False,
        "forbidden_source_truth_acceptance_created": False,
        "forbidden_profit_evidence_created": False,
        "forbidden_quantum_backend_execution_created": False,
        "forbidden_quantum_advantage_claim_created": False,
    }


def validate_record_authority(record: dict[str, Any]) -> AuthorityValidationResult:
    failures: list[str] = []
    for key in ZERO_AUTHORITY_KEYS:
        if int(record.get(key, 0) or 0) != 0:
            failures.append(f"nonzero authority count {key}")
    forbidden_true_fields = (
        "live_execution_created",
        "live_order_authority_created",
        "source_truth_accepted",
        "profit_evidence_created",
        "quantum_backend_executed",
        "quantum_advantage_claimed",
    )
    for field in forbidden_true_fields:
        if record.get(field) is True:
            failures.append(f"forbidden authority flag true: {field}")
    return AuthorityValidationResult(tuple(failures))
