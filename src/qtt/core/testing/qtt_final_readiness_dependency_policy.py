from __future__ import annotations

from enum import Enum


class QttFinalReadinessDependencyPolicyState(str, Enum):
    FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY = (
        "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY"
    )
    FINAL_READINESS_DEPENDENCY_POLICY_OWNER_SHA_RECONSIDERATION_REQUESTED = (
        "FINAL_READINESS_DEPENDENCY_POLICY_OWNER_SHA_RECONSIDERATION_REQUESTED"
    )
    FINAL_READINESS_DEPENDENCY_POLICY_SHA_REACTIVATED_AFTER_OWNER_APPROVAL = (
        "FINAL_READINESS_DEPENDENCY_POLICY_SHA_REACTIVATED_AFTER_OWNER_APPROVAL"
    )


QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATES = tuple(
    state.value for state in QttFinalReadinessDependencyPolicyState
)

CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE = (
    QttFinalReadinessDependencyPolicyState.FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY.value
)
EXPECTED_CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE = (
    QttFinalReadinessDependencyPolicyState.FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY.value
)

ACTIVE_NON_SHA_FINAL_READINESS_DEPENDENCIES = (
    "OWNER_DAY1_LAUNCH_APPROVAL",
    "ACCEPTED_SOURCE_EVIDENCE_FOR_TARGET_FIELDS",
    "CONNECTOR_SEMANTIC_BINDINGS_FOR_TARGET_FIELDS",
    "FRESH_SOURCE_REVALIDATION_STATE",
    "RUNTIME_CASH_COMPONENT_FIELD_MAP",
    "RUNTIME_CASH_RECEIPTS_WHEN_REQUIRED",
    "REPLAY_AND_PAPER_RESULTS_WHEN_REQUIRED",
    "DUAL_RESULT_REVIEW_WHEN_REQUIRED",
    "OWNER_LIVE_PROMOTION_REVIEW_WHEN_REQUIRED",
    "RISK_LIMIT_AND_EXPOSURE_GATES",
    "LIVE_PREFLIGHT_MATRIX",
    "ORDER_ROUTER_SAFETY_GATES",
    "KILL_SWITCH_AND_ROLLBACK_GATES",
    "EXECUTION_RECEIPT_BOUNDARY",
    "QUANTUM_BACKEND_AUTHORITY_GATE",
    "QUANTUM_ADVANTAGE_NO_CLAIM_GATE",
    "PROFIT_NO_CLAIM_GATE",
    "LATENCY_AND_EXECUTION_EVIDENCE_NO_FABRICATION_GATE",
)

EXCLUDED_NON_PARTICIPATING_FINAL_READINESS_SUBSYSTEMS = (
    "SHA_DORMANCY_SYSTEM",
)

_SHA_DEPENDENCY_TOKENS = (
    "SHA",
    "SHA_FREEZE",
    "SHA_FILE",
    "SHA_DIGEST",
    "SHA_ABSENCE",
    "SHA_PRESENCE",
    "SHA_REACTIVATION",
)


def get_qtt_final_readiness_dependency_policy_state() -> str:
    return CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE


def is_sha_required_for_final_readiness() -> bool:
    return False


def is_sha_dormancy_a_final_readiness_blocker() -> bool:
    return False


def get_active_non_sha_final_readiness_dependencies() -> tuple[str, ...]:
    return ACTIVE_NON_SHA_FINAL_READINESS_DEPENDENCIES


def get_excluded_non_participating_final_readiness_subsystems() -> tuple[str, ...]:
    return EXCLUDED_NON_PARTICIPATING_FINAL_READINESS_SUBSYSTEMS


def assert_final_readiness_policy_active_non_sha_gates_only() -> None:
    if (
        get_qtt_final_readiness_dependency_policy_state()
        != EXPECTED_CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE
    ):
        raise AssertionError("final-readiness dependency policy state is not current")
    for dependency in get_active_non_sha_final_readiness_dependencies():
        for token in _SHA_DEPENDENCY_TOKENS:
            if token in dependency:
                raise AssertionError(
                    f"active final-readiness dependency must not include SHA: {dependency}"
                )


def assert_sha_not_required_for_final_readiness() -> None:
    if is_sha_required_for_final_readiness():
        raise AssertionError("SHA must not be required for final readiness")


def assert_sha_dormancy_not_final_readiness_blocker() -> None:
    if is_sha_dormancy_a_final_readiness_blocker():
        raise AssertionError("SHA dormancy must not be a final-readiness blocker")


def assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass() -> None:
    assert_final_readiness_policy_active_non_sha_gates_only()
    assert_sha_not_required_for_final_readiness()
    assert_sha_dormancy_not_final_readiness_blocker()


def assert_current_pr_does_not_create_final_readiness() -> None:
    assert_final_readiness_policy_active_non_sha_gates_only()
