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
PR169_VAL1_BRANCH = registry.PR169_VAL1_BRANCH
PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH = registry.PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH
FIXTURE_BRANCH = registry.VALIDATION_FIXTURE_BRANCH
REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ST12B_ALLOWED_EXACT_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/contextual_computability.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/stack_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/unit_conversion.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dependency_graph.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_runtime_topology.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_manifest_and_ownership.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_math_oracle_vectors.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_resolution_pipeline.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operations.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_source_quantum_model_risk.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/build_qku_computation_control_plane.py",
        "tools/changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/independent_validate_qku_computation_control_plane_latency.py",
        "tools/independent_validate_qku_computation_control_plane_model_risk.py",
        "tools/independent_validate_qku_computation_control_plane_operations.py",
        "tools/independent_validate_qku_computation_control_plane_source.py",
        "tools/run_validation_gates.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
ST12C_PREDECESSOR_CURRENTIZATION_PATHS = frozenset(
    {
        "tests/atomicrows/test_source_backed_classical_quantum_parameter_default_target_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_runtime_topology.py",
        "tools/independent_validate_qku_computation_control_plane_operations.py",
    }
)
EXPECTED_ST12C_ALLOWED_EXACT_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/idempotency.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/lifecycle.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/migrations.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/outbox.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/rollback.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/sqlite_reference.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/transaction.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/accounting/__init__.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/accounting/test_contract_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/execution/__init__.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/execution/test_contract_matrix.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/build_qku_computation_control_plane.py",
        "tools/changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/independent_validate_qku_computation_control_plane_accounting.py",
        "tools/independent_validate_qku_computation_control_plane_execution.py",
        "tools/run_validation_gates.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
) | ST12C_PREDECESSOR_CURRENTIZATION_PATHS
ST12E_PREDECESSOR_CURRENTIZATION_PATHS = frozenset(
    {
        "tests/stage1_prediction_markets/"
        "qku_computation_control_plane/"
        "tranche_b/test_service_operations.py",
    }
)
EXPECTED_ST12E_ALLOWED_EXACT_PATHS = frozenset(
    {
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "docs/master_plan/generated/qku_control_plane/agent_capability/manifest.json",
        "docs/master_plan/generated/qku_control_plane/agent_capability/policy.jsonl",
        "docs/master_plan/generated/qku_control_plane/agent_capability/parameter_scope.jsonl",
        "tools/build_qku_computation_control_plane.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/independent_validate_qku_computation_control_plane_e.py",
        "tools/independent_validate_qku_computation_control_plane_agent.py",
        "tools/independent_validate_qku_computation_control_plane_llm.py",
        "tools/independent_validate_qku_computation_control_plane_security.py",
        "tools/independent_validate_qku_computation_control_plane.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/__init__.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_policy_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_integration_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_adversarial_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_consume_not_rebuild.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_operation_contract_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_runtime_topology.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
) | ST12E_PREDECESSOR_CURRENTIZATION_PATHS

EXPECTED_ST12D_ALLOWED_EXACT_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/contextual_computability.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/mode_snapshot_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/stack_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_policy_state_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_integration_snapshot_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_adversarial_latency_security_matrix.py",
        "tools/independent_validate_qku_computation_control_plane_d.py",
        "tools/independent_validate_qku_computation_control_plane.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/build_qku_computation_control_plane.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/manifest.json",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/control_closure.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/parameter_binding_refs.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/mode_state_registry.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/transition_matrix.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/d_input_universe.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/computability_dispositions.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/artifact_connectivity.jsonl",
        "docs/master_plan/generated/qku_control_plane/mode_snapshot/validation_summary.json",
    }
)

PR169_QKU_FORMULA_EXP1_PR272_PATHS = (
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    "docs/master_plan/generated/pr169_qku_formula_exp1/acceptance.report.json",
    "docs/master_plan/generated/pr169_qku_formula_exp1/bindings.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/family_j_receipts.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/integration.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/manifest.json",
    "docs/master_plan/generated/pr169_qku_formula_exp1/objects.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/policy.json",
    "docs/master_plan/generated/pr169_qku_formula_exp1/reading.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/requirements.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/sources.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/strategies.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/tool_manifest.jsonl",
    "docs/master_plan/generated/pr169_qku_formula_exp1/validator_rules.jsonl",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/__init__.py",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/catalog.py",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/family_j.py",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/objects.py",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/policy.py",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/runtime.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    "tests/pr169_qku_formula_exp1/__init__.py",
    "tests/pr169_qku_formula_exp1/test_contracts.py",
    "tests/pr169_qku_formula_exp1/test_family_j.py",
    "tests/pr169_qku_formula_exp1/test_runtime.py",
    "tests/tools/test_validation_scope_registry.py",
    "tools/build_pr169_qku_formula_exp1.py",
    "tools/pr168_rp5c_config.py",
    "tools/run_validation_gates.py",
    "tools/validate_pr169_qku_formula_exp1.py",
    "tools/validation_inventory.py",
    "tools/validation_scope_registry.py",
)

PR169_QKU_FORMULA_EXP1_ROLLBACK_CORRECTION_PATHS = (
    "tools/pr168_rp5b_validator.py",
    "tests/pr168_rp5b/test_deleted_manifest_matches_git_deletions.py",
)

PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATHS = (
    *PR169_QKU_FORMULA_EXP1_PR272_PATHS,
    *PR169_QKU_FORMULA_EXP1_ROLLBACK_CORRECTION_PATHS,
)


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


def test_pr169_qku_formula_exp1_rollback_scope_is_exactly_owned_universe() -> None:
    assert len(PR169_QKU_FORMULA_EXP1_PR272_PATHS) == 33
    assert registry._PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATTERNS == ()
    assert registry._PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_EXACT_PATHS == frozenset(
        PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATHS
    )


def test_st12a_scope_is_exactly_the_authorized_path_allowlist() -> None:
    assert registry.ST12A_BRANCH == "agent/st12a-contract-envelope"
    assert len(registry.ST12A_ALLOWED_EXACT_PATHS) == 79
    assert {
        "tests/tools/test_ci_branch_context.py",
        "tools/ci_branch_context.py",
    } <= registry.ST12A_ALLOWED_EXACT_PATHS
    assert all(
        registry.explain_pr_scope_decision(
            registry.ST12A_BRANCH,
            path,
        )
        == {
            "allowed": True,
            "branch": registry.ST12A_BRANCH,
            "normalized_path": path,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"exact:{path}",
            "reason": "registered_exact_path",
        }
        for path in registry.ST12A_ALLOWED_EXACT_PATHS
    )


def test_st12a_shared_currentization_scope_is_separate_and_exact() -> None:
    paths = frozenset(
        {
            (
                "docs/master_plan/generated/"
                "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
            ),
            (
                "docs/master_plan/generated/"
                "PR168_RP5A_FinalSummary.report.json"
            ),
            (
                "docs/master_plan/generated/"
                "PR168_RP5A_NoDeletionProof.report.json"
            ),
            "tests/pr168_rp5a/test_no_validation_scope_removal.py",
            "tools/build_pr168_rp5a_legacy_semantic_audit.py",
            "tools/pr168_rp5a_validator.py",
        }
    )
    assert registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS == paths
    for path in paths:
        assert path not in registry.ST12A_ALLOWED_EXACT_PATHS
        assert registry.explain_pr_scope_decision(
            registry.ST12A_BRANCH,
            path,
        ) == {
            "allowed": True,
            "branch": registry.ST12A_BRANCH,
            "normalized_path": path,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"shared_currentization_exact:{path}",
            "reason": "registered_shared_currentization_exact_path",
        }
        assert registry.explain_pr_scope_decision(
            FIXTURE_BRANCH,
            path,
        ) == {
            "allowed": True,
            "branch": FIXTURE_BRANCH,
            "normalized_path": path,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": (
                "validation_context_shared_currentization_exact:"
                f"{path}"
            ),
            "reason": (
                "registered_validation_context_shared_currentization_exact_path"
            ),
        }
        windows_path = ".\\" + path.replace("/", "\\")
        assert registry.is_pr_scoped_changed_path_allowed(
            registry.ST12A_BRANCH,
            windows_path,
        )
        assert registry.is_pr_scoped_changed_path_allowed(
            FIXTURE_BRANCH,
            windows_path,
        )
        assert not registry.is_pr_scoped_changed_path_allowed(
            registry.ST12A_BRANCH,
            f"{path}.copy",
        )
        assert not registry.is_pr_scoped_changed_path_allowed(
            FIXTURE_BRANCH,
            f"{path}.copy",
        )


@pytest.mark.parametrize("path", sorted(registry.ST12A_ALLOWED_EXACT_PATHS))
def test_st12a_exact_scope_is_consumable_by_validation_context(path: str) -> None:
    decision = registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
    assert decision == {
        "allowed": True,
        "branch": FIXTURE_BRANCH,
        "normalized_path": path,
        "pr_id": "ST12-TRANCHE-A",
        "matched_rule": f"validation_context_exact:{path}",
        "reason": "registered_validation_context_exact_path",
    }
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, windows_path)


def test_st12b_exact_44_path_scope_matches_owner_freeze() -> None:
    assert registry.ST12B_BRANCH == "agent/st12b-contextual-computability-v3"
    assert registry.ST12B_ALLOWED_EXACT_PATHS == EXPECTED_ST12B_ALLOWED_EXACT_PATHS
    assert len(registry.ST12B_ALLOWED_EXACT_PATHS) == 44


def test_st12b_validation_context_routes_only_exclusive_exact_paths() -> None:
    expected = frozenset(
        {
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/contextual_computability.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/stack_resolver.py",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/unit_conversion.py",
            "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_manifest_and_ownership.py",
            "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_math_oracle_vectors.py",
            "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_resolution_pipeline.py",
            "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operations.py",
            "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_source_quantum_model_risk.py",
            "tools/independent_validate_qku_computation_control_plane_latency.py",
            "tools/independent_validate_qku_computation_control_plane_model_risk.py",
        }
    )
    shared_pr152 = (
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    )
    assert registry.ST12B_BRANCH == "agent/st12b-contextual-computability-v3"
    assert registry.is_validation_context_branch(FIXTURE_BRANCH)
    assert not registry.is_validation_context_branch(registry.ST12B_BRANCH)
    assert not registry.is_validation_context_branch(f"{FIXTURE_BRANCH}-copy")
    assert len(expected) == 15
    assert registry.ST12B_VALIDATION_CONTEXT_EXACT_PATHS == expected
    assert registry.ST12B_VALIDATION_CONTEXT_EXACT_PATHS == (
        registry.ST12B_ALLOWED_EXACT_PATHS
        - (
            registry.ST12A_ALLOWED_EXACT_PATHS
            | registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
        )
    )
    assert shared_pr152 not in registry.ST12B_VALIDATION_CONTEXT_EXACT_PATHS
    assert shared_pr152 in registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
    assert registry.explain_pr_scope_decision(
        FIXTURE_BRANCH,
        shared_pr152,
    ) == {
        "allowed": True,
        "branch": FIXTURE_BRANCH,
        "normalized_path": shared_pr152,
        "pr_id": "ST12-TRANCHE-A",
        "matched_rule": (
            "validation_context_shared_currentization_exact:"
            f"{shared_pr152}"
        ),
        "reason": (
            "registered_validation_context_shared_currentization_exact_path"
        ),
    }
    for path in sorted(expected):
        decision = {
            "allowed": True,
            "branch": FIXTURE_BRANCH,
            "normalized_path": path,
            "pr_id": "ST12-TRANCHE-B",
            "matched_rule": f"validation_context_exact:{path}",
            "reason": "registered_validation_context_exact_path",
        }
        assert registry.explain_pr_scope_decision(FIXTURE_BRANCH, path) == decision
        windows_path = ".\\" + path.replace("/", "\\")
        assert (
            registry.explain_pr_scope_decision(FIXTURE_BRANCH, windows_path)
            == decision
        )
        assert not registry.is_pr_scoped_changed_path_allowed(
            FIXTURE_BRANCH,
            f"{path}.copy",
        )


@pytest.mark.parametrize("path", sorted(EXPECTED_ST12B_ALLOWED_EXACT_PATHS))
def test_st12b_exact_paths_and_windows_forms_are_allowed(path: str) -> None:
    decision = registry.explain_pr_scope_decision(registry.ST12B_BRANCH, path)
    assert decision == {
        "allowed": True,
        "branch": registry.ST12B_BRANCH,
        "normalized_path": path,
        "pr_id": "ST12-TRANCHE-B",
        "matched_rule": f"exact:{path}",
        "reason": "registered_exact_path",
    }
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.is_pr_scoped_changed_path_allowed(
        registry.ST12B_BRANCH,
        windows_path,
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        registry.ST12B_BRANCH,
        f"{path}.copy",
    )


@pytest.mark.parametrize(
    "path",
    [
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_01.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_extra.py",
        "tools/validate_qku_computation_control_plane_extra.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        ".tmp/qku-output.json",
    ],
)
def test_st12b_scope_rejects_prefix_wildcards_and_unowned_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(
        registry.ST12B_BRANCH,
        path,
    )


def test_st12b_scope_requires_exact_branch() -> None:
    path = (
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "contextual_computability.py"
    )
    for branch in (
        "agent/st12b-contextual-computability",
        "agent/st12b-contextual-computability-v3-copy",
        "agent/st12b-contextual-computability-v3/",
        "Agent/st12b-contextual-computability-v3",
    ):
        assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


def test_st12c_exact_scope_matches_owner_currentization() -> None:
    assert registry.ST12C_BRANCH == (
        "agent/st12c-deterministic-receipts-accounting-v1"
    )
    assert registry.ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS == (
        ST12C_PREDECESSOR_CURRENTIZATION_PATHS
    )
    assert registry.ST12C_ALLOWED_EXACT_PATHS == EXPECTED_ST12C_ALLOWED_EXACT_PATHS
    assert not any("*" in path for path in registry.ST12C_ALLOWED_EXACT_PATHS)
    assert registry.ST12C_VALIDATION_CONTEXT_EXACT_PATHS == (
        registry.ST12C_ALLOWED_EXACT_PATHS
        - (
            registry.ST12A_ALLOWED_EXACT_PATHS
            | registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
            | registry.ST12B_ALLOWED_EXACT_PATHS
            | registry.ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
        )
    )
    assert ST12C_PREDECESSOR_CURRENTIZATION_PATHS <= (
        registry.ST12C_ALLOWED_EXACT_PATHS
    )
    assert ST12C_PREDECESSOR_CURRENTIZATION_PATHS.isdisjoint(
        registry.ST12C_VALIDATION_CONTEXT_EXACT_PATHS
    )
    for path in ST12C_PREDECESSOR_CURRENTIZATION_PATHS:
        decision = registry.explain_pr_scope_decision(registry.ST12C_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-C"
    fixture_decisions = {
        path: registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
        for path in ST12C_PREDECESSOR_CURRENTIZATION_PATHS
    }
    assert all(decision["allowed"] is True for decision in fixture_decisions.values())
    atomicrows_path = (
        "tests/atomicrows/"
        "test_source_backed_classical_quantum_parameter_default_target_matrix.py"
    )
    assert fixture_decisions[atomicrows_path] == {
        "allowed": True,
        "branch": FIXTURE_BRANCH,
        "normalized_path": atomicrows_path,
        "pr_id": "ST12-TRANCHE-C",
        "matched_rule": (
            "validation_context_predecessor_currentization_exact:"
            f"{atomicrows_path}"
        ),
        "reason": (
            "registered_validation_context_"
            "predecessor_currentization_exact_path"
        ),
    }
    for path in ST12C_PREDECESSOR_CURRENTIZATION_PATHS - {atomicrows_path}:
        assert fixture_decisions[path] == {
            "allowed": True,
            "branch": FIXTURE_BRANCH,
            "normalized_path": path,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"validation_context_exact:{path}",
            "reason": "registered_validation_context_exact_path",
        }
    for near_path in (f"{atomicrows_path}.copy", f"{atomicrows_path}.suffix"):
        assert registry.explain_pr_scope_decision(
            FIXTURE_BRANCH,
            near_path,
        )["allowed"] is False
    for path in registry.ST12C_VALIDATION_CONTEXT_EXACT_PATHS:
        decision = registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-C"


@pytest.mark.parametrize("path", sorted(EXPECTED_ST12C_ALLOWED_EXACT_PATHS))
def test_st12c_exact_paths_and_windows_forms_are_allowed(path: str) -> None:
    assert registry.explain_pr_scope_decision(registry.ST12C_BRANCH, path) == {
        "allowed": True,
        "branch": registry.ST12C_BRANCH,
        "normalized_path": path,
        "pr_id": "ST12-TRANCHE-C",
        "matched_rule": f"exact:{path}",
        "reason": "registered_exact_path",
    }
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.is_pr_scoped_changed_path_allowed(
        registry.ST12C_BRANCH,
        windows_path,
    )


@pytest.mark.parametrize(
    ("branch", "path"),
    [
        (
            registry.ST12C_BRANCH,
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py",
        ),
        (
            registry.ST12C_BRANCH,
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py.copy",
        ),
        (
            "agent/st12c-deterministic-receipts-accounting",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        ),
        (
            "agent/st12c-deterministic-receipts-accounting-v1-copy",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        ),
        (
            "agent/st12c-deterministic-receipts-accounting-v1/",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        ),
        (
            "Agent/st12c-deterministic-receipts-accounting-v1",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        ),
    ],
    ids=(
        "unowned-path",
        "path-suffix",
        "branch-version-missing",
        "branch-suffix",
        "branch-trailing-slash",
        "branch-case-change",
    ),
)
def test_st12c_scope_rejects_unowned_paths_and_near_names(
    branch: str,
    path: str,
) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


def test_st12e_scope_is_exactly_the_appendix_h_ledger() -> None:
    assert registry.ST12E_BRANCH == "agent/st12e-capability-guard"
    assert registry.ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS == (
        ST12E_PREDECESSOR_CURRENTIZATION_PATHS
    )
    assert registry.ST12E_ALLOWED_EXACT_PATHS == (
        EXPECTED_ST12E_ALLOWED_EXACT_PATHS
    )
    assert len(registry.ST12E_ALLOWED_EXACT_PATHS) == 40
    assert registry.ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS <= (
        registry.ST12E_ALLOWED_EXACT_PATHS
    )
    assert not any("*" in path for path in registry.ST12E_ALLOWED_EXACT_PATHS)


def test_st12e_validation_context_routes_only_exclusive_exact_paths() -> None:
    expected = registry.ST12E_ALLOWED_EXACT_PATHS - (
        registry.ST12A_ALLOWED_EXACT_PATHS
        | registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
        | registry.ST12B_ALLOWED_EXACT_PATHS
        | registry.ST12C_ALLOWED_EXACT_PATHS
        | registry.ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
    )

    assert len(expected) == 12
    assert registry.ST12E_VALIDATION_CONTEXT_EXACT_PATHS == expected
    assert registry.ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS.isdisjoint(
        registry.ST12E_VALIDATION_CONTEXT_EXACT_PATHS
    )
    for path in expected:
        assert registry.is_pr_scoped_changed_path_allowed(FIXTURE_BRANCH, path)
        assert not registry.is_pr_scoped_changed_path_allowed(
            f"{FIXTURE_BRANCH}-copy", path
        )


@pytest.mark.parametrize("path", sorted(EXPECTED_ST12E_ALLOWED_EXACT_PATHS))
def test_st12e_exact_paths_and_windows_forms_are_allowed(path: str) -> None:
    assert registry.explain_pr_scope_decision(registry.ST12E_BRANCH, path) == {
        "allowed": True,
        "branch": registry.ST12E_BRANCH,
        "normalized_path": path,
        "pr_id": "ST12-TRANCHE-E",
        "matched_rule": f"exact:{path}",
        "reason": "registered_exact_path",
    }
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.is_pr_scoped_changed_path_allowed(
        registry.ST12E_BRANCH, windows_path
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        registry.ST12E_BRANCH, f"{path}.copy"
    )


@pytest.mark.parametrize(
    ("branch", "path"),
    (
        (
            registry.ST12E_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "qku_computation_control_plane/runtime.py",
        ),
        (
            registry.ST12E_BRANCH,
            "docs/master_plan/QTT_MasterPlan_Current.md",
        ),
        (
            registry.ST12E_BRANCH,
            "tests/stage1_prediction_markets/"
            "qku_computation_control_plane/tranche_e/test_extra.py",
        ),
        (
            "agent/st12e-capability",
            "src/qtt/stage1_prediction_markets/"
            "qku_computation_control_plane/agent_policy.py",
        ),
        (
            "agent/st12e-capability-guard-copy",
            "src/qtt/stage1_prediction_markets/"
            "qku_computation_control_plane/agent_policy.py",
        ),
        (
            "Agent/st12e-capability-guard",
            "src/qtt/stage1_prediction_markets/"
            "qku_computation_control_plane/agent_policy.py",
        ),
    ),
)
def test_st12e_scope_rejects_unowned_paths_and_near_branches(
    branch: str, path: str
) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


def test_st12d_scope_is_exactly_the_46_writable_ledger_paths() -> None:
    assert registry.ST12D_BRANCH == "agent/st12d-mode-snapshot-boundary"
    assert registry.ST12D_ALLOWED_EXACT_PATHS == EXPECTED_ST12D_ALLOWED_EXACT_PATHS
    assert len(registry.ST12D_ALLOWED_EXACT_PATHS) == 46
    assert not any("*" in path for path in registry.ST12D_ALLOWED_EXACT_PATHS)
    assert registry.ST12D_VALIDATION_CONTEXT_EXACT_PATHS == (
        registry.ST12D_ALLOWED_EXACT_PATHS
        - (
            registry.ST12A_ALLOWED_EXACT_PATHS
            | registry.ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
            | registry.ST12B_ALLOWED_EXACT_PATHS
            | registry.ST12C_ALLOWED_EXACT_PATHS
            | registry.ST12E_ALLOWED_EXACT_PATHS
        )
    )
    for path in registry.ST12D_VALIDATION_CONTEXT_EXACT_PATHS:
        decision = registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-D"


@pytest.mark.parametrize("path", sorted(EXPECTED_ST12D_ALLOWED_EXACT_PATHS))
def test_st12d_exact_paths_and_windows_forms_are_allowed(path: str) -> None:
    assert registry.explain_pr_scope_decision(registry.ST12D_BRANCH, path) == {
        "allowed": True,
        "branch": registry.ST12D_BRANCH,
        "normalized_path": path,
        "pr_id": "ST12-TRANCHE-D",
        "matched_rule": f"exact:{path}",
        "reason": "registered_exact_path",
    }
    assert registry.is_pr_scoped_changed_path_allowed(
        registry.ST12D_BRANCH,
        ".\\" + path.replace("/", "\\"),
    )
    assert not registry.is_pr_scoped_changed_path_allowed(
        registry.ST12D_BRANCH,
        f"{path}.copy",
    )


@pytest.mark.parametrize(
    ("branch", "path"),
    (
        (
            registry.ST12D_BRANCH,
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py",
        ),
        (
            registry.ST12D_BRANCH,
            "tests/stage1_prediction_markets/qku_computation_control_plane/test_mode_extra.py",
        ),
        (
            "agent/st12d-mode-snapshot",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        ),
        (
            "agent/st12d-mode-snapshot-boundary-copy",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        ),
        (
            "Agent/st12d-mode-snapshot-boundary",
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        ),
    ),
)
def test_st12d_scope_rejects_read_only_unowned_and_near_names(
    branch: str, path: str
) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


@pytest.mark.parametrize(
    ("branch", "path"),
    [
        (
            "pr-ci-fastfail-validation-context-preflight-copy",
            "tools/ci_branch_context.py",
        ),
        (
            FIXTURE_BRANCH,
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py",
        ),
        (
            FIXTURE_BRANCH,
            "docs/master_plan/QTT_MasterPlan_Current.md",
        ),
        (
            registry.ST12A_BRANCH,
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json.copy",
        ),
    ],
)
def test_st12a_validation_context_scope_remains_exact(
    branch: str,
    path: str,
) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


@pytest.mark.parametrize(
    "path",
    [
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_01.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_extra.py",
        "tools/validate_qku_computation_control_plane_extra.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        ".tmp/qku-output.json",
    ],
)
def test_st12a_scope_rejects_prefix_wildcards_and_unowned_paths(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(
        registry.ST12A_BRANCH,
        path,
    )


def test_st12a_scope_requires_exact_branch_and_normalizes_windows_paths() -> None:
    path = (
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "security/test_secret_isolation.py"
    )
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.is_pr_scoped_changed_path_allowed(
        registry.ST12A_BRANCH,
        windows_path,
    )
    for branch in (
        "agent/st12a-contract-envelope-2",
        "ST12-TRANCHE-A",
        "feature/st12a",
    ):
        assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


@pytest.mark.parametrize("path", PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATHS)
def test_pr169_qku_formula_exp1_rollback_owned_paths_are_allowed(path: str) -> None:
    decision = registry.explain_pr_scope_decision(
        PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH,
        path,
    )
    assert decision["allowed"] is True
    assert decision["pr_id"] == "PR169-QKU-FORMULA-EXP1-ROLLBACK"
    assert decision["matched_rule"] == f"exact:{path}"


@pytest.mark.parametrize("path", PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATHS)
def test_pr169_qku_formula_exp1_rollback_paths_are_denied_on_other_branches(path: str) -> None:
    for branch in ("feature/unrelated", "pr169-qku-formula-exp1"):
        assert not registry.is_pr_scoped_changed_path_allowed(branch, path)


def test_pr169_qku_formula_exp1_rollback_specific_path_is_not_exposed_to_fixture_branch() -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(
        FIXTURE_BRANCH,
        "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/runtime.py",
    )


@pytest.mark.parametrize("path", PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATHS)
def test_pr169_qku_formula_exp1_rollback_windows_and_posix_paths_match(path: str) -> None:
    windows_path = ".\\" + path.replace("/", "\\")
    assert registry.normalize_changed_path(windows_path) == path
    assert registry.is_pr_scoped_changed_path_allowed(
        PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH,
        windows_path,
    )
    assert registry.is_pr_scoped_changed_path_allowed(
        PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH,
        path,
    )


@pytest.mark.parametrize(
    "branch",
    [
        "PR169-QKU-FORMULA-EXP1-ROLLBACK",
        "xpr169-qku-formula-exp1-rollback",
        "pr169-qku-formula-exp1-rollback-repair",
        "pr169-qku-formula-exp1-rollback/child",
    ],
)
def test_pr169_qku_formula_exp1_rollback_requires_exact_branch_identity(branch: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(
        branch,
        PR169_QKU_FORMULA_EXP1_PR272_PATHS[0],
    )


@pytest.mark.parametrize(
    "path",
    [
        "docs/master_plan/generated/pr169_qku_formula_exp1/future.report.json",
        "docs/master_plan/generated/pr169_qku_formula_exp1/nested/future.report.json",
        "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/future.py",
        "tests/pr169_qku_formula_exp1/test_future.py",
        "tools/validate_pr169_qku_formula_exp1_extra.py",
        "docs/master_plan/generated/OtherGeneratedReport.report.json",
        "src/qtt/stage1_prediction_markets/other_feature/report.py",
        "tests/random/test_other.py",
        "tools/random_tool.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "../docs/master_plan/generated/pr169_qku_formula_exp1/acceptance.report.json",
    ],
)
def test_pr169_qku_formula_exp1_rollback_rejects_prefix_and_unrelated_leakage(path: str) -> None:
    assert not registry.is_pr_scoped_changed_path_allowed(
        PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH,
        path,
    )


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
def test_st12f_current_main_scope_is_exact_and_fail_closed() -> None:
    assert registry.ST12F_BRANCH == "agent/st12f-evidence-model-risk-v1"
    assert len(registry.ST12F_ALLOWED_EXACT_PATHS) == 82
    assert not any("*" in path for path in registry.ST12F_ALLOWED_EXACT_PATHS)
    added_paths = {
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operations.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_adversarial_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_integration_matrix.py",
    }
    assert added_paths <= registry.ST12F_ALLOWED_EXACT_PATHS
    for path in registry.ST12F_ALLOWED_EXACT_PATHS:
        decision = registry.explain_pr_scope_decision(registry.ST12F_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-F"
        validation_decision = registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
        assert validation_decision["allowed"] is True
    for path in added_paths:
        assert registry.is_pr_scoped_changed_path_allowed(registry.ST12F_BRANCH, path)
        decision = registry.explain_pr_scope_decision(registry.ST12F_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-F"
        assert decision["matched_rule"] == f"exact:{path}"
        assert decision["reason"] == "registered_exact_path"
    for path in {
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operation.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_adversarial_matrix_extra.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_integration_matrix.json",
    }:
        assert path not in registry.ST12F_ALLOWED_EXACT_PATHS
        assert not registry.is_pr_scoped_changed_path_allowed(
            registry.ST12F_BRANCH, path
        )
        decision = registry.explain_pr_scope_decision(registry.ST12F_BRANCH, path)
        assert decision["allowed"] is False
        assert decision["matched_rule"] == "no_st12f_exact_scope_rule"
    for path in {
        "src/qtt/core/testing/gate_result.py",
        "tests/core/test_qtt_cumulative_gate.py",
    }:
        validation_decision = registry.explain_pr_scope_decision(FIXTURE_BRANCH, path)
        assert validation_decision["pr_id"] == "ST12-TRANCHE-F"
    denied = registry.explain_pr_scope_decision(
        registry.ST12F_BRANCH,
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/not_authorized.py",
    )
    assert denied["allowed"] is False
    assert denied["matched_rule"] == "no_st12f_exact_scope_rule"


def test_st12g_authorized_scope_is_exact_and_rejects_near_names() -> None:
    assert registry.ST12G_BRANCH == "agent/st12g-existing-owner-projections-v2"
    assert registry.ST12G_ARCHITECTURE_ADDITIVE_MODULES == (
        "existing_owner_projection.py",
    )
    command = registry.build_st12g_architecture_validation_command("python")
    assert command[:2] == ("python", "-c")
    assert command[2].count("existing_owner_projection.py") == 1
    assert command[2].count("validator.PRODUCTION_NAMES") == 2
    assert len(registry.ST12G_ALLOWED_EXACT_PATHS) == 65
    assert not any("*" in path for path in registry.ST12G_ALLOWED_EXACT_PATHS)
    assert {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py",
        "tools/independent_validate_qku_computation_control_plane_g.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_contract_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_consumer_integration_matrix.py",
        "docs/master_plan/generated/qku_control_plane/existing_owner_projection/st12g_projection_contract_manifest.json",
        "docs/master_plan/generated/pr169_dash1/st12g_evidence_owner_view_contract.generated.jsonl",
    } <= registry.ST12G_ALLOWED_EXACT_PATHS
    for path in registry.ST12G_ALLOWED_EXACT_PATHS:
        decision = registry.explain_pr_scope_decision(registry.ST12G_BRANCH, path)
        assert decision["allowed"] is True
        assert decision["pr_id"] == "ST12-TRANCHE-G"
        assert decision["matched_rule"] == f"exact:{path}"
    for branch in (
        f"{registry.ST12G_BRANCH}-copy",
        registry.ST12G_BRANCH.removesuffix("-v2"),
    ):
        assert not registry.is_pr_scoped_changed_path_allowed(
            branch,
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py",
        )
    denied = registry.explain_pr_scope_decision(
        registry.ST12G_BRANCH,
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dashboard_projection.py",
    )
    assert denied["allowed"] is False
    assert denied["reason"] == "forbidden_path"
