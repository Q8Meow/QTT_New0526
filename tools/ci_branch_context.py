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
    "repair/pr159r-branch-context-relaxation": 159,
    "pr160-pr154-split-reclassification-route-closure-bridge": 160,
    "repair/pr160-main-push-branch-context-relaxation": 160,
}
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
    "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/",
    "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/",
)
PR159R_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr159r_source_locator_value_capture.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/constants.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS = {
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
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_atomicrows_bundle_checksum_hash_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_orphan_status_for_all_targets_and_rows.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_qtt_checksum_freeze_global_digest_authority.py",
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
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_atomicrows_bundle_checksum_hash_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_fake_owner_response_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_external_facts.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_numeric_ranges.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_orphans.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_placeholder_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_qtt_checksum_freeze_global_digest_authority.py",
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


def is_repair_branch(branch: str) -> bool:
    return branch.startswith(REPAIR_BRANCH_PREFIX)


def is_main_cumulative_branch(branch: str) -> bool:
    return branch == "main" or branch.startswith(MAIN_CUMULATIVE_BRANCH_PREFIX)


def roadmap_pr_number(branch: str) -> int | None:
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


def _explicit_downstream_repair_branch_pr_number(branch: str) -> int | None:
    return EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS.get(branch)


def is_explicit_downstream_repair_changed_path(branch: str, path: str) -> bool:
    normalized = path.replace("\\", "/")
    if branch == PR159_BRANCH:
        return normalized in PR159_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR159R_BRANCH or is_same_pr_repair_branch(branch, 159):
        return normalized in PR159R_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159R_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR160_BRANCH or is_same_pr_repair_branch(branch, 160):
        return normalized in PR160_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR160_ALLOWED_CHANGED_PATH_PREFIXES
        )
    return normalized in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.get(
        branch,
        frozenset(),
    )


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
