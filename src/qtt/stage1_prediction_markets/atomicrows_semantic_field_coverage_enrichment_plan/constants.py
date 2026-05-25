"""Central constants for the PR140 AtomicRows semantic coverage gate."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR140"
BRANCH = "pr140-atomicrows-semantic-field-coverage-enrichment-plan"
REPORT_TYPE = "QTT_PR140_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_REPORT"
PLAN_ID = "QTT_PR140_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN"
PLAN_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_ONLY_NOT_VALUE_"
    "MATERIALIZATION_NOT_BUNDLE_MUTATION_NOT_FINAL_READINESS"
)
SUCCESS_MARKER = "QTT_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_FAILED"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"

EXPECTED_BUNDLE_ROW_COUNT = 4183
EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT = 15
EXPECTED_REQUIRED_FIELD_COUNT = 59
EXPECTED_REQUIRED_FIELD_GROUP_COUNT = 8

PLAN_PATH = Path(
    "docs/master_plan/atomic_rows/AtomicRowsSemanticFieldCoverageEnrichmentPlan.yaml"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsSemanticFieldCoverageEnrichmentPlan.report.json"
)
SCHEMA_PATH = Path(
    "schemas/atomicrows/atomicrows_semantic_field_coverage_enrichment_plan.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_semantic_field_coverage_enrichment_plan.v1.fixture.json"
)

PR138_INVENTORY_PATH = Path("docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json")
PR138_REPORT_PATH = Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json")
PR137R_REPORT_PATH = Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json")
PR137R_INDEX_PATH = Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.index.json")
PR137L_REPORT_PATH = Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.report.json")
PR137L_INDEX_PATH = Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.index.json")
PR139_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsRowFamilySourceManifestCurrentization.report.json"
)
PR139_MANIFEST_PATH = Path(
    "docs/master_plan/atomic_rows/AtomicRowsRowFamilySourceManifestCurrentization.yaml"
)
PR139_SCHEMA_PATH = Path(
    "schemas/atomicrows/atomicrows_row_family_source_manifest_currentization.schema.json"
)
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ROW_FAMILY_SOURCE_DIRECTORY = Path("docs/master_plan/atomic_rows/pr98_row_family_sources")
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")

CROSSWALK_REQUESTED_ALIAS = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
CROSSWALK_CANONICAL = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)

CONTROL_PLANE_EVIDENCE_PATHS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json"),
    Path("src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py"),
    Path("src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap.py"),
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
PR137L_EVIDENCE_PATHS = (PR137L_REPORT_PATH, PR137L_INDEX_PATH)
PR137R_EVIDENCE_PATHS = (PR137R_REPORT_PATH, PR137R_INDEX_PATH)
PR138_EVIDENCE_PATHS = (PR138_REPORT_PATH, PR138_INVENTORY_PATH)
PR139_EVIDENCE_PATHS = (PR139_REPORT_PATH, PR139_MANIFEST_PATH, PR139_SCHEMA_PATH)
BRANCH_CONTEXT_EVIDENCE_PATHS = (
    Path("tools/ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context_invariants.py"),
)

AUTHORITY_BOUNDARIES = {
    "bundle_mutation_allowed_flag": False,
    "source_file_mutation_allowed_flag": False,
    "semantic_values_materialized": False,
    "source_acceptance_created": False,
    "connector_semantic_binding_created": False,
    "private_state_fetch_created": False,
    "runtime_cash_authority_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "replay_result_created": False,
    "paper_result_created": False,
    "trading_signal_created": False,
    "scoring_ranking_arbitration_output_created": False,
    "runtime_live_order_authority_created": False,
    "order_execution_created": False,
    "fill_receipt_created": False,
    "profit_evidence_created": False,
    "latency_superiority_claimed": False,
    "execution_superiority_claimed": False,
    "alpha_evidence_created": False,
    "neural_training_or_inference_created": False,
    "quantum_optimizer_input_created": False,
    "quantum_optimizer_output_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "quantum_advantage_claimed": False,
    "final_ready": False,
    "day1_launch_ready": False,
    "qtt_integrity_authority_created": False,
}

COVERAGE_STATUS_VALUES = (
    "PRESENT_EXISTING_ID_ONLY",
    "PLANNED_NOT_MATERIALIZED",
    "BLOCKED_UNTIL_FUTURE_AUTHORIZED_PR",
)
DEPENDENCY_CLASS_VALUES = (
    "EXISTING_ROW_ID_ONLY",
    "STATIC_INTERNAL_POLICY",
    "STATIC_ENUM_OR_TAXONOMY",
    "SOURCE_EVIDENCE_PACKET_REQUIRED",
    "FUTURE_RUNTIME_RECEIPT_REQUIRED",
    "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED",
    "OWNER_AUTHORIZATION_REQUIRED",
    "QUANTUM_METADATA_ONLY",
    "AUTHORITY_FLAG_FORCED_FALSE",
)
FUTURE_PR_DEPENDENCY_CLASS_VALUES = (
    "PR141_OR_PR142_OWNER_AUTHORIZATION_DEPENDENT",
    "ACCEPTED_SOURCE_PACKET_DEPENDENT",
    "RUNTIME_RECEIPT_DEPENDENT",
    "REPLAY_PAPER_EVIDENCE_DEPENDENT",
    "STATIC_POLICY_ONLY",
    "QUANTUM_METADATA_STATIC_ONLY",
)

MARKET_SCOPE_IDS = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)

LATENCY_HOT_PATH_EXCLUSION_MATRIX = {
    "source_retrieval_in_hot_path_allowed": False,
    "source_acceptance_in_hot_path_allowed": False,
    "connector_binding_in_hot_path_allowed": False,
    "runtime_resolver_snapshot_creation_in_hot_path_allowed": False,
    "private_state_fetch_in_hot_path_allowed": False,
    "dashboard_rendering_in_hot_path_allowed": False,
    "telegram_calls_in_hot_path_allowed": False,
    "llm_calls_in_hot_path_allowed": False,
    "replay_execution_in_hot_path_allowed": False,
    "paper_execution_in_hot_path_allowed": False,
    "quantum_backend_calls_in_hot_path_allowed": False,
    "quantum_simulator_calls_in_hot_path_allowed": False,
    "atomicrows_materialization_in_hot_path_allowed": False,
    "network_io_in_hot_path_allowed": False,
    "file_system_document_fetch_in_hot_path_allowed": False,
    "unbounded_search_in_hot_path_allowed": False,
    "future_live_path_consumption_mode": "PRECOMPUTED_SNAPSHOT_ONLY",
}

DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR140 = (
    "semantic_value_materialization",
    "bundle_mutation",
    "row_family_source_mutation",
    "source_acceptance",
    "connector_binding",
    "replay_execution",
    "paper_execution",
    "live_order_authority",
    "quantum_backend_execution",
    "final_readiness",
)

AUTHORITY_FLAG_FIELD_IDS = {
    "live_use_allowed_flag",
    "order_authority_created_flag",
    "profit_evidence_created_flag",
    "quantum_backend_execution_allowed_flag",
    "external_fact_authority_flag",
}
QUANTUM_METADATA_FIELD_IDS = {
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
}
SOURCE_EVIDENCE_FIELD_IDS = {
    "venue_scope",
    "kalshi_compatibility",
    "polymarket_compatibility",
    "forecastex_ibkr_compatibility",
    "source_evidence_required_flag",
    "accepted_source_packet_required_flag",
    "research_input_only_flag",
    "liquidity_context_family",
}
RUNTIME_RECEIPT_FIELD_IDS = {
    "execution_family",
    "capital_family",
    "execution_cost_model_family",
    "capital_intensity_class",
}
REPLAY_PAPER_FIELD_IDS = {
    "expected_net_profit_objective_family",
    "drawdown_control_family",
    "exposure_limit_family",
}
OWNER_AUTHORIZATION_FIELD_IDS = {
    "owner_review_required_flag",
}
STATIC_POLICY_FIELD_IDS = {
    "row_family",
    "row_type",
    "lifecycle_state",
    "version_state",
    "deprecation_state",
    "agent_role",
    "consumer_class",
    "allowed_consumers",
    "blocked_consumers",
    "command_matrix_binding",
    "market_scope",
    "prediction_market_scope",
    "prediction_markets_general_compatibility",
    "replay_required_flag",
    "paper_required_flag",
}

FIELD_RATIONALE_BY_DEPENDENCY_CLASS = {
    "EXISTING_ROW_ID_ONLY": (
        "PR137R evidence shows row_id is the only already supported PR138 semantic field."
    ),
    "STATIC_INTERNAL_POLICY": (
        "PR140 records the policy placement only; row values remain unmaterialized."
    ),
    "STATIC_ENUM_OR_TAXONOMY": (
        "PR140 records a static taxonomy/enrichment locus only; no row values are created."
    ),
    "SOURCE_EVIDENCE_PACKET_REQUIRED": (
        "External or venue-dependent truth requires a future accepted source packet before live use."
    ),
    "FUTURE_RUNTIME_RECEIPT_REQUIRED": (
        "The field can only become true with future runtime/private-state/cash receipts."
    ),
    "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED": (
        "The field can only become true with future replay or paper evidence."
    ),
    "OWNER_AUTHORIZATION_REQUIRED": (
        "Materialization or use of this boundary requires explicit future owner authorization."
    ),
    "QUANTUM_METADATA_ONLY": (
        "Quantum compatibility is static forward metadata only; no optimizer or backend executes."
    ),
    "AUTHORITY_FLAG_FORCED_FALSE": (
        "This authority boundary remains forced false until a later owner-authorized PR opens scope."
    ),
}

PR141_DOWNSTREAM_ALLOWANCE_REASON_CODE = (
    "PR141_DOWNSTREAM_AUTHORIZATION_GATE_CONSUMES_PR140_HANDOFF"
)
PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS = {
    "docs/master_plan/atomic_rows/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.yaml",
    "docs/master_plan/generated/AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.report.json",
    "schemas/atomicrows/atomicrows_semantic_value_materialization_owner_authorization_gate.schema.json",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/__init__.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    "tools/validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    (
        "tests/fixtures/atomicrows/"
        "synthetic_atomicrows_semantic_value_materialization_owner_authorization_gate.v1.fixture.json"
    ),
}
PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS = {
    "docs/master_plan/atomic_rows/AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.yaml",
    "docs/master_plan/generated/AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.report.json",
    "schemas/atomicrows/atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.schema.json",
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/model.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/builder.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/validator.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py"
    ),
    "tools/validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    (
        "tests/fixtures/atomicrows/"
        "synthetic_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.v1.fixture.json"
    ),
}
PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS = {
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
PR150_TARGET_MATRIX_CHANGED_PATHS = {
    (
        "docs/master_plan/generated/"
        "PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/validator.py"
    ),
    "tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py",
    (
        "tests/atomicrows/"
        "test_source_backed_classical_quantum_parameter_default_target_matrix.py"
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
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py"
    ),
}
PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS = {
    (
        "docs/master_plan/generated/"
        "PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/validator.py"
    ),
    "tools/validate_official_source_retrieval_target_pack_parameter_defaults.py",
    (
        "tests/source_evidence/"
        "test_official_source_retrieval_target_pack_parameter_defaults.py"
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
        "source_backed_classical_quantum_parameter_default_target_matrix/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py"
    ),
}

ALLOWED_PR140_CHANGED_PATHS = {
    PLAN_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    SCHEMA_PATH.as_posix(),
    FIXTURE_PATH.as_posix(),
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/__init__.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
    "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/validator.py",
    "tools/build_master_plan_section_coverage_report.py",
    "tools/validate_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py",
    "tests/atomicrows/test_atomicrows_row_family_source_manifest_currentization.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
}

IGNORED_PR140_CHANGED_PATH_PATTERNS = (
    ".tmp/",
    ".tmp/**",
)

FORBIDDEN_BUNDLE_SIDECAR_FRAGMENTS = (
    "AtomicRows.bundle.sha",
    "AtomicRows.bundle.digest",
    "AtomicRows.bundle.hash",
    "AtomicRows.bundle.checksum",
    "atomicrows_bundle_sha",
    "atomicrows_bundle_digest",
    "atomicrows_bundle_hash",
    "atomicrows_bundle_checksum",
)
FORBIDDEN_INTEGRITY_AUTHORITY_KEYS = (
    "qtt_generated_integrity_authority",
    "qtt_generated_sha",
    "qtt_sha_authority",
    "cryptographic_authority",
    "freeze_authority",
)
