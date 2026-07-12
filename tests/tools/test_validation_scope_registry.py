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
PR168_DATA1_BRANCH = registry.PR168_DATA1_BRANCH
PR168_DATA1A_BRANCH = registry.PR168_DATA1A_BRANCH
PR168_GFP2R_BRANCH = registry.PR168_GFP2R_BRANCH
PR168_RP2_BRANCH = registry.PR168_RP2_BRANCH
PR168_MAP3_BRANCH = registry.PR168_MAP3_BRANCH
PR168_RP3_BRANCH = registry.PR168_RP3_BRANCH
PR168_RANK3_BRANCH = registry.PR168_RANK3_BRANCH
PR168_RP5A_BRANCH = registry.PR168_RP5A_BRANCH
PR168_RP5B_BRANCH = registry.PR168_RP5B_BRANCH
PR168_RP5C_BRANCH = registry.PR168_RP5C_BRANCH
PR168_RP5C_POST_MERGE_REPAIR_BRANCH = registry.PR168_RP5C_POST_MERGE_REPAIR_BRANCH
PR168_VS1_BRANCH = registry.PR168_VS1_BRANCH
PR168_RP5D_BRANCH = registry.PR168_RP5D_BRANCH
PR168_RP5E_BRANCH = registry.PR168_RP5E_BRANCH
PR168_RP5D_R1_BRANCH = registry.PR168_RP5D_R1_BRANCH
PR168_RP5F_BRANCH = registry.PR168_RP5F_BRANCH
PR168_RANK4_BRANCH = registry.PR168_RANK4_BRANCH
PR168_QOPT1_BRANCH = registry.PR168_QOPT1_BRANCH
PR168_VS2_BRANCH = registry.PR168_VS2_BRANCH
PR169_DASH1_BRANCH = registry.PR169_DASH1_BRANCH
PR169_DASH1_UI1_BRANCH = registry.PR169_DASH1_UI1_BRANCH
PR169_DASH1_UI1_R1_BRANCH = registry.PR169_DASH1_UI1_R1_BRANCH
PR169_DASH1_UI1_R2_BRANCH = registry.PR169_DASH1_UI1_R2_BRANCH
PR169_DASH1_UI1_R2_R1_BRANCH = registry.PR169_DASH1_UI1_R2_R1_BRANCH
PR169_DASH1_UI1_R2_R2_BRANCH = registry.PR169_DASH1_UI1_R2_R2_BRANCH
PR169_DASH1_UI1_R2_R3_BRANCH = registry.PR169_DASH1_UI1_R2_R3_BRANCH
PR169_DASH1_UI1_R2_R4_BRANCH = registry.PR169_DASH1_UI1_R2_R4_BRANCH
PR169_DASH1_UI1_R2_R5_BRANCH = registry.PR169_DASH1_UI1_R2_R5_BRANCH
PR169_DASH1_UI1_R2_R6_BRANCH = registry.PR169_DASH1_UI1_R2_R6_BRANCH
PR169_READINESS1_BRANCH = registry.PR169_READINESS1_BRANCH
PR169_PRETRADE1_BRANCH = registry.PR169_PRETRADE1_BRANCH
PR169_SVC1_BRANCH = registry.PR169_SVC1_BRANCH
PR169_AGENT_ORCH1_BRANCH = registry.PR169_AGENT_ORCH1_BRANCH
PR169_QKU_FORMULA_EXP1_BRANCH = registry.PR169_QKU_FORMULA_EXP1_BRANCH
PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH = registry.PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH
PR169_VAL1_BRANCH = registry.PR169_VAL1_BRANCH


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_qku_formula_exp1/acceptance.report.json",
        "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/runtime.py",
        "tools/build_pr169_qku_formula_exp1.py",
        "tools/validate_pr169_qku_formula_exp1.py",
        "tests/pr169_qku_formula_exp1/test_family_j.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    ],
)
def test_pr169_qku_formula_exp1_allowed_paths_are_narrow(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_MAP3_FormulaDependencyGraph.report.json",
        "docs/master_plan/generated/map3/formula_dependency_rows.jsonl",
        "docs/master_plan/generated/PR168_RP5C_FormulaAssignmentLibrary.report.json",
        "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
        "docs/master_plan/generated/rp5a/agent_touchpoint_rows.jsonl",
        "docs/master_plan/generated/rp5a/validation_time_risk_rows.jsonl",
        "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
        "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_universal_coverage.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
        "docs/master_plan/generated/pr168_rp5e/tmp_previews.jsonl",
        "docs/master_plan/generated/pr168_rp5f/targets.jsonl",
        "docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl",
        "docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/acceptance.report.json",
        "docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
        "docs/master_plan/generated/pr169_svc1/service_manifest.json",
        "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/pr169_operator_registry.py",
        "tools/pr169_formula_owner_rows.py",
        "tests/pr168_rp5e/test_reading_inputs.py",
    ],
)
def test_pr169_qku_formula_repair_allows_exact_shared_owner_currentization(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/map3/unrelated_rows.jsonl",
        "docs/master_plan/generated/rp5c/unregistered_repair_copy.jsonl",
        "tools/build_unrelated_owner.py",
    ],
)
def test_pr169_qku_formula_repair_shared_owner_scope_stays_fail_closed(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "src/qtt/live_connectors/order_client.py",
        "private_state/account_snapshot.json",
        "cash/account.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
    ],
)
def test_pr169_qku_formula_exp1_forbidden_paths_fail_closed(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH, path)


def test_original_formula_branch_does_not_inherit_repair_shared_owner_scope() -> None:
    path = "docs/master_plan/generated/pr169_svc1/service_registry.jsonl"
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_qku_formula_exp1/acceptance.report.json",
        "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/runtime.py",
        "tools/validate_pr169_qku_formula_exp1.py",
        "tests/pr169_qku_formula_exp1/test_runtime.py",
    ],
)
def test_pr169_qku_formula_exp1_scope_is_available_to_validation_fixture(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)
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
        "docs/master_plan/generated/pr169_dash1/owner_dashboard_surface_registry.jsonl",
        "docs/master_plan/generated/pr169_dash1/ui/owner_dashboard_review_surface.html",
        "docs/master_plan/generated/pr169_dash1/ui/ui1r2_next_step.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui/ui1r2_guidance.report.json",
        "src/qtt/dashboard/owner_surface_resolver.py",
        "src/qtt/dashboard/owner_dashboard_projection_builder.py",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/build_pr169_dash1_owner_dashboard.py",
        "tools/build_pr169_dash1_owner_dashboard_ui.py",
        "tools/playwright_pr169_dash1_ui1_r2_visual_smoke.py",
        "tools/playwright_pr169_dash1_ui1_r2_r3_visual_smoke.py",
        "tools/playwright_pr169_dash1_ui1_r2_r4_visual_smoke.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_dash1_owner_dashboard.py",
        "tools/validate_pr169_dash1_owner_dashboard_ui.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_source_fact_binding_connector_semantic_readiness_static.py",
        "tests/pr169_dash1/test_dash1_owner_surface_registry_single_source.py",
        "tests/pr169_dash1_ui1/test_ui1r2_next_step_router_generated.py",
        "tests/pr169_dash1_ui1/test_ui1r2r5_owner_visual_qa_truth_repair.py",
        "tests/pr169_dash1_ui1/r2_contract_assertions.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "docs/master_plan/generated/pr169_dash1/ui1_r2_r5/owner_visual_qa_truth_repair.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2_r5/centralization_manifest.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2r6/truth.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2r6/centralization_manifest.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2r6/playwright_visual_smoke.report.json",
        "tests/pr169_dash1_ui1/test_ui1r2r6_truth.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/source_evidence/test_source_fact_binding_connector_semantic_readiness_static.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    ],
)
def test_pr169_dash1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R2_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R3_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R4_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R5_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_UI1_R2_R6_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "src/qtt/live_connectors/order_client.py",
        "private_state/account_snapshot.json",
        "cash/account.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
    ],
)
def test_pr169_dash1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_DASH1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R1_BRANCH,
        path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R2_BRANCH,
        path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R2_R1_BRANCH,
        path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R2_R3_BRANCH,
        path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R2_R5_BRANCH,
        path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_DASH1_UI1_R2_R6_BRANCH,
        path,
    )


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
        "docs/master_plan/generated/pr169_readiness1/owner_three_question_coverage.report.json",
        "src/qtt/readiness/pr169_readiness1_resolvers.py",
        "tools/build_pr169_readiness1.py",
        "tools/validate_pr169_readiness1.py",
        "tools/changed_area_validation_router.py",
        "tests/pr169_readiness1/test_pr169_readiness1.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    ],
)
def test_pr169_readiness1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_READINESS1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "src/qtt/live_connectors/order_client.py",
        "private_state/account_snapshot.json",
        "cash/account.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/pr169_dash1/owner_action_registry.generated.jsonl",
    ],
)
def test_pr169_readiness1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_READINESS1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl",
        "docs/master_plan/generated/pr169_pretrade1/pretrade_quality_gates.report.json",
        "docs/master_plan/generated/pr169_pretrade1/no_submit_authority.report.json",
        "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "tools/build_pr169_pretrade1.py",
        "tools/validate_pr169_pretrade1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/pr169_pretrade1/test_pr169_pretrade1.py",
    ],
)
def test_pr169_pretrade1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_PRETRADE1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_mem1/context_signature.jsonl",
        "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
        "src/qtt/live_connectors/order_client.py",
        "private_state/account_snapshot.json",
        "cash/account.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
    ],
)
def test_pr169_pretrade1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_PRETRADE1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
        "docs/master_plan/generated/pr169_svc1/service_quality_gates.report.json",
        "docs/master_plan/generated/pr169_svc1/no_runtime_execution.report.json",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "src/qtt/service/__init__.py",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/build_pr169_svc1.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_svc1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/pr169_svc1/test_pr169_svc1.py",
    ],
)
def test_pr169_svc1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_SVC1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl",
        "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
        "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "src/qtt/live_connectors/order_client.py",
        "private_state/account_snapshot.json",
        "cash/account.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
    ],
)
def test_pr169_svc1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_SVC1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/quality.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_qtt_sha.report.json",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "src/qtt/agents/__init__.py",
        "tools/build_pr169_agent_orch1.py",
        "tools/validate_pr169_agent_orch1.py",
        "tools/pr168_rp5c_config.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/pr169_agent_orch1/test_registry_projection_integrity.py",
    ],
)
def test_pr169_agent_orch1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_AGENT_ORCH1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "tools/build_pr169_svc1.py",
        "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/qtt_sha_authority.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_qtt_sha_extra.report.json",
    ],
)
def test_pr169_agent_orch1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_AGENT_ORCH1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/qtt_validation.yml",
        "docs/master_plan/generated/pr169_val1/manifest.json",
        "docs/master_plan/generated/pr169_val1/shards.report.json",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr169_val1.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_val1.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tests/tools/test_qtt_validation_workflow_matrix.py",
        "tests/tools/test_validation_readability_guard.py",
        "tests/tools/test_validation_shard_partition.py",
        "tests/tools/test_validation_timing_artifacts.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
    ],
)
def test_pr169_val1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR169_VAL1_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "src/qtt/live_connectors/fake.py",
        "docs/master_plan/generated/pr169_val1/future_hint.jsonl",
    ],
)
def test_pr169_val1_forbidden_paths_fail(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR169_VAL1_BRANCH, path)


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


@pytest.mark.parametrize(
    "path",
    [
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
    ],
)
def test_pr168_data1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_DATA1A_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_data1a_audit/fetch_inventory_rows.jsonl",
        "docs/master_plan/generated/pr168_data1a_audit/fetch_inventory_rows.manifest.json",
        "tools/build_pr168_data1a_focused_audit.py",
        "tools/pr168_data1a_validator.py",
        "tools/validate_pr168_data1a_focused_audit.py",
        "tests/pr168_data1a/test_pr168_data1a_fetch_inventory_answers_owner_question_a.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_data1a_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_gfp2r_candidate_compute/formula_variant_rows.jsonl",
        "docs/master_plan/generated/pr168_gfp2r_candidate_compute/formula_execution_rows.manifest.json",
        "tools/build_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/pr168_gfp2r_candidate_formula_executor.py",
        "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tests/pr168_gfp2r/test_pr168_gfp2r_candidate_numeric_evidence_is_non_proof.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_gfp2r_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP2_Final.report.json",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/rp2p/replay_exec.jsonl",
        "docs/master_plan/generated/rp2p/replay_exec.manifest.json",
        "tools/build_pr168_rp2_map2.py",
        "tools/pr168_rp2_engine.py",
        "tools/validate_pr168_rp2_map2.py",
        "tests/pr168_rp2/test_numeric_pnl.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rp2_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_MAP3_OnlineScout.report.json",
        "docs/master_plan/generated/PR168_MAP3_FinalSummary.report.json",
        "docs/master_plan/generated/map3/online_scout_rows.jsonl",
        "docs/master_plan/generated/map3/online_scout_rows.jsonl.manifest.json",
        "tools/build_pr168_map3.py",
        "tools/pr168_map3_online_scout.py",
        "tools/validate_pr168_map3.py",
        "tests/pr168_map3/test_online_scout.py",
        "tools/validation_scope_registry.py",
    ],
)
def test_pr168_map3_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP3_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP3_MarketInstantiation.report.json",
        "docs/master_plan/generated/rp3/replay_rows.jsonl",
        "docs/master_plan/generated/rp3/replay_rows.manifest.json",
        "tools/build_pr168_rp3.py",
        "tools/pr168_rp3_dag_orchestrator.py",
        "tools/validate_pr168_rp3.py",
        "tests/pr168_rp3/test_replay_pnl.py",
        "tools/validation_scope_registry.py",
    ],
)
def test_pr168_rp3_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RANK3_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RANK3_FeatureMatrix.report.json",
        "docs/master_plan/generated/rank3/feature_matrix_rows.jsonl",
        "docs/master_plan/generated/rank3/feature_matrix_rows.manifest.json",
        "tools/build_pr168_rank3.py",
        "tools/pr168_rank3_dag_orchestrator.py",
        "tools/validate_pr168_rank3.py",
        "tests/pr168_rank3/test_feature_matrix.py",
        "tools/validation_scope_registry.py",
    ],
)
def test_pr168_rank3_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RANK3_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5A_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5A_LegacyFileSemanticAudit.report.json",
        "docs/master_plan/generated/rp5a/legacy_file_semantic_rows.jsonl",
        "docs/master_plan/generated/rp5a/legacy_file_semantic_rows.manifest.json",
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/pr168_rp5a_config.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        "tests/pr168_rp5a/test_final_summary_counts.py",
        "tools/validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    ],
)
def test_pr168_rp5a_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5B_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json",
        "docs/master_plan/generated/rp5b/active_artifact_registry_rows.jsonl",
        "docs/master_plan/generated/rp5b/active_artifact_registry_rows.manifest.json",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/pr168_rp5b_config.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tests/pr168_rp5b/test_final_summary_counts.py",
        "tools/validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    ],
)
def test_pr168_rp5b_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5C_ImmutableQKUFormulaLibrary.report.json",
        "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
        "docs/master_plan/generated/rp5c/immutable_qku_formula_library.manifest.json",
        "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_rp5c_immutable_qku_formula_library.py",
        "tests/pr168_rp5c/test_rp5c_immutable_libraries.py",
        "tools/validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    ],
)
def test_pr168_rp5c_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(
        PR168_RP5C_POST_MERGE_REPAIR_BRANCH,
        path,
    )
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_vs1/trade_plan_candidates.jsonl",
        "docs/master_plan/generated/pr168_vs1/trade_plan_candidates.manifest.json",
        "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/validator.py",
        "tools/run_pr168_vs1_trading_intelligence_slice.py",
        "tools/validate_pr168_vs1_trading_intelligence_slice.py",
        "tools/pr168_rp5c_config.py",
        "tests/pr168_vs1/test_vs1_validation.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_vs1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_VS1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_name_registry.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/runner.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py",
        "tools/build_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
        "tests/pr168_rp5d/test_rp5d_validation.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rp5d_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5e/art_reg.json",
        "docs/master_plan/generated/pr168_rp5e/topk.jsonl",
        "docs/master_plan/generated/pr168_rp5e/topk.manifest.json",
        "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/runner.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/validator.py",
        "tools/build_pr168_rp5e_stack_gen.py",
        "tools/validate_pr168_rp5e_stack_gen.py",
        "tests/pr168_rp5e/test_validation.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
    ],
)
def test_pr168_rp5e_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5E_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5d_r1/art_reg.json",
        "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.manifest.json",
        "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/runner.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/validator.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py",
        "tools/build_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/validate_pr168_rp5d_r1_exec_now_unlock.py",
        "tests/pr168_rp5d_r1/test_validation.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rp5d_r1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_R1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5f/art_reg.json",
        "docs/master_plan/generated/pr168_rp5f/targets.jsonl",
        "docs/master_plan/generated/pr168_rp5f/trade_seed.manifest.json",
        "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/runner.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/validator.py",
        "tools/build_pr168_rp5f_dynamic_targets.py",
        "tools/validate_pr168_rp5f_dynamic_targets.py",
        "tools/pr168_rp5c_config.py",
        "tests/pr168_rp5f/test_validation.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rp5f_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RP5F_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
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
        "tools/pr168_rp5c_config.py",
        "tests/pr168_rank4/test_rank4_builder.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_rank4_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_RANK4_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_qopt1/art_reg.json",
        "docs/master_plan/generated/pr168_qopt1/batch_select.jsonl",
        "docs/master_plan/generated/pr168_qopt1/batch_select.manifest.json",
        "docs/master_plan/generated/pr168_qopt1/run_receipt.report.json",
        "docs/master_plan/generated/pr168_qopt1/pr_body.md",
        "src/qtt/optimization/__init__.py",
        "src/qtt/optimization/pr168_qopt1/builder.py",
        "src/qtt/optimization/pr168_qopt1/validator.py",
        "tools/build_pr168_qopt1_batch_optimization.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_qopt1_batch_optimization.py",
        "tests/pr168_qopt1/test_qopt1_builder.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_qopt1_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_QOPT1_BRANCH, path)
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_vs2/art_reg.json",
        "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",
        "docs/master_plan/generated/pr168_vs2/paper_loop_contract.jsonl",
        "docs/master_plan/generated/pr168_vs2/pr_body.md",
        "src/qtt/paper/__init__.py",
        "src/qtt/paper/pr168_vs2/builder.py",
        "src/qtt/paper/pr168_vs2/validator.py",
        "tools/build_pr168_vs2_paper_intent_candidates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_vs2_paper_intent_candidates.py",
        "tests/pr168_vs2/test_vs2_builder.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/run_validation_gates.py",
    ],
)
def test_pr168_vs2_allowed_paths_pass_on_real_branch(path: str) -> None:
    assert registry.is_pr_scoped_changed_path_allowed(PR168_VS2_BRANCH, path)
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
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_VS1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5E_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK4_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_VS2_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
        "tools/pr168_rp5c_validator.py",
        "tests/pr168_rp5c/test_rp5c_no_global_ban_no_orphan.py",
    ],
)
def test_other_pr168_branches_reject_rp5c_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_VS1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_vs1/trade_plan_candidates.jsonl",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/validate_pr168_vs1_trading_intelligence_slice.py",
        "tests/pr168_vs1/test_vs1_no_pnl_forcing.py",
    ],
)
def test_other_pr168_branches_reject_vs1_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/runner.py",
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
        "tests/pr168_rp5d/test_rp5d_validation.py",
    ],
)
def test_other_pr168_branches_reject_rp5d_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_VS1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5E_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr168_rp5e/topk.jsonl",
        "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/runner.py",
        "tools/validate_pr168_rp5e_stack_gen.py",
        "tests/pr168_rp5e/test_validation.py",
    ],
)
def test_other_pr168_branches_reject_rp5e_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_VS1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5D_BRANCH, path)


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
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json",
        "tools/pr168_gfp2r_quantum_structural_candidate_map.py",
        "tests/pr168_gfp2r/test_pr168_gfp2r_quantum_no_backend_no_advantage.py",
    ],
)
def test_other_pr168_branches_reject_gfp2r_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_MAP3_FinalSummary.report.json",
        "tools/pr168_map3_online_scout.py",
        "tests/pr168_map3/test_no_authority.py",
    ],
)
def test_other_pr168_branches_reject_map3_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP2_Final.report.json",
        "tools/pr168_rp2_engine.py",
        "tests/pr168_rp2/test_quantum_no_backend.py",
    ],
)
def test_other_pr168_branches_reject_rp2_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP3_FinalSummary.report.json",
        "tools/pr168_rp3_dag_orchestrator.py",
        "tests/pr168_rp3/test_replay_pnl.py",
    ],
)
def test_other_pr168_branches_reject_rp3_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5A_FinalSummary.report.json",
        "tools/pr168_rp5a_validator.py",
        "tests/pr168_rp5a/test_no_deletion_or_archive.py",
    ],
)
def test_other_pr168_branches_reject_rp5a_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5B_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5C_BRANCH, path)


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/PR168_RP5B_FinalSummary.report.json",
        "tools/pr168_rp5b_validator.py",
        "tests/pr168_rp5b/test_no_raw_legacy_decision_authority.py",
    ],
)
def test_other_pr168_branches_reject_rp5b_scope_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_DATA1A_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_GFP2R_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP2_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_MAP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP3_BRANCH, path)
    assert not registry.is_pr_scoped_changed_path_allowed(PR168_RP5A_BRANCH, path)


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
