import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FormulaInputAdmissionClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    FreshnessError,
    InputAuthorityError,
    PointInTimeError,
    ReasonCode,
    UnitConversionError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    invoke_formula_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolverV1,
    OwnerValuePacketV1,
    RuntimeParameterValueResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    CUMULATIVE_PARAMETER_POLICIES,
    FamilyParameterPolicyCompilerV1,
    RUNTIME_PARAMETER_OWNER_BINDINGS,
)
import src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy as parameter_policy_module
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
    classify_point_in_time_semantics,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    ApplicableStackResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.unit_conversion import (
    ConversionIdentityV1,
    UnitBasisDescriptorV1,
    UnitConversionOwnerV1,
)


AS_OF = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)
STACK_ID = "STACK::MATH-01::MATH-02::V3_4"


def _scope() -> ComputationScopeV1:
    return ComputationScopeV1(
        market_scope_id="MARKET::ST12B",
        venue_scope_id="VENUE::ST12B",
        event_scope_id="EVENT::ST12B",
        instrument_or_contract_scope_id="CONTRACT::ST12B",
        mode_context_id="MODE_CONTEXT::CONTRACT_ONLY",
        input_snapshot_id="SNAPSHOT::ST12B::V1",
    )


def _implementation_pins(
    component_ids: tuple[str, ...],
) -> tuple[ImplementationVersionPinV1, ...]:
    return tuple(
        ImplementationVersionPinV1(
            math_spec_id=component_id,
            implementation_id=IMPLEMENTATION_REGISTRY[
                component_id
            ].contract.implementation_id,
        )
        for component_id in component_ids
    )


def _context(
    context_id: str = "CTX::ST12B",
    *,
    component_ids: tuple[str, ...] = ("MATH-01",),
    scope: ComputationScopeV1 | None = None,
    dependency_graph_id: str | None = None,
) -> ComputationExecutionContextV1:
    return ComputationExecutionContextV1(
        context_id=context_id,
        as_of=AS_OF,
        observed_at=AS_OF - timedelta(seconds=1),
        source_epoch_id="EPOCH::ST12B",
        input_version="V1",
        maximum_age=timedelta(days=1),
        scope=scope or _scope(),
        binding_profile_version="3.4",
        parameter_policy_version="3.4",
        implementation_versions=_implementation_pins(component_ids),
        dependency_graph_id=dependency_graph_id,
        dependency_graph_version=(
            "3.4" if dependency_graph_id is not None else None
        ),
    )


def _clocks() -> PointInTimeClocksV1:
    observed = AS_OF - timedelta(seconds=1)
    return PointInTimeClocksV1(
        observed_time=observed,
        effective_time=observed,
        available_time=observed,
        received_time=observed,
        processed_time=observed,
        as_of_time=AS_OF,
    )


def _formula_packets(
    math_id: str,
    *,
    context: ComputationExecutionContextV1,
    excluded_inputs: frozenset[str] = frozenset(),
    packet_namespace: str = "BASE",
) -> tuple[tuple[OwnerValuePacketV1, ...], dict[str, object]]:
    inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
    packets = tuple(
        OwnerValuePacketV1(
            packet_id=f"PACKET::{packet_namespace}::{binding.binding_id}",
            owner_id=binding.accepted_upstream_owner_id,
            packet_type=binding.accepted_packet_or_snapshot_type,
            schema_id=binding.schema_id,
            schema_version=binding.schema_version,
            context_id=context.context_id,
            scope=context.scope,
            source_epoch_id=context.source_epoch_id,
            input_version=context.input_version,
            clocks=_clocks(),
            ttl=timedelta(days=1),
            values={binding.exact_field_path: inputs[binding.input_name]},
            authorized_binding_ids=(binding.binding_id,),
            producer_receipt_id=f"RECEIPT::{binding.binding_id}",
            producer_receipt_type=binding.producer_receipt_type,
            source_state_and_claim_lineage=(
                binding.source_state_and_claim_lineage
            ),
            provider_sequence=1,
            revision=1,
        )
        for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        if binding.input_name not in excluded_inputs
    )
    assertions = {
        name: value
        for name, value in inputs.items()
        if name not in excluded_inputs
    }
    return packets, assertions


def test_execution_context_admission_matrix() -> None:
    resolved_input_count = 0
    admission_classes = set()

    for math_id in FORMULA_INPUT_AUTHORITY_BY_MATH_ID:
        context = _context(
            context_id=f"CTX::ST12B::{math_id}",
            component_ids=(math_id,),
        )
        packets, assertions = _formula_packets(math_id, context=context)
        resolution = FormulaInputResolverV1.resolve(
            math_id,
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions=assertions,
        )
        invoke_formula_v34(math_id, resolution.authoritative_values)
        assert resolution.execution_context is context
        resolved_input_count += len(resolution.inputs)
        admission_classes.update(
            binding.admission_class
            for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        )

    assert resolved_input_count == 142
    assert admission_classes == set(FormulaInputAdmissionClassV1)
    assert all(
        binding.admission_class.value == binding.current_admitted_mode
        for bindings in FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values()
        for binding in bindings
    )

    context = _context()
    packets, assertions = _formula_packets("MATH-01", context=context)
    registry = CanonicalOwnerPacketRegistryV1(packets)
    exact = FormulaInputResolverV1.resolve(
        "MATH-01",
        context=context,
        owner_registry=registry,
        caller_assertions=assertions,
    )
    assert exact.execution_context is context

    for field_name in (
        "market_scope_id",
        "venue_scope_id",
        "event_scope_id",
        "instrument_or_contract_scope_id",
        "mode_context_id",
        "input_snapshot_id",
    ):
        mismatched_scope = replace(
            context.scope,
            **{
                field_name: (
                    f"{getattr(context.scope, field_name)}::MISMATCH"
                )
            },
        )
        with pytest.raises(InputAuthorityError) as mismatch:
            FormulaInputResolverV1.resolve(
                "MATH-01",
                context=replace(context, scope=mismatched_scope),
                owner_registry=registry,
            )
        assert mismatch.value.reason_code is ReasonCode.INPUT_SCOPE_MISMATCH

    with pytest.raises(PointInTimeError) as wrong_as_of:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=replace(context, as_of=AS_OF + timedelta(seconds=1)),
            owner_registry=registry,
        )
    assert wrong_as_of.value.reason_code is ReasonCode.POINT_IN_TIME_VIOLATION

    with pytest.raises(FreshnessError) as wrong_epoch:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=replace(
                context,
                source_epoch_id="EPOCH::ST12B::MISMATCH",
            ),
            owner_registry=registry,
        )
    assert wrong_epoch.value.reason_code is ReasonCode.SOURCE_EPOCH_STALE

    with pytest.raises(InputAuthorityError) as wrong_input_version:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=replace(context, input_version="V2"),
            owner_registry=registry,
        )
    assert (
        wrong_input_version.value.reason_code
        is ReasonCode.INPUT_SCOPE_MISMATCH
    )

    alternate_scope = replace(
        context.scope,
        market_scope_id="MARKET::ST12B::ALTERNATE",
    )
    alternate_context = replace(context, scope=alternate_scope)
    alternate_packets, _ = _formula_packets(
        "MATH-01",
        context=alternate_context,
        packet_namespace="ALTERNATE",
    )
    first_binding = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-01"][0]
    alternate_packets = (
        replace(
            alternate_packets[0],
            values={first_binding.exact_field_path: "0.52"},
        ),
        *alternate_packets[1:],
    )
    scoped_registry = CanonicalOwnerPacketRegistryV1(
        (*packets, *alternate_packets)
    )
    base_resolution = FormulaInputResolverV1.resolve(
        "MATH-01",
        context=context,
        owner_registry=scoped_registry,
    )
    alternate_resolution = FormulaInputResolverV1.resolve(
        "MATH-01",
        context=alternate_context,
        owner_registry=scoped_registry,
    )
    assert base_resolution.authoritative_values["contract_price"] == Decimal(
        "0.47"
    )
    assert alternate_resolution.authoritative_values[
        "contract_price"
    ] == Decimal("0.52")
    assert set(base_resolution.packet_refs).isdisjoint(
        alternate_resolution.packet_refs
    )


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    (
        ({"owner_id": "NonCanonicalOwnerV1"}, ReasonCode.INPUT_OWNER_MISMATCH),
        ({"source_conflict": True}, ReasonCode.SOURCE_CONFLICT),
    ),
)
def test_owner_and_source_conflicts_fail_closed(
    mutation: dict[str, object],
    reason_code: ReasonCode,
) -> None:
    context = _context()
    packets, assertions = _formula_packets("MATH-01", context=context)
    packets = (replace(packets[0], **mutation), *packets[1:])

    with pytest.raises(InputAuthorityError) as caught:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions=assertions,
        )
    assert caught.value.reason_code is reason_code


def test_caller_value_and_stale_packet_cannot_override_owner_truth() -> None:
    context = _context()
    packets, assertions = _formula_packets("MATH-01", context=context)

    with pytest.raises(InputAuthorityError) as conflict:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions={**assertions, "contract_price": "0.48"},
        )
    assert conflict.value.reason_code is ReasonCode.INPUT_VALUE_CONFLICT

    old = AS_OF - timedelta(days=2)
    stale_clocks = PointInTimeClocksV1(
        observed_time=old,
        effective_time=old,
        available_time=old,
        received_time=old,
        processed_time=old,
        as_of_time=AS_OF,
    )
    stale_packets = (replace(packets[0], clocks=stale_clocks), *packets[1:])
    with pytest.raises(FreshnessError) as stale:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(stale_packets),
        )
    assert stale.value.reason_code is ReasonCode.FRESHNESS_VIOLATION


def test_five_point_in_time_classes_have_one_central_policy() -> None:
    semantic_cases = {
        "one current observation": PointInTimeFieldClassV1.OBSERVATION,
        "scheduled fact; effective time may be later": (
            PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT
        ),
        "future revisions forbidden": PointInTimeFieldClassV1.REVISION,
        "event_outcome effective state": PointInTimeFieldClassV1.EVENT_OUTCOME,
        "settlement state": PointInTimeFieldClassV1.SETTLEMENT,
    }
    context = _context()

    assert {
        classify_point_in_time_semantics(text)
        for text in semantic_cases
    } == set(PointInTimeFieldClassV1)
    for index, (text, field_class) in enumerate(semantic_cases.items()):
        clocks = _clocks()
        if field_class is PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT:
            clocks = replace(clocks, effective_time=AS_OF + timedelta(days=1))
        receipt = PointInTimePolicyV1.validate(
            receipt_id=f"PIT::{index}",
            field_class=classify_point_in_time_semantics(text),
            clocks=clocks,
            context=context,
        )
        assert receipt.admitted
        assert receipt.field_class is field_class

    with pytest.raises(PointInTimeError) as future_outcome:
        PointInTimePolicyV1.validate(
            receipt_id="PIT::FUTURE_OUTCOME",
            field_class=PointInTimeFieldClassV1.EVENT_OUTCOME,
            clocks=replace(
                _clocks(),
                effective_time=AS_OF + timedelta(microseconds=1),
            ),
            context=context,
        )
    assert (
        future_outcome.value.reason_code
        is ReasonCode.POINT_IN_TIME_VIOLATION
    )

    _assert_f12_exact_utc()
    _assert_f14_storage_time_domain()
    _assert_f12_v1_predicates()
    _assert_f12_v1_retention()
    _assert_f12_v1_context_and_gate()
    _assert_f12_v1_typed_gate()


def test_runtime_parameter_hold_and_terminal_application_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("CTX::RUNTIME_PARAMETER")
    parameter_id = "ST10-PARAM::2197"
    binding = RUNTIME_PARAMETER_OWNER_BINDINGS[parameter_id]
    assert len(RUNTIME_PARAMETER_OWNER_BINDINGS) == 190
    assert all(
        row.value_state == "RUNTIME_BINDING_REQUIRED"
        and row.raw["current_computation_admission"]
        == "BLOCKED_PENDING_ACCEPTED_UPSTREAM_VALUE_PACKET"
        and all(
            isinstance(value, str) and value
            for value in (
                row.accepted_upstream_owner_id,
                row.accepted_packet_or_snapshot_type,
                row.schema_id,
                row.schema_version,
                row.producer_receipt_type,
                row.raw["source_state_and_claim_lineage"],
            )
        )
        for row in RUNTIME_PARAMETER_OWNER_BINDINGS.values()
    )
    packet = OwnerValuePacketV1(
        packet_id=f"PACKET::{binding.binding_id}",
        owner_id=binding.accepted_upstream_owner_id,
        packet_type=binding.accepted_packet_or_snapshot_type,
        schema_id=binding.schema_id,
        schema_version=binding.schema_version,
        context_id=context.context_id,
        scope=context.scope,
        source_epoch_id=context.source_epoch_id,
        input_version=context.input_version,
        clocks=_clocks(),
        ttl=timedelta(days=1),
        values={binding.exact_field_path: True},
        authorized_binding_ids=(binding.binding_id,),
        producer_receipt_id=f"RECEIPT::{binding.binding_id}",
        producer_receipt_type=binding.producer_receipt_type,
        source_state_and_claim_lineage=str(
            binding.raw["source_state_and_claim_lineage"]
        ),
        provider_sequence=1,
        revision=1,
    )
    resolution = RuntimeParameterValueResolverV1.resolve(
        parameter_id,
        context=context,
        owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
        caller_assertion=True,
    )

    assert resolution.resolved.value is True
    assert resolution.execution_context is context
    assert (
        resolution.resolved.owner_id == binding.accepted_upstream_owner_id
    )
    with pytest.raises(InputAuthorityError) as conflict:
        RuntimeParameterValueResolverV1.resolve(
            parameter_id,
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
            caller_assertion=False,
        )
    assert conflict.value.reason_code is ReasonCode.INPUT_VALUE_CONFLICT

    for mutation, reason_code in (
        (
            {"owner_id": "NonCanonicalRuntimeOwnerV1"},
            ReasonCode.INPUT_OWNER_MISMATCH,
        ),
        (
            {"schema_version": "9.9.9"},
            ReasonCode.INPUT_SCHEMA_MISMATCH,
        ),
    ):
        with pytest.raises(InputAuthorityError) as rejected:
            RuntimeParameterValueResolverV1.resolve(
                parameter_id,
                context=context,
                owner_registry=CanonicalOwnerPacketRegistryV1(
                    (replace(packet, **mutation),)
                ),
            )
        assert rejected.value.reason_code is reason_code

    with pytest.raises(InputAuthorityError) as wrong_scope:
        RuntimeParameterValueResolverV1.resolve(
            parameter_id,
            context=replace(
                context,
                scope=replace(
                    context.scope,
                    venue_scope_id="VENUE::ST12B::MISMATCH",
                ),
            ),
            owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
        )
    assert wrong_scope.value.reason_code is ReasonCode.INPUT_SCOPE_MISMATCH

    corrupted_raw = dict(binding.raw)
    corrupted_raw["current_computation_admission"] = "UNKNOWN_ADMISSION"
    corrupted_binding = replace(
        binding,
        raw=MappingProxyType(corrupted_raw),
    )
    corrupted_population = dict(RUNTIME_PARAMETER_OWNER_BINDINGS)
    corrupted_population[parameter_id] = corrupted_binding
    with monkeypatch.context() as local_patch:
        local_patch.setattr(
            parameter_policy_module,
            "RUNTIME_PARAMETER_OWNER_BINDINGS",
            MappingProxyType(corrupted_population),
        )
        with pytest.raises(InputAuthorityError) as invalid_admission:
            RuntimeParameterValueResolverV1.resolve(
                parameter_id,
                context=context,
                owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
            )
    assert (
        invalid_admission.value.reason_code
        is ReasonCode.PARAMETER_BINDING_MISMATCH
    )

    compiled = FamilyParameterPolicyCompilerV1.compile(
        "FAMILY_POLICY::CM-05A2"
    )
    assert compiled.parameter_ids == ("ST10-PARAM::0973",)
    assert compiled.application_receipts[0].ultimate_owner == (
        CUMULATIVE_PARAMETER_POLICIES[
            "ST10-PARAM::0973"
        ].ultimate_owner
    )
    assert compiled.application_receipts[0].no_effect_authority is True
    assert "NOT_TERMINAL_CONSUMER" in compiled.compiler_role


def test_unit_conversion_and_dependency_stack_propagate_actual_value() -> None:
    context = _context(
        "CTX::STACK",
        component_ids=("MATH-01", "MATH-02"),
        dependency_graph_id=STACK_ID,
    )
    source = UnitBasisDescriptorV1(
        "Decimal",
        "scalar",
        "dimensionless",
        "winning payout-normalized probability",
    )
    target = UnitBasisDescriptorV1(
        "float64",
        "scalar",
        "probability points",
        "unit interval",
    )
    converted, receipt = UnitConversionOwnerV1.convert(
        conversion_id=(
            ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
        ),
        value=Decimal("0.47"),
        source=source,
        target=target,
        context=context,
        receipt_id="CONVERSION::TEST",
    )
    assert converted == 0.47
    assert receipt.source_value == Decimal("0.47")
    with pytest.raises(UnitConversionError):
        UnitConversionOwnerV1.convert(
            conversion_id=(
                ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
            ),
            value=Decimal("0.47"),
            source=replace(source, basis="wrong basis"),
            target=target,
            context=context,
            receipt_id="CONVERSION::FORBIDDEN",
        )

    math_01_packets, math_01_assertions = _formula_packets(
        "MATH-01", context=context
    )
    math_02_packets, math_02_assertions = _formula_packets(
        "MATH-02",
        context=context,
        excluded_inputs=frozenset({"market_implied_probability"}),
    )
    execution = ApplicableStackResolverV1.execute(
        stack_id=STACK_ID,
        component_ids=("MATH-01", "MATH-02"),
        context=context,
        owner_registry=CanonicalOwnerPacketRegistryV1(
            (*math_01_packets, *math_02_packets)
        ),
        caller_assertions_by_math_id={
            "MATH-01": math_01_assertions,
            "MATH-02": math_02_assertions,
        },
    )
    assert execution.component_outputs == (Decimal("0.47"), 0.14)
    assert execution.execution_context is context
    assert all(
        resolution.execution_context is context
        for resolution in execution.component_inputs
    )
    assert execution.dependency_packet.scope is context.scope
    assert execution.dependency_packet.context_id == context.context_id
    assert execution.dependency_packet.clocks.as_of_time == context.as_of
    assert (
        execution.dependency_packet.source_epoch_id
        == context.source_epoch_id
    )
    assert execution.dependency_packet.input_version == context.input_version
    assert (
        execution.dependency_packet.scope.input_snapshot_id
        == context.scope.input_snapshot_id
    )
    assert execution.conversion_receipt.execution_context is context
    assert execution.propagation_receipt.execution_context is context
    assert execution.propagation_receipt.producer_value == Decimal("0.47")
    assert execution.propagation_receipt.consumer_value == 0.47
    assert execution.propagation_receipt.mutation_propagates is True
    assert execution.conversion_receipt.no_authority_flag is True
    assert execution.propagation_receipt.no_authority_flag is True
    assert execution.no_authority_flag is True


def _assert_f12_exact_utc() -> None:
    """Frozen UTC vectors and integer reconstruction, without a source import."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
        _native_ident, _native_scalar, _native_text,
        _native_utc_nanoseconds, _native_utc_receipt_pair, parse_utc,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
    )

    def rejected(operation, detail="UTC_NANOSECONDS", *, source_label=""):
        with pytest.raises(ContractValidationError) as caught:
            operation()
        assert type(caught.value) is ContractValidationError
        assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
        assert caught.value.args == (f"{ReasonCode.INVALID_CONTRACT}: {detail}",)

    # Each expected companion is independent literal/arithmetic fixture data.
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    vectors = (
        ("1970-01-01T00:00:00Z", 0),
        ("1970-01-01T01:00:00.000000001+01:00", 1),
        ("1969-12-31T23:00:00.000000001-01:00", 1),
        ("1969-12-31T23:59:59.999999999Z", -1),
        ("1970-01-01T23:59:00+23:59", 0),
        ("1969-12-31T00:01:00-23:59", 0),
        ("0001-01-01T00:00:00Z", -62135596800000000000),
        ("9999-12-31T23:59:59.999999999Z", 253402300799999999999),
        ("2000-02-29T00:00:00Z", 951782400000000000),
    )

    def check_pair(source, expected_ns):
        floor_us, remainder = divmod(expected_ns, 1000)
        projected = epoch + timedelta(microseconds=floor_us)
        stamp = (
            f"{projected.year:04d}-{projected.month:02d}-{projected.day:02d}T"
            f"{projected.hour:02d}:{projected.minute:02d}:{projected.second:02d}"
        )
        expected = {
            "source_text": source,
            "utc_ns_text": str(expected_ns),
            "canonical_utc": stamp + f".{expected_ns % 1_000_000_000:09d}Z",
            "receipt_utc_floor": projected.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            "nanosecond_remainder": remainder,
        }
        assert _native_utc_nanoseconds(source) == expected_ns
        pair = _native_utc_receipt_pair(source)
        assert pair == expected
        assert type(pair["nanosecond_remainder"]) is int
        assert 0 <= remainder <= 999
        assert floor_us * 1000 + remainder == int(pair["utc_ns_text"])

    for source, expected_ns in vectors:
        check_pair(source, expected_ns)
    for remainder in range(1000):
        check_pair(f"1970-01-01T00:00:00.{remainder:09d}Z", remainder)
        check_pair(f"1969-12-31T23:59:59.{999999000 + remainder:09d}Z", -1000 + remainder)
    for digits in range(1, 10):
        source = "1970-01-01T00:00:00." + "1" * digits + "Z"
        check_pair(source, int(("1" * digits).ljust(9, "0")))

    class TextSubclass(str):
        pass

    invalid = (
        None, True, 0, 1.0, epoch, TextSubclass("1970-01-01T00:00:00Z"),
        "", "1970-01-01 00:00:00Z", "1970-01-01T00:00:00z",
        "1970-01-01T00:00:00-00:00", "1970-01-01T00:00:00+24:00",
        "1970-01-01T00:00:00+00:60", "1970-01-01T00:00:60Z",
        "1970-01-01T24:00:00Z", "1970-01-01T00:60:00Z",
        "1970-01-01T24:00:00.000000001Z", "1970-01-01T24:00:00+01:00",
        "9999-12-31T24:00:00Z", "1970-01-01T25:00:00Z",
        "1970-01-01T00:00:00.1234567890Z", "1970-01-01T00:00:00.Z",
        "1900-02-29T00:00:00Z", "2026-02-30T00:00:00Z",
        "0000-01-01T00:00:00Z", "10000-01-01T00:00:00Z",
        "0001-01-01T00:00:00+00:01", "9999-12-31T23:59:59-00:01",
        " 1970-01-01T00:00:00Z", "1970-01-01T00:00:00Z\n",
        "\uff11\uff19\uff17\uff10-01-01T00:00:00Z",
    )
    for value in invalid:
        rejected(lambda value=value: _native_utc_nanoseconds(value), source_label=repr(value))
        rejected(lambda value=value: _native_utc_receipt_pair(value), source_label=repr(value))
    for value in (None, "", " x", "x ", "x\x00", "x\x7f", "x\ud800", TextSubclass("x")):
        rejected(lambda value=value: _native_text(value), "TEXT")
    for value in ("x" * 257, "x y", "x\x85y"):
        rejected(lambda value=value: _native_ident(value), "IDENTITY")
    assert _native_ident("x" * 256) == "x" * 256
    for value in (0, 1, "true", None):
        rejected(lambda value=value: _native_scalar(value, "bool"), "BOOLEAN")
    rejected(lambda: _native_scalar(1, "integer"), "UNREGISTERED_SCALAR")
    assert _native_scalar(True, "bool") is True
    assert _native_scalar(False, "bool") is False
    # General compatibility parsing remains broader than the exact text port.
    assert parse_utc("1970-01-01 00:00:00+00:00", field_name="fixture") == epoch
    assert parse_utc(epoch, field_name="fixture") == epoch
    assert parse_utc("1970-01-01T24:00:00Z", field_name="fixture") == epoch + timedelta(days=1)


def _assert_f12_v1_predicates() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        _native_retail_pit_receipt_bridge,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
    )

    cutoff = "2026-07-29T20:00:00.000000500Z"
    future = "2026-07-29T20:00:00.000000501Z"
    clocks = {
        name: "2026-07-29T19:59:59.123456789Z"
        for name in PointInTimePolicyV1.CHECKED_CLOCKS
    }
    clocks["as_of_time"] = cutoff

    def bridge(values, field_class="OBSERVATION", prior=None):
        return _native_retail_pit_receipt_bridge(
            values, field_class=field_class, context_as_of=cutoff,
            prior_revision_available_time=prior,
        )

    def reject(values, detail, field_class="OBSERVATION", prior=None):
        with pytest.raises(PointInTimeError) as caught:
            bridge(values, field_class, prior)
        assert type(caught.value) is PointInTimeError
        assert caught.value.reason_code is ReasonCode.POINT_IN_TIME_VIOLATION
        assert caught.value.args == (f"{ReasonCode.POINT_IN_TIME_VIOLATION}: {detail}",)
        assert type(caught.value.__cause__) is ContractValidationError

    result = bridge(clocks)
    assert set(result) == {
        "state", "field_class", "clock_pairs", "context_pair", "prior_revision_pair",
        "datetime_only_is_lossless", "exact_ns_consumer_required", "source_accepted",
        "runtime_effect_authorized", "receipt_emitted", "full_pit_v3_admitted",
    }
    assert result["state"] == "EXACT_CLOCK_RELATIONS_CHECKED_NOT_ADMISSION"
    assert result["field_class"] == "OBSERVATION"
    assert set(result["clock_pairs"]) == set(clocks)
    assert result["context_pair"]["source_text"] == cutoff
    assert result["prior_revision_pair"] is None
    assert result["datetime_only_is_lossless"] is False
    assert result["exact_ns_consumer_required"] is True
    for flag in ("source_accepted", "runtime_effect_authorized", "receipt_emitted", "full_pit_v3_admitted"):
        assert result[flag] is False
    for field, detail in (
        ("as_of_time", "PIT_CONTEXT_AS_OF_MISMATCH"),
        ("observed_time", "PIT_OBSERVED_AFTER_DECISION"),
        ("available_time", "PIT_AVAILABLE_AFTER_DECISION"),
        ("received_time", "PIT_RECEIVED_AFTER_DECISION"),
        ("processed_time", "PIT_PROCESSED_AFTER_DECISION"),
    ):
        reject({**clocks, field: future}, detail)
    unordered = {
        **clocks, "observed_time": "2026-07-29T20:00:00.000000002Z",
        "available_time": "2026-07-29T20:00:00.000000001Z",
        "received_time": cutoff, "processed_time": cutoff,
    }
    reject(unordered, "PIT_CLOCK_ORDER_INVALID")
    for field_class in ("EVENT_OUTCOME", "SETTLEMENT"):
        reject({**clocks, "effective_time": future}, "PIT_EFFECTIVE_AFTER_DECISION", field_class)
    scheduled = bridge({**clocks, "effective_time": future}, "SCHEDULED_EFFECTIVE_FACT")
    assert scheduled["clock_pairs"]["effective_time"]["source_text"] == future
    reject(clocks, "PIT_REVISION_LEAKAGE", "REVISION", future)
    reject(clocks, "PIT_REVISION_LEAKAGE", "REVISION", "2026-07-29T19:59:59.123456790Z")
    revision = bridge(clocks, "REVISION", "2026-07-29T19:59:59.123456788Z")
    assert revision["prior_revision_pair"]["nanosecond_remainder"] == 788
    for field_class in PointInTimeFieldClassV1:
        assert bridge(clocks, field_class.value)["field_class"] == field_class.value
        if field_class is not PointInTimeFieldClassV1.REVISION:
            reject(clocks, "PIT_UNUSED_PRIOR_REVISION", field_class.value, cutoff)
    reject(clocks, "PIT_FIELD_CLASS", PointInTimeFieldClassV1.OBSERVATION)
    reject({**clocks, "extra": cutoff}, "NATIVE_FIELDS")
    reject({name: value for name, value in clocks.items() if name != "received_time"}, "NATIVE_FIELDS")
    reject({**clocks, "received_time": AS_OF}, "UTC_NANOSECONDS")
    reject(clocks, "UTC_NANOSECONDS", "REVISION", True)
    zero = {name: "2026-07-29T20:00:00Z" for name in clocks}
    lossless = _native_retail_pit_receipt_bridge(
        zero, field_class="OBSERVATION", context_as_of="2026-07-29T20:00:00Z",
    )
    assert lossless["datetime_only_is_lossless"] is True
    assert lossless["exact_ns_consumer_required"] is False


def _f12_v1_fixture():
    context = _context(
        component_ids=("MATH-01", "MATH-02"), dependency_graph_id=STACK_ID,
    )
    cutoff = "2026-07-29T20:00:00.000000500Z"
    clocks = {
        name: "2026-07-29T19:59:59.123456789Z"
        for name in PointInTimePolicyV1.CHECKED_CLOCKS
    }
    clocks["as_of_time"] = cutoff
    return context, {
        "clocks": clocks, "field_class": PointInTimeFieldClassV1.OBSERVATION,
        "context": context, "context_as_of": cutoff,
        "context_observed_at": "2026-07-29T19:59:59.000000001Z",
        "receipt_id": "F12::V1::" + "x" * 300,
    }


def _assert_f12_v1_retention() -> None:
    from copy import deepcopy
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
        ComputationContextKeyV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        ExactPITCompositionV1, compose_exact_pit_v1, restore_exact_pit_composition_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        deterministic_json,
    )

    context, arguments = _f12_v1_fixture()
    composed = compose_exact_pit_v1(**arguments)
    payload = composed.to_payload()
    assert composed.typed_check_receipt.admitted is True
    assert composed.typed_check_receipt.receipt_id == arguments["receipt_id"]
    assert type(composed.clock_projection) is PointInTimeClocksV1
    assert composed.clock_projection.as_of_time == context.as_of
    assert not isinstance(composed, (ComputationContextKeyV1, PointInTimeClocksV1, OwnerValuePacketV1))
    assert set(payload) == {"format", "kind", "receipt_id", "request", "companion", "context_binding"}
    assert payload["format"] == "QTT_F12_EXACT_COMPOSITION_V1"
    assert payload["kind"] == "V1"
    assert payload["request"]["context_as_of"] == arguments["context_as_of"]
    assert payload["request"]["context_observed_at"] == arguments["context_observed_at"]
    assert payload["context_binding"]["context_type"] == "ComputationExecutionContextV1"
    assert len(payload["context_binding"]["scope"]) == 6
    assert len(payload["context_binding"]["implementation_versions"]) == 2
    decoded = json.loads(deterministic_json(payload))
    restored = restore_exact_pit_composition_v1(decoded, context=context)
    assert restored.to_payload() == payload
    assert restored.typed_check_receipt == composed.typed_check_receipt
    assert restored.clock_projection == composed.clock_projection
    for flag in ("source_accepted", "runtime_effect_authorized", "receipt_emitted", "full_pit_v3_admitted"):
        assert restored.companion["bridge"][flag] is False
    with pytest.raises(ContractValidationError, match="F12_FACTORY_REQUIRED"):
        ExactPITCompositionV1()
    with pytest.raises(TypeError):
        composed.request["clocks"]["observed_time"] = "tampered"
    with pytest.raises(TypeError):
        composed.companion["bridge"]["clock_pairs"]["observed_time"]["nanosecond_remainder"] = 0
    with pytest.raises((AttributeError, TypeError)):
        composed.kind = "V3"
    with pytest.raises(InputAuthorityError):
        CanonicalOwnerPacketRegistryV1((composed,))
    altered_copy = composed.to_payload()
    altered_copy["request"]["clocks"]["observed_time"] = "tampered"
    assert composed.to_payload() == payload

    bad_values = []
    missing = deepcopy(payload)
    del missing["companion"]
    bad_values.append(missing)
    forged = deepcopy(payload)
    forged["companion"]["bridge"]["source_accepted"] = True
    bad_values.append(forged)
    extra = deepcopy(payload)
    extra["extra"] = False
    bad_values.append(extra)
    for field, value in (
        ("source_text", "2026-07-29T19:59:59.123456788Z"),
        ("utc_ns_text", "0"), ("canonical_utc", "tampered"),
        ("receipt_utc_floor", "tampered"), ("nanosecond_remainder", 788),
    ):
        changed = deepcopy(payload)
        changed["companion"]["bridge"]["clock_pairs"]["observed_time"][field] = value
        bad_values.append(changed)
    for bad in bad_values:
        with pytest.raises(ContractValidationError):
            restore_exact_pit_composition_v1(bad, context=context)
    # Equality of bool and int must not authenticate an altered remainder.
    zero_args = {
        **arguments,
        "clocks": {name: "2026-07-29T19:59:59Z" for name in PointInTimePolicyV1.CHECKED_CLOCKS},
        "context_as_of": "2026-07-29T20:00:00Z",
        "context_observed_at": "2026-07-29T19:59:59Z",
    }
    zero_args["clocks"]["as_of_time"] = zero_args["context_as_of"]
    zero_payload = compose_exact_pit_v1(**zero_args).to_payload()
    boolean_remainder = deepcopy(zero_payload)
    boolean_remainder["companion"]["context_observed_pair"]["nanosecond_remainder"] = False
    assert boolean_remainder == zero_payload
    with pytest.raises(ContractValidationError, match="F12_COMPANION_MISMATCH"):
        restore_exact_pit_composition_v1(boolean_remainder, context=context)


def _assert_f12_v1_context_and_gate() -> None:
    from dataclasses import fields
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
        ComputationContextKeyV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import point_in_time as pit

    context, arguments = _f12_v1_fixture()
    payload = pit.compose_exact_pit_v1(**arguments).to_payload()
    changes = [
        replace(context, context_id="DIFFERENT"),
        replace(context, source_epoch_id="DIFFERENT"),
        replace(context, input_version="DIFFERENT"),
        replace(context, maximum_age=timedelta(hours=1)),
        replace(context, binding_profile_version="DIFFERENT"),
        replace(context, parameter_policy_version="DIFFERENT"),
        replace(context, dependency_graph_id="DIFFERENT"),
        replace(context, dependency_graph_version="DIFFERENT"),
        replace(context, implementation_versions=tuple(reversed(context.implementation_versions))),
        replace(context, implementation_versions=(
            replace(context.implementation_versions[0], implementation_id="DIFFERENT"),
            context.implementation_versions[1],
        )),
    ]
    for name in (
        "market_scope_id", "venue_scope_id", "event_scope_id",
        "instrument_or_contract_scope_id", "mode_context_id", "input_snapshot_id",
    ):
        changes.append(replace(context, scope=replace(context.scope, **{name: "DIFFERENT"})))
    for changed in changes:
        with pytest.raises(ContractValidationError, match="F12_CONTEXT_BINDING_MISMATCH"):
            pit.restore_exact_pit_composition_v1(payload, context=changed)
    for change in (
        {"context": replace(context, as_of=AS_OF + timedelta(microseconds=1))},
        {"context_observed_at": "2026-07-29T19:59:59.000001001Z"},
    ):
        with pytest.raises(ContractValidationError, match="F12_CONTEXT_PROJECTION_MISMATCH"):
            pit.compose_exact_pit_v1(**{**arguments, **change})
    with pytest.raises(ContractValidationError, match="F12_FIELD_CLASS_TYPE"):
        pit.compose_exact_pit_v1(**{**arguments, "field_class": "OBSERVATION"})
    with pytest.raises(ContractValidationError, match="F12_CONTEXT_TYPE"):
        pit.compose_exact_pit_v1(**{**arguments, "context": object()})
    for receipt_id in ("", " id", "id\n", True):
        with pytest.raises(PointInTimeError, match="F12_RECEIPT_ID_INVALID"):
            pit.compose_exact_pit_v1(**{**arguments, "receipt_id": receipt_id})

    class DurationSubclass(timedelta):
        pass

    with pytest.raises(ContractValidationError, match="F12_CONTEXT_DURATION_TYPE"):
        pit.compose_exact_pit_v1(**{
            **arguments, "context": replace(context, maximum_age=DurationSubclass(days=1)),
        })
    tight = replace(context, observed_at=AS_OF, maximum_age=timedelta(microseconds=1))
    for as_of_text, observed_text, typed_context, reason, detail in (
        ("2026-07-29T20:00:00.000000000Z", "2026-07-29T20:00:00.000000001Z",
         tight, ReasonCode.FUTURE_CONTEXT, "F12_CONTEXT_OBSERVED_AFTER_CUTOFF"),
        ("2026-07-29T20:00:00.000001001Z", "2026-07-29T20:00:00.000000000Z",
         replace(tight, as_of=AS_OF + timedelta(microseconds=1)),
         ReasonCode.STALE_CONTEXT, "F12_EXACT_CONTEXT_STALE"),
    ):
        with pytest.raises(ContractValidationError) as caught:
            pit.compose_exact_pit_v1(**{
                **arguments, "context": typed_context, "context_as_of": as_of_text,
                "context_observed_at": observed_text,
                "clocks": {**arguments["clocks"], "as_of_time": as_of_text},
            })
        assert caught.value.reason_code is reason
        assert caught.value.args == (f"{reason}: {detail}",)
    basic = ComputationContextKeyV1(
        "BASIC", context.as_of, context.observed_at, "EPOCH", "V1", timedelta(days=1),
    )
    basic_result = pit.compose_exact_pit_v1(**{**arguments, "context": basic})
    assert basic_result.context_binding["context_type"] == "ComputationContextKeyV1"
    assert pit.restore_exact_pit_composition_v1(
        basic_result.to_payload(), context=basic,
    ).to_payload() == basic_result.to_payload()
    assert tuple(f.name for f in fields(ComputationContextKeyV1)) == (
        "context_id", "as_of", "observed_at", "source_epoch_id", "input_version", "maximum_age",
    )
    assert tuple(f.name for f in fields(PointInTimeClocksV1)) == PointInTimePolicyV1.CHECKED_CLOCKS


def _assert_f12_v1_typed_gate() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import point_in_time as pit

    context, arguments = _f12_v1_fixture()
    original = pit.PointInTimePolicyV1.validate
    calls = []
    def checked_gate(**kwargs):
        calls.append(kwargs)
        assert type(kwargs["clocks"]) is PointInTimeClocksV1
        assert all(type(getattr(kwargs["clocks"], name)) is datetime for name in PointInTimePolicyV1.CHECKED_CLOCKS)
        return original(**kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pit.PointInTimePolicyV1, "validate", staticmethod(checked_gate))
        pit.compose_exact_pit_v1(**arguments)
    assert len(calls) == 1
    assert calls[0]["context"] is context
    assert calls[0]["receipt_id"] == arguments["receipt_id"]
    sentinel = PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "TYPED_GATE_FIXTURE")
    def rejected_gate(**kwargs):
        raise sentinel
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pit.PointInTimePolicyV1, "validate", staticmethod(rejected_gate))
        with pytest.raises(PointInTimeError) as caught:
            pit.compose_exact_pit_v1(**arguments)
        assert caught.value is sentinel


def _assert_f14_storage_time_domain():
    from datetime import UTC, datetime, timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _f14_native_time_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PointInTimeError
    origin = datetime(1970, 1, 1, tzinfo=UTC)
    base = datetime(2026, 9, 13, 12, 34, 56, tzinfo=UTC)
    count = 0
    for minutes in range(-1439, 1440):
        hour, minute = divmod(abs(minutes), 60)
        zone = f"{'+' if minutes >= 0 else '-'}{hour:02d}:{minute:02d}"
        delta = base - timedelta(minutes=minutes) - origin
        seconds = delta.days * 86400 + delta.seconds
        for width in range(10):
            digits = '123456789'[:width]
            stamp = '2026-09-13T12:34:56' + ('.' + digits if width else '') + zone
            expected = seconds * 1_000_000_000 + int(digits.ljust(9, '0'))
            ns, floor = _f14_native_time_v1(stamp)
            assert ns == expected
            floor_delta = datetime.fromisoformat(floor) - origin
            assert ((floor_delta.days * 86400 + floor_delta.seconds) * 1_000_000
                + floor_delta.microseconds) == ns // 1000
            count += 1
    for stamp, expected in (('0001-01-01T00:00:00Z', -62135596800000000000),
            ('9999-12-31T23:59:59.999999999+00:00', 253402300799999999999),
            ('1969-12-31T23:59:59.999999999Z', -1)):
        assert _f14_native_time_v1(stamp)[0] == expected
    assert count == 28790
    for stamp in (None, True, 1, '', '2026-09-13T00:00:00-00:00', '2026-09-13T00:00:00+24:00',
            '2026-09-13T00:00:00+00:60', '2026-09-13T00:00:60Z', '2026-09-13T24:00:00Z',
            '2026-02-29T00:00:00Z', '2026-09-13T00:00:00.1234567890Z',
            '2026-09-13T00:00:00+00:00:00', '0001-01-01T00:00:00+00:01',
            '9999-12-31T23:59:59-00:01', '2026-09-13t00:00:00z', '2026-09-13T00:00:00Z ',
            '２０２６-09-13T00:00:00Z', '2026-09-13T00:00:00.Z', '2026-09-13T00:00:00', '0000-01-01T00:00:00Z'):
        with pytest.raises(PointInTimeError, match='F14_STORAGE_TIME'):
            _f14_native_time_v1(stamp)
