from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Sequence


class QttActiveNonShaDay1GateRegistryState(str, Enum):
    ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE = (
        "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE"
    )
    ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_PARTIAL_PROGRESS_ONE_GATE_FLIPPED = (
        "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_PARTIAL_PROGRESS_ONE_GATE_FLIPPED"
    )
    ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ALL_REQUIRED_NON_SHA_GATES_SATISFIED_PENDING_OWNER_FINAL_APPROVAL = (
        "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ALL_REQUIRED_NON_SHA_GATES_SATISFIED_PENDING_OWNER_FINAL_APPROVAL"
    )
    ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_FINAL_READINESS_AUTHORIZED_BY_SEPARATE_OWNER_PR = (
        "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_FINAL_READINESS_AUTHORIZED_BY_SEPARATE_OWNER_PR"
    )


QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATES = tuple(
    state.value for state in QttActiveNonShaDay1GateRegistryState
)

CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE = (
    QttActiveNonShaDay1GateRegistryState.ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE.value
)
EXPECTED_CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE = (
    QttActiveNonShaDay1GateRegistryState.ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE.value
)

QTT_ACTIVE_NON_SHA_DAY1_GATE_CLASSES = (
    "OWNER_DECISION_GATE",
    "REQUIRED_POSITIVE_EVIDENCE_GATE",
    "REQUIRED_POSITIVE_RECEIPT_GATE",
    "REQUIRED_STATIC_CONTRACT_GATE",
    "REQUIRED_RUNTIME_RECEIPT_GATE",
    "REQUIRED_REPLAY_PAPER_RESULT_GATE",
    "REQUIRED_REVIEW_GATE",
    "REQUIRED_PREFLIGHT_GATE",
    "REQUIRED_SAFETY_GUARD_GATE",
    "REQUIRED_NO_CLAIM_GUARD_GATE",
    "CONDITIONAL_AUTHORITY_GUARD_GATE",
)

QTT_ACTIVE_NON_SHA_DAY1_GATE_STATES = (
    "BLOCKED_AWAITING_OWNER_APPROVAL",
    "BLOCKED_AWAITING_ACCEPTED_SOURCE_EVIDENCE",
    "BLOCKED_AWAITING_CONNECTOR_SEMANTIC_BINDING",
    "BLOCKED_AWAITING_FRESH_SOURCE_REVALIDATION",
    "BLOCKED_AWAITING_LAUNCH_SCOPED_RUNTIME_CASH_COMPONENT_FIELD_MAP",
    "BLOCKED_AWAITING_RUNTIME_CASH_RECEIPT",
    "BLOCKED_AWAITING_REPLAY_AND_PAPER_RESULTS",
    "BLOCKED_AWAITING_DUAL_RESULT_REVIEW",
    "BLOCKED_AWAITING_OWNER_LIVE_PROMOTION_REVIEW",
    "BLOCKED_AWAITING_RISK_LIMIT_AND_EXPOSURE_GATES",
    "BLOCKED_AWAITING_LIVE_PREFLIGHT_MATRIX",
    "BLOCKED_AWAITING_ORDER_ROUTER_SAFETY_GATES",
    "BLOCKED_AWAITING_KILL_SWITCH_AND_ROLLBACK_GATES",
    "GUARD_ACTIVE_NO_EXECUTION_RECEIPT_REQUIRED_THIS_PR",
    "GUARD_ACTIVE_NO_UNAUTHORIZED_QUANTUM_BACKEND_EXECUTION",
    "GUARD_ACTIVE_NO_QUANTUM_ADVANTAGE_CLAIM",
    "GUARD_ACTIVE_NO_PROFIT_CLAIM",
    "GUARD_ACTIVE_NO_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM",
    "SATISFIED_BY_CANONICAL_RECEIPT",
    "NON_PARTICIPATING_EXCLUDED",
)

QTT_ACTIVE_NON_SHA_DAY1_GATE_EVALUATION_MODES = (
    "POSITIVE_EVIDENCE_BLOCKER",
    "POSITIVE_RECEIPT_BLOCKER",
    "STATIC_CONTRACT_BLOCKER",
    "RUNTIME_RECEIPT_BLOCKER",
    "REPLAY_PAPER_RESULT_BLOCKER",
    "REVIEW_BLOCKER",
    "PREFLIGHT_BLOCKER",
    "SAFETY_PRECONDITION_BLOCKER",
    "ACTIVE_GUARD_UNVIOLATED",
    "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES",
    "EXCLUDED_NON_PARTICIPATING",
)

QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS = (
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

EXCLUDED_NON_PARTICIPATING_SUBSYSTEMS = ("SHA_DORMANCY_SYSTEM",)

_UNIVERSAL_RECORD_FLAGS: dict[str, bool] = {
    "current_pr_may_flip": False,
    "future_flip_pr_must_be_separate": True,
    "future_materialization_must_be_separate_from_unrelated_gate_flips": True,
    "future_materialization_may_enable_only_one_artifact_or_capability_at_a_time": True,
    "creates_authority_in_this_pr": False,
    "creates_evidence_in_this_pr": False,
    "executes_runtime_in_this_pr": False,
}


def _gate_record(
    *,
    gate_id: str,
    gate_class: str,
    current_state: str,
    evaluation_mode: str,
    currently_blocks_final_readiness: bool,
    future_required_artifact_or_receipt: str,
    notes: str,
    future_flip_pr_family: str,
    guard_active_and_unviolated: bool = False,
    conditional_on_future_launch_scope: bool = False,
    conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend: bool = False,
    true_quantum_backend_required_for_non_backend_day1_launch_scope: bool = False,
    blocks_unauthorized_backend_simulator_provider_execution: bool = False,
    blocks_static_quantum_metadata_or_planning: bool = False,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_class": gate_class,
        "current_state": current_state,
        "evaluation_mode": evaluation_mode,
        "currently_blocks_final_readiness": currently_blocks_final_readiness,
        **_UNIVERSAL_RECORD_FLAGS,
        "future_required_artifact_or_receipt": future_required_artifact_or_receipt,
        "future_flip_pr_family": future_flip_pr_family,
        "guard_active_and_unviolated": guard_active_and_unviolated,
        "conditional_on_future_launch_scope": conditional_on_future_launch_scope,
        "conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend": (
            conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend
        ),
        "true_quantum_backend_required_for_non_backend_day1_launch_scope": (
            true_quantum_backend_required_for_non_backend_day1_launch_scope
        ),
        "blocks_unauthorized_backend_simulator_provider_execution": (
            blocks_unauthorized_backend_simulator_provider_execution
        ),
        "blocks_static_quantum_metadata_or_planning": (
            blocks_static_quantum_metadata_or_planning
        ),
        "notes": notes,
    }


QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS: tuple[dict[str, Any], ...] = (
    _gate_record(
        gate_id="OWNER_DAY1_LAUNCH_APPROVAL",
        gate_class="OWNER_DECISION_GATE",
        current_state="BLOCKED_AWAITING_OWNER_APPROVAL",
        evaluation_mode="POSITIVE_RECEIPT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="canonical owner Day-1 launch approval receipt",
        future_flip_pr_family="OWNER_FINAL_APPROVAL_PR_FAMILY",
        notes="Owner approval is absent; this PR only records the blocked state.",
    ),
    _gate_record(
        gate_id="ACCEPTED_SOURCE_EVIDENCE_FOR_TARGET_FIELDS",
        gate_class="REQUIRED_POSITIVE_EVIDENCE_GATE",
        current_state="BLOCKED_AWAITING_ACCEPTED_SOURCE_EVIDENCE",
        evaluation_mode="POSITIVE_EVIDENCE_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="accepted source-evidence packet(s) for exact target fields",
        future_flip_pr_family="SOURCE_EVIDENCE_ACCEPTANCE_PR_FAMILY",
        notes="Accepted source evidence is absent and is not fabricated by this PR.",
    ),
    _gate_record(
        gate_id="CONNECTOR_SEMANTIC_BINDINGS_FOR_TARGET_FIELDS",
        gate_class="REQUIRED_POSITIVE_EVIDENCE_GATE",
        current_state="BLOCKED_AWAITING_CONNECTOR_SEMANTIC_BINDING",
        evaluation_mode="POSITIVE_EVIDENCE_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="connector semantic binding ledger records consuming accepted target-field packets",
        future_flip_pr_family="CONNECTOR_SEMANTIC_BINDING_PR_FAMILY",
        notes="Connector semantic bindings are absent and are not created by this PR.",
    ),
    _gate_record(
        gate_id="FRESH_SOURCE_REVALIDATION_STATE",
        gate_class="REQUIRED_POSITIVE_EVIDENCE_GATE",
        current_state="BLOCKED_AWAITING_FRESH_SOURCE_REVALIDATION",
        evaluation_mode="POSITIVE_EVIDENCE_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="fresh source revalidation state for applicable target fields",
        future_flip_pr_family="SOURCE_REVALIDATION_PR_FAMILY",
        notes="Fresh source revalidation is absent and is not created by this PR.",
    ),
    _gate_record(
        gate_id="RUNTIME_CASH_COMPONENT_FIELD_MAP",
        gate_class="REQUIRED_STATIC_CONTRACT_GATE",
        current_state="BLOCKED_AWAITING_LAUNCH_SCOPED_RUNTIME_CASH_COMPONENT_FIELD_MAP",
        evaluation_mode="STATIC_CONTRACT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="launch-scoped runtime cash component field map contract/packet",
        future_flip_pr_family="RUNTIME_CASH_CONTRACT_PR_FAMILY",
        notes="This does not deny existing schema/static scaffolds; launch-scoped satisfaction is not granted by this PR.",
    ),
    _gate_record(
        gate_id="RUNTIME_CASH_RECEIPTS_WHEN_REQUIRED",
        gate_class="REQUIRED_RUNTIME_RECEIPT_GATE",
        current_state="BLOCKED_AWAITING_RUNTIME_CASH_RECEIPT",
        evaluation_mode="RUNTIME_RECEIPT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="runtime cash/account/balance receipts when required by launch scope",
        future_flip_pr_family="RUNTIME_CASH_RECEIPT_PR_FAMILY",
        notes="Runtime cash receipts are absent and private-state reads are not executed by this PR.",
    ),
    _gate_record(
        gate_id="REPLAY_AND_PAPER_RESULTS_WHEN_REQUIRED",
        gate_class="REQUIRED_REPLAY_PAPER_RESULT_GATE",
        current_state="BLOCKED_AWAITING_REPLAY_AND_PAPER_RESULTS",
        evaluation_mode="REPLAY_PAPER_RESULT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="replay and paper results from authorized execution lanes",
        future_flip_pr_family="REPLAY_PAPER_RESULT_PR_FAMILY",
        notes="Replay and paper execution remain blocked and unexecuted by this PR.",
    ),
    _gate_record(
        gate_id="DUAL_RESULT_REVIEW_WHEN_REQUIRED",
        gate_class="REQUIRED_REVIEW_GATE",
        current_state="BLOCKED_AWAITING_DUAL_RESULT_REVIEW",
        evaluation_mode="REVIEW_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="dual-result review packet/report",
        future_flip_pr_family="DUAL_RESULT_REVIEW_PR_FAMILY",
        notes="Dual-result review is absent and is not created by this PR.",
    ),
    _gate_record(
        gate_id="OWNER_LIVE_PROMOTION_REVIEW_WHEN_REQUIRED",
        gate_class="OWNER_DECISION_GATE",
        current_state="BLOCKED_AWAITING_OWNER_LIVE_PROMOTION_REVIEW",
        evaluation_mode="POSITIVE_RECEIPT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="owner live-promotion review receipt",
        future_flip_pr_family="OWNER_LIVE_PROMOTION_REVIEW_PR_FAMILY",
        notes="Owner live-promotion review receipt is absent and is not created by this PR.",
    ),
    _gate_record(
        gate_id="RISK_LIMIT_AND_EXPOSURE_GATES",
        gate_class="REQUIRED_PREFLIGHT_GATE",
        current_state="BLOCKED_AWAITING_RISK_LIMIT_AND_EXPOSURE_GATES",
        evaluation_mode="PREFLIGHT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="risk limit and exposure gate report",
        future_flip_pr_family="RISK_PREFLIGHT_PR_FAMILY",
        notes="Risk limit and exposure gates remain blocked for Day-1 final readiness.",
    ),
    _gate_record(
        gate_id="LIVE_PREFLIGHT_MATRIX",
        gate_class="REQUIRED_PREFLIGHT_GATE",
        current_state="BLOCKED_AWAITING_LIVE_PREFLIGHT_MATRIX",
        evaluation_mode="PREFLIGHT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="live preflight matrix",
        future_flip_pr_family="LIVE_PREFLIGHT_PR_FAMILY",
        notes="The live preflight matrix is absent and no live authority is created.",
    ),
    _gate_record(
        gate_id="ORDER_ROUTER_SAFETY_GATES",
        gate_class="REQUIRED_PREFLIGHT_GATE",
        current_state="BLOCKED_AWAITING_ORDER_ROUTER_SAFETY_GATES",
        evaluation_mode="PREFLIGHT_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="order-router safety gate report",
        future_flip_pr_family="ORDER_ROUTER_SAFETY_PR_FAMILY",
        notes="Order-router safety gates remain blocked and no order flow is enabled.",
    ),
    _gate_record(
        gate_id="KILL_SWITCH_AND_ROLLBACK_GATES",
        gate_class="REQUIRED_SAFETY_GUARD_GATE",
        current_state="BLOCKED_AWAITING_KILL_SWITCH_AND_ROLLBACK_GATES",
        evaluation_mode="SAFETY_PRECONDITION_BLOCKER",
        currently_blocks_final_readiness=True,
        future_required_artifact_or_receipt="kill-switch and rollback gate contract/report",
        future_flip_pr_family="SAFETY_ROLLBACK_PR_FAMILY",
        notes="Kill-switch and rollback satisfaction is absent and is not created by this PR.",
    ),
    _gate_record(
        gate_id="EXECUTION_RECEIPT_BOUNDARY",
        gate_class="REQUIRED_SAFETY_GUARD_GATE",
        current_state="GUARD_ACTIVE_NO_EXECUTION_RECEIPT_REQUIRED_THIS_PR",
        evaluation_mode="ACTIVE_GUARD_UNVIOLATED",
        currently_blocks_final_readiness=False,
        future_required_artifact_or_receipt="execution receipt boundary contract before live execution",
        future_flip_pr_family="EXECUTION_RECEIPT_BOUNDARY_PR_FAMILY",
        guard_active_and_unviolated=True,
        notes="This PR must not create any execution receipt.",
    ),
    _gate_record(
        gate_id="QUANTUM_BACKEND_AUTHORITY_GATE",
        gate_class="CONDITIONAL_AUTHORITY_GUARD_GATE",
        current_state="GUARD_ACTIVE_NO_UNAUTHORIZED_QUANTUM_BACKEND_EXECUTION",
        evaluation_mode="CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES",
        currently_blocks_final_readiness=False,
        future_required_artifact_or_receipt="owner-approved quantum backend authority receipt plus provider/source/backend evidence if selected launch stack requires true quantum execution",
        future_flip_pr_family="QUANTUM_BACKEND_AUTHORITY_PR_FAMILY",
        guard_active_and_unviolated=True,
        conditional_on_future_launch_scope=True,
        conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend=True,
        true_quantum_backend_required_for_non_backend_day1_launch_scope=False,
        blocks_unauthorized_backend_simulator_provider_execution=True,
        blocks_static_quantum_metadata_or_planning=False,
        notes="This gate blocks unauthorized true quantum backend/simulator/provider execution; it does not require true quantum backend authority for non-backend Day-1 launch scope.",
    ),
    _gate_record(
        gate_id="QUANTUM_ADVANTAGE_NO_CLAIM_GATE",
        gate_class="REQUIRED_NO_CLAIM_GUARD_GATE",
        current_state="GUARD_ACTIVE_NO_QUANTUM_ADVANTAGE_CLAIM",
        evaluation_mode="ACTIVE_GUARD_UNVIOLATED",
        currently_blocks_final_readiness=False,
        future_required_artifact_or_receipt="separate evidence before any future quantum-advantage claim",
        future_flip_pr_family="QUANTUM_ADVANTAGE_EVIDENCE_PR_FAMILY",
        guard_active_and_unviolated=True,
        notes="No quantum advantage evidence or claim is created by this PR.",
    ),
    _gate_record(
        gate_id="PROFIT_NO_CLAIM_GATE",
        gate_class="REQUIRED_NO_CLAIM_GUARD_GATE",
        current_state="GUARD_ACTIVE_NO_PROFIT_CLAIM",
        evaluation_mode="ACTIVE_GUARD_UNVIOLATED",
        currently_blocks_final_readiness=False,
        future_required_artifact_or_receipt="separate evidence before any future profit claim",
        future_flip_pr_family="PROFIT_EVIDENCE_PR_FAMILY",
        guard_active_and_unviolated=True,
        notes="No profit evidence or claim is created by this PR.",
    ),
    _gate_record(
        gate_id="LATENCY_AND_EXECUTION_EVIDENCE_NO_FABRICATION_GATE",
        gate_class="REQUIRED_NO_CLAIM_GUARD_GATE",
        current_state="GUARD_ACTIVE_NO_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM",
        evaluation_mode="ACTIVE_GUARD_UNVIOLATED",
        currently_blocks_final_readiness=False,
        future_required_artifact_or_receipt="separate evidence before latency or execution superiority claim",
        future_flip_pr_family="LATENCY_EXECUTION_EVIDENCE_PR_FAMILY",
        guard_active_and_unviolated=True,
        notes="No latency or execution superiority evidence or claim is created by this PR.",
    ),
)

CURRENT_PR_FLIPS_ANY_GATE = False
CURRENT_PR_MARKS_ANY_GATE_SATISFIED = False
CURRENT_PR_CREATES_FINAL_READINESS = False
CURRENT_PR_CREATES_DAY1_LAUNCH_AUTHORITY = False
CURRENT_PR_CREATES_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_RUNTIME_CASH_BACKEND_PROFIT_AUTHORITY = False
CURRENT_PR_CREATES_REPLAY_PAPER_OPTIMIZER_NEURAL_QUANTUM_BACKEND_EXECUTION = False
CURRENT_PR_CLAIMS_PROFIT_LATENCY_EXECUTION_QUANTUM_ADVANTAGE_EVIDENCE = False
CURRENT_PR_ACCEPTS_SOURCE_FACTS = False
CURRENT_PR_BINDS_CONNECTOR_SEMANTICS = False
CURRENT_PR_CREATES_RUNTIME_CASH_RECEIPTS = False
CURRENT_PR_CREATES_ORDER_FILL_ACCOUNT_RECEIPTS = False
CURRENT_PR_EXECUTES_QUBO_QAOA_VQE_ISING_ANNEALING_BACKEND_SIMULATOR = False

_RECORDS_BY_ID = {
    str(record["gate_id"]): record for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
}

_BLOCKER_EVALUATION_MODES = (
    "POSITIVE_EVIDENCE_BLOCKER",
    "POSITIVE_RECEIPT_BLOCKER",
    "STATIC_CONTRACT_BLOCKER",
    "RUNTIME_RECEIPT_BLOCKER",
    "REPLAY_PAPER_RESULT_BLOCKER",
    "REVIEW_BLOCKER",
    "PREFLIGHT_BLOCKER",
    "SAFETY_PRECONDITION_BLOCKER",
)


def get_qtt_active_non_sha_day1_gate_registry_state() -> str:
    return CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE


def get_active_non_sha_day1_gate_ids() -> tuple[str, ...]:
    return QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS


def get_active_non_sha_day1_gate_records() -> tuple[Mapping[str, Any], ...]:
    return QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS


def get_gate_record(gate_id: str) -> Mapping[str, Any]:
    try:
        return _RECORDS_BY_ID[gate_id]
    except KeyError as exc:
        raise KeyError(f"unknown active non-SHA Day-1 gate ID: {gate_id}") from exc


def get_currently_blocking_positive_gate_ids() -> tuple[str, ...]:
    return tuple(
        str(record["gate_id"])
        for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
        if record["evaluation_mode"] in _BLOCKER_EVALUATION_MODES
        and record["currently_blocks_final_readiness"] is True
    )


def get_guard_active_gate_ids() -> tuple[str, ...]:
    return tuple(
        str(record["gate_id"])
        for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
        if record["guard_active_and_unviolated"] is True
    )


def get_no_claim_guard_gate_ids() -> tuple[str, ...]:
    return tuple(
        str(record["gate_id"])
        for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
        if record["gate_class"] == "REQUIRED_NO_CLAIM_GUARD_GATE"
    )


def get_conditional_authority_guard_gate_ids() -> tuple[str, ...]:
    return tuple(
        str(record["gate_id"])
        for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
        if record["gate_class"] == "CONDITIONAL_AUTHORITY_GUARD_GATE"
    )


def get_excluded_non_participating_subsystems() -> tuple[str, ...]:
    return EXCLUDED_NON_PARTICIPATING_SUBSYSTEMS


def is_sha_dormancy_system_excluded() -> bool:
    return (
        "SHA_DORMANCY_SYSTEM" in EXCLUDED_NON_PARTICIPATING_SUBSYSTEMS
        and "SHA_DORMANCY_SYSTEM" not in QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS
    )


def is_gate_currently_blocking(gate_id: str) -> bool:
    return bool(get_gate_record(gate_id)["currently_blocks_final_readiness"])


def is_gate_guard_active(gate_id: str) -> bool:
    return bool(get_gate_record(gate_id)["guard_active_and_unviolated"])


def is_quantum_backend_gate_conditional() -> bool:
    record = get_gate_record("QUANTUM_BACKEND_AUTHORITY_GATE")
    return (
        record["evaluation_mode"]
        == "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES"
        and record[
            "conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend"
        ]
        is True
        and record["true_quantum_backend_required_for_non_backend_day1_launch_scope"]
        is False
    )


def assert_registry_current() -> None:
    if (
        get_qtt_active_non_sha_day1_gate_registry_state()
        != EXPECTED_CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE
    ):
        raise AssertionError("active non-SHA Day-1 gate registry state is not current")
    if tuple(_RECORDS_BY_ID) != QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS:
        raise AssertionError("active gate records must match active gate IDs exactly")
    if len(_RECORDS_BY_ID) != len(QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS):
        raise AssertionError("active gate IDs must be unique")
    assert_sha_dormancy_system_excluded()
    assert_no_gate_flipped_by_this_pr()
    assert_no_gate_satisfied_by_this_pr()
    assert_all_positive_evidence_gates_remain_blocked()
    assert_guard_gates_active_and_unviolated()


def assert_no_gate_flipped_by_this_pr() -> None:
    if CURRENT_PR_FLIPS_ANY_GATE:
        raise AssertionError("current PR must not flip any active non-SHA gate")
    for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS:
        if record["current_pr_may_flip"] is not False:
            raise AssertionError(f"gate may not be flipped by this PR: {record['gate_id']}")


def assert_no_gate_satisfied_by_this_pr() -> None:
    if CURRENT_PR_MARKS_ANY_GATE_SATISFIED:
        raise AssertionError("current PR must not mark any gate satisfied")
    for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS:
        if record["current_state"] == "SATISFIED_BY_CANONICAL_RECEIPT":
            raise AssertionError(f"gate must not be satisfied by this PR: {record['gate_id']}")


def assert_all_positive_evidence_gates_remain_blocked() -> None:
    for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS:
        if record["evaluation_mode"] not in _BLOCKER_EVALUATION_MODES:
            continue
        if record["currently_blocks_final_readiness"] is not True:
            raise AssertionError(f"blocking gate must still block: {record['gate_id']}")
        if not str(record["current_state"]).startswith("BLOCKED_"):
            raise AssertionError(f"blocking gate must remain blocked: {record['gate_id']}")


def assert_guard_gates_active_and_unviolated() -> None:
    for record in QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS:
        evaluation_mode = record["evaluation_mode"]
        if evaluation_mode not in {
            "ACTIVE_GUARD_UNVIOLATED",
            "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES",
        }:
            continue
        if record["guard_active_and_unviolated"] is not True:
            raise AssertionError(f"guard gate must be active and unviolated: {record['gate_id']}")
        if not str(record["current_state"]).startswith("GUARD_ACTIVE_"):
            raise AssertionError(f"guard gate must remain guard-active: {record['gate_id']}")
        if record["currently_blocks_final_readiness"] is not False:
            raise AssertionError(f"active guard must not be a current positive blocker: {record['gate_id']}")


def assert_sha_dormancy_system_excluded() -> None:
    if not is_sha_dormancy_system_excluded():
        raise AssertionError("SHA_DORMANCY_SYSTEM must be excluded from active gate IDs")


def assert_gate_ids_match_expected_active_non_sha_dependencies(
    expected_gate_ids: Sequence[str],
) -> None:
    if tuple(expected_gate_ids) != QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS:
        raise AssertionError("active non-SHA gate IDs must match final-readiness dependencies")


def assert_quantum_backend_gate_does_not_require_backend_for_non_backend_day1() -> None:
    if not is_quantum_backend_gate_conditional():
        raise AssertionError(
            "QUANTUM_BACKEND_AUTHORITY_GATE must be conditional and nonblocking for non-backend Day-1 scope"
        )
    record = get_gate_record("QUANTUM_BACKEND_AUTHORITY_GATE")
    if record["blocks_static_quantum_metadata_or_planning"] is not False:
        raise AssertionError("quantum backend guard must not block static quantum metadata")


def assert_current_pr_creates_no_final_readiness() -> None:
    if CURRENT_PR_CREATES_FINAL_READINESS:
        raise AssertionError("current PR must not create final readiness")


def assert_current_pr_creates_no_runtime_live_profit_or_backend_authority() -> None:
    if (
        CURRENT_PR_CREATES_DAY1_LAUNCH_AUTHORITY
        or CURRENT_PR_CREATES_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_RUNTIME_CASH_BACKEND_PROFIT_AUTHORITY
    ):
        raise AssertionError(
            "current PR must not create Day-1 launch or runtime/live/order/source/connector/runtime-cash/backend/profit authority"
        )


def assert_current_pr_creates_no_replay_paper_optimizer_neural_quantum_execution() -> None:
    if (
        CURRENT_PR_CREATES_REPLAY_PAPER_OPTIMIZER_NEURAL_QUANTUM_BACKEND_EXECUTION
        or CURRENT_PR_EXECUTES_QUBO_QAOA_VQE_ISING_ANNEALING_BACKEND_SIMULATOR
    ):
        raise AssertionError(
            "current PR must not execute replay/paper/optimizer/neural/quantum/backend/simulator flows"
        )


def assert_current_pr_creates_no_profit_latency_execution_quantum_advantage_evidence() -> None:
    if CURRENT_PR_CLAIMS_PROFIT_LATENCY_EXECUTION_QUANTUM_ADVANTAGE_EVIDENCE:
        raise AssertionError(
            "current PR must not create profit/latency/execution/quantum-advantage evidence"
        )

