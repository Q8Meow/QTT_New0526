"""Single allowlisted registry for all 19 Tranche-A mathematical callables."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal, localcontext
from itertools import product
import math
from random import Random
from statistics import NormalDist
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from .context import decimal_context_v1, exact_decimal, finite_float
from .errors import ContractValidationError, NumericDomainError, ReasonCode
from .models import (
    BenchmarkSignConvention,
    ComputationImplementationV1,
    ObjectiveSense,
    VariableDomain,
)


DecimalInput = Decimal | str | int


def _fail(message: str, reason: ReasonCode = ReasonCode.OUT_OF_DOMAIN) -> None:
    raise NumericDomainError(reason, message)


def _probability(value: object, *, field_name: str) -> float:
    result = finite_float(value, field_name=field_name)
    if not 0.0 <= result <= 1.0:
        _fail(f"{field_name} must be in [0, 1]")
    return result


def _probability_decimal(value: object, *, field_name: str) -> Decimal:
    result = exact_decimal(value, field_name=field_name)  # type: ignore[arg-type]
    if not Decimal(0) <= result <= Decimal(1):
        _fail(f"{field_name} must be in [0, 1]")
    return result


def _cash(value: object, *, field_name: str) -> Decimal:
    return exact_decimal(value, field_name=field_name)  # type: ignore[arg-type]


def _nonnegative(value: Decimal, *, field_name: str) -> Decimal:
    if value < 0:
        _fail(f"{field_name} must be nonnegative")
    return value


def compute_math_01_binary_implied_probability(
    contract_price: DecimalInput,
    payout_per_winning_contract: DecimalInput,
) -> Decimal:
    price = exact_decimal(contract_price, field_name="contract_price")
    payout = exact_decimal(
        payout_per_winning_contract,
        field_name="payout_per_winning_contract",
    )
    if payout <= 0 or price < 0 or price > payout:
        _fail("require 0 <= contract_price <= positive payout")
    with localcontext(decimal_context_v1()):
        return price / payout


def compute_math_02_probability_edge(
    calibrated_model_probability: object,
    market_implied_probability: object,
    *,
    calibrated: bool = True,
) -> float:
    if type(calibrated) is not bool:
        _fail("calibrated must be an exact boolean")
    if not calibrated:
        _fail("uncalibrated model probability is ineligible")
    model = _probability(
        calibrated_model_probability, field_name="calibrated_model_probability"
    )
    market = _probability(
        market_implied_probability, field_name="market_implied_probability"
    )
    return model - market


def _book(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    *,
    payout: DecimalInput = "1",
    stale: bool = False,
    auction_state: bool = False,
) -> tuple[Decimal, Decimal, Decimal]:
    if type(stale) is not bool or type(auction_state) is not bool:
        _fail("book state flags must be exact booleans")
    bid = exact_decimal(best_bid, field_name="best_bid")
    ask = exact_decimal(best_ask, field_name="best_ask")
    payout_value = exact_decimal(payout, field_name="payout")
    if stale:
        _fail("stale orderbook snapshot")
    if payout_value <= 0 or bid < 0 or ask < 0 or bid > payout_value or ask > payout_value:
        _fail("book levels must be inside the declared payout domain")
    if ask < bid and not auction_state:
        _fail("crossed book requires an explicit auction state")
    return bid, ask, payout_value


def compute_math_03_orderbook_midpoint(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    *,
    payout: DecimalInput = "1",
    stale: bool = False,
    auction_state: bool = False,
) -> Decimal:
    bid, ask, _ = _book(
        best_bid,
        best_ask,
        payout=payout,
        stale=stale,
        auction_state=auction_state,
    )
    with localcontext(decimal_context_v1()):
        return (bid + ask) / Decimal(2)


def compute_math_04_full_spread(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    *,
    payout: DecimalInput = "1",
    stale: bool = False,
    auction_state: bool = False,
) -> Decimal:
    bid, ask, _ = _book(
        best_bid,
        best_ask,
        payout=payout,
        stale=stale,
        auction_state=auction_state,
    )
    if ask < bid:
        _fail("full spread is undefined for a crossed book")
    with localcontext(decimal_context_v1()):
        return ask - bid


def compute_math_05_relative_spread(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    *,
    payout: DecimalInput = "1",
    stale: bool = False,
) -> Decimal:
    midpoint = compute_math_03_orderbook_midpoint(
        best_bid, best_ask, payout=payout, stale=stale
    )
    spread = compute_math_04_full_spread(
        best_bid, best_ask, payout=payout, stale=stale
    )
    if midpoint <= 0:
        _fail("midpoint must be positive")
    with localcontext(decimal_context_v1()):
        return spread / midpoint


def compute_math_06_binary_contract_expected_net_cash(
    quantity: DecimalInput,
    p: object,
    win_cash: DecimalInput,
    lose_cash: DecimalInput,
    acquisition_cost: DecimalInput,
    fees: DecimalInput,
    expected_slippage: DecimalInput,
    expected_impact: DecimalInput,
) -> Decimal:
    quantity_value = _nonnegative(
        exact_decimal(quantity, field_name="quantity"), field_name="quantity"
    )
    probability = _probability_decimal(p, field_name="p")
    terms = {
        "win_cash": _cash(win_cash, field_name="win_cash"),
        "lose_cash": _cash(lose_cash, field_name="lose_cash"),
        "acquisition_cost": _nonnegative(
            _cash(acquisition_cost, field_name="acquisition_cost"),
            field_name="acquisition_cost",
        ),
        "fees": _nonnegative(_cash(fees, field_name="fees"), field_name="fees"),
        "expected_slippage": _nonnegative(
            _cash(expected_slippage, field_name="expected_slippage"),
            field_name="expected_slippage",
        ),
        "expected_impact": _nonnegative(
            _cash(expected_impact, field_name="expected_impact"),
            field_name="expected_impact",
        ),
    }
    with localcontext(decimal_context_v1()):
        gross = quantity_value * (
            probability * terms["win_cash"]
            + (Decimal(1) - probability) * terms["lose_cash"]
        )
        return (
            gross
            - terms["acquisition_cost"]
            - terms["fees"]
            - terms["expected_slippage"]
            - terms["expected_impact"]
        )


def compute_math_07_multi_outcome_expected_net_cash(
    probabilities: Sequence[object],
    payoffs: Sequence[DecimalInput],
    quantity: DecimalInput,
    acquisition_cost: DecimalInput,
    fees: DecimalInput,
    expected_slippage: DecimalInput,
    expected_impact: DecimalInput,
) -> Decimal:
    if not probabilities or len(probabilities) != len(payoffs):
        _fail("probability and payoff vectors must be nonempty and aligned")
    float_probabilities = [
        _probability(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(probabilities)
    ]
    tolerance = 8 * math.ulp(1.0) * len(float_probabilities)
    if abs(math.fsum(float_probabilities) - 1.0) > tolerance:
        _fail("probabilities must sum to one within the declared tolerance")
    decimal_probabilities = [
        _probability_decimal(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(probabilities)
    ]
    decimal_payoffs = [
        _cash(value, field_name=f"payoffs[{index}]")
        for index, value in enumerate(payoffs)
    ]
    quantity_value = _nonnegative(
        exact_decimal(quantity, field_name="quantity"), field_name="quantity"
    )
    friction = [
        _nonnegative(
            _cash(acquisition_cost, field_name="acquisition_cost"),
            field_name="acquisition_cost",
        ),
        _nonnegative(_cash(fees, field_name="fees"), field_name="fees"),
        _nonnegative(
            _cash(expected_slippage, field_name="expected_slippage"),
            field_name="expected_slippage",
        ),
        _nonnegative(
            _cash(expected_impact, field_name="expected_impact"),
            field_name="expected_impact",
        ),
    ]
    with localcontext(decimal_context_v1()):
        expected_payoff = sum(
            (
                probability * payoff
                for probability, payoff in zip(
                    decimal_probabilities, decimal_payoffs, strict=True
                )
            ),
            Decimal(0),
        )
        return quantity_value * expected_payoff - sum(friction, Decimal(0))


def _vector(value: object, *, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _fail(f"{field_name} must be a declared sequence")
    return tuple(value)


def compute_math_08_brier_score(
    probability: object,
    outcome: object,
) -> float:
    if isinstance(probability, Sequence) and not isinstance(probability, (str, bytes)):
        probabilities = _vector(probability, field_name="probability")
        outcomes = _vector(outcome, field_name="outcome")
        if not probabilities or len(probabilities) != len(outcomes):
            _fail("multiclass probability and outcome vectors must align")
        p_values = [
            _probability(value, field_name=f"probability[{index}]")
            for index, value in enumerate(probabilities)
        ]
        y_values = tuple(outcomes)
        if abs(math.fsum(p_values) - 1.0) > 8 * math.ulp(1.0) * len(
            p_values
        ):
            _fail("multiclass probabilities must sum to one")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (0, 1)
            for value in y_values
        ) or sum(y_values) != 1:
            _fail("multiclass outcome must be one-hot")
        if not any(isinstance(value, float) for value in probabilities):
            decimal_probabilities = tuple(
                _probability_decimal(
                    value,
                    field_name=f"probability[{index}]",
                )
                for index, value in enumerate(probabilities)
            )
            with localcontext(decimal_context_v1()):
                return float(
                    sum(
                        (
                            (probability_value - Decimal(outcome_value)) ** 2
                            for probability_value, outcome_value in zip(
                                decimal_probabilities,
                                y_values,
                                strict=True,
                            )
                        ),
                        Decimal(0),
                    )
                )
        return math.fsum(
            (p - y) ** 2
            for p, y in zip(p_values, y_values, strict=True)
        )
    p_value = _probability(probability, field_name="probability")
    if (
        isinstance(outcome, bool)
        or not isinstance(outcome, int)
        or outcome not in (0, 1)
    ):
        _fail("binary outcome must be resolved to 0 or 1")
    if not isinstance(probability, float):
        decimal_probability = _probability_decimal(
            probability,
            field_name="probability",
        )
        with localcontext(decimal_context_v1()):
            return float(
                (decimal_probability - Decimal(outcome)) ** 2
            )
    return (p_value - outcome) ** 2


def compute_math_09_log_loss(
    probability: object,
    outcome: object,
    *,
    clip_epsilon: object = math.ulp(1.0),
) -> float:
    epsilon = finite_float(clip_epsilon, field_name="clip_epsilon")
    if not 0 < epsilon < 0.5:
        _fail("clip_epsilon must be in (0, 0.5)")
    if isinstance(probability, Sequence) and not isinstance(probability, (str, bytes)):
        probabilities = _vector(probability, field_name="probability")
        outcomes = _vector(outcome, field_name="outcome")
        if not probabilities or len(probabilities) != len(outcomes):
            _fail("multiclass probability and outcome vectors must align")
        p_values = [
            _probability(value, field_name=f"probability[{index}]")
            for index, value in enumerate(probabilities)
        ]
        tolerance = 8 * math.ulp(1.0) * len(p_values)
        if abs(math.fsum(p_values) - 1.0) > tolerance:
            _fail("multiclass probabilities must sum to one")
        y_values = [
            finite_float(value, field_name=f"outcome[{index}]")
            for index, value in enumerate(outcomes)
        ]
        if any(value not in (0.0, 1.0) for value in y_values) or sum(y_values) != 1:
            _fail("multiclass outcome must be one-hot")
        clipped = [min(max(value, epsilon), 1.0 - epsilon) for value in p_values]
        result = -math.fsum(
            y * math.log(p)
            for p, y in zip(clipped, y_values, strict=True)
            if y
        )
    else:
        p_value = _probability(probability, field_name="probability")
        if (
            isinstance(outcome, bool)
            or not isinstance(outcome, int)
            or outcome not in (0, 1)
        ):
            _fail("binary outcome must be resolved to 0 or 1")
        clipped = min(max(p_value, epsilon), 1.0 - epsilon)
        y_value = int(outcome)
        result = -(
            y_value * math.log(clipped)
            + (1 - y_value) * math.log(1.0 - clipped)
        )
    if not math.isfinite(result):
        _fail("log loss must be finite", ReasonCode.NONFINITE_NUMERIC_INPUT)
    return result


@dataclass(frozen=True, slots=True)
class CalibrationBinV1:
    count: int
    mean_confidence: float
    empirical_frequency: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.count, bool)
            or not isinstance(self.count, int)
            or self.count <= 0
        ):
            _fail("calibration-bin count must be positive")
        object.__setattr__(
            self,
            "mean_confidence",
            _probability(self.mean_confidence, field_name="mean_confidence"),
        )
        object.__setattr__(
            self,
            "empirical_frequency",
            _probability(self.empirical_frequency, field_name="empirical_frequency"),
        )


def compute_math_10_expected_calibration_error(
    probabilities: Sequence[object],
    outcomes: Sequence[object],
    bin_edges: Sequence[object],
) -> float:
    probability_values = tuple(
        _probability(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(probabilities)
    )
    outcome_values = tuple(outcomes)
    if not probability_values or len(probability_values) != len(outcome_values):
        _fail("probability and resolved-outcome vectors must be nonempty and aligned")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1)
        for value in outcome_values
    ):
        _fail("calibration outcomes must be resolved integer values 0 or 1")
    edges = tuple(
        _probability(value, field_name=f"bin_edges[{index}]")
        for index, value in enumerate(bin_edges)
    )
    if (
        len(edges) < 2
        or edges[0] != 0.0
        or edges[-1] != 1.0
        or any(left >= right for left, right in zip(edges, edges[1:]))
    ):
        _fail("bin edges must be strictly increasing and cover [0, 1]")
    confidence_sums = [0.0] * (len(edges) - 1)
    outcome_sums = [0] * (len(edges) - 1)
    counts = [0] * (len(edges) - 1)
    for probability, outcome in zip(
        probability_values, outcome_values, strict=True
    ):
        index = min(bisect_right(edges, probability) - 1, len(counts) - 1)
        confidence_sums[index] += probability
        outcome_sums[index] += outcome
        counts[index] += 1
    bins = tuple(
        CalibrationBinV1(
            count=count,
            mean_confidence=confidence_sums[index] / count,
            empirical_frequency=outcome_sums[index] / count,
        )
        for index, count in enumerate(counts)
        if count
    )
    total = sum(item.count for item in bins)
    return math.fsum(
        (item.count / total)
        * abs(item.mean_confidence - item.empirical_frequency)
        for item in bins
    )


@dataclass(frozen=True, slots=True)
class WilsonIntervalV1:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        lower = finite_float(self.lower, field_name="lower")
        upper = finite_float(self.upper, field_name="upper")
        if not 0.0 <= lower <= upper <= 1.0:
            _fail("Wilson interval bounds must satisfy 0 <= lower <= upper <= 1")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)


def compute_math_11_wilson_score_interval(
    successes: int,
    trials: int,
    *,
    confidence: object = 0.95,
    z: object | None = None,
) -> WilsonIntervalV1:
    if (
        isinstance(successes, bool)
        or isinstance(trials, bool)
        or not isinstance(successes, int)
        or not isinstance(trials, int)
        or trials <= 0
        or not 0 <= successes <= trials
    ):
        _fail("require integer trials > 0 and 0 <= successes <= trials")
    confidence_value = _probability(confidence, field_name="confidence")
    if confidence_value in (0.0, 1.0):
        _fail("confidence must be in (0, 1)")
    z_value = (
        finite_float(z, field_name="z")
        if z is not None
        else NormalDist().inv_cdf(1.0 - (1.0 - confidence_value) / 2.0)
    )
    if z_value <= 0:
        _fail("z must be positive")
    phat = successes / trials
    z2 = z_value * z_value
    denominator = 1.0 + z2 / trials
    center = (phat + z2 / (2.0 * trials)) / denominator
    half = (
        z_value
        / denominator
        * math.sqrt(
            phat * (1.0 - phat) / trials + z2 / (4.0 * trials * trials)
        )
    )
    return WilsonIntervalV1(max(0.0, center - half), min(1.0, center + half))


@dataclass(frozen=True, slots=True)
class MultipleTestingResultV1:
    largest_rank: int
    rejected_original_indices: tuple[int, ...]
    adjusted_p_values: tuple[float, ...]
    correction: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.largest_rank, bool)
            or not isinstance(self.largest_rank, int)
            or self.largest_rank < 0
        ):
            _fail("multiple-testing largest rank must be a nonnegative integer")
        if (
            not isinstance(self.adjusted_p_values, tuple)
            or not self.adjusted_p_values
        ):
            _fail("multiple-testing adjusted p-values must be a nonempty tuple")
        adjusted = tuple(
            _probability(value, field_name=f"adjusted_p_values[{index}]")
            for index, value in enumerate(self.adjusted_p_values)
        )
        rejected = self.rejected_original_indices
        if (
            not isinstance(rejected, tuple)
            or len(rejected) != self.largest_rank
            or rejected != tuple(sorted(rejected))
            or len(set(rejected)) != len(rejected)
            or any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or not 0 <= index < len(adjusted)
                for index in rejected
            )
            or self.largest_rank > len(adjusted)
        ):
            _fail("multiple-testing rejected indices do not match the cutoff rank")
        correction = finite_float(self.correction, field_name="correction")
        if correction < 1.0:
            _fail("multiple-testing correction must be at least one")
        object.__setattr__(self, "adjusted_p_values", adjusted)
        object.__setattr__(self, "correction", correction)


def _multiple_testing(
    p_values: Sequence[object],
    q: object,
    *,
    correction: float,
) -> MultipleTestingResultV1:
    if not p_values:
        _fail("p_values must be nonempty")
    q_value = _probability(q, field_name="q")
    if q_value in (0.0, 1.0):
        _fail("q must be in (0, 1)")
    values = [
        _probability(value, field_name=f"p_values[{index}]")
        for index, value in enumerate(p_values)
    ]
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    largest = 0
    for rank, (_, p_value) in enumerate(ordered, 1):
        if p_value <= rank * q_value / (count * correction):
            largest = rank
    rejected = tuple(sorted(index for index, _ in ordered[:largest]))
    sorted_adjusted = [0.0] * count
    running = 1.0
    for rank in range(count, 0, -1):
        candidate = ordered[rank - 1][1] * count * correction / rank
        running = min(running, candidate)
        sorted_adjusted[rank - 1] = min(1.0, running)
    adjusted = [0.0] * count
    for position, (original_index, _) in enumerate(ordered):
        adjusted[original_index] = sorted_adjusted[position]
    return MultipleTestingResultV1(
        largest_rank=largest,
        rejected_original_indices=rejected,
        adjusted_p_values=tuple(adjusted),
        correction=correction,
    )


def compute_math_12_benjamini_hochberg(
    p_values: Sequence[object], q: object = 0.05
) -> MultipleTestingResultV1:
    return _multiple_testing(p_values, q, correction=1.0)


def compute_math_13_benjamini_yekutieli(
    p_values: Sequence[object], q: object = 0.05
) -> MultipleTestingResultV1:
    if not p_values:
        _fail("p_values must be nonempty")
    correction = math.fsum(1.0 / rank for rank in range(1, len(p_values) + 1))
    return _multiple_testing(p_values, q, correction=correction)


def _stationary_indices(
    length: int, mean_block_length: float, rng: Random
) -> tuple[int, ...]:
    probability = 1.0 / mean_block_length
    current = rng.randrange(length)
    result = [current]
    for _ in range(1, length):
        if rng.random() < probability:
            current = rng.randrange(length)
        else:
            current = (current + 1) % length
        result.append(current)
    return tuple(result)


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


@dataclass(frozen=True, slots=True)
class BootstrapMeanIntervalV1:
    sample_mean: float
    lower: float
    upper: float
    bootstrap_distribution: tuple[float, ...]
    seed: int
    mean_block_length: float

    def __post_init__(self) -> None:
        sample_mean = finite_float(self.sample_mean, field_name="sample_mean")
        lower = finite_float(self.lower, field_name="lower")
        upper = finite_float(self.upper, field_name="upper")
        if lower > upper:
            _fail("bootstrap interval lower bound cannot exceed its upper bound")
        if (
            not isinstance(self.bootstrap_distribution, tuple)
            or not self.bootstrap_distribution
        ):
            _fail("bootstrap distribution must be a nonempty immutable tuple")
        distribution = tuple(
            finite_float(value, field_name=f"bootstrap_distribution[{index}]")
            for index, value in enumerate(self.bootstrap_distribution)
        )
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            _fail("bootstrap result seed must be an exact integer")
        block = finite_float(
            self.mean_block_length,
            field_name="mean_block_length",
        )
        if block <= 0:
            _fail("bootstrap result mean block length must be positive")
        object.__setattr__(self, "sample_mean", sample_mean)
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        object.__setattr__(self, "bootstrap_distribution", distribution)
        object.__setattr__(self, "mean_block_length", block)


def compute_math_14_stationary_bootstrap_mean_interval(
    series: Sequence[object],
    mean_block_length: object,
    *,
    seed: int,
    replicates: int = 1000,
    confidence: object = 0.95,
) -> BootstrapMeanIntervalV1:
    values = tuple(
        finite_float(value, field_name=f"series[{index}]")
        for index, value in enumerate(series)
    )
    if len(values) < 2:
        _fail("series length must be at least two")
    block = finite_float(mean_block_length, field_name="mean_block_length")
    if not 1.0 <= block <= len(values):
        _fail("mean block length must be in [1, series length]")
    if isinstance(seed, bool) or not isinstance(seed, int):
        _fail("seed must be an explicit integer")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates <= 0:
        _fail("replicates must be a positive integer")
    confidence_value = _probability(confidence, field_name="confidence")
    if confidence_value in (0.0, 1.0):
        _fail("confidence must be in (0, 1)")
    rng = Random(seed)
    distribution = tuple(
        math.fsum(values[index] for index in _stationary_indices(len(values), block, rng))
        / len(values)
        for _ in range(replicates)
    )
    alpha = (1.0 - confidence_value) / 2.0
    return BootstrapMeanIntervalV1(
        sample_mean=math.fsum(values) / len(values),
        lower=_percentile(distribution, alpha),
        upper=_percentile(distribution, 1.0 - alpha),
        bootstrap_distribution=distribution,
        seed=seed,
        mean_block_length=block,
    )


@dataclass(frozen=True, slots=True)
class RealityCheckResultV1:
    statistic: float
    p_value: float
    reject: bool
    seed: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "statistic",
            finite_float(self.statistic, field_name="statistic"),
        )
        object.__setattr__(
            self,
            "p_value",
            _probability(self.p_value, field_name="p_value"),
        )
        if type(self.reject) is not bool:
            _fail("reality-check rejection state must be an exact boolean")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            _fail("reality-check result seed must be an exact integer")


def compute_math_15_white_reality_check(
    differentials: Sequence[Sequence[object]],
    *,
    sign_convention: BenchmarkSignConvention | None = None,
    seed: int,
    replicates: int = 1000,
    mean_block_length: object = 2,
    alpha: object = 0.05,
) -> RealityCheckResultV1:
    if not isinstance(sign_convention, BenchmarkSignConvention):
        _fail("benchmark sign convention must be explicitly declared")
    if not differentials:
        _fail("time-by-candidate differential matrix must be nonempty")
    time_rows = tuple(
        tuple(
            finite_float(value, field_name=f"differentials[{row}][{column}]")
            for column, value in enumerate(time_row)
        )
        for row, time_row in enumerate(differentials)
    )
    length = len(time_rows)
    candidate_count = len(time_rows[0])
    if (
        length < 2
        or candidate_count < 1
        or any(len(time_row) != candidate_count for time_row in time_rows)
    ):
        _fail("differentials must have shape [time,candidate] with time >= 2")
    candidates = tuple(
        tuple(time_rows[row][column] for row in range(length))
        for column in range(candidate_count)
    )
    if (
        sign_convention
        is BenchmarkSignConvention.CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS
    ):
        candidates = tuple(
            tuple(-value for value in candidate) for candidate in candidates
        )
    block = finite_float(mean_block_length, field_name="mean_block_length")
    if not 1.0 <= block <= length:
        _fail("mean block length must be in [1, sample length]")
    if isinstance(seed, bool) or not isinstance(seed, int):
        _fail("seed must be an explicit integer")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates <= 0:
        _fail("replicates must be a positive integer")
    alpha_value = _probability(alpha, field_name="alpha")
    if alpha_value in (0.0, 1.0):
        _fail("alpha must be in (0, 1)")
    means = tuple(math.fsum(candidate) / length for candidate in candidates)
    observed = max(math.sqrt(length) * mean for mean in means)
    rng = Random(seed)
    exceedances = 0
    for _ in range(replicates):
        indices = _stationary_indices(length, block, rng)
        statistic = max(
            math.sqrt(length)
            * (
                math.fsum(candidate[index] for index in indices) / length
                - candidate_mean
            )
            for candidate, candidate_mean in zip(candidates, means, strict=True)
        )
        if statistic >= observed:
            exceedances += 1
    p_value = exceedances / replicates
    return RealityCheckResultV1(
        statistic=observed,
        p_value=p_value,
        reject=p_value <= alpha_value,
        seed=seed,
    )


@dataclass(frozen=True, slots=True)
class QuboUpperTermV1:
    i: int
    j: int
    value: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.i, bool)
            or isinstance(self.j, bool)
            or not isinstance(self.i, int)
            or not isinstance(self.j, int)
            or self.i < 0
            or self.j < 0
            or self.i == self.j
        ):
            _fail("QUBO interactions require distinct nonnegative integer indices")
        if self.i > self.j:
            original_i = self.i
            object.__setattr__(self, "i", self.j)
            object.__setattr__(self, "j", original_i)
        object.__setattr__(self, "value", finite_float(self.value, field_name="value"))


@dataclass(frozen=True, slots=True)
class ObjectiveScalingReceiptV1:
    original_objective_id: str
    original_unit: str
    normalized_unit: str
    applied_scale: float

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value
            for value in (
                self.original_objective_id,
                self.original_unit,
                self.normalized_unit,
            )
        ):
            _fail("objective scaling receipt requires exact identity and units")
        scale = finite_float(self.applied_scale, field_name="applied_scale")
        if scale <= 0:
            _fail("objective scaling factor must be positive")
        object.__setattr__(self, "applied_scale", scale)


@dataclass(frozen=True, slots=True)
class QuboModelV1:
    diagonal: tuple[float, ...]
    upper_terms: tuple[QuboUpperTermV1, ...]
    offset: float
    scaling_receipt: ObjectiveScalingReceiptV1

    def __post_init__(self) -> None:
        if not isinstance(self.diagonal, tuple) or not self.diagonal:
            _fail("QUBO diagonal must be nonempty")
        diagonal = tuple(
            finite_float(value, field_name=f"diagonal[{index}]")
            for index, value in enumerate(self.diagonal)
        )
        object.__setattr__(self, "diagonal", diagonal)
        object.__setattr__(self, "offset", finite_float(self.offset, field_name="offset"))
        if not isinstance(self.scaling_receipt, ObjectiveScalingReceiptV1):
            _fail("QUBO requires a typed original-objective scaling receipt")
        if not isinstance(self.upper_terms, tuple) or any(
            not isinstance(term, QuboUpperTermV1) for term in self.upper_terms
        ):
            _fail("QUBO upper terms must be typed immutable values")
        combined: dict[tuple[int, int], float] = {}
        for term in self.upper_terms:
            if term.j >= len(diagonal):
                _fail("QUBO upper term references an unknown variable")
            key = (term.i, term.j)
            combined[key] = combined.get(key, 0.0) + term.value
        object.__setattr__(
            self,
            "upper_terms",
            tuple(
                QuboUpperTermV1(i, j, value)
                for (i, j), value in sorted(combined.items())
                if value != 0.0
            ),
        )

    def energy(self, assignment: Sequence[int]) -> float:
        if len(assignment) != len(self.diagonal) or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (0, 1)
            for value in assignment
        ):
            _fail("QUBO assignment must contain one binary value per variable")
        return (
            self.offset
            + math.fsum(
                coefficient * assignment[index]
                for index, coefficient in enumerate(self.diagonal)
            )
            + math.fsum(
                term.value * assignment[term.i] * assignment[term.j]
                for term in self.upper_terms
            )
        )

    def original_objective_energy(self, assignment: Sequence[int]) -> float:
        return self.energy(assignment) / self.scaling_receipt.applied_scale


@dataclass(frozen=True, slots=True)
class QuboEvaluationV1:
    model: QuboModelV1
    assignment: tuple[int, ...]
    energy: float
    original_objective_energy: float

    def __post_init__(self) -> None:
        if not isinstance(self.model, QuboModelV1):
            _fail("QUBO evaluation requires a typed model")
        if not isinstance(self.assignment, tuple):
            _fail("QUBO evaluation assignment must be immutable")
        verified = self.model.energy(self.assignment)
        numeric_energy = finite_float(self.energy, field_name="energy")
        if numeric_energy != verified:
            _fail("QUBO evaluation energy does not match its model")
        object.__setattr__(self, "energy", numeric_energy)
        original = finite_float(
            self.original_objective_energy,
            field_name="original_objective_energy",
        )
        if original != self.model.original_objective_energy(self.assignment):
            _fail("QUBO original-objective reconciliation failed")
        object.__setattr__(self, "original_objective_energy", original)


def compute_math_46_qubo_upper_triangular_convention(
    diagonal: Sequence[object],
    upper_terms: Sequence[QuboUpperTermV1],
    offset: object,
    assignment: Sequence[int],
    *,
    scaling_receipt: ObjectiveScalingReceiptV1,
) -> QuboEvaluationV1:
    model = QuboModelV1(
        diagonal=tuple(
            finite_float(value, field_name=f"diagonal[{index}]")
            for index, value in enumerate(diagonal)
        ),
        upper_terms=tuple(upper_terms),
        offset=finite_float(offset, field_name="offset"),
        scaling_receipt=scaling_receipt,
    )
    binary = tuple(assignment)
    return QuboEvaluationV1(
        model,
        binary,
        model.energy(binary),
        model.original_objective_energy(binary),
    )


@dataclass(frozen=True, slots=True)
class IsingTermV1:
    i: int
    j: int
    value: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.i, bool)
            or isinstance(self.j, bool)
            or not isinstance(self.i, int)
            or not isinstance(self.j, int)
            or self.i < 0
            or self.j < 0
            or self.i >= self.j
        ):
            _fail("Ising interactions require integer indices i < j")
        object.__setattr__(self, "value", finite_float(self.value, field_name="value"))


@dataclass(frozen=True, slots=True)
class IsingModelV1:
    h: tuple[float, ...]
    interactions: tuple[IsingTermV1, ...]
    offset: float
    energy_parity_tolerance: float
    scaling_receipt: ObjectiveScalingReceiptV1
    binary_to_spin_convention: str = "x_i=(1-s_i)/2"

    def __post_init__(self) -> None:
        if not isinstance(self.h, tuple) or not self.h:
            _fail("Ising linear coefficients must be a nonempty tuple")
        h = tuple(
            finite_float(value, field_name=f"h[{index}]")
            for index, value in enumerate(self.h)
        )
        if not isinstance(self.interactions, tuple) or any(
            not isinstance(term, IsingTermV1)
            for term in self.interactions
        ):
            _fail("Ising interactions must be typed immutable terms")
        combined: dict[tuple[int, int], float] = {}
        for term in self.interactions:
            if term.j >= len(h):
                _fail("Ising interaction references an unknown spin")
            key = (term.i, term.j)
            combined[key] = combined.get(key, 0.0) + term.value
        object.__setattr__(self, "h", h)
        object.__setattr__(
            self,
            "interactions",
            tuple(
                IsingTermV1(i, j, value)
                for (i, j), value in sorted(combined.items())
                if value != 0.0
            ),
        )
        object.__setattr__(
            self, "offset", finite_float(self.offset, field_name="offset")
        )
        if not isinstance(self.scaling_receipt, ObjectiveScalingReceiptV1):
            _fail("Ising model requires the original-objective scaling receipt")
        if self.binary_to_spin_convention != "x_i=(1-s_i)/2":
            _fail("Ising binary-to-spin sign convention is ambiguous")
        tolerance = finite_float(
            self.energy_parity_tolerance,
            field_name="energy_parity_tolerance",
        )
        if tolerance <= 0:
            _fail("energy parity tolerance must be positive")
        object.__setattr__(self, "energy_parity_tolerance", tolerance)

    def energy(self, spins: Sequence[int]) -> float:
        if len(spins) != len(self.h) or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (-1, 1)
            for value in spins
        ):
            _fail("Ising assignment must contain one {-1,+1} spin per variable")
        return (
            self.offset
            + math.fsum(value * spins[index] for index, value in enumerate(self.h))
            + math.fsum(
                term.value * spins[term.i] * spins[term.j]
                for term in self.interactions
            )
        )

    def original_objective_energy(self, spins: Sequence[int]) -> float:
        return self.energy(spins) / self.scaling_receipt.applied_scale


def compute_math_47_qubo_to_ising_transform(
    qubo: QuboModelV1,
) -> IsingModelV1:
    if not isinstance(qubo, QuboModelV1):
        _fail("qubo must be a typed QuboModelV1")
    h = [-value / 2.0 for value in qubo.diagonal]
    interactions: list[IsingTermV1] = []
    offset = qubo.offset + math.fsum(value / 2.0 for value in qubo.diagonal)
    for term in qubo.upper_terms:
        h[term.i] -= term.value / 4.0
        h[term.j] -= term.value / 4.0
        interactions.append(IsingTermV1(term.i, term.j, term.value / 4.0))
        offset += term.value / 4.0
    coefficient_scale = max(
        1.0,
        abs(qubo.offset)
        + math.fsum(abs(value) for value in qubo.diagonal)
        + math.fsum(abs(term.value) for term in qubo.upper_terms),
    )
    operation_count = 1 + len(qubo.diagonal) + len(qubo.upper_terms)
    tolerance = 8 * operation_count * math.ulp(coefficient_scale)
    return IsingModelV1(
        h=tuple(h),
        interactions=tuple(interactions),
        offset=offset,
        energy_parity_tolerance=tolerance,
        scaling_receipt=qubo.scaling_receipt,
    )


@dataclass(frozen=True, slots=True)
class QuadraticVariableV1:
    name: str
    domain: VariableDomain
    lower: int | float
    upper: int | float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            _fail("quadratic variables require a nonempty name")
        if not isinstance(self.domain, VariableDomain):
            _fail("quadratic variable domain must be a typed enum")
        if isinstance(self.lower, bool) or isinstance(self.upper, bool):
            _fail("quadratic variable bounds must be numeric, not booleans")
        if self.domain is VariableDomain.BINARY:
            if self.lower != 0 or self.upper != 1:
                _fail("binary variables require bounds [0, 1]")
        elif self.domain is VariableDomain.INTEGER:
            if (
                not isinstance(self.lower, int)
                or not isinstance(self.upper, int)
                or self.lower > self.upper
            ):
                _fail("integer variables require ordered integer bounds")
        elif self.domain is VariableDomain.REAL:
            lower = finite_float(self.lower, field_name=f"{self.name}.lower")
            upper = finite_float(self.upper, field_name=f"{self.name}.upper")
            if lower > upper:
                _fail("real variables require ordered finite bounds")
            object.__setattr__(self, "lower", lower)
            object.__setattr__(self, "upper", upper)
        else:
            _fail("discrete domains belong to the DQM contract")

    def values(self) -> tuple[int | float, ...]:
        if self.domain is VariableDomain.BINARY:
            return (0, 1)
        if self.domain is VariableDomain.INTEGER:
            return tuple(range(self.lower, self.upper + 1))
        if self.domain is VariableDomain.REAL and self.lower == self.upper:
            return (self.lower,)
        _fail("non-fixed real variables are not enumerable by this CQM contract")


@dataclass(frozen=True, slots=True)
class LinearTermV1:
    variable: str
    coefficient: float

    def __post_init__(self) -> None:
        if not isinstance(self.variable, str) or not self.variable:
            _fail("linear terms require a nonempty variable")
        object.__setattr__(
            self,
            "coefficient",
            finite_float(self.coefficient, field_name="linear coefficient"),
        )


@dataclass(frozen=True, slots=True)
class QuadraticTermV1:
    left: str
    right: str
    coefficient: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.left, str)
            or not self.left
            or not isinstance(self.right, str)
            or not self.right
        ):
            _fail("quadratic terms require named variables")
        object.__setattr__(
            self,
            "coefficient",
            finite_float(self.coefficient, field_name="quadratic coefficient"),
        )


@dataclass(frozen=True, slots=True)
class QuadraticConstraintV1:
    constraint_id: str
    linear_terms: tuple[LinearTermV1, ...]
    quadratic_terms: tuple[QuadraticTermV1, ...]
    sense: str
    rhs: float

    def __post_init__(self) -> None:
        if not isinstance(self.constraint_id, str) or not self.constraint_id:
            _fail("quadratic constraints require a nonempty id")
        if not isinstance(self.linear_terms, tuple) or any(
            not isinstance(term, LinearTermV1) for term in self.linear_terms
        ):
            _fail("constraint linear terms must be typed immutable values")
        if not isinstance(self.quadratic_terms, tuple) or any(
            not isinstance(term, QuadraticTermV1)
            for term in self.quadratic_terms
        ):
            _fail("constraint quadratic terms must be typed immutable values")
        if self.sense not in {"<=", ">=", "=="}:
            _fail("constraint sense must be <=, >=, or ==")
        object.__setattr__(
            self, "rhs", finite_float(self.rhs, field_name="constraint rhs")
        )


@dataclass(frozen=True, slots=True)
class ConstrainedQuadraticResultV1:
    assignment: tuple[tuple[str, int | float], ...]
    objective: float
    feasible: bool
    label_crosswalk: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.assignment, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or isinstance(item[1], bool)
            or not isinstance(item[1], int | float)
            for item in self.assignment
        ):
            _fail("CQM result assignment is malformed")
        if len({name for name, _value in self.assignment}) != len(
            self.assignment
        ):
            _fail("CQM result assignment variable names must be unique")
        for name, value in self.assignment:
            finite_float(value, field_name=f"assignment[{name}]")
        object.__setattr__(
            self,
            "objective",
            finite_float(self.objective, field_name="objective"),
        )
        if type(self.feasible) is not bool or not self.feasible:
            _fail("CQM result must be a verified feasible solution")
        if (
            not isinstance(self.label_crosswalk, tuple)
            or len(self.label_crosswalk) != len(self.assignment)
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or isinstance(item[1], bool)
                or not isinstance(item[1], int)
                for item in self.label_crosswalk
            )
            or len({item[0] for item in self.label_crosswalk})
            != len(self.label_crosswalk)
            or len({item[1] for item in self.label_crosswalk})
            != len(self.label_crosswalk)
            or {item[0] for item in self.label_crosswalk}
            != {item[0] for item in self.assignment}
            or {item[1] for item in self.label_crosswalk}
            != set(range(len(self.label_crosswalk)))
        ):
            _fail("CQM result must preserve the exact variable label crosswalk")


def _expression(
    assignment: Mapping[str, int | float],
    linear_terms: Sequence[LinearTermV1],
    quadratic_terms: Sequence[QuadraticTermV1],
) -> float:
    return math.fsum(
        finite_float(term.coefficient, field_name="linear coefficient")
        * assignment[term.variable]
        for term in linear_terms
    ) + math.fsum(
        finite_float(term.coefficient, field_name="quadratic coefficient")
        * assignment[term.left]
        * assignment[term.right]
        for term in quadratic_terms
    )


def compute_math_48_constrained_quadratic_model(
    variables: Sequence[QuadraticVariableV1],
    objective_linear: Sequence[LinearTermV1],
    objective_quadratic: Sequence[QuadraticTermV1],
    constraints: Sequence[QuadraticConstraintV1],
    *,
    objective_sense: ObjectiveSense,
) -> ConstrainedQuadraticResultV1:
    if not variables or any(
        not isinstance(item, QuadraticVariableV1) for item in variables
    ):
        _fail("CQM variables must be typed and nonempty")
    if any(
        not isinstance(term, LinearTermV1) for term in objective_linear
    ) or any(
        not isinstance(term, QuadraticTermV1) for term in objective_quadratic
    ):
        _fail("CQM objective terms must be typed")
    if any(
        not isinstance(constraint, QuadraticConstraintV1)
        for constraint in constraints
    ):
        _fail("CQM constraints must be typed")
    if not isinstance(objective_sense, ObjectiveSense):
        _fail("objective sense must be a typed enum")
    constraint_ids = tuple(constraint.constraint_id for constraint in constraints)
    if len(set(constraint_ids)) != len(constraint_ids):
        _fail("CQM constraint ids must be unique")
    names = tuple(item.name for item in variables)
    if any(not name for name in names) or len(set(names)) != len(names):
        _fail("CQM variable names must be unique and nonempty")
    known = set(names)
    all_terms = tuple(objective_linear) + tuple(
        term
        for constraint in constraints
        for term in constraint.linear_terms
    )
    all_quadratic = tuple(objective_quadratic) + tuple(
        term
        for constraint in constraints
        for term in constraint.quadratic_terms
    )
    if any(term.variable not in known for term in all_terms) or any(
        term.left not in known or term.right not in known for term in all_quadratic
    ):
        _fail("CQM expression references an unknown variable")
    real_names = {
        variable.name for variable in variables if variable.domain is VariableDomain.REAL
    }
    if any(
        term.left in real_names or term.right in real_names
        for term in all_quadratic
    ):
        _fail("unsupported real-variable quadratic term")
    feasible: list[tuple[float, tuple[tuple[str, int | float], ...]]] = []
    for values in product(*(variable.values() for variable in variables)):
        assignment = dict(zip(names, values, strict=True))
        satisfied = True
        for constraint in constraints:
            lhs = _expression(
                assignment, constraint.linear_terms, constraint.quadratic_terms
            )
            rhs = finite_float(constraint.rhs, field_name="constraint rhs")
            if constraint.sense == "<=":
                satisfied = lhs <= rhs
            elif constraint.sense == ">=":
                satisfied = lhs >= rhs
            elif constraint.sense == "==":
                satisfied = lhs == rhs
            else:
                _fail("constraint sense must be <=, >=, or ==")
            if not satisfied:
                break
        if satisfied:
            objective = _expression(
                assignment, objective_linear, objective_quadratic
            )
            feasible.append((objective, tuple(sorted(assignment.items()))))
    if not feasible:
        _fail("CQM has no feasible assignment")
    if objective_sense is ObjectiveSense.MINIMIZE:
        objective, assignment = min(feasible, key=lambda item: (item[0], item[1]))
    elif objective_sense is ObjectiveSense.MAXIMIZE:
        objective, assignment = min(feasible, key=lambda item: (-item[0], item[1]))
    else:
        _fail("objective sense must be declared")
    selected = dict(assignment)
    for constraint in constraints:
        lhs = _expression(
            selected, constraint.linear_terms, constraint.quadratic_terms
        )
        if (
            (constraint.sense == "<=" and lhs > constraint.rhs)
            or (constraint.sense == ">=" and lhs < constraint.rhs)
            or (constraint.sense == "==" and lhs != constraint.rhs)
        ):
            _fail("CQM selected assignment failed feasibility recheck")
    if objective != _expression(
        selected, objective_linear, objective_quadratic
    ):
        _fail("CQM selected objective failed deterministic recheck")
    return ConstrainedQuadraticResultV1(
        assignment,
        objective,
        True,
        tuple((name, index) for index, name in enumerate(names)),
    )


@dataclass(frozen=True, slots=True)
class DiscreteVariableV1:
    name: str
    cases: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name
            or not isinstance(self.cases, tuple)
            or not self.cases
            or any(not isinstance(case, str) or not case for case in self.cases)
            or len(set(self.cases)) != len(self.cases)
        ):
            _fail("discrete variables require a name and unique cases")


@dataclass(frozen=True, slots=True)
class DiscreteLinearBiasV1:
    variable: str
    case: str
    bias: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.variable, str)
            or not self.variable
            or not isinstance(self.case, str)
            or not self.case
        ):
            _fail("DQM linear bias requires a named variable and case")
        object.__setattr__(
            self, "bias", finite_float(self.bias, field_name="linear bias")
        )


@dataclass(frozen=True, slots=True)
class DiscretePairwiseBiasV1:
    left_variable: str
    left_case: str
    right_variable: str
    right_case: str
    bias: float

    def __post_init__(self) -> None:
        values = (
            self.left_variable,
            self.left_case,
            self.right_variable,
            self.right_case,
        )
        if any(not isinstance(value, str) or not value for value in values):
            _fail("DQM pairwise bias requires named variables and cases")
        object.__setattr__(
            self, "bias", finite_float(self.bias, field_name="pairwise bias")
        )


@dataclass(frozen=True, slots=True)
class DiscreteQuadraticResultV1:
    assignment: tuple[tuple[str, str], ...]
    energy: float
    interpret_back_map: tuple[tuple[str, tuple[str, ...]], ...]
    one_case_per_variable: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.assignment, tuple)
            or not self.assignment
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or any(
                    not isinstance(value, str) or not value for value in item
                )
                for item in self.assignment
            )
            or len({item[0] for item in self.assignment})
            != len(self.assignment)
        ):
            _fail("DQM result assignment must select one named case per variable")
        object.__setattr__(
            self, "energy", finite_float(self.energy, field_name="energy")
        )
        if type(self.one_case_per_variable) is not bool or not (
            self.one_case_per_variable
        ):
            _fail("DQM result must preserve one-case-per-variable semantics")
        if (
            not isinstance(self.interpret_back_map, tuple)
            or len(self.interpret_back_map) != len(self.assignment)
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or not isinstance(item[1], tuple)
                or not item[1]
                or any(
                    not isinstance(case, str) or not case
                    for case in item[1]
                )
                or len(set(item[1])) != len(item[1])
                for item in self.interpret_back_map
            )
            or len({item[0] for item in self.interpret_back_map})
            != len(self.interpret_back_map)
        ):
            _fail("DQM result must preserve the exact interpret-back map")
        cases_by_name = dict(self.interpret_back_map)
        if set(cases_by_name) != {name for name, _case in self.assignment} or any(
            case not in cases_by_name[name] for name, case in self.assignment
        ):
            _fail("DQM selected cases do not match the interpret-back map")


def compute_math_49_discrete_quadratic_model(
    variables: Sequence[DiscreteVariableV1],
    linear_biases: Sequence[DiscreteLinearBiasV1],
    pairwise_biases: Sequence[DiscretePairwiseBiasV1],
) -> DiscreteQuadraticResultV1:
    if not variables or any(
        not isinstance(item, DiscreteVariableV1) for item in variables
    ):
        _fail("DQM variables must be typed and nonempty")
    if any(
        not isinstance(item, DiscreteLinearBiasV1) for item in linear_biases
    ) or any(
        not isinstance(item, DiscretePairwiseBiasV1)
        for item in pairwise_biases
    ):
        _fail("DQM biases must be typed")
    by_name = {item.name: item for item in variables}
    if len(by_name) != len(variables):
        _fail("DQM variable names must be unique")
    seen_linear: set[tuple[str, str]] = set()
    linear: dict[tuple[str, str], float] = {}
    for item in linear_biases:
        key = (item.variable, item.case)
        if (
            item.variable not in by_name
            or item.case not in by_name[item.variable].cases
            or key in seen_linear
        ):
            _fail("DQM linear bias has a duplicate or unknown case")
        seen_linear.add(key)
        linear[key] = finite_float(item.bias, field_name="linear bias")
    pairwise: list[DiscretePairwiseBiasV1] = []
    seen_pairwise: set[tuple[str, str, str, str]] = set()
    for item in pairwise_biases:
        if (
            item.left_variable not in by_name
            or item.right_variable not in by_name
            or item.left_variable == item.right_variable
            or item.left_case not in by_name[item.left_variable].cases
            or item.right_case not in by_name[item.right_variable].cases
        ):
            _fail("DQM pairwise bias references an unknown interaction")
        key = (
            item.left_variable,
            item.left_case,
            item.right_variable,
            item.right_case,
        )
        reverse = (key[2], key[3], key[0], key[1])
        if key in seen_pairwise or reverse in seen_pairwise:
            _fail("DQM pairwise interaction is duplicated")
        seen_pairwise.add(key)
        pairwise.append(item)
    candidates: list[tuple[float, tuple[tuple[str, str], ...]]] = []
    ordered_variables = tuple(sorted(variables, key=lambda item: item.name))
    for selected in product(*(item.cases for item in ordered_variables)):
        assignment = dict(
            zip((item.name for item in ordered_variables), selected, strict=True)
        )
        energy = math.fsum(
            linear.get((name, case), 0.0) for name, case in assignment.items()
        )
        energy += math.fsum(
            finite_float(item.bias, field_name="pairwise bias")
            for item in pairwise
            if assignment[item.left_variable] == item.left_case
            and assignment[item.right_variable] == item.right_case
        )
        candidates.append((energy, tuple(sorted(assignment.items()))))
    energy, assignment = min(candidates, key=lambda item: (item[0], item[1]))
    return DiscreteQuadraticResultV1(
        assignment,
        energy,
        tuple((item.name, item.cases) for item in ordered_variables),
    )


@dataclass(frozen=True, slots=True)
class MathSpecificationMetadataV1:
    certified_formula: str
    domain_and_fail_closed_guards: tuple[str, ...]
    implementation_algorithm: tuple[str, ...]
    mandatory_comparator_or_reconciliation: str
    precision_and_rounding_policy: str
    optional_library_adapter_policy: str
    tie_break_policy: str

    def __post_init__(self) -> None:
        for name in (
            "certified_formula",
            "mandatory_comparator_or_reconciliation",
            "precision_and_rounding_policy",
            "optional_library_adapter_policy",
            "tie_break_policy",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"math specification {name} is required",
                )
        for name in (
            "domain_and_fail_closed_guards",
            "implementation_algorithm",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"math specification {name} must be a nonempty string tuple",
                )
            if len(values) != len(set(values)):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"math specification {name} contains duplicate rows",
                )


@dataclass(frozen=True, slots=True)
class MathImplementationRecordV1:
    contract: ComputationImplementationV1
    name: str
    family: str
    callable: Callable[..., object]
    golden_vector_id: str
    oracle_id: str
    specification_metadata: MathSpecificationMetadataV1
    live_order_authority: bool = False
    replay_or_paper_effect_allowed: bool = False
    provider_or_qpu_effect_allowed: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.contract, ComputationImplementationV1)
            or not isinstance(self.name, str)
            or not self.name
            or not isinstance(self.family, str)
            or not self.family
            or not callable(self.callable)
            or not isinstance(self.golden_vector_id, str)
            or not self.golden_vector_id
            or not isinstance(self.oracle_id, str)
            or not self.oracle_id
            or not isinstance(
                self.specification_metadata,
                MathSpecificationMetadataV1,
            )
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "math implementation registry entry is malformed",
            )
        for name in (
            "live_order_authority",
            "replay_or_paper_effect_allowed",
            "provider_or_qpu_effect_allowed",
        ):
            if type(getattr(self, name)) is not bool:
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a boolean",
                )
        if (
            self.live_order_authority
            or self.replay_or_paper_effect_allowed
            or self.provider_or_qpu_effect_allowed
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "math registry entries cannot authorize runtime effects",
            )


@dataclass(frozen=True, slots=True)
class LegacyFormulaComparatorViewV1:
    math_spec_id: str
    legacy_formula_id: str
    callable_name: str
    callable: Callable[..., object]
    source_owner: str = "PR162D_R2A_FORMULA_SEED_LIBRARY"
    source_version: str = "PR162D-R2A"
    source_path: str = (
        "src/qtt/stage1_prediction_markets/"
        "pr162d_r2a_real_formulations/formula_seed_library.py"
    )
    exact_decimal_alias: bool = False

    def __post_init__(self) -> None:
        for name in (
            "math_spec_id",
            "legacy_formula_id",
            "callable_name",
            "source_owner",
            "source_version",
            "source_path",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise ContractValidationError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"legacy comparator {name} is required",
                )
        if not callable(self.callable):
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "legacy comparator callable is malformed",
            )
        if type(self.exact_decimal_alias) is not bool or self.exact_decimal_alias:
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "float legacy predecessors cannot be exact Decimal aliases",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_path)


_LEGACY_FORMULA_PREDECESSORS = (
    ("MATH-01", "IMPLIED_PROBABILITY"),
    ("MATH-02", "PROBABILITY_EDGE"),
    ("MATH-03", "MID_PRICE"),
    ("MATH-04", "SPREAD"),
    ("MATH-05", "RELATIVE_SPREAD"),
    ("MATH-08", "BRIER_SCORE"),
    ("MATH-09", "LOG_LOSS"),
)


def load_legacy_formula_comparators() -> tuple[LegacyFormulaComparatorViewV1, ...]:
    """Load selected float predecessors only for explicit differential tests."""

    from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (
        formula_by_id,
    )

    try:
        legacy = formula_by_id()
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(
            ReasonCode.OWNER_DATA_MALFORMED,
            "legacy formula predecessor library could not be loaded",
        ) from exc
    if not isinstance(legacy, dict):
        raise ContractValidationError(
            ReasonCode.OWNER_DATA_MALFORMED,
            "legacy formula predecessor library must be an object",
        )
    views: list[LegacyFormulaComparatorViewV1] = []
    for math_spec_id, legacy_formula_id in _LEGACY_FORMULA_PREDECESSORS:
        try:
            spec = legacy[legacy_formula_id]
            function = spec.compute
        except (AttributeError, KeyError) as exc:
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_MISSING,
                f"legacy predecessor is missing: {legacy_formula_id}",
            ) from exc
        views.append(
            LegacyFormulaComparatorViewV1(
                math_spec_id=math_spec_id,
                legacy_formula_id=legacy_formula_id,
                callable_name=function.__name__,
                callable=function,
            )
        )
    return tuple(views)


_PRECISION_AND_ROUNDING_POLICY = (
    "DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; "
    "FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; "
    "NO_IMPLICIT_QUANTIZATION"
)
_OPTIONAL_LIBRARY_ADAPTER_POLICY = (
    "NO_MANDATORY_IMPORT; metadata/compatibility only in Tranche A"
)
_TIE_BREAK_POLICY = (
    "STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_"
    "STRONGER_RULE"
)


def _metadata(
    certified_formula: str,
    guards: tuple[str, ...],
    algorithm: tuple[str, ...],
    comparator: str,
) -> MathSpecificationMetadataV1:
    return MathSpecificationMetadataV1(
        certified_formula=certified_formula,
        domain_and_fail_closed_guards=guards,
        implementation_algorithm=algorithm,
        mandatory_comparator_or_reconciliation=comparator,
        precision_and_rounding_policy=_PRECISION_AND_ROUNDING_POLICY,
        optional_library_adapter_policy=_OPTIONAL_LIBRARY_ADAPTER_POLICY,
        tie_break_policy=_TIE_BREAK_POLICY,
    )


_MATH_SPECIFICATION_METADATA: Mapping[str, MathSpecificationMetadataV1] = (
    MappingProxyType(
        {
            "MATH-01": _metadata(
                "p_market = contract_price / payout_per_winning_contract",
                (
                    "Require 0 <= contract_price <= payout.",
                    "Reject negative or nonfinite input.",
                ),
                (
                    "Validate payout > 0.",
                    "Divide in Decimal context precision 34.",
                    "Return exact typed probability.",
                ),
                "Complement probability and venue payout identity",
            ),
            "MATH-02": _metadata(
                "edge_probability = calibrated_model_probability - "
                "market_implied_probability",
                (
                    "Each probability must be in [0,1].",
                    "Uncalibrated model probability is ineligible for order planning.",
                ),
                (
                    "Validate both probabilities.",
                    "Subtract without clipping.",
                    "Carry calibration and market-source receipts.",
                ),
                "No-trade alternative on the same net friction basis",
            ),
            "MATH-03": _metadata(
                "mid = (best_bid + best_ask) / 2",
                (
                    "Require 0 <= best_bid <= best_ask <= payout.",
                    "Reject crossed book unless explicitly typed as auction state.",
                ),
                (
                    "Read best levels from a sequence-valid snapshot.",
                    "Add and divide by two in Decimal.",
                    "Validate 0 <= midpoint <= payout and emit the declared "
                    "currency-per-contract unit without tick quantization.",
                ),
                "Last trade and one-sided fallback are diagnostics only",
            ),
            "MATH-04": _metadata(
                "spread = best_ask - best_bid",
                (
                    "Require ask >= bid.",
                    "No value for one-sided book unless an explicit proxy policy is bound.",
                ),
                (
                    "Subtract in Decimal.",
                    "Preserve source tick basis.",
                    "Validate nonnegative spread on a noncrossed book, preserve "
                    "the source tick basis, and emit a typed crossed-book failure "
                    "otherwise.",
                ),
                "Half-spread implementation-cost component",
            ),
            "MATH-05": _metadata(
                "relative_spread = (best_ask - best_bid) / midpoint",
                (
                    "Require midpoint > 0.",
                    "Reject crossed or stale book.",
                ),
                (
                    "Compute midpoint using MATH-03.",
                    "Divide spread by midpoint.",
                    "Reject midpoint <= 0, compute the ratio in Decimal precision "
                    "34 without implicit quantization, and validate a finite "
                    "dimensionless output.",
                ),
                "Absolute spread retained in receipt",
            ),
            "MATH-06": _metadata(
                "E_net = quantity * (p * win_cash + (1-p) * lose_cash) - "
                "acquisition_cost - fees - expected_slippage - expected_impact",
                (
                    "Require p in [0,1], quantity >= 0 and finite cash terms.",
                    "No fee or impact omission is allowed.",
                ),
                (
                    "Convert p to Decimal from its canonical string representation.",
                    "Compute each term separately.",
                    "Reconcile gross minus each friction component.",
                ),
                "Realized net cash and no-trade zero-exposure alternative",
            ),
            "MATH-07": _metadata(
                "E_net = quantity * sum_k p_k * payoff_k - acquisition_cost - "
                "fees - expected_slippage - expected_impact",
                (
                    "Require all p_k >= 0 and sum approximately one.",
                    "Reject silent renormalization outside tolerance.",
                ),
                (
                    "Validate aligned vectors.",
                    "Use compensated float summation for probability check.",
                    "Convert probabilities to canonical Decimal strings for cash "
                    "multiplication.",
                ),
                "Outcome-by-outcome realized settlement reconciliation",
            ),
            "MATH-08": _metadata(
                "binary: BS=(p-y)^2; multiclass: BS=sum_k (p_k-y_k)^2",
                (
                    "No unresolved outcome.",
                    "No nonfinite prediction.",
                ),
                (
                    "Validate probability simplex.",
                    "Compute per sample.",
                    "Aggregate mean with compensated summation.",
                ),
                "Climatology and market-implied score on identical observations",
            ),
            "MATH-09": _metadata(
                "binary: LL=-[y*ln(p_clip)+(1-y)*ln(1-p_clip)]; "
                "multiclass: LL=-sum_k y_k ln(p_k_clip)",
                (
                    "Require resolved label and p in [0,1] before numeric clip.",
                    "Reject NaN or infinite output.",
                ),
                (
                    "Clip only for logarithm evaluation and retain original p in receipt.",
                    "Use natural logarithm.",
                    "Aggregate per sample.",
                ),
                "Climatology and market-implied log loss",
            ),
            "MATH-10": _metadata(
                "ECE=sum_b (n_b/N) * abs(mean_confidence_b - "
                "empirical_frequency_b)",
                (
                    "Require N > 0 and strictly monotone edges covering [0,1].",
                    "Do not report empty-bin confidence as zero evidence.",
                ),
                (
                    "Assign every sample to exactly one bin.",
                    "Compute weighted absolute gap.",
                    "Return bin counts and gaps.",
                ),
                "Reliability diagram, Brier and log-loss comparators",
            ),
            "MATH-11": _metadata(
                "center=(phat+z^2/(2n))/(1+z^2/n); "
                "half=z/(1+z^2/n)*sqrt(phat(1-phat)/n+z^2/(4n^2))",
                (
                    "Require n > 0, 0 <= x <= n and 0 < confidence < 1.",
                ),
                (
                    "Compute phat=x/n.",
                    "Compute center and half-width.",
                    "Clip final endpoints to [0,1].",
                ),
                "Exact binomial interval for small-n diagnostic when tractable",
            ),
            "MATH-12": _metadata(
                "k=max{i: p_(i) <= i*q/m}; reject ranks 1..k",
                (
                    "Require nonempty finite p-values in [0,1] and q in (0,1).",
                ),
                (
                    "Stable-sort p-values with original indices.",
                    "Find largest admissible rank.",
                    "Compute monotone adjusted p-values backward.",
                ),
                "BY under arbitrary dependence",
            ),
            "MATH-13": _metadata(
                "c_m=sum_{j=1}^m 1/j; "
                "k=max{i: p_(i) <= i*q/(m*c_m)}",
                ("Same domain guards as BH.",),
                (
                    "Compute harmonic correction deterministically.",
                    "Apply BH mechanics with q/c_m.",
                    "Return correction in receipt.",
                ),
                "BH when dependence assumptions are justified",
            ),
            "MATH-14": _metadata(
                "blocks have geometric length with restart probability 1/L; "
                "statistic is recomputed on each circular resample",
                (
                    "Require series length >= 2 and 1 <= L <= series length.",
                    "Seed and block length must be recorded.",
                ),
                (
                    "Draw a random start at each restart.",
                    "Continue current block with probability 1-1/L using circular index.",
                    "Recompute statistic 1000 times.",
                ),
                "IID bootstrap only as a rejected negative control for dependent series",
            ),
            "MATH-15": _metadata(
                "T=max_j sqrt(n)*mean(d_j); "
                "p=Pr_bootstrap(max_j sqrt(n)*(mean(d_j*)-mean(d_j)) >= T)",
                (
                    "Require aligned finite losses and declared benchmark sign convention.",
                    "No post-hoc candidate removal.",
                ),
                (
                    "Use full material candidate matrix.",
                    "Center under null.",
                    "Apply common stationary-bootstrap indices to every candidate.",
                    "Compute max-statistic p-value.",
                ),
                "Hansen SPA and unadjusted best-candidate statistic",
            ),
            "MATH-46": _metadata(
                "E(x)=c + sum_i Q_ii x_i + sum_{i<j} Q_ij x_i x_j, "
                "x_i in {0,1}",
                (
                    "All coefficients finite.",
                    "Original objective and scaling receipt required.",
                ),
                (
                    "Canonicalize each unordered pair to i<j.",
                    "Sum duplicate coefficients deterministically.",
                    "Drop only exact zeros after declared scaling.",
                ),
                "Direct original-objective recomputation",
            ),
            "MATH-47": _metadata(
                "x_i=(1-s_i)/2; h_i=-Q_ii/2-sum_{j!=i}"
                "Q_min(i,j),max(i,j)/4; J_ij=Q_ij/4; "
                "offset=c+sum_i Q_ii/2+sum_{i<j}Q_ij/4",
                (
                    "Energy parity tolerance must be derived from coefficient "
                    "scale and float precision.",
                    "No sign-convention ambiguity.",
                ),
                (
                    "Apply coefficient formulas exactly.",
                    "Enumerate all assignments for small fixture problems.",
                    "For larger cases, verify random assignment parity with "
                    "deterministic seed.",
                ),
                "QUBO energy on interpreted binary assignment",
            ),
            "MATH-48": _metadata(
                "min/max declared quadratic objective subject to explicit "
                "linear/quadratic constraints over binary, integer and supported "
                "real variables",
                (
                    "Reject unsupported real-variable quadratic terms or hidden constraints.",
                    "Feasibility recheck mandatory.",
                ),
                (
                    "Create variables with exact bounds.",
                    "Add objective.",
                    "Add each named constraint with sense and RHS.",
                    "Persist label crosswalk.",
                ),
                "Classical MILP/MIQP on identical formulation",
            ),
            "MATH-49": _metadata(
                "one discrete variable selects exactly one case; linear and "
                "pairwise case biases define energy without manual one-hot penalty",
                (
                    "Reject duplicate cases, unknown interactions or silent "
                    "one-hot expansion.",
                ),
                (
                    "Create each variable with ordered cases.",
                    "Assign linear case biases and pairwise case interactions.",
                    "Persist interpret-back map.",
                ),
                "One-hot QUBO with proved penalty and classical enumeration for "
                "small fixtures",
            ),
        }
    )
)


def _record(
    math_spec_id: str,
    name: str,
    family: str,
    callable_name: str,
    function: Callable[..., object],
    *,
    seed_required: bool = False,
) -> MathImplementationRecordV1:
    if type(seed_required) is not bool:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "seed_required must be an exact boolean",
        )
    return MathImplementationRecordV1(
        contract=ComputationImplementationV1(
            implementation_id=f"{math_spec_id}::1.1R1",
            math_spec_id=math_spec_id,
            callable_name=callable_name,
            specification_version="1.1R1",
            deterministic=True,
            seed_required=seed_required,
        ),
        name=name,
        family=family,
        callable=function,
        golden_vector_id=f"GOLDEN::{math_spec_id}",
        oracle_id=f"ORACLE::{math_spec_id}",
        specification_metadata=_MATH_SPECIFICATION_METADATA[math_spec_id],
    )


_ENTRIES = (
    _record(
        "MATH-01",
        "BINARY_IMPLIED_PROBABILITY",
        "MARKET_PROBABILITY",
        "compute_math_01_binary_implied_probability",
        compute_math_01_binary_implied_probability,
    ),
    _record(
        "MATH-02",
        "PROBABILITY_EDGE",
        "ALPHA",
        "compute_math_02_probability_edge",
        compute_math_02_probability_edge,
    ),
    _record(
        "MATH-03",
        "ORDERBOOK_MIDPOINT",
        "MICROSTRUCTURE",
        "compute_math_03_orderbook_midpoint",
        compute_math_03_orderbook_midpoint,
    ),
    _record(
        "MATH-04",
        "FULL_SPREAD",
        "MICROSTRUCTURE",
        "compute_math_04_full_spread",
        compute_math_04_full_spread,
    ),
    _record(
        "MATH-05",
        "RELATIVE_SPREAD",
        "MICROSTRUCTURE",
        "compute_math_05_relative_spread",
        compute_math_05_relative_spread,
    ),
    _record(
        "MATH-06",
        "BINARY_CONTRACT_EXPECTED_NET_CASH",
        "EXPECTED_UTILITY",
        "compute_math_06_binary_contract_expected_net_cash",
        compute_math_06_binary_contract_expected_net_cash,
    ),
    _record(
        "MATH-07",
        "MULTI_OUTCOME_EXPECTED_NET_CASH",
        "EXPECTED_UTILITY",
        "compute_math_07_multi_outcome_expected_net_cash",
        compute_math_07_multi_outcome_expected_net_cash,
    ),
    _record(
        "MATH-08",
        "BRIER_SCORE",
        "PROPER_SCORING",
        "compute_math_08_brier_score",
        compute_math_08_brier_score,
    ),
    _record(
        "MATH-09",
        "LOG_LOSS",
        "PROPER_SCORING",
        "compute_math_09_log_loss",
        compute_math_09_log_loss,
    ),
    _record(
        "MATH-10",
        "EXPECTED_CALIBRATION_ERROR",
        "CALIBRATION",
        "compute_math_10_expected_calibration_error",
        compute_math_10_expected_calibration_error,
    ),
    _record(
        "MATH-11",
        "WILSON_SCORE_INTERVAL",
        "STATISTICAL_INTERVAL",
        "compute_math_11_wilson_score_interval",
        compute_math_11_wilson_score_interval,
    ),
    _record(
        "MATH-12",
        "BENJAMINI_HOCHBERG",
        "MULTIPLE_TESTING",
        "compute_math_12_benjamini_hochberg",
        compute_math_12_benjamini_hochberg,
    ),
    _record(
        "MATH-13",
        "BENJAMINI_YEKUTIELI",
        "MULTIPLE_TESTING",
        "compute_math_13_benjamini_yekutieli",
        compute_math_13_benjamini_yekutieli,
    ),
    _record(
        "MATH-14",
        "STATIONARY_BOOTSTRAP_MEAN_INTERVAL",
        "BOOTSTRAP",
        "compute_math_14_stationary_bootstrap_mean_interval",
        compute_math_14_stationary_bootstrap_mean_interval,
        seed_required=True,
    ),
    _record(
        "MATH-15",
        "WHITE_REALITY_CHECK",
        "MODEL_RISK",
        "compute_math_15_white_reality_check",
        compute_math_15_white_reality_check,
        seed_required=True,
    ),
    _record(
        "MATH-46",
        "QUBO_UPPER_TRIANGULAR_CONVENTION",
        "QUANTUM_MAPPING",
        "compute_math_46_qubo_upper_triangular_convention",
        compute_math_46_qubo_upper_triangular_convention,
    ),
    _record(
        "MATH-47",
        "QUBO_TO_ISING_TRANSFORM",
        "QUANTUM_MAPPING",
        "compute_math_47_qubo_to_ising_transform",
        compute_math_47_qubo_to_ising_transform,
    ),
    _record(
        "MATH-48",
        "CONSTRAINED_QUADRATIC_MODEL",
        "QUANTUM_MAPPING",
        "compute_math_48_constrained_quadratic_model",
        compute_math_48_constrained_quadratic_model,
    ),
    _record(
        "MATH-49",
        "DISCRETE_QUADRATIC_MODEL",
        "QUANTUM_MAPPING",
        "compute_math_49_discrete_quadratic_model",
        compute_math_49_discrete_quadratic_model,
    ),
)

IMPLEMENTATION_REGISTRY: Mapping[str, MathImplementationRecordV1] = MappingProxyType(
    {entry.contract.math_spec_id: entry for entry in _ENTRIES}
)
if (
    len(_ENTRIES) != 19
    or len(IMPLEMENTATION_REGISTRY) != 19
    or tuple(_MATH_SPECIFICATION_METADATA) != tuple(IMPLEMENTATION_REGISTRY)
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "the centralized math registry must contain 19 unique implementations",
    )


def get_math_implementation(math_spec_id: str) -> MathImplementationRecordV1:
    if not isinstance(math_spec_id, str) or not math_spec_id:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            "math specification identity must be nonempty text",
        )
    try:
        return IMPLEMENTATION_REGISTRY[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"math implementation is not allowlisted: {math_spec_id}",
        ) from exc


def get_math_callable(math_spec_id: str) -> Callable[..., object]:
    return get_math_implementation(math_spec_id).callable
