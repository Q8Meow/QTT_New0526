import inspect

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    compute_math_09_log_loss,
    compute_math_10_expected_calibration_error,
    compute_math_11_wilson_score_interval,
    compute_math_14_stationary_bootstrap_mean_interval,
    compute_math_15_white_reality_check,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    BenchmarkSignConvention,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    validate_all_golden_vectors,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    MATH_IO_CONTRACTS,
)


def test_registry_oracle_and_vector_lineage_is_cross_consistent() -> None:
    for math_id, implementation in IMPLEMENTATION_REGISTRY.items():
        oracle = ORACLE_BY_MATH_ID[math_id]
        vector = GOLDEN_VECTOR_BY_MATH_ID[math_id]
        assert implementation.contract.math_spec_id == math_id
        assert implementation.oracle_id == oracle.oracle_id
        assert implementation.golden_vector_id == vector.vector_id
        assert vector.oracle_id == oracle.oracle_id
    assert validate_all_golden_vectors().passed
    assert tuple(MATH_IO_CONTRACTS) == tuple(IMPLEMENTATION_REGISTRY)
    assert tuple(
        field.name for field in MATH_IO_CONTRACTS["MATH-01"].inputs
    ) == ("contract_price", "payout_per_winning_contract")
    assert tuple(
        inspect.signature(compute_math_09_log_loss).parameters
    )[:2] == ("p", "y")
    assert tuple(
        inspect.signature(compute_math_11_wilson_score_interval).parameters
    ) == ("successes", "trials", "confidence")
    assert tuple(
        inspect.signature(
            compute_math_14_stationary_bootstrap_mean_interval
        ).parameters
    )[:2] == ("series", "expected_block_length")
    assert next(
        iter(inspect.signature(compute_math_15_white_reality_check).parameters)
    ) == "loss_differentials"


def test_raw_calibration_and_time_candidate_model_risk_contracts() -> None:
    assert (
        compute_math_10_expected_calibration_error(
            (0.3, 0.3, 0.8, 0.8),
            (1, 0, 1, 0),
            (0.0, 0.5, 1.0),
        )
        == 0.25
    )
    with pytest.raises(NumericDomainError):
        compute_math_10_expected_calibration_error(
            (0.3, 0.8),
            (1, 0),
            (0.0, 0.5, 0.5, 1.0),
        )
    with pytest.raises(NumericDomainError):
        compute_math_09_log_loss((0.8, 0.8), (1, 0))
    result = compute_math_15_white_reality_check(
        ((1.0, 0.0),) * 4,
        sign_convention=(
            BenchmarkSignConvention.BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS
        ),
        seed=1501,
        replicates=32,
    )
    assert result.statistic == 2.0
    assert result.p_value == 0.0
    assert result.reject
    reversed_result = compute_math_15_white_reality_check(
        ((1.0,),) * 4,
        sign_convention=(
            BenchmarkSignConvention.CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS
        ),
        seed=1501,
        replicates=32,
    )
    assert reversed_result.statistic == -2.0
    assert reversed_result.p_value == 1.0
    assert not reversed_result.reject
    with pytest.raises(NumericDomainError):
        compute_math_15_white_reality_check(
            ((0.0, 0.0),) * 2,
            sign_convention=(
                BenchmarkSignConvention.BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS
            ),
            seed=1501,
            replicates=8,
        )
