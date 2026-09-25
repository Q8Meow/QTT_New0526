"""Single registry for 19 preserved predecessors and 30 active v3.4 callables."""

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


# ST12-B v3.4 production procedures.  These consume only already-resolved typed
# values; owner/PIT/freshness resolution remains outside formula mathematics.


def _v34_list(value: object, name: str, *, minimum: int = 1) -> list[object]:
    if (
        isinstance(value, str | bytes)
        or not isinstance(value, Sequence)
        or len(value) < minimum
    ):
        _fail(f"{name} must be a sequence with at least {minimum} item(s)")
    return list(value)


def _v34_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(f"{name} must be a mapping")
    return value


def _v34_positive_int(value: object, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{name} must be an integer >= {minimum}")
    return value


def _v34_mean(values: Sequence[float]) -> float:
    if not values:
        _fail("mean requires a nonempty sequence")
    return math.fsum(values) / len(values)


def _v34_sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        _fail("sample variance requires at least two values")
    center = _v34_mean(values)
    return math.fsum((value - center) ** 2 for value in values) / (
        len(values) - 1
    )


def _v34_matrix(value: object, name: str) -> list[list[float]]:
    rows = _v34_list(value, name)
    if any(
        isinstance(row, str | bytes) or not isinstance(row, Sequence) or not row
        for row in rows
    ):
        _fail(f"{name} must be a nonempty rectangular matrix")
    width = len(rows[0])  # type: ignore[arg-type]
    if any(len(row) != width for row in rows):  # type: ignore[arg-type]
        _fail(f"{name} must be rectangular")
    return [
        [
            finite_float(item, field_name=f"{name}[{i}][{j}]")
            for j, item in enumerate(row)  # type: ignore[union-attr]
        ]
        for i, row in enumerate(rows)
    ]


def _v34_probability_rows(
    probability_rows: object,
    outcome_indices: object,
) -> tuple[list[list[float]], list[int]]:
    rows = _v34_list(probability_rows, "probability_rows")
    outcomes = _v34_list(outcome_indices, "outcome_indices")
    if len(rows) != len(outcomes):
        _fail("probability_rows and outcome_indices must align")
    width: int | None = None
    parsed: list[list[float]] = []
    labels: list[int] = []
    for row_index, raw_row in enumerate(rows):
        raw = _v34_list(raw_row, f"probability_rows[{row_index}]", minimum=2)
        if width is None:
            width = len(raw)
        elif len(raw) != width:
            _fail("all probability rows must have the same class count")
        probabilities = [
            _probability(value, field_name=f"probability_rows[{row_index}][{j}]")
            for j, value in enumerate(raw)
        ]
        if abs(math.fsum(probabilities) - 1.0) > (
            PROBABILITY_NORMALIZATION_ULP_MULTIPLIER
            * math.ulp(1.0)
            * len(probabilities)
        ):
            _fail("each probability row must sum to one")
        outcome = outcomes[row_index]
        if (
            isinstance(outcome, bool)
            or not isinstance(outcome, int)
            or not 0 <= outcome < len(probabilities)
        ):
            _fail("outcome index is outside the class domain")
        parsed.append(probabilities)
        labels.append(outcome)
    return parsed, labels


def compute_math_01_v34(
    contract_price: DecimalInput,
    payout_per_winning_contract: DecimalInput,
) -> Decimal:
    return compute_math_01_binary_implied_probability(
        contract_price, payout_per_winning_contract
    )


def compute_math_02_v34(
    calibrated_model_probability: object,
    market_implied_probability: object,
    calibration_state: str,
) -> float:
    if calibration_state != "CALIBRATED_FOR_DECLARED_CONTEXT":
        _fail("calibration_state must be CALIBRATED_FOR_DECLARED_CONTEXT")
    return compute_math_02_probability_edge(
        calibrated_model_probability,
        market_implied_probability,
        calibrated=True,
    )


def _v34_book_state(
    *,
    same_instrument_snapshot: object,
    snapshot_state: object,
) -> None:
    if same_instrument_snapshot is not True:
        _fail("book fields must come from the same instrument snapshot")
    if snapshot_state != "CURRENT_CONTIGUOUS_BOOK":
        _fail("book snapshot must be current and contiguous")


def compute_math_03_v34(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    payout: DecimalInput,
    same_instrument_snapshot: bool,
    snapshot_state: str,
) -> Decimal:
    _v34_book_state(
        same_instrument_snapshot=same_instrument_snapshot,
        snapshot_state=snapshot_state,
    )
    return compute_math_03_orderbook_midpoint(
        best_bid, best_ask, payout=payout, stale=False, auction_state=False
    )


def compute_math_04_v34(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    payout: DecimalInput,
    same_instrument_snapshot: bool,
    snapshot_state: str,
) -> Decimal:
    _v34_book_state(
        same_instrument_snapshot=same_instrument_snapshot,
        snapshot_state=snapshot_state,
    )
    return compute_math_04_full_spread(
        best_bid, best_ask, payout=payout, stale=False, auction_state=False
    )


def compute_math_05_v34(
    best_bid: DecimalInput,
    best_ask: DecimalInput,
    payout: DecimalInput,
    same_instrument_snapshot: bool,
    snapshot_state: str,
) -> dict[str, Decimal]:
    midpoint = compute_math_03_v34(
        best_bid,
        best_ask,
        payout,
        same_instrument_snapshot,
        snapshot_state,
    )
    spread = compute_math_04_v34(
        best_bid,
        best_ask,
        payout,
        same_instrument_snapshot,
        snapshot_state,
    )
    if midpoint <= 0:
        _fail("relative spread requires a positive midpoint")
    with localcontext(decimal_context_v1()):
        ratio = spread / midpoint
        return {
            "relative_spread_ratio": ratio,
            "relative_spread_bps": ratio * Decimal(10_000),
        }


_SIGNED_CASHFLOW_BASIS = (
    "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE"
)


def _v34_named_costs(
    *,
    platform_fee_total: DecimalInput,
    builder_fee_total: DecimalInput,
    other_fee_total: DecimalInput,
    expected_rebate_total: DecimalInput,
    exit_slippage_reserve_total: DecimalInput,
    market_impact_reserve_total: DecimalInput,
    latency_adverse_selection_reserve_total: DecimalInput,
    capital_time_cost_reserve_total: DecimalInput,
) -> tuple[Decimal, Decimal]:
    cost_values = tuple(
        _nonnegative(_cash(value, field_name=name), field_name=name)
        for name, value in (
            ("platform_fee_total", platform_fee_total),
            ("builder_fee_total", builder_fee_total),
            ("other_fee_total", other_fee_total),
            ("exit_slippage_reserve_total", exit_slippage_reserve_total),
            ("market_impact_reserve_total", market_impact_reserve_total),
            (
                "latency_adverse_selection_reserve_total",
                latency_adverse_selection_reserve_total,
            ),
            ("capital_time_cost_reserve_total", capital_time_cost_reserve_total),
        )
    )
    rebate = _nonnegative(
        _cash(expected_rebate_total, field_name="expected_rebate_total"),
        field_name="expected_rebate_total",
    )
    return sum(cost_values, Decimal(0)), rebate


def compute_math_06_binary_contract_expected_net_cash_v2(
    p_win: object,
    p_void: object,
    fill_probability: object,
    entry_trade_cashflow_total: DecimalInput,
    win_terminal_cashflow_total: DecimalInput,
    lose_terminal_cashflow_total: DecimalInput,
    void_terminal_cashflow_total: DecimalInput,
    no_fill_cashflow_total: DecimalInput,
    platform_fee_total: DecimalInput,
    builder_fee_total: DecimalInput,
    other_fee_total: DecimalInput,
    expected_rebate_total: DecimalInput,
    exit_slippage_reserve_total: DecimalInput,
    market_impact_reserve_total: DecimalInput,
    latency_adverse_selection_reserve_total: DecimalInput,
    capital_time_cost_reserve_total: DecimalInput,
    cashflow_basis: str,
) -> dict[str, Decimal]:
    if cashflow_basis != _SIGNED_CASHFLOW_BASIS:
        _fail("cashflow basis must be the exact signed total-account convention")
    win = _probability_decimal(p_win, field_name="p_win")
    void = _probability_decimal(p_void, field_name="p_void")
    fill = _probability_decimal(fill_probability, field_name="fill_probability")
    with localcontext(decimal_context_v1()):
        lose = Decimal(1) - win - void
        if lose < 0:
            _fail("p_win + p_void may not exceed one")
        entry = _cash(
            entry_trade_cashflow_total, field_name="entry_trade_cashflow_total"
        )
        win_cash = _cash(
            win_terminal_cashflow_total,
            field_name="win_terminal_cashflow_total",
        )
        lose_cash = _cash(
            lose_terminal_cashflow_total,
            field_name="lose_terminal_cashflow_total",
        )
        void_cash = _cash(
            void_terminal_cashflow_total,
            field_name="void_terminal_cashflow_total",
        )
        no_fill = _cash(
            no_fill_cashflow_total, field_name="no_fill_cashflow_total"
        )
        costs, rebate = _v34_named_costs(
            platform_fee_total=platform_fee_total,
            builder_fee_total=builder_fee_total,
            other_fee_total=other_fee_total,
            expected_rebate_total=expected_rebate_total,
            exit_slippage_reserve_total=exit_slippage_reserve_total,
            market_impact_reserve_total=market_impact_reserve_total,
            latency_adverse_selection_reserve_total=(
                latency_adverse_selection_reserve_total
            ),
            capital_time_cost_reserve_total=capital_time_cost_reserve_total,
        )
        terminal = win * win_cash + lose * lose_cash + void * void_cash
        if_filled = entry + terminal - costs + rebate
        expected = fill * if_filled + (Decimal(1) - fill) * no_fill
        return {
            "expected_net_cash": expected,
            "expected_net_cash_if_filled": if_filled,
            "expected_terminal_cashflow": terminal,
            "p_lose": lose,
        }


def compute_math_07_multi_outcome_expected_net_cash_v2(
    outcome_ids: Sequence[object],
    outcome_probabilities: Sequence[object],
    outcome_terminal_cashflow_totals: Sequence[DecimalInput],
    probability_simplex_tolerance: DecimalInput,
    fill_probability: object,
    entry_trade_cashflow_total: DecimalInput,
    no_fill_cashflow_total: DecimalInput,
    platform_fee_total: DecimalInput,
    builder_fee_total: DecimalInput,
    other_fee_total: DecimalInput,
    expected_rebate_total: DecimalInput,
    exit_slippage_reserve_total: DecimalInput,
    market_impact_reserve_total: DecimalInput,
    latency_adverse_selection_reserve_total: DecimalInput,
    capital_time_cost_reserve_total: DecimalInput,
    cashflow_basis: str,
) -> dict[str, object]:
    if cashflow_basis != _SIGNED_CASHFLOW_BASIS:
        _fail("cashflow basis must be the exact signed total-account convention")
    ids = _v34_list(outcome_ids, "outcome_ids", minimum=2)
    if (
        any(not isinstance(value, str) or not value for value in ids)
        or len(ids) != len(set(ids))
    ):
        _fail("outcome_ids must be unique nonempty text")
    probabilities = _v34_list(
        outcome_probabilities, "outcome_probabilities", minimum=2
    )
    cashflows = _v34_list(
        outcome_terminal_cashflow_totals,
        "outcome_terminal_cashflow_totals",
        minimum=2,
    )
    if len(ids) != len(probabilities) or len(ids) != len(cashflows):
        _fail("outcome IDs, probabilities, and cashflows must align")
    decimal_probabilities = tuple(
        _probability_decimal(value, field_name=f"outcome_probabilities[{index}]")
        for index, value in enumerate(probabilities)
    )
    tolerance = exact_decimal(
        probability_simplex_tolerance,
        field_name="probability_simplex_tolerance",
    )
    if tolerance < 0:
        _fail("probability simplex tolerance must be nonnegative")
    with localcontext(decimal_context_v1()):
        original_sum = sum(decimal_probabilities, Decimal(0))
        if abs(original_sum - Decimal(1)) > tolerance or original_sum <= 0:
            _fail("outcome probabilities are outside the declared simplex tolerance")
        normalization_applied = original_sum != Decimal(1)
        normalized = (
            tuple(value / original_sum for value in decimal_probabilities)
            if normalization_applied
            else decimal_probabilities
        )
        terminals = tuple(
            _cash(value, field_name=f"outcome_terminal_cashflow_totals[{index}]")
            for index, value in enumerate(cashflows)
        )
        expected_terminal = sum(
            (
                probability * cashflow
                for probability, cashflow in zip(
                    normalized, terminals, strict=True
                )
            ),
            Decimal(0),
        )
        costs, rebate = _v34_named_costs(
            platform_fee_total=platform_fee_total,
            builder_fee_total=builder_fee_total,
            other_fee_total=other_fee_total,
            expected_rebate_total=expected_rebate_total,
            exit_slippage_reserve_total=exit_slippage_reserve_total,
            market_impact_reserve_total=market_impact_reserve_total,
            latency_adverse_selection_reserve_total=(
                latency_adverse_selection_reserve_total
            ),
            capital_time_cost_reserve_total=capital_time_cost_reserve_total,
        )
        entry = _cash(
            entry_trade_cashflow_total, field_name="entry_trade_cashflow_total"
        )
        no_fill = _cash(
            no_fill_cashflow_total, field_name="no_fill_cashflow_total"
        )
        fill = _probability_decimal(fill_probability, field_name="fill_probability")
        if_filled = entry + expected_terminal - costs + rebate
        expected = fill * if_filled + (Decimal(1) - fill) * no_fill
        return {
            "expected_net_cash": expected,
            "expected_net_cash_if_filled": if_filled,
            "expected_terminal_cashflow": expected_terminal,
            "outcome_ids": tuple(ids),
            "normalized_probabilities": normalized,
            "original_probability_sum": original_sum,
            "normalization_applied": normalization_applied,
        }


def compute_math_08_v34(
    probability_rows: Sequence[object],
    outcome_indices: Sequence[object],
) -> dict[str, object]:
    rows, outcomes = _v34_probability_rows(probability_rows, outcome_indices)
    per_observation = tuple(
        compute_math_08_brier_score(
            row,
            tuple(1 if index == outcome else 0 for index in range(len(row))),
        )
        for row, outcome in zip(rows, outcomes, strict=True)
    )
    return {
        "mean_brier_score": math.fsum(per_observation) / len(per_observation),
        "per_observation": per_observation,
    }


def compute_math_09_v34(
    probability_rows: Sequence[object],
    outcome_indices: Sequence[object],
    clip_epsilon: object,
) -> dict[str, object]:
    rows, outcomes = _v34_probability_rows(probability_rows, outcome_indices)
    epsilon = finite_float(clip_epsilon, field_name="clip_epsilon")
    if not 0.0 < epsilon < 0.5:
        _fail("clip_epsilon must be in (0,0.5)")
    per_observation = tuple(
        -math.log(min(max(row[outcome], epsilon), 1.0 - epsilon))
        for row, outcome in zip(rows, outcomes, strict=True)
    )
    return {
        "mean_log_loss": math.fsum(per_observation) / len(per_observation),
        "per_observation": per_observation,
    }


def _v34_type7(values: Sequence[float], probability: float) -> float:
    return _percentile(values, probability)


def compute_math_10_expected_calibration_error_v2(
    probabilities: Sequence[object],
    outcomes: Sequence[object],
    bin_policy: str,
    bin_count: int,
) -> dict[str, object]:
    raw_probabilities = _v34_list(probabilities, "probabilities")
    raw_outcomes = _v34_list(outcomes, "outcomes")
    if len(raw_probabilities) != len(raw_outcomes):
        _fail("probabilities and outcomes must align")
    ps = tuple(
        _probability(value, field_name=f"probabilities[{index}]")
        for index, value in enumerate(raw_probabilities)
    )
    ys: list[int] = []
    for index, value in enumerate(raw_outcomes):
        if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
            _fail(f"outcomes[{index}] must be an integer 0 or 1")
        ys.append(value)
    count = _v34_positive_int(bin_count, "bin_count")
    if bin_policy == "EQUAL_WIDTH":
        edges = [index / count for index in range(count + 1)]
    elif bin_policy == "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES":
        if count > len(ps):
            _fail("equal-frequency bin_count may not exceed sample count")
        raw_edges = [
            _v34_type7(ps, index / count) for index in range(count + 1)
        ]
        raw_edges[0], raw_edges[-1] = 0.0, 1.0
        edges = []
        for edge in raw_edges:
            if not edges or edge > edges[-1]:
                edges.append(edge)
        if len(edges) < 2:
            edges = [0.0, 1.0]
    else:
        _fail("unsupported calibration bin policy")
    bins: list[dict[str, object]] = []
    expected = 0.0
    for bin_index, (left, right) in enumerate(zip(edges, edges[1:])):
        indices = [
            index
            for index, probability in enumerate(ps)
            if left <= probability < right
            or (
                bin_index == len(edges) - 2
                and left <= probability <= right
            )
        ]
        inclusive = bin_index == len(edges) - 2
        if not indices:
            bins.append(
                {
                    "bin_index": bin_index,
                    "left": left,
                    "right": right,
                    "right_inclusive": inclusive,
                    "count": 0,
                    "mean_confidence": None,
                    "empirical_frequency": None,
                    "absolute_gap": None,
                }
            )
            continue
        confidence = math.fsum(ps[index] for index in indices) / len(indices)
        frequency = math.fsum(ys[index] for index in indices) / len(indices)
        gap = abs(confidence - frequency)
        expected += len(indices) / len(ps) * gap
        bins.append(
            {
                "bin_index": bin_index,
                "left": left,
                "right": right,
                "right_inclusive": inclusive,
                "count": len(indices),
                "mean_confidence": confidence,
                "empirical_frequency": frequency,
                "absolute_gap": gap,
            }
        )
    if sum(int(row["count"]) for row in bins) != len(ps):
        _fail("calibration bins did not cover every observation exactly once")
    return {
        "expected_calibration_error": expected,
        "bin_policy": bin_policy,
        "requested_bin_count": count,
        "effective_edges": tuple(edges),
        "bins": tuple(bins),
    }


def compute_math_11_v34(
    successes: int,
    trials: int,
    confidence: object,
) -> dict[str, float]:
    interval = compute_math_11_wilson_score_interval(
        successes, trials, confidence=confidence
    )
    return {"lower": interval.lower, "upper": interval.upper}


def _v34_multiple_result(result: MultipleTestingResultV1) -> dict[str, object]:
    return {
        "largest_rank": result.largest_rank,
        "rejected_original_indices": result.rejected_original_indices,
        "adjusted_p_values": result.adjusted_p_values,
        "correction": result.correction,
    }


def compute_math_12_v34(
    p_values: Sequence[object],
    q: object,
) -> dict[str, object]:
    return _v34_multiple_result(compute_math_12_benjamini_hochberg(p_values, q))


def compute_math_13_v34(
    p_values: Sequence[object],
    q: object,
) -> dict[str, object]:
    return _v34_multiple_result(compute_math_13_benjamini_yekutieli(p_values, q))


def compute_math_14_stationary_bootstrap_mean_interval_v2(
    series: Sequence[object],
    expected_block_length: object,
    seed: int,
    replicates: int,
    confidence: object,
    interval_method: str,
) -> dict[str, object]:
    if interval_method != "PERCENTILE_TYPE7":
        _fail("only PERCENTILE_TYPE7 is frozen")
    result = compute_math_14_stationary_bootstrap_mean_interval(
        series,
        expected_block_length,
        seed=seed,
        replicates=replicates,
        confidence=confidence,
    )
    return {
        "sample_mean": result.sample_mean,
        "lower": result.lower,
        "upper": result.upper,
        "bootstrap_distribution": result.bootstrap_distribution,
        "seed": result.seed,
        "replicates": replicates,
        "expected_block_length": result.mean_block_length,
        "interval_method": interval_method,
    }


def _v34_differentials(
    loss_differentials: object,
    sign_convention: str,
) -> list[list[float]]:
    matrix = _v34_matrix(loss_differentials, "loss_differentials")
    if (
        sign_convention
        == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"
    ):
        return matrix
    if (
        sign_convention
        == "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"
    ):
        return [[-value for value in row] for row in matrix]
    _fail("explicit frozen benchmark sign convention is required")


def compute_math_15_white_reality_check_v2(
    loss_differentials: Sequence[Sequence[object]],
    sign_convention: str,
    seed: int,
    replicates: int,
    expected_block_length: object,
    alpha: object,
) -> dict[str, object]:
    matrix = _v34_differentials(loss_differentials, sign_convention)
    observation_count, candidate_count = len(matrix), len(matrix[0])
    if observation_count < 2 or candidate_count < 1:
        _fail("White reality check matrix is too small")
    if isinstance(seed, bool) or not isinstance(seed, int):
        _fail("seed must be an explicit integer")
    repetitions = _v34_positive_int(replicates, "replicates")
    block = finite_float(
        expected_block_length, field_name="expected_block_length"
    )
    if not 1.0 <= block <= observation_count:
        _fail("expected_block_length must be in [1,n]")
    alpha_value = finite_float(alpha, field_name="alpha")
    if not 0.0 < alpha_value < 1.0:
        _fail("alpha must be in (0,1)")
    series = [
        [matrix[row][column] for row in range(observation_count)]
        for column in range(candidate_count)
    ]
    means = [_v34_mean(candidate) for candidate in series]
    statistic = max(
        0.0, max(math.sqrt(observation_count) * value for value in means)
    )
    if all(value == 0.0 for row in matrix for value in row):
        simulated = [0.0] * repetitions
        p_value = 1.0
    else:
        rng = Random(seed)
        simulated = []
        exceedances = 0
        for _ in range(repetitions):
            indices = _stationary_indices(observation_count, block, rng)
            draw = max(
                0.0,
                max(
                    math.sqrt(observation_count)
                    * (
                        math.fsum(candidate[index] for index in indices)
                        / observation_count
                        - center
                    )
                    for candidate, center in zip(series, means, strict=True)
                ),
            )
            simulated.append(draw)
            if draw >= statistic:
                exceedances += 1
        p_value = (1 + exceedances) / (repetitions + 1)
    return {
        "statistic": statistic,
        "p_value": p_value,
        "reject": p_value <= alpha_value,
        "candidate_means": tuple(means),
        "simulated_statistics": tuple(simulated),
        "recenter_policy": (
            "CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN"
        ),
    }


def _v34_spa_long_run_variance(series: Sequence[float], block: float) -> float:
    count = len(series)
    center = _v34_mean(series)
    demeaned = tuple(value - center for value in series)
    restart_probability = 1.0 / block
    variance = math.fsum(value * value for value in demeaned) / count
    for lag in range(1, count):
        weight = (1.0 - lag / count) * (
            (1.0 - restart_probability) ** lag
        ) + (lag / count) * (
            (1.0 - restart_probability) ** (count - lag)
        )
        covariance = math.fsum(
            demeaned[index] * demeaned[index + lag]
            for index in range(count - lag)
        ) / count
        variance += 2.0 * weight * covariance
    return max(0.0, variance)


def compute_math_16_hansen_spa(
    loss_differentials: Sequence[Sequence[object]],
    sign_convention: str,
    seed: int,
    replicates: int,
    expected_block_length: object,
    alpha: object,
    recenter_variant: str,
) -> dict[str, object]:
    matrix = _v34_differentials(loss_differentials, sign_convention)
    count, candidate_count = len(matrix), len(matrix[0])
    if count < 3 or candidate_count < 1:
        _fail("Hansen SPA requires at least three observations")
    if recenter_variant != "HANSEN_CONSISTENT_LOG_LOG_THRESHOLD":
        _fail("only the frozen Hansen consistent recenter variant is accepted")
    if isinstance(seed, bool) or not isinstance(seed, int):
        _fail("seed must be an explicit integer")
    repetitions = _v34_positive_int(replicates, "replicates")
    block = finite_float(
        expected_block_length, field_name="expected_block_length"
    )
    if not 1.0 <= block <= count:
        _fail("expected_block_length must be in [1,n]")
    alpha_value = finite_float(alpha, field_name="alpha")
    if not 0.0 < alpha_value < 1.0:
        _fail("alpha must be in (0,1)")
    series = [
        [matrix[row][column] for row in range(count)]
        for column in range(candidate_count)
    ]
    means = [_v34_mean(candidate) for candidate in series]
    variances = [
        _v34_spa_long_run_variance(candidate, block) for candidate in series
    ]
    valid: list[bool] = []
    standardized: list[float] = []
    for index, (center, variance) in enumerate(
        zip(means, variances, strict=True)
    ):
        if variance <= 0:
            if center > 0:
                _fail(
                    f"candidate {index} has positive mean and zero long-run variance"
                )
            valid.append(False)
            standardized.append(float("-inf"))
            continue
        threshold = -math.sqrt(
            variance / count * 2.0 * math.log(math.log(count))
        )
        valid.append(center >= threshold)
        standardized.append(math.sqrt(count) * center / math.sqrt(variance))
    statistic = max(
        0.0,
        max((value for value in standardized if math.isfinite(value)), default=0.0),
    )
    recentered = [
        center if admitted else 0.0
        for center, admitted in zip(means, valid, strict=True)
    ]
    rng = Random(seed)
    simulated: list[float] = []
    exceedances = 0
    for _ in range(repetitions):
        indices = _stationary_indices(count, block, rng)
        candidate_statistics = [
            math.sqrt(count)
            * (
                math.fsum(candidate[index] for index in indices) / count - center
            )
            / math.sqrt(variance)
            for candidate, center, variance in zip(
                series, recentered, variances, strict=True
            )
            if variance > 0
        ]
        draw = max(0.0, max(candidate_statistics, default=0.0))
        simulated.append(draw)
        if draw >= statistic:
            exceedances += 1
    p_value = (1 + exceedances) / (repetitions + 1)
    return {
        "statistic": statistic,
        "p_value": p_value,
        "reject": p_value <= alpha_value,
        "candidate_means": tuple(means),
        "long_run_variances": tuple(variances),
        "consistent_valid_columns": tuple(valid),
        "simulated_statistics": tuple(simulated),
        "recenter_variant": recenter_variant,
    }


def _v34_probabilistic_sharpe(
    estimated_sharpe: object,
    reference_sharpe: object,
    independent_equivalent_observations: int,
    sample_skewness: object,
    sample_non_excess_kurtosis: object,
) -> dict[str, float]:
    estimate = finite_float(estimated_sharpe, field_name="estimated_sharpe")
    reference = finite_float(reference_sharpe, field_name="reference_sharpe")
    count = _v34_positive_int(
        independent_equivalent_observations,
        "independent_equivalent_observations",
        minimum=2,
    )
    skewness = finite_float(sample_skewness, field_name="sample_skewness")
    kurtosis = finite_float(
        sample_non_excess_kurtosis,
        field_name="sample_non_excess_kurtosis",
    )
    if kurtosis < 1.0:
        _fail("sample non-excess kurtosis must be at least one")
    denominator_squared = (
        1.0
        - skewness * estimate
        + (kurtosis - 1.0) / 4.0 * estimate * estimate
    )
    if denominator_squared <= 0:
        _fail("probabilistic Sharpe denominator must be positive")
    z_score = (
        (estimate - reference)
        * math.sqrt(count - 1)
        / math.sqrt(denominator_squared)
    )
    return {
        "probabilistic_sharpe_ratio": NormalDist().cdf(z_score),
        "z_score": z_score,
    }


def compute_math_17_probabilistic_sharpe_ratio(
    estimated_sharpe: object,
    reference_sharpe: object,
    independent_equivalent_observations: int,
    sample_skewness: object,
    sample_non_excess_kurtosis: object,
) -> dict[str, float]:
    return _v34_probabilistic_sharpe(
        estimated_sharpe,
        reference_sharpe,
        independent_equivalent_observations,
        sample_skewness,
        sample_non_excess_kurtosis,
    )


def compute_math_18_deflated_sharpe_ratio(
    complete_material_trial_sharpes: Sequence[object],
    effective_independent_trial_count: object,
    candidate_estimated_sharpe: object,
    candidate_independent_equivalent_observations: int,
    candidate_sample_skewness: object,
    candidate_sample_non_excess_kurtosis: object,
) -> dict[str, float]:
    raw = _v34_list(
        complete_material_trial_sharpes,
        "complete_material_trial_sharpes",
        minimum=2,
    )
    sharpes = tuple(
        finite_float(
            value,
            field_name=f"complete_material_trial_sharpes[{index}]",
        )
        for index, value in enumerate(raw)
    )
    effective_count = finite_float(
        effective_independent_trial_count,
        field_name="effective_independent_trial_count",
    )
    if not 1.0 < effective_count <= len(sharpes):
        _fail(
            "effective independent trial count must be in "
            "(1, complete material trial count]"
        )
    trial_mean = _v34_mean(sharpes)
    trial_variance = _v34_sample_variance(sharpes)
    euler_mascheroni = 0.5772156649015329
    expected_maximum = trial_mean + math.sqrt(trial_variance) * (
        (1.0 - euler_mascheroni)
        * NormalDist().inv_cdf(1.0 - 1.0 / effective_count)
        + euler_mascheroni
        * NormalDist().inv_cdf(1.0 - 1.0 / (effective_count * math.e))
    )
    psr = _v34_probabilistic_sharpe(
        candidate_estimated_sharpe,
        expected_maximum,
        candidate_independent_equivalent_observations,
        candidate_sample_skewness,
        candidate_sample_non_excess_kurtosis,
    )
    return {
        "deflated_sharpe_ratio": psr["probabilistic_sharpe_ratio"],
        "expected_maximum_sharpe_threshold": expected_maximum,
        "trial_mean_sharpe": trial_mean,
        "trial_sharpe_variance": trial_variance,
    }


def _v34_contiguous_groups(length: int, group_count: int) -> list[list[int]]:
    if length % group_count:
        _fail(
            "observation count must be divisible by the frozen exact group count"
        )
    width = length // group_count
    return [
        list(range(group * width, (group + 1) * width))
        for group in range(group_count)
    ]


def _v34_stable_midranks(values: Sequence[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda index: (values[index], index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[cursor]]:
            end += 1
        midrank = ((cursor + 1) + end) / 2.0
        for index in ordered[cursor:end]:
            ranks[index] = midrank
        cursor = end
    return ranks


def compute_math_19_probability_of_backtest_overfitting(
    performance_matrix: Sequence[Sequence[object]],
    strategy_ids: Sequence[str],
    S: int,
) -> dict[str, object]:
    matrix = _v34_matrix(performance_matrix, "performance_matrix")
    strategies = _v34_list(strategy_ids, "strategy_ids")
    if (
        len(strategies) != len(matrix[0])
        or len(strategies) != len(set(strategies))
        or any(not isinstance(value, str) or not value for value in strategies)
    ):
        _fail("strategy_ids must uniquely identify every matrix column")
    group_count = _v34_positive_int(S, "S", minimum=2)
    if group_count % 2:
        _fail("S must be even")
    groups = _v34_contiguous_groups(len(matrix), group_count)
    split_rows: list[dict[str, object]] = []
    logits: list[float] = []
    for train_group_tuple in combinations(
        range(group_count), group_count // 2
    ):
        train_groups = set(train_group_tuple)
        train_indices = [
            index for group in train_groups for index in groups[group]
        ]
        test_indices = [
            index
            for group in range(group_count)
            if group not in train_groups
            for index in groups[group]
        ]
        train_means = [
            math.fsum(matrix[index][column] for index in train_indices)
            / len(train_indices)
            for column in range(len(strategies))
        ]
        best = max(train_means)
        winner = min(
            (
                column
                for column, value in enumerate(train_means)
                if value == best
            ),
            key=lambda column: str(strategies[column]),
        )
        test_means = [
            math.fsum(matrix[index][column] for index in test_indices)
            / len(test_indices)
            for column in range(len(strategies))
        ]
        ranks = _v34_stable_midranks(test_means)
        relative_rank = ranks[winner] / (len(strategies) + 1.0)
        logit = math.log(relative_rank / (1.0 - relative_rank))
        logits.append(logit)
        split_rows.append(
            {
                "train_groups": tuple(train_group_tuple),
                "is_winner_strategy_id": strategies[winner],
                "oos_midrank_worst_1_best_n": ranks[winner],
                "relative_rank": relative_rank,
                "logit": logit,
            }
        )
    return {
        "probability_of_backtest_overfitting": (
            sum(value <= 0.0 for value in logits) / len(logits)
        ),
        "S": group_count,
        "split_count": len(split_rows),
        "logits": tuple(logits),
        "splits": tuple(split_rows),
    }


def _v34_intervals(value: object) -> list[dict[str, object]]:
    raw = _v34_list(value, "sample_intervals")
    rows: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, item in enumerate(raw):
        row = _v34_mapping(item, f"sample_intervals[{index}]")
        identifier = row.get("sample_id")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
        ):
            _fail("sample_id must be unique nonempty text")
        identifiers.add(identifier)
        start = finite_float(
            row.get("start"), field_name=f"sample_intervals[{index}].start"
        )
        end = finite_float(
            row.get("end"), field_name=f"sample_intervals[{index}].end"
        )
        if not start < end:
            _fail("half-open sample intervals require start < end")
        rows.append({"sample_id": identifier, "start": start, "end": end})
    return sorted(
        rows,
        key=lambda row: (
            float(row["start"]),
            float(row["end"]),
            str(row["sample_id"]),
        ),
    )


def _v34_balanced_blocks(length: int, count: int) -> list[list[int]]:
    if not 2 <= count <= length:
        _fail("fold/group count must be in [2,n]")
    base, remainder = divmod(length, count)
    blocks: list[list[int]] = []
    cursor = 0
    for index in range(count):
        width = base + (1 if index < remainder else 0)
        blocks.append(list(range(cursor, cursor + width)))
        cursor += width
    return blocks


def _v34_overlap(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    return float(left["start"]) < float(right["end"]) and float(
        right["start"]
    ) < float(left["end"])


def _v34_merged_intervals(
    rows: Sequence[Mapping[str, object]],
) -> list[tuple[float, float]]:
    ordered = sorted((float(row["start"]), float(row["end"])) for row in rows)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _v34_purged_split(
    intervals: Sequence[Mapping[str, object]],
    test_indices: Sequence[int],
    embargo_duration: float,
) -> dict[str, object]:
    test_set = set(test_indices)
    test = [intervals[index] for index in test_indices]
    merged = _v34_merged_intervals(test)
    train: list[str] = []
    purged: list[str] = []
    embargoed: list[str] = []
    for index, row in enumerate(intervals):
        if index in test_set:
            continue
        identifier = str(row["sample_id"])
        if any(_v34_overlap(row, test_row) for test_row in test):
            purged.append(identifier)
        elif any(
            end
            <= float(row["start"])
            < end + embargo_duration
            for _, end in merged
        ):
            embargoed.append(identifier)
        else:
            train.append(identifier)
    return {
        "test_sample_ids": tuple(str(row["sample_id"]) for row in test),
        "train_sample_ids": tuple(train),
        "purged_sample_ids": tuple(purged),
        "embargoed_sample_ids": tuple(embargoed),
        "merged_test_intervals": tuple(tuple(value) for value in merged),
    }


def compute_math_20_purged_kfold_with_embargo(
    sample_intervals: Sequence[Mapping[str, object]],
    folds: int,
    embargo_duration: object,
) -> dict[str, object]:
    intervals = _v34_intervals(sample_intervals)
    fold_count = _v34_positive_int(folds, "folds", minimum=2)
    embargo = finite_float(embargo_duration, field_name="embargo_duration")
    if embargo < 0:
        _fail("embargo duration must be nonnegative event time")
    blocks = _v34_balanced_blocks(len(intervals), fold_count)
    results: list[dict[str, object]] = []
    for fold_id, indices in enumerate(blocks):
        row = _v34_purged_split(intervals, indices, embargo)
        row["fold_id"] = fold_id
        results.append(row)
    return {
        "ordered_sample_ids": tuple(str(row["sample_id"]) for row in intervals),
        "interval_semantics": "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE",
        "embargo_basis": "TIME_DURATION_AFTER_MERGED_TEST_INTERVAL",
        "folds": tuple(results),
    }


def _v34_set_partitions(
    items: tuple[int, ...], block_size: int
) -> list[tuple[tuple[int, ...], ...]]:
    if not items:
        return [tuple()]
    first = items[0]
    result: list[tuple[tuple[int, ...], ...]] = []
    for rest in combinations(items[1:], block_size - 1):
        block = tuple(sorted((first, *rest)))
        remaining = tuple(item for item in items if item not in block)
        for suffix in _v34_set_partitions(remaining, block_size):
            result.append(tuple(sorted((block, *suffix))))
    return sorted(set(result))


def _v34_resolvable_paths(
    group_count: int, test_group_count: int
) -> list[list[tuple[int, ...]]]:
    if group_count % test_group_count:
        _fail("frozen CPCV exact-cover profile requires k to divide N")
    splits = list(combinations(range(group_count), test_group_count))
    split_set = set(splits)
    partitions = _v34_set_partitions(
        tuple(range(group_count)), test_group_count
    )
    target_count = math.comb(group_count - 1, test_group_count - 1)
    candidates = {
        split: tuple(partition for partition in partitions if split in partition)
        for split in splits
    }

    def solve(
        uncovered: frozenset[tuple[int, ...]],
        chosen: tuple[tuple[tuple[int, ...], ...], ...],
    ) -> tuple[tuple[tuple[int, ...], ...], ...] | None:
        if not uncovered:
            return chosen if len(chosen) == target_count else None
        if len(chosen) >= target_count:
            return None
        pivot = min(
            uncovered,
            key=lambda split: (
                sum(set(partition) <= uncovered for partition in candidates[split]),
                split,
            ),
        )
        for partition in candidates[pivot]:
            members = frozenset(partition)
            if members <= uncovered:
                answer = solve(uncovered - members, (*chosen, partition))
                if answer is not None:
                    return answer
        return None

    solution = solve(frozenset(split_set), tuple())
    if solution is None:
        _fail("deterministic resolvable CPCV path design does not exist")
    return [[tuple(block) for block in partition] for partition in solution]


def compute_math_21_combinatorial_purged_cross_validation(
    sample_intervals: Sequence[Mapping[str, object]],
    N_groups: int,
    k_test_groups: int,
    embargo_duration: object,
    aggregation_rule: str,
) -> dict[str, object]:
    intervals = _v34_intervals(sample_intervals)
    group_count = _v34_positive_int(N_groups, "N_groups", minimum=2)
    test_group_count = _v34_positive_int(
        k_test_groups, "k_test_groups"
    )
    if (
        not 1 <= test_group_count < group_count
        or group_count > len(intervals)
        or group_count > 8
    ):
        _fail("CPCV requires 1<=k<N<=sample_count and N<=8")
    embargo = finite_float(embargo_duration, field_name="embargo_duration")
    if embargo < 0:
        _fail("embargo_duration must be nonnegative")
    if not isinstance(aggregation_rule, str) or not aggregation_rule:
        _fail("aggregation_rule must be an exact method token")
    groups = _v34_balanced_blocks(len(intervals), group_count)
    split_rows: list[dict[str, object]] = []
    split_lookup: dict[tuple[int, ...], int] = {}
    for split_id, group_tuple in enumerate(
        combinations(range(group_count), test_group_count)
    ):
        test_indices = [index for group in group_tuple for index in groups[group]]
        split = _v34_purged_split(intervals, test_indices, embargo)
        split.update(
            {"split_id": split_id, "test_groups": tuple(group_tuple)}
        )
        split_rows.append(split)
        split_lookup[group_tuple] = split_id
    path_partitions = _v34_resolvable_paths(group_count, test_group_count)
    paths = tuple(
        {
            "path_id": path_id,
            "split_ids": tuple(split_lookup[tuple(block)] for block in partition),
            "test_group_partition": tuple(tuple(block) for block in partition),
        }
        for path_id, partition in enumerate(path_partitions)
    )
    expected_path_count = math.comb(group_count - 1, test_group_count - 1)
    if (
        len(paths) != expected_path_count
        or sorted(
            split_id for path in paths for split_id in path["split_ids"]
        )
        != list(range(len(split_rows)))
    ):
        _fail("CPCV path coverage invariant failed")
    return {
        "N_groups": group_count,
        "k_test_groups": test_group_count,
        "split_count": len(split_rows),
        "expected_path_count": expected_path_count,
        "path_count": len(paths),
        "aggregation_rule": aggregation_rule,
        "splits": tuple(split_rows),
        "paths": paths,
    }


def _v34_logged_rows(value: object) -> list[dict[str, object]]:
    raw_rows = _v34_list(value, "logged_rows")
    rows: list[dict[str, object]] = []
    for row_index, raw_row in enumerate(raw_rows):
        row = _v34_mapping(raw_row, f"logged_rows[{row_index}]")
        behavior_raw = _v34_list(
            row.get("behavior_action_probabilities"),
            f"logged_rows[{row_index}].behavior_action_probabilities",
        )
        target_raw = _v34_list(
            row.get("target_action_probabilities"),
            f"logged_rows[{row_index}].target_action_probabilities",
        )
        model_raw = _v34_list(
            row.get("cross_fitted_reward_model_predictions"),
            f"logged_rows[{row_index}].cross_fitted_reward_model_predictions",
        )
        if not len(behavior_raw) == len(target_raw) == len(model_raw):
            _fail("behavior, target, and reward model vectors must align")
        behavior = [
            _probability(value, field_name=f"behavior[{index}]")
            for index, value in enumerate(behavior_raw)
        ]
        target = [
            _probability(value, field_name=f"target[{index}]")
            for index, value in enumerate(target_raw)
        ]
        if (
            abs(math.fsum(behavior) - 1.0) > 1e-12
            or abs(math.fsum(target) - 1.0) > 1e-12
            or any(
                target_probability > 0 and behavior_probability <= 0
                for behavior_probability, target_probability in zip(
                    behavior, target, strict=True
                )
            )
        ):
            _fail("target/behavior policies violate simplex or support")
        model = [
            finite_float(value, field_name=f"reward_model[{index}]")
            for index, value in enumerate(model_raw)
        ]
        action = row.get("logged_action_index")
        fold_id = row.get("fold_id")
        if (
            isinstance(action, bool)
            or not isinstance(action, int)
            or not 0 <= action < len(behavior)
            or isinstance(fold_id, bool)
            or not isinstance(fold_id, int)
            or fold_id < 0
            or row.get("cross_fitted_prediction") is not True
        ):
            _fail("logged action/fold/cross-fit state is invalid")
        rows.append(
            {
                "row_id": str(row.get("row_id")),
                "behavior": behavior,
                "target": target,
                "model": model,
                "action": action,
                "reward": finite_float(
                    row.get("reward"),
                    field_name=f"logged_rows[{row_index}].reward",
                ),
                "fold_id": fold_id,
            }
        )
    return rows


def _v34_logged_row_terms(
    row: Mapping[str, object],
) -> tuple[float, float, float, float]:
    action = int(row["action"])
    behavior = row["behavior"]
    target = row["target"]
    model = row["model"]
    assert isinstance(behavior, list)
    assert isinstance(target, list)
    assert isinstance(model, list)
    mu = float(behavior[action])
    pi = float(target[action])
    if pi > 0 and mu <= 0:
        _fail("logged row violates positivity")
    weight = 0.0 if pi == 0 else pi / mu
    direct = math.fsum(
        float(probability) * float(prediction)
        for probability, prediction in zip(target, model, strict=True)
    )
    reward = float(row["reward"])
    residual = reward - float(model[action])
    return direct, weight, residual, reward


def _v34_effective_sample_size(weights: Sequence[float]) -> float:
    total = math.fsum(weights)
    squares = math.fsum(value * value for value in weights)
    if total <= 0 or squares <= 0:
        _fail("weights require positive total and squared total")
    return total * total / squares


def compute_math_22_doubly_robust_ope(
    logged_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = _v34_logged_rows(logged_rows)
    values: list[float] = []
    weights: list[float] = []
    for row in rows:
        direct, weight, residual, _ = _v34_logged_row_terms(row)
        values.append(direct + weight * residual)
        weights.append(weight)
    return {
        "doubly_robust_estimate": _v34_mean(values),
        "row_values": tuple(values),
        "importance_weights": tuple(weights),
        "effective_sample_size": (
            _v34_effective_sample_size(weights)
            if any(weight > 0 for weight in weights)
            else 0.0
        ),
        "clipping_applied": False,
    }


def compute_math_23_inverse_propensity_score_ope(
    logged_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = _v34_logged_rows(logged_rows)
    values: list[float] = []
    weights: list[float] = []
    for row in rows:
        _, weight, _, reward = _v34_logged_row_terms(row)
        values.append(weight * reward)
        weights.append(weight)
    return {
        "inverse_propensity_score_estimate": _v34_mean(values),
        "row_values": tuple(values),
        "importance_weights": tuple(weights),
        "effective_sample_size": (
            _v34_effective_sample_size(weights)
            if any(weight > 0 for weight in weights)
            else 0.0
        ),
        "clipping_applied": False,
    }


def compute_math_24_self_normalized_ips(
    weights: Sequence[object],
    rewards: Sequence[object],
) -> dict[str, float]:
    raw_weights = _v34_list(weights, "weights")
    raw_rewards = _v34_list(rewards, "rewards")
    if len(raw_weights) != len(raw_rewards):
        _fail("weights and rewards must align")
    parsed_weights = tuple(
        finite_float(value, field_name=f"weights[{index}]")
        for index, value in enumerate(raw_weights)
    )
    parsed_rewards = tuple(
        finite_float(value, field_name=f"rewards[{index}]")
        for index, value in enumerate(raw_rewards)
    )
    if any(value < 0 for value in parsed_weights):
        _fail("importance weights must be nonnegative")
    total = math.fsum(parsed_weights)
    if total <= 0:
        _fail("importance weights must have positive total")
    return {
        "self_normalized_ips_estimate": (
            math.fsum(
                weight * reward
                for weight, reward in zip(
                    parsed_weights, parsed_rewards, strict=True
                )
            )
            / total
        ),
        "weight_sum": total,
        "effective_sample_size": _v34_effective_sample_size(parsed_weights),
    }


def _v34_tau(value: object) -> float:
    if value == "INF":
        return math.inf
    result = finite_float(value, field_name="tau")
    if result < 0:
        _fail("tau must be nonnegative")
    return result


def _v34_switch_value(row: Mapping[str, object], tau: float) -> float:
    direct, weight, residual, _ = _v34_logged_row_terms(row)
    return direct + (weight * residual if weight <= tau else 0.0)


def _v34_switch_bias_bound(
    rows: Sequence[Mapping[str, object]], tau: float, reward_range: float
) -> float:
    masses: list[float] = []
    for row in rows:
        behavior = row["behavior"]
        target = row["target"]
        assert isinstance(behavior, list)
        assert isinstance(target, list)
        mass = math.fsum(
            float(pi)
            for mu, pi in zip(behavior, target, strict=True)
            if float(pi) > 0 and float(pi) / float(mu) > tau
        )
        masses.append(mass)
    return reward_range * _v34_mean(masses)


def compute_math_25_switch_ope(
    logged_rows: Sequence[Mapping[str, object]],
    tau_grid: Sequence[object],
    outer_fold_count: int,
    reward_lower_bound: object,
    reward_upper_bound: object,
) -> dict[str, object]:
    rows = _v34_logged_rows(logged_rows)
    lower = finite_float(
        reward_lower_bound, field_name="reward_lower_bound"
    )
    upper = finite_float(
        reward_upper_bound, field_name="reward_upper_bound"
    )
    if not lower < upper or any(
        not lower <= float(row["reward"]) <= upper for row in rows
    ):
        _fail("reward bounds must be ordered and cover logged rewards")
    fold_count = _v34_positive_int(
        outer_fold_count, "outer_fold_count", minimum=2
    )
    if {int(row["fold_id"]) for row in rows} != set(range(fold_count)):
        _fail("outer fold IDs must cover 0..outer_fold_count-1")
    raw_taus = _v34_list(tau_grid, "tau_grid")
    taus = [_v34_tau(value) for value in raw_taus]
    if taus != sorted(set(taus)):
        _fail("tau_grid must be unique and ascending")
    fold_results: list[dict[str, object]] = []
    held_out_values: list[float] = []
    for fold in range(fold_count):
        train = [row for row in rows if int(row["fold_id"]) != fold]
        held = [row for row in rows if int(row["fold_id"]) == fold]
        if len(train) < 2 or not held:
            _fail("each outer fold needs training and held-out support")
        criteria: list[dict[str, object]] = []
        for tau in taus:
            values = [_v34_switch_value(row, tau) for row in train]
            variance_of_mean = _v34_sample_variance(values) / len(values)
            bias = _v34_switch_bias_bound(train, tau, upper - lower)
            criteria.append(
                {
                    "tau": "INF" if math.isinf(tau) else tau,
                    "variance_of_mean": variance_of_mean,
                    "bias_upper_bound": bias,
                    "estimated_mse_upper_bound": (
                        variance_of_mean + bias * bias
                    ),
                }
            )
        selected_index = min(
            range(len(criteria)),
            key=lambda index: (
                float(criteria[index]["estimated_mse_upper_bound"]),
                taus[index],
            ),
        )
        selected_tau = taus[selected_index]
        values = [_v34_switch_value(row, selected_tau) for row in held]
        held_out_values.extend(values)
        fold_results.append(
            {
                "outer_fold": fold,
                "selected_tau": (
                    "INF" if math.isinf(selected_tau) else selected_tau
                ),
                "criteria": tuple(criteria),
                "held_out_row_values": tuple(values),
            }
        )
    return {
        "switch_ope_estimate": _v34_mean(held_out_values),
        "held_out_row_values": tuple(held_out_values),
        "outer_fold_results": tuple(fold_results),
        "selection_rule": (
            "MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU"
        ),
        "clipping_applied": False,
    }


def compute_math_36_kalshi_binary_book_transform(
    yes_bids: Sequence[DecimalInput],
    no_bids: Sequence[DecimalInput],
    payout: DecimalInput,
    book_sequence: int,
    expected_sequence: int,
    book_state: str,
    price_ranges: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    ranges = tuple(
        ActivePriceGridRangeV1(
            minimum=row.get("minimum"),
            maximum=row.get("maximum"),
            step=row.get("step"),
        )
        for index, raw_row in enumerate(_v34_list(price_ranges, "price_ranges"))
        for row in (_v34_mapping(raw_row, f"price_ranges[{index}]"),)
    )
    snapshot = BinaryBookSnapshotV1(
        snapshot_ref=f"PREDECESSOR_COMPATIBILITY::MATH-36::{book_sequence}",
        sequence_ref=f"PREDECESSOR_COMPATIBILITY::SEQUENCE::{book_sequence}",
        source_binding_ref="PREDECESSOR_IMPLEMENTATION_REGISTRY::MATH-36",
        unit="DECLARED_PAYOUT_UNIT",
        basis="BINARY_CONTRACT_PAYOUT",
        yes_bids=tuple(_v34_list(yes_bids, "yes_bids")),
        no_bids=tuple(_v34_list(no_bids, "no_bids")),
        payout=payout,
        book_sequence=book_sequence,
        expected_sequence=expected_sequence,
        book_state=book_state,
        active_price_grid_ranges=ranges,
    )
    touches = binary_book_implied_asks_v1(snapshot=snapshot)
    return {
        "best_yes_bid": snapshot.yes_bids[-1],
        "best_no_bid": snapshot.no_bids[-1],
        "derived_yes_ask": touches.yes_implied_ask,
        "derived_no_ask": touches.no_implied_ask,
        "book_sequence": touches.book_sequence,
    }


def _v34_binary_assignment(
    value: object, variable_count: int, name: str
) -> list[int]:
    items = _v34_list(value, name, minimum=variable_count)
    if len(items) != variable_count or any(
        isinstance(item, bool)
        or not isinstance(item, int)
        or item not in (0, 1)
        for item in items
    ):
        _fail(f"{name} must contain one binary integer per variable")
    return [int(item) for item in items]


def _v34_canonical_qubo(
    *,
    representation: str,
    diagonal: Sequence[object],
    upper_terms: Sequence[Mapping[str, object]],
    full_symmetric_matrix: Sequence[Sequence[object]],
    constant: object,
) -> dict[str, object]:
    raw_diagonal = _v34_list(diagonal, "diagonal")
    diagonal_values = [
        finite_float(value, field_name=f"diagonal[{index}]")
        for index, value in enumerate(raw_diagonal)
    ]
    variable_count = len(diagonal_values)
    interactions: dict[tuple[int, int], float] = {}
    if representation == "CANONICAL_UPPER_TRIANGULAR":
        if list(full_symmetric_matrix):
            _fail("full_symmetric_matrix must be empty for canonical upper input")
        for index, raw_term in enumerate(
            _v34_list(upper_terms, "upper_terms", minimum=0)
            if upper_terms
            else []
        ):
            term = _v34_mapping(raw_term, f"upper_terms[{index}]")
            i, j = term.get("i"), term.get("j")
            if (
                isinstance(i, bool)
                or isinstance(j, bool)
                or not isinstance(i, int)
                or not isinstance(j, int)
                or not 0 <= i < j < variable_count
                or (i, j) in interactions
            ):
                _fail("upper terms require unique 0<=i<j<n identities")
            interactions[(i, j)] = finite_float(
                term.get("value"), field_name=f"upper_terms[{index}].value"
            )
    elif representation == "FULL_SYMMETRIC_ADAPTER_SUM_OFF_DIAGONAL_PAIRS":
        if list(upper_terms):
            _fail("upper_terms must be empty for the full-matrix adapter")
        matrix = _v34_matrix(
            full_symmetric_matrix, "full_symmetric_matrix"
        )
        if len(matrix) != variable_count or any(
            len(row) != variable_count for row in matrix
        ):
            _fail("full_symmetric_matrix must be n by n")
        for i in range(variable_count):
            if matrix[i][i] != diagonal_values[i]:
                _fail("full matrix diagonal must equal explicit diagonal")
            for j in range(i + 1, variable_count):
                interactions[(i, j)] = matrix[i][j] + matrix[j][i]
    else:
        _fail("unknown QUBO representation")
    return {
        "schema_version": "CANONICAL_QUBO_MODEL_V1",
        "representation": "CANONICAL_UPPER_TRIANGULAR",
        "variable_count": variable_count,
        "diagonal": tuple(diagonal_values),
        "upper_terms": tuple(
            {"i": i, "j": j, "value": interactions[(i, j)]}
            for i, j in sorted(interactions)
        ),
        "constant": finite_float(constant, field_name="constant"),
    }


def _v34_qubo_parts(
    canonical: Mapping[str, object],
) -> tuple[list[float], dict[tuple[int, int], float], float]:
    if (
        canonical.get("schema_version") != "CANONICAL_QUBO_MODEL_V1"
        or canonical.get("representation") != "CANONICAL_UPPER_TRIANGULAR"
    ):
        _fail("canonical QUBO identity fields are inconsistent")
    diagonal = [
        finite_float(value, field_name=f"canonical.diagonal[{index}]")
        for index, value in enumerate(
            _v34_list(canonical.get("diagonal"), "canonical.diagonal")
        )
    ]
    if canonical.get("variable_count") != len(diagonal):
        _fail("canonical QUBO variable count differs from diagonal")
    interactions: dict[tuple[int, int], float] = {}
    raw_terms = canonical.get("upper_terms")
    if not isinstance(raw_terms, Sequence) or isinstance(raw_terms, str | bytes):
        _fail("canonical upper terms must be a sequence")
    for index, raw_term in enumerate(raw_terms):
        term = _v34_mapping(raw_term, f"canonical.upper_terms[{index}]")
        i, j = term.get("i"), term.get("j")
        if (
            isinstance(i, bool)
            or isinstance(j, bool)
            or not isinstance(i, int)
            or not isinstance(j, int)
            or not 0 <= i < j < len(diagonal)
            or (i, j) in interactions
        ):
            _fail("canonical upper interaction identity is invalid")
        interactions[(i, j)] = finite_float(
            term.get("value"),
            field_name=f"canonical.upper_terms[{index}].value",
        )
    return (
        diagonal,
        interactions,
        finite_float(canonical.get("constant"), field_name="canonical.constant"),
    )


def _v34_qubo_energy(
    diagonal: Sequence[float],
    interactions: Mapping[tuple[int, int], float],
    constant: float,
    assignment: Sequence[int],
) -> float:
    return (
        constant
        + math.fsum(
            diagonal[index] * assignment[index]
            for index in range(len(assignment))
        )
        + math.fsum(
            coefficient * assignment[i] * assignment[j]
            for (i, j), coefficient in interactions.items()
        )
    )


def compute_math_46_qubo_upper_triangular_convention_v2(
    representation: str,
    diagonal: Sequence[object],
    upper_terms: Sequence[Mapping[str, object]],
    full_symmetric_matrix: Sequence[Sequence[object]],
    constant: object,
    binary_assignment: Sequence[int],
) -> dict[str, object]:
    canonical = _v34_canonical_qubo(
        representation=representation,
        diagonal=diagonal,
        upper_terms=upper_terms,
        full_symmetric_matrix=full_symmetric_matrix,
        constant=constant,
    )
    diagonal_values, interactions, offset = _v34_qubo_parts(canonical)
    assignment = _v34_binary_assignment(
        binary_assignment, len(diagonal_values), "binary_assignment"
    )
    exhaustive = tuple(
        {
            "binary_assignment": tuple(bits),
            "energy": _v34_qubo_energy(
                diagonal_values, interactions, offset, bits
            ),
        }
        for bits in product((0, 1), repeat=len(diagonal_values))
    ) if len(diagonal_values) <= 12 else ()
    return {
        "canonical_qubo": canonical,
        "binary_assignment": tuple(assignment),
        "energy": _v34_qubo_energy(
            diagonal_values, interactions, offset, assignment
        ),
        "exhaustive_assignments": exhaustive,
    }


def compute_math_47_qubo_to_ising_transform_v2(
    representation: str,
    diagonal: Sequence[object],
    upper_terms: Sequence[Mapping[str, object]],
    full_symmetric_matrix: Sequence[Sequence[object]],
    constant: object,
    binary_assignment: Sequence[int],
) -> dict[str, object]:
    canonical = _v34_canonical_qubo(
        representation=representation,
        diagonal=diagonal,
        upper_terms=upper_terms,
        full_symmetric_matrix=full_symmetric_matrix,
        constant=constant,
    )
    diagonal_values, interactions, qubo_constant = _v34_qubo_parts(canonical)
    assignment = _v34_binary_assignment(
        binary_assignment, len(diagonal_values), "binary_assignment"
    )
    fields = tuple(
        -diagonal_values[index] / 2.0
        - math.fsum(
            coefficient
            for (i, j), coefficient in interactions.items()
            if i == index or j == index
        )
        / 4.0
        for index in range(len(diagonal_values))
    )
    couplers = {
        key: coefficient / 4.0
        for key, coefficient in interactions.items()
    }
    offset = (
        qubo_constant
        + math.fsum(diagonal_values) / 2.0
        + math.fsum(interactions.values()) / 4.0
    )

    def ising_energy(spins: Sequence[int]) -> float:
        return (
            offset
            + math.fsum(
                fields[index] * spins[index]
                for index in range(len(spins))
            )
            + math.fsum(
                coefficient * spins[i] * spins[j]
                for (i, j), coefficient in couplers.items()
            )
        )

    spins = tuple(1 - 2 * value for value in assignment)
    qubo_energy = _v34_qubo_energy(
        diagonal_values, interactions, qubo_constant, assignment
    )
    transformed_energy = ising_energy(spins)
    tolerance = 1e-10 * max(1.0, abs(qubo_energy), abs(transformed_energy))
    if abs(qubo_energy - transformed_energy) > tolerance:
        _fail("QUBO/Ising energy parity failed")
    exhaustive: list[dict[str, object]] = []
    if len(diagonal_values) <= 12:
        for bits in product((0, 1), repeat=len(diagonal_values)):
            spin_row = tuple(1 - 2 * value for value in bits)
            qubo_row = _v34_qubo_energy(
                diagonal_values, interactions, qubo_constant, bits
            )
            ising_row = ising_energy(spin_row)
            if abs(qubo_row - ising_row) > 1e-10 * max(
                1.0, abs(qubo_row), abs(ising_row)
            ):
                _fail("exhaustive QUBO/Ising parity failed")
            exhaustive.append(
                {
                    "binary_assignment": tuple(bits),
                    "spin_assignment": spin_row,
                    "qubo_energy": qubo_row,
                    "ising_energy": ising_row,
                }
            )
    return {
        "binary_to_spin_convention": (
            "x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1"
        ),
        "linear_fields_h": fields,
        "couplers_J": tuple(
            {"i": i, "j": j, "value": couplers[(i, j)]}
            for i, j in sorted(couplers)
        ),
        "offset": offset,
        "binary_assignment": tuple(assignment),
        "spin_assignment": spins,
        "qubo_energy": qubo_energy,
        "ising_energy": transformed_energy,
        "exhaustive_parity_rows": tuple(exhaustive),
    }


def _v34_cqm_variables(
    model: Mapping[str, object],
) -> tuple[dict[str, dict[str, object]], tuple[str, ...]]:
    if model.get("schema_version") != "QTT_CQM_GRAMMAR_V1":
        _fail("CQM model must use QTT_CQM_GRAMMAR_V1")
    raw_variables = _v34_list(model.get("variables"), "model.variables")
    registry: dict[str, dict[str, object]] = {}
    order: list[str] = []
    for index, raw_variable in enumerate(raw_variables):
        variable = _v34_mapping(raw_variable, f"model.variables[{index}]")
        identifier = variable.get("id")
        kind = variable.get("type")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in registry
            or kind not in {"BINARY", "INTEGER", "REAL"}
        ):
            _fail("CQM variable identity or type is invalid")
        lower = finite_float(
            variable.get("lower"), field_name=f"variables[{index}].lower"
        )
        upper = finite_float(
            variable.get("upper"), field_name=f"variables[{index}].upper"
        )
        if lower > upper or kind == "BINARY" and (lower, upper) != (0.0, 1.0):
            _fail("CQM variable bounds are invalid")
        enumeration = [
            finite_float(
                value,
                field_name=f"variables[{index}].enumeration_values",
            )
            for value in _v34_list(
                variable.get("enumeration_values"),
                f"variables[{index}].enumeration_values",
            )
        ]
        if (
            len(enumeration) != len(set(enumeration))
            or any(value < lower or value > upper for value in enumeration)
            or kind in {"BINARY", "INTEGER"}
            and any(value != int(value) for value in enumeration)
        ):
            _fail("CQM enumeration values violate type or bounds")
        if kind == "BINARY" and enumeration != [0.0, 1.0]:
            _fail("binary enumeration must be exactly [0,1]")
        if kind == "INTEGER":
            if lower != int(lower) or upper != int(upper):
                _fail("integer bounds must be integral")
            if enumeration != [
                float(value) for value in range(int(lower), int(upper) + 1)
            ]:
                _fail("integer enumeration must exhaust the declared domain")
        registry[identifier] = {
            "type": kind,
            "lower": lower,
            "upper": upper,
            "unit": variable.get("unit"),
            "enumeration_values": enumeration,
        }
        order.append(identifier)
    return registry, tuple(order)


def _v34_cqm_assignment(
    value: object, registry: Mapping[str, Mapping[str, object]]
) -> dict[str, float]:
    raw = _v34_mapping(value, "assignment")
    if set(raw) != set(registry):
        _fail("CQM assignment must provide every variable exactly once")
    assignment = {
        key: finite_float(raw[key], field_name=f"assignment.{key}")
        for key in raw
    }
    for key, item in assignment.items():
        spec = registry[key]
        if (
            not float(spec["lower"]) <= item <= float(spec["upper"])
            or spec["type"] in {"BINARY", "INTEGER"} and item != int(item)
            or item not in spec["enumeration_values"]  # type: ignore[operator]
        ):
            _fail("CQM assignment violates bounds/type/enumeration")
    return assignment


def _v34_linear_expression(
    value: object, assignment: Mapping[str, float], name: str
) -> float:
    coefficients = _v34_mapping(value, name)
    if set(coefficients) - set(assignment):
        _fail(f"{name} references an unknown variable")
    return math.fsum(
        finite_float(coefficient, field_name=f"{name}.{variable}")
        * assignment[variable]
        for variable, coefficient in coefficients.items()
    )


def _v34_quadratic_expression(
    value: object, assignment: Mapping[str, float], name: str
) -> float:
    raw_terms = value
    if (
        isinstance(raw_terms, str | bytes)
        or not isinstance(raw_terms, Sequence)
    ):
        _fail(f"{name} must be a sequence")
    seen: set[tuple[str, str]] = set()
    result = 0.0
    for index, raw_term in enumerate(raw_terms):
        term = _v34_mapping(raw_term, f"{name}[{index}]")
        u, v = term.get("u"), term.get("v")
        if (
            not isinstance(u, str)
            or not isinstance(v, str)
            or u not in assignment
            or v not in assignment
            or tuple(sorted((u, v))) in seen
        ):
            _fail(f"{name} has an unknown or duplicate quadratic term")
        seen.add(tuple(sorted((u, v))))
        result += (
            finite_float(
                term.get("coefficient"),
                field_name=f"{name}[{index}].coefficient",
            )
            * assignment[u]
            * assignment[v]
        )
    return result


def _v34_constraint_violation(sense: object, lhs: float, rhs: float) -> float:
    if sense == "LE":
        return max(0.0, lhs - rhs)
    if sense == "GE":
        return max(0.0, rhs - lhs)
    if sense == "EQ":
        return abs(lhs - rhs)
    _fail("constraint sense must be LE, GE, or EQ")


def _v34_evaluate_cqm(
    model: Mapping[str, object], assignment: Mapping[str, float]
) -> dict[str, object]:
    sense = model.get("objective_sense")
    if sense not in {"MINIMIZE", "MAXIMIZE"}:
        _fail("objective_sense must be MINIMIZE or MAXIMIZE")
    objective = (
        finite_float(
            model.get("objective_constant"), field_name="objective_constant"
        )
        + _v34_linear_expression(
            model.get("objective_linear"), assignment, "objective_linear"
        )
        + _v34_quadratic_expression(
            model.get("objective_quadratic"),
            assignment,
            "objective_quadratic",
        )
    )
    constraints = model.get("constraints")
    if isinstance(constraints, str | bytes) or not isinstance(
        constraints, Sequence
    ):
        _fail("constraints must be a sequence")
    tolerance = finite_float(
        model.get("feasibility_tolerance"),
        field_name="feasibility_tolerance",
    )
    if tolerance < 0:
        _fail("feasibility_tolerance must be nonnegative")
    seen: set[str] = set()
    evaluations: list[dict[str, object]] = []
    soft_penalty = 0.0
    hard_violation_squared = 0.0
    feasible = True
    for index, raw_constraint in enumerate(constraints):
        constraint = _v34_mapping(
            raw_constraint, f"constraints[{index}]"
        )
        identifier = constraint.get("id")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in seen
        ):
            _fail("constraint identities must be unique nonempty text")
        seen.add(identifier)
        lhs = (
            finite_float(
                constraint.get("constant"),
                field_name=f"constraints[{index}].constant",
            )
            + _v34_linear_expression(
                constraint.get("linear"),
                assignment,
                f"constraints[{index}].linear",
            )
            + _v34_quadratic_expression(
                constraint.get("quadratic"),
                assignment,
                f"constraints[{index}].quadratic",
            )
        )
        rhs = finite_float(
            constraint.get("rhs"),
            field_name=f"constraints[{index}].rhs",
        )
        violation = _v34_constraint_violation(
            constraint.get("sense"), lhs, rhs
        )
        hard = constraint.get("hard")
        weight = finite_float(
            constraint.get("soft_penalty_weight"),
            field_name=f"constraints[{index}].soft_penalty_weight",
        )
        if type(hard) is not bool:
            _fail("constraint hard flag must be an exact boolean")
        if hard:
            if weight != 0.0:
                _fail("hard constraint must have zero soft penalty weight")
            hard_violation_squared += violation * violation
            feasible = feasible and violation <= tolerance
        else:
            if weight <= 0:
                _fail("soft constraint requires positive penalty weight")
            soft_penalty += weight * violation * violation
        evaluations.append(
            {
                "id": identifier,
                "lhs": lhs,
                "sense": constraint.get("sense"),
                "rhs": rhs,
                "violation": violation,
                "hard": hard,
                "soft_penalty_weight": weight,
            }
        )
    penalized = (
        objective + soft_penalty
        if sense == "MINIMIZE"
        else objective - soft_penalty
    )
    return {
        "raw_objective": objective,
        "soft_penalty": soft_penalty,
        "penalized_objective": penalized,
        "original_model_feasible": feasible,
        "hard_violation_squared": hard_violation_squared,
        "constraint_evaluations": tuple(evaluations),
    }


def compute_math_48_constrained_quadratic_model_v2(
    model: Mapping[str, object],
    assignment: Mapping[str, object],
) -> dict[str, object]:
    model_row = _v34_mapping(model, "model")
    registry, order = _v34_cqm_variables(model_row)
    supplied = _v34_cqm_assignment(assignment, registry)
    evaluated = _v34_evaluate_cqm(model_row, supplied)
    total_states = math.prod(
        len(registry[variable]["enumeration_values"])  # type: ignore[arg-type]
        for variable in order
    )
    if total_states > 4096:
        _fail("small exact CQM domain is limited to 4096 assignments")
    all_rows: list[dict[str, object]] = []
    for selected in product(
        *(
            registry[variable]["enumeration_values"]  # type: ignore[misc]
            for variable in order
        )
    ):
        candidate = dict(zip(order, selected, strict=True))
        all_rows.append(
            {
                "assignment": candidate,
                **_v34_evaluate_cqm(model_row, candidate),
            }
        )
    feasible_rows = [
        row for row in all_rows if row["original_model_feasible"]
    ]
    sense = str(model_row["objective_sense"])
    if feasible_rows:
        selector = min if sense == "MINIMIZE" else max
        best = selector(
            feasible_rows,
            key=lambda row: float(row["penalized_objective"]),
        )
        small_exact_solution: dict[str, object] = {
            "state": "EXACT_FEASIBLE_OPTIMUM",
            "assignment": best["assignment"],
            "raw_objective": best["raw_objective"],
            "penalized_objective": best["penalized_objective"],
            "feasible_assignment_count": len(feasible_rows),
            "enumerated_assignment_count": len(all_rows),
        }
    else:
        small_exact_solution = {
            "state": "NO_FEASIBLE_ASSIGNMENT",
            "assignment": None,
            "raw_objective": None,
            "penalized_objective": None,
            "feasible_assignment_count": 0,
            "enumerated_assignment_count": len(all_rows),
        }
    penalty_candidate = model_row.get("conversion_penalty_candidate")
    if penalty_candidate is None:
        adequacy: dict[str, object] = {
            "state": "NOT_APPLICABLE_NATIVE_CQM_NO_CONVERSION_REQUESTED",
            "penalty": None,
            "converted_best_assignment": None,
            "matches_native_feasible_optimum": None,
        }
    else:
        penalty = finite_float(
            penalty_candidate, field_name="conversion_penalty_candidate"
        )
        if penalty <= 0:
            _fail("conversion penalty candidate must be positive")

        def converted_score(row: Mapping[str, object]) -> float:
            base = float(row["penalized_objective"])
            if sense == "MAXIMIZE":
                base = -base
            return base + penalty * float(row["hard_violation_squared"])

        converted_best = min(all_rows, key=converted_score)
        native_assignment = small_exact_solution["assignment"]
        adequate = (
            converted_best["original_model_feasible"] is True
            and native_assignment is not None
            and converted_best["assignment"] == native_assignment
        )
        adequacy = {
            "state": (
                "ADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE"
                if adequate
                else "INADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE"
            ),
            "penalty": penalty,
            "converted_best_assignment": converted_best["assignment"],
            "matches_native_feasible_optimum": adequate,
        }
    return {
        "schema_version": model_row["schema_version"],
        "objective_sense": sense,
        "raw_objective": evaluated["raw_objective"],
        "soft_penalty": evaluated["soft_penalty"],
        "penalized_objective": evaluated["penalized_objective"],
        "original_model_feasible": evaluated["original_model_feasible"],
        "constraint_evaluations": evaluated["constraint_evaluations"],
        "assignment": supplied,
        "interpret_back_state": (
            "EXACT_ORIGINAL_VARIABLE_LABELS_AND_UNITS_PRESERVED"
        ),
        "small_exact_solution": small_exact_solution,
        "conversion_penalty_adequacy": adequacy,
    }


def compute_math_49_discrete_quadratic_model_v2(
    model: Mapping[str, object],
    assignment: Mapping[str, object],
) -> dict[str, object]:
    model_row = _v34_mapping(model, "model")
    if model_row.get("schema_version") != "QTT_DQM_GRAMMAR_V1":
        _fail("DQM model must use QTT_DQM_GRAMMAR_V1")
    variables = _v34_list(model_row.get("variables"), "model.variables")
    registry: dict[str, tuple[str, ...]] = {}
    for index, raw_variable in enumerate(variables):
        variable = _v34_mapping(raw_variable, f"variables[{index}]")
        identifier = variable.get("id")
        cases = _v34_list(variable.get("cases"), f"variables[{index}].cases")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in registry
            or len(cases) != len(set(cases))
            or any(not isinstance(case, str) or not case for case in cases)
        ):
            _fail("DQM variable and case identities must be unique ordered text")
        registry[identifier] = tuple(str(case) for case in cases)
    selected = _v34_mapping(assignment, "assignment")
    if set(selected) != set(registry) or any(
        selected[variable] not in registry[variable] for variable in registry
    ):
        _fail("DQM assignment must select one known case per variable")
    expected_linear = {
        (variable, case)
        for variable, cases in registry.items()
        for case in cases
    }
    linear: dict[tuple[str, str], float] = {}
    for index, raw_bias in enumerate(
        _v34_list(model_row.get("linear_biases"), "linear_biases")
    ):
        bias = _v34_mapping(raw_bias, f"linear_biases[{index}]")
        key = (bias.get("variable"), bias.get("case"))
        if key not in expected_linear or key in linear:
            _fail("DQM linear bias identity is duplicate or unknown")
        linear[(str(key[0]), str(key[1]))] = finite_float(
            bias.get("bias"), field_name=f"linear_biases[{index}].bias"
        )
    if set(linear) != expected_linear:
        _fail("every DQM variable/case requires an explicit bias, including zero")
    variable_order = {variable: index for index, variable in enumerate(registry)}
    pairwise: dict[tuple[str, str, str, str], float] = {}
    raw_pairwise = model_row.get("pairwise_biases")
    if isinstance(raw_pairwise, str | bytes) or not isinstance(
        raw_pairwise, Sequence
    ):
        _fail("pairwise_biases must be a sequence")
    for index, raw_bias in enumerate(raw_pairwise):
        bias = _v34_mapping(raw_bias, f"pairwise_biases[{index}]")
        u, v = bias.get("u"), bias.get("v")
        case_u, case_v = bias.get("case_u"), bias.get("case_v")
        if (
            not isinstance(u, str)
            or not isinstance(v, str)
            or u not in registry
            or v not in registry
            or u == v
            or case_u not in registry[u]
            or case_v not in registry[v]
        ):
            _fail("DQM pairwise bias references an unknown variable or case")
        if variable_order[u] > variable_order[v]:
            u, v = v, u
            case_u, case_v = case_v, case_u
        key = (u, str(case_u), v, str(case_v))
        if key in pairwise:
            _fail("DQM pairwise interaction is duplicated")
        pairwise[key] = finite_float(
            bias.get("bias"), field_name=f"pairwise_biases[{index}].bias"
        )
    constant = finite_float(model_row.get("constant"), field_name="constant")

    def energy(candidate: Mapping[str, object]) -> float:
        return (
            constant
            + math.fsum(
                linear[(variable, str(candidate[variable]))]
                for variable in registry
            )
            + math.fsum(
                coefficient
                for (u, case_u, v, case_v), coefficient in pairwise.items()
                if candidate[u] == case_u and candidate[v] == case_v
            )
        )

    total_states = math.prod(len(cases) for cases in registry.values())
    if total_states > 4096:
        _fail("small exact DQM domain is limited to 4096 assignments")
    exhaustive = tuple(
        {
            "assignment": dict(zip(registry, cases, strict=True)),
            "energy": energy(dict(zip(registry, cases, strict=True))),
        }
        for cases in product(*(registry[variable] for variable in registry))
    )
    return {
        "schema_version": model_row["schema_version"],
        "assignment": dict(selected),
        "energy": energy(selected),
        "exhaustive_assignments": exhaustive,
        "interpret_back_state": (
            "EXACT_ORDERED_VARIABLE_AND_CASE_LABELS_PRESERVED"
        ),
        "one_hot_expansion_applied": False,
    }


from .specification import (  # noqa: E402
    FROZEN_FORMULA_INPUT_CONTRACTS,
    FROZEN_FORMULA_REPOSITORY_DISPOSITIONS,
    FROZEN_FORMULA_REQUIREMENTS,
    validate_formula_output_v34,
)


PREDECESSOR_IMPLEMENTATION_REGISTRY = IMPLEMENTATION_REGISTRY
PREDECESSOR_IMPLEMENTATION_VERSION_REGISTRY: Mapping[
    str, MathImplementationRecordV1
] = MappingProxyType(
    {
        row.contract.implementation_id: row
        for row in PREDECESSOR_IMPLEMENTATION_REGISTRY.values()
    }
)


_V34_INVOCATION_ADAPTERS: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "MATH-01": compute_math_01_v34,
        "MATH-02": compute_math_02_v34,
        "MATH-03": compute_math_03_v34,
        "MATH-04": compute_math_04_v34,
        "MATH-05": compute_math_05_v34,
        "MATH-06": compute_math_06_binary_contract_expected_net_cash_v2,
        "MATH-07": compute_math_07_multi_outcome_expected_net_cash_v2,
        "MATH-08": compute_math_08_v34,
        "MATH-09": compute_math_09_v34,
        "MATH-10": compute_math_10_expected_calibration_error_v2,
        "MATH-11": compute_math_11_v34,
        "MATH-12": compute_math_12_v34,
        "MATH-13": compute_math_13_v34,
        "MATH-14": compute_math_14_stationary_bootstrap_mean_interval_v2,
        "MATH-15": compute_math_15_white_reality_check_v2,
        "MATH-16": compute_math_16_hansen_spa,
        "MATH-17": compute_math_17_probabilistic_sharpe_ratio,
        "MATH-18": compute_math_18_deflated_sharpe_ratio,
        "MATH-19": compute_math_19_probability_of_backtest_overfitting,
        "MATH-20": compute_math_20_purged_kfold_with_embargo,
        "MATH-21": compute_math_21_combinatorial_purged_cross_validation,
        "MATH-22": compute_math_22_doubly_robust_ope,
        "MATH-23": compute_math_23_inverse_propensity_score_ope,
        "MATH-24": compute_math_24_self_normalized_ips,
        "MATH-25": compute_math_25_switch_ope,
        "MATH-36": compute_math_36_kalshi_binary_book_transform,
        "MATH-46": compute_math_46_qubo_upper_triangular_convention_v2,
        "MATH-47": compute_math_47_qubo_to_ising_transform_v2,
        "MATH-48": compute_math_48_constrained_quadratic_model_v2,
        "MATH-49": compute_math_49_discrete_quadratic_model_v2,
    }
)
FORMULA_INVOCATION_ADAPTERS = _V34_INVOCATION_ADAPTERS


def _v34_metadata(math_spec_id: str) -> MathSpecificationMetadataV1:
    requirement = FROZEN_FORMULA_REQUIREMENTS[math_spec_id]
    raw = requirement.raw
    frozen_guards = tuple(
        dict.fromkeys(
            str(value)
            for value in (
                *raw["hard_mathematical_bounds"],
                *raw["denominator_and_log_guards"],
                str(raw["missing_stale_conflict_nonfinite_behavior"]),
            )
        )
    )
    guards = (
        (
            "Energy parity tolerance must be derived from coefficient scale "
            "and float precision.",
            *frozen_guards,
        )
        if math_spec_id == "MATH-47"
        else frozen_guards
    )
    return MathSpecificationMetadataV1(
        certified_formula=requirement.formula_or_procedure,
        domain_and_fail_closed_guards=guards,
        implementation_algorithm=tuple(
            dict.fromkeys(str(value) for value in raw["algorithm_steps"])
        ),
        mandatory_comparator_or_reconciliation=str(
            raw["comparator_and_reconciliation"]
        ),
        precision_and_rounding_policy=str(raw["precision_and_rounding"]),
        optional_library_adapter_policy=(
            "OPTIONAL_LIBRARY_ADAPTER_MUST_PRESERVE_FROZEN_SEMANTICS; "
            "STANDARD_LIBRARY_PRODUCTION_PATH_IS_AUTHORITATIVE"
        ),
        tie_break_policy=(
            "USE_ONLY_THE_EXPLICIT_FROZEN_TIE_BREAK_OR_STABLE_DECLARED_ORDER"
        ),
    )


def _v34_active_record(math_spec_id: str) -> MathImplementationRecordV1:
    requirement = FROZEN_FORMULA_REQUIREMENTS[math_spec_id]
    disposition = FROZEN_FORMULA_REPOSITORY_DISPOSITIONS[math_spec_id]
    if disposition.disposition == "REUSE_EXISTING_EXACT_VERSION":
        predecessor = PREDECESSOR_IMPLEMENTATION_REGISTRY[math_spec_id]
        contract = predecessor.contract
        function = predecessor.callable
    else:
        function = _V34_INVOCATION_ADAPTERS[math_spec_id]
        contract = ComputationImplementationV1(
            implementation_id=disposition.implementation_target,
            math_spec_id=math_spec_id,
            callable_name=function.__name__,
            specification_version=disposition.frozen_v3_4_version,
            deterministic=True,
            seed_required=math_spec_id in {"MATH-14", "MATH-15", "MATH-16"},
        )
    return MathImplementationRecordV1(
        contract=contract,
        name=requirement.name,
        family=requirement.family,
        callable=function,
        golden_vector_id=f"VECTOR::{math_spec_id}::GOLDEN",
        oracle_id=f"ORACLE::{math_spec_id}::V3_4",
        specification_metadata=_v34_metadata(math_spec_id),
    )


_ACTIVE_V34_ENTRIES = tuple(
    _v34_active_record(math_spec_id)
    for math_spec_id in FROZEN_FORMULA_REQUIREMENTS
)
IMPLEMENTATION_REGISTRY = MappingProxyType(
    {
        entry.contract.math_spec_id: entry
        for entry in _ACTIVE_V34_ENTRIES
    }
)
IMPLEMENTATION_VERSION_REGISTRY: Mapping[
    str, MathImplementationRecordV1
] = MappingProxyType(
    {
        **PREDECESSOR_IMPLEMENTATION_VERSION_REGISTRY,
        **{
            entry.contract.implementation_id: entry
            for entry in _ACTIVE_V34_ENTRIES
        },
    }
)


def get_math_implementation(
    math_spec_id: str,
    *,
    implementation_id: str | None = None,
) -> MathImplementationRecordV1:
    if not isinstance(math_spec_id, str) or not math_spec_id:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            "math specification identity must be nonempty text",
        )
    try:
        row = (
            IMPLEMENTATION_REGISTRY[math_spec_id]
            if implementation_id is None
            else IMPLEMENTATION_VERSION_REGISTRY[implementation_id]
        )
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"math implementation is not allowlisted: "
            f"{implementation_id or math_spec_id}",
        ) from exc
    if row.contract.math_spec_id != math_spec_id:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            "requested implementation version belongs to another math identity",
        )
    return row


def get_math_callable(
    math_spec_id: str,
    *,
    implementation_id: str | None = None,
) -> Callable[..., object]:
    return get_math_implementation(
        math_spec_id, implementation_id=implementation_id
    ).callable


def _v34_mutable_call_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _v34_mutable_call_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_v34_mutable_call_value(item) for item in value]
    return value


def invoke_formula_v34(
    math_spec_id: str,
    inputs: Mapping[str, object],
) -> object:
    """Invoke one active formula through the sole central adapter boundary."""

    if math_spec_id not in IMPLEMENTATION_REGISTRY:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown active v3.4 formula: {math_spec_id}",
        )
    if not isinstance(inputs, Mapping):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "formula inputs must be an exact named mapping",
        )
    declared = FROZEN_FORMULA_INPUT_CONTRACTS[
        math_spec_id
    ].declared_input_keys
    if set(inputs) != set(declared):
        missing = sorted(set(declared) - set(inputs))
        extra = sorted(set(inputs) - set(declared))
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{math_spec_id} input identity mismatch; missing={missing}, extra={extra}",
        )
    call_inputs = {
        name: _v34_mutable_call_value(inputs[name]) for name in declared
    }
    value = _V34_INVOCATION_ADAPTERS[math_spec_id](**call_inputs)
    validate_formula_output_v34(math_spec_id, value)
    return value


if (
    len(PREDECESSOR_IMPLEMENTATION_REGISTRY) != 19
    or len(IMPLEMENTATION_REGISTRY) != 30
    or len(IMPLEMENTATION_VERSION_REGISTRY) != 39
    or tuple(IMPLEMENTATION_REGISTRY) != tuple(FROZEN_FORMULA_REQUIREMENTS)
    or set(FORMULA_INVOCATION_ADAPTERS) != set(IMPLEMENTATION_REGISTRY)
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "v3.4 requires 30 active routes and 39 preserved version records",
    )


# Tranche-C overlay.  IMPLEMENTATION_REGISTRY intentionally remains the exact
# 30-row v3.4 compatibility view consumed by the existing public surface.
from .economic_math import (
    ActivePriceGridRangeV1,
    BinaryBookSnapshotV1,
    TRANCHE_C_MATH_SPECIFICATIONS,
    binary_book_implied_asks_v1,
)


_ST12C_FORMULAS = {
    "MATH-26": "E[posterior best utility] - current best utility - acquisition cost",
    "MATH-27": "(b*p-(1-p))/b",
    "MATH-28": "min(k*max(0,full_kelly), every approved cap)",
    "MATH-29": "mu^T*w - lambda/2*w^T*Sigma*w - transaction_cost",
    "MATH-30": "exact empirical Rockafellar-Uryasev CVaR",
    "MATH-31": "probability-weighted worst-tail empirical loss",
    "MATH-32": "signed_quantity*(execution-decision)+declared costs",
    "MATH-33": "signed_quantity*(execution-midpoint_at_decision)",
    "MATH-34": "contracts*fee_rate*price*(1-price)",
    "MATH-35": "contracts*theta*price*(1-price)",
    "MATH-36": "binary complement book transform with sequence and grid custody",
    "MATH-37": "externally calibrated complete-fill probability by horizon",
    "MATH-38": "sum(quantity*probability) over explicit fill distribution",
}
_ST12C_FAMILIES = {
    "MATH-26": "RESEARCH_PRIORITIZATION",
    "MATH-27": "POSITION_SIZING",
    "MATH-28": "POSITION_SIZING",
    "MATH-29": "PORTFOLIO",
    "MATH-30": "RISK",
    "MATH-31": "RISK",
    "MATH-32": "TCA",
    "MATH-33": "TCA",
    "MATH-34": "PROVIDER_FEE",
    "MATH-35": "PROVIDER_FEE",
    "MATH-36": "PROVIDER_MARKET_DATA",
    "MATH-37": "EXECUTION_MODEL",
    "MATH-38": "EXECUTION_MODEL",
}


def _st12c_record(math_spec_id: str) -> MathImplementationRecordV1:
    specification = TRANCHE_C_MATH_SPECIFICATIONS[math_spec_id]
    implementation = specification.implementation
    return MathImplementationRecordV1(
        contract=ComputationImplementationV1(
            implementation_id=f"qku/economic_math.py::{math_spec_id}::ST12C-CURRENTIZED-1.0",
            math_spec_id=math_spec_id,
            callable_name=implementation.__name__,
            specification_version="ST12C-CURRENTIZED-1.0",
            deterministic=True,
            seed_required=False,
        ),
        name=specification.name,
        family=_ST12C_FAMILIES[math_spec_id],
        callable=implementation,
        golden_vector_id=f"GOLDEN::{math_spec_id}",
        oracle_id=f"ORACLE::{math_spec_id}",
        specification_metadata=MathSpecificationMetadataV1(
            certified_formula=_ST12C_FORMULAS[math_spec_id],
            domain_and_fail_closed_guards=(
                "Reject missing, stale, invalid, nonfinite, unit-incompatible, or out-of-domain inputs",
                "No provider, private-state, replay/PAPER, order, capital, LLM, or QPU effect",
            ),
            implementation_algorithm=(
                "Convert financial inputs through the centralized exact Decimal authority",
                "Apply the frozen deterministic formula and explicit domain guards",
                "Quantize only at an explicitly supplied downstream field boundary",
            ),
            mandatory_comparator_or_reconciliation=f"ORACLE::{math_spec_id}",
            precision_and_rounding_policy="DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN; NO_IMPLICIT_QUANTIZATION",
            optional_library_adapter_policy="STANDARD_LIBRARY_ONLY; NO_NEW_DEPENDENCY",
            tie_break_policy="STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_STRONGER_EXISTING_INVARIANT",
        ),
    )


TRANCHE_C_IMPLEMENTATION_REGISTRY: Mapping[str, MathImplementationRecordV1] = MappingProxyType(
    {math_spec_id: _st12c_record(math_spec_id) for math_spec_id in TRANCHE_C_MATH_SPECIFICATIONS}
)
ST12C_CUMULATIVE_IMPLEMENTATION_REGISTRY: Mapping[str, MathImplementationRecordV1] = MappingProxyType(
    {**IMPLEMENTATION_REGISTRY, **TRANCHE_C_IMPLEMENTATION_REGISTRY}
)


def get_tranche_c_math_implementation(math_spec_id: str) -> MathImplementationRecordV1:
    try:
        return TRANCHE_C_IMPLEMENTATION_REGISTRY[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(ReasonCode.UNKNOWN_IMPLEMENTATION, f"unknown Tranche-C math identity: {math_spec_id}") from exc


if (
    len(TRANCHE_C_IMPLEMENTATION_REGISTRY) != 13
    or tuple(TRANCHE_C_IMPLEMENTATION_REGISTRY) != tuple(f"MATH-{number}" for number in range(26, 39))
    or len(ST12C_CUMULATIVE_IMPLEMENTATION_REGISTRY) != 42
):
    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "Tranche-C math implementation closure must be 13 with cumulative union 42")


# ST12-D adds one formula identity while reusing MATH-13/14/15 by object
# identity.  The predecessor 30-row public registry remains unchanged.
def validate_math_39_event_context(
    *,
    sequence_continuous: bool,
    matching_priority_known: bool,
    unit: str,
    basis: str,
    venue_evidence_ref: str,
) -> None:
    """Fail closed before the pure queue-ahead formula is invoked."""

    if type(sequence_continuous) is not bool or not sequence_continuous:
        raise NumericDomainError(
            ReasonCode.SEQUENCE_GAP,
            "MATH-39 requires sequence-continuous events",
        )
    if type(matching_priority_known) is not bool or not matching_priority_known:
        raise NumericDomainError(
            ReasonCode.MATCHING_PRIORITY_UNKNOWN,
            "MATH-39 requires a declared matching-priority convention",
        )
    if unit != "units" or basis != "ACKNOWLEDGED_INSERTION_POINT":
        raise NumericDomainError(
            ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
            "MATH-39 requires units at the acknowledged insertion point",
        )
    if not isinstance(venue_evidence_ref, str) or not venue_evidence_ref.strip():
        raise NumericDomainError(
            ReasonCode.MATCHING_PRIORITY_UNKNOWN,
            "MATH-39 cannot claim an exact estimate without venue evidence",
        )


def compute_math_39_queue_position_estimate(
    displayed_quantity_before_order: DecimalInput,
    net_prior_additions: DecimalInput,
    observed_prior_cancellations: DecimalInput,
    observed_trades_ahead: DecimalInput,
) -> Decimal:
    """Exact conservative queue-ahead arithmetic on already admitted inputs."""

    values = tuple(
        _nonnegative(exact_decimal(value, field_name=name), field_name=name)
        for name, value in (
            ("displayed_quantity_before_order", displayed_quantity_before_order),
            ("net_prior_additions", net_prior_additions),
            ("observed_prior_cancellations", observed_prior_cancellations),
            ("observed_trades_ahead", observed_trades_ahead),
        )
    )
    displayed, additions, cancellations, trades = values
    with localcontext(decimal_context_v1()):
        return max(
            Decimal(0),
            displayed + additions - cancellations - trades,
        )


_ST12D_MATH_39_RECORD = MathImplementationRecordV1(
    contract=ComputationImplementationV1(
        implementation_id=(
            "qku/implementation_registry.py::MATH-39::ST12D-CURRENTIZED-1.0"
        ),
        math_spec_id="MATH-39",
        callable_name="compute_math_39_queue_position_estimate",
        specification_version="ST12D-CURRENTIZED-1.0",
        deterministic=True,
        seed_required=False,
    ),
    name="QUEUE_POSITION_ESTIMATE",
    family="EXECUTION_MODEL",
    callable=compute_math_39_queue_position_estimate,
    golden_vector_id="GOLDEN::MATH-39",
    oracle_id="ORACLE::MATH-39",
    specification_metadata=MathSpecificationMetadataV1(
        certified_formula=(
            "max(0, displayed_quantity_before_order + net_prior_additions - "
            "observed_prior_cancellations - observed_trades_ahead)"
        ),
        domain_and_fail_closed_guards=(
            "Reject missing, invalid, nonfinite, or negative quantities",
            "Reject sequence gaps, unknown matching priority, and unit/basis mismatch before invocation",
            "Never claim exact queue position without a venue-evidence reference",
        ),
        implementation_algorithm=(
            "Initialize at the acknowledged insertion point",
            "Consume only declared sequence-continuous events in stable order",
            "Apply exact Decimal queue-ahead arithmetic and floor at zero",
        ),
        mandatory_comparator_or_reconciliation=(
            "Empirical time-to-fill conditioned on price level"
        ),
        precision_and_rounding_policy=(
            "DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN; NO_IMPLICIT_QUANTIZATION"
        ),
        optional_library_adapter_policy="STANDARD_LIBRARY_ONLY; NO_NEW_DEPENDENCY",
        tie_break_policy="DECLARED_SEQUENCE_THEN_CANONICAL_EVENT_ID_ASCENDING",
    ),
)

TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY: Mapping[
    str, MathImplementationRecordV1
] = MappingProxyType({"MATH-39": _ST12D_MATH_39_RECORD})
ST12D_MATH_IMPLEMENTATION_REGISTRY: Mapping[
    str, MathImplementationRecordV1
] = MappingProxyType(
    {
        "MATH-13": IMPLEMENTATION_REGISTRY["MATH-13"],
        "MATH-14": IMPLEMENTATION_REGISTRY["MATH-14"],
        "MATH-15": IMPLEMENTATION_REGISTRY["MATH-15"],
        "MATH-39": _ST12D_MATH_39_RECORD,
    }
)
ST12D_CUMULATIVE_IMPLEMENTATION_REGISTRY: Mapping[
    str, MathImplementationRecordV1
] = MappingProxyType(
    {**ST12C_CUMULATIVE_IMPLEMENTATION_REGISTRY, **TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY}
)
CURRENT_IMPLEMENTATION_REGISTRY: Mapping[str, MathImplementationRecordV1] = (
    MappingProxyType({**IMPLEMENTATION_REGISTRY, **TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY})
)


def get_current_math_implementation(
    math_spec_id: str,
) -> MathImplementationRecordV1:
    try:
        return CURRENT_IMPLEMENTATION_REGISTRY[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown current math identity: {math_spec_id}",
        ) from exc


def invoke_current_formula(
    math_spec_id: str,
    inputs: Mapping[str, object],
) -> object:
    """Central invocation boundary for v3.4 plus the additive MATH-39 route."""

    if math_spec_id != "MATH-39":
        return invoke_formula_v34(math_spec_id, inputs)
    if not isinstance(inputs, Mapping):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "MATH-39 inputs must be an exact named mapping",
        )
    declared = (
        "displayed_quantity_before_order",
        "net_prior_additions",
        "observed_prior_cancellations",
        "observed_trades_ahead",
    )
    if tuple(inputs) != declared:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "MATH-39 derived input identity and order differ from the current contract",
        )
    value = _ST12D_MATH_39_RECORD.callable(
        *(inputs[name] for name in declared)
    )
    from .specification import validate_current_formula_output

    validate_current_formula_output(math_spec_id, value)
    return value


def get_tranche_d_math_implementation(
    math_spec_id: str,
) -> MathImplementationRecordV1:
    try:
        return ST12D_MATH_IMPLEMENTATION_REGISTRY[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown Tranche-D math identity: {math_spec_id}",
        ) from exc


if (
    tuple(ST12D_MATH_IMPLEMENTATION_REGISTRY)
    != ("MATH-13", "MATH-14", "MATH-15", "MATH-39")
    or len(TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY) != 1
    or len(ST12D_CUMULATIVE_IMPLEMENTATION_REGISTRY) != 43
    or any(
        ST12D_MATH_IMPLEMENTATION_REGISTRY[math_id]
        is not IMPLEMENTATION_REGISTRY[math_id]
        for math_id in ("MATH-13", "MATH-14", "MATH-15")
    )
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "Tranche-D must reuse MATH-13/14/15 and add only MATH-39",
    )


# ST12-F private evidence registry.  The public service dispatch above remains
# byte-stable and does not route any of these evidence-only callables.
def compute_math_40_adverse_selection_cost(
    *,
    signed_fill_quantity: DecimalInput,
    midpoint_after_fill: DecimalInput,
    fill_price: DecimalInput,
) -> Decimal:
    quantity = exact_decimal(signed_fill_quantity, field_name="signed_fill_quantity")
    midpoint = exact_decimal(midpoint_after_fill, field_name="midpoint_after_fill")
    price = exact_decimal(fill_price, field_name="fill_price")
    return quantity * (midpoint - price)


def compute_math_41_latency_alpha_decay(
    *, edge_now: float, latency: float, tau: float
) -> float:
    edge = finite_float(edge_now, field_name="edge_now")
    elapsed = finite_float(latency, field_name="latency")
    decay_time = finite_float(tau, field_name="tau")
    if elapsed < 0 or decay_time <= 0:
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "latency must be nonnegative and fitted tau strictly positive",
        )
    return edge * math.exp(-elapsed / decay_time)


def compute_math_42_square_root_market_impact(
    *, Y: float, sigma: float, Q: DecimalInput, ADV: DecimalInput
) -> float:
    coefficient = finite_float(Y, field_name="Y")
    volatility = finite_float(sigma, field_name="sigma")
    quantity = exact_decimal(Q, field_name="Q")
    average_volume = exact_decimal(ADV, field_name="ADV")
    if coefficient < 0 or volatility < 0 or average_volume <= 0:
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "impact coefficient/volatility must be nonnegative and ADV positive",
        )
    return coefficient * volatility * math.sqrt(float(abs(quantity) / average_volume))


def compute_math_43_capacity_crowding_penalty(
    *, participation: float, approved_participation_cap: float, penalty_scale: float
) -> float:
    observed = finite_float(participation, field_name="participation")
    cap = finite_float(
        approved_participation_cap,
        field_name="approved_participation_cap",
    )
    scale = finite_float(penalty_scale, field_name="penalty_scale")
    if observed < 0 or cap <= 0 or scale < 0:
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "participation/scale must be nonnegative and cap strictly positive",
        )
    return max(0.0, observed / cap - 1.0) ** 2 * scale


def compute_math_44_covariance_shrinkage(
    *,
    sample_covariance: Sequence[Sequence[float]],
    target: Sequence[Sequence[float]],
    delta: float,
) -> tuple[tuple[float, ...], ...]:
    weight = finite_float(delta, field_name="delta")
    if not 0 <= weight <= 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "delta must be in [0,1]")
    sample = tuple(tuple(finite_float(value, field_name="sample_covariance") for value in row) for row in sample_covariance)
    goal = tuple(tuple(finite_float(value, field_name="target") for value in row) for row in target)
    size = len(sample)
    if size == 0 or len(goal) != size or any(len(row) != size for row in (*sample, *goal)):
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "covariance and target must be same-sized nonempty square matrices",
        )
    if any(abs(sample[i][j] - sample[j][i]) > 1e-12 or abs(goal[i][j] - goal[j][i]) > 1e-12 for i in range(size) for j in range(size)):
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "covariance and target must be symmetric",
        )
    result = tuple(
        tuple((1.0 - weight) * sample[i][j] + weight * goal[i][j] for j in range(size))
        for i in range(size)
    )
    # Deterministic semidefinite Cholesky check.  Gershgorin bounds are only
    # sufficient and would reject valid covariance matrices that are not
    # diagonally dominant.
    tolerance = 1e-12
    lower = [[0.0 for _ in range(size)] for _ in range(size)]
    for row_index in range(size):
        for column_index in range(row_index + 1):
            residual = result[row_index][column_index] - math.fsum(
                lower[row_index][offset] * lower[column_index][offset]
                for offset in range(column_index)
            )
            if row_index == column_index:
                if residual < -tolerance:
                    raise NumericDomainError(
                        ReasonCode.OUT_OF_DOMAIN,
                        "shrunk covariance must be positive semidefinite",
                    )
                lower[row_index][column_index] = math.sqrt(max(0.0, residual))
            elif lower[column_index][column_index] > tolerance:
                lower[row_index][column_index] = (
                    residual / lower[column_index][column_index]
                )
            elif abs(residual) > tolerance:
                raise NumericDomainError(
                    ReasonCode.OUT_OF_DOMAIN,
                    "shrunk covariance must be positive semidefinite",
                )
    return result


def compute_math_45_lower_confidence_bound_no_trade_gate(
    *,
    estimated_net_edge: DecimalInput,
    uncertainty: DecimalInput,
    z_or_quantile: DecimalInput,
    model_risk_haircut: DecimalInput,
) -> Mapping[str, object]:
    edge = exact_decimal(estimated_net_edge, field_name="estimated_net_edge")
    uncertainty_value = exact_decimal(uncertainty, field_name="uncertainty")
    quantile = exact_decimal(z_or_quantile, field_name="z_or_quantile")
    haircut = exact_decimal(model_risk_haircut, field_name="model_risk_haircut")
    if uncertainty_value < 0 or quantile < 0 or haircut < 0:
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "uncertainty, quantile, and model-risk haircut must be nonnegative",
        )
    lcb = edge - quantile * uncertainty_value - haircut
    return MappingProxyType({"lcb_net": lcb, "trade_gate": lcb > 0})


def compute_math_50_qaoa_preexisting_trace_validation(
    *,
    input_lock_id: str,
    formulation_id: str,
    objective_id: str,
    parameter_order: Sequence[str],
    seed_policy_ref: str,
    bounds_ref: str,
    constraint_refs: Sequence[str],
    trace_complete: bool,
    original_model_interpret_back_valid: bool,
    trace_weights: Mapping[str, DecimalInput],
    locked_costs: Mapping[str, DecimalInput],
    observed_feasibility: Mapping[str, bool],
    original_economic_utilities: Mapping[str, DecimalInput],
    resource_use: Mapping[str, DecimalInput],
    latency: Mapping[str, DecimalInput],
    selected_candidate_id: str,
    objective_sense: str,
    quantum_basis: Mapping[str, object],
    strongest_classical_basis: Mapping[str, object],
    no_trade_basis: Mapping[str, object],
) -> Mapping[str, object]:
    keys = set(trace_weights)
    if (
        not isinstance(input_lock_id, str)
        or not input_lock_id
        or not isinstance(formulation_id, str)
        or not formulation_id
        or not isinstance(objective_id, str)
        or not objective_id
        or not tuple(parameter_order)
        or len(tuple(parameter_order)) != len(set(parameter_order))
        or any(not isinstance(value, str) or not value for value in parameter_order)
        or not isinstance(seed_policy_ref, str)
        or not seed_policy_ref
        or not isinstance(bounds_ref, str)
        or not bounds_ref
        or not tuple(constraint_refs)
        or len(tuple(constraint_refs)) != len(set(constraint_refs))
        or any(not isinstance(value, str) or not value for value in constraint_refs)
        or trace_complete is not True
        or original_model_interpret_back_valid is not True
        or not keys
        or keys != set(locked_costs)
        or keys != set(observed_feasibility)
        or keys != set(original_economic_utilities)
        or keys != set(resource_use)
        or keys != set(latency)
        or objective_sense not in {"MAXIMIZE", "MINIMIZE"}
        or not isinstance(selected_candidate_id, str)
        or not selected_candidate_id
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA trace keys, objective sense, and selected identity must match exactly",
        )
    _validate_math_52_basis_records(
        quantum_basis,
        strongest_classical_basis,
        no_trade_basis,
    )
    if (
        quantum_basis["input_lock_id"] != input_lock_id
        or quantum_basis["original_formulation_id"] != formulation_id
        or quantum_basis["objective_sense"] != objective_sense
        or tuple(quantum_basis["constraint_refs"]) != tuple(constraint_refs)
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA trace identities differ from the locked economic basis",
        )
    weights = {key: exact_decimal(value, field_name=f"trace_weight[{key}]") for key, value in trace_weights.items()}
    costs = {key: exact_decimal(value, field_name=f"locked_cost[{key}]") for key, value in locked_costs.items()}
    utilities = {key: exact_decimal(value, field_name=f"original_economic_utility[{key}]") for key, value in original_economic_utilities.items()}
    resources = {key: exact_decimal(value, field_name=f"resource_use[{key}]") for key, value in resource_use.items()}
    latencies = {key: exact_decimal(value, field_name=f"latency[{key}]") for key, value in latency.items()}
    if any(value < 0 for value in weights.values()) or sum(weights.values(), Decimal(0)) != Decimal(1):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA trace weights must be nonnegative and sum exactly to one",
        )
    if any(type(value) is not bool for value in observed_feasibility.values()):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA feasibility values must be exact booleans",
        )
    if any(value < 0 for value in resources.values()) or any(value < 0 for value in latencies.values()):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA resource use and latency must be nonnegative",
        )
    feasible = tuple(key for key in sorted(costs) if observed_feasibility[key])
    if not feasible:
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA trace contains no original-model feasible candidate",
        )
    selected = min(
        feasible,
        key=lambda key: (
            -utilities[key] if objective_sense == "MAXIMIZE" else utilities[key],
            key,
        ),
    )
    if selected_candidate_id != selected:
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "QAOA selected candidate differs from the original economic objective",
        )
    expected = sum((weights[key] * costs[key] for key in weights), Decimal(0))
    return MappingProxyType(
        {
            "trace_expected_locked_cost": expected,
            "original_economic_objective": utilities[selected],
            "selected_candidate_id": selected,
            "selected_original_model_feasible": True,
            "effect_call_count": 0,
        }
    )


def compute_math_51_vqe_preexisting_trace_validation(
    *,
    input_lock_id: str,
    formulation_id: str,
    hamiltonian_id: str,
    ansatz_metadata_ref: str,
    parameter_order: Sequence[str],
    optimizer_metadata_ref: str,
    seed_policy_ref: str,
    bounds_ref: str,
    constraint_refs: Sequence[str],
    trace_complete: bool,
    original_model_interpret_back_valid: bool,
    parameter_point_ids: Sequence[str],
    expectation_trace: Sequence[DecimalInput],
    variance_trace: Sequence[DecimalInput],
    locked_costs: Sequence[DecimalInput],
    original_economic_utilities: Sequence[DecimalInput],
    observed_feasibility: Sequence[bool],
    resource_use: Sequence[DecimalInput],
    latency: Sequence[DecimalInput],
    selected_point_id: str,
    objective_sense: str,
    quantum_basis: Mapping[str, object],
    strongest_classical_basis: Mapping[str, object],
    no_trade_basis: Mapping[str, object],
) -> Mapping[str, object]:
    point_ids = tuple(parameter_point_ids)
    expectations = tuple(exact_decimal(value, field_name="expectation") for value in expectation_trace)
    variances = tuple(exact_decimal(value, field_name="variance") for value in variance_trace)
    costs = tuple(exact_decimal(value, field_name="locked_cost") for value in locked_costs)
    utilities = tuple(exact_decimal(value, field_name="original_economic_utility") for value in original_economic_utilities)
    feasibility = tuple(observed_feasibility)
    resources = tuple(exact_decimal(value, field_name="resource_use") for value in resource_use)
    latencies = tuple(exact_decimal(value, field_name="latency") for value in latency)
    if (
        not isinstance(input_lock_id, str)
        or not input_lock_id
        or not isinstance(formulation_id, str)
        or not formulation_id
        or any(
            not isinstance(value, str) or not value
            for value in (
                hamiltonian_id,
                ansatz_metadata_ref,
                optimizer_metadata_ref,
                seed_policy_ref,
                bounds_ref,
            )
        )
        or not tuple(parameter_order)
        or len(tuple(parameter_order)) != len(set(parameter_order))
        or any(not isinstance(value, str) or not value for value in parameter_order)
        or not tuple(constraint_refs)
        or len(tuple(constraint_refs)) != len(set(constraint_refs))
        or any(not isinstance(value, str) or not value for value in constraint_refs)
        or trace_complete is not True
        or original_model_interpret_back_valid is not True
        or not point_ids
        or len(point_ids) != len(expectations)
        or len(point_ids) != len(variances)
        or len(point_ids) != len(costs)
        or len(point_ids) != len(utilities)
        or len(point_ids) != len(feasibility)
        or len(point_ids) != len(resources)
        or len(point_ids) != len(latencies)
        or len(point_ids) != len(set(point_ids))
        or any(not isinstance(value, str) or not value for value in point_ids)
        or any(value < 0 for value in variances)
        or any(value < 0 for value in resources)
        or any(value < 0 for value in latencies)
        or any(type(value) is not bool for value in feasibility)
        or objective_sense not in {"MAXIMIZE", "MINIMIZE"}
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "VQE trace is incomplete, nonfinite, infeasible, or cross-lock",
        )
    _validate_math_52_basis_records(
        quantum_basis,
        strongest_classical_basis,
        no_trade_basis,
    )
    if (
        quantum_basis["input_lock_id"] != input_lock_id
        or quantum_basis["original_formulation_id"] != formulation_id
        or quantum_basis["objective_sense"] != objective_sense
        or tuple(quantum_basis["constraint_refs"]) != tuple(constraint_refs)
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "VQE trace identities differ from the locked economic basis",
        )
    feasible_indexes = tuple(
        index for index, is_feasible in enumerate(feasibility) if is_feasible
    )
    if not feasible_indexes:
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "VQE trace contains no original-model feasible point",
        )
    index = min(
        feasible_indexes,
        key=lambda item: (
            -utilities[item] if objective_sense == "MAXIMIZE" else utilities[item],
            point_ids[item],
        ),
    )
    if selected_point_id != point_ids[index]:
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "VQE selected point differs from the original economic objective",
        )
    return MappingProxyType(
        {
            "trace_expectation": expectations[index],
            "variance": variances[index],
            "original_economic_objective": utilities[index],
            "selected_candidate_id": point_ids[index],
            "selected_original_model_feasible": True,
            "effect_call_count": 0,
        }
    )


_MATH_52_BASIS_FIELDS = (
    "input_lock_id",
    "original_formulation_id",
    "objective_sense",
    "constraint_refs",
    "accounting_basis_ref",
    "cost_basis_ref",
    "capacity_basis_ref",
    "scenario_set_ref",
    "resource_budget_ref",
    "ttl_policy_ref",
    "version_epoch_pins",
)


def _validate_math_52_basis_records(
    quantum_basis: Mapping[str, object],
    strongest_classical_basis: Mapping[str, object],
    no_trade_basis: Mapping[str, object],
) -> None:
    bases = (quantum_basis, strongest_classical_basis, no_trade_basis)
    if any(not isinstance(value, Mapping) or set(value) != set(_MATH_52_BASIS_FIELDS) for value in bases):
        raise ContractValidationError(
            ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
            "MATH-52 comparison basis is incomplete or unordered",
        )
    normalized: list[dict[str, object]] = []
    text_fields = tuple(
        field_name
        for field_name in _MATH_52_BASIS_FIELDS
        if field_name not in {"constraint_refs", "version_epoch_pins"}
    )
    for value in bases:
        assert isinstance(value, Mapping)
        if any(
            not isinstance(value[field_name], str)
            or not value[field_name]
            or value[field_name] != value[field_name].strip()
            for field_name in text_fields
        ) or value["objective_sense"] not in {"MAXIMIZE", "MINIMIZE"}:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-52 basis identities and objective sense must be canonical",
            )
        row = dict(value)
        for field_name in ("constraint_refs", "version_epoch_pins"):
            refs = value[field_name]
            if (
                not isinstance(refs, (list, tuple))
                or not refs
                or any(
                    not isinstance(item, str)
                    or not item
                    or item != item.strip()
                    for item in refs
                )
                or len(refs) != len(set(refs))
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    f"MATH-52 {field_name} must be a nonempty unique canonical sequence",
                )
            row[field_name] = tuple(refs)
        normalized.append(row)
    for field_name in _MATH_52_BASIS_FIELDS:
        values = tuple(value[field_name] for value in normalized)
        if any(item != values[0] for item in values[1:]):
            reason = (
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH
                if field_name == "input_lock_id"
                else ReasonCode.ST12F_QUANTUM_TRACE_INVALID
            )
            raise ContractValidationError(
                reason,
                f"MATH-52 comparison basis differs at {field_name}",
            )


def compute_math_52_quantum_classical_benchmark_utility(
    *,
    quantum_basis: Mapping[str, object],
    strongest_classical_basis: Mapping[str, object],
    no_trade_basis: Mapping[str, object],
    validated_quantum: Mapping[str, object],
    strongest_classical: Mapping[str, object],
    no_trade: Mapping[str, object],
) -> Mapping[str, object]:
    _validate_math_52_basis_records(
        quantum_basis,
        strongest_classical_basis,
        no_trade_basis,
    )
    expected_fields = {
        "comparator_class",
        "feasible",
        "hard_veto",
        "conservative_utility",
        "resource_use",
        "latency",
        "deterministic_tie_break",
    }
    rows = (validated_quantum, strongest_classical, no_trade)
    expected_classes = ("VALIDATED_QUANTUM", "STRONGEST_CLASSICAL", "NO_TRADE")
    normalized: list[tuple[str, bool, bool, Decimal, Decimal, Decimal, str]] = []
    for row, expected_class in zip(rows, expected_classes, strict=True):
        if not isinstance(row, Mapping) or set(row) != expected_fields or row["comparator_class"] != expected_class:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-52 comparator receipt fields differ",
            )
        feasible = row["feasible"]
        hard_veto = row["hard_veto"]
        tie_break = row["deterministic_tie_break"]
        if type(feasible) is not bool or type(hard_veto) is not bool or not isinstance(tie_break, str) or not tie_break:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-52 comparator feasibility, veto, or tie-break is invalid",
            )
        if expected_class == "NO_TRADE" and (
            feasible is not True or hard_veto is not False
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-52 permanent NO_TRADE must remain feasible without veto",
            )
        utility = exact_decimal(row["conservative_utility"], field_name="conservative_utility")
        resource = exact_decimal(row["resource_use"], field_name="resource_use")
        latency_value = exact_decimal(row["latency"], field_name="latency")
        if resource < 0 or latency_value < 0:
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-52 resource use and latency must be nonnegative",
            )
        normalized.append((expected_class, feasible, hard_veto, utility, resource, latency_value, tie_break))
    priority = {"NO_TRADE": 0, "STRONGEST_CLASSICAL": 1, "VALIDATED_QUANTUM": 2}
    winner = min(
        normalized,
        key=lambda row: (
            0 if row[1] and not row[2] else 1,
            -row[3],
            row[4],
            row[5],
            priority[row[0]],
            row[6],
        ),
    )[0]
    utilities = {row[0]: row[3] for row in normalized}
    return MappingProxyType(
        {
            "delta_quantum_vs_classical": utilities["VALIDATED_QUANTUM"] - utilities["STRONGEST_CLASSICAL"],
            "delta_quantum_vs_no_trade": utilities["VALIDATED_QUANTUM"] - utilities["NO_TRADE"],
            "winner": winner,
            "quantum_advantage_claim_allowed": False,
        }
    )


_ST12F_NEW_EVIDENCE_CALLABLES_V1: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "MATH-40": compute_math_40_adverse_selection_cost,
        "MATH-41": compute_math_41_latency_alpha_decay,
        "MATH-42": compute_math_42_square_root_market_impact,
        "MATH-43": compute_math_43_capacity_crowding_penalty,
        "MATH-44": compute_math_44_covariance_shrinkage,
        "MATH-45": compute_math_45_lower_confidence_bound_no_trade_gate,
        "MATH-50": compute_math_50_qaoa_preexisting_trace_validation,
        "MATH-51": compute_math_51_vqe_preexisting_trace_validation,
        "MATH-52": compute_math_52_quantum_classical_benchmark_utility,
    }
)
_ST12F_REUSED_EVIDENCE_CALLABLES_V1: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        **{
            f"MATH-{number:02d}": IMPLEMENTATION_REGISTRY[f"MATH-{number:02d}"].callable
            for number in range(1, 26)
        },
        **{
            f"MATH-{number:02d}": TRANCHE_C_IMPLEMENTATION_REGISTRY[f"MATH-{number:02d}"].callable
            for number in range(26, 39)
        },
        "MATH-39": TRANCHE_D_NEW_IMPLEMENTATION_REGISTRY["MATH-39"].callable,
    }
)
ST12F_EVIDENCE_MATH_CALLABLE_REGISTRY_V1: Mapping[str, Callable[..., object]] = MappingProxyType(
    {**_ST12F_REUSED_EVIDENCE_CALLABLES_V1, **_ST12F_NEW_EVIDENCE_CALLABLES_V1}
)


def get_st12f_evidence_math_callable_v1(math_spec_id: str) -> Callable[..., object]:
    """Internal evidence lookup; it is intentionally outside public service dispatch."""

    try:
        return ST12F_EVIDENCE_MATH_CALLABLE_REGISTRY_V1[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown ST12-F evidence math identity: {math_spec_id}",
        ) from exc


if (
    len(_ST12F_REUSED_EVIDENCE_CALLABLES_V1) != 39
    or len(_ST12F_NEW_EVIDENCE_CALLABLES_V1) != 9
    or len(ST12F_EVIDENCE_MATH_CALLABLE_REGISTRY_V1) != 48
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "ST12-F evidence registry must reuse 39 and add exactly nine callables",
    )


# V35 private scientific producer. Existing public MATH identities stay unchanged.
from fractions import Fraction as _ProbabilityFractionV1
import re
import sys
import warnings

from .models import CompiledProbabilityPredictionV1, _probability_text_v1
from .serialization import _probability_binary64_v1


class _ProbabilityNumericalFailureV1(NumericDomainError):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(ReasonCode.OUT_OF_DOMAIN, detail)


def _probability_require_synchronous_worker_v1() -> None:
    """Reject observable overlap before touching warning filters.

    This local guard supplements the original job's admitted worker custody;
    it neither creates a worker nor qualifies its environment. Selected calls
    are synchronous and never dispatch Python tasks or threads. On builds with
    process-wide warning filters even an idle second Python thread denies work.
    """
    import asyncio
    import threading
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise ContractValidationError(ReasonCode.OWNER_DATA_MISSING, "synchronous numerical worker is required")
    if not getattr(sys.flags, "context_aware_warnings", False):
        active = threading.enumerate()
        if len(active) != 1 or active[0] is not threading.current_thread():
            raise ContractValidationError(ReasonCode.OWNER_DATA_MISSING, "exclusive Python warning context is unavailable")


def _probability_numeric_require_v1(value: bool, detail: str) -> None:
    if not value:
        raise _ProbabilityNumericalFailureV1(detail)


def _probability_numeric_text_v1(value: object) -> str:
    _probability_text_v1(value)
    return value


def _probability_decimal34_prediction_v1(value: _ProbabilityFractionV1, rounding: str) -> Decimal:
    _probability_numeric_require_v1(type(value) is _ProbabilityFractionV1 and rounding in
        ('ROUND_HALF_EVEN', 'ROUND_FLOOR', 'ROUND_CEILING'), 'PAYOUT_ROUNDING')
    context = decimal_context_v1()
    context.rounding = rounding
    with localcontext(context):
        return Decimal(value.numerator) / Decimal(value.denominator)


def _probability_integer_v1(value: object, minimum: int = 0) -> int:
    _probability_numeric_require_v1(type(value) is int and minimum <= value and value.bit_length() <= 512, 'INTEGER')
    return value



def _probability_dec_v1(value: object) -> Decimal:
    _probability_numeric_require_v1(type(value) is str and re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', value) is not None, 'DECIMAL_TEXT')
    _probability_numeric_require_v1(len(value) <= 128, 'DECIMAL_BOUND')
    result = Decimal(value)
    _probability_numeric_require_v1(result.is_finite() and not (result == 0 and result.is_signed()), 'DECIMAL_DOMAIN')
    return result



def _probability_rational_v1(value: object, nonnegative: bool = False) -> _ProbabilityFractionV1:
    result = _ProbabilityFractionV1(_probability_dec_v1(value))
    _probability_numeric_require_v1(not nonnegative or result >= 0, 'NEGATIVE')
    return result



def _probability_closed_v1(value: object, keys: set[str]) -> dict:
    _probability_numeric_require_v1(type(value) is dict and set(value) == keys, 'FIELD_SET')
    return value



def _probability_unique_names_v1(value: object) -> list[str]:
    _probability_numeric_require_v1(type(value) is list and bool(value), 'IDENTITIES')
    names = [_probability_numeric_text_v1(v) for v in value]
    _probability_numeric_require_v1(len(set(names)) == len(names), 'DUPLICATE_IDENTITY')
    return names



def _probability_finite_decimal_text_v1(value: _ProbabilityFractionV1) -> str:
    """Exact finite-decimal rendering from a rational; independent of Decimal context."""
    f=_ProbabilityFractionV1(value); n,d=f.numerator,f.denominator; twos=fives=0
    while d % 2 == 0: d//=2; twos+=1
    while d % 5 == 0: d//=5; fives+=1
    _probability_numeric_require_v1(d == 1, 'NONTERMINATING_DECIMAL')
    scale=max(twos,fives); n*=2**(scale-twos)*5**(scale-fives)
    digits=str(abs(n)).rjust(scale+1,'0')
    if scale: digits=(digits[:-scale]+'.'+digits[-scale:]).rstrip('0').rstrip('.')
    return ('-' if n<0 else '')+digits if n else '0'



def _probability_selected_scaler_v1(means: tuple, variances: tuple, scales: tuple,
                               n_samples: int) -> None:
    """Validate the selected no-fallback StandardScaler state without NumPy I/O.

    Reproduce the pinned dense-binary64 constant-feature test in its stated
    operation order. QTT keeps its stronger exclusion of scale-one fallback;
    neither positive near-constant variance nor forged sqrt(var) admits it.
    This is preparation-time numerical validation, not source authentication.
    """
    _probability_integer_v1(n_samples, 1)
    _probability_numeric_require_v1(type(means) is tuple and type(variances) is tuple and type(scales) is tuple
            and 0 < len(means) == len(variances) == len(scales), 'SCALER_DIMENSION')
    _probability_numeric_require_v1(all(type(x) is float and math.isfinite(x)
                for values in (means, variances, scales) for x in values), 'SCALER_VARIANCE')
    _probability_numeric_require_v1(all(x > 0 for x in (*variances, *scales)), 'ZERO_VARIANCE')
    eps = 2.0 ** -52  # binary64 machine epsilon, not a selected financial threshold.
    n = float(n_samples)
    for mean, variance, scale in zip(means, variances, scales, strict=True):
        mean_error = (n * mean) * eps
        upper_bound = (n * eps) * variance + mean_error * mean_error
        _probability_numeric_require_v1(math.isfinite(upper_bound) and variance > upper_bound, 'SCALER_VARIANCE')
        # Retain the original nonconstant variance/scale consistency tolerance.
        _probability_numeric_require_v1(math.isclose(scale * scale, variance, rel_tol=1e-12, abs_tol=0.0),
                'SCALER_VARIANCE')



def _probability_prediction_feature_cells_v1(fit_rows: int, calibration_rows: int,
                                        query_rows: int, feature_count: int) -> int:
    """Live Xf + Xc + Xp element count; not total RSS or allocator memory.

    Xp contains every calibration row again, plus queries, zero/basis/extreme
    probes. Label vectors, transformed copies, solver workspace, model snapshots,
    Python containers and returned predictions remain separately budgeted.
    """
    for count in (fit_rows, calibration_rows, query_rows): _probability_integer_v1(count, 0)
    _probability_integer_v1(feature_count, 1)
    return feature_count * (fit_rows + 2 * calibration_rows + query_rows
                            + 2 * feature_count + 3)



def _probability_validate_model_v1(a: dict):
    _probability_numeric_require_v1(type(a) is dict,'MODEL_FIELD_SET')
    keys={'schema','kind','feature_names','environment','scaler','coefficients','intercept','classes','calibration','fit_ids','calibration_ids','final_ids'}
    if a.get('kind')=='HUBER':keys.add('scale')
    _probability_closed_v1(a,keys);_probability_numeric_require_v1(a['schema']=='QTT_MODEL_DATA_ONLY_V35','MODEL_SCHEMA');_probability_numeric_require_v1(a['kind'] in ('CALIBRATED_LOGISTIC','HUBER'),'MODEL_KIND')
    names=_probability_unique_names_v1(a['feature_names']);n=len(names)
    _probability_closed_v1(a['environment'],{'python','numpy','scipy','scikit-learn'})
    for value in a['environment'].values():_probability_numeric_text_v1(value)
    s=_probability_closed_v1(a['scaler'],{'mean','var','scale','n_samples_seen'})
    for k in ['mean','var','scale']:_probability_numeric_require_v1(type(s[k]) is list and len(s[k])==n,'SCALER_DIMENSION')
    means=list(map(_probability_binary64_v1,s['mean']));variances=list(map(_probability_binary64_v1,s['var']));scales=list(map(_probability_binary64_v1,s['scale']))
    _probability_numeric_require_v1(all(v>0 for v in variances) and all(v>0 for v in scales),'ZERO_VARIANCE')
    _probability_selected_scaler_v1(tuple(means), tuple(variances), tuple(scales),
                               _probability_integer_v1(s['n_samples_seen'], 1))
    ids=[_probability_unique_names_v1(a[k]) for k in ['fit_ids','calibration_ids','final_ids']]
    _probability_numeric_require_v1(not(set(ids[0])&set(ids[1]) or set(ids[0])&set(ids[2]) or set(ids[1])&set(ids[2])),'SPLIT_LEAKAGE')
    _probability_numeric_require_v1(_probability_integer_v1(s['n_samples_seen'],1)==len(ids[0]),'SCALER_FIT_COUNT')
    _probability_numeric_require_v1(type(a['coefficients']) is list and len(a['coefficients'])==n,'COEFFICIENT_DIMENSION')
    beta=list(map(_probability_binary64_v1,a['coefficients']));intercept=_probability_binary64_v1(a['intercept'])
    if a['kind']=='CALIBRATED_LOGISTIC':
        _probability_numeric_require_v1(a['classes']==[0,1] and all(type(x) is int for x in a['classes']),'CLASSES')
        cal=_probability_closed_v1(a['calibration'],{'method','response','a','b'});_probability_numeric_require_v1(cal['method']=='sigmoid' and cal['response']=='decision_function','CALIBRATION_METHOD');_probability_binary64_v1(cal['a']);_probability_binary64_v1(cal['b'])
    else:
        _probability_numeric_require_v1(a['classes']==[] and a['calibration'] is None,'HUBER_SCHEMA');_probability_numeric_require_v1(_probability_binary64_v1(a['scale'])>0,'HUBER_SCALE')
    return means,scales,beta,intercept



def _probability_prediction_parity_v1(kind: str, reference: float, candidate: float) -> bool:
    """PM2-035/036: exact comparison of finite binary64 model outputs.

    abs(candidate-reference) <= atol + rtol*abs(reference), with no monetary tolerance.
    Existing stronger probability/regression policies control the synthetic adapter.
    """
    _probability_numeric_require_v1(kind in ('CALIBRATED_LOGISTIC','HUBER'),'MODEL_KIND')
    _probability_numeric_require_v1(type(reference) is float and type(candidate) is float and
            math.isfinite(reference) and math.isfinite(candidate),'PARITY_FINITE_BINARY64')
    absolute=_ProbabilityFractionV1(1,10**15) if kind=='CALIBRATED_LOGISTIC' else _ProbabilityFractionV1(1,10**12)
    relative=_ProbabilityFractionV1(1,10**12)
    return abs(_ProbabilityFractionV1(candidate)-_ProbabilityFractionV1(reference)) <= absolute+relative*abs(_ProbabilityFractionV1(reference))



def _probability_scalar_logit_identifiability_v1(logits: tuple[_ProbabilityFractionV1,...], labels: tuple[int,...]) -> str:
    """Exact 1-D unpenalized logistic geometry, not a fitted model or a tolerance."""
    _probability_numeric_require_v1(type(logits) is tuple and type(labels) is tuple and 2<=len(logits)<=10000 and len(logits)==len(labels),'DIAGNOSTIC_SHAPE')
    _probability_numeric_require_v1(all(type(x) is _ProbabilityFractionV1 and x.numerator.bit_length()<=4096 and x.denominator.bit_length()<=4096 for x in logits),'DIAGNOSTIC_VALUE')
    _probability_numeric_require_v1(all(type(y) is int and y in (0,1) for y in labels),'DIAGNOSTIC_LABEL')
    if len(set(labels))!=2:return 'CLASS_ABSENT'
    if len(set(logits))<2:return 'RANK_DEFICIENT'
    zero=[x for x,y in zip(logits,labels,strict=True) if y==0]
    one=[x for x,y in zip(logits,labels,strict=True) if y==1]
    if max(zero)<min(one) or max(one)<min(zero):return 'COMPLETE_SEPARATION'
    if max(zero)==min(one) or max(one)==min(zero):return 'QUASI_SEPARATION'
    return 'FINITE_MLE_GEOMETRY'



_PROBABILITY_DIAGNOSTIC_FAILURES_V1 = frozenset((
    'CLASS_ABSENT', 'RANK_DEFICIENT', 'COMPLETE_SEPARATION', 'QUASI_SEPARATION',
    'FIT_NUMERIC_FAILURE', 'FIT_NOT_CONVERGED', 'FIT_OUTPUT_INVALID',
    'FIT_EXPORT_PARITY',
))



def _fit_probability_calibration_diagnostic_v1(probabilities: tuple[float, ...],
                                         labels: tuple[int, ...], *,
                                         max_rows: int) -> dict:
    """Fresh unpenalized intercept/slope diagnostic; installed-library evidence.

    Inputs are occurrence-expanded rows, not cluster averages. No sample weights,
    tuning, cached estimator, callback, or target-environment claim is accepted.
    """
    _probability_work_observation_v1()
    _probability_integer_v1(max_rows, 2)
    _probability_numeric_require_v1(type(probabilities) is tuple and type(labels) is tuple and
            2 <= len(probabilities) == len(labels) <= min(max_rows, 10000),
            'DIAGNOSTIC_SHAPE')
    _probability_numeric_require_v1(all(type(q) is float and math.isfinite(q) and 0 <= q <= 1
                for q in probabilities), 'DIAGNOSTIC_PROBABILITY')
    _probability_numeric_require_v1(all(type(y) is int and y in (0, 1) for y in labels), 'DIAGNOSTIC_LABEL')
    low, high = math.nextafter(0., 1.), math.nextafter(1., 0.)
    logits = tuple(math.log(min(high, max(low, q))) -
                   math.log1p(-min(high, max(low, q))) for q in probabilities)
    geometry = _probability_scalar_logit_identifiability_v1(tuple(_ProbabilityFractionV1.from_float(x) for x in logits), labels)
    if geometry != 'FINITE_MLE_GEOMETRY':
        return {'status': 'INVALID', 'values': None, 'reason': geometry,
                'fit_calls': 0, 'occurrence_rows': len(labels)}
    # An unavailable dependency is an environment failure, not a numerical
    # observation or an excuse to publish a successfully evaluated window.
    import warnings
    import numpy as np
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    X = np.ascontiguousarray(np.asarray(logits, dtype=np.float64).reshape(-1, 1))
    y = np.asarray(labels, dtype=np.int64)
    estimator = LogisticRegression(C=float('inf'), l1_ratio=0., solver='lbfgs',
        tol=1e-4, max_iter=100, fit_intercept=True, dual=False,
        intercept_scaling=1., class_weight=None, random_state=None,
        verbose=0, warm_start=False, n_jobs=1)
    def invalid(reason):
        return {'status': 'INVALID', 'values': None, 'reason': reason,
                'fit_calls': 1, 'occurrence_rows': len(labels)}
    _probability_require_synchronous_worker_v1()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            estimator.fit(X, y)
        except (ValueError, FloatingPointError, OverflowError):
            return invalid('FIT_NUMERIC_FAILURE')
    if any(issubclass(w.category, (ConvergenceWarning, RuntimeWarning)) for w in caught):
        return invalid('FIT_NOT_CONVERGED')
    # The same binary-classifier counter contract applies to the unpenalized
    # drift diagnostic. A malformed native interface is not a numerical INVALID
    # observation and must escape the bank's numerical-failure classification.
    iterations = _probability_prediction_iterations_v1('CALIBRATED_LOGISTIC', estimator.n_iter_)
    if (estimator.classes_.tolist() != [0, 1] or estimator.coef_.shape != (1, 1)
            or estimator.intercept_.shape != (1,)):
        return invalid('FIT_OUTPUT_INVALID')
    intercept, slope = float(estimator.intercept_[0]), float(estimator.coef_[0, 0])
    if not all(math.isfinite(v) for v in (intercept, slope)):
        return invalid('FIT_OUTPUT_INVALID')
    try:
        native = estimator.predict_proba(X)[:, 1]
        verified_pairs = set()
        for x, q in zip(logits, native, strict=True):
            # Repeating an identical deterministic input/output pair does not
            # need another exact-ratio parity calculation. Fit rows themselves
            # remain fully occurrence-expanded and unit weighted.
            pair = (x, float(q))
            if pair in verified_pairs:
                continue
            margin = math.fsum((intercept, slope * x))
            if not math.isfinite(margin):
                return invalid('FIT_EXPORT_PARITY')
            e = math.exp(-abs(margin))
            exported = 1. / (1. + e) if margin >= 0 else e / (1. + e)
            if not _probability_prediction_parity_v1('CALIBRATED_LOGISTIC', float(q), exported):
                return invalid('FIT_EXPORT_PARITY')
            verified_pairs.add(pair)
    except (ValueError, OverflowError, FloatingPointError, _ProbabilityNumericalFailureV1):
        return invalid('FIT_EXPORT_PARITY')
    return {'status': 'VALID', 'values': (
                (0. if intercept == 0 else intercept).hex(),
                (0. if slope == 0 else slope).hex()),
            'reason': None, 'fit_calls': 1, 'occurrence_rows': len(labels),
            'n_iter': iterations,
            'warning_classes': sorted({w.category.__name__ for w in caught})}



def _probability_inverse_ecdf_v1(values: tuple[_ProbabilityFractionV1,...], p: _ProbabilityFractionV1) -> _ProbabilityFractionV1:
    _probability_numeric_require_v1(type(values) is tuple and 1<=len(values)<=10000 and all(type(x) is _ProbabilityFractionV1 for x in values),'QUANTILE_VALUES')
    _probability_numeric_require_v1(type(p) is _ProbabilityFractionV1 and 0<p<=1,'QUANTILE_PROBABILITY')
    rank=(len(values)*p.numerator+p.denominator-1)//p.denominator
    return sorted(values)[rank-1]



def _probability_cluster_occurrence_lineage_v1(clusters: tuple[tuple[str,...],...], indices: tuple[int,...],
                               *, partition: str, replicate: int, max_rows: int) -> tuple:
    """Data-only accepted-input projection; no source-admission authority."""
    _probability_numeric_require_v1(partition in ('FIT','CALIBRATION','METRIC_REFERENCE','METRIC_CURRENT','JOINT_ACTIONS'),'PARTITION')
    _probability_integer_v1(replicate);_probability_integer_v1(max_rows,1)
    _probability_numeric_require_v1(type(clusters) is tuple and 1<=len(clusters)<=10000,'CLUSTER_SHAPE')
    _probability_numeric_require_v1(all(type(c) is tuple and c for c in clusters),'CLUSTER_ROWS')
    flat=[_probability_numeric_text_v1(r) for c in clusters for r in c]
    _probability_numeric_require_v1(len(flat)==len(set(flat)),'ORIGINAL_ROW_DUPLICATE')
    _probability_numeric_require_v1(type(indices) is tuple and len(indices)==len(clusters),'DRAW_COUNT')
    _probability_numeric_require_v1(all(type(i) is int and 0<=i<len(clusters) for i in indices),'DRAW_INDEX')
    required_rows=sum(len(clusters[i]) for i in indices)
    _probability_numeric_require_v1(required_rows<=max_rows,'RESOURCE_ROW_BUDGET')
    return tuple(((partition,replicate,d,j),i,r) for d,i in enumerate(indices) for j,r in enumerate(clusters[i]))



def _probability_conformal_cluster_maxima_v1(scores_by_cluster: tuple[tuple[_ProbabilityFractionV1,...],...]) -> tuple[_ProbabilityFractionV1,...]:
    """Selected cluster-envelope score, not a per-row exchangeability claim."""
    _probability_numeric_require_v1(type(scores_by_cluster) is tuple and scores_by_cluster,'SCORE_CLUSTER_SHAPE')
    _probability_numeric_require_v1(all(type(c) is tuple and c and all(type(x) is _ProbabilityFractionV1 and x>=0 for x in c) for c in scores_by_cluster),'SCORE_DOMAIN')
    return tuple(max(c) for c in scores_by_cluster)



_PROBABILITY_REPLICATE_FAILURES_V1 = frozenset({
    'PREDICTION_SINGLE_CLASS', 'ZERO_VARIANCE', 'PREDICTION_FIT_FAILURE',
    'CALIBRATION_FIT_FAILURE', 'PREDICTION_CONVERGENCE', 'PREDICTION_ITERATIONS',
    'PREDICTION_PARITY', 'CANONICAL_FLOAT_HEX', 'SCALER_VARIANCE',
    'HUBER_SCALE', 'TRANSFORM_NONFINITE', 'MARGIN_NONFINITE', 'CALIBRATION_NONFINITE',
    'CALIBRATION_VERIFICATION',
})



def _probability_compile_prediction_v1(artifact: dict) -> CompiledProbabilityPredictionV1:
    """Validate full data-only custody once; copy immutable bounded inference state."""
    means, scales, beta, intercept = _probability_validate_model_v1(artifact)
    calibration = (None if artifact['kind'] == 'HUBER' else
                   (_probability_binary64_v1(artifact['calibration']['a']), _probability_binary64_v1(artifact['calibration']['b'])))
    return CompiledProbabilityPredictionV1(artifact['kind'], tuple(artifact['feature_names']),
                                       tuple(means), tuple(scales), tuple(beta), intercept, calibration)



def _probability_predict_compiled_v1(state: CompiledProbabilityPredictionV1, values: tuple[float, ...],
                               feature_names: tuple[str, ...]) -> tuple[float, float]:
    """No library import, model fit, ID-history scan, or artifact decode in this function."""
    _probability_numeric_require_v1(type(state) is CompiledProbabilityPredictionV1 and
            type(feature_names) is tuple and feature_names == state.feature_names,
            'FEATURE_ORDER_BINDING')
    _probability_numeric_require_v1(type(values) is tuple and len(values) == len(state.coefficients) and
            all(type(x) is float and math.isfinite(x) for x in values), 'FEATURE_VALUE')
    z = tuple((x - m) / s for x, m, s in zip(values, state.means, state.scales, strict=True))
    _probability_numeric_require_v1(all(math.isfinite(x) for x in z), 'TRANSFORM_NONFINITE')
    terms = (state.intercept, *(b * x for b, x in zip(state.coefficients, z, strict=True)))
    _probability_numeric_require_v1(all(math.isfinite(x) for x in terms), 'MARGIN_NONFINITE')
    try:
        margin = math.fsum(terms)
    except (ValueError, OverflowError) as exc:
        raise _ProbabilityNumericalFailureV1('MARGIN_NONFINITE') from exc
    _probability_numeric_require_v1(math.isfinite(margin), 'MARGIN_NONFINITE')
    if state.kind == 'HUBER':
        return margin, margin
    a, b = state.calibration
    u = -(a * margin + b)
    _probability_numeric_require_v1(math.isfinite(u), 'CALIBRATION_NONFINITE')
    if u >= 0:
        probability = 1.0 / (1.0 + math.exp(-u))
    else:
        e = math.exp(u)
        probability = e / (1.0 + e)
    return margin, probability



def _probability_prediction_iterations_v1(kind: str, raw: object) -> int:
    """Validate the selected native iteration representation without coercion.

    A solver may converge at its initialized point. Type/shape/bound errors are
    interface failures (not Rejected numerical slots), so a bank must stop.
    The caller separately enforces convergence warnings, geometry and parity.
    """
    import numpy as np
    if kind == 'CALIBRATED_LOGISTIC':
        if (type(raw) is not np.ndarray or raw.shape != (1,)
                or raw.dtype.kind not in 'iu'):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_ITERATIONS: classifier requires one native integer array cell')
        count = raw[0].item()
    elif kind == 'HUBER':
        if type(raw) is int:
            count = raw
        elif isinstance(raw, np.integer) and not isinstance(raw, np.bool_):
            count = raw.item()
        else:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_ITERATIONS: Huber requires a native integer scalar')
    else:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_ITERATIONS: unselected model kind')
    if type(count) is not int or not 0 <= count <= 100:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_ITERATIONS: count outside the fixed zero-to-max_iter domain')
    return count



def _probability_fit_prediction_v1(fit_rows: tuple, cal_rows: tuple, final_ids: tuple[str, ...],
                              features: tuple[str, ...], request_values: tuple, kind: str, work: dict) -> dict:
    """One original or one bootstrap fit, using only frozen constructors and source rows.

    A row is (unique original-or-occurrence ID, finite feature tuple, exact label).
    Bootstrap IDs identify occurrences; the caller retains the original index plan.
    No final feature or target is accepted by this private numerical function.
    """
    _probability_work_observation_v1()
    _probability_numeric_require_v1(kind in ('CALIBRATED_LOGISTIC', 'HUBER'), 'MODEL_KIND')
    _probability_closed_v1(work, {'base_fit_calls', 'calibration_fit_calls', 'calibration_verification_calls'})
    for v in work.values(): _probability_integer_v1(v, 0)
    for rows in (fit_rows, cal_rows):
        _probability_numeric_require_v1(type(rows) is tuple and bool(rows), 'PREDICTION_ROWS')
        _probability_unique_names_v1([r[0] for r in rows])
        for row in rows:
            _probability_numeric_require_v1(type(row) is tuple and len(row) == 3 and type(row[1]) is tuple
                    and len(row[1]) == len(features) and
                    all(type(x) is float and math.isfinite(x) for x in row[1]), 'PREDICTION_ROW')
            _probability_numeric_require_v1((kind == 'CALIBRATED_LOGISTIC' and type(row[2]) is int and row[2] in (0, 1)) or
                    (kind == 'HUBER' and type(row[2]) is Decimal and row[2].is_finite()), 'PREDICTION_LABEL')
    if kind == 'CALIBRATED_LOGISTIC':
        _probability_numeric_require_v1({r[2] for r in fit_rows} == {0, 1} and {r[2] for r in cal_rows} == {0, 1},
                'PREDICTION_SINGLE_CLASS')
    import numpy as np
    import scipy
    import sklearn
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression, HuberRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.frozen import FrozenEstimator
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits
    Xf = np.ascontiguousarray([r[1] for r in fit_rows], dtype=np.float64)
    Xc = np.ascontiguousarray([r[1] for r in cal_rows], dtype=np.float64)
    yf = np.asarray([r[2] for r in fit_rows], dtype=np.int64 if kind == 'CALIBRATED_LOGISTIC' else np.float64)
    yc = np.asarray([r[2] for r in cal_rows], dtype=np.int64 if kind == 'CALIBRATED_LOGISTIC' else np.float64)
    base = (LogisticRegression(C=1.0, l1_ratio=0.0, dual=False, tol=0.0001,
                fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None,
                solver='lbfgs', max_iter=100, verbose=0, warm_start=False, n_jobs=None)
            if kind == 'CALIBRATED_LOGISTIC' else
            HuberRegressor(epsilon=1.35, max_iter=100, alpha=0.0001,
                           warm_start=False, fit_intercept=True, tol=0.00001))
    pipe = Pipeline([('scaler', StandardScaler(copy=True, with_mean=True, with_std=True)), ('base', base)])
    _probability_require_synchronous_worker_v1()
    verification = None
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        _probability_numeric_require_v1(np.all(np.isfinite(yf)) and np.all(np.isfinite(yc)), 'PREDICTION_TARGET_CONVERSION')
        if kind == 'HUBER':
            _probability_numeric_require_v1(all(v != 0 or row[2] == 0 for rows, vals in ((fit_rows, yf), (cal_rows, yc))
                        for row, v in zip(rows, vals, strict=True)), 'PREDICTION_TARGET_UNDERFLOW')
        work['base_fit_calls'] += 1
        try:
            pipe.fit(Xf, yf)
        except (ValueError, FloatingPointError, OverflowError) as exc:
            raise _ProbabilityNumericalFailureV1('PREDICTION_FIT_FAILURE') from exc
        # Validate before calibration; do not spend another fit on invalid metadata.
        iterations = _probability_prediction_iterations_v1(kind, base.n_iter_)
        scaler = pipe.named_steps['scaler']
        _probability_numeric_require_v1(np.all(np.isfinite(scaler.var_)) and np.all(scaler.var_ > 0), 'ZERO_VARIANCE')
        _probability_selected_scaler_v1(tuple(float(x) for x in scaler.mean_),
                                   tuple(float(x) for x in scaler.var_),
                                   tuple(float(x) for x in scaler.scale_), len(fit_rows))
        before = tuple(np.array(v, copy=True) for v in
                       (base.coef_, base.intercept_, scaler.mean_, scaler.var_, scaler.scale_, scaler.n_samples_seen_))
        if kind == 'CALIBRATED_LOGISTIC':
            _probability_numeric_require_v1(base.classes_.tolist() == [0, 1], 'CLASSES')
            work['calibration_fit_calls'] += 1
            try:
                predicted = CalibratedClassifierCV(FrozenEstimator(pipe), method='sigmoid', cv=None,
                                                   n_jobs=1, ensemble=False).fit(Xc, yc)
            except (ValueError, FloatingPointError, OverflowError) as exc:
                raise _ProbabilityNumericalFailureV1('CALIBRATION_FIT_FAILURE') from exc
            _probability_numeric_require_v1(len(predicted.calibrated_classifiers_) == 1 and
                    len(predicted.calibrated_classifiers_[0].calibrators) == 1, 'CALIBRATOR_COUNT')
            sigmoid = predicted.calibrated_classifiers_[0].calibrators[0]
            calibration = {'method': 'sigmoid', 'response': 'decision_function',
                           'a': float(sigmoid.a_).hex(), 'b': float(sigmoid.b_).hex()}
            work['calibration_verification_calls'] += 1
            verified_a, verified_b, _ = _probability_checked_sigmoid_v1(pipe.decision_function(Xc), yc)
            verification = (verified_a, verified_b)
        else:
            predicted = pipe
            calibration = None
        after = (base.coef_, base.intercept_, scaler.mean_, scaler.var_, scaler.scale_, scaler.n_samples_seen_)
        _probability_numeric_require_v1(all(np.array_equal(a, b) for a, b in zip(before, after, strict=True)), 'FROZEN_BASE_MUTATION')
    _probability_numeric_require_v1(not any(issubclass(w.category, ConvergenceWarning) for w in captured), 'PREDICTION_CONVERGENCE')
    if _probability_prediction_iterations_v1(kind, base.n_iter_) != iterations:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_ITERATIONS: calibration changed the original counter')
    state = {'schema': 'QTT_MODEL_DATA_ONLY_V35', 'kind': kind, 'feature_names': list(features),
             'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                             'scipy': scipy.__version__, 'scikit-learn': sklearn.__version__},
             'scaler': {k: [float(x).hex() for x in getattr(scaler, k + '_')]
                        for k in ('mean', 'var', 'scale')},
             'coefficients': [float(x).hex() for x in base.coef_.ravel()],
             'intercept': float(np.asarray(base.intercept_).ravel()[0]).hex(),
             'classes': [0, 1] if kind == 'CALIBRATED_LOGISTIC' else [],
             'calibration': calibration, 'fit_ids': [r[0] for r in fit_rows],
             'calibration_ids': [r[0] for r in cal_rows], 'final_ids': list(final_ids)}
    state['scaler']['n_samples_seen'] = int(scaler.n_samples_seen_)
    if kind == 'HUBER':
        state['scale'] = float(base.scale_).hex()
    compiled = _probability_compile_prediction_v1(state)
    # Exact frozen request roster plus deterministic zero/basis/extreme probes.
    d = len(features)
    probes = (*request_values, *((r[1]) for r in cal_rows),
              tuple(0.0 for _ in features),
              *(tuple(1.0 if i == j else 0.0 for j in range(d)) for i in range(d)),
              *(tuple(-1.0 if i == j else 0.0 for j in range(d)) for i in range(d)),
              tuple(30.0 for _ in features), tuple(-30.0 for _ in features))
    Xp = np.ascontiguousarray(probes, dtype=np.float64)
    native = predicted.predict_proba(Xp)[:, 1] if kind == 'CALIBRATED_LOGISTIC' else predicted.predict(Xp)
    outputs = tuple(_probability_predict_compiled_v1(compiled, tuple(row), features) for row in probes)
    _probability_numeric_require_v1(all(_probability_prediction_parity_v1(kind, float(a), b[1]) for a, b in zip(native, outputs, strict=True)),
            'PREDICTION_PARITY')
    if verification is not None:
        for native_probability, (margin, _) in zip(native, outputs, strict=True):
            u = -(verification[0] * margin + verification[1])
            _probability_numeric_require_v1(math.isfinite(u), 'CALIBRATION_VERIFICATION')
            e = math.exp(-abs(u))
            checked_probability = 1.0 / (1.0 + e) if u >= 0 else e / (1.0 + e)
            _probability_numeric_require_v1(
                _probability_prediction_parity_v1(kind, float(native_probability), checked_probability),
                'CALIBRATION_VERIFICATION')
    return {'model': state, 'requests': outputs[:len(request_values)],
            'calibration_predictions': tuple(v[1] for v in outputs[len(request_values):len(request_values) + len(cal_rows)]),
            'convergence_warnings': 0, 'iterations': iterations,
            'iteration_limit_diagnostic': iterations == 100,
            'fit_calls': 2 if kind == 'CALIBRATED_LOGISTIC' else 1,
            'max_absolute_parity_error': max(abs(float(a) - b[1]) for a, b in zip(native, outputs, strict=True))}



def _probability_prediction_partition_v1(clusters: tuple, features: tuple[str, ...], *,
                                     minimum: int, cutoff_ns: int, kind: str) -> tuple:
    """Validate numerical projection shape, not accepted-source authority.

    Cluster tuple: (cluster_id, available_ns, matured_ns, info_start_ns,
                    info_end_ns, ((row_id, feature_tuple, target), ...)).
    All summaries must be derived from the separately validated original rows.
    """
    _probability_numeric_require_v1(type(clusters) is tuple and len(clusters) >= minimum, 'PREDICTION_CLUSTER_SUPPORT')
    _probability_integer_v1(cutoff_ns, 0)
    _probability_numeric_require_v1(all(type(c) is tuple and len(c) == 6 for c in clusters), 'PREDICTION_CLUSTER_SHAPE')
    _probability_unique_names_v1([c[0] for c in clusters])
    rows = []
    previous = None
    for cluster in clusters:
        _probability_numeric_require_v1(type(cluster) is tuple and len(cluster) == 6, 'PREDICTION_CLUSTER_SHAPE')
        cid, available, matured, start, end, cr = cluster
        for v in (available, matured, start, end): _probability_integer_v1(v, 0)
        _probability_numeric_require_v1(available <= cutoff_ns and matured <= cutoff_ns and start <= end <= matured,
                'PREDICTION_POINT_IN_TIME')
        order = (matured, cid)
        _probability_numeric_require_v1(previous is None or order > previous, 'PREDICTION_CLUSTER_ORDER')
        previous = order
        _probability_numeric_require_v1(type(cr) is tuple and cr, 'PREDICTION_CLUSTER_ROWS')
        for r in cr:
            _probability_numeric_require_v1(type(r) is tuple and len(r) == 3, 'PREDICTION_ROW')
            _probability_numeric_text_v1(r[0]); _probability_numeric_require_v1(type(r[1]) is tuple and len(r[1]) == len(features) and
                all(type(x) is float and math.isfinite(x) for x in r[1]), 'PREDICTION_FEATURES')
            _probability_numeric_require_v1((kind == 'CALIBRATED_LOGISTIC' and type(r[2]) is int and r[2] in (0, 1)) or
                    (kind == 'HUBER' and type(r[2]) is Decimal and r[2].is_finite()), 'PREDICTION_LABEL')
            rows.append(r)
    _probability_unique_names_v1([r[0] for r in rows])
    return tuple(rows)



def _probability_prediction_occurrence_prefix_v1(original_row_ids: tuple[str, ...]) -> str:
    """Temporary numerical occurrence labels occupy a disjoint namespace.

    Original FIT/CALIBRATION/FINAL IDs remain opaque and unchanged. Select the
    smallest unused decimal namespace component, without parsing arbitrary
    original components as integers. This helper supplies neither identity
    authority nor an alternative source roster. Its derived set is charged to
    the already admitted original-row metadata budget.
    """
    _probability_numeric_require_v1(type(original_row_ids) is tuple and bool(original_row_ids), 'PREDICTION_ORIGINAL_ROW_ROSTER')
    stem = 'V35_OCCURRENCE:'
    occupied = set()
    for row_id in original_row_ids:
        _probability_numeric_text_v1(row_id)
        if row_id.startswith(stem):
            tail = row_id[len(stem):]
            component, separator, _ = tail.partition(':')
            if separator:
                occupied.add(component)
    candidate = 0
    while str(candidate) in occupied:
        candidate += 1
    # At most one occupied component per original ID; termination is bounded.
    return f'{stem}{candidate}:'



def _probability_construct_prediction_bank_v1(*, fit_clusters: tuple, calibration_clusters: tuple,
        final_cluster_ids: tuple[str, ...], final_row_ids: tuple[str, ...], final_start_ns: int,
        feature_names: tuple[str, ...], requests: tuple, input_lock_id: str,
        prediction_input_lock_id: str, plan_id: str, master_seed: int, replicate_count: int,
        method: str, block_length: int | None, fit_cutoff_ns: int,
        calibration_cutoff_ns: int, embargo_ns: int, max_plan_cells: int,
        max_expanded_rows: int, max_prediction_cells: int, max_feature_cells: int,
        max_fit_calls: int, work: dict) -> dict:
    """Complete request-locked B-refit probability bank, not a model-use authorization.

    No defaults select budgets, seeds, data, method, or block length. The native
    owner must admit source/dependence/resource policies and the full environment
    before invoking this numerical boundary. Calling this numerical helper does not qualify an environment or authenticate its inputs.
    """
    for x in (input_lock_id, prediction_input_lock_id, plan_id): _probability_numeric_text_v1(x)
    _probability_numeric_require_v1(type(feature_names) is tuple, 'FEATURE_NAMES'); _probability_unique_names_v1(list(feature_names))
    for x in (master_seed, embargo_ns, final_start_ns): _probability_integer_v1(x, 0)
    _probability_numeric_require_v1(type(replicate_count) is int and replicate_count in (1000, 5000), 'PREDICTION_REPLICATE_POLICY')
    for x in (max_plan_cells, max_expanded_rows, max_prediction_cells, max_feature_cells, max_fit_calls): _probability_integer_v1(x, 1)
    _probability_numeric_require_v1(3 * (replicate_count + 1) <= max_fit_calls, 'PREDICTION_FIT_WORK_BUDGET')
    _probability_closed_v1(work, {'base_fit_calls', 'calibration_fit_calls', 'calibration_verification_calls'})
    _probability_numeric_require_v1(all(type(value) is int and value == 0 for value in work.values()), 'PREDICTION_WORK_ORIGIN')
    _probability_numeric_require_v1(type(requests) is tuple and bool(requests), 'PREDICTION_REQUESTS')
    for r in requests:
        _probability_numeric_require_v1(type(r) is tuple and len(r) == 2 and type(r[1]) is tuple and
                len(r[1]) == len(feature_names) and
                all(type(x) is float and math.isfinite(x) for x in r[1]), 'PREDICTION_REQUESTS')
    _probability_unique_names_v1([r[0] for r in requests])
    fr = _probability_prediction_partition_v1(fit_clusters, feature_names, minimum=97,
                    cutoff_ns=fit_cutoff_ns, kind='CALIBRATED_LOGISTIC')
    cr = _probability_prediction_partition_v1(calibration_clusters, feature_names, minimum=100,
                    cutoff_ns=calibration_cutoff_ns, kind='CALIBRATED_LOGISTIC')
    _probability_numeric_require_v1(type(final_cluster_ids) is tuple and len(final_cluster_ids) >= 30 and
            type(final_row_ids) is tuple and len(final_row_ids) >= len(final_cluster_ids), 'FINAL_CUSTODY')
    _probability_unique_names_v1(list(final_cluster_ids)); _probability_unique_names_v1(list(final_row_ids))
    csets = [set(c[0] for c in fit_clusters), set(c[0] for c in calibration_clusters), set(final_cluster_ids)]
    rsets = [set(r[0] for r in fr), set(r[0] for r in cr), set(final_row_ids)]
    _probability_numeric_require_v1(all(not (sets[a] & sets[b]) for sets in (csets, rsets) for a, b in ((0, 1), (0, 2), (1, 2))), 'SPLIT_LEAKAGE')
    _probability_numeric_require_v1(max(c[4] for c in fit_clusters) + embargo_ns < min(c[3] for c in calibration_clusters)
            and max(c[4] for c in calibration_clusters) + embargo_ns < final_start_ns,
            'PURGE_EMBARGO_OVERLAP')
    _probability_numeric_require_v1(fit_cutoff_ns < min(c[3] for c in calibration_clusters) and
            calibration_cutoff_ns < final_start_ns, 'FIT_CALIBRATION_FINAL_CUTOFF')
    sizes = (len(fit_clusters), len(calibration_clusters))
    _probability_numeric_require_v1(replicate_count * sum(sizes) <= max_plan_cells, 'PREDICTION_PLAN_BUDGET')
    _probability_numeric_require_v1((replicate_count + 1) * len(requests) <= max_prediction_cells, 'PREDICTION_OUTPUT_BUDGET')
    _probability_numeric_require_v1(all(len(cs) * max(len(c[5]) for c in cs) <= max_expanded_rows
                for cs in (fit_clusters, calibration_clusters)), 'PREDICTION_EXPANSION_BUDGET')
    _probability_numeric_require_v1(_probability_prediction_feature_cells_v1(max_expanded_rows, max_expanded_rows,
                    len(requests), len(feature_names)) <= max_feature_cells, 'PREDICTION_FEATURE_BUDGET')
    _probability_numeric_require_v1(method in ('PAIRED_IID_CLUSTERS', 'PAIRED_STATIONARY_CLUSTERS'), 'DEPENDENCE_METHOD_UNAVAILABLE')
    if method == 'PAIRED_IID_CLUSTERS': _probability_numeric_require_v1(block_length is None, 'IID_BLOCK_LENGTH')
    else: _probability_numeric_require_v1(type(block_length) is int and 1 <= block_length <= min(sizes), 'BLOCK_BOUND')
    # Row labels are temporary coordinates, not original source identities.
    # Reserve one namespace against all three original rosters before any fit.
    occurrence_prefix = _probability_prediction_occurrence_prefix_v1(
        tuple(r[0] for r in fr) + tuple(r[0] for r in cr) + final_row_ids)
    # Streams and call order are exactly the retained PCG64 plan; no resampling service.
    import numpy as np
    plans = []
    for r in range(replicate_count):
        _probability_work_observation_v1()
        pair = []
        for code, n in enumerate(sizes, 1):
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([master_seed, code, r])))
            starts = [int(x) for x in rng.integers(0, n, size=n, dtype=np.int64, endpoint=False)]
            uniforms = ([] if block_length is None else
                        [_ProbabilityFractionV1.from_float(float(x)) for x in rng.random(size=n, dtype=np.float64)])
            pair.append(_probability_resampling_indices_v1(starts, uniforms, n, block_length))
        plans.append(tuple(pair))
    request_values = tuple(r[1] for r in requests)
    original = _probability_fit_prediction_v1(fr, cr, final_row_ids, feature_names, request_values, 'CALIBRATED_LOGISTIC', work)
    records = []; counts = []; max_error = original['max_absolute_parity_error']
    fit_calls = original['fit_calls']
    for r, pair in enumerate(plans):
        _probability_work_observation_v1()
        draws = []
        for code, cs, indices in zip((1, 2), (fit_clusters, calibration_clusters), pair, strict=True):
            row_ids = [list(x[0] for x in c[5]) for c in cs]
            lineage = _probability_expand_cluster_draw_v1(row_ids, indices)
            lookup = {row[0]: row for c in cs for row in c[5]}
            draw = tuple((f'{occurrence_prefix}{code}:{r}:{occurrence}', lookup[source][1], lookup[source][2])
                         for occurrence, source in lineage)
            _probability_numeric_require_v1(len(draw) == sum(len(cs[i][5]) for i in indices), 'PREDICTION_OCCURRENCE_LINEAGE')
            draws.append(draw)
        counts.append(tuple(map(len, draws)))
        try:
            result = _probability_fit_prediction_v1(draws[0], draws[1], final_row_ids,
                                               feature_names, request_values, 'CALIBRATED_LOGISTIC', work)
        except _ProbabilityNumericalFailureV1 as exc:
            _probability_numeric_require_v1(exc.detail in _PROBABILITY_REPLICATE_FAILURES_V1, 'UNCLASSIFIED_PREDICTION_FAILURE')
            # Rejected rows stay in the fixed ordinal bank. No redraw or retry.
            records.append({'replicate': r, 'status': 'INVALID', 'values': None, 'reason': exc.detail})
            continue
        fit_calls += result['fit_calls']
        max_error = max(max_error, result['max_absolute_parity_error'])
        records.append({'replicate': r, 'status': 'VALID', 'values':
                       {q[0]: float(out[1]).hex() for q, out in zip(requests, result['requests'], strict=True)},
                        'reason': None})
    reduced = _probability_bootstrap_bank_v1(records, replicate_count, [r[0] for r in requests])
    intervals = None
    if reduced['state'] == 'COMPLETE':
        intervals = {request[0]: (float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(1, 40))),
                                  float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(39, 40))))
                     for j, request in enumerate(requests)}
    return {'schema': 'QTT_REQUEST_LOCKED_PREDICTION_BANK_V36', 'plan_id': plan_id,
            'input_lock_id': input_lock_id, 'prediction_input_lock_id': prediction_input_lock_id,
            'feature_names': feature_names, 'requests': requests, 'replicate_count': replicate_count,
            'method': method, 'block_length': block_length, 'master_seed': master_seed,
            'numpy_version': np.__version__, 'partition_codes': (1, 2), 'plans': tuple(plans),
            'ordered_cluster_ids': tuple(tuple(c[0] for c in cs) for cs in (fit_clusters, calibration_clusters)),
            'ordered_row_ids_by_cluster': tuple(tuple(tuple(row[0] for row in c[5]) for c in cs)
                                               for cs in (fit_clusters, calibration_clusters)),
            'expanded_row_counts': tuple(counts), 'original_model': original['model'],
            'original_predictions': {q[0]: out for q, out in zip(requests, original['requests'], strict=True)},
            'records': records, 'state': reduced['state'], 'intervals': intervals,
            'actual_fit_calls': {key: work[key] for key in ('base_fit_calls', 'calibration_fit_calls')},
            'successful_fit_calls': fit_calls, 'max_absolute_parity_error': max_error,
            'inference_scope': 'EXACT_LOCKED_REQUESTS_ONLY', 'model_use_authorized': False,
            'source_authentication': False, 'target_environment_qualified': False}



def _probability_prediction_interval_v1(records: list[dict], replicate_count: int,
                                  request_ids: tuple[str, ...]) -> dict:
    """Bank admission always checks every original ordinal, target and value first."""
    _probability_numeric_require_v1(type(request_ids) is tuple, 'PREDICTION_TARGETS')
    _probability_numeric_require_v1(type(replicate_count) is int and replicate_count in (1000, 5000), 'PREDICTION_REPLICATE_POLICY')
    # Validate every declared VALID row even when another slot is INVALID.
    _probability_numeric_require_v1(type(records) is list, 'REPLICATE_COUNT')
    for row in records:
        _probability_numeric_require_v1(type(row) is dict, 'REPLICATE_STATUS')
        if row.get('status') == 'VALID':
            _probability_closed_v1(row.get('values'), set(request_ids))
            # This is the selected operational-format prediction bank, not the
            # dual-domain standalone arithmetic oracle. A decimal value cannot
            # select a legacy operational migration or be rounded into validity.
            for value in row['values'].values():
                try:
                    _probability_binary64_v1(value, probability=True)
                except ContractValidationError as error:
                    raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, 'PREDICTION_SCIENTIFIC_ENCODING') from error
        elif row.get('status') == 'INVALID':
            _probability_numeric_require_v1(row.get('reason') in _PROBABILITY_REPLICATE_FAILURES_V1, 'PREDICTION_FAILURE_REASON')
    result = _probability_bootstrap_bank_v1(records, replicate_count, list(request_ids))
    if result['state'] != 'COMPLETE':
        return {'state': 'ABSTAIN', 'reason': result['state'], 'intervals': None,
                'failed_replicates': result['failed_replicates'], 'model_use_authorized': False}
    _probability_numeric_require_v1(all(0 <= x <= 1 for row in result['values'] for x in row), 'PREDICTION_RANGE')
    return {'state': 'SCORE_RESEARCH_ONLY', 'reason': None,
            'intervals': tuple((q, float(_probability_inverse_ecdf_v1(tuple(r[j] for r in result['values']), _ProbabilityFractionV1(1, 40))),
                               float(_probability_inverse_ecdf_v1(tuple(r[j] for r in result['values']), _ProbabilityFractionV1(39, 40))))
                               for j, q in enumerate(request_ids)),
            'failed_replicates': (), 'model_use_authorized': False}



def _probability_validate_prediction_lineage_v1(bank: dict) -> None:
    """Offline structural/stream replay, never proof of source or fit authenticity.

    Called at preparation admission, not inside compiled per-order inference.
    Source-owner locks still prove the original features, labels and environment.
    """
    _probability_numeric_text_v1(bank['plan_id'])
    _probability_numeric_require_v1(type(bank['feature_names']) is tuple, 'PREDICTION_FEATURE_ORDER')
    _probability_unique_names_v1(list(bank['feature_names']))
    _probability_numeric_require_v1(list(bank['feature_names']) == bank['original_model']['feature_names'],
            'PREDICTION_FEATURE_ORDER')
    B = bank['replicate_count']
    _probability_numeric_require_v1(type(B) is int and B in (1000, 5000), 'PREDICTION_REPLICATE_POLICY')
    _probability_integer_v1(bank['master_seed'], 0)
    _probability_numeric_require_v1(type(bank['partition_codes']) is tuple and
            all(type(x) is int for x in bank['partition_codes']) and
            bank['partition_codes'] == (1, 2), 'PREDICTION_PARTITION_CODES')
    method = bank['method']; block = bank['block_length']
    _probability_numeric_require_v1(type(method) is str and method in ('PAIRED_IID_CLUSTERS', 'PAIRED_STATIONARY_CLUSTERS'),
            'DEPENDENCE_METHOD_UNAVAILABLE')
    ids = bank['ordered_cluster_ids']; rows = bank['ordered_row_ids_by_cluster']
    _probability_numeric_require_v1(type(ids) is tuple and len(ids) == 2 and type(rows) is tuple and len(rows) == 2,
            'PREDICTION_LINEAGE_SHAPE')
    flat = []
    for part, minimum in enumerate((97, 100)):
        _probability_numeric_require_v1(type(ids[part]) is tuple and len(ids[part]) >= minimum,
                'PREDICTION_CLUSTER_SUPPORT')
        _probability_unique_names_v1(list(ids[part]))
        _probability_numeric_require_v1(type(rows[part]) is tuple and len(rows[part]) == len(ids[part]),
                'PREDICTION_LINEAGE_SHAPE')
        rr = []
        for group in rows[part]:
            _probability_numeric_require_v1(type(group) is tuple and bool(group), 'PREDICTION_CLUSTER_ROWS')
            _probability_unique_names_v1(list(group)); rr.extend(group)
        _probability_unique_names_v1(rr); flat.append(rr)
    _probability_numeric_require_v1(not set(ids[0]).intersection(ids[1]), 'PREDICTION_CLUSTER_LEAKAGE')
    model = bank['original_model']
    _probability_numeric_require_v1(flat[0] == model['fit_ids'] and flat[1] == model['calibration_ids'],
            'PREDICTION_ORIGINAL_ROW_ROSTER')
    _probability_numeric_require_v1(not set(flat[0]).intersection(flat[1]) and
            not set(model['final_ids']).intersection((*flat[0], *flat[1])), 'SPLIT_LEAKAGE')
    sizes = tuple(map(len, ids))
    if method == 'PAIRED_IID_CLUSTERS':
        _probability_numeric_require_v1(block is None, 'IID_BLOCK_LENGTH')
    else:
        _probability_numeric_require_v1(type(block) is int and 1 <= block <= min(sizes), 'BLOCK_BOUND')
    plans = bank['plans']; counts = bank['expanded_row_counts']
    _probability_numeric_require_v1(type(plans) is tuple and len(plans) == B and
            type(counts) is tuple and len(counts) == B, 'PREDICTION_PLAN_FRAMING')
    # Check all shapes and original-row expansion before invoking any generator.
    for pair, count in zip(plans, counts, strict=True):
        _probability_numeric_require_v1(type(pair) is tuple and len(pair) == 2 and
                type(count) is tuple and len(count) == 2, 'PREDICTION_PLAN_FRAMING')
        for part, n in enumerate(sizes):
            _probability_numeric_require_v1(type(pair[part]) is tuple and len(pair[part]) == n and
                    all(type(i) is int and 0 <= i < n for i in pair[part]),
                    'PREDICTION_PLAN_INDEX')
            _probability_numeric_require_v1(type(count[part]) is int and count[part] ==
                    sum(len(rows[part][i]) for i in pair[part]), 'PREDICTION_EXPANSION_LINEAGE')
    import numpy as np
    _probability_numeric_require_v1(type(bank['numpy_version']) is str and
            bank['numpy_version'] == model['environment']['numpy'] == np.__version__,
            'PREDICTION_PLAN_ENVIRONMENT')
    for r, pair in enumerate(plans):
        for code, n in enumerate(sizes, 1):
            gen = np.random.Generator(np.random.PCG64(np.random.SeedSequence([bank['master_seed'], code, r])))
            starts = [int(x) for x in gen.integers(0, n, size=n, dtype=np.int64, endpoint=False)]
            uniforms = ([] if block is None else
                        [_ProbabilityFractionV1.from_float(float(x)) for x in gen.random(size=n, dtype=np.float64)])
            _probability_numeric_require_v1(pair[code-1] == _probability_resampling_indices_v1(starts, uniforms, n, block),
                    'PREDICTION_PLAN_REPLAY')
    calls = _probability_closed_v1(bank['actual_fit_calls'], {'base_fit_calls', 'calibration_fit_calls'})
    for v in calls.values(): _probability_integer_v1(v, 1)
    _probability_numeric_require_v1(calls['calibration_fit_calls'] <= calls['base_fit_calls'] <= B+1,
            'PREDICTION_FIT_ACCOUNTING')
    successful = bank['successful_fit_calls']; _probability_integer_v1(successful, 2)
    valid = sum(row.get('status') == 'VALID' for row in bank['records'])
    _probability_numeric_require_v1(successful == 2*(1+valid) and calls['calibration_fit_calls'] >= 1+valid,
            'PREDICTION_FIT_ACCOUNTING')
    error = bank['max_absolute_parity_error']
    _probability_numeric_require_v1(type(error) is float and math.isfinite(error) and error >= 0.0,
            'PREDICTION_PARITY_ACCOUNTING')



def _probability_read_locked_prediction_bank_v1(bank: dict, *, input_lock_id: str,
        prediction_input_lock_id: str, feature_names: tuple[str, ...], requests: tuple) -> dict:
    """Pure numerical consumer. Exact value binding is necessary, not source acceptance."""
    _probability_closed_v1(bank, {'schema','plan_id','input_lock_id','prediction_input_lock_id','feature_names',
        'requests','replicate_count','method','block_length','master_seed','numpy_version',
        'partition_codes','plans','ordered_cluster_ids','ordered_row_ids_by_cluster','expanded_row_counts',
        'original_model','original_predictions','records','state','intervals','actual_fit_calls',
        'successful_fit_calls','max_absolute_parity_error','inference_scope','model_use_authorized',
        'source_authentication','target_environment_qualified'})
    for x in (input_lock_id, prediction_input_lock_id): _probability_numeric_text_v1(x)
    _probability_numeric_require_v1(bank['schema']=='QTT_REQUEST_LOCKED_PREDICTION_BANK_V36' and
            bank['input_lock_id']==input_lock_id and bank['prediction_input_lock_id']==prediction_input_lock_id,
            'PREDICTION_LOCK_MISMATCH')
    _probability_numeric_require_v1(type(feature_names) is tuple and feature_names==bank['feature_names'] and
            type(requests) is tuple and requests and type(bank['requests']) is tuple,
            'PREDICTION_REQUEST_MISMATCH')
    def values_key(rows):
        result=[]
        for r in rows:
            _probability_numeric_require_v1(type(r) is tuple and len(r)==2 and type(r[1]) is tuple and
                    len(r[1])==len(feature_names) and all(type(x) is float and math.isfinite(x) for x in r[1]),
                    'PREDICTION_REQUEST_MISMATCH')
            _probability_numeric_text_v1(r[0]);result.append((r[0],tuple(x.hex() for x in r[1])))
        _probability_unique_names_v1([r[0] for r in rows]);return tuple(result)
    _probability_numeric_require_v1(values_key(requests)==values_key(bank['requests']), 'PREDICTION_REQUEST_MISMATCH')
    _probability_numeric_require_v1(bank['inference_scope']=='EXACT_LOCKED_REQUESTS_ONLY' and
            all(bank[k] is False for k in ('model_use_authorized','source_authentication','target_environment_qualified')),
            'PREDICTION_AUTHORITY')
    model=bank['original_model'];compiled=_probability_compile_prediction_v1(model)
    _probability_numeric_require_v1(compiled.kind=='CALIBRATED_LOGISTIC', 'MODEL_KIND')
    _probability_closed_v1(bank['original_predictions'],set(r[0] for r in requests))
    for rid, vector in requests:
        expected=_probability_predict_compiled_v1(compiled,vector,feature_names)
        actual=bank['original_predictions'][rid]
        _probability_numeric_require_v1(type(actual) is tuple and len(actual)==2 and
                all(type(x) is float and math.isfinite(x) for x in actual) and actual==expected,
                'PREDICTION_ORIGINAL_MISMATCH')
    out=_probability_prediction_interval_v1(bank['records'],bank['replicate_count'],tuple(r[0] for r in requests))
    _probability_validate_prediction_lineage_v1(bank)
    expected_intervals=(None if out['intervals'] is None else {r[0]:(r[1],r[2]) for r in out['intervals']})
    _probability_numeric_require_v1(bank['intervals']==expected_intervals and bank['state']==('COMPLETE' if expected_intervals is not None else 'UNAVAILABLE_INVALID_REPLICATE'),
            'PREDICTION_SUMMARY_MISMATCH')
    return {'state':out['state'],'values':None if expected_intervals is None else
            tuple((r[0],bank['original_predictions'][r[0]][1],*expected_intervals[r[0]]) for r in requests),
            'reason':out['reason'],'model_use_authorized':False,'source_authentication':False,
            'record_authenticity_proven':False}



def _probability_fair_value_v1(*, probability: float, epistemic_bounds: tuple[float, float],
                         payoff_yes: str, payoff_no: str, estimand: str,
                         validity_probability: float | None, expected_void_payout: str | None) -> dict:
    """Source-admitted fixed-input payout transform, never executable net cash or an LCB."""
    _probability_numeric_require_v1(type(probability) is float and math.isfinite(probability) and 0 <= probability <= 1,
            'FAIR_VALUE_PROBABILITY')
    _probability_numeric_require_v1(type(epistemic_bounds) is tuple and len(epistemic_bounds) == 2 and
            all(type(x) is float and math.isfinite(x) and 0 <= x <= 1 for x in epistemic_bounds)
            and epistemic_bounds[0] <= epistemic_bounds[1], 'FAIR_VALUE_INTERVAL')
    _probability_numeric_require_v1(estimand in ('CONDITIONAL_ON_VALID', 'UNCONDITIONAL_EXPECTED_PAYOUT'), 'FAIR_VALUE_ESTIMAND')
    yes = _probability_dec_v1(payoff_yes); no = _probability_dec_v1(payoff_no)
    _probability_numeric_require_v1(yes >= 0 and no >= 0, 'FAIR_VALUE_PAYOUT_DOMAIN')
    if estimand == 'UNCONDITIONAL_EXPECTED_PAYOUT' and (validity_probability is None or expected_void_payout is None):
        return {'state': 'ABSTAIN', 'reason': 'VALIDITY_OR_VOID_EVIDENCE_MISSING',
                'estimand': estimand, 'expected_payout': None, 'q_only_bounds': None,
                'net_cash_lcb': None, 'model_use_authorized': False}
    if validity_probability is not None:
        _probability_numeric_require_v1(type(validity_probability) is float and math.isfinite(validity_probability)
                and 0 <= validity_probability <= 1, 'VALIDITY_PROBABILITY')
    void = None if expected_void_payout is None else _probability_dec_v1(expected_void_payout)
    if void is not None: _probability_numeric_require_v1(void >= 0, 'VOID_PAYOUT_DOMAIN')
    def value(q):
        qd=_ProbabilityFractionV1(Decimal(repr(q)))
        conditional=qd*_ProbabilityFractionV1(yes)+(1-qd)*_ProbabilityFractionV1(no)
        if estimand=='CONDITIONAL_ON_VALID':return conditional
        pv=_ProbabilityFractionV1(Decimal(repr(validity_probability)))
        return pv*conditional+(1-pv)*_ProbabilityFractionV1(void)
    point=_probability_decimal34_prediction_v1(value(probability),'ROUND_HALF_EVEN')
    exact_bounds=tuple(sorted(value(x) for x in epistemic_bounds))
    endpoints=(_probability_decimal34_prediction_v1(exact_bounds[0],'ROUND_FLOOR'),
               _probability_decimal34_prediction_v1(exact_bounds[1],'ROUND_CEILING'))
    return {'state': 'SCORE_RESEARCH_ONLY', 'reason': None, 'estimand': estimand,
            'expected_payout': str(point), 'q_only_bounds': tuple(map(str, endpoints)),
            'uncertainty_scope': 'POINTWISE_Q_ONLY_GIVEN_FIXED_PAYOUT_AND_VALIDITY_INPUTS',
            'net_cash_lcb': None, 'model_use_authorized': False}



def _probability_continuous_prediction_v1(*, fit_clusters: tuple, calibration_clusters: tuple,
        final_row_ids: tuple[str, ...], final_cluster_ids: tuple[str, ...], final_start_ns: int,
        feature_names: tuple[str, ...], requests: tuple, fit_cutoff_ns: int,
        calibration_cutoff_ns: int, embargo_ns: int, max_rows: int, max_feature_cells: int,
        work: dict | None = None) -> dict:
    """Selected Huber fit and cluster-max split-conformal numerical projection."""
    _probability_numeric_require_v1(type(feature_names) is tuple, 'FEATURE_NAMES'); _probability_unique_names_v1(list(feature_names))
    _probability_integer_v1(embargo_ns, 0)
    fr = _probability_prediction_partition_v1(fit_clusters, feature_names, minimum=97,
                                        cutoff_ns=fit_cutoff_ns, kind='HUBER')
    cr = _probability_prediction_partition_v1(calibration_clusters, feature_names, minimum=100,
                                        cutoff_ns=calibration_cutoff_ns, kind='HUBER')
    _probability_numeric_require_v1(not ({c[0] for c in fit_clusters} & {c[0] for c in calibration_clusters}) and
            not ({r[0] for r in fr} & {r[0] for r in cr}) and
            not (set(final_row_ids) & {r[0] for r in (*fr, *cr)}), 'SPLIT_LEAKAGE')
    _probability_numeric_require_v1(max(c[4] for c in fit_clusters) + embargo_ns < min(c[3] for c in calibration_clusters),
            'PURGE_EMBARGO_OVERLAP')
    _probability_numeric_require_v1(type(requests) is tuple and bool(requests), 'PREDICTION_REQUESTS')
    _probability_numeric_require_v1(type(final_cluster_ids) is tuple and len(final_cluster_ids) >= 30 and
            type(final_row_ids) is tuple and len(final_row_ids) >= len(final_cluster_ids), 'FINAL_CUSTODY')
    _probability_unique_names_v1(list(final_cluster_ids)); _probability_unique_names_v1(list(final_row_ids)); _probability_integer_v1(final_start_ns, 0)
    _probability_numeric_require_v1(not(set(final_cluster_ids) & {c[0] for c in (*fit_clusters, *calibration_clusters)}), 'SPLIT_LEAKAGE')
    _probability_numeric_require_v1(max(c[4] for c in calibration_clusters) + embargo_ns < final_start_ns and
            fit_cutoff_ns < min(c[3] for c in calibration_clusters) and calibration_cutoff_ns < final_start_ns,
            'FIT_CALIBRATION_FINAL_CUTOFF')
    for r in requests:
        _probability_numeric_require_v1(type(r) is tuple and len(r) == 2 and type(r[1]) is tuple and len(r[1]) == len(feature_names)
                and all(type(x) is float and math.isfinite(x) for x in r[1]), 'PREDICTION_REQUESTS')
    _probability_unique_names_v1([r[0] for r in requests])
    _probability_integer_v1(max_rows, 1); _probability_integer_v1(max_feature_cells, 1)
    _probability_numeric_require_v1(len(fr) + len(cr) <= max_rows, 'PREDICTION_ROW_BUDGET')
    _probability_numeric_require_v1(_probability_prediction_feature_cells_v1(len(fr), len(cr), len(requests),
                    len(feature_names)) <= max_feature_cells, 'PREDICTION_FEATURE_BUDGET')
    if work is None:
        work = {'base_fit_calls': 0, 'calibration_fit_calls': 0, 'calibration_verification_calls': 0}
    _probability_closed_v1(work, {'base_fit_calls', 'calibration_fit_calls', 'calibration_verification_calls'})
    _probability_numeric_require_v1(all(type(value) is int and value == 0 for value in work.values()),
                                    'PREDICTION_WORK_ORIGIN')
    out = _probability_fit_prediction_v1(fr, cr, final_row_ids, feature_names,
                                    tuple(r[1] for r in requests), 'HUBER', work)
    residuals = []; offset = 0
    for cluster in calibration_clusters:
        rows = cluster[5]; predictions = out['calibration_predictions'][offset:offset + len(rows)]
        residuals.append(max(abs(_ProbabilityFractionV1(r[2]) - _ProbabilityFractionV1(Decimal(repr(p))))
                             for r, p in zip(rows, predictions, strict=True)))
        offset += len(rows)
    n = len(residuals); rank = (19 * (n + 1) + 19) // 20
    _probability_numeric_require_v1(rank <= n, 'CONFORMAL_RANK_UNAVAILABLE')
    q = sorted(residuals)[rank - 1]
    # Do not round a scientific interval inward; exact rational endpoints retained.
    values = tuple((r[0], _ProbabilityFractionV1(Decimal(repr(p[1]))), _ProbabilityFractionV1(Decimal(repr(p[1]))) - q,
                    _ProbabilityFractionV1(Decimal(repr(p[1]))) + q) for r, p in zip(requests, out['requests'], strict=True))
    return {'state': 'SCORE_RESEARCH_ONLY', 'model': out['model'], 'values': values,
            'decimal34_values': tuple((r[0],str(_probability_decimal34_prediction_v1(r[1],'ROUND_HALF_EVEN')),
                str(_probability_decimal34_prediction_v1(r[2],'ROUND_FLOOR')),str(_probability_decimal34_prediction_v1(r[3],'ROUND_CEILING')))
                for r in values),
            'cluster_residuals': tuple(residuals), 'rank': rank, 'q': q,
            'original_predictions': tuple((r[0], float(p[1]).hex()) for r, p in zip(requests, out['requests'], strict=True)),
            'actual_fit_calls': dict(work), 'fit_calls': work['base_fit_calls'],
            'calibrator_fit_calls': work['calibration_fit_calls'],
            'coverage_scope': 'ONE_FUTURE_CLUSTER_FIXED_SCHEDULE_UNDER_EXCHANGEABLE_ENVELOPES',
            'model_use_authorized': False, 'empirical_coverage_proven': False,
            'max_absolute_parity_error': out['max_absolute_parity_error']}



def _probability_construct_continuous_bank_v1(*, fit_clusters, calibration_clusters,
        final_row_ids, final_cluster_ids, final_start_ns, feature_names, requests,
        fit_cutoff_ns, calibration_cutoff_ns, embargo_ns, max_rows, max_feature_cells,
        unit, input_lock_id, prediction_input_lock_id, plan_id, master_seed, replicate_count,
        method, block_length, max_plan_cells, max_expanded_rows, max_prediction_cells,
        max_fit_calls, max_model_bytes, max_record_bytes, max_total_bank_bytes,
        resource_envelope, allocation_calculation, work_roster, deadline_ns, work, attempt):
    """One original conformal fit plus B independent full scaler/Huber refits.

    This private working bank retains signed values in the parent's units. Its
    descriptive bootstrap quantiles do not replace the original cluster-envelope
    conformal interval, financial acceptance, or subsequent independent review.
    All resource values come from the original accepted source; none is a grant
    inferred from this function, successful outputs, or the current host.
    """
    import time
    from types import MappingProxyType
    from .models import _ContinuousRefitBankV1
    from .serialization import _bounded_probability_json_v1

    need = _probability_numeric_require_v1
    for value in (unit, input_lock_id, prediction_input_lock_id, plan_id):
        _probability_numeric_text_v1(value)
    _probability_integer_v1(master_seed, 0)
    need(type(replicate_count) is int and replicate_count in (1000, 5000), 'PREDICTION_REPLICATE_POLICY')
    for value in (max_rows, max_feature_cells, max_plan_cells, max_expanded_rows,
                  max_prediction_cells, max_fit_calls, max_model_bytes, max_record_bytes,
                  max_total_bank_bytes, deadline_ns):
        _probability_integer_v1(value, 1)
    _probability_closed_v1(work, {'base_fit_calls', 'calibration_fit_calls', 'calibration_verification_calls'})
    need(all(type(value) is int and value == 0 for value in work.values()), 'PREDICTION_WORK_ORIGIN')
    need(type(attempt) is dict and not attempt, 'CONTINUOUS_ORIGINAL_ATTEMPT_REQUIRED')
    envelope_fields = {'max_source_clusters', 'max_expanded_rows_per_replicate',
                       'max_prediction_targets', 'max_memory_bytes', 'max_duration_ns'}
    allocation_fields = {'index_bytes', 'prediction_bytes', 'lineage_bytes', 'fitted_state_bytes',
                         'numerical_scratch_bytes', 'python_object_bytes', 'artifact_bytes', 'storage_bytes'}
    need(type(resource_envelope) is MappingProxyType and set(resource_envelope) == envelope_fields and
         type(allocation_calculation) is MappingProxyType and set(allocation_calculation) == allocation_fields and
         type(work_roster) is MappingProxyType and set(work_roster) == set(work), 'CONTINUOUS_ACCEPTED_WORKLOAD')
    for value in (*resource_envelope.values(), *allocation_calculation.values()):
        _probability_integer_v1(value, 1)
    expected_work = {'base_fit_calls': replicate_count + 1,
                     'calibration_fit_calls': 0, 'calibration_verification_calls': 0}
    need(all(type(value) is int for value in work_roster.values()) and dict(work_roster) == expected_work and
         replicate_count + 1 <= max_fit_calls, 'PREDICTION_FIT_WORK_BUDGET')
    started = time.monotonic_ns()
    need(started < deadline_ns, 'CONTINUOUS_WORK_DEADLINE')
    deadline = min(deadline_ns, started + resource_envelope['max_duration_ns'])

    def observe():
        _probability_work_observation_v1()
        if time.monotonic_ns() >= deadline:
            raise ContractValidationError(ReasonCode.RESOURCE_BOUND_EXCEEDED, 'CONTINUOUS_WORK_DEADLINE')

    observe()
    need(type(feature_names) is tuple, 'FEATURE_NAMES')
    _probability_unique_names_v1(list(feature_names))
    need(type(fit_clusters) is tuple and type(calibration_clusters) is tuple and
         len(fit_clusters) + len(calibration_clusters) <= resource_envelope['max_source_clusters'],
         'CONTINUOUS_SOURCE_CLUSTER_BUDGET')
    need(type(requests) is tuple and bool(requests) and len(requests) <= resource_envelope['max_prediction_targets'],
         'PREDICTION_REQUESTS')
    for request in requests:
        need(type(request) is tuple and len(request) == 2 and type(request[1]) is tuple and
             len(request[1]) == len(feature_names) and
             all(type(x) is float and math.isfinite(x) for x in request[1]), 'PREDICTION_REQUESTS')
    names = _probability_unique_names_v1([request[0] for request in requests])
    for clusters in (fit_clusters, calibration_clusters):
        need(all(type(cluster) is tuple and len(cluster) == 6 and type(cluster[5]) is tuple
                 for cluster in clusters), 'PREDICTION_CLUSTER_SHAPE')
    need(sum(len(cluster[5]) for clusters in (fit_clusters, calibration_clusters) for cluster in clusters)
         <= max_rows, 'PREDICTION_ROW_BUDGET')
    fr = _probability_prediction_partition_v1(fit_clusters, feature_names, minimum=97,
                                             cutoff_ns=fit_cutoff_ns, kind='HUBER')
    cr = _probability_prediction_partition_v1(calibration_clusters, feature_names, minimum=100,
                                             cutoff_ns=calibration_cutoff_ns, kind='HUBER')
    sizes = (len(fit_clusters), len(calibration_clusters))
    expanded = tuple(len(clusters) * max(len(cluster[5]) for cluster in clusters)
                     for clusters in (fit_clusters, calibration_clusters))
    need(all(count <= max_expanded_rows and count <= resource_envelope['max_expanded_rows_per_replicate']
             for count in expanded), 'PREDICTION_EXPANSION_BUDGET')
    feature_cells = _probability_prediction_feature_cells_v1(*expanded, len(requests), len(feature_names))
    need(feature_cells <= max_feature_cells, 'PREDICTION_FEATURE_BUDGET')
    plan_cells = replicate_count * sum(sizes)
    prediction_cells = (replicate_count + 1) * len(requests)
    need(plan_cells <= max_plan_cells, 'PREDICTION_PLAN_BUDGET')
    need(prediction_cells <= max_prediction_cells, 'PREDICTION_OUTPUT_BUDGET')
    need(method in ('PAIRED_IID_CLUSTERS', 'PAIRED_STATIONARY_CLUSTERS'), 'DEPENDENCE_METHOD_UNAVAILABLE')
    if method == 'PAIRED_IID_CLUSTERS':
        need(block_length is None, 'IID_BLOCK_LENGTH')
    else:
        need(type(block_length) is int and 1 <= block_length <= min(sizes), 'BLOCK_BOUND')
    # Admit the complete original split before constructing either tape. FINAL
    # has identities only; no FINAL feature/target argument can reach the fitter.
    need(type(final_row_ids) is tuple and type(final_cluster_ids) is tuple and
         len(final_cluster_ids) >= 30 and len(final_row_ids) >= len(final_cluster_ids), 'FINAL_CUSTODY')
    need(sum(sizes) + len(final_cluster_ids) <= resource_envelope['max_source_clusters'],
         'CONTINUOUS_SOURCE_CLUSTER_BUDGET')
    _probability_unique_names_v1(list(final_row_ids)); _probability_unique_names_v1(list(final_cluster_ids))
    _probability_integer_v1(embargo_ns, 0); _probability_integer_v1(final_start_ns, 0)
    for groups in (({row[0] for row in fr}, {row[0] for row in cr}, set(final_row_ids)),
                   ({c[0] for c in fit_clusters}, {c[0] for c in calibration_clusters}, set(final_cluster_ids))):
        need(all(not groups[a] & groups[b] for a, b in ((0, 1), (0, 2), (1, 2))), 'SPLIT_LEAKAGE')
    need(max(c[4] for c in fit_clusters) + embargo_ns < min(c[3] for c in calibration_clusters) and
         max(c[4] for c in calibration_clusters) + embargo_ns < final_start_ns and
         fit_cutoff_ns < min(c[3] for c in calibration_clusters) and calibration_cutoff_ns < final_start_ns,
         'FIT_CALIBRATION_FINAL_CUTOFF')
    prefix = _probability_prediction_occurrence_prefix_v1(tuple(row[0] for row in (*fr, *cr)) + final_row_ids)
    rosters = tuple(tuple(tuple(row[0] for row in cluster[5]) for cluster in clusters)
                    for clusters in (fit_clusters, calibration_clusters))
    cluster_ids = tuple(tuple(cluster[0] for cluster in clusters) for clusters in (fit_clusters, calibration_clusters))
    basis = dict(plan_id=plan_id, input_lock_id=input_lock_id, prediction_input_lock_id=prediction_input_lock_id,
        unit=unit, feature_names=feature_names, requests=tuple((q, tuple(x.hex() for x in xs)) for q, xs in requests),
        master_seed=master_seed, replicate_count=replicate_count, method=method, block_length=block_length,
        ordered_cluster_ids=cluster_ids, ordered_row_ids_by_cluster=rosters, final_row_ids=final_row_ids,
        occurrence_prefix=prefix)
    basis_bytes = len(_bounded_probability_json_v1(basis, max_bytes=min(max_model_bytes, max_total_bank_bytes)).encode('utf-8'))
    # Bound each complete four-field record before drawing/fitting. The longest
    # finite binary64 spelling is bounded by the negative normal/subnormal ends.
    widest_hex = max((-float.fromhex('0x1.fffffffffffffp+1023')).hex(),
                     (-float.fromhex('0x0.0000000000001p-1022')).hex(), key=len)
    failures = _PROBABILITY_REPLICATE_FAILURES_V1 - {
        'PREDICTION_SINGLE_CLASS', 'PREDICTION_ITERATIONS', 'CALIBRATION_FIT_FAILURE',
        'CALIBRATION_NONFINITE', 'CALIBRATION_VERIFICATION'}
    for record in (dict(replicate=replicate_count - 1, status='VALID', values=dict.fromkeys(names, widest_hex), reason=None),
                   dict(replicate=replicate_count - 1, status='INVALID', values=None, reason=max(failures, key=len))):
        _bounded_probability_json_v1(record, max_bytes=max_record_bytes)
    # JSON index/row-count integer widths are conservatively charged; the fixed
    # per-record bound also reserves original predictions and summary fields.
    plan_bytes = replicate_count * sum(2 + count * (len(str(count - 1)) + 1) for count in sizes)
    count_bytes = replicate_count * (4 + sum(len(str(count)) + 1 for count in expanded))
    artifact_bound = basis_bytes + plan_bytes + count_bytes + max_model_bytes + (replicate_count + 2) * (max_record_bytes + 1)
    lineage_bound = basis_bytes + sum(expanded) * (len(prefix.encode('utf-8')) +
        len(str(replicate_count)) + len(str(max(expanded))) + 32 +
        max(len(row[0].encode('utf-8')) for row in (*fr, *cr)))
    need(artifact_bound <= max_total_bank_bytes and allocation_calculation['artifact_bytes'] >= artifact_bound and
         allocation_calculation['storage_bytes'] >= artifact_bound, 'CONTINUOUS_ARTIFACT_STORAGE_BUDGET')
    need(allocation_calculation['index_bytes'] >= 8 * plan_cells and
         allocation_calculation['prediction_bytes'] >= 8 * prediction_cells and
         allocation_calculation['lineage_bytes'] >= lineage_bound and
         allocation_calculation['fitted_state_bytes'] >= max_model_bytes,
         'CONTINUOUS_ALLOCATION_BUDGET')
    # Scratch and Python-object bounds are separately supplied admitted values,
    # not inferred from the logical feature-cell calculation or host free RAM.
    memory_charge = 8 * feature_cells + sum(value for key, value in allocation_calculation.items()
                                            if key != 'storage_bytes')
    need(memory_charge <= resource_envelope['max_memory_bytes'], 'CONTINUOUS_MEMORY_BUDGET')
    observe()
    attempt.update(state='PLANNED', work=work, records=[], original=None, active_ordinal=None,
        preflight=dict(fit_calls=replicate_count + 1, plan_cells=plan_cells, expanded_rows=expanded,
                       prediction_cells=prediction_cells, feature_cells=feature_cells,
                       artifact_bytes=artifact_bound, memory_bytes=memory_charge, deadline_ns=deadline))
    try:
        import numpy as np
        plans = []
        attempt['plans'] = plans
        for replicate in range(replicate_count):
            observe()
            pair = []
            for code, size in enumerate(sizes, 1):
                rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([master_seed, code, replicate])))
                starts = [int(x) for x in rng.integers(0, size, size=size, dtype=np.int64, endpoint=False)]
                uniforms = ([] if block_length is None else
                    [_ProbabilityFractionV1.from_float(float(x)) for x in rng.random(size=size, dtype=np.float64)])
                pair.append(_probability_resampling_indices_v1(starts, uniforms, size, block_length))
            plans.append(tuple(pair))
        attempt['state'], attempt['active_ordinal'] = 'FITTING_ORIGINAL', -1
        observe()
        original = _probability_continuous_prediction_v1(fit_clusters=fit_clusters,
            calibration_clusters=calibration_clusters, final_row_ids=final_row_ids,
            final_cluster_ids=final_cluster_ids, final_start_ns=final_start_ns,
            feature_names=feature_names, requests=requests, fit_cutoff_ns=fit_cutoff_ns,
            calibration_cutoff_ns=calibration_cutoff_ns, embargo_ns=embargo_ns,
            max_rows=max_rows, max_feature_cells=max_feature_cells, work=work)
        attempt['original'] = original
        need(work == {'base_fit_calls': 1, 'calibration_fit_calls': 0, 'calibration_verification_calls': 0} and
             original['fit_calls'] == 1 and original['calibrator_fit_calls'] == 0, 'CONTINUOUS_ORIGINAL_WORK')
        _bounded_probability_json_v1(original['model'], max_bytes=max_model_bytes)
        records, row_counts = attempt['records'], []
        request_values = tuple(request[1] for request in requests)
        for replicate, pair in enumerate(plans):
            observe()
            attempt['state'], attempt['active_ordinal'] = 'FITTING_REPLICATE', replicate
            draws = []
            for code, clusters, indices in zip((1, 2), (fit_clusters, calibration_clusters), pair, strict=True):
                lineage = _probability_expand_cluster_draw_v1([list(row[0] for row in cluster[5]) for cluster in clusters], indices)
                lookup = {row[0]: row for cluster in clusters for row in cluster[5]}
                draw = tuple((f'{prefix}{code}:{replicate}:{occurrence}', lookup[source][1], lookup[source][2])
                             for occurrence, source in lineage)
                need(len(draw) == sum(len(clusters[index][5]) for index in indices), 'PREDICTION_OCCURRENCE_LINEAGE')
                draws.append(draw)
            row_counts.append(tuple(map(len, draws)))
            before_work = dict(work)
            try:
                fitted = _probability_fit_prediction_v1(draws[0], draws[1], final_row_ids,
                                                       feature_names, request_values, 'HUBER', work)
            except _ProbabilityNumericalFailureV1 as exc:
                need(exc.detail in failures, 'UNCLASSIFIED_PREDICTION_FAILURE')
                record = dict(replicate=replicate, status='INVALID', values=None, reason=exc.detail)
            else:
                need(work['base_fit_calls'] == before_work['base_fit_calls'] + 1 and
                     fitted['fit_calls'] == 1, 'CONTINUOUS_REFIT_WORK')
                _bounded_probability_json_v1(fitted['model'], max_bytes=max_model_bytes)
                need(len(fitted['requests']) == len(requests), 'PREDICTION_OUTPUT_SHAPE')
                need(all(type(output) is tuple and len(output) == 2 and
                         all(type(value) is float and math.isfinite(value) for value in output) and
                         output[0].hex() == output[1].hex() for output in fitted['requests']),
                     'CONTINUOUS_SIGNED_BINARY64_OUTPUT')
                values = {request[0]: output[1].hex()
                          for request, output in zip(requests, fitted['requests'], strict=True)}
                for value in values.values():
                    _probability_functional_scalar_v1(value)
                record = dict(replicate=replicate, status='VALID', values=values, reason=None)
            need(0 <= work['base_fit_calls'] - before_work['base_fit_calls'] <= 1 and
                 work['calibration_fit_calls'] == work['calibration_verification_calls'] == 0,
                 'CONTINUOUS_NO_SIGMOID_OR_RESCUE')
            _bounded_probability_json_v1(record, max_bytes=max_record_bytes)
            records.append(record)
            observe()
        reduced = _probability_bootstrap_bank_v1(records, replicate_count, list(names))
        bounds = None
        if reduced['state'] == 'COMPLETE':
            need(work == expected_work, 'CONTINUOUS_COMPLETE_WORK')
            bounds = tuple((name,
                float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(1, 40))).hex(),
                float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(39, 40))).hex())
                for j, name in enumerate(names))
        bank = _ContinuousRefitBankV1(plan_id, input_lock_id, prediction_input_lock_id, unit,
            feature_names, requests, replicate_count, master_seed, method, block_length, np.__version__,
            cluster_ids, rosters, final_row_ids, (1, 2), tuple(plans), prefix, tuple(row_counts), original['original_predictions'],
            tuple(_bounded_probability_json_v1(record, max_bytes=max_record_bytes) for record in records),
            tuple((name, work[name]) for name in expected_work), reduced['state'], bounds)
        observe()
        attempt.update(state=bank.state, active_ordinal=None, bank=bank)
        return bank, original
    except BaseException as exc:
        # Keep the exact successful/invalid prefix and work counters. Interface,
        # deadline and resource exceptions are not recoded as numerical slots.
        attempt.update(state='INCOMPLETE_UNAVAILABLE', failure=exc)
        raise


def _probability_read_continuous_bank_v1(bank, *, input_lock_id, prediction_input_lock_id,
        feature_names, requests, unit, max_record_bytes):
    """Read only the same signed request roster; never grant probability use."""
    from .models import _ContinuousRefitBankV1
    from .serialization import _native_strict_json
    need = _probability_numeric_require_v1
    need(type(bank) is _ContinuousRefitBankV1, 'CONTINUOUS_REFIT_BANK_TYPE')
    bank.__post_init__()
    need((input_lock_id, prediction_input_lock_id, feature_names, unit) ==
         (bank.input_lock_id, bank.prediction_input_lock_id, bank.feature_names, bank.unit), 'CONTINUOUS_REQUEST_LOCK')
    need(type(feature_names) is tuple, 'CONTINUOUS_REQUEST_LOCK')
    _probability_unique_names_v1(list(feature_names))
    need(type(requests) is tuple and bool(requests) and len(requests) == len(bank.requests), 'CONTINUOUS_REQUEST_LOCK')
    for actual, expected in zip(requests, bank.requests, strict=True):
        need(type(expected) is tuple and len(expected) == 2 and type(expected[1]) is tuple and
             len(expected[1]) == len(feature_names) and
             all(type(value) is float and math.isfinite(value) for value in expected[1]), 'CONTINUOUS_REQUEST_LOCK')
        need(type(actual) is tuple and len(actual) == 2 and type(actual[0]) is str and actual[0] == expected[0] and
             type(actual[1]) is tuple and len(actual[1]) == len(expected[1]) and
             all(type(a) is float and a.hex() == b.hex() for a, b in zip(actual[1], expected[1], strict=True)),
             'CONTINUOUS_REQUEST_LOCK')
    names = list(_probability_unique_names_v1([request[0] for request in requests]))
    need(len(bank.ordered_cluster_ids) == len(bank.ordered_row_ids_by_cluster) == 2,
         'CONTINUOUS_PARTITION_ROSTERS')
    original_ids = []
    for clusters, rows in zip(bank.ordered_cluster_ids, bank.ordered_row_ids_by_cluster, strict=True):
        need(type(clusters) is tuple and type(rows) is tuple and len(clusters) == len(rows), 'CONTINUOUS_PARTITION_ROSTERS')
        _probability_unique_names_v1(list(clusters))
        for group in rows:
            need(type(group) is tuple and bool(group), 'CONTINUOUS_ROW_ROSTER')
            original_ids.extend(group)
    _probability_unique_names_v1([name for partition in bank.ordered_cluster_ids for name in partition])
    need(len(bank.ordered_cluster_ids[0]) >= 97 and len(bank.ordered_cluster_ids[1]) >= 100 and
         len(bank.final_row_ids) >= 30 and
         (bank.block_length is None or bank.block_length <= min(map(len, bank.ordered_cluster_ids))),
         'CONTINUOUS_PARTITION_ROSTERS')
    _probability_unique_names_v1([*original_ids, *bank.final_row_ids])
    need(bank.occurrence_prefix == _probability_prediction_occurrence_prefix_v1(tuple(original_ids) + bank.final_row_ids),
         'CONTINUOUS_OCCURRENCE_NAMESPACE')
    for pair, counts in zip(bank.plans, bank.expanded_row_counts, strict=True):
        need(type(pair) is tuple and len(pair) == 2 and type(counts) is tuple and len(counts) == 2,
             'CONTINUOUS_PLAN_SHAPE')
        for indices, rows, count in zip(pair, bank.ordered_row_ids_by_cluster, counts, strict=True):
            need(type(indices) is tuple and len(indices) == len(rows) and
                 all(type(index) is int and 0 <= index < len(rows) for index in indices), 'CONTINUOUS_PLAN_INDEX')
            need(type(count) is int and count == sum(len(rows[index]) for index in indices), 'CONTINUOUS_EXPANSION_LINEAGE')
    need(all(type(row) is tuple and len(row) == 2 for row in bank.original_predictions) and
         tuple(name for name, _ in bank.original_predictions) == tuple(names), 'CONTINUOUS_ORIGINAL_PREDICTION_ROSTER')
    for _, value in bank.original_predictions:
        _probability_binary64_v1(value)
    records = [_native_strict_json(record.encode('utf-8'), max_record_bytes) for record in bank.records]
    reduced = _probability_bootstrap_bank_v1(records, bank.replicate_count, names)
    for record in records:
        if record['status'] == 'VALID':
            for value in record['values'].values():
                _probability_binary64_v1(value)
    need(reduced['state'] == bank.state, 'CONTINUOUS_BANK_STATE')
    if bank.state != 'COMPLETE':
        return None
    expected_bounds = tuple((name,
        float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(1, 40))).hex(),
        float(_probability_inverse_ecdf_v1(tuple(row[j] for row in reduced['values']), _ProbabilityFractionV1(39, 40))).hex())
        for j, name in enumerate(names))
    need(bank.descriptive_bounds == expected_bounds and
         dict(bank.actual_fit_calls) == {'base_fit_calls': bank.replicate_count + 1,
             'calibration_fit_calls': 0, 'calibration_verification_calls': 0}, 'CONTINUOUS_BANK_BOUNDS_AND_WORK')
    return expected_bounds


def _probability_resampling_indices_v1(starts: list[int], uniforms: list[_ProbabilityFractionV1], n: int, block: int | None) -> tuple[int, ...]:
    """Paired IID or circular stationary resampling from an explicit random tape."""
    _probability_integer_v1(n,1);_probability_numeric_require_v1(n<=100000,'RESAMPLE_BOUND')
    _probability_numeric_require_v1(type(starts) is list and len(starts)==n and all(type(x) is int and 0<=x<n for x in starts),'RESAMPLE_STARTS')
    if block is None:
        _probability_numeric_require_v1(uniforms==[],'IID_HAS_NO_CONTINUATION_TAPE');return tuple(starts)
    _probability_integer_v1(block,1);_probability_numeric_require_v1(block<=n,'BLOCK_BOUND')
    _probability_numeric_require_v1(type(uniforms) is list and len(uniforms)==n and all(type(u) is _ProbabilityFractionV1 and 0<=u<1 for u in uniforms),'RESAMPLE_UNIFORMS')
    out=starts.copy();p=_ProbabilityFractionV1(1,block)
    for i in range(1,n):
        if uniforms[i]>p:out[i]=(out[i-1]+1)%n
    return tuple(out)



def _probability_expand_cluster_draw_v1(cluster_rows: list[list[str]], indices: tuple[int,...]) -> tuple[tuple[str,str],...]:
    """Occurrence identity and original row lineage are separate; never deduplicate draws."""
    _probability_numeric_require_v1(type(cluster_rows) is list and bool(cluster_rows),'CLUSTERS')
    seen=set()
    for rows in cluster_rows:
        for row in _probability_unique_names_v1(rows):_probability_numeric_require_v1(row not in seen,'ROW_IN_MULTIPLE_CLUSTERS');seen.add(row)
    _probability_numeric_require_v1(type(indices) is tuple and len(indices)==len(cluster_rows),'DRAW_DIMENSION')
    result=[]
    for draw,index in enumerate(indices):
        _probability_numeric_require_v1(type(index) is int and 0<=index<len(cluster_rows),'DRAW_INDEX')
        for offset,row in enumerate(cluster_rows[index]):result.append((f'draw:{draw}:row:{offset}',row))
    return tuple(result)



def _probability_functional_scalar_v1(value: object) -> _ProbabilityFractionV1:
    """Scientific result channel only; retain the decimal-only financial decoder.

    New native producers emit canonical float.hex strings. Bounded decimal strings
    are retained for the historical standalone arithmetic fixtures, not converted
    through float. The scientific hexadecimal route preserves the exact supplied
    binary64 value, including subnormals, without unbounded decimal expansion.
    """
    if type(value) is str and value.startswith(('0x', '-0x')):
        number = _probability_binary64_v1(value)
        _probability_numeric_require_v1(not (number == 0.0 and math.copysign(1.0, number) < 0.0),
                'FUNCTIONAL_NEGATIVE_ZERO')
        return _ProbabilityFractionV1.from_float(number)
    return _probability_rational_v1(value)



def _probability_cluster_functional_bank_v1(cluster_values: tuple, targets: tuple[str, ...],
                            index_plans: tuple, *, max_rows: int,
                            max_targets: int, max_plan_cells: int) -> dict:
    """Pure fixed-primitive paired reducer, not model fitting or source acceptance.

    Within-cluster and across-cluster means use exact ratios of already-computed
    finite binary64 primitives. Round only each final functional to binary64;
    reject nonzero underflow and overflow. Cache each original cluster summary,
    then use draw multiplicities; never substitute this for an estimator refit.
    Limits are explicit fixture/runtime inputs, not selected production defaults.
    """
    for limit in (max_rows, max_targets, max_plan_cells): _probability_integer_v1(limit, 1)
    _probability_numeric_require_v1(type(targets) is tuple and 0 < len(targets) <= max_targets,
            'FUNCTIONAL_TARGETS')
    _probability_unique_names_v1(list(targets))
    _probability_numeric_require_v1(type(cluster_values) is tuple and bool(cluster_values), 'FUNCTIONAL_CLUSTERS')
    n = len(cluster_values)
    _probability_numeric_require_v1(type(index_plans) is tuple and bool(index_plans), 'FUNCTIONAL_PLANS')
    _probability_numeric_require_v1(len(index_plans) <= 10000 and n * len(index_plans) <= max_plan_cells,
            'FUNCTIONAL_PLAN_BUDGET')
    _probability_numeric_require_v1(all(type(cluster) is tuple and bool(cluster) for cluster in cluster_values),
            'FUNCTIONAL_CLUSTER_ROWS')
    _probability_numeric_require_v1(sum(len(cluster) for cluster in cluster_values) <= max_rows,
            'FUNCTIONAL_ROW_BUDGET')
    summaries = []
    for cluster in cluster_values:
        _probability_numeric_require_v1(all(type(row) is tuple and len(row) == len(targets) for row in cluster),
                'FUNCTIONAL_ROW_SHAPE')
        _probability_numeric_require_v1(all(type(value) is float and math.isfinite(value)
                    for row in cluster for value in row), 'FUNCTIONAL_FLOAT')
        summaries.append(tuple(sum((_ProbabilityFractionV1.from_float(row[j]) for row in cluster), _ProbabilityFractionV1(0))
                               / len(cluster) for j in range(len(targets))))
    def encoded_means(indices):
        _probability_numeric_require_v1(type(indices) is tuple and len(indices) == n and
                all(type(i) is int and 0 <= i < n for i in indices), 'FUNCTIONAL_INDEX')
        multiplicities = [0] * n
        for i in indices: multiplicities[i] += 1
        result = {}
        for j, target in enumerate(targets):
            exact = sum((summaries[i][j] * count for i, count in enumerate(multiplicities)
                         if count), _ProbabilityFractionV1(0)) / n
            try: number = float(exact)
            except OverflowError as exc: raise _ProbabilityNumericalFailureV1('FUNCTIONAL_OVERFLOW') from exc
            _probability_numeric_require_v1(math.isfinite(number), 'FUNCTIONAL_OVERFLOW')
            _probability_numeric_require_v1(exact == 0 or number != 0.0, 'FUNCTIONAL_UNDERFLOW')
            result[target] = (0.0 if number == 0.0 else number).hex()
        return result
    original = encoded_means(tuple(range(n)))
    records = []
    for r, indices in enumerate(index_plans):
        try:
            values = encoded_means(indices)
        except _ProbabilityNumericalFailureV1 as exc:
            if exc.detail not in ('FUNCTIONAL_UNDERFLOW', 'FUNCTIONAL_OVERFLOW'):
                raise
            records.append({'replicate': r, 'status': 'INVALID',
                            'values': None, 'reason': exc.detail})
        else:
            records.append({'replicate': r, 'status': 'VALID',
                            'values': values, 'reason': None})
    return {'original': original, 'records': records, 'targets': targets,
            'independent_cluster_count': n, 'source_row_count': sum(map(len, cluster_values)),
            'model_fits': 0, 'source_authentication': False}



def _probability_bootstrap_bank_v1(records: list[dict], expected_replicates: int, targets: list[str]) -> dict:
    """No failed-replicate deletion, redraw, imputation, or variable denominator."""
    _probability_integer_v1(expected_replicates,1);_probability_numeric_require_v1(expected_replicates<=10000,'REPLICATE_BOUND');names=_probability_unique_names_v1(targets)
    _probability_numeric_require_v1(type(records) is list and len(records)==expected_replicates,'REPLICATE_COUNT')
    invalid=[];values=[]
    for i,row in enumerate(records):
        _probability_closed_v1(row,{'replicate','status','values','reason'})
        _probability_numeric_require_v1(type(row['replicate']) is int and row['replicate']==i,'REPLICATE_SEQUENCE')
        if row['status']=='INVALID':
            _probability_numeric_require_v1(row['values'] is None,'INVALID_HAS_NO_VALUES');_probability_numeric_text_v1(row['reason']);invalid.append(i)
        elif row['status']=='VALID':
            _probability_numeric_require_v1(row['reason'] is None,'VALID_HAS_NO_FAILURE');_probability_closed_v1(row['values'],set(names))
            values.append(tuple(_probability_functional_scalar_v1(row['values'][name]) for name in names))
        else:raise _ProbabilityNumericalFailureV1('REPLICATE_STATUS')
    if invalid:return {'state':'UNAVAILABLE_INVALID_REPLICATE','failed_replicates':tuple(invalid),'target_names':tuple(names),'values':None}
    return {'state':'COMPLETE','failed_replicates':(),'target_names':tuple(names),'values':tuple(values)}



def _probability_checked_sigmoid_v1(margins: object, labels: object):
    """Return checked same-objective coefficients plus raw termination evidence.

    Call only after the existing owner has validated scope, source, budget,
    selected environment and CAL lineage. The numerical worker must satisfy the
    specification's synchronous warning-context exclusivity condition. This local
    helper is not a process isolation mechanism. No replacement of public coefficients.
    """
    import numpy as np
    from scipy.optimize import minimize
    from sklearn._loss import HalfBinomialLoss
    from sklearn.exceptions import ConvergenceWarning

    _probability_require_synchronous_worker_v1()
    x = np.asarray(margins)
    y = np.asarray(labels)
    if (x.dtype != np.dtype('float64') or x.ndim != 1 or y.ndim != 1
            or x.shape != y.shape or x.size == 0
            or y.dtype.kind not in 'ifu' or not np.all(np.isfinite(x))
            or not np.all(np.isfinite(y)) or set(y.tolist()) != {0, 1}):
        raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION')
    # Copies prevent caller mutation by this reference; real custody is upstream.
    original = x.copy()
    y = y.copy()
    maximum = float(np.max(np.abs(original)))
    divisor = maximum if maximum >= 30.0 else 1.0
    scaled = original / divisor if maximum >= 30.0 else original
    negative = float(np.count_nonzero(y <= 0))
    positive = float(y.size) - negative
    targets = np.where(y > 0, (positive + 1.0) / (positive + 2.0),
                       1.0 / (negative + 2.0)).astype(np.float64)
    loss = HalfBinomialLoss()

    def objective(theta):
        predictor = -(theta[0] * scaled + theta[1]).astype(np.float64)
        values, derivative = loss.loss_gradient(
            y_true=targets, raw_prediction=predictor, sample_weight=None)
        gradient = np.asarray([-derivative @ scaled, -derivative.sum()], dtype=np.float64)
        return values.sum(), gradient

    # A success flag cannot erase a convergence warning from this same solve.
    # Filter restoration assumes the declared exclusive/context-aware worker.
    # Other warning categories are not silenced.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            result = minimize(
                objective, np.asarray([0.0, math.log((negative + 1.0) / (positive + 1.0))]),
                method='L-BFGS-B', jac=True,
                options={'gtol': 1e-6, 'ftol': 64 * np.finfo(float).eps})
    except ConvergenceWarning as exc:
        raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION') from exc
    if (type(result.status) is not int or result.status != 0
            or type(result.success) is not bool or result.success is not True):
        raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION')
    for name in ('nit', 'nfev', 'njev'):
        value = getattr(result, name)
        if type(value) is not int or value < (0 if name == 'nit' else 1):
            raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION')
    theta = np.asarray(result.x)
    gradient = np.asarray(result.jac)
    # Do not let Boolean/integer arrays or a one-element array masquerade as
    # the selected binary64 vector/scalar result. No dtype coercion is performed.
    if (theta.dtype != np.dtype('float64') or gradient.dtype != np.dtype('float64')
            or theta.shape != (2,) or gradient.shape != (2,)
            or type(result.fun) not in (float, np.float64)
            or not np.all(np.isfinite(theta)) or not np.all(np.isfinite(gradient))
            or not np.isfinite(result.fun) or result.fun < 0):
        raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION')
    a, b = float(theta[0] / divisor), float(theta[1])
    if not np.isfinite(a) or not np.isfinite(b):
        raise _ProbabilityNumericalFailureV1('CALIBRATION_VERIFICATION')
    return a, b, result


def _derive_probability_drift_result_v1(reference: dict, current: dict, reference_bank: dict, current_bank: dict) -> dict:
    """Consume the original MATH-13 decision after exact centered-tail counting."""
    need = _probability_numeric_require_v1
    fraction = _ProbabilityFractionV1
    need(type(reference) is dict and bool(reference) and type(current) is dict and
         set(reference) == set(current), 'DRIFT_FAMILY')
    need(type(reference_bank) is dict and type(reference_bank.get('target_names')) is tuple, 'DRIFT_TARGET_NAMES')
    names = _probability_unique_names_v1(list(reference_bank['target_names']))
    need(set(names) == set(reference), 'DRIFT_TARGET_NAMES')
    originals = tuple(_probability_functional_scalar_v1(reference[name]) for name in names)
    observed = tuple(_probability_functional_scalar_v1(current[name]) for name in names)
    for bank in (reference_bank, current_bank):
        need(type(bank) is dict and bank.get('state') == 'COMPLETE' and bank.get('failed_replicates') == (),
             'DRIFT_BANK_UNAVAILABLE')
        need(bank.get('target_names') == tuple(names), 'DRIFT_TARGET_ORDER')
        need(type(bank.get('values')) is tuple and len(bank['values']) > 0 and
             all(type(row) is tuple and len(row) == len(names) and all(type(x) is fraction for x in row)
                 for row in bank['values']), 'DRIFT_BANK_SHAPE')
    before, after = reference_bank['values'], current_bank['values']
    need(len(before) == len(after), 'DRIFT_REPLICATE_COUNT')
    count = len(before)
    rows, pvalues = [], []
    for index, name in enumerate(names):
        delta = observed[index] - originals[index]
        exceedances = sum(abs(w[index] - r[index] - delta) >= abs(delta) for r, w in zip(before, after, strict=True))
        pvalue = fraction(exceedances + 1, count + 1)
        pvalues.append(pvalue)
        ordered = sorted(row[index] for row in before)
        low = ordered[math.ceil(fraction(count, 40)) - 1]
        high = ordered[math.ceil(fraction(39 * count, 40)) - 1]
        rows.append({'name': name, 'change': delta, 'pvalue': pvalue,
                     'tail_numerator': exceedances + 1, 'tail_denominator': count + 1,
                     'outside_reference_band': not low <= observed[index] <= high})
    native = compute_math_13_benjamini_yekutieli(tuple(float(value) for value in pvalues), q=0.05)
    # Independent exact step-up reconstruction is only a rejection invariant.
    # A disagreement makes this family unavailable; it never overrides MATH-13.
    family_size = len(names)
    harmonic = sum((fraction(1, index) for index in range(1, family_size + 1)), fraction(0))
    order = sorted(range(family_size), key=lambda index: (pvalues[index], index))
    last = 0
    for rank, index in enumerate(order, 1):
        if pvalues[index] <= fraction(rank, 20 * family_size) / harmonic:
            last = rank
    expected = tuple(sorted(order[:last]))
    need(native.rejected_original_indices == expected, 'DRIFT_NATIVE_BY_INCONSISTENCY')
    # Retain exact arithmetic in the diagnostic summary. The accepted native
    # MATH-13 decision above remains the sole decision consumed by the producer.
    adjusted = [fraction(1)] * family_size
    running = fraction(1)
    for rank in range(family_size, 0, -1):
        index = order[rank - 1]
        running = min(running, pvalues[index] * family_size * harmonic / rank)
        adjusted[index] = running
    for index, row in enumerate(rows):
        row['adjusted_pvalue'] = adjusted[index]
        row['material_breach'] = index in native.rejected_original_indices and row['outside_reference_band']
    return {'state': 'MATERIAL_BREACH' if any(row['material_breach'] for row in rows) else 'GREEN_STATISTICAL_FAMILY_ONLY',
            'rows': tuple(rows), 'hard_gate_override_allowed': False}


def _probability_metric_plans_v1(*, master_seed: int, replicate_count: int,
        reference_clusters: int, current_clusters: int, method: str,
        block_length: int | None, max_plan_cells: int) -> tuple:
    """Retain both complete PCG64 tapes for fixed-model metric partitions 3/4."""
    need = _probability_numeric_require_v1
    for value in (reference_clusters, current_clusters, max_plan_cells):
        _probability_integer_v1(value, 1)
    _probability_integer_v1(master_seed, 0)
    need(type(replicate_count) is int and replicate_count in (1000, 5000), 'REPLICATE_COUNT')
    need(replicate_count * (reference_clusters + current_clusters) <= max_plan_cells, 'FUNCTIONAL_PLAN_BUDGET')
    need(method in ('PAIRED_IID_CLUSTERS', 'PAIRED_STATIONARY_CLUSTERS'), 'DEPENDENCE_METHOD_UNAVAILABLE')
    if method == 'PAIRED_IID_CLUSTERS':
        need(block_length is None, 'IID_BLOCK_LENGTH')
    else:
        need(type(block_length) is int and 1 <= block_length <= min(reference_clusters, current_clusters), 'BLOCK_BOUND')
    import numpy as np
    partitions = []
    for code, clusters in ((3, reference_clusters), (4, current_clusters)):
        plans = []
        for replicate in range(replicate_count):
            _probability_work_observation_v1()
            generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence([master_seed, code, replicate])))
            starts = [int(value) for value in generator.integers(0, clusters, size=clusters, dtype=np.int64, endpoint=False)]
            uniforms = ([] if block_length is None else
                        [_ProbabilityFractionV1.from_float(float(value)) for value in generator.random(size=clusters, dtype=np.float64)])
            plans.append(_probability_resampling_indices_v1(starts, uniforms, clusters, block_length))
        partitions.append(tuple(plans))
    return tuple(partitions)


from .models import (_probability_require_v1, _probability_projection_text_v1, _probability_projection_names_v1)

def _compile_probability_binary_drift_family_v1(family) -> tuple[tuple[str, str], ...]:
    _probability_projection_text_v1(family.family_ref, 'FULL_FAMILY_REF')
    _probability_projection_names_v1(family.feature_names, 'FULL_FAMILY_FEATURES')
    _probability_projection_names_v1(family.missingness_names, 'FULL_FAMILY_MISSINGNESS', empty=True)
    _probability_projection_names_v1(family.composition_names, 'FULL_FAMILY_COMPOSITION', empty=True)
    _probability_require_v1(type(family.calibration_material) is bool, 'FULL_FAMILY_MATERIALITY')
    rows = tuple((item for name in family.feature_names for item in (('feature:' + name + ':mean', 'REAL'), ('feature:' + name + ':second_moment', 'NONNEGATIVE'))))
    rows += tuple((('missing:' + name, 'UNIT_INTERVAL') for name in family.missingness_names))
    rows += (('base_rate', 'UNIT_INTERVAL'), ('brier', 'UNIT_INTERVAL'), ('log_loss', 'NONNEGATIVE'), ('ood_rate', 'UNIT_INTERVAL'))
    rows += tuple((('composition:' + name, 'UNIT_INTERVAL') for name in family.composition_names))
    if family.calibration_material:
        rows += (('calibration_intercept', 'REAL'), ('calibration_slope', 'REAL'))
    _probability_projection_names_v1(tuple((name for name, _ in rows)), 'FULL_FAMILY_TARGET_COLLISION')
    return rows

def _probability_model_predict_v1(artifact, values, *, feature_names):
    state = _probability_compile_prediction_v1(artifact)
    return _probability_predict_compiled_v1(state, tuple(values), feature_names=tuple(feature_names))[1]


from contextlib import contextmanager as _probability_contextmanager_v1
from contextvars import ContextVar as _ProbabilityContextVarV1
_probability_work_context_v1 = _ProbabilityContextVarV1("probability_work_context", default=None)


def _probability_work_observation_v1():
    import time
    limits = _probability_work_context_v1.get()
    if limits is None:
        return
    now = time.time_ns()
    if now < limits[2] or now >= limits[1] or time.monotonic_ns() >= limits[0]:
        raise ContractValidationError(ReasonCode.RESOURCE_BOUND_EXCEEDED, "PROBABILITY_NUMERICAL_WORK_EXPIRED")
    limits[2] = now


@_probability_contextmanager_v1
def _probability_numerical_work_v1(*, deadline_ns, valid_until_ns):
    import time
    from importlib import metadata
    from itertools import islice
    # A runtime join of the frozen four-component model projection, before
    # fitting. This does not replace the existing full graph, provenance,
    # ABI/platform or independently accepted model-environment preflight.
    if (tuple(sys.version_info[:3]) != (3, 14, 7) or sys.version_info.releaselevel != "final"):
        raise ContractValidationError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_MODEL_INTERPRETER_MISMATCH")
    for name, version in (("numpy", "2.5.2"), ("scipy", "1.18.1"), ("scikit-learn", "1.9.0")):
        installed = tuple(islice(metadata.distributions(name=name), 2))
        if len(installed) != 1 or installed[0].version != version:
            raise ContractValidationError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_MODEL_DISTRIBUTION_MISMATCH: " + name)
    _probability_require_synchronous_worker_v1()
    if _probability_work_context_v1.get() is not None:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "PROBABILITY_NUMERICAL_WORK_REENTRANT")
    token = _probability_work_context_v1.set([deadline_ns, valid_until_ns, time.time_ns()])
    try:
        _probability_work_observation_v1()
        # The accepted numerical profile uses one native numerical thread.
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            yield
            _probability_work_observation_v1()
        _probability_work_observation_v1()
    finally:
        _probability_work_context_v1.reset(token)


def _probability_ood_cluster_envelope_v1(*, artifact, feature_names, calibration_clusters,
        current_cluster, schedule_ref, calibration_schedule_ref, current_schedule_ref,
        max_rows, max_feature_cells):
    """Fixed-scaler cluster-envelope OOD; no exchangeability or source claim."""
    need = _probability_numeric_require_v1
    for value in (max_rows, max_feature_cells):
        _probability_integer_v1(value, 1)
    for ref in (schedule_ref, calibration_schedule_ref, current_schedule_ref):
        _probability_numeric_text_v1(ref)
    need(schedule_ref == calibration_schedule_ref == current_schedule_ref, 'OOD_SCHEDULE_BINDING')
    need(type(feature_names) is tuple and feature_names and tuple(artifact['feature_names']) == feature_names,
         'OOD_FEATURE_ORDER')
    means, scales, _, _ = _probability_validate_model_v1(artifact)
    need(type(calibration_clusters) is tuple and 100 <= len(calibration_clusters) <= max_rows and
         type(current_cluster) is tuple and bool(current_cluster), 'OOD_CLUSTER_SUPPORT')
    rows = len(current_cluster)
    for cluster in calibration_clusters:
        need(type(cluster) is tuple and bool(cluster), 'OOD_CLUSTER_SHAPE')
        rows += len(cluster)
        need(rows <= max_rows and rows * len(feature_names) <= max_feature_cells, 'OOD_FEATURE_BUDGET')
    def cluster_maximum(cluster):
        maximum = 0.0
        for values in cluster:
            _probability_work_observation_v1()
            need(type(values) is tuple and len(values) == len(feature_names) and
                 all(type(value) is float and math.isfinite(value) for value in values), 'OOD_FEATURE_VALUES')
            score = 0.0
            for value, mean, scale in zip(values, means, scales, strict=True):
                transformed = (value - mean) / scale
                need(math.isfinite(transformed), 'TRANSFORM_NONFINITE')
                score = max(score, abs(transformed))
            maximum = max(maximum, score)
        return maximum
    current = cluster_maximum(current_cluster)
    calibration = tuple(cluster_maximum(cluster) for cluster in calibration_clusters)
    numerator, denominator = 1 + sum(value >= current for value in calibration), len(calibration) + 1
    pvalue = _ProbabilityFractionV1(numerator, denominator)
    return {'state': 'OOD' if pvalue <= _ProbabilityFractionV1(1, 100) else 'IN_SUPPORT',
            'current_prefix_maximum': current, 'calibration_cluster_maxima': calibration,
            'tail_numerator': numerator, 'tail_denominator': denominator, 'pvalue': pvalue,
            'schedule_ref': schedule_ref, 'coverage_scope': 'EXCHANGEABLE_COMPLETE_CLUSTER_ENVELOPES_REQUIRED',
            'source_authentication': False, 'empirical_coverage_proven': False, 'model_use_authorized': False}
