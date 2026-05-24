"""Central constants for the PR141 AtomicRows semantic materialization gate."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR141"
BRANCH = "pr141-atomicrows-semantic-value-materialization-owner-authorization-gate"
GATE_ID = "QTT_PR141_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_OWNER_AUTHORIZATION_GATE"
GATE_VERSION = "v1"
REPORT_TYPE = (
    "QTT_PR141_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_OWNER_AUTHORIZATION_GATE_REPORT"
)
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_OWNER_AUTHORIZATION_GATE_ONLY_"
    "NOT_VALUE_MATERIALIZATION_NOT_BUNDLE_MUTATION_NOT_FINAL_READINESS"
)
SUCCESS_MARKER = (
    "QTT_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_OWNER_AUTHORIZATION_GATE_OK"
)
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"

EXPECTED_BUNDLE_ROW_COUNT = 4183
EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT = 15
EXPECTED_REQUIRED_FIELD_COUNT = 59
EXPECTED_REQUIRED_FIELD_GROUP_COUNT = 8

GATE_PATH = Path(
    "docs/master_plan/atomic_rows/"
    "AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.yaml"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.report.json"
)
SCHEMA_PATH = Path(
    "schemas/atomicrows/"
    "atomicrows_semantic_value_materialization_owner_authorization_gate.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_semantic_value_materialization_owner_authorization_gate.v1.fixture.json"
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
PR140_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsSemanticFieldCoverageEnrichmentPlan.report.json"
)
PR140_PLAN_PATH = Path(
    "docs/master_plan/atomic_rows/AtomicRowsSemanticFieldCoverageEnrichmentPlan.yaml"
)
PR140_SCHEMA_PATH = Path(
    "schemas/atomicrows/atomicrows_semantic_field_coverage_enrichment_plan.schema.json"
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
PR139_EVIDENCE_PATHS = (PR139_REPORT_PATH, PR139_MANIFEST_PATH)
PR140_EVIDENCE_PATHS = (PR140_REPORT_PATH, PR140_PLAN_PATH, PR140_SCHEMA_PATH)
VALIDATION_CONTEXT_EVIDENCE_PATHS = (
    Path("tools/ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context.py"),
    Path("tests/tools/test_ci_branch_context_invariants.py"),
    Path("tools/run_validation_gates.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
    Path("tools/build_master_plan_section_coverage_report.py"),
    Path("src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/validator.py"),
)

AUTHORITY_BOUNDARIES = {
    "semantic_values_materialized": False,
    "materialization_permission_created": False,
    "owner_approval_receipt_created": False,
    "bundle_mutation_allowed_flag": False,
    "source_file_mutation_allowed_flag": False,
    "row_family_sources_mutated": False,
    "atomicrows_bundle_mutated": False,
    "source_retrieval_created": False,
    "source_acceptance_created": False,
    "accepted_source_packet_created": False,
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
    "quantum_optimizer_input_created": False,
    "quantum_optimizer_output_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "quantum_advantage_claimed": False,
    "final_ready": False,
    "day1_launch_ready": False,
    "integrity_authority_created": False,
    "bundle_freeze_authority_created": False,
}

OWNER_AUTHORIZATION_READINESS_STATES = (
    "EXISTING_ROW_ID_ONLY_NO_AUTHORIZATION_NEEDED",
    "ELIGIBLE_TO_REQUEST_OWNER_AUTHORIZATION_METADATA_ONLY",
    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_MATERIALIZATION",
    "BLOCKED_UNTIL_ACCEPTED_SOURCE_EVIDENCE",
    "BLOCKED_UNTIL_RUNTIME_RECEIPT",
    "BLOCKED_UNTIL_REPLAY_PAPER_EVIDENCE",
    "BLOCKED_UNTIL_OWNER_SCOPE_DECISION",
    "FORCED_FALSE_AUTHORITY_BOUNDARY",
    "QUANTUM_METADATA_ONLY_NOT_BACKEND_AUTHORIZED",
)
MATERIALIZATION_ELIGIBILITY_STATES = (
    "EXISTING_FIELD_ALREADY_SUPPORTED",
    "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION",
    "BLOCKED_BY_SOURCE_EVIDENCE_DEPENDENCY",
    "BLOCKED_BY_RUNTIME_RECEIPT_DEPENDENCY",
    "BLOCKED_BY_REPLAY_PAPER_EVIDENCE_DEPENDENCY",
    "BLOCKED_BY_AUTHORITY_BOUNDARY",
    "BLOCKED_BY_QUANTUM_BACKEND_EXECUTION_BOUNDARY",
    "NOT_MATERIALIZED_BY_PR141",
)
DOWNSTREAM_DEPENDENCY_CLASSES = (
    "PR142_CONSUMABLE_STATIC_AUTHORIZATION_INPUT",
    "ACCEPTED_SOURCE_PACKET_DEPENDENT",
    "RUNTIME_RECEIPT_DEPENDENT",
    "REPLAY_PAPER_EVIDENCE_DEPENDENT",
    "OWNER_SCOPE_DECISION_DEPENDENT",
    "STATIC_POLICY_ONLY",
    "QUANTUM_METADATA_STATIC_ONLY",
    "AUTHORITY_BOUNDARY_FORCED_FALSE",
    "EXISTING_ROW_ID_ONLY",
)

PR140_COVERAGE_STATUS_VALUES = (
    "PRESENT_EXISTING_ID_ONLY",
    "PLANNED_NOT_MATERIALIZED",
    "BLOCKED_UNTIL_FUTURE_AUTHORIZED_PR",
)
PR140_DEPENDENCY_CLASS_VALUES = (
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
PR140_FUTURE_PR_DEPENDENCY_CLASS_VALUES = (
    "PR141_OR_PR142_OWNER_AUTHORIZATION_DEPENDENT",
    "ACCEPTED_SOURCE_PACKET_DEPENDENT",
    "RUNTIME_RECEIPT_DEPENDENT",
    "REPLAY_PAPER_EVIDENCE_DEPENDENT",
    "STATIC_POLICY_ONLY",
    "QUANTUM_METADATA_STATIC_ONLY",
)

FIELD_GROUP_IDS = (
    "IDENTITY",
    "PARAMETER_ALGORITHM_CLASSIFICATION",
    "AGENT_CONSUMER_BINDING",
    "MARKET_VENUE_SCOPE",
    "TRADING_OBJECTIVE_SUPPORT",
    "REPLAY_PAPER_LIVE_BOUNDARY",
    "QUANTUM_COMPATIBILITY",
    "SOURCE_PROVENANCE_BOUNDARY",
)
MARKET_SCOPE_IDS = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)

FORCED_FALSE_FIELD_IDS = {
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

FIELD_STATE_BY_PR140_DEPENDENCY_CLASS = {
    "EXISTING_ROW_ID_ONLY": (
        "EXISTING_ROW_ID_ONLY_NO_AUTHORIZATION_NEEDED",
        "EXISTING_FIELD_ALREADY_SUPPORTED",
        "EXISTING_ROW_ID_ONLY",
        "PR141_ROW_ID_ALREADY_SUPPORTED",
    ),
    "STATIC_INTERNAL_POLICY": (
        "ELIGIBLE_TO_REQUEST_OWNER_AUTHORIZATION_METADATA_ONLY",
        "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION",
        "PR142_CONSUMABLE_STATIC_AUTHORIZATION_INPUT",
        "PR141_STATIC_POLICY_METADATA_ELIGIBLE",
    ),
    "STATIC_ENUM_OR_TAXONOMY": (
        "ELIGIBLE_TO_REQUEST_OWNER_AUTHORIZATION_METADATA_ONLY",
        "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION",
        "PR142_CONSUMABLE_STATIC_AUTHORIZATION_INPUT",
        "PR141_STATIC_TAXONOMY_METADATA_ELIGIBLE",
    ),
    "SOURCE_EVIDENCE_PACKET_REQUIRED": (
        "BLOCKED_UNTIL_ACCEPTED_SOURCE_EVIDENCE",
        "BLOCKED_BY_SOURCE_EVIDENCE_DEPENDENCY",
        "ACCEPTED_SOURCE_PACKET_DEPENDENT",
        "PR141_BLOCKED_UNTIL_ACCEPTED_SOURCE_EVIDENCE",
    ),
    "FUTURE_RUNTIME_RECEIPT_REQUIRED": (
        "BLOCKED_UNTIL_RUNTIME_RECEIPT",
        "BLOCKED_BY_RUNTIME_RECEIPT_DEPENDENCY",
        "RUNTIME_RECEIPT_DEPENDENT",
        "PR141_BLOCKED_UNTIL_RUNTIME_RECEIPT",
    ),
    "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED": (
        "BLOCKED_UNTIL_REPLAY_PAPER_EVIDENCE",
        "BLOCKED_BY_REPLAY_PAPER_EVIDENCE_DEPENDENCY",
        "REPLAY_PAPER_EVIDENCE_DEPENDENT",
        "PR141_BLOCKED_UNTIL_REPLAY_PAPER_EVIDENCE",
    ),
    "OWNER_AUTHORIZATION_REQUIRED": (
        "OWNER_AUTHORIZATION_REQUIRED_BEFORE_MATERIALIZATION",
        "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION",
        "OWNER_SCOPE_DECISION_DEPENDENT",
        "PR141_OWNER_SCOPE_DECISION_REQUIRED",
    ),
    "QUANTUM_METADATA_ONLY": (
        "QUANTUM_METADATA_ONLY_NOT_BACKEND_AUTHORIZED",
        "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION",
        "QUANTUM_METADATA_STATIC_ONLY",
        "PR141_QUANTUM_METADATA_ONLY_NO_BACKEND",
    ),
    "AUTHORITY_FLAG_FORCED_FALSE": (
        "FORCED_FALSE_AUTHORITY_BOUNDARY",
        "BLOCKED_BY_AUTHORITY_BOUNDARY",
        "AUTHORITY_BOUNDARY_FORCED_FALSE",
        "PR141_FORCED_FALSE_AUTHORITY_BOUNDARY",
    ),
}

FIELD_RATIONALE_BY_REASON_CODE = {
    "PR141_ROW_ID_ALREADY_SUPPORTED": (
        "PR137R records row_id as the only already supported field; PR141 does not "
        "need or create owner authorization for it."
    ),
    "PR141_STATIC_POLICY_METADATA_ELIGIBLE": (
        "PR140 planned this static policy field as metadata only. PR141 marks it "
        "eligible to request future owner-authorized materialization."
    ),
    "PR141_STATIC_TAXONOMY_METADATA_ELIGIBLE": (
        "PR140 planned this taxonomy field as metadata only. PR141 creates only "
        "future authorization-readiness metadata."
    ),
    "PR141_BLOCKED_UNTIL_ACCEPTED_SOURCE_EVIDENCE": (
        "This field depends on future accepted source evidence before any value can "
        "be materialized or used."
    ),
    "PR141_BLOCKED_UNTIL_RUNTIME_RECEIPT": (
        "This field depends on future runtime or private-state receipt evidence; "
        "PR141 creates no runtime receipt."
    ),
    "PR141_BLOCKED_UNTIL_REPLAY_PAPER_EVIDENCE": (
        "This field depends on future replay or paper evidence; PR141 creates no "
        "replay or paper result."
    ),
    "PR141_OWNER_SCOPE_DECISION_REQUIRED": (
        "This field can only move forward after a future owner scope decision; "
        "PR141 records readiness only."
    ),
    "PR141_QUANTUM_METADATA_ONLY_NO_BACKEND": (
        "Quantum compatibility remains static metadata only and cannot authorize "
        "optimizer input, simulator execution, backend execution, or advantage claims."
    ),
    "PR141_FORCED_FALSE_AUTHORITY_BOUNDARY": (
        "This authority field remains forced false; PR141 creates no permission, "
        "receipt, live use, order authority, profit evidence, external fact authority, "
        "or quantum backend authority."
    ),
    "PR141_QUANTUM_BACKEND_EXECUTION_BOUNDARY_FORCED_FALSE": (
        "The quantum backend execution flag is a forced-false boundary and remains "
        "metadata only; PR141 creates no quantum execution authority."
    ),
}

LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY = {
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
    "future_live_path_consumption_mode": (
        "PRECOMPUTED_SNAPSHOT_ONLY_AFTER_FUTURE_AUTHORIZED_PR"
    ),
}

DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR141 = (
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

FORBIDDEN_PROPERTY_NAME_FRAGMENTS = ("sha", "sha256", "digest", "hash", "checksum")
FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS = ("AtomicRows.bundle", ".sha256")


def forbidden_bundle_reference_text() -> str:
    return "".join(FORBIDDEN_BUNDLE_REFERENCE_FRAGMENTS)

PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
)
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_DOWNSTREAM_AFTER_PR = 143
PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS = {
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
    "tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py",
}
PR140_GUARD_REPAIR_ALLOWANCE_REASON_CODE = (
    "PR140_GUARD_REPAIR_REQUIRED_FOR_PR141_DOWNSTREAM_HANDOFF"
)
PR140_GUARD_REPAIR_CHANGED_PATHS = {
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
}
PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS = {
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

ALLOWED_PR141_CHANGED_PATHS = {
    GATE_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    SCHEMA_PATH.as_posix(),
    FIXTURE_PATH.as_posix(),
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/__init__.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    "tools/validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
}
IGNORED_PR141_CHANGED_PATH_PATTERNS = (".tmp/", ".tmp/**")
