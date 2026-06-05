"""Central authority boundary policy for PR162R-B.

This module is the single source for no-result, no-live, no-profit,
no-source-acceptance, no-connector, no-private-state, no-quantum-backend,
and no-checksum authority fields used by PR162R-B builders and validators.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


PR_ID = "PR162R-B"
EXPECTED_BRANCH = "pr162r-b-replay-paper-data-binding-completion"
AUTHORITY_CLASS = (
    "PR162R_B_REPLAY_PAPER_DATA_BINDING_COMPLETION_NONLIVE_NO_EXECUTION_NO_AUTHORITY"
)
POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets."
    "pr162r_b_replay_paper_data_binding_completion.authority_policy"
)

ALLOWED_BINDING_STATUSES = (
    "BINDING_MATERIALIZED",
    "BINDING_PARTIAL_WITH_EXACT_REASON",
    "BINDING_FANOUT_MATERIALIZED",
    "SYNTHETIC_FIXTURE_BOUND",
    "REPO_LOCAL_FIXTURE_BOUND",
    "SOURCE_CANDIDATE_BOUND",
    "SOURCE_CANDIDATE_LOCATOR_REQUIRED_WITH_QUERY",
    "DATASET_FAMILY_UNAVAILABLE_WITH_REASON",
    "OWNER_REVIEW_REQUIRED_WITH_REASON",
    "NOT_STAGE1_RELEVANT_WITH_REASON",
)
DISALLOWED_GENERATED_STATUSES = (
    "BLOCKER",
    "PLACEHOLDER_ONLY",
    "METADATA_ONLY_READY",
    "QUEUE_ONLY_READY",
    "FUTURE_CONSUMER_NOTE_ONLY",
    "SOURCE_ACCEPTED",
    "CONNECTOR_BOUND",
    "LIVE_READY",
    "ORDER_READY",
    "RESULT_READY",
    "REPLAY_RESULT_PROVEN",
    "PAPER_RESULT_PROVEN",
    "PROFIT_PROVEN",
    "QUANTUM_ADVANTAGE_PROVEN",
)
SOURCE_CLASSES = (
    "OFFICIAL_SOURCE_CANDIDATE",
    "NON_OFFICIAL_WEB_CANDIDATE",
    "RESEARCH_SOURCE_CANDIDATE",
    "SOCIAL_SOURCE_CANDIDATE",
    "INSTITUTIONAL_SOURCE_CANDIDATE",
    "OWNER_PROVIDED_CANDIDATE",
    "PUBLIC_DATASET_CANDIDATE",
    "REPO_LOCAL_ARTIFACT_CANDIDATE",
    "SYNTHETIC_TEST_FIXTURE",
)
TRUTH_STATUSES = (
    "OFFICIAL_SOURCE_CANDIDATE",
    "NON_OFFICIAL_WEB_CANDIDATE",
    "RESEARCH_SOURCE_CANDIDATE",
    "SOCIAL_SOURCE_CANDIDATE",
    "INSTITUTIONAL_SOURCE_CANDIDATE",
    "OWNER_PROVIDED_CANDIDATE",
    "PUBLIC_DATASET_CANDIDATE",
    "REPO_LOCAL_ARTIFACT_CANDIDATE",
    "SYNTHETIC_TEST_FIXTURE",
    "SOURCE_CANDIDATE_BOUND",
    "REPO_LOCAL_FIXTURE_BOUND",
    "SYNTHETIC_FIXTURE_BOUND",
)
DATA_QUALITY_TIERS = (
    "DQ0_SYNTHETIC_TEST_ONLY",
    "DQ1_RESEARCH_CANDIDATE",
    "DQ2_REPO_LOCAL_HISTORICAL",
    "DQ3_VENUE_SOURCED_HISTORICAL_CANDIDATE",
    "DQ4_REPLAY_READY_VALIDATED",
    "DQ5_PAPER_READY_VALIDATED",
)
PAIRED_BINDING_STATUSES = (
    "REPLAY_AND_PAPER_BOUND",
    "REPLAY_BOUND_PAPER_PARTIAL",
    "PAPER_BOUND_REPLAY_PARTIAL",
    "REPLAY_PARTIAL_PAPER_PARTIAL",
    "SYNTHETIC_REPLAY_AND_PAPER_FIXTURE_BOUND",
    "SOURCE_CANDIDATE_REPLAY_AND_PAPER_BOUND",
    "DATASET_FAMILY_UNAVAILABLE_WITH_REASON",
    "OWNER_REVIEW_REQUIRED_WITH_REASON",
    "NOT_STAGE1_RELEVANT_WITH_REASON",
)
LATENCY_CLASSES = (
    "HOT_PATH_REQUIRED",
    "PRECOMPUTE_REQUIRED",
    "BATCH_ONLY",
    "QUANTUM_BATCH_ONLY",
    "CACHEABLE",
    "INCREMENTAL_UPDATE",
    "REPLAY_ONLY",
    "PAPER_ONLY",
    "BENCHMARK_REQUIRED_BEFORE_LIVE",
    "NOT_LIVE_ELIGIBLE_IN_THIS_PR",
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
    "qtt_freeze_checksum_global_digest_authority_count": 0,
    "qtt_generated_sha_authority_count": 0,
    "protected_atomicrows_bundle_checksum_mutation_count": 0,
    "dedup_group_label_sha_hash_checksum_violation_count": 0,
}
PROTECTED_FILES_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "protected AtomicRows bundle/checksum/hash artifacts",
)

DEDUP_FORBIDDEN_WORDS = (
    "HASH",
    "CHECKSUM",
    "DIGEST",
    "FREEZE",
    "CRYPTOGRAPHIC",
    "ATOMICROWS BUNDLE",
)
DEDUP_FORBIDDEN_PATTERNS = (
    re.compile(r"\bSHA(?:1|224|256|384|512)?\b", re.IGNORECASE),
    re.compile(r"\bQTT[-_ ]?GENERATED[-_ ]?SHA\b", re.IGNORECASE),
)
HEX_DIGEST_RE = re.compile(r"\b[a-fA-F0-9]{32,}\b")


@dataclass(frozen=True)
class AuthorityCheck:
    ok: bool
    failures: tuple[str, ...]


def boundary_payload(record_id: str = "PR162R_B_AUTHORITY_BOUNDARY") -> dict[str, Any]:
    return {
        "record_id": record_id,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "authority_class": AUTHORITY_CLASS,
        "central_policy_consumed_flag": True,
        "allowed_binding_statuses": list(ALLOWED_BINDING_STATUSES),
        "source_classes": list(SOURCE_CLASSES),
        "truth_statuses": list(TRUTH_STATUSES),
        "data_quality_tiers": list(DATA_QUALITY_TIERS),
        "paired_binding_statuses": list(PAIRED_BINDING_STATUSES),
        "latency_classes": list(LATENCY_CLASSES),
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


def validate_dedup_group_label(label: str) -> AuthorityCheck:
    failures: list[str] = []
    text = str(label or "")
    if not text:
        failures.append("dedup_group_label missing")
    upper = text.upper()
    for word in DEDUP_FORBIDDEN_WORDS:
        if word in upper:
            failures.append(f"dedup_group_label contains forbidden authority word: {word}")
    for pattern in DEDUP_FORBIDDEN_PATTERNS:
        if pattern.search(text):
            failures.append("dedup_group_label contains forbidden SHA authority language")
    if HEX_DIGEST_RE.search(text):
        failures.append("dedup_group_label resembles an opaque digest")
    return AuthorityCheck(not failures, tuple(failures))


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
    for value in record.values():
        if isinstance(value, str) and value in DISALLOWED_GENERATED_STATUSES:
            failures.append(f"disallowed generated status: {value}")
    return AuthorityCheck(not failures, tuple(failures))
