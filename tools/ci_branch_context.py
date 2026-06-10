#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import os
import pathlib
import re
import subprocess
from typing import Callable, Sequence

BRANCH_CONTEXT_ENV_CANDIDATES = (
    "GITHUB_HEAD_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF",
    "BRANCH_NAME",
    "CI_COMMIT_REF_NAME",
)

CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    "DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_ACTIVE"
)
REPAIR_BRANCH_PREFIX = "repair/"
MAIN_CUMULATIVE_BRANCH_PREFIX = "repair/main-cumulative-"
CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH = "pr-ci-runtime-parallel-cache-timeout"
PR208_CI_RUNTIME_RATIONALIZATION_BRANCH = "pr208-ci-runtime-rationalization"
VALIDATION_INFRASTRUCTURE_BRANCHES = frozenset(
    {
        "pr-ci-fastfail-validation-context-preflight",
        CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH,
        PR208_CI_RUNTIME_RATIONALIZATION_BRANCH,
    }
)
VALIDATION_INFRASTRUCTURE_CHANGED_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "docs/master_plan/generated/PR208_ChangedAreaRoutingPolicy.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_CrossPlatformPathInvariant.report.json",
        "docs/master_plan/generated/PR208_FinalSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "agent_consumable_parameter_default_registry/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "agent_default_binding_universal_intake_gate/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/constants.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/report.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_cross_platform_path_invariant.py",
        "tests/tools/test_validation_inventory.py",
        "tools/ci_branch_context.py",
        "tools/changed_area_validation_router.py",
        "tools/cross_platform_path_invariant.py",
        "tools/repo_path_refs.py",
        "tools/run_validation_gates.py",
        "tools/validate_validation_inventory.py",
        "tools/validate_ci_branch_context_matrix.py",
        "tools/validate_nested_validator_contracts.py",
        "tools/validate_repair_pr_changed_file_scope.py",
        "tools/validation_inventory.py",
    }
)
PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr163-c-main-branch-context-after-merge"
)
PR159R_BRANCH_CONTEXT_REPAIR_BRANCH = "repair/pr159r-branch-context-relaxation"
PR159R_DETACHED_HEAD_REPAIR_BRANCH = "repair/pr159r-detached-head-branch-context"
PR159S_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr159s-open-intake-branch-context-relaxation"
)
PR160_MAIN_ANCESTRY_REPAIR_BRANCH = "repair/pr160-main-ancestry-after-pr176"
PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr160-main-push-branch-context-relaxation"
)
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS = {
    "repair-pr153r-redo-report-determinism": 153,
    "repair/pr153s-source-value-capture-closure-classifier": 153,
    "pr154-atomicrows-parameter-default-value-materialization-gate": 154,
    "repair/pr154-post-merge-pytest-context-hygiene": 154,
    "pr155-agent-consumable-parameter-default-registry": 155,
    "pr156-agent-default-binding-universal-intake-gate": 156,
    "pr157-pr154-atomicrows-fillpath-owner-agent-bridge": 157,
    "pr158-owner-response-atomicrows-selection-readiness-bridge": 158,
    "pr159-official-source-retry-atomicrows-source-completion-bridge": 159,
    "pr159r-exact-source-locator-value-unit-capture": 159,
    "pr159s-open-source-intelligence-candidate-completion": 159,
    PR159R_BRANCH_CONTEXT_REPAIR_BRANCH: 159,
    PR159R_DETACHED_HEAD_REPAIR_BRANCH: 159,
    PR159S_BRANCH_CONTEXT_REPAIR_BRANCH: 159,
    "pr160-pr154-split-reclassification-route-closure-bridge": 160,
    PR160_MAIN_ANCESTRY_REPAIR_BRANCH: 160,
    PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH: 160,
    "pr161a-atomicrows-pr154-value-state-materialization-bridge": 161,
    "repair/pr161a-atomicrows-pr154-value-state-materialization-bridge": 161,
    "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge": 161,
    "repair/pr161b-master-plan-residual-candidate-coverage-assimilation-bridge": 161,
    "pr161c-qku-residual-candidate-assimilation-fill-campaign": 161,
    "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization": 161,
    "pr161e-replay-paper-outcome-capture-scenario-learning-bridge": 161,
    "pr161f-replay-paper-executor-input-run-artifact-generation": 161,
    "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge": 162,
    "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate": 162,
    "pr162b-qku-formula-algorithm-solver-market-scope-materialization": 162,
    "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage": 162,
    "pr162d-aggressive-qku-candidate-materialization-agent-routing": 162,
    "pr162d-r1-external-formula-data-quantum-acquisition-expansion": 162,
    "pr162r-a-replay-paper-executability-classification-audit": 162,
    "pr162d-r2a-real-computable-formulations-redo": 162,
    "pr162r-generic-replay-paper-adapter-rerun": 162,
    "pr162r-b-replay-paper-data-binding-completion": 162,
    "pr163-generic-paper-adapter-capture-framework": 163,
    "pr163-b-paired-replay-paper-concurrent-executor": 163,
    "pr163-c-pretrade-infrastructure-rejection-remediation": 163,
    PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH: 163,
    "pr164-review-provenance-qku-canonical-coverage-audit": 164,
    "pr165-evidence-backed-scoring-ranking": 165,
    "pr165-b-condition-scoped-negative-memory": 165,
    "pr165-c-replay-paper-memory-consumer-integration": 165,
    "pr165-d-scenario-qku-combination-selection": 165,
}
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CONTEXT_ALLOWANCES = {
    159: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
    160: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
    161: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
}
PR152_CURRENTIZATION_AFTER_FASTFAIL_MERGE_CHANGED_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/constants.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tools/ci_branch_context.py",
    }
)
PR159_BRANCH = "pr159-official-source-retry-atomicrows-source-completion-bridge"
PR159_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159_",
    "src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge/",
    "tests/stage1_prediction_markets/pr159_official_source_completion_bridge/",
)
PR160_BRANCH = "pr160-pr154-split-reclassification-route-closure-bridge"
PR160_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR160_",
    "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/",
    "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/",
)
PR160_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr160_split_reclassification_route_closure.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR161A_BRANCH = "pr161a-atomicrows-pr154-value-state-materialization-bridge"
PR161A_REPAIR_BRANCH = "repair/pr161a-atomicrows-pr154-value-state-materialization-bridge"
PR161A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR161A_",
    "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/",
    "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/schemas/pr161a_",
    "tests/stage1_prediction_markets/atomicrows_pr154_value_state/",
)
PR161A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/__init__.py",
        "tools/build_pr161a_atomicrows_pr154_value_state_materialization.py",
        "tools/validate_pr161a_atomicrows_pr154_value_state_materialization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR161B_BRANCH = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
PR161B_REPAIR_BRANCH = "repair/pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
PR161B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR161B_",
    "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/",
    "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/",
)
PR161B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161b_master_plan_residual_candidate_coverage.py",
        "tools/validate_pr161b_master_plan_residual_candidate_coverage.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR161C_BRANCH = "pr161c-qku-residual-candidate-assimilation-fill-campaign"
PR161C_GENERATED_REPORT_FILENAMES = (
    "PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT.report.json",
    "PR161C_PR161APrimaryEntityDiagnostic.report.json",
    "PR161C_PR161AFieldValueFacetDiagnostic.report.json",
    "PR161C_PR161BQueueDiagnostic.report.json",
    "PR161C_PR161BToPR161AFieldCoverageDiagnostic.report.json",
    "PR161C_QKUSupplementalArtifactScout.report.json",
    "PR161C_QKUResidualTypeBreakdown.report.json",
    "PR161C_QKUResidualDiagnosticJustification.report.json",
    "PR161C_QKUFillLaneBreakdown.report.json",
    "PR161C_QKUAuthorityAndProvenanceBreakdown.report.json",
    "PR161C_QKUAgentAndWorkflowBreakdown.report.json",
    "PR161C_QKUMarketBreakdown.report.json",
    "PR161C_QKULaunchStageBreakdown.report.json",
    "PR161C_QKUClassicalQuantumHybridBreakdown.report.json",
    "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    "PR161C_QKUExpandedRecordAccounting.report.json",
    "PR161C_QKUDefaultMaterializationCoverage.report.json",
    "PR161C_QKUNumericDefaultMaterialization.report.json",
    "PR161C_QKUFormulaDefaultMaterialization.report.json",
    "PR161C_QKUAlgorithmConfigMaterialization.report.json",
    "PR161C_QKUOptimizerDefaultMaterialization.report.json",
    "PR161C_QKUOwnerFallbackDefaultMaterialization.report.json",
    "PR161C_QKUOnlineSourceMaterialization.report.json",
    "PR161C_QKUAgentLaunchReadinessMaterialization.report.json",
    "PR161C_QKUCanonicalRegistry.report.json",
    "PR161C_QKUAliasMap.report.json",
    "PR161C_QKUTypeTaxonomy.report.json",
    "PR161C_QKUResidualAssimilationRegistry.report.json",
    "PR161C_QKUResidualAssimilationDelta.report.json",
    "PR161C_QKUFormulaAlgorithmAssimilation.report.json",
    "PR161C_QKUParameterRangeAssimilation.report.json",
    "PR161C_QKUQuantumAssimilation.report.json",
    "PR161C_QKUQuantumResidualTrace.report.json",
    "PR161C_QKUClassicalHybridAssimilation.report.json",
    "PR161C_QKUReplayPaperRouteBridge.report.json",
    "PR161C_QKUAgentConsumptionBridge.report.json",
    "PR161C_QKUUpstreamDownstreamTraceability.report.json",
    "PR161C_QKUWorkflowProcessBridge.report.json",
    "PR161C_QKUDownstreamPRFileBridge.report.json",
    "PR161C_QKUOrchestrationCompleteness.report.json",
    "PR161C_QKUOrchestrationGraph.report.json",
    "PR161C_QKUOrchestrationGraphEdges.report.json",
    "PR161C_QKUOrchestrationGraphCompleteness.report.json",
    "PR161C_QKUGraphQualityMetrics.report.json",
    "PR161C_QKUIsolatedNodeAudit.report.json",
    "PR161C_QKUSourceUpgradeQueue.report.json",
    "PR161C_QKUOnlineScoutQueue.report.json",
    "PR161C_QKUSourceIntakeAcceptancePolicy.report.json",
    "PR161C_QKUOnlineRetrievalAudit.report.json",
    "PR161C_QKUMasterInventoryBridge.report.json",
    "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "PR161C_QKUPR154CompatibilityBridge.report.json",
    "PR161C_QKUMarketClassificationInventory.report.json",
    "PR161C_QKULaunchStageClassification.report.json",
    "PR161C_QKUClassicalQuantumHybridInventory.report.json",
    "PR161C_QKUAlgorithmFormulaStrategyInventory.report.json",
    "PR161C_QKUQuantumForwardOptimizationInventory.report.json",
    "PR161C_QKUAgentRetrievalIndex.report.json",
    "PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json",
    "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    "PR161C_QKUCrossMarketReuseIndex.report.json",
    "PR161C_QKURangeOptimizerMaterializationAudit.report.json",
    "PR161C_QKUFallbackDefaultExhaustionAudit.report.json",
    "PR161C_QKUFinalAssimilationSummary.report.json",
    "PR161C_ForbiddenAuthorityScan.report.json",
    "PR161C_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161C_QKUReportShardManifest.report.json",
    "PR161C_BranchContextAndDeterministicAudit.report.json",
)
PR161C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161c_qku_report_shards/",
    "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation/",
    "tests/stage1_prediction_markets/qku_residual_candidate_assimilation/",
)
PR161C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161c_qku_residual_candidate_assimilation.py",
        "tools/validate_pr161c_qku_residual_candidate_assimilation.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161C_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161D_BRANCH = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"
PR161D_GENERATED_REPORT_FILENAMES = (
    "PR161D_QKU_CANDIDATE_QUALITY_PREFLIGHT_RECEIPT.report.json",
    "PR161D_QKUOnlineSearchCapabilityReceipt.report.json",
    "PR161D_QKUQualityScoreRegistry.report.json",
    "PR161D_QKUScoreComponentBreakdown.report.json",
    "PR161D_QKUQualityLaneClassification.report.json",
    "PR161D_QKUReplayPaperPriorityQueue.report.json",
    "PR161D_QKUReplayPaperScenarioInputs.report.json",
    "PR161D_QKUOnlineEnrichmentClusterMap.report.json",
    "PR161D_QKUOnlineEnrichmentCoverage.report.json",
    "PR161D_QKUOnlineSourceCandidateRegistry.report.json",
    "PR161D_QKUQuantumPriorityQueue.report.json",
    "PR161D_QKUClassicalBaselinePriorityQueue.report.json",
    "PR161D_QKUHybridArbitrationPriorityQueue.report.json",
    "PR161D_QKUAtomicRowsPR154PriorityBridge.report.json",
    "PR161D_QKUAgentTaskQueue.report.json",
    "PR161D_QTTAgentRoleNetworkRegistry.report.json",
    "PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "PR161D_QKUAgentLayerCoverage.report.json",
    "PR161D_QKUAgentRoleCoverageGaps.report.json",
    "PR161D_QKUStage1Day1PriorityIndex.report.json",
    "PR161D_QKUOwnerReviewQueue.report.json",
    "PR161D_QKUGraphConsumptionAudit.report.json",
    "PR161D_QKUScoringPolicyConsumptionAudit.report.json",
    "PR161D_QKUScenarioOutcomeMatrix.report.json",
    "PR161D_QKUOrderConditionScenarioRegistry.report.json",
    "PR161D_QKUCombinationCandidateRegistry.report.json",
    "PR161D_QKUCombinationScenarioMap.report.json",
    "PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "PR161D_QKUCombinationGenerationBoundedness.report.json",
    "PR161D_QKUMarketBundleActivationPolicy.report.json",
    "PR161D_QKUMarketBundleActivationDashboardOptions.report.json",
    "PR161D_QKUMarketBundleDormancyQueue.report.json",
    "PR161D_QKUMarketActiveBundleSet.report.json",
    "PR161D_QKUAgentRoleBundleSlice.report.json",
    "PR161D_QKUAgentRoleBundleReferenceFanout.report.json",
    "PR161D_QKUCategoryRankingRegistry.report.json",
    "PR161D_QKUCategoryTopListIndex.report.json",
    "PR161D_QKUCategoryRankingBreakdown.report.json",
    "PR161D_QKUFutureProfitabilityPatternFields.report.json",
    "PR161D_QKUResultBackedRankingSlots.report.json",
    "PR161D_QKUForbiddenAuthorityScan.report.json",
    "PR161D_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161D_ReportShardManifest.report.json",
    "PR161D_FinalSummary.report.json",
)
PR161D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161d_qku_candidate_quality_shards/",
    "src/qtt/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/",
    "tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/",
)
PR161D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
        "tools/validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161D_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161E_BRANCH = "pr161e-replay-paper-outcome-capture-scenario-learning-bridge"
PR161E_GENERATED_REPORT_FILENAMES = (
    "PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json",
    "PR161E_ReplayPaperResultArtifactDiscovery.report.json",
    "PR161E_ResultAuthenticityClassification.report.json",
    "PR161E_ReplayResultPacketValidation.report.json",
    "PR161E_PaperResultPacketValidation.report.json",
    "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "PR161E_QKUBundleResultLedger.report.json",
    "PR161E_QKUReplayPaperProfitabilityLedger.report.json",
    "PR161E_QKUScenarioResultAttribution.report.json",
    "PR161E_QKUResultBackedRankingUpdateCandidates.report.json",
    "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json",
    "PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
    "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json",
    "PR161E_ResultConfidenceGate.report.json",
    "PR161E_OwnerReviewResultPromotionQueue.report.json",
    "PR161E_AgentOutcomeTaskQueue.report.json",
    "PR161E_OnlineMetricCandidateIntake.report.json",
    "PR161E_OpenIntakeCandidateBridge.report.json",
    "PR161E_MissingValueCandidateMaterialization.report.json",
    "PR161E_QKUGraphTraceabilityBridge.report.json",
    "PR161E_QKUCoverageAndOrphanAudit.report.json",
    "PR161E_ForbiddenAuthorityScan.report.json",
    "PR161E_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161E_SharedDictionary.report.json",
    "PR161E_ReportShardManifest.report.json",
    "PR161E_FinalSummary.report.json",
)
PR161E_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161e_replay_paper_outcome_capture_shards/",
    "src/qtt/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/",
    "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/",
)
PR161E_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161e_replay_paper_outcome_capture_scenario_learning.py",
        "tools/validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161E_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161F_BRANCH = "pr161f-replay-paper-executor-input-run-artifact-generation"
PR161F_GENERATED_REPORT_FILENAMES = (
    "PR161F_ReplayPaperExecutorInputPreflightReceipt.report.json",
    "PR161F_ExecutorCapabilityDiscovery.report.json",
    "PR161F_HistoricalDataCandidateDiscovery.report.json",
    "PR161F_DatasetAuthorityClassification.report.json",
    "PR161F_ExecutorInputRegistry.report.json",
    "PR161F_ReplayRunRequestRegistry.report.json",
    "PR161F_PaperRunRequestRegistry.report.json",
    "PR161F_PairedReplayPaperRunPlan.report.json",
    "PR161F_RunArtifactEnvelopeRegistry.report.json",
    "PR161F_SyntheticSmokeRunArtifactRegistry.report.json",
    "PR161F_RealNonLiveRunArtifactRegistry.report.json",
    "PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "PR161F_QuantumClassicalHybridRunPlan.report.json",
    "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "PR161F_AgentRunTaskQueue.report.json",
    "PR161F_OwnerReviewRunReadinessQueue.report.json",
    "PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "PR161F_QTTAgentRoleIOContract.report.json",
    "PR161F_QTTAgentHandoffMatrix.report.json",
    "PR161F_QTTAgentFailureResponseMatrix.report.json",
    "PR161F_QTTAgentTaskReceiptLedger.report.json",
    "PR161F_QTTAgentCommunicationProtocol.report.json",
    "PR161F_QTTAgentKPIReadinessBridge.report.json",
    "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
    "PR161F_QTTAgentOwnerEscalationQueue.report.json",
    "PR161F_OnlineCandidateIntake.report.json",
    "PR161F_MissingValueCandidateMaterialization.report.json",
    "PR161F_QKUGraphTraceabilityBridge.report.json",
    "PR161F_ForbiddenAuthorityScan.report.json",
    "PR161F_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161F_SharedDictionary.report.json",
    "PR161F_ReportShardManifest.report.json",
    "PR161F_SizeAudit.report.json",
    "PR161F_FinalSummary.report.json",
)
PR161F_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161f_replay_paper_executor_input_run_artifact_generation_shards/",
    "src/qtt/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/",
    "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/",
)
PR161F_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161f_replay_paper_executor_input_run_artifact_generation.py",
        "tools/validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation/validator.py",
        "src/qtt/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/validator.py",
        "src/qtt/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/validator.py",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161F_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162_BRANCH = "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge"
PR162_GENERATED_REPORT_FILENAMES = (
    "PR162_FinalSummary.report.json",
    "PR162_SharedDictionary.report.json",
    "PR162_NonLiveDatasetDiscovery.report.json",
    "PR162_DataAuthorityAndProvenanceGate.report.json",
    "PR162_ReplayDataAdapterContract.report.json",
    "PR162_PaperDataAdapterContract.report.json",
    "PR162_AdapterCapabilityDiscovery.report.json",
    "PR162_SyntheticVsRealNonLiveSeparation.report.json",
    "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "PR162_ResultPacketReadinessHandoffCandidate.report.json",
    "PR162_PR161EIngestionHandoffCandidate.report.json",
    "PR162_QKUArtifactCoverageBridge.report.json",
    "PR162_QTTAgentExecutorHandoffBridge.report.json",
    "PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
    "PR162_ExternalCandidateIntakeRegistry.report.json",
    "PR162_ForbiddenAuthorityScan.report.json",
    "PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "PR162_QuantumParameterRangeCandidateRegistry.report.json",
    "PR162_QuantumBackendFitCandidateMatrix.report.json",
    "PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
    "PR162_QuantumReplayPaperWorkOrderQueue.report.json",
    "PR162_QuantumLiveModeControlPlaneBridge.report.json",
    "PR162_QuantumLatencyLivePathReadinessBridge.report.json",
    "PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
    "PR162_ReportShardManifest.report.json",
)
PR162_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162_safe_nonlive_replay_paper_quantum_forward_shards/",
    "src/qtt/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge/",
    "tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge/",
)
PR162_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162A_BRANCH = "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate"
PR162A_GENERATED_REPORT_FILENAMES = (
    "PR162A_FinalSummary.report.json",
    "PR162A_SharedDictionary.report.json",
    "PR162A_SourceDiscoveryCandidateRegistry.report.json",
    "PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json",
    "PR162A_DatasetMaterializationManifest.report.json",
    "PR162A_DatasetAuthorityGate.report.json",
    "PR162A_DatasetProvenanceAccessRightsLedger.report.json",
    "PR162A_DatasetSafetyAndForbiddenPathScan.report.json",
    "PR162A_DatasetLifecycleStateRegistry.report.json",
    "PR162A_DatasetSchemaNormalizationContract.report.json",
    "PR162A_NormalizedDatasetInventory.report.json",
    "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json",
    "PR162A_MarketScenarioQKUMappingMatrix.report.json",
    "PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
    "PR162A_PR162AdapterRerunReadinessBridge.report.json",
    "PR162A_PR163ReadinessBlockerStatus.report.json",
    "PR162A_QuantumQKUDatasetFeatureBridge.report.json",
    "PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
    "PR162A_QTTAgentDatasetHandoffBridge.report.json",
    "PR162A_MissingValueCandidateRegistry.report.json",
    "PR162A_ForbiddenAuthorityScan.report.json",
    "PR162A_ReportShardManifest.report.json",
)
PR162A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162a_safe_repo_local_nonlive_dataset_shards/",
    "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/",
    "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/",
    "data/stage1_prediction_markets/nonlive_datasets/pr162a/",
)
PR162A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162A_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162B_BRANCH = "pr162b-qku-formula-algorithm-solver-market-scope-materialization"
PR162B_GENERATED_REPORT_FILENAMES = (
    "PR162B_FinalSummary.report.json",
    "PR162B_SharedDictionary.report.json",
    "PR162B_FormulaSourceRetrievalTargetMatrix.report.json",
    "PR162B_QKUExecutionClassificationAudit.report.json",
    "PR162B_QKUMarketClassificationRegistry.report.json",
    "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
    "PR162B_QKUDormancyRegistry.report.json",
    "PR162B_QKUTradeRoleRegistry.report.json",
    "PR162B_QKUMarketInputFieldRequirementMatrix.report.json",
    "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    "PR162B_QKUMarketClassificationCoverageAudit.report.json",
    "PR162B_QKUFormulaCoverageAudit.report.json",
    "PR162B_QKUFormulaRegistry.report.json",
    "PR162B_QKUAlgorithmRegistry.report.json",
    "PR162B_QKUObjectiveFunctionRegistry.report.json",
    "PR162B_QKUConstraintRegistry.report.json",
    "PR162B_QKUParameterValueRegistry.report.json",
    "PR162B_QKUParameterRangeScaleRegistry.report.json",
    "PR162B_QKUTradableValueCandidateRegistry.report.json",
    "PR162B_QKUSolverMappingRegistry.report.json",
    "PR162B_QKUExecutableComputeContractRegistry.report.json",
    "PR162B_QKUFormulaTestVectorRegistry.report.json",
    "PR162B_QKUAlgorithmTestVectorRegistry.report.json",
    "PR162B_QKUFormulaImplementationBindingRegistry.report.json",
    "PR162B_QKUFormulaBindingProofMatrix.report.json",
    "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "PR162B_QuantumSolverSmokeExecutionReport.report.json",
    "PR162B_AgentFormulaConsumerRoutingMatrix.report.json",
    "PR162B_LiveModeFormulaGateStatus.report.json",
    "PR162B_MetadataOnlyBlockerAudit.report.json",
    "PR162B_PR162CDataRequirementHandoff.report.json",
    "PR162B_ForbiddenAuthorityScan.report.json",
    "PR162B_ReportShardManifest.report.json",
)
PR162B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162b_qku_formula_solver_market_scope_shards/",
    "src/qtt/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization/",
    "tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization/",
)
PR162B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162B_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162C_BRANCH = "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
PR162C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162C_",
    "docs/master_plan/generated/PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT.report.json",
    "docs/master_plan/generated/pr162c_multisource_safe_nonlive_dataset_shards/",
    "src/qtt/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/",
    "tests/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/",
)
PR162C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
        "tools/validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_BRANCH = "pr162d-aggressive-qku-candidate-materialization-agent-routing"
PR162D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_",
    "docs/master_plan/generated/pr162d_aggressive_qku_candidate_materialization_agent_routing_shards/",
    "src/qtt/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing/",
    "tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing/",
)
PR162D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
        "tools/validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_R1_BRANCH = "pr162d-r1-external-formula-data-quantum-acquisition-expansion"
PR162D_R1_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_R1_",
    "src/qtt/stage1_prediction_markets/"
    "pr162d_r1_external_formula_data_quantum_acquisition_expansion/",
    "tests/stage1_prediction_markets/"
    "pr162d_r1_external_formula_data_quantum_acquisition_expansion/",
)
PR162D_R1_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
        "tools/validate_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162R_A_BRANCH = "pr162r-a-replay-paper-executability-classification-audit"
PR162R_A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162R_A_",
    "src/qtt/stage1_prediction_markets/"
    "pr162r_a_replay_paper_executability_classification_audit/",
    "tests/stage1_prediction_markets/"
    "pr162r_a_replay_paper_executability_classification_audit/",
)
PR162R_A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_a_replay_paper_executability_classification_audit.py",
        "tools/validate_pr162r_a_replay_paper_executability_classification_audit.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_R2A_BRANCH = "pr162d-r2a-real-computable-formulations-redo"
PR162D_R2A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_R2A_",
    "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/",
    "tests/stage1_prediction_markets/pr162d_r2a_real_formulations/",
)
PR162D_R2A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_r2a_real_formulations.py",
        "tools/validate_pr162d_r2a_real_formulations.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR162R_BRANCH = "pr162r-generic-replay-paper-adapter-rerun"
PR162R_GENERATED_REPORT_FILENAMES = (
    "PR162R_InputConsumptionAudit.report.json",
    "PR162R_CandidatePacketV1IngestionLedger.report.json",
    "PR162R_CandidatePacketSchemaCompatibilityAudit.report.json",
    "PR162R_QKUComputabilityClassificationMatrix.report.json",
    "PR162R_QKUNonPlaceholderCompletionAudit.report.json",
    "PR162R_FormulationCallableImportAudit.report.json",
    "PR162R_FormulationSmokeExecutionLedger.report.json",
    "PR162R_SourceCandidateMaterializationQueue.report.json",
    "PR162R_OnlineSourceScoutQueue.report.json",
    "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
    "PR162R_MissingDataBindingActionQueue.report.json",
    "PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "PR162R_PaperAdapterInputPacketRegistry.report.json",
    "PR162R_ReplayRunRequestCandidateQueue.report.json",
    "PR162R_PaperRunRequestCandidateQueue.report.json",
    "PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json",
    "PR162R_LatencyPrecomputeRoutingMatrix.report.json",
    "PR162R_RouteTriageCrosswalkConsumptionAudit.report.json",
    "PR162R_MarketSpecificQKUAdapterIndex.report.json",
    "PR162R_CommandActionQKUBindingMatrix.report.json",
    "PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "PR162R_PR163PaperAdapterHandoffSeed.report.json",
    "PR162R_PR164ReviewProvenanceHandoffSeed.report.json",
    "PR162R_PR165ScoringRankingHandoffSeed.report.json",
    "PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json",
    "PR162R_OrphanCandidateReportAudit.report.json",
    "PR162R_NoReplayPaperResultPacketAudit.report.json",
    "PR162R_NoLiveOrderProfitAuthorityAudit.report.json",
    "PR162R_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
    "PR162R_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR162R_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR162R_Old548CompatibilityTrace.report.json",
    "PR162R_FinalSummary.report.json",
    "PR162R_DecisionAndNextPRRecommendation.report.json",
    "PR162R_ReportManifest.report.json",
)
PR162R_ALLOWED_CHANGED_PATH_PREFIXES = (
    "src/qtt/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/",
    "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/",
)
PR162R_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_generic_replay_paper_adapter_rerun.py",
        "tools/validate_pr162r_generic_replay_paper_adapter_rerun.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162R_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162R_B_BRANCH = "pr162r-b-replay-paper-data-binding-completion"
PR162R_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162R_B_",
    "docs/master_plan/generated/pr162r_b_shards/",
    "src/qtt/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
    "tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
    "tests/fixtures/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
)
PR162R_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_b_replay_paper_data_binding_completion.py",
        "tools/validate_pr162r_b_replay_paper_data_binding_completion.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/validators.py",
        "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/test_orphan_audit.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_BRANCH = "pr163-generic-paper-adapter-capture-framework"
PR163_B_BRANCH = "pr163-b-paired-replay-paper-concurrent-executor"
PR163_C_BRANCH = "pr163-c-pretrade-infrastructure-rejection-remediation"
PR164_BRANCH = "pr164-review-provenance-qku-canonical-coverage-audit"
PR165_BRANCH = "pr165-evidence-backed-scoring-ranking"
PR165_B_BRANCH = "pr165-b-condition-scoped-negative-memory"
PR165_C_BRANCH = "pr165-c-replay-paper-memory-consumer-integration"
PR165_D_BRANCH = "pr165-d-scenario-qku-combination-selection"
PR163_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_",
    "docs/master_plan/generated/pr163_shards/",
    "src/qtt/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework/",
    "tests/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework/",
)
PR163_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_generic_paper_adapter_capture_framework.py",
        "tools/validate_pr163_generic_paper_adapter_capture_framework.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_B_",
    "docs/master_plan/generated/pr163_b_shards/",
    "src/qtt/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor/",
    "tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor/",
)
PR163_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_b_paired_replay_paper_concurrent_executor.py",
        "tools/validate_pr163_b_paired_replay_paper_concurrent_executor.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_C_",
    "docs/master_plan/generated/pr163_c_shards/",
    "src/qtt/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation/",
    "tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation/",
)
PR163_C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR164_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR164_",
    "docs/master_plan/generated/pr164_shards/",
    "src/qtt/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit/",
    "tests/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit/",
)
PR164_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr164_review_provenance_qku_canonical_coverage_audit.py",
        "tools/validate_pr164_review_provenance_qku_canonical_coverage_audit.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_",
    "docs/master_plan/generated/pr165_shards/",
    "src/qtt/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking/",
    "tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking/",
)
PR165_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_evidence_backed_scoring_ranking.py",
        "tools/validate_pr165_evidence_backed_scoring_ranking.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_B_",
    "docs/master_plan/generated/pr165_b_shards/",
    "src/qtt/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory/",
    "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory/",
)
PR165_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_b_condition_scoped_negative_memory.py",
        "tools/validate_pr165_b_condition_scoped_negative_memory.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_C_",
    "docs/master_plan/generated/pr165_c_shards/",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/",
    "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/",
)
PR165_C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
        "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_D_",
    "docs/master_plan/generated/pr165_d_shards/",
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/",
    "tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/",
)
PR165_D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_d_scenario_qku_combination_selection.py",
        "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR159_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr159_official_source_completion_bridge.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR159R_BRANCH = "pr159r-exact-source-locator-value-unit-capture"
PR159R_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159R_",
    "docs/master_plan/generated/PR159S_",
    "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/",
    "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/",
    "src/qtt/stage1_prediction_markets/source_intelligence/schemas/",
    "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/",
    "tests/stage1_prediction_markets/source_intelligence/",
)
PR159R_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr159r_source_locator_value_capture.py",
        "tools/build_pr159s_open_intake_completion.py",
        "tools/validate_pr159s_open_intake_completion.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/__init__.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/constants.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR159S_BRANCH = "pr159s-open-source-intelligence-candidate-completion"
PR159S_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159S_",
    "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/",
    "src/qtt/stage1_prediction_markets/source_intelligence/schemas/",
    "tests/stage1_prediction_markets/source_intelligence/",
)
PR159S_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr159s_open_intake_completion.py",
        "tools/validate_pr159s_open_intake_completion.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/__init__.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/constants.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/constants.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    }
)
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS = {
    PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH: frozenset(
        {
            "tools/ci_branch_context.py",
            "tests/tools/test_ci_branch_context.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "src/qtt/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/validator.py",
            "tests/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/"
            "test_pr159r_branch_context_relaxation.py",
            "src/qtt/stage1_prediction_markets/"
            "source_intelligence/pr159s_open_intake/validator.py",
            "tests/stage1_prediction_markets/"
            "source_intelligence/test_pr159s_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/validator.py",
            "tests/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/"
            "test_pr160_branch_context_relaxation.py",
            "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "pr161a_materialization_bridge/validator.py",
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "test_pr161a_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/validator.py",
            "tests/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/"
            "test_pr161b_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
            "validator.py",
            "src/qtt/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
            "tests/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/"
            "test_pr163_c_repeat_run_determinism.py",
        }
    ),
    "repair-pr153r-redo-report-determinism": frozenset(
        {
            "tools/ci_branch_context.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        }
    ),
    "repair/pr153s-source-value-capture-closure-classifier": frozenset(
        {
            "docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/__init__.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/classifier.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/inputs.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/report.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/taxonomy.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/validator.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/source_evidence/test_pr153s_source_value_capture_closure_classifier.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr153s_source_value_capture_closure_classifier.py",
        }
    ),
    "repair/pr154-post-merge-pytest-context-hygiene": frozenset(
        {
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
        }
    ),
    "pr154-atomicrows-parameter-default-value-materialization-gate": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/__init__.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/inputs.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/materializer.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/report.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/taxonomy.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/validator.py",
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_atomicrows_parameter_default_value_materialization_gate.py",
        }
    ),
    "pr155-agent-consumable-parameter-default-registry": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json",
            "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.report.json",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/__init__.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/builder.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/constants.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/input_discovery.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/io.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/mapper.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/models.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/report.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/schema_projection.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/validator.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_agent_consumable_parameter_default_registry.py",
        }
    ),
    "pr156-agent-default-binding-universal-intake-gate": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.registry.json",
            "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.report.json",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/__init__.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/agent_binding.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/atomicrows_ingestion.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/builder.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/classical_quantum_applicability.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/constants.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/future_routing.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/input_discovery.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/intake_templates.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/io.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/models.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/population_router.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/report.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/schema_projection.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/validator.py",
            "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate/test_agent_default_binding_universal_intake_gate.py",
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_agent_default_binding_universal_intake_gate.py",
        }
    ),
    "pr157-pr154-atomicrows-fillpath-owner-agent-bridge": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.report.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.registry.json",
            "docs/master_plan/generated/PR157_OwnerCompletionInputRequest.packet.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0001.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0002.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0003.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0004.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0005.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0006.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0007.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0008.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0009.json",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/__init__.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/agent_responsibility_bridge.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_4183_completion.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_fill_path.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_source_requirement_classification.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/completion_registry.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/constants.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/input_discovery.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/io.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/models.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_editability.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_input_request.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_input_validator.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/pr154_completion.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/report.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/source_authority_state.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/split_reclassification.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/validator.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_agent_responsibility_does_not_invent_exact_agent_ids.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_4183_universe_reconciles.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_classification_counts_sum_to_4183.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_no_placeholder_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_source_requirement_classification_exactly_one_primary.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_classical_quantum_hybrid_metadata_only.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_constants_centralize_blockers_and_authority_profiles.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_fill_paths_have_exact_steps_acceptance_criteria_and_unblock_validator.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_generated_artifacts_are_deterministic.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_mandatory_orchestration_inputs_consumed.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/"
            "test_pr157_no_atomicrows_bundle_check"
            "sum_hash_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_orphan_status_for_all_targets_and_rows.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/"
            "test_pr157_no_qtt_check"
            "sum_freeze_global_"
            "digest_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_runtime_live_connector_replay_paper_scoring_optimizer_quantum_profit_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_scattered_hardcoded_no_authority_vocabulary.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_orphan_count_zero.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editability_classification_for_all_targets_and_rows.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_changes_do_not_mutate_open_orders_or_positions.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_changes_route_to_replay_paper_and_block_live.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_external_facts_forbidden.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_input_request_packet_generated.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_absent_does_not_fabricate_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_validator_rejects_ambiguous_or_external_fact_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_pr154_count_invariants.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_private_doc_requires_attestation.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_public_external_requires_existing_source_evidence.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_public_external_subpartition_invariant.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_retry_records_do_not_execute_future_source_retry_scope.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_run_validation_gates_includes_pr157.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_split_reclassification_requires_basis.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_unresolved_atomicrows_fields_have_fill_path.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_unresolved_items_have_exact_next_action.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_support.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
        }
    ),
    "pr158-owner-response-atomicrows-selection-readiness-bridge": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.registry.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
            "docs/master_plan/generated/PR157_OwnerCompletionInputRequest.packet.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.report.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0001.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0002.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0003.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0004.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0005.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0006.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0007.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0008.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0009.json",
            "docs/master_plan/generated/PR158_AgentAssignmentCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_AgentAssignmentCandidateMap.report.json",
            "docs/master_plan/generated/PR158_AgentFormulaAlgorithmSelectionCompatibilityMap.registry.json",
            "docs/master_plan/generated/PR158_AgentFormulaAlgorithmSelectionCompatibilityMap.report.json",
            "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.registry.json",
            "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.report.json",
            "docs/master_plan/generated/PR158_FutureResearchAdditionIntakeCompatibility.report.json",
            "docs/master_plan/generated/PR158_MasterPlanOwnerResponseSelectionReadinessBridge.registry.json",
            "docs/master_plan/generated/PR158_MasterPlanOwnerResponseSelectionReadinessBridge.report.json",
            "docs/master_plan/generated/PR158_OwnerDecisionSummaryForReview.md",
            "docs/master_plan/generated/PR158_OwnerPolicyDefaultCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_OwnerPolicyDefaultCandidateMap.report.json",
            "docs/master_plan/generated/PR158_OwnerResponseMaterializationPreview.report.json",
            "docs/master_plan/generated/PR158_PR154OwnerRouteCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_PR154OwnerRouteCandidateMap.report.json",
            "docs/master_plan/generated/PR158_PR154SplitReclassificationCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_PR154SplitReclassificationCandidateMap.report.json",
            "docs/master_plan/generated/PR158_ParameterRangeOwnerPolicyCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_ParameterRangeOwnerPolicyCandidateMap.report.json",
            "docs/master_plan/generated/PR158_PrecomputedLowLatencySelectionReadinessIndex.report.json",
            "docs/master_plan/generated/PR158_PrivateDocAttestationOwnerReview.md",
            "docs/master_plan/generated/PR158_TradeContextScoringFeatureMap.report.json",
            "docs/master_plan/owner_inputs/PR157_OwnerCompletionInputResponse.json",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/__init__.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/atomicrows_selection_readiness_overlay.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/constants.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/future_research_addition_intake.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/input_discovery.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/io.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_a_agent_assignment.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_b_owner_policy_default.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_c_parameter_range_owner_policy.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_d_pr154_owner_route.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_e_split_reclassification.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_f_private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/low_latency_precomputed_index.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/master_plan_authority.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/models.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_decision_summary.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_response_builder.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_response_validator.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/prior_artifact_reconciliation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/registry.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/report.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/scoring_ranking_readiness.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/trade_context_selection_readiness.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/validator.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_atomicrows_selection_readiness_overlay_count_4183.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_atomicrows_semantic_contract_compatibility_preserved.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_constants_centralize_blockers_and_authority_profiles.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_future_research_addition_intake_compatibility.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_generated_artifacts_are_deterministic.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_agent_assignment_uses_prior_artifacts.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_defer_exact_agent_id_to_pr163_when_ambiguous.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_exact_agent_ids_only_when_uniquely_supported.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_b_conservative_policy_defaults_replay_paper_required.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_b_owner_policy_defaults_use_prior_artifacts_first.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_count_invariants.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_c_no_fake_numeric_ranges.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_c_parameter_ranges_use_prior_artifacts_first.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_d_pr154_owner_routes_internal_metadata_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_e_ambiguous_records_route_to_pr160.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_e_split_reclassification_deterministic_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_f_private_doc_requires_owner_attestation.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_f_raw_secret_capture_forbidden.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_low_latency_precomputed_index_static_metadata_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_mandatory_orchestration_inputs_consumed.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_master_plan_consumed_not_edited.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/"
            "test_pr158_no_atomicrows_bundle_check"
            "sum_hash_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_fake_owner_response_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_external_facts.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_numeric_ranges.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_orphans.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_placeholder_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/"
            "test_pr158_no_qtt_check"
            "sum_freeze_global_"
            "digest_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_execution_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_scattered_hardcoded_no_authority_vocabulary.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_changes_route_to_replay_paper_and_block_live.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_decision_summary_is_human_readable.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_editability_lifecycle_preserved.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_response_items_map_to_request_ids.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_pr157_owner_request_packet_count_invariant.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_quantum_metadata_only_no_backend_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_run_validation_gates_includes_pr158.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_scoring_ranking_readiness_no_scoring_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_selection_readiness_overlay_has_scoring_feature_roles.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_source_evidence_packet_consumed.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_source_required_records_route_to_pr159.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_trade_context_selection_readiness_no_selection_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/pr158_test_support.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_absent_does_not_fabricate_values.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr158_owner_response_selection_readiness_bridge.py",
        }
    ),
}

GitStdout = Callable[[pathlib.Path, Sequence[str]], tuple[int, str, str]]


@dataclass(frozen=True)
class BranchContext:
    branch: str
    source: str
    git_error: str = ""


@dataclass(frozen=True)
class UpstreamBranchGatePolicy:
    gate_id: str
    upstream_pr: int
    allowed_branches: frozenset[str]
    local_repair_branches_requiring_ancestry: frozenset[str]
    detached_head_ref_branches: frozenset[str]
    main_push_allowed: bool = True


PR162_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR162_BRANCH,
        PR162A_BRANCH,
        PR162B_BRANCH,
        PR162C_BRANCH,
        PR162D_BRANCH,
        PR162D_R1_BRANCH,
        PR162R_A_BRANCH,
        PR162D_R2A_BRANCH,
        PR162R_BRANCH,
        PR162R_B_BRANCH,
        PR163_BRANCH,
        PR163_B_BRANCH,
        PR163_C_BRANCH,
        PR164_BRANCH,
        PR165_BRANCH,
        PR165_B_BRANCH,
        PR165_C_BRANCH,
        PR165_D_BRANCH,
    }
)
PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161C_BRANCH,
        PR161D_BRANCH,
        PR161E_BRANCH,
        PR161F_BRANCH,
        *PR162_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161B_BRANCH,
        *PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161A_BRANCH,
        *PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY = frozenset(
    {
        PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
        PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
    }
)
PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY = frozenset(
    {
        PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH,
    }
)
PR159R_DETACHED_HEAD_REPAIR_BRANCHES = frozenset(
    {
        *PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
    }
)
PR160_DETACHED_HEAD_REPAIR_BRANCHES = frozenset(
    {
        *PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
    }
)
BRANCH_CONTEXT_GATE_POLICIES = {
    "PR159R": UpstreamBranchGatePolicy(
        gate_id="PR159R",
        upstream_pr=159,
        allowed_branches=frozenset(
            {
                PR159R_BRANCH,
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=(
            PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY
        ),
        detached_head_ref_branches=PR159R_DETACHED_HEAD_REPAIR_BRANCHES,
    ),
    "PR159S": UpstreamBranchGatePolicy(
        gate_id="PR159S",
        upstream_pr=159,
        allowed_branches=frozenset(
            {
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(
            {PR159S_BRANCH_CONTEXT_REPAIR_BRANCH}
        ),
        detached_head_ref_branches=frozenset(
            {
                PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR160": UpstreamBranchGatePolicy(
        gate_id="PR160",
        upstream_pr=160,
        allowed_branches=frozenset(
            {
                PR160_BRANCH,
                PR159R_BRANCH,
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=(
            PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY
        ),
        detached_head_ref_branches=PR160_DETACHED_HEAD_REPAIR_BRANCHES,
    ),
    "PR161A": UpstreamBranchGatePolicy(
        gate_id="PR161A",
        upstream_pr=161,
        allowed_branches=frozenset(
            {
                PR161A_BRANCH,
                PR161A_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(
            {
                PR161A_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR161B": UpstreamBranchGatePolicy(
        gate_id="PR161B",
        upstream_pr=161,
        allowed_branches=frozenset(
            {
                PR161B_BRANCH,
                PR161B_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(
            {
                PR161B_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR162A": UpstreamBranchGatePolicy(
        gate_id="PR162A",
        upstream_pr=162,
        allowed_branches=frozenset(
            {
                PR162A_BRANCH,
                PR162B_BRANCH,
                PR162C_BRANCH,
                PR162D_BRANCH,
                PR162D_R1_BRANCH,
                PR162R_A_BRANCH,
                PR162D_R2A_BRANCH,
                PR162R_BRANCH,
                PR162R_B_BRANCH,
                PR163_BRANCH,
                PR163_B_BRANCH,
                PR163_C_BRANCH,
                PR164_BRANCH,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(),
    ),
    "PR163-C": UpstreamBranchGatePolicy(
        gate_id="PR163-C",
        upstream_pr=163,
        allowed_branches=frozenset({PR163_C_BRANCH}),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(),
    ),
}


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    if branch.startswith("refs/pull/"):
        return ""
    if re.match(r"^[0-9]+/(head|merge)$", branch):
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def current_branch_context(
    repo_root: pathlib.Path,
    env_candidates: Sequence[str] = BRANCH_CONTEXT_ENV_CANDIDATES,
    *,
    git_stdout: GitStdout | None = None,
) -> BranchContext:
    git_stdout = git_stdout or _git_stdout
    for env_name in env_candidates:
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return BranchContext(branch=branch, source=env_name)

    git_errors: list[str] = []
    for args in (["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]):
        branch_rc, branch_stdout, branch_err = git_stdout(repo_root, args)
        if branch_rc != 0:
            git_errors.append(branch_err or f"git {' '.join(args)} failed")
            continue
        branch = normalize_branch_context(branch_stdout)
        if branch:
            return BranchContext(branch=branch, source=f"git {' '.join(args)}")

    return BranchContext(branch="", source="", git_error="; ".join(git_errors))


def github_actions_branch_context() -> str:
    if github_actions_active() and os.getenv("GITHUB_EVENT_NAME") == "pull_request":
        return github_actions_head_ref_branch_context()
    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME", "GITHUB_REF"):
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return branch
    return ""


def github_actions_head_ref_branch_context() -> str:
    return normalize_branch_context(os.getenv("GITHUB_HEAD_REF", ""))


def github_actions_pull_request_detached_context_active(
    *,
    branch_returncode: int | None = None,
    branch: str = "",
) -> bool:
    if not github_actions_active():
        return False
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    pull_request_event = event_name in {"pull_request", "pull_request_target"}
    pull_request_ref = (
        github_ref.startswith("refs/pull/")
        or re.match(r"^[0-9]+/(head|merge)$", github_ref_name) is not None
    )
    if branch_returncode is None:
        return pull_request_event or pull_request_ref

    merge_ref = (
        re.match(r"^refs/(?:remotes/)?pull/[0-9]+/merge$", github_ref) is not None
        or re.match(r"^[0-9]+/merge$", github_ref_name) is not None
    )
    detached_branch = branch_returncode != 0 or branch.strip() in {"", "HEAD"}
    return merge_ref or (pull_request_event and detached_branch)


def github_actions_main_push_context_active() -> bool:
    if not github_actions_active():
        return False
    return (
        os.getenv("GITHUB_EVENT_NAME") == "push"
        and os.getenv("GITHUB_REF") == "refs/heads/main"
        and os.getenv("GITHUB_REF_NAME") == "main"
    )


def normalize_upstream_branch_gate(value: str | int) -> str:
    if isinstance(value, int):
        return f"PR{value}"
    gate_id = str(value).strip().upper().replace("_", "-")
    if gate_id == "PR163C":
        return "PR163-C"
    return gate_id


def upstream_branch_gate_policy(value: str | int) -> UpstreamBranchGatePolicy:
    gate_id = normalize_upstream_branch_gate(value)
    try:
        return BRANCH_CONTEXT_GATE_POLICIES[gate_id]
    except KeyError as exc:
        raise KeyError(f"unknown upstream branch gate: {value!r}") from exc


def upstream_branch_gate_pr_number(value: str | int) -> int | None:
    gate_id = normalize_upstream_branch_gate(value)
    match = re.match(r"^PR(?P<number>[0-9]+)", gate_id)
    if match is None:
        return None
    return int(match.group("number"))


def is_explicit_repair_branch_allowed_for_upstream_pr_gate(
    branch: str,
    upstream_gate: str | int,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    return (
        normalized in policy.allowed_branches
        or normalized in policy.local_repair_branches_requiring_ancestry
        or normalized in policy.detached_head_ref_branches
    )


def is_branch_allowed_for_upstream_pr_gate(
    branch: str,
    upstream_gate: str | int,
    *,
    ancestry_present: bool = False,
    include_main: bool = False,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    if is_validation_infrastructure_branch(normalized):
        return True
    if normalized == "main":
        return include_main and ancestry_present
    if normalized in policy.allowed_branches:
        return True
    gate_pr_number = upstream_branch_gate_pr_number(upstream_gate)
    branch_pr_number = roadmap_pr_number(normalized)
    if (
        ancestry_present
        and gate_pr_number is not None
        and branch_pr_number is not None
        and branch_pr_number >= gate_pr_number
    ):
        return True
    return (
        normalized in policy.local_repair_branches_requiring_ancestry
        and ancestry_present
    )


def is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
    branch_context: str,
    upstream_gate: str | int,
) -> bool:
    normalized = normalize_branch_context(branch_context)
    if not normalized:
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    return (
        is_validation_infrastructure_branch(normalized)
        or normalized in policy.allowed_branches
        or normalized in policy.local_repair_branches_requiring_ancestry
        or normalized in policy.detached_head_ref_branches
        or (
            upstream_branch_gate_pr_number(upstream_gate) is not None
            and roadmap_pr_number(normalized) is not None
            and roadmap_pr_number(normalized)
            >= upstream_branch_gate_pr_number(upstream_gate)
        )
    )


def is_main_push_context_allowed_for_upstream_pr_gate(
    branch_context: str,
    upstream_gate: str | int,
    *,
    ancestry_present: bool,
) -> bool:
    return (
        github_actions_main_push_context_active()
        and upstream_branch_gate_policy(upstream_gate).main_push_allowed
        and normalize_branch_context(branch_context) == "main"
        and ancestry_present
    )


def changed_path_allowed_for_explicit_repair_branch(branch: str, path: str) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    return is_explicit_downstream_repair_changed_path(normalized, path)


def is_validation_infrastructure_branch(branch: str) -> bool:
    normalized = normalize_branch_context(branch)
    return normalized in VALIDATION_INFRASTRUCTURE_BRANCHES


def is_validation_infrastructure_changed_path(branch: str, path: str) -> bool:
    if not is_validation_infrastructure_branch(branch):
        return False
    normalized = path.replace("\\", "/")
    return (
        normalized in VALIDATION_INFRASTRUCTURE_CHANGED_PATHS
        or _is_pr165_scoring_changed_path(normalized)
        or _is_pr165_b_condition_memory_changed_path(normalized)
        or _is_pr165_c_memory_consumer_changed_path(normalized)
        or _is_pr165_d_scenario_selection_changed_path(normalized)
    )


def is_repair_branch(branch: str) -> bool:
    return branch.startswith(REPAIR_BRANCH_PREFIX)


def is_main_cumulative_branch(branch: str) -> bool:
    return (
        branch == "main"
        or branch in VALIDATION_INFRASTRUCTURE_BRANCHES
        or branch.startswith(MAIN_CUMULATIVE_BRANCH_PREFIX)
    )


def roadmap_pr_number(branch: str) -> int | None:
    if normalize_branch_context(branch).startswith(PR208_CI_RUNTIME_RATIONALIZATION_BRANCH):
        return None
    match = re.match(r"^pr(?P<number>[0-9]+)[a-z]*-", branch)
    if match is None:
        return None
    return int(match.group("number"))


def is_same_pr_repair_branch(branch: str, pr_number: int) -> bool:
    if not is_repair_branch(branch):
        return False
    repair_target = branch[len(REPAIR_BRANCH_PREFIX) :]
    return roadmap_pr_number(repair_target) == pr_number


def pr_branch_ancestry_ref_candidates(branch: str) -> tuple[str, ...]:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return ()
    return (
        normalized,
        f"refs/heads/{normalized}",
        f"origin/{normalized}",
        f"refs/remotes/origin/{normalized}",
    )


def pr_branch_ancestry_present(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    for ancestor_ref in pr_branch_ancestry_ref_candidates(branch):
        ancestor_rc, _ancestor_out, _ancestor_err = git_stdout(
            repo_root,
            ["merge-base", "--is-ancestor", ancestor_ref, descendant],
        )
        if ancestor_rc == 0:
            return True
    return False


def github_merge_commit_subject_mentions_branch(subject: str, branch: str) -> bool:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    return (
        re.match(
            rf"^Merge pull request #[0-9]+ from [^\s/]+/{re.escape(normalized)}$",
            subject.strip(),
        )
        is not None
    )


def pr_branch_merged_ancestry_present(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    if pr_branch_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    ):
        return True

    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    log_rc, log_out, _log_err = git_stdout(
        repo_root,
        [
            "log",
            "--format=%s",
            "--fixed-strings",
            f"--grep=/{normalized}",
            descendant,
        ],
    )
    if log_rc != 0:
        return False
    return any(
        github_merge_commit_subject_mentions_branch(line, normalized)
        for line in log_out.splitlines()
    )


def _shallow_repository(
    repo_root: pathlib.Path,
    *,
    git_stdout: GitStdout,
) -> bool:
    shallow_rc, shallow_out, _shallow_err = git_stdout(
        repo_root,
        ["rev-parse", "--is-shallow-repository"],
    )
    return shallow_rc == 0 and shallow_out.strip().lower() == "true"


def _refresh_shallow_repository_history(
    repo_root: pathlib.Path,
    *,
    git_stdout: GitStdout,
) -> bool:
    fetch_attempts = (
        ["fetch", "--no-tags", "--prune", "--unshallow", "origin"],
        ["fetch", "--no-tags", "--prune", "--depth=2147483647", "origin"],
    )
    for args in fetch_attempts:
        fetch_rc, _fetch_out, _fetch_err = git_stdout(repo_root, args)
        if fetch_rc == 0:
            return True
    return False


def pr_branch_merged_ancestry_present_with_shallow_refresh(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    if pr_branch_merged_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    ):
        return True
    if not _shallow_repository(repo_root, git_stdout=git_stdout):
        return False
    if not _refresh_shallow_repository_history(repo_root, git_stdout=git_stdout):
        return False
    return pr_branch_merged_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    )


def _explicit_downstream_repair_branch_pr_number(branch: str) -> int | None:
    return EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS.get(branch)


def is_explicit_downstream_repair_branch_context_allowed(
    branch: str,
    *,
    upstream_pr: int,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    repair_pr = _explicit_downstream_repair_branch_pr_number(normalized)
    return (
        repair_pr is not None
        and repair_pr > upstream_pr
        and (
            normalized
            in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CONTEXT_ALLOWANCES.get(
                upstream_pr,
                frozenset(),
            )
        )
    )


def is_explicit_downstream_repair_changed_path(branch: str, path: str) -> bool:
    normalized = path.replace("\\", "/")
    if (
        is_pr_or_later_branch(
            branch,
            152,
            allow_main=False,
            allow_repair=False,
        )
        and normalized in PR152_CURRENTIZATION_AFTER_FASTFAIL_MERGE_CHANGED_PATHS
    ):
        return True
    if branch == PR163_BRANCH:
        return normalized in PR163_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR163_B_BRANCH:
        return normalized in PR163_B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR163_C_BRANCH:
        return normalized in PR163_C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR164_BRANCH:
        return normalized in PR164_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR164_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR165_BRANCH:
        return _is_pr165_scoring_changed_path(normalized)
    if branch == PR165_B_BRANCH:
        return _is_pr165_b_condition_memory_changed_path(normalized)
    if branch == PR165_C_BRANCH:
        return _is_pr165_c_memory_consumer_changed_path(normalized)
    if branch == PR165_D_BRANCH:
        return _is_pr165_d_scenario_selection_changed_path(normalized)
    if branch == PR162R_B_BRANCH:
        return normalized in PR162R_B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162R_BRANCH:
        return normalized in PR162R_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_R2A_BRANCH:
        return normalized in PR162D_R2A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_R2A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162R_A_BRANCH:
        return normalized in PR162R_A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_R1_BRANCH:
        return normalized in PR162D_R1_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_R1_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_BRANCH:
        return normalized in PR162D_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162C_BRANCH:
        return normalized in PR162C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162B_BRANCH:
        return normalized in PR162B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162A_BRANCH:
        return normalized in PR162A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162_BRANCH:
        return normalized in PR162_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161F_BRANCH:
        return normalized in PR161F_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161F_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161E_BRANCH:
        return normalized in PR161E_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161E_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161D_BRANCH:
        return normalized in PR161D_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161D_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161C_BRANCH:
        return normalized in PR161C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR159_BRANCH:
        return normalized in PR159_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR159S_BRANCH or ci_branch_context_pr159s_repair(branch):
        return normalized in PR159S_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159S_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch in {
        PR159R_BRANCH,
        PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
    }:
        return normalized in PR159R_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159R_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch in {
        PR160_BRANCH,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH,
    }:
        return normalized in PR160_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR160_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161B_BRANCH or branch == PR161B_REPAIR_BRANCH:
        return normalized in PR161B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161A_BRANCH or branch == PR161A_REPAIR_BRANCH:
        return normalized in PR161A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    return normalized in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.get(
        branch,
        frozenset(),
    )


def _is_pr165_scoring_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_b_condition_memory_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_B_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_B_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_c_memory_consumer_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_C_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_C_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_d_scenario_selection_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_D_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_D_ALLOWED_CHANGED_PATH_PREFIXES
    )


def ci_branch_context_pr159s_repair(branch: str) -> bool:
    return branch == PR159S_BRANCH_CONTEXT_REPAIR_BRANCH


def is_downstream_roadmap_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr > after_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number > after_pr


def is_downstream_or_main_validation_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    return is_main_cumulative_branch(branch) or is_downstream_roadmap_branch(
        branch,
        after_pr,
        allow_repair=allow_repair,
    )


def is_pr_or_later_branch(
    branch: str,
    minimum_pr: int,
    *,
    allow_main: bool = True,
    allow_repair: bool = True,
) -> bool:
    if allow_main and is_main_cumulative_branch(branch):
        return True
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr >= minimum_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number >= minimum_pr
