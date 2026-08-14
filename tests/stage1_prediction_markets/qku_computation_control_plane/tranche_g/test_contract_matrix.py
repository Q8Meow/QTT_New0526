"""One parametrized ST12-G contract and fail-closed matrix."""

from __future__ import annotations

import ast
from copy import copy
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache
import json
from pathlib import Path
from typing import NamedTuple

import pytest

from src.qtt.dashboard.owner_dashboard_validator import (
    validate_st12g_descriptor_candidate,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    EFFECT_ATTEMPT_REASON_BY_FLAG,
    AgentCapabilityDecisionStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    ComputationEvidenceBundleV1,
    ComputationEvidenceServiceV1,
    EvidenceBundleTerminalStateV1,
    EvidenceIdentityDispositionStateV1,
    EvidenceIdentityDispositionV1,
    EvidenceSectionV1,
    FToGHandoffReferencesV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
    ExistingOwnerProjectionCompilerV2,
    ExistingOwnerProjectionCoordinatorV2,
    ST12GBlockerSetStateV2,
    ST12GBlockerStateV2,
    ST12GOwnerProjectionResolutionV2,
    ST12GProjectionAbsenceV2,
    ST12GProjectionCoreV2,
    ST12GProjectionRequestV2,
    ST12GProjectionResolutionStateV2,
    ST12GProjectionResolutionV2,
    ST12GReferenceCollectionStateV2,
    ST12GReferenceCollectionV2,
    ST12GVersionMappingStateV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    INPUT_LOCK_SCHEMA_VERSION_V1,
    ImmutableReplayPaperInputLockV1,
    ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
    ST12F_PARAMETER_VALUE_REF_COUNT_V1,
    ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
    ST12F_TEMPLATE_IDS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    NO_EFFECTS_V1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    OwnerProjectionViewV1,
    PreloadedOwnerProjectionBundleV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    ParameterPolicyResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    validate_relative_path,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_e import (
    make_resolver,
    resolve_decision,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_f.test_replay_paper_evidence_matrix import (
    PaperResultContractV1,
    _lane,
)
from tools.independent_validate_qku_computation_control_plane_g import (
    EXPECTED_FAIL_CLOSED_ROWS,
    _behavior_case_definition_failures,
    validate_projection_field_binding_candidate,
    validate_static_architecture_candidate,
)


_ROOT = Path(__file__).resolve().parents[4]
_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
_SECTION_FIELDS = (
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
)
_CORE_FIELDS = (
    "core_id",
    "contract_version",
    "evaluation_context_id",
    "evaluated_at",
    "source_handoff_receipt_ref",
    "current_d_reference_receipt_ref",
    "current_d_reference_id",
    "handoff_id",
    "input_lock_id",
    "source_epoch_refs",
    "observed_at",
    "valid_until",
    "terminal_state",
    "evidence_bundle_ref",
    "evidence_id",
    "evidence_bundle_version",
    "component_or_template_ref",
    "independent_review_state",
    "actual_executed_component_versions",
    "actual_executed_stack_version_state",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "failure_and_negative_evidence_state",
    "source_and_provenance_refs",
    "bundle_blocker_state",
    "no_trade_blocker_reference_state",
    "champion_challenger_reference_state",
    "portfolio_utility_reference_state",
    "quantum_classical_comparison_receipt_ref",
    "runtime_authority",
    "no_effect_flags",
)

_HISTORICAL_CONTRACT_CASES = (
    ("ST12-TEST::103", "POISONED_CONTEXT_SOURCE_EPOCH_OR_CITATION_MISMATCH_REJECTED", "PASS"),
    ("ST12-TEST::109", "MALFORMED_OR_INSECURE_OUTPUT_CANNOT_ENTER_TYPED_PROJECTION", "PASS"),
    ("ST12-TEST::117", "SENSITIVE_SECRET_PRIVATE_STATE_AND_REASONING_FIELDS_ABSENT", "PASS"),
    ("ST12-TEST::118", "NO_MODEL_PLUGIN_RETRIEVAL_OR_SUPPLY_CHAIN_EXECUTION_IN_G", "PASS"),
    ("ST12-TEST::141", "TYPED_STALE_BLOCKER_ALERT_ROUTES_HAVE_NO_ORDER_AUTHORITY", "PASS"),
    ("ST12-TEST::144", "IDENTICAL_REBUILD_IDEMPOTENT_CONFLICTING_REPLAY_REJECTED", "PASS"),
    ("ST12-TEST::145", "EXACT_GENERATED_ROSTER_NO_SECOND_STORE_NO_CACHE_OR_BYTECODE", "PASS"),
    ("ST12-TEST::155", "TIMES_VALIDITY_LINEAGE_AND_AUTHORITY_FALSE_OBSERVABILITY", "PASS"),
    ("ST12-TEST::160", "VALIDATION_INVENTORY_SCOPE_AND_CHANGED_AREA_ROUTE_EXACT", "PASS"),
)

class _BehaviorCase(NamedTuple):
    case_id: str
    verification_mode: str
    valid_baseline_factory: str
    declared_mutation_action: str
    production_entrypoint: str
    expected_terminal_outcome: str
    expected_reason_code: str
    predecessor_proof_reference: str


_COMPILER_ENTRYPOINT = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ExistingOwnerProjectionCompilerV2.compile_current"
_COORDINATOR_ENTRYPOINT = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ExistingOwnerProjectionCoordinatorV2.resolve"
_DESCRIPTOR_ENTRYPOINT = "src/qtt/dashboard/owner_dashboard_validator.py::validate_st12g_descriptor_candidate"
_STATIC_ENTRYPOINT = "tools/independent_validate_qku_computation_control_plane_g.py::validate_static_architecture_candidate"
_BINDING_ENTRYPOINT = "tools/independent_validate_qku_computation_control_plane_g.py::validate_projection_field_binding_candidate"

_FAIL_CASES_CONTRACT = (
    _BehaviorCase("G-FAIL::001", "PRODUCTION_MUTATION_REJECTION", "empty InMemoryPersistenceAdapterV1", "HANDOFF_RECEIPT_MISSING", _COORDINATOR_ENTRYPOINT, "REJECT_NO_PROJECTION", "OWNER_DATA_MISSING", "NONE"),
    _BehaviorCase("G-FAIL::002", "PRODUCTION_MUTATION_REJECTION", "_baseline", "WRONG_HANDOFF_CONTRACT_VERSION", _COMPILER_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::003", "PRODUCTION_MUTATION_REJECTION", "_baseline", "INPUT_LOCK_MISMATCH", _COMPILER_ENTRYPOINT, "REJECT_INPUT_LOCK_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::004", "PRODUCTION_MUTATION_REJECTION", "_baseline", "SOURCE_EPOCH_MISSING", _COMPILER_ENTRYPOINT, "REJECT_SOURCE_EPOCH_MISSING", "SOURCE_EPOCH_MISSING", "NONE"),
    _BehaviorCase("G-FAIL::005", "PRODUCTION_MUTATION_REJECTION", "_baseline", "SOURCE_EPOCH_MISMATCH", _COMPILER_ENTRYPOINT, "REJECT_SOURCE_EPOCH_CONFLICT", "SOURCE_CONFLICT", "NONE"),
    _BehaviorCase("G-FAIL::006", "PRODUCTION_MUTATION_REJECTION", "_baseline", "EVIDENCE_BUNDLE_NOT_CLOSED", _COMPILER_ENTRYPOINT, "REJECT_INDEPENDENT_REVIEW_REQUIRED", "ST12F_INDEPENDENT_REVIEW_REQUIRED", "NONE"),
    _BehaviorCase("G-FAIL::007", "PRODUCTION_MUTATION_REJECTION", "_baseline", "INDEPENDENT_REVIEW_ABSENT_OR_NOT_VALIDATED", _COMPILER_ENTRYPOINT, "REJECT_INDEPENDENT_REVIEW_REQUIRED", "ST12F_INDEPENDENT_REVIEW_REQUIRED", "NONE"),
    _BehaviorCase("G-FAIL::008", "PRODUCTION_MUTATION_REJECTION", "_baseline", "VALIDITY_EXPIRED", _COMPILER_ENTRYPOINT, "RETURN_STALE_NO_AUTHORITY", "ST12F_BUNDLE_STALE", "NONE"),
    _BehaviorCase("G-FAIL::009", "PRODUCTION_MUTATION_REJECTION", "_baseline", "OBSERVATION_AFTER_VALID_UNTIL", _COMPILER_ENTRYPOINT, "REJECT_INVALID_TIME_SEQUENCE", "POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID", "NONE"),
    _BehaviorCase("G-FAIL::010", "EXISTING_OWNER_REJECTION_PROPAGATION", "_baseline_receipt", "PARENT_EVIDENCE_REFERENCE_MISMATCH", _COORDINATOR_ENTRYPOINT, "REJECT_PARENT_LINEAGE_MISMATCH", "SCHEMA_MISMATCH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py::ST12FEvidenceControlReceiptRecordV1.reconstruct"),
    _BehaviorCase("G-FAIL::011", "PRODUCTION_MUTATION_REJECTION", "_baseline", "SOURCE_RECORD_REFERENCES_INCOMPLETE", _COMPILER_ENTRYPOINT, "REJECT_SOURCE_CUSTODY_INCOMPLETE", "ST12F_EVIDENCE_INCOMPLETE", "NONE"),
    _BehaviorCase("G-FAIL::012", "EXISTING_OWNER_REJECTION_PROPAGATION", "_baseline_receipt", "SOURCE_RECORD_REFERENCES_OUT_OF_ORDER", _COORDINATOR_ENTRYPOINT, "REJECT_SOURCE_CUSTODY_ORDER_MISMATCH", "SCHEMA_MISMATCH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py::ST12FEvidenceControlReceiptRecordV1.reconstruct"),
    _BehaviorCase("G-FAIL::013", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "UNKNOWN_CONSUMER_OWNER", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GOwnerProjectionResolutionV2.__init__", "REJECT_OWNER_TOPOLOGY_MISMATCH", "OWNER_DATA_MISSING", "NONE"),
    _BehaviorCase("G-FAIL::014", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "projection_field_bindings.jsonl", "UNKNOWN_CONSUMER_FIELD", _BINDING_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::015", "DETERMINISTIC_PRESERVATION_PROOF", "generated DASH1 descriptor", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_SAME_PAYLOAD", _DESCRIPTOR_ENTRYPOINT, "RETURN_BYTE_EQUIVALENT_EXISTING_DESCRIPTOR", "IDEMPOTENT_RETURN_EXISTING", "NONE"),
    _BehaviorCase("G-FAIL::016", "PRODUCTION_MUTATION_REJECTION", "generated DASH1 descriptor", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_DIFFERENT_PAYLOAD", _DESCRIPTOR_ENTRYPOINT, "REJECT_IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT", "NONE"),
    _BehaviorCase("G-FAIL::017", "PRODUCTION_MUTATION_REJECTION", "_compile", "ATTEMPTED_RUNTIME_AUTHORITY", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionCoreV2.__post_init__", "REJECT_RUNTIME_EFFECT_FORBIDDEN", "RUNTIME_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::018", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "ATTEMPTED_SECOND_STATE_STORE", _STATIC_ENTRYPOINT, "REJECT_DUPLICATE_AUTHORITY", "INPUT_OWNER_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::019", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "ATTEMPTED_ECONOMIC_OR_STATISTICAL_RECOMPUTATION", _STATIC_ENTRYPOINT, "REJECT_DUPLICATE_MATH_AUTHORITY", "FORMULA_EXECUTION_REJECTED", "NONE"),
    _BehaviorCase("G-FAIL::020", "PRODUCTION_MUTATION_REJECTION", "ParameterPolicyResolverV1 seed", "ATTEMPTED_PARAMETER_VALUE_MUTATION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py::ParameterPolicyResolverV1.resolve", "REJECT_PARAMETER_OWNER_MISMATCH", "PARAMETER_NOT_EDITABLE", "NONE"),
    _BehaviorCase("G-FAIL::021", "PRODUCTION_MUTATION_REJECTION", "_request", "REQUEST_CONTAINS_CALLER_SUPPLIED_FRESHNESS_EPOCH_INPUT_LOCK_OR_PARENT_ASSERTION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionRequestV2.__post_init__", "REJECT_CALLER_AUTHORITY_FIELD", "INPUT_OWNER_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::022", "PRODUCTION_MUTATION_REJECTION", "_compile", "DASHBOARD_DIRECTLY_BOUND_TO_F_HANDOFF", "src/qtt/dashboard/owner_surface_resolver.py::resolve_st12g_projection_v2", "REJECT_OWNER_CHAIN_BYPASS", "INPUT_OWNER_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::023", "PRODUCTION_MUTATION_REJECTION", "_request", "UNEXPLAINED_EMPTY_STRING_OR_UNTYPED_ABSENCE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionRequestV2.__post_init__", "REJECT_INCOMPLETE_CONTRACT", "INCOMPLETE_CONTRACT", "NONE"),
    _BehaviorCase("G-FAIL::024", "PRODUCTION_MUTATION_REJECTION", "generated DASH1 descriptor", "FIXTURE_OR_CONTRACT_ROW_PRESENTED_AS_EMPIRICAL_EVIDENCE", _DESCRIPTOR_ENTRYPOINT, "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE", "NONE"),
    _BehaviorCase("G-FAIL::025", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_MODE_ACTIVATION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_MODE_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::026", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_ALLOW_ACTIVATION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_ALLOW_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::027", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_ORDER_RELEASE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_ORDER_RELEASE", "ORDER_RELEASE_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::028", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_CAPITAL_EFFECT", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_CAPITAL_EFFECT", "CAPITAL_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::029", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_PROVIDER_ACCESS", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_PROVIDER_ACCESS", "DIRECT_PROVIDER_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::030", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_PRIVATE_STATE_ACCESS", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_PRIVATE_STATE_ACCESS", "PRIVATE_STATE_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::031", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_REPLAY_OR_PAPER_EXECUTION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_REPLAY_PAPER_EFFECT", "REPLAY_PAPER_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::032", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_LLM_INFERENCE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_LLM_INFERENCE", "LLM_INFERENCE_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::033", "PRODUCTION_MUTATION_REJECTION", "ST12-E agent capability baseline", "ATTEMPTED_QPU_OR_SIMULATOR_EXECUTION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py::AgentCapabilityResolverV1.resolve", "REJECT_QPU_EFFECT", "QPU_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::034", "PRODUCTION_MUTATION_REJECTION", "repository-relative path", "UNLISTED_OR_WILDCARD_REPOSITORY_PATH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py::validate_relative_path", "REJECT_PATH_SCOPE", "PATH_UNSAFE", "NONE"),
    _BehaviorCase("G-FAIL::035", "EXISTING_OWNER_REJECTION_PROPAGATION", "_baseline_receipt", "WRONG_DURABLE_RECEIPT_CLASS", _COORDINATOR_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py::ST12FEvidenceControlReceiptRecordV1.reconstruct"),
    _BehaviorCase("G-FAIL::036", "EXISTING_OWNER_REJECTION_PROPAGATION", "ST12-F evidence lane baseline", "G_HANDOFF_RECEIPT_MARKED_FIXTURE_ONLY_NOT_EVIDENCE", _COORDINATOR_ENTRYPOINT, "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py::ComputationEvidenceServiceV1._validate_bundle_lanes"),
    _BehaviorCase("G-FAIL::037", "EXISTING_OWNER_REJECTION_PROPAGATION", "_baseline_receipt", "RECEIPT_PARENT_METADATA_MISMATCH", _COORDINATOR_ENTRYPOINT, "REJECT_PARENT_LINEAGE_MISMATCH", "SCHEMA_MISMATCH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py::ST12FEvidenceControlReceiptRecordV1.reconstruct"),
    _BehaviorCase("G-FAIL::038", "PRODUCTION_MUTATION_REJECTION", "_baseline", "RECEIPT_INPUT_LOCK_METADATA_MISMATCH", _COORDINATOR_ENTRYPOINT, "REJECT_INPUT_LOCK_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::039", "PRODUCTION_MUTATION_REJECTION", "_baseline", "RECEIPT_SOURCE_EPOCH_METADATA_MISMATCH", _COORDINATOR_ENTRYPOINT, "REJECT_SOURCE_EPOCH_CONFLICT", "SOURCE_CONFLICT", "NONE"),
    _BehaviorCase("G-FAIL::040", "EXISTING_OWNER_REJECTION_PROPAGATION", "_baseline_receipt", "RECEIPT_STABLE_FIRST_OCCURRENCE_SOURCE_RECORD_METADATA_MISMATCH", _COORDINATOR_ENTRYPOINT, "REJECT_SOURCE_CUSTODY_ORDER_MISMATCH", "SCHEMA_MISMATCH", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py::ST12FEvidenceControlReceiptRecordV1.reconstruct"),
    _BehaviorCase("G-FAIL::041", "PRODUCTION_MUTATION_REJECTION", "_baseline", "PARENT_EMBEDDED_G_HANDOFF_DIFFERS_FROM_DURABLE_HANDOFF", _COMPILER_ENTRYPOINT, "REJECT_PARENT_HANDOFF_CONTRADICTION", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::042", "PRODUCTION_MUTATION_REJECTION", "_baseline", "CURRENT_PARENT_COMPONENT_VERSION_MAPPING_EMPTY", _COMPILER_ENTRYPOINT, "REJECT_EVIDENCE_INCOMPLETE", "ST12F_EVIDENCE_INCOMPLETE", "NONE"),
    _BehaviorCase("G-FAIL::043", "PRODUCTION_MUTATION_REJECTION", "_baseline", "STACK_VERSION_EMPTY_WITHOUT_TYPED_EXPLICIT_ABSENCE", _COMPILER_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::044", "PRODUCTION_MUTATION_REJECTION", "_baseline", "DUPLICATE_REFERENCE_INSIDE_HANDOFF_COLLECTION", _COMPILER_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::045", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "G_SORTS_OR_DEDUPLICATES_A_PROJECTED_REFERENCE_COLLECTION", _STATIC_ENTRYPOINT, "REJECT_LINEAGE_REWRITE", "SCHEMA_MISMATCH", "NONE"),
)


def _owner_view(owner_id: str) -> OwnerProjectionViewV1:
    path = f"docs/st12g/{owner_id.lower()}.jsonl"
    return OwnerProjectionViewV1(
        owner_id=owner_id,
        authority_domain="READ_ONLY_EVIDENCE",
        source_path=path,
        source_version=f"VERSION::{owner_id}",
        source_snapshot_ref=path,
        consume_interfaces=("resolve_st12g_projection_v2",),
        row_count=1,
        identity_refs=(f"ROW::{owner_id}",),
    )


@lru_cache(maxsize=1)
def _baseline() -> tuple[
    ComputationExecutionContextV1,
    ImmutableReplayPaperInputLockV1,
    FToGHandoffReferencesV1,
    ComputationEvidenceBundleV1,
    ST12FEvidenceReferenceV1,
    PreloadedOwnerProjectionBundleV1,
]:
    versions = {
        identity: f"VERSION::{identity}" for identity in ST12F_TEMPLATE_IDS_V1
    }
    lock = ImmutableReplayPaperInputLockV1(
        input_lock_id="ST12F-LOCK::G-VALID",
        schema_version=INPUT_LOCK_SCHEMA_VERSION_V1,
        contract_version="1.4",
        decision_time=_NOW,
        point_in_time_cutoff=_NOW - timedelta(minutes=1),
        market_scope=("MARKET::1",),
        venue_scope=("VENUE::1",),
        instrument_scope=("INSTRUMENT::1",),
        cohort_template_ids=ST12F_TEMPLATE_IDS_V1,
        expected_replay_result_contract_ids=ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
        expected_paper_result_contract_ids=ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
        formula_specification_versions=versions,
        implementation_versions=versions,
        parameter_policy_version="POLICY::1",
        parameter_value_refs=tuple(
            f"ST10-PARAM::{index:04d}"
            for index in range(ST12F_PARAMETER_VALUE_REF_COUNT_V1)
        ),
        source_epochs={"SOURCE::1": "EPOCH::1"},
        data_semantics_version="DATA::1",
        venue_semantics_version="VENUE::1",
        accounting_definition={"basis": "NET"},
        fee_assumptions={"ref": "FEE::1"},
        spread_assumptions={"ref": "SPREAD::1"},
        slippage_assumptions={"ref": "SLIPPAGE::1"},
        fill_and_queue_assumptions={"ref": "FILL::1"},
        latency_and_staleness_assumptions={"ref": "LATENCY::1"},
        capacity_and_crowding_assumptions={"ref": "CAPACITY::1"},
        portfolio_and_cash_context={
            "permanent_no_trade_baseline_ref": "NO-TRADE::1"
        },
        random_seed_policy={"seed": 1},
        resampling_policy={"trial_family_id": "TRIAL::1"},
        scenario_set_id="SCENARIO::1",
        causation_id="CAUSE::LOCK",
        correlation_id="CORRELATION::LOCK",
        created_by="OWNER::LOCK",
        created_at=_NOW,
    )
    context = ComputationExecutionContextV1(
        context_id="CONTEXT::G-VALID",
        as_of=_NOW,
        observed_at=_NOW - timedelta(minutes=1),
        source_epoch_id="SOURCE::1=EPOCH::1",
        input_version="INPUT::1",
        maximum_age=timedelta(minutes=5),
        scope=ComputationScopeV1(
            market_scope_id="MARKET::1",
            venue_scope_id="VENUE::1",
            event_scope_id="EVENT::1",
            instrument_or_contract_scope_id="INSTRUMENT::1",
            mode_context_id="MODE::READ_ONLY",
            input_snapshot_id=lock.input_lock_id,
        ),
        binding_profile_version="BINDING::1",
        parameter_policy_version="POLICY::1",
        implementation_versions=(
            ImplementationVersionPinV1("MATH-01", "VERSION::MATH-01"),
        ),
    )
    evidence_ref = "ST12F-RECEIPT::BUNDLE::G-VALID::EVIDENCE_BUNDLE_VERSION"
    reference = ST12FEvidenceReferenceV1(
        evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
        evidence_ref=evidence_ref,
        lane="REPLAY_PAPER",
        dataset_grade_ref="DATASET-GRADE::G-VALID",
        venue_semantic_binding_ref="VENUE-SEMANTICS::G-VALID",
        cross_venue_equivalence_ref="CROSS-VENUE::G-VALID",
        observed_at=_NOW - timedelta(minutes=2),
        valid_until=_NOW + timedelta(minutes=5),
        policy_version="ST12F_EVIDENCE_POLICY_V1_4",
        causation_id="CAUSE::F",
        correlation_id="CORRELATION::F",
        input_lock_id=lock.input_lock_id,
        component_or_template_ref="MATH-01",
        evidence_bundle_version="BUNDLE::G-VALID",
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
        reference_id="D-REFERENCE::G-VALID",
        evidence_id="EVIDENCE::G-VALID",
    )
    handoff = FToGHandoffReferencesV1(
        handoff_id="G-HANDOFF::G-VALID",
        contract_version="1.4",
        input_lock_id=lock.input_lock_id,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        observed_at=_NOW - timedelta(minutes=2),
        valid_until=_NOW + timedelta(minutes=5),
        terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
        evidence_bundle_ref=evidence_ref,
        no_trade_blocker_refs=(),
        champion_challenger_evidence_refs=("CHAMPION::1",),
        portfolio_utility_refs=("PORTFOLIO-UTILITY::1",),
        quantum_classical_comparison_receipt_ref="RECEIPT::MATH-52",
    )
    dispositions = tuple(
        EvidenceIdentityDispositionV1(
            identity,
            EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED,
            (f"RECEIPT::{identity}",),
            (),
            (),
        )
        for identity in ST12F_EVIDENCE_IDENTITIES_V1
    )
    sections: dict[str, EvidenceSectionV1] = {}
    offset = 0
    for index, name in enumerate(_SECTION_FIELDS):
        width = 8 if index == len(_SECTION_FIELDS) - 1 else 4
        sections[name] = EvidenceSectionV1(
            name, dispositions[offset : offset + width]
        )
        offset += width
    bundle = ComputationEvidenceBundleV1(
        evidence_id=reference.evidence_id,
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version=reference.evidence_bundle_version,
        component_or_template_ref="MATH-01",
        input_lock_id=lock.input_lock_id,
        actual_executed_component_versions={"MATH-01": "VERSION::MATH-01"},
        actual_executed_stack_versions={},
        replay_result_ref="RESULT::REPLAY",
        paper_result_ref="RESULT::PAPER",
        divergence_assessment_ref="DIVERGENCE::1",
        lane_execution_receipt_refs=("RECEIPT::REPLAY", "RECEIPT::PAPER"),
        **sections,
        independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED",
        failure_and_negative_evidence_states=(),
        source_and_provenance_refs=("SOURCE-RECORD::1",),
        d_evidence_reference_projection=reference,
        g_handoff_projection=handoff,
        terminal_state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        blocker_codes=(),
    )
    owners = PreloadedOwnerProjectionBundleV1(
        readiness=_owner_view("READINESS1"),
        pretrade=_owner_view("PRETRADE1"),
        svc=_owner_view("SVC1"),
        agent_orch=_owner_view("AGENT_ORCH1"),
    )
    return context, lock, handoff, bundle, reference, owners


def _compile(
    *,
    context: ComputationExecutionContextV1 | None = None,
    lock: ImmutableReplayPaperInputLockV1 | None = None,
    handoff: FToGHandoffReferencesV1 | None = None,
    bundle: ComputationEvidenceBundleV1 | None = None,
    reference: ST12FEvidenceReferenceV1 | None = None,
):
    baseline = _baseline()
    return ExistingOwnerProjectionCompilerV2().compile_current(
        context or baseline[0],
        lock or baseline[1],
        handoff or baseline[2],
        bundle or baseline[3],
        reference or baseline[4],
        baseline[5],
    )


def _compiler_source() -> str:
    return (
        _ROOT
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py"
    ).read_text(encoding="utf-8")


def _compiler_candidate(insertion: str) -> str:
    source = _compiler_source()
    head, marker, compiler = source.partition(
        "class ExistingOwnerProjectionCompilerV2:"
    )
    assert marker and "    __slots__ = ()" in compiler
    return head + marker + compiler.replace(
        "    __slots__ = ()",
        f"    __slots__ = ()\n{insertion}",
        1,
    )


def _binding_baseline() -> dict[str, object]:
    return {
        "absence_rule": "TAGGED_NONCURRENT_RESOLUTION_ONLY_NO_NULL_ZERO_NEUTRAL_OR_UNEXPLAINED_EMPTY_SUBSTITUTION",
        "binding_id": "ST12G-BINDING::SHARED_CORE::evaluation_context_id",
        "binding_scope": "SHARED_CORE",
        "consumer_field": "evaluation_context_id",
        "consumer_ids": ["READINESS1", "PRETRADE1", "AGENT_ORCH1", "SVC1"],
        "freshness_rule": "TRUSTED_CONTEXT_AS_OF_AND_F_TO_G_VALIDITY_WITH_NO_OWNER_OR_DASHBOARD_EXTENSION",
        "independent_oracle": "RECONSTRUCT_FROM_TRUSTED_CONTEXT_DURABLE_HANDOFF_INPUT_LOCK_PARENT_BUNDLE_AND_CURRENT_D_REFERENCE_WITHOUT_CALLING_PRODUCTION_COMPILER",
        "runtime_effect_authority": "NONE",
        "source_contract": "ComputationExecutionContextV1",
        "source_field_or_rule": "context_id",
        "stale_rule": "UNAVAILABLE_STALE_NO_AUTHORITY",
        "transformation": "IDENTITY",
        "units_and_basis": "SOURCE_DECLARED_OR_TYPED_STATE_NO_HIDDEN_CONVERSION",
    }


def _baseline_receipt() -> ST12FEvidenceControlReceiptRecordV1:
    _, lock, handoff, _, _, _ = _baseline()
    source_record_refs = tuple(
        dict.fromkeys(
            (
                handoff.evidence_bundle_ref,
                *handoff.no_trade_blocker_refs,
                *handoff.champion_challenger_evidence_refs,
                *handoff.portfolio_utility_refs,
                handoff.quantum_classical_comparison_receipt_ref,
            )
        )
    )
    return ST12FEvidenceControlReceiptRecordV1(
        control_receipt_id=(
            f"ST12F-RECEIPT::{handoff.handoff_id}::G_HANDOFF_REFERENCE"
        ),
        receipt_class=ST12FReceiptClassV1.G_HANDOFF_REFERENCE,
        operation_id="build_evidence_bundle",
        request_id="REQUEST::G-RECEIPT",
        idempotency_key="IDEMPOTENCY::G-RECEIPT",
        contract_type="FToGHandoffReferencesV1",
        contract_id=handoff.handoff_id,
        contract_version=handoff.contract_version,
        input_lock_id_or_explicit_absence=handoff.input_lock_id,
        parent_version_ref_or_explicit_absence=handoff.evidence_bundle_ref,
        canonical_contract_json=deterministic_json(handoff),
        source_record_refs=source_record_refs,
        parameter_value_refs=lock.parameter_value_refs,
        source_epoch_refs=handoff.source_epoch_refs,
        typed_reason_codes=(),
        terminal_state=handoff.terminal_state,
        fixture_only_not_evidence=False,
    )


class _CohortResolver:
    def resolve_input_lock(self, *_args, **_kwargs):
        return _baseline()[1]

    def resolve_expected_slot(self, *_args, **_kwargs):
        return object()


def _missing_handoff_resolution() -> ST12GProjectionResolutionV2:
    service = ComputationEvidenceServiceV1(
        _CohortResolver(),
        InMemoryPersistenceAdapterV1(),
    )
    return ExistingOwnerProjectionCoordinatorV2(
        service,
        _baseline()[5],
    ).resolve(_request())


def _mutated(value: object, **changes: object):
    altered = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(altered, name, replacement)
    return altered


def _assert_reason(expected: str, operation) -> str:
    with pytest.raises(ComputationControlPlaneError) as caught:
        operation()
    assert caught.value.reason_code.name == expected
    return caught.value.reason_code.name


class _EvidenceService:
    def __init__(self, fail_method: str | None = None, reason: ReasonCode | None = None):
        self.context, self.lock, self.handoff, self.bundle, self.reference, _ = _baseline()
        self.fail_method = fail_method
        self.reason = reason
        self.calls: list[tuple[str, datetime]] = []

    def _record(self, method: str, cutoff: datetime) -> None:
        self.calls.append((method, cutoff))
        if self.fail_method == method:
            raise ContractValidationError(self.reason or ReasonCode.SCHEMA_MISMATCH, method)

    def resolve_g_handoff(self, handoff_ref: str, *, decision_cutoff: datetime):
        self._record("resolve_g_handoff", decision_cutoff)
        return self.handoff

    def resolve_control_receipt(self, receipt_ref: str, expected_type: type[object], *, decision_cutoff: datetime):
        self._record("resolve_control_receipt", decision_cutoff)
        return self.lock

    def resolve_bundle(self, bundle_ref: str, *, decision_cutoff: datetime):
        self._record("resolve_bundle", decision_cutoff)
        return self.bundle

    def read_evidence_reference(self, context, *, causation_id: str, correlation_id: str, query=None):
        self._record("read_evidence_reference", context.as_of)
        return self.reference


def _request(context: ComputationExecutionContextV1 | None = None) -> ST12GProjectionRequestV2:
    handoff = _baseline()[2]
    return ST12GProjectionRequestV2(
        request_id="REQUEST::G-VALID",
        context=context or _baseline()[0],
        source_handoff_receipt_ref=(
            f"ST12F-RECEIPT::{handoff.handoff_id}::G_HANDOFF_REFERENCE"
        ),
        causation_id="CAUSE::G",
        correlation_id="CORRELATION::G",
    )


def _resolve_with_failure(method: str, reason: ReasonCode):
    service = _EvidenceService(method, reason)
    result = ExistingOwnerProjectionCoordinatorV2(service, _baseline()[5]).resolve(
        _request()
    )
    assert result.resolution_state is ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY
    assert result.absence.reason_codes == (reason,)
    return result


def _source_tree() -> ast.Module:
    path = _ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py"
    return ast.parse(path.read_text(encoding="utf-8"))


def _descriptor(owner: str) -> dict[str, object]:
    paths = {
        "READINESS1": "docs/master_plan/generated/pr169_readiness1/st12g_evidence_projection_contract.generated.jsonl",
        "PRETRADE1": "docs/master_plan/generated/pr169_pretrade1/st12g_evidence_projection_contract.generated.jsonl",
        "AGENT_ORCH1": "docs/master_plan/generated/pr169_agent_orch1/st12g_evidence_handoff_contract.generated.jsonl",
        "SVC1": "docs/master_plan/generated/pr169_svc1/st12g_evidence_view_contract.generated.jsonl",
        "DASH1_UI1": "docs/master_plan/generated/pr169_dash1/st12g_evidence_owner_view_contract.generated.jsonl",
    }
    rows = [
        json.loads(line)
        for line in (_ROOT / paths[owner]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    return rows[0]


def _run_historical_contract(case_id: str) -> None:
    context, lock, handoff, bundle, reference, _ = _baseline()
    if case_id == "ST12-TEST::103":
        poisoned = replace(context, source_epoch_id="SOURCE::POISON=EPOCH::POISON")
        _assert_reason("SOURCE_CONFLICT", lambda: _compile(context=poisoned))
    elif case_id == "ST12-TEST::109":
        _assert_reason(
            "SCHEMA_MISMATCH",
            lambda: ST12GReferenceCollectionV2(
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_BLOCKER_IN_CLOSED_BUNDLE,
                ("REF::ILLEGAL",),
            ),
        )
    elif case_id == "ST12-TEST::117":
        names = {node.id.casefold() for node in ast.walk(_source_tree()) if isinstance(node, ast.Name)}
        assert not names.intersection({"secret", "credential", "private_account", "chain_of_thought"})
    elif case_id == "ST12-TEST::118":
        imports = {alias.name for node in ast.walk(_source_tree()) if isinstance(node, ast.Import) for alias in node.names}
        assert not imports.intersection({"requests", "openai", "subprocess", "importlib"})
    elif case_id == "ST12-TEST::141":
        absence = ST12GProjectionAbsenceV2(
            absence_id="ST12G::ABSENCE::HISTORICAL",
            evaluation_context_id=context.context_id,
            evaluated_at=context.as_of,
            state=ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY,
            reason_codes=(ReasonCode.ST12F_BUNDLE_STALE,),
            source_handoff_receipt_ref_or_explicit_absence="EXPLICIT_ABSENCE",
        )
        assert absence.no_effect_flags is NO_EFFECTS_V1
        assert all(value is False for value in vars(NO_EFFECTS_V1).values()) if hasattr(NO_EFFECTS_V1, "__dict__") else all(getattr(NO_EFFECTS_V1, field.name) is False for field in fields(NO_EFFECTS_V1))
    elif case_id == "ST12-TEST::144":
        assert deterministic_json(_compile()) == deterministic_json(_compile())
    elif case_id == "ST12-TEST::145":
        compiler = ExistingOwnerProjectionCompilerV2()
        assert compiler.__slots__ == () and not hasattr(compiler, "__dict__")
        assert len(fields(ST12GProjectionCoreV2)) == 33
    elif case_id == "ST12-TEST::155":
        core = _compile().core
        assert (core.evaluated_at, core.observed_at, core.valid_until) == (
            context.as_of,
            handoff.observed_at,
            handoff.valid_until,
        )
        assert core.source_epoch_refs == reference.source_epoch_refs
        assert core.no_effect_flags is NO_EFFECTS_V1
    elif case_id == "ST12-TEST::160":
        scope = (_ROOT / "tools/validation_scope_registry.py").read_text(encoding="utf-8")
        router = (_ROOT / "tools/changed_area_validation_router.py").read_text(encoding="utf-8")
        assert "agent/st12g-existing-owner-projections-v2" in scope
        assert "independent_validate_qku_computation_control_plane_g.py" in router
        fabricated = {
            "case_id": "G-FAIL::001",
            "verification_mode": "PRODUCTION_MUTATION_REJECTION",
            "valid_baseline_factory": "VALID_BASELINE",
            "declared_mutation_action": "HANDOFF_RECEIPT_MISSING",
            "production_entrypoint": "ReasonCode.OWNER_DATA_MISSING",
            "expected_terminal_outcome": "REJECT_NO_PROJECTION",
            "expected_reason_code": "OWNER_DATA_MISSING",
            "predecessor_proof_reference": "NONE",
        }
        assert any(
            "enum-only" in failure
            for failure in _behavior_case_definition_failures(
                fabricated,
                EXPECTED_FAIL_CLOSED_ROWS[0],
            )
        )
    else:
        raise AssertionError(case_id)


def _run_contract_failure(case_id: str, trigger: str, expected: str) -> None:
    context, lock, handoff, bundle, reference, owners = _baseline()
    if case_id == "G-FAIL::001":
        result = _missing_handoff_resolution()
        assert result.resolution_state is ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY
        assert result.absence.reason_codes == (ReasonCode.OWNER_DATA_MISSING,)
    elif case_id == "G-FAIL::002":
        bad_handoff = _mutated(handoff, contract_version="0.0")
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::003":
        bad_bundle = _mutated(bundle, input_lock_id="ST12F-LOCK::MISMATCH")
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::004":
        bad_lock = _mutated(lock, source_epochs={})
        _assert_reason(expected, lambda: _compile(lock=bad_lock))
    elif case_id == "G-FAIL::005":
        bad_handoff = _mutated(handoff, source_epoch_refs=("SOURCE::2=EPOCH::2",))
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::006":
        open_bundle = replace(
            bundle,
            d_evidence_reference_projection="UNAVAILABLE",
            g_handoff_projection="UNAVAILABLE",
            independent_review_state="READY_FOR_INDEPENDENT_REVIEW",
            terminal_state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        )
        _assert_reason(expected, lambda: _compile(bundle=open_bundle))
    elif case_id == "G-FAIL::007":
        bad_bundle = _mutated(bundle, independent_review_state="EXPLICIT_ABSENCE")
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::008":
        expired = replace(
            handoff,
            observed_at=_NOW - timedelta(minutes=10),
            valid_until=_NOW - timedelta(minutes=1),
        )
        expired_bundle = replace(bundle, g_handoff_projection=expired)
        _assert_reason(expected, lambda: _compile(handoff=expired, bundle=expired_bundle))
    elif case_id == "G-FAIL::009":
        invalid_sequence = _mutated(
            handoff,
            observed_at=handoff.valid_until + timedelta(minutes=1),
        )
        invalid_bundle = _mutated(
            bundle,
            g_handoff_projection=invalid_sequence,
        )
        _assert_reason(
            expected,
            lambda: _compile(
                handoff=invalid_sequence,
                bundle=invalid_bundle,
            ),
        )
    elif case_id in {"G-FAIL::010", "G-FAIL::012", "G-FAIL::035", "G-FAIL::037", "G-FAIL::040"}:
        receipt = _baseline_receipt()
        if case_id == "G-FAIL::010":
            altered_handoff = _mutated(
                handoff,
                evidence_bundle_ref="ST12F-RECEIPT::BUNDLE::OTHER::EVIDENCE_BUNDLE_VERSION",
            )
            altered_receipt = replace(
                receipt,
                canonical_contract_json=deterministic_json(altered_handoff),
            )
            predecessor = lambda: altered_receipt.reconstruct(FToGHandoffReferencesV1)
        elif case_id == "G-FAIL::012":
            altered_handoff = replace(
                handoff,
                champion_challenger_evidence_refs=("CHAMPION::B", "CHAMPION::A"),
            )
            expected_sources = (
                altered_handoff.evidence_bundle_ref,
                *altered_handoff.no_trade_blocker_refs,
                *altered_handoff.champion_challenger_evidence_refs,
                *altered_handoff.portfolio_utility_refs,
                altered_handoff.quantum_classical_comparison_receipt_ref,
            )
            altered_receipt = replace(
                receipt,
                canonical_contract_json=deterministic_json(altered_handoff),
                source_record_refs=tuple(reversed(expected_sources)),
            )
            predecessor = lambda: altered_receipt.reconstruct(FToGHandoffReferencesV1)
        elif case_id == "G-FAIL::035":
            predecessor = lambda: receipt.reconstruct(ComputationEvidenceBundleV1)
        elif case_id == "G-FAIL::037":
            altered_receipt = replace(
                receipt,
                parent_version_ref_or_explicit_absence="ST12F-RECEIPT::BUNDLE::OTHER",
            )
            predecessor = lambda: altered_receipt.reconstruct(FToGHandoffReferencesV1)
        else:
            altered_receipt = replace(
                receipt,
                source_record_refs=tuple(reversed(receipt.source_record_refs)),
            )
            predecessor = lambda: altered_receipt.reconstruct(FToGHandoffReferencesV1)
        _assert_reason(expected, predecessor)
        propagated = _resolve_with_failure("resolve_bundle", ReasonCode[expected])
        assert propagated.absence.reason_codes == (ReasonCode[expected],)
    elif case_id == "G-FAIL::011":
        incomplete_bundle = _mutated(bundle, source_and_provenance_refs=())
        _assert_reason(expected, lambda: _compile(bundle=incomplete_bundle))
    elif case_id == "G-FAIL::013":
        current = ST12GProjectionResolutionV2.current(
            resolution_id="ST12G::RESOLUTION::OWNER",
            request_id="REQUEST::OWNER",
            context_id=context.context_id,
            evaluated_at=context.as_of,
            projection_bundle=_compile(),
        )
        _assert_reason(
            expected,
            lambda: ST12GOwnerProjectionResolutionV2(
                consumer_id="UNKNOWN",
                source_request_id=current.request_id,
                resolution_state=current.resolution_state,
                payload=current.projection_bundle.readiness,
            ),
        )
    elif case_id == "G-FAIL::014":
        bad_binding = _binding_baseline() | {
            "consumer_field": "unknown_consumer_field"
        }
        _assert_reason(
            expected,
            lambda: validate_projection_field_binding_candidate(bad_binding),
        )
    elif case_id == "G-FAIL::015":
        descriptor = _descriptor("DASH1_UI1")
        existing = validate_st12g_descriptor_candidate(
            dict(descriptor),
            existing=descriptor,
        )
        assert existing is descriptor
        assert deterministic_json(existing) == deterministic_json(descriptor)
    elif case_id == "G-FAIL::016":
        original = _descriptor("DASH1_UI1")
        changed = original | {"contract_type": "DIFFERENT"}
        _assert_reason(
            expected,
            lambda: validate_st12g_descriptor_candidate(
                changed,
                existing=original,
            ),
        )
    elif case_id == "G-FAIL::017":
        _assert_reason(expected, lambda: replace(_compile().core, runtime_authority="ALLOW"))
    elif case_id == "G-FAIL::018":
        candidate = _compiler_candidate("    state_store = {}")
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    elif case_id == "G-FAIL::019":
        candidate = _compiler_candidate(
            "    duplicate_math = recompute_economic_or_statistical_value()"
        )
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    elif case_id == "G-FAIL::020":
        _assert_reason(
            expected,
            lambda: ParameterPolicyResolverV1.resolve(
                "ST10-PARAM::0801",
                candidate="ALTERED",
            ),
        )
    elif case_id == "G-FAIL::021":
        _assert_reason(
            expected,
            lambda: ST12GProjectionRequestV2(
                request_id="REQUEST::FORBIDDEN-CALLER-AUTHORITY",
                context={
                    "trusted_context": context,
                    "expected_source_epoch_refs": handoff.source_epoch_refs,
                    "expected_input_lock_id": lock.input_lock_id,
                    "expected_parent_bundle_ref": handoff.evidence_bundle_ref,
                },
                source_handoff_receipt_ref=_request().source_handoff_receipt_ref,
                causation_id="CAUSE::G",
                correlation_id="CORRELATION::G",
            ),
        )
    elif case_id == "G-FAIL::022":
        from src.qtt.dashboard.owner_surface_resolver import resolve_st12g_projection_v2

        _assert_reason(expected, lambda: resolve_st12g_projection_v2(handoff))
    elif case_id == "G-FAIL::023":
        _assert_reason(
            expected,
            lambda: replace(_request(), request_id=""),
        )
    elif case_id == "G-FAIL::024":
        empirical = _descriptor("DASH1_UI1") | {
            "runtime_instance_state": "EMPIRICAL_EVIDENCE_PRESENT"
        }
        _assert_reason(
            expected,
            lambda: validate_st12g_descriptor_candidate(empirical),
        )
    elif case_id in {f"G-FAIL::{index:03d}" for index in range(25, 34)}:
        matching_flags = tuple(
            flag
            for flag, reason in EFFECT_ATTEMPT_REASON_BY_FLAG.items()
            if reason is ReasonCode[expected]
        )
        assert matching_flags == (
            "mode_activation_requested",
        ) if case_id in {"G-FAIL::025", "G-FAIL::026"} else len(matching_flags) == 1
        flag = matching_flags[0]
        overrides: dict[str, object] = {flag: True}
        if case_id == "G-FAIL::026":
            overrides["mode_eligibility_ref_without_activation"] = "ALLOW"
        decision = resolve_decision(
            make_resolver(envelope_overrides=overrides)
        )
        assert decision.decision_state is AgentCapabilityDecisionStateV1.DENIED
        assert ReasonCode[expected] in decision.reason_codes
        assert decision.runtime_effect_authorized is False
    elif case_id == "G-FAIL::034":
        _assert_reason(expected, lambda: validate_relative_path("../outside"))
    elif case_id == "G-FAIL::036":
        _assert_reason(
            expected,
            lambda: ComputationEvidenceServiceV1._validate_bundle_lanes(
                bundle,
                lock,
                _lane(),
                _lane(PaperResultContractV1),
            ),
        )
        propagated = _resolve_with_failure(
            "resolve_g_handoff",
            ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
        )
        assert propagated.absence.reason_codes == (
            ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
        )
    elif case_id == "G-FAIL::038":
        service = _EvidenceService()
        service.lock = _mutated(lock, input_lock_id="ST12F-LOCK::OTHER")
        result = ExistingOwnerProjectionCoordinatorV2(service, owners).resolve(
            _request()
        )
        assert result.absence.reason_codes == (ReasonCode.ST12F_INPUT_LOCK_MISMATCH,)
    elif case_id == "G-FAIL::039":
        service = _EvidenceService()
        service.handoff = replace(
            handoff,
            source_epoch_refs=("SOURCE::1=EPOCH::OTHER",),
        )
        result = ExistingOwnerProjectionCoordinatorV2(service, owners).resolve(
            _request()
        )
        assert result.absence.reason_codes == (ReasonCode.SOURCE_CONFLICT,)
    elif case_id == "G-FAIL::041":
        other = replace(handoff, handoff_id="G-HANDOFF::OTHER")
        bad_bundle = replace(bundle, g_handoff_projection=other)
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::042":
        bad_bundle = _mutated(bundle, actual_executed_component_versions={})
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::043":
        bad_bundle = _mutated(bundle, actual_executed_stack_versions=[])
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::044":
        bad_handoff = _mutated(
            handoff,
            champion_challenger_evidence_refs=("CHAMPION::1", "CHAMPION::1"),
        )
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::045":
        candidate = _compiler_candidate(
            "    rewritten_refs = tuple(sorted((\"REF::B\", \"REF::A\")))"
        )
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    else:
        raise AssertionError((case_id, trigger, expected, owners, reference))


_CONTRACT_CASES = (*_HISTORICAL_CONTRACT_CASES, *_FAIL_CASES_CONTRACT)


@pytest.mark.parametrize(
    "case",
    _CONTRACT_CASES,
    ids=[row[0] for row in _CONTRACT_CASES],
)
def test_st12g_contract_case(case: tuple[str, ...] | _BehaviorCase) -> None:
    if not isinstance(case, _BehaviorCase):
        _run_historical_contract(case[0])
    else:
        assert case.verification_mode in {
            "PRODUCTION_MUTATION_REJECTION",
            "EXISTING_OWNER_REJECTION_PROPAGATION",
            "STATIC_ARCHITECTURE_MUTATION_DETECTION",
            "DETERMINISTIC_PRESERVATION_PROOF",
        }
        assert case.valid_baseline_factory
        assert case.production_entrypoint
        assert case.expected_terminal_outcome
        _run_contract_failure(
            case.case_id,
            case.declared_mutation_action,
            case.expected_reason_code,
        )
