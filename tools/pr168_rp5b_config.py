#!/usr/bin/env python3
"""Central configuration for PR168-RP5B active registry cleanup."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT = GENERATED_ROOT / "rp5b"
RP5A_SHARD_ROOT = GENERATED_ROOT / "rp5a"

REPORT_VERSION = "PR168-RP5B-v1.0"
CREATED_AT_UTC = "2026-06-24T00:00:00Z"
BRANCH_NAME = "pr168-rp5b-active-registry-safe-legacy-cleanup"
ROADMAP_PR = "PR168-RP5B"
PR_TITLE = "PR168-RP5B: Active registry and safe legacy cleanup from RP5A audit"

MAX_TOTAL_ROWS_PER_SHARD = 500_000
PREFERRED_MAX_PHYSICAL_PATH_LENGTH = 180
WARNING_THRESHOLD_PHYSICAL_PATH_LENGTH = 200
HARD_FAIL_PHYSICAL_PATH_LENGTH = 240

FILE_KIND_GENERATED_REPORT = "GENERATED_REPORT"
FILE_KIND_GENERATED_SHARD = "GENERATED_SHARD"
FILE_KIND_MANIFEST = "MANIFEST"
FILE_KIND_TOOL_SOURCE = "TOOL_SOURCE"
FILE_KIND_TEST_SOURCE = "TEST_SOURCE"
FILE_KIND_DOC = "DOC"
FILE_KIND_VALIDATOR = "VALIDATOR"
FILE_KIND_CURRENTIZATION = "CURRENTIZATION"
FILE_KIND_UNKNOWN = "UNKNOWN"

CLEANUP_CANDIDATE_CLASSIFICATIONS = frozenset(
    {
        "DELETE_FROM_ACTIVE_TREE_SAFE",
        "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM",
        "KEEP_LEGACY_SUMMARY_ONLY",
        "ARCHIVE_NO_VALIDATION_SCAN",
        "REWRITE_CONSUMER_FIRST",
    }
)

PROTECTED_CLASSIFICATIONS = frozenset(
    {
        "UNCLEAR_DO_NOT_DELETE",
        "KEEP_ACTIVE_CONSUMER",
        "KEEP_VALIDATION_DEPENDENCY",
        "KEEP_UNIQUE_QKU_FORMULA_SOURCE",
        "KEEP_TEST_FIXTURE",
    }
)

FINAL_ACTIONS = frozenset(
    {
        "DELETE_ACTIVE_TREE_NOW",
        "ARCHIVE_NO_VALIDATION_SCAN_NOW",
        "KEEP_ACTIVE_CONSUMER",
        "KEEP_VALIDATION_DEPENDENCY",
        "KEEP_UNIQUE_IDENTITY_SOURCE",
        "KEEP_TEST_FIXTURE",
        "KEEP_SOURCE_CODE",
        "REWRITE_CONSUMER_FIRST",
        "UNCLEAR_DO_NOT_DELETE",
        "DEFER_TO_RP5C_IDENTITY_RECLAIM",
        "DEFER_TO_RP5D_EXECUTABILITY",
    }
)

DELETE_ACTIONS = frozenset({"DELETE_ACTIVE_TREE_NOW"})
ARCHIVE_ACTIONS = frozenset({"ARCHIVE_NO_VALIDATION_SCAN_NOW"})

HARD_ZERO_FINAL_SUMMARY_FIELDS = (
    "unique_qku_formula_identity_lost_count",
    "runtime_stack_generation_count",
    "trade_simulation_count",
    "formula_reclaim_full_library_count",
    "live_order_authority_created_count",
    "source_truth_authority_created_count",
    "quantum_backend_execution_count",
    "qtt_sha_or_atomicrows_hash_authority_count",
)

RP5A_REQUIRED_REPORTS = (
    "PR168_RP5A_FinalSummary.report.json",
    "PR168_RP5A_DeleteEligibilityDraft.report.json",
    "PR168_RP5A_LegacyFileSemanticAudit.report.json",
    "PR168_RP5A_LegacyPRSemanticAudit.report.json",
    "PR168_RP5A_WrongConceptTermIndex.report.json",
    "PR168_RP5A_ConsumerGraph.report.json",
    "PR168_RP5A_ValidationDependencyGraph.report.json",
    "PR168_RP5A_QKUFormulaIdentityDependency.report.json",
    "PR168_RP5A_IdentityCustodyGraph.report.json",
    "PR168_RP5A_StaleSemanticBlastRadius.report.json",
    "PR168_RP5A_ValidationTimeRisk.report.json",
    "PR168_RP5A_FutureRP5BPlan.report.json",
    "PR168_RP5A_NoDeletionProof.report.json",
    "PR168_RP5A_ScanPerformance.report.json",
)

RP5A_REQUIRED_SHARDS = {
    "delete_eligibility_rows": "delete_eligibility_rows.jsonl",
    "future_rp5b_plan_rows": "future_rp5b_plan_rows.jsonl",
    "legacy_file_semantic_rows": "legacy_file_semantic_rows.jsonl",
    "legacy_pr_semantic_rows": "legacy_pr_semantic_rows.jsonl",
    "wrong_concept_term_rows": "wrong_concept_term_rows.jsonl",
    "consumer_graph_rows": "consumer_graph_rows.jsonl",
    "validation_dependency_rows": "validation_dependency_rows.jsonl",
    "qku_formula_identity_dependency_rows": "qku_formula_identity_dependency_rows.jsonl",
    "identity_custody_rows": "identity_custody_rows.jsonl",
    "agent_touchpoint_rows": "agent_touchpoint_rows.jsonl",
    "blast_radius_rows": "blast_radius_rows.jsonl",
    "validation_time_risk_rows": "validation_time_risk_rows.jsonl",
}

REPORT_NAMES = (
    "PR168_RP5B_Input.report.json",
    "PR168_RP5B_Preflight.report.json",
    "PR168_RP5B_RP5AInputIntegrity.report.json",
    "PR168_RP5B_CleanupCandidateUniverse.report.json",
    "PR168_RP5B_SafeDeletionVerification.report.json",
    "PR168_RP5B_QKUFormulaIdentityPreservation.report.json",
    "PR168_RP5B_ActiveArtifactRegistry.report.json",
    "PR168_RP5B_LegacySemanticSupersession.report.json",
    "PR168_RP5B_NoRawLegacyDecisionAuthority.report.json",
    "PR168_RP5B_DeletedFromActiveTreeManifest.report.json",
    "PR168_RP5B_LegacyKeepReasonLedger.report.json",
    "PR168_RP5B_ValidationScopeReduction.report.json",
    "PR168_RP5B_ActiveWordingCleanup.report.json",
    "PR168_RP5B_AgentRoutePreservation.report.json",
    "PR168_RP5B_PathAudit.report.json",
    "PR168_RP5B_FinalSummary.report.json",
)

ROW_SHARDS = {
    "input_rows": "input_rows.jsonl",
    "rp5a_input_integrity_rows": "rp5a_input_integrity_rows.jsonl",
    "cleanup_candidate_rows": "cleanup_candidate_rows.jsonl",
    "safe_deletion_verification_rows": "safe_deletion_verification_rows.jsonl",
    "qku_formula_identity_preservation_rows": "qku_formula_identity_preservation_rows.jsonl",
    "active_artifact_registry_rows": "active_artifact_registry_rows.jsonl",
    "legacy_semantic_supersession_rows": "legacy_semantic_supersession_rows.jsonl",
    "no_raw_legacy_decision_authority_rows": "no_raw_legacy_decision_authority_rows.jsonl",
    "deleted_from_active_tree_rows": "deleted_from_active_tree_rows.jsonl",
    "legacy_keep_reason_rows": "legacy_keep_reason_rows.jsonl",
    "validation_scope_reduction_rows": "validation_scope_reduction_rows.jsonl",
    "active_wording_cleanup_rows": "active_wording_cleanup_rows.jsonl",
    "agent_route_preservation_rows": "agent_route_preservation_rows.jsonl",
    "path_audit_rows": "path_audit_rows.jsonl",
}


def normalize_repo_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def generated_ref(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return normalize_repo_path(path_obj.relative_to(REPO_ROOT))
    except ValueError:
        return normalize_repo_path(path_obj)


def report_path(name: str) -> Path:
    return GENERATED_ROOT / name


def shard_path(key: str) -> Path:
    return SHARD_ROOT / ROW_SHARDS[key]


def manifest_path_for_shard(path: Path) -> Path:
    return path.with_name(path.stem + ".manifest.json")


def rp5a_report_path(name: str) -> Path:
    return GENERATED_ROOT / name


def rp5a_shard_path(key: str) -> Path:
    return RP5A_SHARD_ROOT / RP5A_REQUIRED_SHARDS[key]


def classify_file_kind(path: str | Path) -> str:
    normalized = normalize_repo_path(path)
    name = Path(normalized).name
    lowered = normalized.lower()
    if "currentization" in lowered or "currentize" in lowered:
        return FILE_KIND_CURRENTIZATION
    if normalized.startswith("docs/master_plan/generated/"):
        if name.endswith(".manifest.json"):
            return FILE_KIND_MANIFEST
        if name.endswith(".jsonl"):
            return FILE_KIND_GENERATED_SHARD
        if name.endswith(".report.json") or name.endswith(".json"):
            return FILE_KIND_GENERATED_REPORT
    if normalized.startswith("tools/"):
        if name.startswith("validate_") or "validation" in name or name == "run_validation_gates.py":
            return FILE_KIND_VALIDATOR
        return FILE_KIND_TOOL_SOURCE
    if normalized.startswith("tests/"):
        return FILE_KIND_TEST_SOURCE
    if normalized.startswith("docs/") or name.endswith(".md"):
        return FILE_KIND_DOC
    return FILE_KIND_UNKNOWN


def is_generated_artifact(path: str | Path) -> bool:
    kind = classify_file_kind(path)
    return kind in {FILE_KIND_GENERATED_REPORT, FILE_KIND_GENERATED_SHARD, FILE_KIND_MANIFEST}
