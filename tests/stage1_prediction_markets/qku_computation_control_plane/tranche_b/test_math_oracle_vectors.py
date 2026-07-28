"""Tranche-B registry, independent-oracle, vector, and mutation proofs."""

from __future__ import annotations

from decimal import Decimal
import inspect
import math
from statistics import NormalDist

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (
    implementation_registry as production,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_A_SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_B_SOURCE_CLAIM_BINDING_RULES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    ORACLE_PACK,
    TRANCHE_A_ORACLE_PACK,
    TRANCHE_B_ORACLE_COVERAGE_ROWS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    PARAMETER_POLICIES,
    STEP12_PARAMETER_POLICIES,
    TRANCHE_A_PARAMETER_POLICIES,
    TRANCHE_B_PARAMETER_POLICIES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    MATH_IO_CONTRACTS,
    TRANCHE_B_MATH_SPECIFICATIONS,
)


def test_exact_a_b_registry_counts_and_unique_union() -> None:
    assert len(TRANCHE_A_PARAMETER_POLICIES) == 135
    assert len(TRANCHE_B_PARAMETER_POLICIES) == 344
    assert len(PARAMETER_POLICIES) == 135
    assert len(STEP12_PARAMETER_POLICIES) == 479
    assert len({row.parameter_id for row in STEP12_PARAMETER_POLICIES}) == 479
    assert len(production.TRANCHE_A_MATH_IDS) == 19
    assert len(production.TRANCHE_B_MATH_IDS) == 30
    assert len(production.IMPLEMENTATION_REGISTRY) == 30
    assert len(TRANCHE_B_MATH_SPECIFICATIONS) == 30
    assert len(MATH_IO_CONTRACTS) == 30
    assert len(TRANCHE_A_ORACLE_PACK) == 19
    assert len(TRANCHE_B_ORACLE_COVERAGE_ROWS) == 30
    assert len(ORACLE_PACK) == 30
    assert len(TRANCHE_A_SOURCE_CLAIM_BINDING_RULES) == 1
    assert len(TRANCHE_B_SOURCE_CLAIM_BINDING_RULES) == 10
    assert len(SOURCE_CLAIM_BINDING_RULES) == 10


def test_production_registry_does_not_import_oracle_expected_values() -> None:
    source = inspect.getsource(production)
    assert "oracle_contracts" not in source
    assert "_GOLDEN_VECTOR_ROWS_JSON" not in source
    assert "expected_json" not in source
    assert all(
        entry.callable is not None
        and entry.callable.__module__ == production.__name__
        for entry in production.IMPLEMENTATION_REGISTRY.values()
    )


def test_math_16_independent_null_invariant_and_mutation() -> None:
    null = production.compute_math_16_hansen_spa(
        differentials=[[0, 0, 0, 0], [0, 0, 0, 0]],
        seed=1601,
        replicates=64,
    )
    assert (null.p_value, null.reject, null.statistic) == (1.0, False, 0.0)
    mutated = production.compute_math_16_hansen_spa(
        differentials=[
            [0.1, -0.2],
            [0.2, 0.1],
            [0.3, -0.1],
            [0.5, 0.2],
        ],
        seed=1601,
        replicates=64,
    )
    assert mutated.statistic > null.statistic
    assert mutated.candidate_count == 2
    assert mutated.observation_count == 4


def test_math_17_independent_formula_and_mutation() -> None:
    denominator = math.sqrt(1.0 + ((3.0 - 1.0) / 4.0) * 0.5**2)
    expected_z = 0.5 * math.sqrt(99) / denominator
    expected_psr = NormalDist().cdf(expected_z)
    result = production.compute_math_17_probabilistic_sharpe_ratio(
        0.5, 0.0, 100, 0.0, 3.0
    )
    assert result.z_score == pytest.approx(expected_z, abs=1e-12)
    assert result.psr == pytest.approx(expected_psr, abs=1e-12)
    mutated = production.compute_math_17_probabilistic_sharpe_ratio(
        0.6, 0.0, 100, 0.0, 3.0
    )
    assert mutated.psr != result.psr


def test_math_18_independent_bounded_monotonic_invariant() -> None:
    moments = {
        "sharpe_hat": 1.0,
        "n": 100,
        "skewness": 0.0,
        "kurtosis": 3.0,
    }
    values = tuple(
        production.compute_math_18_deflated_sharpe_ratio(
            [0.2, 0.5, 1.0],
            count,
            moments,
        ).dsr
        for count in (1, 10, 100)
    )
    assert all(0.0 <= value <= 1.0 for value in values)
    assert values == tuple(sorted(values, reverse=True))
    mutated = production.compute_math_18_deflated_sharpe_ratio(
        [0.2, 0.5, 1.0],
        10,
        {**moments, "sharpe_hat": 0.5},
    )
    assert mutated.dsr != values[1]


def test_math_19_independent_rank_fraction_and_mutation() -> None:
    ranks = (0.25, 0.75, 0.4, 0.9)
    expected = sum(rank <= 0.5 for rank in ranks) / len(ranks)
    result = production.compute_math_19_probability_of_backtest_overfitting(
        split_oos_relative_ranks=ranks
    )
    assert result.pbo == expected == 0.5
    mutated = production.compute_math_19_probability_of_backtest_overfitting(
        split_oos_relative_ranks=(0.6, 0.75, 0.4, 0.9)
    )
    assert mutated.pbo != result.pbo


def test_math_20_independent_overlap_embargo_and_mutation() -> None:
    intervals = ((0, 3), (1, 4), (5, 6), (7, 9))
    result = production.compute_math_20_purged_kfold_with_embargo(
        intervals,
        test_indices=(1,),
        embargo_horizon=1,
    )
    independently_valid = tuple(
        index
        for index, (start, end) in enumerate(intervals)
        if index != 1
        and not (start <= 4 and end >= 1)
        and not (4 < start < 5)
    )
    assert result.training_indices == independently_valid == (2, 3)
    assert result.purged_indices == (0,)
    mutated = production.compute_math_20_purged_kfold_with_embargo(
        ((0, 3), (1, 4), (4.5, 6), (7, 9)),
        test_indices=(1,),
        embargo_horizon=1,
    )
    assert mutated.training_indices != result.training_indices
    assert mutated.embargoed_indices == (2,)


def test_math_21_independent_combination_count_and_mutation() -> None:
    result = production.compute_math_21_combinatorial_purged_cross_validation(
        4, 2
    )
    assert result.split_count == math.comb(4, 2) == 6
    assert result.no_post_hoc_path_selection
    mutated = production.compute_math_21_combinatorial_purged_cross_validation(
        5, 2
    )
    assert mutated.split_count == math.comb(5, 2)
    assert mutated.split_count != result.split_count


def test_math_22_independent_dr_formula_and_mutation() -> None:
    samples = (
        {
            "mu_logged": 0.5,
            "pi_logged": 0.8,
            "pi_q_sum": 0.5,
            "q_logged": 0.6,
            "reward": 1.0,
        },
        {
            "mu_logged": 0.5,
            "pi_logged": 0.2,
            "pi_q_sum": 0.5,
            "q_logged": 0.4,
            "reward": 0.0,
        },
    )
    expected = (
        0.5 + (0.8 / 0.5) * (1.0 - 0.6)
        + 0.5
        + (0.2 / 0.5) * (0.0 - 0.4)
    ) / 2
    result = production.compute_math_22_doubly_robust_off_policy_evaluation(
        samples
    )
    assert result.dr_estimate == pytest.approx(expected, abs=1e-12)
    mutated_samples = ({**samples[0], "reward": 0.8}, samples[1])
    mutated = production.compute_math_22_doubly_robust_off_policy_evaluation(
        mutated_samples
    )
    assert mutated.dr_estimate != result.dr_estimate


@pytest.mark.parametrize(
    ("math_id", "expected"),
    (("MATH-23", 0.8), ("MATH-24", 0.8)),
)
def test_math_23_24_independent_ope_formulas(
    math_id: str,
    expected: float,
) -> None:
    weights = (1.6, 0.4)
    rewards = (1.0, 0.0)
    if math_id == "MATH-23":
        independent = sum(
            weight * reward for weight, reward in zip(weights, rewards, strict=True)
        ) / len(weights)
    else:
        independent = sum(
            weight * reward for weight, reward in zip(weights, rewards, strict=True)
        ) / sum(weights)
    actual = production.get_math_callable(math_id)(weights, rewards)
    assert independent == expected
    assert actual == pytest.approx(independent, abs=1e-12)
    assert production.get_math_callable(math_id)(weights, (0.5, 0.0)) != actual


def test_math_25_independent_switch_partition_and_mutation() -> None:
    result = production.compute_math_25_switch_ope(
        (0.5, 3.0),
        (1.0, 0.0),
        (0.6, 0.4),
        1.0,
    )
    assert result.importance_corrected_indices == (0,)
    assert result.direct_model_indices == (1,)
    mutated = production.compute_math_25_switch_ope(
        (0.5, 0.75),
        (1.0, 0.0),
        (0.6, 0.4),
        1.0,
    )
    assert mutated.importance_corrected_indices != (
        result.importance_corrected_indices
    )


def test_math_36_independent_decimal_complements_and_mutation() -> None:
    result = production.compute_math_36_kalshi_binary_book_transform(
        Decimal("0.42"),
        Decimal("0.56"),
        Decimal("1.00"),
    )
    assert result.yes_implied_ask == Decimal("1.00") - Decimal("0.56")
    assert result.no_implied_ask == Decimal("1.00") - Decimal("0.42")
    mutated = production.compute_math_36_kalshi_binary_book_transform(
        Decimal("0.47"),
        Decimal("0.56"),
        Decimal("1.00"),
    )
    assert mutated.no_implied_ask != result.no_implied_ask
