#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validation_scope_registry import (  # noqa: E402
    PR168_GFP_BRANCH,
    PR168_DATA1A_BRANCH,
    PR168_DATA1_BRANCH,
    PR168_RP5A_BRANCH,
    PR168_RP5B_BRANCH,
    PR168_RANK4_BRANCH,
    PR168_RP_BRANCH,
    VALIDATION_FIXTURE_BRANCH,
    explain_pr_scope_decision,
    is_pr_scoped_changed_path_allowed,
    is_validation_context_branch,
    normalize_changed_path,
)


SUCCESS_MARKER = "VALIDATION_SCOPE_REGISTRY_OK"


def main() -> int:
    failures: list[str] = []

    allowed_paths = [
        "docs/master_plan/generated/PR168_GFP_QKUBaselineCountReconcile.report.json",
        "docs/master_plan/generated/pr168_gfp_shards/PR168_GFP_FormulaAssignmentMatrix.report.shard_0001.json",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/pnl.py",
        "tests/pr168_gfp/test_pr168_gfp_prediction_market_math.py",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "tools/validate_pr168_gfp_formula_assignment_coverage.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py",
    ]
    for branch in (PR168_GFP_BRANCH, VALIDATION_FIXTURE_BRANCH):
        for path in allowed_paths:
            if not is_pr_scoped_changed_path_allowed(branch, path):
                failures.append(f"EXPECTED_ALLOWED:{branch}:{path}:{explain_pr_scope_decision(branch, path)}")

    rp_allowed_paths = [
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR168_RP_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_rp_shards/PR168_RP_ComputedReplayResults.part_0001_of_0001.report.json",
        "tools/build_pr168_rp_formula_based_replay_paper_recompute.py",
        "tools/pr168_rp_compute_kernel.py",
        "tools/validate_pr168_rp_formula_execution.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/pr168_rp/test_formula_execution.py",
        "tools/run_validation_gates.py",
    ]
    for path in rp_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_RP_BRANCH}:{path}:{explain_pr_scope_decision(PR168_RP_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    data1_allowed_paths = [
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR168_DATA1_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_data1_snapshots/kalshi/kalshi_snapshots.jsonl",
        "docs/master_plan/generated/pr168_data1_snapshots/kalshi/kalshi_snapshots.manifest.json",
        "docs/master_plan/generated/pr168_data1_forward_l2/polymarket/polymarket_forward_l2.jsonl",
        "docs/master_plan/generated/pr168_data1_historical_replay_candidates/candidate_sources/historical_full_book_candidates.manifest.json",
        "tools/build_pr168_data1_public_market_data_snapshots.py",
        "tools/pr168_data1_validator.py",
        "tools/validate_pr168_data1_public_market_data_snapshots.py",
        "tests/pr168_data1/test_pr168_data1_public_fetch_summary_exists.py",
        "tools/run_validation_gates.py",
    ]
    for path in data1_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_DATA1_BRANCH}:{path}:{explain_pr_scope_decision(PR168_DATA1_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    data1a_allowed_paths = [
        "docs/master_plan/generated/PR168_DATA1A_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_data1a_audit/fetch_inventory_rows.jsonl",
        "docs/master_plan/generated/pr168_data1a_audit/fetch_inventory_rows.manifest.json",
        "tools/build_pr168_data1a_focused_audit.py",
        "tools/pr168_data1a_validator.py",
        "tools/validate_pr168_data1a_focused_audit.py",
        "tests/pr168_data1a/test_pr168_data1a_fetch_inventory_answers_owner_question_a.py",
        "tools/run_validation_gates.py",
    ]
    for path in data1a_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_DATA1A_BRANCH}:{path}:{explain_pr_scope_decision(PR168_DATA1A_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    rp5a_allowed_paths = [
        "docs/master_plan/generated/PR168_RP5A_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5A_LegacyFileSemanticAudit.report.json",
        "docs/master_plan/generated/rp5a/legacy_file_semantic_rows.jsonl",
        "docs/master_plan/generated/rp5a/legacy_file_semantic_rows.manifest.json",
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/pr168_rp5a_config.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        "tests/pr168_rp5a/test_final_summary_counts.py",
        "tools/run_validation_gates.py",
    ]
    for path in rp5a_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_RP5A_BRANCH}:{path}:{explain_pr_scope_decision(PR168_RP5A_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    rp5b_allowed_paths = [
        "docs/master_plan/generated/PR168_RP5B_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json",
        "docs/master_plan/generated/rp5b/active_artifact_registry_rows.jsonl",
        "docs/master_plan/generated/rp5b/active_artifact_registry_rows.manifest.json",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/pr168_rp5b_config.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tests/pr168_rp5b/test_final_summary_counts.py",
        "tools/run_validation_gates.py",
    ]
    for path in rp5b_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_RP5B_BRANCH}:{path}:{explain_pr_scope_decision(PR168_RP5B_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    rank4_allowed_paths = [
        "docs/master_plan/generated/pr168_rank4/art_reg.json",
        "docs/master_plan/generated/pr168_rank4/rank_order.jsonl",
        "docs/master_plan/generated/pr168_rank4/rank_order.manifest.json",
        "docs/master_plan/generated/pr168_rank4/run_receipt.report.json",
        "docs/master_plan/generated/pr168_rank4/pr_body.md",
        "src/qtt/ranking/__init__.py",
        "src/qtt/ranking/pr168_rank4/builder.py",
        "src/qtt/ranking/pr168_rank4/validator.py",
        "tools/build_pr168_rank4_advisory_ranking.py",
        "tools/validate_pr168_rank4_advisory_ranking.py",
        "tests/pr168_rank4/test_rank4_builder.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    ]
    for path in rank4_allowed_paths:
        if not is_pr_scoped_changed_path_allowed(PR168_RANK4_BRANCH, path):
            failures.append(f"EXPECTED_ALLOWED:{PR168_RANK4_BRANCH}:{path}:{explain_pr_scope_decision(PR168_RANK4_BRANCH, path)}")
        if not is_pr_scoped_changed_path_allowed(VALIDATION_FIXTURE_BRANCH, path):
            failures.append(
                f"EXPECTED_ALLOWED:{VALIDATION_FIXTURE_BRANCH}:{path}:"
                f"{explain_pr_scope_decision(VALIDATION_FIXTURE_BRANCH, path)}"
            )

    disallowed_paths = [
        "docs/master_plan/generated/SomeOtherReport.report.json",
        "tools/random_helper.py",
        "src/qtt/stage1_prediction_markets/other_feature/report.py",
        "tests/random/test_other.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "AtomicRows.bundle.sha256",
        ".tmp/qtt-validation-router/result.json",
        "src/qtt/live_connectors/live_exchange.py",
        "src/qtt/private_state/read_cash.py",
        "cash/account.json",
        "src/qtt/live_order_router.py",
        "secrets/token.txt",
    ]
    for branch in (PR168_GFP_BRANCH, VALIDATION_FIXTURE_BRANCH, "main"):
        for path in disallowed_paths:
            if is_pr_scoped_changed_path_allowed(branch, path):
                failures.append(f"EXPECTED_REJECTED:{branch}:{path}")
    for path in disallowed_paths:
        if is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_DATA1_BRANCH}:{path}")
        if is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_DATA1A_BRANCH}:{path}")
        if is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_RP5A_BRANCH}:{path}")
        if is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_RP5B_BRANCH}:{path}")
        if is_pr_scoped_changed_path_allowed(PR168_RANK4_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_RANK4_BRANCH}:{path}")
    for path in [
        "docs/master_plan/generated/PR168_GFP_QKUBaselineCountReconcile.report.json",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/pnl.py",
    ]:
        if is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_RP_BRANCH}:{path}")
        if is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path):
            failures.append(f"EXPECTED_REJECTED:{PR168_RP5B_BRANCH}:{path}")

    if is_pr_scoped_changed_path_allowed("feature/unregistered", allowed_paths[0]):
        failures.append("UNREGISTERED_BRANCH_ALLOWED")
    if normalize_changed_path(".\\docs\\master_plan\\generated\\PR168_GFP_Test.report.json") != (
        "docs/master_plan/generated/PR168_GFP_Test.report.json"
    ):
        failures.append("NORMALIZE_CHANGED_PATH_FAILED")
    if not is_validation_context_branch(VALIDATION_FIXTURE_BRANCH):
        failures.append("FIXTURE_BRANCH_NOT_MARKED_VALIDATION_CONTEXT")
    if is_validation_context_branch(PR168_GFP_BRANCH):
        failures.append("REAL_BRANCH_MARKED_AS_FIXTURE_CONTEXT")

    if failures:
        print("\n".join(failures))
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
