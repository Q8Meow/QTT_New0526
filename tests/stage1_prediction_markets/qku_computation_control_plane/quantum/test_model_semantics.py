from itertools import product

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    ObjectiveScalingReceiptV1,
    QuboModelV1,
    QuboUpperTermV1,
    compute_math_47_qubo_to_ising_transform,
)


def test_qubo_and_ising_semantics_have_assignment_energy_parity() -> None:
    reversed_term = QuboUpperTermV1(1, 0, 0.5)
    assert (reversed_term.i, reversed_term.j) == (0, 1)
    qubo = QuboModelV1(
        (1.0, 2.0),
        (reversed_term,),
        0.1,
        ObjectiveScalingReceiptV1(
            "fixture-objective",
            "original objective",
            "normalized objective",
            2.0,
        ),
    )
    ising = compute_math_47_qubo_to_ising_transform(qubo)
    for binary in product((0, 1), repeat=2):
        spins = tuple(1 - 2 * value for value in binary)
        assert (
            abs(qubo.energy(binary) - ising.energy(spins))
            <= ising.energy_parity_tolerance
        )
        assert (
            abs(
                qubo.original_objective_energy(binary)
                - ising.original_objective_energy(spins)
            )
            <= ising.energy_parity_tolerance
            / qubo.scaling_receipt.applied_scale
        )
        assert qubo.original_objective_energy(binary) == (
            qubo.energy(binary) / 2.0
        )
    assert ising.scaling_receipt is qubo.scaling_receipt
    assert ising.binary_to_spin_convention == "x_i=(1-s_i)/2"
    with pytest.raises(NumericDomainError):
        qubo.energy((True, 0))
    with pytest.raises(NumericDomainError):
        ising.energy((True, -1))
