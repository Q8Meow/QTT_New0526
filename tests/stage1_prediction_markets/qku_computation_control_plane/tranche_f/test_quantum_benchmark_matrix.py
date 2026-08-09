"""Compact trace-only ST12-F quantum benchmark semantic matrix."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (
    QAOAPreexistingTraceV1,
    QAOATracePointV1,
    QuantumBenchmarkServiceV1,
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


def _qaoa_trace() -> QAOAPreexistingTraceV1:
    return QAOAPreexistingTraceV1(
        trace_id="QAOA-TRACE::1",
        input_lock_id="ST12F-LOCK::QUANTUM",
        formulation_id="FORMULATION::1",
        objective_id="OBJECTIVE::LOCKED",
        parameter_order=("theta-1",),
        seed_policy_ref="SEED::LOCKED",
        points=(
            QAOATracePointV1("CANDIDATE::A", Decimal("0.25"), Decimal("2"), True, Decimal("0.6")),
            QAOATracePointV1("CANDIDATE::B", Decimal("0.75"), Decimal("1"), True, Decimal("0.7")),
        ),
        selected_candidate_id="CANDIDATE::B",
        strongest_classical_receipt_ref="CLASSICAL::1",
        no_trade_receipt_ref="NO-TRADE::1",
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _vqe_trace() -> VQEPreexistingTraceV1:
    return VQEPreexistingTraceV1(
        trace_id="VQE-TRACE::1",
        input_lock_id="ST12F-LOCK::QUANTUM",
        formulation_id="FORMULATION::1",
        hamiltonian_id="HAMILTONIAN::SUPPLIED",
        ansatz_metadata_ref="ANSATZ-METADATA::SUPPLIED-NOT-EXECUTED",
        parameter_order=("phi-1",),
        optimizer_metadata_ref="OPTIMIZER-METADATA::SUPPLIED-NOT-EXECUTED",
        seed_policy_ref="SEED::LOCKED",
        points=(
            VQETracePointV1("POINT::A", Decimal("0.2"), Decimal("0.01"), True, Decimal("0.55")),
            VQETracePointV1("POINT::B", Decimal("0.4"), Decimal("0.02"), True, Decimal("0.50")),
        ),
        selected_point_id="POINT::A",
        strongest_classical_receipt_ref="CLASSICAL::1",
        no_trade_receipt_ref="NO-TRADE::1",
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
        strongest_classical_receipt_ref="CLASSICAL::1",
        strongest_classical_input_lock_id=qaoa_receipt.input_lock_id,
        strongest_classical_formulation_id=qaoa_receipt.formulation_id,
        strongest_classical_utility=Decimal("0.65"),
        no_trade_receipt_ref="NO-TRADE::1",
        no_trade_input_lock_id=qaoa_receipt.input_lock_id,
        no_trade_formulation_id=qaoa_receipt.formulation_id,
        no_trade_utility=Decimal("0"),
    )
    try:
        service.compare_same_lock(
            comparison_id="COMPARISON::MUTATED",
            quantum_receipt=qaoa_receipt,
            strongest_classical_receipt_ref="CLASSICAL::1",
            strongest_classical_input_lock_id="ST12F-LOCK::OTHER",
            strongest_classical_formulation_id=qaoa_receipt.formulation_id,
            strongest_classical_utility=Decimal("0.65"),
            no_trade_receipt_ref="NO-TRADE::1",
            no_trade_input_lock_id=qaoa_receipt.input_lock_id,
            no_trade_formulation_id=qaoa_receipt.formulation_id,
            no_trade_utility=Decimal("0"),
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_INPUT_LOCK_MISMATCH
    else:
        raise AssertionError("ST12-TEST::229 did not reach SAME_LOCK_COMPARISON")
    results.append(("ST12-TEST::229", "SAME_LOCK_COMPARISON"))
    assert tuple(case_id for case_id, _ in results) == _SEMANTIC_IDS
    return tuple(results)


def test_qaoa_trace_only_matrix() -> None:
    assert len(_run_st12f_quantum_fixture_preflight_v1()) == 7
    receipt = QuantumBenchmarkServiceV1().validate_qaoa_trace(_qaoa_trace())
    assert receipt.terminal_state == "VALIDATED_TRACE_ONLY"
    assert set(receipt.effect_counts.values()) == {0}


def test_vqe_trace_only_matrix() -> None:
    receipt = QuantumBenchmarkServiceV1().validate_vqe_trace(_vqe_trace())
    assert receipt.terminal_state == "VALIDATED_TRACE_ONLY"
    assert receipt.quantum_advantage_claim_allowed is False


def test_same_lock_quantum_classical_no_trade_matrix() -> None:
    service = QuantumBenchmarkServiceV1()
    receipt = service.validate_qaoa_trace(_qaoa_trace())
    comparison = service.compare_same_lock(
        comparison_id="COMPARISON::1",
        quantum_receipt=receipt,
        strongest_classical_receipt_ref="CLASSICAL::1",
        strongest_classical_input_lock_id=receipt.input_lock_id,
        strongest_classical_formulation_id=receipt.formulation_id,
        strongest_classical_utility=Decimal("0.65"),
        no_trade_receipt_ref="NO-TRADE::1",
        no_trade_input_lock_id=receipt.input_lock_id,
        no_trade_formulation_id=receipt.formulation_id,
        no_trade_utility=Decimal("0"),
    )
    assert comparison.winner == "VALIDATED_QUANTUM"
    assert comparison.quantum_advantage_claim_allowed is False
