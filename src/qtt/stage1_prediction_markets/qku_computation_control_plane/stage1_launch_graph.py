"""Immutable Stage-1 selected-scope and launch-graph no-effect projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
import heapq
import json
import re

from .errors import ContractValidationError, ReasonCode
from .models import NO_EFFECTS_V1, NoEffectFlagsV1
from .serialization import deterministic_json, safe_json_loads, validate_relative_path


STAGE1_SELECTED_SCOPE_SCHEMA_VERSION = "STAGE1_SELECTED_SCOPE_V2"
SELECTED_LAUNCH_GRAPH_SCHEMA_VERSION = "SELECTED_LAUNCH_GRAPH_V2"
STAGE1_LAUNCH_GRAPH_AUTHORITY_CLASS = (
    "OWNER_SCOPE_AND_IMPLEMENTATION_CLOSURE_PROJECTION_NO_RUNTIME_EFFECT"
)
STAGE1_LAUNCH_GRAPH_GRAPH_SEMANTICS = (
    "IMPLEMENTATION_CLOSURE_DAG_NOT_RUNTIME_GATE_DAG"
)
S1_LAUNCH_GRAPH_PACKAGE_REF = "S1-LAUNCH-GRAPH-MATERIALIZATION-01"

_ROLE_ID_PATTERN = re.compile(r"ROLE-(?:0[1-9]|1[0-9]|2[0-8])")
_PATH_REASON_BY_DISPOSITION = {
    "EXISTING_CANONICAL_OWNER": "CURRENT_CANONICAL_OWNER_PATH",
    "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED": (
        "FUTURE_OWNER_PATH_RESERVED_NO_IMPLEMENTATION_AUTHORITY"
    ),
}


class Stage1VenueProfileIdV1(StrEnum):
    GEMINI_TITAN_DIRECT = "GEMINI_TITAN_DIRECT"
    POLYMARKET_US_RETAIL_DIRECT = "POLYMARKET_US_RETAIL_DIRECT"
    KALSHI_US_DCM_DIRECT = "KALSHI_US_DCM_DIRECT"
    FORECASTEX_IBKR = "FORECASTEX_IBKR"
    FORECASTEX_DIRECT_MEMBER = "FORECASTEX_DIRECT_MEMBER"


class Stage1ProfileScopeStateV1(StrEnum):
    SELECTED_CORE = "SELECTED_CORE"
    OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION = (
        "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION"
    )


class Stage1RoleDispositionV1(StrEnum):
    BINDING_ONLY_GAP = "BINDING_ONLY_GAP"
    EVIDENCE_ONLY_GAP = "EVIDENCE_ONLY_GAP"
    TRUE_MISSING_DEPENDENCY = "TRUE_MISSING_DEPENDENCY"


class Stage1LaunchGraphTerminalStateV1(StrEnum):
    VALIDATED_NO_EFFECT = "VALIDATED_NO_EFFECT"
    REJECTED_INVALID = "REJECTED_INVALID"


class Stage1FailureRouteV1(StrEnum):
    NO_TRADE = "NO_TRADE"
    UNAVAILABLE = "UNAVAILABLE"
    SAFE_HOLD = "SAFE_HOLD"
    SUBMIT_DISABLED = "SUBMIT_DISABLED"
    CLASSICAL_ONLY = "CLASSICAL_ONLY"
    EVIDENCE_INSUFFICIENT_FAIL_CLOSED = "EVIDENCE_INSUFFICIENT_FAIL_CLOSED"
    NO_TRADE_AND_SUBMIT_DISABLED = "NO_TRADE_AND_SUBMIT_DISABLED"
    QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD = (
        "QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD"
    )


class Stage1OperationClassV1(StrEnum):
    NEW_OR_INCREASED_EXPOSURE = "NEW_OR_INCREASED_EXPOSURE"
    CANCEL_QUERY_RECONCILE = "CANCEL_QUERY_RECONCILE"
    RISK_REDUCING_POSITION_ACTION = "RISK_REDUCING_POSITION_ACTION"
    REPLAY_PAPER_EVIDENCE = "REPLAY_PAPER_EVIDENCE"
    QUANTUM_CHALLENGER_RESEARCH = "QUANTUM_CHALLENGER_RESEARCH"


class Stage1RoleLatencyClassV1(StrEnum):
    BOUNDED_HOTPATH_COMPUTE = "BOUNDED_HOTPATH_COMPUTE"
    HARD_CONTROL_HOTPATH = "HARD_CONTROL_HOTPATH"
    PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH = (
        "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH"
    )
    IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP = (
        "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP"
    )
    OFFLINE_EVIDENCE_ONLY = "OFFLINE_EVIDENCE_ONLY"
    ASYNC_CHALLENGER_ONLY = "ASYNC_CHALLENGER_ONLY"
    SOLE_WRITE_HOTPATH = "SOLE_WRITE_HOTPATH"


class Stage1OperationConsumptionLawV1(StrEnum):
    EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES = (
        "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES"
    )


class Stage1ResearchStateV1(StrEnum):
    COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED = (
        "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
    )
    NOT_APPLICABLE_WITH_PROOF = "NOT_APPLICABLE_WITH_PROOF"
    BLOCKED_OWNER_DECISION_REQUIRED = "BLOCKED_OWNER_DECISION_REQUIRED"


class Stage1RepositoryPathDispositionV1(StrEnum):
    EXISTING_CANONICAL_OWNER = "EXISTING_CANONICAL_OWNER"
    FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED = (
        "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
    )


def _exact_text(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty canonical text",
        )
    return value


def _exact_role_id(value: object, field_name: str) -> str:
    text = _exact_text(value, field_name)
    if _ROLE_ID_PATTERN.fullmatch(text) is None:
        raise ContractValidationError(
            ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
            f"{field_name} must be ROLE-01 through ROLE-28",
        )
    return text


def _exact_no_effects(value: object, field_name: str) -> None:
    if type(value) is not NoEffectFlagsV1 or value != NO_EFFECTS_V1:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            f"{field_name} must equal NO_EFFECTS_V1",
        )


def _exact_unique_role_tuple(
    values: object, field_name: str, *, allow_empty: bool
) -> tuple[str, ...]:
    if type(values) is not tuple or (not allow_empty and not values):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be an exact tuple",
        )
    result = tuple(_exact_role_id(value, field_name) for value in values)
    if len(result) != len(set(result)):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} contains duplicate role IDs",
        )
    return result


@dataclass(frozen=True, slots=True)
class Stage1VenueProfileV1:
    profile_id: Stage1VenueProfileIdV1
    scope_state: Stage1ProfileScopeStateV1
    serialization_ordinal_or_none: int | None
    operating_legal_entity: str
    clearing_or_access_route: str
    product_family: str
    api_profile: str
    jurisdiction: str
    authority_ref: str
    research_state: Stage1ResearchStateV1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        if type(self.scope_state) is not Stage1ProfileScopeStateV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "scope_state must be an exact Stage1ProfileScopeStateV1",
            )
        if self.scope_state is Stage1ProfileScopeStateV1.SELECTED_CORE:
            if (
                type(self.serialization_ordinal_or_none) is not int
                or self.serialization_ordinal_or_none not in {1, 2, 3}
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "selected profile ordinal must be exact 1, 2, or 3",
                )
            if self.research_state is not (
                Stage1ResearchStateV1.COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "selected profile research state must be complete",
                )
        elif self.serialization_ordinal_or_none is not None:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "excluded profile ordinal must be None",
            )
        if type(self.research_state) is not Stage1ResearchStateV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "research_state must be an exact Stage1ResearchStateV1",
            )
        for name in (
            "operating_legal_entity",
            "clearing_or_access_route",
            "product_family",
            "api_profile",
            "jurisdiction",
            "authority_ref",
        ):
            _exact_text(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class Stage1SelectedScopeV2:
    schema_version: str
    profiles: tuple[Stage1VenueProfileV1, ...]
    selected_profile_ids: tuple[Stage1VenueProfileIdV1, ...]
    excluded_profile_ids: tuple[Stage1VenueProfileIdV1, ...]
    serialization: tuple[Stage1VenueProfileIdV1, ...]
    active_live_profile_ids: tuple[Stage1VenueProfileIdV1, ...]
    authority_class: str
    source_decision_ref: str
    no_effects: NoEffectFlagsV1

    def __post_init__(self) -> None:
        _exact_text(self.schema_version, "schema_version")
        if (
            type(self.profiles) is not tuple
            or not self.profiles
            or any(type(row) is not Stage1VenueProfileV1 for row in self.profiles)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "profiles must be a nonempty exact Stage1VenueProfileV1 tuple",
            )
        for name in (
            "selected_profile_ids",
            "excluded_profile_ids",
            "serialization",
            "active_live_profile_ids",
        ):
            values = getattr(self, name)
            if (
                type(values) is not tuple
                or any(type(value) is not Stage1VenueProfileIdV1 for value in values)
                or len(values) != len(set(values))
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be an ordered unique profile tuple",
                )
        _exact_text(self.authority_class, "authority_class")
        _exact_text(self.source_decision_ref, "source_decision_ref")
        _exact_no_effects(self.no_effects, "no_effects")


@dataclass(frozen=True, slots=True)
class Stage1RepositoryPathRefV1:
    path: str
    disposition: Stage1RepositoryPathDispositionV1
    semantic_owner: str
    reason: str

    def __post_init__(self) -> None:
        if type(self.path) is not str or any(
            token in self.path for token in ("*", "?", "[", "]")
        ):
            raise ContractValidationError(
                ReasonCode.PATH_UNSAFE,
                "path must be exact repository-relative text without wildcards",
            )
        normalized = validate_relative_path(self.path)
        if normalized != self.path:
            raise ContractValidationError(
                ReasonCode.PATH_UNSAFE,
                "path must already be canonical repo-relative POSIX text",
            )
        if type(self.disposition) is not Stage1RepositoryPathDispositionV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "disposition must be an exact Stage1RepositoryPathDispositionV1",
            )
        _exact_text(self.semantic_owner, "semantic_owner")
        _exact_text(self.reason, "reason")
        if self.reason != _PATH_REASON_BY_DISPOSITION[self.disposition.value]:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "path reason does not match its disposition",
            )


@dataclass(frozen=True, slots=True)
class Stage1LaunchRoleV2:
    role_id: str
    responsibility: str
    disposition: Stage1RoleDispositionV1
    semantic_owner: str
    path_refs: tuple[Stage1RepositoryPathRefV1, ...]
    frozen_output: str
    direct_prerequisite_role_ids: tuple[str, ...]
    default_failure_route: Stage1FailureRouteV1
    latency_class: Stage1RoleLatencyClassV1
    research_state: Stage1ResearchStateV1

    def __post_init__(self) -> None:
        _exact_role_id(self.role_id, "role_id")
        _exact_text(self.responsibility, "responsibility")
        if type(self.disposition) is not Stage1RoleDispositionV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "disposition must be an exact Stage1RoleDispositionV1",
            )
        _exact_text(self.semantic_owner, "semantic_owner")
        if (
            type(self.path_refs) is not tuple
            or not self.path_refs
            or any(type(value) is not Stage1RepositoryPathRefV1 for value in self.path_refs)
            or len({value.path for value in self.path_refs}) != len(self.path_refs)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "path_refs must be a nonempty unique exact tuple",
            )
        if any(value.semantic_owner != self.semantic_owner for value in self.path_refs):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "path_refs must inherit the role semantic owner",
            )
        _exact_text(self.frozen_output, "frozen_output")
        prerequisites = _exact_unique_role_tuple(
            self.direct_prerequisite_role_ids,
            "direct_prerequisite_role_ids",
            allow_empty=True,
        )
        if self.role_id in prerequisites:
            raise ContractValidationError(
                ReasonCode.DEPENDENCY_CYCLE,
                "a role cannot directly depend on itself",
            )
        if type(self.default_failure_route) is not Stage1FailureRouteV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "default_failure_route must be an exact Stage1FailureRouteV1",
            )
        if type(self.latency_class) is not Stage1RoleLatencyClassV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "latency_class must be an exact Stage1RoleLatencyClassV1",
            )
        if self.research_state is not (
            Stage1ResearchStateV1.COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "launch role research state must be complete",
            )


@dataclass(frozen=True, slots=True)
class Stage1LaunchDependencyEdgeV1:
    edge_id: str
    producer_role_id: str
    consumer_role_id: str
    required: bool
    failure_route: Stage1FailureRouteV1

    def __post_init__(self) -> None:
        producer = _exact_role_id(self.producer_role_id, "producer_role_id")
        consumer = _exact_role_id(self.consumer_role_id, "consumer_role_id")
        if producer == consumer:
            raise ContractValidationError(
                ReasonCode.DEPENDENCY_CYCLE,
                "an edge cannot be a self-loop",
            )
        if self.edge_id != f"S1-EDGE::{producer}->{consumer}":
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "edge_id does not match producer and consumer",
            )
        if type(self.required) is not bool or self.required is not True:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "every launch-graph edge must be exact required=true",
            )
        if type(self.failure_route) is not Stage1FailureRouteV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "failure_route must be an exact Stage1FailureRouteV1",
            )


@dataclass(frozen=True, slots=True)
class Stage1OperationDependencyProfileV1:
    operation_class: Stage1OperationClassV1
    required_role_ids: tuple[str, ...]
    optional_role_ids: tuple[str, ...]
    terminal_failure_route: Stage1FailureRouteV1
    purpose: str
    consumption_law: Stage1OperationConsumptionLawV1
    no_effects: NoEffectFlagsV1
    research_state: Stage1ResearchStateV1

    def __post_init__(self) -> None:
        if type(self.operation_class) is not Stage1OperationClassV1:
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "operation_class must be an exact Stage1OperationClassV1",
            )
        required = _exact_unique_role_tuple(
            self.required_role_ids, "required_role_ids", allow_empty=False
        )
        optional = _exact_unique_role_tuple(
            self.optional_role_ids, "optional_role_ids", allow_empty=True
        )
        if set(required).intersection(optional):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "required and optional role IDs must be disjoint",
            )
        if type(self.terminal_failure_route) is not Stage1FailureRouteV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "terminal_failure_route must be exact Stage1FailureRouteV1",
            )
        _exact_text(self.purpose, "purpose")
        if type(self.consumption_law) is not Stage1OperationConsumptionLawV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "consumption_law must be exact Stage1OperationConsumptionLawV1",
            )
        _exact_no_effects(self.no_effects, "no_effects")
        if self.research_state is not (
            Stage1ResearchStateV1.COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "operation profile research state must be complete",
            )


@dataclass(frozen=True, slots=True)
class SelectedLaunchGraphV2:
    schema_version: str
    graph_semantics: str
    scope: Stage1SelectedScopeV2
    roles: tuple[Stage1LaunchRoleV2, ...]
    dependency_edges: tuple[Stage1LaunchDependencyEdgeV1, ...]
    topological_order: tuple[str, ...]
    operation_profiles: tuple[Stage1OperationDependencyProfileV1, ...]
    binding_only_role_ids: tuple[str, ...]
    evidence_only_role_ids: tuple[str, ...]
    true_missing_role_ids: tuple[str, ...]
    future_sole_write_role_id: str
    terminal_state: Stage1LaunchGraphTerminalStateV1
    reason_codes: tuple[ReasonCode, ...]
    no_effects: NoEffectFlagsV1

    def __post_init__(self) -> None:
        _exact_text(self.schema_version, "schema_version")
        _exact_text(self.graph_semantics, "graph_semantics")
        if type(self.scope) is not Stage1SelectedScopeV2:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "scope must be an exact Stage1SelectedScopeV2",
            )
        for field_name, row_type, allow_empty in (
            ("roles", Stage1LaunchRoleV2, False),
            ("dependency_edges", Stage1LaunchDependencyEdgeV1, False),
            ("operation_profiles", Stage1OperationDependencyProfileV1, False),
        ):
            values = getattr(self, field_name)
            if (
                type(values) is not tuple
                or (not allow_empty and not values)
                or any(type(value) is not row_type for value in values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{field_name} must be an exact nonempty tuple",
                )
        for field_name in (
            "topological_order",
            "binding_only_role_ids",
            "evidence_only_role_ids",
            "true_missing_role_ids",
        ):
            _exact_unique_role_tuple(
                getattr(self, field_name), field_name, allow_empty=False
            )
        _exact_role_id(self.future_sole_write_role_id, "future_sole_write_role_id")
        if type(self.terminal_state) is not Stage1LaunchGraphTerminalStateV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "terminal_state must be exact Stage1LaunchGraphTerminalStateV1",
            )
        if (
            type(self.reason_codes) is not tuple
            or any(type(value) is not ReasonCode for value in self.reason_codes)
            or len(self.reason_codes) != len(set(self.reason_codes))
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "reason_codes must be an ordered unique ReasonCode tuple",
            )
        _exact_no_effects(self.no_effects, "no_effects")


@dataclass(frozen=True, slots=True)
class Stage1LaunchGraphValidationV1:
    terminal_state: Stage1LaunchGraphTerminalStateV1
    reason_codes: tuple[ReasonCode, ...]
    checked_profile_count: int
    checked_role_count: int
    checked_edge_count: int
    checked_operation_profile_count: int
    checked_path_count: int

    def __post_init__(self) -> None:
        if type(self.terminal_state) is not Stage1LaunchGraphTerminalStateV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "terminal_state must be exact Stage1LaunchGraphTerminalStateV1",
            )
        if (
            type(self.reason_codes) is not tuple
            or any(type(value) is not ReasonCode for value in self.reason_codes)
            or tuple(sorted(self.reason_codes, key=lambda value: value.value))
            != self.reason_codes
            or len(self.reason_codes) != len(set(self.reason_codes))
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "reason_codes must be sorted unique ReasonCode values",
            )
        if (
            self.terminal_state
            is Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT
            and self.reason_codes
        ) or (
            self.terminal_state
            is Stage1LaunchGraphTerminalStateV1.REJECTED_INVALID
            and not self.reason_codes
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "validation terminal state and reason codes are inconsistent",
            )
        for name in (
            "checked_profile_count",
            "checked_role_count",
            "checked_edge_count",
            "checked_operation_profile_count",
            "checked_path_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a nonnegative exact integer",
                )


_STAGE1_VENUE_PROFILE_ROWS_JSON = r"""[
  {
    "profile_id": "GEMINI_TITAN_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 1,
    "operating_legal_entity": "Gemini Titan, LLC",
    "clearing_or_access_route": "Gemini Olympus, LLC",
    "product_family": "GEMINI_PREDICTION_MARKETS_EVENT_CONTRACTS",
    "api_profile": "DIRECT_ACCOUNT_SCOPED_REST_WEBSOCKET",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "POLYMARKET_US_RETAIL_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 2,
    "operating_legal_entity": "QCX LLC d/b/a Polymarket US",
    "clearing_or_access_route": "QC Clearing LLC d/b/a Polymarket Clearing",
    "product_family": "POLYMARKET_US_RETAIL_EVENT_CONTRACTS",
    "api_profile": "RETAIL_APP_USER_REST_MARKET_PRIVATE_WEBSOCKET",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "KALSHI_US_DCM_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 3,
    "operating_legal_entity": "KalshiEX LLC",
    "clearing_or_access_route": "Kalshi Klear LLC",
    "product_family": "KALSHI_EVENT_CONTRACTS",
    "api_profile": "DIRECT_REST_WEBSOCKET_FIX_IF_ENTITLED",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "FORECASTEX_IBKR",
    "scope_state": "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION",
    "serialization_ordinal_or_none": null,
    "operating_legal_entity": "ForecastEx LLC",
    "clearing_or_access_route": "Interactive Brokers access route",
    "product_family": "FORECASTEX_EVENT_CONTRACTS",
    "api_profile": "INTERMEDIATED_IBKR",
    "jurisdiction": "UNITED_STATES_CFTC_DCM",
    "authority_ref": "CURRENT_OWNER_EXCLUSION",
    "research_state": "NOT_APPLICABLE_WITH_PROOF"
  },
  {
    "profile_id": "FORECASTEX_DIRECT_MEMBER",
    "scope_state": "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION",
    "serialization_ordinal_or_none": null,
    "operating_legal_entity": "ForecastEx LLC",
    "clearing_or_access_route": "Direct member route",
    "product_family": "FORECASTEX_EVENT_CONTRACTS",
    "api_profile": "DIRECT_MEMBER",
    "jurisdiction": "UNITED_STATES_CFTC_DCM",
    "authority_ref": "CURRENT_OWNER_EXCLUSION",
    "research_state": "NOT_APPLICABLE_WITH_PROOF"
  }
]"""

_STAGE1_LAUNCH_ROLE_ROWS_JSON = r"""[
  {
    "role_id": "ROLE-01",
    "responsibility": "Canonical venue/product/account/API-profile identity",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Identity/specification owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/stage1_launch_graph.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/identity_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Stage1SelectedScopeV2 plus exact compound profile identities and authority lineage",
    "direct_prerequisite_role_ids": [],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-02",
    "responsibility": "Market/event/contract discovery",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Source/PIT owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/market_data.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Current contract inventory with lifecycle and resolution binding",
    "direct_prerequisite_role_ids": [
      "ROLE-01"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-03",
    "responsibility": "Point-in-time source acceptance",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Source/rights/PIT owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Observed/effective/available/received/processed clocks and rights",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-04",
    "responsibility": "Local order-book reconstruction",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Selected venue public-state owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/market_data.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Snapshot + contiguous deltas + gap/reconnect receipt",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-05",
    "responsibility": "Trade-flow and microstructure features",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU computation owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Point-in-time feature vector with own-action lineage",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-04"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-06",
    "responsibility": "Market-implied probability/fair value",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU computation owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Executable-side probability/fair value under exact scale",
    "direct_prerequisite_role_ids": [
      "ROLE-04"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-07",
    "responsibility": "Source/model probability and calibration",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Evidence/model-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Versioned probability distribution and calibration artifact",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-05",
      "ROLE-06"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-08",
    "responsibility": "Uncertainty decomposition",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Evidence/model-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Typed source/model/parameter/regime/execution/latency/settlement vector",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-07"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-09",
    "responsibility": "Fee/rebate/reward computation",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Binding plus economic-math owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/profiles.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Exact effective-time/eligibility/rounding/embedding result",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-10",
    "responsibility": "Executable depth/slippage/impact",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU economic-math owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Exact book walk plus residual impact and embedding ledger",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-09"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-11",
    "responsibility": "Fill and partial-fill distribution",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Evidence/model owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Contextual fill probability and quantity distribution",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-05",
      "ROLE-10",
      "ROLE-12"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-12",
    "responsibility": "Queue position and survival",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-science owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Native queue state or independently validated proxy",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-05"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-13",
    "responsibility": "Adverse selection and markout",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "TCA/evidence owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Conditional signed markout distribution by horizon/context",
    "direct_prerequisite_role_ids": [
      "ROLE-05",
      "ROLE-11"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-14",
    "responsibility": "Latency-decay curve and economic-TTL inputs",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Latency/economic owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Versioned net-cash decay function, current opportunity age, joint latency safety margin, and deterministic TTL resolver",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-04",
      "ROLE-05"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-15",
    "responsibility": "Expected executable net cash",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Economic/accounting owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Complete projected executable cash once, with embedding flags",
    "direct_prerequisite_role_ids": [
      "ROLE-06",
      "ROLE-07",
      "ROLE-08",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-13",
      "ROLE-14"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-16",
    "responsibility": "Joint robust net-cash LCB and final economic TTL",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Evidence/model-risk/QKU owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Dependent lower bound versus NO_TRADE/best alternative plus final positive-TTL decision",
    "direct_prerequisite_role_ids": [
      "ROLE-08",
      "ROLE-15"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-17",
    "responsibility": "Cash/reservation/order-custody truth",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Accounting/capital-risk/private-state owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/transaction.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/private_state.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/reconciliation.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "OrderCustodyStateV2 and conservative reservations",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-18",
    "responsibility": "Hard risk and exposure",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Capital-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Exact selected scope and cash/event/venue/concentration/drawdown gates",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-17"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-19",
    "responsibility": "Position sizing",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU/capital-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Micro-only cash size under robust edge/capacity/loss caps",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-17",
      "ROLE-18"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-20",
    "responsibility": "Portfolio and capital-time allocation",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Portfolio/QKU/quantum owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Deterministic classical constrained allocation plus optional challenger",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-21",
    "responsibility": "Entry/execution action policy",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-policy owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/lifecycle.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "MAKE/TAKE/SPLIT/WAIT/CANCEL/NO_TRADE state machine",
    "direct_prerequisite_role_ids": [
      "ROLE-14",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19",
      "ROLE-20",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-22",
    "responsibility": "Exit/hold/reduce/hedge/reverse policy",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-policy/lifecycle/risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/lifecycle.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Bounded current-state lifecycle policy",
    "direct_prerequisite_role_ids": [
      "ROLE-14",
      "ROLE-15",
      "ROLE-17",
      "ROLE-18",
      "ROLE-26"
    ],
    "default_failure_route": "SAFE_HOLD",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-23",
    "responsibility": "TCA and realized attribution",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "TCA/evidence/accounting owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Attempt-level source/model/execution/cost attribution",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-13",
      "ROLE-14",
      "ROLE-17",
      "ROLE-21",
      "ROLE-22"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "OFFLINE_EVIDENCE_ONLY",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-24",
    "responsibility": "Mode/ALLOW/snapshot eligibility",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Mode/snapshot owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/mode_snapshot_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Pinned graph/source/evidence/security/risk/owner envelope",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-08",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-21",
      "ROLE-22",
      "ROLE-23",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-25",
    "responsibility": "Sole venue-write release",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "ExecutionRouterV1 owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_router.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Idempotent stale-checked fenced custody-aware dispatch",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-14",
      "ROLE-17",
      "ROLE-18",
      "ROLE-21",
      "ROLE-22",
      "ROLE-24",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "SOLE_WRITE_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-26",
    "responsibility": "Deterministic classical fallback",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Dependency/fallback owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dependency_graph.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Same-input admissible fallback for every selected path",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-27",
    "responsibility": "Quantum challenger artifact",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Quantum mapper/benchmark owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/plugin_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Same-formulation challenger with feasibility/economic interpret-back",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-20",
      "ROLE-26"
    ],
    "default_failure_route": "CLASSICAL_ONLY",
    "latency_class": "ASYNC_CHALLENGER_ONLY",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-28",
    "responsibility": "Agent capability and duty enforcement",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Agent/LLM policy owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/llm_gateway.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Typed tasks, duties, budgets, abstention, quarantine",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-26"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  }
]"""

_STAGE1_OPERATION_PROFILE_ROWS_JSON = r"""[
  {
    "operation_class": "NEW_OR_INCREASED_EXPOSURE",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03",
      "ROLE-04",
      "ROLE-05",
      "ROLE-06",
      "ROLE-07",
      "ROLE-08",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-12",
      "ROLE-13",
      "ROLE-14",
      "ROLE-15",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19",
      "ROLE-20",
      "ROLE-21",
      "ROLE-22",
      "ROLE-23",
      "ROLE-24",
      "ROLE-25",
      "ROLE-26",
      "ROLE-28"
    ],
    "optional_role_ids": [
      "ROLE-27"
    ],
    "terminal_failure_route": "NO_TRADE_AND_SUBMIT_DISABLED",
    "purpose": "Full release-critical lifecycle closure for any new or increased exposure.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "CANCEL_QUERY_RECONCILE",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-17",
      "ROLE-24",
      "ROLE-25",
      "ROLE-28"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD",
    "purpose": "Narrow emergency/control path independent of public-source, market-discovery, alpha, hard-risk computation, portfolio, and quantum availability.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "RISK_REDUCING_POSITION_ACTION",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03",
      "ROLE-04",
      "ROLE-09",
      "ROLE-10",
      "ROLE-14",
      "ROLE-15",
      "ROLE-17",
      "ROLE-18",
      "ROLE-22",
      "ROLE-24",
      "ROLE-25",
      "ROLE-26",
      "ROLE-28"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "SAFE_HOLD",
    "purpose": "Bounded hold, cancel-only, reduce-only, close-only, offset, or exact reverse using current authoritative state.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "REPLAY_PAPER_EVIDENCE",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03",
      "ROLE-04",
      "ROLE-05",
      "ROLE-06",
      "ROLE-07",
      "ROLE-08",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-12",
      "ROLE-13",
      "ROLE-14",
      "ROLE-15",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-23",
      "ROLE-26",
      "ROLE-28"
    ],
    "optional_role_ids": [
      "ROLE-27"
    ],
    "terminal_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "purpose": "Immutable-input replay and distinct PAPER evidence without order authority.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "QUANTUM_CHALLENGER_RESEARCH",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-08",
      "ROLE-15",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19",
      "ROLE-20",
      "ROLE-26",
      "ROLE-27"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "CLASSICAL_ONLY",
    "purpose": "Same-formulation true-quantum challenger evidence with deterministic classical fallback.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  }
]"""


_PROFILE_ROW_KEYS = frozenset(
    {
        "profile_id",
        "scope_state",
        "serialization_ordinal_or_none",
        "operating_legal_entity",
        "clearing_or_access_route",
        "product_family",
        "api_profile",
        "jurisdiction",
        "authority_ref",
        "research_state",
    }
)
_ROLE_ROW_KEYS = frozenset(
    {
        "role_id",
        "responsibility",
        "disposition",
        "semantic_owner",
        "path_refs",
        "frozen_output",
        "direct_prerequisite_role_ids",
        "default_failure_route",
        "latency_class",
        "research_state",
    }
)
_PATH_ROW_KEYS = frozenset({"path", "disposition"})
_OPERATION_ROW_KEYS = frozenset(
    {
        "operation_class",
        "required_role_ids",
        "optional_role_ids",
        "terminal_failure_route",
        "purpose",
        "consumption_law",
        "research_state",
    }
)


def _decode_rows(
    text: str, expected_keys: frozenset[str], family: str
) -> tuple[dict[str, object], ...]:
    try:
        raw = safe_json_loads(text)
    except Exception as exc:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{family} row literal is invalid",
        ) from exc
    if type(raw) is not list or not raw:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{family} row literal must be a nonempty JSON array",
        )
    rows: list[dict[str, object]] = []
    for row in raw:
        if type(row) is not dict or frozenset(row) != expected_keys:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"{family} row fields differ from the exact schema",
            )
        rows.append(row)
    return tuple(rows)


def _parse_profiles() -> tuple[Stage1VenueProfileV1, ...]:
    rows = _decode_rows(
        _STAGE1_VENUE_PROFILE_ROWS_JSON,
        _PROFILE_ROW_KEYS,
        "profile",
    )
    parsed: list[Stage1VenueProfileV1] = []
    try:
        for row in rows:
            parsed.append(
                Stage1VenueProfileV1(
                    profile_id=Stage1VenueProfileIdV1(row["profile_id"]),
                    scope_state=Stage1ProfileScopeStateV1(row["scope_state"]),
                    serialization_ordinal_or_none=row[
                        "serialization_ordinal_or_none"
                    ],
                    operating_legal_entity=row["operating_legal_entity"],
                    clearing_or_access_route=row["clearing_or_access_route"],
                    product_family=row["product_family"],
                    api_profile=row["api_profile"],
                    jurisdiction=row["jurisdiction"],
                    authority_ref=row["authority_ref"],
                    research_state=Stage1ResearchStateV1(row["research_state"]),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "profile row could not be converted to its exact contract",
        ) from exc
    if len({row.profile_id for row in parsed}) != len(parsed):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "profile rows contain duplicate profile IDs",
        )
    return tuple(parsed)


def _parse_roles() -> tuple[Stage1LaunchRoleV2, ...]:
    rows = _decode_rows(
        _STAGE1_LAUNCH_ROLE_ROWS_JSON,
        _ROLE_ROW_KEYS,
        "role",
    )
    parsed: list[Stage1LaunchRoleV2] = []
    try:
        for row in rows:
            raw_path_refs = row["path_refs"]
            if type(raw_path_refs) is not list or not raw_path_refs:
                raise TypeError("path_refs")
            path_refs: list[Stage1RepositoryPathRefV1] = []
            for path_row in raw_path_refs:
                if (
                    type(path_row) is not dict
                    or frozenset(path_row) != _PATH_ROW_KEYS
                ):
                    raise TypeError("path_ref")
                disposition = Stage1RepositoryPathDispositionV1(
                    path_row["disposition"]
                )
                path_refs.append(
                    Stage1RepositoryPathRefV1(
                        path=path_row["path"],
                        disposition=disposition,
                        semantic_owner=row["semantic_owner"],
                        reason=_PATH_REASON_BY_DISPOSITION[disposition.value],
                    )
                )
            raw_prerequisites = row["direct_prerequisite_role_ids"]
            if type(raw_prerequisites) is not list:
                raise TypeError("direct_prerequisite_role_ids")
            parsed.append(
                Stage1LaunchRoleV2(
                    role_id=row["role_id"],
                    responsibility=row["responsibility"],
                    disposition=Stage1RoleDispositionV1(row["disposition"]),
                    semantic_owner=row["semantic_owner"],
                    path_refs=tuple(path_refs),
                    frozen_output=row["frozen_output"],
                    direct_prerequisite_role_ids=tuple(raw_prerequisites),
                    default_failure_route=Stage1FailureRouteV1(
                        row["default_failure_route"]
                    ),
                    latency_class=Stage1RoleLatencyClassV1(
                        row["latency_class"]
                    ),
                    research_state=Stage1ResearchStateV1(
                        row["research_state"]
                    ),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "role row could not be converted to its exact contract",
        ) from exc
    if len({row.role_id for row in parsed}) != len(parsed):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "role rows contain duplicate role IDs",
        )
    return tuple(parsed)


def _parse_operation_profiles(
) -> tuple[Stage1OperationDependencyProfileV1, ...]:
    rows = _decode_rows(
        _STAGE1_OPERATION_PROFILE_ROWS_JSON,
        _OPERATION_ROW_KEYS,
        "operation profile",
    )
    parsed: list[Stage1OperationDependencyProfileV1] = []
    try:
        for row in rows:
            if (
                type(row["required_role_ids"]) is not list
                or type(row["optional_role_ids"]) is not list
            ):
                raise TypeError("operation role IDs")
            parsed.append(
                Stage1OperationDependencyProfileV1(
                    operation_class=Stage1OperationClassV1(
                        row["operation_class"]
                    ),
                    required_role_ids=tuple(row["required_role_ids"]),
                    optional_role_ids=tuple(row["optional_role_ids"]),
                    terminal_failure_route=Stage1FailureRouteV1(
                        row["terminal_failure_route"]
                    ),
                    purpose=row["purpose"],
                    consumption_law=Stage1OperationConsumptionLawV1(
                        row["consumption_law"]
                    ),
                    no_effects=NO_EFFECTS_V1,
                    research_state=Stage1ResearchStateV1(
                        row["research_state"]
                    ),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "operation row could not be converted to its exact contract",
        ) from exc
    if len({row.operation_class for row in parsed}) != len(parsed):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "operation rows contain duplicate operation classes",
        )
    return tuple(parsed)


def _derive_edges(
    roles: tuple[Stage1LaunchRoleV2, ...],
) -> tuple[Stage1LaunchDependencyEdgeV1, ...]:
    edges: list[Stage1LaunchDependencyEdgeV1] = []
    for consumer in roles:
        for producer_role_id in sorted(
            consumer.direct_prerequisite_role_ids
        ):
            edges.append(
                Stage1LaunchDependencyEdgeV1(
                    edge_id=(
                        f"S1-EDGE::{producer_role_id}->{consumer.role_id}"
                    ),
                    producer_role_id=producer_role_id,
                    consumer_role_id=consumer.role_id,
                    required=True,
                    failure_route=consumer.default_failure_route,
                )
            )
    return tuple(edges)


def _lexicographic_kahn(
    role_ids: tuple[str, ...],
    edges: tuple[Stage1LaunchDependencyEdgeV1, ...],
) -> tuple[str, ...]:
    indegree = {role_id: 0 for role_id in role_ids}
    adjacency = {role_id: [] for role_id in role_ids}
    for edge in edges:
        if (
            edge.producer_role_id not in indegree
            or edge.consumer_role_id not in indegree
        ):
            raise ContractValidationError(
                ReasonCode.DEPENDENCY_UNKNOWN,
                "dependency edge references an unknown role",
            )
        indegree[edge.consumer_role_id] += 1
        adjacency[edge.producer_role_id].append(edge.consumer_role_id)
    ready = [role_id for role_id, value in indegree.items() if value == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        role_id = heapq.heappop(ready)
        order.append(role_id)
        for consumer_role_id in sorted(adjacency[role_id]):
            indegree[consumer_role_id] -= 1
            if indegree[consumer_role_id] == 0:
                heapq.heappush(ready, consumer_role_id)
    if len(order) != len(role_ids):
        raise ContractValidationError(
            ReasonCode.DEPENDENCY_CYCLE,
            "launch graph contains a dependency cycle",
        )
    return tuple(order)


_STAGE1_VENUE_PROFILES_V1 = _parse_profiles()
STAGE1_SELECTED_PROFILE_IDS_V2 = tuple(
    row.profile_id
    for row in sorted(
        (
            row
            for row in _STAGE1_VENUE_PROFILES_V1
            if row.scope_state is Stage1ProfileScopeStateV1.SELECTED_CORE
        ),
        key=lambda row: row.serialization_ordinal_or_none,
    )
)
_STAGE1_EXCLUDED_PROFILE_IDS_V2 = tuple(
    row.profile_id
    for row in _STAGE1_VENUE_PROFILES_V1
    if row.scope_state
    is Stage1ProfileScopeStateV1.OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION
)
STAGE1_SELECTED_SCOPE_V2 = Stage1SelectedScopeV2(
    schema_version=STAGE1_SELECTED_SCOPE_SCHEMA_VERSION,
    profiles=_STAGE1_VENUE_PROFILES_V1,
    selected_profile_ids=STAGE1_SELECTED_PROFILE_IDS_V2,
    excluded_profile_ids=_STAGE1_EXCLUDED_PROFILE_IDS_V2,
    serialization=STAGE1_SELECTED_PROFILE_IDS_V2,
    active_live_profile_ids=(),
    authority_class=STAGE1_LAUNCH_GRAPH_AUTHORITY_CLASS,
    source_decision_ref="S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    no_effects=NO_EFFECTS_V1,
)
STAGE1_LAUNCH_ROLES_V2 = _parse_roles()
STAGE1_LAUNCH_DEPENDENCY_EDGES_V1 = _derive_edges(
    STAGE1_LAUNCH_ROLES_V2
)
STAGE1_OPERATION_DEPENDENCY_PROFILES_V1 = _parse_operation_profiles()

_EXPECTED_PROFILE_IDS = (
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT,
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
    Stage1VenueProfileIdV1.FORECASTEX_IBKR,
    Stage1VenueProfileIdV1.FORECASTEX_DIRECT_MEMBER,
)
_EXPECTED_SELECTED_PROFILE_IDS = _EXPECTED_PROFILE_IDS[:3]
_EXPECTED_EXCLUDED_PROFILE_IDS = _EXPECTED_PROFILE_IDS[3:]
_EXPECTED_ROLE_IDS = tuple(f"ROLE-{value:02d}" for value in range(1, 29))
_EXPECTED_OPERATION_CLASSES = tuple(Stage1OperationClassV1)
_EXPECTED_EDGE_COUNT = 102
_EXPECTED_UNIQUE_ROLE_PATH_COUNT = 34
_EXPECTED_TOPOLOGICAL_ORDER = (
    "ROLE-01",
    "ROLE-02",
    "ROLE-03",
    "ROLE-04",
    "ROLE-05",
    "ROLE-06",
    "ROLE-07",
    "ROLE-08",
    "ROLE-09",
    "ROLE-10",
    "ROLE-12",
    "ROLE-11",
    "ROLE-13",
    "ROLE-14",
    "ROLE-15",
    "ROLE-16",
    "ROLE-17",
    "ROLE-18",
    "ROLE-19",
    "ROLE-20",
    "ROLE-26",
    "ROLE-22",
    "ROLE-27",
    "ROLE-28",
    "ROLE-21",
    "ROLE-23",
    "ROLE-24",
    "ROLE-25",
)


def _disposition_ids(
    disposition: Stage1RoleDispositionV1,
) -> tuple[str, ...]:
    return tuple(
        role.role_id
        for role in STAGE1_LAUNCH_ROLES_V2
        if role.disposition is disposition
    )


def _assemble_canonical_graph() -> SelectedLaunchGraphV2:
    return SelectedLaunchGraphV2(
        schema_version=SELECTED_LAUNCH_GRAPH_SCHEMA_VERSION,
        graph_semantics=STAGE1_LAUNCH_GRAPH_GRAPH_SEMANTICS,
        scope=STAGE1_SELECTED_SCOPE_V2,
        roles=STAGE1_LAUNCH_ROLES_V2,
        dependency_edges=STAGE1_LAUNCH_DEPENDENCY_EDGES_V1,
        topological_order=_lexicographic_kahn(
            tuple(role.role_id for role in STAGE1_LAUNCH_ROLES_V2),
            STAGE1_LAUNCH_DEPENDENCY_EDGES_V1,
        ),
        operation_profiles=STAGE1_OPERATION_DEPENDENCY_PROFILES_V1,
        binding_only_role_ids=_disposition_ids(
            Stage1RoleDispositionV1.BINDING_ONLY_GAP
        ),
        evidence_only_role_ids=_disposition_ids(
            Stage1RoleDispositionV1.EVIDENCE_ONLY_GAP
        ),
        true_missing_role_ids=_disposition_ids(
            Stage1RoleDispositionV1.TRUE_MISSING_DEPENDENCY
        ),
        future_sole_write_role_id="ROLE-25",
        terminal_state=Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT,
        reason_codes=(),
        no_effects=NO_EFFECTS_V1,
    )


_STAGE1_CANONICAL_GRAPH_V2 = _assemble_canonical_graph()


def build_stage1_launch_graph_v2() -> SelectedLaunchGraphV2:
    """Return the immutable canonical no-effect launch graph."""

    return _STAGE1_CANONICAL_GRAPH_V2


def _sorted_reasons(reasons: set[ReasonCode]) -> tuple[ReasonCode, ...]:
    return tuple(sorted(reasons, key=lambda value: value.value))


def validate_stage1_launch_graph_v2(
    graph: SelectedLaunchGraphV2,
) -> Stage1LaunchGraphValidationV1:
    """Validate exact scope, graph, operation, path, writer, and no-effect closure."""

    if type(graph) is not SelectedLaunchGraphV2:
        return Stage1LaunchGraphValidationV1(
            terminal_state=Stage1LaunchGraphTerminalStateV1.REJECTED_INVALID,
            reason_codes=(ReasonCode.INVALID_CONTRACT,),
            checked_profile_count=0,
            checked_role_count=0,
            checked_edge_count=0,
            checked_operation_profile_count=0,
            checked_path_count=0,
        )

    reasons: set[ReasonCode] = set()
    profiles = graph.scope.profiles
    roles = graph.roles
    edges = graph.dependency_edges
    operations = graph.operation_profiles
    unique_paths = {
        path_ref.path for role in roles for path_ref in role.path_refs
    }

    if (
        graph.schema_version != SELECTED_LAUNCH_GRAPH_SCHEMA_VERSION
        or graph.graph_semantics != STAGE1_LAUNCH_GRAPH_GRAPH_SEMANTICS
        or graph.terminal_state
        is not Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT
        or graph.reason_codes
    ):
        reasons.add(ReasonCode.INVALID_CONTRACT)

    if (
        tuple(row.profile_id for row in profiles) != _EXPECTED_PROFILE_IDS
        or graph.scope.selected_profile_ids != _EXPECTED_SELECTED_PROFILE_IDS
        or graph.scope.excluded_profile_ids != _EXPECTED_EXCLUDED_PROFILE_IDS
        or graph.scope.serialization != _EXPECTED_SELECTED_PROFILE_IDS
    ):
        reasons.add(ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED)
    if graph.scope != STAGE1_SELECTED_SCOPE_V2:
        reasons.add(ReasonCode.INVALID_CONTRACT)
    if graph.scope.active_live_profile_ids:
        reasons.add(ReasonCode.RUNTIME_EFFECT_FORBIDDEN)

    if tuple(role.role_id for role in roles) != _EXPECTED_ROLE_IDS:
        reasons.add(ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED)
    if roles != STAGE1_LAUNCH_ROLES_V2:
        reasons.add(ReasonCode.INVALID_CONTRACT)
    if any(
        path_ref.semantic_owner != role.semantic_owner
        for role in roles
        for path_ref in role.path_refs
    ):
        reasons.add(ReasonCode.INVALID_CONTRACT)
    for role in roles:
        for path_ref in role.path_refs:
            try:
                if (
                    validate_relative_path(path_ref.path) != path_ref.path
                    or any(
                        token in path_ref.path
                        for token in ("*", "?", "[", "]")
                    )
                ):
                    reasons.add(ReasonCode.PATH_UNSAFE)
            except Exception:
                reasons.add(ReasonCode.PATH_UNSAFE)

    try:
        derived_edges = _derive_edges(roles)
        derived_order = _lexicographic_kahn(
            tuple(role.role_id for role in roles), derived_edges
        )
    except ContractValidationError as exc:
        reasons.add(exc.reason_code)
        derived_edges = ()
        derived_order = ()

    if (
        len(edges) != _EXPECTED_EDGE_COUNT
        or len({edge.edge_id for edge in edges}) != len(edges)
        or edges != derived_edges
        or edges != STAGE1_LAUNCH_DEPENDENCY_EDGES_V1
        or graph.topological_order != derived_order
        or graph.topological_order != _EXPECTED_TOPOLOGICAL_ORDER
    ):
        reasons.add(ReasonCode.DEPENDENCY_CLOSURE_FAILED)

    if (
        tuple(row.operation_class for row in operations)
        != _EXPECTED_OPERATION_CLASSES
    ):
        reasons.add(ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED)
    if operations != STAGE1_OPERATION_DEPENDENCY_PROFILES_V1:
        reasons.add(ReasonCode.INVALID_CONTRACT)
    if any(
        set(row.required_role_ids).intersection(row.optional_role_ids)
        or not set(row.required_role_ids).issubset(_EXPECTED_ROLE_IDS)
        or not set(row.optional_role_ids).issubset(_EXPECTED_ROLE_IDS)
        or row.consumption_law
        is not (
            Stage1OperationConsumptionLawV1.EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES
        )
        for row in operations
    ):
        reasons.add(ReasonCode.DEPENDENCY_CLOSURE_FAILED)

    expected_binding = _disposition_ids(
        Stage1RoleDispositionV1.BINDING_ONLY_GAP
    )
    expected_evidence = _disposition_ids(
        Stage1RoleDispositionV1.EVIDENCE_ONLY_GAP
    )
    expected_missing = _disposition_ids(
        Stage1RoleDispositionV1.TRUE_MISSING_DEPENDENCY
    )
    if (
        graph.binding_only_role_ids != expected_binding
        or graph.evidence_only_role_ids != expected_evidence
        or graph.true_missing_role_ids != expected_missing
        or len(expected_binding) != 11
        or len(expected_evidence) != 5
        or len(expected_missing) != 12
    ):
        reasons.add(ReasonCode.DEPENDENCY_CLOSURE_FAILED)

    writer_roles = tuple(
        role.role_id
        for role in roles
        if role.latency_class is Stage1RoleLatencyClassV1.SOLE_WRITE_HOTPATH
    )
    if (
        graph.future_sole_write_role_id != "ROLE-25"
        or writer_roles != ("ROLE-25",)
        or any(
            "execution_router.py" in path_ref.path
            and role.role_id != "ROLE-25"
            for role in roles
            for path_ref in role.path_refs
        )
    ):
        reasons.add(ReasonCode.EXECUTION_ROUTER_BYPASS_FORBIDDEN)

    try:
        _exact_no_effects(graph.no_effects, "no_effects")
        _exact_no_effects(graph.scope.no_effects, "scope.no_effects")
        for row in operations:
            _exact_no_effects(row.no_effects, "operation.no_effects")
    except ContractValidationError:
        reasons.add(ReasonCode.RUNTIME_EFFECT_FORBIDDEN)

    if len(unique_paths) != _EXPECTED_UNIQUE_ROLE_PATH_COUNT:
        reasons.add(ReasonCode.DEPENDENCY_CLOSURE_FAILED)

    reason_codes = _sorted_reasons(reasons)
    return Stage1LaunchGraphValidationV1(
        terminal_state=(
            Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT
            if not reason_codes
            else Stage1LaunchGraphTerminalStateV1.REJECTED_INVALID
        ),
        reason_codes=reason_codes,
        checked_profile_count=len(profiles),
        checked_role_count=len(roles),
        checked_edge_count=len(edges),
        checked_operation_profile_count=len(operations),
        checked_path_count=len(unique_paths),
    )


def stage1_launch_graph_projection_v2() -> Mapping[str, object]:
    """Return one deterministic JSON-safe builder projection."""

    graph = build_stage1_launch_graph_v2()
    validation = validate_stage1_launch_graph_v2(graph)
    if (
        validation.terminal_state
        is not Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT
    ):
        raise ContractValidationError(
            ReasonCode.VALIDATION_FAILED,
            "canonical Stage-1 launch graph did not validate",
        )
    return {
        "package_ref": S1_LAUNCH_GRAPH_PACKAGE_REF,
        "graph": json.loads(deterministic_json(graph)),
        "validation": json.loads(deterministic_json(validation)),
    }


_CANONICAL_VALIDATION = validate_stage1_launch_graph_v2(
    _STAGE1_CANONICAL_GRAPH_V2
)
if (
    _CANONICAL_VALIDATION.terminal_state
    is not Stage1LaunchGraphTerminalStateV1.VALIDATED_NO_EFFECT
    or _CANONICAL_VALIDATION.checked_profile_count != 5
    or _CANONICAL_VALIDATION.checked_role_count != 28
    or _CANONICAL_VALIDATION.checked_edge_count != 102
    or _CANONICAL_VALIDATION.checked_operation_profile_count != 5
    or _CANONICAL_VALIDATION.checked_path_count != 34
):
    raise ContractValidationError(
        ReasonCode.VALIDATION_FAILED,
        "canonical Stage-1 launch graph constants are internally inconsistent",
    )
