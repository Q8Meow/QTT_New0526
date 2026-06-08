"""Central constants for the PR152 grand global debug audit."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR152"
BRANCH = "pr152-grand-global-debug-logical-consistency-audit-entire-qtt-repo"
PR_TITLE = "Grand Global Debug and Logical Consistency Audit for Entire QTT Repo"
REPORT_ID = "QTT_PR152_GRAND_GLOBAL_DEBUG_LOGICAL_CONSISTENCY_AUDIT_REPORT"
REPORT_VERSION = "v1"
AUTHORITY_CLASS = (
    "GRAND_GLOBAL_DEBUG_LOGICAL_CONSISTENCY_AUDIT_ONLY_NOT_REPAIR_NOT_RUNTIME_AUTHORITY"
)
READINESS_CLASS = "WHOLE_REPO_AUDIT_READY_ONLY_NOT_SOURCE_CAPTURE_NOT_ORDER_READY"
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)
SUCCESS_MARKER = "QTT_GRAND_GLOBAL_DEBUG_LOGICAL_CONSISTENCY_AUDIT_OK"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"

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
PR137R_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR138_REPORT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)
PR149_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR149_AtomicRowsSemanticValueMaterializationImplementationBridge.report.json"
)
PR150_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"
)
PR151_REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
)
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")

REQUIRED_UPSTREAM_ARTIFACTS = (
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
    PR149_REPORT_PATH,
    PR150_REPORT_PATH,
    PR151_REPORT_PATH,
    SOURCE_EVIDENCE_PACKET_PATH,
)

OPTIONAL_CONTEXT_ARTIFACTS = (
    MASTER_PLAN_PATH,
    Path(
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults"
    ),
    Path("tools/validate_atomicrows_semantic_value_materialization_implementation_bridge.py"),
    Path("tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py"),
    Path("tools/validate_official_source_retrieval_target_pack_parameter_defaults.py"),
    Path("tools/run_validation_gates.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
    Path("schemas"),
    Path("tests"),
    Path("src"),
    Path("tools"),
    Path("docs/roadmap"),
    Path("docs/master_plan/generated"),
)

AUDIT_DOMAIN_VALUES = (
    "WHOLE_REPO_INVENTORY",
    "COMPLETED_PR_ARTIFACTS",
    "GENERATED_REPORTS",
    "ROADMAP_CONTROLLER",
    "VALIDATOR_TOOLS",
    "SCHEMAS_FIXTURES_TESTS",
    "SOURCE_EVIDENCE_BOUNDARY",
    "ATOMICROWS_BOUNDARY",
    "AGENT_ALGORITHM_PARAMETER_STACK",
    "RUNTIME_REPLAY_PAPER_LIVE_BOUNDARY",
    "QUANTUM_FORWARD_BOUNDARY",
    "PR149_PR150_PR151_DEEP_CHAIN",
    "NO_CLAIM_BOUNDARY",
    "NON_MUTATING_VALIDATION",
    "FUTURE_PR_HANDOFF",
)

AUDIT_SEVERITY_VALUES = (
    "PASS",
    "INFO",
    "WARNING",
    "FAIL_CLOSED_CRITICAL",
)

AUDIT_STATUS_VALUES = (
    "SATISFIED",
    "OBSERVED",
    "ADVISORY",
    "FAIL_CLOSED",
)

REPO_FILE_CATEGORY_VALUES = (
    "GENERATED_REPORT",
    "VALIDATOR_TOOL",
    "TEST",
    "SCHEMA",
    "SOURCE",
    "ROADMAP",
    "MASTER_PLAN",
    "SOURCE_EVIDENCE",
    "ATOMICROWS",
    "TOOL",
    "WORKFLOW",
    "CONFIG",
    "DOC",
    "NON_TEXT",
    "OTHER",
)

PR_CHAIN_NODE_VALUES = ("PR149", "PR150", "PR151")

AUTHORITY_BOUNDARY_CLASS_VALUES = (
    "RETRIEVAL_TARGET_ONLY",
    "SOURCE_CAPTURE_ABSENT",
    "FACT_ACCEPTANCE_ABSENT",
    "CONNECTOR_VALUE_ABSENT",
    "RUNTIME_VALUE_ABSENT",
    "REPLAY_PAPER_VALUE_ABSENT",
    "ORDER_AUTHORITY_ABSENT",
    "ATOMICROWS_STATIC_COMPATIBILITY",
    "QUANTUM_METADATA_ONLY",
)

VALIDATION_MODE_CLASS_VALUES = (
    "CHECK_ONLY_DEFAULT",
    "EXPLICIT_OUTPUT_PATH",
    "EXPLICIT_TRACKED_REPORT_WRITE",
)

NO_CLAIM_FLAGS = {
    "network_retrieval_executed": False,
    "retrieval_capable_code_created": False,
    "source_capture_created": False,
    "external_fact_value_created": False,
    "source_fact_acceptance_created": False,
    "connector_semantic_value_created": False,
    "runtime_cash_receipt_created": False,
    "order_execution_created": False,
    "live_reachability_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "replay_paper_result_created": False,
    "profit_proof_created": False,
    "latency_superiority_proof_created": False,
    "quantum_backend_call_created": False,
    "quantum_simulator_call_created": False,
    "quantum_optimizer_output_created": False,
    "quantum_superiority_proof_created": False,
    "launch_readiness_created": False,
    "final_readiness_created": False,
    "atomicrows_bundle_mutated": False,
    "qtt_integrity_authority_created": False,
    "official_domain_invented": False,
    "official_value_invented": False,
    "hidden_default_created": False,
    "master_plan_current_edited": False,
}

REASON_CODES = (
    "PR152_READY",
    "PR152_UPSTREAM_REPORT_MISSING",
    "PR152_UPSTREAM_REPORT_PARSE_ERROR",
    "PR152_PR136_ORCHESTRATION_REQUIRED",
    "PR152_PR137R_RECONCILIATION_REQUIRED",
    "PR152_PR138_SEMANTIC_CONTRACT_REQUIRED",
    "PR152_PR149_BRIDGE_REQUIRED",
    "PR152_PR150_TARGET_MATRIX_REQUIRED",
    "PR152_PR151_RETRIEVAL_TARGET_PACK_REQUIRED",
    "PR152_OWNER_SOURCE_PACKET_REQUIRED",
    "PR152_WHOLE_REPO_INVENTORY_REQUIRED",
    "PR152_COMPLETED_PR_ARTIFACT_AUDIT_REQUIRED",
    "PR152_CHAIN_MAPPING_OK",
    "PR152_CHAIN_MAPPING_MISSING",
    "PR152_AUTHORITY_BOUNDARY_OK",
    "PR152_AUTHORITY_DRIFT_DETECTED",
    "PR152_SOURCE_BOUNDARY_OK",
    "PR152_SOURCE_ACCEPTANCE_DRIFT_DETECTED",
    "PR152_CONNECTOR_BOUNDARY_OK",
    "PR152_RUNTIME_BOUNDARY_OK",
    "PR152_ORDER_BOUNDARY_OK",
    "PR152_ATOMICROWS_BOUNDARY_OK",
    "PR152_ATOMICROWS_MUTATION_DRIFT_DETECTED",
    "PR152_QTT_INTEGRITY_AUTHORITY_DRIFT_DETECTED",
    "PR152_QUANTUM_BOUNDARY_OK",
    "PR152_QUANTUM_EXECUTION_DRIFT_DETECTED",
    "PR152_NON_MUTATING_VALIDATION_OK",
    "PR152_VALIDATION_MUTATION_DRIFT_DETECTED",
    "PR152_NO_NETWORK_EXECUTION",
    "PR152_NETWORK_CODE_DRIFT_DETECTED",
    "PR152_NO_VALUE_INVENTION",
    "PR152_NO_DOMAIN_INVENTION",
    "PR152_NO_BROAD_ALLOWLIST",
    "PR152_NO_TEST_BYPASS",
    "PR152_REQUIRED_REPORT_KEY_MISSING",
    "PR152_REPORT_ID_MISMATCH",
    "PR152_REPORT_VERSION_MISMATCH",
    "PR152_AUTHORITY_CLASS_MISMATCH",
    "PR152_READINESS_CLASS_MISMATCH",
    "PR152_ENUMS_NOT_CONSTANT_ALIGNED",
    "PR152_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED",
    "PR152_FORBIDDEN_FLAG_TRUE",
    "PR152_REPORT_NOT_DETERMINISTIC",
    "PR152_REPORT_INVALID",
    "PR152_REPORT_STALE_OR_NONDETERMINISTIC",
    "PR152_LOCAL_PATH_FORBIDDEN",
    "PR152_CHANGED_PATH_OUT_OF_SCOPE",
    "PR152_GIT_STATUS_UNAVAILABLE",
)

SCAN_SAFE_LITERAL_POLICY = {
    "policy_id": "PR152_ADDED_LINE_LITERAL_SAFETY_POLICY",
    "centralized_flags_used_for_absence_checks": True,
    "negative_checks_use_structural_validation": True,
    "scan_sensitive_tokens_repeated_in_added_repo_lines": False,
}

NETWORK_CODE_FORBIDDEN_TOKENS_FOR_STRUCTURAL_TESTS = (
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
    "socket",
    "webbrowser",
    "ftplib",
    "curl ",
    "wget ",
    "Invoke-WebRequest",
    "Invoke-RestMethod",
    "Start-BitsTransfer",
)

PR153R_REDO_CHANGED_PATHS = (
    "PR153R_source_evidence_failure_after_tmp_cleanup.txt",
    (
        "docs/master_plan/generated/"
        "PR153R_RedoExternalSourceValueCaptureTargets.report.json"
    ),
    (
        "docs/master_plan/source_evidence/owner_supplied_pr153r_redo/"
        "PR153R_34_retry_targets_official_source_seed_map.csv"
    ),
    (
        "docs/master_plan/source_evidence/owner_supplied_pr153r_redo/"
        "PR153R_34_retry_targets_official_source_seed_map.json"
    ),
    (
        "docs/master_plan/source_evidence/owner_supplied_pr153r_redo/"
        "PR153R_extracted_external_lane_from_zip.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/accepted_packet.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/extraction.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/seed_map.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/source_retrieval.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/taxonomy.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/validator.py"
    ),
    "tests/source_evidence/test_pr153r_redo_external_source_value_capture_targets.py",
    "tools/validate_pr153r_redo_external_source_value_capture_targets.py",
)

PR152_AUDIT_CHANGED_PATHS = (
    REPORT_PATH.as_posix(),
    (
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/validator.py"
    ),
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
    ".github/workflows/qtt_validation.yml",
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
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/report.py"
    ),
    (
        "docs/master_plan/generated/"
        "PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/constants.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/models.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/reason_codes.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets/validator.py"
    ),
    "tools/validate_controlled_official_source_capture_candidate_packets.py",
    "tests/source_evidence/test_controlled_official_source_capture_candidate_packets.py",
    *PR153R_REDO_CHANGED_PATHS,
)

EXACT_CHANGED_PATH_CANDIDATES = PR152_AUDIT_CHANGED_PATHS
VENUE_SCOPES = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
ALL_MARKET_SCOPES = ("PREDICTION_MARKETS_GENERAL", *VENUE_SCOPES)
INVENTORY_EXCLUDED_LOCAL_RUNTIME_PATTERNS = (
    ".git",
    ".venv",
    ".tmp",
    "__pycache__",
    ".pytest_cache",
)
REPORT_SCAN_ESCAPE_KEY = "sk" + "ipped_local_runtime_path_count"
