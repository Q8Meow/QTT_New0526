"""Central PR165-C authority boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from .central_vocab import AUTHORITY_BOUNDARY_REF, AUTHORITY_CLASS

POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr165_c_replay_paper_memory_consumer_integration.authority_policy"
)

FILES_INTENTIONALLY_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "protected AtomicRows bundle artifacts",
    "AtomicRows bundle integrity authority artifacts",
    "QTT integrity freeze/checksum/global-digest authority artifacts",
    "connector/private-state/runtime-cash/order/live artifacts",
    "quantum backend/runtime execution artifacts",
    "LLM hot-path/source-acceptance/order-release/result-rewrite artifacts",
    "profit evidence / profit guarantee artifacts",
)

FORBIDDEN_ACTION_LITERALS = (
    "LIVE_EXECUTION_ALLOWED",
    "ORDER_READY",
    "PROFIT_EVIDENCE_CREATED",
    "CONNECTOR_BOUND",
    "PRIVATE_STATE_USED",
    "QTT_SHA_CREATED",
    "ATOMICROWS_SHA_CREATED",
    "QUANTUM_BACKEND_EXECUTED",
    "QUANTUM_ADVANTAGE_CLAIMED",
    "LLM_ORDER_RELEASE",
)

FORBIDDEN_COMPUTABILITY_LITERALS = (
    "UNKNOWN",
    "PLACEHOLDER",
    "METADATA_ONLY",
    "BLOCKED_WITHOUT_ROUTE",
    "FUTURE_CONSUMER_ONLY",
)

SCATTERED_LITERAL_EXCLUDED_FILES = frozenset(
    {
        "authority_policy.py",
        "central_vocab.py",
        "agent_duty_vocab.py",
        "memory_consumer_action_vocab.py",
        "retest_ingestion_vocab.py",
        "agent_conflict_vocab.py",
        "computability_action_vocab.py",
        "materialization_candidate_vocab.py",
    }
)


@dataclass(frozen=True)
class AuthorityValidation:
    ok: bool
    failures: tuple[str, ...]


def authority_boundary_record() -> dict[str, object]:
    return {
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "authority_class": AUTHORITY_CLASS,
        "policy_module_ref": POLICY_MODULE_REF,
        "replay_paper_consumer_actions_allowed": True,
        "retest_queue_creation_allowed": True,
        "materialization_task_creation_allowed": True,
        "repair_route_creation_allowed": True,
        "dashboard_governance_commander_handoffs_allowed": True,
        "live_order_authority_allowed": False,
        "live_promotion_claim_allowed": False,
        "order_ready_claim_allowed": False,
        "profit_evidence_claim_allowed": False,
        "connector_runtime_binding_allowed": False,
        "private_state_fetch_allowed": False,
        "runtime_cash_receipt_allowed": False,
        "quantum_backend_execution_allowed": False,
        "quantum_advantage_claim_allowed": False,
        "llm_hot_path_or_order_release_allowed": False,
        "protected_integrity_authority_allowed": False,
    }


def authority_zero_counts() -> dict[str, int]:
    return {
        "live_order_authority_count": 0,
        "live_promotion_claim_count": 0,
        "order_ready_claim_count": 0,
        "profit_evidence_claim_count": 0,
        "connector_runtime_binding_count": 0,
        "private_state_fetch_count": 0,
        "runtime_cash_receipt_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "llm_hot_path_or_order_release_count": 0,
        "protected_integrity_authority_count": 0,
    }


def authority_absence_confirmation() -> dict[str, bool]:
    return {key.replace("_count", "_absent"): value == 0 for key, value in authority_zero_counts().items()}


def validate_record_authority(record: dict[str, object]) -> AuthorityValidation:
    failures: list[str] = []
    for key in authority_zero_counts():
        if int(record.get(key, 0) or 0) != 0:
            failures.append(f"nonzero authority count: {key}")
    boundary = record.get("authority_boundary_ref") or record.get("authority_boundary")
    if not boundary:
        failures.append("missing authority boundary")
    return AuthorityValidation(not failures, tuple(failures))
