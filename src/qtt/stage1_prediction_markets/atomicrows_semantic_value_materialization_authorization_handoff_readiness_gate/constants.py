"""Central constants for the PR142 AtomicRows handoff-readiness gate."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR142"
BRANCH = "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate"
ARTIFACT_STEM = "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate"
PACKAGE_NAME = (
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate"
)
GATE_ID = "QTT_PR142_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_AUTHORIZATION_HANDOFF_READINESS_GATE"
REPORT_TYPE = (
    "QTT_PR142_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_AUTHORIZATION_HANDOFF_"
    "READINESS_GATE_REPORT"
)
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_AUTHORIZATION_HANDOFF_"
    "READINESS_GATE_ONLY_NOT_VALUE_MATERIALIZATION_NOT_OWNER_APPROVAL_NOT_BUNDLE_"
    "MUTATION_NOT_FINAL_READINESS"
)
AUTHORITY_CLASS_VALUES = (AUTHORITY_CLASS,)
SUCCESS_MARKER = (
    "QTT_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_AUTHORIZATION_HANDOFF_"
    "READINESS_GATE_OK"
)
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
MAIN_PREFLIGHT_HEAD_SHORT_SHA_AS_VCS_METADATA_ONLY = "0715a3c"
GITHUB_MAIN_VALIDATION_STATUS = "SUCCESS"
GITHUB_STATUS_CLAIMED = True

YAML_PATH = Path(
    "docs/master_plan/atomic_rows/"
    "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.yaml"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.report.json"
)
SCHEMA_PATH = Path(
    "schemas/atomicrows/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.v1.fixture.json"
)

PR141_YAML_PATH = Path(
    "docs/master_plan/atomic_rows/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.yaml"
)
PR141_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.report.json"
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
OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
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
    PR141_YAML_PATH,
    PR141_REPORT_PATH,
)

VALIDATION_CONTEXT_EVIDENCE_PATHS = (
    Path("tools/ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context_invariants.py"),
    Path("tools/run_validation_gates.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
)

READINESS_STATES = (
    "STATIC_HANDOFF_READY_FOR_OWNER_REVIEW_REQUEST",
    "STATIC_MATERIALIZATION_PLAN_INPUT_READY_OWNER_ACTION_REQUIRED",
    "BLOCKED_FOR_MATERIALIZATION_UNTIL_OWNER_APPROVAL_AND_EVIDENCE",
)

BLOCK_REASON_CODES = (
    "MISSING_OWNER_APPROVAL",
    "MISSING_OWNER_APPROVAL_RECEIPT",
    "MISSING_MATERIALIZATION_PERMISSION",
    "MISSING_ACCEPTED_SOURCE_PACKETS",
    "MISSING_RUNTIME_RECEIPTS",
    "MISSING_REPLAY_PAPER_RESULTS",
    "MISSING_OPTIMIZER_DEFAULT_POLICY_OR_ACCEPTED_EVIDENCE",
    "VALUE_MATERIALIZATION_STILL_BLOCKED",
)

QUANTUM_FORWARD_METADATA_ONLY_FIELDS = (
    "quantum_family",
    "quantum_applicability_class",
    "classical_only_flag",
    "quantum_inspired_flag",
    "true_quantum_compatible_flag",
    "qubo_compatible_flag",
    "ising_compatible_flag",
    "qaoa_compatible_flag",
    "vqe_compatible_flag",
    "annealing_compatible_flag",
    "quantum_kernel_feature_map_compatible_flag",
)

CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS = (
    "deterministic_field_identity_ready",
    "missing_value_materialization_blocks_optimizer_use",
    "missing_external_fact_evidence_blocks_runtime_use",
    "missing_owner_approval_blocks_materialization",
    "missing_replay_paper_results_blocks_live_promotion",
    "missing_runtime_cash_receipt_blocks_exposure",
)

ATOMICROWS_ENRICHMENT_ORDER = (
    "PR137R AtomicRows bundle reconciliation",
    "PR137L latency hot-path snapshot boundary",
    "PR138 semantic row contract and semantic field inventory",
    "PR139 row-family source manifest currentization",
    "PR140 semantic field coverage/enrichment plan",
    "PR141 semantic value materialization owner-authorization-readiness gate",
    "PR142 static downstream handoff-readiness gate",
    "Future owner-authorized approval/materialization planning only after explicit evidence and owner approval",
)

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
    "owner_approval_created",
    "owner_approval_receipt_created",
)
NO_CLAIM_BOUNDARY = {field: False for field in NO_CLAIM_FALSE_FIELDS}

FORBIDDEN_AUTHORITY_OUTPUT_FIELDS = (
    "semantic_values_materialized",
    "materialization_permission_created",
    "owner_approval_created",
    "owner_approval_receipt_created",
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
    "quantum_optimizer_input_output_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "quantum_advantage_claim_created",
    "atomicrows_bundle_mutation_created",
    "row_family_source_mutation_created",
    "bundle_authority_created",
    "bundle_freeze_authority_created",
)
FORBIDDEN_AUTHORITY_OUTPUT_BOUNDARY = {
    field: False for field in FORBIDDEN_AUTHORITY_OUTPUT_FIELDS
}

FORBIDDEN_PAYLOAD_BOUNDARY_FIELDS = (
    "semantic_value_payloads_allowed",
    "bundle_mutation_payloads_allowed",
    "row_family_source_mutation_payloads_allowed",
    "optimizer_result_payloads_allowed",
    "source_accepted_external_fact_payloads_allowed",
    "connector_semantic_binding_payloads_allowed",
    "live_order_execution_payloads_allowed",
    "qtt_generated_integrity_authority_payloads_allowed",
    "atomicrows_forbidden_bundle_reference_created",
)
FORBIDDEN_PAYLOAD_BOUNDARY = {field: False for field in FORBIDDEN_PAYLOAD_BOUNDARY_FIELDS}

QUANTUM_EXECUTION_FALSE_FIELDS = (
    "true_quantum_backend_execution_created",
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
)
QUANTUM_EXECUTION_BOUNDARY = {field: False for field in QUANTUM_EXECUTION_FALSE_FIELDS}

CLASSICAL_OPTIMIZER_FALSE_FIELDS = (
    "classical_optimizer_execution_created",
    "scoring_execution_created",
    "ranking_execution_created",
    "arbitration_execution_created",
    "strategy_selection_created",
)
CLASSICAL_OPTIMIZER_BOUNDARY = {field: False for field in CLASSICAL_OPTIMIZER_FALSE_FIELDS}

LATENCY_HOT_PATH_BOUNDARY = {
    "control_plane_only": True,
    "live_pretrade_dependency_created": False,
    "live_path_import_created": False,
    "runtime_service_created": False,
    "order_router_dependency_created": False,
    "no_live_path_runtime_call": True,
    "no_doc_retrieval_in_live_path": True,
    "no_quantum_call_in_live_path": True,
    "no_optimizer_call_in_live_path": True,
}

PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
)
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_DOWNSTREAM_AFTER_PR = 143
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS = {
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
    "tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py",
}
PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_REQUIRED"
)
PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_DOWNSTREAM_AFTER_PR = 145
PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_CHANGED_PATHS = {
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/atomicrows/test_atomicrows_exact_row_authority_classifier_bridge.py",
    "tests/atomicrows/test_atomicrows_exact_row_expansion_manifest.py",
    "tests/atomicrows/test_atomicrows_exact_row_generator_dry_run_manifest.py",
    "tests/atomicrows/test_atomicrows_owner_approved_exact_15_family_count_distribution.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
    "tests/source_evidence/test_pr134_preserves_run_validation_gates_fresh_tempdir.py",
    "tools/validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    "tools/validate_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tools/validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tools/validate_historical_dataset_policy_literal_drift.py",
    "tools/validate_pr136_roadmap_policy_literal_drift.py",
    "tools/validate_source_revalidation_scheduler.py",
    "tools/validate_connector_semantic_binding_implementation_gate.py",
    "tools/validate_per_venue_execution_lifecycle_model.py",
    "tools/validate_cross_venue_execution_normalization_binding.py",
    "tools/runtime_cash_component_field_map_validate.py",
    "tools/private_state_read_receipt_gate_validate.py",
    "tools/validate_atomicrows_bundle_materialization_manifest.py",
    "tools/validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
    "tools/validate_atomicrows_exact_row_source_materialization_manifest.py",
    "tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
    "tools/validate_atomicrows_sha_system_dormancy_state_contract.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "report.py"
    ),
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "report.py"
    ),
}
PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_DOWNSTREAM_AFTER_PR = 147
PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_CHANGED_PATHS = {
    "docs/master_plan/generated/QttPrIdentityRoster.report.json",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
}
PR149_IMPLEMENTATION_BRIDGE_CHANGED_PATHS = {
    (
        "docs/master_plan/generated/"
        "PR149_AtomicRowsSemanticValueMaterializationImplementationBridge.report.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/validator.py"
    ),
    "tools/validate_atomicrows_semantic_value_materialization_implementation_bridge.py",
    (
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_implementation_bridge.py"
    ),
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
        "report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
        "report.py"
    ),
}

ALLOWED_PR142_CHANGED_PATHS = {
    YAML_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    SCHEMA_PATH.as_posix(),
    FIXTURE_PATH.as_posix(),
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/__init__.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/constants.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/model.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/builder.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/validator.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
    "tools/validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "docs/master_plan/governance/QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.yaml",
    (
        "docs/master_plan/generated/"
        "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.report.json"
    ),
    (
        "schemas/governance/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release.schema.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/model.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/builder.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/validator.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py"
    ),
    "tools/validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    (
        "tests/fixtures/governance/"
        "synthetic_qtt_owner_global_override_directive_currentization_and_internal_gate_release.v1.fixture.json"
    ),
}
IGNORED_PR142_CHANGED_PATH_PATTERNS = (".tmp/", ".tmp/**")

FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS = ("AtomicRows.bundle", ".sha256")
ALLOWED_VCS_METADATA_FIELD_NAMES = ("main_head_short_sha_as_vcs_metadata_only",)


def forbidden_bundle_reference_text() -> str:
    return "".join(FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS)
