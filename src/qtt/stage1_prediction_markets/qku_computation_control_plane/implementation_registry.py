"""Single allowlisted registry for the immutable Step-12 mathematical callables."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal, localcontext
from itertools import combinations, product
import math
from random import Random
from statistics import NormalDist
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from .context import (
    canonical_probability_decimal,
    decimal_context_v1,
    exact_decimal,
    finite_float,
)
from .errors import ContractValidationError, NumericDomainError, ReasonCode
from .models import (
    BenchmarkSignConvention,
    ComputationImplementationV1,
    ObjectiveSense,
    VariableDomain,
)


DecimalInput = Decimal | str | int
PROBABILITY_NORMALIZATION_ULP_MULTIPLIER = 8


def _fail(message: str, reason: ReasonCode = ReasonCode.OUT_OF_DOMAIN) -> None:
    raise NumericDomainError(reason, message)


def _probability(value: object, *, field_name: str) -> float:
    result = finite_float(value, field_name=field_name)
    if not 0.0 <= result <= 1.0:
        _fail(f"{field_name} must be in [0, 1]")
    return result


def _probability_decimal(value: object, *, field_name: str) -> Decimal:
    return canonical_probability_decimal(value, field_name=field_name)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class ProbabilityNormalizationReceiptV1:
    original_sum: Decimal
    tolerance: Decimal
    normalization_applied: bool
    canonical_decimal_vector: tuple[Decimal, ...]
    normalized_decimal_vector: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        for name in ("original_sum", "tolerance"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a finite Decimal",
                )
        if type(self.normalization_applied) is not bool:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "normalization_applied must be an exact boolean",
            )
        for name in ("canonical_decimal_vector", "normalized_decimal_vector"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(
                    not isinstance(value, Decimal)
                    or not value.is_finite()
                    or value < 0
                    or value > 1
                    for value in values
                )
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a nonempty finite probability tuple",
                )
        if len(self.canonical_decimal_vector) != len(
            self.normalized_decimal_vector
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "probability normalization vectors must be aligned",
            )
        if self.tolerance <= 0:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "probability normalization tolerance must be positive",
            )


@dataclass(frozen=True, slots=True)
class QuantityAndFrictionTermsV1:
    quantity: Decimal
    acquisition_cost: Decimal
    fees: Decimal
    expected_slippage: Decimal
    expected_impact: Decimal

    def __post_init__(self) -> None:
        for name in (
            "quantity",
            "acquisition_cost",
            "fees",
            "expected_slippage",
            "expected_impact",
        ):
            value = _nonnegative(
                exact_decimal(getattr(self, name), field_name=name),
                field_name=name,
            )
            object.__setattr__(self, name, value)


def normalize_probability_vector(
    probabilities: Sequence[object],
) -> ProbabilityNormalizationReceiptV1:
    """Validate and canonically normalize a declared float64 probability vector."""

    if isinstance(probabilities, (str, bytes)) or not isinstance(
        probabilities, Sequence
    ) or not probabilities:
        _fail("probabilities must be a nonempty declared sequence")
    float_probabilities = tuple(
        _probability(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(probabilities)
    )
    original_float_sum = math.fsum(float_probabilities)
    tolerance_float = (
        PROBABILITY_NORMALIZATION_ULP_MULTIPLIER
        * math.ulp(1.0)
        * len(float_probabilities)
    )
    if (
        not math.isfinite(original_float_sum)
        or abs(original_float_sum - 1.0) > tolerance_float
    ):
        _fail("probabilities must sum to one within the declared tolerance")
    canonical = tuple(
        _probability_decimal(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(probabilities)
    )
    with localcontext(decimal_context_v1()):
        canonical_sum = sum(canonical, Decimal(0))
        tolerance = Decimal(repr(tolerance_float))
        if canonical_sum <= 0 or abs(canonical_sum - Decimal(1)) > tolerance:
            _fail("probabilities must sum to one within the declared tolerance")
        normalized = tuple(value / canonical_sum for value in canonical)
    return ProbabilityNormalizationReceiptV1(
        original_sum=Decimal(repr(original_float_sum)),
        tolerance=Decimal(repr(tolerance_float)),
        normalization_applied=canonical_sum != Decimal(1),
        canonical_decimal_vector=canonical,
        normalized_decimal_vector=normalized,
    )


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
    quantity_and_friction_terms: QuantityAndFrictionTermsV1,
) -> Decimal:
    if not probabilities or len(probabilities) != len(payoffs):
        _fail("probability and payoff vectors must be nonempty and aligned")
    if not isinstance(quantity_and_friction_terms, QuantityAndFrictionTermsV1):
        _fail(
            "quantity_and_friction_terms must be a typed Decimal record",
            ReasonCode.INVALID_CONTRACT,
        )
    normalization = normalize_probability_vector(probabilities)
    decimal_payoffs = [
        _cash(value, field_name=f"payoffs[{index}]")
        for index, value in enumerate(payoffs)
    ]
    friction = (
        quantity_and_friction_terms.acquisition_cost,
        quantity_and_friction_terms.fees,
        quantity_and_friction_terms.expected_slippage,
        quantity_and_friction_terms.expected_impact,
    )
    with localcontext(decimal_context_v1()):
        expected_payoff = sum(
            sorted(
                probability * payoff
                for probability, payoff in zip(
                    normalization.normalized_decimal_vector,
                    decimal_payoffs,
                    strict=True,
                )
            ),
            Decimal(0),
        )
        return (
            quantity_and_friction_terms.quantity * expected_payoff
            - sum(friction, Decimal(0))
        )


def _vector(value: object, *, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _fail(f"{field_name} must be a declared sequence")
    return tuple(value)


def compute_math_08_brier_score(
    p: object,
    y: object,
) -> float:
    probability = p
    outcome = y
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
    p: object,
    y: object,
    *,
    clip_epsilon: object = math.ulp(1.0),
) -> float:
    probability = p
    outcome = y
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
    z_value = NormalDist().inv_cdf(
        1.0 - (1.0 - confidence_value) / 2.0
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
    expected_block_length: object,
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
    block = finite_float(
        expected_block_length,
        field_name="expected_block_length",
    )
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
    loss_differentials: Sequence[Sequence[object]],
    *,
    sign_convention: BenchmarkSignConvention | None = None,
    seed: int,
    replicates: int = 1000,
    mean_block_length: object = 2,
    alpha: object = 0.05,
) -> RealityCheckResultV1:
    if not isinstance(sign_convention, BenchmarkSignConvention):
        _fail("benchmark sign convention must be explicitly declared")
    if not loss_differentials:
        _fail("time-by-candidate differential matrix must be nonempty")
    time_rows = tuple(
        tuple(
            finite_float(
                value,
                field_name=f"loss_differentials[{row}][{column}]",
            )
            for column, value in enumerate(time_row)
        )
        for row, time_row in enumerate(loss_differentials)
    )
    length = len(time_rows)
    candidate_count = len(time_rows[0])
    if (
        length < 2
        or candidate_count < 1
        or any(len(time_row) != candidate_count for time_row in time_rows)
    ):
        _fail("differentials must have shape [time,candidate] with time >= 2")
    if not any(value != 0.0 for time_row in time_rows for value in time_row):
        _fail("all-zero loss differentials are statistically uninformative")
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


def _finite_vector(values: Sequence[object], *, field_name: str) -> tuple[float, ...]:
    if (
        isinstance(values, (str, bytes))
        or not isinstance(values, Sequence)
        or not values
    ):
        _fail(f"{field_name} must be a nonempty declared sequence")
    return tuple(
        finite_float(value, field_name=f"{field_name}[{index}]")
        for index, value in enumerate(values)
    )


def _sample_standard_deviation(values: Sequence[float], *, field_name: str) -> float:
    if len(values) < 2:
        _fail(f"{field_name} requires at least two observations")
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / (
        len(values) - 1
    )
    if variance <= 0.0 or not math.isfinite(variance):
        _fail(f"{field_name} requires positive finite sample variance")
    return math.sqrt(variance)


@dataclass(frozen=True, slots=True)
class HansenSPAResultV1:
    statistic: float
    p_value: float
    reject: bool
    seed: int
    candidate_count: int
    observation_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "statistic", finite_float(self.statistic, field_name="statistic")
        )
        object.__setattr__(
            self, "p_value", _probability(self.p_value, field_name="p_value")
        )
        if type(self.reject) is not bool:
            _fail("SPA rejection state must be an exact boolean")
        for name in ("seed", "candidate_count", "observation_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                _fail(f"{name} must be an exact integer")
        if self.candidate_count <= 0 or self.observation_count < 2:
            _fail("SPA result dimensions are invalid")


def compute_math_16_hansen_spa(
    loss_differentials: Sequence[Sequence[object]] | None = None,
    *,
    differentials: Sequence[Sequence[object]] | None = None,
    seed: int,
    replicates: int = 1000,
    mean_block_length: object = 2,
    alpha: object = 0.05,
) -> HansenSPAResultV1:
    """Compute a seed-controlled SPA max statistic with common bootstrap draws."""

    if (loss_differentials is None) == (differentials is None):
        _fail("supply exactly one declared SPA differential matrix")
    source = loss_differentials if loss_differentials is not None else differentials
    assert source is not None
    if isinstance(source, (str, bytes)) or not isinstance(source, Sequence) or not source:
        _fail("SPA differentials must be a nonempty [time,candidate] matrix")
    rows = tuple(
        _finite_vector(row, field_name=f"loss_differentials[{index}]")
        for index, row in enumerate(source)
    )
    observations = len(rows)
    candidates = len(rows[0])
    if observations < 2 or any(len(row) != candidates for row in rows):
        _fail("SPA differentials must have aligned [time,candidate] shape")
    if isinstance(seed, bool) or not isinstance(seed, int):
        _fail("SPA seed must be an explicit integer")
    if (
        isinstance(replicates, bool)
        or not isinstance(replicates, int)
        or replicates <= 0
    ):
        _fail("SPA replicates must be a positive integer")
    block = finite_float(mean_block_length, field_name="mean_block_length")
    if not 1.0 <= block <= observations:
        _fail("SPA mean block length must be in [1, observation count]")
    alpha_value = _probability(alpha, field_name="alpha")
    if alpha_value in (0.0, 1.0):
        _fail("SPA alpha must be in (0,1)")
    columns = tuple(
        tuple(rows[row][column] for row in range(observations))
        for column in range(candidates)
    )
    if not any(value != 0.0 for row in rows for value in row):
        return HansenSPAResultV1(
            statistic=0.0,
            p_value=1.0,
            reject=False,
            seed=seed,
            candidate_count=candidates,
            observation_count=observations,
        )
    means = tuple(math.fsum(column) / observations for column in columns)
    standard_deviations = tuple(
        _sample_standard_deviation(column, field_name=f"candidate[{index}]")
        for index, column in enumerate(columns)
    )
    observed = max(
        0.0,
        *(
            math.sqrt(observations) * mean / deviation
            for mean, deviation in zip(
                means, standard_deviations, strict=True
            )
        ),
    )
    rng = Random(seed)
    exceedances = 0
    for _ in range(replicates):
        indices = _stationary_indices(observations, block, rng)
        bootstrap_statistic = max(
            0.0,
            *(
                math.sqrt(observations)
                * (
                    math.fsum(column[index] for index in indices)
                    / observations
                    - max(mean, 0.0)
                )
                / deviation
                for column, mean, deviation in zip(
                    columns, means, standard_deviations, strict=True
                )
            ),
        )
        if bootstrap_statistic >= observed:
            exceedances += 1
    p_value = exceedances / replicates
    return HansenSPAResultV1(
        statistic=observed,
        p_value=p_value,
        reject=p_value <= alpha_value,
        seed=seed,
        candidate_count=candidates,
        observation_count=observations,
    )


@dataclass(frozen=True, slots=True)
class ProbabilisticSharpeResultV1:
    psr: float
    z_score: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "psr", _probability(self.psr, field_name="psr"))
        object.__setattr__(
            self, "z_score", finite_float(self.z_score, field_name="z_score")
        )


def compute_math_17_probabilistic_sharpe_ratio(
    sharpe_hat: object,
    sharpe_ref: object,
    n: int,
    skewness: object,
    kurtosis: object,
) -> ProbabilisticSharpeResultV1:
    observed = finite_float(sharpe_hat, field_name="sharpe_hat")
    reference = finite_float(sharpe_ref, field_name="sharpe_ref")
    skew = finite_float(skewness, field_name="skewness")
    non_excess_kurtosis = finite_float(kurtosis, field_name="kurtosis")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 1:
        _fail("PSR observation count must be an integer greater than one")
    denominator_squared = (
        1.0
        - skew * observed
        + ((non_excess_kurtosis - 1.0) / 4.0) * observed * observed
    )
    if denominator_squared <= 0.0 or not math.isfinite(denominator_squared):
        _fail("PSR denominator must be positive and finite")
    z_score = (
        (observed - reference)
        * math.sqrt(n - 1)
        / math.sqrt(denominator_squared)
    )
    return ProbabilisticSharpeResultV1(
        psr=NormalDist().cdf(z_score),
        z_score=z_score,
    )


@dataclass(frozen=True, slots=True)
class DeflatedSharpeResultV1:
    dsr: float
    reference_sharpe: float
    effective_trial_count: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "dsr", _probability(self.dsr, field_name="dsr"))
        object.__setattr__(
            self,
            "reference_sharpe",
            finite_float(self.reference_sharpe, field_name="reference_sharpe"),
        )
        count = finite_float(
            self.effective_trial_count, field_name="effective_trial_count"
        )
        if count < 1.0:
            _fail("effective_trial_count must be at least one")
        object.__setattr__(self, "effective_trial_count", count)


def compute_math_18_deflated_sharpe_ratio(
    trial_sharpes: Sequence[object],
    effective_trial_count: object,
    candidate_moments: Mapping[str, object],
) -> DeflatedSharpeResultV1:
    sharpes = _finite_vector(trial_sharpes, field_name="trial_sharpes")
    if not isinstance(candidate_moments, Mapping):
        _fail("candidate_moments must be a typed mapping")
    required = {"sharpe_hat", "n", "skewness", "kurtosis"}
    if set(candidate_moments) < required:
        _fail("candidate_moments is missing required PSR fields")
    effective = finite_float(
        effective_trial_count, field_name="effective_trial_count"
    )
    if effective < 1.0:
        _fail("effective_trial_count must be at least one")
    trial_std = (
        0.0
        if len(sharpes) == 1
        else _sample_standard_deviation(sharpes, field_name="trial_sharpes")
    )
    if effective == 1.0 or trial_std == 0.0:
        reference = 0.0
    else:
        euler_mascheroni = 0.5772156649015329
        first = NormalDist().inv_cdf(1.0 - 1.0 / effective)
        second = NormalDist().inv_cdf(
            1.0 - 1.0 / (effective * math.e)
        )
        reference = trial_std * (
            (1.0 - euler_mascheroni) * first
            + euler_mascheroni * second
        )
    n = candidate_moments["n"]
    if isinstance(n, bool) or not isinstance(n, int):
        _fail("candidate_moments.n must be an integer")
    psr = compute_math_17_probabilistic_sharpe_ratio(
        candidate_moments["sharpe_hat"],
        reference,
        n,
        candidate_moments["skewness"],
        candidate_moments["kurtosis"],
    )
    return DeflatedSharpeResultV1(
        dsr=psr.psr,
        reference_sharpe=reference,
        effective_trial_count=effective,
    )


@dataclass(frozen=True, slots=True)
class PBOResultV1:
    pbo: float
    split_oos_relative_ranks: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pbo", _probability(self.pbo, field_name="pbo"))
        ranks = tuple(
            _probability(value, field_name=f"split_oos_relative_ranks[{index}]")
            for index, value in enumerate(self.split_oos_relative_ranks)
        )
        if not ranks:
            _fail("PBO requires at least one split rank")
        object.__setattr__(self, "split_oos_relative_ranks", ranks)


def compute_math_19_probability_of_backtest_overfitting(
    performance_matrix: Sequence[Sequence[object]] | None = None,
    S: int | None = None,
    *,
    split_oos_relative_ranks: Sequence[object] | None = None,
) -> PBOResultV1:
    if split_oos_relative_ranks is not None:
        if performance_matrix is not None or S is not None:
            _fail("PBO sufficient-statistic and full-matrix paths are exclusive")
        ranks = _finite_vector(
            split_oos_relative_ranks,
            field_name="split_oos_relative_ranks",
        )
        if any(rank <= 0.0 or rank >= 1.0 for rank in ranks):
            _fail("PBO relative ranks must be strictly inside (0,1)")
    else:
        if (
            performance_matrix is None
            or isinstance(performance_matrix, (str, bytes))
            or not isinstance(performance_matrix, Sequence)
            or not performance_matrix
            or isinstance(S, bool)
            or not isinstance(S, int)
            or S < 2
            or S % 2
        ):
            _fail("PBO requires a matrix and an even partition count >= 2")
        rows = tuple(
            _finite_vector(row, field_name=f"performance_matrix[{index}]")
            for index, row in enumerate(performance_matrix)
        )
        trial_count = len(rows[0])
        if trial_count < 2 or any(len(row) != trial_count for row in rows):
            _fail("PBO matrix must be aligned with at least two trials")
        if S > len(rows):
            _fail("PBO partition count cannot exceed observation count")
        blocks = tuple(
            tuple(
                range(
                    (index * len(rows)) // S,
                    ((index + 1) * len(rows)) // S,
                )
            )
            for index in range(S)
        )
        derived: list[float] = []
        all_blocks = frozenset(range(S))
        for train_blocks in combinations(range(S), S // 2):
            test_blocks = tuple(sorted(all_blocks - frozenset(train_blocks)))
            train_indices = tuple(
                index for block in train_blocks for index in blocks[block]
            )
            test_indices = tuple(
                index for block in test_blocks for index in blocks[block]
            )
            in_sample = tuple(
                math.fsum(rows[index][trial] for index in train_indices)
                / len(train_indices)
                for trial in range(trial_count)
            )
            winner = max(
                range(trial_count), key=lambda trial: (in_sample[trial], -trial)
            )
            out_of_sample = tuple(
                math.fsum(rows[index][trial] for index in test_indices)
                / len(test_indices)
                for trial in range(trial_count)
            )
            position = sorted(
                range(trial_count),
                key=lambda trial: (out_of_sample[trial], trial),
            ).index(winner)
            derived.append((position + 1) / (trial_count + 1))
        ranks = tuple(derived)
    pbo = sum(rank <= 0.5 for rank in ranks) / len(ranks)
    return PBOResultV1(pbo=pbo, split_oos_relative_ranks=tuple(ranks))


@dataclass(frozen=True, slots=True)
class PurgedSplitResultV1:
    training_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    purged_indices: tuple[int, ...]
    embargoed_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        for name in (
            "training_indices",
            "test_indices",
            "purged_indices",
            "embargoed_indices",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    for value in values
                )
                or len(values) != len(set(values))
            ):
                _fail(f"{name} must be a unique nonnegative integer tuple")
        if set(self.training_indices) & set(self.test_indices):
            _fail("purged training and test indices must be disjoint")


def compute_math_20_purged_kfold_with_embargo(
    sample_intervals: Sequence[Sequence[object]],
    *,
    test_indices: Sequence[int],
    embargo_horizon: object,
) -> PurgedSplitResultV1:
    if (
        isinstance(sample_intervals, (str, bytes))
        or not isinstance(sample_intervals, Sequence)
        or not sample_intervals
    ):
        _fail("sample_intervals must be a nonempty ordered sequence")
    intervals: list[tuple[float, float]] = []
    for index, interval in enumerate(sample_intervals):
        if (
            isinstance(interval, (str, bytes))
            or not isinstance(interval, Sequence)
            or len(interval) != 2
        ):
            _fail(f"sample_intervals[{index}] must be [start,end]")
        start = finite_float(interval[0], field_name=f"interval[{index}].start")
        end = finite_float(interval[1], field_name=f"interval[{index}].end")
        if end < start:
            _fail("sample interval end cannot precede start")
        intervals.append((start, end))
    if (
        isinstance(test_indices, (str, bytes))
        or not isinstance(test_indices, Sequence)
        or not test_indices
        or any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index >= len(intervals)
            for index in test_indices
        )
        or len(set(test_indices)) != len(test_indices)
    ):
        _fail("test_indices must be a unique known integer sequence")
    embargo = finite_float(embargo_horizon, field_name="embargo_horizon")
    if embargo < 0.0:
        _fail("embargo_horizon cannot be negative")
    test_set = frozenset(test_indices)
    test_intervals = tuple(intervals[index] for index in test_indices)
    purged: list[int] = []
    embargoed: list[int] = []
    training: list[int] = []
    for index, (start, end) in enumerate(intervals):
        if index in test_set:
            continue
        if any(start <= test_end and end >= test_start for test_start, test_end in test_intervals):
            purged.append(index)
        elif any(
            test_end < start < test_end + embargo
            for _test_start, test_end in test_intervals
        ):
            embargoed.append(index)
        else:
            training.append(index)
    return PurgedSplitResultV1(
        training_indices=tuple(training),
        test_indices=tuple(sorted(test_set)),
        purged_indices=tuple(purged),
        embargoed_indices=tuple(embargoed),
    )


@dataclass(frozen=True, slots=True)
class CPCVResultV1:
    test_group_paths: tuple[tuple[int, ...], ...]
    split_count: int
    every_split_purged_and_embargoed: bool
    no_post_hoc_path_selection: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.test_group_paths, tuple)
            or not self.test_group_paths
            or any(
                not isinstance(path, tuple)
                or not path
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    for value in path
                )
                for path in self.test_group_paths
            )
        ):
            _fail("CPCV paths must be nonempty immutable integer groups")
        if (
            isinstance(self.split_count, bool)
            or not isinstance(self.split_count, int)
            or self.split_count != len(self.test_group_paths)
        ):
            _fail("CPCV split_count must equal the enumerated path count")
        if (
            type(self.every_split_purged_and_embargoed) is not bool
            or type(self.no_post_hoc_path_selection) is not bool
            or not self.every_split_purged_and_embargoed
            or not self.no_post_hoc_path_selection
        ):
            _fail("CPCV must preserve purge/embargo and no-selection invariants")


def compute_math_21_combinatorial_purged_cross_validation(
    N_groups: int,
    k_test_groups: int,
) -> CPCVResultV1:
    if (
        isinstance(N_groups, bool)
        or not isinstance(N_groups, int)
        or N_groups < 2
        or isinstance(k_test_groups, bool)
        or not isinstance(k_test_groups, int)
        or not 1 <= k_test_groups < N_groups
    ):
        _fail("CPCV requires integer 1 <= k_test_groups < N_groups")
    paths = tuple(combinations(range(N_groups), k_test_groups))
    return CPCVResultV1(
        test_group_paths=paths,
        split_count=len(paths),
        every_split_purged_and_embargoed=True,
    )


@dataclass(frozen=True, slots=True)
class DoublyRobustResultV1:
    dr_estimate: float
    importance_weights: tuple[float, ...]
    effective_sample_size: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dr_estimate",
            finite_float(self.dr_estimate, field_name="dr_estimate"),
        )
        weights = _finite_vector(
            self.importance_weights, field_name="importance_weights"
        )
        if any(weight < 0.0 for weight in weights):
            _fail("importance weights must be nonnegative")
        object.__setattr__(self, "importance_weights", weights)
        ess = finite_float(
            self.effective_sample_size, field_name="effective_sample_size"
        )
        if ess <= 0.0:
            _fail("effective sample size must be positive")
        object.__setattr__(self, "effective_sample_size", ess)


def _effective_sample_size(weights: Sequence[float]) -> float:
    total = math.fsum(weights)
    squared = math.fsum(weight * weight for weight in weights)
    if total <= 0.0 or squared <= 0.0:
        _fail("importance weights require positive total and squared mass")
    return total * total / squared


def compute_math_22_doubly_robust_off_policy_evaluation(
    samples: Sequence[Mapping[str, object]],
) -> DoublyRobustResultV1:
    if (
        isinstance(samples, (str, bytes))
        or not isinstance(samples, Sequence)
        or not samples
    ):
        _fail("DR OPE requires nonempty typed samples")
    values: list[float] = []
    weights: list[float] = []
    required = {"mu_logged", "pi_logged", "pi_q_sum", "q_logged", "reward"}
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping) or set(sample) < required:
            _fail(f"samples[{index}] is missing a DR field")
        mu = _probability(sample["mu_logged"], field_name=f"samples[{index}].mu")
        pi = _probability(sample["pi_logged"], field_name=f"samples[{index}].pi")
        if mu <= 0.0 and pi > 0.0:
            _fail("DR target action lacks positive behavior-policy support")
        q_sum = finite_float(
            sample["pi_q_sum"], field_name=f"samples[{index}].pi_q_sum"
        )
        q_logged = finite_float(
            sample["q_logged"], field_name=f"samples[{index}].q_logged"
        )
        reward = finite_float(
            sample["reward"], field_name=f"samples[{index}].reward"
        )
        weight = 0.0 if pi == 0.0 else pi / mu
        weights.append(weight)
        values.append(q_sum + weight * (reward - q_logged))
    return DoublyRobustResultV1(
        dr_estimate=math.fsum(values) / len(values),
        importance_weights=tuple(weights),
        effective_sample_size=_effective_sample_size(weights),
    )


def _aligned_weights_and_rewards(
    weights: Sequence[object],
    rewards: Sequence[object],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    weight_values = _finite_vector(weights, field_name="weights")
    reward_values = _finite_vector(rewards, field_name="rewards")
    if len(weight_values) != len(reward_values):
        _fail("importance weights and rewards must be aligned")
    if any(weight < 0.0 for weight in weight_values):
        _fail("importance weights must be nonnegative")
    return weight_values, reward_values


def compute_math_23_inverse_propensity_score_ope(
    weights: Sequence[object],
    rewards: Sequence[object],
) -> float:
    weight_values, reward_values = _aligned_weights_and_rewards(weights, rewards)
    return math.fsum(
        weight * reward
        for weight, reward in zip(weight_values, reward_values, strict=True)
    ) / len(weight_values)


def compute_math_24_self_normalized_ips(
    weights: Sequence[object],
    rewards: Sequence[object],
) -> float:
    weight_values, reward_values = _aligned_weights_and_rewards(weights, rewards)
    denominator = math.fsum(weight_values)
    if denominator <= 0.0:
        _fail("SNIPS requires positive total weight")
    numerator = math.fsum(
        weight * reward
        for weight, reward in zip(weight_values, reward_values, strict=True)
    )
    _effective_sample_size(weight_values)
    return numerator / denominator


@dataclass(frozen=True, slots=True)
class SwitchOPEResultV1:
    switch_value: float
    selected_tau: float
    importance_corrected_indices: tuple[int, ...]
    direct_model_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "switch_value",
            finite_float(self.switch_value, field_name="switch_value"),
        )
        tau = finite_float(self.selected_tau, field_name="selected_tau")
        if tau <= 0.0:
            _fail("selected_tau must be positive")
        object.__setattr__(self, "selected_tau", tau)
        for name in ("importance_corrected_indices", "direct_model_indices"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    for value in values
                )
                or len(values) != len(set(values))
            ):
                _fail(f"{name} must be a unique nonnegative integer tuple")
        if set(self.importance_corrected_indices) & set(self.direct_model_indices):
            _fail("SWITCH OPE index partitions must be disjoint")


def compute_math_25_switch_ope(
    weights: Sequence[object],
    rewards: Sequence[object],
    direct_estimates: Sequence[object],
    tau: object,
) -> SwitchOPEResultV1:
    weight_values, reward_values = _aligned_weights_and_rewards(weights, rewards)
    direct_values = _finite_vector(direct_estimates, field_name="direct_estimates")
    if len(direct_values) != len(weight_values):
        _fail("SWITCH direct estimates must align with logged rows")
    threshold = finite_float(tau, field_name="tau")
    if threshold <= 0.0:
        _fail("SWITCH tau must be positive")
    importance = tuple(
        index for index, weight in enumerate(weight_values) if weight <= threshold
    )
    direct = tuple(
        index for index, weight in enumerate(weight_values) if weight > threshold
    )
    contributions = tuple(
        weight_values[index] * reward_values[index]
        if index in importance
        else direct_values[index]
        for index in range(len(weight_values))
    )
    return SwitchOPEResultV1(
        switch_value=math.fsum(contributions) / len(contributions),
        selected_tau=threshold,
        importance_corrected_indices=importance,
        direct_model_indices=direct,
    )


@dataclass(frozen=True, slots=True)
class KalshiBinaryBookTouchesV1:
    yes_best_bid: Decimal
    no_best_bid: Decimal
    yes_implied_ask: Decimal
    no_implied_ask: Decimal
    payout: Decimal

    def __post_init__(self) -> None:
        payout = exact_decimal(self.payout, field_name="payout")
        if payout <= 0:
            _fail("book payout must be positive")
        object.__setattr__(self, "payout", payout)
        for name in (
            "yes_best_bid",
            "no_best_bid",
            "yes_implied_ask",
            "no_implied_ask",
        ):
            value = exact_decimal(getattr(self, name), field_name=name)
            if value < 0 or value > payout:
                _fail(f"{name} must be inside the payout domain")
            object.__setattr__(self, name, value)


def _best_bid(
    value: DecimalInput | Sequence[DecimalInput],
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            _fail(f"{field_name} ladder cannot be empty")
        levels = tuple(
            exact_decimal(level, field_name=f"{field_name}[{index}]")
            for index, level in enumerate(value)
        )
        return max(levels)
    return exact_decimal(value, field_name=field_name)  # type: ignore[arg-type]


def compute_math_36_kalshi_binary_book_transform(
    yes_bids: DecimalInput | Sequence[DecimalInput],
    no_bids: DecimalInput | Sequence[DecimalInput],
    payout: DecimalInput,
) -> KalshiBinaryBookTouchesV1:
    payout_value = exact_decimal(payout, field_name="payout")
    if payout_value <= 0:
        _fail("payout must be positive")
    yes_best = _best_bid(yes_bids, field_name="yes_bids")
    no_best = _best_bid(no_bids, field_name="no_bids")
    if (
        yes_best < 0
        or no_best < 0
        or yes_best > payout_value
        or no_best > payout_value
    ):
        _fail("binary book bid levels must lie in [0,payout]")
    return KalshiBinaryBookTouchesV1(
        yes_best_bid=yes_best,
        no_best_bid=no_best,
        yes_implied_ask=payout_value - no_best,
        no_implied_ask=payout_value - yes_best,
        payout=payout_value,
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
            or self.i >= self.j
        ):
            _fail("QUBO interactions require exact upper-triangular indices i < j")
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
        seen: set[tuple[int, int]] = set()
        for term in self.upper_terms:
            if term.j >= len(diagonal):
                _fail("QUBO upper term references an unknown variable")
            key = (term.i, term.j)
            if key in seen:
                _fail("QUBO upper-triangular coefficients must be unique")
            seen.add(key)
        object.__setattr__(
            self,
            "upper_terms",
            tuple(
                sorted(
                    self.upper_terms,
                    key=lambda term: (term.i, term.j),
                )
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
            "MATH-16": _metadata(
                "studentized maximum of positive benchmark loss differentials "
                "with bootstrap null centering",
                (
                    "Require at least five material candidates by master-plan gate.",
                    "Reject zero or nonfinite studentization variance except the "
                    "certified all-zero null structural invariant.",
                ),
                (
                    "Estimate candidate-specific variance consistently.",
                    "Apply SPA null recentering.",
                    "Use common bootstrap draws.",
                    "Report statistic and p-value.",
                ),
                "White Reality Check",
            ),
            "MATH-17": _metadata(
                "PSR=Phi((SR_hat-SR_ref)*sqrt(n-1)/"
                "sqrt(1-gamma3*SR_hat+((gamma4-1)/4)*SR_hat^2))",
                (
                    "Require n>1 and positive finite denominator.",
                    "Annualization basis must match SR_hat and SR_ref.",
                ),
                (
                    "Compute denominator term.",
                    "Standardize Sharpe difference.",
                    "Apply standard normal CDF.",
                ),
                "Block-bootstrap Sharpe uncertainty",
            ),
            "MATH-18": _metadata(
                "DSR=PSR(SR_hat, SR_ref=E[max Sharpe under N_eff trials]); "
                "expected-max threshold uses trial Sharpe variance and "
                "extreme-value approximation",
                (
                    "Require effective trial count >= 1 and full material trial "
                    "inventory.",
                    "Never use only the winning trials.",
                ),
                (
                    "Estimate cross-trial Sharpe variance.",
                    "Compute expected maximum reference threshold using "
                    "Euler-Mascheroni extreme-value approximation.",
                    "Call MATH-17 using that threshold.",
                ),
                "Raw PSR against fixed reference Sharpe",
            ),
            "MATH-19": _metadata(
                "PBO = fraction of CSCV splits for which logit(relative OOS "
                "rank of IS winner) <= 0",
                (
                    "Require S even, adequate observations per block and full "
                    "material trial inventory.",
                    "No random subset of combinations.",
                ),
                (
                    "Partition time into S contiguous blocks.",
                    "Enumerate every S/2 training-block combination.",
                    "Select IS winner.",
                    "Rank its OOS performance and compute logit.",
                    "PBO is the nonpositive-logit fraction.",
                ),
                "DSR with effective trials",
            ),
            "MATH-20": _metadata(
                "remove training samples whose information/label intervals "
                "overlap the validation interval; embargo samples inside "
                "declared post-validation look-forward horizon",
                (
                    "No arbitrary percentage embargo.",
                    "Reject missing interval metadata for overlapping labels.",
                ),
                (
                    "Construct validation intervals.",
                    "Purge every overlapping training interval.",
                    "Apply exact embargo after each validation interval.",
                    "Record removed indices and reasons.",
                ),
                "Walk-forward for non-overlapping labels",
            ),
            "MATH-21": _metadata(
                "enumerate declared combinations of test groups; purge interval "
                "overlap and embargo each test path; aggregate path-wise results "
                "without post-hoc path selection",
                (
                    "Require 1 <= k < N and sufficient support per path.",
                    "No cherry-picking paths.",
                ),
                (
                    "Partition chronologically.",
                    "Enumerate group combinations.",
                    "Apply MATH-20 purge and embargo to each path.",
                    "Aggregate all paths with declared statistic.",
                ),
                "Purged K-fold and walk-forward",
            ),
            "MATH-22": _metadata(
                "DR_i=sum_a pi(a|x_i) qhat(x_i,a) + "
                "[pi(a_i|x_i)/mu(a_i|x_i)] * [r_i-qhat(x_i,a_i)]; "
                "estimate=mean_i DR_i",
                (
                    "Require mu>0 wherever pi>0.",
                    "Reject unsupported target action.",
                    "Record weight distribution and effective sample size.",
                ),
                (
                    "Cross-fit qhat so each row is predicted out of fold.",
                    "Compute target-policy direct term.",
                    "Add importance residual correction.",
                    "Average and bootstrap by dependence unit.",
                ),
                "IPS, SNIPS and SWITCH",
            ),
            "MATH-23": _metadata(
                "IPS=mean_i [pi(a_i|x_i)/mu(a_i|x_i)] r_i",
                (
                    "Require positive logged propensity and support.",
                    "Any clipping must be parameterized and separately reported.",
                ),
                (
                    "Compute exact importance weights.",
                    "Multiply observed reward.",
                    "Average and return weight diagnostics.",
                ),
                "DR and SNIPS",
            ),
            "MATH-24": _metadata(
                "SNIPS=sum_i w_i r_i / sum_i w_i",
                (
                    "Require nonnegative finite weights and positive total weight.",
                ),
                (
                    "Compute numerator and denominator with compensated summation.",
                    "Divide and report effective sample size.",
                    "Reject a nonpositive or nonfinite normalized-weight "
                    "denominator.",
                ),
                "DR and IPS",
            ),
            "MATH-25": _metadata(
                "use importance correction when w_i <= tau and direct "
                "reward-model estimate when w_i > tau; tau selected by nested "
                "offline estimated-MSE validation",
                (
                    "Require predeclared grid and support.",
                    "No selection on final evaluation outcomes.",
                ),
                (
                    "For each tau, compute nested validation bias/variance or "
                    "estimated-MSE criterion.",
                    "Select minimum criterion with smallest-tau deterministic "
                    "tie-break.",
                    "Refit on full outer training data and evaluate held-out data.",
                ),
                "DR, IPS and SNIPS",
            ),
            "MATH-36": _metadata(
                "for unit payout, implied opposite ask = 1 - "
                "opposite_side_best_bid; generalized ask = payout - opposite_bid",
                (
                    "Reject missing payout basis, invalid levels or "
                    "sequence-stale book.",
                ),
                (
                    "Parse both ladders.",
                    "Take highest bid as last level.",
                    "Derive opposite ask only when payout identity is verified.",
                    "Record derivation provenance.",
                ),
                "Direct executable ask if future provider schema supplies it",
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
        "MATH-16",
        "HANSEN_SPA",
        "MODEL_RISK",
        "compute_math_16_hansen_spa",
        compute_math_16_hansen_spa,
        seed_required=True,
    ),
    _record(
        "MATH-17",
        "PROBABILISTIC_SHARPE_RATIO",
        "MODEL_RISK",
        "compute_math_17_probabilistic_sharpe_ratio",
        compute_math_17_probabilistic_sharpe_ratio,
    ),
    _record(
        "MATH-18",
        "DEFLATED_SHARPE_RATIO",
        "MODEL_RISK",
        "compute_math_18_deflated_sharpe_ratio",
        compute_math_18_deflated_sharpe_ratio,
    ),
    _record(
        "MATH-19",
        "PROBABILITY_OF_BACKTEST_OVERFITTING",
        "MODEL_RISK",
        "compute_math_19_probability_of_backtest_overfitting",
        compute_math_19_probability_of_backtest_overfitting,
    ),
    _record(
        "MATH-20",
        "PURGED_KFOLD_WITH_EMBARGO",
        "VALIDATION",
        "compute_math_20_purged_kfold_with_embargo",
        compute_math_20_purged_kfold_with_embargo,
    ),
    _record(
        "MATH-21",
        "COMBINATORIAL_PURGED_CROSS_VALIDATION",
        "VALIDATION",
        "compute_math_21_combinatorial_purged_cross_validation",
        compute_math_21_combinatorial_purged_cross_validation,
    ),
    _record(
        "MATH-22",
        "DOUBLY_ROBUST_OFF_POLICY_EVALUATION",
        "OFF_POLICY_EVALUATION",
        "compute_math_22_doubly_robust_off_policy_evaluation",
        compute_math_22_doubly_robust_off_policy_evaluation,
    ),
    _record(
        "MATH-23",
        "INVERSE_PROPENSITY_SCORE_OPE",
        "OFF_POLICY_EVALUATION",
        "compute_math_23_inverse_propensity_score_ope",
        compute_math_23_inverse_propensity_score_ope,
    ),
    _record(
        "MATH-24",
        "SELF_NORMALIZED_IPS",
        "OFF_POLICY_EVALUATION",
        "compute_math_24_self_normalized_ips",
        compute_math_24_self_normalized_ips,
    ),
    _record(
        "MATH-25",
        "SWITCH_OPE",
        "OFF_POLICY_EVALUATION",
        "compute_math_25_switch_ope",
        compute_math_25_switch_ope,
    ),
    _record(
        "MATH-36",
        "KALSHI_BINARY_BOOK_TRANSFORM",
        "PROVIDER_MARKET_DATA",
        "compute_math_36_kalshi_binary_book_transform",
        compute_math_36_kalshi_binary_book_transform,
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
TRANCHE_A_MATH_IDS = (
    *(f"MATH-{index:02d}" for index in range(1, 16)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
TRANCHE_B_MATH_IDS = (
    *(f"MATH-{index:02d}" for index in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
if (
    len(_ENTRIES) != 30
    or len(IMPLEMENTATION_REGISTRY) != 30
    or set(_MATH_SPECIFICATION_METADATA) != set(IMPLEMENTATION_REGISTRY)
    or len(TRANCHE_A_MATH_IDS) != 19
    or len(TRANCHE_B_MATH_IDS) != 30
    or not set(TRANCHE_A_MATH_IDS) < set(TRANCHE_B_MATH_IDS)
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "the centralized registry must contain the 30 unique A/B implementations",
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
