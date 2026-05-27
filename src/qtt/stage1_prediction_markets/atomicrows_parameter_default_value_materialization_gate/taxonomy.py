"""Central PR154 taxonomy for candidate acceptance and materialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SEMANTIC_PR_LABEL = "PR154"
REPORT_ID = "QTT_PR154_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_GATE_REPORT"
VALIDATOR_MARKER = "QTT_PR154_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_GATE_OK"
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json"
)
TAXONOMY_MODULE_PATH = (
    "src/qtt/stage1_prediction_markets/"
    "atomicrows_parameter_default_value_materialization_gate/taxonomy.py"
)
PURPOSE = (
    "Deterministically bridge PR153S closure records into an AtomicRows-compatible "
    "PR154 materialization ledger by accepting complete official-source candidates, "
    "owner-authorizing safe internal control-plane policy defaults, and fail-closing "
    "all still-incomplete routes with exact completion paths."
)

PR154_BRANCH = "pr154-atomicrows-parameter-default-value-materialization-gate"

ORCHESTRATION_ARTIFACT_PATHS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    Path("docs/master_plan/generated/PR136RouteTriage.report.json"),
    Path("docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"),
    Path("docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"),
    Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
)

SOURCE_VALUE_ARTIFACT_PATHS = (
    Path("docs/master_plan/generated/PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"),
    Path("docs/master_plan/generated/PR151_OfficialSourceRetrievalTargetPackParameterDefaults.report.json"),
    Path("docs/master_plan/generated/PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"),
    Path("docs/master_plan/generated/PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json"),
    Path("docs/master_plan/generated/PR153R_RedoExternalSourceValueCaptureTargets.report.json"),
    Path("docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json"),
    Path("docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"),
)

VALIDATOR_AND_MODULE_CONTEXT_PATHS = (
    Path("tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py"),
    Path("tools/validate_official_source_retrieval_target_pack_parameter_defaults.py"),
    Path("tools/validate_controlled_official_source_capture_candidate_packets.py"),
    Path("tools/validate_pr153r_redo_external_source_value_capture_targets.py"),
    Path("tools/validate_pr153s_source_value_capture_closure_classifier.py"),
    Path("tools/validate_grand_global_debug_logical_consistency_audit.py"),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "pr153s_source_value_capture_closure_classifier"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit"
    ),
)

QUANTUM_FORWARD_ARTIFACT_PATHS = (
    Path("docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json"),
    Path("docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json"),
    Path("docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json"),
    Path("docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"),
    Path("docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json"),
    Path("tools/validate_quantum_applicability_classification_registry.py"),
    Path("tools/validate_owner_quantum_priority_policy_registry.py"),
    Path("tools/validate_parameter_algorithm_scoring_policy_registry.py"),
    Path("tools/validate_parameter_stack_scoring_and_ranking_gate.py"),
    Path("tools/validate_quantum_classical_optimizer_arbitration_gate.py"),
)

CONSUMED_ARTIFACT_PATHS = (
    *ORCHESTRATION_ARTIFACT_PATHS,
    *SOURCE_VALUE_ARTIFACT_PATHS,
    *VALIDATOR_AND_MODULE_CONTEXT_PATHS,
    *QUANTUM_FORWARD_ARTIFACT_PATHS,
)

CHANGED_PATHS = (
    REPORT_PATH.as_posix(),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/__init__.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/inputs.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/materializer.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/report.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/taxonomy.py"
    ),
    (
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/validator.py"
    ),
    "tools/validate_atomicrows_parameter_default_value_materialization_gate.py",
    "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    (
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
    ),
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/tools/test_ci_branch_context.py",
)

ACCEPTANCE_OWNER_FAST_LANE = (
    "OWNER_APPROVED_ACCEPTED_SOURCE_VALUE_FOR_PR154_MATERIALIZATION"
)
ACCEPTANCE_EXISTING_ACCEPTED_SOURCE = "EXISTING_ACCEPTED_SOURCE_PACKET_VALUE"
ACCEPTANCE_OWNER_INTERNAL_POLICY = "OWNER_APPROVED_INTERNAL_QTT_POLICY_VALUE"
ACCEPTANCE_INTERNAL_ARCHITECTURE = "EXISTING_INTERNAL_ARCHITECTURE_VALUE"
ACCEPTANCE_BLOCKED = "BLOCKED_NO_VALUE_AUTHORITY"

ACCEPTANCE_DECISIONS = (
    ACCEPTANCE_OWNER_FAST_LANE,
    ACCEPTANCE_EXISTING_ACCEPTED_SOURCE,
    ACCEPTANCE_OWNER_INTERNAL_POLICY,
    ACCEPTANCE_INTERNAL_ARCHITECTURE,
    ACCEPTANCE_BLOCKED,
)

MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE = (
    "ACCEPTED_AND_MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE"
)
MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE = (
    "MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE"
)
MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT = (
    "MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT"
)
MATERIALIZED_INTERNAL_ARCHITECTURE_VALUE = "MATERIALIZED_INTERNAL_ARCHITECTURE_VALUE"
BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE = (
    "BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE"
)
BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET = "BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET"
BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW = (
    "BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW"
)
BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION = (
    "BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION"
)
BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION = (
    "BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION"
)
BLOCKED_PENDING_OWNER_ROUTE_PACKET = "BLOCKED_PENDING_OWNER_ROUTE_PACKET"
BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE = (
    "BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE"
)
BLOCKED_PENDING_RUNTIME_RECEIPT = "BLOCKED_PENDING_RUNTIME_RECEIPT"
BLOCKED_PENDING_REPLAY_PAPER_REVIEW = "BLOCKED_PENDING_REPLAY_PAPER_REVIEW"
BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE = (
    "BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE"
)
BLOCKED_UNKNOWN_FAIL_CLOSED = "BLOCKED_UNKNOWN_FAIL_CLOSED"

MATERIALIZATION_DECISIONS = (
    MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE,
    MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE,
    MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT,
    MATERIALIZED_INTERNAL_ARCHITECTURE_VALUE,
    BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE,
    BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET,
    BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW,
    BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION,
    BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION,
    BLOCKED_PENDING_OWNER_ROUTE_PACKET,
    BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE,
    BLOCKED_PENDING_RUNTIME_RECEIPT,
    BLOCKED_PENDING_REPLAY_PAPER_REVIEW,
    BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE,
    BLOCKED_UNKNOWN_FAIL_CLOSED,
)

MISSING_CAPTURED_VALUE = "MISSING_CAPTURED_VALUE"
MISSING_UNIT_OR_SCALE = "MISSING_UNIT_OR_SCALE"
MISSING_TARGET_FIELD_MATCH = "MISSING_TARGET_FIELD_MATCH"
MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR = (
    "MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR"
)
MISSING_OFFICIAL_SOURCE_LOCATOR = "MISSING_OFFICIAL_SOURCE_LOCATOR"
MISSING_OFFICIAL_SOURCE_AUTHORITY_CLASS = "MISSING_OFFICIAL_SOURCE_AUTHORITY_CLASS"
CONFLICT_REVIEW_REQUIRED = "CONFLICT_REVIEW_REQUIRED"
SPLIT_RECLASSIFICATION_REQUIRED = "SPLIT_RECLASSIFICATION_REQUIRED"
PRIVATE_DOC_ATTESTATION_REQUIRED = "PRIVATE_DOC_ATTESTATION_REQUIRED"
OWNER_ROUTE_LOCATOR_REQUIRED = "OWNER_ROUTE_LOCATOR_REQUIRED"
RUNTIME_RECEIPT_REQUIRED = "RUNTIME_RECEIPT_REQUIRED"
REPLAY_PAPER_EVIDENCE_REQUIRED = "REPLAY_PAPER_EVIDENCE_REQUIRED"
QUANTUM_EXECUTION_EVIDENCE_REQUIRED = "QUANTUM_EXECUTION_EVIDENCE_REQUIRED"
INTERNAL_OWNER_POLICY_VALUE_REQUIRED = "INTERNAL_OWNER_POLICY_VALUE_REQUIRED"

MISSING_FIELD_CODES = (
    MISSING_CAPTURED_VALUE,
    MISSING_UNIT_OR_SCALE,
    MISSING_TARGET_FIELD_MATCH,
    MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR,
    MISSING_OFFICIAL_SOURCE_LOCATOR,
    MISSING_OFFICIAL_SOURCE_AUTHORITY_CLASS,
    CONFLICT_REVIEW_REQUIRED,
    SPLIT_RECLASSIFICATION_REQUIRED,
    PRIVATE_DOC_ATTESTATION_REQUIRED,
    OWNER_ROUTE_LOCATOR_REQUIRED,
    RUNTIME_RECEIPT_REQUIRED,
    REPLAY_PAPER_EVIDENCE_REQUIRED,
    QUANTUM_EXECUTION_EVIDENCE_REQUIRED,
    INTERNAL_OWNER_POLICY_VALUE_REQUIRED,
)

VALUE_TYPE_NONE = "NONE"
VALUE_TYPE_SOURCE_TEXT_LITERAL = "SOURCE_TEXT_LITERAL"
VALUE_TYPE_OWNER_INTERNAL_POLICY_STATUS = "OWNER_INTERNAL_POLICY_STATUS_LABEL"
VALUE_TYPE_INTERNAL_ARCHITECTURE = "INTERNAL_ARCHITECTURE_VALUE"

VALUE_TYPES = (
    VALUE_TYPE_NONE,
    VALUE_TYPE_SOURCE_TEXT_LITERAL,
    VALUE_TYPE_OWNER_INTERNAL_POLICY_STATUS,
    VALUE_TYPE_INTERNAL_ARCHITECTURE,
)

VALUE_UNIT_NONE = "NONE"
VALUE_SCALE_NONE = "NONE"
VALUE_UNIT_SOURCE_TEXT_LITERAL = "SOURCE_TEXT_LITERAL_NO_NUMERIC_UNIT_MATERIALIZED"
VALUE_SCALE_SOURCE_TEXT_LITERAL = "SOURCE_TEXT_LITERAL_NO_NUMERIC_SCALE_MATERIALIZED"
VALUE_UNIT_INTERNAL_POLICY_STATUS = "NOT_APPLICABLE_INTERNAL_POLICY_STATUS"
VALUE_SCALE_INTERNAL_POLICY_STATUS = "NOT_APPLICABLE_INTERNAL_POLICY_STATUS"

VALUE_SOURCE_NONE = "NONE"
VALUE_SOURCE_COMPLETE_OFFICIAL_SOURCE_CANDIDATE_FAST_LANE = (
    "COMPLETE_OFFICIAL_SOURCE_CANDIDATE_ACCEPTED_BY_PR154_FAST_LANE"
)
VALUE_SOURCE_EXISTING_ACCEPTED_SOURCE_PACKET = "EXISTING_ACCEPTED_SOURCE_PACKET"
VALUE_SOURCE_OWNER_INTERNAL_POLICY_DEFAULT = (
    "PR154_OWNER_AUTHORIZED_INTERNAL_POLICY_DEFAULT"
)
VALUE_SOURCE_INTERNAL_ARCHITECTURE = "EXISTING_CANONICAL_INTERNAL_ARCHITECTURE_VALUE"

VALUE_SOURCE_CLASSES = (
    VALUE_SOURCE_NONE,
    VALUE_SOURCE_COMPLETE_OFFICIAL_SOURCE_CANDIDATE_FAST_LANE,
    VALUE_SOURCE_EXISTING_ACCEPTED_SOURCE_PACKET,
    VALUE_SOURCE_OWNER_INTERNAL_POLICY_DEFAULT,
    VALUE_SOURCE_INTERNAL_ARCHITECTURE,
)

AUTHORITY_BLOCKED = "BLOCKED"
AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE = (
    "OWNER_APPROVED_PR154_FAST_LANE_OFFICIAL_SOURCE_VALUE_NOT_CONNECTOR_NOT_LIVE"
)
AUTHORITY_EXISTING_ACCEPTED_SOURCE_PACKET = (
    "EXISTING_ACCEPTED_SOURCE_PACKET_VALUE_AUTHORITY"
)
AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT = (
    "OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT_NOT_EXTERNAL_FACT"
)
AUTHORITY_INTERNAL_ARCHITECTURE = "EXISTING_INTERNAL_ARCHITECTURE_NOT_EXTERNAL_FACT"

AUTHORITY_CLASSES = (
    AUTHORITY_BLOCKED,
    AUTHORITY_OFFICIAL_SOURCE_PR154_FAST_LANE,
    AUTHORITY_EXISTING_ACCEPTED_SOURCE_PACKET,
    AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT,
    AUTHORITY_INTERNAL_ARCHITECTURE,
)

AUTHORITY_REF_OWNER_OFFICIAL_FAST_LANE = (
    "OWNER_GLOBAL_OVERRIDE_PR154_COMPLETE_OFFICIAL_SOURCE_CANDIDATE_ACCEPTANCE_FAST_LANE"
)
AUTHORITY_REF_OWNER_INTERNAL_POLICY = (
    "OWNER_GLOBAL_OVERRIDE_PR154_INTERNAL_CONTROL_PLANE_POLICY_DEFAULT_FAST_LANE"
)

OWNER_INTERNAL_POLICY_DEFAULT_KEY = (
    "PR154_OWNER_INTERNAL_POLICY_DEFAULT_FAIL_CLOSED_METADATA_ONLY"
)
OWNER_INTERNAL_POLICY_DEFAULT_VALUE = (
    "OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT__FAIL_CLOSED_CONTROL_PLANE_METADATA_ONLY"
)
OWNER_INTERNAL_POLICY_DEFAULT_SOURCE_FIELD = (
    "OWNER_INTERNAL_POLICY_DEFAULTS."
    "PR154_OWNER_INTERNAL_POLICY_DEFAULT_FAIL_CLOSED_METADATA_ONLY"
)
OWNER_INTERNAL_POLICY_DEFAULT_LOGIC = (
    "All PR153S internal/control-plane targets receive the exact owner-approved "
    "status label OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT__FAIL_CLOSED_"
    "CONTROL_PLANE_METADATA_ONLY. The value is an internal policy status, not an "
    "external fact, venue rule, capital sizing, runtime receipt, replay result, "
    "quantum result, live authority, or profit evidence."
)

ATOMICROWS_COMPAT_MATERIALIZED_LEDGER_ONLY = (
    "ATOMICROWS_COMPATIBLE_PR154_LEDGER_MATERIALIZED_VALUE_NO_BUNDLE"
)
ATOMICROWS_COMPAT_BLOCKED_COMPLETION_PATH = (
    "ATOMICROWS_COMPATIBLE_PR154_LEDGER_BLOCKED_WITH_COMPLETION_PATH"
)
ATOMICROWS_COMPAT_UNKNOWN_FAIL_CLOSED = "ATOMICROWS_COMPATIBILITY_UNKNOWN_FAIL_CLOSED"

ATOMICROWS_COMPATIBILITY_CLASSES = (
    ATOMICROWS_COMPAT_MATERIALIZED_LEDGER_ONLY,
    ATOMICROWS_COMPAT_BLOCKED_COMPLETION_PATH,
    ATOMICROWS_COMPAT_UNKNOWN_FAIL_CLOSED,
)

ATOMICROWS_ROW_STATUS_MATERIALIZED_LEDGER_ONLY = (
    "PR154_LEDGER_VALUE_MATERIALIZED_NO_ATOMICROWS_BUNDLE_ROW"
)
ATOMICROWS_ROW_STATUS_BLOCKED_LEDGER_ONLY = (
    "PR154_LEDGER_BLOCKED_NO_ATOMICROWS_BUNDLE_ROW"
)

AGENT_CONSUMABLE_DEFAULT_READY = "AGENT_CONSUMABLE_DEFAULT_READY"
AGENT_BLOCKED_PENDING_ACCEPTED_SOURCE = "AGENT_BLOCKED_PENDING_ACCEPTED_SOURCE"
AGENT_BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW = (
    "AGENT_BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW"
)
AGENT_BLOCKED_PENDING_INTERNAL_OWNER_POLICY = (
    "AGENT_BLOCKED_PENDING_INTERNAL_OWNER_POLICY"
)
AGENT_BLOCKED_PENDING_SPLIT_RECLASSIFICATION = (
    "AGENT_BLOCKED_PENDING_SPLIT_RECLASSIFICATION"
)
AGENT_BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION = (
    "AGENT_BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION"
)
AGENT_BLOCKED_PENDING_OWNER_ROUTE = "AGENT_BLOCKED_PENDING_OWNER_ROUTE"
AGENT_BLOCKED_PENDING_RUNTIME_RECEIPT = "AGENT_BLOCKED_PENDING_RUNTIME_RECEIPT"
AGENT_BLOCKED_PENDING_REPLAY_PAPER_REVIEW = (
    "AGENT_BLOCKED_PENDING_REPLAY_PAPER_REVIEW"
)
AGENT_BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE = (
    "AGENT_BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE"
)
AGENT_BLOCKED_INCOMPLETE_CANDIDATE = "AGENT_BLOCKED_INCOMPLETE_CANDIDATE"
AGENT_BLOCKED_UNKNOWN_FAIL_CLOSED = "AGENT_BLOCKED_UNKNOWN_FAIL_CLOSED"

AGENT_READINESS_CLASSES = (
    AGENT_CONSUMABLE_DEFAULT_READY,
    AGENT_BLOCKED_PENDING_ACCEPTED_SOURCE,
    AGENT_BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW,
    AGENT_BLOCKED_PENDING_INTERNAL_OWNER_POLICY,
    AGENT_BLOCKED_PENDING_SPLIT_RECLASSIFICATION,
    AGENT_BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION,
    AGENT_BLOCKED_PENDING_OWNER_ROUTE,
    AGENT_BLOCKED_PENDING_RUNTIME_RECEIPT,
    AGENT_BLOCKED_PENDING_REPLAY_PAPER_REVIEW,
    AGENT_BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE,
    AGENT_BLOCKED_INCOMPLETE_CANDIDATE,
    AGENT_BLOCKED_UNKNOWN_FAIL_CLOSED,
)

QUANTUM_FORWARD_NOT_APPLICABLE = "QUANTUM_FORWARD_NOT_APPLICABLE_STATIC_LEDGER"
QUANTUM_FORWARD_METADATA_ONLY = "QUANTUM_FORWARD_METADATA_ONLY_NO_EXECUTION"
QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY = (
    "QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY_NO_ARBITRATION"
)
QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED = (
    "QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED_BEFORE_VALUE_USE"
)
QUANTUM_FORWARD_UNKNOWN_FAIL_CLOSED = "QUANTUM_FORWARD_UNKNOWN_FAIL_CLOSED"

QUANTUM_FORWARD_CLASSES = (
    QUANTUM_FORWARD_NOT_APPLICABLE,
    QUANTUM_FORWARD_METADATA_ONLY,
    QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY,
    QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED,
    QUANTUM_FORWARD_UNKNOWN_FAIL_CLOSED,
)

QUANTUM_OPTIMIZER_ROUTE_NOT_APPLICABLE = "QUANTUM_OPTIMIZER_ROUTE_NOT_APPLICABLE"
QUANTUM_OPTIMIZER_ROUTE_METADATA_ONLY = (
    "PR159_PR160_FUTURE_QUANTUM_METADATA_ONLY_NO_EXECUTION"
)
QUANTUM_OPTIMIZER_ROUTE_EXECUTION_EVIDENCE_REQUIRED = (
    "PR159_PR160_QUANTUM_EXECUTION_EVIDENCE_REQUIRED_BEFORE_VALUE_USE"
)

LOW_LATENCY_READY_FOR_PR155_PRECOMPUTED_REGISTRY = (
    "LOW_LATENCY_READY_FOR_PR155_PRECOMPUTED_AGENT_REGISTRY_NOT_LIVE_PRETRADE"
)
LOW_LATENCY_EXCLUDED_UNAUTHORIZED_OR_INCOMPLETE = (
    "LOW_LATENCY_EXCLUDED_UNAUTHORIZED_OR_INCOMPLETE_VALUE"
)

FINAL_STATUS_READY = "PR154_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_GATE_READY"
FINAL_STATUS_FAIL_CLOSED = "PR154_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_GATE_FAIL_CLOSED"
FINAL_STATUS_LABELS = (FINAL_STATUS_READY, FINAL_STATUS_FAIL_CLOSED)

COMPLETION_PATHS: dict[str, dict[str, Any]] = {
    BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE: {
        "materialization_block_reason": "Official-source candidate is incomplete for PR154 fast-lane acceptance.",
        "required_next_task": "COMPLETE_OFFICIAL_SOURCE_CANDIDATE_PACKET",
        "required_next_pr_or_phase": "PR154_CANDIDATE_ACCEPTANCE_REPAIR_OR_FUTURE_SOURCE_CAPTURE",
        "responsible_authority": "CODEX_SOURCE_EVIDENCE_REPAIR_WITH_OWNER_REVIEW_IF_NEEDED",
        "required_input_artifact": "OFFICIAL_SOURCE_CANDIDATE_COMPLETION_PACKET",
        "exact_unblock_condition": "official locator + captured value + target-field match + quote/span or machine-field locator + unit/scale when applicable + provenance + no unresolved conflict",
        "materialization_retry_route": "PR154_FAST_LANE_RETRY_AFTER_CANDIDATE_COMPLETION",
        "codex_actionable_completion_steps": (
            "Inspect candidate missing_fields.",
            "Repair only the missing official-source packet fields from source evidence.",
            "Regenerate PR154 and rerun the PR154 validator.",
        ),
    },
    BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET: {
        "materialization_block_reason": "Accepted source packet is required and not present.",
        "required_next_task": "CREATE_ACCEPTED_SOURCE_VALUE_PACKET",
        "required_next_pr_or_phase": "FUTURE_ACCEPTED_SOURCE_PACKET_REPAIR",
        "responsible_authority": "CODEX_SOURCE_EVIDENCE_ACCEPTANCE_WITH_OWNER_REVIEW",
        "required_input_artifact": "ACCEPTED_SOURCE_VALUE_PACKET",
        "exact_unblock_condition": "accepted packet provides exact value/type/unit/scale/source locator/field locator/provenance for this target",
        "materialization_retry_route": "RETRY_PR154_AFTER_ACCEPTED_SOURCE_PACKET",
        "codex_actionable_completion_steps": (
            "Create or consume an accepted source packet for this exact target.",
            "Verify target identity and source locator match.",
            "Regenerate PR154.",
        ),
    },
    BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW: {
        "materialization_block_reason": "PR153R retry record lacks complete accepted target-field source evidence.",
        "required_next_task": "COMPLETE_PR153R_RETRY_ACCEPTANCE_REVIEW",
        "required_next_pr_or_phase": "PR153R_ACCEPTANCE_REPAIR_OR_FUTURE_SOURCE_CAPTURE",
        "responsible_authority": "CODEX_SOURCE_EVIDENCE_REPAIR_WITH_OWNER_REVIEW",
        "required_input_artifact": "PR153R_ACCEPTED_TARGET_FIELD_SOURCE_PACKET",
        "exact_unblock_condition": "exact target value + quote/span or machine-field locator + target-field scope match + official locator + provenance",
        "materialization_retry_route": "PR154_FAST_LANE_RETRY_AFTER_PR153R_COMPLETION",
        "codex_actionable_completion_steps": (
            "Use the PR153R retrieved official locators as candidates only.",
            "Capture the exact target-field value and locator.",
            "Run PR153R and PR154 validators after repair.",
        ),
    },
    BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION: {
        "materialization_block_reason": "Target must be split or reclassified before value materialization.",
        "required_next_task": "SPLIT_OR_RECLASSIFY_TARGET",
        "required_next_pr_or_phase": "PR154_SPLIT_RECLASSIFICATION_REPAIR_OR_FUTURE_SOURCE_TARGET_SPLIT",
        "responsible_authority": "OWNER_AND_CODEX_TARGET_TAXONOMY_REVIEW",
        "required_input_artifact": "TARGET_SPLIT_RECLASSIFICATION_PACKET",
        "exact_unblock_condition": "child targets with authority lanes and materialization routes exist",
        "materialization_retry_route": "RETRY_PR154_ON_CHILD_TARGETS_AFTER_SPLIT",
        "codex_actionable_completion_steps": (
            "Create precise child targets.",
            "Assign each child target to an evidence lane.",
            "Regenerate PR151/PR153S successor inputs and PR154.",
        ),
    },
    BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION: {
        "materialization_block_reason": "Private document or access-rights attestation is required.",
        "required_next_task": "OWNER_PRIVATE_DOC_ATTESTATION_PACKET",
        "required_next_pr_or_phase": "PRIVATE_DOC_ATTESTATION_REPAIR_OR_OWNER_PACKET_PHASE",
        "responsible_authority": "OWNER_PRIVATE_DOC_AUTHORITY",
        "required_input_artifact": "PRIVATE_DOC_ATTESTATION_PACKET_WITH_VALUE_LOCATOR",
        "exact_unblock_condition": "attestation + value + locator + target-field match are present",
        "materialization_retry_route": "RETRY_PR154_AFTER_PRIVATE_DOC_ATTESTATION_PACKET",
        "codex_actionable_completion_steps": (
            "Obtain owner access-rights attestation.",
            "Record private-doc value locator without exposing secrets.",
            "Regenerate PR154.",
        ),
    },
    BLOCKED_PENDING_OWNER_ROUTE_PACKET: {
        "materialization_block_reason": "Owner route is only a hint and lacks complete locator/value evidence.",
        "required_next_task": "OWNER_ROUTE_LOCATOR_PACKET_COMPLETION",
        "required_next_pr_or_phase": "OWNER_ROUTE_PACKET_COMPLETION_PHASE",
        "responsible_authority": "OWNER_ROUTE_AUTHORITY_WITH_CODEX_VALIDATION",
        "required_input_artifact": "OWNER_PROVIDED_ROUTE_LOCATOR_PACKET",
        "exact_unblock_condition": "official locator + value + field match + unit/scale + provenance",
        "materialization_retry_route": "RETRY_PR154_AFTER_OWNER_ROUTE_LOCATOR_PACKET",
        "codex_actionable_completion_steps": (
            "Collect owner route packet with exact value and official locator.",
            "Verify it is not only a hint.",
            "Regenerate PR154.",
        ),
    },
    BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE: {
        "materialization_block_reason": "Internal owner policy target lacks an exact deterministic policy value.",
        "required_next_task": "CREATE_OWNER_INTERNAL_POLICY_VALUE_LEDGER_ENTRY",
        "required_next_pr_or_phase": "OWNER_INTERNAL_POLICY_VALUE_LEDGER_PHASE",
        "responsible_authority": "OWNER_INTERNAL_QTT_POLICY_AUTHORITY",
        "required_input_artifact": "OWNER_INTERNAL_POLICY_VALUE_PACKET",
        "exact_unblock_condition": "exact value/type/unit/scale/source path/key/field provided",
        "materialization_retry_route": "RETRY_PR154_AFTER_OWNER_INTERNAL_POLICY_VALUE_PACKET",
        "codex_actionable_completion_steps": (
            "Define exact owner internal policy value.",
            "Record value type, unit, scale, source path, key, and field.",
            "Regenerate PR154.",
        ),
    },
    BLOCKED_PENDING_RUNTIME_RECEIPT: {
        "materialization_block_reason": "Runtime/private-state receipt is required and PR154 must not create it.",
        "required_next_task": "BIND_RUNTIME_PRIVATE_STATE_RECEIPT",
        "required_next_pr_or_phase": "PR158_RUNTIME_CASH_PRIVATE_STATE_RECEIPT_BINDING",
        "responsible_authority": "RUNTIME_RECEIPT_GATE_WITH_OWNER_REVIEW",
        "required_input_artifact": "RUNTIME_PRIVATE_STATE_RECEIPT_PACKET",
        "exact_unblock_condition": "runtime receipt exists",
        "materialization_retry_route": "RETRY_PR154_AFTER_PR158_RECEIPT",
        "codex_actionable_completion_steps": (
            "Wait for PR158 runtime receipt.",
            "Verify receipt is target-scoped.",
            "Regenerate PR154 or downstream registry.",
        ),
    },
    BLOCKED_PENDING_REPLAY_PAPER_REVIEW: {
        "materialization_block_reason": "Replay/paper review evidence is required and PR154 must not create it.",
        "required_next_task": "CREATE_REPLAY_PAPER_REVIEW_EVIDENCE",
        "required_next_pr_or_phase": "PR156_PR157_REPLAY_PAPER_CALIBRATION",
        "responsible_authority": "REPLAY_PAPER_REVIEW_GATE_WITH_OWNER_REVIEW",
        "required_input_artifact": "REPLAY_PAPER_RESULT_REVIEW_PACKET",
        "exact_unblock_condition": "replay/paper result and review evidence exists",
        "materialization_retry_route": "RETRY_PR154_AFTER_PR156_PR157_EVIDENCE",
        "codex_actionable_completion_steps": (
            "Wait for replay/paper calibration evidence.",
            "Verify reviewed result is target-scoped.",
            "Regenerate PR154 or downstream registry.",
        ),
    },
    BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE: {
        "materialization_block_reason": "Quantum execution evidence is required and PR154 must not create it.",
        "required_next_task": "CREATE_QUANTUM_EXECUTION_EVIDENCE_PACKET",
        "required_next_pr_or_phase": "PR159_PR160_QUANTUM_EVIDENCE_CALIBRATION",
        "responsible_authority": "QUANTUM_EVIDENCE_GATE_WITH_OWNER_REVIEW",
        "required_input_artifact": "QUANTUM_EXECUTION_EVIDENCE_PACKET",
        "exact_unblock_condition": "quantum backend/simulator/optimizer execution evidence exists",
        "materialization_retry_route": "RETRY_PR154_AFTER_PR159_PR160_EVIDENCE",
        "codex_actionable_completion_steps": (
            "Wait for quantum evidence calibration.",
            "Verify backend/simulator/optimizer evidence is target-scoped.",
            "Regenerate PR154 or downstream registry.",
        ),
    },
    BLOCKED_UNKNOWN_FAIL_CLOSED: {
        "materialization_block_reason": "Unknown lane fails closed.",
        "required_next_task": "REPAIR_PR153S_CLASSIFICATION",
        "required_next_pr_or_phase": "PR153S_CLASSIFICATION_REPAIR",
        "responsible_authority": "CODEX_SOURCE_VALUE_CLASSIFICATION_REPAIR",
        "required_input_artifact": "PR153S_CLASSIFICATION_REPAIR_PACKET",
        "exact_unblock_condition": "PR153S emits a known closure lane and materialization route",
        "materialization_retry_route": "RETRY_PR154_AFTER_PR153S_REPAIR",
        "codex_actionable_completion_steps": (
            "Repair upstream PR153S classification.",
            "Regenerate PR153S.",
            "Regenerate PR154.",
        ),
    },
}

BLOCK_TO_AGENT_READINESS = {
    BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE: AGENT_BLOCKED_INCOMPLETE_CANDIDATE,
    BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET: AGENT_BLOCKED_PENDING_ACCEPTED_SOURCE,
    BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW: (
        AGENT_BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW
    ),
    BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION: (
        AGENT_BLOCKED_PENDING_SPLIT_RECLASSIFICATION
    ),
    BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION: (
        AGENT_BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION
    ),
    BLOCKED_PENDING_OWNER_ROUTE_PACKET: AGENT_BLOCKED_PENDING_OWNER_ROUTE,
    BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE: (
        AGENT_BLOCKED_PENDING_INTERNAL_OWNER_POLICY
    ),
    BLOCKED_PENDING_RUNTIME_RECEIPT: AGENT_BLOCKED_PENDING_RUNTIME_RECEIPT,
    BLOCKED_PENDING_REPLAY_PAPER_REVIEW: AGENT_BLOCKED_PENDING_REPLAY_PAPER_REVIEW,
    BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE: (
        AGENT_BLOCKED_PENDING_QUANTUM_EXECUTION_EVIDENCE
    ),
    BLOCKED_UNKNOWN_FAIL_CLOSED: AGENT_BLOCKED_UNKNOWN_FAIL_CLOSED,
}

NO_AUTHORITY_COUNTERS = {
    "connector_unlock_count": 0,
    "runtime_private_state_receipt_value_count": 0,
    "runtime_cash_receipt_count": 0,
    "order_receipt_count": 0,
    "fill_receipt_count": 0,
    "replay_result_count": 0,
    "paper_result_count": 0,
    "live_reachability_count": 0,
    "profit_evidence_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_simulator_execution_count": 0,
    "quantum_optimizer_execution_count": 0,
    "quantum_advantage_claim_count": 0,
    "atomicrows_bundle_mutation_count": 0,
    "atomicrows_bundle_hash_sha_authority_count": 0,
    "qtt_sha_freeze_checksum_authority_count": 0,
    "global_repository_digest_authority_count": 0,
}

REQUIRED_RECORD_FIELDS = (
    "pr154_record_id",
    "source_pr153s_target_id",
    "pr153s_canonical_identity_key",
    "platform_scope",
    "market_scope_if_available",
    "target_field_path",
    "parameter_family_or_target_family",
    "pr153s_closure_lane",
    "pr153s_materialization_route",
    "acceptance_decision",
    "materialization_decision",
    "materialization_allowed",
    "materialized_value",
    "materialized_value_type",
    "materialized_value_unit",
    "materialized_value_scale",
    "materialized_value_source_class",
    "materialized_value_authority_class",
    "materialized_value_authority_ref",
    "materialized_value_source_path",
    "materialized_value_source_record_key",
    "materialized_value_source_field_path",
    "official_source_locator",
    "quote_span_or_machine_field_locator",
    "candidate_value_present_upstream",
    "candidate_value_promoted_to_materialized_value",
    "accepted_source_packet_required",
    "accepted_source_packet_present",
    "owner_internal_policy_required",
    "owner_internal_policy_present",
    "split_reclassification_required",
    "private_doc_attestation_required",
    "owner_route_packet_required",
    "runtime_receipt_required",
    "replay_paper_review_required",
    "quantum_execution_evidence_required",
    "materialization_block_code",
    "materialization_block_reason",
    "missing_fields",
    "required_next_task",
    "required_next_pr_or_phase",
    "responsible_authority",
    "required_input_artifact",
    "exact_unblock_condition",
    "materialization_retry_route",
    "codex_actionable_completion_steps",
    "atomicrows_compatibility_class",
    "atomicrows_row_materialization_status",
    "atomicrows_bundle_mutation_created",
    "atomicrows_bundle_hash_authority_created",
    "agent_consumption_readiness_class",
    "agent_consumption_block_reason",
    "low_latency_hot_path_eligibility",
    "live_pretrade_consumption_allowed",
    "quantum_forward_compatibility_class",
    "quantum_optimizer_default_route",
    "quantum_execution_required_before_use",
    "runtime_live_order_authority_created",
    "profit_evidence_created",
)


def completion_path(block_code: str) -> dict[str, Any]:
    return dict(COMPLETION_PATHS.get(block_code, COMPLETION_PATHS[BLOCKED_UNKNOWN_FAIL_CLOSED]))


def zero_authority_counters() -> dict[str, int]:
    return dict(NO_AUTHORITY_COUNTERS)
