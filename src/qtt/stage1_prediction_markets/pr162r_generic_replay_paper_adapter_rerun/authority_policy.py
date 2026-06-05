"""Central authority boundary policy for PR162R.

All PR162R builders and validators consume this module so no-result,
no-live, no-profit, no-source-acceptance, no-connector, no-private-state,
no-quantum-backend, and no-checksum boundaries are not redefined across
reports or tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PR_ID = "PR162R"
EXPECTED_BRANCH = "pr162r-generic-replay-paper-adapter-rerun"
AUTHORITY_CLASS = (
    "PR162R_GENERIC_REPLAY_PAPER_ADAPTER_INPUT_RERUN_NO_EXECUTION_NO_LIVE_AUTHORITY"
)
POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr162r_generic_replay_paper_adapter_rerun.authority_policy"
)

TRUTH_STATUSES = (
    "OWNER_PROVIDED_CANDIDATE",
    "OFFICIAL_SOURCE_CANDIDATE",
    "NON_OFFICIAL_SOURCE_CANDIDATE",
    "RESEARCH_SOURCE_CANDIDATE",
    "SOCIAL_SOURCE_CANDIDATE",
    "INSTITUTIONAL_SOURCE_CANDIDATE",
    "WEB_SOURCE_CANDIDATE",
    "REPO_LOCAL_ARTIFACT_CANDIDATE",
    "TEST_VECTOR_BACKED_CANDIDATE",
    "FORMULATION_EXECUTABLE_CANDIDATE",
    "REPLAY_PAPER_INPUT_READY_CANDIDATE",
    "FILL_REQUIRED_WITH_EXACT_REASON",
    "OWNER_REVIEW_REQUIRED_WITH_REASON",
    "NOT_STAGE1_RELEVANT_WITH_REASON",
)

SOURCE_CLASSES = (
    "OFFICIAL_DOC_CANDIDATE",
    "NON_OFFICIAL_WEB_CANDIDATE",
    "RESEARCH_PAPER_CANDIDATE",
    "SOCIAL_SIGNAL_CANDIDATE",
    "INSTITUTIONAL_NOTE_CANDIDATE",
    "OWNER_PROVIDED_CANDIDATE",
    "REPO_LOCAL_ARTIFACT_CANDIDATE",
    "CLASSICAL_LIBRARY_DOC_CANDIDATE",
    "QUANTUM_PROVIDER_DOC_CANDIDATE",
)

COMPUTABILITY_ROUTES = (
    "FORMULA_EXECUTABLE",
    "ALGORITHM_CALLABLE",
    "QUANTUM_SHAPE_BUILDABLE",
    "CLASSICAL_COMPARATOR_EXECUTABLE",
    "PARAMETER_VALUE_COMPUTABLE_FROM_INPUTS",
    "DATA_BINDING_FILL_REQUIRED_WITH_EXACT_ACTION",
    "SOURCE_VALUE_FILL_REQUIRED_WITH_EXACT_ACTION",
    "OWNER_REVIEW_REQUIRED_WITH_EXACT_REASON",
    "NOT_STAGE1_RELEVANT_WITH_EXACT_REASON",
)

REPLAY_STATUSES = (
    "REPLAY_INPUT_READY",
    "REPLAY_INPUT_PARTIAL",
    "REPLAY_INPUT_FILL_REQUIRED",
    "REPLAY_NOT_STAGE1_RELEVANT_WITH_REASON",
    "REPLAY_OWNER_REVIEW_REQUIRED",
)
PAPER_STATUSES = (
    "PAPER_INPUT_READY",
    "PAPER_INPUT_PARTIAL",
    "PAPER_INPUT_FILL_REQUIRED",
    "PAPER_NOT_STAGE1_RELEVANT_WITH_REASON",
    "PAPER_OWNER_REVIEW_REQUIRED",
)
PAIRED_STATUSES = (
    "PAIRED_REPLAY_PAPER_INPUT_READY",
    "PAIRED_PARTIAL",
    "REPLAY_ONLY_READY",
    "PAPER_ONLY_READY",
    "PAIRED_FILL_REQUIRED",
    "NOT_STAGE1_RELEVANT_WITH_REASON",
    "OWNER_REVIEW_REQUIRED",
)

DATA_BINDING_STATUSES = (
    "DATA_BINDING_READY",
    "DATA_BINDING_PARTIAL",
    "DATA_BINDING_FILL_REQUIRED",
)
DATA_BINDING_CLASSES = (
    "SYNTHETIC_TEST_VECTOR_READY",
    "REPLAY_HISTORICAL_DATA_BINDING_READY",
    "PAPER_SIMULATED_MARKET_DATA_BINDING_READY",
    "PAPER_CURRENT_MARKET_DATA_BINDING_REQUIRED",
    "DATA_BINDING_PARTIAL",
    "DATA_BINDING_FILL_REQUIRED",
    "OWNER_REVIEW_REQUIRED_WITH_REASON",
    "NOT_STAGE1_RELEVANT_WITH_REASON",
)

FILL_ACTION_FAMILIES = (
    "MISSING_HISTORICAL_PRICE_SERIES",
    "MISSING_ORDERBOOK_SNAPSHOT_SERIES",
    "MISSING_EVENT_STATE_SERIES",
    "MISSING_VOLUME_OR_DEPTH_SERIES",
    "MISSING_OUTCOME_LABEL",
    "MISSING_PROBABILITY_MODEL_INPUT",
    "MISSING_FEE_MODEL_INPUT",
    "MISSING_SLIPPAGE_MODEL_INPUT",
    "MISSING_LATENCY_MEASUREMENT",
    "MISSING_COVARIANCE_INPUT",
    "MISSING_CORRELATION_INPUT",
    "MISSING_QUANTUM_OBJECTIVE_PARAMETER",
    "MISSING_QUANTUM_VARIABLE_DOMAIN",
    "MISSING_QUANTUM_CONSTRAINT_PARAMETER",
    "MISSING_CLASSICAL_COMPARATOR_INPUT",
    "MISSING_PAPER_MARKET_STATE_BINDING",
    "MISSING_MARKET_SPECIFIC_ROUTE",
    "MISSING_AGENT_CONSUMER_ROUTE",
)

SMOKE_STATUSES = (
    "SMOKE_EXECUTION_PASSED",
    "SMOKE_EXECUTION_SKIPPED_WITH_EXACT_REASON",
    "SMOKE_EXECUTION_FAILED",
)

QUANTUM_LANES = (
    "QUANTUM_BATCH_PRECOMPUTE_READY",
    "QUANTUM_BATCH_PRECOMPUTE_PARTIAL",
    "QUANTUM_BATCH_FIELD_FILL_REQUIRED",
    "CLASSICAL_COMPARATOR_ONLY_FOR_NOW",
)

DISALLOWED_GENERATED_STATUSES = (
    "BLOCKER",
    "PLACEHOLDER_ONLY",
    "METADATA_ONLY_READY",
    "SOLVER_COMPATIBLE_LABEL_ONLY",
    "FUTURE_CONSUMER_NOTE_ONLY",
    "SOURCE_ACCEPTED",
    "LIVE_READY",
    "ORDER_READY",
    "PROFIT_PROVEN",
    "QUANTUM_ADVANTAGE_PROVEN",
)

NO_AUTHORITY_FLAGS: dict[str, bool] = {
    "creates_replay_result_packets": False,
    "creates_paper_result_packets": False,
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
    "creates_latency_superiority_claim": False,
    "creates_execution_superiority_claim": False,
    "creates_qtt_freeze_checksum_global_digest_authority": False,
    "creates_qtt_generated_sha_authority": False,
    "mutates_protected_atomicrows_bundle_checksum_artifacts": False,
    "ci_requires_network": False,
}

BOUNDARY_COUNT_FIELDS: dict[str, int] = {
    "replay_result_packet_count": 0,
    "paper_result_packet_count": 0,
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
    "latency_superiority_claim_count": 0,
    "execution_superiority_claim_count": 0,
    "qtt_freeze_checksum_global_digest_authority_count": 0,
    "qtt_generated_sha_authority_count": 0,
    "protected_atomicrows_bundle_checksum_mutation_count": 0,
}

PROTECTED_FILES_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "protected AtomicRows bundle/checksum artifacts",
)


@dataclass(frozen=True)
class AuthorityCheck:
    ok: bool
    failures: tuple[str, ...]


def map_source_truth_status(raw_status: Any) -> str:
    text = str(raw_status or "").upper()
    if "OFFICIAL" in text:
        return "OFFICIAL_SOURCE_CANDIDATE"
    if "SOCIAL" in text:
        return "SOCIAL_SOURCE_CANDIDATE"
    if "INSTITUTIONAL" in text:
        return "INSTITUTIONAL_SOURCE_CANDIDATE"
    if "WEB" in text:
        return "WEB_SOURCE_CANDIDATE"
    if "RESEARCH" in text or "QUANTUM_PROVIDER" in text:
        return "RESEARCH_SOURCE_CANDIDATE"
    if "OWNER" in text:
        return "OWNER_PROVIDED_CANDIDATE"
    return "REPO_LOCAL_ARTIFACT_CANDIDATE"


def candidate_truth_status_for_adapter(
    *, smoke_passed: bool, fill_required: bool, owner_review: bool = False
) -> str:
    if owner_review:
        return "OWNER_REVIEW_REQUIRED_WITH_REASON"
    if fill_required:
        return "FILL_REQUIRED_WITH_EXACT_REASON"
    if smoke_passed:
        return "FORMULATION_EXECUTABLE_CANDIDATE"
    return "FILL_REQUIRED_WITH_EXACT_REASON"


def boundary_payload(record_id: str = "PR162R_AUTHORITY_BOUNDARY") -> dict[str, Any]:
    return {
        "record_id": record_id,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "authority_class": AUTHORITY_CLASS,
        "central_policy_consumed_flag": True,
        "truth_statuses": list(TRUTH_STATUSES),
        "computability_routes": list(COMPUTABILITY_ROUTES),
        "data_binding_statuses": list(DATA_BINDING_STATUSES),
        "no_authority_flags": dict(NO_AUTHORITY_FLAGS),
        "boundary_count_fields": dict(BOUNDARY_COUNT_FIELDS),
        "protected_files_not_touched": list(PROTECTED_FILES_NOT_TOUCHED),
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
    }


def no_authority_record(record_id: str, audit_family: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "audit_family": audit_family,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
    }


def validate_record_authority(record: dict[str, Any]) -> AuthorityCheck:
    failures: list[str] = []
    for key, expected in NO_AUTHORITY_FLAGS.items():
        if key in record and record.get(key) is not expected:
            failures.append(f"authority flag drift: {key}={record.get(key)!r}")
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        if key in record and record.get(key) != expected:
            failures.append(f"boundary count drift: {key}={record.get(key)!r}")
    if record.get("live_order_authority") is True:
        failures.append("live_order_authority true")
    if record.get("no_live_order_authority") is False:
        failures.append("no_live_order_authority false")
    text_values = [str(value) for value in record.values() if isinstance(value, str)]
    for disallowed in DISALLOWED_GENERATED_STATUSES:
        if any(value == disallowed for value in text_values):
            failures.append(f"disallowed generated status: {disallowed}")
    return AuthorityCheck(not failures, tuple(failures))
