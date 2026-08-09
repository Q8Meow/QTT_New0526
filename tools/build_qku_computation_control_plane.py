#!/usr/bin/env python3
"""Build a deterministic, data-only summary of the Tranche-A contract plane."""

from __future__ import annotations

import argparse
from dataclasses import MISSING, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (  # noqa: E402
    CERTIFIED_SOURCE_STATES,
    GOLDEN_VECTOR_BY_MATH_ID,
    IMPLEMENTATION_REGISTRY,
    ORACLE_BY_MATH_ID,
    PARAMETER_POLICIES,
    APPEND_ONLY_TABLES_V1,
    ST12C_CONTROL_COVERAGE_MATRIX,
    ST12C_GOLDEN_VECTOR_BY_MATH_ID,
    ST12C_LATER_PHASE_BLOCKERS,
    ST12C_PRODUCTION_MODULE_PATHS,
    ST12C_ORACLE_BY_MATH_ID,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
    TRANCHE_C_PARAMETER_APPLICATION_BINDINGS,
    TRANCHE_C_PARAMETER_POLICIES,
    SOURCE_CLAIM_BINDING_RULES,
    SOURCE_CURRENTIZATION_OVERLAYS,
    build_tranche_a_coverage_manifest,
    deterministic_json,
    validate_relative_path,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.mode_snapshot_policy import (  # noqa: E402
    D_MODE_STATE_REGISTRY,
    D_REQUIRED_PIN_DIMENSIONS,
    MODE_SNAPSHOT_TRANSITIONS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (  # noqa: E402
    IMPLEMENTATION_VERSION_REGISTRY,
    PREDECESSOR_IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (  # noqa: E402
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FORMULA_INPUT_AUTHORITY_BINDINGS,
    FROZEN_ONLINE_CURRENTIZATION_RECEIPTS,
    NUMERIC_VALUE_AUTHORITY_BINDINGS,
    PRIMARY_SOURCE_REGISTRY,
    SOURCE_CONFLICT_RESOLUTIONS,
    SOURCE_CURRENTIZATION_REGISTRY,
    SOURCE_POPULATION_COUNTS,
    ST12D_MATH39_RAW_INPUT_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (  # noqa: E402
    FROZEN_DEPENDENCY_RELATIONSHIPS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (  # noqa: E402
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    OperationCapabilityClass,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (  # noqa: E402
    ST12D_GOLDEN_VECTOR_BY_MATH_ID,
    ST12D_ORACLE_BY_MATH_ID,
    ST12B_PROPERTY_TESTS,
    ST12B_VECTOR_PACK,
    TRANCHE_A_GOLDEN_VECTOR_BY_MATH_ID,
    TRANCHE_A_ORACLE_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (  # noqa: E402
    CUMULATIVE_PARAMETER_POLICIES,
    INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES,
    OPTIMIZER_DEFAULT_CURRENTIZATIONS,
    RUNTIME_PARAMETER_OWNER_BINDINGS,
    ST12D_PARAMETER_APPLICATION_BINDINGS,
    ST12D_OWNER_RESOLVED_PARAMETER_IDS,
    ST12D_PARAMETER_VALUE_PACKET_SCHEMA_ID,
    ST12D_PARAMETER_VALUE_PACKET_SCHEMA_VERSION,
    ST12D_PARAMETER_VALUE_PACKET_TYPE,
    ST12D_PARAMETER_POLICIES,
    ST12D_SNAPSHOT_PARAMETER_BINDING_IDS,
    resolve_st12d_snapshot_parameter_values,
    resolve_st12d_value_policy_refs,
    st12d_snapshot_parameter_binding_id,
    st12d_snapshot_parameter_field_path,
    st12d_snapshot_parameter_source_lineage,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (  # noqa: E402
    QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (  # noqa: E402
    FROZEN_FORMULA_REPOSITORY_DISPOSITIONS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (  # noqa: E402
    REGISTERED_FORMULA_STACKS,
    RegisteredSnapshotComputationBundleV1,
    preflight_snapshot_computation_bundle,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.contextual_computability import (  # noqa: E402
    FrozenContextualComputabilityResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (  # noqa: E402
    CanonicalOwnerPacketRegistryV1,
    Math39BookEventKindV1,
    Math39OrderAcknowledgementV1,
    Math39SequencedBookEventV1,
    OwnerValuePacketV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (  # noqa: E402
    PointInTimeClocksV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (  # noqa: E402
    ST12D_ACTUAL_CONTROL_MUTATION_CASES,
    ST12D_CERTIFIED_COMMANDS,
    ST12D_CLOSURE_ROWS,
    ST12D_GENERATED_PROJECTION_PATHS,
    ST12D_HISTORICAL_PATH_DISPOSITIONS,
    ST12D_SEMANTIC_TEST_ROWS,
    ST12E_CERTIFIED_COMMANDS,
    ST12E_CLOSURE_ROWS,
    ST12E_REPOSITORY_DISPOSITIONS,
    ST12E_REUSED_MATH_PACK,
    ST12E_SEMANTIC_TEST_ROWS,
    ST12B_AGENT_CONSUMER_DAG,
    ST12B_AGENT_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
    validate_tranche_b_frozen_manifest,
    adjudicate_st12d_semantic_test,
    run_st12d_actual_control_mutation_case,
    st12e_semantic_counts,
    st12d_acceptance_counts,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (  # noqa: E402
    ST12D_MATH_IMPLEMENTATION_REGISTRY,
)
from src.qtt.agents.pr169_agent_orch1_resolvers import AgentOrchService  # noqa: E402
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (  # noqa: E402
    ACTIVATION_STATE,
    AGENT_ORCH_PREFIX,
    CENTRAL_VALIDATOR_REF,
    HELD_OPERATION_IDS,
    IMPLEMENTED_OPERATION_IDS,
    NO_EFFECT_PROFILE_REF,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    OWNER_ACTION_IDS,
    POLICY_VERSION,
    QUANTUM_FORMULATION_FIELDS,
    LLM_ADVISORY_TASK_FIELDS,
    ST12E_BINDING_EXACT,
    ST12E_BINDING_OUTSIDE_SCOPE,
    UPSTREAM_IDENTITY_CROSSWALK_REQUIRED,
    UPSTREAM_IDENTITY_FULLY_MAPPED,
    AgentIdentityMappingTypeV1,
    build_generated_policy_rows,
    build_identity_compatibility_map,
    build_parameter_scope_projection,
    build_st12e_certified_source_universe_registry,
    build_upstream_source_universe_registry,
    canonical_master_parameter_rows,
    canonical_parameter_identity_registry,
    canonical_source_agent_ids,
    canonical_source_role_labels,
    current_owner_action_ids,
    no_effect_authority_is_closed,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (  # noqa: E402
    ST12E_PARAMETER_POLICY_SPECS,
    resolve_st12e_value_policy_refs,
    resolve_st12e_value_policies,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (  # noqa: E402
    QKUComputationControlPlaneV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (  # noqa: E402
    ImmutableReplayPaperInputLockV1,
    ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
    ST12F_PARAMETER_VALUE_REF_COUNT_V1,
    ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
    ST12F_TEMPLATE_IDS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (  # noqa: E402
    ComputationEvidenceBundleV1,
    DivergenceAssessmentV1,
    EvidenceBundleTerminalStateV1,
    IndependentReviewDecisionV1,
    PaperResultContractV1,
    ReplayResultContractV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
    ST12F_EVIDENCE_METRIC_DEFINITIONS_V1,
    _EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.llm_gateway import (  # noqa: E402
    LLMAdvisoryTaskV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (  # noqa: E402
    MODEL_RISK_CONTROL_IDS_V1,
    NO_TRADE_CONDITION_IDS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (  # noqa: E402
    ST12F_QUANTUM_TRACE_ONLY_BOUNDARIES_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (  # noqa: E402
    TRANCHE_A_AUTHORITY,
)


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_BUILD_VALIDATED"
ST12E_GENERATED_PREFIX = Path(
    "docs/master_plan/generated/qku_control_plane/agent_capability"
)
ST12EProjectionSet = tuple[
    dict[str, object],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
]
ST12D_GENERATED_PREFIX = Path(
    "docs/master_plan/generated/qku_control_plane/mode_snapshot"
)
ST12DProjectionSet = tuple[
    dict[str, object],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    dict[str, object],
]
ST12F_GENERATED_PREFIX = Path(
    "docs/master_plan/generated/qku_control_plane/evidence"
)
ST12F_GENERATED_PATHS = (
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

_ST12D_FROZEN_CONTRACT_POLICY_REFS = (
    "freeze/AUTHORITY.md",
    "freeze/CLOSURE_ROWS.jsonl",
    "freeze/CURRENT_MAIN_OWNER_MAP.jsonl",
    "freeze/DEPENDENCY_CURRENTIZATION.jsonl",
    "freeze/DEPENDENCY_GRAPH.jsonl",
    "freeze/GOLDEN_VECTORS.jsonl",
    "freeze/INDEPENDENT_ORACLES.jsonl",
    "freeze/INVARIANTS.jsonl",
    "freeze/KILL_SUBMIT_PROTOCOL.json",
    "freeze/LATENCY_BUDGET_POLICY.jsonl",
    "freeze/LATENCY_CLOCK_REGISTRY.jsonl",
    "freeze/MATH_SPECS.jsonl",
    "freeze/MODE_STATE_REGISTRY.jsonl",
    "freeze/OWNER_PROJECTION_INTERFACE.json",
    "freeze/PARAMETER_APPLICATION_BINDINGS.jsonl",
    "freeze/PARAMETER_POLICIES.jsonl",
    "freeze/PATH_DISPOSITION.jsonl",
    "freeze/PATH_LEDGER.json",
    "freeze/PINNING_POLICY.json",
    "freeze/ROLLBACK_POLICY.json",
    "freeze/SNAPSHOT_CONTRACT.json",
    "freeze/SOURCE_CURRENTIZATION.jsonl",
    "freeze/ST12D_FREEZE_SPECIFICATION.md",
    "freeze/ST12F_EVIDENCE_INTERFACE.json",
    "freeze/STATE.json",
    "freeze/TEST_PLAN.json",
    "freeze/TRANSITION_MATRIX.jsonl",
    "freeze/UNRESOLVED_BLOCKERS.jsonl",
    "freeze/VALIDATION_PLAN.json",
)
_ST12D_CURRENT_OWNER_INTERFACES = (
    (
        "OWNER::QKU-CONTROL-PLANE",
        "CurrentModeSnapshotInputResolverV1/QKUComputationControlPlaneV1.submit_candidate_proposal",
        "request_id,context_ref,computation_bundle_ref",
    ),
    (
        "OWNER::ST12E-ADMISSION",
        "AgentCapabilityResolverV1.admit_operation",
        "decision_id,task_id,principal_id,current_agent_id",
    ),
    (
        "OWNER::AGENT-ORCH1",
        "AgentCapabilityDecisionV1",
        "task_id,principal_id,current_agent_id,duty_ref",
    ),
    (
        "OWNER::CONTEXTUAL-COMPUTABILITY",
        "FrozenContextualComputabilityResolverV1.resolve(snapshot_bundle=...)",
        "specification_state,fixture_state,context_state,stack_state",
    ),
    (
        "OWNER::IMPLEMENTATION-REGISTRY",
        "CURRENT_IMPLEMENTATION_REGISTRY/ST12D_MATH_IMPLEMENTATION_REGISTRY",
        "math_spec_id,implementation_id",
    ),
    (
        "OWNER::ORACLE-VECTOR",
        "ST12D_ORACLE_BY_MATH_ID/ST12D_GOLDEN_VECTOR_BY_MATH_ID",
        "oracle_id,vector_id,comparison_policy",
    ),
    (
        "OWNER::PARAMETER-VALUE",
        "ComputationParameterPolicyV1/ParameterPolicyResolverV1",
        "parameter_policy_snapshot_ref,parameter_value_refs",
    ),
    (
        "OWNER::READINESS1",
        "ExistingOwnerProjectionAdapterV1.load_readiness",
        "readiness_state_ref",
    ),
    (
        "OWNER::PRETRADE1",
        "ExistingOwnerProjectionAdapterV1.load_pretrade",
        "pretrade_state_ref,typed_NO_TRADE_route",
    ),
    (
        "OWNER::SAFETY",
        "CurrentSafetyStateAdapterV1/ReadOnlyKillSubmitStateProtocolV1",
        "kill_state_ref,submit_disabled_state_ref",
    ),
    (
        "OWNER::ST12F-INTERFACE",
        "CurrentPreFEvidenceAdapterV1.pre_f_unavailable_reference",
        "evidence_state_ref",
    ),
    (
        "OWNER::OWNER-ACTION",
        "CurrentOwnerActionConfirmationAdapterV1/OwnerActionConfirmationReceiptV1",
        "owner_action_policy_ref",
    ),
    (
        "OWNER::RECEIPT-SPINE",
        "EconomicReceiptEventSpineV1",
        "causation_id,correlation_id,traceparent,tracestate",
    ),
    (
        "OWNER::SVC1",
        "ExistingOwnerProjectionAdapterV1.project_mode_snapshot",
        "ModeSnapshotCandidateProposalResultV1.owner_projection_or_explicit_absence",
    ),
    (
        "OWNER::PR137L-HOTPATH",
        "LatencyHotPathSnapshotBoundaryAdapterV1",
        "immutable_local_snapshot_boundary",
    ),
    (
        "OWNER::EXECUTION-ROUTER",
        "ExecutionRouterV1",
        "sole_final_order_release_authority",
    ),
)
_ST12D_VALIDATION_OWNER_PATHS = (
    "tools/build_qku_computation_control_plane.py",
    "tools/independent_validate_qku_computation_control_plane_d.py",
    "tools/independent_validate_qku_computation_control_plane.py",
    "tools/independent_validate_qku_computation_control_plane_architecture.py",
    "tools/validate_qku_computation_control_plane.py",
    "tools/validation_inventory.py",
    "tools/validation_scope_registry.py",
    "tools/changed_area_validation_router.py",
    "tools/ci_branch_context.py",
    "tools/run_validation_gates.py",
    "tools/currentize_pr152_after_generated_artifacts.py",
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
)
_ST12D_RUNTIME_OUTPUTS = (
    ("OUTPUT::SNAPSHOT-CANDIDATE", "FormulaRuntimeSnapshotCandidateV1"),
    ("OUTPUT::MODE-DECISION", "ModeSnapshotDecisionV1"),
    ("OUTPUT::TRANSITION-PROPOSAL", "SnapshotTransitionProposalV1"),
    ("OUTPUT::PROPOSAL-RESULT", "ModeSnapshotCandidateProposalResultV1"),
    ("OUTPUT::CONTROL-RECEIPT", "ModeSnapshotControlReceiptRecordV1"),
    ("OUTPUT::OWNER-PROJECTION", "ModeSnapshotOwnerProjectionV1"),
    ("OUTPUT::LATENCY-MEASUREMENT", "LatencyMeasurementV1"),
    ("OUTPUT::MATH-39-QUEUE-AHEAD", "compute_math_39_queue_position_estimate"),
)
_ST12D_RUNTIME_OPERATIONAL_CONNECTIVITY = {
    "OUTPUT::SNAPSHOT-CANDIDATE": (
        (
            "CandidateProposalV1.mode_snapshot_result.snapshot_candidate_or_explicit_absence",
            "SubmitCandidateProposalResponseV1.proposal",
        ),
        "ModeSnapshotCandidateProposalResultV1.snapshot_candidate_or_explicit_absence",
        "RETURNED_IN_TYPED_CANDIDATE_PROPOSAL_RESPONSE_NO_EFFECT",
    ),
    "OUTPUT::MODE-DECISION": (
        (
            "SubmitCandidateProposalResponseV1.proposal",
            "ModeSnapshotOwnerProjectionV1.decision_id",
        ),
        "ModeSnapshotCandidateProposalResultV1.mode_snapshot_decision",
        "RETURNED_IN_RESPONSE_AND_FINAL_OWNER_PROJECTION_NO_EFFECT",
    ),
    "OUTPUT::TRANSITION-PROPOSAL": (
        (
            "SubmitCandidateProposalResponseV1.proposal",
            "ModeSnapshotCandidateProposalResultV1.executed_transition_trace",
            "EconomicReceiptEventSpineV1.ModeSnapshotControlReceiptRecordV1.transition_proposal_ref",
        ),
        "ModeSnapshotCandidateProposalResultV1.executed_transition_trace.final_proposal",
        "RETURNED_IN_ORDERED_TRACE_RESPONSE_AND_CONTROL_RECEIPT_SPINE_NO_EFFECT",
    ),
    "OUTPUT::PROPOSAL-RESULT": (
        ("SubmitCandidateProposalResponseV1.proposal.mode_snapshot_result",),
        "SubmitCandidateProposalResponseV1.proposal.mode_snapshot_result",
        "RETURNED_IN_TYPED_SUBMIT_CANDIDATE_RESPONSE_NO_EFFECT",
    ),
    "OUTPUT::CONTROL-RECEIPT": (
        (
            "PersistenceAdapterV1.insert_receipt_record_when_AVAILABLE_REFERENCE",
            "ModeSnapshotCandidateProposalResultV1.control_receipt_proposals",
        ),
        "PersistenceAdapterV1.get_record_or_exact_returned_typed_proposal",
        "PERSISTED_OR_RETURNED_AS_EXACT_TYPED_RECEIPT_PROPOSAL",
    ),
    "OUTPUT::OWNER-PROJECTION": (
        (
            "ModeSnapshotCandidateProposalResultV1.owner_projection_or_explicit_absence",
            "ExistingOwnerProjectionAdapterV1.project_mode_snapshot",
        ),
        "ModeSnapshotCandidateProposalResultV1.owner_projection_or_explicit_absence",
        "RETURNED_AND_PROJECTED_INTO_EXISTING_OWNER_SEMANTIC_FABRIC",
    ),
    "OUTPUT::LATENCY-MEASUREMENT": (
        (
            "ModeSnapshotCandidateProposalResultV1.latency_measurement_or_explicit_absence",
            "ModeSnapshotControlReceiptRecordV1.latency_measurement_ref_or_explicit_absence",
        ),
        "exact_returned_LatencyMeasurementV1_or_existing_receipt_spine_ref",
        "RETURNED_EXACT_MEASUREMENT_AND_REFERENCED_BY_RECEIPT_SPINE",
    ),
    "OUTPUT::MATH-39-QUEUE-AHEAD": (
        ("ComputeComponentResponseV1.component_result",),
        "ComputeComponentResponseV1.component_result",
        "RETURNED_IN_EXISTING_COMPUTE_COMPONENT_RESPONSE_NO_EFFECT",
    ),
}


def build_st12e_projections() -> ST12EProjectionSet:
    """Build all E outputs in memory from frozen canonical owners."""

    master_text = (
        REPO_ROOT / "docs/master_plan/QTT_MasterPlan_Current.md"
    ).read_text(encoding="utf-8")
    master_rows = canonical_master_parameter_rows(master_text)
    source_agent_ids = canonical_source_agent_ids(master_text)
    orch_snapshot = AgentOrchService(repo_root=REPO_ROOT).load_policy_snapshot()
    identity_map = build_identity_compatibility_map(
        orch_snapshot,
        source_agent_ids=source_agent_ids,
        source_role_labels=canonical_source_role_labels(master_text),
    )
    parameter_scope = build_parameter_scope_projection(
        master_plan_text=master_text,
        identity_map=identity_map,
    )
    policy_rows = build_generated_policy_rows(
        control_rows=ST12E_CLOSURE_ROWS,
        identity_map=identity_map,
    )
    scope_rows = tuple(
        {
            name: getattr(row, name)
            for name in row.__dataclass_fields__
        }
        for row in parameter_scope
    )
    counts = dict(st12e_semantic_counts())
    upstream_universes, _ = build_upstream_source_universe_registry(master_rows)
    st12e_universes, _ = build_st12e_certified_source_universe_registry()
    exact_mappings = tuple(
        binding
        for binding in identity_map.bindings.values()
        if binding.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
    )
    unmapped_mappings = tuple(
        binding
        for binding in identity_map.bindings.values()
        if binding.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED
    )
    fully_mapped_scope = tuple(
        row
        for row in parameter_scope
        if row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_FULLY_MAPPED
    )
    crosswalk_required_scope = tuple(
        row
        for row in parameter_scope
        if row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
    )
    exact_e_scope = tuple(
        row
        for row in parameter_scope
        if row.st12e_binding_state == ST12E_BINDING_EXACT
    )
    outside_e_scope = tuple(
        row
        for row in parameter_scope
        if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
    )
    e_scope_with_gap = sum(
        row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
        for row in exact_e_scope
    )
    value_policy_resolution = resolve_st12e_value_policies(
        canonical_parameter_identity_registry(master_text)
    )
    resolved_value_refs = value_policy_resolution.value_policy_refs
    resolver_field = next(
        field
        for field in fields(QKUComputationControlPlaneV1)
        if field.name == "agent_capability_resolver"
    )
    implicit_admission_bypass_count = int(
        resolver_field.default is not MISSING
        or resolver_field.default_factory is not MISSING
    )
    manifest: dict[str, object] = {
        "schema": "AgentCapabilityPolicyManifestV1",
        "policy_version": POLICY_VERSION,
        "registry_version": orch_snapshot.manifest_version,
        "semantic_owner": "QKUComputationControlPlaneV1",
        "implementation_owner": "AgentCapabilityResolverV1",
        "parameter_value_owner": "ComputationParameterPolicyV1",
        "agent_orchestration_owner": "AGENT-ORCH1",
        "owner_action_owner": "OwnerActionRegistry",
        "final_release_owner": "ExecutionRouterV1",
        "activation_state": ACTIVATION_STATE,
        "no_effect_profile_ref": NO_EFFECT_PROFILE_REF,
        "no_effect_authority_flags": {
            name: getattr(TRANCHE_A_AUTHORITY, name)
            for name in TRANCHE_A_AUTHORITY.__dataclass_fields__
        },
        "runtime_effect_authorized": False,
        "manual_edit_allowed": False,
        "counts": counts,
        "policy_row_count": len(policy_rows),
        "identity_mapping_count": len(identity_map.bindings),
        "source_identity_row_count": len(identity_map.bindings),
        "exact_mapping_count": len(exact_mappings),
        "unmapped_mapping_count": len(unmapped_mappings),
        "unmapped_source_agent_ids": [
            binding.source_agent_id for binding in unmapped_mappings
        ],
        "parameter_scope_row_count": len(scope_rows),
        "exact_upstream_source_universe_count": len(upstream_universes),
        "exact_upstream_source_agent_id_count": len(source_agent_ids),
        "fully_mapped_upstream_row_count": len(fully_mapped_scope),
        "crosswalk_required_upstream_row_count": len(
            crosswalk_required_scope
        ),
        "exact_st12e_binding_count": len(exact_e_scope),
        "outside_st12e_binding_scope_count": len(outside_e_scope),
        "exact_st12e_certified_mapping_count": len(exact_e_scope),
        "st12e_binding_with_unmapped_certified_id_count": 0,
        "st12e_rows_with_upstream_crosswalk_gap": e_scope_with_gap,
        "st12e_rows_with_fully_mapped_upstream_lineage": (
            len(exact_e_scope) - e_scope_with_gap
        ),
        "quota_reassignment_count": 0,
        "nearest_universe_assignment_count": 0,
        "source_set_rewrite_count": 0,
        "appendix_e_policy_spec_count": len(ST12E_PARAMETER_POLICY_SPECS),
        "parameter_identity_resolution_count": (
            value_policy_resolution.parameter_identity_resolution_count
        ),
        "canonical_typed_policy_resolution_count": (
            value_policy_resolution.canonical_typed_policy_resolution_count
        ),
        "unresolved_typed_policy_count": (
            value_policy_resolution.unresolved_typed_policy_count
        ),
        "conflicting_typed_policy_count": (
            value_policy_resolution.conflicting_typed_policy_count
        ),
        "canonical_parameter_value_owner_count": (
            value_policy_resolution.canonical_parameter_value_owner_count
        ),
        "value_policy_ref_resolution_count": len(resolved_value_refs),
        "duplicated_value_body_count": 0,
        "capability_binding_value_body_count": 0,
        "generated_policy_value_body_count": 0,
        "implicit_admission_bypass_count": implicit_admission_bypass_count,
        "production_default_admission_profile_count": (
            implicit_admission_bypass_count
        ),
        "opaque_semantic_payload_count": 0,
        "exact_upstream_source_universes": {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
            }
            for universe_ref, specification in upstream_universes.items()
        },
        "st12e_certified_source_universes": {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
                "authority_created": False,
            }
            for universe_ref, specification in st12e_universes.items()
        },
        "closure_ids": [row["closure_id"] for row in ST12E_CLOSURE_ROWS],
        "repository_disposition_ids": list(ST12E_REPOSITORY_DISPOSITIONS),
        "reused_math_oracle_vector_refs": [
            list(row) for row in ST12E_REUSED_MATH_PACK
        ],
        "semantic_test_ids": [
            row["test_id"] for row in ST12E_SEMANTIC_TEST_ROWS
        ],
        "validation_commands": list(ST12E_CERTIFIED_COMMANDS),
        "owner_action_ids": list(current_owner_action_ids()),
        "implemented_operation_ids": list(IMPLEMENTED_OPERATION_IDS),
        "held_operation_ids": list(HELD_OPERATION_IDS),
        "no_trade_reoptimization_variable_ids": list(
            NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
        ),
        "quantum_formulation_required_fields": list(
            QUANTUM_FORMULATION_FIELDS
        ),
        "llm_advisory_task_fields": list(LLM_ADVISORY_TASK_FIELDS),
        "agent_orch_source_prefix": AGENT_ORCH_PREFIX,
        "central_validator_ref": CENTRAL_VALIDATOR_REF,
        "identity_join_state": "EXACT_OR_TYPED_UNMAPPED_NO_AUTHORITY",
        "qku_formula_mutation_authorized": False,
        "trade_plan_candidate_is_only_mutable_optimization_object": True,
        "no_trade_reoptimization_route_preserved": True,
        "memory_is_condition_scoped_prior_only": True,
        "llm_inference_allowed": False,
        "quantum_mapping_or_execution_allowed": False,
        "raw_jsonl_request_time_scan_allowed": False,
        "no_effect_authority_closed": no_effect_authority_is_closed(),
        "terminal_route": "NO_EFFECT_ELIGIBILITY_OR_TYPED_DENIAL",
    }
    return manifest, policy_rows, scope_rows


def _st12d_input_member(
    *,
    member_ref: str,
    input_class: str,
    semantic_owner_ref: str,
    producer_path_or_interface: str,
    exact_fields_or_refs: tuple[str, ...],
    downstream_predicate_or_field: tuple[str, ...],
    mutation_test_ref_or_explicit_not_material: str,
    terminal_disposition: str,
) -> dict[str, object]:
    return {
        "member_ref": member_ref,
        "input_class": input_class,
        "semantic_owner_ref": semantic_owner_ref,
        "producer_path_or_interface": producer_path_or_interface,
        "exact_fields_or_refs": exact_fields_or_refs,
        "downstream_predicate_or_field": downstream_predicate_or_field,
        "mutation_test_ref_or_explicit_not_material": (
            mutation_test_ref_or_explicit_not_material
        ),
        "terminal_disposition": terminal_disposition,
        "runtime_effect_authorized": False,
        "order_release_authorized": False,
    }


def _build_st12d_input_universe() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in ST12D_CLOSURE_ROWS:
        case = ST12D_ACTUAL_CONTROL_MUTATION_CASES[str(row["control_id"])]
        rows.append(
            _st12d_input_member(
                member_ref=str(row["closure_id"]),
                input_class="closure_control",
                semantic_owner_ref=case.control_id,
                producer_path_or_interface=case.grouped_module,
                exact_fields_or_refs=(
                    str(row["control_id"]),
                    str(row["predicate_ref"]),
                    case.causal_owner_field_ref,
                    case.expected_positive_terminal_state,
                    case.expected_negative_reason_or_terminal_state,
                ),
                downstream_predicate_or_field=(
                    "run_st12d_actual_control_mutation_case",
                    str(row["predicate_ref"]),
                    case.expected_positive_terminal_state,
                ),
                mutation_test_ref_or_explicit_not_material=(
                    case.causal_mutation_ref
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for historical_path, disposition, current_owner_paths in ST12D_HISTORICAL_PATH_DISPOSITIONS:
        rows.append(
            _st12d_input_member(
                member_ref=f"HISTORICAL-PATH::{historical_path}",
                input_class="historical_path_disposition",
                semantic_owner_ref="QKUComputationControlPlaneV1",
                producer_path_or_interface="freeze/PATH_DISPOSITION.jsonl",
                exact_fields_or_refs=(historical_path, disposition),
                downstream_predicate_or_field=(current_owner_paths,),
                mutation_test_ref_or_explicit_not_material=(
                    "EXPLICIT_NOT_MATERIAL_WITH_PROOF::PATH_DISPOSITION_ONLY"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for parameter_id, binding in ST12D_PARAMETER_APPLICATION_BINDINGS.items():
        rows.append(
            _st12d_input_member(
                member_ref=f"PARAMETER-BINDING::{parameter_id}",
                input_class="parameter_binding",
                semantic_owner_ref=(
                    "QKUComputationControlPlaneV1.ComputationParameterPolicyV1"
                ),
                producer_path_or_interface="ParameterPolicyResolverV1",
                exact_fields_or_refs=(
                    parameter_id,
                    binding.authoritative_value_policy_ref,
                    *binding.current_source_binding_refs,
                ),
                downstream_predicate_or_field=(
                    "FormulaRuntimeSnapshotCandidateV1.parameter_value_refs",
                    "ModeSnapshotDecisionV1.parameter_policy_snapshot_ref",
                    binding.d_application_class,
                    binding.snapshot_binding_class,
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_integration_snapshot_matrix.py"
                ),
                terminal_disposition=(
                    "CONSUMED_BY_D_CANDIDATE"
                    if binding.d_application_class
                    == "IMMUTABLE_D_SNAPSHOT_INPUT_BINDING"
                    else "CONSUMED_BY_D_VALIDATION_OR_PROJECTION"
                ),
            )
        )
    for math_id, implementation in ST12D_MATH_IMPLEMENTATION_REGISTRY.items():
        rows.append(
            _st12d_input_member(
                member_ref=f"MATH-COMPONENT::{math_id}",
                input_class="math_component",
                semantic_owner_ref="QKUComputationControlPlaneV1",
                producer_path_or_interface=(
                    "CURRENT_IMPLEMENTATION_REGISTRY/ST12D_MATH_IMPLEMENTATION_REGISTRY"
                ),
                exact_fields_or_refs=(
                    math_id,
                    implementation.contract.implementation_id,
                ),
                downstream_predicate_or_field=(
                    "FormulaRuntimeSnapshotCandidateV1.formula_spec_refs",
                    "FormulaRuntimeSnapshotCandidateV1.implementation_version_pins",
                    "RegisteredSnapshotComputationBundleV1.component_closures",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_integration_snapshot_matrix.py"
                ),
                terminal_disposition="CONSUMED_BY_D_CANDIDATE",
            )
        )
        rows.append(
            _st12d_input_member(
                member_ref=f"INDEPENDENT-ORACLE::{math_id}",
                input_class="independent_oracle",
                semantic_owner_ref="QKUComputationControlPlaneV1.OracleContractV1",
                producer_path_or_interface="ST12D_ORACLE_BY_MATH_ID",
                exact_fields_or_refs=(ST12D_ORACLE_BY_MATH_ID[math_id].oracle_id,),
                downstream_predicate_or_field=(
                    "four_dimensional_computability.fixture_state",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tools/independent_validate_qku_computation_control_plane_d.py"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
        rows.append(
            _st12d_input_member(
                member_ref=f"GOLDEN-VECTOR::{math_id}",
                input_class="golden_vector",
                semantic_owner_ref="QKUComputationControlPlaneV1.GoldenVectorV1",
                producer_path_or_interface="ST12D_GOLDEN_VECTOR_BY_MATH_ID",
                exact_fields_or_refs=(
                    ST12D_GOLDEN_VECTOR_BY_MATH_ID[math_id].vector_id,
                ),
                downstream_predicate_or_field=(
                    "four_dimensional_computability.fixture_state",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tools/independent_validate_qku_computation_control_plane_d.py"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for row in ST12D_SEMANTIC_TEST_ROWS:
        mapped_ref = str(row["mapped_control_case_or_validator_ref"])
        rows.append(
            _st12d_input_member(
                member_ref=str(row["test_id"]),
                input_class="semantic_test",
                semantic_owner_ref=mapped_ref,
                producer_path_or_interface=str(row["grouped_module"]),
                exact_fields_or_refs=(
                    str(row["test_id"]),
                    mapped_ref,
                    str(row["predicate_ref"]),
                    str(row["causal_owner_field_ref"]),
                    str(row["expected_terminal_state"]),
                ),
                downstream_predicate_or_field=(
                    "adjudicate_st12d_semantic_test",
                    mapped_ref,
                    str(row["expected_terminal_state"]),
                ),
                mutation_test_ref_or_explicit_not_material=(
                    str(row["causal_mutation_ref"])
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for command_id, command in enumerate(ST12D_CERTIFIED_COMMANDS, start=1):
        rows.append(
            _st12d_input_member(
                member_ref=f"CERTIFIED-COMMAND::{command_id:02d}",
                input_class="certified_command",
                semantic_owner_ref="QKUComputationControlPlaneV1.validation",
                producer_path_or_interface="freeze/VALIDATION_PLAN.json",
                exact_fields_or_refs=(command,),
                downstream_predicate_or_field=("implementation_time_validation_route",),
                mutation_test_ref_or_explicit_not_material=(
                    "EXPLICIT_NOT_MATERIAL_WITH_PROOF::COMMAND_INVENTORY"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for dimension, states in D_MODE_STATE_REGISTRY.items():
        for state in states:
            rows.append(
                _st12d_input_member(
                    member_ref=f"MODE-STATE::{dimension}::{state}",
                    input_class="mode_state",
                    semantic_owner_ref="QKUComputationControlPlaneV1",
                    producer_path_or_interface="D_MODE_STATE_REGISTRY",
                    exact_fields_or_refs=(dimension, state),
                    downstream_predicate_or_field=(
                        "ModeSnapshotDecisionV1",
                        "SnapshotTransitionProposalV1.proposed_state",
                    ),
                    mutation_test_ref_or_explicit_not_material=(
                        "tests/stage1_prediction_markets/qku_computation_control_plane/"
                        "test_policy_state_matrix.py"
                    ),
                    terminal_disposition="CONSUMED_BY_D_CANDIDATE",
                )
            )
    for transition in MODE_SNAPSHOT_TRANSITIONS:
        rows.append(
            _st12d_input_member(
                member_ref=f"MODE-TRANSITION::{transition.transition_id}",
                input_class="mode_transition",
                semantic_owner_ref="QKUComputationControlPlaneV1",
                producer_path_or_interface="MODE_SNAPSHOT_TRANSITIONS",
                exact_fields_or_refs=(
                    transition.source_state,
                    transition.destination_state,
                    transition.reason_code.name,
                ),
                downstream_predicate_or_field=(
                    "SnapshotTransitionProposalV1.transition_id",
                    "SnapshotTransitionProposalV1.typed_reason_codes",
                    transition.terminal_route,
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_policy_state_matrix.py"
                ),
                terminal_disposition="CONSUMED_BY_D_CANDIDATE",
            )
        )
    for dimension in D_REQUIRED_PIN_DIMENSIONS:
        rows.append(
            _st12d_input_member(
                member_ref=f"PIN-DIMENSION::{dimension}",
                input_class="pin_dimension",
                semantic_owner_ref="QKUComputationControlPlaneV1",
                producer_path_or_interface="freeze/PINNING_POLICY.json",
                exact_fields_or_refs=(dimension,),
                downstream_predicate_or_field=(
                    "validate_candidate_pin_identity",
                    "FormulaRuntimeSnapshotCandidateV1",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_integration_snapshot_matrix.py"
                ),
                terminal_disposition="CONSUMED_BY_D_CANDIDATE",
            )
        )
    for source_ref in _ST12D_FROZEN_CONTRACT_POLICY_REFS:
        rows.append(
            _st12d_input_member(
                member_ref=f"FROZEN-CONTRACT-POLICY::{source_ref}",
                input_class="frozen_contract_policy_file",
                semantic_owner_ref="ST12D_OWNER_FREEZE",
                producer_path_or_interface=source_ref,
                exact_fields_or_refs=(source_ref,),
                downstream_predicate_or_field=("builder_and_independent_validation",),
                mutation_test_ref_or_explicit_not_material=(
                    "EXPLICIT_NOT_MATERIAL_WITH_PROOF::OWNER_FREEZE_REFERENCE_ONLY"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for owner_ref, interface_ref, field_refs in _ST12D_CURRENT_OWNER_INTERFACES:
        rows.append(
            _st12d_input_member(
                member_ref=owner_ref,
                input_class="current_owner_interface",
                semantic_owner_ref=owner_ref,
                producer_path_or_interface=interface_ref,
                exact_fields_or_refs=tuple(field_refs.split(",")),
                downstream_predicate_or_field=(
                    "ModeSnapshotCandidateInputsV1",
                    "ModeSnapshotDecisionV1",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_integration_snapshot_matrix.py"
                ),
                terminal_disposition="CONSUMED_BY_D_CANDIDATE",
            )
        )
    for path in _ST12D_VALIDATION_OWNER_PATHS:
        rows.append(
            _st12d_input_member(
                member_ref=f"VALIDATION-OWNER::{path}",
                input_class="validation_currentization_owner",
                semantic_owner_ref="QKUComputationControlPlaneV1.validation",
                producer_path_or_interface=path,
                exact_fields_or_refs=(
                    path,
                    "DETERMINISTIC_REBUILD_MATCH",
                    "INDEPENDENT_CONTENT_VALIDATION",
                ),
                downstream_predicate_or_field=("D_validation_or_currentization_route",),
                mutation_test_ref_or_explicit_not_material=(
                    "EXPLICIT_NOT_MATERIAL_WITH_PROOF::VALIDATION_OWNER"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for output_ref, schema_ref in _ST12D_RUNTIME_OUTPUTS:
        rows.append(
            _st12d_input_member(
                member_ref=output_ref,
                input_class="runtime_no_effect_output",
                semantic_owner_ref="QKUComputationControlPlaneV1",
                producer_path_or_interface=schema_ref,
                exact_fields_or_refs=(schema_ref,),
                downstream_predicate_or_field=(
                    "submit_candidate_proposal.no_effect_result",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tests/stage1_prediction_markets/qku_computation_control_plane/"
                    "test_integration_snapshot_matrix.py"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    for path in ST12D_GENERATED_PROJECTION_PATHS:
        rows.append(
            _st12d_input_member(
                member_ref=f"GENERATED-OUTPUT::{path}",
                input_class="generated_audit_output",
                semantic_owner_ref="QKUComputationControlPlaneV1.validation",
                producer_path_or_interface="tools/build_qku_computation_control_plane.py",
                exact_fields_or_refs=(
                    path,
                    "DETERMINISTIC_REBUILD_MATCH",
                    "INDEPENDENT_CONTENT_VALIDATION",
                ),
                downstream_predicate_or_field=(
                    "independent_D_validator",
                    "changed_area_validation_router",
                ),
                mutation_test_ref_or_explicit_not_material=(
                    "tools/independent_validate_qku_computation_control_plane_d.py"
                ),
                terminal_disposition="CONSUMED_BY_D_VALIDATION_OR_PROJECTION",
            )
        )
    result = tuple(rows)
    member_refs = tuple(str(row["member_ref"]) for row in result)
    if len(member_refs) != len(set(member_refs)):
        raise ValueError("ST12-D input-universe member identities must be unique")
    return result


def _build_st12d_audit_bundle() -> tuple[
    RegisteredSnapshotComputationBundleV1,
    CanonicalOwnerPacketRegistryV1,
]:
    """Build a deterministic typed audit fixture, then run the real preflight."""

    raw_math39 = json.loads(
        ST12D_GOLDEN_VECTOR_BY_MATH_ID["MATH-39"].inputs_json
    )
    raw_ack = raw_math39["order_ack"]
    acknowledged_at = datetime.fromisoformat(str(raw_ack["acknowledged_at"]))
    as_of = acknowledged_at + timedelta(seconds=2)
    observed = acknowledged_at - timedelta(seconds=2)
    scope = ComputationScopeV1(
        market_scope_id="MARKET::ST12D::AUDIT",
        venue_scope_id=str(raw_ack["venue_id"]),
        event_scope_id="EVENT::ST12D::AUDIT",
        instrument_or_contract_scope_id=str(raw_ack["instrument_id"]),
        mode_context_id="SAFE_CLASSICAL",
        input_snapshot_id="SNAPSHOT::ST12D::AUDIT",
    )
    context = ComputationExecutionContextV1(
        context_id="CONTEXT::ST12D::BUILDER_AUDIT",
        as_of=as_of,
        observed_at=observed,
        source_epoch_id="SOURCE-EPOCH::ST12D::BUILDER_AUDIT",
        input_version="ST12D-BUILDER-AUDIT-V1",
        maximum_age=timedelta(days=1),
        scope=scope,
        binding_profile_version="3.4",
        parameter_policy_version="3.4",
        implementation_versions=tuple(
            ImplementationVersionPinV1(
                math_spec_id=math_id,
                implementation_id=implementation.contract.implementation_id,
            )
            for math_id, implementation in ST12D_MATH_IMPLEMENTATION_REGISTRY.items()
        ),
    )
    clocks = PointInTimeClocksV1(
        observed_time=observed,
        effective_time=observed,
        available_time=acknowledged_at + timedelta(seconds=1),
        received_time=acknowledged_at + timedelta(seconds=1),
        processed_time=acknowledged_at + timedelta(seconds=1),
        as_of_time=as_of,
    )
    packets: list[OwnerValuePacketV1] = []
    for math_id in ("MATH-13", "MATH-14", "MATH-15"):
        vector_inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
        for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]:
            packets.append(
                OwnerValuePacketV1(
                    packet_id=f"PACKET::ST12D-AUDIT::{binding.binding_id}",
                    owner_id=binding.accepted_upstream_owner_id,
                    packet_type=binding.accepted_packet_or_snapshot_type,
                    schema_id=binding.schema_id,
                    schema_version=binding.schema_version,
                    context_id=context.context_id,
                    scope=context.scope,
                    source_epoch_id=context.source_epoch_id,
                    input_version=context.input_version,
                    clocks=clocks,
                    ttl=timedelta(days=1),
                    values={binding.exact_field_path: vector_inputs[binding.input_name]},
                    authorized_binding_ids=(binding.binding_id,),
                    producer_receipt_id=f"RECEIPT::ST12D-AUDIT::{binding.binding_id}",
                    producer_receipt_type=binding.producer_receipt_type,
                    source_state_and_claim_lineage=(
                        binding.source_state_and_claim_lineage
                    ),
                    provider_sequence=1,
                    revision=1,
                )
            )
    ack_receipt_ref = "RECEIPT::ST12D-AUDIT::MATH39-ACK"
    book_receipt_ref = "RECEIPT::ST12D-AUDIT::MATH39-BOOK"
    acknowledgement = Math39OrderAcknowledgementV1(
        order_id=str(raw_ack["order_id"]),
        venue_id=str(raw_ack["venue_id"]),
        instrument_id=str(raw_ack["instrument_id"]),
        side=str(raw_ack["side"]),
        price=Decimal(str(raw_ack["price"])),
        acknowledged_at=acknowledged_at,
        available_at=acknowledged_at,
        matching_priority=str(raw_ack["matching_priority"]),
        venue_evidence_ref=str(raw_ack["venue_evidence_ref"]),
        unit=str(raw_ack["unit"]),
        basis=str(raw_ack["basis"]),
        producer_receipt_ref=ack_receipt_ref,
    )
    event_rows: list[Math39SequencedBookEventV1] = []
    for position, raw_event in enumerate(raw_math39["sequenced_book_events"]):
        kind = Math39BookEventKindV1(str(raw_event["event_kind"]))
        event_time = (
            acknowledged_at - timedelta(seconds=1)
            if kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            else acknowledged_at + timedelta(milliseconds=100 * position)
        )
        event_rows.append(
            Math39SequencedBookEventV1(
                event_id=str(raw_event["event_id"]),
                sequence=int(raw_event["sequence"]),
                event_kind=kind,
                venue_id=acknowledgement.venue_id,
                instrument_id=acknowledgement.instrument_id,
                side=acknowledgement.side,
                price=acknowledgement.price,
                quantity=Decimal(str(raw_event["quantity"])),
                event_time=event_time,
                available_at=event_time,
                priority_order_id=acknowledgement.order_id,
                venue_evidence_ref=acknowledgement.venue_evidence_ref,
                unit=acknowledgement.unit,
                basis=acknowledgement.basis,
                producer_receipt_ref=book_receipt_ref,
            )
        )
    for binding, value, packet_id, receipt_ref, sequence, revision in (
        (
            ST12D_MATH39_RAW_INPUT_BINDINGS[0],
            tuple(event_rows),
            "PACKET::ST12D-AUDIT::MATH39-BOOK",
            book_receipt_ref,
            event_rows[-1].sequence,
            None,
        ),
        (
            ST12D_MATH39_RAW_INPUT_BINDINGS[1],
            acknowledgement,
            "PACKET::ST12D-AUDIT::MATH39-ACK",
            ack_receipt_ref,
            None,
            1,
        ),
    ):
        packets.append(
            OwnerValuePacketV1(
                packet_id=packet_id,
                owner_id=binding.accepted_upstream_owner_id,
                packet_type=binding.accepted_packet_or_snapshot_type,
                schema_id=binding.schema_id,
                schema_version=binding.schema_version,
                context_id=context.context_id,
                scope=context.scope,
                source_epoch_id=context.source_epoch_id,
                input_version=context.input_version,
                clocks=clocks,
                ttl=timedelta(days=1),
                values={binding.exact_field_path: value},
                authorized_binding_ids=(binding.binding_id,),
                producer_receipt_id=receipt_ref,
                producer_receipt_type=binding.producer_receipt_type,
                source_state_and_claim_lineage=binding.source_state_and_claim_lineage,
                provider_sequence=sequence,
                revision=revision,
            )
        )
    audit_parameter_values: dict[str, object] = {
        "ST10-PARAM::0764": Decimal("0.04"),
        "ST10-PARAM::0940": Decimal("0.03"),
        "ST10-PARAM::1946": "OPEN_OR_CLOSE_FROM_PRETRADE_POSITION_SNAPSHOT",
        "ST10-PARAM::2117": "BOLO::ST12D-AUDIT::1",
        "ST10-PARAM::2157": "ETF-BASKET::ST12D-AUDIT::1",
        "ST10-PARAM::3490": "FEE-TIER::ST12D-AUDIT::1",
        "ST10-PARAM::3598": "BOOK-FRESHNESS::ST12D-AUDIT::CURRENT",
        "ST10-PARAM::3639": Decimal("1.5"),
    }
    if set(audit_parameter_values) != set(ST12D_OWNER_RESOLVED_PARAMETER_IDS):
        raise ValueError("ST12-D audit fixture must cover every owner-resolved parameter")
    for parameter_id in ST12D_SNAPSHOT_PARAMETER_BINDING_IDS:
        if parameter_id not in ST12D_OWNER_RESOLVED_PARAMETER_IDS:
            continue
        policy = ST12D_PARAMETER_POLICIES[parameter_id]
        binding_id = st12d_snapshot_parameter_binding_id(parameter_id)
        packets.append(
            OwnerValuePacketV1(
                packet_id=f"PACKET::ST12D-AUDIT::PARAMETER::{parameter_id}",
                owner_id=policy.canonical_owner,
                packet_type=ST12D_PARAMETER_VALUE_PACKET_TYPE,
                schema_id=ST12D_PARAMETER_VALUE_PACKET_SCHEMA_ID,
                schema_version=ST12D_PARAMETER_VALUE_PACKET_SCHEMA_VERSION,
                context_id=context.context_id,
                scope=context.scope,
                source_epoch_id=context.source_epoch_id,
                input_version=context.input_version,
                clocks=clocks,
                ttl=timedelta(days=1),
                values={
                    st12d_snapshot_parameter_field_path(parameter_id): (
                        audit_parameter_values[parameter_id]
                    )
                },
                authorized_binding_ids=(binding_id,),
                producer_receipt_id=(
                    f"RECEIPT::ST12D-AUDIT::PARAMETER::{parameter_id}"
                ),
                producer_receipt_type=ST12D_PARAMETER_VALUE_PACKET_TYPE,
                source_state_and_claim_lineage=(
                    st12d_snapshot_parameter_source_lineage(parameter_id)
                ),
                revision=1,
            )
        )
    registry = CanonicalOwnerPacketRegistryV1(tuple(packets))
    resolved_parameter_values = resolve_st12d_snapshot_parameter_values(
        context=context,
        owner_registry=registry,
    )
    bundle = preflight_snapshot_computation_bundle(
        context=context,
        owner_registry=registry,
        parameter_policy_snapshot_ref="ComputationParameterPolicyV1::3.4",
        parameter_value_refs=tuple(
            row.resolved_value_ref for row in resolved_parameter_values
        ),
        resolved_parameter_values=resolved_parameter_values,
        source_epoch_refs=(context.source_epoch_id,),
    )
    return bundle, registry


def _build_st12d_computability_rows() -> tuple[dict[str, object], ...]:
    bundle, registry = _build_st12d_audit_bundle()
    rows: list[dict[str, object]] = []
    for math_id in ST12D_MATH_IMPLEMENTATION_REGISTRY:
        snapshot = FrozenContextualComputabilityResolverV1.resolve(
            math_id,
            context=bundle.execution_context,
            owner_registry=registry,
            snapshot_bundle=bundle,
        )
        dimensions = (
            snapshot.resolution.specification,
            snapshot.resolution.fixture,
            snapshot.resolution.context,
            snapshot.resolution.stack,
        )
        rows.append(
            {
                "component_ref": math_id,
                "specification_state": dimensions[0].state.value,
                "fixture_state": dimensions[1].state.value,
                "context_state": dimensions[2].state.value,
                "stack_state": dimensions[3].state.value,
                "dimension_computable": tuple(row.computable for row in dimensions),
                "dimension_producer_receipt_refs": tuple(
                    {
                        "dimension": row.state.value,
                        "dependency_receipt_refs": row.dependency_receipt_refs,
                        "oracle_receipt_refs": row.oracle_receipt_refs,
                    }
                    for row in dimensions
                ),
                "implementation_ref_or_explicit_absence": (
                    ST12D_MATH_IMPLEMENTATION_REGISTRY[
                        math_id
                    ].contract.implementation_id
                ),
                "oracle_and_vector_refs": (
                    ST12D_ORACLE_BY_MATH_ID[math_id].oracle_id,
                    ST12D_GOLDEN_VECTOR_BY_MATH_ID[math_id].vector_id,
                ),
                "input_owner_and_source_refs": (
                    *snapshot.input_resolution.packet_refs,
                    *snapshot.input_resolution.receipt_refs,
                    *bundle.source_epoch_refs,
                ),
                "parameter_policy_refs": (
                    bundle.parameter_policy_snapshot_ref,
                    *bundle.parameter_value_refs,
                ),
                "selected_snapshot_bundle_ref": bundle.bundle_ref,
                "dependency_graph_ref": "EXPLICIT_ABSENCE_NO_FABRICATED_DATA_EDGE",
                "consumer_ref": "FormulaRuntimeSnapshotCandidateV1.formula_spec_refs",
                "blocking_reason_codes": tuple(
                    reason.value
                    for row in dimensions
                    for reason in row.blocker_codes
                ),
                "materialization_owner_ref_or_explicit_absence": "EXPLICIT_ABSENCE",
                "fallback_or_no_trade_route": (
                    "REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE"
                ),
                "terminal_disposition": (
                    "ADMIT_ONLY_WHEN_ALL_FOUR_STATES_TRUE"
                    if all(row.computable for row in dimensions)
                    else "BLOCK_WITH_EXACT_DIMENSION_RECEIPTS"
                ),
                "runtime_effect_authorized": False,
                "order_release_authorized": False,
            }
        )
    return tuple(rows)


def _build_st12d_connectivity(
    universe: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    principal_bound_classes = {
        "runtime_no_effect_output",
    }
    for item in universe:
        member_ref = str(item["member_ref"])
        input_class = str(item["input_class"])
        candidate_consumed = item["terminal_disposition"] == "CONSUMED_BY_D_CANDIDATE"
        runtime_route = _ST12D_RUNTIME_OPERATIONAL_CONNECTIVITY.get(member_ref)
        if runtime_route is not None:
            downstream_consumer_refs, consumer_acknowledgment, terminal_route = (
                runtime_route
            )
        elif candidate_consumed:
            downstream_consumer_refs = (
                "FormulaRuntimeSnapshotCandidateV1",
                "ModeSnapshotDecisionV1",
            )
            consumer_acknowledgment = "EXPLICIT_ABSENCE"
            terminal_route = "ADMIT_EXACT_PIN_OR_TYPED_BLOCKER"
        else:
            downstream_consumer_refs = (
                "tools/independent_validate_qku_computation_control_plane_d.py",
            )
            consumer_acknowledgment = "EXPLICIT_ABSENCE"
            terminal_route = "VALIDATE_OR_FAIL_CLOSED"
        rows.append(
            {
                "semantic_ref": f"CONNECTIVITY::{member_ref}",
                "artifact_ref": member_ref,
                "artifact_or_row_class": input_class,
                "canonical_identity_refs": (member_ref,),
                "semantic_owner": str(item["semantic_owner_ref"]),
                "implementation_owner": (
                    "tools/build_qku_computation_control_plane.py"
                    if input_class == "generated_audit_output"
                    else "QKUComputationControlPlaneV1"
                ),
                "producer_path_or_interface": str(
                    item["producer_path_or_interface"]
                ),
                "exact_upstream_fields_or_refs_consumed": tuple(
                    item["exact_fields_or_refs"]
                ),
                "upstream_refs": tuple(item["exact_fields_or_refs"]),
                "current_value_owner_ref_or_explicit_absence": (
                    "QKUComputationControlPlaneV1.ComputationParameterPolicyV1"
                    if input_class == "parameter_binding"
                    else "EXPLICIT_ABSENCE"
                ),
                "current_principal_and_duty_refs_or_explicit_absence": (
                    (
                        "AgentCapabilityDecisionV1.principal_id",
                        "AgentCapabilityDecisionV1.current_agent_id",
                        "AgentCapabilityDecisionV1.task_id",
                        "AGENT_ORCH1.task_envelope.duty_ref",
                    )
                    if input_class in principal_bound_classes
                    or member_ref in {"OWNER::ST12E-ADMISSION", "OWNER::AGENT-ORCH1"}
                    else "EXPLICIT_ABSENCE"
                ),
                "downstream_D_contract_fields_affected": tuple(
                    item["downstream_predicate_or_field"]
                ),
                "downstream_consumer_refs": downstream_consumer_refs,
                "consumer_acknowledgment_ref_or_explicit_absence": (
                    consumer_acknowledgment
                ),
                "schema_ref": (
                    "DInputUniverseReceiptV1::BUILDER_AUDIT_SCHEMA"
                ),
                "validator_ref": (
                    "tools/independent_validate_qku_computation_control_plane_d.py"
                ),
                "mutation_test_ref_or_explicit_not_material": str(
                    item["mutation_test_ref_or_explicit_not_material"]
                ),
                "computability_disposition_ref_or_explicit_absence": (
                    f"COMPUTABILITY::{member_ref.rsplit('::', 1)[-1]}"
                    if input_class == "math_component"
                    else "EXPLICIT_ABSENCE"
                ),
                "terminal_disposition": str(item["terminal_disposition"]),
                "terminal_route": terminal_route,
                "consumption_status": "TERMINAL",
                "runtime_effect_authorized": False,
                "order_release_authorized": False,
            }
        )
    return tuple(rows)


def build_st12d_projections() -> ST12DProjectionSet:
    """Build compact D audit projections without copying owner value bodies."""

    control_rows = tuple(dict(row) for row in ST12D_CLOSURE_ROWS)
    parameter_rows = tuple(
        {
            "parameter_id": parameter_id,
            "parameter_symbol": binding.parameter_symbol,
            "d_application_class": binding.d_application_class,
            "snapshot_binding_class": binding.snapshot_binding_class,
            "current_source_binding_refs": binding.current_source_binding_refs,
            "authoritative_value_policy_ref": binding.authoritative_value_policy_ref,
            "canonical_value_owner": ST12D_PARAMETER_POLICIES[
                parameter_id
            ].canonical_owner,
            "value_mutation_authorized_by_st12d": False,
        }
        for parameter_id, binding in ST12D_PARAMETER_APPLICATION_BINDINGS.items()
    )
    state_rows = tuple(
        {
            "dimension": dimension,
            "state": state,
            "runtime_effect_authorized": False,
            "order_release_authorized": False,
        }
        for dimension, states in D_MODE_STATE_REGISTRY.items()
        for state in states
    )
    transition_rows = tuple(
        {
            "transition_id": row.transition_id,
            "source_state": row.source_state,
            "destination_state": row.destination_state,
            "trigger": row.trigger,
            "reason_code": row.reason_code.name,
            "terminal_route": row.terminal_route,
            "owner_confirmation_required": row.owner_confirmation_required,
            "mutation_allowed": False,
            "active_pointer_commit_allowed": False,
            "runtime_effect_authorized": False,
            "order_release_authorized": False,
        }
        for row in MODE_SNAPSHOT_TRANSITIONS
    )
    universe = _build_st12d_input_universe()
    computability = _build_st12d_computability_rows()
    connectivity = _build_st12d_connectivity(universe)
    counts = dict(st12d_acceptance_counts())
    count_by_class = {
        input_class: sum(row["input_class"] == input_class for row in universe)
        for input_class in sorted({str(row["input_class"]) for row in universe})
    }
    terminal_counts = {
        disposition: sum(
            row["terminal_disposition"] == disposition for row in connectivity
        )
        for disposition in sorted(
            {str(row["terminal_disposition"]) for row in connectivity}
        )
    }
    computability_unresolved_count = sum(
        not all(row["dimension_computable"]) for row in computability
    )
    material_universe = tuple(
        row
        for row in universe
        if not str(row["mutation_test_ref_or_explicit_not_material"]).startswith(
            "EXPLICIT_NOT_MATERIAL_WITH_PROOF::"
        )
    )
    value_level_gap_count = sum(
        not row["exact_fields_or_refs"] or not row["downstream_predicate_or_field"]
        for row in material_universe
    )
    path_existence_only_count = sum(
        len(row["exact_fields_or_refs"]) == 1
        and row["exact_fields_or_refs"][0]
        == row["producer_path_or_interface"]
        and "/" in str(row["producer_path_or_interface"])
        for row in material_universe
    )
    connected_artifacts = {
        str(row["artifact_ref"])
        for row in connectivity
        if (
            bool(row["downstream_consumer_refs"])
            and (
                row["artifact_or_row_class"] != "runtime_no_effect_output"
                or (
                    all(
                        "independent_validate" not in str(consumer)
                        for consumer in row["downstream_consumer_refs"]
                    )
                    and row[
                        "consumer_acknowledgment_ref_or_explicit_absence"
                    ]
                    != "EXPLICIT_ABSENCE"
                )
            )
        )
        or row["terminal_disposition"]
        == "ROUTED_TO_NAMED_LATER_OWNER_WITH_NO_D_EFFECT"
    }
    orphan_count = len(
        {str(row["member_ref"]) for row in universe} - connected_artifacts
    )
    future_handoff_count = sum(
        row["consumption_status"] != "TERMINAL" for row in connectivity
    )
    metadata_only_completion_count = sum(
        row["terminal_disposition"] == "CONSUMED_BY_D_CANDIDATE"
        and not row["exact_upstream_fields_or_refs_consumed"]
        for row in connectivity
    )
    active_pointer_commit_count = sum(
        bool(row["active_pointer_commit_allowed"]) for row in transition_rows
    )
    runtime_effect_count = sum(
        bool(row["runtime_effect_authorized"])
        for rows in (control_rows, state_rows, transition_rows, universe, connectivity)
        for row in rows
        if "runtime_effect_authorized" in row
    )
    order_release_count = sum(
        bool(row["order_release_authorized"])
        for rows in (control_rows, state_rows, transition_rows, universe, connectivity)
        for row in rows
        if "order_release_authorized" in row
    )
    control_mutation_results = tuple(
        run_st12d_actual_control_mutation_case(control_id)
        for control_id in ST12D_ACTUAL_CONTROL_MUTATION_CASES
    )
    mutation_result_by_control = {
        row.control_id: row for row in control_mutation_results
    }
    actual_control_positive_pass_count = sum(
        row.positive_passed for row in control_mutation_results
    )
    actual_control_mutation_rejection_count = sum(
        row.actual_mutation_rejected for row in control_mutation_results
    )
    semantic_test_pass_count = sum(
        adjudicate_st12d_semantic_test(str(row["test_id"]))
        for row in ST12D_SEMANTIC_TEST_ROWS
    )
    resolver_authority_result = mutation_result_by_control["ST11-EXECUTION::012"]
    receipt_ontology_result = mutation_result_by_control["ST11-EXECUTION::013"]
    source_epoch_ontology_result = mutation_result_by_control[
        "ST11-EXECUTION::014"
    ]
    stage_transition_result = mutation_result_by_control["ST11-SECURITY::012"]
    canonical_current_resolver_enforced_count = int(
        resolver_authority_result.positive_passed
    )
    custom_resolver_bypass_count = int(
        not resolver_authority_result.actual_mutation_rejected
    )
    executed_transition_trace_gap_count = int(
        not stage_transition_result.positive_passed
    )
    stage_transition_receipt_mismatch_count = int(
        not stage_transition_result.actual_mutation_rejected
    )
    phantom_receipt_ref_count = int(
        not receipt_ontology_result.actual_mutation_rejected
    )
    synthetic_source_epoch_ref_count = int(
        not source_epoch_ontology_result.actual_mutation_rejected
    )
    synthetic_override_mutation_count = sum(
        row.positive_terminal_state == row.negative_reason_or_terminal_state
        or not row.actual_mutation_rejected
        for row in control_mutation_results
    )
    current_public_methods = {
        name
        for name, value in QKUComputationControlPlaneV1.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    new_public_operation_count = len(
        current_public_methods - set(IMPLEMENTED_OPERATION_IDS)
    )
    universe_text = deterministic_json(universe).casefold()
    conditional_merge_count = int("conditional_merge" in universe_text)
    digest_authority_count = sum(
        token in universe_text for token in ("qtt_checksum", "sha_authority")
    )
    external_discovery_count = sum(
        row["input_class"] == "external_candidate_discovery" for row in universe
    )
    web_search_count = sum(row["input_class"] == "web_search" for row in universe)
    effect_counts = {
        effect: runtime_effect_count
        for effect in (
            "provider",
            "private_state",
            "replay_or_paper_execution",
            "llm_inference",
            "qpu_or_simulator_execution",
        )
    }
    generated_paths = tuple(ST12D_GENERATED_PROJECTION_PATHS)
    expected_paths = tuple(
        f"{ST12D_GENERATED_PREFIX.as_posix()}/{name}"
        for name in (
            "manifest.json",
            "control_closure.jsonl",
            "parameter_binding_refs.jsonl",
            "mode_state_registry.jsonl",
            "transition_matrix.jsonl",
            "d_input_universe.jsonl",
            "computability_dispositions.jsonl",
            "artifact_connectivity.jsonl",
            "validation_summary.json",
        )
    )
    if generated_paths != expected_paths:
        raise ValueError("ST12-D generated path owner does not match the exact nine-file ledger")
    manifest: dict[str, object] = {
        "schema": "DInputUniverseReceiptV1",
        "tranche": "ST12-TRANCHE-D",
        "semantic_owner": "QKUComputationControlPlaneV1",
        "implementation_owner": "tools/build_qku_computation_control_plane.py",
        "acceptance_counts": counts,
        "generated_projection_paths": generated_paths,
        "d_input_universe_count": len(universe),
        "d_input_universe_count_by_class": count_by_class,
        "d_input_universe_unresolved_count": computability_unresolved_count,
        "d_value_level_upstream_consumption_gap_count": value_level_gap_count,
        "d_path_existence_only_consumption_count": path_existence_only_count,
        "artifact_connectivity_terminal_counts": terminal_counts,
        "orphan_d_artifact_count": orphan_count,
        "state_count": len(state_rows),
        "transition_count": len(transition_rows),
        "pin_dimension_count": len(D_REQUIRED_PIN_DIMENSIONS),
        "parameter_value_owner_count": len(
            {row["canonical_value_owner"] for row in parameter_rows}
        ),
        "actual_control_mutation_case_count": len(
            ST12D_ACTUAL_CONTROL_MUTATION_CASES
        ),
        "actual_control_positive_pass_count": actual_control_positive_pass_count,
        "actual_control_mutation_rejection_count": (
            actual_control_mutation_rejection_count
        ),
        "semantic_test_identity_count": len(ST12D_SEMANTIC_TEST_ROWS),
        "semantic_test_pass_count": semantic_test_pass_count,
        "canonical_current_resolver_enforced_count": (
            canonical_current_resolver_enforced_count
        ),
        "custom_resolver_bypass_count": custom_resolver_bypass_count,
        "executed_transition_trace_gap_count": executed_transition_trace_gap_count,
        "stage_transition_receipt_mismatch_count": (
            stage_transition_receipt_mismatch_count
        ),
        "phantom_receipt_ref_count": phantom_receipt_ref_count,
        "synthetic_source_epoch_ref_count": synthetic_source_epoch_ref_count,
        "synthetic_override_mutation_count": synthetic_override_mutation_count,
        "new_public_operation_id_count": new_public_operation_count,
        "agent_policy_edit_count": 0,
        "active_pointer_commit_count": active_pointer_commit_count,
        "runtime_effect_count": runtime_effect_count,
        "order_release_count": order_release_count,
        "manual_edit_allowed": False,
        "runtime_effect_authorized": False,
        "order_release_authorized": False,
    }
    summary: dict[str, object] = {
        "schema": "ST12DValidationSummaryV1",
        "acceptance_counts": counts,
        "d_input_universe_count_by_class": count_by_class,
        "d_input_universe_unresolved_count": computability_unresolved_count,
        "d_value_level_upstream_consumption_gap_count": value_level_gap_count,
        "d_path_existence_only_consumption_count": path_existence_only_count,
        "artifact_connectivity_terminal_counts": terminal_counts,
        "orphan_d_artifact_count": orphan_count,
        "unacknowledged_future_handoff_count": future_handoff_count,
        "unmapped_current_agent_authority_count_for_d_rows": sum(
            row["current_principal_and_duty_refs_or_explicit_absence"]
            == "EXPLICIT_ABSENCE"
            and row["artifact_or_row_class"] == "runtime_no_effect_output"
            for row in connectivity
        ),
        "metadata_only_completion_count": metadata_only_completion_count,
        "active_pointer_commit_count": active_pointer_commit_count,
        "runtime_effect_count": runtime_effect_count,
        "order_release_count": order_release_count,
        "provider_private_replay_paper_llm_qpu_counts": effect_counts,
        "web_search_count": web_search_count,
        "external_candidate_discovery_count": external_discovery_count,
        "conditional_merge_implementation_count": conditional_merge_count,
        "qtt_checksum_or_digest_authority_count": digest_authority_count,
        "actual_control_mutation_case_count": len(
            ST12D_ACTUAL_CONTROL_MUTATION_CASES
        ),
        "actual_control_positive_pass_count": actual_control_positive_pass_count,
        "actual_control_mutation_rejection_count": (
            actual_control_mutation_rejection_count
        ),
        "semantic_test_identity_count": len(ST12D_SEMANTIC_TEST_ROWS),
        "semantic_test_pass_count": semantic_test_pass_count,
        "canonical_current_resolver_enforced_count": (
            canonical_current_resolver_enforced_count
        ),
        "custom_resolver_bypass_count": custom_resolver_bypass_count,
        "executed_transition_trace_gap_count": executed_transition_trace_gap_count,
        "stage_transition_receipt_mismatch_count": (
            stage_transition_receipt_mismatch_count
        ),
        "phantom_receipt_ref_count": phantom_receipt_ref_count,
        "synthetic_source_epoch_ref_count": synthetic_source_epoch_ref_count,
        "synthetic_override_mutation_count": synthetic_override_mutation_count,
        "runtime_effect_authorized": False,
        "order_release_authorized": False,
    }
    return (
        manifest,
        control_rows,
        parameter_rows,
        state_rows,
        transition_rows,
        universe,
        computability,
        connectivity,
        summary,
    )


def _jsonl(rows: tuple[dict[str, object], ...]) -> str:
    return "".join(deterministic_json(row) + "\n" for row in rows)


def _write_generated_if_changed(path: Path, text: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")


def materialize_st12e_projections(
    manifest: dict[str, object],
    policy_rows: tuple[dict[str, object], ...],
    scope_rows: tuple[dict[str, object], ...],
) -> None:
    output_dir = REPO_ROOT / ST12E_GENERATED_PREFIX
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_generated_if_changed(
        output_dir / "manifest.json", deterministic_json(manifest) + "\n"
    )
    _write_generated_if_changed(
        output_dir / "policy.jsonl", _jsonl(policy_rows)
    )
    _write_generated_if_changed(
        output_dir / "parameter_scope.jsonl", _jsonl(scope_rows)
    )


def materialize_st12d_projections(projections: ST12DProjectionSet) -> None:
    (
        manifest,
        control_rows,
        parameter_rows,
        state_rows,
        transition_rows,
        universe,
        computability,
        connectivity,
        summary,
    ) = projections
    output_dir = REPO_ROOT / ST12D_GENERATED_PREFIX
    output_dir.mkdir(parents=True, exist_ok=True)
    json_payloads = {
        "manifest.json": manifest,
        "validation_summary.json": summary,
    }
    jsonl_payloads = {
        "control_closure.jsonl": control_rows,
        "parameter_binding_refs.jsonl": parameter_rows,
        "mode_state_registry.jsonl": state_rows,
        "transition_matrix.jsonl": transition_rows,
        "d_input_universe.jsonl": universe,
        "computability_dispositions.jsonl": computability,
        "artifact_connectivity.jsonl": connectivity,
    }
    for name, payload in json_payloads.items():
        _write_generated_if_changed(
            output_dir / name,
            deterministic_json(payload) + "\n",
        )
    for name, rows in jsonl_payloads.items():
        _write_generated_if_changed(
            output_dir / name,
            _jsonl(rows),
        )


def _st12f_dataclass_row(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def build_st12f_projections() -> dict[str, str]:
    """Build static, non-empirical ST12-F contract projections."""

    replay_fields = tuple(field.name for field in fields(ReplayResultContractV1))
    paper_fields = tuple(field.name for field in fields(PaperResultContractV1))
    lock_fields = tuple(field.name for field in fields(ImmutableReplayPaperInputLockV1))
    divergence_fields = tuple(field.name for field in fields(DivergenceAssessmentV1))
    bundle_fields = tuple(field.name for field in fields(ComputationEvidenceBundleV1))
    cohort_rows = tuple(
        {
            "template_id": template_id,
            "ordinal": index,
            "replay_result_contract_id": ST12F_REPLAY_RESULT_CONTRACT_IDS_V1[index - 1],
            "paper_result_contract_id": ST12F_PAPER_RESULT_CONTRACT_IDS_V1[index - 1],
            "campaign_execution_authorized": False,
            "empirical_evidence": False,
        }
        for index, template_id in enumerate(ST12F_TEMPLATE_IDS_V1, 1)
    )
    replay_rows = tuple(
        {
            "expected_result_contract_id": contract_id,
            "cohort_template_id": ST12F_TEMPLATE_IDS_V1[index],
            "lane": "REPLAY",
            "contract_type": "ReplayResultContractV1",
            "field_roster": replay_fields,
            "empirical_instance_count": 0,
        }
        for index, contract_id in enumerate(ST12F_REPLAY_RESULT_CONTRACT_IDS_V1)
    )
    paper_rows = tuple(
        {
            "expected_result_contract_id": contract_id,
            "cohort_template_id": ST12F_TEMPLATE_IDS_V1[index],
            "lane": "PAPER",
            "contract_type": "PaperResultContractV1",
            "field_roster": paper_fields,
            "empirical_instance_count": 0,
        }
        for index, contract_id in enumerate(ST12F_PAPER_RESULT_CONTRACT_IDS_V1)
    )
    metric_rows = tuple(_st12f_dataclass_row(row) for row in ST12F_EVIDENCE_METRIC_DEFINITIONS_V1)
    identity_rows = tuple(
        {
            "evidence_identity": identity,
            "terminal_disposition_schema": (
                "APPLICABLE_EXECUTED_AND_RECEIPTED",
                "APPLICABLE_BLOCKED_WITH_TYPED_REASON",
                "NOT_APPLICABLE_WITH_PROOF",
            ),
            "actual_disposition": "UNAVAILABLE_NO_EMPIRICAL_INSTANCE",
            "empirical_evidence": False,
        }
        for identity in ST12F_EVIDENCE_IDENTITIES_V1
    )
    review_rows = tuple(
        {"lifecycle_state": state.value, "immutable_version_required": True, "self_review_allowed": False}
        for state in EvidenceBundleTerminalStateV1
    ) + tuple(
        {"review_decision": decision.value, "immutable_version_required": True, "self_review_allowed": False}
        for decision in IndependentReviewDecisionV1
    ) + tuple(
        {
            "from": source.value,
            "to": target.value,
            "guard": guard,
            "immutable_version_required": True,
            "self_review_allowed": False,
        }
        for (source, target), guard in _EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1.items()
    )
    if len(review_rows) != 16:
        raise ValueError("ST12-F independent-review projection must contain exactly 16 rows")
    llm_rows = tuple(
        {"advisory_task": task.value, "preexisting_annotation_only": True, "inference_authorized": False, "numeric_authority": False}
        for task in LLMAdvisoryTaskV1
    )
    model_risk_rows = tuple(
        {"control_id": control_id, "terminal_evidence_required": True, "automatic_promotion_allowed": False}
        for control_id in MODEL_RISK_CONTROL_IDS_V1
    )
    no_trade_rows = tuple(
        {"condition_id": condition_id, "permanent_no_trade_wins_when_active": True}
        for condition_id in NO_TRADE_CONDITION_IDS_V1
    )
    quantum_rows = tuple(_st12f_dataclass_row(row) for row in ST12F_QUANTUM_TRACE_ONLY_BOUNDARIES_V1)
    full_paths = tuple((ST12F_GENERATED_PREFIX / name).as_posix() for name in ST12F_GENERATED_PATHS)
    manifest = {
        "schema": "QTT_ST12F_EVIDENCE_PROJECTION_MANIFEST_V1_4",
        "generated_projection_paths": full_paths,
        "projection_count": 13,
        "template_count": 52,
        "replay_slot_count": 52,
        "paper_slot_count": 52,
        "total_slot_count": 104,
        "parameter_value_ref_count": ST12F_PARAMETER_VALUE_REF_COUNT_V1,
        "evidence_metric_definition_count": 38,
        "evidence_identity_disposition_count": 48,
        "empirical_evidence_count": 0,
        "source_truth_count": 0,
        "runtime_effect_authorized": False,
    }
    summary = {
        "schema": "QTT_ST12F_STATIC_CODE_VALIDATION_SUMMARY_V1_4",
        "static_code_validation_only": True,
        "contract_field_counts": {
            "ImmutableReplayPaperInputLockV1": len(lock_fields),
            "ReplayResultContractV1": len(replay_fields),
            "PaperResultContractV1": len(paper_fields),
            "DivergenceAssessmentV1": len(divergence_fields),
            "ComputationEvidenceBundleV1": len(bundle_fields),
        },
        "empirical_campaign_executed": False,
        "evidence_pass_claimed": False,
        "independent_review_claimed": False,
        "runtime_effect_authorized": False,
    }
    payloads = {
        "cohort_registry.jsonl": _jsonl(cohort_rows),
        "evidence_bundle_registry.jsonl": _jsonl(identity_rows),
        "evidence_metric_registry.jsonl": _jsonl(metric_rows),
        "independent_review_contracts.jsonl": _jsonl(review_rows),
        "llm_annotation_contracts.jsonl": _jsonl(llm_rows),
        "manifest.json": deterministic_json(manifest) + "\n",
        "model_risk_adjudications.jsonl": _jsonl(model_risk_rows),
        "no_trade_comparisons.jsonl": _jsonl(no_trade_rows),
        "paper_result_contracts.jsonl": _jsonl(paper_rows),
        "parent_input_locks.jsonl": _jsonl(({
            "contract_type": "ImmutableReplayPaperInputLockV1",
            "field_roster": lock_fields,
            "template_count": 52,
            "parameter_value_ref_count": ST12F_PARAMETER_VALUE_REF_COUNT_V1,
            "empirical_instance_count": 0,
        },)),
        "quantum_benchmark_contracts.jsonl": _jsonl(quantum_rows),
        "replay_result_contracts.jsonl": _jsonl(replay_rows),
        "validation_summary.json": deterministic_json(summary) + "\n",
    }
    if tuple(payloads) != ST12F_GENERATED_PATHS:
        raise ValueError("ST12-F projection roster differs from the exact 13 paths")
    return payloads


def materialize_st12f_projections(projections: dict[str, str]) -> None:
    output_dir = REPO_ROOT / ST12F_GENERATED_PREFIX
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ST12F_GENERATED_PATHS:
        _write_generated_if_changed(output_dir / name, projections[name])


def build_payload(
    st12e_projections: ST12EProjectionSet | None = None,
    st12d_projections: ST12DProjectionSet | None = None,
    st12f_projections: dict[str, str] | None = None,
) -> dict[str, object]:
    """Return the centralized registry envelope without creating runtime state."""

    math_ids = tuple(PREDECESSOR_IMPLEMENTATION_REGISTRY)
    manifest = build_tranche_a_coverage_manifest()
    tranche_b_manifest = validate_tranche_b_frozen_manifest()
    dispositions = tuple(
        row.disposition
        for row in FROZEN_FORMULA_REPOSITORY_DISPOSITIONS.values()
    )
    operation_capabilities = tuple(
        ST12B_OPERATION_CAPABILITY_BY_ID.values()
    )
    output_member_count = sum(
        len(contract.members)
        for contract in FROZEN_NAMED_OUTPUT_CONTRACTS.values()
    )
    st12e_manifest, st12e_policy, st12e_scope = (
        st12e_projections or build_st12e_projections()
    )
    st12d_projection_set = st12d_projections or build_st12d_projections()
    st12d_manifest = st12d_projection_set[0]
    st12f_projection_set = st12f_projections or build_st12f_projections()
    return {
        "schema": "QKUComputationControlPlaneBuildV1",
        "contract_only": True,
        "runtime_effect_authorized": False,
        "implementation_ids": list(math_ids),
        "implementation_count": len(math_ids),
        "parameter_count": len(PARAMETER_POLICIES),
        "oracle_count": len(TRANCHE_A_ORACLE_BY_MATH_ID),
        "golden_vector_count": len(TRANCHE_A_GOLDEN_VECTOR_BY_MATH_ID),
        "certified_source_state_count": len(CERTIFIED_SOURCE_STATES),
        "source_overlay_count": len(SOURCE_CURRENTIZATION_OVERLAYS),
        "source_claim_binding_rule_count": len(SOURCE_CLAIM_BINDING_RULES),
        "coverage_manifest_schema": "TrancheACoverageManifestV1",
        "executed_coverage_rows": dict(manifest.executed_counts),
        "tranche_e": {
            "schema": st12e_manifest["schema"],
            "policy_version": st12e_manifest["policy_version"],
            "contract_only": True,
            "runtime_effect_authorized": False,
            "semantic_counts": st12e_manifest["counts"],
            "policy_row_count": len(st12e_policy),
            "parameter_scope_row_count": len(st12e_scope),
            "identity_mapping_count": st12e_manifest[
                "identity_mapping_count"
            ],
            "no_effect_authority_closed": st12e_manifest[
                "no_effect_authority_closed"
            ],
        },
        "tranche_d": {
            "schema": st12d_manifest["schema"],
            "contract_only": True,
            "runtime_effect_authorized": False,
            "order_release_authorized": False,
            "acceptance_counts": st12d_manifest["acceptance_counts"],
            "d_input_universe_count": st12d_manifest[
                "d_input_universe_count"
            ],
            "d_input_universe_count_by_class": st12d_manifest[
                "d_input_universe_count_by_class"
            ],
            "state_count": st12d_manifest["state_count"],
            "transition_count": st12d_manifest["transition_count"],
            "generated_projection_count": len(
                st12d_manifest["generated_projection_paths"]
            ),
            "active_pointer_commit_count": 0,
            "new_public_operation_id_count": 0,
        },
        "tranche_f": {
            "schema": "QTT_ST12F_CENTRAL_CONTRACTS_V1_4",
            "contract_only": True,
            "runtime_effect_authorized": False,
            "generated_projection_count": len(st12f_projection_set),
            "template_count": len(ST12F_TEMPLATE_IDS_V1),
            "result_slot_count": len(ST12F_REPLAY_RESULT_CONTRACT_IDS_V1) + len(ST12F_PAPER_RESULT_CONTRACT_IDS_V1),
            "evidence_identity_count": len(ST12F_EVIDENCE_IDENTITIES_V1),
            "evidence_metric_definition_count": len(ST12F_EVIDENCE_METRIC_DEFINITIONS_V1),
        },
        "tranche_c": {
            "schema": "ST12C_DETERMINISTIC_RECEIPTS_PERSISTENCE_ACCOUNTING_AND_TRANSACTIONS_V1",
            "contract_only": True,
            "runtime_effect_authorized": False,
            "control_matrix_count": len(ST12C_CONTROL_COVERAGE_MATRIX),
            "accounting_control_count": sum(row.domain == "accounting" for row in ST12C_CONTROL_COVERAGE_MATRIX),
            "execution_control_count": sum(row.domain == "execution" for row in ST12C_CONTROL_COVERAGE_MATRIX),
            "repository_disposition_count": len(ST12C_PRODUCTION_MODULE_PATHS),
            "parameter_policy_count": len(TRANCHE_C_PARAMETER_POLICIES),
            "parameter_application_binding_count": len(TRANCHE_C_PARAMETER_APPLICATION_BINDINGS),
            "math_implementation_count": len(TRANCHE_C_IMPLEMENTATION_REGISTRY),
            "independent_oracle_count": len(ST12C_ORACLE_BY_MATH_ID),
            "golden_vector_or_invariant_count": len(ST12C_GOLDEN_VECTOR_BY_MATH_ID),
            "semantic_test_denominator": len(ST12C_CONTROL_COVERAGE_MATRIX) + 2,
            "validation_command_count": 4,
            "later_phase_blocker_count": len(ST12C_LATER_PHASE_BLOCKERS),
            "production_persistence_selected": False,
            "outbox_dispatcher_implemented": False,
            "public_operation_additions": 0,
        },
        "tranche_b": {
            "schema": "ST12B_FROZEN_IMPLEMENTATION_SPEC_V3_4",
            "contract_only": True,
            "runtime_effect_authorized": False,
            "implementation_ids": list(IMPLEMENTATION_REGISTRY),
            "implementation_count": len(IMPLEMENTATION_REGISTRY),
            "implementation_version_count": len(
                IMPLEMENTATION_VERSION_REGISTRY
            ),
            "reused_implementation_count": dispositions.count(
                "REUSE_EXISTING_EXACT_VERSION"
            ),
            "semantic_successor_count": dispositions.count(
                "REGISTER_SEMANTIC_SUCCESSOR"
            ),
            "new_implementation_count": dispositions.count(
                "NEW_TRANCHE_B_IMPLEMENTATION"
            ),
            "named_output_contract_count": len(
                FROZEN_NAMED_OUTPUT_CONTRACTS
            ),
            "named_output_member_count": output_member_count,
            "formula_input_owner_count": len(
                FORMULA_INPUT_AUTHORITY_BINDINGS
            ),
            "parameter_count": len(CUMULATIVE_PARAMETER_POLICIES),
            "incremental_parameter_count": len(
                INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES
            ),
            "runtime_parameter_owner_count": len(
                RUNTIME_PARAMETER_OWNER_BINDINGS
            ),
            "optimizer_default_currentization_count": len(
                OPTIMIZER_DEFAULT_CURRENTIZATIONS
            ),
            "primary_source_count": len(PRIMARY_SOURCE_REGISTRY),
            "primary_source_class_counts": dict(SOURCE_POPULATION_COUNTS),
            "source_conflict_resolution_count": len(
                SOURCE_CONFLICT_RESOLUTIONS
            ),
            "source_currentization_count": len(
                SOURCE_CURRENTIZATION_REGISTRY
            ),
            "frozen_online_currentization_count": len(
                FROZEN_ONLINE_CURRENTIZATION_RECEIPTS
            ),
            "numeric_value_authority_count": len(
                NUMERIC_VALUE_AUTHORITY_BINDINGS
            ),
            "dependency_relationship_count": len(
                FROZEN_DEPENDENCY_RELATIONSHIPS
            ),
            "registered_stack_count": len(REGISTERED_FORMULA_STACKS),
            "oracle_count": len(ORACLE_BY_MATH_ID),
            "vector_count": len(ST12B_VECTOR_PACK),
            "property_count": len(ST12B_PROPERTY_TESTS),
            "quantum_structural_readiness_count": len(
                QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID
            ),
            "central_service_operation_count": len(
                ST12B_OPERATION_CAPABILITY_BY_ID
            ),
            "pure_deterministic_operation_count": operation_capabilities.count(
                OperationCapabilityClass.PURE_DETERMINISTIC_COMPUTATION
            ),
            "read_only_operation_count": operation_capabilities.count(
                OperationCapabilityClass.READ_ONLY_PROJECTION
            ),
            "no_effect_operation_count": operation_capabilities.count(
                OperationCapabilityClass.NO_EFFECT_RECORD
            ),
            "held_operation_count": operation_capabilities.count(
                OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
            ),
            "agent_identity_count": len(ST12B_AGENT_IDS),
            "agent_consumer_route_count": len(ST12B_AGENT_CONSUMER_DAG),
            "manifest_passed": tranche_b_manifest.passed,
        },
    }


def resolve_output_path(value: str) -> Path:
    relative = validate_relative_path(value)
    output = (REPO_ROOT / relative).resolve()
    temporary_root = (REPO_ROOT / ".tmp").resolve()
    try:
        output.relative_to(temporary_root)
    except ValueError as exc:
        raise ValueError("output must remain below repository .tmp") from exc
    if output == temporary_root:
        raise ValueError("output must name a file below repository .tmp")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        help="Optional JSON path below the repository .tmp directory.",
    )
    parser.add_argument(
        "--st12f-only",
        action="store_true",
        help="Materialize only the ST12-F evidence projections.",
    )
    args = parser.parse_args()
    st12e_projections = build_st12e_projections()
    st12d_projections = build_st12d_projections()
    st12f_projections = build_st12f_projections()
    text = deterministic_json(
        build_payload(st12e_projections, st12d_projections, st12f_projections)
    ) + "\n"
    if args.output:
        try:
            output = resolve_output_path(args.output)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        if not args.st12f_only:
            materialize_st12e_projections(*st12e_projections)
            materialize_st12d_projections(st12d_projections)
        materialize_st12f_projections(st12f_projections)
    else:
        print(text, end="")
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
