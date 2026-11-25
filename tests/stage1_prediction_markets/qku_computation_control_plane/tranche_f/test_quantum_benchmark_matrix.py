"""Compact trace-only ST12-F quantum benchmark semantic matrix."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (
    EconomicComparatorReceiptV1,
    QAOAPreexistingTraceV1,
    QAOATracePointV1,
    QuantumBenchmarkServiceV1,
    QuantumEconomicBasisV1,
    VQEPreexistingTraceV1,
    VQETracePointV1,
)


_SEMANTIC_IDS = (
    "ST12-TEST::161",
    "ST12-TEST::165",
    "ST12-TEST::166",
    "ST12-TEST::167",
    "ST12-TEST::177",
    "ST12-TEST::179",
    "ST12-TEST::229",
)


def _basis(**overrides: object) -> QuantumEconomicBasisV1:
    values: dict[str, object] = {
        "input_lock_id": "ST12F-LOCK::QUANTUM",
        "original_formulation_id": "FORMULATION::1",
        "objective_sense": "MAXIMIZE",
        "constraint_refs": ("CONSTRAINT::1",),
        "accounting_basis_ref": "ACCOUNTING::NET",
        "cost_basis_ref": "COST::ALL-IN",
        "capacity_basis_ref": "CAPACITY::LOCKED",
        "scenario_set_ref": "SCENARIO::LOCKED",
        "resource_budget_ref": "RESOURCE::LOCKED",
        "ttl_policy_ref": "TTL::LOCKED",
        "version_epoch_pins": ("SOURCE::1=EPOCH::1", "VERSION::1"),
    }
    values.update(overrides)
    return QuantumEconomicBasisV1(**values)


def _comparator(
    comparator_class: str,
    *,
    basis: QuantumEconomicBasisV1 | None = None,
    utility: str = "0.65",
    resource: str = "2",
    latency: str = "2",
    feasible: bool = True,
    hard_veto: bool = False,
) -> EconomicComparatorReceiptV1:
    return EconomicComparatorReceiptV1(
        receipt_id=f"RECEIPT::{comparator_class}",
        comparator_class=comparator_class,
        comparison_basis=_basis() if basis is None else basis,
        feasible=feasible,
        hard_veto=hard_veto,
        conservative_utility=Decimal(utility),
        resource_use=Decimal(resource),
        latency=Decimal(latency),
        deterministic_tie_break=f"TIE::{comparator_class}",
    )


def _qaoa_trace() -> QAOAPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator("NO_TRADE", utility="0", resource="0", latency="0")
    return QAOAPreexistingTraceV1(
        trace_id="QAOA-TRACE::1",
        input_lock_id="ST12F-LOCK::QUANTUM",
        formulation_id="FORMULATION::1",
        objective_id="OBJECTIVE::LOCKED",
        objective_sense="MAXIMIZE",
        parameter_order=("theta-1",),
        seed_policy_ref="SEED::LOCKED",
        bounds_ref="BOUNDS::LOCKED",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            QAOATracePointV1("CANDIDATE::A", Decimal("0.25"), Decimal("2"), True, Decimal("0.6"), Decimal("2"), Decimal("2")),
            QAOATracePointV1("CANDIDATE::B", Decimal("0.75"), Decimal("1"), True, Decimal("0.7"), Decimal("1"), Decimal("1")),
        ),
        selected_candidate_id="CANDIDATE::B",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _vqe_trace() -> VQEPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator("NO_TRADE", utility="0", resource="0", latency="0")
    return VQEPreexistingTraceV1(
        trace_id="VQE-TRACE::1",
        input_lock_id="ST12F-LOCK::QUANTUM",
        formulation_id="FORMULATION::1",
        objective_sense="MAXIMIZE",
        hamiltonian_id="HAMILTONIAN::SUPPLIED",
        ansatz_metadata_ref="ANSATZ-METADATA::SUPPLIED-NOT-EXECUTED",
        parameter_order=("phi-1",),
        optimizer_metadata_ref="OPTIMIZER-METADATA::SUPPLIED-NOT-EXECUTED",
        seed_policy_ref="SEED::LOCKED",
        bounds_ref="BOUNDS::LOCKED",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            VQETracePointV1("POINT::A", Decimal("0.2"), Decimal("0.01"), Decimal("1"), True, Decimal("0.55"), Decimal("1"), Decimal("1")),
            VQETracePointV1("POINT::B", Decimal("0.4"), Decimal("0.02"), Decimal("2"), True, Decimal("0.50"), Decimal("2"), Decimal("2")),
        ),
        selected_point_id="POINT::A",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _run_st12f_quantum_fixture_preflight_v1() -> tuple[tuple[str, str], ...]:
    service = QuantumBenchmarkServiceV1()
    qaoa = _qaoa_trace()
    vqe = _vqe_trace()
    qaoa_receipt = service.validate_qaoa_trace(qaoa)
    vqe_receipt = service.validate_vqe_trace(vqe)
    assert qaoa_receipt.math_spec_id == "MATH-50"
    assert vqe_receipt.math_spec_id == "MATH-51"
    results: list[tuple[str, str]] = [
        ("ST12-TEST::161", "QAOA_TRACE_RECOMPUTED"),
    ]
    cases = (
        (
            "ST12-TEST::165",
            lambda: service.validate_qaoa_trace(
                replace(qaoa, points=(replace(qaoa.points[0], trace_weight=Decimal("0.35")), qaoa.points[1]))
            ),
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA_WEIGHT_NORMALIZATION",
        ),
        (
            "ST12-TEST::166",
            lambda: service.validate_qaoa_trace(
                replace(qaoa, points=tuple(replace(point, original_model_feasible=False) for point in qaoa.points))
            ),
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "ORIGINAL_MODEL_FEASIBILITY",
        ),
        (
            "ST12-TEST::167",
            lambda: service.validate_qaoa_trace(replace(qaoa, selected_candidate_id="CANDIDATE::A")),
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA_SELECTED_CANDIDATE",
        ),
    )
    for case_id, mutation, expected, stage in cases:
        service.validate_qaoa_trace(_qaoa_trace())
        try:
            mutation()
        except ContractValidationError as exc:
            assert exc.reason_code is expected
        else:
            raise AssertionError(f"{case_id} did not reach {stage}")
        results.append((case_id, stage))
    results.append(("ST12-TEST::177", "VQE_TRACE_RECOMPUTED"))
    service.validate_vqe_trace(_vqe_trace())
    try:
        service.validate_vqe_trace(replace(vqe, selected_point_id="POINT::B"))
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
    else:
        raise AssertionError("ST12-TEST::179 did not reach VQE_SELECTED_POINT")
    results.append(("ST12-TEST::179", "VQE_SELECTED_POINT"))
    service.compare_same_lock(
        comparison_id="COMPARISON::BASELINE",
        quantum_receipt=qaoa_receipt,
        strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
        no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0"),
    )
    try:
        service.compare_same_lock(
            comparison_id="COMPARISON::MUTATED",
            quantum_receipt=qaoa_receipt,
            strongest_classical_receipt=_comparator(
                "STRONGEST_CLASSICAL",
                basis=_basis(input_lock_id="ST12F-LOCK::OTHER"),
            ),
            no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0"),
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_INPUT_LOCK_MISMATCH
    else:
        raise AssertionError("ST12-TEST::229 did not reach SAME_LOCK_COMPARISON")
    results.append(("ST12-TEST::229", "SAME_LOCK_COMPARISON"))
    assert tuple(case_id for case_id, _ in results) == _SEMANTIC_IDS
    return tuple(results)


def _assert_lp03_native_quantum_fixture_v1(tmp_path, math_id, cases):
    from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_f.test_replay_paper_evidence_matrix import (
        _assert_lp03_authorization_data_contract,
    )

    for case in cases:
        original = tmp_path/(case or "original_native_quantum")
        original.mkdir()
        _assert_lp03_authorization_data_contract(original, selected_math=math_id, review_cut=case)


def test_qaoa_trace_only_matrix(tmp_path) -> None:
    assert len(_run_st12f_quantum_fixture_preflight_v1()) == 7
    receipt = QuantumBenchmarkServiceV1().validate_qaoa_trace(_qaoa_trace())
    assert receipt.terminal_state == "VALIDATED_TRACE_ONLY"
    assert set(receipt.effect_counts.values()) == {0}
    infeasible_selected = replace(
        _qaoa_trace(),
        points=(
            replace(
                _qaoa_trace().points[0],
                original_model_feasible=False,
                original_economic_utility=Decimal("9"),
            ),
            _qaoa_trace().points[1],
        ),
        selected_candidate_id="CANDIDATE::A",
    )
    try:
        QuantumBenchmarkServiceV1().validate_qaoa_trace(infeasible_selected)
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
    else:
        raise AssertionError("MATH-50 accepted an infeasible selected candidate")
    _assert_original_quantum_raw_constructor_outcomes()
    _assert_private_wire_quantum_invocations()
    _assert_lp03_native_quantum_fixture_v1(tmp_path, "MATH-50", (None, "observed_quantum_claim", "quantum_lock_epoch_stale"))


def _assert_private_wire_quantum_invocations() -> None:
    import sys
    from collections.abc import Mapping
    from types import MappingProxyType
    from decimal import Inexact, ROUND_DOWN, localcontext
    import json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import quantum_benchmark as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        _evidence_snapshot_version_pins_v1, resolve_evidence_invocation_v1, invoke_evidence_private_wire_v1,
        _compose_evidence_quantum_bridge_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import EvidenceOriginV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    specifications, implementations = _evidence_snapshot_version_pins_v1()
    observed = []
    targets = tuple((f"MATH-{number}", owner.get_st12f_evidence_math_callable_v1(f"MATH-{number}")) for number in (50, 51, 52))
    previous_profile = sys.getprofile()
    def observe(frame, event, arg):
        if event == "return":
            for math_id, function in targets:
                if frame.f_code is function.__code__:
                    observed.append((math_id, arg))

    def invoke(number, values):
        math_id = f"MATH-{number}"
        row = resolve_evidence_invocation_v1(math_id, implementation_pin=implementations[math_id],
            specification_pin=specifications[math_id], resource_policy_ref="WIRE::QUANTUM-RESOURCES",
            origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)
        assert row.actual_adapter_ref.startswith("quantum_benchmark.py::QuantumBenchmarkServiceV1::")
        raw = deterministic_json(values).encode("utf-8")
        return invoke_evidence_private_wire_v1(row, raw, maximum_input_bytes=16384, maximum_nodes=2048,
            maximum_output_bytes=16384, maximum_output_nodes=2048)

    try:
        sys.setprofile(observe)
        with localcontext() as hostile:
            hostile.prec, hostile.rounding = 2, ROUND_DOWN
            hostile.traps[Inexact] = True
            qaoa = invoke(50, dict(trace=_qaoa_trace()))
            vqe = invoke(51, dict(trace=_vqe_trace()))
            comparison = invoke(52, dict(comparison_id="WIRE::COMPARISON", quantum_receipt=qaoa.constructor_receipt_or_none,
                strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
                no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0")))
        assert len(observed) == 3 and tuple(row[0] for row in observed) == ("MATH-50", "MATH-51", "MATH-52")
        assert all(original_raw is result.raw_result for (_, original_raw), result in zip(observed, (qaoa, vqe, comparison), strict=True))
        for (math_id, function), result in zip(targets, (qaoa, vqe, comparison), strict=True):
            assert result.actual_callable is function and result.actual_adapter is getattr(owner.QuantumBenchmarkServiceV1,
                {"MATH-50": "_validate_qaoa_trace_with_raw_v1", "MATH-51": "_validate_vqe_trace_with_raw_v1",
                 "MATH-52": "_compare_same_lock_with_raw_v1"}[math_id])
            assert result.output_json == deterministic_json(result.raw_result).encode("utf-8")
            assert result.decoded_output == result.raw_result and result.decoded_output is not result.raw_result
        assert dict(qaoa.raw_result) == dict(trace_expected_locked_cost=Decimal("1.25"), original_economic_objective=Decimal("0.7"),
            selected_candidate_id="CANDIDATE::B", selected_original_model_feasible=True, effect_call_count=0)
        assert dict(vqe.raw_result) == dict(trace_expectation=Decimal("0.2"), variance=Decimal("0.01"), original_economic_objective=Decimal("0.55"),
            selected_candidate_id="POINT::A", selected_original_model_feasible=True, effect_call_count=0)
        assert dict(comparison.raw_result) == dict(delta_quantum_vs_classical=Decimal("0.05"), delta_quantum_vs_no_trade=Decimal("0.7"),
            winner="VALIDATED_QUANTUM", quantum_advantage_claim_allowed=False)
        assert qaoa.constructor_receipt_or_none.recomputed_objective == Decimal("1.25")
        assert vqe.constructor_receipt_or_none.recomputed_variance_or_explicit_absence == Decimal("0.01")
        assert comparison.constructor_receipt_or_none.delta_quantum_vs_classical == Decimal("0.05")
        malformed = json.loads(deterministic_json(_qaoa_trace()))
        malformed["points"][0]["original_model_feasible"] = 1
        with pytest.raises(ComputationControlPlaneError):
            invoke(50, dict(trace=malformed))
        malformed = json.loads(deterministic_json(qaoa.constructor_receipt_or_none))
        malformed["effect_counts"]["qpu"] = False
        with pytest.raises(ComputationControlPlaneError):
            invoke(52, dict(comparison_id="WIRE::MALFORMED", quantum_receipt=malformed,
                strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
                no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0")))
        assert len(observed) == 3  # Decoding denials never invoke a constructor.
        with pytest.MonkeyPatch.context() as patch:
            def foreign_lookup(math_id):
                raise AssertionError("foreign lookup executed")
            patch.setattr(owner, "get_st12f_evidence_math_callable_v1", foreign_lookup)
            with pytest.raises(ComputationControlPlaneError, match="LP03_QUANTUM_ORIGINAL_LOOKUP_CHANGED"):
                invoke(50, dict(trace=_qaoa_trace()))
        with pytest.MonkeyPatch.context() as patch:
            def foreign_constructor(*args, **kwargs):
                raise AssertionError("foreign constructor executed")
            patch.setattr(owner.QuantumBenchmarkServiceV1, "_validate_qaoa_trace_with_raw_v1", foreign_constructor)
            with pytest.raises(ComputationControlPlaneError, match="LP03_QUANTUM_ORIGINAL_CONSTRUCTOR_CHANGED"):
                invoke(50, dict(trace=_qaoa_trace()))
        assert len(observed) == 3
        bridge_calls, proxy_calls = [], []
        class ForeignMapping(Mapping):
            def __iter__(self):
                proxy_calls.append("iter")
                raise AssertionError("foreign proxy inspected")
            def __len__(self):
                proxy_calls.append("len")
                raise AssertionError("foreign proxy inspected")
            def __getitem__(self, key):
                proxy_calls.append("getitem")
                raise AssertionError("foreign proxy inspected")
        foreign_raw = MappingProxyType(ForeignMapping())
        def foreign_bridge(*args):
            bridge_calls.append(args)
            return foreign_raw, qaoa.constructor_receipt_or_none, qaoa.actual_adapter
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(owner, "_invoke_evidence_original_quantum_v1", foreign_bridge)
            with pytest.raises(ComputationControlPlaneError, match="LP03_QUANTUM_ORIGINAL_BRIDGE_CHANGED"):
                invoke(50, dict(trace=_qaoa_trace()))
        assert bridge_calls == [] and proxy_calls == [] and len(observed) == 3
        with pytest.raises(ComputationControlPlaneError, match="LP03_QUANTUM_ORIGINAL_BRIDGE_COMPOSITION"):
            _compose_evidence_quantum_bridge_v1(owner._invoke_evidence_original_quantum_v1)
    finally:
        sys.setprofile(previous_profile)


def _assert_original_quantum_raw_constructor_outcomes() -> None:
    """One original pure call supplies both raw and typed constructor outputs."""
    from types import MappingProxyType
    import sys
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import quantum_benchmark as owner

    service, observed = QuantumBenchmarkServiceV1(), []
    targets = tuple((f"MATH-{number}", owner.get_st12f_evidence_math_callable_v1(f"MATH-{number}")) for number in (50, 51, 52))
    previous_profile = sys.getprofile()
    def observe(frame, event, arg):
        if event == "return":
            for math_id, function in targets:
                if frame.f_code is function.__code__:
                    observed.append((math_id, arg))
    try:
        sys.setprofile(observe)
        qaoa_raw, qaoa = service._validate_qaoa_trace_with_raw_v1(_qaoa_trace())
        assert len(observed) == 1 and observed[-1][0] == "MATH-50" and observed[-1][1] is qaoa_raw
        vqe_raw, vqe = service._validate_vqe_trace_with_raw_v1(_vqe_trace())
        assert len(observed) == 2 and observed[-1][0] == "MATH-51" and observed[-1][1] is vqe_raw
        comparison_raw, comparison = service._compare_same_lock_with_raw_v1(comparison_id="COMPARISON::RAW",
            quantum_receipt=qaoa, strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
            no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0"))
        assert len(observed) == 3 and observed[-1][0] == "MATH-52" and observed[-1][1] is comparison_raw
    finally:
        sys.setprofile(previous_profile)
    assert dict(qaoa_raw) == dict(trace_expected_locked_cost=Decimal("1.25"), original_economic_objective=Decimal("0.7"),
        selected_candidate_id="CANDIDATE::B", selected_original_model_feasible=True, effect_call_count=0)
    assert dict(vqe_raw) == dict(trace_expectation=Decimal("0.2"), variance=Decimal("0.01"),
        original_economic_objective=Decimal("0.55"), selected_candidate_id="POINT::A", selected_original_model_feasible=True, effect_call_count=0)
    assert dict(comparison_raw) == dict(delta_quantum_vs_classical=Decimal("0.05"), delta_quantum_vs_no_trade=Decimal("0.7"),
        winner="VALIDATED_QUANTUM", quantum_advantage_claim_allowed=False)
    assert qaoa.recomputed_objective == Decimal("1.25") and qaoa.original_economic_utility == Decimal("0.7")
    assert vqe.recomputed_objective == Decimal("0.2") and vqe.recomputed_variance_or_explicit_absence == Decimal("0.01")
    assert comparison.delta_quantum_vs_classical == Decimal("0.05") and comparison.delta_quantum_vs_no_trade == Decimal("0.7")
    for raw in (qaoa_raw, vqe_raw, comparison_raw):
        assert type(raw) is MappingProxyType
        with pytest.raises(TypeError):
            raw["invented"] = 0
    assert service.validate_qaoa_trace(_qaoa_trace()) == qaoa
    assert service.validate_vqe_trace(_vqe_trace()) == vqe
    assert service.compare_same_lock(comparison_id="COMPARISON::RAW", quantum_receipt=qaoa,
        strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
        no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0")) == comparison


def test_vqe_trace_only_matrix(tmp_path) -> None:
    receipt = QuantumBenchmarkServiceV1().validate_vqe_trace(_vqe_trace())
    assert receipt.terminal_state == "VALIDATED_TRACE_ONLY"
    assert receipt.quantum_advantage_claim_allowed is False
    infeasible_selected = replace(
        _vqe_trace(),
        points=(
            replace(
                _vqe_trace().points[0],
                original_model_feasible=False,
                original_economic_utility=Decimal("9"),
            ),
            _vqe_trace().points[1],
        ),
        selected_point_id="POINT::A",
    )
    try:
        QuantumBenchmarkServiceV1().validate_vqe_trace(infeasible_selected)
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
    else:
        raise AssertionError("MATH-51 accepted an infeasible selected point")
    _assert_lp03_native_quantum_fixture_v1(tmp_path, "MATH-51", (None,))


def test_same_lock_quantum_classical_no_trade_matrix(tmp_path) -> None:
    service = QuantumBenchmarkServiceV1()
    receipt = service.validate_qaoa_trace(_qaoa_trace())
    comparison = service.compare_same_lock(
        comparison_id="COMPARISON::1",
        quantum_receipt=receipt,
        strongest_classical_receipt=_comparator("STRONGEST_CLASSICAL"),
        no_trade_receipt=_comparator("NO_TRADE", utility="0", resource="0", latency="0"),
    )
    assert comparison.winner == "VALIDATED_QUANTUM"
    assert comparison.quantum_advantage_claim_allowed is False
    _assert_lp03_native_quantum_fixture_v1(tmp_path, "MATH-52", (None, "quantum_basis_mismatch"))


def test_math52_complete_basis_and_conservative_tie_matrix() -> None:
    service = QuantumBenchmarkServiceV1()
    receipt = service.validate_qaoa_trace(_qaoa_trace())
    mutations: tuple[tuple[str, object], ...] = (
        ("input_lock_id", "ST12F-LOCK::OTHER"),
        ("original_formulation_id", "FORMULATION::OTHER"),
        ("objective_sense", "MINIMIZE"),
        ("constraint_refs", ("CONSTRAINT::OTHER",)),
        ("accounting_basis_ref", "ACCOUNTING::OTHER"),
        ("cost_basis_ref", "COST::OTHER"),
        ("capacity_basis_ref", "CAPACITY::OTHER"),
        ("scenario_set_ref", "SCENARIO::OTHER"),
        ("resource_budget_ref", "RESOURCE::OTHER"),
        ("ttl_policy_ref", "TTL::OTHER"),
        ("version_epoch_pins", ("SOURCE::1=EPOCH::OTHER", "VERSION::1")),
    )
    for field_name, value in mutations:
        changed = replace(_basis(), **{field_name: value})
        try:
            service.compare_same_lock(
                comparison_id=f"COMPARISON::MISMATCH::{field_name}",
                quantum_receipt=receipt,
                strongest_classical_receipt=_comparator(
                    "STRONGEST_CLASSICAL", basis=changed
                ),
                no_trade_receipt=_comparator(
                    "NO_TRADE", utility="0", resource="0", latency="0"
                ),
            )
        except ContractValidationError as exc:
            expected = (
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH
                if field_name == "input_lock_id"
                else ReasonCode.ST12F_QUANTUM_TRACE_INVALID
            )
            assert exc.reason_code is expected
        else:
            raise AssertionError(f"MATH-52 accepted mismatched {field_name}")

    tied = service.compare_same_lock(
        comparison_id="COMPARISON::CONSERVATIVE-TIE",
        quantum_receipt=receipt,
        strongest_classical_receipt=_comparator(
            "STRONGEST_CLASSICAL", utility="0.7", resource="1", latency="1"
        ),
        no_trade_receipt=_comparator(
            "NO_TRADE", utility="0.7", resource="1", latency="1"
        ),
    )
    assert tied.winner == "NO_TRADE"
    for feasibility, hard_veto in ((False, False), (True, True)):
        try:
            _comparator(
                "NO_TRADE",
                utility="0",
                resource="0",
                latency="0",
                feasible=feasibility,
                hard_veto=hard_veto,
            )
        except ContractValidationError as exc:
            assert exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
        else:
            raise AssertionError("permanent NO_TRADE was made unavailable")
