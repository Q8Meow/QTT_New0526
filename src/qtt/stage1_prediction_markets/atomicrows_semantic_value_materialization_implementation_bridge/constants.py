"""Central constants for the PR149 AtomicRows implementation bridge."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR149"
BRANCH = "pr149-atomicrows-semantic-value-materialization-implementation-bridge"
PR_TITLE = "AtomicRows Semantic Value Materialization Implementation Bridge"
REPORT_ID = (
    "QTT_PR149_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_IMPLEMENTATION_BRIDGE_REPORT"
)
REPORT_VERSION = "v1"
AUTHORITY_CLASS = "ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_IMPLEMENTATION_BRIDGE_ONLY"
READINESS_CLASS = "IMPLEMENTATION_BRIDGE_READY_ONLY_NOT_RUNTIME_READY"
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR149_AtomicRowsSemanticValueMaterializationImplementationBridge.report.json"
)
SUCCESS_MARKER = (
    "QTT_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_IMPLEMENTATION_BRIDGE_OK"
)
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
QUANTUM_FORWARD_STATE = (
    "OWNER_APPROVED_QUANTUM_PLANNING_RELEASED_EXECUTION_EVIDENCE_PENDING"
)

ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
CONTROLLER_PATH = Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json")
ROADMAP_PATH = Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md")
ROADMAP_POLICY_PATH = Path(
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap_policy.py"
)
PR136_ROUTE_TRIAGE_PATH = Path("docs/master_plan/generated/PR136RouteTriage.report.json")
PR136_SECTION_CROSSWALK_ALIAS_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_CANONICAL_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)
PR136_MARKET_INDEX_PATH = Path(
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
)
PR136_COMMAND_MATRIX_PATH = Path(
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json"
)
PR136_AGENT_MAP_PATH = Path(
    "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json"
)
PR136_SEQUENCE_PATH = Path(
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"
)
PR136_QUANTUM_MAP_PATH = Path(
    "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json"
)
PR137R_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR138_REPORT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)
PR138_FIELD_INVENTORY_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json"
)
PR139_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsRowFamilySourceManifestCurrentization.report.json"
)
PR140_REPORT_PATH = Path(
    "docs/master_plan/generated/AtomicRowsSemanticFieldCoverageEnrichmentPlan.report.json"
)
PR141_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "AtomicRowsSemanticValueMaterializationOwnerAuthorizationGate.report.json"
)
PR142_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "AtomicRowsSemanticValueMaterializationAuthorizationHandoffReadinessGate.report.json"
)
PR143_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.report.json"
)
OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ROW_FAMILY_SOURCE_DIRECTORY = Path("docs/master_plan/atomic_rows/pr98_row_family_sources")

ALLOWED_INPUT_ARTIFACT_PATHS = (
    ROSTER_PATH,
    CONTROLLER_PATH,
    ROADMAP_PATH,
    ROADMAP_POLICY_PATH,
    PR136_ROUTE_TRIAGE_PATH,
    PR136_SECTION_CROSSWALK_CANONICAL_PATH,
    PR136_MARKET_INDEX_PATH,
    PR136_COMMAND_MATRIX_PATH,
    PR137R_REPORT_PATH,
    PR138_REPORT_PATH,
    PR139_REPORT_PATH,
    PR140_REPORT_PATH,
    PR141_REPORT_PATH,
    PR142_REPORT_PATH,
)
OPTIONAL_CONTEXT_ARTIFACT_PATHS = (
    PR136_AGENT_MAP_PATH,
    PR136_SEQUENCE_PATH,
    PR136_QUANTUM_MAP_PATH,
    PR138_FIELD_INVENTORY_PATH,
    PR143_REPORT_PATH,
    OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH,
)
REQUIRED_UPSTREAM_ARTIFACT_KEYS = (
    "control_plane_roster",
    "control_plane_controller",
    "launch_roadmap",
    "launch_roadmap_policy",
    "pr136_route_triage",
    "pr136_section_crosswalk_or_alias",
    "pr136_market_index",
    "pr136_command_matrix",
    "pr137r_reconciliation",
    "pr138_semantic_contract",
    "pr139_row_family_manifest",
    "pr140_field_coverage",
    "pr141_owner_authorization",
    "pr142_handoff_readiness",
)

MATERIALIZATION_STATE_VALUES = (
    "IMPLEMENTATION_BRIDGE_READY",
    "CONFIGURATION_READY_WITH_TYPED_LIMITS",
    "METADATA_ONLY_READY",
    "BLOCKED_WAITING_UPSTREAM_AUTHORIZATION",
    "BLOCKED_WAITING_FIELD_COVERAGE",
    "BLOCKED_WAITING_HANDOFF_READINESS",
    "BLOCKED_WAITING_ORCHESTRATION_ALIGNMENT",
    "BLOCKED_EXTERNAL_FACT_REQUIRED",
    "BLOCKED_RUNTIME_RECEIPT_REQUIRED",
    "BLOCKED_NO_LIVE_AUTHORITY",
    "BLOCKED_NO_ORDER_AUTHORITY",
    "BLOCKED_NO_BUNDLE_AUTHORITY",
    "BLOCKED_NO_QTT_INTEGRITY_AUTHORITY",
    "UNRESOLVED_PENDING_UPSTREAM",
)
VALUE_SOURCE_CLASS_VALUES = (
    "OWNER_INTERNAL_POLICY_VALUE",
    "INTERNAL_QTT_ARCHITECTURE_VALUE",
    "UPSTREAM_STATIC_REPORT_VALUE",
    "ATOMICROWS_SEMANTIC_CONTRACT_VALUE",
    "SOURCE_EVIDENCE_REQUIRED_EXTERNAL_FACT_VALUE",
    "RUNTIME_RECEIPT_REQUIRED_VALUE",
    "QUANTUM_FORWARD_METADATA_VALUE",
    "UNRESOLVED_PENDING_UPSTREAM_VALUE",
)
DOWNSTREAM_AGENT_SURFACE_CLASS_VALUES = (
    "ATOMICROWS_COMPILER_MATERIALIZATION_AGENT_CLASS",
    "QTT_ROLE_DUTY_REGISTRY_AGENT_SURFACE",
    "PARAMETER_STACK_SELECTION_SURFACE",
    "REPLAY_PAPER_CANDIDATE_PREPARATION_SURFACE",
    "OWNER_DASHBOARD_READ_ONLY_CONFIGURATION_SURFACE",
    "QUANTUM_OPTIMIZER_METADATA_SURFACE",
    "STATIC_METADATA_CONSUMER_ONLY",
    "UNRESOLVED_AGENT_SURFACE",
)

NO_CLAIM_FLAGS = {
    "source_fact_acceptance_created": False,
    "connector_semantic_binding_created": False,
    "runtime_cash_receipt_created": False,
    "order_execution_created": False,
    "live_reachability_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "profit_evidence_created": False,
    "latency_superiority_evidence_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "quantum_advantage_evidence_created": False,
    "launch_readiness_created": False,
    "final_readiness_created": False,
    "atomicrows_bundle_mutated": False,
    "qtt_integrity_authority_created": False,
    "external_fact_value_created": False,
    "venue_fact_value_created": False,
    "institutional_parameter_value_invented": False,
    "hidden_default_created": False,
}

REASON_CODES = (
    "PR149_READY",
    "PR149_UPSTREAM_REPORT_MISSING",
    "PR149_UPSTREAM_REPORT_PARSE_ERROR",
    "PR149_PR136_ORCHESTRATION_ALIGNMENT_REQUIRED",
    "PR149_PR137R_RECONCILIATION_REQUIRED",
    "PR149_PR138_SEMANTIC_CONTRACT_REQUIRED",
    "PR149_PR140_FIELD_COVERAGE_REQUIRED",
    "PR149_PR141_OWNER_AUTHORIZATION_REQUIRED",
    "PR149_PR142_HANDOFF_REQUIRED",
    "PR149_EXTERNAL_FACT_EVIDENCE_REQUIRED",
    "PR149_RUNTIME_RECEIPT_REQUIRED",
    "PR149_ROW_FAMILY_SCOPE_UNRESOLVED",
    "PR149_MARKET_SCOPE_UNRESOLVED",
    "PR149_AGENT_SURFACE_UNRESOLVED",
    "PR149_QUANTUM_METADATA_ONLY",
    "PR149_NO_RUNTIME_AUTHORITY",
    "PR149_NO_LIVE_AUTHORITY",
    "PR149_NO_ORDER_AUTHORITY",
    "PR149_NO_BUNDLE_MUTATION_AUTHORITY",
    "PR149_NO_QTT_INTEGRITY_AUTHORITY",
    "PR149_NO_HIDDEN_DEFAULTS",
    "PR149_OWNER_INTERNAL_POLICY_ONLY",
)

FORBIDDEN_NEW_REPO_LITERAL_POLICY = {
    "policy_id": "PR149_OWNER_SCAN_LITERAL_SAFETY_POLICY",
    "negative_checks_use_structural_flags": True,
    "owner_scan_phrase_list_repeated_in_added_repo_lines": False,
    "centralized_flags_used_for_absence_checks": True,
}

CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES = (
    REPORT_PATH.as_posix(),
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_implementation_bridge/__init__.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_implementation_bridge/constants.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_implementation_bridge/report.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_implementation_bridge/validator.py",
    "tools/validate_atomicrows_semantic_value_materialization_implementation_bridge.py",
    "tests/atomicrows/"
    "test_atomicrows_semantic_value_materialization_implementation_bridge.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_field_coverage_enrichment_plan/constants.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_owner_authorization_gate/constants.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
    "constants.py",
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
    "report.py",
    "src/qtt/stage1_prediction_markets/"
    "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
    "constants.py",
    "src/qtt/stage1_prediction_markets/"
    "qtt_owner_global_override_directive_currentization_and_internal_gate_release/"
    "report.py",
)
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

DEPENDENCY_CLASS_TO_BRIDGE = {
    "EXISTING_ROW_ID_ONLY": (
        "UPSTREAM_STATIC_REPORT_VALUE",
        "IMPLEMENTATION_BRIDGE_READY",
        ("PR149_READY",),
    ),
    "STATIC_INTERNAL_POLICY": (
        "INTERNAL_QTT_ARCHITECTURE_VALUE",
        "CONFIGURATION_READY_WITH_TYPED_LIMITS",
        ("PR149_OWNER_INTERNAL_POLICY_ONLY",),
    ),
    "STATIC_ENUM_OR_TAXONOMY": (
        "INTERNAL_QTT_ARCHITECTURE_VALUE",
        "CONFIGURATION_READY_WITH_TYPED_LIMITS",
        ("PR149_OWNER_INTERNAL_POLICY_ONLY",),
    ),
    "SOURCE_EVIDENCE_PACKET_REQUIRED": (
        "SOURCE_EVIDENCE_REQUIRED_EXTERNAL_FACT_VALUE",
        "BLOCKED_EXTERNAL_FACT_REQUIRED",
        ("PR149_EXTERNAL_FACT_EVIDENCE_REQUIRED",),
    ),
    "FUTURE_RUNTIME_RECEIPT_REQUIRED": (
        "RUNTIME_RECEIPT_REQUIRED_VALUE",
        "BLOCKED_RUNTIME_RECEIPT_REQUIRED",
        ("PR149_RUNTIME_RECEIPT_REQUIRED",),
    ),
    "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED": (
        "RUNTIME_RECEIPT_REQUIRED_VALUE",
        "BLOCKED_RUNTIME_RECEIPT_REQUIRED",
        ("PR149_RUNTIME_RECEIPT_REQUIRED",),
    ),
    "OWNER_AUTHORIZATION_REQUIRED": (
        "OWNER_INTERNAL_POLICY_VALUE",
        "CONFIGURATION_READY_WITH_TYPED_LIMITS",
        ("PR149_OWNER_INTERNAL_POLICY_ONLY",),
    ),
    "QUANTUM_METADATA_ONLY": (
        "QUANTUM_FORWARD_METADATA_VALUE",
        "METADATA_ONLY_READY",
        ("PR149_QUANTUM_METADATA_ONLY",),
    ),
    "AUTHORITY_FLAG_FORCED_FALSE": (
        "INTERNAL_QTT_ARCHITECTURE_VALUE",
        "CONFIGURATION_READY_WITH_TYPED_LIMITS",
        ("PR149_NO_RUNTIME_AUTHORITY",),
    ),
}

FORCED_FALSE_FIELD_REASON_CODES = {
    "live_use_allowed_flag": ("PR149_NO_LIVE_AUTHORITY",),
    "order_authority_created_flag": ("PR149_NO_ORDER_AUTHORITY",),
    "profit_evidence_created_flag": ("PR149_NO_RUNTIME_AUTHORITY",),
    "quantum_backend_execution_allowed_flag": ("PR149_QUANTUM_METADATA_ONLY",),
    "external_fact_authority_flag": ("PR149_EXTERNAL_FACT_EVIDENCE_REQUIRED",),
}
