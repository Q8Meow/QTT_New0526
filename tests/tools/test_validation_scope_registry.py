from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from tools import validation_scope_registry as registry
from src.qtt.stage1_prediction_markets.atomicrows_semantic_field_coverage_enrichment_plan import (
    report as pr140_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate import (
    report as pr142_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_owner_authorization_gate import (
    report as pr141_report,
)
from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    report as pr152_report,
)
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import (
    constants as pr167_constants,
)
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import (
    io as pr167_io,
)
from src.qtt.stage1_prediction_markets.qtt_owner_global_override_directive_currentization_and_internal_gate_release import (
    report as pr143_report,
)


PR168_BRANCH = registry.PR168_GFP_BRANCH
PR168_RP_BRANCH = registry.PR168_RP_BRANCH
PR168_RANK_BRANCH = registry.PR168_RANK_BRANCH
FIXTURE_BRANCH = registry.VALIDATION_FIXTURE_BRANCH
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_GFP_QKUBaselineCountReconcile.report.json",
        "docs/master_plan/generated/pr168_gfp_shards/PR168_GFP_FormulaAssignmentMatrix.report.shard_0001.json",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/prediction_market_math.py",
        "tests/pr168_gfp/test_pr168_gfp_prediction_market_math.py",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "tools/validate_pr168_gfp_formula_assignment_coverage.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py",
    ],
)
def test_pr168_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
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
    ],
)
def test_pr168_rp_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR168_RANK_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_EvidenceBackedRanking.part_0001_of_0001.report.json",
        "tools/build_pr168_rank_evidence_backed_ranking.py",
        "tools/pr168_rank_compute_kernel.py",
        "tools/validate_pr168_rank_input_consumption.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tests/pr168_rank/test_input_consumption.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rank_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


def test_pr168_allowed_paths_pass_on_validation_fixture_branch_only_when_registered() -> None:
    assert registry.is_validation_context_branch(FIXTURE_BRANCH)
    assert registry.is_pr_scoped_changed_path_allowed(
        FIXTURE_BRANCH,
        "docs/master_plan/generated/PR168_GFP_GlobalLabelInventory.report.json",
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        FIXTURE_BRANCH,
        "docs/master_plan/generated/OtherGeneratedReport.report.json",
    )


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/OtherGeneratedReport.report.json",
        "tools/random_tool.py",
        "src/qtt/stage1_prediction_markets/other_feature/report.py",
        "tests/random/test_other.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "AtomicRows.bundle.sha256",
        "docs/master_plan/generated/AtomicRows.bundle.sha256",
        ".tmp/qtt-validation-router/result.json",
        "src/qtt/live_connectors/live_exchange.py",
        "src/qtt/private_state/cash_reader.py",
        "cash/account.json",
        "src/qtt/live_order_router.py",
        "secrets/token.txt",
    ],
)
def test_pr168_disallowed_and_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_GFP_QKUBaselineCountReconcile.report.json",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/pnl.py",
    ],
)
def test_pr168_rp_rejects_gfp_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)


def test_pr167_production_builder_still_rejects_pr168_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pr167_io, "_current_branch", lambda _repo_root: PR168_BRANCH)
    monkeypatch.setattr(pr167_io, "_ci_branch_context", lambda _repo_root: PR168_BRANCH)
    with pytest.raises(RuntimeError, match=PR168_BRANCH):
        pr167_io.ensure_branch(REPO_ROOT)


@pytest.mark.parametrize("branch", [pr167_constants.BASE_BRANCH, pr167_constants.EXPECTED_BRANCH])
def test_pr167_builder_fixture_can_use_valid_contexts(
    monkeypatch: pytest.MonkeyPatch,
    branch: str,
) -> None:
    monkeypatch.setattr(pr167_io, "_current_branch", lambda _repo_root: branch)
    monkeypatch.setattr(pr167_io, "_ci_branch_context", lambda _repo_root: branch)
    pr167_io.ensure_branch(REPO_ROOT)


def test_downstream_scope_guards_consume_central_registry() -> None:
    modules = [pr152_report, pr140_report, pr141_report, pr142_report, pr143_report]
    for module in modules:
        source = inspect.getsource(module)
        assert "is_pr_scoped_changed_path_allowed" in source
        assert "is_pr168_gfp_changed_path" not in source
