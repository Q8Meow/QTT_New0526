"""Immutable ST12-F parent input lock built only from canonical owner snapshots."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
import math
import re
from types import MappingProxyType
from typing import Mapping

from .context import parse_utc
from .errors import ContractValidationError, ReasonCode
from .parameter_policy import (
    ST12FParameterRegistryV1,
    initialize_st12f_parameter_registry_v1,
)
from .serialization import deterministic_json


INPUT_LOCK_SCHEMA_VERSION_V1 = "QTT_ST12F_IMMUTABLE_REPLAY_PAPER_INPUT_LOCK_V1_4"
INPUT_LOCK_CONTRACT_VERSION_V1 = "1.4"
ST12F_TEMPLATE_IDS_V1 = tuple(f"MATH-{number:02d}" for number in range(1, 53))
ST12F_REPLAY_RESULT_CONTRACT_IDS_V1 = tuple(
    f"ST12F-REPLAY-CONTRACT::{template_id}" for template_id in ST12F_TEMPLATE_IDS_V1
)
ST12F_PAPER_RESULT_CONTRACT_IDS_V1 = tuple(
    f"ST12F-PAPER-CONTRACT::{template_id}" for template_id in ST12F_TEMPLATE_IDS_V1
)
ST12F_PARAMETER_VALUE_REF_COUNT_V1 = 3096
_IDENTITY_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _text(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be bounded canonical text",
        )
    return value


def _identity_tuple(value: object, name: str, *, count: int | None = None) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item or item != item.strip() for item in value)
        or len(value) != len(set(value))
        or (count is not None and len(value) != count)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique identity tuple",
        )
    return value


def _freeze_json(value: object, name: str) -> object:
    if value is None or type(value) in {bool, int, str} or isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                f"{name} contains a nonfinite float",
            )
        return value
    if isinstance(value, tuple | list):
        return tuple(_freeze_json(item, name) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"{name} contains a non-text mapping key",
            )
        return MappingProxyType(
            {
                key: _freeze_json(item, f"{name}.{key}")
                for key, item in sorted(value.items())
            }
        )
    raise ContractValidationError(
        ReasonCode.CONTRACT_OR_TYPE_INVALID,
        f"{name} contains unsupported {type(value).__name__}",
    )


def _mapping(value: object, name: str, *, nonempty: bool = True) -> Mapping[str, object]:
    frozen = _freeze_json(value, name)
    if not isinstance(frozen, Mapping) or (nonempty and not frozen):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{name} must be a nonempty immutable mapping",
        )
    return frozen


def validated_st12f_identity_token_v1(value: object) -> str:
    text = _text(value, "identity token")
    if _IDENTITY_TOKEN.fullmatch(text) is None:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "identity token is outside the bounded canonical grammar",
        )
    return text


def canonical_st12f_parameter_value_refs_v1(
    registry: ST12FParameterRegistryV1 | None = None,
) -> tuple[str, ...]:
    ready = initialize_st12f_parameter_registry_v1() if registry is None else registry
    if type(ready) is not ST12FParameterRegistryV1:
        raise ContractValidationError(
            ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
            "parameter registry must be the exact READY registry",
        )
    refs = tuple(row.parameter_id for row in ready.parameter_policies)
    _identity_tuple(refs, "parameter_value_refs", count=ST12F_PARAMETER_VALUE_REF_COUNT_V1)
    return refs


@dataclass(frozen=True, slots=True)
class CanonicalReplayPaperInputSnapshotV1:
    """Injected canonical-owner state; never accepted from an OP13 request body."""

    decision_time: datetime
    point_in_time_cutoff: datetime
    market_scope: tuple[str, ...]
    venue_scope: tuple[str, ...]
    instrument_scope: tuple[str, ...]
    formula_specification_versions: Mapping[str, object]
    implementation_versions: Mapping[str, object]
    parameter_policy_version: str
    parameter_value_refs: tuple[str, ...]
    source_epochs: Mapping[str, object]
    data_semantics_version: str
    venue_semantics_version: str
    accounting_definition: Mapping[str, object]
    fee_assumptions: Mapping[str, object]
    spread_assumptions: Mapping[str, object]
    slippage_assumptions: Mapping[str, object]
    fill_and_queue_assumptions: Mapping[str, object]
    latency_and_staleness_assumptions: Mapping[str, object]
    capacity_and_crowding_assumptions: Mapping[str, object]
    portfolio_and_cash_context: Mapping[str, object]
    random_seed_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    scenario_set_id: str
    causation_id: str
    correlation_id: str
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        decision = parse_utc(self.decision_time, field_name="decision_time")
        cutoff = parse_utc(self.point_in_time_cutoff, field_name="point_in_time_cutoff")
        created = parse_utc(self.created_at, field_name="created_at")
        if cutoff > decision or created < decision:
            raise ContractValidationError(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "input snapshot times violate point-in-time custody",
            )
        object.__setattr__(self, "decision_time", decision)
        object.__setattr__(self, "point_in_time_cutoff", cutoff)
        object.__setattr__(self, "created_at", created)
        for name in ("market_scope", "venue_scope", "instrument_scope"):
            _identity_tuple(getattr(self, name), name)
            if not getattr(self, name):
                raise ContractValidationError(
                    ReasonCode.INPUT_SCOPE_MISMATCH,
                    f"{name} cannot be empty",
                )
        for name in (
            "formula_specification_versions",
            "implementation_versions",
            "source_epochs",
            "accounting_definition",
            "fee_assumptions",
            "spread_assumptions",
            "slippage_assumptions",
            "fill_and_queue_assumptions",
            "latency_and_staleness_assumptions",
            "capacity_and_crowding_assumptions",
            "portfolio_and_cash_context",
            "random_seed_policy",
            "resampling_policy",
        ):
            object.__setattr__(self, name, _mapping(getattr(self, name), name))
        if set(self.formula_specification_versions) != set(ST12F_TEMPLATE_IDS_V1):
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "formula version pins must cover the exact 52-template roster",
            )
        if set(self.implementation_versions) != set(ST12F_TEMPLATE_IDS_V1):
            raise ContractValidationError(
                ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
                "implementation version pins must cover the exact 52-template roster",
            )
        _identity_tuple(
            self.parameter_value_refs,
            "parameter_value_refs",
            count=ST12F_PARAMETER_VALUE_REF_COUNT_V1,
        )
        if any(not value.startswith("ST10-PARAM::") for value in self.parameter_value_refs):
            raise ContractValidationError(
                ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
                "parameter references must remain canonical identities only",
            )
        for name in (
            "parameter_policy_version",
            "data_semantics_version",
            "venue_semantics_version",
            "scenario_set_id",
            "causation_id",
            "correlation_id",
            "created_by",
        ):
            _text(getattr(self, name), name)
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "causation and correlation identities must remain distinct",
            )
        if not isinstance(self.resampling_policy.get("trial_family_id"), str):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "resampling_policy must contain trial_family_id",
            )
        if not isinstance(
            self.portfolio_and_cash_context.get("permanent_no_trade_baseline_ref"),
            str,
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "portfolio context must contain the permanent NO_TRADE baseline",
            )


@dataclass(frozen=True, slots=True)
class ImmutableReplayPaperInputLockV1:
    input_lock_id: str
    schema_version: str
    contract_version: str
    decision_time: datetime
    point_in_time_cutoff: datetime
    market_scope: tuple[str, ...]
    venue_scope: tuple[str, ...]
    instrument_scope: tuple[str, ...]
    cohort_template_ids: tuple[str, ...]
    expected_replay_result_contract_ids: tuple[str, ...]
    expected_paper_result_contract_ids: tuple[str, ...]
    formula_specification_versions: Mapping[str, object]
    implementation_versions: Mapping[str, object]
    parameter_policy_version: str
    parameter_value_refs: tuple[str, ...]
    source_epochs: Mapping[str, object]
    data_semantics_version: str
    venue_semantics_version: str
    accounting_definition: Mapping[str, object]
    fee_assumptions: Mapping[str, object]
    spread_assumptions: Mapping[str, object]
    slippage_assumptions: Mapping[str, object]
    fill_and_queue_assumptions: Mapping[str, object]
    latency_and_staleness_assumptions: Mapping[str, object]
    capacity_and_crowding_assumptions: Mapping[str, object]
    portfolio_and_cash_context: Mapping[str, object]
    random_seed_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    scenario_set_id: str
    causation_id: str
    correlation_id: str
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        if len(fields(self)) != 33:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "immutable input lock must contain exactly 33 top-level fields",
            )
        if self.schema_version != INPUT_LOCK_SCHEMA_VERSION_V1 or self.contract_version != INPUT_LOCK_CONTRACT_VERSION_V1:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "immutable input lock schema or contract version differs",
            )
        token = self.input_lock_id.removeprefix("ST12F-LOCK::")
        if self.input_lock_id != f"ST12F-LOCK::{validated_st12f_identity_token_v1(token)}":
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "input_lock_id is not the deterministic natural identity",
            )
        snapshot = CanonicalReplayPaperInputSnapshotV1(
            **{
                name: getattr(self, name)
                for name in (
                    "decision_time",
                    "point_in_time_cutoff",
                    "market_scope",
                    "venue_scope",
                    "instrument_scope",
                    "formula_specification_versions",
                    "implementation_versions",
                    "parameter_policy_version",
                    "parameter_value_refs",
                    "source_epochs",
                    "data_semantics_version",
                    "venue_semantics_version",
                    "accounting_definition",
                    "fee_assumptions",
                    "spread_assumptions",
                    "slippage_assumptions",
                    "fill_and_queue_assumptions",
                    "latency_and_staleness_assumptions",
                    "capacity_and_crowding_assumptions",
                    "portfolio_and_cash_context",
                    "random_seed_policy",
                    "resampling_policy",
                    "scenario_set_id",
                    "causation_id",
                    "correlation_id",
                    "created_by",
                    "created_at",
                )
            }
        )
        for name in (
            "decision_time",
            "point_in_time_cutoff",
            "formula_specification_versions",
            "implementation_versions",
            "source_epochs",
            "accounting_definition",
            "fee_assumptions",
            "spread_assumptions",
            "slippage_assumptions",
            "fill_and_queue_assumptions",
            "latency_and_staleness_assumptions",
            "capacity_and_crowding_assumptions",
            "portfolio_and_cash_context",
            "random_seed_policy",
            "resampling_policy",
            "created_at",
        ):
            object.__setattr__(self, name, getattr(snapshot, name))
        if self.cohort_template_ids != ST12F_TEMPLATE_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "input lock template roster must be the exact ordered 52 identities",
            )
        if (
            self.expected_replay_result_contract_ids != ST12F_REPLAY_RESULT_CONTRACT_IDS_V1
            or self.expected_paper_result_contract_ids != ST12F_PAPER_RESULT_CONTRACT_IDS_V1
            or set(self.expected_replay_result_contract_ids)
            & set(self.expected_paper_result_contract_ids)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "REPLAY and PAPER must define disjoint exact 52-slot rosters",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ImmutableReplayPaperInputLockV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "input-lock payload field roster differs",
            )
        payload = dict(value)
        for name in (
            "market_scope",
            "venue_scope",
            "instrument_scope",
            "cohort_template_ids",
            "expected_replay_result_contract_ids",
            "expected_paper_result_contract_ids",
            "parameter_value_refs",
        ):
            payload[name] = tuple(payload[name])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class EvidenceAssemblerContextV1:
    """Original private assembler composition; no lane or generic-store permit."""

    __slots__ = ("_issuer", "_host", "_owner_resolvers", "_parameter_resolver", "_parameter_receipt",
                 "_inventory_byte_bounds")

    def __init__(self):
        raise TypeError("use explicit original-owner assembler binding")

    def __copy__(self):
        raise TypeError("LP03 assembler context cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 assembler context cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 assembler context cannot be serialized")

    def _require_original_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1, EvidenceIssuerContextV1, _EvidenceIssuerStateV1
        from .context import _native_require
        from .parameter_policy import _st12f_parameter_registry_build_receipt_v1

        state = getattr(self, "_issuer", None)
        _native_require(type(self) is EvidenceAssemblerContextV1 and type(state) is _EvidenceIssuerStateV1
                        and state.assembler_context is self,
                        "LP03_ASSEMBLER_CONTEXT_NOT_ORIGINAL")
        EvidenceIssuerContextV1._state_for_owner_v1(state.context, state.service)
        EvidenceHostBindingV1._assert_local_binding_v1(self._host)
        _native_require(_st12f_parameter_registry_build_receipt_v1(self._parameter_resolver) is self._parameter_receipt,
                        "LP03_ORIGINAL_PARAMETER_REGISTRY_CHANGED")
        _native_require(len(self._owner_resolvers) == len(state.source_custodies)
                        and all(registry is custody.registry for registry, custody
                                in zip(self._owner_resolvers, state.source_custodies)),
                        "LP03_ORIGINAL_ASSEMBLY_RESOLVERS_CHANGED")
        return state


def bind_evidence_input_assembler_v1(*, issuer_service, issuer_context, host_binding,
                                    owner_resolvers, parameter_resolver):
    """Explicit private setup over the same issuer and existing READY owners."""
    from ...agents.pr169_agent_orch1_resolvers import AgentOrchService, EvidenceHostBindingV1, EvidenceIssuerContextV1
    from .context import _native_require
    from .models import EvidenceKeyPurposeV1, EvidenceOriginV1
    from .parameter_policy import _st12f_parameter_registry_build_receipt_v1

    _native_require(type(issuer_service) is AgentOrchService and type(issuer_context) is EvidenceIssuerContextV1
                    and type(host_binding) is EvidenceHostBindingV1, "LP03_ASSEMBLER_ORIGINAL_BINDINGS_REQUIRED")
    state = EvidenceIssuerContextV1._state_for_owner_v1(issuer_context, issuer_service)
    with state.lock:
        _native_require(state.assembler_context is None, "LP03_ASSEMBLER_ALREADY_BOUND")
        EvidenceHostBindingV1._assert_local_binding_v1(host_binding)
        config, issuer_config = host_binding.public_configuration, state.host.public_configuration
        _native_require(config.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                        and config.service_owner == "QKU_COMPUTATION_CONTROL_PLANE"
                        and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER,
                        "LP03_ASSEMBLER_HOST_ROLE")
        _native_require((config.deployment_id, config.host_identity, config.package_identity_ref,
                         config.environment_identity, config.generation, set(config.store_bindings))
                        == (issuer_config.deployment_id, issuer_config.host_identity, issuer_config.package_identity_ref,
                            issuer_config.environment_identity, issuer_config.generation, set(issuer_config.store_bindings))
                        and all(row[3].assembly_scope.assembler_principal == config.service_principal
                                for row in state.owner_envelopes), "LP03_ASSEMBLER_HOST_SCOPE_JOIN")
        _native_require(type(owner_resolvers) is tuple and len(owner_resolvers) == len(state.source_custodies)
                        and all(registry is custody.registry for registry, custody in zip(owner_resolvers, state.source_custodies)),
                        "LP03_ORIGINAL_ASSEMBLY_RESOLVERS_REQUIRED")
        _native_require(type(parameter_resolver) is ST12FParameterRegistryV1, "LP03_ORIGINAL_PARAMETER_REGISTRY_REQUIRED")
        receipt = _st12f_parameter_registry_build_receipt_v1(parameter_resolver)
        result = object.__new__(EvidenceAssemblerContextV1)
        result._issuer, result._host, result._owner_resolvers = state, host_binding, owner_resolvers
        result._parameter_resolver, result._parameter_receipt = parameter_resolver, receipt
        from .implementation_registry import _evidence_snapshot_version_pins_v1
        version_pins = _evidence_snapshot_version_pins_v1()
        result._inventory_byte_bounds = (
            len(deterministic_json(canonical_st12f_parameter_value_refs_v1(parameter_resolver)).encode("utf-8")),
            len(deterministic_json(version_pins).encode("utf-8")),
        )
        state.assembler_context = result
        return result


_LP03_SNAPSHOT_POLICY_FIELDS_V1 = MappingProxyType({
    "data_semantics_version": "VERSION_IDENTITY",
    "venue_semantics_version": "VERSION_IDENTITY",
    "accounting_definition": "ACCOUNTING_POLICY",
    "fee_assumptions": "POLICY",
    "spread_assumptions": "POLICY",
    "slippage_assumptions": "POLICY",
    "fill_and_queue_assumptions": "POLICY",
    "latency_and_staleness_assumptions": "POLICY",
    "capacity_and_crowding_assumptions": "POLICY",
    "portfolio_and_cash_context": "CURRENCY_AND_CONTRACT_CONTEXT",
    "resampling_policy": "RESAMPLING_POLICY",
})


class EvidenceInputAssemblyOutcomeV1:
    """Original assembler proposal; only issuer sealing makes it durable."""

    __slots__ = ("_operation", "_assembler", "_slices", "_snapshot", "_record", "_resolved_inputs", "_resolved_input_originals",
                 "_source_originals")

    def __init__(self):
        raise TypeError("input assembly outcomes require the original assembler")

    def __copy__(self):
        raise TypeError("LP03 assembly outcomes cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 assembly outcomes cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 assembly outcomes cannot be serialized")

    @property
    def canonical_snapshot(self):
        return self._snapshot

    @property
    def assembly_record(self):
        return self._record


def _original_input_assembly_members_v1(operation, outcome):
    from .context import _native_require
    original = operation.input_assembly_members
    _native_require(type(outcome) is EvidenceInputAssemblyOutcomeV1 and operation.input_assembly_outcome is outcome
                    and type(original) is tuple and len(original) == 10
                    and outcome._resolved_input_originals is original[8]
                    and outcome._source_originals is original[9]
                    and outcome._operation is operation
                    and all(getattr(outcome, name) is value for name, value in zip(
                        ("_assembler", "_slices", "_snapshot", "_record", "_resolved_inputs"), original[:5])),
                    "LP03_ORIGINAL_ASSEMBLY_MEMBERS_CHANGED")
    from .input_resolver import (FormulaInputResolutionV1, _EvidencePendingProbabilityEdgeInputsV1,
                                 _require_evidence_resolution_witness_v1)
    roster = original[4]
    _native_require(type(roster) is tuple and 0 < len(roster) <= 48
                    and (all(type(row) is FormulaInputResolutionV1 for row in roster)
                         or len(roster) == 2 and operation.envelope_entry[3].component_closure == ("MATH-01", "MATH-02")
                         and type(roster[0]) is FormulaInputResolutionV1 and type(roster[1]) is _EvidencePendingProbabilityEdgeInputsV1
                         and roster[0].execution_context is roster[1].execution_context)
                    and tuple(row.math_spec_id for row in roster) == operation.envelope_entry[3].component_closure
                    and type(original[8]) is tuple and len(original[8]) == len(roster),
                    "LP03_ORIGINAL_ASSEMBLY_RESOLUTION_ROSTER_CHANGED")
    for row, witness in zip(roster, original[8]):
        _require_evidence_resolution_witness_v1(row, witness, canonical=False)
    from .input_resolver import _require_evidence_source_slice_roster_v1
    _require_evidence_source_slice_roster_v1(operation, original[1], originals=original[9], canonical=False)
    return original


def _require_original_input_assembly_outcome_v1(operation, outcome):
    from .context import _native_require
    original = _original_input_assembly_members_v1(operation, outcome)
    from .input_resolver import _require_evidence_source_slice_roster_v1
    _require_evidence_source_slice_roster_v1(operation, original[1], originals=original[9])
    _native_require(deterministic_json(outcome._record) == original[5]
                    and deterministic_json(outcome._snapshot) == original[6]
                    and deterministic_json(outcome._resolved_inputs) == original[7], "LP03_ORIGINAL_ASSEMBLY_MEMBERS_CHANGED")
    return original[3]


def assemble_evidence_input_snapshot_v1(request, *, assembly_grant, owner_resolvers,
                                       parameter_resolver, source_grants, clock):
    """Resolve the signed original selection, then assemble the unchanged snapshot."""
    from contextlib import ExitStack
    from datetime import UTC, timedelta
    from ...agents.pr169_agent_orch1_resolvers import AgentOrchService, EvidenceAssemblyGrantV1
    from .context import _native_require, exact_decimal
    from .models import (EvidenceAssemblyRequestV1, EvidenceAssemblyStateV1, EvidenceInputAssemblyRecordV1,
                         EvidenceRecordHeaderV1, EvidenceOriginV1)
    from .input_resolver import (CanonicalOwnerPacketRegistryV1, _validate_evidence_assembly_inputs_v1,
                                 _require_evidence_source_slice_roster_v1)
    from .source_policy import _EvidenceHistoricalReadV1
    from .persistence import _EvidenceControlBootstrapV1
    from .implementation_registry import _evidence_snapshot_version_pins_v1
    from .serialization import _evidence_canonical_object_v1

    _native_require(type(assembly_grant) is EvidenceAssemblyGrantV1 and type(request) is EvidenceAssemblyRequestV1,
                    "LP03_ASSEMBLY_ORIGINAL_GRANT_REQUIRED")
    state = assembly_grant._owner
    assembler = state.assembler_context
    _native_require(type(assembler) is EvidenceAssemblerContextV1
                    and EvidenceAssemblerContextV1._require_original_v1(assembler) is state,
                    "LP03_ASSEMBLER_CONTEXT_NOT_ORIGINAL")
    _native_require(type(owner_resolvers) is tuple and len(owner_resolvers) == len(assembler._owner_resolvers)
                    and all(left is right for left, right in zip(owner_resolvers, assembler._owner_resolvers))
                    and parameter_resolver is assembler._parameter_resolver and clock is state.clock,
                    "LP03_ASSEMBLY_ORIGINAL_RESOLVERS_AND_CLOCK_REQUIRED")
    AgentOrchService.resolve_evidence_assembly_grant_v1(state.service, assembly_grant.grant_ref,
        purpose="EVIDENCE_INPUT_ASSEMBLY_V1", requester_context=assembler)
    operation, original_grant, _source_original = state.preparations[assembly_grant.grant_ref]
    scope = operation.envelope_entry[3].assembly_scope
    _native_require(original_grant is assembly_grant and request == operation.request
                    and operation.input_assembly_outcome is None, "LP03_ASSEMBLY_REQUEST_OR_OUTCOME_CONFLICT")
    _native_require(type(source_grants) is tuple and len(source_grants) == len(scope.source_selections)
                    and all(type(cap) is _EvidenceHistoricalReadV1 and cap.requester is assembler
                            and cap.assembly_grant is assembly_grant and cap.selection is selection
                            and any(cap is original for original in operation.source_read_capabilities)
                            for cap, selection in zip(source_grants, scope.source_selections)),
                    "LP03_ASSEMBLY_EXACT_SOURCE_GRANTS_REQUIRED")
    with state.lock, ExitStack() as locks:
        state._lock_original_source_custodies_v1(locks)
        _native_require(state.operation is None and operation.current_state.state in (
            EvidenceAssemblyStateV1.ADMITTED, EvidenceAssemblyStateV1.READING), "LP03_PREPARATION_NOT_READABLE")
        state.operation = operation
        try:
            started_wall, started_mono, _ = _EvidenceControlBootstrapV1._check_current_v1(operation)
        finally:
            state.operation = None
        slices = tuple(CanonicalOwnerPacketRegistryV1.read_evidence_source_slice_v1(cap.registry, cap)
                       for cap in source_grants)
        source_originals = _require_evidence_source_slice_roster_v1(operation, slices)
        state.operation = operation
        try:
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            _require_evidence_source_slice_roster_v1(operation, slices, originals=source_originals, canonical=False)
            _native_require(scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE,
                            "LP03_OBSERVED_ASSEMBLY_REQUIRES_ORIGINAL_NATIVE_SOURCE_PATH")
            events = tuple(event for part in slices for event in part.reconstructed_canonical_events)
            refs = tuple(ref for part in slices for ref in part.original_record_refs)
            _native_require(len(set(refs)) == len(refs) and bool(events), "LP03_ASSEMBLY_DUPLICATE_OR_EMPTY_SOURCE")
            first_scope, first_context = events[0]["scope"], events[0]["context_id"]
            for event in events:
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                times = event["native_clocks"]
                _native_require(event["scope"] == first_scope and event["context_id"] == first_context
                                and (event["schema_id"], event["schema_version"]) in scope.input_schema_and_version_pins,
                                "LP03_ASSEMBLY_SOURCE_SCOPE_OR_SCHEMA")
                _native_require(max(times.values()) <= scope.snapshot_decision_wall_ns
                                and times["available_time"] <= scope.snapshot_pit_cutoff_wall_ns
                                and 0 <= scope.snapshot_decision_wall_ns - times["observed_time"] <= event["ttl_ns"],
                                "LP03_ASSEMBLY_SOURCE_PIT_OR_TTL")
                prior = event["prior_revision_available_wall_ns_or_absence"]
                _native_require(isinstance(prior, Mapping) or prior <= scope.snapshot_pit_cutoff_wall_ns,
                                "LP03_ASSEMBLY_LATE_REVISION")
            resolved_inputs, resolved_originals = _validate_evidence_assembly_inputs_v1(operation, slices)
            # Closed deterministic profiles; no generic statistical or
            # arbitrary component admission follows from source metadata.
            selected_math = tuple(row.math_spec_id for row in resolved_inputs)
            _native_require(selected_math in (("MATH-06",), ("MATH-07",), ("MATH-01",), ("MATH-03",), ("MATH-04",), ("MATH-05",), ("MATH-08",), ("MATH-09",), ("MATH-10",), ("MATH-11",), ("MATH-14",), ("MATH-15",), ("MATH-16",), ("MATH-17",), ("MATH-18",), ("MATH-19",), ("MATH-20",), ("MATH-21",), ("MATH-22",), ("MATH-23",), ("MATH-24",), ("MATH-25",), ("MATH-12",), ("MATH-13",), ("MATH-26",), ("MATH-27",), ("MATH-28",), ("MATH-29",), ("MATH-30",), ("MATH-31",), ("MATH-37",), ("MATH-32",), ("MATH-33",), ("MATH-35",), ("MATH-36",), ("MATH-38",), ("MATH-39",), ("MATH-40",), ("MATH-41",), ("MATH-42",), ("MATH-43",), ("MATH-44",), ("MATH-45",), ("MATH-50",), ("MATH-51",), ("MATH-52",), ("MATH-01", "MATH-02")),
                            "LP03_ASSEMBLY_SNAPSHOT_PROFILE_UNAVAILABLE")
            edge = selected_math == ("MATH-01", "MATH-02")
            brier = selected_math == ("MATH-08",)
            multiple = selected_math in (("MATH-12",), ("MATH-13",))
            pbo = selected_math == ("MATH-19",)
            held_out = selected_math in (("MATH-20",), ("MATH-21",))
            recorded_dr = selected_math == ("MATH-22",)
            private_execution = selected_math in (("MATH-32",), ("MATH-33",), ("MATH-35",), ("MATH-36",), ("MATH-38",), ("MATH-39",), ("MATH-40",), ("MATH-41",), ("MATH-42",), ("MATH-43",), ("MATH-44",), ("MATH-45",))
            analytic = selected_math in (("MATH-29",), ("MATH-30",), ("MATH-31",), ("MATH-37",))
            quantum = selected_math in (("MATH-50",), ("MATH-51",), ("MATH-52",))
            private_values = analytic or private_execution or quantum
            if private_values:
                from .evidence import EVIDENCE_PROJECTION_CONTRACTS_V1
                analytic_basis = EVIDENCE_PROJECTION_CONTRACTS_V1[selected_math[0]].basis_requirement
            ope_point = selected_math in (("MATH-23",), ("MATH-24",), ("MATH-25",))
            if ope_point:
                from .models import _LP03_OPE_POINT_PROJECTION_PROFILES_V1
                ope_basis = _LP03_OPE_POINT_PROJECTION_PROFILES_V1[selected_math[0]][2]
            sharpe = selected_math in (("MATH-17",), ("MATH-18",))
            spa = selected_math == ("MATH-16",)
            reality = selected_math == ("MATH-15",)
            bootstrap = selected_math == ("MATH-14",)
            wilson = selected_math == ("MATH-11",)
            calibration = selected_math == ("MATH-10",)
            log_loss = selected_math == ("MATH-09",)
            research = selected_math == ("MATH-26",)
            kelly27 = selected_math == ("MATH-27",)
            kelly28 = selected_math == ("MATH-28",)
            kelly = kelly27 or kelly28
            cashflow = selected_math in (("MATH-06",),("MATH-07",))
            market = selected_math in (("MATH-01",), ("MATH-04",), ("MATH-05",))
            math_id = selected_math[-1] if edge else selected_math[0]
            from .models import _LP03_MARKET_METRIC_PROFILES_V1, _LP03_SHARPE_PROJECTION_PROFILES_V1
            from .parameter_policy import _LP03_HELDOUT_PROTOCOL_METRICS_V1
            policy_values, lineage = {}, {}
            for event in events:
                for key, contribution in event["values"].items():
                    if not key.startswith("snapshot."):
                        continue
                    name = key.removeprefix("snapshot.")
                    _native_require(name in _LP03_SNAPSHOT_POLICY_FIELDS_V1 and name not in policy_values,
                                    "LP03_ASSEMBLY_UNKNOWN_OR_DUPLICATE_FIELD")
                    _native_require((event["owner_id"], event["record_kind"], event["schema_id"], event["schema_version"])
                                    == ("QKU_COMPUTATION_CONTROL_PLANE", "EvidenceSnapshotPolicyV1",
                                        "QTT_LP03_SNAPSHOT_POLICY_V1", "1.0"), "LP03_ASSEMBLY_POLICY_OWNER_SCHEMA")
                    _native_require(isinstance(contribution, Mapping) and set(contribution) == {"value", "unit", "basis", "version"}
                                    and contribution["unit"] == _LP03_SNAPSHOT_POLICY_FIELDS_V1[name]
                                    and contribution["basis"] == "DECLARED_SOFTWARE_CONFORMANCE"
                                    and contribution["version"] == event["input_version"], "LP03_ASSEMBLY_POLICY_UNIT_OR_VERSION")
                    policy_values[name] = contribution["value"]
                    lineage[name] = (event["record_ref"], event["producer_receipt_id"])
            _native_require(set(policy_values) == set(_LP03_SNAPSHOT_POLICY_FIELDS_V1), "LP03_ASSEMBLY_REQUIRED_INPUTS_MISSING")
            portfolio, accounting = policy_values["portfolio_and_cash_context"], policy_values["accounting_definition"]
            _native_require(isinstance(portfolio, Mapping) and set(portfolio) == {"permanent_no_trade_baseline_ref", "currency"}
                            and isinstance(accounting, Mapping) and set(accounting) == {
                                "currency", "quantity_unit", "entry_rule", "real_account_state", "cash_account_ref", "equity_account_ref",
                                "ledger_unit", "opening_basis", "scale", "rounding_policy_ref",
                                "measurement_basis" if brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or multiple or research or market or cashflow or kelly or edge else "midpoint_basis"} | (
                                    {"input_snapshot_ref","event_ref","instrument_ref","horizon_ref","horizon_end_wall_ns","cashflow_basis",
                                     "account_basis","account_context_ref","outcome_ids","ordered_outcome_roles"} if cashflow else
                                    {"risk_capital_basis_ref", "risk_capital_currency", "instrument_ref", "horizon_ref", "sizing_decision_ref"} if kelly else
                                    {"utility_unit", "utility_basis_ref", "horizon_ref", "research_decision_ref"} if research else {"quantity_scope_ref", "horizon_ref", "output_unit"} if private_values else set())
                            and accounting["quantity_unit"] == ("TOTAL_ACCOUNT_CASHFLOW" if cashflow else "NOT_APPLICABLE_TO_PROBABILITY_EDGE" if edge else "SIZING_DECISION" if kelly else "RESEARCH_DECISION" if research else
                                "NOT_APPLICABLE_TO_MULTIPLE_TESTING" if multiple else "NOT_APPLICABLE_TO_RECORDED_DR_UNCERTAINTY" if recorded_dr else "NOT_APPLICABLE_TO_RECORDED_OPE_POINT" if ope_point else "NOT_APPLICABLE_TO_PRIVATE_ANALYTIC_CONVERSION" if analytic else "UNIT_OF_ORIGINAL_PRIVATE_EXECUTION" if private_execution else "NOT_APPLICABLE_TO_QUANTUM_TRACE_ACCOUNTING" if quantum else "NOT_APPLICABLE_TO_HELD_OUT_SCORING" if held_out else "NOT_APPLICABLE_TO_CSCV_SPLIT_RECORD" if pbo else "NOT_APPLICABLE_TO_SHARPE_PROBABILITY" if sharpe else "NOT_APPLICABLE_TO_SPA_RECORD" if spa else "NOT_APPLICABLE_TO_REALITY_CHECK_RECORD" if reality else "NOT_APPLICABLE_TO_BOOTSTRAP_RECORD" if bootstrap else "NOT_APPLICABLE_TO_WILSON_INTERVAL" if wilson else "NOT_APPLICABLE_TO_CALIBRATION" if calibration else "NOT_APPLICABLE_TO_LOG_LOSS" if log_loss else "NOT_APPLICABLE_TO_BRIER_SCORE" if brier else "CONTRACT")
                            and accounting["entry_rule"] == "BALANCED_DEBIT_CREDIT",
                            "LP03_ASSEMBLY_ACCOUNTING_PROFILE_UNSUPPORTED")
            from .context import _native_ident, _public_counter_v1
            for field_name in ("cash_account_ref", "equity_account_ref", "rounding_policy_ref", "ledger_unit", "opening_basis"):
                _native_ident(accounting[field_name])
            _public_counter_v1(accounting["scale"], allow_zero=True)
            _native_require(accounting["cash_account_ref"] != accounting["equity_account_ref"]
                            and accounting["ledger_unit"] == "CASH" and accounting["opening_basis"] == "SYNTHETIC_OPENING_BALANCE"
                            and accounting["measurement_basis" if brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or multiple or research or market or cashflow or kelly or edge else "midpoint_basis"] == (
                                "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE" if cashflow else "MODEL_MINUS_MARKET_SAME_SNAPSHOT" if edge else "bounded_fractional_wealth_fraction" if kelly28 else "wealth_fraction" if kelly27 else _LP03_MARKET_METRIC_PROFILES_V1[math_id][3] if market else
                                "EXPECTED_VALUE_OF_INFORMATION_PER_DECISION" if research else
                                "MEAN_CONDITIONAL_RECORDED_DR_SCORE" if recorded_dr else ope_basis if ope_point else analytic_basis if private_values else _LP03_HELDOUT_PROTOCOL_METRICS_V1[math_id][1] if held_out else "adjusted_p_and_rejection_mask" if multiple else "probability_of_backtest_overfitting" if pbo else _LP03_SHARPE_PROJECTION_PROFILES_V1[math_id][3] if sharpe else "studentized_loss_differential_spa_p_value" if spa else "benchmark_candidate_loss_differential_p_value" if reality else "bootstrap_statistic_distribution_and_interval" if bootstrap else "lower_upper_probability_interval" if wilson else "absolute_calibration_gap" if calibration else "per_sample_natural_log_loss" if log_loss else "PER_SAMPLE_SQUARED_PROBABILITY" if brier else "SAME_INSTRUMENT_SAME_SNAPSHOT_BEST_BID_ASK_MIDPOINT"),
                            "LP03_ASSEMBLY_OPENING_ACCOUNTING_POLICY")
            explicit_unused = {"state": "ABSENT_WITH_REASON", "reason": "NO_EMPIRICAL_MODEL_FEE_OR_ACCOUNT_BUNDLE_IN_SOFTWARE_FIXTURE" if cashflow else "NOT_USED_BY_SELECTED_" + math_id.replace("-", "_") if market or kelly or multiple or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or edge else
                "NOT_USED_BY_SELECTED_MATH_26" if research else
                "NOT_USED_BY_SELECTED_MATH_14" if bootstrap else "NOT_USED_BY_SELECTED_MATH_11" if wilson else "NOT_USED_BY_SELECTED_MATH_10" if calibration else "NOT_USED_BY_SELECTED_MATH_09" if log_loss else "NOT_USED_BY_SELECTED_MATH_08" if brier else "NOT_USED_BY_SELECTED_MATH_03"}
            _native_require(accounting["real_account_state"] == explicit_unused and all(policy_values[name] == explicit_unused
                for name in ("fee_assumptions", "slippage_assumptions", "fill_and_queue_assumptions", "capacity_and_crowding_assumptions")),
                "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
            _native_require(policy_values["data_semantics_version"] == "SYNTHETIC_ORIGINAL_PACKET_V1"
                            and policy_values["venue_semantics_version"] == (
                                "SOFTWARE_CONFORMANCE_SIGNED_TOTAL_CASHFLOW_V1" if cashflow else "SOFTWARE_CONFORMANCE_SAME_SNAPSHOT_PROBABILITY_EDGE_V1" if edge else
                                "SOFTWARE_CONFORMANCE_CONTRACT_PRICE_V1" if math_id == "MATH-01" else
                                "SOFTWARE_CONFORMANCE_FRACTIONAL_KELLY_V1" if kelly28 else "SOFTWARE_CONFORMANCE_KELLY_PROBABILITY_PAYOFF_V1" if kelly27 else
                                "SOFTWARE_CONFORMANCE_RESEARCH_DECISION_V1" if research else
                                "SOFTWARE_CONFORMANCE_ORIGINAL_RECORDED_DR_V1" if recorded_dr else "SOFTWARE_CONFORMANCE_ORIGINAL_RECORDED_OPE_POINT_V1" if ope_point else "SOFTWARE_CONFORMANCE_ORIGINAL_PRIVATE_ANALYTIC_V1" if analytic else "SOFTWARE_CONFORMANCE_ORIGINAL_PRIVATE_EXECUTION_V1" if private_execution else "SOFTWARE_CONFORMANCE_ORIGINAL_QUANTUM_CONSTRUCTOR_V1" if quantum else "SOFTWARE_CONFORMANCE_ORIGINAL_HELD_OUT_SCORING_V1" if held_out else "SOFTWARE_CONFORMANCE_DECLARED_TRIAL_LEDGER_V1" if multiple else "SOFTWARE_CONFORMANCE_CSCV_MATRIX_AND_GROUP_POLICY_V1" if pbo else "SOFTWARE_CONFORMANCE_SHARPE_LEDGER_AND_MOMENTS_V1" if sharpe else "SOFTWARE_CONFORMANCE_COMPLETE_LOSS_FAMILY_V1" if reality or spa else "SOFTWARE_CONFORMANCE_ORDERED_BOOTSTRAP_SERIES_V1" if bootstrap else "SOFTWARE_CONFORMANCE_BERNOULLI_COUNTS_V1" if wilson else "SOFTWARE_CONFORMANCE_CALIBRATION_DATASET_V1" if calibration else "SOFTWARE_CONFORMANCE_LOG_LOSS_DATASET_V1" if log_loss else "SOFTWARE_CONFORMANCE_FORECAST_DATASET_V1" if brier else "SOFTWARE_CONFORMANCE_BOOK_V1"),
                            "LP03_ASSEMBLY_SEMANTICS_PROFILE_UNSUPPORTED")
            if edge:
                from .models import _evidence_probability_edge_chain_sources_v1
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                                "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                original_sources = []
                for row in (*resolved_inputs[0].inputs,*resolved_inputs[1].external_inputs):
                    matches = tuple(part for part in slices if len(part.original_record_refs) == 1
                        and part.original_record_refs[0].record_id == row.packet_id)
                    _native_require(len(matches) == 1,"LP03_ASSEMBLY_EDGE_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    association_profile="ORIGINAL_SOFTWARE_MARKET_PREDICTION_AND_INDEPENDENT_CALIBRATION_CONTEXT",
                    stack_id="STACK::MATH-01::MATH-02::V3_4",edge_id="EDGE::MATH-01::MATH-02",
                    source_slices=original_sources)).encode("utf-8"))
                _evidence_probability_edge_chain_sources_v1(source_data)
                metadata = original_sources[0].reconstructed_canonical_events[0]["values"]["contract_context"]
                _native_require(accounting["currency"] == metadata["currency"]
                    and scope.exclusive_expiry_wall_ns <= metadata["horizon_end_wall_ns"],
                    "LP03_ASSEMBLY_EDGE_CURRENCY_HORIZON")
            elif kelly27:
                from .models import _evidence_kelly27_source_slices_v1
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                                "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                original_sources = []
                for row in resolved_inputs[0].inputs:
                    matches = tuple(part for part in slices if len(part.original_record_refs) == 1
                                    and part.original_record_refs[0].record_id == row.packet_id)
                    _native_require(len(matches) == 1, "LP03_ASSEMBLY_KELLY27_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    association_profile="SHARED_ORIGINAL_KELLY_PROBABILITY_PAYOFF_CONTEXT", source_slices=original_sources)).encode("utf-8"))
                _evidence_kelly27_source_slices_v1(source_data)
                metadata = original_sources[0].reconstructed_canonical_events[0]["values"]["private_source_context"]
                _native_require(accounting["currency"] == metadata["risk_capital_currency"]
                                and all(accounting[name] == metadata[name] for name in (
                                    "risk_capital_basis_ref", "risk_capital_currency", "instrument_ref", "horizon_ref", "sizing_decision_ref")),
                                "LP03_ASSEMBLY_KELLY27_ORIGINAL_BASIS_JOIN")
            elif kelly28:
                from .models import _evidence_kelly28_source_slices_v1
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                                "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                original_sources = []
                for row in resolved_inputs[0].inputs:
                    matches = tuple(part for part in slices if len(part.original_record_refs) == 1
                                    and part.original_record_refs[0].record_id == row.packet_id)
                    _native_require(len(matches) == 1, "LP03_ASSEMBLY_KELLY28_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    association_profile="ORIGINAL_PUBLISHED_KELLY_AND_CURRENT_CONSTRAINTS",
                    source_slice_jsons=tuple(next(entry[5] for entry in source_originals if entry[3] is part).decode("utf-8", "strict")
                        for part in original_sources),
                    consumer_decision_wall_ns=scope.snapshot_decision_wall_ns, consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns)).encode("utf-8"))
                _evidence_kelly28_source_slices_v1(source_data)
                metadata = original_sources[1].reconstructed_canonical_events[0]["values"]["private_source_context"]
                _native_require(accounting["currency"] == metadata["risk_capital_currency"]
                                and all(accounting[name] == metadata[name] for name in (
                                    "risk_capital_basis_ref", "risk_capital_currency", "instrument_ref", "horizon_ref", "sizing_decision_ref")),
                                "LP03_ASSEMBLY_KELLY28_ORIGINAL_BASIS_JOIN")
            elif private_values:
                from .models import _evidence_original_private_input_profile_v1, _evidence_original_private_inputs_v1

                _native_require(policy_values["spread_assumptions"] == explicit_unused, "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                parts = []
                ids = resolved_inputs[0].packet_refs if math_id == "MATH-39" else tuple(row.packet_id for row in resolved_inputs[0].inputs)
                for source_id in ids:
                    matching = tuple(part for part in slices if len(part.original_record_refs) == 1
                        and part.original_record_refs[0].record_id == source_id)
                    _native_require(len(matching) == 1, "LP03_ASSEMBLY_ANALYTIC_ORIGINAL_SOURCE_ROSTER")
                    parts.append(matching[0])
                source_profile, _, _ = _evidence_original_private_input_profile_v1(math_id)
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    profile=source_profile, math_id=math_id,
                    decision_wall_ns=scope.snapshot_decision_wall_ns, cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
                    source_slices=tuple(parts))).encode("utf-8"))
                _, values, original_scope = _evidence_original_private_inputs_v1(source_data, math_id=math_id)
                _native_require(deterministic_json(values) == deterministic_json(resolved_inputs[0].authoritative_values)
                    and (accounting["quantity_scope_ref"], accounting["horizon_ref"], accounting["output_unit"], analytic_basis)
                    == tuple(original_scope[name] for name in ("quantity_scope_ref", "horizon_ref", "unit", "basis")),
                    "LP03_ASSEMBLY_ANALYTIC_ORIGINAL_SOURCE_SCOPE")
            elif ope_point:
                from .models import _evidence_recorded_ope_source_data_v1

                _native_require(policy_values["spread_assumptions"] == explicit_unused, "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                original_sources = []
                for selected in resolved_inputs[0].inputs:
                    matching = tuple(part for part in slices if len(part.original_record_refs) == 1
                        and part.original_record_refs[0].record_id == selected.packet_id)
                    _native_require(len(matching) == 1, "LP03_ASSEMBLY_OPE_POINT_ORIGINAL_SOURCE_ROSTER")
                    original_sources.append(matching[0])
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    profile="ORIGINAL_SOFTWARE_OPE_POINT_ESTIMATION", selected_math_id=math_id,
                    consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                    consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=tuple(original_sources))).encode("utf-8"))
                _, original_values, _, _ = _evidence_recorded_ope_source_data_v1(source_data, math_id=math_id)
                _native_require(deterministic_json(original_values) == deterministic_json(resolved_inputs[0].authoritative_values),
                    "LP03_ASSEMBLY_OPE_POINT_ORIGINAL_VALUES")
            elif recorded_dr:
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                    "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                policies = tuple(row for row in events if row["record_kind"] == "EvidenceRecordedDrUncertaintyPolicyV1")
                _native_require(len(policies) == 1 and policies[0]["owner_id"] == "ComputationParameterPolicyOwnerV1",
                    "LP03_ASSEMBLY_ORIGINAL_DR_UNCERTAINTY_POLICY")
            elif held_out:
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                    "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                trace = tuple(event for event in events if event["record_kind"] == "EvidenceHeldOutPredictionTraceV1")
                labels = tuple(event for event in events if event["record_kind"] == "EvidenceHeldOutOutcomeLabelRosterV1")
                _native_require(len(trace) == 1, "LP03_MISSING_PREDICTION_PRODUCER")
                _native_require(len(labels) == 1, "LP03_HELD_OUT_ORIGINAL_LABELS_REQUIRED")
            elif brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or multiple or research:
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                                "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                from .models import _evidence_cscv_source_slices_v1, _evidence_sharpe_source_slices_v1, _evidence_spa_source_slices_v1, _evidence_reality_check_source_slices_v1, _evidence_bootstrap_source_slices_v1, _evidence_wilson_source_slices_v1, _evidence_forecast_source_slices_v1, _evidence_multiple_testing_source_slices_v1, _evidence_calibration_source_slices_v1, _evidence_log_loss_source_slices_v1, _evidence_research_source_slices_v1
                original_sources = []
                for row in resolved_inputs[0].inputs:
                    matches = tuple(part for part in slices if len(part.original_record_refs) == 1
                                    and part.original_record_refs[0].record_id == row.packet_id)
                    _native_require(len(matches) == 1, "LP03_ASSEMBLY_RESEARCH_SOURCE_ROSTER" if research else
                        "LP03_ASSEMBLY_FORECAST_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                # Existing original resolution witnesses supply authority; this
                # closed data check verifies the two-slice dataset association.
                if pbo:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="ORIGINAL_DECLARED_SOFTWARE_CSCV_MATRIX_AND_GROUP_POLICY",
                        row_identity_profile="COMPLETE_DECLARED_CHRONOLOGICAL_MATRIX_AND_STRATEGY_ROSTER",
                        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=original_sources)).encode("utf-8"))
                    _evidence_cscv_source_slices_v1(source_data)
                elif sharpe:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="ORIGINAL_DECLARED_SOFTWARE_SHARPE_LEDGER_AND_MOMENTS", math_id=math_id,
                        row_identity_profile="COMPLETE_DECLARED_ATTEMPTED_AND_PRUNED_ROSTER_NO_STATISTICAL_SUPPORT_CLAIM",
                        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=original_sources)).encode("utf-8"))
                    _evidence_sharpe_source_slices_v1(source_data)
                elif spa:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="ORIGINAL_DECLARED_SOFTWARE_LOSS_FAMILY_AND_SPA_POLICY",
                        row_identity_profile="COMPLETE_DECLARED_CANDIDATE_TIME_GRID_NO_EMPIRICAL_UNIVERSE_CLAIM",
                        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=original_sources)).encode("utf-8"))
                    _evidence_spa_source_slices_v1(source_data)
                elif reality:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="ORIGINAL_DECLARED_SOFTWARE_LOSS_FAMILY_AND_REALITY_CHECK_POLICY",
                        row_identity_profile="COMPLETE_DECLARED_CANDIDATE_TIME_GRID_NO_EMPIRICAL_UNIVERSE_CLAIM",
                        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=original_sources)).encode("utf-8"))
                    _evidence_reality_check_source_slices_v1(source_data)
                elif multiple:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="ORIGINAL_DECLARED_SOFTWARE_TRIAL_LEDGER_AND_Q_POLICY", math_id=math_id,
                        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
                        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=original_sources)).encode("utf-8"))
                    _evidence_multiple_testing_source_slices_v1(source_data)
                elif research:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="SHARED_ORIGINAL_RESEARCH_DECISION_CONTEXT", source_slices=original_sources)).encode("utf-8"))
                    _evidence_research_source_slices_v1(source_data)
                    metadata = original_sources[0].reconstructed_canonical_events[0]["values"]["private_source_context"]
                    _native_require(all(accounting[name] == metadata[name] for name in (
                        "utility_unit", "utility_basis_ref", "horizon_ref", "research_decision_ref")),
                        "LP03_ASSEMBLY_RESEARCH_UTILITY_BASIS_JOIN")
                else:
                    source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                        association_profile="SHARED_ORIGINAL_ORDERED_SERIES_AND_BOOTSTRAP_POLICY_CONTEXT" if bootstrap else "SHARED_ORIGINAL_COUNTS_AND_CONFIDENCE_POLICY_CONTEXT" if wilson else "SHARED_ORIGINAL_DATASET_AND_BIN_POLICY_CONTEXT" if calibration else "SHARED_ORIGINAL_DATASET_AND_CLIP_POLICY_CONTEXT" if log_loss else "SHARED_ORIGINAL_DATASET_CONTEXT",
                        row_identity_profile="ORDERED_SYNTHETIC_SERIES_NO_EMPIRICAL_DEPENDENCE_CLAIM" if bootstrap else "AGGREGATE_SYNTHETIC_BERNOULLI_COUNTS_NO_TRIAL_OBSERVATIONS" if wilson else "ORDERED_SYNTHETIC_ROWS_NO_SAMPLE_IDS", source_slices=original_sources)).encode("utf-8"))
                    (_evidence_bootstrap_source_slices_v1 if bootstrap else _evidence_wilson_source_slices_v1 if wilson else _evidence_calibration_source_slices_v1 if calibration else _evidence_log_loss_source_slices_v1 if log_loss else _evidence_forecast_source_slices_v1)(source_data)
            elif cashflow:
                from .models import _evidence_cashflow_source_slices_v1
                _native_require(policy_values["spread_assumptions"] == explicit_unused,
                    "LP03_ASSEMBLY_UNUSED_POLICY_NOT_EXPLICIT")
                original_sources=[]
                for row in resolved_inputs[0].inputs:
                    matches=tuple(part for part in slices if len(part.original_record_refs)==1
                        and part.original_record_refs[0].record_id==row.packet_id)
                    _native_require(len(matches)==1,"LP03_ASSEMBLY_CASHFLOW_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                source_data=_evidence_canonical_object_v1(deterministic_json(dict(
                    association_profile="ORIGINAL_SOFTWARE_SIGNED_TOTAL_CASHFLOW_CONTEXT",math_id=math_id,
                    source_slices=original_sources)).encode("utf-8"))
                _evidence_cashflow_source_slices_v1(source_data)
                metadata=original_sources[0].reconstructed_canonical_events[0]["values"]["cashflow_context"]
                _native_require(all(deterministic_json(accounting[key])==deterministic_json(metadata[key]) for key in (
                    "currency","input_snapshot_ref","event_ref","instrument_ref","horizon_ref","horizon_end_wall_ns",
                    "cashflow_basis","account_basis","account_context_ref","outcome_ids","ordered_outcome_roles"))
                    and accounting["measurement_basis"]==metadata["cashflow_basis"]
                    and scope.exclusive_expiry_wall_ns<=metadata["horizon_end_wall_ns"],
                    "LP03_ASSEMBLY_CASHFLOW_ACCOUNT_CONTEXT_HORIZON_JOIN")
            elif market:
                from .models import _evidence_market_source_slices_v1
                original_sources = []
                for row in resolved_inputs[0].inputs:
                    matches = tuple(part for part in slices if len(part.original_record_refs) == 1
                                    and part.original_record_refs[0].record_id == row.packet_id)
                    _native_require(len(matches) == 1, "LP03_ASSEMBLY_MARKET_SOURCE_ROSTER")
                    original_sources.append(matches[0])
                source_data = _evidence_canonical_object_v1(deterministic_json(dict(
                    association_profile="SHARED_ORIGINAL_MARKET_AND_PAYOUT_CONTEXT", math_id=math_id,
                    source_slices=original_sources)).encode("utf-8"))
                _evidence_market_source_slices_v1(source_data)
                original_market = original_sources[0].reconstructed_canonical_events[0]
                _native_require(accounting["currency"] == original_market["values"]["market_state"]["currency"],
                                "LP03_ASSEMBLY_MARKET_CURRENCY_JOIN")
                spread = explicit_unused if math_id == "MATH-01" else {"original_book_refs": tuple(
                    next(row.packet_id for row in resolved_inputs[0].inputs if row.input_name == name)
                    for name in ("best_bid", "best_ask"))}
                _native_require(policy_values["spread_assumptions"] == spread, "LP03_ASSEMBLY_ORIGINAL_BOOK_POLICY_JOIN")
            else:
                book_refs = tuple(next(row.packet_id for row in resolved_inputs[0].inputs if row.input_name == name)
                                  for name in ("best_bid", "best_ask"))
                _native_require(policy_values["spread_assumptions"] == {"original_book_refs": book_refs},
                                "LP03_ASSEMBLY_ORIGINAL_BOOK_POLICY_JOIN")
            latency = policy_values["latency_and_staleness_assumptions"]
            _native_require(isinstance(latency, Mapping) and set(latency) == {"ttl_ns", "native_clock_policy"}
                            and type(latency["ttl_ns"]) is int and latency["ttl_ns"] > 0
                            and latency["ttl_ns"] == min(event["ttl_ns"] for event in events)
                            and latency["native_clock_policy"] == "ORIGINAL_SIX_CLOCKS",
                            "LP03_ASSEMBLY_ORIGINAL_LATENCY_POLICY_JOIN")
            baseline_ref = portfolio["permanent_no_trade_baseline_ref"]
            baselines = tuple(event for event in events if event["record_ref"] == baseline_ref)
            _native_require(len(baselines) == 1 and (baselines[0]["owner_id"], baselines[0]["record_kind"],
                baselines[0]["schema_id"], baselines[0]["schema_version"]) == ("QKU_COMPUTATION_CONTROL_PLANE",
                "EvidenceSyntheticBaselineV1", "QTT_LP03_SYNTHETIC_BASELINE_V1", "1.0"), "LP03_ASSEMBLY_ORIGINAL_BASELINE_REQUIRED")
            baseline = baselines[0]["values"].get("baseline")
            _native_require(isinstance(baseline, Mapping) and set(baseline) == {"cash", "currency", "positions", "origin"}
                            and baseline["positions"] == () and baseline["origin"] == scope.origin.value
                            and type(baseline["currency"]) is str and bool(baseline["currency"]), "LP03_ASSEMBLY_BASELINE_SHAPE")
            _native_require(exact_decimal(baseline["cash"], field_name="baseline.cash") >= 0, "LP03_ASSEMBLY_BASELINE_CASH")
            _native_require(exact_decimal(baseline["cash"], field_name="baseline.cash").as_tuple().exponent == -accounting["scale"],
                            "LP03_ASSEMBLY_BASELINE_ACCOUNTING_SCALE")
            _native_require(type(portfolio["currency"]) is str and portfolio["currency"] == accounting["currency"] == baseline["currency"],
                            "LP03_ASSEMBLY_CURRENCY_BASIS_MISMATCH")
            resampling = policy_values["resampling_policy"]
            _native_require(isinstance(resampling, Mapping) and set(resampling) == {"trial_family_id", "rule"}
                            and resampling["rule"] == ("NO_RESAMPLING_FOR_SELECTED_SIGNED_TOTAL_CASHFLOW" if cashflow else "NO_RESAMPLING_FOR_SELECTED_PROBABILITY_EDGE" if edge else
                                "NO_RESAMPLING_FOR_SELECTED_FRACTIONAL_KELLY" if kelly28 else
                                "NO_RESAMPLING_FOR_SELECTED_KELLY_PROBABILITY_PAYOFF" if kelly27 else
                                "NO_RESAMPLING_FOR_SELECTED_MARKET_CONTEXT" if market else
                                "NO_RESAMPLING_FOR_SELECTED_RESEARCH_DECISION" if research else
                                "ORIGINAL_COMPLETE_ORDERED_DR_GROUPS" if recorded_dr else "ORIGINAL_COMPLETE_ORDERED_OPE_POINT_ROWS" if ope_point else "ORIGINAL_PRIVATE_ANALYTIC_NO_RESAMPLING" if analytic else "ORIGINAL_PRIVATE_EXECUTION_NO_RESAMPLING" if private_execution or quantum else "ORIGINAL_COMPLETE_PURGED_FOLD_PLAN" if held_out else "NO_RESAMPLING_FOR_SELECTED_DECLARED_TRIAL_LEDGER" if multiple else "ORIGINAL_FIXED_CONTIGUOUS_CSCV_SPLIT_PARTITION" if pbo else "NO_RESAMPLING_FOR_SELECTED_SHARPE_LEDGER_AND_MOMENTS" if sharpe else "ORIGINAL_COMPLETE_FAMILY_SPA_FIXED_SEED_STUDENTIZED_LOG_LOG_PLUS_ONE" if spa else "ORIGINAL_COMPLETE_FAMILY_STATIONARY_BOOTSTRAP_FIXED_SEED_PLUS_ONE" if reality else "ORIGINAL_STATIONARY_BOOTSTRAP_FIXED_SEED_TYPE7" if bootstrap else "NO_RESAMPLING_FOR_SELECTED_BERNOULLI_COUNTS" if wilson else "NO_RESAMPLING_FOR_SELECTED_CALIBRATION_DATASET" if calibration else "NO_RESAMPLING_FOR_SELECTED_LOG_LOSS_DATASET" if log_loss else "NO_RESAMPLING_FOR_SELECTED_BRIER_DATASET" if brier else
                                "NO_RESAMPLING_FOR_SELECTED_MIDPOINT"), "LP03_ASSEMBLY_RESAMPLING_PROFILE_UNSUPPORTED")
            family_ref = resampling["trial_family_id"]
            families = tuple(event for event in events if event["record_ref"] == family_ref)
            _native_require(len(families) == 1 and (families[0]["owner_id"], families[0]["record_kind"],
                families[0]["schema_id"], families[0]["schema_version"]) == ("QKU_COMPUTATION_CONTROL_PLANE",
                "EvidenceClaimPolicyV1", "QTT_LP03_CLAIM_POLICY_V1", "1.0")
                and family_ref == operation.envelope_entry[3].claim_policy_ref, "LP03_ASSEMBLY_ORIGINAL_TRIAL_FAMILY_REQUIRED")
            family = families[0]["values"].get("trial_family")
            _native_require(isinstance(family, Mapping) and set(family) == {"family_ref", "first_unrevealed_group_ordinal", "origin"}
                            and family["family_ref"] == family_ref and type(family["first_unrevealed_group_ordinal"]) is int
                            and family["first_unrevealed_group_ordinal"] > 0 and family["origin"] == scope.origin.value,
                            "LP03_ASSEMBLY_TRIAL_FAMILY_SHAPE")
            # Published identity metadata is acquired once per assembly. It is
            # not a claim that the 3,096 runtime parameter values are present.
            inventory_bound = sum(assembler._inventory_byte_bounds)
            _EvidenceControlBootstrapV1._room_v1(operation, owner_queries=2, record_reads=2,
                query_result_records=2, read_bytes=inventory_bound)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            _EvidenceControlBootstrapV1._charge_v1(operation, owner_queries=2)
            parameter_refs = canonical_st12f_parameter_value_refs_v1(parameter_resolver)
            formula_versions, implementation_versions = _evidence_snapshot_version_pins_v1()
            actual_bytes = len(deterministic_json(parameter_refs).encode("utf-8")) + len(
                deterministic_json((formula_versions, implementation_versions)).encode("utf-8"))
            _EvidenceControlBootstrapV1._charge_v1(operation, record_reads=2, query_result_records=2, read_bytes=actual_bytes)
            _native_require(actual_bytes == inventory_bound, "LP03_ASSEMBLY_ORIGINAL_INVENTORY_CHANGED")
            completed_wall, completed_mono, _ = _EvidenceControlBootstrapV1._check_current_v1(operation)
            def projected(ns):
                seconds, remainder = divmod(ns, 1_000_000_000)
                return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=remainder // 1000)
            values = dict(policy_values,
                decision_time=projected(scope.snapshot_decision_wall_ns), point_in_time_cutoff=projected(scope.snapshot_pit_cutoff_wall_ns),
                market_scope=(first_scope["market_scope_id"],), venue_scope=(first_scope["venue_scope_id"],),
                instrument_scope=(first_scope["instrument_or_contract_scope_id"],),
                formula_specification_versions=formula_versions, implementation_versions=implementation_versions,
                parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1", parameter_value_refs=parameter_refs,
                source_epochs={event["record_ref"]: event["source_epoch_id"] for event in events},
                random_seed_policy={"scenario_plan_ref": operation.plan.record_id, "master_seed": operation.plan.master_seed,
                                    "sampling_profile": operation.plan.sampling_profile},
                scenario_set_id=operation.plan.record_id, causation_id=operation.grant_record.record_id,
                correlation_id=operation.grant_record.correlation_ref, created_by=scope.assembler_principal,
                created_at=projected(completed_wall))
            snapshot = CanonicalReplayPaperInputSnapshotV1(**values)
            grant_ref = operation.grant_record.record_id
            package_ref = state.host.public_configuration.package_identity_ref
            for name in ("decision_time", "point_in_time_cutoff", "causation_id", "correlation_id", "created_by", "created_at"):
                lineage[name] = (grant_ref,)
            for name in ("market_scope", "venue_scope", "instrument_scope", "source_epochs"):
                lineage[name] = tuple(ref.record_id for ref in refs)
            for name in ("formula_specification_versions", "implementation_versions"):
                lineage[name] = (package_ref, "CP/implementation_registry.py")
            for name in ("parameter_policy_version", "parameter_value_refs"):
                lineage[name] = (package_ref, assembler._parameter_receipt.canonical_value_owner)
            for name in ("random_seed_policy", "scenario_set_id"):
                lineage[name] = (operation.plan.record_id,)
            common = {field.name: getattr(operation.grant_record, field.name) for field in fields(EvidenceRecordHeaderV1)
                      if field.name != "kind"}
            common.update(record_id=grant_ref + "::INPUT_ASSEMBLY", causation_ref=grant_ref,
                producing_owner="QKU_COMPUTATION_CONTROL_PLANE", producing_principal=scope.assembler_principal,
                source_lineage_refs=tuple(ref.record_id for ref in refs), created_wall_ns=completed_wall)
            # Preserve the complete six-clock roster as bounded canonical data.
            # The unchanged1.4 snapshot inventory and all original source facts
            # remain inside the original whole stored-spine4096-node admission.
            source_clock_rows=tuple(row for part in slices for row in part.original_native_clock_companions)
            source_clock_fields=(dict(source_clock_encoding="ORIGINAL_SIX_CLOCK_RECORDS_CANONICAL_JSON_V1",
                source_records_json=deterministic_json(dict(source_records=source_clock_rows)))
                if cashflow or recorded_dr or ope_point or private_execution or quantum or operation.envelope_entry[3].callback_pins
                else dict(source_records=source_clock_rows))
            record = EvidenceInputAssemblyRecordV1(**common,
                # The full typed snapshot retains all3096 parameter identities.
                # Match its existing frozen-body and enclosing storage1MiB cap;
                # source/frame defaults and the4096-node/depth guards stay intact.
                existing_snapshot_body=_evidence_canonical_object_v1(
                    deterministic_json(snapshot).encode("utf-8"),max_bytes=1048576),
                native_clock_companions=dict(decision_wall_ns=scope.snapshot_decision_wall_ns,
                    pit_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, created_wall_ns=completed_wall,
                    **source_clock_fields),
                ordered_field_lineage=tuple((field.name, lineage[field.name]) for field in fields(snapshot)),
                source_grant_refs=tuple(dict.fromkeys(ref for part in slices for ref in part.rights_refs)),
                owner_packet_refs=refs, registry_version_tuple=(("CanonicalReplayPaperInputSnapshotV1", INPUT_LOCK_CONTRACT_VERSION_V1),
                    ("ComputationParameterPolicyV1", "ST12F_PARAMETER_RESOURCE_ROW_V1")), actual_missing_fields=(),
                snapshot_origin=scope.origin, actual_assembly_times=(("started_wall_ns", started_wall),
                    ("completed_wall_ns", completed_wall), ("started_monotonic_ns", started_mono), ("completed_monotonic_ns", completed_mono)),
                assembly_grant_ref=grant_ref, preparation_ordinal=operation.grant_record.preparation_ordinal)
            result = object.__new__(EvidenceInputAssemblyOutcomeV1)
            result._operation, result._assembler, result._slices = operation, assembler, slices
            result._snapshot, result._record = snapshot, record
            result._resolved_inputs = resolved_inputs
            result._resolved_input_originals = resolved_originals
            result._source_originals = source_originals
            operation.input_assembly_outcome = result
            operation.input_assembly_members = (assembler, slices, snapshot, record, resolved_inputs,
                                                deterministic_json(record), deterministic_json(snapshot), deterministic_json(resolved_inputs),
                                                resolved_originals, source_originals)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            _require_original_input_assembly_outcome_v1(operation, result)
            return result
        except BaseException:
            operation.commit_state = "ASSEMBLY_FAILED_REQUIRES_AUDIT"
            raise
        finally:
            state.operation = None


def build_immutable_replay_paper_input_lock_v1(
    *,
    identity_token: str,
    asserted_input_lock_id: str,
    canonical_snapshot: CanonicalReplayPaperInputSnapshotV1,
) -> ImmutableReplayPaperInputLockV1:
    token = validated_st12f_identity_token_v1(identity_token)
    expected_lock_id = f"ST12F-LOCK::{token}"
    if asserted_input_lock_id != expected_lock_id:
        raise ContractValidationError(
            ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
            "caller lock text is only an equality assertion",
        )
    if type(canonical_snapshot) is not CanonicalReplayPaperInputSnapshotV1:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "input lock content must come from the exact canonical snapshot owner",
        )
    values = {
        field.name: getattr(canonical_snapshot, field.name)
        for field in fields(canonical_snapshot)
    }
    return ImmutableReplayPaperInputLockV1(
        input_lock_id=expected_lock_id,
        schema_version=INPUT_LOCK_SCHEMA_VERSION_V1,
        contract_version=INPUT_LOCK_CONTRACT_VERSION_V1,
        cohort_template_ids=ST12F_TEMPLATE_IDS_V1,
        expected_replay_result_contract_ids=ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
        expected_paper_result_contract_ids=ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
        **values,
    )


if (
    len(ST12F_TEMPLATE_IDS_V1) != 52
    or len(ST12F_REPLAY_RESULT_CONTRACT_IDS_V1) != 52
    or len(ST12F_PAPER_RESULT_CONTRACT_IDS_V1) != 52
    or len(set((*ST12F_REPLAY_RESULT_CONTRACT_IDS_V1, *ST12F_PAPER_RESULT_CONTRACT_IDS_V1))) != 104
    or len(fields(ImmutableReplayPaperInputLockV1)) != 33
):
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "ST12-F immutable lock denominators are not exact",
    )
