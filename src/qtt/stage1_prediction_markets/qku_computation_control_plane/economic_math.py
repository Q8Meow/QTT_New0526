"""Pure deterministic Tranche-C economic mathematics (MATH-26 through MATH-38)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from types import MappingProxyType
from typing import Mapping, Sequence

from .context import (
    QuantizationPolicyV1,
    QuantizationReceiptV1,
    decimal_context_v1,
    exact_decimal,
    quantize_decimal_v1,
    parse_utc,
)
from .errors import ContractValidationError, NumericDomainError, ReasonCode


DecimalInput = Decimal | str | int


def _decimal(value: DecimalInput, field_name: str) -> Decimal:
    return exact_decimal(value, field_name=field_name)


def _nonnegative(value: DecimalInput, field_name: str) -> Decimal:
    result = _decimal(value, field_name)
    if result < 0:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, f"{field_name} must be nonnegative")
    return result


def _probability(value: DecimalInput, field_name: str) -> Decimal:
    result = _decimal(value, field_name)
    if result < 0 or result > 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, f"{field_name} must be in [0, 1]")
    return result


def _nonempty(values: Sequence[DecimalInput], field_name: str) -> tuple[Decimal, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{field_name} must be nonempty")
    return tuple(_decimal(value, f"{field_name}[{index}]") for index, value in enumerate(values))


def _require_positive_semidefinite(matrix: tuple[tuple[Decimal, ...], ...]) -> None:
    """Exact Schur-complement PSD test under the canonical Decimal context."""

    working = [list(row) for row in matrix]
    with localcontext(decimal_context_v1()) as context:
        while working:
            if any(working[index][index] < 0 for index in range(len(working))):
                raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "covariance is not positive semidefinite")
            pivot_index = next((index for index in range(len(working)) if working[index][index] > 0), None)
            if pivot_index is None:
                if any(value != 0 for row in working for value in row):
                    raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "zero-variance covariance block has nonzero covariance")
                return
            if pivot_index:
                working[0], working[pivot_index] = working[pivot_index], working[0]
                for row in working:
                    row[0], row[pivot_index] = row[pivot_index], row[0]
            pivot = working[0][0]
            working = [
                [
                    context.subtract(working[i][j], context.divide(context.multiply(working[i][0], working[0][j]), pivot))
                    for j in range(1, len(working))
                ]
                for i in range(1, len(working))
            ]


@dataclass(frozen=True, slots=True)
class KellyFractionV1:
    raw_fraction: Decimal
    sizing_candidate: Decimal


@dataclass(frozen=True, slots=True)
class TailRiskV1:
    value_at_risk: Decimal
    conditional_value_at_risk: Decimal
    confidence: Decimal


@dataclass(frozen=True, slots=True)
class QuantizedEconomicAmountV1:
    amount_before_rounding: Decimal
    amount_after_rounding: Decimal
    quantization_receipt: QuantizationReceiptV1
    component_class: str
    source_binding_ref: str
    embedded_in_price: bool = False

    def __post_init__(self) -> None:
        if not self.component_class or not self.source_binding_ref:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "economic amount lineage is required")
        if type(self.embedded_in_price) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "embedded_in_price must be bool")
        if self.amount_after_rounding != self.quantization_receipt.post_value:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "quantization receipt/output mismatch")


@dataclass(frozen=True, slots=True)
class FeeScheduleBindingV1:
    """Point-in-time source custody for a venue/market fee schedule."""

    binding_ref: str
    venue_ref: str
    market_or_category_ref: str
    schedule_version: str
    source_epoch_ref: str
    valid_from: datetime | str
    valid_until: datetime | str | None
    evaluated_at: datetime | str
    component_classes: tuple[str, ...]
    component_rate_bindings: tuple[tuple[str, DecimalInput], ...]

    def __post_init__(self) -> None:
        for name in ("binding_ref", "venue_ref", "market_or_category_ref", "schedule_version", "source_epoch_ref"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"fee binding {name} is required")
        if (
            not isinstance(self.component_classes, tuple)
            or not self.component_classes
            or any(not isinstance(value, str) or not value for value in self.component_classes)
            or len(self.component_classes) != len(set(self.component_classes))
        ):
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "fee component classes must be explicit and unique")
        if not isinstance(self.component_rate_bindings, tuple) or not self.component_rate_bindings:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "fee component rate bindings are required")
        rates: dict[str, Decimal] = {}
        for row in self.component_rate_bindings:
            if not isinstance(row, tuple) or len(row) != 2:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "fee rate binding must be a (component, rate) pair")
            component, value = row
            if not isinstance(component, str) or not component or component in rates or component not in self.component_classes:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "fee rate component is missing, duplicate, or outside the schedule")
            rates[component] = _decimal(value, f"component_rate[{component}]")
        valid_from = parse_utc(self.valid_from, field_name="valid_from")
        valid_until = None if self.valid_until is None else parse_utc(self.valid_until, field_name="valid_until")
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        if evaluated < valid_from or (valid_until is not None and evaluated >= valid_until):
            raise ContractValidationError(ReasonCode.SOURCE_EPOCH_STALE, "fee schedule is not effective at the declared evaluation time")
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "component_rate_bindings", tuple((component, rates[component]) for component, _ in self.component_rate_bindings))

    def rate_for(self, component_class: str) -> Decimal:
        for component, rate in self.component_rate_bindings:
            if component == component_class:
                return rate  # type: ignore[return-value]
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"fee schedule does not bind {component_class}",
        )


@dataclass(frozen=True, slots=True)
class FillProbabilityModelArtifactV1:
    """Externally supplied model output and calibration custody; no model is selected here."""

    artifact_id: str
    artifact_version: str
    feature_schema_ref: str
    calibration_receipt_ref: str
    scope_ref: str
    horizon_seconds: int
    probability: DecimalInput
    feature_snapshot_ref: str
    feature_observed_at: datetime | str
    evaluated_at: datetime | str
    artifact_valid_until: datetime | str
    maximum_feature_age: timedelta
    calibration_state: str

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "artifact_version",
            "feature_schema_ref",
            "calibration_receipt_ref",
            "scope_ref",
            "feature_snapshot_ref",
            "calibration_state",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, f"{name} is required")
        if isinstance(self.horizon_seconds, bool) or not isinstance(self.horizon_seconds, int) or self.horizon_seconds <= 0:
            raise ContractValidationError(ReasonCode.OUT_OF_DOMAIN, "horizon_seconds must be positive")
        observed = parse_utc(self.feature_observed_at, field_name="feature_observed_at")
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        valid_until = parse_utc(self.artifact_valid_until, field_name="artifact_valid_until")
        if not isinstance(self.maximum_feature_age, timedelta) or self.maximum_feature_age <= timedelta(0):
            raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "maximum_feature_age must be explicit and positive")
        if self.calibration_state != "VALIDATED" or evaluated < observed or evaluated - observed > self.maximum_feature_age or evaluated >= valid_until:
            raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "model calibration, validity, or feature freshness gate failed")
        object.__setattr__(self, "probability", _probability(self.probability, "probability"))
        object.__setattr__(self, "feature_observed_at", observed)
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "artifact_valid_until", valid_until)


@dataclass(frozen=True, slots=True)
class FillQuantityDistributionArtifactV1:
    artifact_id: str
    artifact_version: str
    source_binding_ref: str
    scope_ref: str
    horizon_seconds: int
    evaluated_at: datetime | str
    artifact_valid_until: datetime | str
    order_quantity: DecimalInput
    normalization_tolerance: DecimalInput
    fill_quantity_distribution: tuple[tuple[DecimalInput, DecimalInput], ...]

    def __post_init__(self) -> None:
        for name in ("artifact_id", "artifact_version", "source_binding_ref", "scope_ref"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, f"distribution {name} is required")
        if isinstance(self.horizon_seconds, bool) or not isinstance(self.horizon_seconds, int) or self.horizon_seconds <= 0:
            raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "distribution horizon must be explicit and positive")
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        valid_until = parse_utc(self.artifact_valid_until, field_name="artifact_valid_until")
        if evaluated >= valid_until or not isinstance(self.fill_quantity_distribution, tuple) or not self.fill_quantity_distribution:
            raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "distribution artifact is stale or empty")
        object.__setattr__(self, "order_quantity", _nonnegative(self.order_quantity, "order_quantity"))
        object.__setattr__(self, "normalization_tolerance", _nonnegative(self.normalization_tolerance, "normalization_tolerance"))
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "artifact_valid_until", valid_until)


@dataclass(frozen=True, slots=True)
class ActivePriceGridRangeV1:
    minimum: DecimalInput
    maximum: DecimalInput
    step: DecimalInput

    def __post_init__(self) -> None:
        minimum = _decimal(self.minimum, "price_grid.minimum")
        maximum = _decimal(self.maximum, "price_grid.maximum")
        step = _decimal(self.step, "price_grid.step")
        if minimum < 0 or minimum > maximum or step <= 0:
            raise NumericDomainError(
                ReasonCode.OUT_OF_DOMAIN,
                "active price-grid range is invalid",
            )
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "step", step)

    def contains(self, value: Decimal) -> bool:
        with localcontext(decimal_context_v1()):
            return (
                self.minimum <= value <= self.maximum
                and (value - self.minimum) % self.step == 0
            )


@dataclass(frozen=True, slots=True)
class BinaryBookSnapshotV1:
    snapshot_ref: str
    sequence_ref: str
    source_binding_ref: str
    unit: str
    basis: str
    yes_bids: tuple[DecimalInput, ...]
    no_bids: tuple[DecimalInput, ...]
    payout: DecimalInput
    book_sequence: int
    expected_sequence: int
    book_state: str
    active_price_grid_ranges: tuple[ActivePriceGridRangeV1, ...]

    def __post_init__(self) -> None:
        for name in ("snapshot_ref", "sequence_ref", "source_binding_ref", "unit", "basis"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"book snapshot {name} is required")
        yes = _nonempty(self.yes_bids, "yes_bids")
        no = _nonempty(self.no_bids, "no_bids")
        payout = _decimal(self.payout, "payout")
        if (
            isinstance(self.book_sequence, bool)
            or not isinstance(self.book_sequence, int)
            or isinstance(self.expected_sequence, bool)
            or not isinstance(self.expected_sequence, int)
            or self.book_sequence != self.expected_sequence
            or self.book_state != "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS"
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "binary book must be current, contiguous, and sequence-exact",
            )
        if (
            not isinstance(self.active_price_grid_ranges, tuple)
            or not self.active_price_grid_ranges
            or any(
                not isinstance(row, ActivePriceGridRangeV1)
                for row in self.active_price_grid_ranges
            )
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "typed active price-grid ranges are required",
            )
        if payout <= 0 or any(value < 0 or value > payout for value in (*yes, *no)):
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "binary book levels must be within the positive payout")
        if any(left >= right for left, right in zip(yes, yes[1:])) or any(left >= right for left, right in zip(no, no[1:])):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "binary book ladders must be strictly ascending with best bid last")
        if any(
            not any(price_range.contains(value) for price_range in self.active_price_grid_ranges)
            for value in (*yes, *no)
        ):
            raise NumericDomainError(
                ReasonCode.OUT_OF_DOMAIN,
                "binary book bid is outside the active price grid",
            )
        with localcontext(decimal_context_v1()) as context:
            complements = (
                context.subtract(payout, no[-1]),
                context.subtract(payout, yes[-1]),
            )
        if any(
            not any(price_range.contains(value) for price_range in self.active_price_grid_ranges)
            for value in complements
        ):
            raise NumericDomainError(
                ReasonCode.OUT_OF_DOMAIN,
                "binary book derived complement is outside the active price grid",
            )
        object.__setattr__(self, "yes_bids", yes)
        object.__setattr__(self, "no_bids", no)
        object.__setattr__(self, "payout", payout)


@dataclass(frozen=True, slots=True)
class BinaryBookTouchesV1:
    snapshot_ref: str
    sequence_ref: str
    source_binding_ref: str
    book_sequence: int
    yes_implied_ask: Decimal
    no_implied_ask: Decimal
    payout: Decimal
    unit: str
    basis: str
    derivation_id: str = "MATH-36"

    def __post_init__(self) -> None:
        for name in ("snapshot_ref", "sequence_ref", "source_binding_ref", "unit", "basis", "derivation_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"book touch {name} is required")
        if isinstance(self.book_sequence, bool) or not isinstance(self.book_sequence, int):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "book touch sequence must be an integer",
            )
        payout = _decimal(self.payout, "payout")
        yes = _decimal(self.yes_implied_ask, "yes_implied_ask")
        no = _decimal(self.no_implied_ask, "no_implied_ask")
        if payout <= 0 or yes < 0 or yes > payout or no < 0 or no > payout:
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "derived binary book touches are outside payout")
        object.__setattr__(self, "payout", payout)
        object.__setattr__(self, "yes_implied_ask", yes)
        object.__setattr__(self, "no_implied_ask", no)


def expected_value_of_information_v1(
    current_action_values: Sequence[DecimalInput],
    new_information_scenarios: Sequence[tuple[DecimalInput, Sequence[DecimalInput]]],
    acquisition_cost: DecimalInput,
) -> Decimal:
    """MATH-26: posterior expected best utility less current best and full cost."""

    current = _nonempty(current_action_values, "current_action_values")
    if not new_information_scenarios:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "new_information_scenarios are required")
    probability_sum = Decimal(0)
    posterior_best = Decimal(0)
    with localcontext(decimal_context_v1()) as context:
        for index, scenario in enumerate(new_information_scenarios):
            if not isinstance(scenario, tuple) or len(scenario) != 2:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scenario must be (probability, action_values)")
            probability = _probability(scenario[0], f"scenario[{index}].probability")
            values = _nonempty(scenario[1], f"scenario[{index}].action_values")
            if len(values) != len(current):
                raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "scenario action utilities must align with current actions")
            probability_sum = context.add(probability_sum, probability)
            posterior_best = context.add(posterior_best, context.multiply(probability, max(values)))
        if probability_sum != 1:
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "scenario probabilities must sum exactly to one")
        return context.subtract(context.subtract(posterior_best, max(current)), _nonnegative(acquisition_cost, "acquisition_cost"))


def binary_kelly_fraction_v1(win_probability: DecimalInput, net_odds: DecimalInput) -> KellyFractionV1:
    """MATH-27: retain the raw fraction and separately expose max(0, raw)."""

    probability = _probability(win_probability, "win_probability")
    odds = _decimal(net_odds, "net_odds")
    if odds <= 0:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "net_odds must be positive")
    with localcontext(decimal_context_v1()) as context:
        raw = context.divide(
            context.subtract(context.multiply(odds, probability), context.subtract(Decimal(1), probability)),
            odds,
        )
    return KellyFractionV1(raw_fraction=raw, sizing_candidate=max(Decimal(0), raw))


def fractional_kelly_v1(
    full_kelly_fraction: DecimalInput,
    fraction_multiplier: DecimalInput,
    risk_caps: Sequence[DecimalInput],
) -> Decimal:
    """MATH-28: cap a nonnegative fractional-Kelly candidate by every supplied cap."""

    full = _decimal(full_kelly_fraction, "full_kelly_fraction")
    multiplier = _decimal(fraction_multiplier, "fraction_multiplier")
    if multiplier <= 0 or multiplier > 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "fraction_multiplier must be in (0, 1]")
    caps = _nonempty(risk_caps, "risk_caps")
    if any(cap < 0 for cap in caps):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "risk caps must be nonnegative")
    with localcontext(decimal_context_v1()) as context:
        candidate = context.multiply(max(Decimal(0), full), multiplier)
    return min((candidate, *caps))


def mean_variance_utility_v1(
    weights: Sequence[DecimalInput],
    expected_returns: Sequence[DecimalInput],
    covariance: Sequence[Sequence[DecimalInput]],
    risk_aversion: DecimalInput,
    transaction_cost: DecimalInput,
) -> Decimal:
    """MATH-29: mu^T w - lambda/2 w^T Sigma w - declared transaction cost."""

    weight = _nonempty(weights, "weights")
    mean = _nonempty(expected_returns, "expected_returns")
    if len(weight) != len(mean) or len(covariance) != len(weight):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "mean, weights and covariance dimensions must align")
    matrix = tuple(_nonempty(row, f"covariance[{index}]") for index, row in enumerate(covariance))
    if any(len(row) != len(weight) for row in matrix):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "covariance must be square")
    risk = _nonnegative(risk_aversion, "risk_aversion")
    cost = _nonnegative(transaction_cost, "transaction_cost")
    with localcontext(decimal_context_v1()) as context:
        symmetric = tuple(
            tuple(context.divide(context.add(matrix[i][j], matrix[j][i]), Decimal(2)) for j in range(len(weight)))
            for i in range(len(weight))
        )
        _require_positive_semidefinite(symmetric)
        mean_term = sum((context.multiply(w, m) for w, m in zip(weight, mean, strict=True)), Decimal(0))
        variance = sum(
            (
                context.multiply(context.multiply(weight[i], symmetric[i][j]), weight[j])
                for i in range(len(weight))
                for j in range(len(weight))
            ),
            Decimal(0),
        )
        if variance < 0:
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "covariance produces negative variance without a declared PSD-repair receipt")
        return context.subtract(context.subtract(mean_term, context.divide(context.multiply(risk, variance), Decimal(2))), cost)


def empirical_expected_shortfall_v1(losses: Sequence[DecimalInput], alpha: DecimalInput) -> Decimal:
    """MATH-31: exact equal-weight worst-tail mean with fractional boundary mass."""

    observations = sorted(_nonempty(losses, "losses"), reverse=True)
    confidence = _probability(alpha, "alpha")
    if confidence <= 0 or confidence >= 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "alpha must be in (0, 1)")
    with localcontext(decimal_context_v1()) as context:
        observation_mass = context.divide(Decimal(1), Decimal(len(observations)))
        required_mass = context.subtract(Decimal(1), confidence)
        remaining = required_mass
        weighted_loss = Decimal(0)
        for loss in observations:
            if remaining <= 0:
                break
            used = min(observation_mass, remaining)
            weighted_loss = context.add(weighted_loss, context.multiply(loss, used))
            remaining = context.subtract(remaining, used)
        if remaining != 0:
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "insufficient empirical tail support")
        return context.divide(weighted_loss, required_mass)


def conditional_value_at_risk_v1(losses: Sequence[DecimalInput], alpha: DecimalInput) -> TailRiskV1:
    """MATH-30: exact empirical RU value using the upper breakpoint tie convention."""

    observations = sorted(_nonempty(losses, "losses"), reverse=True)
    confidence = _probability(alpha, "alpha")
    if confidence <= 0 or confidence >= 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "alpha must be in (0, 1)")
    with localcontext(decimal_context_v1()) as context:
        observation_mass = context.divide(Decimal(1), Decimal(len(observations)))
        remaining = context.subtract(Decimal(1), confidence)
        value_at_risk = observations[0]
        for loss in observations:
            value_at_risk = loss
            remaining = context.subtract(remaining, min(observation_mass, remaining))
            if remaining == 0:
                break
    return TailRiskV1(
        value_at_risk=value_at_risk,
        conditional_value_at_risk=empirical_expected_shortfall_v1(observations, confidence),
        confidence=confidence,
    )


def implementation_shortfall_v1(
    *,
    side: str,
    quantity: DecimalInput,
    execution_price: DecimalInput,
    decision_price: DecimalInput,
    explicit_fees: DecimalInput,
    opportunity_cost_unfilled: DecimalInput,
    other_declared_costs: DecimalInput,
) -> Decimal:
    """MATH-32 with BUY positive and SELL negative signed quantity."""

    if side not in {"BUY", "SELL"}:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "side must be BUY or SELL")
    qty = _nonnegative(quantity, "quantity")
    signed_qty = qty if side == "BUY" else -qty
    with localcontext(decimal_context_v1()) as context:
        market = context.multiply(signed_qty, context.subtract(_decimal(execution_price, "execution_price"), _decimal(decision_price, "decision_price")))
        return sum(
            (
                market,
                _decimal(explicit_fees, "explicit_fees"),
                _decimal(opportunity_cost_unfilled, "opportunity_cost_unfilled"),
                _decimal(other_declared_costs, "other_declared_costs"),
            ),
            Decimal(0),
        )


def spread_cost_v1(*, side: str, quantity: DecimalInput, execution_price: DecimalInput, midpoint_at_decision: DecimalInput) -> Decimal:
    """MATH-33 immediate spread cost, separated from later market movement."""

    if side not in {"BUY", "SELL"}:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "side must be BUY or SELL")
    quantity_decimal = _nonnegative(quantity, "quantity")
    signed_quantity = quantity_decimal if side == "BUY" else -quantity_decimal
    with localcontext(decimal_context_v1()) as context:
        return context.multiply(signed_quantity, context.subtract(_decimal(execution_price, "execution_price"), _decimal(midpoint_at_decision, "midpoint_at_decision")))


def global_prediction_market_fee_v1(
    *,
    contracts: DecimalInput,
    fee_rate: DecimalInput,
    price: DecimalInput,
    schedule_binding: FeeScheduleBindingV1,
    quantization_policy: QuantizationPolicyV1,
    receipt_id: str,
) -> QuantizedEconomicAmountV1:
    """MATH-34; a separate additive fee component, never silently embedded."""

    if not isinstance(schedule_binding, FeeScheduleBindingV1) or "PLATFORM_FEE" not in schedule_binding.component_classes:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "current platform-fee schedule binding is required")
    if not isinstance(quantization_policy, QuantizationPolicyV1):
        raise ContractValidationError(ReasonCode.QUANTIZATION_POLICY_MISSING, "typed fee quantization policy is required")
    if (
        quantization_policy.increment != Decimal("0.00001")
        or quantization_policy.scale != 5
        or quantization_policy.rounding.value != "ROUND_HALF_EVEN"
        or quantization_policy.source_binding_ref != schedule_binding.binding_ref
    ):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "MATH-34 requires the currentized 5dp HALF_EVEN boundary")
    quantity = _nonnegative(contracts, "contracts")
    rate = _nonnegative(fee_rate, "fee_rate")
    if rate != schedule_binding.rate_for("PLATFORM_FEE"):
        raise ContractValidationError(ReasonCode.SOURCE_CONFLICT, "fee_rate conflicts with the effective schedule binding")
    probability = _probability(price, "price")
    with localcontext(decimal_context_v1()) as context:
        raw = context.multiply(context.multiply(context.multiply(quantity, rate), probability), context.subtract(Decimal(1), probability))
    receipt = quantize_decimal_v1(raw, policy=quantization_policy, receipt_id=receipt_id)
    return QuantizedEconomicAmountV1(raw, receipt.post_value, receipt, "EXPLICIT_VENUE_FEE", schedule_binding.binding_ref)


def us_prediction_market_fee_or_rebate_v1(
    *,
    contracts: DecimalInput,
    theta: DecimalInput,
    price: DecimalInput,
    liquidity_role: str,
    schedule_binding: FeeScheduleBindingV1,
    quantization_policy: QuantizationPolicyV1,
    receipt_id: str,
) -> QuantizedEconomicAmountV1:
    """MATH-35; signed fee/rebate amount under an explicit effective schedule."""

    if liquidity_role not in {"MAKER", "TAKER"} or not isinstance(schedule_binding, FeeScheduleBindingV1):
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "liquidity role and effective schedule are required")
    component_required = "MAKER_REBATE" if liquidity_role == "MAKER" else "TAKER_FEE"
    if component_required not in schedule_binding.component_classes:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "fee schedule does not bind the requested liquidity role")
    if not isinstance(quantization_policy, QuantizationPolicyV1):
        raise ContractValidationError(ReasonCode.QUANTIZATION_POLICY_MISSING, "typed fee quantization policy is required")
    if quantization_policy.increment != Decimal("0.01") or quantization_policy.scale != 2 or quantization_policy.rounding.value != "ROUND_HALF_EVEN" or quantization_policy.source_binding_ref != schedule_binding.binding_ref:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "MATH-35 requires the currentized bankers-cent boundary")
    quantity = _nonnegative(contracts, "contracts")
    rate = _decimal(theta, "theta")
    if rate != schedule_binding.rate_for(component_required):
        raise ContractValidationError(ReasonCode.SOURCE_CONFLICT, "theta conflicts with the effective schedule binding")
    if (liquidity_role == "MAKER" and rate > 0) or (liquidity_role == "TAKER" and rate < 0):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "signed theta conflicts with maker/taker economic role")
    probability = _probability(price, "price")
    with localcontext(decimal_context_v1()) as context:
        raw = context.multiply(context.multiply(context.multiply(quantity, rate), probability), context.subtract(Decimal(1), probability))
    receipt = quantize_decimal_v1(raw, policy=quantization_policy, receipt_id=receipt_id)
    component = "EXPLICIT_MAKER_REBATE" if raw < 0 else "EXPLICIT_TAKER_FEE"
    return QuantizedEconomicAmountV1(raw, receipt.post_value, receipt, component, schedule_binding.binding_ref)


def binary_book_implied_asks_v1(*, snapshot: BinaryBookSnapshotV1) -> BinaryBookTouchesV1:
    """MATH-36: YES ask = payout - NO bid; NO ask = payout - YES bid."""

    if not isinstance(snapshot, BinaryBookSnapshotV1):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed same-snapshot binary book is required")
    yes = snapshot.yes_bids[-1]
    no = snapshot.no_bids[-1]
    with localcontext(decimal_context_v1()) as context:
        return BinaryBookTouchesV1(
            snapshot.snapshot_ref,
            snapshot.sequence_ref,
            snapshot.source_binding_ref,
            snapshot.book_sequence,
            context.subtract(snapshot.payout, no),
            context.subtract(snapshot.payout, yes),
            snapshot.payout,
            snapshot.unit,
            snapshot.basis,
        )


def fill_probability_v1(
    *, artifact: FillProbabilityModelArtifactV1 | None, feature_schema_ref: str, scope_ref: str, horizon_seconds: int
) -> Decimal:
    """MATH-37 consumes a typed externally calibrated artifact or abstains."""

    if artifact is None:
        raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "no default fill-probability model exists")
    if (
        artifact.feature_schema_ref != feature_schema_ref
        or artifact.scope_ref != scope_ref
        or artifact.horizon_seconds != horizon_seconds
    ):
        raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "model artifact is outside declared schema, scope, or horizon")
    return artifact.probability  # type: ignore[return-value]


def expected_partial_fill_quantity_v1(
    *, artifact: FillQuantityDistributionArtifactV1 | None,
) -> Decimal:
    """MATH-38 exact discrete expectation; no implicit full-fill distribution."""

    if artifact is None or not isinstance(artifact, FillQuantityDistributionArtifactV1):
        raise ContractValidationError(ReasonCode.MODEL_ARTIFACT_REQUIRED, "a versioned fill distribution is required")
    fill_quantity_distribution = artifact.fill_quantity_distribution
    maximum = artifact.order_quantity
    tolerance = artifact.normalization_tolerance
    if tolerance >= 1:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "normalization tolerance must be less than one")
    probability_sum = Decimal(0)
    expected = Decimal(0)
    with localcontext(decimal_context_v1()) as context:
        for index, item in enumerate(fill_quantity_distribution):
            if not isinstance(item, tuple) or len(item) != 2:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "distribution rows must be (quantity, probability)")
            quantity = _nonnegative(item[0], f"distribution[{index}].quantity")
            probability = _probability(item[1], f"distribution[{index}].probability")
            if quantity > maximum:
                raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "fill support exceeds order quantity")
            probability_sum = context.add(probability_sum, probability)
            expected = context.add(expected, context.multiply(quantity, probability))
    if probability_sum <= 0 or abs(probability_sum - Decimal(1)) > tolerance:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "fill probabilities exceed the explicitly declared normalization tolerance")
    with localcontext(decimal_context_v1()) as context:
        expected = context.divide(expected, probability_sum)
    if expected < 0 or expected > maximum:
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "expected fill is outside order support")
    return expected


@dataclass(frozen=True, slots=True)
class TrancheCMathSpecificationV1:
    math_spec_id: str
    name: str
    implementation: object
    oracle_ref: str
    golden_vector_ref: str
    no_effects: tuple[str, ...] = (
        "NO_PROVIDER_CONNECTION",
        "NO_PRIVATE_STATE",
        "NO_REPLAY_PAPER",
        "NO_LLM",
        "NO_QPU",
        "NO_MODE_ALLOW",
        "NO_ORDER_RELEASE",
        "NO_CAPITAL_MUTATION",
    )

    def __post_init__(self) -> None:
        if not self.math_spec_id.startswith("MATH-") or not self.name or not callable(self.implementation) or self.oracle_ref != f"ORACLE::{self.math_spec_id}" or self.golden_vector_ref != f"GOLDEN::{self.math_spec_id}":
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "math specification registration is incomplete")


_MATH_ROWS = (
    ("MATH-26", "EXPECTED_VALUE_OF_INFORMATION", expected_value_of_information_v1),
    ("MATH-27", "BINARY_KELLY_FRACTION", binary_kelly_fraction_v1),
    ("MATH-28", "FRACTIONAL_KELLY", fractional_kelly_v1),
    ("MATH-29", "MEAN_VARIANCE_UTILITY", mean_variance_utility_v1),
    ("MATH-30", "CONDITIONAL_VALUE_AT_RISK", conditional_value_at_risk_v1),
    ("MATH-31", "HISTORICAL_EXPECTED_SHORTFALL", empirical_expected_shortfall_v1),
    ("MATH-32", "IMPLEMENTATION_SHORTFALL", implementation_shortfall_v1),
    ("MATH-33", "SPREAD_COST", spread_cost_v1),
    ("MATH-34", "POLYMARKET_GLOBAL_FEE", global_prediction_market_fee_v1),
    ("MATH-35", "POLYMARKET_US_FEE_OR_REBATE", us_prediction_market_fee_or_rebate_v1),
    ("MATH-36", "KALSHI_BINARY_BOOK_TRANSFORM", binary_book_implied_asks_v1),
    ("MATH-37", "FILL_PROBABILITY", fill_probability_v1),
    ("MATH-38", "EXPECTED_PARTIAL_FILL_QUANTITY", expected_partial_fill_quantity_v1),
)

TRANCHE_C_MATH_SPECIFICATIONS: Mapping[str, TrancheCMathSpecificationV1] = MappingProxyType(
    {
        math_id: TrancheCMathSpecificationV1(
            math_spec_id=math_id,
            name=name,
            implementation=implementation,
            oracle_ref=f"ORACLE::{math_id}",
            golden_vector_ref=f"GOLDEN::{math_id}",
        )
        for math_id, name, implementation in _MATH_ROWS
    }
)

if tuple(TRANCHE_C_MATH_SPECIFICATIONS) != tuple(f"MATH-{number}" for number in range(26, 39)):
    raise RuntimeError("Tranche-C math registry must contain MATH-26 through MATH-38 exactly")
