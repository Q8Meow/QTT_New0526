"""Central constants for the PR143 owner global override currentization."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR143"
BRANCH = "pr143-qtt-owner-global-override-directive-currentization-internal-gate-release"
ARTIFACT_STEM = "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease"
PACKAGE_NAME = "qtt_owner_global_override_directive_currentization_and_internal_gate_release"
REPORT_TYPE = "QTT_OWNER_GLOBAL_OVERRIDE_DIRECTIVE_CURRENTIZATION_AND_INTERNAL_GATE_RELEASE_REPORT"
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_QTT_OWNER_GLOBAL_OVERRIDE_DIRECTIVE_CURRENTIZATION_INTERNAL_GATE_RELEASE_"
    "ONLY_NOT_EXTERNAL_FACT_AUTHORITY_NOT_MATERIALIZATION_NOT_RUNTIME_NOT_QUANTUM_EXECUTION"
)
AUTHORITY_CLASS_VALUES = (AUTHORITY_CLASS,)
SUCCESS_MARKER = "QTT_OWNER_GLOBAL_OVERRIDE_DIRECTIVE_CURRENTIZATION_AND_INTERNAL_GATE_RELEASE_OK"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
MAIN_PREFLIGHT_HEAD_SHORT_SHA_AS_VCS_METADATA_ONLY = "4f2bf35"
GITHUB_MAIN_VALIDATION_STATUS = "SUCCESS"
GITHUB_STATUS_CLAIMED = True

YAML_PATH = Path(
    "docs/master_plan/governance/"
    "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.yaml"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.report.json"
)
SCHEMA_PATH = Path(
    "schemas/governance/"
    "qtt_owner_global_override_directive_currentization_and_internal_gate_release.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/governance/"
    "synthetic_qtt_owner_global_override_directive_currentization_and_internal_gate_release.v1.fixture.json"
)

MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ROW_FAMILY_SOURCE_DIRECTORY = Path("docs/master_plan/atomic_rows/pr98_row_family_sources")

CROSSWALK_REQUESTED_ALIAS = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
CROSSWALK_CANONICAL = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)

PR142_YAML_PATH = Path(
    "docs/master_plan/atomic_rows/"
    "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.yaml"
)
PR142_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.report.json"
)
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)

OWNER_GLOBAL_OVERRIDE_AUTHORITY_TOOL_PATH = Path(
    "tools/validate_qtt_owner_global_override_authority.py"
)
OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH = Path(
    "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json"
)
EXISTING_OWNER_OVERRIDE_AUTHORITY_EVIDENCE_PATHS = (
    OWNER_GLOBAL_OVERRIDE_AUTHORITY_TOOL_PATH,
    OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH,
)

CONTROL_PLANE_EVIDENCE_PATHS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json"),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap.py"
    ),
)

PR136_EVIDENCE_PATHS = (
    Path("docs/master_plan/generated/PR136RouteTriage.report.json"),
    Path("docs/master_plan/generated/PR136ReadReceipt.report.json"),
    Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    CROSSWALK_CANONICAL,
    Path("docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json"),
    Path("docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json"),
    Path("docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json"),
    Path("docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"),
    Path("docs/master_plan/generated/PR136FuturePRCardRegistry.report.json"),
    Path("docs/master_plan/generated/PR136RoadmapReplacementAndInsertionMatrix.report.json"),
    Path("docs/master_plan/generated/PR136Day1LaunchReadinessRoadmap.report.json"),
    Path("docs/master_plan/generated/PR136PolicyManifest.report.json"),
    Path("docs/master_plan/generated/PR136PolicyLiteralDrift.report.json"),
    Path("docs/master_plan/generated/PR136ValidationGateIntegration.report.json"),
)

ATOMICROWS_EVIDENCE_PATHS = (
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.index.json"),
    Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.report.json"),
    Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.index.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json"),
    Path("docs/master_plan/generated/AtomicRowsRowFamilySourceManifestCurrentization.report.json"),
    Path("docs/master_plan/generated/AtomicRowsSemanticFieldCoverageEnrichmentPlan.report.json"),
    Path("docs/master_plan/atomic_rows/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.yaml"),
    Path("docs/master_plan/generated/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.report.json"),
)

PR142_EVIDENCE_PATHS = (
    PR142_YAML_PATH,
    PR142_REPORT_PATH,
)

VALIDATION_CONTEXT_EVIDENCE_PATHS = (
    Path("tools/ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context_invariants.py"),
    Path("tools/run_validation_gates.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
)

OWNER_GLOBAL_OVERRIDE_CANONICAL_NORMALIZED_TEXT = (
    "OWNER_APPROVES_AND_OVERRIDES_ALL_QTT_INTERNAL_GATES_BLOCKS_RULES_PERMISSIONS_NOW"
)

RELEASED_INTERNAL_GATE_CLASSES = (
    "OWNER_APPROVAL",
    "OWNER_APPROVAL_RECEIPT",
    "OWNER_PERMISSION",
    "OWNER_ACTION_REQUIRED",
    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_IMPLEMENTATION",
    "OWNER_PERMISSION_REQUIRED_FOR_INTERNAL_GATE_TRANSITION",
    "OWNER_PERMISSION_REQUIRED_FOR_QUANTUM_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_QUANTUM_OPTIMIZATION_ARCHITECTURE",
    "OWNER_PERMISSION_REQUIRED_FOR_TRUE_QUANTUM_BACKEND_INTEGRATION_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_OPTIMIZER_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_ATOMICROWS_INTERNAL_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_AGENT_ORCHESTRATION_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_DASHBOARD_OR_APPROVAL_UX_PLANNING",
)

OWNER_GATE_CODES_RELEASED_BY_PR143 = (
    "MISSING_OWNER_APPROVAL",
    "MISSING_OWNER_APPROVAL_RECEIPT",
    "MISSING_MATERIALIZATION_PERMISSION",
)

NON_OWNER_EVIDENCE_CLASSES_PRESERVED = (
    "ACCEPTED_SOURCE_EVIDENCE",
    "CONNECTOR_SEMANTIC_BINDING",
    "RUNTIME_CASH_RECEIPT",
    "ORDER_RECEIPT",
    "FILL_RECEIPT",
    "REPLAY_RESULT",
    "PAPER_RESULT",
    "OPTIMIZER_RESULT",
    "QUANTUM_BACKEND_RESULT",
    "QUANTUM_SIMULATOR_RESULT",
    "LIVE_EXECUTION_EVIDENCE",
    "PROFIT_EVIDENCE",
)

NON_OWNER_EVIDENCE_STATE_LABEL = "PENDING_EVIDENCE_OR_RUNTIME_RECEIPT_NOT_OWNER_APPROVAL"
READINESS_STATE_AFTER_PR143 = "OWNER_GLOBAL_OVERRIDE_SATISFIED_NON_OWNER_EVIDENCE_PENDING"
INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143 = "OWNER_GLOBAL_OVERRIDE_SATISFIED"
QUANTUM_PLANNING_STATE = "OWNER_APPROVED_QUANTUM_PLANNING_RELEASED_EXECUTION_EVIDENCE_PENDING"

OWNER_QUANTUM_PLANNING_RELEASE_LIST = (
    "OWNER_PERMISSION_REQUIRED_FOR_QUANTUM_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_QUANTUM_OPTIMIZATION_ARCHITECTURE",
    "OWNER_PERMISSION_REQUIRED_FOR_TRUE_QUANTUM_BACKEND_INTEGRATION_PLANNING",
    "OWNER_PERMISSION_REQUIRED_FOR_HYBRID_CLASSICAL_QUANTUM_ARBITRATION_PLANNING",
)

QUANTUM_PLANNING_ALLOWED_FIELDS = (
    "qaoa_planning_allowed",
    "vqe_planning_allowed",
    "annealing_planning_allowed",
    "qubo_problem_form_mapping_planning_allowed",
    "ising_problem_form_mapping_planning_allowed",
    "quantum_inspired_optimizer_planning_allowed",
    "hybrid_classical_quantum_arbitration_planning_allowed",
    "quantum_priority_policy_planning_allowed",
    "future_backend_adapter_architecture_planning_allowed",
    "quantum_parameter_schema_planning_allowed",
    "atomicrows_to_quantum_feature_compatibility_metadata_allowed",
    "quantum_optimizer_configuration_placeholders_allowed_if_marked_pending_evidence_or_backend",
)

QUANTUM_FORWARD_METADATA_ONLY_FIELDS = (
    "owner_internal_permission_for_quantum_planning_satisfied",
    "owner_internal_permission_for_quantum_optimization_architecture_satisfied",
    "owner_internal_permission_for_true_quantum_backend_integration_planning_satisfied",
    "quantum_planning_state",
    "quantum_forward_metadata_only",
    *QUANTUM_PLANNING_ALLOWED_FIELDS,
)

CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS = (
    "owner_internal_permission_for_optimizer_planning_satisfied",
    "deterministic_field_identity_ready",
    "external_fact_evidence_pending_not_owner_approval",
    "replay_paper_results_pending_not_owner_approval",
    "runtime_cash_receipt_pending_not_owner_approval",
)

ATOMICROWS_ENRICHMENT_ORDER = (
    "PR137R AtomicRows bundle reconciliation",
    "PR137L latency hot-path snapshot boundary",
    "PR138 semantic row contract and semantic field inventory",
    "PR139 row-family source manifest currentization",
    "PR140 semantic field coverage/enrichment plan",
    "PR141 semantic value materialization owner-authorization-readiness gate",
    "PR142 static downstream handoff-readiness gate",
    "PR143 QTT owner global override directive currentization and internal gate release",
    "PR143K/PR143P/PR143F venue/source/connector lanes",
    (
        "Future materialization implementation only after non-owner evidence gates "
        "are satisfied or explicitly scoped without fabricating facts"
    ),
)

LATENCY_HOT_PATH_BOUNDARY = {
    "control_plane_only": True,
    "live_pretrade_dependency_created": False,
    "live_path_import_created": False,
    "runtime_service_created": False,
    "order_router_dependency_created": False,
    "no_live_path_runtime_call": True,
    "no_doc_retrieval_in_live_path": True,
    "no_quantum_backend_call_in_live_path": True,
    "no_quantum_simulator_call_in_live_path": True,
    "no_optimizer_call_in_live_path": True,
    "owner_global_override_validation_not_live_hot_path_dependency": True,
    "future_live_path_must_consume_precomputed_owner_override_snapshot_only": True,
    "future_live_path_must_consume_precomputed_quantum_decision_snapshot_only": True,
}

NO_CLAIM_FALSE_FIELDS = (
    "source_acceptance_created",
    "connector_binding_created",
    "replay_execution_created",
    "paper_execution_created",
    "live_reachability_created",
    "order_authority_created",
    "runtime_cash_receipt_created",
    "profit_evidence_created",
    "latency_superiority_evidence_created",
    "execution_superiority_evidence_created",
    "final_readiness_created",
    "day1_launch_created",
    "semantic_values_materialized",
    "materialization_permission_for_actual_value_writes_created",
    "qtt_generated_integrity_authority_created",
    "atomicrows_bundle_sha_path_reference_created",
)
NO_CLAIM_BOUNDARY = {field: False for field in NO_CLAIM_FALSE_FIELDS}

FORBIDDEN_AUTHORITY_OUTPUT_FIELDS = (
    "owner_override_does_not_fabricate_external_facts",
    "owner_override_does_not_fabricate_source_acceptance",
    "owner_override_does_not_fabricate_connector_semantics",
    "owner_override_does_not_fabricate_runtime_cash",
    "owner_override_does_not_fabricate_order_or_fill_receipts",
    "owner_override_does_not_fabricate_replay_paper_results",
    "owner_override_does_not_fabricate_optimizer_results",
    "owner_override_does_not_fabricate_quantum_backend_results",
    "owner_override_does_not_fabricate_quantum_simulator_results",
    "owner_override_does_not_fabricate_live_order_authority",
    "owner_override_does_not_fabricate_profit_evidence",
)
FORBIDDEN_AUTHORITY_OUTPUT_BOUNDARY = {
    field: True for field in FORBIDDEN_AUTHORITY_OUTPUT_FIELDS
}

FORBIDDEN_CREATION_FALSE_FIELDS = (
    "materialization_permission_for_actual_value_writes_created",
    "semantic_values_materialized",
    "bundle_mutation_created",
    "row_family_source_mutation_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_resolver_execution_created",
    "replay_execution_created",
    "paper_execution_created",
    "live_reachability_created",
    "order_authority_created",
    "order_intent_execution_created",
    "runtime_cash_receipt_created",
    "profit_evidence_created",
    "latency_superiority_evidence_created",
    "execution_superiority_evidence_created",
    "final_readiness_created",
    "day1_launch_readiness_created",
    "true_quantum_backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solving_created",
    "ising_solving_created",
    "quantum_optimizer_input_output_created",
    "quantum_advantage_claim_created",
    "parameter_ranges_invented",
    "optimizer_defaults_invented",
    "classical_optimizer_execution_created",
    "scoring_execution_created",
    "ranking_execution_created",
    "arbitration_execution_created",
    "strategy_selection_created",
    "bundle_authority_created",
    "bundle_freeze_authority_created",
)
FORBIDDEN_CREATION_BOUNDARY = {field: False for field in FORBIDDEN_CREATION_FALSE_FIELDS}

FUTURE_PROMPT_CONSUMPTION_REQUIREMENTS = (
    "future_prompts_must_not_ask_owner_again_for_internal_qtt_approval",
    "future_validators_must_not_reblock_on_owner_approval_for_internal_qtt_workflow",
    "future_qtt_agents_must_treat_owner_internal_override_as_satisfied",
)

DOWNSTREAM_PR143_COMPATIBILITY_FIELDS = (
    "pr143_does_not_replace_pr143k",
    "pr143k_static_input_created",
    "pr143k_must_consume_owner_global_override_directive",
    "pr143k_must_not_ask_owner_again_for_internal_owner_approval",
    "pr143k_must_preserve_non_owner_evidence_boundaries",
    "pr143k_may_not_materialize_values_by_default",
    "pr143k_may_not_create_source_acceptance_unless separately scoped and evidence-backed",
    "pr143k_may_not_create_connector_binding_unless separately scoped and evidence-backed",
)

FORBIDDEN_PAYLOAD_FIELDS = (
    "semantic_value_payloads_allowed",
    "bundle_mutation_payloads_allowed",
    "row_family_source_mutation_payloads_allowed",
    "optimizer_result_payloads_allowed",
    "quantum_execution_result_payloads_allowed",
    "source_accepted_external_fact_payloads_allowed",
    "connector_semantic_binding_payloads_allowed",
    "live_order_execution_payloads_allowed",
    "qtt_generated_integrity_authority_payloads_allowed",
)
FORBIDDEN_PAYLOAD_BOUNDARY = {field: False for field in FORBIDDEN_PAYLOAD_FIELDS}

PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
)
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_DOWNSTREAM_AFTER_PR = 143
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS = {
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
    "tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py",
}
PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
)
PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_DOWNSTREAM_AFTER_PR = 143
PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS = {
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "report.py"
    ),
    (
        "tools/"
        "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
    ),
}

ALLOWED_PR143_CHANGED_PATHS = {
    YAML_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    SCHEMA_PATH.as_posix(),
    FIXTURE_PATH.as_posix(),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "model.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "builder.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "validator.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "report.py"
    ),
    "tools/validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    (
        "tests/fixtures/governance/"
        "synthetic_qtt_owner_global_override_directive_currentization_and_internal_gate_release.v1.fixture.json"
    ),
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/constants.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
}
IGNORED_PR143_CHANGED_PATH_PATTERNS = (".tmp/", ".tmp/**")

FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS = ("AtomicRows.bundle", ".sha256")
ALLOWED_INTEGRITY_FIELD_NAMES = (
    "main_head_short_sha_as_vcs_metadata_only",
    "atomicrows_bundle_sha_path_reference_created",
)


def forbidden_bundle_reference_text() -> str:
    return "".join(FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS)
