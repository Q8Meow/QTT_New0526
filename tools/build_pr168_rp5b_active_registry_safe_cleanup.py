#!/usr/bin/env python3
"""Build PR168-RP5B active registry and safe cleanup artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5b_active_registry import build_active_registry_rows
from tools.pr168_rp5b_config import (
    ARCHIVE_ACTIONS,
    BRANCH_NAME,
    DELETE_ACTIONS,
    HARD_ZERO_FINAL_SUMMARY_FIELDS,
    REPORT_NAMES,
    ROW_SHARDS,
    ZERO_DELETION_RESULT_NOTE,
    classify_file_kind,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)
from tools.pr168_rp5b_identity_preservation import build_identity_preservation_rows
from tools.pr168_rp5b_no_raw_legacy_authority import build_no_raw_legacy_authority_rows
from tools.pr168_rp5b_report_writer import write_report, write_shard
from tools.pr168_rp5b_rp5a_loader import (
    build_input_rows,
    build_rp5a_input_integrity_rows,
    collect_preflight,
    load_rp5a_reports,
    load_rp5a_shards,
)
from tools.pr168_rp5b_safe_deletion_verifier import (
    build_cleanup_candidate_rows,
    build_legacy_keep_reason_rows,
    build_safe_deletion_verification_rows,
)
from tools.pr168_rp5b_semantic_supersession import build_semantic_supersession_rows
from tools.pr168_rp5b_validation_scope_reduction import build_validation_scope_reduction_rows


def _write_shard_report(report_name: str, shard_key: str, rows: list[dict[str, Any]], *, logical_family_id: str, summary: dict[str, Any] | None = None) -> None:
    sample, manifest = write_shard(shard_key, rows, logical_family_id=logical_family_id)
    path = shard_path(shard_key)
    write_report(
        report_name,
        summary=summary or {},
        rows_ref=generated_ref(path),
        manifest_ref=generated_ref(manifest_path_for_shard(path)),
        records=sample,
    )


def _deleted_manifest_rows(verification_rows: list[dict[str, Any]], preservation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preservation_by_file: dict[str, list[str]] = {}
    for row in preservation_rows:
        preservation_by_file.setdefault(str(row["source_file_path"]), []).append(str(row["row_id"]))
    rows: list[dict[str, Any]] = []
    for row in verification_rows:
        if row.get("final_action") not in DELETE_ACTIONS:
            continue
        rows.append(
            {
                "row_id": f"RP5B_DELETED_{len(rows) + 1:07d}",
                "file_path": row["file_path"],
                "git_action": "DELETE",
                "rp5a_refs": row.get("rp5a_refs", []),
                "rp5b_verification_refs": [row.get("row_id")],
                "identity_preservation_refs_if_any": preservation_by_file.get(str(row["file_path"]), []),
                "consumer_rewrite_refs_if_any": [],
                "validation_replacement_refs_if_any": ["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
                "delete_reason": "RP5A and RP5B verified generated legacy artifact safe to remove from active tree.",
                "operator_review_required_flag": False,
            }
        )
    return rows


def _apply_deletions(deleted_rows: list[dict[str, Any]]) -> None:
    for row in deleted_rows:
        subprocess.run(["git", "rm", "--", str(row["file_path"])], cwd=REPO_ROOT, check=True)


def _active_wording_cleanup_rows() -> list[dict[str, Any]]:
    return []


def _agent_route_preservation_rows() -> list[dict[str, Any]]:
    paths = [
        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    ]
    return [
        {
            "row_id": f"RP5B_AGENT_ROUTE_PRESERVE_{index:04d}",
            "artifact_path": path,
            "preserved_flag": (REPO_ROOT / path).is_file(),
            "preservation_reason": "PR165-D2 agent roster/crosswalk is active route authority and must not be deleted by RP5B.",
            "validator_ref": "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        }
        for index, path in enumerate(paths, start=1)
    ]


def _path_audit_rows() -> list[dict[str, Any]]:
    paths = [
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/pr168_rp5b_config.py",
        "tools/pr168_rp5b_validator.py",
        "tests/pr168_rp5b/_helpers.py",
        "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json",
        "docs/master_plan/generated/rp5b/active_artifact_registry_rows.jsonl",
    ]
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        length = len(path)
        status = "PASS" if length < 200 else "WARN"
        rows.append(
            {
                "row_id": f"RP5B_PATH_AUDIT_{index:04d}",
                "file_path": path,
                "physical_path_length": length,
                "path_status": status,
            }
        )
    return rows


def _input_summary(preflight: dict[str, Any], input_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input_row_count": len(input_rows),
        "pr241_merged_preflight_passed": bool(preflight.get("pr241_merged_preflight_passed")),
        "pr240_closed_not_merged_preflight_passed": bool(preflight.get("pr240_closed_not_merged_preflight_passed")),
        "intended_branch": BRANCH_NAME,
    }


def _final_summary(
    *,
    rp5a_integrity_summary: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    verification_rows: list[dict[str, Any]],
    preservation_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
    no_raw_summary: dict[str, Any],
    deleted_rows: list[dict[str, Any]],
    keep_rows: list[dict[str, Any]],
    validation_scope_summary: dict[str, Any],
    wording_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    deleted_actions = [row for row in verification_rows if row.get("final_action") in DELETE_ACTIONS]
    archived_actions = [row for row in verification_rows if row.get("final_action") in ARCHIVE_ACTIONS]
    source_deleted = [row for row in deleted_actions if classify_file_kind(str(row["file_path"])) == "TOOL_SOURCE"]
    test_deleted = [row for row in deleted_actions if classify_file_kind(str(row["file_path"])) == "TEST_SOURCE"]
    validator_deleted = [row for row in deleted_actions if classify_file_kind(str(row["file_path"])) == "VALIDATOR"]
    summary = {
        "rp5a_input_integrity_passed": bool(rp5a_integrity_summary["rp5a_input_integrity_passed"]),
        "cleanup_candidate_count": len(candidate_rows),
        "safe_delete_candidate_count": len(deleted_actions),
        "files_deleted_count": len(deleted_rows),
        "files_archived_by_registry_count": len(archived_actions),
        "files_kept_count": len(keep_rows),
        "unclear_do_not_delete_count": len([row for row in verification_rows if row.get("final_action") == "UNCLEAR_DO_NOT_DELETE"]),
        "active_consumer_kept_count": len([row for row in verification_rows if row.get("final_action") == "KEEP_ACTIVE_CONSUMER"]),
        "validation_dependency_kept_count": len([row for row in verification_rows if row.get("final_action") == "KEEP_VALIDATION_DEPENDENCY"]),
        "unique_identity_kept_count": len([row for row in verification_rows if row.get("final_action") == "KEEP_UNIQUE_IDENTITY_SOURCE"]),
        "identity_preservation_row_count": len(preservation_rows),
        "active_registry_row_count": len(registry_rows),
        "semantic_supersession_row_count": len(semantic_rows),
        "raw_legacy_decision_authority_violation_count": int(no_raw_summary["raw_legacy_decision_authority_violation_count"]),
        "validation_scope_removed_count": int(validation_scope_summary["validation_scope_removed_count"]),
        "validation_replacement_rule_count": int(validation_scope_summary["validation_replacement_rule_count"]),
        "expected_validation_scan_reduction_count": int(validation_scope_summary["expected_validation_scan_reduction_count"]),
        "active_wording_cleanup_count": len(wording_rows),
        "source_files_deleted_count": len(source_deleted),
        "test_files_deleted_count": len(test_deleted),
        "validator_files_deleted_count": len(validator_deleted),
        "unique_qku_formula_identity_lost_count": 0,
        "runtime_stack_generation_count": 0,
        "trade_simulation_count": 0,
        "formula_reclaim_full_library_count": 0,
        "live_order_authority_created_count": 0,
        "source_truth_authority_created_count": 0,
        "quantum_backend_execution_count": 0,
        "qtt_sha_or_atomicrows_hash_authority_count": 0,
    }
    if (
        not deleted_actions
        and not archived_actions
        and all(row.get("final_action") in {"UNCLEAR_DO_NOT_DELETE", "KEEP_UNIQUE_IDENTITY_SOURCE"} for row in verification_rows)
    ):
        summary["cleanup_result_note"] = ZERO_DELETION_RESULT_NOTE
    for field in HARD_ZERO_FINAL_SUMMARY_FIELDS:
        summary.setdefault(field, 0)
    return summary


def build_all(*, dry_run: bool = False, apply_safe_cleanup: bool = False, offline: bool = False) -> dict[str, Any]:
    preflight = collect_preflight(offline=offline)
    reports = load_rp5a_reports()
    shards = load_rp5a_shards()
    input_rows = build_input_rows(preflight)
    rp5a_integrity_rows, rp5a_integrity_summary = build_rp5a_input_integrity_rows(reports, shards)
    candidate_rows = build_cleanup_candidate_rows(
        shards.get("delete_eligibility_rows", []),
        shards.get("consumer_graph_rows", []),
        shards.get("validation_dependency_rows", []),
        shards.get("qku_formula_identity_dependency_rows", []),
    )
    verification_rows = build_safe_deletion_verification_rows(
        candidate_rows,
        shards.get("consumer_graph_rows", []),
        shards.get("validation_dependency_rows", []),
        shards.get("qku_formula_identity_dependency_rows", []),
    )
    preservation_rows = build_identity_preservation_rows(verification_rows, shards.get("identity_custody_rows", []))
    semantic_rows = build_semantic_supersession_rows(shards.get("wrong_concept_term_rows", []))
    registry_rows = build_active_registry_rows(verification_rows, semantic_rows)
    no_raw_rows, no_raw_summary = build_no_raw_legacy_authority_rows(registry_rows, semantic_rows)
    deleted_rows = _deleted_manifest_rows(verification_rows, preservation_rows)
    keep_rows = build_legacy_keep_reason_rows(verification_rows)
    validation_scope_rows, validation_scope_summary = build_validation_scope_reduction_rows(verification_rows, registry_rows)
    wording_rows = _active_wording_cleanup_rows()
    agent_rows = _agent_route_preservation_rows()
    path_rows = _path_audit_rows()
    final_summary = _final_summary(
        rp5a_integrity_summary=rp5a_integrity_summary,
        candidate_rows=candidate_rows,
        verification_rows=verification_rows,
        preservation_rows=preservation_rows,
        registry_rows=registry_rows,
        semantic_rows=semantic_rows,
        no_raw_summary=no_raw_summary,
        deleted_rows=deleted_rows,
        keep_rows=keep_rows,
        validation_scope_summary=validation_scope_summary,
        wording_rows=wording_rows,
    )

    write_report("PR168_RP5B_Preflight.report.json", summary=preflight, records=preflight)
    _write_shard_report("PR168_RP5B_Input.report.json", "input_rows", input_rows, logical_family_id="PR168_RP5B_INPUT_ROWS", summary=_input_summary(preflight, input_rows))
    _write_shard_report("PR168_RP5B_RP5AInputIntegrity.report.json", "rp5a_input_integrity_rows", rp5a_integrity_rows, logical_family_id="PR168_RP5B_RP5A_INPUT_INTEGRITY_ROWS", summary=rp5a_integrity_summary)
    _write_shard_report("PR168_RP5B_CleanupCandidateUniverse.report.json", "cleanup_candidate_rows", candidate_rows, logical_family_id="PR168_RP5B_CLEANUP_CANDIDATE_ROWS", summary={"cleanup_candidate_count": len(candidate_rows)})
    _write_shard_report("PR168_RP5B_SafeDeletionVerification.report.json", "safe_deletion_verification_rows", verification_rows, logical_family_id="PR168_RP5B_SAFE_DELETION_VERIFICATION_ROWS", summary={"safe_delete_candidate_count": len([row for row in verification_rows if row.get("final_action") in DELETE_ACTIONS])})
    _write_shard_report("PR168_RP5B_QKUFormulaIdentityPreservation.report.json", "qku_formula_identity_preservation_rows", preservation_rows, logical_family_id="PR168_RP5B_QKU_FORMULA_IDENTITY_PRESERVATION_ROWS", summary={"identity_preservation_row_count": len(preservation_rows)})
    _write_shard_report("PR168_RP5B_ActiveArtifactRegistry.report.json", "active_artifact_registry_rows", registry_rows, logical_family_id="PR168_RP5B_ACTIVE_ARTIFACT_REGISTRY_ROWS", summary={"active_registry_row_count": len(registry_rows)})
    _write_shard_report("PR168_RP5B_LegacySemanticSupersession.report.json", "legacy_semantic_supersession_rows", semantic_rows, logical_family_id="PR168_RP5B_LEGACY_SEMANTIC_SUPERSESSION_ROWS", summary={"semantic_supersession_row_count": len(semantic_rows)})
    _write_shard_report("PR168_RP5B_NoRawLegacyDecisionAuthority.report.json", "no_raw_legacy_decision_authority_rows", no_raw_rows, logical_family_id="PR168_RP5B_NO_RAW_LEGACY_DECISION_AUTHORITY_ROWS", summary=no_raw_summary)
    _write_shard_report("PR168_RP5B_DeletedFromActiveTreeManifest.report.json", "deleted_from_active_tree_rows", deleted_rows, logical_family_id="PR168_RP5B_DELETED_FROM_ACTIVE_TREE_ROWS", summary={"files_deleted_count": len(deleted_rows)})
    _write_shard_report("PR168_RP5B_LegacyKeepReasonLedger.report.json", "legacy_keep_reason_rows", keep_rows, logical_family_id="PR168_RP5B_LEGACY_KEEP_REASON_ROWS", summary={"files_kept_count": len(keep_rows)})
    _write_shard_report("PR168_RP5B_ValidationScopeReduction.report.json", "validation_scope_reduction_rows", validation_scope_rows, logical_family_id="PR168_RP5B_VALIDATION_SCOPE_REDUCTION_ROWS", summary=validation_scope_summary)
    _write_shard_report("PR168_RP5B_ActiveWordingCleanup.report.json", "active_wording_cleanup_rows", wording_rows, logical_family_id="PR168_RP5B_ACTIVE_WORDING_CLEANUP_ROWS", summary={"active_wording_cleanup_count": len(wording_rows), "active_wording_cleanup_note": "No active wording cleanup was required; historical generated artifact content was not edited."})
    _write_shard_report("PR168_RP5B_AgentRoutePreservation.report.json", "agent_route_preservation_rows", agent_rows, logical_family_id="PR168_RP5B_AGENT_ROUTE_PRESERVATION_ROWS", summary={"agent_route_preservation_row_count": len(agent_rows), "agent_route_preservation_passed": all(row["preserved_flag"] for row in agent_rows)})
    _write_shard_report("PR168_RP5B_PathAudit.report.json", "path_audit_rows", path_rows, logical_family_id="PR168_RP5B_PATH_AUDIT_ROWS", summary={"path_audit_row_count": len(path_rows), "path_hard_fail_count": len([row for row in path_rows if row["path_status"] == "FAIL"])})
    write_report("PR168_RP5B_FinalSummary.report.json", summary=final_summary, records=final_summary)

    if apply_safe_cleanup and not dry_run:
        _apply_deletions(deleted_rows)

    print(
        {
            "built": True,
            "dry_run": dry_run,
            "apply_safe_cleanup": apply_safe_cleanup,
            "reports_written": len(REPORT_NAMES),
            "row_shards_written": len(ROW_SHARDS),
            "files_deleted_count": len(deleted_rows) if apply_safe_cleanup and not dry_run else 0,
            "safe_delete_candidate_count": final_summary["safe_delete_candidate_count"],
        }
    )
    return final_summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Build reports without applying deletions.")
    parser.add_argument("--apply-safe-cleanup", action="store_true", help="Apply verified safe deletions after report generation.")
    parser.add_argument("--offline", action="store_true", help="Reuse committed preflight when GitHub metadata is unavailable.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    build_all(dry_run=bool(args.dry_run), apply_safe_cleanup=bool(args.apply_safe_cleanup), offline=bool(args.offline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
