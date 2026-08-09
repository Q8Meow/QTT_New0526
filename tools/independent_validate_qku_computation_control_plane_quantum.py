#!/usr/bin/env python3
"""Independent trace-only MATH-50 through MATH-52 validation."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (
    QAOAPreexistingTraceV1,
    QAOATracePointV1,
    QuantumBenchmarkServiceV1,
    VQEPreexistingTraceV1,
    VQETracePointV1,
)


def main() -> int:
    service = QuantumBenchmarkServiceV1()
    qaoa = QAOAPreexistingTraceV1(
        "Q::1", "L::1", "F::1", "O::1", ("theta",), "S::1",
        (QAOATracePointV1("A", Decimal("0.25"), Decimal("2"), True, Decimal("0.6")), QAOATracePointV1("B", Decimal("0.75"), Decimal("1"), True, Decimal("0.7"))),
        "B", "C::1", "N::1", True, True,
    )
    vqe = VQEPreexistingTraceV1(
        "V::1", "L::1", "F::1", "H::1", "A::SUPPLIED", ("phi",), "O::SUPPLIED", "S::1",
        (VQETracePointV1("A", Decimal("0.2"), Decimal("0.01"), True, Decimal("0.55")), VQETracePointV1("B", Decimal("0.4"), Decimal("0.02"), True, Decimal("0.5"))),
        "A", "C::1", "N::1", True, True,
    )
    q_receipt = service.validate_qaoa_trace(qaoa)
    v_receipt = service.validate_vqe_trace(vqe)
    comparison = service.compare_same_lock(
        comparison_id="QCNT::1", quantum_receipt=q_receipt,
        strongest_classical_receipt_ref="C::1", strongest_classical_input_lock_id="L::1", strongest_classical_formulation_id="F::1", strongest_classical_utility=Decimal("0.65"),
        no_trade_receipt_ref="N::1", no_trade_input_lock_id="L::1", no_trade_formulation_id="F::1", no_trade_utility=Decimal("0"),
    )
    source = (ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py").read_text(encoding="utf-8")
    forbidden_calls = ("Estimator(", "Sampler(", "transpile(", ".run(", "AerSimulator(", "provider.", "qpu.")
    checks = (
        q_receipt.recomputed_objective == Decimal("1.25"),
        q_receipt.selected_candidate_id == "B",
        v_receipt.recomputed_objective == Decimal("0.2"),
        v_receipt.recomputed_variance_or_explicit_absence == Decimal("0.01"),
        comparison.winner == "VALIDATED_QUANTUM",
        comparison.delta_quantum_vs_classical == Decimal("0.05"),
        not any(token in source for token in forbidden_calls),
        set(q_receipt.effect_counts.values()) == {0},
    )
    if not all(checks):
        print("QKU_QUANTUM_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print("QKU_QUANTUM_INDEPENDENTLY_VALIDATED checks=8 trace_only=3 effect_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
