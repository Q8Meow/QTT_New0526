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


def _v34_on_price_grid(
    value: Decimal, ranges: Sequence[Mapping[str, object]]
) -> bool:
    for index, row in enumerate(ranges):
        minimum = exact_decimal(
            row.get("minimum"), field_name=f"price_ranges[{index}].minimum"
        )
        maximum = exact_decimal(
            row.get("maximum"), field_name=f"price_ranges[{index}].maximum"
        )
        step = exact_decimal(
            row.get("step"), field_name=f"price_ranges[{index}].step"
        )
        if minimum > maximum or step <= 0:
            _fail("price range minimum/maximum/step is invalid")
        if minimum <= value <= maximum:
            with localcontext(decimal_context_v1()):
                return (value - minimum) % step == 0
    return False


def compute_math_36_kalshi_binary_book_transform(
    yes_bids: Sequence[DecimalInput],
    no_bids: Sequence[DecimalInput],
    payout: DecimalInput,
    book_sequence: int,
    expected_sequence: int,
    book_state: str,
    price_ranges: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    if (
        isinstance(book_sequence, bool)
        or not isinstance(book_sequence, int)
        or isinstance(expected_sequence, bool)
        or not isinstance(expected_sequence, int)
        or book_sequence != expected_sequence
        or book_state != "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS"
    ):
        _fail("Kalshi book must be current, contiguous, and sequence-exact")
    yes = tuple(
        exact_decimal(value, field_name=f"yes_bids[{index}]")
        for index, value in enumerate(_v34_list(yes_bids, "yes_bids"))
    )
    no = tuple(
        exact_decimal(value, field_name=f"no_bids[{index}]")
        for index, value in enumerate(_v34_list(no_bids, "no_bids"))
    )
    payout_value = exact_decimal(payout, field_name="payout")
    if payout_value <= 0:
        _fail("payout must be positive")
    ranges = [
        _v34_mapping(row, f"price_ranges[{index}]")
        for index, row in enumerate(_v34_list(price_ranges, "price_ranges"))
    ]
    if any(
        value < 0
        or value > payout_value
        or not _v34_on_price_grid(value, ranges)
        for value in (*yes, *no)
    ):
        _fail("book price is outside the active market-specific grid")
    best_yes = max(yes)
    best_no = max(no)
    with localcontext(decimal_context_v1()):
        yes_ask = payout_value - best_no
        no_ask = payout_value - best_yes
    if (
        not _v34_on_price_grid(yes_ask, ranges)
        or not _v34_on_price_grid(no_ask, ranges)
    ):
        _fail("derived complements are outside the active price grid")
    return {
        "best_yes_bid": best_yes,
        "best_no_bid": best_no,
        "derived_yes_ask": yes_ask,
        "derived_no_ask": no_ask,
        "book_sequence": book_sequence,
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
from .economic_math import TRANCHE_C_MATH_SPECIFICATIONS


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
    implementation = (
        IMPLEMENTATION_REGISTRY["MATH-36"].callable
        if math_spec_id == "MATH-36"
        else specification.implementation
    )
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
