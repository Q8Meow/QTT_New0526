import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from tools import ci_branch_context
from tools import (
    validate_atomicrows_research_provenance_evidence_tier_classification as research_provenance_gate,
)
from tools import (
    validate_atomicrows_owner_submitted_research_source_intake_registry as owner_intake_gate,
)
from tools import (
    validate_atomicrows_research_source_to_candidate_family_gate as candidate_family_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_role_taxonomy as parameter_stack_role_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_completeness_gate as parameter_stack_completeness_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_compatibility_gate as parameter_stack_compatibility_gate,
)
from tools import validate_edge_parameter_stack_selection_packet as edge_packet_gate
from tools import validate_qtt_trade_context_packet as trade_context_gate
from tools import (
    validate_atomicrows_parameter_selection_universe_registry as selection_universe_gate,
)
from tools import (
    validate_atomicrows_parameter_selection_universe_consumer_gate as selection_universe_consumer_gate,
)
from tools import (
    validate_trade_context_selection_universe_routing_gate as trade_context_routing_gate,
)
from tools import (
    validate_quantum_applicability_classification_registry as quantum_applicability_gate,
)
from tools import (
    validate_owner_quantum_priority_policy_registry as owner_quantum_priority_gate,
)
from tools import (
    validate_parameter_algorithm_scoring_policy_registry as scoring_policy_gate,
)
from tools import (
    validate_parameter_stack_scoring_and_ranking_gate as stack_scoring_gate,
)
from tools import (
    validate_quantum_classical_optimizer_arbitration_gate as optimizer_arbitration_gate,
)
from tools import (
    validate_candidate_parameter_stack_generation_gate as candidate_generation_gate,
)
from tools import (
    validate_trade_context_parameter_stack_selection_gate as trade_context_stack_selection_gate,
)
from tools import (
    validate_selected_parameter_stack_handoff_packet as selected_stack_handoff_gate,
)
from tools import (
    validate_replay_paper_candidate_stack_competition_gate as replay_paper_competition_gate,
)
from tools import (
    validate_dual_result_review_for_parameter_stacks as dual_result_review_gate,
)
from tools import (
    validate_owner_live_promotion_review_for_parameter_stacks as owner_live_promotion_review_gate,
)
from tools import (
    validate_owner_approval_request_queue_registry as owner_approval_request_queue_gate,
)
from tools import (
    validate_owner_override_receipt_authoring_gate as owner_override_receipt_authoring_gate,
)
from tools import (
    validate_owner_dashboard_approval_menu_schema as owner_dashboard_approval_menu_schema_gate,
)
from tools import (
    validate_owner_dashboard_approval_static_screen_contract
    as owner_dashboard_approval_static_screen_contract_gate,
)
from tools import (
    validate_atomicrows_full_bundle_row_expansion_plan
    as atomicrows_full_bundle_row_expansion_plan_gate,
)
from tools import (
    validate_atomicrows_bundle_row_family_source_files
    as atomicrows_bundle_row_family_source_files_gate,
)
from tools import (
    validate_atomicrows_bundle_builder_deterministic_assembly_gate
    as atomicrows_bundle_builder_deterministic_assembly_gate,
)
from tools import (
    validate_atomicrows_sha_system_dormancy_state_contract
    as atomicrows_sha_system_dormancy_state_contract,
)
from tools import (
    validate_qtt_final_readiness_dependency_policy_contract
    as qtt_final_readiness_dependency_policy_contract,
)
from tools import (
    validate_qtt_active_non_sha_day1_gate_state_registry_contract
    as qtt_active_non_sha_day1_gate_state_registry_contract,
)
from tools import validate_qtt_pr_identity_roster as qtt_pr_identity_roster
from tools import (
    validate_qtt_roadmap_execution_state_controller
    as qtt_roadmap_execution_state_controller,
)
from tools import (
    validate_atomicrows_bundle_sha_freeze_authority_gate
    as atomicrows_bundle_sha_freeze_authority_gate,
)
from tools import (
    validate_atomicrows_exact_row_authority_classifier_bridge
    as atomicrows_exact_row_authority_classifier_bridge,
)
from tools import (
    validate_atomicrows_owner_approved_exact_15_family_count_distribution
    as atomicrows_owner_approved_exact_15_family_count_distribution,
)
from tools import (
    validate_atomicrows_exact_row_expansion_manifest
    as atomicrows_exact_row_expansion_manifest,
)
from tools import (
    validate_atomicrows_exact_row_generator_dry_run_manifest
    as atomicrows_exact_row_generator_dry_run_manifest,
)
from tools import (
    validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest
    as atomicrows_repair_chain_grand_debug_logic_audit_manifest,
)
from tools import (
    validate_atomicrows_exact_row_source_materialization_manifest
    as atomicrows_exact_row_source_materialization_manifest,
)
from tools import (
    validate_atomicrows_exact_row_agent_family_eligibility_matrix
    as atomicrows_exact_row_agent_family_eligibility_matrix,
)
from tools import (
    validate_atomicrows_bundle_materialization_manifest
    as atomicrows_bundle_materialization_manifest,
)
from tools import (
    validate_atomicrows_bundle_boundary_state_contract
    as atomicrows_bundle_boundary_state_contract,
)
from tools import (
    validate_atomicrows_sha_freeze_final_readiness_state_contract
    as atomicrows_sha_freeze_final_readiness_state_contract,
)
from tools import validate_qtt_agent_algorithm_command_matrix as command_matrix_gate
from tools import (
    validate_pr137_generated_integrity_authority_boundary as pr137_integrity_boundary_gate,
)
from tools import (
    validate_pr137_launch_readiness_dependency_controller as pr137_dependency_controller_gate,
)
from tools import run_validation_gates as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
PR153R_REPAIR_BRANCH = "repair-pr153r-redo-report-determinism"
PR153S_REPAIR_BRANCH = "repair/pr153s-source-value-capture-closure-classifier"
PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH = (
    ci_branch_context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH
)
BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)


def _clear_branch_context_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _env_without_pythonpath() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def _owner_gate_git_metadata_responses(branch: str):
    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, branch, ""
        if command == ("rev-parse", "--short", "HEAD"):
            return 0, "abcdef0", ""
        if (
            len(command) == 3
            and command[:2] == ("cat-file", "-e")
            and command[2].endswith("^{commit}")
        ):
            return 0, "", ""
        if (
            len(command) == 4
            and command[:2] == ("merge-base", "--is-ancestor")
            and command[3] == "HEAD"
        ):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    return fake_git_stdout


def _default_temp_generated_report(filename: str) -> str:
    return str(
        runner._validation_generated_output(
            runner._default_validation_dir(),
            f"docs/master_plan/generated/{filename}",
        )
    )


def test_run_validation_gates_direct_script_imports_router_without_pythonpath():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path("tools") / "run_validation_gates.py"),
            "--phase",
            "fast-preflight",
            "--validation-mode",
            "reduced",
            "--changed-file",
            "docs/master_plan/generated/UnownedGeneratedReport.report.json",
        ],
        cwd=REPO_ROOT,
        env=_env_without_pythonpath(),
        capture_output=True,
        text=True,
        timeout=60,
    )

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 2
    assert "GENERATED_REPORT_OWNER_MISSING" in combined_output
    assert "ModuleNotFoundError" not in combined_output
    assert "No module named 'tools'" not in combined_output


def test_validate_validation_inventory_direct_script_imports_pr208_modules_without_pythonpath():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path("tools") / "validate_validation_inventory.py"),
        ],
        cwd=REPO_ROOT,
        env=_env_without_pythonpath(),
        capture_output=True,
        text=True,
        timeout=60,
    )

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined_output
    assert "VALIDATION_INVENTORY_OK" in completed.stdout
    assert "ModuleNotFoundError" not in combined_output
    assert "No module named 'tools'" not in combined_output


def _expected_commands(
    python_executable: str,
    pytest_basetemp: Path | None = None,
) -> list[list[str]]:
    validation_dir = runner._default_validation_dir()
    if pytest_basetemp is None:
        pytest_basetemp = runner._default_pytest_basetemp()
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    row_family_currentization_report = (
        validation_dir / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
    )
    master_plan = Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    commands = [
        [
            python_executable,
            str(Path("tools") / "master_plan_ingest.py"),
            "--input",
            str(master_plan),
            "--section-manifest-out",
            str(section_manifest),
            "--traceability-out",
            str(traceability_report),
            "--scope-report-out",
            str(first_pr_scope_report),
        ],
        [
            python_executable,
            str(Path("tools") / "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_first_pr_scope.py"),
            "--repo-root",
            ".",
            "--scope-report",
            str(first_pr_scope_report),
            "--block-runtime",
            "--block-live",
            "--block-sha",
            "--block-companion-package",
            "--block-profit-claims",
            "--block-source-retrieval",
            "--block-source-acceptance",
            "--block-connector-binding",
            "--block-private-state-fetch",
            "--block-order-execution",
            "--block-neural-training",
            "--block-neural-inference",
            "--block-external-repo-clone",
            "--block-package-install-scripts",
        ],
        [
            python_executable,
            "-c",
            runner.PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_row_family_source_manifest_currentization.py"
            ),
            "--repo-root",
            ".",
            "--out",
            str(row_family_currentization_report),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_idempotence_runtime_containment.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTOwnerGlobalOverrideAuthority.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_implementation_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_source_backed_classical_quantum_parameter_default_target_matrix.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_official_source_retrieval_target_pack_parameter_defaults.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_grand_global_debug_logical_consistency_audit.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_controlled_official_source_capture_candidate_packets.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr153r_redo_external_source_value_capture_targets.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr153s_source_value_capture_closure_classifier.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_default_value_materialization_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_agent_consumable_parameter_default_registry.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_agent_default_binding_universal_intake_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr158_owner_response_selection_readiness_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159_official_source_completion_bridge.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr160_split_reclassification_route_closure.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159r_source_locator_value_capture.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159s_open_intake_completion.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr161b_master_plan_residual_candidate_coverage.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr161c_qku_residual_candidate_assimilation.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162r_a_replay_paper_executability_classification_audit.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162d_r2a_real_formulations.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162r_generic_replay_paper_adapter_rerun.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162r_b_replay_paper_data_binding_completion.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr163_generic_paper_adapter_capture_framework.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr163_b_paired_replay_paper_concurrent_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_evidence_backed_scoring_ranking.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_b_condition_scoped_negative_memory.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_c_replay_paper_memory_consumer_integration.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d_scenario_qku_combination_selection.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_s_replay_paper_scenario_retest_execution.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sf_repair_materialization_before_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_s2_replay_paper_retest_loop_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sm2_score_memory_refresh_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr166_sm3_score_memory_refresh_v3.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_q_quantum_classical_hybrid_comparator.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr166_qb_bounded_quantum_benchmark.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_q_quantum_automapper.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr167_open_trade_simulator_integration.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_plugin_framework.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_negative_repair_factory.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_no_orphan_lineage.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "build_pr168_gfp_global_formula_discovery_real_computation.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_baseline_count_reconcile.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_no_fake_positive_negative_labels.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_assignment_coverage.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_real_formula_computation.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_registry_integrity.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_atomicrows_computation_coverage.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_qku_computation_coverage.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_candidate_packet_v1_coverage.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_quantum_objective_coefficients.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_metadata_placeholder_demotions.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_truth_overlay_required.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_report_compactness.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_source_arbitration.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_master_plan_formula_catalog_diff.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_minimum_tradability_formula_set.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_forbidden_bundle_terminology.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_no_orphan_lineage.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_authority_boundaries.py"),
        ],
        *[
            [
                python_executable,
                str(Path("tools") / script_name),
            ]
            for script_name in (
                "build_pr168_rp_formula_based_replay_paper_recompute.py",
                "validate_qtt_authority_reason_code_registry.py",
                "validate_pr168_rp_formula_execution.py",
                "validate_pr168_rp_replay_paper_results.py",
                "validate_pr168_rp_no_fake_computed_labels.py",
                "validate_pr168_rp_tca_pnl_math.py",
                "validate_pr168_rp_microstructure_fill_model.py",
                "validate_pr168_rp_pretrade_simulation_kernel.py",
                "validate_pr168_rp_order_policy_candidate_ranking.py",
                "validate_pr168_rp_no_trade_candidate.py",
                "validate_pr168_rp_scenario_ladder.py",
                "validate_pr168_rp_latency_budget.py",
                "validate_pr168_rp_live_candidate_handoff_no_order_authority.py",
                "validate_pr168_rp_probability_calibration.py",
                "validate_pr168_rp_overfit_fdr.py",
                "validate_pr168_rp_quantum_objective_recompute.py",
                "validate_pr168_rp_quantum_structural_readiness.py",
                "validate_pr168_rp_portfolio_marginal_utility.py",
                "validate_pr168_rp_capacity_crowding.py",
                "validate_pr168_rp_regime_memory.py",
                "validate_pr168_rp_champion_challenger.py",
                "validate_pr168_rp_combination_selection.py",
                "validate_pr168_rp_negative_recovery.py",
                "validate_pr168_rp_edge_attribution.py",
                "validate_pr168_rp_agent_duty_orchestration.py",
                "validate_pr168_rp_connector_candidate_routing.py",
                "validate_pr168_rp_strict_input_consumption.py",
                "validate_pr168_rp_no_orphan_lineage.py",
                "validate_pr168_rp_artifact_information_value_dag.py",
                "validate_pr168_rp_authority_boundaries.py",
                "validate_pr168_rp_report_compactness.py",
                "validate_pr168_rp_validation_scope_registry_integration.py",
                "validate_pr168_rp_windows_linux_compatibility.py",
                "validate_pr168_rp_no_metadata_only_pass.py",
                "validate_pr168_rp_no_forced_negative_to_positive.py",
                "validate_pr168_rp_no_scattered_authority_wording.py",
            )
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rank_evidence_backed_ranking.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_data1_public_market_data_snapshots.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_data1a_focused_audit.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp2r_data1a_gated_candidate_recompute.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp2_map2.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp2_map2.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_map3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_map3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rank3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rank3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5a_legacy_semantic_audit.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5a_legacy_semantic_audit.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5b_active_registry_safe_cleanup.py"),
            "--dry-run",
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5b_active_registry_safe_cleanup.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5c_immutable_qku_formula_library.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5c_immutable_qku_formula_library.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "run_pr168_vs1_trading_intelligence_slice.py"),
            "--fixture",
            "all",
            "--top-k",
            "10",
            "--max-identities",
            "50",
            "--max-stacks-per-fixture",
            "20",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_vs1_trading_intelligence_slice.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5d_replay_paper_executability_tiers.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5d_replay_paper_executability_tiers.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5e_stack_gen.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-stacks",
            "1000",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5e_stack_gen.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5d_r1_exec_now_unlock.py"),
            "--offline",
            "--fixture",
            "sample",
            "--target-min",
            "5",
            "--target-max",
            "15",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5d_r1_exec_now_unlock.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5f_dynamic_targets.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-targets",
            "25",
            "--max-seeds",
            "500",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5f_dynamic_targets.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5g_trade_plan_sim.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-candidates",
            "10",
            "--out",
            "docs/master_plan/generated/pr168_rp5g",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5g_trade_plan_sim.py"),
            "--generated",
            "docs/master_plan/generated/pr168_rp5g",
            "--timeout-ms",
            "3600000",
        ],
        *[
            [
                python_executable,
                str(Path("tools") / f"validate_pr168_rank_{name}.py"),
            ]
            for name in (
                "input_consumption",
                "no_fake_ranking",
                "score_math",
                "binary_prediction_market_pnl",
                "candidate_stack_generation",
                "mode_policy_matrix",
                "pretrade_order_simulation",
                "order_decision_tournament",
                "tca_decomposition",
                "champion_challenger",
                "no_trade_dominance",
                "overfit_fdr",
                "regime_ranking",
                "portfolio_ranking",
                "capacity_crowding",
                "quantum_structural_ranking",
                "quantum_combinatorial_selection",
                "latency_hot_path_seed",
                "agent_work_orders",
                "downstream_orchestration",
                "dag_orchestration",
                "no_orphan",
                "authority_boundaries",
                "validation_scope_registry_integration",
                "centralized_systems_coverage",
                "edge_capture_attribution",
                "negative_recovery_tournament",
                "threshold_surfaces",
                "maker_taker_tradeoff",
                "size_price_time_sensitivity",
                "scenario_stress_surface",
                "materialized_artifacts_not_blueprints",
                "scalar_value_no_orphan",
                "terminal_artifact_lifecycle",
                "connector_candidate_routing",
                "two_speed_decision_surface",
                "future_expansion_registries",
                "market_adapter_registry_seed",
                "venue_cost_model_registry_seed",
                "contract_payoff_model_registry_seed",
                "formula_algorithm_plugin_registry_seed",
                "quantum_objective_registry_seed",
                "order_policy_registry_seed",
                "agent_capability_registry_seed",
                "connector_readiness_registry_seed",
                "runtime_allowlist_seed_registry",
                "hot_path_decision_surface_registry",
                "registry_seed_no_orphan",
                "registry_anti_scatter",
            )
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentRoleOperatingCharterReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAlgorithmFormulaFamilyReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_static.py"),
            "--schema",
            str(Path("schemas") / "source_evidence" / "source_evidence.schema.json"),
            "--owner-packet",
            str(
                Path("docs")
                / "master_plan"
                / "source_evidence"
                / "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
            ),
            "--registry-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_acceptance_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_gate_confirmation_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "source_evidence"
                / "source_evidence_gate_confirmation.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_retrieval_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_acceptance.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_accepted_source_to_connector_semantic_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_revalidation_scheduler.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_connector_semantic_binding_implementation_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_per_venue_execution_lifecycle_model.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_cross_venue_execution_normalization_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "runtime_cash_component_field_map_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "private_state_read_receipt_gate_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "credential_alias_secret_no_capture_readiness_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "venue_market_data_ingest_adapters_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "orderbook_event_state_snapshot_builder_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "runtime_resolver_snapshot_executor_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_historical_dataset_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_historical_dataset_digest_and_loader.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr136_roadmap_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr136_day1_launch_readiness_roadmap.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_connector_capability_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_capability_registry.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_capability_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_runtime_orchestration_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "runtime_orchestration_skeleton.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_runtime_orchestration_skeleton.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_replay_paper_execution_graph_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "replay_paper_review"
                / "replay_paper_execution_graph.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "replay_paper_review"
                / "synthetic_replay_paper_execution_graph.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_venue_abstraction_layer_static.py"),
            "--schema",
            str(Path("schemas") / "connectors" / "venue_abstraction_layer.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_venue_abstraction_layer.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_order_intent_execution_router_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "order_intent_execution_router_scaffolding.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_readiness_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_unblocking_requirements_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_canonical_row_specification_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_canonical_row_specification_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
            "--repo-root",
            ".",
            "--row-schema",
            str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
            "--bundle-schema",
            str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecyclePromotionReceiptGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_registry_mutation_guard.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleRegistryMutationGuard.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleGateCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_registry.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_source_to_candidate_family_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_completeness_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_compatibility_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_selection_universe_routing_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_applicability_classification_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_quantum_priority_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_algorithm_scoring_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_stack_scoring_and_ranking_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_classical_optimizer_arbitration_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_candidate_parameter_stack_generation_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_parameter_stack_selection_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_selected_parameter_stack_handoff_packet.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_replay_paper_candidate_stack_competition_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_dual_result_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_live_promotion_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_approval_request_queue_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_override_receipt_authoring_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_menu_schema.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_static_screen_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_sha_system_dormancy_state_contract.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_final_readiness_dependency_policy_contract.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_roadmap_execution_state_controller.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_source_materialization_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_materialization_manifest.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_boundary_state_contract.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "master_plan"
                / "generated_derivative_bootstrap_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "master_plan"
                / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "stage1_prediction_markets"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "stage1_prediction_markets"
                / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_venue_neutral_prediction_adapter_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "venue_neutral_prediction_adapter"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "venue_neutral_prediction_adapter"
                / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_connector_scaffold_source_required_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_scaffold_source_required_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "stage1_runtime_scaffold_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_source_fact_binding_connector_semantic_readiness_static.py"
            ),
            "--repo-root",
            ".",
            "--source-to-connector-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_source_to_connector_field_binding_matrix.schema.json"
            ),
            "--source-to-connector-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
            ),
            "--connector-target-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_target_field_matrix.schema.json"
            ),
            "--connector-target-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
            ),
            "--gate-report-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_readiness_gate_report.schema.json"
            ),
            "--gate-report-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "source_evidence_acceptance_consumer_contract_check.py"),
            "--repo-root",
            ".",
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "accepted_source_evidence_consumer_contract.schema.json"
            ),
            "--target-field-ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_target_field_acceptance_ledger_record.schema.json"
            ),
            "--export-record-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_accepted_source_evidence_export_record.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "acceptance_consumer_contract"
                / "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_connector_semantic_binding_ledger_check.py"),
            "--repo-root",
            ".",
            "--ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_ledger_record.schema.json"
            ),
            "--canonicalization-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_value_canonicalization.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_consumer_contract.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "connector_semantic_binding"
                / "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConnectorSemanticBindingLedgerCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
            "--repo-root",
            ".",
            "--input-lock-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
            ),
            "--manifest-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_manifest.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_consumer_contract.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver"
                / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverSnapshotContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
            ),
            "--repo-root",
            ".",
            "--consumer-allowlist-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
            ),
            "--handoff-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
            ),
            "--handoff-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver_snapshot"
                / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
            "--repo-root",
            ".",
            "--input-identity-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_input_identity.schema.json"
            ),
            "--replay-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_lane_contract.schema.json"
            ),
            "--paper-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_paper_lane_contract.schema.json"
            ),
            "--replay-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "replay_result_packet_boundary.schema.json"
            ),
            "--paper-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "paper_result_packet_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_execution_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "replay_paper"
                / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConcurrentReplayPaperContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_input_contract.schema.json"
            ),
            "--comparison-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_replay_paper_comparison_matrix.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_gate_report.schema.json"
            ),
            "--owner-handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_owner_live_promotion_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "dual_result_review"
                / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1DualResultReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_input_contract.schema.json"
            ),
            "--owner-approval-receipt-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_approval_receipt_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_gate_report.schema.json"
            ),
            "--handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "owner_live_promotion_review"
                / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1OwnerLivePromotionReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
            ),
            "--readiness-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_platform_readiness_matrix.schema.json"
            ),
            "--handoff-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
            ),
            "--execution-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_limited_live_canary_execution_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "three_venue_canary_eligibility"
                / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_master_plan_section_coverage_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_master_plan_section_coverage.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_coverage_triage_routes.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_roadmap_crosswalk.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_coverage_command_matrix.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "qtt_test_gate.py"),
            "--phase",
            "first-coding-runbook",
            "--repo-root",
            ".",
            "--strict-no-claim",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "QTTTestGate.report.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "local_gate_command_matrix.py"),
            "--repo-root",
            ".",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "LocalGateCommandMatrix.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "pr_handoff_check.py"),
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "FirstCodingPRHandoff.packet.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_no_runtime_artifacts.py"),
            "--repo-root",
            ".",
            "--forbid-source-retrieval",
            "--forbid-source-acceptance",
            "--forbid-connector-binding",
            "--forbid-private-state-fetch",
            "--forbid-order-execution",
            "--forbid-neural-training",
            "--forbid-neural-inference",
            "--forbid-external-repo-clone",
            "--forbid-package-install-scripts",
        ],
        [
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            str(
                Path("tests")
                / "source_evidence"
                / "test_controlled_official_source_capture_candidate_packets.py"
            ),
            "-q",
            runner.PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
        [
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            "tests",
            "-q",
            "--ignore",
            str(
                Path("tests")
                / "source_evidence"
                / "test_controlled_official_source_capture_candidate_packets.py"
            ),
            runner.PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
    ]
    return [
        runner._route_command_generated_outputs_to_temp(command, validation_dir)
        for command in commands
    ]


def _pytest_basetemp_from_commands(commands: list[list[str]]) -> Path:
    pytest_command = next(
        command for command in reversed(commands) if "--basetemp" in command
    )
    return Path(pytest_command[pytest_command.index("--basetemp") + 1])


def _validation_dir_from_commands(commands: list[list[str]]) -> Path:
    ingest_command = next(
        command
        for command in commands
        if len(command) > 1 and Path(command[1]).name == "master_plan_ingest.py"
    )
    return Path(ingest_command[ingest_command.index("--section-manifest-out") + 1]).parent


def test_runner_builds_expected_command_sequence(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    assert runner.build_validation_commands() == _expected_commands(python_executable)


def test_runner_phase_manifest_covers_full_validation_plan(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    manifest = runner.build_phase_manifest(validation_dir, pytest_basetemp)
    manifest_commands = [
        command
        for phase_record in manifest
        for command in phase_record["commands"]
    ]

    assert [record["phase"] for record in manifest] == list(runner.ORDERED_PHASES)
    assert manifest_commands == runner.build_phase_commands(
        runner.ALL_PHASE,
        validation_dir,
        pytest_basetemp,
    )


def test_runner_assigns_canonical_non_pytest_commands_to_one_phase(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    canonical_commands = runner.build_validation_commands(validation_dir, pytest_basetemp)
    canonical_non_pytest = [
        command
        for command in canonical_commands
        if not runner._command_uses_pytest_helper(command)
    ]
    phase_non_pytest = (
        runner.build_phase_commands(runner.FAST_PREFLIGHT_PHASE, validation_dir, pytest_basetemp)
        + runner.build_phase_commands(
            runner.DETERMINISTIC_VALIDATORS_PHASE,
            validation_dir,
            pytest_basetemp,
        )
    )

    for command in canonical_non_pytest:
        assert phase_non_pytest.count(command) == 1
    assert not any(
        runner._command_uses_pytest_helper(command) for command in phase_non_pytest
    )


def test_runner_deterministic_phase_moves_preflight_validator_out_of_long_phase():
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    fast_names = [
        Path(command[1]).name
        for command in runner.build_phase_commands(
            runner.FAST_PREFLIGHT_PHASE,
            validation_dir,
            pytest_basetemp,
        )
    ]
    deterministic_names = [
        Path(command[1]).name
        for command in runner.build_phase_commands(
            runner.DETERMINISTIC_VALIDATORS_PHASE,
            validation_dir,
            pytest_basetemp,
        )
    ]

    assert set(fast_names) == runner.FAST_PREFLIGHT_SCRIPT_NAMES
    assert "validate_grand_global_debug_logical_consistency_audit.py" in fast_names
    assert "validate_grand_global_debug_logical_consistency_audit.py" not in deterministic_names


def test_runner_pytest_shards_cover_each_test_file_once():
    all_tests = set(runner.discover_pytest_files(REPO_ROOT))
    shard_manifest = runner.pytest_shard_manifest(REPO_ROOT)
    flattened = [
        path
        for shard_paths in shard_manifest.values()
        for path in shard_paths
    ]

    assert all_tests
    assert set(flattened) == all_tests
    assert len(flattened) == len(set(flattened))
    assert set(shard_manifest) == set(runner.PYTEST_SHARD_PHASES)
    assert (
        runner.ISOLATED_SOURCE_EVIDENCE_PYTEST
        in shard_manifest["pytest-shard-8"]
    )
    assert "tests/tools/test_ci_branch_context.py" in shard_manifest["pytest-shard-1"]
    assert (
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py"
        in shard_manifest["pytest-shard-3"]
    )
    assert (
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py"
        in shard_manifest["pytest-shard-8"]
    )
    assert (
        "tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/"
        "test_pr165_d3_validator.py"
        in shard_manifest["pytest-shard-7"]
    )


def test_runner_pytest_runtime_budget_plan_is_complete_and_fail_closed():
    failures = runner.pytest_runtime_budget_failures(REPO_ROOT)
    plan = runner.pytest_runtime_budget_plan()

    assert failures == ()
    assert set(plan["pytest_shards"]) == set(runner.PYTEST_SHARD_PHASES)
    assert set(plan["shard_budgets"]) == set(runner.PYTEST_SHARD_PHASES)
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_target_seconds"] == 20 * 60
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_warning_seconds"] == 25 * 60
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_hard_review_seconds"] == 30 * 60
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_subprocess_group_target_seconds"]
        == 8 * 60
    )
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_subprocess_group_warning_seconds"]
        == 10 * 60
    )
    assert runner.RUNTIME_BUDGET_POLICY["pytest_file_warning_seconds"] == 120
    assert runner.RUNTIME_BUDGET_POLICY["pytest_file_hard_review_seconds"] == 300
    assert runner.RUNTIME_BUDGET_POLICY["pytest_idempotence_warning_seconds"] == 120
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_idempotence_hard_review_seconds"]
        == 180
    )
    assert runner.BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS == frozenset(
        {
            _pr166_sf_r2_idempotence_path(),
            _pr166_sm3_idempotence_path(),
            _pr166_q_idempotence_path(),
            _pr166_qb_idempotence_path(),
            _pr166_qc_idempotence_path(),
            _pr162e_q_idempotence_path(),
            _pr167_idempotence_path(),
            _pr162e_idempotence_path(),
        }
    )


def _pr166_sm2_group_paths() -> list[tuple[str, ...]]:
    return [
        tuple(
            f"{runner.PR166_SM2_TEST_ROOT}/{file_name}"
            for file_name in group
        )
        for group in runner.PR166_SM2_PYTEST_FILE_GROUPS
    ]


def _pr166_sf_r2_group_paths() -> list[tuple[str, ...]]:
    return [
        tuple(
            f"{runner.PR166_SF_R2_TEST_ROOT}/{file_name}"
            for file_name in group
        )
        for group in runner.PR166_SF_R2_PYTEST_FILE_GROUPS
    ]


def _pr166_sf_r2_idempotence_path() -> str:
    return (
        f"{runner.PR166_SF_R2_TEST_ROOT}/"
        f"{runner.PR166_SF_R2_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_sm3_idempotence_path() -> str:
    return (
        f"{runner.PR166_SM3_TEST_ROOT}/"
        f"{runner.PR166_SM3_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_q_idempotence_path() -> str:
    return (
        f"{runner.PR166_Q_TEST_ROOT}/"
        f"{runner.PR166_Q_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_qb_idempotence_path() -> str:
    return (
        f"{runner.PR166_QB_TEST_ROOT}/"
        f"{runner.PR166_QB_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_qc_idempotence_path() -> str:
    return (
        f"{runner.PR166_QC_TEST_ROOT}/"
        f"{runner.PR166_QC_IDEMPOTENCE_TEST_FILE}"
    )


def _pr162e_q_idempotence_path() -> str:
    return (
        f"{runner.PR162E_Q_TEST_ROOT}/"
        f"{runner.PR162E_Q_IDEMPOTENCE_TEST_FILE}"
    )


def _pr167_idempotence_path() -> str:
    return (
        f"{runner.PR167_TEST_ROOT}/"
        f"{runner.PR167_IDEMPOTENCE_TEST_FILE}"
    )


def _pr162e_idempotence_path() -> str:
    return (
        f"{runner.PR162E_TEST_ROOT}/"
        f"{runner.PR162E_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_sf_r2_non_idempotence_group_paths() -> list[tuple[str, ...]]:
    idempotence_group = (_pr166_sf_r2_idempotence_path(),)
    return [
        group_paths
        for group_paths in _pr166_sf_r2_group_paths()
        if group_paths != idempotence_group
    ]


def _pr166_sf_r2_split_command_placements():
    return [
        (phase, command.paths)
        for phase in runner.PYTEST_SHARD_PHASES
        for command in runner.PYTEST_SHARD_COMMANDS[phase]
        if any(
            path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
            for path in command.paths
        )
    ]


def test_runner_splits_pytest_shard_2_longest_group_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-2"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry",
            "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate",
            "tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing",
            "tests/stage1_prediction_markets/atomicrows_bundle_reconciliation",
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state",
            "tests/stage1_prediction_markets/latency_hot_path_snapshot_boundary",
        ),
        (
            "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure",
            "tests/stage1_prediction_markets/pr162d_r1_external_formula_data_quantum_acquisition_expansion",
            "tests/stage1_prediction_markets/pr162d_r2a_real_formulations",
            "tests/stage1_prediction_markets/pr162r_a_replay_paper_executability_classification_audit",
            "tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion",
            "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun",
            "tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor",
            "tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation",
        ),
        ("tests/atomicrows",),
        ("tests/pr168_gfp",),
        ("tests/pr168_rp",),
        ("tests/pr168_rank",),
        ("tests/pr168_data1",),
        ("tests/pr168_data1a",),
        ("tests/pr168_gfp2r",),
        ("tests/pr168_rp2",),
        ("tests/pr168_map3",),
        ("tests/pr168_rp3",),
        ("tests/pr168_rank3",),
        ("tests/pr168_rp5a",),
        ("tests/pr168_rp5b",),
        ("tests/pr168_rp5c",),
        ("tests/pr168_vs1",),
        ("tests/pr168_rp5d",),
        ("tests/pr168_rp5e",),
        ("tests/pr168_rp5d_r1",),
        ("tests/pr168_rp5f",),
        ("tests/pr168_rp5g",),
    ]
    assert all(command.reason for command in commands)
    assert ("tests/stage1_prediction_markets",) not in [
        command.paths for command in commands
    ]

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-2"]
    )


def test_runner_pr166_sm2_split_groups_cover_each_test_file_once():
    expected = {
        path
        for path in runner.discover_pytest_files(REPO_ROOT)
        if path.startswith(f"{runner.PR166_SM2_TEST_ROOT}/")
    }
    grouped = [
        path
        for group in _pr166_sm2_group_paths()
        for path in group
    ]
    expanded = [
        path
        for command in runner.PYTEST_SHARD_COMMANDS["pytest-shard-5"]
        if any(path.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for path in command.paths)
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(runner.PR166_SM2_PYTEST_FILE_GROUPS) == 6
    assert all(0 < len(group) <= 14 for group in runner.PR166_SM2_PYTEST_FILE_GROUPS)
    assert grouped == sorted(grouped)
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == expected
    assert expanded == grouped
    assert set(expanded).issubset(
        set(runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-5"])
    )


def test_runner_pr166_sf_r2_split_groups_cover_each_test_file_once():
    expected = {
        path
        for path in runner.discover_pytest_files(REPO_ROOT)
        if path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
    }
    grouped = [
        path
        for group in _pr166_sf_r2_group_paths()
        for path in group
    ]
    expanded_by_phase = {
        phase: [
            path
            for command in runner.PYTEST_SHARD_COMMANDS[phase]
            if any(
                command_path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
                for command_path in command.paths
            )
            for path in runner._pytest_files_for_command(command, REPO_ROOT)
        ]
        for phase in runner.PYTEST_SHARD_PHASES
    }
    expanded = [
        path
        for phase_paths in expanded_by_phase.values()
        for path in phase_paths
    ]
    idempotence_path = _pr166_sf_r2_idempotence_path()
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert len(runner.PR166_SF_R2_PYTEST_FILE_GROUPS) == 8
    assert all(
        0 < len(group) <= 14 for group in runner.PR166_SF_R2_PYTEST_FILE_GROUPS
    )
    assert grouped == sorted(grouped)
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == expected
    assert len(expanded) == len(set(expanded))
    assert sorted(expanded) == grouped
    assert expanded.count(idempotence_path) == 1
    assert idempotence_path not in expanded_by_phase["pytest-shard-2"]
    assert not expanded_by_phase["pytest-shard-2"]
    assert expanded_by_phase["pytest-shard-4"] == [idempotence_path]
    assert sorted(expanded_by_phase["pytest-shard-6"]) == sorted(
        path
        for group in _pr166_sf_r2_non_idempotence_group_paths()
        for path in group
    )
    assert manifest_hits == [("pytest-shard-4", idempotence_path)]


def test_runner_pr166_sf_r2_idempotence_is_own_early_shard4_subgroup():
    idempotence_path = _pr166_sf_r2_idempotence_path()
    placements = [
        (phase, paths)
        for phase, paths in _pr166_sf_r2_split_command_placements()
        if idempotence_path in paths
    ]
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert placements == [("pytest-shard-4", (idempotence_path,))]
    idempotence_command = runner.PYTEST_SHARD_COMMANDS["pytest-shard-4"][1]
    assert idempotence_command.paths == (
        idempotence_path,
    )
    assert idempotence_command.bounded_idempotence is True
    assert manifest_hits == [("pytest-shard-4", idempotence_path)]


def test_runner_pr166_sm3_idempotence_is_bounded_shard7_subgroup():
    idempotence_path = _pr166_sm3_idempotence_path()
    placements = [
        (phase, command.paths)
        for phase in runner.PYTEST_SHARD_PHASES
        for command in runner.PYTEST_SHARD_COMMANDS[phase]
        if idempotence_path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert placements == [("pytest-shard-7", (idempotence_path,))]
    idempotence_command = runner.PYTEST_SHARD_COMMANDS["pytest-shard-7"][1]
    assert idempotence_command.paths == (idempotence_path,)
    assert idempotence_command.bounded_idempotence is True
    assert manifest_hits == [("pytest-shard-7", idempotence_path)]


@pytest.mark.parametrize(
    "pr166_sm2_subgroup_index",
    range(len(runner.PR166_SM2_PYTEST_FILE_GROUPS)),
)
def test_runner_fails_closed_if_any_pr166_sm2_subgroup_fails(
    pr166_sm2_subgroup_index,
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = runner.build_pytest_shard_commands(
        "pytest-shard-5",
        Path(".tmp") / "pytest-basetemp",
    )
    pr166_commands = [
        command
        for command in commands
        if any(part.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for part in command)
    ]
    failing_command = pr166_commands[pr166_sm2_subgroup_index]
    failing_index = commands.index(failing_command)
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(73 if command == failing_command else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands, phase="pytest-shard-5")

    assert exit_code == 73
    assert seen == commands[: failing_index + 1]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


@pytest.mark.parametrize(
    "pr166_sf_r2_subgroup_index",
    range(len(runner.PR166_SF_R2_PYTEST_FILE_GROUPS)),
)
def test_runner_fails_closed_if_any_pr166_sf_r2_subgroup_fails(
    pr166_sf_r2_subgroup_index,
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    expected_paths = _pr166_sf_r2_group_paths()[pr166_sf_r2_subgroup_index]
    placements = [
        (phase, paths)
        for phase, paths in _pr166_sf_r2_split_command_placements()
        if paths == expected_paths
    ]
    assert len(placements) == 1
    phase, failing_paths = placements[0]
    commands = runner.build_pytest_shard_commands(
        phase,
        Path(".tmp") / "pytest-basetemp",
    )
    failing_command = next(
        command
        for command in commands
        if tuple(command[2 : 2 + len(failing_paths)]) == failing_paths
    )
    failing_index = commands.index(failing_command)
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(83 if command == failing_command else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands, phase=phase)

    assert exit_code == 83
    assert seen == commands[: failing_index + 1]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_rebalances_pytest_shard_3_with_stage1_legacy_group():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-3"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage",
            "tests/stage1_prediction_markets/"
            "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage",
            "tests/stage1_prediction_markets/"
            "nonlive_replay_paper_data_adapter_quantum_forward_bridge",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge",
            "tests/stage1_prediction_markets/"
            "pr158_owner_response_selection_readiness_bridge",
            "tests/stage1_prediction_markets/"
            "pr159_official_source_completion_bridge",
            "tests/stage1_prediction_markets/pr159r_source_locator_value_capture",
        ),
        (
            "tests/stage1_prediction_markets/"
            "pr163_generic_paper_adapter_capture_framework",
            "tests/stage1_prediction_markets/"
            "pr164_review_provenance_qku_canonical_coverage_audit",
            "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory",
            "tests/stage1_prediction_markets/"
            "pr165_c_replay_paper_memory_consumer_integration",
            "tests/stage1_prediction_markets/"
            "pr165_d_scenario_qku_combination_selection",
            "tests/stage1_prediction_markets/"
            "pr165_d2_score_refreshed_scenario_selection_v2",
            "tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking",
            "tests/stage1_prediction_markets/"
            "pr166_s_replay_paper_scenario_retest_execution",
            "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2",
        ),
        (
            "tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization",
            "tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization",
            "tests/stage1_prediction_markets/qku_residual_candidate_assimilation",
            "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation",
            "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning",
            "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
            "tests/stage1_prediction_markets/source_intelligence",
            "tests/stage1_prediction_markets/test_validate_stage1_packet_schema_gate_static.py",
        ),
    ]
    assert all(command.reason for command in commands)

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-3"]
    )
    assert (
        "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2/"
        "test_pr166_s2_exec_readiness.py"
        in runner._pytest_files_for_command(commands[1], REPO_ROOT)
    )


def test_runner_splits_pytest_shard_4_bounded_idempotence_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-4"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest",
            "tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results",
        ),
        (_pr166_sf_r2_idempotence_path(),),
    ]
    assert commands[1].bounded_idempotence is True
    assert all(command.reason for command in commands)

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-4"]
    )


def test_runner_splits_pytest_shard_7_current_pr_group_first():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-7"]
    idempotence_path = _pr166_sm3_idempotence_path()

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/"
            "pr165_d3_quantum_aware_scenario_selection_v3",
        ),
        (idempotence_path,),
        (runner.PR166_SM3_TEST_ROOT,),
    ]
    assert commands[1].bounded_idempotence is True
    assert commands[2].ignores == (idempotence_path,)
    assert (
        "tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/"
        "test_pr165_d3_validator.py"
        in runner._pytest_files_for_command(commands[0], REPO_ROOT)
    )
    assert idempotence_path in runner._pytest_files_for_command(
        commands[1],
        REPO_ROOT,
    )
    assert idempotence_path not in runner._pytest_files_for_command(
        commands[2],
        REPO_ROOT,
    )
    assert all(command.reason for command in commands)


def test_runner_splits_pytest_shard_8_residual_tests_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-8"]
    idempotence_path = _pr166_q_idempotence_path()
    qb_idempotence_path = _pr166_qb_idempotence_path()
    qc_idempotence_path = _pr166_qc_idempotence_path()
    pr162e_q_idempotence_path = _pr162e_q_idempotence_path()
    pr167_idempotence_path = _pr167_idempotence_path()
    pr162e_idempotence_path = _pr162e_idempotence_path()

    assert [command.paths for command in commands] == [
        (idempotence_path,),
        (runner.PR166_Q_TEST_ROOT,),
        (qb_idempotence_path,),
        (runner.PR166_QB_TEST_ROOT,),
        (qc_idempotence_path,),
        (runner.PR166_QC_TEST_ROOT,),
        (pr162e_q_idempotence_path,),
        (runner.PR162E_Q_TEST_ROOT,),
        (pr167_idempotence_path,),
        (runner.PR167_TEST_ROOT,),
        (pr162e_idempotence_path,),
        (runner.PR162E_TEST_ROOT,),
        (runner.ISOLATED_SOURCE_EVIDENCE_PYTEST,),
        (
            "tests/agent_algorithm",
            "tests/agents",
            "tests/algorithms",
            "tests/connectors",
        ),
        (
            "tests/core",
            "tests/dashboard",
            "tests/edge",
            "tests/external_repo",
            "tests/governance",
            "tests/launch",
            "tests/master_plan",
        ),
        ("tests/global_debug",),
        (
            "tests/neural_signal",
            "tests/quantum",
            "tests/replay_paper",
            "tests/replay_paper_review",
            "tests/research",
            "tests/roadmap",
        ),
        (
            "tests/runtime_cash",
            "tests/runtime_orchestration",
            "tests/runtime_resolver",
            "tests/scoring",
            "tests/selection",
            "tests/venue_neutral_prediction_adapter",
        ),
        ("tests/source_evidence",),
    ]
    assert commands[0].bounded_idempotence is True
    assert commands[1].ignores == (idempotence_path,)
    assert commands[2].bounded_idempotence is True
    assert commands[3].ignores == (qb_idempotence_path,)
    assert commands[4].bounded_idempotence is True
    assert commands[5].ignores == (qc_idempotence_path,)
    assert commands[6].bounded_idempotence is True
    assert commands[7].ignores == (pr162e_q_idempotence_path,)
    assert commands[8].bounded_idempotence is True
    assert commands[9].ignores == (pr167_idempotence_path,)
    assert commands[10].bounded_idempotence is True
    assert commands[11].ignores == (pr162e_idempotence_path,)
    assert commands[-1].ignores == (runner.ISOLATED_SOURCE_EVIDENCE_PYTEST,)
    assert all(command.reason for command in commands)
    assert ("tests",) not in [command.paths for command in commands]

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-8"]
    )
    assert (
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py"
        in runner._pytest_files_for_command(commands[15], REPO_ROOT)
    )


def test_runner_commands_use_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands
    assert all(command[0] == python_executable for command in commands)


def test_runner_includes_pr153_family_and_pr154_validators_after_pr152(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr152_index = command_names.index(
        "validate_grand_global_debug_logical_consistency_audit.py"
    )
    pr153_index = command_names.index(
        "validate_controlled_official_source_capture_candidate_packets.py"
    )
    pr153r_index = command_names.index(
        "validate_pr153r_redo_external_source_value_capture_targets.py"
    )
    pr153s_index = command_names.index(
        "validate_pr153s_source_value_capture_closure_classifier.py"
    )
    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    next_gate_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )

    assert (
        command_names.count(
            "validate_controlled_official_source_capture_candidate_packets.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr153r_redo_external_source_value_capture_targets.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr153s_source_value_capture_closure_classifier.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_atomicrows_parameter_default_value_materialization_gate.py"
        )
        == 1
    )
    assert pr152_index < pr153_index < pr153r_index < pr153s_index < pr154_index
    assert pr154_index < next_gate_index
    assert commands[pr153_index] == [
        python_executable,
        str(Path("tools") / "validate_controlled_official_source_capture_candidate_packets.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr153r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr153r_redo_external_source_value_capture_targets.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr153s_index] == [
        python_executable,
        str(Path("tools") / "validate_pr153s_source_value_capture_closure_classifier.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr154_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_default_value_materialization_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr153_index]
    assert "--output" not in commands[pr153_index]
    assert "--write-report" not in commands[pr153r_index]
    assert "--output" not in commands[pr153r_index]
    assert "--write-report" not in commands[pr153s_index]
    assert "--output" not in commands[pr153s_index]
    assert "--write-report" not in commands[pr154_index]
    assert "--output" not in commands[pr154_index]


def test_runner_guidance_requires_pr152_finalization_before_validation_gates():
    guidance = runner.build_pre_validation_finalization_guidance()
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]

    assert guidance == [
        {
            "command_id": "pr152_currentize_after_generated_artifacts",
            "command": (
                ".\\.venv\\Scripts\\python.exe "
                "tools\\currentize_pr152_after_generated_artifacts.py"
            ),
            "when": "after final generated artifacts settle and before validation gates",
            "ci_tracked_report_mutation_allowed": False,
        }
    ]
    assert "currentize_pr152_after_generated_artifacts.py" not in command_names
    assert "validate_grand_global_debug_logical_consistency_audit.py" in command_names


def test_runner_includes_pr157_bridge_after_pr156_without_tracked_write(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    pr155_index = command_names.index(
        "validate_agent_consumable_parameter_default_registry.py"
    )
    pr156_index = command_names.index(
        "validate_agent_default_binding_universal_intake_gate.py"
    )
    pr157_index = command_names.index(
        "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
    )
    pr158_index = command_names.index(
        "validate_pr158_owner_response_selection_readiness_bridge.py"
    )
    pr159_index = command_names.index(
        "validate_pr159_official_source_completion_bridge.py"
    )
    pr160_index = command_names.index(
        "validate_pr160_split_reclassification_route_closure.py"
    )
    pr159r_index = command_names.index(
        "validate_pr159r_source_locator_value_capture.py"
    )
    pr159s_index = command_names.index("validate_pr159s_open_intake_completion.py")
    pr161a_index = command_names.index(
        "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
    )
    pr161b_index = command_names.index(
        "validate_pr161b_master_plan_residual_candidate_coverage.py"
    )
    pr161c_index = command_names.index(
        "validate_pr161c_qku_residual_candidate_assimilation.py"
    )
    pr161d_index = command_names.index(
        "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
    )
    pr161e_index = command_names.index(
        "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
    )
    pr161f_index = command_names.index(
        "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
    )
    pr162_index = command_names.index(
        "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
    )
    pr162a_index = command_names.index(
        "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
    )
    pr162b_index = command_names.index(
        "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
    )
    pr162c_index = command_names.index(
        "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
    )
    pr162d_index = command_names.index(
        "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
    )
    pr162r_a_index = command_names.index(
        "validate_pr162r_a_replay_paper_executability_classification_audit.py"
    )
    pr162d_r2a_index = command_names.index(
        "validate_pr162d_r2a_real_formulations.py"
    )
    pr162r_index = command_names.index(
        "validate_pr162r_generic_replay_paper_adapter_rerun.py"
    )
    pr162r_b_index = command_names.index(
        "validate_pr162r_b_replay_paper_data_binding_completion.py"
    )
    pr163_index = command_names.index(
        "validate_pr163_generic_paper_adapter_capture_framework.py"
    )
    pr163_b_index = command_names.index(
        "validate_pr163_b_paired_replay_paper_concurrent_executor.py"
    )
    pr164_index = command_names.index(
        "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
    )
    pr163_c_index = command_names.index(
        "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
    )
    pr165_index = command_names.index(
        "validate_pr165_evidence_backed_scoring_ranking.py"
    )
    pr165_b_index = command_names.index(
        "validate_pr165_b_condition_scoped_negative_memory.py"
    )
    pr165_c_index = command_names.index(
        "validate_pr165_c_replay_paper_memory_consumer_integration.py"
    )
    pr165_d_index = command_names.index(
        "validate_pr165_d_scenario_qku_combination_selection.py"
    )
    pr166_s_index = command_names.index(
        "validate_pr166_s_replay_paper_scenario_retest_execution.py"
    )
    pr166_sm_index = command_names.index(
        "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
    )
    pr166_sf_index = command_names.index(
        "validate_pr166_sf_repair_materialization_before_retest.py"
    )
    pr166_s2_index = command_names.index(
        "validate_pr166_s2_replay_paper_retest_loop_v2.py"
    )
    pr166_sm2_index = command_names.index(
        "validate_pr166_sm2_score_memory_refresh_v2.py"
    )
    pr166_sf_r2_index = command_names.index(
        "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
    )
    pr166_sm3_index = command_names.index(
        "validate_pr166_sm3_score_memory_refresh_v3.py"
    )
    pr166_q_index = command_names.index(
        "validate_pr166_q_quantum_classical_hybrid_comparator.py"
    )
    pr166_qb_index = command_names.index(
        "validate_pr166_qb_bounded_quantum_benchmark.py"
    )
    pr166_qc_index = command_names.index(
        "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
    )
    pr162e_q_index = command_names.index(
        "validate_pr162e_q_quantum_automapper.py"
    )
    pr167_index = command_names.index(
        "validate_pr167_open_trade_simulator_integration.py"
    )
    pr162e_plugin_index = command_names.index(
        "validate_pr162e_plugin_framework.py"
    )
    pr162e_negative_repair_index = command_names.index(
        "validate_pr162e_negative_repair_factory.py"
    )
    pr162e_no_orphan_index = command_names.index(
        "validate_pr162e_no_orphan_lineage.py"
    )
    pr165_d2_index = command_names.index(
        "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
    )
    pr165_d3_index = command_names.index(
        "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
    )
    next_gate_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )

    assert (
        command_names.count(
            "validate_agent_consumable_parameter_default_registry.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_agent_default_binding_universal_intake_gate.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr158_owner_response_selection_readiness_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count("validate_pr159_official_source_completion_bridge.py")
        == 1
    )
    assert (
        command_names.count("validate_pr160_split_reclassification_route_closure.py")
        == 1
    )
    assert command_names.count("validate_pr159r_source_locator_value_capture.py") == 1
    assert command_names.count("validate_pr159s_open_intake_completion.py") == 1
    assert (
        command_names.count(
            "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161b_master_plan_residual_candidate_coverage.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161c_qku_residual_candidate_assimilation.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162r_a_replay_paper_executability_classification_audit.py"
        )
        == 1
    )
    assert command_names.count("validate_pr162d_r2a_real_formulations.py") == 1
    assert (
        command_names.count(
            "validate_pr162r_generic_replay_paper_adapter_rerun.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162r_b_replay_paper_data_binding_completion.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_generic_paper_adapter_capture_framework.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_b_paired_replay_paper_concurrent_executor.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
        )
        == 1
    )
    assert (
        command_names.count("validate_pr165_evidence_backed_scoring_ranking.py")
        == 1
    )
    assert (
        command_names.count("validate_pr165_b_condition_scoped_negative_memory.py")
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_c_replay_paper_memory_consumer_integration.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_d_scenario_qku_combination_selection.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_s_replay_paper_scenario_retest_execution.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sf_repair_materialization_before_retest.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_s2_replay_paper_retest_loop_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sm2_score_memory_refresh_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
        )
        == 1
    )
    assert command_names.count("validate_pr166_sm3_score_memory_refresh_v3.py") == 1
    assert (
        command_names.count("validate_pr166_q_quantum_classical_hybrid_comparator.py")
        == 1
    )
    assert command_names.count("validate_pr166_qb_bounded_quantum_benchmark.py") == 1
    assert (
        command_names.count(
            "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
        )
        == 1
    )
    assert command_names.count("validate_pr162e_q_quantum_automapper.py") == 1
    assert command_names.count("validate_pr167_open_trade_simulator_integration.py") == 1
    assert command_names.count("validate_pr162e_plugin_framework.py") == 1
    assert command_names.count("validate_pr162e_negative_repair_factory.py") == 1
    assert command_names.count("validate_pr162e_no_orphan_lineage.py") == 1
    assert (
        command_names.count(
            "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
        )
        == 1
    )
    assert (
        pr154_index
        < pr155_index
        < pr156_index
        < pr157_index
        < pr158_index
        < pr159_index
        < pr160_index
        < pr159r_index
        < pr159s_index
        < pr161a_index
        < pr161b_index
        < pr161c_index
        < pr161d_index
        < pr161e_index
        < pr161f_index
        < pr162_index
        < pr162a_index
        < pr162b_index
        < pr162c_index
        < pr162d_index
        < pr162r_a_index
        < pr162d_r2a_index
        < pr162r_index
        < pr162r_b_index
        < pr163_index
        < pr163_b_index
        < pr164_index
        < pr163_c_index
        < pr165_index
        < pr165_b_index
        < pr165_c_index
        < pr165_d_index
        < pr166_s_index
        < pr166_sm_index
        < pr166_sf_index
        < pr166_s2_index
        < pr166_sm2_index
        < pr166_sf_r2_index
        < pr166_sm3_index
        < pr166_q_index
        < pr166_qb_index
        < pr166_qc_index
        < pr162e_q_index
        < pr167_index
        < pr162e_plugin_index
        < pr162e_negative_repair_index
        < pr162e_no_orphan_index
        < pr165_d2_index
        < pr165_d3_index
        < next_gate_index
    )
    assert commands[pr155_index] == [
        python_executable,
        str(Path("tools") / "validate_agent_consumable_parameter_default_registry.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr155_index]
    assert "--output" not in commands[pr155_index]
    assert commands[pr156_index] == [
        python_executable,
        str(Path("tools") / "validate_agent_default_binding_universal_intake_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr156_index]
    assert "--output" not in commands[pr156_index]
    assert commands[pr157_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr157_index]
    assert "--output" not in commands[pr157_index]
    assert commands[pr158_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr158_owner_response_selection_readiness_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr158_index]
    assert commands[pr159_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159_official_source_completion_bridge.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159_index]
    assert commands[pr160_index] == [
        python_executable,
        str(Path("tools") / "validate_pr160_split_reclassification_route_closure.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr160_index]
    assert "--branch" not in commands[pr160_index]
    assert "--allow-main" not in commands[pr160_index]
    assert commands[pr159r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159r_source_locator_value_capture.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159r_index]
    assert "--branch" not in commands[pr159r_index]
    assert "--allow-main" not in commands[pr159r_index]
    assert commands[pr159s_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159s_open_intake_completion.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159s_index]
    assert "--branch" not in commands[pr159s_index]
    assert "--allow-main" not in commands[pr159s_index]
    assert commands[pr161a_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161a_atomicrows_pr154_value_state_materialization.py"),
        "--repo-root",
        ".",
    ]
    pr161b_index = command_names.index(
        "validate_pr161b_master_plan_residual_candidate_coverage.py"
    )
    assert commands[pr161b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161b_master_plan_residual_candidate_coverage.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr161c_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161c_qku_residual_candidate_assimilation.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr161d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr161e_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr161f_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162a_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162b_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_a_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162r_a_replay_paper_executability_classification_audit.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162d_r2a_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162d_r2a_real_formulations.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162r_generic_replay_paper_adapter_rerun.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162r_b_replay_paper_data_binding_completion.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_index] == [
        python_executable,
        str(Path("tools") / "validate_pr163_generic_paper_adapter_capture_framework.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr163_b_paired_replay_paper_concurrent_executor.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr164_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_evidence_backed_scoring_ranking.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_b_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_b_condition_scoped_negative_memory.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_c_replay_paper_memory_consumer_integration.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_d_scenario_qku_combination_selection.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_s_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_s_replay_paper_scenario_retest_execution.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sf_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sf_repair_materialization_before_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_s2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_s2_replay_paper_retest_loop_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sm2_score_memory_refresh_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sf_r2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm3_index] == [
        python_executable,
        str(Path("tools") / "validate_pr166_sm3_score_memory_refresh_v3.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_q_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_q_quantum_classical_hybrid_comparator.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_qb_index] == [
        python_executable,
        str(Path("tools") / "validate_pr166_qb_bounded_quantum_benchmark.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_qc_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_q_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_q_quantum_automapper.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr167_index] == [
        python_executable,
        str(Path("tools") / "validate_pr167_open_trade_simulator_integration.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_plugin_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_plugin_framework.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_negative_repair_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_negative_repair_factory.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_no_orphan_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_no_orphan_lineage.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_d2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr161a_index]
    assert "--write-report" not in commands[pr161b_index]
    assert "--write-report" not in commands[pr161c_index]
    assert "--write-report" not in commands[pr161d_index]
    assert "--write-report" not in commands[pr161e_index]
    assert "--write-report" not in commands[pr161f_index]
    assert "--write-report" not in commands[pr162_index]
    assert "--write-report" not in commands[pr162a_index]
    assert "--write-report" not in commands[pr162b_index]
    assert "--write-report" not in commands[pr162c_index]
    assert "--write-report" not in commands[pr162d_index]
    assert "--write-report" not in commands[pr162r_a_index]
    assert "--write-report" not in commands[pr162d_r2a_index]
    assert "--write-report" not in commands[pr162r_index]
    assert "--write-report" not in commands[pr162r_b_index]
    assert "--write-report" not in commands[pr163_index]
    assert "--write-report" not in commands[pr163_b_index]
    assert "--write-report" not in commands[pr164_index]
    assert "--write-report" not in commands[pr163_c_index]
    assert "--write-report" not in commands[pr165_index]
    assert "--write-report" not in commands[pr165_b_index]
    assert "--write-report" not in commands[pr165_c_index]
    assert "--write-report" not in commands[pr165_d_index]
    assert "--write-report" not in commands[pr166_s_index]
    assert "--write-report" not in commands[pr166_sm_index]
    assert "--write-report" not in commands[pr166_s2_index]
    assert "--write-report" not in commands[pr166_sm2_index]
    assert "--write-report" not in commands[pr166_sf_r2_index]
    assert "--write-report" not in commands[pr166_sm3_index]
    assert "--write-report" not in commands[pr166_q_index]
    assert "--write-report" not in commands[pr165_d2_index]
    assert "--branch" not in commands[pr161a_index]
    assert "--branch" not in commands[pr161b_index]
    assert "--branch" not in commands[pr161c_index]
    assert "--branch" not in commands[pr161d_index]
    assert "--branch" not in commands[pr161e_index]
    assert "--branch" not in commands[pr161f_index]
    assert "--branch" not in commands[pr162_index]
    assert "--branch" not in commands[pr162a_index]
    assert "--branch" not in commands[pr162b_index]
    assert "--branch" not in commands[pr162c_index]
    assert "--branch" not in commands[pr162d_index]
    assert "--branch" not in commands[pr162d_r2a_index]
    assert "--branch" not in commands[pr162r_a_index]
    assert "--branch" not in commands[pr162r_index]
    assert "--branch" not in commands[pr162r_b_index]
    assert "--branch" not in commands[pr163_index]
    assert "--branch" not in commands[pr164_index]
    assert "--branch" not in commands[pr163_c_index]
    assert "--branch" not in commands[pr165_index]
    assert "--branch" not in commands[pr165_b_index]
    assert "--branch" not in commands[pr165_c_index]
    assert "--branch" not in commands[pr165_d_index]
    assert "--branch" not in commands[pr166_s_index]
    assert "--branch" not in commands[pr166_sm_index]
    assert "--branch" not in commands[pr166_s2_index]
    assert "--branch" not in commands[pr166_sf_r2_index]
    assert "--branch" not in commands[pr166_sm3_index]
    assert "--branch" not in commands[pr166_q_index]
    assert "--branch" not in commands[pr165_d2_index]
    assert "--allow-main" not in commands[pr161a_index]
    assert "--allow-main" not in commands[pr161b_index]
    assert "--allow-main" not in commands[pr161c_index]
    assert "--allow-main" not in commands[pr161d_index]
    assert "--allow-main" not in commands[pr161e_index]
    assert "--allow-main" not in commands[pr161f_index]
    assert "--allow-main" not in commands[pr162_index]
    assert "--allow-main" not in commands[pr162a_index]
    assert "--allow-main" not in commands[pr162b_index]
    assert "--allow-main" not in commands[pr162c_index]
    assert "--allow-main" not in commands[pr162d_index]
    assert "--allow-main" not in commands[pr162r_a_index]
    assert "--allow-main" not in commands[pr162d_r2a_index]
    assert "--allow-main" not in commands[pr162r_index]
    assert "--allow-main" not in commands[pr162r_b_index]
    assert "--allow-main" not in commands[pr163_index]
    assert "--allow-main" not in commands[pr164_index]
    assert "--allow-main" not in commands[pr163_c_index]
    assert "--allow-main" not in commands[pr165_index]
    assert "--allow-main" not in commands[pr165_b_index]
    assert "--allow-main" not in commands[pr165_c_index]
    assert "--allow-main" not in commands[pr165_d_index]
    assert "--allow-main" not in commands[pr166_s_index]
    assert "--allow-main" not in commands[pr166_sm_index]
    assert "--allow-main" not in commands[pr166_s2_index]
    assert "--allow-main" not in commands[pr166_sf_r2_index]
    assert "--allow-main" not in commands[pr166_sm3_index]
    assert "--allow-main" not in commands[pr166_q_index]
    assert "--allow-main" not in commands[pr165_d2_index]
    assert "--output" not in commands[pr158_index]
    assert "--output" not in commands[pr159_index]
    assert "--output" not in commands[pr160_index]
    assert "--output" not in commands[pr159r_index]
    assert "--output" not in commands[pr159s_index]
    assert "--output" not in commands[pr161a_index]
    assert "--output" not in commands[pr161b_index]
    assert "--output" not in commands[pr161c_index]
    assert "--output" not in commands[pr161d_index]
    assert "--output" not in commands[pr161e_index]
    assert "--output" not in commands[pr161f_index]
    assert "--output" not in commands[pr162_index]
    assert "--output" not in commands[pr162a_index]
    assert "--output" not in commands[pr162b_index]
    assert "--output" not in commands[pr162c_index]
    assert "--output" not in commands[pr162d_index]
    assert "--output" not in commands[pr162r_a_index]
    assert "--output" not in commands[pr162d_r2a_index]
    assert "--output" not in commands[pr162r_index]
    assert "--output" not in commands[pr162r_b_index]
    assert "--output" not in commands[pr163_index]
    assert "--output" not in commands[pr163_b_index]
    assert "--output" not in commands[pr164_index]
    assert "--output" not in commands[pr163_c_index]
    assert "--output" not in commands[pr165_b_index]
    assert "--output" not in commands[pr165_c_index]
    assert "--output" not in commands[pr165_d_index]
    assert "--output" not in commands[pr166_s_index]
    assert "--output" not in commands[pr166_sm_index]
    assert "--output" not in commands[pr166_s2_index]
    assert "--output" not in commands[pr166_sf_r2_index]
    assert "--output" not in commands[pr166_sm3_index]
    assert "--output" not in commands[pr166_q_index]
    assert "--output" not in commands[pr165_d2_index]


def test_runner_validates_pr138_without_tracked_artifact_writer(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    pr138_mutating_commands = [
        command
        for command in commands
        if command[1] == str(Path("tools") / "stage1_atomicrows_semantic_row_contract_gate.py")
    ]
    pr138_non_mutating_commands = [
        command
        for command in commands
        if command[1] == "-c"
        and command[2] == runner.PR138_NON_MUTATING_VALIDATION_SCRIPT
    ]

    assert pr138_mutating_commands == []
    assert pr138_non_mutating_commands == [
        [
            python_executable,
            "-c",
            runner.PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ]
    ]
    assert "--write-report" not in pr138_non_mutating_commands[0]


def test_runner_runs_pr140_gate_before_tracked_generated_report_writers(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    scope_index = command_names.index("validate_first_pr_scope.py")
    pr138_index = next(
        index
        for index, command in enumerate(commands)
        if command[1] == "-c"
        and command[2] == runner.PR138_NON_MUTATING_VALIDATION_SCRIPT
    )
    pr139_index = command_names.index(
        "validate_atomicrows_row_family_source_manifest_currentization.py"
    )
    pr140_index = command_names.index(
        "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
    )
    pr141_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
    )
    pr142_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
    )
    owner_override_index = command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    )

    assert (
        scope_index
        < pr138_index
        < pr139_index
        < pr140_index
        < pr141_index
        < pr142_index
        < owner_override_index
    )
    assert commands[pr139_index][-2:] == [
        "--out",
        str(
            runner._default_validation_dir()
            / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
        ),
    ]
    assert commands[pr140_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr141_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr142_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
        ),
        "--repo-root",
        ".",
    ]


def test_runner_routes_generated_report_outputs_to_validation_temp(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    validation_dir = Path("validation-dir")
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands(
        validation_dir,
        Path("pytest-basetemp"),
    )

    tracked_prefixes = (
        "docs/master_plan/generated/",
        "docs/roadmap/generated/",
        "docs/master_plan/source_evidence/generated/",
    )
    for command in commands:
        for token in command:
            normalized = str(token).replace("\\", "/")
            assert not normalized.startswith(tracked_prefixes)

    command_by_name = {Path(command[1]).name: command for command in commands}
    owner_override_command = command_by_name[
        "validate_qtt_owner_global_override_authority.py"
    ]
    assert owner_override_command[-2:] == [
        "--out",
        str(
            validation_dir
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        ),
    ]
    assert "--check-only" in command_by_name[
        "validate_source_evidence_retrieval_executor.py"
    ]
    assert "--check-only" in command_by_name["validate_source_evidence_acceptance.py"]
    assert "--check-only" in command_by_name[
        "validate_source_revalidation_scheduler.py"
    ]
    assert "--check-only" in command_by_name[
        "validate_connector_semantic_binding_implementation_gate.py"
    ]
    assert "--check-only" in command_by_name[
        "runtime_cash_component_field_map_validate.py"
    ]
    assert "--check-only" in command_by_name[
        "private_state_read_receipt_gate_validate.py"
    ]
    assert "--write-artifacts" not in command_by_name[
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    ]


def test_runner_allows_routed_temp_generated_report_to_differ_from_tracked_by_default(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    with tempfile.TemporaryDirectory(prefix="qtt_pr146_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        tracked_report = (
            repo_root
            / "docs"
            / "master_plan"
            / "generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        temp_report = (
            repo_root
            / "validation"
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        tracked_report.parent.mkdir(parents=True)
        temp_report.parent.mkdir(parents=True)
        tracked_report.write_text('{"value": "tracked"}\n', encoding="utf-8")
        temp_report.write_text('{"value": "expected"}\n', encoding="utf-8")

        def fake_run(command: list[str], **kwargs) -> Completed:
            return Completed()

        monkeypatch.setattr(runner.subprocess, "run", fake_run)

        exit_code = runner.run_commands(
            [
                [
                    "python",
                    str(
                        Path("tools")
                        / "validate_qtt_owner_global_override_authority.py"
                    ),
                    "--out",
                    str(temp_report),
                ]
            ],
            repo_root=repo_root,
        )
        tracked_text = tracked_report.read_text(encoding="utf-8")

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "TRACKED_GENERATED_REPORT_STALE" not in captured.err
    assert tracked_text == '{"value": "tracked"}\n'


def test_runner_ignores_volatile_branch_context_when_comparing_temp_report(
    monkeypatch,
):
    class Completed:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    with tempfile.TemporaryDirectory(prefix="qtt_pr146_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        tracked_report = (
            repo_root
            / "docs"
            / "master_plan"
            / "generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        temp_report = (
            repo_root
            / "validation"
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        tracked_report.parent.mkdir(parents=True)
        temp_report.parent.mkdir(parents=True)
        tracked_report.write_text(
            '{"base_head": "old", "branch": "original", "value": "same"}\n',
            encoding="utf-8",
        )
        temp_report.write_text(
            '{"base_head": "new", "branch": "downstream", "value": "same"}\n',
            encoding="utf-8",
        )

        def fake_run(command: list[str], **kwargs) -> Completed:
            return Completed()

        monkeypatch.setattr(runner.subprocess, "run", fake_run)
        monkeypatch.setitem(
            runner.GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS,
            "validate_qtt_owner_global_override_authority.py",
            (
                "--out",
                "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json",
            ),
        )

        exit_code = runner.run_commands(
            [
                [
                    "python",
                    str(
                        Path("tools")
                        / "validate_qtt_owner_global_override_authority.py"
                    ),
                    "--out",
                    str(temp_report),
                ]
            ],
            repo_root=repo_root,
        )

    assert exit_code == 0


def test_runner_restores_only_runtime_side_effects_before_pr142_pr143_and_final_pytest(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(
            self,
            returncode: int = 0,
            stdout: str = "",
            stderr: str = "",
        ) -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    intended_repair_paths = [
        "tools/run_validation_gates.py",
        "tests/fail_closed/test_run_validation_gates.py",
    ]
    generated_side_effect_paths = [
        "docs/master_plan/generated/GateSideEffect.report.json",
        "tests/fixtures/atomicrows/synthetic_gate_side_effect.v1.fixture.json",
    ]
    modified_outputs = iter(
        [
            "\n".join(intended_repair_paths) + "\n",
            "\n".join([*intended_repair_paths, *generated_side_effect_paths]) + "\n",
            "\n".join([*intended_repair_paths, *generated_side_effect_paths]) + "\n",
            "\n".join(intended_repair_paths) + "\n",
            "\n".join([*intended_repair_paths, *generated_side_effect_paths]) + "\n",
            "\n".join(intended_repair_paths) + "\n",
            "\n".join([*intended_repair_paths, *generated_side_effect_paths]) + "\n",
        ]
    )
    events: list[tuple[str, list[str]]] = []
    commands = runner.build_validation_commands(
        Path("validation-dir"),
        Path("pytest-basetemp"),
    )

    def fake_run(command: list[str], **kwargs) -> Completed:
        if command[0] == "git":
            git_args = command[1:]
            events.append(("git", git_args))
            if git_args == ["ls-files", "-m"]:
                return Completed(stdout=next(modified_outputs))
            if git_args == [
                "restore",
                "--source=HEAD",
                "--worktree",
                "--",
                *generated_side_effect_paths,
            ]:
                return Completed()
            raise AssertionError(f"unexpected git command: {git_args}")

        events.append(("gate", command))
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner,
        "_routed_generated_output_currentness_failures",
        lambda command, repo_root: [],
    )

    exit_code = runner.run_commands(commands, repo_root=Path("repo-root"))

    ls_files_event = ("git", ["ls-files", "-m"])
    restore_event = (
        "git",
        [
            "restore",
            "--source=HEAD",
            "--worktree",
            "--",
            *generated_side_effect_paths,
        ],
    )
    assert exit_code == 0
    assert events[0] == ls_files_event
    assert events.count(ls_files_event) == 7
    assert restore_event in events
    assert events.count(restore_event) == 4
    assert "tools/run_validation_gates.py" not in restore_event[1]
    assert "tests/fail_closed/test_run_validation_gates.py" not in restore_event[1]
    pr142_command = next(
        command
        for command in commands
        if Path(command[1]).name == runner.PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT
    )
    pr143_command = next(
        command
        for command in commands
        if Path(command[1]).name
        == runner.PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT
    )
    restore_indices = [
        index for index, event in enumerate(events) if event == restore_event
    ]
    assert events[restore_indices[0] + 1] == ("gate", pr142_command)
    assert events[restore_indices[1] + 1] == ("gate", pr143_command)
    assert events[restore_indices[2] - 2] == ("gate", commands[-2])
    assert events[-3:] == [
        ("gate", commands[-1]),
        ls_files_event,
        restore_event,
    ]
    assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER


def test_runner_preserves_initially_modified_files_after_final_pytest(
    monkeypatch,
):
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    with tempfile.TemporaryDirectory(prefix="qtt_pr162r_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        report_rel = (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
        )
        report_path = repo_root / report_rel
        report_path.parent.mkdir(parents=True)
        report_path.write_text("updated\n", encoding="utf-8")
        modified_sets = iter([{report_rel}, {report_rel}, set()])

        def fake_run(command: list[str], **kwargs) -> Completed:
            report_path.write_text("head\n", encoding="utf-8")
            return Completed()

        monkeypatch.setattr(
            runner, "_tracked_modified_paths", lambda repo_root: next(modified_sets)
        )
        monkeypatch.setattr(runner.subprocess, "run", fake_run)
        monkeypatch.setattr(
            runner,
            "_routed_generated_output_currentness_failures",
            lambda command, repo_root: [],
        )

        command = [
            runner.sys.executable,
            str(Path("tools") / runner.PYTEST_FRESH_BASETEMP_SCRIPT),
        ]
        assert runner.run_commands([command], repo_root=repo_root) == 0
        assert report_path.read_text(encoding="utf-8") == "updated\n"


def test_runner_includes_qtt_pr_identity_roster_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    active_registry_index = command_names.index(
        "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
    )
    roster_index = command_names.index("validate_qtt_pr_identity_roster.py")
    controller_index = command_names.index(
        "validate_qtt_roadmap_execution_state_controller.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )

    assert active_registry_index < roster_index < controller_index < pr100_index
    assert commands[roster_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        "--report-out",
        _default_temp_generated_report("QttPrIdentityRoster.report.json"),
    ]


def test_runner_includes_pr130_private_state_receipt_gate_after_runtime_cash(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    runtime_cash_index = command_names.index("runtime_cash_component_field_map_validate.py")
    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert runtime_cash_index < private_state_index < no_runtime_index
    assert commands[private_state_index] == [
        python_executable,
        str(Path("tools") / "private_state_read_receipt_gate_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr131_credential_readiness_gate_after_private_state(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert private_state_index < credential_index < no_runtime_index
    assert commands[credential_index] == [
        python_executable,
        str(Path("tools") / "credential_alias_secret_no_capture_readiness_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr132_market_data_ingest_after_pr131_credential_readiness(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert credential_index < market_data_index < connector_index
    assert commands[market_data_index] == [
        python_executable,
        str(Path("tools") / "venue_market_data_ingest_adapters_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr133_snapshot_builder_after_pr132_market_data_ingest(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    snapshot_index = command_names.index(
        "orderbook_event_state_snapshot_builder_validate.py"
    )
    runtime_resolver_index = command_names.index(
        "runtime_resolver_snapshot_executor_validate.py"
    )
    policy_drift_index = command_names.index(
        "validate_historical_dataset_policy_literal_drift.py"
    )
    historical_dataset_index = command_names.index(
        "validate_historical_dataset_digest_and_loader.py"
    )
    pr136_policy_drift_index = command_names.index(
        "validate_pr136_roadmap_policy_literal_drift.py"
    )
    pr136_roadmap_index = command_names.index(
        "validate_pr136_day1_launch_readiness_roadmap.py"
    )
    pr137_integrity_index = command_names.index(
        "validate_pr137_generated_integrity_authority_boundary.py"
    )
    pr137_controller_index = command_names.index(
        "validate_pr137_launch_readiness_dependency_controller.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert (
        market_data_index
        < snapshot_index
        < runtime_resolver_index
        < policy_drift_index
        < historical_dataset_index
        < pr136_policy_drift_index
        < pr136_roadmap_index
        < pr137_integrity_index
        < pr137_controller_index
        < connector_index
    )
    assert commands[snapshot_index] == [
        python_executable,
        str(Path("tools") / "orderbook_event_state_snapshot_builder_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]
    assert commands[runtime_resolver_index] == [
        python_executable,
        str(Path("tools") / "runtime_resolver_snapshot_executor_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]
    assert commands[policy_drift_index] == [
        python_executable,
        str(Path("tools") / "validate_historical_dataset_policy_literal_drift.py"),
        "--repo-root",
        ".",
    ]
    assert commands[historical_dataset_index] == [
        python_executable,
        str(Path("tools") / "validate_historical_dataset_digest_and_loader.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr136_policy_drift_index] == [
        python_executable,
        str(Path("tools") / "validate_pr136_roadmap_policy_literal_drift.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr136_roadmap_index] == [
        python_executable,
        str(Path("tools") / "validate_pr136_day1_launch_readiness_roadmap.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_integrity_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
        "--repo-root",
        ".",
    ]


def test_runner_includes_pr137_validators_after_pr136_and_before_downstream_static_gates(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr136_policy_drift_index = command_names.index(
        "validate_pr136_roadmap_policy_literal_drift.py"
    )
    pr136_roadmap_index = command_names.index(
        "validate_pr136_day1_launch_readiness_roadmap.py"
    )
    pr137_integrity_index = command_names.index(
        "validate_pr137_generated_integrity_authority_boundary.py"
    )
    pr137_controller_index = command_names.index(
        "validate_pr137_launch_readiness_dependency_controller.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert command_names.count("validate_pr137_generated_integrity_authority_boundary.py") == 1
    assert command_names.count("validate_pr137_launch_readiness_dependency_controller.py") == 1
    assert (
        pr136_policy_drift_index
        < pr136_roadmap_index
        < pr137_integrity_index
        < pr137_controller_index
        < connector_index
    )
    assert commands[pr137_integrity_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
        "--repo-root",
        ".",
    ]


def test_cumulative_gate_calls_validate_historical_dataset_digest_and_loader(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_historical_dataset_digest_and_loader.py" in command_names


def test_cumulative_gate_calls_policy_literal_drift_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_historical_dataset_policy_literal_drift.py" in command_names


def test_cumulative_gate_calls_pr136_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_pr136_day1_launch_readiness_roadmap.py" in command_names


def test_cumulative_gate_calls_pr136_policy_literal_drift_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_pr136_roadmap_policy_literal_drift.py" in command_names


def _assert_pr135_gate_failure_stops(monkeypatch, capsys, failing_name: str) -> None:
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_historical_dataset_policy_literal_drift.py"],
        ["python", "validate_historical_dataset_digest_and_loader.py"],
        ["python", "later_gate.py"],
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(51 if command[1] == failing_name else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 51
    assert seen == commands[: len(seen)]
    assert seen[-1][1] == failing_name
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_cumulative_gate_fails_when_pr135_report_missing(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_pr135_schema_invalid(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_pr135_marker_absent(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_validator_emits_marker_with_forbidden_authority_flag(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_owner_verified_placeholders_remain(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_policy_literal_drift_exists(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_atomicrows_bundle_or_sha_diff_exists(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_master_plan_diff_exists_for_unauthorized_edit(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_repo_pr135_maps_to_roadmap_pr135(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_source_acceptance_or_connector_binding_appears(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_quantum_execution_or_optimizer_input_appears(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def _assert_pr136_gate_failure_stops(monkeypatch, capsys, failing_name: str) -> None:
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_pr136_roadmap_policy_literal_drift.py"],
        ["python", "validate_pr136_day1_launch_readiness_roadmap.py"],
        ["python", "later_gate.py"],
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(61 if command[1] == failing_name else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 61
    assert seen[-1][1] == failing_name
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_cumulative_gate_fails_when_pr136_reports_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_pr136_marker_absent(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_pr135_currentization_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_same_number_inference_true(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_domain_count_hardcoded_to_13(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_roadmap_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_arbitrary_domain_count_forced(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_fixed_13_domain_model_used(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_roadmap_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_derived_domain_evidence_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_provisional_pr_unclassified(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_classification_evidence_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_domain_map_missing_entry(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_dependency_graph_cycle_exists(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_market_scope_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_atomicrows_bundle_sha_diff_exists(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_master_plan_diff_exists(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_source_or_connector_authority_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_replay_paper_order_profit_live_authority_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_quantum_execution_or_advantage_claim_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_agent_authority_escalates(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_live_hot_path_accepts_control_plane_call(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_day1_launch_marked_started(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_runner_fails_closed_if_pr134_runtime_resolver_snapshot_executor_fails(
    monkeypatch,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "orderbook_event_state_snapshot_builder_validate.py"],
        ["python", "runtime_resolver_snapshot_executor_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 1, 0]
    seen = []

    def fake_run(command, cwd=None):
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 1
    assert seen == commands[:2]


def test_runner_fails_closed_if_pr131_credential_readiness_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "private_state_read_receipt_gate_validate.py"],
        ["python", "credential_alias_secret_no_capture_readiness_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 41, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 41
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_fails_closed_if_pr132_market_data_ingest_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "credential_alias_secret_no_capture_readiness_validate.py"],
        ["python", "venue_market_data_ingest_adapters_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 42, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 42
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_fails_closed_if_pr133_snapshot_builder_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "venue_market_data_ingest_adapters_validate.py"],
        ["python", "orderbook_event_state_snapshot_builder_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 43, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 43
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_invokes_pytest_through_fresh_basetemp_helper(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    pytest_basetemp = Path(".tmp") / "run_validation_gates_pytest_123"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands(pytest_basetemp=pytest_basetemp)

    assert commands[-1] == [
        python_executable,
        str(Path("tools") / "run_pytest_fresh_basetemp.py"),
        "tests",
        "-q",
        "--ignore",
        str(
            Path("tests")
            / "source_evidence"
            / "test_controlled_official_source_capture_candidate_packets.py"
        ),
        runner.PYTEST_DURATIONS_ARG,
        "--basetemp",
        str(pytest_basetemp),
    ]


def test_runner_includes_owner_global_override_authority_dev_gate(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    scope_index = command_names.index("validate_first_pr_scope.py")
    owner_override_index = command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    )
    owner_override_currentization_index = command_names.index(
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    )
    agent_charter_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )
    algorithm_registry_index = command_names.index(
        "validate_qtt_algorithm_formula_family_registry.py"
    )
    agent_algorithm_binding_index = command_names.index(
        "validate_qtt_agent_algorithm_binding_registry.py"
    )
    agent_algorithm_consumer_gate_index = command_names.index(
        "validate_qtt_agent_algorithm_consumer_gate.py"
    )
    agent_algorithm_cumulative_readiness_index = command_names.index(
        "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"
    )
    agent_algorithm_command_matrix_index = command_names.index(
        "validate_qtt_agent_algorithm_command_matrix.py"
    )
    source_evidence_index = command_names.index("validate_source_evidence_static.py")

    assert (
        scope_index
        < owner_override_index
        < owner_override_currentization_index
        < agent_charter_index
        < algorithm_registry_index
        < agent_algorithm_binding_index
        < agent_algorithm_consumer_gate_index
        < agent_algorithm_cumulative_readiness_index
        < agent_algorithm_command_matrix_index
        < source_evidence_index
    )
    assert commands[owner_override_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTOwnerGlobalOverrideAuthority.report.json"),
    ]
    assert commands[owner_override_currentization_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[agent_charter_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentRoleOperatingCharterReport.json"),
    ]
    assert commands[algorithm_registry_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAlgorithmFormulaFamilyReport.json"),
    ]
    assert commands[agent_algorithm_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmBindingReport.json"),
    ]
    assert commands[agent_algorithm_consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmConsumerGate.report.json"),
    ]
    assert commands[agent_algorithm_cumulative_readiness_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report(
            "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[agent_algorithm_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmCommandMatrix.json"),
    ]


def test_runner_exposes_agent_algorithm_command_matrix_success_marker():
    assert command_matrix_gate.SUCCESS_MARKER == "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_OK"


def test_runner_exposes_atomicrows_research_provenance_success_marker():
    assert (
        research_provenance_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_OK"
    )


def test_runner_exposes_owner_submitted_research_source_intake_success_marker():
    assert (
        owner_intake_gate.SUCCESS_MARKER
        == "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_OK"
    )


def test_runner_exposes_research_source_to_candidate_family_gate_success_marker():
    assert (
        candidate_family_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_OK"
    )


def test_runner_exposes_parameter_stack_role_taxonomy_success_marker():
    assert (
        parameter_stack_role_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
    )


def test_runner_exposes_parameter_stack_completeness_gate_success_marker():
    assert (
        parameter_stack_completeness_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
    )


def test_runner_exposes_parameter_stack_compatibility_gate_success_marker():
    assert (
        parameter_stack_compatibility_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
    )


def test_runner_exposes_edge_parameter_stack_selection_packet_success_marker():
    assert edge_packet_gate.SUCCESS_MARKER == "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"


def test_runner_exposes_qtt_trade_context_packet_success_marker():
    assert trade_context_gate.SUCCESS_MARKER == "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK"


def test_runner_exposes_parameter_selection_universe_consumer_gate_success_marker():
    assert (
        selection_universe_consumer_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK"
    )


def test_runner_exposes_trade_context_selection_universe_routing_gate_success_marker():
    assert (
        trade_context_routing_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK"
    )


def test_runner_exposes_quantum_applicability_classification_registry_success_marker():
    assert (
        quantum_applicability_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
    )


def test_runner_exposes_owner_quantum_priority_policy_registry_success_marker():
    assert (
        owner_quantum_priority_gate.SUCCESS_MARKER
        == "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_algorithm_scoring_policy_registry_success_marker():
    assert (
        scoring_policy_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_stack_scoring_and_ranking_gate_success_marker():
    assert (
        stack_scoring_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK"
    )


def test_runner_exposes_quantum_classical_optimizer_arbitration_gate_success_marker():
    assert (
        optimizer_arbitration_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK"
    )


def test_runner_exposes_candidate_parameter_stack_generation_gate_success_marker():
    assert (
        candidate_generation_gate.SUCCESS_MARKER
        == "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK"
    )


def test_runner_exposes_trade_context_parameter_stack_selection_gate_success_marker():
    assert (
        trade_context_stack_selection_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK"
    )


def test_runner_exposes_selected_parameter_stack_handoff_packet_success_marker():
    assert (
        selected_stack_handoff_gate.SUCCESS_MARKER
        == "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_OK"
    )


def test_runner_exposes_replay_paper_candidate_stack_competition_gate_success_marker():
    assert (
        replay_paper_competition_gate.SUCCESS_MARKER
        == "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_OK"
    )


def test_runner_exposes_dual_result_review_for_parameter_stacks_success_marker():
    assert (
        dual_result_review_gate.SUCCESS_MARKER
        == "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_live_promotion_review_for_parameter_stacks_success_marker():
    assert (
        owner_live_promotion_review_gate.SUCCESS_MARKER
        == "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_approval_request_queue_registry_success_marker():
    assert (
        owner_approval_request_queue_gate.SUCCESS_MARKER
        == "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    )


def test_runner_exposes_owner_override_receipt_authoring_gate_success_marker():
    assert (
        owner_override_receipt_authoring_gate.SUCCESS_MARKER
        == "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
    )


def test_pr153r_repair_branch_is_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153R_REPAIR_BRANCH,
            after_pr=138,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153R_REPAIR_BRANCH,
            after_pr=153,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "repair-pr999-unapproved",
            after_pr=138,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "feature/non-downstream-validation",
            after_pr=138,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153R_REPAIR_BRANCH,
            "tools/ci_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153R_REPAIR_BRANCH,
            "tools/run_validation_gates.py",
        )
        is False
    )


def test_pr153s_repair_branch_is_narrow_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153S_REPAIR_BRANCH,
            after_pr=152,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153S_REPAIR_BRANCH,
            after_pr=153,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "repair/pr999-unapproved",
            after_pr=152,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr153s_source_value_capture_closure_classifier/report.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "tests/atomicrows/"
            "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "docs/master_plan/QTT_MasterPlan_Current.md",
        )
        is False
    )


def test_pr163_c_main_context_repair_branch_is_narrow_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=159,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=160,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=161,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=162,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=163,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            after_pr=160,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            after_pr=163,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/"
            "test_pr159r_branch_context_relaxation.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "source_intelligence/pr159s_open_intake/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "source_intelligence/test_pr159s_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "pr161a_materialization_bridge/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "test_pr161a_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/"
            "test_pr161b_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
            "validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/"
            "test_pr163_c_repeat_run_determinism.py",
        )
        is True
    )
    atomicrows_bundle_path = (
        "docs/master_plan/atomic_rows/" + "AtomicRows" + ".bundle" + ".jsonl"
    )
    atomicrows_sidecar_path = (
        "docs/master_plan/atomic_rows/"
        + "AtomicRows"
        + ".bundle"
        + "."
        + "sha256"
    )
    forbidden_repair_paths = (
        "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/PR163_C_RuntimeCashAuthority.report.json",
        atomicrows_bundle_path,
        atomicrows_sidecar_path,
        "docs/master_plan/source_evidence/accepted_source_packet.json",
        "src/qtt/source_evidence/connector_binding.py",
        "src/qtt/stage1_prediction_markets/private_state/account_snapshot.py",
        "src/qtt/stage1_prediction_markets/runtime_cash/cash_state.py",
        "src/qtt/stage1_prediction_markets/order_live/live_order_router.py",
        "src/qtt/stage1_prediction_markets/quantum_backend/backend_runtime.py",
        "src/qtt/stage1_prediction_markets/llm_runtime/model_client.py",
        "src/qtt/stage1_prediction_markets/freeze_checksum/qku_digest.py",
        "src/qtt/stage1_prediction_markets/profit_claims/profit_summary.py",
    )
    for forbidden_path in forbidden_repair_paths:
        assert (
            ci_branch_context.is_explicit_downstream_repair_changed_path(
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                forbidden_path,
            )
            is False
        )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
        )
        is False
    )


def test_pr93_pr94_metadata_allow_pr153r_repair_downstream_branch(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    fake_git_stdout = _owner_gate_git_metadata_responses(PR153R_REPAIR_BRANCH)
    monkeypatch.setattr(owner_approval_request_queue_gate, "_git_stdout", fake_git_stdout)
    monkeypatch.setattr(owner_override_receipt_authoring_gate, "_git_stdout", fake_git_stdout)

    pr93_failures, pr93_metadata = (
        owner_approval_request_queue_gate.validate_pr93_roadmap_metadata(Path("."))
    )
    pr94_failures, pr94_metadata = (
        owner_override_receipt_authoring_gate.validate_pr94_roadmap_metadata(Path("."))
    )

    assert pr93_failures == []
    assert pr94_failures == []
    assert pr93_metadata["branch"] == PR153R_REPAIR_BRANCH
    assert pr94_metadata["branch"] == PR153R_REPAIR_BRANCH
    assert (
        owner_approval_request_queue_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        in pr93_metadata["ci_info_lines"]
    )
    assert (
        owner_override_receipt_authoring_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        in pr94_metadata["ci_info_lines"]
    )


def test_pr93_pr94_metadata_still_reject_arbitrary_branch(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    branch = "feature/non-downstream-validation"
    fake_git_stdout = _owner_gate_git_metadata_responses(branch)
    monkeypatch.setattr(owner_approval_request_queue_gate, "_git_stdout", fake_git_stdout)
    monkeypatch.setattr(owner_override_receipt_authoring_gate, "_git_stdout", fake_git_stdout)

    pr93_failures, pr93_metadata = (
        owner_approval_request_queue_gate.validate_pr93_roadmap_metadata(Path("."))
    )
    pr94_failures, pr94_metadata = (
        owner_override_receipt_authoring_gate.validate_pr94_roadmap_metadata(Path("."))
    )

    assert (
        f"current branch must be {owner_approval_request_queue_gate.TARGET_BRANCH}, "
        f"got {branch}"
    ) in pr93_failures
    assert (
        f"current branch must be {owner_override_receipt_authoring_gate.TARGET_BRANCH}, "
        f"got {branch}"
    ) in pr94_failures
    assert pr93_metadata["branch"] == branch
    assert pr94_metadata["branch"] == branch


def test_runner_exposes_owner_dashboard_approval_menu_schema_success_marker():
    assert (
        owner_dashboard_approval_menu_schema_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"
    )


def test_runner_exposes_owner_dashboard_approval_static_screen_contract_success_marker():
    assert (
        owner_dashboard_approval_static_screen_contract_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_OK"
    )


def test_runner_exposes_atomicrows_full_bundle_row_expansion_plan_success_marker():
    assert (
        atomicrows_full_bundle_row_expansion_plan_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_OK"
    )


def test_runner_exposes_atomicrows_bundle_row_family_source_files_success_marker():
    assert (
        atomicrows_bundle_row_family_source_files_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_OK"
    )


def test_runner_exposes_atomicrows_bundle_builder_success_marker():
    assert (
        atomicrows_bundle_builder_deterministic_assembly_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_BUILDER_OK"
    )


def test_runner_exposes_active_non_sha_gate_registry_success_marker():
    assert (
        qtt_active_non_sha_day1_gate_state_registry_contract.SUCCESS_MARKER
        == "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_OK"
    )


def test_runner_exposes_roadmap_execution_state_controller_success_marker():
    assert (
        qtt_roadmap_execution_state_controller.SUCCESS_MARKER
        == "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK"
    )


def test_runner_exposes_atomicrows_bundle_sha_freeze_authority_gate_success_marker():
    assert (
        atomicrows_bundle_sha_freeze_authority_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_BLOCKED_OK"
    )


def test_runner_exposes_atomicrows_exact_row_authority_classifier_bridge_success_marker():
    assert (
        atomicrows_exact_row_authority_classifier_bridge.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_OK"
    )


def test_runner_exposes_atomicrows_exact_row_expansion_manifest_success_marker():
    assert (
        atomicrows_exact_row_expansion_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_OK"
    )


def test_runner_exposes_atomicrows_exact_row_generator_dry_run_success_marker():
    assert (
        atomicrows_exact_row_generator_dry_run_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_OK"
    )


def test_runner_exposes_atomicrows_repair_chain_grand_debug_logic_audit_success_marker():
    assert (
        atomicrows_repair_chain_grand_debug_logic_audit_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_OK"
    )


def test_runner_exposes_atomicrows_exact_row_source_materialization_success_marker():
    assert (
        atomicrows_exact_row_source_materialization_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_OK"
    )


def test_runner_exposes_atomicrows_exact_row_agent_family_eligibility_matrix_success_marker():
    assert (
        atomicrows_exact_row_agent_family_eligibility_matrix.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_OK"
    )


def test_runner_exposes_atomicrows_bundle_materialization_success_marker():
    assert (
        atomicrows_bundle_materialization_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_OK"
    )


def test_runner_exposes_atomicrows_bundle_boundary_state_contract_success_marker():
    assert (
        atomicrows_bundle_boundary_state_contract.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT_OK"
    )


def test_runner_does_not_use_direct_python_m_pytest(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(command[:3] == [python_executable, "-m", "pytest"] for command in commands)


def test_runner_does_not_use_direct_pytest_command(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(
        Path(token).name.lower() in {"pytest", "pytest.exe"}
        for command in commands
        for token in command
    )


def test_runner_includes_no_runtime_artifact_flags(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    no_runtime_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_no_runtime_artifacts.py")
    )

    assert "--forbid-source-retrieval" in no_runtime_command
    assert "--forbid-source-acceptance" in no_runtime_command
    assert "--forbid-connector-binding" in no_runtime_command
    assert "--forbid-private-state-fetch" in no_runtime_command
    assert "--forbid-order-execution" in no_runtime_command
    assert "--forbid-neural-training" in no_runtime_command
    assert "--forbid-neural-inference" in no_runtime_command
    assert "--forbid-external-repo-clone" in no_runtime_command
    assert "--forbid-package-install-scripts" in no_runtime_command


def test_runner_keeps_scope_runtime_live_order_profit_and_source_blocks(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    scope_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_first_pr_scope.py")
    )

    assert "--block-runtime" in scope_command
    assert "--block-live" in scope_command
    assert "--block-profit-claims" in scope_command
    assert "--block-source-retrieval" in scope_command
    assert "--block-source-acceptance" in scope_command
    assert "--block-connector-binding" in scope_command
    assert "--block-order-execution" in scope_command


def test_runner_orders_owner_intake_after_pr70_classifier(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
    )
    trade_context_index = command_names.index("validate_qtt_trade_context_packet.py")
    selection_universe_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
        < trade_context_index
        < selection_universe_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr70_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterStackRoleTaxonomy.report.json"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]
    assert commands[trade_context_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    assert commands[selection_universe_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]


def test_runner_pr74_completeness_gate_has_no_runtime_source_or_bundle_args(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )

    assert pr70_index < pr71_index < pr72_index < pr73_index < pr74_index
    assert commands[pr74_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    pr74_text = " ".join(commands[pr74_index]).lower()
    assert "source-retrieval" not in pr74_text
    assert "source-acceptance" not in pr74_text
    assert "connector" not in pr74_text
    assert "runtime" not in pr74_text
    assert "live" not in pr74_text
    assert "order" not in pr74_text
    assert "profit" not in pr74_text
    assert "atomicrows.bundle.jsonl" not in pr74_text
    assert "atomicrows.bundle.sha256" not in pr74_text


def test_runner_includes_pr75_compatibility_gate_after_pr74_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr75_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]


def test_runner_pr75_compatibility_gate_has_no_runtime_source_connector_or_future_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr75_command = commands[
        command_names.index("validate_atomicrows_parameter_stack_compatibility_gate.py")
    ]

    assert pr75_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    pr75_text = " ".join(pr75_command).lower()
    assert "source-retrieval" not in pr75_text
    assert "source-acceptance" not in pr75_text
    assert "connector" not in pr75_text
    assert "runtime" not in pr75_text
    assert "live" not in pr75_text
    assert "order" not in pr75_text
    assert "profit" not in pr75_text
    assert "replay" not in pr75_text
    assert "paper" not in pr75_text
    assert "quantum-backend" not in pr75_text
    assert "quantum-advantage" not in pr75_text
    assert "ranking" not in pr75_text
    assert "scoring" not in pr75_text
    assert "selection" not in pr75_text
    assert "arbitration" not in pr75_text
    assert "trade-context" not in pr75_text
    assert "candidate-stack" not in pr75_text
    assert "atomicrows.bundle.jsonl" not in pr75_text
    assert "atomicrows.bundle.sha256" not in pr75_text


def test_pr75_static_contract_preserves_no_claim_boundaries():
    production = parameter_stack_compatibility_gate.load_yaml(
        parameter_stack_compatibility_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_compatibility_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert flags["creates_profit_evidence"] is False
    assert flags["creates_replay_results"] is False
    assert flags["creates_paper_results"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert flags["creates_quantum_backend_evidence"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert flags["creates_quantum_advantage_claim"] is False
    assert flags["creates_scoring"] is False
    assert flags["creates_ranking"] is False
    assert flags["creates_stack_selection"] is False
    assert flags["creates_optimizer_arbitration"] is False
    assert flags["creates_trade_context_routing"] is False
    assert flags["creates_candidate_stack_generation"] is False
    assert future["this_gate_performs_scoring"] is False
    assert future["this_gate_performs_ranking"] is False
    assert future["this_gate_performs_selection"] is False
    assert future["this_gate_performs_arbitration"] is False
    assert future["this_gate_routes_trade_context"] is False
    assert future["this_gate_executes_replay_or_paper"] is False
    assert future["this_gate_executes_runtime_or_live"] is False
    assert (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_JSONL
    ).exists()
    assert not (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_SHA256
    ).exists()


def test_runner_includes_pr77_edge_packet_after_pr75_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
    )
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]


def test_runner_includes_pr78_trade_context_packet_after_pr77_and_before_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < generated_gate_index
    )
    assert commands[pr78_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    assert commands[pr79_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]


def test_runner_pr77_edge_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr77_command = commands[
        command_names.index("validate_edge_parameter_stack_selection_packet.py")
    ]

    assert pr77_command == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]
    pr77_text = " ".join(pr77_command).lower()
    assert "source-retrieval" not in pr77_text
    assert "source-acceptance" not in pr77_text
    assert "connector-binding" not in pr77_text
    assert "runtime-live" not in pr77_text
    assert "live-use" not in pr77_text
    assert "order-authority" not in pr77_text
    assert "profit-evidence" not in pr77_text
    assert "replay-execution" not in pr77_text
    assert "paper-execution" not in pr77_text
    assert "quantum-backend" not in pr77_text
    assert "quantum-advantage" not in pr77_text
    assert "atomicrows.bundle.jsonl" not in pr77_text
    assert "atomicrows.bundle.sha256" not in pr77_text


def test_pr77_static_contract_preserves_no_claim_boundaries():
    production = edge_packet_gate.load_yaml(edge_packet_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_advisory_policy"]
    source = production["source_evidence_boundary_policy"]
    bundle = production["atomicrows_bundle_boundary_policy"]
    readiness = production["production_readiness"]
    static_policy = production["static_packet_policy"]

    assert production["selected_stack_id"] == "SYNTHETIC_SELECTED_STACK_ID_SCHEMA_FIELD_ONLY"
    assert production["candidate_stack_generation_count"] == 0
    assert production["replay_paper_competition_required_flag"] is True
    assert production["owner_review_required_flag"] is True
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert source["source_dependency_state_is_static_metadata_only"] is True
    assert bundle["atomicrows_bundle_digest_ref_static_placeholder_allowed"] is True
    assert bundle["atomicrows_bundle_file_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_sha_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_hash_authority_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_rows_created_by_this_pr"] is False
    assert quantum["selected_quantum_advisory_family_ids_required"] is True
    assert quantum["quantum_advisory_static_metadata_only"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_scoring_created"] is False
    assert quantum["quantum_ranking_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["edge_parameter_stack_selection_packet_schema_ready"] is True
    assert readiness["production_edge_packet_evaluated"] is False
    assert readiness["production_edge_packet_ready"] is False
    assert readiness["production_stack_selected"] is False
    assert readiness["final_ready"] is False
    assert static_policy["selected_stack_id_is_static_schema_field_only"] is True
    assert all(flags[field] is False for field in edge_packet_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in edge_packet_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / edge_packet_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / edge_packet_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr78_trade_context_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr78_command = commands[command_names.index("validate_qtt_trade_context_packet.py")]

    assert pr78_command == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    pr78_text = " ".join(pr78_command).lower()
    assert "source-retrieval" not in pr78_text
    assert "source-acceptance" not in pr78_text
    assert "connector-binding" not in pr78_text
    assert "runtime-live" not in pr78_text
    assert "live-use" not in pr78_text
    assert "order-authority" not in pr78_text
    assert "profit-evidence" not in pr78_text
    assert "replay-execution" not in pr78_text
    assert "paper-execution" not in pr78_text
    assert "quantum-backend" not in pr78_text
    assert "quantum-advantage" not in pr78_text
    assert "atomicrows.bundle.jsonl" not in pr78_text
    assert "atomicrows.bundle.sha256" not in pr78_text


def test_pr78_static_contract_preserves_no_claim_boundaries():
    production = trade_context_gate.load_yaml(trade_context_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_priority_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    readiness = production["production_readiness"]
    context = production["context_static_policy"]

    assert context["trade_context_is_static_schema_only"] is True
    assert context["trade_context_routes_selection_universe"] is False
    assert context["trade_context_selects_stack"] is False
    assert context["trade_context_scores_stack"] is False
    assert context["trade_context_ranks_stack"] is False
    assert context["trade_context_arbitrates_optimizer"] is False
    assert context["trade_context_executes_replay_or_paper"] is False
    assert context["trade_context_executes_runtime_or_live"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["qtt_trade_context_packet_schema_ready"] is True
    assert readiness["production_trade_context_evaluated"] is False
    assert readiness["production_trade_context_ready"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(flags[field] is False for field in trade_context_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in trade_context_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert (Path(".") / trade_context_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / trade_context_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / trade_context_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr79_selection_universe_registry_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr79_command = commands[
        command_names.index("validate_atomicrows_parameter_selection_universe_registry.py")
    ]

    assert pr79_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]
    pr79_text = " ".join(pr79_command).lower()
    assert "source-retrieval" not in pr79_text
    assert "source-acceptance" not in pr79_text
    assert "connector-binding" not in pr79_text
    assert "runtime-live" not in pr79_text
    assert "live-use" not in pr79_text
    assert "order-authority" not in pr79_text
    assert "profit-evidence" not in pr79_text
    assert "replay-execution" not in pr79_text
    assert "paper-execution" not in pr79_text
    assert "quantum-backend" not in pr79_text
    assert "quantum-advantage" not in pr79_text
    assert "consumer-gate" not in pr79_text
    assert "routing-gate" not in pr79_text
    assert "score" not in pr79_text
    assert "ranking" not in pr79_text
    assert "arbitration" not in pr79_text
    assert "candidate-stack" not in pr79_text
    assert "atomicrows.bundle.jsonl" not in pr79_text
    assert "atomicrows.bundle.sha256" not in pr79_text


def test_pr79_static_contract_preserves_no_claim_boundaries():
    production = selection_universe_gate.load_yaml(
        selection_universe_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    flags = production["explicit_no_claim_flags"]
    static = production["registry_static_policy"]
    membership = production["universe_membership_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_universe_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_created"] is False
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert static["member_row_ids_created"] is False
    assert membership["membership_uses_random_sampling"] is False
    assert membership["membership_evaluated_against_live_data"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_selection_universe_consumer_gate"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["atomicrows_parameter_selection_universe_registry_ready"] is True
    assert readiness["production_selection_universe_registry_evaluated"] is False
    assert readiness["production_selection_universe_registry_ready"] is False
    assert readiness["production_universe_membership_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_includes_pr80_pr81_pr82_pr83_pr84_pr85_pr86_pr87_pr88_pr89_pr90_pr91_pr92_and_pr93_gates_after_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    pr80_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
    )
    pr81_index = command_names.index(
        "validate_trade_context_selection_universe_routing_gate.py"
    )
    pr82_index = command_names.index(
        "validate_quantum_applicability_classification_registry.py"
    )
    pr83_index = command_names.index(
        "validate_owner_quantum_priority_policy_registry.py"
    )
    pr84_index = command_names.index(
        "validate_parameter_algorithm_scoring_policy_registry.py"
    )
    pr85_index = command_names.index(
        "validate_parameter_stack_scoring_and_ranking_gate.py"
    )
    pr86_index = command_names.index(
        "validate_quantum_classical_optimizer_arbitration_gate.py"
    )
    pr87_index = command_names.index(
        "validate_candidate_parameter_stack_generation_gate.py"
    )
    pr88_index = command_names.index(
        "validate_trade_context_parameter_stack_selection_gate.py"
    )
    pr89_index = command_names.index(
        "validate_selected_parameter_stack_handoff_packet.py"
    )
    pr90_index = command_names.index(
        "validate_replay_paper_candidate_stack_competition_gate.py"
    )
    pr91_index = command_names.index(
        "validate_dual_result_review_for_parameter_stacks.py"
    )
    pr92_index = command_names.index(
        "validate_owner_live_promotion_review_for_parameter_stacks.py"
    )
    pr93_index = command_names.index(
        "validate_owner_approval_request_queue_registry.py"
    )
    pr94_index = command_names.index(
        "validate_owner_override_receipt_authoring_gate.py"
    )
    pr95_index = command_names.index(
        "validate_owner_dashboard_approval_menu_schema.py"
    )
    pr96_index = command_names.index(
        "validate_owner_dashboard_approval_static_screen_contract.py"
    )
    pr97_index = command_names.index(
        "validate_atomicrows_full_bundle_row_expansion_plan.py"
    )
    pr98_index = command_names.index(
        "validate_atomicrows_bundle_row_family_source_files.py"
    )
    pr99_index = command_names.index(
        "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
    )
    sha_dormancy_index = command_names.index(
        "validate_atomicrows_sha_system_dormancy_state_contract.py"
    )
    final_readiness_dependency_policy_index = command_names.index(
        "validate_qtt_final_readiness_dependency_policy_contract.py"
    )
    active_non_sha_gate_registry_index = command_names.index(
        "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
    )
    pr_identity_roster_index = command_names.index(
        "validate_qtt_pr_identity_roster.py"
    )
    roadmap_execution_state_controller_index = command_names.index(
        "validate_qtt_roadmap_execution_state_controller.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )
    repair_bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    repair_c0_index = command_names.index(
        "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
    )
    repair_manifest_index = command_names.index(
        "validate_atomicrows_exact_row_expansion_manifest.py"
    )
    repair_dry_run_index = command_names.index(
        "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
    )
    repair_c1_index = command_names.index(
        "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
    )
    repair_d_index = command_names.index(
        "validate_atomicrows_exact_row_source_materialization_manifest.py"
    )
    repair_d2_e0_index = command_names.index(
        "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
    )
    bundle_materialization_index = command_names.index(
        "validate_atomicrows_bundle_materialization_manifest.py"
    )
    bundle_boundary_index = command_names.index(
        "validate_atomicrows_bundle_boundary_state_contract.py"
    )
    sha_freeze_final_readiness_state_index = command_names.index(
        "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < pr80_index
        < pr81_index
        < pr82_index
        < pr83_index
        < pr84_index
        < pr85_index
        < pr86_index
        < pr87_index
        < pr88_index
        < pr89_index
        < pr90_index
        < pr91_index
        < pr92_index
        < pr93_index
        < pr94_index
        < pr95_index
        < pr96_index
        < pr97_index
        < pr98_index
        < pr99_index
        < sha_dormancy_index
        < final_readiness_dependency_policy_index
        < active_non_sha_gate_registry_index
        < pr_identity_roster_index
        < roadmap_execution_state_controller_index
        < pr100_index
        < repair_bridge_index
        < repair_manifest_index
        < repair_c0_index
        < repair_dry_run_index
        < repair_c1_index
        < repair_d_index
        < repair_d2_e0_index
        < bundle_materialization_index
        < bundle_boundary_index
        < sha_freeze_final_readiness_state_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr80_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
        ),
    ]
    assert commands[pr81_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_trade_context_selection_universe_routing_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
        ),
    ]
    assert commands[pr82_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "QuantumApplicabilityClassificationRegistry.report.json"
        ),
    ]
    assert commands[pr83_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerQuantumPriorityPolicyRegistry.report.json"),
    ]
    assert commands[pr84_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
        "--out",
        _default_temp_generated_report(
            "ParameterAlgorithmScoringPolicyRegistry.report.json"
        ),
    ]
    assert commands[pr85_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
        "--out",
        _default_temp_generated_report("ParameterStackScoringAndRankingGate.report.json"),
    ]
    assert commands[pr86_index] == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
        "--out",
        _default_temp_generated_report(
            "QuantumClassicalOptimizerArbitrationGate.report.json"
        ),
    ]
    assert commands[pr87_index] == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
        "--out",
        _default_temp_generated_report("CandidateParameterStackGenerationGate.report.json"),
    ]
    assert commands[pr88_index] == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
        "--out",
        _default_temp_generated_report(
            "TradeContextParameterStackSelectionGate.report.json"
        ),
    ]
    assert commands[pr89_index] == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
        "--out",
        _default_temp_generated_report("SelectedParameterStackHandoffPacket.report.json"),
    ]
    assert commands[pr90_index] == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
        "--out",
        _default_temp_generated_report(
            "ReplayPaperCandidateStackCompetitionGate.report.json"
        ),
    ]
    assert commands[pr91_index] == [
        python_executable,
        str(Path("tools") / "validate_dual_result_review_for_parameter_stacks.py"),
        "--out",
        _default_temp_generated_report("DualResultReviewForParameterStacks.report.json"),
    ]
    assert commands[pr92_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_live_promotion_review_for_parameter_stacks.py"
        ),
        "--out",
        _default_temp_generated_report(
            "OwnerLivePromotionReviewForParameterStacks.report.json"
        ),
    ]
    assert commands[pr93_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_approval_request_queue_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerApprovalRequestQueueRegistry.report.json"),
    ]
    assert commands[pr94_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_override_receipt_authoring_gate.py"),
        "--out",
        _default_temp_generated_report("OwnerOverrideReceiptAuthoringGate.report.json"),
    ]
    assert commands[pr95_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_dashboard_approval_menu_schema.py"),
        "--out",
        _default_temp_generated_report("OwnerDashboardApprovalMenuSchema.report.json"),
    ]
    assert commands[pr96_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_dashboard_approval_static_screen_contract.py"
        ),
        "--out",
        _default_temp_generated_report(
            "OwnerDashboardApprovalStaticScreenContract.report.json"
        ),
    ]
    assert commands[pr97_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsFullBundleRowExpansionPlan.report.json"),
    ]
    assert commands[pr98_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsBundleRowFamilySourceFiles.report.json"),
    ]
    assert commands[pr99_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json"
        ),
    ]
    assert commands[sha_dormancy_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_sha_system_dormancy_state_contract.py"),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsShaSystemDormancyStateContract.report.json"
        ),
    ]
    assert commands[final_readiness_dependency_policy_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_final_readiness_dependency_policy_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report("QttFinalReadinessDependencyPolicy.report.json"),
    ]
    assert commands[active_non_sha_gate_registry_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "QttActiveNonShaDay1GateStateRegistry.report.json"
        ),
    ]
    assert commands[pr_identity_roster_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        "--report-out",
        _default_temp_generated_report("QttPrIdentityRoster.report.json"),
    ]
    assert commands[roadmap_execution_state_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_roadmap_execution_state_controller.py"),
        "--report-out",
        _default_temp_generated_report("QttRoadmapExecutionStateController.report.json"),
    ]
    assert commands[pr100_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleShaFreezeAuthorityGate.report.json"),
    ]
    assert commands[repair_bridge_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowAuthorityClassifierBridge.report.json"
        ),
    ]
    assert commands[repair_c0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json"
        ),
    ]
    assert commands[repair_manifest_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsExactRowExpansionManifest.report.json"),
    ]
    assert commands[repair_dry_run_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report("AtomicRowsExactRowGeneratorDryRun.report.json"),
    ]
    assert commands[repair_c1_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsRepairChainGrandDebugLogicAudit.report.json"
        ),
    ]
    assert commands[repair_d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_source_materialization_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowSourceMaterialization.report.json"
        ),
    ]
    assert commands[repair_d2_e0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json"
        ),
    ]
    assert commands[bundle_materialization_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_materialization_manifest.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleMaterialization.report.json"),
    ]
    assert commands[bundle_boundary_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_boundary_state_contract.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleBoundaryStateContract.report.json"),
    ]
    assert commands[sha_freeze_final_readiness_state_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsShaFreezeFinalReadinessStateContract.report.json"
        ),
    ]


def test_runner_does_not_emit_success_marker_if_selection_universe_consumer_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 37, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 37
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_trade_context_routing_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 41, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 41
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_quantum_applicability_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 43, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 43
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_quantum_priority_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 47, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 47
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_algorithm_scoring_policy_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 53, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 53
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_scoring_and_ranking_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 59, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 59
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_optimizer_arbitration_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 61, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 61
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_generation_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 62, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 62
    assert seen == commands[:9]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selected_stack_handoff_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 63, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 63
    assert seen == commands[:11]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_replay_paper_competition_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 64
    assert seen == commands[:12]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_dual_result_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 65
    assert seen == commands[:13]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_live_promotion_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 66, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 66
    assert seen == commands[:14]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_approval_request_queue_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 67, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 67
    assert seen == commands[:15]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_override_receipt_authoring_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 68, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 68
    assert seen == commands[:16]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_menu_schema_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 69, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 69
    assert seen == commands[:17]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_static_screen_contract_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 70
    assert seen == commands[:18]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_full_bundle_row_expansion_plan_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 71, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 71
    assert seen == commands[:19]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_bundle_row_family_source_files_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "validate_atomicrows_bundle_row_family_source_files.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        72,
        0,
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 72
    assert seen == commands[:20]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_pr80_consumer_gate_has_no_runtime_source_connector_or_routing_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr80_command = commands[
        command_names.index(
            "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        )
    ]

    assert pr80_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
        ),
    ]
    pr80_text = " ".join(pr80_command).lower()
    assert "source-retrieval" not in pr80_text
    assert "source-acceptance" not in pr80_text
    assert "connector-binding" not in pr80_text
    assert "runtime-live" not in pr80_text
    assert "live-use" not in pr80_text
    assert "order-authority" not in pr80_text
    assert "profit-evidence" not in pr80_text
    assert "replay-execution" not in pr80_text
    assert "paper-execution" not in pr80_text
    assert "quantum-backend" not in pr80_text
    assert "quantum-advantage" not in pr80_text
    assert "atomicrows.bundle.jsonl" not in pr80_text
    assert "atomicrows.bundle.sha256" not in pr80_text


def test_pr80_static_contract_preserves_consumer_gate_no_claim_boundaries():
    production = selection_universe_consumer_gate.load_yaml(
        selection_universe_consumer_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    static = production["gate_static_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_consumer_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_is_static_only"] is True
    assert static["agent_universe_consumer_access_is_deterministic"] is True
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["routed_universe_ids_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_selection"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["parameter_selection_universe_consumer_gate_ready"] is True
    assert readiness["production_selection_universe_consumer_gate_evaluated"] is False
    assert readiness["production_selection_universe_consumer_gate_ready"] is False
    assert readiness["production_consumer_access_evaluated"] is False
    assert readiness["production_routing_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_consumer_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_consumer_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_consumer_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr81_routing_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr81_command = commands[
        command_names.index("validate_trade_context_selection_universe_routing_gate.py")
    ]

    assert pr81_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_selection_universe_routing_gate.py"),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
        ),
    ]
    pr81_text = " ".join(pr81_command).lower()
    assert "source-retrieval" not in pr81_text
    assert "source-acceptance" not in pr81_text
    assert "connector-binding" not in pr81_text
    assert "runtime-live" not in pr81_text
    assert "live-use" not in pr81_text
    assert "order-authority" not in pr81_text
    assert "profit-evidence" not in pr81_text
    assert "replay-execution" not in pr81_text
    assert "paper-execution" not in pr81_text
    assert "quantum-backend" not in pr81_text
    assert "quantum-advantage" not in pr81_text
    assert "atomicrows.bundle.jsonl" not in pr81_text
    assert "atomicrows.bundle.sha256" not in pr81_text


def test_runner_pr82_quantum_applicability_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr82_command = commands[
        command_names.index("validate_quantum_applicability_classification_registry.py")
    ]

    assert pr82_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "QuantumApplicabilityClassificationRegistry.report.json"
        ),
    ]
    pr82_text = " ".join(pr82_command).lower()
    assert "source-retrieval" not in pr82_text
    assert "source-acceptance" not in pr82_text
    assert "connector-binding" not in pr82_text
    assert "runtime-live" not in pr82_text
    assert "live-use" not in pr82_text
    assert "order-authority" not in pr82_text
    assert "profit-evidence" not in pr82_text
    assert "replay-execution" not in pr82_text
    assert "paper-execution" not in pr82_text
    assert "quantum-backend" not in pr82_text
    assert "quantum-simulator" not in pr82_text
    assert "atomicrows.bundle.jsonl" not in pr82_text
    assert "atomicrows.bundle.sha256" not in pr82_text


def test_runner_pr83_owner_quantum_priority_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr83_command = commands[
        command_names.index("validate_owner_quantum_priority_policy_registry.py")
    ]

    assert pr83_command == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerQuantumPriorityPolicyRegistry.report.json"),
    ]
    pr83_text = " ".join(pr83_command).lower()
    assert "source-retrieval" not in pr83_text
    assert "source-acceptance" not in pr83_text
    assert "connector-binding" not in pr83_text
    assert "runtime-live" not in pr83_text
    assert "live-use" not in pr83_text
    assert "order-authority" not in pr83_text
    assert "profit-evidence" not in pr83_text
    assert "replay-execution" not in pr83_text
    assert "paper-execution" not in pr83_text
    assert "quantum-backend" not in pr83_text
    assert "quantum-simulator" not in pr83_text
    assert "optimizer-execution" not in pr83_text
    assert "optimizer-arbitration" not in pr83_text
    assert "scoring-execution" not in pr83_text
    assert "ranking" not in pr83_text
    assert "selection" not in pr83_text
    assert "atomicrows.bundle.jsonl" not in pr83_text
    assert "atomicrows.bundle.sha256" not in pr83_text


def test_runner_pr84_parameter_algorithm_scoring_policy_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr84_command = commands[
        command_names.index("validate_parameter_algorithm_scoring_policy_registry.py")
    ]

    assert pr84_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
        "--out",
        _default_temp_generated_report(
            "ParameterAlgorithmScoringPolicyRegistry.report.json"
        ),
    ]
    pr84_text = " ".join(pr84_command).lower()
    assert "source-retrieval" not in pr84_text
    assert "source-acceptance" not in pr84_text
    assert "connector-binding" not in pr84_text
    assert "runtime-live" not in pr84_text
    assert "live-use" not in pr84_text
    assert "order-authority" not in pr84_text
    assert "profit-evidence" not in pr84_text
    assert "replay-execution" not in pr84_text
    assert "paper-execution" not in pr84_text
    assert "quantum-backend" not in pr84_text
    assert "quantum-simulator" not in pr84_text
    assert "optimizer-execution" not in pr84_text
    assert "optimizer-arbitration" not in pr84_text
    assert "scoring-execution" not in pr84_text
    assert "ranking" not in pr84_text
    assert "selection" not in pr84_text
    assert "atomicrows.bundle.jsonl" not in pr84_text
    assert "atomicrows.bundle.sha256" not in pr84_text


def test_runner_pr85_parameter_stack_scoring_and_ranking_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr85_command = commands[
        command_names.index("validate_parameter_stack_scoring_and_ranking_gate.py")
    ]

    assert pr85_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
        "--out",
        _default_temp_generated_report("ParameterStackScoringAndRankingGate.report.json"),
    ]
    pr85_text = " ".join(pr85_command).lower()
    assert "source-retrieval" not in pr85_text
    assert "source-acceptance" not in pr85_text
    assert "connector-binding" not in pr85_text
    assert "runtime-live" not in pr85_text
    assert "live-use" not in pr85_text
    assert "order-authority" not in pr85_text
    assert "profit-evidence" not in pr85_text
    assert "replay-execution" not in pr85_text
    assert "paper-execution" not in pr85_text
    assert "quantum-backend" not in pr85_text
    assert "quantum-simulator" not in pr85_text
    assert "optimizer-execution" not in pr85_text
    assert "optimizer-arbitration" not in pr85_text
    assert "atomicrows.bundle.jsonl" not in pr85_text
    assert "atomicrows.bundle.sha256" not in pr85_text


def test_runner_pr86_optimizer_arbitration_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr86_command = commands[
        command_names.index("validate_quantum_classical_optimizer_arbitration_gate.py")
    ]

    assert pr86_command == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
        "--out",
        _default_temp_generated_report(
            "QuantumClassicalOptimizerArbitrationGate.report.json"
        ),
    ]
    pr86_text = " ".join(pr86_command).lower()
    assert "source-retrieval" not in pr86_text
    assert "source-acceptance" not in pr86_text
    assert "connector-binding" not in pr86_text
    assert "runtime-live" not in pr86_text
    assert "live-use" not in pr86_text
    assert "order-authority" not in pr86_text
    assert "profit-evidence" not in pr86_text
    assert "replay-execution" not in pr86_text
    assert "paper-execution" not in pr86_text
    assert "quantum-backend" not in pr86_text
    assert "quantum-simulator" not in pr86_text
    assert "optimizer-execution" not in pr86_text
    assert "atomicrows.bundle.jsonl" not in pr86_text
    assert "atomicrows.bundle.sha256" not in pr86_text


def test_runner_pr87_candidate_generation_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr87_command = commands[
        command_names.index("validate_candidate_parameter_stack_generation_gate.py")
    ]

    assert pr87_command == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
        "--out",
        _default_temp_generated_report("CandidateParameterStackGenerationGate.report.json"),
    ]
    pr87_text = " ".join(pr87_command).lower()
    assert "source-retrieval" not in pr87_text
    assert "source-acceptance" not in pr87_text
    assert "connector-binding" not in pr87_text
    assert "runtime-live" not in pr87_text
    assert "live-use" not in pr87_text
    assert "order-authority" not in pr87_text
    assert "profit-evidence" not in pr87_text
    assert "replay-execution" not in pr87_text
    assert "paper-execution" not in pr87_text
    assert "quantum-backend" not in pr87_text
    assert "quantum-simulator" not in pr87_text
    assert "optimizer-execution" not in pr87_text
    assert "atomicrows.bundle.jsonl" not in pr87_text
    assert "atomicrows.bundle.sha256" not in pr87_text


def test_runner_pr88_trade_context_stack_selection_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr88_command = commands[
        command_names.index("validate_trade_context_parameter_stack_selection_gate.py")
    ]

    assert pr88_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
        "--out",
        _default_temp_generated_report(
            "TradeContextParameterStackSelectionGate.report.json"
        ),
    ]
    pr88_text = " ".join(pr88_command).lower()
    assert "source-retrieval" not in pr88_text
    assert "source-acceptance" not in pr88_text
    assert "connector-binding" not in pr88_text
    assert "runtime-live" not in pr88_text
    assert "live-use" not in pr88_text
    assert "order-authority" not in pr88_text
    assert "profit-evidence" not in pr88_text
    assert "replay-execution" not in pr88_text
    assert "paper-execution" not in pr88_text
    assert "selected-stack-handoff" not in pr88_text
    assert "quantum-backend" not in pr88_text
    assert "quantum-simulator" not in pr88_text
    assert "optimizer-execution" not in pr88_text
    assert "atomicrows.bundle.jsonl" not in pr88_text
    assert "atomicrows.bundle.sha256" not in pr88_text


def test_runner_pr89_selected_stack_handoff_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr89_command = commands[
        command_names.index("validate_selected_parameter_stack_handoff_packet.py")
    ]

    assert pr89_command == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
        "--out",
        _default_temp_generated_report("SelectedParameterStackHandoffPacket.report.json"),
    ]
    pr89_text = " ".join(pr89_command).lower()
    assert "source-retrieval" not in pr89_text
    assert "source-acceptance" not in pr89_text
    assert "connector-binding" not in pr89_text
    assert "runtime-live" not in pr89_text
    assert "live-use" not in pr89_text
    assert "order-authority" not in pr89_text
    assert "profit-evidence" not in pr89_text
    assert "replay-execution" not in pr89_text
    assert "paper-execution" not in pr89_text
    assert "quantum-backend" not in pr89_text
    assert "quantum-simulator" not in pr89_text
    assert "optimizer-execution" not in pr89_text
    assert "atomicrows.bundle.jsonl" not in pr89_text
    assert "atomicrows.bundle.sha256" not in pr89_text


def test_runner_pr90_replay_paper_competition_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr90_command = commands[
        command_names.index("validate_replay_paper_candidate_stack_competition_gate.py")
    ]

    assert pr90_command == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
        "--out",
        _default_temp_generated_report(
            "ReplayPaperCandidateStackCompetitionGate.report.json"
        ),
    ]
    pr90_text = " ".join(pr90_command).lower()
    assert "source-retrieval" not in pr90_text
    assert "source-acceptance" not in pr90_text
    assert "connector-binding" not in pr90_text
    assert "runtime-live" not in pr90_text
    assert "live-use" not in pr90_text
    assert "order-authority" not in pr90_text
    assert "profit-evidence" not in pr90_text
    assert "replay-execution" not in pr90_text
    assert "paper-execution" not in pr90_text
    assert "quantum-backend" not in pr90_text
    assert "quantum-simulator" not in pr90_text
    assert "optimizer-execution" not in pr90_text
    assert "atomicrows.bundle.jsonl" not in pr90_text
    assert "atomicrows.bundle.sha256" not in pr90_text


def test_pr81_static_contract_preserves_route_only_boundaries():
    production = trade_context_routing_gate.load_yaml(
        trade_context_routing_gate.DEFAULT_PRODUCTION_GATE
    )
    report = json.loads(
        trade_context_routing_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["routing_static_policy"]["routing_gate_is_static_only"] is True
    assert production["routing_static_policy"][
        "trade_context_to_selection_universe_static_routing_gate_created"
    ] is True
    assert report["route_scope"] == (
        "STATIC_TRADE_CONTEXT_TO_SELECTION_UNIVERSE_ELIGIBILITY_ONLY"
    )
    assert report["route_is_selection"] is False
    assert report["stack_selection_created"] is False
    assert report["selected_stack_id"] is None
    assert report["score_breakdown_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_selection_used"] is False
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in trade_context_routing_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_SHA256).exists()


def test_pr82_static_contract_preserves_metadata_only_boundaries():
    production = quantum_applicability_gate.load_yaml(
        quantum_applicability_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        quantum_applicability_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
    assert production["registry_scope"] == "STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["classification_is_metadata_only"] is True
    assert report["backend_execution_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["scoring_execution_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_classification_used"] is False
    assert report["future_owner_quantum_priority_policy_required"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["missing_canonical_family_ids"] == []
    assert (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / quantum_applicability_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / quantum_applicability_gate.PR76_OLD_LONG_TEST).exists()


def test_pr83_static_contract_preserves_owner_quantum_priority_boundaries():
    assert owner_quantum_priority_gate.main([]) == 0
    production = owner_quantum_priority_gate.load_yaml(
        owner_quantum_priority_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        owner_quantum_priority_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-OWNER-QUANTUM-PRIORITY-POLICY"
    assert production["policy_scope"] == "STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["policy_is_metadata_only"] is True
    assert report["owner_quantum_priority_enabled"] is True
    assert report["default_quantum_priority_mode"] == "QUANTUM_PREFERRED"
    assert report["supported_quantum_priority_modes"] == list(
        owner_quantum_priority_gate.MODE_ORDER
    )
    assert report["classical_only_families_valid_as_comparators"] is True
    assert report["hybrid_compare_requires_classical_comparator"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_stack_ranking_gate_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["future_candidate_stack_generation_required"] is True
    assert report["future_trade_context_stack_selection_required"] is True
    assert report["future_consumer_contract_execution_created"] is False
    assert report["pr82_quantum_applicability_registry_consumed"] is True
    assert report["classical_only_label_validated_from_pr82"] is True
    for field in owner_quantum_priority_gate.ROOT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / owner_quantum_priority_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / owner_quantum_priority_gate.PR76_OLD_LONG_TEST).exists()


def test_pr84_static_contract_preserves_formula_registry_only_boundaries():
    assert scoring_policy_gate.main([]) == 0
    production = scoring_policy_gate.load_yaml(
        scoring_policy_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        scoring_policy_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-AND-ALGORITHM-SCORING-POLICY-REGISTRY"
    )
    assert production["policy_scope"] == (
        "STATIC_PARAMETER_AND_ALGORITHM_SCORING_FORMULA_REGISTRY_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["formula_registry_only_flag"] is True
    assert report["formula_definition_allowed"] is True
    assert report["formula_execution_created"] is False
    assert report["scoring_result_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["candidate_stack_generation_created"] is False
    assert report["pr82_quantum_applicability_metadata_consumed"] is True
    assert report["pr83_owner_quantum_priority_policy_consumed"] is True
    assert report["formula_ids"] == list(scoring_policy_gate.FORMULA_ORDER)
    assert report["formula_outputs"] == list(scoring_policy_gate.FORMULA_OUTPUT_ORDER)
    assert report["scoring_component_names"] == list(scoring_policy_gate.COMPONENT_ORDER)
    assert report["future_consumer_ids"] == list(scoring_policy_gate.FUTURE_CONSUMER_ORDER)
    for field in scoring_policy_gate.NO_AUTHORITY_FALSE_FIELDS:
        assert report[field] is False
    assert report["expected_net_profit_score_is_profit_evidence"] is False
    assert report["latency_fit_score_is_latency_superiority_evidence"] is False
    assert report["optimizer_score_is_optimizer_execution"] is False
    assert report["runtime_readiness_score_is_runtime_receipt"] is False
    assert report["replay_paper_score_is_replay_paper_result"] is False
    assert report["source_currentness_penalty_is_source_authority"] is False
    assert report["execution_cost_penalty_is_venue_fact"] is False
    assert report["owner_override_score_can_fabricate_external_facts"] is False
    assert (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / scoring_policy_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / scoring_policy_gate.PR76_OLD_LONG_TEST).exists()


def test_pr85_static_contract_preserves_parameter_stack_ranking_boundaries():
    assert stack_scoring_gate.main([]) == 0
    production = stack_scoring_gate.load_yaml(
        stack_scoring_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        stack_scoring_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-STACK-SCORING-AND-RANKING-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_PARAMETER_STACK_SCORING_AND_RANKING_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["scoring_ranking_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        stack_scoring_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        stack_scoring_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(stack_scoring_gate.FORMULA_ORDER)
    assert report["ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["blocked_candidate_descriptor_ids"] == [
        "BLOCKED_INVALID_STACK_FIXTURE"
    ]
    assert report["highest_ranked_candidate_is_final_selected_stack"] is False
    assert report["future_pr86_optimizer_arbitration_implemented"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    for field in stack_scoring_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / stack_scoring_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / stack_scoring_gate.PR76_OLD_LONG_TEST).exists()


def test_pr86_static_contract_preserves_optimizer_arbitration_boundaries():
    assert optimizer_arbitration_gate.main([]) == 0
    production = optimizer_arbitration_gate.load_yaml(
        optimizer_arbitration_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        optimizer_arbitration_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-QUANTUM-CLASSICAL-OPTIMIZER-ARBITRATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["optimizer_arbitration_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(
        optimizer_arbitration_gate.pr85_gate.FORMULA_ORDER
    )
    assert report["pr85_ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["arbitration_ordered_fixture_ids"] == list(
        optimizer_arbitration_gate.EXPECTED_ORDERED_VALID_FIXTURE_IDS
    )
    assert report["blocked_arbitration_fixture_ids"] == [
        "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE",
        "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE",
    ]
    assert report["static_arbitration_decision_is_final_selected_stack"] is False
    assert report["static_arbitration_decision_is_live_order_authority"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in optimizer_arbitration_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / optimizer_arbitration_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / optimizer_arbitration_gate.PR76_OLD_LONG_TEST).exists()


def test_pr87_static_contract_preserves_candidate_generation_boundaries(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert candidate_generation_gate.main([]) == 0
    production = candidate_generation_gate.load_yaml(
        candidate_generation_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        candidate_generation_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-CANDIDATE-PARAMETER-STACK-GENERATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["candidate_generation_contract_only_flag"] is True
    assert report["candidate_generation_packet_status"] == (
        "STATIC_CANDIDATE_GENERATION_PACKET_READY"
    )
    assert report["active_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_ACTIVE_CANDIDATE_IDS
    )
    assert report["blocked_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_BLOCKED_CANDIDATE_IDS
    )
    assert report["static_candidate_generation_packet_is_final_selection"] is False
    assert report["static_candidate_generation_packet_is_live_order_authority"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in candidate_generation_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_SHA256).exists()


def test_runner_orders_source_evidence_gate_confirmation_before_connectors(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    source_evidence_index = command_names.index("validate_source_evidence_static.py")
    gate_confirmation_index = command_names.index(
        "validate_source_evidence_gate_confirmation_static.py"
    )
    retrieval_index = command_names.index("validate_source_evidence_retrieval_executor.py")
    acceptance_index = command_names.index("validate_source_evidence_acceptance.py")
    binding_index = command_names.index(
        "validate_accepted_source_to_connector_semantic_binding.py"
    )
    revalidation_index = command_names.index("validate_source_revalidation_scheduler.py")
    implementation_index = command_names.index(
        "validate_connector_semantic_binding_implementation_gate.py"
    )
    lifecycle_index = command_names.index(
        "validate_per_venue_execution_lifecycle_model.py"
    )
    normalization_index = command_names.index(
        "validate_cross_venue_execution_normalization_binding.py"
    )
    runtime_cash_index = command_names.index("runtime_cash_component_field_map_validate.py")
    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert source_evidence_index < gate_confirmation_index < retrieval_index
    assert retrieval_index < acceptance_index < binding_index < revalidation_index
    assert (
        revalidation_index
        < implementation_index
        < lifecycle_index
        < normalization_index
        < runtime_cash_index
        < private_state_index
        < credential_index
        < market_data_index
        < connector_index
    )


def test_runner_includes_per_venue_execution_lifecycle_model_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "validate_per_venue_execution_lifecycle_model.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_cross_venue_execution_normalization_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "validate_cross_venue_execution_normalization_binding.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_runtime_cash_component_field_map_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "runtime_cash_component_field_map_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_non_mutating_atomicrows_readiness_audit(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_atomicrows_readiness_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_readiness_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_non_mutating_atomicrows_unblocking_requirements_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_unblocking_requirements_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_non_mutating_atomicrows_canonical_row_specification_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(
            Path("tools")
            / "validate_atomicrows_canonical_row_specification_static.py"
        )
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_canonical_row_specification_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_canonical_row_specification_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_atomicrows_bundle_schema_checker_after_row_specification(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    row_spec_index = command_names.index(
        "validate_atomicrows_canonical_row_specification_static.py"
    )
    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert row_spec_index < bundle_checker_index < no_runtime_index

    audit_command = commands[bundle_checker_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
        "--repo-root",
        ".",
        "--row-schema",
        str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
        "--bundle-schema",
        str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
        ),
    ]


def test_runner_includes_generated_derivative_gate_after_bundle_checker(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    lifecycle_build_index = command_names.index(
        "build_atomicrows_parameter_lifecycle_report.py"
    )
    lifecycle_validate_index = command_names.index(
        "validate_atomicrows_parameter_lifecycle.py"
    )
    consumer_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_consumer_gate.py"
    )
    promotion_receipt_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
    )
    mutation_guard_index = command_names.index(
        "validate_atomicrows_lifecycle_registry_mutation_guard.py"
    )
    cumulative_readiness_index = command_names.index(
        "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
    )
    lifecycle_command_matrix_index = command_names.index(
        "validate_atomicrows_lifecycle_gate_command_matrix.py"
    )
    parameter_agent_binding_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_registry.py"
    )
    parameter_agent_binding_consumer_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
    )
    parameter_agent_binding_cumulative_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
    )
    parameter_agent_binding_command_matrix_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_command_matrix.py"
    )
    research_provenance_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        bundle_checker_index
        < lifecycle_build_index
        < lifecycle_validate_index
        < consumer_gate_index
        < promotion_receipt_gate_index
        < mutation_guard_index
        < cumulative_readiness_index
        < lifecycle_command_matrix_index
        < parameter_agent_binding_index
        < parameter_agent_binding_consumer_gate_index
        < parameter_agent_binding_cumulative_gate_index
        < parameter_agent_binding_command_matrix_index
        < research_provenance_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[lifecycle_build_index] == [
        python_executable,
        str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterLifecycleReport.json"),
    ]
    assert commands[lifecycle_validate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[lifecycle_validate_index]
    assert commands[consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsLifecycleConsumerGate.report.json"),
    ]
    assert commands[promotion_receipt_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecyclePromotionReceiptGate.report.json"
        ),
    ]
    assert commands[mutation_guard_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_registry_mutation_guard.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecycleRegistryMutationGuard.report.json"
        ),
    ]
    assert commands[cumulative_readiness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[lifecycle_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsLifecycleGateCommandMatrix.json"),
    ]
    assert commands[parameter_agent_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_agent_binding_registry.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsParameterAgentBindingReport.json"),
    ]
    assert commands[parameter_agent_binding_consumer_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterAgentBindingConsumerGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_cumulative_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_command_matrix_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsParameterAgentBindingCommandMatrix.json"),
    ]
    assert commands[research_provenance_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterStackRoleTaxonomy.report.json"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]

    audit_command = commands[generated_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "master_plan"
            / "generated_derivative_bootstrap_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "master_plan"
            / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_packet_schema_gate_after_generated_derivative_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert generated_gate_index < stage1_gate_index < no_runtime_index

    audit_command = commands[stage1_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "stage1_prediction_markets"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "stage1_prediction_markets"
            / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_venue_neutral_adapter_gate_after_stage1_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert stage1_gate_index < adapter_gate_index < no_runtime_index

    audit_command = commands[adapter_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_venue_neutral_prediction_adapter_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "venue_neutral_prediction_adapter"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "venue_neutral_prediction_adapter"
            / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_connector_scaffold_gate_after_adapter_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert adapter_gate_index < connector_scaffold_gate_index < no_runtime_index

    audit_command = commands[connector_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_connector_scaffold_source_required_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "connectors"
            / "connector_scaffold_source_required_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "connectors"
            / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_runtime_scaffold_gate_after_connector_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    stage1_runtime_scaffold_gate_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        connector_scaffold_gate_index
        < stage1_runtime_scaffold_gate_index
        < no_runtime_index
    )

    audit_command = commands[stage1_runtime_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "runtime_orchestration"
            / "stage1_runtime_scaffold_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "runtime_orchestration"
            / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_pr37_static_gates_after_stage1_runtime_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_runtime_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    matrix_index = command_names.index("local_gate_command_matrix.py")
    handoff_index = command_names.index("pr_handoff_check.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        stage1_runtime_index
        < qtt_gate_index
        < matrix_index
        < handoff_index
        < no_runtime_index
    )
    assert commands[qtt_gate_index] == [
        python_executable,
        str(Path("tools") / "qtt_test_gate.py"),
        "--phase",
        "first-coding-runbook",
        "--repo-root",
        ".",
        "--strict-no-claim",
        "--out",
        _default_temp_generated_report("QTTTestGate.report.json"),
    ]
    assert commands[matrix_index] == [
        python_executable,
        str(Path("tools") / "local_gate_command_matrix.py"),
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("LocalGateCommandMatrix.json"),
    ]
    assert commands[handoff_index] == [
        python_executable,
        str(Path("tools") / "pr_handoff_check.py"),
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("FirstCodingPRHandoff.packet.json"),
    ]


def test_runner_includes_pr41_runtime_resolver_contract_gate_after_pr40_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr40_index = command_names.index("stage1_connector_semantic_binding_ledger_check.py")
    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr40_index < pr41_index < qtt_gate_index < no_runtime_index
    assert commands[pr41_index] == [
        python_executable,
        str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
        "--repo-root",
        ".",
        "--input-lock-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
        ),
        "--manifest-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_manifest.schema.json"
        ),
        "--consumer-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_consumer_contract.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver"
            / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1RuntimeResolverSnapshotContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr42_runtime_resolver_to_replay_paper_handoff_after_pr41_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr41_index < pr42_index < qtt_gate_index < no_runtime_index
    assert commands[pr42_index] == [
        python_executable,
        str(
            Path("tools")
            / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
        ),
        "--repo-root",
        ".",
        "--consumer-allowlist-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
        ),
        "--handoff-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
        ),
        "--handoff-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver_snapshot"
            / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
        ),
    ]


def test_runner_includes_pr43_concurrent_replay_paper_contract_after_pr42_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr42_index < pr43_index < qtt_gate_index < no_runtime_index
    assert commands[pr43_index] == [
        python_executable,
        str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
        "--repo-root",
        ".",
        "--input-identity-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_input_identity.schema.json"
        ),
        "--replay-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_lane_contract.schema.json"
        ),
        "--paper-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_paper_lane_contract.schema.json"
        ),
        "--replay-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "replay_result_packet_boundary.schema.json"
        ),
        "--paper-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "paper_result_packet_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_execution_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "replay_paper"
            / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1ConcurrentReplayPaperContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr44_dual_result_review_contract_after_pr43_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr43_index < pr44_index < qtt_gate_index < no_runtime_index
    assert commands[pr44_index] == [
        python_executable,
        str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_input_contract.schema.json"
        ),
        "--comparison-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_replay_paper_comparison_matrix.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_gate_report.schema.json"
        ),
        "--owner-handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_owner_live_promotion_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "dual_result_review"
            / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report("Stage1DualResultReviewContractCheck.report.json"),
    ]


def test_runner_includes_pr45_owner_live_promotion_review_contract_after_pr44_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr44_index < pr45_index < qtt_gate_index < no_runtime_index
    assert commands[pr45_index] == [
        python_executable,
        str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_input_contract.schema.json"
        ),
        "--owner-approval-receipt-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_approval_receipt_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_gate_report.schema.json"
        ),
        "--handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "owner_live_promotion_review"
            / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1OwnerLivePromotionReviewContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr46_three_venue_canary_eligibility_contract_after_pr45_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    pr46_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr45_index < pr46_index < qtt_gate_index < no_runtime_index
    assert commands[pr46_index] == [
        python_executable,
        str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
        ),
        "--readiness-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_platform_readiness_matrix.schema.json"
        ),
        "--handoff-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
        ),
        "--execution-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_limited_live_canary_execution_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "three_venue_canary_eligibility"
            / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
        ),
    ]


def test_runner_includes_section_coverage_dev_gate_after_three_venue_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    three_venue_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    build_index = command_names.index("build_master_plan_section_coverage_report.py")
    validate_index = command_names.index("validate_master_plan_section_coverage.py")
    triage_routes_index = command_names.index(
        "validate_qtt_master_plan_section_coverage_triage_routes.py"
    )
    crosswalk_index = command_names.index(
        "validate_qtt_master_plan_section_roadmap_crosswalk.py"
    )
    command_matrix_index = command_names.index(
        "validate_qtt_master_plan_section_coverage_command_matrix.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert three_venue_index < build_index < validate_index < triage_routes_index
    assert triage_routes_index < crosswalk_index < command_matrix_index < qtt_gate_index
    assert qtt_gate_index < no_runtime_index
    assert commands[build_index] == [
        python_executable,
        str(Path("tools") / "build_master_plan_section_coverage_report.py"),
        "--out",
        _default_temp_generated_report("MasterPlanSectionCoverageReport.json"),
    ]
    assert commands[validate_index] == [
        python_executable,
        str(Path("tools") / "validate_master_plan_section_coverage.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[validate_index]
    assert commands[triage_routes_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_coverage_triage_routes.py"),
    ]
    assert commands[crosswalk_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_roadmap_crosswalk.py"),
    ]
    assert commands[command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_coverage_command_matrix.py"),
    ]


def test_runner_stops_on_first_failure_and_returns_failing_exit_code(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [["python", "gate_a.py"], ["python", "gate_b.py"], ["python", "gate_c.py"]]
    returncodes = [0, 9, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 9
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_intake_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 7, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 7
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_family_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 11, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 11
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_role_taxonomy_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 13, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 13
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_completeness_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 17, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 17
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_compatibility_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 19, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 19
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_edge_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 23, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 23
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_qtt_trade_context_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 29, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 29
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selection_universe_registry_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 31, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 31
    assert seen == commands[:9]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_timing_summary_preserves_success_return_code(monkeypatch, capsys):
    class Completed:
        returncode = 0

    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands([["python", "ok.py"]], phase="timing-test")

    output = capsys.readouterr().out
    assert exit_code == 0
    assert seen == [["python", "ok.py"]]
    assert "QTT_VALIDATION_TIMING_COMMAND phase=timing-test" in output
    assert "QTT_VALIDATION_TIMING_TOTAL phase=timing-test" in output
    assert output.splitlines()[-1] == runner.SUCCESS_MARKER


def test_runner_timing_summary_preserves_failure_return_code(monkeypatch, capsys):
    class Completed:
        returncode = 7

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands([["python", "fails.py"]], phase="timing-test")

    output = capsys.readouterr().out
    assert exit_code == 7
    assert "QTT_VALIDATION_TIMING_TOTAL phase=timing-test" in output
    assert runner.SUCCESS_MARKER not in output


def test_runner_timing_report_writes_only_when_requested(monkeypatch, tmp_path):
    class Completed:
        returncode = 0

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    report_path = tmp_path / "timing" / "report.json"

    assert runner.run_commands([["python", "ok.py"]], phase="no-report") == 0
    assert not report_path.exists()

    assert (
        runner.run_commands(
            [["python", "ok.py"]],
            phase="with-report",
            timing_report_path=report_path,
        )
        == 0
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == runner.TIMING_SCHEMA_VERSION
    assert payload["phase"] == "with-report"
    assert payload["runtime_budget_policy"] == runner.RUNTIME_BUDGET_POLICY
    assert payload["runtime_budget_warnings"] == []
    assert payload["command_entries"][0]["command"] == ["python", "ok.py"]
    assert payload["slowest_entries"]
    assert payload["total_elapsed_seconds"] >= 0


def test_runner_rejects_tracked_generated_timing_report_path(monkeypatch):
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(
        [["python", "ok.py"]],
        repo_root=REPO_ROOT,
        phase="bad-report",
        timing_report_path=(
            REPO_ROOT
            / "docs"
            / "master_plan"
            / "generated"
            / "timing.json"
        ),
    )

    assert exit_code == 2


def test_runner_returns_zero_when_all_mocked_commands_pass(monkeypatch, capsys):
    _clear_branch_context_env(monkeypatch)

    class Completed:
        def __init__(self, stdout: str = "", stderr: str = "") -> None:
            self.returncode = 0
            self.stdout = stdout
            self.stderr = stderr

    seen: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> Completed:
        if command[0] == "git":
            return Completed()
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner,
        "_routed_generated_output_currentness_failures",
        lambda command, repo_root: [],
    )

    exit_code = runner.main([])

    assert exit_code == 0
    validation_dir = _validation_dir_from_commands(seen)
    pytest_basetemp = _pytest_basetemp_from_commands(seen)
    assert pytest_basetemp.name.startswith("run_validation_gates_pytest_")
    expected = [
        command
        for command in runner.build_phase_commands(
            runner.ALL_PHASE,
            validation_dir,
            pytest_basetemp,
        )
        if command[0] != "git"
    ]
    assert seen == expected
    assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER


def test_runner_sets_run_local_no_runtime_scan_cache_env(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.delenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, raising=False)
    monkeypatch.delenv(runner.PR152_BUILD_REPORT_CACHE_ENV, raising=False)

    repo_root = (Path(".tmp") / "test_run_validation_gates_scan_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    cache_paths: list[Path] = []
    pr152_cache_paths: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        cache_text = os.environ.get(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV)
        assert cache_text is not None
        cache_path = Path(cache_text)
        assert cache_path.name == "NoRuntimeArtifactScanCache.json"
        assert cache_path.parent.name.startswith("qtt_validation_gates_")
        cache_paths.append(cache_path)
        pr152_cache_text = os.environ.get(runner.PR152_BUILD_REPORT_CACHE_ENV)
        assert pr152_cache_text is not None
        pr152_cache_path = Path(pr152_cache_text)
        assert pr152_cache_path.name == "PR152BuildReportCache.json"
        assert pr152_cache_path.parent.name.startswith("qtt_validation_gates_")
        pr152_cache_paths.append(pr152_cache_path)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert cache_paths
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)

    assert os.environ.get(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV) is None
    assert os.environ.get(runner.PR152_BUILD_REPORT_CACHE_ENV) is None
    assert pr152_cache_paths


def test_runner_preserves_explicit_no_runtime_scan_cache_env(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    repo_root = (Path(".tmp") / "test_run_validation_gates_explicit_scan_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    explicit_cache = repo_root / ".tmp" / "explicit_scan_cache.json"
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(explicit_cache))
    seen: list[str] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        seen.append(os.environ[runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV])
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert seen == [str(explicit_cache)]
        assert os.environ[runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV] == str(
            explicit_cache
        )
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_preserves_explicit_pr152_build_report_cache_env(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    repo_root = (Path(".tmp") / "test_run_validation_gates_explicit_pr152_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    explicit_cache = repo_root / ".tmp" / "explicit_pr152_build_cache.json"
    monkeypatch.setenv(runner.PR152_BUILD_REPORT_CACHE_ENV, str(explicit_cache))
    seen: list[str] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        seen.append(os.environ[runner.PR152_BUILD_REPORT_CACHE_ENV])
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert seen == [str(explicit_cache)]
        assert os.environ[runner.PR152_BUILD_REPORT_CACHE_ENV] == str(explicit_cache)
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def _no_runtime_strict_options():
    from tools.validate_no_runtime_artifacts import ScanOptions

    return ScanOptions(
        forbid_source_retrieval=True,
        forbid_source_acceptance=True,
        forbid_connector_binding=True,
        forbid_private_state_fetch=True,
        forbid_order_execution=True,
        forbid_neural_training=True,
        forbid_neural_inference=True,
        forbid_external_repo_clone=True,
        forbid_package_install_scripts=True,
    )


def _runtime_scan_cache_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "ok.py").write_text("# ok\n", encoding="utf-8")
    return repo_root


def test_runner_no_runtime_scan_cache_reuses_matching_result(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / ".tmp" / "no_runtime_scan_cache.json"),
    )
    calls = 0

    def fake_scan(root: Path, options) -> list[str]:
        nonlocal calls
        calls += 1
        assert root == repo_root.resolve()
        return ["synthetic violation"]

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == ["synthetic violation"]
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == ["synthetic violation"]
    assert calls == 1


def test_runner_no_runtime_scan_cache_reruns_when_stale(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / ".tmp" / "no_runtime_scan_cache.json"),
    )
    calls: list[str] = []

    def fake_scan(root: Path, options) -> list[str]:
        calls.append("scan")
        return []

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    (repo_root / "src" / "new.py").write_text("# new\n", encoding="utf-8")
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    assert calls == ["scan", "scan"]


def test_runner_no_runtime_scan_cache_reruns_when_corrupt(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    cache_path = repo_root / ".tmp" / "no_runtime_scan_cache.json"
    cache_path.parent.mkdir()
    cache_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(cache_path))

    calls = 0

    def fake_scan(root: Path, options) -> list[str]:
        nonlocal calls
        calls += 1
        return []

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    assert calls == 1


def test_runner_no_runtime_scan_cache_rejects_scanned_tree_path(
    tmp_path,
    monkeypatch,
):
    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / "no_runtime_scan_cache.json"),
    )

    with pytest.raises(RuntimeError, match="must point outside the scanned tree"):
        runner.scan_no_runtime_artifacts_with_run_cache(
            repo_root,
            _no_runtime_strict_options(),
        )


def test_runner_records_successful_no_runtime_command_cache(
    tmp_path,
    monkeypatch,
):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    cache_path = repo_root / ".tmp" / "no_runtime_scan_cache.json"
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(cache_path))

    class Completed:
        returncode = 0

    monkeypatch.setattr(runner.subprocess, "run", lambda command: Completed())

    command = [
        sys.executable,
        str(Path("tools") / "validate_no_runtime_artifacts.py"),
        "--repo-root",
        str(repo_root),
        "--forbid-source-retrieval",
        "--forbid-source-acceptance",
        "--forbid-connector-binding",
        "--forbid-private-state-fetch",
        "--forbid-order-execution",
        "--forbid-neural-training",
        "--forbid-neural-inference",
        "--forbid-external-repo-clone",
        "--forbid-package-install-scripts",
    ]

    assert runner.run_commands([command]) == 0
    assert cache_path.is_file()

    def fail_if_uncached(root: Path, options) -> list[str]:
        raise AssertionError("successful scanner command should seed the cache")

    monkeypatch.setattr(scanner, "scan_repository", fail_if_uncached)
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []


def test_runner_pr152_build_report_cache_reuses_matching_result(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / ".tmp" / "pr152_build_cache.json"),
    )
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": "stable"},
    )
    calls = 0

    def fake_builder(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"calls": calls, "root": str(root)}

    first = runner.build_pr152_report_with_run_cache(repo_root, fake_builder)
    first["calls"] = 99
    second = runner.build_pr152_report_with_run_cache(repo_root, fake_builder)

    assert second == {"calls": 1, "root": str(repo_root.resolve())}
    assert calls == 1


def test_runner_pr152_build_report_cache_reruns_when_stale(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / ".tmp" / "pr152_build_cache.json"),
    )
    state = {"value": "initial"}
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": state["value"]},
    )
    calls: list[str] = []

    def fake_builder(root: Path) -> dict[str, object]:
        calls.append(state["value"])
        return {"state": state["value"]}

    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "state": "initial"
    }
    state["value"] = "changed"
    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "state": "changed"
    }
    assert calls == ["initial", "changed"]


def test_runner_pr152_build_report_cache_reruns_when_corrupt(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_path = repo_root / ".tmp" / "pr152_build_cache.json"
    cache_path.parent.mkdir()
    cache_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(runner.PR152_BUILD_REPORT_CACHE_ENV, str(cache_path))
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": "stable"},
    )
    calls = 0

    def fake_builder(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"rebuilt": True}

    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "rebuilt": True
    }
    assert calls == 1


def test_runner_pr152_build_report_cache_rejects_repo_root_path(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / "pr152_build_cache.json"),
    )

    with pytest.raises(RuntimeError, match="must point outside the repo"):
        runner.build_pr152_report_with_run_cache(repo_root, lambda root: {})


def test_runner_creates_tmp_parent_before_running_commands(monkeypatch, capsys):
    _clear_branch_context_env(monkeypatch)

    class Completed:
        def __init__(self, stdout: str = "", stderr: str = "") -> None:
            self.returncode = 0
            self.stdout = stdout
            self.stderr = stderr

    repo_root = (Path(".tmp") / "test_run_validation_gates_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    tmp_parent = repo_root / ".tmp"
    seen: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> Completed:
        assert tmp_parent.is_dir()
        if command[0] == "git":
            return Completed()
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner,
        "_routed_generated_output_currentness_failures",
        lambda command, repo_root: [],
    )

    assert not tmp_parent.exists()

    try:
        exit_code = runner.main([])

        assert exit_code == 0
        assert seen
        pytest_basetemp = _pytest_basetemp_from_commands(seen)
        assert tmp_parent.is_dir()
        assert not pytest_basetemp.is_relative_to(repo_root)
        assert pytest_basetemp.name.startswith("run_validation_gates_pytest_")
        assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_uses_unique_pytest_basetemp_for_each_main_run(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    repo_root = (Path(".tmp") / "test_run_validation_gates_unique_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    pytest_basetemps: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        pytest_basetemp = _pytest_basetemp_from_commands(commands)
        assert not pytest_basetemp.is_relative_to(repo_root)
        assert pytest_basetemp.name.startswith("run_validation_gates_pytest_")
        assert pytest_basetemp.is_dir()
        pytest_basetemps.append(pytest_basetemp)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main([]) == 0
        assert runner.main([]) == 0

        assert len(pytest_basetemps) == 2
        assert pytest_basetemps[0] != pytest_basetemps[1]
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_does_not_touch_stale_fixed_pytest_basetemp(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    repo_root = (Path(".tmp") / "test_run_validation_gates_stale_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    tmp_parent = repo_root / ".tmp"
    stale_basetemp = tmp_parent / "run_validation_gates_pytest"
    sentinel = stale_basetemp / "sentinel.txt"
    stale_basetemp.mkdir(parents=True)
    sentinel.write_text("do-not-touch", encoding="utf-8")
    pytest_basetemps: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        pytest_basetemp = _pytest_basetemp_from_commands(commands)
        assert pytest_basetemp != stale_basetemp
        assert pytest_basetemp.name.startswith("run_validation_gates_pytest_")
        assert stale_basetemp.is_dir()
        assert sentinel.read_text(encoding="utf-8") == "do-not-touch"
        pytest_basetemps.append(pytest_basetemp)
        return 0

    original_cwd = Path.cwd()
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main([]) == 0

        assert pytest_basetemps
        assert stale_basetemp.is_dir()
        assert sentinel.read_text(encoding="utf-8") == "do-not-touch"
    finally:
        monkeypatch.chdir(original_cwd)
        shutil.rmtree(repo_root, ignore_errors=True)


def _workflow_text() -> str:
    return (
        Path(__file__).resolve().parents[2]
        / ".github/workflows/qtt_validation.yml"
    ).read_text(encoding="utf-8")


def _workflow_job_block(workflow: str, job_id: str) -> str:
    marker = f"  {job_id}:\n"
    start = workflow.index(marker)
    next_job = workflow.find("\n  ", start + len(marker))
    while next_job != -1 and workflow[next_job + 3 : next_job + 5] == "  ":
        next_job = workflow.find("\n  ", next_job + 1)
    if next_job == -1:
        return workflow[start:]
    return workflow[start:next_job]


def test_github_workflow_preserves_required_validation_check_identity():
    workflow = _workflow_text()
    validation_block = _workflow_job_block(workflow, "validation")

    assert workflow.startswith("name: QTT Validation\n")
    assert "  validation:\n" in workflow
    assert "    name: Validation Gates\n" in validation_block


def test_github_workflow_splits_validation_into_parallel_phase_jobs():
    workflow = _workflow_text()
    shard_block = _workflow_job_block(workflow, "validation_shards")

    assert "    timeout-minutes: 90\n" in shard_block
    assert "    strategy:\n" in shard_block
    assert "      fail-fast: false\n" in shard_block
    assert "          python-version: '3.14'\n" in shard_block
    assert "      - name: Restore pip download cache\n" in shard_block
    assert "        uses: actions/cache@v4\n" in shard_block
    assert "cache-dependency-path" not in shard_block
    assert "          cache: pip\n" not in shard_block
    assert "        with: &pip_cache\n" in shard_block
    assert "          path: ~/.cache/pip\n" in shard_block
    assert (
        "          key: ${{ runner.os }}-python-3.14-pip-pytest-"
        "${{ hashFiles('.github/workflows/qtt_validation.yml') }}\n"
    ) in shard_block
    assert "            ${{ runner.os }}-python-3.14-pip-pytest-\n" in shard_block
    assert "        run: &install_pytest |\n" in shard_block
    assert "          python -m pip install pytest\n" in shard_block
    for phase in runner.ORDERED_PHASES:
        assert f"          - phase: {phase}\n" in shard_block
    assert "--phase ${{ matrix.phase }}" in shard_block
    assert "--timing-report .tmp/qtt-validation-timing/${{ matrix.phase }}.json" in shard_block
    assert "Run canonical validation gates" not in workflow


def test_github_workflow_aggregate_depends_on_validation_shard_matrix():
    workflow = _workflow_text()
    validation_block = _workflow_job_block(workflow, "validation")

    assert "      - validation_shards\n" in validation_block
    assert "    if: ${{ always() }}\n" in validation_block
    assert 'if result != "success":' in validation_block
    assert "raise SystemExit(1)" in validation_block


def test_github_workflow_matrix_contains_post_validation_phase():
    workflow = _workflow_text()
    shard_block = _workflow_job_block(workflow, "validation_shards")

    assert "          - phase: post-validation\n" in shard_block
    assert "            group: repo-wide-integrity\n" in shard_block


def test_nested_validator_contract_scan_blocks_hidden_full_rerun():
    from tools import validate_nested_validator_contracts as nested_contracts

    with tempfile.TemporaryDirectory(prefix="qtt_nested_contract_") as temp_dir:
        repo_root = Path(temp_dir)
        validator = repo_root / "tools" / "validate_pr200_downstream.py"
        validator.parent.mkdir(parents=True)
        validator.write_text(
            "import subprocess\n"
            "subprocess.run(['python', "
            "'tools/validate_pr159r_source_locator_value_capture.py'])\n",
            encoding="utf-8",
        )

        failures = nested_contracts.nested_validator_contract_failures_for_paths(
            repo_root,
            (validator,),
        )

    assert len(failures) == 1
    assert "nested full validator rerun forbidden" in failures[0]
    assert "validate_pr159r_source_locator_value_capture.py" in failures[0]


def test_nested_validator_contract_scan_allows_recorded_receipt_contract_text():
    from tools import validate_nested_validator_contracts as nested_contracts

    with tempfile.TemporaryDirectory(prefix="qtt_nested_contract_") as temp_dir:
        repo_root = Path(temp_dir)
        validator = repo_root / "tools" / "validate_pr200_downstream.py"
        validator.parent.mkdir(parents=True)
        validator.write_text(
            "RECEIPT_CONTRACT = {\n"
            "    'validator_that_recorded_receipt': "
            "'tools/validate_pr159r_source_locator_value_capture.py',\n"
            "    'rerun_full_validator': False,\n"
            "}\n",
            encoding="utf-8",
        )

        assert (
            nested_contracts.nested_validator_contract_failures_for_paths(
                repo_root,
                (validator,),
            )
            == ()
        )
