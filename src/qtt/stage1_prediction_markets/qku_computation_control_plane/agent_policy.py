"""Central ST12-E no-effect agent capability policy and projection owner."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from src.qtt.agents.pr169_agent_orch1_resolvers import (
    AgentOrchPolicySnapshotV1,
    AgentOrchService,
)
from src.qtt.dashboard.owner_action_registry import OwnerActionRegistry

from .authority import TRANCHE_A_AUTHORITY
from .errors import AuthorityDeniedError, ReasonCode
from .parameter_policy import (
    ST12E_PARAMETER_CAPABILITY_BINDINGS,
    ST12E_PARAMETER_POLICY_SPECS,
    resolve_st12e_value_policy_refs,
    resolve_st12e_value_policies,
)


POLICY_VERSION = "ST12E_AGENT_CAPABILITY_POLICY_V1_1"
ACTIVATION_STATE = "NO_EFFECT_CONTRACT_ONLY"
NO_EFFECT_PROFILE_REF = "TRANCHE_A_AUTHORITY"
CENTRAL_VALIDATOR_REF = (
    "tools/independent_validate_qku_computation_control_plane_e.py"
)
CURRENT_ROSTER_REF = (
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
)
CURRENT_DUTY_REF = (
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"
)
AGENT_ORCH_PREFIX = "docs/master_plan/generated/pr169_agent_orch1"
MASTER_PARAMETER_SOURCE_REF = "docs/master_plan/QTT_MasterPlan_Current.md"
IDENTITY_MAPPING_EXACT = "EXACT_CURRENT_SCOPED_NO_EFFECT_MAPPING"
IDENTITY_MAPPING_UNMAPPED = "UNMAPPED_CROSSWALK_REQUIRED_NO_AUTHORITY"
UPSTREAM_IDENTITY_FULLY_MAPPED = "UPSTREAM_IDENTITY_FULLY_MAPPED"
UPSTREAM_IDENTITY_CROSSWALK_REQUIRED = (
    "UPSTREAM_IDENTITY_CROSSWALK_REQUIRED"
)
ST12E_BINDING_EXACT = "EXACT_ST12E_CAPABILITY_BINDING"
ST12E_BINDING_OUTSIDE_SCOPE = "OUTSIDE_ST12E_CAPABILITY_BINDING_SCOPE"

IMPLEMENTED_OPERATION_IDS = (
    "resolve_identity",
    "resolve_contextual_computability",
    "resolve_applicable_stack",
    "resolve_required_inputs",
    "compute_component",
    "compute_stack",
    "compare_with_no_trade",
    "evaluate_trade_plan",
    "get_snapshot_view",
    "explain_resolution",
    "submit_candidate_proposal",
    "request_materialization_work_order",
)
HELD_OPERATION_IDS = (
    "compile_replay_paper_cohort",
    "register_replay_paper_result",
    "build_evidence_bundle",
)
SAFETY_NON_MATERIAL_OPERATION_IDS = (
    "resolve_identity",
    "get_snapshot_view",
    "explain_resolution",
)
OWNER_ACTION_IDS = (
    "REQUEST_AGENT_TASK",
    "SUBMIT_RESEARCH_CANDIDATE",
    "ADD_SOURCE_REQUEST",
    "REQUEST_VARIABLE_OPTIMIZATION",
    "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW",
    "REQUEST_MEMORY_REVALIDATION",
    "REQUEST_QSTRUCT_MAPPING_REVIEW",
    "REQUEST_REPLAY_TEST",
    "REQUEST_PAPER_TEST",
    "PROMOTE_TO_LIVE_REVIEW_REQUEST",
    "REQUEST_KILL_SWITCH_REVIEW",
)
ALLOWED_ADVISORY_ACTIONS = (
    "research",
    "summarize",
    "critique",
    "explain",
    "propose",
    "route",
)
FORBIDDEN_AUTHORITY_ACTIONS = (
    "source_truth",
    "risk_pass",
    "profit_proof",
    "order_authority",
    "connector_authority",
    "live_readiness",
)
ALLOWED_TOOL_SCOPE_REFS = (
    "QKUComputationControlPlaneV1",
    "GroundedLLMGatewayV1",
)
SCOPE_REASON_BY_FIELD: Mapping[str, ReasonCode] = MappingProxyType(
    {
        "qku_scope_refs": ReasonCode.QKU_SCOPE_MISMATCH,
        "formula_scope_refs": ReasonCode.FORMULA_SCOPE_MISMATCH,
        "data_scope_refs": ReasonCode.DATA_SCOPE_MISMATCH,
        "tool_scope_refs": ReasonCode.TOOL_SCOPE_MISMATCH,
        "action_scope_refs": ReasonCode.ACTION_SCOPE_MISMATCH,
    }
)
EFFECT_ATTEMPT_REASON_BY_FLAG: Mapping[str, ReasonCode] = MappingProxyType(
    {
        "direct_provider_requested": ReasonCode.DIRECT_PROVIDER_FORBIDDEN,
        "private_state_requested": ReasonCode.PRIVATE_STATE_FORBIDDEN,
        "accepted_source_truth_requested": ReasonCode.SOURCE_TRUTH_FORBIDDEN,
        "replay_paper_effect_requested": (
            ReasonCode.REPLAY_PAPER_EFFECT_FORBIDDEN
        ),
        "llm_inference_requested": ReasonCode.LLM_INFERENCE_FORBIDDEN,
        "qpu_effect_requested": ReasonCode.QPU_EFFECT_FORBIDDEN,
        "mode_activation_requested": ReasonCode.MODE_ACTIVATION_FORBIDDEN,
        "order_release_requested": ReasonCode.ORDER_RELEASE_FORBIDDEN,
        "capital_effect_requested": ReasonCode.CAPITAL_EFFECT_FORBIDDEN,
        "execution_router_bypass_requested": (
            ReasonCode.EXECUTION_ROUTER_BYPASS_FORBIDDEN
        ),
        "self_promotion_requested": ReasonCode.SELF_PROMOTION_FORBIDDEN,
        "self_quarantine_release_requested": (
            ReasonCode.SELF_QUARANTINE_RELEASE_FORBIDDEN
        ),
        "qku_mutation_requested": ReasonCode.SELF_PROMOTION_FORBIDDEN,
        "formula_mutation_requested": ReasonCode.SELF_PROMOTION_FORBIDDEN,
        "parameter_value_mutation_requested": (
            ReasonCode.PARAMETER_SCOPE_MISMATCH
        ),
        "tradeplan_optimization_execution_requested": (
            ReasonCode.OPERATION_NOT_ALLOWED
        ),
    }
)

TASK_ENVELOPE_FIELDS = (
    "principal_id",
    "current_agent_id",
    "certified_source_agent_ids",
    "role_ref",
    "duty_ref",
    "task_id",
    "operation_id",
    "objective_ref",
    "prohibited_objective_refs",
    "qku_scope_refs",
    "formula_scope_refs",
    "data_scope_refs",
    "tool_scope_refs",
    "action_scope_refs",
    "context_ref",
    "market_scope",
    "venue_scope",
    "candidate_scope_ref",
    "portfolio_scope_ref_or_none",
    "mode_eligibility_ref_without_activation",
    "snapshot_version_requirements",
    "policy_version",
    "registry_version",
    "implementation_version_requirements",
    "deadline",
    "latency_class",
    "idempotency_key",
    "retry_policy_ref",
    "money_budget",
    "compute_budget",
    "token_budget",
    "tool_call_budget",
    "external_call_budget",
    "peer_challenge_requirement",
    "segregation_of_duties_requirement",
    "abstention_route",
    "quarantine_route",
    "owner_escalation_route",
    "no_effect_profile_ref",
)
EXPLICIT_ABSENCE = "ABSENT_NOT_APPLICABLE"

QUANTUM_FORMULATION_FIELDS = (
    "problem_id",
    "formulation_version",
    "objective_sense",
    "decision_variable_ids",
    "decision_variable_domains",
    "linear_coefficient_vector_ref",
    "quadratic_coefficient_matrix_ref",
    "constraint_matrix_or_expression_refs",
    "right_hand_side_refs",
    "coefficient_units_and_basis",
    "scaling_and_normalization_policy_ref",
    "penalty_or_native_constraint_policy_ref",
    "original_economic_model_ref",
    "inverse_mapping_ref",
    "original_model_feasibility_recheck_ref",
    "same_formulation_classical_comparator_ref",
    "provider_backend_state_ref_or_explicit_unavailable_state",
    "queue_cost_latency_budget_refs",
    "result_ttl",
    "classical_fallback",
    "no_trade_fallback",
)
LLM_ADVISORY_TASK_FIELDS = (
    "structured_task_type",
    "redacted_context_refs",
    "untrusted_content_boundary",
    "allowlisted_tool_refs",
    "closed_output_schema_ref",
    "citation_provenance_requirements",
    "numerical_recheck_requirement",
    "source_truth_prohibition",
    "risk_mode_order_prohibition",
    "latency_token_cost_tool_budgets",
    "abstention_route",
)
EXTERNAL_CANDIDATE_FIELDS = (
    "candidate_id",
    "provenance_refs",
    "source_class",
    "retrieval_state_or_explicit_absence",
    "effective_state_or_explicit_absence",
    "downstream_consumer_ref",
    "validation_route",
    "terminal_disposition",
)
CANDIDATE_INTAKE_ACTION_IDS = frozenset(
    {"SUBMIT_RESEARCH_CANDIDATE", "ADD_SOURCE_REQUEST"}
)
NO_TRADE_REOPTIMIZATION_VARIABLE_IDS = (
    "market",
    "venue",
    "stack",
    "side",
    "entry",
    "size",
    "hold_duration",
    "exit_rule",
    "maker_taker_split",
    "cancel_replace_interval",
    "liquidity_filter",
    "spread_filter",
    "latency_budget",
    "portfolio_exposure",
    "source_refresh",
    "retest_batch",
    "next_target",
)
OPTIONAL_BOOLEAN_ENVELOPE_FIELDS = frozenset(
    {
        *EFFECT_ATTEMPT_REASON_BY_FLAG,
        "terminal_no_trade",
        "llm_advisory_requested",
        "quantum_challenger",
        "self_review_requested",
        "peer_challenge_satisfied",
        "untrusted_content_instruction_detected",
    }
)
QUANTUM_TUPLE_FIELDS = frozenset(
    {
        "decision_variable_ids",
        "decision_variable_domains",
        "constraint_matrix_or_expression_refs",
        "right_hand_side_refs",
        "queue_cost_latency_budget_refs",
    }
)
FORBIDDEN_MODE_ELIGIBILITY_STATES = frozenset(
    {"ALLOW", "GRANTED", "ACTIVATED", "LIVE_READY", "ORDER_READY"}
)


def current_owner_action_ids() -> tuple[str, ...]:
    """Resolve the E subset through the existing owner action grammar."""

    registry = OwnerActionRegistry.default()
    for action_id in OWNER_ACTION_IDS:
        try:
            definition = registry.get(action_id)
        except KeyError as exc:
            raise AuthorityDeniedError(
                ReasonCode.ACTION_SCOPE_MISMATCH,
                f"central OwnerActionRegistry is missing {action_id}",
            ) from exc
        if definition.get("confirmation_class") not in {
            "OWNER_REVIEW_REQUIRED",
            "CRITICAL_CONFIRMATION",
        }:
            raise AuthorityDeniedError(
                ReasonCode.ACTION_SCOPE_MISMATCH,
                f"{action_id} is not a request/review action",
            )
    return OWNER_ACTION_IDS


class AgentCapabilityDecisionStateV1(StrEnum):
    ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST = (
        "ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST"
    )
    DENIED = "DENIED"
    QUARANTINED = "QUARANTINED"
    OWNER_ESCALATION_REQUIRED = "OWNER_ESCALATION_REQUIRED"
    NO_TRADE_REOPTIMIZATION_ROUTED = "NO_TRADE_REOPTIMIZATION_ROUTED"


class AgentIdentityMappingTypeV1(StrEnum):
    EXACT_ONE_TO_ONE = "EXACT_ONE_TO_ONE"
    EXACT_SCOPED_MULTI_ROLE = "EXACT_SCOPED_MULTI_ROLE"
    UNMAPPED = "UNMAPPED"


class AgentSafetyStateV1(StrEnum):
    GREEN = "GREEN"
    MISSING = "MISSING"
    STALE = "STALE"
    CONFLICT = "CONFLICT"


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise AuthorityDeniedError(
            ReasonCode.TASK_ENVELOPE_MISSING, f"{name} is required"
        )
    return value


def _text_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise AuthorityDeniedError(
            ReasonCode.TASK_SCOPE_MISMATCH,
            f"{name} must be an immutable text tuple",
        )
    if len(value) != len(set(value)):
        raise AuthorityDeniedError(
            ReasonCode.TASK_SCOPE_MISMATCH, f"{name} must be unique"
        )
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in sorted(value.items())}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    return value


@dataclass(frozen=True, slots=True)
class AgentPrincipalBindingV1:
    source_agent_id: str
    source_role_label: str
    mapping_type: AgentIdentityMappingTypeV1
    current_principal_refs: tuple[str, ...]
    current_role_refs: tuple[str, ...]
    current_duty_refs: tuple[str, ...]
    source_scope: tuple[str, ...]
    current_scope: tuple[str, ...]
    intersection_scope: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    terminal_mapping_state: str
    owner_review_currentization_route: str = (
        "OWNER_REVIEW_SOURCE_IDENTITY_CROSSWALK"
    )
    activation_state: str = ACTIVATION_STATE

    def __post_init__(self) -> None:
        _required_text(self.source_agent_id, "source_agent_id")
        _required_text(self.source_role_label, "source_role_label")
        _required_text(self.terminal_mapping_state, "terminal_mapping_state")
        _required_text(
            self.owner_review_currentization_route,
            "owner_review_currentization_route",
        )
        if not isinstance(self.mapping_type, AgentIdentityMappingTypeV1):
            raise AuthorityDeniedError(
                ReasonCode.PRINCIPAL_AMBIGUOUS,
                "identity mapping type must be exact and typed",
            )
        typed_values: dict[str, tuple[str, ...]] = {}
        for name in (
            "current_principal_refs",
            "current_role_refs",
            "current_duty_refs",
            "source_scope",
            "current_scope",
            "intersection_scope",
            "evidence_refs",
        ):
            typed_values[name] = _text_tuple(getattr(self, name), name)
        if not typed_values["source_scope"] or not typed_values["evidence_refs"]:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                f"{self.source_agent_id} lacks source scope or mapping evidence",
            )
        if self.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED:
            if any(
                typed_values[name]
                for name in (
                    "current_principal_refs",
                    "current_role_refs",
                    "current_duty_refs",
                    "current_scope",
                    "intersection_scope",
                )
            ):
                raise AuthorityDeniedError(
                    ReasonCode.PRINCIPAL_AMBIGUOUS,
                    "an unmapped source identity cannot carry current scope",
                )
        elif any(
            not typed_values[name]
            for name in (
                "current_principal_refs",
                "current_role_refs",
                "current_duty_refs",
                "current_scope",
                "intersection_scope",
            )
        ):
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                f"{self.source_agent_id} has no exact current mapping",
            )
        if not set(self.intersection_scope) <= set(self.source_scope) & set(
            self.current_scope
        ):
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY,
                f"{self.source_agent_id} mapping widens certified scope",
            )
        if self.activation_state != ACTIVATION_STATE:
            raise AuthorityDeniedError(
                ReasonCode.SELF_PROMOTION_FORBIDDEN,
                "identity compatibility cannot activate authority",
            )
        if (
            self.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED
            and self.terminal_mapping_state != IDENTITY_MAPPING_UNMAPPED
        ) or (
            self.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
            and self.terminal_mapping_state != IDENTITY_MAPPING_EXACT
        ):
            raise AuthorityDeniedError(
                ReasonCode.PRINCIPAL_AMBIGUOUS,
                "identity mapping state does not match its typed disposition",
            )


@dataclass(frozen=True, slots=True)
class AgentIdentityCompatibilityMapV1:
    bindings: Mapping[str, AgentPrincipalBindingV1]

    def __post_init__(self) -> None:
        if not self.bindings or any(
            key != value.source_agent_id
            for key, value in self.bindings.items()
        ):
            raise AuthorityDeniedError(
                ReasonCode.PRINCIPAL_AMBIGUOUS,
                "source identity compatibility map is incomplete",
            )
        object.__setattr__(
            self, "bindings", MappingProxyType(dict(self.bindings))
        )

    def describe_for_lineage(
        self, source_agent_id: str
    ) -> AgentPrincipalBindingV1:
        try:
            return self.bindings[source_agent_id]
        except KeyError as exc:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED, source_agent_id
            ) from exc

    def require_current_authority_mapping(
        self, source_agent_id: str
    ) -> AgentPrincipalBindingV1:
        binding = self.describe_for_lineage(source_agent_id)
        if binding.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED, source_agent_id
            )
        return binding

    def resolve(self, source_agent_id: str) -> AgentPrincipalBindingV1:
        """Compatibility alias for the fail-closed authority lookup."""

        return self.require_current_authority_mapping(source_agent_id)


@dataclass(frozen=True, slots=True)
class AgentBoundaryStateViewV1:
    state: AgentSafetyStateV1
    state_ref: str
    observed_at: str
    valid_until: str
    safety_state_non_material: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, AgentSafetyStateV1):
            raise AuthorityDeniedError(
                ReasonCode.SAFETY_STATE_CONFLICT,
                "safety state must use AgentSafetyStateV1",
            )
        _required_text(self.state_ref, "state_ref")
        _required_text(self.observed_at, "observed_at")
        _required_text(self.valid_until, "valid_until")
        if type(self.safety_state_non_material) is not bool:
            raise AuthorityDeniedError(
                ReasonCode.SAFETY_STATE_CONFLICT,
                "safety materiality must be explicit",
            )


@dataclass(frozen=True, slots=True)
class AgentCapabilityBundleV1:
    bundle_id: str
    principal_id: str
    current_agent_id: str
    certified_source_agent_ids: tuple[str, ...]
    role_ref: str
    duty_ref: str
    permission_scope: tuple[str, ...]
    task_envelope: Mapping[str, object]
    boundary_state: AgentBoundaryStateViewV1
    trust_state: str = "SUFFICIENT_FOR_NO_EFFECT_REVIEW"
    quarantined: bool = False

    def __post_init__(self) -> None:
        for name in (
            "bundle_id",
            "principal_id",
            "current_agent_id",
            "role_ref",
            "duty_ref",
            "trust_state",
        ):
            _required_text(getattr(self, name), name)
        source_agent_ids = _text_tuple(
            self.certified_source_agent_ids, "certified_source_agent_ids"
        )
        permission_scope = _text_tuple(self.permission_scope, "permission_scope")
        if not source_agent_ids:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                "a capability bundle requires a certified source identity",
            )
        if not permission_scope:
            raise AuthorityDeniedError(
                ReasonCode.OPERATION_NOT_ALLOWED,
                "a capability bundle requires a bounded permission scope",
            )
        if not isinstance(self.task_envelope, Mapping):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_MISSING,
                "task_envelope must be a typed mapping",
            )
        missing = tuple(
            name for name in TASK_ENVELOPE_FIELDS if name not in self.task_envelope
        )
        if missing:
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_MISSING,
                f"task envelope fields missing: {missing}",
            )
        for name in (
            "certified_source_agent_ids",
            "prohibited_objective_refs",
            "qku_scope_refs",
            "formula_scope_refs",
            "data_scope_refs",
            "tool_scope_refs",
            "action_scope_refs",
            "snapshot_version_requirements",
            "implementation_version_requirements",
        ):
            values = _text_tuple(self.task_envelope[name], name)
            if not values:
                raise AuthorityDeniedError(
                    ReasonCode.TASK_SCOPE_MISMATCH,
                    f"{name} requires an exact value or explicit absence state",
                )
        for name in (
            "principal_id",
            "current_agent_id",
            "role_ref",
            "duty_ref",
            "task_id",
            "operation_id",
            "objective_ref",
            "context_ref",
            "market_scope",
            "venue_scope",
            "candidate_scope_ref",
            "portfolio_scope_ref_or_none",
            "mode_eligibility_ref_without_activation",
            "policy_version",
            "registry_version",
            "deadline",
            "latency_class",
            "idempotency_key",
            "retry_policy_ref",
            "abstention_route",
            "quarantine_route",
            "owner_escalation_route",
            "no_effect_profile_ref",
        ):
            _required_text(self.task_envelope[name], name)
        for name in (
            "peer_challenge_requirement",
            "segregation_of_duties_requirement",
        ):
            if type(self.task_envelope[name]) is not bool:
                raise AuthorityDeniedError(
                    ReasonCode.TASK_SCOPE_MISMATCH,
                    f"{name} must be an explicit boolean",
                )
        for name in (
            "money_budget",
            "compute_budget",
            "token_budget",
            "tool_call_budget",
            "external_call_budget",
        ):
            value = self.task_envelope[name]
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or (isinstance(value, float) and not math.isfinite(value))
                or value < 0
            ):
                raise AuthorityDeniedError(
                    ReasonCode.BUDGET_EXCEEDED,
                    f"{name} must be one explicit nonnegative bound",
                )
        object.__setattr__(self, "task_envelope", _freeze(self.task_envelope))
        if not isinstance(self.boundary_state, AgentBoundaryStateViewV1):
            raise AuthorityDeniedError(
                ReasonCode.SAFETY_STATE_MISSING,
                "a read-only safety-state view is required",
            )
        if type(self.quarantined) is not bool:
            raise AuthorityDeniedError(
                ReasonCode.QUARANTINED,
                "quarantine state must be explicit",
            )


@dataclass(frozen=True, slots=True)
class AgentCapabilityPolicyRowV1:
    row_id: str
    domain: str
    operation_ids: tuple[str, ...]
    source_agent_ids: tuple[str, ...]
    downstream_consumer_refs: tuple[str, ...]
    terminal_route: str
    validator_ref: str = CENTRAL_VALIDATOR_REF
    activation_state: str = ACTIVATION_STATE

    def __post_init__(self) -> None:
        for name in ("row_id", "domain", "terminal_route", "validator_ref"):
            _required_text(getattr(self, name), name)
        for name in (
            "operation_ids",
            "source_agent_ids",
            "downstream_consumer_refs",
        ):
            if not _text_tuple(getattr(self, name), name):
                raise AuthorityDeniedError(
                    ReasonCode.TASK_SCOPE_MISMATCH,
                    f"capability policy {name} cannot be empty",
                )
        if (
            not set(self.operation_ids) <= set(IMPLEMENTED_OPERATION_IDS)
            or self.activation_state != ACTIVATION_STATE
        ):
            raise AuthorityDeniedError(
                ReasonCode.SELF_PROMOTION_FORBIDDEN,
                "capability policy row is out of E no-effect scope",
            )


@dataclass(frozen=True, slots=True)
class AgentParameterScopeViewV1:
    parameter_id: str
    parameter_symbol: str
    upstream_source_universe_ref: str
    upstream_identity_mapping_state: str
    mapped_compatibility_refs: tuple[str, ...]
    unmapped_compatibility_refs: tuple[str, ...]
    current_principal_refs_or_exact_gap: tuple[str, ...]
    value_policy_ref: str
    st12e_binding_state: str
    st12e_capability_binding_ref_or_explicit_absence: str
    st12e_certified_source_universe_ref_or_explicit_absence: str
    st12e_current_principal_refs_or_explicit_absence: tuple[str, ...]
    lifecycle_state: str
    timing_state: str
    downstream_consumer_refs: tuple[str, ...]
    validator_ref: str
    terminal_route: str
    semantic_owner: str
    implementation_owner: str
    producer_ref: str
    upstream_artifact_refs: tuple[str, ...]
    upstream_row_or_value_refs: tuple[str, ...]
    current_principal_duty_policy_refs: tuple[str, ...]
    activation_state: str = ACTIVATION_STATE

    def __post_init__(self) -> None:
        for name in (
            "parameter_id",
            "parameter_symbol",
            "upstream_source_universe_ref",
            "upstream_identity_mapping_state",
            "value_policy_ref",
            "st12e_binding_state",
            "st12e_capability_binding_ref_or_explicit_absence",
            "st12e_certified_source_universe_ref_or_explicit_absence",
            "lifecycle_state",
            "timing_state",
            "validator_ref",
            "terminal_route",
            "semantic_owner",
            "implementation_owner",
            "producer_ref",
        ):
            _required_text(getattr(self, name), name)
        for name in (
            "mapped_compatibility_refs",
            "unmapped_compatibility_refs",
            "current_principal_refs_or_exact_gap",
            "st12e_current_principal_refs_or_explicit_absence",
            "downstream_consumer_refs",
            "upstream_artifact_refs",
            "upstream_row_or_value_refs",
            "current_principal_duty_policy_refs",
        ):
            if not _text_tuple(getattr(self, name), name):
                raise AuthorityDeniedError(
                    ReasonCode.PARAMETER_SCOPE_MISMATCH,
                    f"{self.parameter_id} has no {name}",
                )
        if self.activation_state != ACTIVATION_STATE:
            raise AuthorityDeniedError(
                ReasonCode.SELF_PROMOTION_FORBIDDEN,
                f"{self.parameter_id} has an effect-bearing activation state",
            )
        has_unmapped = self.unmapped_compatibility_refs != (EXPLICIT_ABSENCE,)
        expected_upstream_state = (
            UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
            if has_unmapped
            else UPSTREAM_IDENTITY_FULLY_MAPPED
        )
        if self.upstream_identity_mapping_state != expected_upstream_state:
            raise AuthorityDeniedError(
                ReasonCode.PARAMETER_SCOPE_MISMATCH,
                f"{self.parameter_id} has a mismatched upstream mapping state",
            )
        if self.st12e_binding_state == ST12E_BINDING_EXACT:
            if (
                self.st12e_capability_binding_ref_or_explicit_absence
                == EXPLICIT_ABSENCE
                or self.st12e_certified_source_universe_ref_or_explicit_absence
                == EXPLICIT_ABSENCE
                or self.st12e_current_principal_refs_or_explicit_absence
                == (EXPLICIT_ABSENCE,)
                or self.terminal_route
                != "NO_EFFECT_QKU_REQUEST_OR_TYPED_DENIAL"
            ):
                raise AuthorityDeniedError(
                    ReasonCode.PARAMETER_SCOPE_MISMATCH,
                    f"{self.parameter_id} exact E binding is incomplete",
                )
        elif self.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE:
            if (
                self.st12e_capability_binding_ref_or_explicit_absence
                != EXPLICIT_ABSENCE
                or self.st12e_certified_source_universe_ref_or_explicit_absence
                != EXPLICIT_ABSENCE
                or self.st12e_current_principal_refs_or_explicit_absence
                != (EXPLICIT_ABSENCE,)
                or self.terminal_route
                != "ST12E_CAPABILITY_BINDING_NOT_APPLICABLE"
            ):
                raise AuthorityDeniedError(
                    ReasonCode.PARAMETER_SCOPE_MISMATCH,
                    f"{self.parameter_id} outside-E state carries E authority",
                )
        else:
            raise AuthorityDeniedError(
                ReasonCode.PARAMETER_SCOPE_MISMATCH,
                f"{self.parameter_id} has an unknown E binding state",
            )


@dataclass(frozen=True, slots=True)
class AgentCapabilityDecisionV1:
    decision_id: str
    request_id: str
    task_id: str
    principal_id: str
    current_agent_id: str
    source_agent_refs: tuple[str, ...]
    operation_id: str
    policy_version: str
    decision_state: AgentCapabilityDecisionStateV1
    reason_codes: tuple[ReasonCode, ...]
    scope_refs: tuple[str, ...]
    idempotency_key: str
    retry_disposition: str
    peer_sod_disposition: str
    safety_state_disposition: str
    terminal_route: str
    agent_orch_receipt_ref: str
    st12c_causation_correlation_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    alternative_route_refs: tuple[str, ...]
    disagreement_state: str
    confidence_state: str
    limitation_codes: tuple[str, ...]
    no_effect_profile_ref: str = NO_EFFECT_PROFILE_REF
    runtime_effect_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "request_id",
            "task_id",
            "principal_id",
            "current_agent_id",
            "operation_id",
            "policy_version",
            "idempotency_key",
            "retry_disposition",
            "peer_sod_disposition",
            "safety_state_disposition",
            "terminal_route",
            "agent_orch_receipt_ref",
            "disagreement_state",
            "confidence_state",
        ):
            _required_text(getattr(self, name), name)
        for name in (
            "source_agent_refs",
            "st12c_causation_correlation_refs",
            "evidence_refs",
            "alternative_route_refs",
            "limitation_codes",
        ):
            values = _text_tuple(getattr(self, name), name)
            if not values:
                raise AuthorityDeniedError(
                    ReasonCode.TASK_SCOPE_MISMATCH,
                    f"decision {name} cannot be empty",
                )
        _text_tuple(self.scope_refs, "scope_refs")
        if (
            not isinstance(self.decision_state, AgentCapabilityDecisionStateV1)
            or any(not isinstance(reason, ReasonCode) for reason in self.reason_codes)
            or len(self.reason_codes) != len(set(self.reason_codes))
            or self.no_effect_profile_ref != NO_EFFECT_PROFILE_REF
            or self.runtime_effect_authorized is not False
        ):
            raise AuthorityDeniedError(
                ReasonCode.SELF_PROMOTION_FORBIDDEN,
                "capability decision is malformed or effect-bearing",
            )
        if (
            self.decision_state
            is not AgentCapabilityDecisionStateV1.DENIED
            and not self.scope_refs
        ):
            raise AuthorityDeniedError(
                ReasonCode.TASK_SCOPE_MISMATCH,
                "non-denial capability decisions require resolved scope evidence",
            )
        if (
            self.decision_state
            is AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
            and self.reason_codes
        ) or (
            self.decision_state
            is not AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
            and not self.reason_codes
        ):
            raise AuthorityDeniedError(
                ReasonCode.SELF_PROMOTION_FORBIDDEN,
                "eligible decisions cannot carry blockers and terminal decisions require one",
            )

    @property
    def eligible(self) -> bool:
        return self.decision_state is (
            AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
        )


@dataclass(frozen=True, slots=True)
class AgentCapabilityPolicySnapshotV1:
    policy_version: str
    registry_version: str
    identity_map: AgentIdentityCompatibilityMapV1
    policy_rows: Mapping[str, Mapping[str, object]]
    parameter_scope_rows: Mapping[str, AgentParameterScopeViewV1]
    agent_orch_task_rows: Mapping[str, Mapping[str, object]]
    agent_orch_receipt_refs_by_candidate_id: Mapping[str, str]
    agent_orch_receipt_rows: Mapping[str, Mapping[str, object]]
    owner_action_ids: tuple[str, ...]
    no_effect_profile_ref: str

    def __post_init__(self) -> None:
        if (
            self.policy_version != POLICY_VERSION
            or not self.registry_version
            or not isinstance(self.identity_map, AgentIdentityCompatibilityMapV1)
            or self.no_effect_profile_ref != NO_EFFECT_PROFILE_REF
        ):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_STALE,
                "capability snapshot identity or authority profile is invalid",
            )
        owner_action_ids = _text_tuple(
            self.owner_action_ids, "owner_action_ids"
        )
        if not owner_action_ids:
            raise AuthorityDeniedError(
                ReasonCode.ACTION_SCOPE_MISMATCH,
                "capability snapshot has no central owner actions",
            )
        for name in (
            "policy_rows",
            "parameter_scope_rows",
            "agent_orch_task_rows",
            "agent_orch_receipt_refs_by_candidate_id",
            "agent_orch_receipt_rows",
        ):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise AuthorityDeniedError(
                    ReasonCode.TASK_ENVELOPE_STALE,
                    f"capability snapshot {name} must be an indexed mapping",
                )
            object.__setattr__(self, name, _freeze(value))


_SOURCE_IDENTITY_SPEC = (
    ("AGENT_RT_07", "Live Risk Gate", ("risk_manager_agent",), ("RISK_AGENT",)),
    (
        "AGENT_RT_09",
        "Trade Executor",
        ("connector_venue_readiness_future_consumer",),
        ("EXECUTION_PREP_AGENT",),
    ),
    (
        "AGENT_RT_11",
        "Dashboard API / Local Control Surface",
        ("dashboard_agent",),
        ("COMMANDER_AGENT",),
    ),
    (
        "AGENT_RT_13",
        "Kill Switch / Safe Harbor Controller",
        ("governance_agent",),
        ("GOVERNANCE_AGENT",),
    ),
    (
        "AGENT_NL_02",
        "Research & Intelligence Agent",
        ("research_agent",),
        ("SCOUT_AGENT", "SOURCE_AGENT"),
    ),
    (
        "AGENT_NL_05",
        "Proposal / Approval Packager",
        ("commander_agent",),
        ("COMMANDER_AGENT",),
    ),
    (
        "AGENT_NL_09",
        "Replay Result Synthesizer",
        ("parameter_selector_agent",),
        ("SIMULATION_PRETRADE_AGENT",),
    ),
    (
        "AGENT_NL_10",
        "Artifact Promotion Recommender",
        ("parameter_selector_agent",),
        ("RANKING_AGENT",),
    ),
    (
        "AGENT_OFF_01",
        "Quantum Job Orchestrator",
        ("quantum_optimizer_agent",),
        ("QUANTUM_AGENT",),
    ),
    (
        "AGENT_OFF_03",
        "Quantum Allocation Challenger",
        ("quantum_optimizer_agent",),
        ("QUANTUM_AGENT",),
    ),
    (
        "AGENT_OFF_07",
        "Model / Feature Retraining",
        ("research_agent",),
        ("FORMULA_AGENT",),
    ),
    (
        "AGENT_OFF_11",
        "Quantum Preset Recon & Development Agent",
        ("quantum_optimizer_agent", "research_agent"),
        ("QUANTUM_AGENT", "SCOUT_AGENT"),
    ),
)

_CURRENT_PRINCIPAL_ROLE_BY_ID: Mapping[str, str] = MappingProxyType(
    {
        "research_agent": "external_signal_and_materialization_research",
        "parameter_selector_agent": (
            "scenario_selection_and_retest_batch_building"
        ),
        "risk_manager_agent": (
            "tca_false_discovery_capacity_and_microstructure_review"
        ),
        "quantum_optimizer_agent": (
            "quantum_candidate_priority_and_mapping_review"
        ),
        "commander_agent": (
            "downstream_pr_route_and_command_action_ownership"
        ),
        "governance_agent": (
            "authority_boundary_no_orphan_status_and_validation_review"
        ),
        "dashboard_agent": (
            "owner_visible_selection_handoff_and_review_labels"
        ),
        "connector_venue_readiness_future_consumer": (
            "future_connector_readiness_reference_consumption_only"
        ),
    }
)


def build_identity_compatibility_map(
    orch_snapshot: AgentOrchPolicySnapshotV1,
    *,
    source_agent_ids: Iterable[str] | None = None,
    source_role_labels: Mapping[str, str] | None = None,
) -> AgentIdentityCompatibilityMapV1:
    def unique_index(
        rows: Iterable[Mapping[str, Any]], key: str
    ) -> dict[str, Mapping[str, Any]]:
        indexed: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            value = str(row.get(key) or "")
            if not value or value in indexed:
                raise AuthorityDeniedError(
                    ReasonCode.PRINCIPAL_AMBIGUOUS,
                    f"current identity owner has a missing or duplicate {key}",
                )
            indexed[value] = row
        return indexed

    role_rows = unique_index(orch_snapshot.role_rows, "agent_id_or_role")
    duty_rows = unique_index(orch_snapshot.duty_rows, "agent_id_or_role")
    roster_rows = unique_index(orch_snapshot.pr165_roster_rows, "agent_id")
    duty_source_rows = unique_index(
        orch_snapshot.pr165_duty_source_rows, "agent_id"
    )
    permission_scopes = [
        {str(action) for action in tuple(row.get("allowed_actions") or ())}
        for row in orch_snapshot.permission_rows
    ]
    permission_forbidden = [
        {str(action) for action in tuple(row.get("forbidden_actions") or ())}
        for row in orch_snapshot.permission_rows
    ]
    permission_actions = (
        set.intersection(*permission_scopes) if permission_scopes else set()
    )
    if (
        not orch_snapshot.manifest_version
        or not permission_actions
        or not permission_actions <= set(ALLOWED_ADVISORY_ACTIONS)
        or any(
            not set(FORBIDDEN_AUTHORITY_ACTIONS) <= forbidden
            for forbidden in permission_forbidden
        )
    ):
        raise AuthorityDeniedError(
            ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY,
            "AGENT-ORCH1 policy snapshot is absent or broader than review-only",
        )
    exact_source_ids = tuple(row[0] for row in _SOURCE_IDENTITY_SPEC)
    complete_source_ids = tuple(
        sorted(
            set(exact_source_ids)
            if source_agent_ids is None
            else set(source_agent_ids)
        )
    )
    if (
        not set(exact_source_ids) <= set(complete_source_ids)
        or any(
            not re.fullmatch(r"AGENT_(?:RT|NL|OFF)_\d{2}", source_id)
            for source_id in complete_source_ids
        )
    ):
        raise AuthorityDeniedError(
            ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
            "canonical source identity universe omits an authorized mapping",
        )
    role_labels = dict(source_role_labels or {})
    bindings: dict[str, AgentPrincipalBindingV1] = {}
    for source_id, label, principals, roles in _SOURCE_IDENTITY_SPEC:
        if not set(roles) <= set(role_rows) & set(duty_rows):
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                f"{source_id} lacks an exact current role/duty join",
            )
        evidence_refs: list[str] = []
        for role in roles:
            evidence_refs.extend(
                (
                    f"{AGENT_ORCH_PREFIX}/role_map.jsonl::{role_rows[role]['row_id']}",
                    f"{AGENT_ORCH_PREFIX}/duty_map.jsonl::{duty_rows[role]['row_id']}",
                )
            )
        evidence_refs.extend(
            f"{AGENT_ORCH_PREFIX}/perm_scope.jsonl::{row['row_id']}"
            for row in orch_snapshot.permission_rows
        )
        for principal in principals:
            roster_row = roster_rows.get(principal)
            duty_source_row = duty_source_rows.get(principal)
            if (
                roster_row is None
                or duty_source_row is None
                or roster_row.get("validation_status") != "PASS"
                or duty_source_row.get("validation_status") != "PASS"
                or roster_row.get("agent_role")
                != _CURRENT_PRINCIPAL_ROLE_BY_ID.get(principal)
                or duty_source_row.get("historical_duty_preserved_flag")
                is not True
            ):
                raise AuthorityDeniedError(
                    ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                    f"{source_id} lacks an exact PR165-D2 principal/duty row",
                )
            evidence_refs.extend(
                (
                    f"{CURRENT_ROSTER_REF}::{roster_row['row_id']}",
                    f"{CURRENT_DUTY_REF}::{duty_source_row['row_id']}",
                )
            )
        scope_sets = [
            permission_actions,
            *(
                {
                    str(action)
                    for action in tuple(
                        role_rows[role].get("allowed_actions") or ()
                    )
                }
                for role in roles
            ),
            *(
                {
                    str(action)
                    for action in tuple(
                        duty_rows[role].get("allowed_actions") or ()
                    )
                }
                for role in roles
            ),
        ]
        current_scope = set.intersection(*scope_sets)
        intersection_scope = current_scope & set(ALLOWED_ADVISORY_ACTIONS)
        if not intersection_scope or current_scope != intersection_scope:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY,
                f"{source_id} current scope is empty or broader than E",
            )
        mapping_type = (
            AgentIdentityMappingTypeV1.EXACT_ONE_TO_ONE
            if len(principals) == len(roles) == 1
            else AgentIdentityMappingTypeV1.EXACT_SCOPED_MULTI_ROLE
        )
        bindings[source_id] = AgentPrincipalBindingV1(
            source_agent_id=source_id,
            source_role_label=label,
            mapping_type=mapping_type,
            current_principal_refs=principals,
            current_role_refs=roles,
            current_duty_refs=roles,
            source_scope=ALLOWED_ADVISORY_ACTIONS,
            current_scope=tuple(sorted(current_scope)),
            intersection_scope=tuple(sorted(intersection_scope)),
            evidence_refs=tuple(dict.fromkeys(evidence_refs)),
            terminal_mapping_state=IDENTITY_MAPPING_EXACT,
        )
    for source_id in sorted(set(complete_source_ids) - set(bindings)):
        bindings[source_id] = AgentPrincipalBindingV1(
            source_agent_id=source_id,
            source_role_label=role_labels.get(source_id, EXPLICIT_ABSENCE),
            mapping_type=AgentIdentityMappingTypeV1.UNMAPPED,
            current_principal_refs=(),
            current_role_refs=(),
            current_duty_refs=(),
            source_scope=("LINEAGE_ONLY_NO_AUTHORITY",),
            current_scope=(),
            intersection_scope=(),
            evidence_refs=(
                f"{MASTER_PARAMETER_SOURCE_REF}::source_agent_id={source_id}",
            ),
            terminal_mapping_state=IDENTITY_MAPPING_UNMAPPED,
        )
    return AgentIdentityCompatibilityMapV1(bindings)


_UNIVERSE_LINE = re.compile(
    r"\{\s*((?:AGENT_(?:RT|NL|OFF)_\d{2})(?:\s*,\s*AGENT_(?:RT|NL|OFF)_\d{2})*)\s*\}"
)
_PARAMETER_LINE = re.compile(r"`parameter_symbol`\s*:\s*`([^`]+)`")
_SOURCE_ROLE_LINE = re.compile(
    r"^#{5,6} .*?`(AGENT_(?:RT|NL|OFF)_\d{2})`\s+(?:\N{EM DASH}|-)\s+(.+?)\s*$"
)


def canonical_master_parameter_rows(
    master_plan_text: str,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Parse exact parameter identities and source sets from the canonical owner."""

    rows: list[tuple[str, str, tuple[str, ...]]] = []
    source_agents: tuple[str, ...] | None = None
    awaiting_universe = False
    for line in master_plan_text.splitlines():
        if "Explicit agent-selection-universe binding" in line:
            source_agents = None
            awaiting_universe = True
        if awaiting_universe:
            match = _UNIVERSE_LINE.search(line)
            if match:
                source_agents = tuple(
                    value.strip() for value in match.group(1).split(",")
                )
                awaiting_universe = False
        match = _PARAMETER_LINE.search(line)
        if match:
            if source_agents is None:
                raise AuthorityDeniedError(
                    ReasonCode.PARAMETER_SCOPE_MISMATCH,
                    "master parameter lacks an explicit source-agent universe",
                )
            parameter_number = len(rows) + 1
            rows.append(
                (
                    f"ST10-PARAM::{parameter_number:04d}",
                    match.group(1),
                    source_agents,
                )
            )
    return tuple(rows)


def _master_parameter_rows(
    master_plan_text: str,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Compatibility view over the canonical parser."""

    return canonical_master_parameter_rows(master_plan_text)


def canonical_source_role_labels(
    master_plan_text: str,
) -> Mapping[str, str]:
    labels = {
        match.group(1): match.group(2)
        for line in master_plan_text.splitlines()
        if (match := _SOURCE_ROLE_LINE.match(line))
    }
    return MappingProxyType(dict(sorted(labels.items())))


def canonical_parameter_identity_registry(
    master_plan_text: str,
) -> Mapping[str, str]:
    return MappingProxyType(
        {
            parameter_id: symbol
            for parameter_id, symbol, _ in canonical_master_parameter_rows(
                master_plan_text
            )
        }
    )


def canonical_source_agent_ids(master_plan_text: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                source_agent_id
                for _, _, source_agent_ids in canonical_master_parameter_rows(
                    master_plan_text
                )
                for source_agent_id in source_agent_ids
            }
        )
    )


_SOURCE_AGENT_ID_TOKEN = re.compile(r"^AGENT_(RT|NL|OFF)_(\d{2})$")
_SOURCE_UNIVERSE_NAMESPACES = frozenset(
    {"UPSTREAM_SOURCE_UNIVERSE", "ST12E_CERTIFIED_SOURCE_UNIVERSE"}
)


def stable_source_universe_ref(
    namespace: str,
    source_agent_ids: tuple[str, ...],
) -> str:
    """Return an order-preserving readable identity for one exact source set."""

    if namespace not in _SOURCE_UNIVERSE_NAMESPACES:
        raise AuthorityDeniedError(
            ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
            "source-universe namespace is not canonical",
        )
    if (
        not isinstance(source_agent_ids, tuple)
        or not source_agent_ids
        or len(source_agent_ids) != len(set(source_agent_ids))
    ):
        raise AuthorityDeniedError(
            ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
            "source universe must be a nonempty ordered unique tuple",
        )
    tokens: list[str] = []
    for source_agent_id in source_agent_ids:
        match = _SOURCE_AGENT_ID_TOKEN.fullmatch(source_agent_id)
        if match is None:
            raise AuthorityDeniedError(
                ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
                f"source identity cannot form a stable reference: {source_agent_id}",
            )
        tokens.append(f"{match.group(1)}{match.group(2)}")
    return f"{namespace}::{'-'.join(tokens)}"


def build_upstream_source_universe_registry(
    master_rows: Iterable[tuple[str, str, tuple[str, ...]]],
) -> tuple[
    Mapping[str, Mapping[str, object]],
    Mapping[tuple[str, ...], str],
]:
    counts = Counter(source_ids for _, _, source_ids in master_rows)
    definitions: dict[str, Mapping[str, object]] = {}
    refs_by_source_set: dict[tuple[str, ...], str] = {}
    for source_ids in sorted(counts):
        universe_ref = stable_source_universe_ref(
            "UPSTREAM_SOURCE_UNIVERSE", source_ids
        )
        definitions[universe_ref] = MappingProxyType(
            {
                "source_agent_ids": source_ids,
                "parameter_count": counts[source_ids],
            }
        )
        refs_by_source_set[source_ids] = universe_ref
    return (
        MappingProxyType(definitions),
        MappingProxyType(refs_by_source_set),
    )


def build_st12e_certified_source_universe_registry() -> tuple[
    Mapping[str, Mapping[str, object]],
    Mapping[tuple[str, ...], str],
]:
    """Deduplicate the audited E source sets without granting authority."""

    counts = Counter(
        binding.certified_source_agent_ids
        for binding in ST12E_PARAMETER_CAPABILITY_BINDINGS.values()
    )
    definitions: dict[str, Mapping[str, object]] = {}
    refs_by_source_set: dict[tuple[str, ...], str] = {}
    for source_ids in sorted(counts):
        universe_ref = stable_source_universe_ref(
            "ST12E_CERTIFIED_SOURCE_UNIVERSE", source_ids
        )
        definitions[universe_ref] = MappingProxyType(
            {
                "source_agent_ids": source_ids,
                "parameter_count": counts[source_ids],
                "authority_created": False,
            }
        )
        refs_by_source_set[source_ids] = universe_ref
    return (
        MappingProxyType(definitions),
        MappingProxyType(refs_by_source_set),
    )


def build_parameter_scope_projection(
    *,
    master_plan_text: str,
    identity_map: AgentIdentityCompatibilityMapV1,
) -> tuple[AgentParameterScopeViewV1, ...]:
    """Preserve exact upstream lineage and orthogonal E capability state."""

    master_rows = canonical_master_parameter_rows(master_plan_text)
    canonical_identities = canonical_parameter_identity_registry(
        master_plan_text
    )
    resolve_st12e_value_policy_refs(canonical_identities)
    upstream_universes, universe_refs = (
        build_upstream_source_universe_registry(master_rows)
    )
    del upstream_universes
    _, st12e_universe_refs = build_st12e_certified_source_universe_registry()
    canonical_source_ids = {
        source_id
        for _, _, source_ids in master_rows
        for source_id in source_ids
    }
    if set(identity_map.bindings) != canonical_source_ids:
        raise AuthorityDeniedError(
            ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
            "identity compatibility map does not cover the exact source universe",
        )

    output: list[AgentParameterScopeViewV1] = []
    for parameter_id, symbol, upstream_source_ids in master_rows:
        lineage_bindings = tuple(
            identity_map.describe_for_lineage(source_id)
            for source_id in upstream_source_ids
        )
        mapped_bindings = tuple(
            binding
            for binding in lineage_bindings
            if binding.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
        )
        unmapped_bindings = tuple(
            binding
            for binding in lineage_bindings
            if binding.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED
        )
        mapped_refs = tuple(
            f"ST12E_IDENTITY::{binding.source_agent_id}"
            for binding in mapped_bindings
        ) or (EXPLICIT_ABSENCE,)
        unmapped_refs = tuple(
            f"ST12E_IDENTITY::{binding.source_agent_id}"
            for binding in unmapped_bindings
        ) or (EXPLICIT_ABSENCE,)
        mapped_principals = tuple(
            dict.fromkeys(
                principal
                for binding in mapped_bindings
                for principal in binding.current_principal_refs
            )
        )
        principal_refs_or_gap = (
            *mapped_principals,
            *(
                f"IDENTITY_GAP::{binding.source_agent_id}"
                for binding in unmapped_bindings
            ),
        ) or (EXPLICIT_ABSENCE,)
        e_binding = ST12E_PARAMETER_CAPABILITY_BINDINGS.get(parameter_id)
        if e_binding is None:
            st12e_state = ST12E_BINDING_OUTSIDE_SCOPE
            st12e_capability_ref = EXPLICIT_ABSENCE
            st12e_universe_ref = EXPLICIT_ABSENCE
            st12e_principals = (EXPLICIT_ABSENCE,)
            terminal_route = "ST12E_CAPABILITY_BINDING_NOT_APPLICABLE"
        else:
            certified_bindings = tuple(
                identity_map.require_current_authority_mapping(source_id)
                for source_id in e_binding.certified_source_agent_ids
            )
            st12e_principals = tuple(
                dict.fromkeys(
                    principal
                    for binding in certified_bindings
                    for principal in binding.current_principal_refs
                )
            )
            st12e_state = ST12E_BINDING_EXACT
            st12e_capability_ref = e_binding.capability_policy_ref
            st12e_universe_ref = st12e_universe_refs[
                e_binding.certified_source_agent_ids
            ]
            terminal_route = "NO_EFFECT_QKU_REQUEST_OR_TYPED_DENIAL"

        upstream_universe_ref = universe_refs[upstream_source_ids]
        output.append(
            AgentParameterScopeViewV1(
                parameter_id=parameter_id,
                parameter_symbol=symbol,
                upstream_source_universe_ref=upstream_universe_ref,
                upstream_identity_mapping_state=(
                    UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
                    if unmapped_bindings
                    else UPSTREAM_IDENTITY_FULLY_MAPPED
                ),
                mapped_compatibility_refs=mapped_refs,
                unmapped_compatibility_refs=unmapped_refs,
                current_principal_refs_or_exact_gap=principal_refs_or_gap,
                value_policy_ref=(
                    "QKUComputationControlPlaneV1."
                    f"ComputationParameterPolicyV1::{parameter_id}"
                ),
                st12e_binding_state=st12e_state,
                st12e_capability_binding_ref_or_explicit_absence=(
                    st12e_capability_ref
                ),
                st12e_certified_source_universe_ref_or_explicit_absence=(
                    st12e_universe_ref
                ),
                st12e_current_principal_refs_or_explicit_absence=(
                    st12e_principals
                ),
                lifecycle_state="CURRENT_EXACT_UPSTREAM_LINEAGE",
                timing_state="BUILD_TIME_FROZEN_TYPED_SNAPSHOT",
                downstream_consumer_refs=(
                    "AgentCapabilityResolverV1",
                    "QKUComputationControlPlaneV1",
                ),
                validator_ref=CENTRAL_VALIDATOR_REF,
                terminal_route=terminal_route,
                semantic_owner="ComputationParameterPolicyV1",
                implementation_owner="AgentCapabilityResolverV1",
                producer_ref=(
                    "QKUComputationControlPlaneV1."
                    f"ComputationParameterPolicyV1::{parameter_id}"
                ),
                upstream_artifact_refs=(
                    MASTER_PARAMETER_SOURCE_REF,
                    CURRENT_ROSTER_REF,
                    CURRENT_DUTY_REF,
                    f"{AGENT_ORCH_PREFIX}/perm_scope.jsonl",
                ),
                upstream_row_or_value_refs=(
                    parameter_id,
                    upstream_universe_ref,
                ),
                current_principal_duty_policy_refs=tuple(
                    dict.fromkeys(
                        (
                            *mapped_refs,
                            *unmapped_refs,
                            *st12e_principals,
                            f"{AGENT_ORCH_PREFIX}/duty_map.jsonl",
                            st12e_capability_ref,
                        )
                    )
                ),
            )
        )
    return tuple(output)


def _decision_id(
    *, request_id: str, principal_id: str, operation_id: str, idempotency_key: str
) -> str:
    safe = re.sub(
        r"[^A-Za-z0-9_.:-]+",
        "_",
        f"{principal_id}:{operation_id}:{idempotency_key}",
    )
    return f"ST12E_DECISION::{safe[:240]}"


def _normalized_role_key(value: object) -> str:
    key = re.sub(r"[^A-Z0-9]+", "", str(value).upper())
    return key.removesuffix("AGENT")


class AgentCapabilityPolicyStoreV1:
    """One immutable indexed E snapshot; request-time file reads are forbidden."""

    def __init__(self, snapshot: AgentCapabilityPolicySnapshotV1) -> None:
        if not isinstance(snapshot, AgentCapabilityPolicySnapshotV1):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_MISSING,
                "a typed frozen capability snapshot is required",
            )
        self.snapshot = snapshot

    @classmethod
    def from_generated(
        cls, repo_root: str | Path
    ) -> "AgentCapabilityPolicyStoreV1":
        root = Path(repo_root).resolve()
        artifact_dir = (
            root
            / "docs/master_plan/generated/qku_control_plane/agent_capability"
        )
        manifest = json.loads(
            (artifact_dir / "manifest.json").read_text(encoding="utf-8")
        )
        policy_rows = tuple(
            json.loads(line)
            for line in (artifact_dir / "policy.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
        scope_payloads = tuple(
            json.loads(line)
            for line in (artifact_dir / "parameter_scope.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
        master_plan_text = (root / MASTER_PARAMETER_SOURCE_REF).read_text(
            encoding="utf-8"
        )
        master_rows = canonical_master_parameter_rows(master_plan_text)
        canonical_source_ids = canonical_source_agent_ids(master_plan_text)
        canonical_role_labels = canonical_source_role_labels(master_plan_text)
        canonical_parameter_identities = canonical_parameter_identity_registry(
            master_plan_text
        )
        value_policy_resolution = resolve_st12e_value_policies(
            canonical_parameter_identities
        )
        upstream_universes, _ = build_upstream_source_universe_registry(
            master_rows
        )
        st12e_universes, st12e_universe_refs = (
            build_st12e_certified_source_universe_registry()
        )

        orch_snapshot = AgentOrchService(repo_root=root).load_policy_snapshot()
        identity_map = build_identity_compatibility_map(
            orch_snapshot,
            source_agent_ids=canonical_source_ids,
            source_role_labels=canonical_role_labels,
        )
        expected_scope_rows = build_parameter_scope_projection(
            master_plan_text=master_plan_text,
            identity_map=identity_map,
        )
        expected_scope_payloads = {
            row.parameter_id: _jsonable(
                {
                    name: getattr(row, name)
                    for name in row.__dataclass_fields__
                }
            )
            for row in expected_scope_rows
        }
        if {
            str(row.get("parameter_id") or ""): row
            for row in scope_payloads
        } != expected_scope_payloads:
            raise AuthorityDeniedError(
                ReasonCode.PARAMETER_SCOPE_MISMATCH,
                "generated parameter lineage differs from the canonical source rows",
            )
        scope = {
            row.parameter_id: row for row in expected_scope_rows
        }

        control_rows = tuple(
            row for row in policy_rows if row.get("row_type") == "CONTROL"
        )
        binding_rows = tuple(
            row
            for row in policy_rows
            if row.get("row_type") == "PARAMETER_CAPABILITY_BINDING"
        )
        identity_rows = tuple(
            row
            for row in policy_rows
            if row.get("row_type") == "IDENTITY_COMPATIBILITY"
        )
        generated_identity_rows = {
            str(row.get("source_agent_id") or ""): row
            for row in identity_rows
        }
        identity_field_names = tuple(AgentPrincipalBindingV1.__dataclass_fields__)
        identity_rows_match = set(generated_identity_rows) == set(
            identity_map.bindings
        ) and all(
            all(
                generated_identity_rows[source_id].get(name)
                == _jsonable(getattr(binding, name))
                for name in identity_field_names
            )
            for source_id, binding in identity_map.bindings.items()
        )

        forbidden_value_body_fields = {
            "raw",
            "day1_seed_or_resolution_rule",
            "reference_range_or_structural_constraint",
            "bounded_search_space_or_fit_constraint",
            "unit_or_basis",
            "precision_and_rounding_policy",
            "runtime_resolution_procedure",
            "fallback_behavior_when_value_unavailable",
            "value_source_class",
            "source_state_refs",
        }
        generated_binding_rows = {
            str(row.get("parameter_id") or ""): row
            for row in binding_rows
        }
        bindings_are_reference_only = set(generated_binding_rows) == set(
            ST12E_PARAMETER_CAPABILITY_BINDINGS
        ) and all(
            not forbidden_value_body_fields.intersection(row)
            and row.get("parameter_symbol") == binding.parameter_symbol
            and row.get("certified_source_universe_ref")
            == st12e_universe_refs[binding.certified_source_agent_ids]
            and row.get("value_policy_ref") == binding.value_policy_ref
            and row.get("capability_policy_ref")
            == binding.capability_policy_ref
            and row.get("st12e_binding_state") == ST12E_BINDING_EXACT
            for parameter_id, binding in ST12E_PARAMETER_CAPABILITY_BINDINGS.items()
            for row in (generated_binding_rows.get(parameter_id, {}),)
        )

        task_rows = {
            str(row["task_id"]): row
            for row in orch_snapshot.task_envelope_rows
        }
        receipt_refs = {
            str(row["candidate_id"]): str(row["row_id"])
            for row in orch_snapshot.decision_receipt_rows
        }
        receipt_rows = {
            str(row["row_id"]): row
            for row in orch_snapshot.decision_receipt_rows
        }
        receipt_rows_are_no_effect = all(
            row.get("object_type") == "AgentDecisionReceiptV1"
            and row.get("object_version") == orch_snapshot.manifest_version
            and row.get("runtime_side_effect_allowed") is False
            and row.get("source_truth_created") is False
            and row.get("live_execution_created") is False
            and row.get("order_submission_created") is False
            and row.get("fake_receipt_created") is False
            for row in orch_snapshot.decision_receipt_rows
        )

        owner_action_ids = current_owner_action_ids()
        policy_row_ids = tuple(str(row.get("row_id") or "") for row in policy_rows)
        reused_math = tuple(
            manifest.get("reused_math_oracle_vector_refs") or ()
        )
        derived_counts = {
            "closure_controls": len(control_rows),
            "repository_dispositions": len(
                tuple(manifest.get("repository_disposition_ids") or ())
            ),
            "parameter_bindings": len(binding_rows),
            "math_specifications": len(reused_math),
            "independent_oracle_specifications": len(reused_math),
            "golden_vectors_and_invariants": len(reused_math),
            "semantic_test_rows": len(
                tuple(manifest.get("semantic_test_ids") or ())
            ),
            "validation_commands": len(
                tuple(manifest.get("validation_commands") or ())
            ),
            "parameter_source_universe": len(scope),
        }
        expected_universe_payload = {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
            }
            for universe_ref, specification in upstream_universes.items()
        }
        expected_st12e_universe_payload = {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
                "authority_created": False,
            }
            for universe_ref, specification in st12e_universes.items()
        }
        exact_mappings = sum(
            binding.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
            for binding in identity_map.bindings.values()
        )
        unmapped_mappings = len(identity_map.bindings) - exact_mappings
        fully_mapped_scope = sum(
            row.upstream_identity_mapping_state
            == UPSTREAM_IDENTITY_FULLY_MAPPED
            for row in scope.values()
        )
        crosswalk_required_scope = len(scope) - fully_mapped_scope
        exact_e_scope = tuple(
            row
            for row in scope.values()
            if row.st12e_binding_state == ST12E_BINDING_EXACT
        )
        outside_e_scope = tuple(
            row
            for row in scope.values()
            if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
        )
        e_scope_with_gap = sum(
            row.upstream_identity_mapping_state
            == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
            for row in exact_e_scope
        )
        required_lineage_fields = {
            "semantic_owner",
            "implementation_owner",
            "producer_ref",
            "upstream_artifact_refs",
            "upstream_row_or_value_refs",
            "current_principal_duty_policy_refs",
            "downstream_consumer_refs",
            "lifecycle_state",
            "timing_or_snapshot_state",
            "activation_state",
            "terminal_route",
            "validator_ref",
        }
        policy_rows_are_closed = all(
            required_lineage_fields <= set(row)
            and row.get("activation_state") == ACTIVATION_STATE
            for row in policy_rows
        )
        authority_flag_view = {
            name: getattr(TRANCHE_A_AUTHORITY, name)
            for name in TRANCHE_A_AUTHORITY.__dataclass_fields__
        }
        manifest_counts_match = all(
            manifest.get(field) == value
            for field, value in {
                "source_identity_row_count": len(identity_map.bindings),
                "exact_mapping_count": exact_mappings,
                "unmapped_mapping_count": unmapped_mappings,
                "parameter_scope_row_count": len(scope),
                "exact_upstream_source_universe_count": len(upstream_universes),
                "exact_upstream_source_agent_id_count": len(canonical_source_ids),
                "fully_mapped_upstream_row_count": fully_mapped_scope,
                "crosswalk_required_upstream_row_count": crosswalk_required_scope,
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
                "appendix_e_policy_spec_count": len(
                    ST12E_PARAMETER_POLICY_SPECS
                ),
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
                "value_policy_ref_resolution_count": len(binding_rows),
                "duplicated_value_body_count": 0,
                "capability_binding_value_body_count": 0,
                "generated_policy_value_body_count": 0,
                "implicit_admission_bypass_count": 0,
                "production_default_admission_profile_count": 0,
            }.items()
        )
        if (
            manifest.get("policy_version") != POLICY_VERSION
            or manifest.get("activation_state") != ACTIVATION_STATE
            or manifest.get("runtime_effect_authorized") is not False
            or manifest.get("registry_version") != orch_snapshot.manifest_version
            or tuple(manifest.get("owner_action_ids", ())) != owner_action_ids
            or manifest.get("policy_row_count") != len(policy_rows)
            or len(policy_row_ids) != len(set(policy_row_ids))
            or not all(policy_row_ids)
            or manifest.get("counts") != derived_counts
            or len(control_rows) + len(binding_rows) + len(identity_rows)
            != len(policy_rows)
            or not identity_rows_match
            or not bindings_are_reference_only
            or not manifest_counts_match
            or manifest.get("exact_upstream_source_universes")
            != expected_universe_payload
            or manifest.get("st12e_certified_source_universes")
            != expected_st12e_universe_payload
            or "parameter_scope_distribution_is_aggregate_only" in manifest
            or len(task_rows) != len(orch_snapshot.task_envelope_rows)
            or len(receipt_refs) != len(orch_snapshot.decision_receipt_rows)
            or len(receipt_rows) != len(orch_snapshot.decision_receipt_rows)
            or not receipt_rows_are_no_effect
            or not policy_rows_are_closed
            or manifest.get("no_effect_authority_flags") != authority_flag_view
            or manifest.get("no_effect_authority_closed") is not True
            or manifest.get("qku_formula_mutation_authorized") is not False
            or manifest.get(
                "trade_plan_candidate_is_only_mutable_optimization_object"
            )
            is not True
            or manifest.get("llm_inference_allowed") is not False
            or manifest.get("quantum_mapping_or_execution_allowed") is not False
            or manifest.get("raw_jsonl_request_time_scan_allowed") is not False
            or tuple(manifest.get("implemented_operation_ids") or ())
            != IMPLEMENTED_OPERATION_IDS
            or tuple(manifest.get("held_operation_ids") or ())
            != HELD_OPERATION_IDS
        ):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_STALE,
                "generated policy lineage is stale or effect-bearing",
            )
        snapshot = AgentCapabilityPolicySnapshotV1(
            policy_version=POLICY_VERSION,
            registry_version=orch_snapshot.manifest_version,
            identity_map=identity_map,
            policy_rows=MappingProxyType(
                {str(row["row_id"]): _freeze(row) for row in policy_rows}
            ),
            parameter_scope_rows=MappingProxyType(scope),
            agent_orch_task_rows=MappingProxyType(task_rows),
            agent_orch_receipt_refs_by_candidate_id=MappingProxyType(
                receipt_refs
            ),
            agent_orch_receipt_rows=MappingProxyType(receipt_rows),
            owner_action_ids=owner_action_ids,
            no_effect_profile_ref=NO_EFFECT_PROFILE_REF,
        )
        return cls(snapshot)


class AgentCapabilityResolverV1:
    """Default-deny E admission; eligibility never creates authority."""

    def __init__(
        self,
        policy_store: AgentCapabilityPolicyStoreV1,
        capability_bundles: Mapping[str, AgentCapabilityBundleV1],
    ) -> None:
        if not isinstance(policy_store, AgentCapabilityPolicyStoreV1):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_MISSING,
                "one central policy store is required",
            )
        if not isinstance(capability_bundles, Mapping) or any(
            not isinstance(bundle_id, str)
            or not bundle_id
            or not isinstance(bundle, AgentCapabilityBundleV1)
            or bundle_id != bundle.bundle_id
            for bundle_id, bundle in capability_bundles.items()
        ):
            raise AuthorityDeniedError(
                ReasonCode.TASK_ENVELOPE_MISSING,
                "capability bundles must be exact typed bundle-id mappings",
            )
        self.policy_store = policy_store
        self._bundles = MappingProxyType(dict(capability_bundles))
        self._idempotency: dict[
            tuple[str, str], tuple[str, AgentCapabilityDecisionV1]
        ] = {}
        self._request_claims: dict[
            tuple[str, str], tuple[str, str]
        ] = {}
        self.last_decision: AgentCapabilityDecisionV1 | None = None

    def _agent_orch_receipt_ref(self, task_id: str) -> str:
        task_row = self.policy_store.snapshot.agent_orch_task_rows.get(task_id)
        if task_row is None:
            return f"AGENT_ORCH1_RECEIPT_GAP::{task_id}"
        candidate_id = str(task_row.get("candidate_id") or "")
        return self.policy_store.snapshot.agent_orch_receipt_refs_by_candidate_id.get(
            candidate_id,
            f"AGENT_ORCH1_RECEIPT_GAP::{task_id}",
        )

    def _decision(
        self,
        *,
        bundle: AgentCapabilityBundleV1,
        request_id: str,
        operation_id: str,
        state: AgentCapabilityDecisionStateV1,
        reasons: tuple[ReasonCode, ...],
        scope_refs: tuple[str, ...],
        terminal_route: str,
    ) -> AgentCapabilityDecisionV1:
        envelope = bundle.task_envelope
        agent_orch_receipt_ref = self._agent_orch_receipt_ref(
            str(envelope["task_id"])
        )
        st12c_refs = (
            f"OperationRequestEnvelopeV1.request_id={request_id}",
            (
                "OperationRequestEnvelopeV1.idempotency_key="
                f"{envelope['idempotency_key']}"
            ),
        )
        disagreement_state = str(
            envelope.get("disagreement_state", "NONE_DECLARED")
        )
        peer_receipt_ref = envelope.get("peer_challenge_receipt_ref")
        peer_reasoning_ref = envelope.get("peer_reasoning_chain_ref")
        peer_evidence = tuple(
            value
            for value in (peer_receipt_ref, peer_reasoning_ref)
            if isinstance(value, str) and value
        )
        peer_required = envelope["peer_challenge_requirement"] is True
        peer_missing = ReasonCode.PEER_CHALLENGE_REQUIRED in reasons
        decision = AgentCapabilityDecisionV1(
            decision_id=_decision_id(
                request_id=request_id,
                principal_id=bundle.principal_id,
                operation_id=operation_id,
                idempotency_key=str(envelope["idempotency_key"]),
            ),
            request_id=request_id,
            task_id=str(envelope["task_id"]),
            principal_id=bundle.principal_id,
            current_agent_id=bundle.current_agent_id,
            source_agent_refs=bundle.certified_source_agent_ids,
            operation_id=operation_id,
            policy_version=POLICY_VERSION,
            decision_state=state,
            reason_codes=reasons,
            scope_refs=scope_refs,
            idempotency_key=str(envelope["idempotency_key"]),
            retry_disposition="BOUNDED_BY_TASK_ENVELOPE_NO_EFFECT_ONLY",
            peer_sod_disposition=(
                "PEER_CHALLENGE_REQUIRED_DENY"
                if peer_missing
                else (
                    "PEER_CHALLENGE_AND_SOD_ENFORCED"
                    if peer_required
                    else "SOD_ENFORCED_PEER_NOT_REQUIRED"
                )
            ),
            safety_state_disposition=bundle.boundary_state.state.value,
            terminal_route=terminal_route,
            agent_orch_receipt_ref=agent_orch_receipt_ref,
            st12c_causation_correlation_refs=st12c_refs,
            evidence_refs=tuple(
                dict.fromkeys(
                    (
                        agent_orch_receipt_ref,
                        str(envelope["task_id"]),
                        *st12c_refs,
                        *peer_evidence,
                    )
                )
            ),
            alternative_route_refs=tuple(
                dict.fromkeys(
                    (
                        "DENY_TASK",
                        str(envelope["owner_escalation_route"]),
                        str(envelope["quarantine_route"]),
                        "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION",
                    )
                )
            ),
            disagreement_state=disagreement_state,
            confidence_state=bundle.trust_state,
            limitation_codes=tuple(
                dict.fromkeys(
                    (
                        "NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_RUNTIME_EFFECT",
                        "QKU_AND_FORMULA_IMMUTABLE",
                        "TRADEPLAN_CANDIDATE_ONLY_MUTABLE_OPTIMIZATION_OBJECT",
                        *(reason.value for reason in reasons),
                    )
                )
            ),
        )
        self.last_decision = decision
        return decision

    def resolve(
        self,
        *,
        request_id: str,
        principal_id: str,
        capability_bundle_id: str,
        operation_id: str,
        context_ref: str,
        requested_scope_refs: Mapping[str, tuple[str, ...]] | None = None,
        requested_parameter_ids: tuple[str, ...] = (),
        request_idempotency_key: str | None = None,
    ) -> AgentCapabilityDecisionV1:
        try:
            bundle = self._bundles[capability_bundle_id]
        except KeyError:
            safe_request_id = request_id or "REQUEST_ID_UNRESOLVED"
            safe_principal_id = principal_id or "PRINCIPAL_UNRESOLVED"
            safe_operation_id = operation_id or "OPERATION_UNRESOLVED"
            safe_idempotency_key = (
                request_idempotency_key or "IDEMPOTENCY_KEY_UNRESOLVED"
            )
            st12c_refs = (
                f"OperationRequestEnvelopeV1.request_id={safe_request_id}",
                (
                    "OperationRequestEnvelopeV1.idempotency_key="
                    f"{safe_idempotency_key}"
                ),
            )
            decision = AgentCapabilityDecisionV1(
                decision_id=_decision_id(
                    request_id=safe_request_id,
                    principal_id=safe_principal_id,
                    operation_id=safe_operation_id,
                    idempotency_key=safe_idempotency_key,
                ),
                request_id=safe_request_id,
                task_id="TASK_ENVELOPE_MISSING",
                principal_id=safe_principal_id,
                current_agent_id="CURRENT_AGENT_UNRESOLVED",
                source_agent_refs=("SOURCE_AGENT_ID_UNMAPPED",),
                operation_id=safe_operation_id,
                policy_version=POLICY_VERSION,
                decision_state=AgentCapabilityDecisionStateV1.DENIED,
                reason_codes=(ReasonCode.TASK_ENVELOPE_MISSING,),
                scope_refs=(),
                idempotency_key=safe_idempotency_key,
                retry_disposition="RETRY_FORBIDDEN_WITHOUT_TASK_ENVELOPE",
                peer_sod_disposition="UNRESOLVED_DENY",
                safety_state_disposition=AgentSafetyStateV1.MISSING.value,
                terminal_route="DENY_TASK",
                agent_orch_receipt_ref=(
                    "AGENT_ORCH1_RECEIPT_GAP::TASK_ENVELOPE_MISSING"
                ),
                st12c_causation_correlation_refs=st12c_refs,
                evidence_refs=(
                    "AgentCapabilityPolicyStoreV1::NO_BUNDLE_MATCH",
                    *st12c_refs,
                ),
                alternative_route_refs=("DENY_TASK", "OWNER_REVIEW_REQUIRED"),
                disagreement_state="UNRESOLVED_DENY",
                confidence_state="INSUFFICIENT_MISSING_TASK_ENVELOPE",
                limitation_codes=(
                    "NO_EFFECT_ONLY",
                    "QKU_AND_FORMULA_IMMUTABLE",
                    ReasonCode.TASK_ENVELOPE_MISSING.value,
                ),
            )
            self.last_decision = decision
            return decision
        envelope = bundle.task_envelope
        reasons: list[ReasonCode] = []
        if not request_id or not principal_id or not operation_id or not context_ref:
            reasons.append(ReasonCode.TASK_ENVELOPE_MISSING)
        if any(
            field in envelope and type(envelope[field]) is not bool
            for field in OPTIONAL_BOOLEAN_ENVELOPE_FIELDS
        ):
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        if not str(envelope["candidate_scope_ref"]).startswith(
            "TradePlanCandidateV1::"
        ):
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        if str(envelope["mode_eligibility_ref_without_activation"]).upper() in (
            FORBIDDEN_MODE_ELIGIBILITY_STATES
        ):
            reasons.append(ReasonCode.MODE_ACTIVATION_FORBIDDEN)
        if (
            principal_id != bundle.principal_id
            or principal_id != envelope["principal_id"]
        ):
            reasons.append(ReasonCode.PRINCIPAL_UNKNOWN)
        if bundle.current_agent_id != envelope["current_agent_id"]:
            reasons.append(ReasonCode.PRINCIPAL_AMBIGUOUS)
        resolved_sources: list[AgentPrincipalBindingV1] = []
        for source_id in bundle.certified_source_agent_ids:
            try:
                resolved_sources.append(
                    self.policy_store.snapshot.identity_map.resolve(source_id)
                )
            except AuthorityDeniedError:
                reasons.append(ReasonCode.SOURCE_AGENT_ID_UNMAPPED)
        if resolved_sources and not any(
            bundle.current_agent_id in row.current_principal_refs
            for row in resolved_sources
        ):
            reasons.append(ReasonCode.DUTY_MISMATCH)
        if resolved_sources and not any(
            bundle.role_ref in row.current_role_refs
            for row in resolved_sources
        ):
            reasons.append(ReasonCode.ROLE_MISMATCH)
        if resolved_sources and not any(
            bundle.duty_ref in row.current_duty_refs
            for row in resolved_sources
        ):
            reasons.append(ReasonCode.DUTY_MISMATCH)
        if resolved_sources and not any(
            bundle.current_agent_id in row.current_principal_refs
            and bundle.role_ref in row.current_role_refs
            and bundle.duty_ref in row.current_duty_refs
            and set(bundle.permission_scope) <= set(row.intersection_scope)
            for row in resolved_sources
        ):
            reasons.append(
                ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY
            )
        if envelope["role_ref"] != bundle.role_ref:
            reasons.append(ReasonCode.ROLE_MISMATCH)
        if envelope["duty_ref"] != bundle.duty_ref:
            reasons.append(ReasonCode.DUTY_MISMATCH)
        if operation_id not in IMPLEMENTED_OPERATION_IDS:
            reasons.append(
                ReasonCode.REPLAY_PAPER_EFFECT_FORBIDDEN
                if operation_id in HELD_OPERATION_IDS
                else ReasonCode.OPERATION_NOT_ALLOWED
            )
        if envelope["operation_id"] != operation_id:
            reasons.append(ReasonCode.OPERATION_NOT_ALLOWED)
        if envelope["context_ref"] != context_ref:
            reasons.append(ReasonCode.CONTEXT_SCOPE_MISMATCH)
        agent_orch_task = self.policy_store.snapshot.agent_orch_task_rows.get(
            str(envelope["task_id"])
        )
        if agent_orch_task is None:
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        else:
            if (
                agent_orch_task.get("object_type") != "AgentTaskEnvelopeV1"
                or agent_orch_task.get("object_version")
                != self.policy_store.snapshot.registry_version
                or agent_orch_task.get("runtime_side_effect_allowed") is not False
            ):
                reasons.append(ReasonCode.TASK_ENVELOPE_STALE)
            if not set(bundle.permission_scope) <= set(
                tuple(agent_orch_task.get("allowed_actions", ()))
            ):
                reasons.append(
                    ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY
                )
            if not set(FORBIDDEN_AUTHORITY_ACTIONS) <= set(
                tuple(agent_orch_task.get("forbidden_actions", ()))
            ):
                reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
            if envelope["retry_policy_ref"] != agent_orch_task.get(
                "retry_policy_ref_or_gap"
            ):
                reasons.append(ReasonCode.RETRY_NOT_ALLOWED)
            candidate_id = str(agent_orch_task.get("candidate_id") or "")
            if candidate_id not in (
                self.policy_store.snapshot.agent_orch_receipt_refs_by_candidate_id
            ):
                reasons.append(ReasonCode.OWNER_REVIEW_REQUIRED)
        if (
            tuple(envelope["certified_source_agent_ids"])
            != bundle.certified_source_agent_ids
        ):
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        requested_scope_refs = requested_scope_refs or {}
        if not isinstance(requested_scope_refs, Mapping):
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
            requested_scope_refs = {}
        for field, reason in SCOPE_REASON_BY_FIELD.items():
            requested = requested_scope_refs.get(field, ())
            if (
                not isinstance(requested, tuple)
                or any(
                    not isinstance(value, str) or not value
                    for value in requested
                )
                or not set(requested) <= set(tuple(envelope[field]))
            ):
                reasons.append(reason)
        if "QKUComputationControlPlaneV1" not in tuple(
            envelope["tool_scope_refs"]
        ):
            reasons.append(ReasonCode.TOOL_SCOPE_MISMATCH)
        if not set(tuple(envelope["tool_scope_refs"])) <= set(
            ALLOWED_TOOL_SCOPE_REFS
        ):
            reasons.append(ReasonCode.LLM_TOOL_NOT_ALLOWED)
        if not set(tuple(envelope["action_scope_refs"])) <= set(
            self.policy_store.snapshot.owner_action_ids
        ):
            reasons.append(ReasonCode.ACTION_SCOPE_MISMATCH)
        if not isinstance(requested_parameter_ids, tuple) or any(
            not isinstance(parameter_id, str) or not parameter_id
            for parameter_id in requested_parameter_ids
        ):
            reasons.append(ReasonCode.PARAMETER_SCOPE_MISMATCH)
            requested_parameter_ids = ()
        for parameter_id in requested_parameter_ids:
            parameter_scope = (
                self.policy_store.snapshot.parameter_scope_rows.get(
                    parameter_id
                )
            )
            capability_binding = ST12E_PARAMETER_CAPABILITY_BINDINGS.get(
                parameter_id
            )
            if (
                parameter_scope is None
                or capability_binding is None
                or parameter_scope.st12e_binding_state
                != ST12E_BINDING_EXACT
                or not set(bundle.certified_source_agent_ids)
                <= set(capability_binding.certified_source_agent_ids)
                or bundle.current_agent_id
                not in parameter_scope.st12e_current_principal_refs_or_explicit_absence
            ):
                reasons.append(ReasonCode.PARAMETER_SCOPE_MISMATCH)
        if envelope["policy_version"] != POLICY_VERSION:
            reasons.append(ReasonCode.TASK_ENVELOPE_STALE)
        if envelope["registry_version"] != self.policy_store.snapshot.registry_version:
            reasons.append(ReasonCode.TASK_ENVELOPE_STALE)
        if self.policy_store.snapshot.registry_version not in tuple(
            envelope["snapshot_version_requirements"]
        ):
            reasons.append(ReasonCode.TASK_ENVELOPE_STALE)
        for formula_ref in tuple(envelope["formula_scope_refs"]):
            if formula_ref.startswith("MATH-") and not any(
                implementation_ref.startswith(f"{formula_ref}::")
                for implementation_ref in tuple(
                    envelope["implementation_version_requirements"]
                )
            ):
                reasons.append(ReasonCode.FORMULA_SCOPE_MISMATCH)
        if envelope["no_effect_profile_ref"] != NO_EFFECT_PROFILE_REF:
            reasons.append(ReasonCode.SELF_PROMOTION_FORBIDDEN)
        if not set(bundle.permission_scope) <= set(ALLOWED_ADVISORY_ACTIONS):
            reasons.append(
                ReasonCode.SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY
            )
        if set(bundle.permission_scope) & set(FORBIDDEN_AUTHORITY_ACTIONS):
            reasons.append(ReasonCode.SELF_PROMOTION_FORBIDDEN)
        if envelope["segregation_of_duties_requirement"] is not True:
            reasons.append(ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION)
        if envelope["peer_challenge_requirement"] is True:
            peer_principal_id = envelope.get("peer_challenge_principal_id")
            peer_duty_ref = envelope.get("peer_challenge_duty_ref")
            peer_receipt_ref = envelope.get("peer_challenge_receipt_ref")
            peer_reasoning_ref = envelope.get("peer_reasoning_chain_ref")
            independent_peer = any(
                isinstance(peer_principal_id, str)
                and peer_principal_id in binding.current_principal_refs
                and isinstance(peer_duty_ref, str)
                and peer_duty_ref in binding.current_duty_refs
                for binding in (
                    self.policy_store.snapshot.identity_map.bindings.values()
                )
            )
            peer_receipt = (
                self.policy_store.snapshot.agent_orch_receipt_rows.get(
                    peer_receipt_ref
                )
                if isinstance(peer_receipt_ref, str)
                else None
            )
            peer_receipt_role_keys = {
                _normalized_role_key(value)
                for field in ("required_roles", "responsible_roles")
                for value in tuple(
                    peer_receipt.get(field, ())
                    if peer_receipt is not None
                    else ()
                )
            }
            if (
                envelope.get("peer_challenge_satisfied") is not True
                or not independent_peer
                or peer_principal_id == bundle.current_agent_id
                or peer_receipt is None
                or _normalized_role_key(peer_duty_ref)
                not in peer_receipt_role_keys
                or not isinstance(peer_reasoning_ref, str)
                or not peer_reasoning_ref
            ):
                reasons.append(ReasonCode.PEER_CHALLENGE_REQUIRED)
        if envelope.get("self_review_requested") is True:
            reasons.append(ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION)
        retry_count = envelope.get("retry_count", 0)
        max_retry_count = (
            agent_orch_task.get("max_retry_count")
            if agent_orch_task is not None
            else None
        )
        if (
            isinstance(retry_count, bool)
            or not isinstance(retry_count, int)
            or retry_count < 0
            or isinstance(max_retry_count, bool)
            or not isinstance(max_retry_count, int)
            or max_retry_count < 0
            or retry_count > max_retry_count
        ):
            reasons.append(ReasonCode.RETRY_NOT_ALLOWED)
        reoptimization_variable_ids: tuple[str, ...] = ()
        raw_reoptimization_variables = envelope.get(
            "reoptimization_variable_ids", EXPLICIT_ABSENCE
        )
        if envelope.get("terminal_no_trade") is True:
            if (
                not isinstance(raw_reoptimization_variables, tuple)
                or not raw_reoptimization_variables
                or any(
                    not isinstance(value, str) or not value
                    for value in raw_reoptimization_variables
                )
                or len(raw_reoptimization_variables)
                != len(set(raw_reoptimization_variables))
                or not set(raw_reoptimization_variables)
                <= set(NO_TRADE_REOPTIMIZATION_VARIABLE_IDS)
            ):
                reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
            else:
                reoptimization_variable_ids = raw_reoptimization_variables
        elif raw_reoptimization_variables != EXPLICIT_ABSENCE:
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        decision_scope_refs = tuple(
            dict.fromkeys(
                (
                    f"operation_id={operation_id or 'OPERATION_UNRESOLVED'}",
                    f"context_ref={context_ref or 'CONTEXT_UNRESOLVED'}",
                    *(
                        f"{field}={value}"
                        for field in SCOPE_REASON_BY_FIELD
                        for value in tuple(requested_scope_refs.get(field, ()))
                        if isinstance(value, str) and value
                    ),
                    *(
                        f"parameter_id={parameter_id}"
                        for parameter_id in requested_parameter_ids
                    ),
                    *(
                        f"reoptimization_variable_id={variable_id}"
                        for variable_id in reoptimization_variable_ids
                    ),
                )
            )
        )
        if bundle.quarantined:
            return self._decision(
                bundle=bundle,
                request_id=request_id,
                operation_id=operation_id,
                state=AgentCapabilityDecisionStateV1.QUARANTINED,
                reasons=(ReasonCode.QUARANTINED,),
                scope_refs=decision_scope_refs,
                terminal_route=str(envelope["quarantine_route"]),
            )
        if bundle.trust_state != "SUFFICIENT_FOR_NO_EFFECT_REVIEW":
            reasons.append(ReasonCode.TRUST_STATE_INSUFFICIENT)
        boundary_reason = {
            AgentSafetyStateV1.MISSING: ReasonCode.SAFETY_STATE_MISSING,
            AgentSafetyStateV1.STALE: ReasonCode.SAFETY_STATE_STALE,
            AgentSafetyStateV1.CONFLICT: ReasonCode.SAFETY_STATE_CONFLICT,
        }.get(bundle.boundary_state.state)
        safety_non_material = (
            bundle.boundary_state.safety_state_non_material
            and operation_id in SAFETY_NON_MATERIAL_OPERATION_IDS
        )
        if boundary_reason and not safety_non_material:
            reasons.append(boundary_reason)
        if bundle.boundary_state.state is AgentSafetyStateV1.GREEN:
            try:
                observed_at = datetime.fromisoformat(
                    bundle.boundary_state.observed_at.replace("Z", "+00:00")
                )
                valid_until = datetime.fromisoformat(
                    bundle.boundary_state.valid_until.replace("Z", "+00:00")
                )
                now = datetime.now(timezone.utc)
                if (
                    observed_at.tzinfo is None
                    or valid_until.tzinfo is None
                    or observed_at > now
                    or valid_until <= now
                ):
                    reasons.append(ReasonCode.SAFETY_STATE_STALE)
            except ValueError:
                reasons.append(ReasonCode.SAFETY_STATE_CONFLICT)
        if any(
            envelope[name] != 0
            for name in ("money_budget", "external_call_budget")
        ):
            reasons.append(ReasonCode.BUDGET_EXCEEDED)
        try:
            deadline = datetime.fromisoformat(
                str(envelope["deadline"]).replace("Z", "+00:00")
            )
            if deadline.tzinfo is None or deadline <= datetime.now(timezone.utc):
                reasons.append(ReasonCode.DEADLINE_EXCEEDED)
        except ValueError:
            reasons.append(ReasonCode.TASK_ENVELOPE_STALE)
        if envelope.get("untrusted_content_instruction_detected") is True:
            reasons.append(ReasonCode.UNTRUSTED_CONTENT_INSTRUCTION_REJECTED)
        disagreement_state = envelope.get(
            "disagreement_state", "NONE_DECLARED"
        )
        if disagreement_state == "SEMANTIC_DISAGREEMENT_PRESERVED":
            reasons.append(ReasonCode.OWNER_REVIEW_REQUIRED)
        elif disagreement_state != "NONE_DECLARED":
            reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
        llm_task = envelope.get("llm_advisory_task")
        if envelope.get("llm_advisory_requested") is True or llm_task is not None:
            llm_text_fields = set(LLM_ADVISORY_TASK_FIELDS) - {
                "redacted_context_refs",
                "allowlisted_tool_refs",
                "numerical_recheck_requirement",
                "source_truth_prohibition",
                "risk_mode_order_prohibition",
            }
            if (
                not isinstance(llm_task, Mapping)
                or any(field not in llm_task for field in LLM_ADVISORY_TASK_FIELDS)
                or any(
                    not isinstance(llm_task.get(field), str)
                    or not llm_task.get(field)
                    for field in llm_text_fields
                )
                or not isinstance(llm_task.get("redacted_context_refs"), tuple)
                or not tuple(llm_task.get("redacted_context_refs") or ())
                or any(
                    not isinstance(value, str) or not value
                    for value in tuple(llm_task.get("redacted_context_refs") or ())
                )
                or not isinstance(llm_task.get("allowlisted_tool_refs"), tuple)
                or not tuple(llm_task.get("allowlisted_tool_refs") or ())
                or not set(tuple(llm_task.get("allowlisted_tool_refs") or ()))
                <= set(ALLOWED_TOOL_SCOPE_REFS)
                or llm_task.get("source_truth_prohibition") is not True
                or llm_task.get("risk_mode_order_prohibition") is not True
                or llm_task.get("numerical_recheck_requirement") is not True
            ):
                reasons.append(ReasonCode.LLM_ADVISORY_ONLY)
        action_scope = set(tuple(envelope["action_scope_refs"]))
        if action_scope & CANDIDATE_INTAKE_ACTION_IDS:
            candidate_packet = envelope.get("candidate_information_packet")
            if (
                not isinstance(candidate_packet, Mapping)
                or any(field not in candidate_packet for field in EXTERNAL_CANDIDATE_FIELDS)
                or not isinstance(candidate_packet.get("provenance_refs"), tuple)
                or not tuple(candidate_packet.get("provenance_refs") or ())
                or any(
                    not isinstance(value, str) or not value
                    for value in tuple(candidate_packet.get("provenance_refs") or ())
                )
                or any(
                    not isinstance(candidate_packet.get(field), str)
                    or not candidate_packet.get(field)
                    for field in set(EXTERNAL_CANDIDATE_FIELDS)
                    - {"provenance_refs"}
                )
            ):
                reasons.append(ReasonCode.TASK_SCOPE_MISMATCH)
            elif candidate_packet.get("accepted_source_truth") is not False:
                reasons.append(ReasonCode.SOURCE_TRUTH_FORBIDDEN)
        for flag, reason in EFFECT_ATTEMPT_REASON_BY_FLAG.items():
            if envelope.get(flag) is True:
                reasons.append(reason)
        memory_prior_ref = envelope.get("memory_prior_ref", EXPLICIT_ABSENCE)
        if memory_prior_ref != EXPLICIT_ABSENCE:
            memory_is_current = (
                isinstance(memory_prior_ref, str)
                and bool(memory_prior_ref)
                and envelope.get("memory_revalidation_state")
                == "CURRENT_REVALIDATED"
                and envelope.get("memory_context_similarity_state")
                == "CURRENT_CONTEXT_MATCH"
                and envelope.get("memory_context_ref") == context_ref
                and isinstance(envelope.get("memory_version_ref"), str)
                and bool(envelope.get("memory_version_ref"))
            )
            try:
                memory_valid_until = datetime.fromisoformat(
                    str(envelope.get("memory_valid_until", "")).replace(
                        "Z", "+00:00"
                    )
                )
                memory_is_current = (
                    memory_is_current
                    and memory_valid_until.tzinfo is not None
                    and memory_valid_until > datetime.now(timezone.utc)
                )
            except ValueError:
                memory_is_current = False
            if not memory_is_current:
                reasons.append(ReasonCode.MEMORY_PRIOR_REVALIDATION_REQUIRED)
        if envelope.get("quantum_challenger") is True:
            formulation = envelope.get("quantum_formulation_bundle")
            quantum_text_fields = set(QUANTUM_FORMULATION_FIELDS) - set(
                QUANTUM_TUPLE_FIELDS
            )
            if (
                not isinstance(formulation, Mapping)
                or any(field not in formulation for field in QUANTUM_FORMULATION_FIELDS)
                or any(
                    not isinstance(formulation.get(field), str)
                    or not formulation.get(field)
                    for field in quantum_text_fields
                )
                or any(
                    not isinstance(formulation.get(field), tuple)
                    or not tuple(formulation.get(field) or ())
                    or any(
                        not isinstance(value, str) or not value
                        for value in tuple(formulation.get(field) or ())
                    )
                    for field in QUANTUM_TUPLE_FIELDS
                )
            ):
                reasons.append(ReasonCode.QPU_EFFECT_FORBIDDEN)
        idempotency_key = str(envelope["idempotency_key"])
        if (
            request_idempotency_key is not None
            and request_idempotency_key != idempotency_key
        ):
            reasons.append(ReasonCode.IDEMPOTENCY_CONFLICT)
        fingerprint = json.dumps(
            {
                "request_id": request_id,
                "principal_id": principal_id,
                "capability_bundle_id": capability_bundle_id,
                "operation_id": operation_id,
                "context_ref": context_ref,
                "requested_scope_refs": _jsonable(requested_scope_refs),
                "requested_parameter_ids": list(requested_parameter_ids),
                "task_envelope": _jsonable(envelope),
                "boundary_state": {
                    name: _jsonable(getattr(bundle.boundary_state, name))
                    for name in bundle.boundary_state.__dataclass_fields__
                },
                "trust_state": bundle.trust_state,
                "quarantined": bundle.quarantined,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        request_claim_key = (principal_id, request_id)
        prior_request_claim = self._request_claims.get(request_claim_key)
        if prior_request_claim is not None and prior_request_claim != (
            idempotency_key,
            fingerprint,
        ):
            reasons.append(ReasonCode.IDEMPOTENCY_CONFLICT)
        seen_key = (principal_id, idempotency_key)
        prior = self._idempotency.get(seen_key)
        if prior is not None:
            if prior[0] == fingerprint and not reasons:
                self.last_decision = prior[1]
                return prior[1]
            if prior[0] != fingerprint:
                reasons.append(ReasonCode.IDEMPOTENCY_CONFLICT)
        if reasons:
            unique_reasons = tuple(dict.fromkeys(reasons))
            escalation_only = set(unique_reasons) <= {
                ReasonCode.PEER_CHALLENGE_REQUIRED,
                ReasonCode.OWNER_REVIEW_REQUIRED,
            }
            decision = self._decision(
                bundle=bundle,
                request_id=request_id,
                operation_id=operation_id,
                state=(
                    AgentCapabilityDecisionStateV1.OWNER_ESCALATION_REQUIRED
                    if escalation_only
                    else AgentCapabilityDecisionStateV1.DENIED
                ),
                reasons=unique_reasons,
                scope_refs=decision_scope_refs,
                terminal_route=(
                    str(envelope["owner_escalation_route"])
                    if escalation_only
                    else "DENY_TASK_OR_OWNER_ESCALATION"
                ),
            )
        elif envelope.get("terminal_no_trade") is True:
            decision = self._decision(
                bundle=bundle,
                request_id=request_id,
                operation_id=operation_id,
                state=AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED,
                reasons=(ReasonCode.NO_TRADE_REOPTIMIZATION_REQUIRED,),
                scope_refs=decision_scope_refs,
                terminal_route="PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION",
            )
        else:
            decision = self._decision(
                bundle=bundle,
                request_id=request_id,
                operation_id=operation_id,
                state=AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST,
                reasons=(),
                scope_refs=decision_scope_refs,
                terminal_route="QKUComputationControlPlaneV1_NO_EFFECT_REQUEST",
            )
        self._idempotency.setdefault(seen_key, (fingerprint, decision))
        self._request_claims.setdefault(
            request_claim_key, (idempotency_key, fingerprint)
        )
        return decision

    def admit_operation(self, request: object) -> AgentCapabilityDecisionV1:
        context = getattr(request, "context", None)
        requested_scope_refs: dict[str, tuple[str, ...]] = {
            "tool_scope_refs": ("QKUComputationControlPlaneV1",),
        }
        for singular_name, plural_name, scope_field in (
            ("qku_id", "qku_ids", "qku_scope_refs"),
            ("formula_id", "formula_ids", "formula_scope_refs"),
            ("data_scope_ref", "data_scope_refs", "data_scope_refs"),
            ("owner_action_id", "owner_action_ids", "action_scope_refs"),
        ):
            values = getattr(request, plural_name, None)
            if values is None:
                value = getattr(request, singular_name, None)
                values = (value,) if isinstance(value, str) and value else ()
            requested_scope_refs[scope_field] = tuple(values)
        if not requested_scope_refs["formula_scope_refs"]:
            component_values = getattr(request, "component_ids", None)
            if component_values is None:
                component = getattr(request, "component_id", None)
                component_values = (
                    (component,)
                    if isinstance(component, str) and component
                    else ()
                )
            requested_scope_refs["formula_scope_refs"] = tuple(
                component_values
            )
        requested_parameter_ids = getattr(request, "parameter_ids", ())
        if not isinstance(requested_parameter_ids, tuple):
            requested_parameter_ids = ("INVALID_PARAMETER_SCOPE",)
        decision = self.resolve(
            request_id=str(getattr(request, "request_id", "")),
            principal_id=str(getattr(request, "principal_id", "")),
            capability_bundle_id=str(
                getattr(request, "capability_bundle_id", "")
            ),
            operation_id=str(getattr(request, "operation_name", "")),
            context_ref=str(getattr(context, "context_id", "")),
            requested_scope_refs=requested_scope_refs,
            requested_parameter_ids=requested_parameter_ids,
            request_idempotency_key=str(
                getattr(request, "idempotency_key", "")
            ),
        )
        return decision


def build_generated_policy_rows(
    *, control_rows: Iterable[Mapping[str, object]],
    identity_map: AgentIdentityCompatibilityMapV1,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    _, st12e_universe_refs = build_st12e_certified_source_universe_registry()
    for binding in identity_map.bindings.values():
        current_refs_or_gap = tuple(
            dict.fromkeys(
                (
                    *binding.current_principal_refs,
                    *binding.current_role_refs,
                    *binding.current_duty_refs,
                    *binding.intersection_scope,
                )
            )
        ) or (f"IDENTITY_GAP::{binding.source_agent_id}",)
        rows.append(
            {
                "row_id": f"ST12E_IDENTITY::{binding.source_agent_id}",
                "row_type": "IDENTITY_COMPATIBILITY",
                **_jsonable(
                    {
                        name: getattr(binding, name)
                        for name in binding.__dataclass_fields__
                    }
                ),
                "semantic_owner": "AgentIdentityCompatibilityMapV1",
                "implementation_owner": "AgentCapabilityResolverV1",
                "producer_ref": MASTER_PARAMETER_SOURCE_REF,
                "upstream_artifact_refs": [
                    MASTER_PARAMETER_SOURCE_REF,
                    CURRENT_ROSTER_REF,
                    CURRENT_DUTY_REF,
                ],
                "upstream_row_or_value_refs": list(binding.evidence_refs),
                "current_principal_duty_policy_refs": list(
                    current_refs_or_gap
                ),
                "downstream_consumer_refs": ["AgentCapabilityResolverV1"],
                "lifecycle_state": (
                    "CURRENT_EXACT_SCOPED_MAPPING"
                    if binding.mapping_type
                    is not AgentIdentityMappingTypeV1.UNMAPPED
                    else "CURRENT_TYPED_UNMAPPED_LINEAGE"
                ),
                "timing_or_snapshot_state": "BUILD_TIME_FROZEN",
                "activation_state": ACTIVATION_STATE,
                "terminal_route": binding.terminal_mapping_state,
                "validator_ref": CENTRAL_VALIDATOR_REF,
            }
        )
    for row in control_rows:
        rows.append(
            {
                "row_id": str(row["closure_id"]),
                "row_type": "CONTROL",
                "closure_id": str(row["closure_id"]),
                "control_id": str(row["control_id"]),
                "domain": str(row["domain"]),
                "control_slug": str(row["control_slug"]),
                "predicate_group": str(row["predicate_group"]),
                "semantic_owner": str(row["semantic_owner"]),
                "validator_owner": str(row["validator_owner"]),
                "implementation_owner": "AgentCapabilityResolverV1",
                "producer_ref": "ST12E_COMPACT_CLOSURE_REGISTRY",
                "upstream_artifact_refs": [str(row["semantic_owner"])],
                "upstream_row_or_value_refs": [str(row["control_id"])],
                "current_principal_duty_policy_refs": [
                    "AgentCapabilityResolverV1",
                    str(row["semantic_owner"]),
                ],
                "downstream_consumer_refs": [
                    "AgentCapabilityResolverV1",
                    "QKUComputationControlPlaneV1",
                ],
                "lifecycle_state": "CURRENT_POLICY_CONTROL",
                "timing_or_snapshot_state": "BUILD_TIME_FROZEN",
                "activation_state": ACTIVATION_STATE,
                "terminal_route": (
                    "VALIDATE_NO_EFFECT_PREDICATE::"
                    f"{row['predicate_group']}"
                ),
                "validator_ref": CENTRAL_VALIDATOR_REF,
            }
        )
    for binding in ST12E_PARAMETER_CAPABILITY_BINDINGS.values():
        current_identity_refs = tuple(
            dict.fromkeys(
                ref
                for source_agent_id in binding.certified_source_agent_ids
                for mapped in (identity_map.resolve(source_agent_id),)
                for ref in (
                    *mapped.current_principal_refs,
                    *mapped.current_role_refs,
                    *mapped.current_duty_refs,
                    *mapped.intersection_scope,
                )
            )
        )
        rows.append(
            {
                "row_id": f"ST12E_BINDING::{binding.parameter_id}",
                "row_type": "PARAMETER_CAPABILITY_BINDING",
                "parameter_id": binding.parameter_id,
                "parameter_symbol": binding.parameter_symbol,
                "certified_source_universe_ref": st12e_universe_refs[
                    binding.certified_source_agent_ids
                ],
                "value_policy_ref": binding.value_policy_ref,
                "capability_policy_ref": binding.capability_policy_ref,
                "st12e_binding_state": binding.st12e_binding_state,
                "semantic_owner": "ComputationParameterPolicyV1",
                "implementation_owner": "AgentCapabilityResolverV1",
                "producer_ref": "ST12E_COMPACT_CAPABILITY_BINDING_REGISTRY",
                "upstream_artifact_refs": [MASTER_PARAMETER_SOURCE_REF],
                "upstream_row_or_value_refs": [
                    binding.parameter_id,
                    binding.value_policy_ref,
                ],
                "current_principal_duty_policy_refs": [
                    *current_identity_refs,
                    binding.capability_policy_ref,
                    binding.value_policy_ref,
                ],
                "downstream_consumer_refs": [
                    "AgentCapabilityResolverV1",
                    "QKUComputationControlPlaneV1",
                ],
                "lifecycle_state": "CURRENT_CAPABILITY_BINDING",
                "timing_or_snapshot_state": "BUILD_TIME_FROZEN",
                "activation_state": ACTIVATION_STATE,
                "terminal_route": "NO_EFFECT_ELIGIBILITY_OR_NO_TRADE",
                "validator_ref": CENTRAL_VALIDATOR_REF,
            }
        )
    return tuple(sorted(rows, key=lambda row: str(row["row_id"])))


def no_effect_authority_is_closed() -> bool:
    envelope = TRANCHE_A_AUTHORITY
    return all(
        getattr(envelope, name) is False
        for name in (
            "provider_connection_allowed",
            "private_state_read_allowed",
            "replay_or_paper_execution_allowed",
            "mode_or_grant_activation_allowed",
            "order_release_allowed",
            "qpu_execution_allowed",
            "profit_or_quantum_advantage_claim_allowed",
            "master_plan_mutation_authorized",
            "merge_canary_live_or_launch_allowed",
            "llm_inference_allowed",
        )
    )
