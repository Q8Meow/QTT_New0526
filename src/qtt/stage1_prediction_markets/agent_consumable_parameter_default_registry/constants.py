"""Central constants for PR155 agent-consumable defaults."""

from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.atomicrows_parameter_default_value_materialization_gate import (
    taxonomy as pr154_tx,
)
from src.qtt.stage1_prediction_markets.launch_readiness import (
    day1_launch_readiness_roadmap_policy as day1_policy,
)


PR_ID = "PR155"
SEMANTIC_TASK_ID = "PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY"
BRANCH = "pr155-agent-consumable-parameter-default-registry"
REGISTRY_TYPE = "QTT_PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY"
REPORT_TYPE = "QTT_PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY_REPORT"
SUCCESS_MARKER = "QTT_PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY_OK"
AUTHORITY_CLASS = (
    "AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY_NOT_RUNTIME_NOT_LIVE_NOT_CONNECTOR_"
    "NOT_REPLAY_NOT_PAPER_NOT_QUANTUM_EXECUTION_NOT_PROFIT_AUTHORITY"
)
AUTHORITY_CLASS_VALUES = (AUTHORITY_CLASS,)

REGISTRY_PATH = Path(
    "docs/master_plan/generated/"
    "PR155_AgentConsumableParameterDefaultRegistry.registry.json"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR155_AgentConsumableParameterDefaultRegistry.report.json"
)

PR154_INPUT_REPORT_PATH = pr154_tx.REPORT_PATH
PR154_INPUT_REPORT_ID = pr154_tx.REPORT_ID
PR154_INPUT_VALIDATOR_MARKER = pr154_tx.VALIDATOR_MARKER

EXPECTED_INPUT_PR154_TOTAL_RECORDS = 342
EXPECTED_MATERIALIZED_RECORDS = 230
EXPECTED_BLOCKED_RECORDS = 112
EXPECTED_OFFICIAL_SOURCE_MATERIALIZED_DEFAULTS = 92
EXPECTED_OWNER_INTERNAL_CONTROL_PLANE_DEFAULTS = 138
EXPECTED_ZERO_AUTHORITY_COUNT = 0

PR154_ALLOWED_AUTHORITY_CLASSES = (
    pr154_tx.AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE,
    pr154_tx.AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT,
)
PR154_OFFICIAL_SOURCE_AUTHORITY_CLASSES = (
    pr154_tx.AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE,
)
PR154_OWNER_INTERNAL_AUTHORITY_CLASSES = (
    pr154_tx.AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT,
)
PR154_ALLOWED_MATERIALIZATION_DECISIONS = (
    pr154_tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE,
    pr154_tx.MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT,
)
PR154_BLOCKED_AUTHORITY_CLASS = pr154_tx.AUTHORITY_BLOCKED

ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
ROADMAP_EXECUTION_STATE_PATH = Path(
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
)
LAUNCH_READINESS_ROADMAP_PATH = Path(
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
)
LAUNCH_READINESS_POLICY_PATH = Path(
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap_policy.py"
)
PR136_ROUTE_TRIAGE_PATH = Path(
    "docs/master_plan/generated/PR136RouteTriage.report.json"
)
PR136_SECTION_CROSSWALK_ALIAS_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_SUCCESSOR_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)
PR136_MARKET_INDEX_PATH = Path(
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
)
PR136_COMMAND_MATRIX_PATH = Path(
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json"
)
PR137R_RECONCILIATION_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR138_SEMANTIC_CONTRACT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)

MANDATORY_ORCHESTRATION_ARTIFACT_PATHS = (
    ROSTER_PATH,
    ROADMAP_EXECUTION_STATE_PATH,
    LAUNCH_READINESS_ROADMAP_PATH,
    LAUNCH_READINESS_POLICY_PATH,
    PR136_ROUTE_TRIAGE_PATH,
    PR136_MARKET_INDEX_PATH,
    PR136_COMMAND_MATRIX_PATH,
    PR137R_RECONCILIATION_PATH,
    PR138_SEMANTIC_CONTRACT_PATH,
)
ORCHESTRATION_ENRICHMENT_ARTIFACT_KEYS = (
    "pr_identity_roster",
    "roadmap_execution_state",
    "launch_readiness_roadmap",
    "launch_readiness_policy",
    "route_triage",
    "section_crosswalk_or_successor",
    "market_specific_index",
    "command_action_matrix",
    "atomicrows_reconciliation",
    "atomicrows_semantic_contract",
)

REGISTRY_READY_NONLIVE = "REGISTRY_DEFAULT_READY_NONLIVE"
REGISTRY_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING = (
    "REGISTRY_DEFAULT_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING"
)
REGISTRY_READY_NONLIVE_EXPLICIT_AGENT_BINDING = (
    "REGISTRY_DEFAULT_READY_NONLIVE_EXPLICIT_AGENT_BINDING"
)
NON_CONSUMABLE_BLOCKED_PR154_INCOMPLETE = "NON_CONSUMABLE_BLOCKED_PR154_INCOMPLETE"
NON_CONSUMABLE_BLOCKED_AUTHORITY_MISSING = "NON_CONSUMABLE_BLOCKED_AUTHORITY_MISSING"
NON_CONSUMABLE_BLOCKED_VALUE_MISSING = "NON_CONSUMABLE_BLOCKED_VALUE_MISSING"
NON_CONSUMABLE_BLOCKED_PROVENANCE_MISSING = "NON_CONSUMABLE_BLOCKED_PROVENANCE_MISSING"
NON_CONSUMABLE_BLOCKED_ORCHESTRATION_PRECHECK = (
    "NON_CONSUMABLE_BLOCKED_ORCHESTRATION_PRECHECK"
)
NON_CONSUMABLE_BLOCKED_ATOMICROWS_ALIGNMENT = (
    "NON_CONSUMABLE_BLOCKED_ATOMICROWS_ALIGNMENT"
)
NON_CONSUMABLE_BLOCKED_SCHEMA_INVALID = "NON_CONSUMABLE_BLOCKED_SCHEMA_INVALID"
NON_CONSUMABLE_BLOCKED_AMBIGUOUS = "NON_CONSUMABLE_BLOCKED_AMBIGUOUS"
REGISTRY_CONSUMPTION_STATES = (
    REGISTRY_READY_NONLIVE,
    REGISTRY_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING,
    REGISTRY_READY_NONLIVE_EXPLICIT_AGENT_BINDING,
    NON_CONSUMABLE_BLOCKED_PR154_INCOMPLETE,
    NON_CONSUMABLE_BLOCKED_AUTHORITY_MISSING,
    NON_CONSUMABLE_BLOCKED_VALUE_MISSING,
    NON_CONSUMABLE_BLOCKED_PROVENANCE_MISSING,
    NON_CONSUMABLE_BLOCKED_ORCHESTRATION_PRECHECK,
    NON_CONSUMABLE_BLOCKED_ATOMICROWS_ALIGNMENT,
    NON_CONSUMABLE_BLOCKED_SCHEMA_INVALID,
    NON_CONSUMABLE_BLOCKED_AMBIGUOUS,
)

AGENT_ASSIGNMENT_NOT_REQUIRED = "AGENT_ASSIGNMENT_NOT_REQUIRED_FOR_REGISTRY_DEFAULT"
AGENT_ASSIGNMENT_PENDING = "AGENT_ASSIGNMENT_PENDING_DOWNSTREAM_BINDING"
EXPLICIT_AGENT_ALLOWLIST_BOUND = "EXPLICIT_AGENT_ALLOWLIST_BOUND"
AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING = (
    "AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING"
)
AGENT_ASSIGNMENT_BLOCKED_AMBIGUOUS = "AGENT_ASSIGNMENT_BLOCKED_AMBIGUOUS"
AGENT_ASSIGNMENT_STATES = (
    AGENT_ASSIGNMENT_NOT_REQUIRED,
    AGENT_ASSIGNMENT_PENDING,
    EXPLICIT_AGENT_ALLOWLIST_BOUND,
    AGENT_ASSIGNMENT_BLOCKED_MISSING_BINDING,
    AGENT_ASSIGNMENT_BLOCKED_AMBIGUOUS,
)

NONLIVE_OFFICIAL_SOURCE_MATERIALIZED_DEFAULT = (
    "NONLIVE_OFFICIAL_SOURCE_MATERIALIZED_DEFAULT"
)
NONLIVE_OWNER_INTERNAL_POLICY_DEFAULT = "NONLIVE_OWNER_INTERNAL_POLICY_DEFAULT"
NONLIVE_CONTROL_PLANE_METADATA_DEFAULT = "NONLIVE_CONTROL_PLANE_METADATA_DEFAULT"
NONLIVE_REGISTRY_DEFAULT_PENDING_AGENT_ASSIGNMENT = (
    "NONLIVE_REGISTRY_DEFAULT_PENDING_AGENT_ASSIGNMENT"
)
NONCONSUMABLE_BLOCKED_RECORD = "NONCONSUMABLE_BLOCKED_RECORD"
DEFAULT_USE_CLASSES = (
    NONLIVE_OFFICIAL_SOURCE_MATERIALIZED_DEFAULT,
    NONLIVE_OWNER_INTERNAL_POLICY_DEFAULT,
    NONLIVE_CONTROL_PLANE_METADATA_DEFAULT,
    NONLIVE_REGISTRY_DEFAULT_PENDING_AGENT_ASSIGNMENT,
    NONCONSUMABLE_BLOCKED_RECORD,
)

MATERIALIZATION_LANES = (
    "MATERIALIZATION_ROUTE_INTERNAL_OWNER_POLICY_REQUIRED",
    "MATERIALIZATION_ROUTE_OFFICIAL_SOURCE_CANDIDATE_FAST_LANE",
    "MATERIALIZATION_ROUTE_PR153R_RETRY_REQUIRED",
    "MATERIALIZATION_ROUTE_SPLIT_OR_RECLASSIFICATION_REQUIRED",
    "MATERIALIZATION_ROUTE_PRIVATE_DOC_ATTESTATION_REQUIRED",
    "MATERIALIZATION_ROUTE_OWNER_PROVIDED_ROUTE_REQUIRED",
    *pr154_tx.MATERIALIZATION_DECISIONS,
)

ATOMICROWS_COMPATIBLE_PR154_MATERIALIZED_DEFAULT = (
    "ATOMICROWS_COMPATIBLE_PR154_MATERIALIZED_DEFAULT"
)
ATOMICROWS_COMPATIBLE_PARTIAL_ORCHESTRATION = (
    "ATOMICROWS_COMPATIBLE_WITH_PARTIAL_ORCHESTRATION_METADATA"
)
ATOMICROWS_BLOCKED_PR154_INCOMPLETE = "ATOMICROWS_BLOCKED_PR154_INCOMPLETE"
ATOMICROWS_BLOCKED_SEMANTIC_CONTRACT_MISSING = (
    "ATOMICROWS_BLOCKED_SEMANTIC_CONTRACT_MISSING"
)
ATOMICROWS_BLOCKED_RECONCILIATION_MISSING = (
    "ATOMICROWS_BLOCKED_RECONCILIATION_MISSING"
)
ATOMICROWS_NOT_BUNDLE_AUTHORITY = "ATOMICROWS_NOT_BUNDLE_AUTHORITY"
ATOMICROWS_COMPATIBILITY_STATES = (
    ATOMICROWS_COMPATIBLE_PR154_MATERIALIZED_DEFAULT,
    ATOMICROWS_COMPATIBLE_PARTIAL_ORCHESTRATION,
    ATOMICROWS_BLOCKED_PR154_INCOMPLETE,
    ATOMICROWS_BLOCKED_SEMANTIC_CONTRACT_MISSING,
    ATOMICROWS_BLOCKED_RECONCILIATION_MISSING,
    ATOMICROWS_NOT_BUNDLE_AUTHORITY,
)

QUANTUM_FORWARD_METADATA_READY_NOT_EXECUTION = (
    "QUANTUM_FORWARD_METADATA_READY_NOT_EXECUTION"
)
QUANTUM_FORWARD_METADATA_PARTIAL_NOT_EXECUTION = (
    "QUANTUM_FORWARD_METADATA_PARTIAL_NOT_EXECUTION"
)
QUANTUM_FORWARD_METADATA_BLOCKED_MISSING_CLASSIFICATION = (
    "QUANTUM_FORWARD_METADATA_BLOCKED_MISSING_CLASSIFICATION"
)
QUANTUM_NOT_APPLICABLE_CLASSICAL_ONLY = "QUANTUM_NOT_APPLICABLE_CLASSICAL_ONLY"
QUANTUM_EXECUTION_FORBIDDEN_IN_PR155 = "QUANTUM_EXECUTION_FORBIDDEN_IN_PR155"
QUANTUM_FORWARD_COMPATIBILITY_STATES = (
    QUANTUM_FORWARD_METADATA_READY_NOT_EXECUTION,
    QUANTUM_FORWARD_METADATA_PARTIAL_NOT_EXECUTION,
    QUANTUM_FORWARD_METADATA_BLOCKED_MISSING_CLASSIFICATION,
    QUANTUM_NOT_APPLICABLE_CLASSICAL_ONLY,
    QUANTUM_EXECUTION_FORBIDDEN_IN_PR155,
)

OPTIMIZER_METADATA_READY_NOT_EXECUTION = "OPTIMIZER_METADATA_READY_NOT_EXECUTION"
OPTIMIZER_METADATA_PARTIAL_NOT_EXECUTION = "OPTIMIZER_METADATA_PARTIAL_NOT_EXECUTION"
OPTIMIZER_METADATA_MISSING = "OPTIMIZER_METADATA_MISSING"
OPTIMIZER_EXECUTION_FORBIDDEN_IN_PR155 = "OPTIMIZER_EXECUTION_FORBIDDEN_IN_PR155"
OPTIMIZER_READINESS_HINTS = (
    OPTIMIZER_METADATA_READY_NOT_EXECUTION,
    OPTIMIZER_METADATA_PARTIAL_NOT_EXECUTION,
    OPTIMIZER_METADATA_MISSING,
    OPTIMIZER_EXECUTION_FORBIDDEN_IN_PR155,
)

CONTROL_PLANE_NONLIVE_METADATA_ONLY = "CONTROL_PLANE_NONLIVE_METADATA_ONLY"
LOW_LATENCY_LIVE_PATH_NOT_CREATED = "LOW_LATENCY_LIVE_PATH_NOT_CREATED"
LATENCY_METADATA_READY_FOR_FUTURE_ROUTING = (
    "LATENCY_METADATA_READY_FOR_FUTURE_ROUTING"
)
LATENCY_METADATA_MISSING = "LATENCY_METADATA_MISSING"
LATENCY_PATH_STATES = (
    CONTROL_PLANE_NONLIVE_METADATA_ONLY,
    LOW_LATENCY_LIVE_PATH_NOT_CREATED,
    LATENCY_METADATA_READY_FOR_FUTURE_ROUTING,
    LATENCY_METADATA_MISSING,
)

LAUNCH_READINESS_PLACEMENT_ENUMS = (
    *day1_policy.READINESS_STATE_CLASSES,
    "PR155_MAPPING_UNKNOWN_NO_EXACT_RECORD_LEVEL_PR136_DOMAIN",
    "PR155_ORCHESTRATION_PRECHECK_BLOCKED",
)

PR155_READY = "PR155_READY"
PR155_PR154_INPUT_MISSING = "PR155_PR154_INPUT_MISSING"
PR155_PR154_INPUT_AMBIGUOUS = "PR155_PR154_INPUT_AMBIGUOUS"
PR155_PR154_INPUT_INVALID = "PR155_PR154_INPUT_INVALID"
PR155_PR154_COUNT_MISMATCH = "PR155_PR154_COUNT_MISMATCH"
PR155_PR154_RECORD_ID_DUPLICATE = "PR155_PR154_RECORD_ID_DUPLICATE"
PR155_ORCHESTRATION_ARTIFACT_MISSING = "PR155_ORCHESTRATION_ARTIFACT_MISSING"
PR155_ORCHESTRATION_ARTIFACT_INVALID = "PR155_ORCHESTRATION_ARTIFACT_INVALID"
PR155_ORCHESTRATION_CROSSWALK_MISSING = "PR155_ORCHESTRATION_CROSSWALK_MISSING"
PR155_RECORD_SCHEMA_INVALID = "PR155_RECORD_SCHEMA_INVALID"
PR155_READY_RECORD_VALUE_MISSING = "PR155_READY_RECORD_VALUE_MISSING"
PR155_READY_RECORD_AUTHORITY_INVALID = "PR155_READY_RECORD_AUTHORITY_INVALID"
PR155_READY_RECORD_PROVENANCE_MISSING = "PR155_READY_RECORD_PROVENANCE_MISSING"
PR155_BLOCKED_COMPLETION_PATH_INCOMPLETE = (
    "PR155_BLOCKED_COMPLETION_PATH_INCOMPLETE"
)
PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE = "PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE"
PR155_QTT_SHA_AUTHORITY_CREATED = "PR155_QTT_SHA_AUTHORITY_CREATED"
PR155_ATOMICROWS_BUNDLE_AUTHORITY_CREATED = (
    "PR155_ATOMICROWS_BUNDLE_AUTHORITY_CREATED"
)
PR155_FORBIDDEN_ARTIFACT_REFERENCE_CREATED = (
    "PR155_FORBIDDEN_ARTIFACT_REFERENCE_CREATED"
)
PR155_REPORT_STALE_OR_NONDETERMINISTIC = "PR155_REPORT_STALE_OR_NONDETERMINISTIC"
PR155_REGISTRY_STALE_OR_NONDETERMINISTIC = (
    "PR155_REGISTRY_STALE_OR_NONDETERMINISTIC"
)
PR155_CHANGED_PATH_OUT_OF_SCOPE = "PR155_CHANGED_PATH_OUT_OF_SCOPE"
PR155_GIT_STATUS_UNAVAILABLE = "PR155_GIT_STATUS_UNAVAILABLE"
PR155_MASTER_PLAN_MUTATION_DETECTED = "PR155_MASTER_PLAN_MUTATION_DETECTED"
PR155_ATOMICROWS_BUNDLE_MUTATION_DETECTED = (
    "PR155_ATOMICROWS_BUNDLE_MUTATION_DETECTED"
)
BLOCK_CODES = (
    PR155_READY,
    PR155_PR154_INPUT_MISSING,
    PR155_PR154_INPUT_AMBIGUOUS,
    PR155_PR154_INPUT_INVALID,
    PR155_PR154_COUNT_MISMATCH,
    PR155_PR154_RECORD_ID_DUPLICATE,
    PR155_ORCHESTRATION_ARTIFACT_MISSING,
    PR155_ORCHESTRATION_ARTIFACT_INVALID,
    PR155_ORCHESTRATION_CROSSWALK_MISSING,
    PR155_RECORD_SCHEMA_INVALID,
    PR155_READY_RECORD_VALUE_MISSING,
    PR155_READY_RECORD_AUTHORITY_INVALID,
    PR155_READY_RECORD_PROVENANCE_MISSING,
    PR155_BLOCKED_COMPLETION_PATH_INCOMPLETE,
    PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE,
    PR155_QTT_SHA_AUTHORITY_CREATED,
    PR155_ATOMICROWS_BUNDLE_AUTHORITY_CREATED,
    PR155_FORBIDDEN_ARTIFACT_REFERENCE_CREATED,
    PR155_REPORT_STALE_OR_NONDETERMINISTIC,
    PR155_REGISTRY_STALE_OR_NONDETERMINISTIC,
    PR155_CHANGED_PATH_OUT_OF_SCOPE,
    PR155_GIT_STATUS_UNAVAILABLE,
    PR155_MASTER_PLAN_MUTATION_DETECTED,
    PR155_ATOMICROWS_BUNDLE_MUTATION_DETECTED,
)

RECORD_ALWAYS_FALSE_FIELDS = (
    "live_order_ready_flag",
    "runtime_ready_flag",
    "connector_semantic_bound_flag",
    "replay_tested_flag",
    "paper_approved_flag",
    "quantum_execution_evidence_flag",
    "profit_evidence_flag",
)
REPORT_FALSE_AUTHORITY_FIELDS = (
    "qtt_sha_authority_created",
    "qtt_generated_sha_created",
    "qtt_freeze_checksum_global_digest_authority_created",
    "atomicrows_bundle_created",
    "atomicrows_bundle_sha_or_hash_authority_created",
)
FORBIDDEN_CREATED_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_binding_created",
    "runtime_private_state_receipt_created",
    "runtime_cash_receipt_created",
    "replay_result_created",
    "paper_result_created",
    "optimizer_backend_execution_created",
    "quantum_advantage_claim_created",
    "profit_evidence_created",
    "latency_superiority_evidence_created",
    "execution_superiority_evidence_created",
    *REPORT_FALSE_AUTHORITY_FIELDS,
)
NON_AUTHORITY_BOUNDARY_FLAGS = {
    field: False for field in FORBIDDEN_CREATED_FIELDS
}
ALLOWED_SOURCE_EVIDENCE_PROVENANCE_DIGEST_KEYS = (
    "retrieval_artifact_digest",
    "source_packet_integrity_digest",
)

NONLIVE_REGISTRY_REASON = (
    "PR155_NONLIVE_REGISTRY_DEFAULT_NOT_RUNTIME_NOT_CONNECTOR_NOT_REPLAY_NOT_PAPER_"
    "NOT_ORDER_NOT_PROFIT"
)
NONLIVE_PENDING_AGENT_BINDING_REASON = (
    "PR155_REGISTRY_READY_PENDING_FUTURE_AGENT_BINDING_NOT_DIRECT_ASSIGNMENT"
)
NONLIVE_BLOCKED_PR154_REASON = "PR155_BLOCKED_PR154_INCOMPLETE_NONCONSUMABLE"
ALLOWED_NO_LIVE_REASON_CODES = (
    NONLIVE_REGISTRY_REASON,
    NONLIVE_PENDING_AGENT_BINDING_REASON,
    NONLIVE_BLOCKED_PR154_REASON,
)

ELIGIBLE_AGENT_BASIS_PENDING = (
    "REGISTRY_DEFAULT_READY_PENDING_FUTURE_AGENT_BINDING"
)
FORBIDDEN_AGENT_BASIS_UNDECLARED = (
    "NO_FORBIDDEN_AGENT_LIST_DECLARED_IN_CONSUMED_ARTIFACTS"
)
DIRECT_AGENT_BINDING_PENDING_BLOCK_CODE = (
    "PR155_DIRECT_AGENT_BINDING_PENDING_DOWNSTREAM"
)
NO_EXACT_PR136_RECORD_MAPPING = (
    "PR155_MAPPING_UNKNOWN_NO_EXACT_RECORD_LEVEL_PR136_DOMAIN"
)
FUTURE_REPLAY_PAPER_PLACEMENT_HINT = (
    "FUTURE_REPLAY_PAPER_PLACEMENT_REQUIRES_PR156_PR157_EVIDENCE"
)
FUTURE_LIVE_TRANSITION_BLOCK_REASON = (
    "FUTURE_LIVE_TRANSITION_BLOCKED_NO_CONNECTOR_RUNTIME_REPLAY_PAPER_OWNER_LIVE_GATE"
)
RISK_METADATA_NOT_EXPLICIT = "PR155_RISK_METADATA_NOT_EXPLICIT_IN_PR154"
LATENCY_METADATA_NOT_EXPLICIT = "PR155_LATENCY_METADATA_NOT_EXPLICIT_IN_PR154"
NO_EXPLICIT_QUANTUM_STRATEGY_TAGS = (
    "PR155_NO_EXPLICIT_QUANTUM_STRATEGY_COMPATIBILITY_TAGS_IN_CONSUMED_ARTIFACTS"
)

REGISTRY_TOP_LEVEL_KEYS = (
    "registry_type",
    "pr_id",
    "semantic_task_id",
    "authority_class",
    "input_pr154_artifact",
    "control_plane_preflight",
    "counts",
    "records",
    "blocked_records",
    "non_authority_boundary",
    "validation_result",
)
REPORT_TOP_LEVEL_KEYS = (
    "report_type",
    "pr_id",
    "semantic_task_id",
    "authority_class",
    "input_pr154_total_records",
    "agent_consumable_default_ready_count",
    "direct_agent_assignment_ready_count",
    "agent_assignment_pending_count",
    "non_consumable_blocked_count",
    "official_source_materialized_default_count",
    "owner_internal_control_plane_default_count",
    "live_order_ready_count",
    "runtime_ready_count",
    "connector_semantic_bound_count",
    "replay_tested_count",
    "paper_approved_count",
    "quantum_execution_evidence_count",
    "profit_evidence_count",
    "qtt_sha_authority_created",
    "qtt_generated_sha_created",
    "qtt_freeze_checksum_global_digest_authority_created",
    "atomicrows_bundle_created",
    "atomicrows_bundle_sha_or_hash_authority_created",
    "control_plane_preflight",
    "orchestration_alignment_summary",
    "market_specific_readiness_summary",
    "atomicrows_compatibility_summary",
    "quantum_forward_compatibility_summary",
    "agent_registry_summary",
    "blocked_completion_path_summary",
    "determinism_metadata_without_runtime_git_volatility",
    "validation_result",
)

RECORD_REQUIRED_FIELDS = (
    "registry_record_id",
    "source_pr154_record_id",
    "source_target_id_or_atomic_row_id",
    "source_materialization_lane",
    "source_authority_class",
    "value",
    "value_type",
    "unit_or_basis",
    "scale",
    "source_value_status",
    "default_use_class",
    "registry_consumption_state",
    "agent_assignment_state",
    "agent_consumable_default_ready_flag",
    "direct_agent_assignment_ready_flag",
    *RECORD_ALWAYS_FALSE_FIELDS,
    "source_packet_path_or_null",
    "source_candidate_packet_id_or_null",
    "official_url_or_null",
    "quote_span_or_machine_field_locator_or_null",
    "owner_internal_policy_basis_or_null",
    "eligible_agent_ids",
    "eligible_agent_basis",
    "forbidden_agent_ids",
    "forbidden_agent_basis",
    "agent_binding_block_codes",
    "decision_family_scope",
    "allowed_profile_bundle_ids",
    "market_scope",
    "platform_scope",
    "launch_readiness_domain",
    "route_triage_domain",
    "section_crosswalk_refs",
    "market_specific_index_refs",
    "command_action_matrix_refs",
    "atomicrows_reconciliation_refs",
    "atomicrows_semantic_contract_refs",
    "atomicrows_compatibility_state",
    "quantum_forward_compatibility_state",
    "quantum_applicability_hint",
    "quantum_strategy_compatibility_tags",
    "optimizer_readiness_hint",
    "latency_path_state",
    "latency_sensitivity_hint",
    "risk_sensitivity_hint",
    "consumer_gate_block_codes",
    "non_live_reason",
    "blocked_completion_path_if_any",
    "created_by_pr",
    "authority_boundary",
)
COMPLETION_PATH_FIELDS = (
    "missing_fields",
    "required_next_task",
    "required_next_pr_or_phase",
    "responsible_authority",
    "required_input_artifact",
    "exact_unblock_condition",
    "materialization_retry_route",
    "codex_actionable_completion_steps",
)

MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ATOMICROWS_BUNDLE_SIDE_CAR_SUFFIX_PARTS = ("sha", "256")
FORBIDDEN_ATOMICROWS_BUNDLE_STEM = "AtomicRows.bundle"

CHANGED_PATHS = (
    REGISTRY_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/__init__.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/constants.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/models.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/input_discovery.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/orchestration_preflight.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/mapper.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/builder.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/validator.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/report.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/schema_projection.py",
    "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/io.py",
    "tools/validate_agent_consumable_parameter_default_registry.py",
    "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/tools/test_ci_branch_context.py",
)
