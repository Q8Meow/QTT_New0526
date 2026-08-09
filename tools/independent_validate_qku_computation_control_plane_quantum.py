#!/usr/bin/env python3
"""Independent executable MATH-50 through MATH-52 validation."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (  # noqa: E402
    EconomicComparatorReceiptV1,
    QAOAPreexistingTraceV1,
    QAOATracePointV1,
    QuantumBenchmarkServiceV1,
    QuantumEconomicBasisV1,
    VQEPreexistingTraceV1,
    VQETracePointV1,
)


def _basis(**overrides: object) -> QuantumEconomicBasisV1:
    values: dict[str, object] = {
        "input_lock_id": "L::1",
        "original_formulation_id": "F::1",
        "objective_sense": "MAXIMIZE",
        "constraint_refs": ("CONSTRAINT::1",),
        "accounting_basis_ref": "ACCOUNTING::1",
        "cost_basis_ref": "COST::1",
        "capacity_basis_ref": "CAPACITY::1",
        "scenario_set_ref": "SCENARIO::1",
        "resource_budget_ref": "RESOURCE::1",
        "ttl_policy_ref": "TTL::1",
        "version_epoch_pins": ("VERSION::1", "SOURCE::1=EPOCH::1"),
    }
    values.update(overrides)
    return QuantumEconomicBasisV1(**values)


def _comparator(
    comparator_class: str,
    *,
    basis: QuantumEconomicBasisV1 | None = None,
    utility: str = "0.65",
    resource_use: str = "2",
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
        resource_use=Decimal(resource_use),
        latency=Decimal(latency),
        deterministic_tie_break=f"TIE::{comparator_class}",
    )


def _qaoa() -> QAOAPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator(
        "NO_TRADE", utility="0", resource_use="0", latency="0"
    )
    return QAOAPreexistingTraceV1(
        trace_id="Q::1",
        input_lock_id="L::1",
        formulation_id="F::1",
        objective_id="O::1",
        objective_sense="MAXIMIZE",
        parameter_order=("theta",),
        seed_policy_ref="SEED::1",
        bounds_ref="BOUNDS::1",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            QAOATracePointV1(
                "A", Decimal("0.25"), Decimal("2"), True,
                Decimal("0.6"), Decimal("2"), Decimal("2"),
            ),
            QAOATracePointV1(
                "B", Decimal("0.75"), Decimal("1"), True,
                Decimal("0.7"), Decimal("1"), Decimal("1"),
            ),
        ),
        selected_candidate_id="B",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def _vqe() -> VQEPreexistingTraceV1:
    classical = _comparator("STRONGEST_CLASSICAL")
    no_trade = _comparator(
        "NO_TRADE", utility="0", resource_use="0", latency="0"
    )
    return VQEPreexistingTraceV1(
        trace_id="V::1",
        input_lock_id="L::1",
        formulation_id="F::1",
        objective_sense="MAXIMIZE",
        hamiltonian_id="H::1",
        ansatz_metadata_ref="ANSATZ::SUPPLIED",
        parameter_order=("phi",),
        optimizer_metadata_ref="OPTIMIZER::SUPPLIED",
        seed_policy_ref="SEED::1",
        bounds_ref="BOUNDS::1",
        constraint_refs=("CONSTRAINT::1",),
        comparison_basis=_basis(),
        points=(
            VQETracePointV1(
                "A", Decimal("0.2"), Decimal("0.01"), Decimal("1"),
                True, Decimal("0.55"), Decimal("1"), Decimal("1"),
            ),
            VQETracePointV1(
                "B", Decimal("0.4"), Decimal("0.02"), Decimal("2"),
                True, Decimal("0.5"), Decimal("2"), Decimal("2"),
            ),
        ),
        selected_point_id="A",
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        strongest_classical_comparator=classical,
        no_trade_comparator=no_trade,
        trace_complete=True,
        original_model_interpret_back_valid=True,
    )


def main() -> int:
    service = QuantumBenchmarkServiceV1()
    qaoa = _qaoa()
    vqe = _vqe()
    q_receipt = service.validate_qaoa_trace(qaoa)
    v_receipt = service.validate_vqe_trace(vqe)

    # These expected values are reconstructed here from raw supplied traces;
    # they are not read from a production result or a generated projection.
    independent_qaoa_trace_cost = sum(
        point.trace_weight * point.locked_cost for point in qaoa.points
    )
    independent_qaoa_winner = sorted(
        (point for point in qaoa.points if point.original_model_feasible),
        key=lambda point: (-point.original_economic_utility, point.candidate_id),
    )[0]
    independent_vqe_winner = sorted(
        (point for point in vqe.points if point.original_model_feasible),
        key=lambda point: (
            -point.original_economic_utility,
            point.parameter_point_id,
        ),
    )[0]

    basis_mutations: tuple[tuple[str, object], ...] = (
        ("input_lock_id", "L::OTHER"),
        ("original_formulation_id", "F::OTHER"),
        ("objective_sense", "MINIMIZE"),
        ("constraint_refs", ("CONSTRAINT::OTHER",)),
        ("accounting_basis_ref", "ACCOUNTING::OTHER"),
        ("cost_basis_ref", "COST::OTHER"),
        ("capacity_basis_ref", "CAPACITY::OTHER"),
        ("scenario_set_ref", "SCENARIO::OTHER"),
        ("resource_budget_ref", "RESOURCE::OTHER"),
        ("ttl_policy_ref", "TTL::OTHER"),
        ("version_epoch_pins", ("VERSION::OTHER",)),
    )
    rejected_dimensions: list[str] = []
    for field_name, value in basis_mutations:
        try:
            service.compare_same_lock(
                comparison_id=f"MISMATCH::{field_name}",
                quantum_receipt=q_receipt,
                strongest_classical_receipt=_comparator(
                    "STRONGEST_CLASSICAL",
                    basis=replace(_basis(), **{field_name: value}),
                ),
                no_trade_receipt=_comparator(
                    "NO_TRADE", utility="0", resource_use="0", latency="0"
                ),
            )
        except ContractValidationError as exc:
            expected = (
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH
                if field_name == "input_lock_id"
                else ReasonCode.ST12F_QUANTUM_TRACE_INVALID
            )
            if exc.reason_code is expected:
                rejected_dimensions.append(field_name)

    infeasible_a = replace(
        qaoa.points[0], original_model_feasible=False, original_economic_utility=Decimal("9")
    )
    feasible_only = service.validate_qaoa_trace(
        replace(qaoa, points=(infeasible_a, qaoa.points[1]))
    )
    infeasible_selection_rejected = False
    try:
        service.validate_qaoa_trace(
            replace(
                qaoa,
                points=(infeasible_a, qaoa.points[1]),
                selected_candidate_id="A",
            )
        )
    except ContractValidationError as exc:
        infeasible_selection_rejected = (
            exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID
        )
    tie = service.compare_same_lock(
        comparison_id="CONSERVATIVE::TIE",
        quantum_receipt=q_receipt,
        strongest_classical_receipt=_comparator(
            "STRONGEST_CLASSICAL",
            utility="0.7",
            resource_use="1",
            latency="1",
        ),
        no_trade_receipt=_comparator(
            "NO_TRADE", utility="0.7", resource_use="1", latency="1"
        ),
    )
    no_trade_rejections = 0
    for feasible, hard_veto in ((False, False), (True, True)):
        try:
            _comparator(
                "NO_TRADE",
                utility="0",
                resource_use="0",
                latency="0",
                feasible=feasible,
                hard_veto=hard_veto,
            )
        except ContractValidationError as exc:
            if exc.reason_code is ReasonCode.ST12F_QUANTUM_TRACE_INVALID:
                no_trade_rejections += 1

    source = (
        ROOT
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py"
    ).read_text(encoding="utf-8")
    forbidden_calls = (
        "Estimator(", "Sampler(", "transpile(", ".run(",
        "AerSimulator(", "provider.", "qpu.",
    )
    checks = (
        q_receipt.recomputed_objective == independent_qaoa_trace_cost,
        q_receipt.selected_candidate_id == independent_qaoa_winner.candidate_id,
        q_receipt.original_economic_utility
        == independent_qaoa_winner.original_economic_utility,
        v_receipt.recomputed_objective == independent_vqe_winner.expectation,
        v_receipt.recomputed_variance_or_explicit_absence
        == independent_vqe_winner.variance,
        v_receipt.original_economic_utility
        == independent_vqe_winner.original_economic_utility,
        feasible_only.selected_candidate_id == "B",
        infeasible_selection_rejected,
        tuple(rejected_dimensions)
        == tuple(field_name for field_name, _ in basis_mutations),
        tie.winner == "NO_TRADE",
        tie.quantum_advantage_claim_allowed is False,
        no_trade_rejections == 2,
        not any(token in source for token in forbidden_calls),
        set(q_receipt.effect_counts.values()) == {0},
    )
    if not all(checks):
        print("QKU_QUANTUM_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print(
        "QKU_QUANTUM_INDEPENDENTLY_VALIDATED "
        "checks=14 trace_only=3 math52_basis_dimensions=11 effect_calls=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
