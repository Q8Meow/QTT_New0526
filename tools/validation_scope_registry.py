#!/usr/bin/env python3
"""Centralized narrow changed-path scope registry for validation guards."""

from __future__ import annotations

from fnmatch import fnmatchcase


PR168_GFP_BRANCH = "pr168-gfp-global-formula-discovery-real-computation"
PR168_RP_BRANCH = "pr168-rp-formula-based-replay-paper-recompute"
PR168_RANK_BRANCH = "pr168-rank-evidence-backed-ranking"
PR168_DATA1_BRANCH = "pr168-data1-public-market-data-snapshots"
PR168_DATA1A_BRANCH = "pr168-data1a-focused-audit-gfp2r-readiness"
PR168_GFP2R_BRANCH = "pr168-gfp2r-data1a-gated-candidate-recompute"
PR168_RP2_BRANCH = "pr168-rp2-map2-gfp2r-replay-paper-recompute"
PR168_MAP3_BRANCH = "pr168-map3-qku-formula-id-intake"
PR168_RP3_BRANCH = "pr168-rp3-map3-formula-replay-paper-evidence"
PR168_RANK3_BRANCH = "pr168-rank3-rp3-evidence-stack-ranking"
PR168_RP5A_BRANCH = "pr168-rp5a-legacy-semantic-audit"
PR168_RP5B_BRANCH = "pr168-rp5b-active-registry-safe-legacy-cleanup"
PR168_RP5C_BRANCH = "pr168-rp5c-immutable-qku-formula-library"
PR168_RP5C_POST_MERGE_REPAIR_BRANCH = "pr168-rp5c-postmerge-ci-repair"
PR168_VS1_BRANCH = "pr168-vs1-trading-intelligence-vertical-slice"
PR168_RP5D_BRANCH = "pr168-rp5d-replay-paper-executability-tiers"
PR168_RP5E_BRANCH = "pr168-rp5e-stack-gen"
PR168_RP5D_R1_BRANCH = "pr168-rp5d-r1-exec-now-unlock"
PR168_RP5F_BRANCH = "pr168-rp5f-dynamic-target-order-grid"
PR168_RP5G_BRANCH = "pr168-rp5g-trade-plan-sim-engine"
PR168_RANK4_BRANCH = "pr168-rank4-exec-advisory-ranking"
PR168_QOPT1_BRANCH = "pr168-qopt1-quantum-classical-batch-optimization"
PR168_VS2_BRANCH = "pr168-vs2-paper-intent-candidate-generator"
PR168_MEM1_BRANCH = "pr168-mem1-condition-scoped-outcome-memory"
PR169_DASH1_BRANCH = "pr169-dash1-owner-dashboard-interactive-research-v6"
PR169_DASH1_UI1_BRANCH = "pr169-dash1-ui1-theme-switch-safe-renderer-v9"
PR169_DASH1_UI1_R1_BRANCH = "pr169-dash1-ui1-r1-v3-owner12"
PR169_DASH1_UI1_R2_BRANCH = "pr169-dash1-ui1-r2-guided-owner-coach-v7"
PR169_DASH1_UI1_R2_R1_BRANCH = "pr169-dash1-ui1-r2-r1-interaction-v4"
PR169_DASH1_UI1_R2_R2_BRANCH = "pr169-dash1-ui1-r2-r2-owner-product-ux"
PR169_DASH1_UI1_R2_R3_BRANCH = "pr169-dash1-ui1-r2-r3-owner-product-polish"
PR169_DASH1_UI1_R2_R4_BRANCH = "pr169-dash1-ui1-r2-r4-owner-visual-acceptance-agent-monitoring"
PR169_DASH1_UI1_R2_R5_BRANCH = "pr169-dash1-ui1-r2-r5-owner-visual-qa-truth-repair"
PR169_DASH1_UI1_R2_R6_BRANCH = "pr169-ui1-r2r6"
PR169_READINESS1_BRANCH = "pr169-readiness1"
PR169_PRETRADE1_BRANCH = "pr169-pretrade1"
PR169_SVC1_BRANCH = "pr169-svc1"
PR169_AGENT_ORCH1_BRANCH = "pr169-agent-orch1"
PR169_VAL1_BRANCH = "pr169-val1"
PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH = "pr169-qku-formula-exp1-rollback"
VALIDATION_FIXTURE_BRANCH = "pr-ci-fastfail-validation-context-preflight"
ST12A_BRANCH = "agent/st12a-contract-envelope"
ST12B_BRANCH = "agent/st12b-contextual-computability-v3"
ST12C_BRANCH = "agent/st12c-deterministic-receipts-accounting-v1"
ST12E_BRANCH = "agent/st12e-capability-guard"
ST12D_BRANCH = "agent/st12d-mode-snapshot-boundary"
ST12F_BRANCH = "agent/st12f-evidence-model-risk-v1"

_PR168_BRANCHES = frozenset(
    {
        PR168_GFP_BRANCH,
        PR168_RP_BRANCH,
        PR168_RANK_BRANCH,
        PR168_DATA1_BRANCH,
        PR168_DATA1A_BRANCH,
        PR168_GFP2R_BRANCH,
        PR168_RP2_BRANCH,
        PR168_MAP3_BRANCH,
        PR168_RP3_BRANCH,
        PR168_RANK3_BRANCH,
        PR168_RP5A_BRANCH,
        PR168_RP5B_BRANCH,
        PR168_RP5C_BRANCH,
        PR168_RP5C_POST_MERGE_REPAIR_BRANCH,
        PR168_VS1_BRANCH,
        PR168_RP5D_BRANCH,
        PR168_RP5E_BRANCH,
        PR168_RP5D_R1_BRANCH,
        PR168_RP5F_BRANCH,
        PR168_RP5G_BRANCH,
        PR168_RANK4_BRANCH,
        PR168_QOPT1_BRANCH,
        PR168_VS2_BRANCH,
        PR168_MEM1_BRANCH,
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
        PR169_DASH1_UI1_R2_BRANCH,
        PR169_DASH1_UI1_R2_R1_BRANCH,
        PR169_DASH1_UI1_R2_R2_BRANCH,
        PR169_DASH1_UI1_R2_R3_BRANCH,
        PR169_DASH1_UI1_R2_R4_BRANCH,
        PR169_DASH1_UI1_R2_R5_BRANCH,
        PR169_DASH1_UI1_R2_R6_BRANCH,
        PR169_READINESS1_BRANCH,
        PR169_PRETRADE1_BRANCH,
        PR169_SVC1_BRANCH,
        PR169_AGENT_ORCH1_BRANCH,
        PR169_VAL1_BRANCH,
        PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH,
        VALIDATION_FIXTURE_BRANCH,
        ST12A_BRANCH,
    }
)
_VALIDATION_CONTEXT_BRANCHES = frozenset({VALIDATION_FIXTURE_BRANCH})

ST12A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dependency_graph.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/identity_adapter.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/plugin_adapter.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_canonical_owner_uniqueness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_consume_not_rebuild.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_contextual_computability.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_contract_envelope_completeness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_control_plane_boundary.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_cross_platform_paths.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_current_repository_reconciliation.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_dependency_graph_soundness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_generated_artifact_ownership.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_identity_plane_binding.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_mode_evidence_orthogonality.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_no_orphan_consumers.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_operation_contract_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_route_not_runtime.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_schema_cross_consistency.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_snapshot_boundary.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_step12_tranche_readiness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_tranche_dag_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_transaction_boundary.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_configuration_control.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_health_readiness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_lifecycle_supervision.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_runtime_topology.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_constraint_mapping.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_consume_existing_mapper.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_model_semantics.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_objective_sense_and_scale.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_problem_shape_classification.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_variable_encoding.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_authentication_binding.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_authorization_least_privilege.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_default_deny_capabilities.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_deserialization_safety.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_input_validation.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_secret_isolation.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/test_threat_model_completeness.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/source/test_all_29_revalidated.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/source/test_conflict_resolution.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/source/test_effective_epoch.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/source/test_fact_atomicity.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/source/test_source_precedence.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/build_qku_computation_control_plane.py",
        "tools/changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/independent_validate_qku_computation_control_plane.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/independent_validate_qku_computation_control_plane_operations.py",
        "tools/independent_validate_qku_computation_control_plane_quantum.py",
        "tools/independent_validate_qku_computation_control_plane_security.py",
        "tools/independent_validate_qku_computation_control_plane_source.py",
        "tools/run_validation_gates.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    }
)
ST12A_SHARED_CURRENTIZATION_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR168_RP5A_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5A_NoDeletionProof.report.json",
        "tests/pr168_rp5a/test_no_validation_scope_removal.py",
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/pr168_rp5a_validator.py",
    }
)
ST12B_ALLOWED_EXACT_PATHS = frozenset(
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
ST12B_VALIDATION_CONTEXT_EXACT_PATHS = frozenset(
    ST12B_ALLOWED_EXACT_PATHS
    - (
        ST12A_ALLOWED_EXACT_PATHS
        | ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
    )
)

ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS = frozenset(
    {
        "tests/atomicrows/test_source_backed_classical_quantum_parameter_default_target_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_runtime_topology.py",
        "tools/independent_validate_qku_computation_control_plane_operations.py",
    }
)
ST12C_ALLOWED_EXACT_PATHS = frozenset(
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
) | ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
ST12C_VALIDATION_CONTEXT_EXACT_PATHS = frozenset(
    ST12C_ALLOWED_EXACT_PATHS
    - (
        ST12A_ALLOWED_EXACT_PATHS
        | ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
        | ST12B_ALLOWED_EXACT_PATHS
        | ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
    )
)

ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS = frozenset(
    {
        "tests/stage1_prediction_markets/"
        "qku_computation_control_plane/"
        "tranche_b/test_service_operations.py",
    }
)
ST12E_ALLOWED_EXACT_PATHS = frozenset(
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
) | ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
ST12E_VALIDATION_CONTEXT_EXACT_PATHS = frozenset(
    ST12E_ALLOWED_EXACT_PATHS
    - (
        ST12A_ALLOWED_EXACT_PATHS
        | ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
        | ST12B_ALLOWED_EXACT_PATHS
        | ST12C_ALLOWED_EXACT_PATHS
        | ST12E_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
    )
)

ST12D_ALLOWED_EXACT_PATHS = frozenset(
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
ST12D_VALIDATION_CONTEXT_EXACT_PATHS = frozenset(
    ST12D_ALLOWED_EXACT_PATHS
    - (
        ST12A_ALLOWED_EXACT_PATHS
        | ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
        | ST12B_ALLOWED_EXACT_PATHS
        | ST12C_ALLOWED_EXACT_PATHS
        | ST12E_ALLOWED_EXACT_PATHS
    )
)

_ST12F_RESOURCE_NAMES = (
    "st12f_parameter_resources_manifest.json",
    "st12f_parameter_rows_0001_0320.jsonl",
    "st12f_parameter_rows_0321_0640.jsonl",
    "st12f_parameter_rows_0641_0960.jsonl",
    "st12f_parameter_rows_0961_1280.jsonl",
    "st12f_parameter_rows_1281_1600.jsonl",
    "st12f_parameter_rows_1601_1920.jsonl",
    "st12f_parameter_rows_1921_2240.jsonl",
    "st12f_parameter_rows_2241_2560.jsonl",
    "st12f_parameter_rows_2561_2880.jsonl",
    "st12f_parameter_rows_2881_3200.jsonl",
    "st12f_parameter_rows_3201_3520.jsonl",
    "st12f_parameter_rows_3521_3840.jsonl",
)
_ST12F_PROJECTION_NAMES = (
    "cohort_registry.jsonl",
    "evidence_bundle_registry.jsonl",
    "evidence_metric_registry.jsonl",
    "independent_review_contracts.jsonl",
    "llm_annotation_contracts.jsonl",
    "manifest.json",
    "model_risk_adjudications.jsonl",
    "no_trade_comparisons.jsonl",
    "paper_result_contracts.jsonl",
    "parent_input_locks.jsonl",
    "quantum_benchmark_contracts.jsonl",
    "replay_result_contracts.jsonl",
    "validation_summary.json",
)
ST12F_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(f"src/qtt/stage1_prediction_markets/qku_computation_control_plane/data/{name}" for name in _ST12F_RESOURCE_NAMES),
        *(f"docs/master_plan/generated/qku_control_plane/evidence/{name}" for name in _ST12F_PROJECTION_NAMES),
        "src/qtt/core/testing/gate_result.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/cohort_compiler.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_lock.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/llm_gateway.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
        "tests/core/test_qtt_cumulative_gate.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_repository_file_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_mode_evidence_orthogonality.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/test_policy_state_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operations.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_adversarial_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_integration_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_f/test_model_risk_llm_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_f/test_quantum_benchmark_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_f/test_replay_paper_evidence_matrix.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/build_qku_computation_control_plane.py",
        "tools/changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tools/independent_validate_qku_computation_control_plane.py",
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/independent_validate_qku_computation_control_plane_d.py",
        "tools/independent_validate_qku_computation_control_plane_execution.py",
        "tools/independent_validate_qku_computation_control_plane_llm.py",
        "tools/independent_validate_qku_computation_control_plane_model_risk.py",
        "tools/independent_validate_qku_computation_control_plane_operations.py",
        "tools/independent_validate_qku_computation_control_plane_quantum.py",
        "tools/independent_validate_qku_computation_control_plane_security.py",
        "tools/independent_validate_qku_computation_control_plane_source.py",
        "tools/run_validation_gates.py",
        "tools/validate_qku_computation_control_plane.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    }
)
if len(ST12F_ALLOWED_EXACT_PATHS) != 82:
    raise RuntimeError("ST12-F exact current-main scope must contain 82 paths")

_PR168_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py",
        "src/qtt/stage1_prediction_markets/qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
        "tools/ci_branch_context.py",
        "tools/validate_idempotence_runtime_containment.py",
    }
)

_PR168_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP_*.report.json",
    "docs/master_plan/generated/pr168_gfp_shards/PR168_GFP_*.json",
    "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/**",
    "tests/pr168_gfp/**",
    "tools/validate_pr168_gfp_*.py",
)

_PR168_RP_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/build_pr168_rp_formula_based_replay_paper_recompute.py",
        "tools/run_validation_gates.py",
    }
)

_PR168_RP_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP_*.report.json",
    "docs/master_plan/generated/pr168_rp_shards/PR168_RP_*.report.json",
    "tools/pr168_rp_*.py",
    "tools/validate_pr168_rp_*.py",
    "tests/pr168_rp/**",
)

_PR168_RANK_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "tools/build_pr168_rank_evidence_backed_ranking.py",
    }
)

_PR168_RANK_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK_*.report.json",
    "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_*.report.json",
    "tools/pr168_rank_*.py",
    "tools/validate_pr168_rank_*.py",
    "tests/pr168_rank/**",
)

_PR168_DATA1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1_public_market_data_snapshots.py",
        "tools/validate_pr168_data1_public_market_data_snapshots.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
    }
)

_PR168_DATA1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1_*.report.json",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.manifest.json",
    "tools/pr168_data1_*.py",
    "tests/pr168_data1/**",
)

_PR168_DATA1A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1a_focused_audit.py",
        "tools/validate_pr168_data1a_focused_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_DATA1A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1A_*.report.json",
    "docs/master_plan/generated/pr168_data1a_audit/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/*.manifest.json",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.manifest.json",
    "tools/pr168_data1a_*.py",
    "tests/pr168_data1a/**",
)

_PR168_GFP2R_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_GFP2R_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP2R_*.report.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.manifest.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.manifest.json",
    "tools/pr168_gfp2r_*.py",
    "tests/pr168_gfp2r/**",
)

_PR168_RP2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp2_map2.py",
        "tools/validate_pr168_rp2_map2.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP2_*.report.json",
    "docs/master_plan/generated/rp2p/*.jsonl",
    "docs/master_plan/generated/rp2p/*.manifest.json",
    "docs/master_plan/generated/rp2p/**/*.jsonl",
    "docs/master_plan/generated/rp2p/**/*.manifest.json",
    "tools/pr168_rp2_*.py",
    "tests/pr168_rp2/**",
)

_PR168_MAP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_map3.py",
        "tools/validate_pr168_map3.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_MAP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_MAP3_*.report.json",
    "docs/master_plan/generated/map3/*.jsonl",
    "docs/master_plan/generated/map3/*.manifest.json",
    "docs/master_plan/generated/map3/**/*.jsonl",
    "docs/master_plan/generated/map3/**/*.manifest.json",
    "tools/pr168_map3_*.py",
    "tests/pr168_map3/**",
)

_PR168_RP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp3.py",
        "tools/validate_pr168_rp3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP3_*.report.json",
    "docs/master_plan/generated/rp3/*.jsonl",
    "docs/master_plan/generated/rp3/*.manifest.json",
    "docs/master_plan/generated/rp3/**/*.jsonl",
    "docs/master_plan/generated/rp3/**/*.manifest.json",
    "tools/pr168_rp3_*.py",
    "tests/pr168_rp3/**",
)

_PR168_RANK3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rank3.py",
        "tools/validate_pr168_rank3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK3_*.report.json",
    "docs/master_plan/generated/rank3/*.jsonl",
    "docs/master_plan/generated/rank3/*.manifest.json",
    "docs/master_plan/generated/rank3/**/*.jsonl",
    "docs/master_plan/generated/rank3/**/*.manifest.json",
    "tools/pr168_rank3_*.py",
    "tests/pr168_rank3/**",
)

_PR168_RP5A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5A_*.report.json",
    "docs/master_plan/generated/rp5a/*.jsonl",
    "docs/master_plan/generated/rp5a/*.manifest.json",
    "docs/master_plan/generated/rp5a/**/*.jsonl",
    "docs/master_plan/generated/rp5a/**/*.manifest.json",
    "tools/pr168_rp5a_*.py",
    "tests/pr168_rp5a/**",
)

_PR168_RP5B_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5B_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5B_*.report.json",
    "docs/master_plan/generated/rp5b/*.jsonl",
    "docs/master_plan/generated/rp5b/*.manifest.json",
    "docs/master_plan/generated/rp5b/**/*.jsonl",
    "docs/master_plan/generated/rp5b/**/*.manifest.json",
    "tools/pr168_rp5b_*.py",
    "tests/pr168_rp5b/**",
)

_PR168_RP5C_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/validate_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5C_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5C_*.report.json",
    "docs/master_plan/generated/rp5c/*.jsonl",
    "docs/master_plan/generated/rp5c/*.manifest.json",
    "docs/master_plan/generated/rp5c/**/*.jsonl",
    "docs/master_plan/generated/rp5c/**/*.manifest.json",
    "tools/pr168_rp5c_*.py",
    "tests/pr168_rp5c/**",
)

_PR168_VS1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/run_pr168_vs1_trading_intelligence_slice.py",
        "tools/validate_pr168_vs1_trading_intelligence_slice.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_VS1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs1/*.jsonl",
    "docs/master_plan/generated/pr168_vs1/*.manifest.json",
    "docs/master_plan/generated/pr168_vs1/*.report.json",
    "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/**",
    "tools/pr168_vs1_*.py",
    "tools/*pr168_vs1*.py",
    "tests/pr168_vs1/**",
)

_PR168_RP5D_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d/*.report.json",
    "docs/master_plan/generated/pr168_rp5d/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/**",
    "tools/*pr168_rp5d*.py",
    "tests/pr168_rp5d/**",
)

_PR168_RP5E_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5e_stack_gen.py",
        "tools/validate_pr168_rp5e_stack_gen.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
    }
)

_PR168_RP5E_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5e/*.jsonl",
    "docs/master_plan/generated/pr168_rp5e/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5e/*.report.json",
    "docs/master_plan/generated/pr168_rp5e/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/**",
    "tools/*pr168_rp5e*.py",
    "tests/pr168_rp5e/**",
)

_PR168_RP5D_R1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/validate_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_R1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d_r1/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/**",
    "tools/*pr168_rp5d_r1*.py",
    "tests/pr168_rp5d_r1/**",
)

_PR168_RP5F_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5f_dynamic_targets.py",
        "tools/validate_pr168_rp5f_dynamic_targets.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    }
)

_PR168_RP5F_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5f/*.jsonl",
    "docs/master_plan/generated/pr168_rp5f/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5f/*.report.json",
    "docs/master_plan/generated/pr168_rp5f/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/**",
    "tools/*pr168_rp5f*.py",
    "tests/pr168_rp5f/**",
)

_PR168_RP5G_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5g_trade_plan_sim.py",
        "tools/validate_pr168_rp5g_trade_plan_sim.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP5G_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5g/*.jsonl",
    "docs/master_plan/generated/pr168_rp5g/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5g/*.report.json",
    "docs/master_plan/generated/pr168_rp5g/*.json",
    "docs/master_plan/generated/pr168_rp5g/*.md",
    "src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/**",
    "tools/*pr168_rp5g*.py",
    "tests/pr168_rp5g/**",
)

_PR168_RANK4_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/ranking/__init__.py",
        "tools/build_pr168_rank4_advisory_ranking.py",
        "tools/validate_pr168_rank4_advisory_ranking.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK4_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rank4/*.jsonl",
    "docs/master_plan/generated/pr168_rank4/*.manifest.json",
    "docs/master_plan/generated/pr168_rank4/*.report.json",
    "docs/master_plan/generated/pr168_rank4/*.json",
    "docs/master_plan/generated/pr168_rank4/*.md",
    "src/qtt/ranking/pr168_rank4/**",
    "tools/*pr168_rank4*.py",
    "tests/pr168_rank4/**",
)

_PR168_QOPT1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/optimization/__init__.py",
        "tools/build_pr168_qopt1_batch_optimization.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_qopt1_batch_optimization.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_QOPT1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_qopt1/*.jsonl",
    "docs/master_plan/generated/pr168_qopt1/*.manifest.json",
    "docs/master_plan/generated/pr168_qopt1/*.report.json",
    "docs/master_plan/generated/pr168_qopt1/*.json",
    "docs/master_plan/generated/pr168_qopt1/*.md",
    "src/qtt/optimization/pr168_qopt1/**",
    "tools/*pr168_qopt1*.py",
    "tests/pr168_qopt1/**",
)

_PR168_VS2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/paper/__init__.py",
        "tools/build_pr168_vs2_paper_intent_candidates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_vs2_paper_intent_candidates.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_VS2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs2/*.jsonl",
    "docs/master_plan/generated/pr168_vs2/*.manifest.json",
    "docs/master_plan/generated/pr168_vs2/*.report.json",
    "docs/master_plan/generated/pr168_vs2/*.json",
    "docs/master_plan/generated/pr168_vs2/*.md",
    "src/qtt/paper/pr168_vs2/**",
    "tools/*pr168_vs2*.py",
    "tests/pr168_vs2/**",
)

_PR168_MEM1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/memory/__init__.py",
        "tools/build_pr168_mem1_condition_scoped_memory.py",
        "tools/query_pr168_mem1_memory.py",
        "tools/validate_pr168_mem1_condition_scoped_memory.py",
        "tools/run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_MEM1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_mem1/*.jsonl",
    "docs/master_plan/generated/pr168_mem1/*.manifest.json",
    "docs/master_plan/generated/pr168_mem1/*.report.json",
    "docs/master_plan/generated/pr168_mem1/*.json",
    "docs/master_plan/generated/pr168_mem1/*.md",
    "src/qtt/memory/pr168_mem1/**",
    "tools/*pr168_mem1*.py",
    "tests/pr168_mem1/**",
)

_PR169_DASH1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/dashboard/__init__.py",
        "src/qtt/dashboard/owner_surface_models.py",
        "src/qtt/dashboard/owner_surface_registry.py",
        "src/qtt/dashboard/owner_surface_resolver.py",
        "src/qtt/dashboard/owner_action_registry.py",
        "src/qtt/dashboard/owner_dashboard_packet_builder.py",
        "src/qtt/dashboard/owner_dashboard_projection_builder.py",
        "src/qtt/dashboard/owner_dashboard_validator.py",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/build_pr169_dash1_owner_dashboard.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_dash1_owner_dashboard.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_source_fact_binding_connector_semantic_readiness_static.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "tests/source_evidence/test_source_fact_binding_connector_semantic_readiness_static.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_DASH1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_dash1/**",
    "src/qtt/dashboard/**",
    "tools/*pr169_dash1*.py",
    "tests/pr169_dash1/**",
    "tests/pr169_dash1_ui1/**",
)

_PR169_READINESS1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/readiness/__init__.py",
        "src/qtt/readiness/pr169_readiness1_resolvers.py",
        "tools/build_pr169_readiness1.py",
        "tools/validate_pr169_readiness1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_readiness1/test_pr169_readiness1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_READINESS1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_readiness1/**",
    "src/qtt/readiness/**",
    "tools/*pr169_readiness1*.py",
    "tests/pr169_readiness1/**",
)

_PR169_PRETRADE1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/pretrade/__init__.py",
        "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "tools/build_pr169_pretrade1.py",
        "tools/validate_pr169_pretrade1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_pretrade1/test_pr169_pretrade1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_PRETRADE1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_pretrade1/**",
    "src/qtt/pretrade/**",
    "tools/*pr169_pretrade1*.py",
    "tests/pr169_pretrade1/**",
)

_PR169_SVC1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/service/__init__.py",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/build_pr169_svc1.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_svc1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_svc1/test_pr169_svc1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_SVC1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_svc1/**",
    "src/qtt/service/**",
    "tools/*pr169_svc1*.py",
    "tests/pr169_svc1/**",
)

_PR169_AGENT_ORCH1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/agents/__init__.py",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "tools/build_pr169_agent_orch1.py",
        "tools/validate_pr169_agent_orch1.py",
        "tools/pr168_rp5c_config.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_agent_orch1/__init__.py",
        "tests/pr169_agent_orch1/conftest.py",
        "tests/pr169_agent_orch1/test_registry_projection_integrity.py",
        "tests/pr169_agent_orch1/test_dag_task_receipts.py",
        "tests/pr169_agent_orch1/test_no_authority.py",
        "tests/pr169_agent_orch1/test_qku_formula_mem_routes.py",
        "tests/pr169_agent_orch1/test_no_orphan_raw_scan.py",
        "tests/pr169_agent_orch1/test_resolvers.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_AGENT_ORCH1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_agent_orch1/**",
    "src/qtt/agents/**",
    "tools/*pr169_agent_orch1*.py",
    "tests/pr169_agent_orch1/**",
)

_PR169_VAL1_ALLOWED_EXACT_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr169_val1/acceptance.report.json",
        "docs/master_plan/generated/pr169_val1/manifest.json",
        "docs/master_plan/generated/pr169_val1/parity.report.json",
        "docs/master_plan/generated/pr169_val1/readability.report.json",
        "docs/master_plan/generated/pr169_val1/shards.report.json",
        "docs/master_plan/generated/pr169_val1/timing.report.json",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_qtt_validation_workflow_matrix.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_readability_guard.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_shard_partition.py",
        "tests/tools/test_validation_timing_artifacts.py",
        "tools/build_pr169_val1.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tools/validate_pr169_val1.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    }
)

_PR169_VAL1_ALLOWED_PATTERNS: tuple[str, ...] = ()

_PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_EXACT_PATHS = frozenset(
    {
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
        "tests/pr168_rp5b/test_deleted_manifest_matches_git_deletions.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "tests/pr169_qku_formula_exp1/__init__.py",
        "tests/pr169_qku_formula_exp1/test_contracts.py",
        "tests/pr169_qku_formula_exp1/test_family_j.py",
        "tests/pr169_qku_formula_exp1/test_runtime.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/build_pr169_qku_formula_exp1.py",
        "tools/pr168_rp5b_validator.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validate_pr169_qku_formula_exp1.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    }
)

_PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATTERNS: tuple[str, ...] = ()

_FORBIDDEN_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "AtomicRows.bundle.sha256",
        "docs/master_plan/generated/AtomicRows.bundle.sha256",
    }
)

_FORBIDDEN_PREFIXES = (
    ".tmp/",
    "src/qtt/live_connectors/",
    "src/qtt/connectors/live/",
    "src/qtt/private_state/",
    "src/qtt/live_order",
    "private-state/",
    "private_state/",
    "cash/",
    "secrets/",
)

_FORBIDDEN_NAME_TOKENS = (
    "live_order",
    "private_state",
    "private-state",
    "cash_account",
    "account_cash",
    "secret",
    "atomicrows.bundle.sha256",
    "qtt_sha",
    "qtt-sha",
    "qtt_freeze",
    "qtt-freeze",
    "qtt_checksum",
    "qtt-checksum",
    "qtt_global_digest",
    "qtt-global-digest",
)

_FORBIDDEN_TOKEN_EXACT_PROOF_REPORT_EXCEPTIONS = frozenset(
    {
        "docs/master_plan/generated/pr169_agent_orch1/no_qtt_sha.report.json",
    }
)


def normalize_changed_path(path: str) -> str:
    """Normalize a changed path into repo-relative POSIX form."""
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_validation_context_branch(branch: str) -> bool:
    return str(branch).strip() in _VALIDATION_CONTEXT_BRANCHES


def is_pr_scoped_changed_path_allowed(branch: str, path: str) -> bool:
    return bool(explain_pr_scope_decision(branch, path)["allowed"])


def _pr168_rp_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_gfp2r_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_GFP2R_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_GFP2R_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP2R",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_map3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MAP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MAP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MAP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5b_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5B_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5B_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5B",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5c_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5C_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5C_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5C",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5e_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5E_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5E_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5E",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_r1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_R1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_R1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D-R1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5f_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5F_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5F_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5F",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5g_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5G_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5G_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5G",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank4_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK4_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK4_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK4",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_qopt1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_QOPT1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_QOPT1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-QOPT1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_mem1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MEM1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MEM1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MEM1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_readiness1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_READINESS1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-READINESS1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_READINESS1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-READINESS1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_pretrade1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_PRETRADE1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-PRETRADE1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_PRETRADE1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-PRETRADE1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_svc1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_SVC1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-SVC1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_SVC1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-SVC1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_agent_orch1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_AGENT_ORCH1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-AGENT-ORCH1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_AGENT_ORCH1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-AGENT-ORCH1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_val1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_VAL1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-VAL1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_VAL1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-VAL1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_qku_formula_exp1_rollback_scope_decision(
    branch_name: str,
    normalized: str,
) -> dict[str, object] | None:
    if normalized in _PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-QKU-FORMULA-EXP1-ROLLBACK",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_QKU_FORMULA_EXP1_ROLLBACK_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-QKU-FORMULA-EXP1-ROLLBACK",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_dash1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_DASH1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_DASH1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-DASH1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def explain_pr_scope_decision(branch: str, path: str) -> dict[str, object]:
    normalized = normalize_changed_path(path)
    branch_name = str(branch).strip()
    if branch_name == ST12F_BRANCH and normalized in ST12F_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-F",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if branch_name == ST12D_BRANCH and normalized in ST12D_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-D",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if branch_name == ST12E_BRANCH and normalized in ST12E_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-E",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if branch_name == ST12C_BRANCH and normalized in ST12C_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-C",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if branch_name == ST12B_BRANCH and normalized in ST12B_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-B",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if branch_name == ST12A_BRANCH and normalized in ST12A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    if (
        branch_name == ST12A_BRANCH
        and normalized in ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"shared_currentization_exact:{normalized}",
            "reason": "registered_shared_currentization_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12A_ALLOWED_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": f"validation_context_shared_currentization_exact:{normalized}",
            "reason": "registered_validation_context_shared_currentization_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized.endswith(".copy")
        and normalized.removesuffix(".copy")
        in ST12A_SHARED_CURRENTIZATION_EXACT_PATHS
    ):
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": "no_shared_currentization_exact_near_name",
            "reason": "path_not_registered_for_pr_scope",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12B_VALIDATION_CONTEXT_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-B",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12C_PREDECESSOR_CURRENTIZATION_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-C",
            "matched_rule": (
                f"validation_context_predecessor_currentization_exact:{normalized}"
            ),
            "reason": (
                "registered_validation_context_"
                "predecessor_currentization_exact_path"
            ),
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12C_VALIDATION_CONTEXT_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-C",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12E_VALIDATION_CONTEXT_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-E",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12D_VALIDATION_CONTEXT_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-D",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    if (
        is_validation_context_branch(branch_name)
        and normalized in ST12F_ALLOWED_EXACT_PATHS
    ):
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-F",
            "matched_rule": f"validation_context_exact:{normalized}",
            "reason": "registered_validation_context_exact_path",
        }
    forbidden_reason = _forbidden_reason(normalized)
    if forbidden_reason:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": forbidden_reason,
            "reason": "forbidden_path",
        }
    if branch_name == ST12A_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-A",
            "matched_rule": "no_st12a_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name == ST12B_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-B",
            "matched_rule": "no_st12b_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name == ST12C_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-C",
            "matched_rule": "no_st12c_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name == ST12E_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-E",
            "matched_rule": "no_st12e_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name == ST12F_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-F",
            "matched_rule": "no_st12f_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name == ST12D_BRANCH:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "ST12-TRANCHE-D",
            "matched_rule": "no_st12d_exact_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }
    if branch_name not in _PR168_BRANCHES:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": "branch_not_registered_for_pr_scope",
            "reason": "branch_not_registered",
        }
    if branch_name == PR168_RP_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": "no_pr168_rp_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK_BRANCH:
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": "no_pr168_rank_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1_BRANCH:
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": "no_pr168_data1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1A_BRANCH:
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": "no_pr168_data1a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_GFP2R_BRANCH:
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": "no_pr168_gfp2r_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP2_BRANCH:
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": "no_pr168_rp2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MAP3_BRANCH:
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": "no_pr168_map3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP3_BRANCH:
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": "no_pr168_rp3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK3_BRANCH:
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": "no_pr168_rank3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5A_BRANCH:
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": "no_pr168_rp5a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5B_BRANCH:
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": "no_pr168_rp5b_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {PR168_RP5C_BRANCH, PR168_RP5C_POST_MERGE_REPAIR_BRANCH}:
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": "no_pr168_rp5c_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS1_BRANCH:
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": "no_pr168_vs1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_BRANCH:
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": "no_pr168_rp5d_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5E_BRANCH:
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": "no_pr168_rp5e_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_R1_BRANCH:
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": "no_pr168_rp5d_r1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5F_BRANCH:
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": "no_pr168_rp5f_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5G_BRANCH:
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": "no_pr168_rp5g_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK4_BRANCH:
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": "no_pr168_rank4_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_QOPT1_BRANCH:
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": "no_pr168_qopt1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS2_BRANCH:
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": "no_pr168_vs2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MEM1_BRANCH:
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": "no_pr168_mem1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_READINESS1_BRANCH:
        readiness1_decision = _pr169_readiness1_scope_decision(branch_name, normalized)
        if readiness1_decision:
            return readiness1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-READINESS1",
            "matched_rule": "no_pr169_readiness1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_PRETRADE1_BRANCH:
        pretrade1_decision = _pr169_pretrade1_scope_decision(branch_name, normalized)
        if pretrade1_decision:
            return pretrade1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-PRETRADE1",
            "matched_rule": "no_pr169_pretrade1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_SVC1_BRANCH:
        svc1_decision = _pr169_svc1_scope_decision(branch_name, normalized)
        if svc1_decision:
            return svc1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-SVC1",
            "matched_rule": "no_pr169_svc1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_AGENT_ORCH1_BRANCH:
        agent_orch1_decision = _pr169_agent_orch1_scope_decision(branch_name, normalized)
        if agent_orch1_decision:
            return agent_orch1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-AGENT-ORCH1",
            "matched_rule": "no_pr169_agent_orch1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_VAL1_BRANCH:
        val1_decision = _pr169_val1_scope_decision(branch_name, normalized)
        if val1_decision:
            return val1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-VAL1",
            "matched_rule": "no_pr169_val1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_QKU_FORMULA_EXP1_ROLLBACK_BRANCH:
        rollback_decision = _pr169_qku_formula_exp1_rollback_scope_decision(
            branch_name,
            normalized,
        )
        if rollback_decision:
            return rollback_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-QKU-FORMULA-EXP1-ROLLBACK",
            "matched_rule": "no_pr169_qku_formula_exp1_rollback_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
        PR169_DASH1_UI1_R2_BRANCH,
        PR169_DASH1_UI1_R2_R1_BRANCH,
        PR169_DASH1_UI1_R2_R2_BRANCH,
        PR169_DASH1_UI1_R2_R3_BRANCH,
        PR169_DASH1_UI1_R2_R4_BRANCH,
        PR169_DASH1_UI1_R2_R5_BRANCH,
        PR169_DASH1_UI1_R2_R6_BRANCH,
    }:
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": "no_pr169_dash1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == VALIDATION_FIXTURE_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        readiness1_decision = _pr169_readiness1_scope_decision(branch_name, normalized)
        if readiness1_decision:
            return readiness1_decision
        pretrade1_decision = _pr169_pretrade1_scope_decision(branch_name, normalized)
        if pretrade1_decision:
            return pretrade1_decision
        svc1_decision = _pr169_svc1_scope_decision(branch_name, normalized)
        if svc1_decision:
            return svc1_decision
        agent_orch1_decision = _pr169_agent_orch1_scope_decision(branch_name, normalized)
        if agent_orch1_decision:
            return agent_orch1_decision
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision

    if normalized in _PR168_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return {
        "allowed": False,
        "branch": branch_name,
        "normalized_path": normalized,
        "pr_id": "PR168-GFP",
        "matched_rule": "no_pr168_scope_rule",
        "reason": "path_not_registered_for_pr_scope",
    }


def _forbidden_reason(normalized: str) -> str | None:
    lowered = normalized.lower()
    if lowered in _FORBIDDEN_TOKEN_EXACT_PROOF_REPORT_EXCEPTIONS:
        return None
    if lowered.startswith("docs/master_plan/generated/pr168_vs2/no_private_state.") or lowered in {
        "docs/master_plan/generated/pr168_vs2/no_private_state.jsonl",
        "docs/master_plan/generated/pr168_vs2/no_private_state.manifest.json",
    }:
        return None
    if normalized in _FORBIDDEN_EXACT_PATHS:
        return f"forbidden_exact:{normalized}"
    if lowered.endswith("/atomicrows.bundle.sha256") or lowered == "atomicrows.bundle.sha256":
        return "forbidden_atomicrows_bundle_sha"
    for prefix in _FORBIDDEN_PREFIXES:
        if lowered.startswith(prefix):
            return f"forbidden_prefix:{prefix}"
    for token in _FORBIDDEN_NAME_TOKENS:
        if token in lowered:
            if (
                token == "live_order"
                and lowered.startswith("tests/")
                and "/test_no_live_order" in lowered
            ):
                continue
            if (
                token in {"qtt_sha", "qtt-sha"}
                and lowered.startswith("tests/pr169_dash1/")
                and "/test_dash1_no_qtt_sha" in lowered
            ):
                continue
            return f"forbidden_token:{token}"
    return None
