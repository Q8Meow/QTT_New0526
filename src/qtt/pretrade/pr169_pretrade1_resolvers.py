from __future__ import annotations

from _thread import RLock
import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
import json
import time
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Iterable, Mapping

from ..stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    KalshiFeeRoundingInputV1,
    KalshiQuadraticTakerBuyYesFillV1,
    _kalshi_bounded_fraction,
    _kalshi_decimal6,
    kalshi_fee_rounding_v1,
    kalshi_quadratic_taker_buy_yes_input_v1,
)
from ..stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    NumericDomainError,
    PointInTimeError,
    ReasonCode,
)
from ..stage1_prediction_markets.qku_computation_control_plane.context import ComputationContextKeyV1, _native_ident
from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    KalshiFeeObservationOwnerV1,
    KalshiObservedFeeCohortV1,
    KalshiQuadraticSeriesFeeCandidateV1,
    KalshiScheduledFeeStateV1,
    PITRightsAdmissionReceiptV1,
    PITSourceCurrentizationReceiptV1,
    decode_kalshi_market_linked_series_fee_candidate_v1,
    decode_kalshi_quadratic_series_fee_candidate_v1,
    resolve_kalshi_scheduled_fee_scenario_v1,
)
if TYPE_CHECKING:
    from ..stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
        ST12GOwnerProjectionResolutionV2,
        ST12GProjectionResolutionV2,
    )


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"


def resolve_selected_venue_semantics_v1(*, binding, profile_id, instrument_id: str,
                                      known_as_of_ns: int, effective_at_ns: int,
                                      required_capabilities: tuple[str, ...]) -> Mapping[str, str]:
    """Resolve submit-disabled semantic rules for a conditional PRETRADE use.

    The returned values are source semantics, never a native execution grant.
    A missing capability blocks only the requesting conditional calculation.
    """
    from ..stage1_prediction_markets.qku_computation_control_plane.context import (
        _native_require, _public_refs_v1, _public_nanoseconds_v1,
    )
    from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import SelectedVenueRealityBindingV1

    _native_require(type(binding) is SelectedVenueRealityBindingV1, "exact venue reality binding required")
    binding.__post_init__()
    _native_ident(instrument_id)
    _public_refs_v1(required_capabilities)
    _public_nanoseconds_v1(known_as_of_ns)
    _public_nanoseconds_v1(effective_at_ns)
    _native_require(binding.profile_id is profile_id and instrument_id in binding.instrument_scope
        and binding.known_at_ns <= known_as_of_ns < binding.expires_at_ns
        and binding.effective_from_ns <= effective_at_ns < binding.expires_at_ns,
        "venue semantics scope/knowledge/effective interval mismatch")
    resolved = {}
    for capability in required_capabilities:
        section, separator, name = capability.partition(".")
        _native_require(separator and section in {"order_semantics", "quantity_price_semantics", "queue_semantics",
            "maintenance_semantics", "settlement_semantics", "emergency_profile"}, "unselected semantic capability")
        values = getattr(binding, section)
        fact = getattr(values, name, None) if section == "emergency_profile" else dict(values.fields).get(name)
        if (fact is None or capability in binding.unavailable_capabilities
                or fact.disposition != "SOURCE_BOUND_SUPPORTED"):
            raise ContractValidationError(ReasonCode.OWNER_DATA_MISSING, "venue capability unavailable: " + capability)
        resolved[capability] = fact.rule_id_or_none
    return MappingProxyType(resolved)


@dataclass(frozen=True, slots=True)
class PublicConditionalFillV1:
    """A proposed YES-oriented fill, without order or execution authority."""

    contracts: Decimal
    price: Decimal
    side: str
    liquidity_role: str
    fill_at_ns: int

    def __post_init__(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require, _public_nanoseconds_v1

        quantity = _kalshi_bounded_fraction(self.contracts, "contracts", nonnegative=True)
        price = _kalshi_bounded_fraction(self.price, "price", nonnegative=True)
        _native_require(quantity > 0 and price <= 1, "conditional fill quantity/price domain")
        _native_require(type(self.side) is str and self.side in {"BUY", "SELL"}
                        and type(self.liquidity_role) is str and self.liquidity_role in {"MAKER", "TAKER"},
                        "conditional fill side/role unavailable")
        _public_nanoseconds_v1(self.fill_at_ns)


def compose_public_fee_cashflows_v1(*, profile_id, market_scope: tuple[str, ...],
                                  epochs, applicability, known_as_of_ns: int,
                                  fills: tuple[PublicConditionalFillV1, ...],
                                  order_ref: str, cap_domain_epoch_refs: tuple[str, ...],
                                  prior_unrounded: Decimal, prior_collected: Decimal,
                                  prior_rounding_overpayment: Decimal,
                                  carry_evidence_refs: tuple[str, ...],
                                  fresh_hypothetical_order: bool,
                                  include_deferred_taker_rebate: bool) -> Mapping[str, object]:
    """Compose one conditional order through existing scalar and cash owners.

    These are evidence-use values. The public packet factory separately proves
    original source/account/carry custody before any native consumer admission.
    """
    from ..stage1_prediction_markets.qku_computation_control_plane.context import (
        _native_require, _native_retail_finite_decimal_text_v1, _public_refs_v1, _public_nanoseconds_v1,
    )
    from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import resolve_public_fee_epoch_v1
    from ..stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import Stage1VenueProfileIdV1
    from ..stage1_prediction_markets.qku_computation_control_plane.economic_math import (
        _public_unrounded_fee_v1, public_fee_amount_v1, public_deferred_taker_rebate_v1,
    )

    _native_ident(order_ref)
    _public_refs_v1(market_scope)
    _public_refs_v1(cap_domain_epoch_refs)
    _public_refs_v1(carry_evidence_refs, allow_empty=True)
    _public_nanoseconds_v1(known_as_of_ns)
    _native_require(type(fresh_hypothetical_order) is bool and type(include_deferred_taker_rebate) is bool
        and type(fills) is tuple and 1 <= len(fills) <= 4096, "conditional order inputs invalid")
    raw = _kalshi_bounded_fraction(prior_unrounded, "prior_unrounded", nonnegative=True)
    collected = _kalshi_bounded_fraction(prior_collected, "prior_collected", nonnegative=True)
    carry = _kalshi_bounded_fraction(prior_rounding_overpayment, "prior_rounding_overpayment", nonnegative=True, microdollars=True)
    if fresh_hypothetical_order:
        _native_require(raw == collected == carry == 0 and not carry_evidence_refs,
                        "fresh hypothetical order cannot discard or relabel prior carry")
    else:
        _native_require(bool(carry_evidence_refs), "existing order requires full prior carry evidence")
    selected, last = [], known_as_of_ns
    for fill in fills:
        _native_require(type(fill) is PublicConditionalFillV1, "exact conditional fill required")
        fill.__post_init__()
        _native_require(fill.fill_at_ns >= last, "conditional fills must be ordered and not precede the as-of")
        last = fill.fill_at_ns
        epoch = resolve_public_fee_epoch_v1(epochs=epochs, profile_id=profile_id, market_scope=market_scope,
            applicability=applicability, known_as_of_ns=known_as_of_ns, effective_at_ns=fill.fill_at_ns,
            liquidity_role=fill.liquidity_role)
        _native_require(epoch.epoch_id in cap_domain_epoch_refs, "fee regime is outside the accepted order/cap domain")
        selected.append(epoch)
    _native_require(set(cap_domain_epoch_refs) <= {epoch.epoch_id for epoch in epochs}, "unknown order/cap epoch")
    principal = sum((Fraction(fill.contracts)*Fraction(fill.price)*(1 if fill.side == "SELL" else -1) for fill in fills), Fraction(0))
    render = _native_retail_finite_decimal_text_v1
    amount = lambda value: Decimal(render(value))
    charges = credits = deferred = Fraction(0)
    if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
        _native_require(applicability.fee_profile_id_or_none is not None
            and applicability.balance_increment_text_or_none is not None,
            "KAL-045 account fee classification/balance grid unavailable")
        _native_require(raw == collected == 0 and not include_deferred_taker_rebate,
                        "Kalshi does not use Retail fee-cap or weekly-rebate semantics")
        compiled = []
        for fill, epoch in zip(fills, selected, strict=True):
            _native_require(epoch.formula_family == "EXPLICIT_ZERO" or (
                epoch.formula_family == "QUADRATIC" and epoch.rounding_rule == "KALSHI_ACCOUNT_GRID"
                and Fraction(dict(epoch.coefficients)["rate"]) == Fraction("0.07" if fill.liquidity_role == "TAKER" else "0.0175")),
                "unsupported Kalshi fee family/role")
            compiled.append(KalshiFeeRoundingInputV1(
                revenue=_kalshi_decimal6(Fraction(fill.contracts)*Fraction(fill.price)*(1 if fill.side == "SELL" else -1), "revenue"),
                model_fee=amount(_public_unrounded_fee_v1(epoch=epoch, contracts=fill.contracts, price=fill.price))))
        terms = compose_kalshi_conditional_cashflows_v1(profile_id=profile_id.value, currency="USD", fills=tuple(compiled),
            balance_increment=Decimal(applicability.balance_increment_text_or_none), prior_rounding_overpayment=prior_rounding_overpayment)
        charges, credits, carry = Fraction(terms.platform_fee_total), Fraction(terms.expected_rebate_total), Fraction(terms.rounding_overpayment_after)
    else:
        _native_require(carry == 0, "non-Kalshi fee rule cannot consume Kalshi cash-grid carry")
        retail = profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
        _native_require(retail or profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT, "unselected fee profile")
        _native_require(retail or raw == collected == 0, "Gemini has no Retail cap carry")
        if include_deferred_taker_rebate:
            _native_require(retail and applicability.taker_tier_or_none is not None,
                            "independent taker rebate qualification unavailable")
        for fill, epoch in zip(fills, selected, strict=True):
            use_cap = retail and fill.liquidity_role == "TAKER"
            result = public_fee_amount_v1(epoch=epoch, contracts=fill.contracts, price=fill.price,
                prior_unrounded=amount(raw) if use_cap else Decimal(0),
                prior_collected=amount(collected) if use_cap else Decimal(0))
            fee = Fraction(result["charged"])
            charges += max(fee, Fraction(0))
            credits += max(-fee, Fraction(0))
            if use_cap:
                raw, collected = Fraction(result["cumulative_unrounded"]), Fraction(result["cumulative_collected"])
                if include_deferred_taker_rebate:
                    deferred += Fraction(public_deferred_taker_rebate_v1(qualifying_collected_fee=amount(fee),
                        proven_tier=applicability.taker_tier_or_none)["amount"])
    return MappingProxyType(dict(entry_trade_cashflow_total=amount(principal), platform_fee_total=amount(charges),
        expected_rebate_total=amount(credits+deferred), rounding_overpayment_after=amount(carry),
        immediate_rebate_total=amount(credits), contingent_deferred_rebate_total=amount(deferred),
        cumulative_unrounded=amount(raw), cumulative_collected=amount(collected),
        selected_epoch_refs=tuple(epoch.epoch_id for epoch in selected), order_ref=order_ref,
        cap_domain_epoch_refs=cap_domain_epoch_refs, carry_evidence_refs=carry_evidence_refs,
        accounting_class="CONDITIONAL_CASHFLOW_NOT_AVAILABLE_BALANCE", no_order_authority=True))


def compose_public_contractual_settlement_cashflow_v1(*, metadata, translations, known_as_of_ns, fills):
    """Resolve one observed binary branch for proposed YES-position changes.

    The other terminal branches, outcome probabilities and private cash posting
    retain their own owners. A resolved branch does not create those inputs.
    """
    from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
    from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import resolve_public_contractual_settlement_v1

    _native_require(type(fills) is tuple and 0 < len(fills) <= 4096, "conditional settlement fills unavailable")
    quantity, previous = Fraction(0), known_as_of_ns
    for fill in fills:
        _native_require(type(fill) is PublicConditionalFillV1, "conditional settlement requires exact proposed fills")
        fill.__post_init__()
        _native_require(fill.fill_at_ns >= previous, "conditional settlement fills precede the decision or are reordered")
        previous = fill.fill_at_ns
        quantity += Fraction(fill.contracts) * (1 if fill.side == "BUY" else -1)
    value = resolve_public_contractual_settlement_v1(metadata=metadata,translations=translations,
        known_as_of_ns=known_as_of_ns,effective_at_ns=known_as_of_ns,position_outcome="YES")
    field = "win_terminal_cashflow_total" if value["resolved_outcome"] == "YES" else "lose_terminal_cashflow_total"
    from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_retail_finite_decimal_text_v1

    return MappingProxyType(dict(field_name=field,
        value=Decimal(_native_retail_finite_decimal_text_v1(quantity*Fraction(value["value_per_contract"]))),
        source_observation_refs=tuple(dict.fromkeys((value["resolution_ref"],*value["original_observation_refs"]))),
        resolution_revision=value["resolution_revision"],accounting_class="CONDITIONAL_CONTRACTUAL_VALUE_NOT_ACCOUNT_CASH",
        no_order_authority=True))


@dataclass(frozen=True, slots=True)
class KalshiConditionalCashflowTermsV1:
    """Conditional principal, charges and refunds; carry is not spendable cash."""

    entry_trade_cashflow_total: Decimal
    platform_fee_total: Decimal
    expected_rebate_total: Decimal
    rounding_overpayment_after: Decimal

    def __post_init__(self) -> None:
        amounts = []
        for name in (
            "entry_trade_cashflow_total", "platform_fee_total",
            "expected_rebate_total", "rounding_overpayment_after",
        ):
            value = getattr(self, name)
            amounts.append(_kalshi_bounded_fraction(
                value, name, nonnegative=name != "entry_trade_cashflow_total",
                microdollars=True,
            ))
            if name != "rounding_overpayment_after":
                digits = value.as_tuple().digits
                significant = len(digits)
                while significant > 1 and digits[significant - 1] == 0:
                    significant -= 1
                if significant > 34:
                    raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, f"{name} exceeds current MATH-06 precision")
        if amounts[1] < amounts[2]:
            raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "conditional credits exceed charges")


def compose_kalshi_conditional_cashflows_v1(
    *, profile_id: str, currency: str, fills: tuple[KalshiFeeRoundingInputV1, ...],
    balance_increment: Decimal, prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Compose one declared ordered hypothetical sequence, without native admission."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    if type(fills) is not tuple or not 1 <= len(fills) <= 4096:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "fills must be a tuple of 1..4096 conditional rows")
    principal = Fraction(0)
    charges = Fraction(0)
    credits = Fraction(0)
    carry = prior_rounding_overpayment
    for row in fills:
        if type(row) is not KalshiFeeRoundingInputV1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact typed conditional fill required")
        rounded = kalshi_fee_rounding_v1(
            revenue=row.revenue, model_fee=row.model_fee,
            balance_increment=balance_increment, prior_rounding_overpayment=carry,
        )
        principal += Fraction(row.revenue)
        charges += Fraction(rounded.trade_fee) + Fraction(rounded.rounding_fee)
        credits += Fraction(rounded.rounding_rebate)
        carry = rounded.rounding_overpayment_after
    return KalshiConditionalCashflowTermsV1(
        entry_trade_cashflow_total=_kalshi_decimal6(principal, "entry_trade_cashflow_total"),
        platform_fee_total=_kalshi_decimal6(charges, "platform_fee_total"),
        expected_rebate_total=_kalshi_decimal6(credits, "expected_rebate_total"),
        rounding_overpayment_after=carry,
    )


def compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
    *, profile_id: str, currency: str,
    fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...],
    fee_multiplier: Decimal, balance_increment: Decimal,
    prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Compile hypothetical quadratic fills and reuse the conditional cash owner."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    if type(fills) is not tuple or not 1 <= len(fills) <= 4096:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "fills must be a tuple of 1..4096 conditional rows")
    if any(type(row) is not KalshiQuadraticTakerBuyYesFillV1 for row in fills):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact quadratic taker BUY-YES fills required")
    compiled = tuple(
        kalshi_quadratic_taker_buy_yes_input_v1(fill=row, fee_multiplier=fee_multiplier)
        for row in fills
    )
    return compose_kalshi_conditional_cashflows_v1(
        profile_id=profile_id, currency=currency, fills=compiled,
        balance_increment=balance_increment,
        prior_rounding_overpayment=prior_rounding_overpayment,
    )


def compose_kalshi_series_quadratic_taker_buy_yes_cashflows_v1(
    *, profile_id: str, currency: str,
    raw_series_response: bytes, expected_series_ticker: str,
    fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...],
    balance_increment: Decimal, prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Consume unadmitted Series fee fields in one hypothetical cashflow sequence."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    candidate = decode_kalshi_quadratic_series_fee_candidate_v1(
        raw_response=raw_series_response, expected_series_ticker=expected_series_ticker,
    )
    return compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
        profile_id=profile_id, currency=currency, fills=fills,
        fee_multiplier=candidate.fee_multiplier, balance_increment=balance_increment,
        prior_rounding_overpayment=prior_rounding_overpayment,
    )


@dataclass(frozen=True, slots=True)
class KalshiScheduledTakerBuyYesFillV1:
    """A proposed conditional fill, without execution or account authority."""

    fill: KalshiQuadraticTakerBuyYesFillV1
    fill_at_utc: datetime

    def __post_init__(self) -> None:
        if type(self.fill) is not KalshiQuadraticTakerBuyYesFillV1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact quadratic fill required")
        if type(self.fill_at_utc) is not datetime or self.fill_at_utc.tzinfo is not UTC:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact UTC scheduled fill required")
        try:
            contracts, price = self.fill.contracts, self.fill.yes_price
        except AttributeError as error:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scheduled fill fields missing") from error
        object.__setattr__(self, "fill", KalshiQuadraticTakerBuyYesFillV1(contracts, price))


def compose_kalshi_scheduled_fee_scenario_cashflows_v1(
    *, profile_id: str, currency: str, context: ComputationContextKeyV1,
    expected_series_ticker: str, expected_event_ticker: str,
    states: tuple[KalshiScheduledFeeStateV1, ...],
    fills: tuple[KalshiScheduledTakerBuyYesFillV1, ...],
    balance_increment: Decimal, prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Compose one offline hypothetical order, never source/account admission."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    if type(fills) is not tuple or not 1 <= len(fills) <= 4096:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scheduled fills must be a tuple of 1..4096 rows")
    grid = _kalshi_bounded_fraction(balance_increment, "balance_increment", nonnegative=True)
    _kalshi_bounded_fraction(prior_rounding_overpayment, "prior_rounding_overpayment", nonnegative=True, microdollars=True)
    if grid not in (Fraction(1, 10_000), Fraction(1, 100)):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "explicit balance increment must be 0.0001 or 0.01 USD")
    local_fills = []
    for row in fills:
        if type(row) is not KalshiScheduledTakerBuyYesFillV1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact scheduled fill required")
        try:
            fill, moment = row.fill, row.fill_at_utc
        except AttributeError as error:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scheduled fill fields missing") from error
        local_fills.append(KalshiScheduledTakerBuyYesFillV1(fill, moment))
    multipliers = resolve_kalshi_scheduled_fee_scenario_v1(
        context=context, expected_series_ticker=expected_series_ticker,
        expected_event_ticker=expected_event_ticker, states=states,
        fill_times=tuple(row.fill_at_utc for row in local_fills),
    )
    compiled = tuple(kalshi_quadratic_taker_buy_yes_input_v1(fill=row.fill, fee_multiplier=multiplier)
                     for row, multiplier in zip(local_fills, multipliers, strict=True))
    return compose_kalshi_conditional_cashflows_v1(
        profile_id=profile_id, currency=currency, fills=compiled,
        balance_increment=balance_increment, prior_rounding_overpayment=prior_rounding_overpayment,
    )


def compose_kalshi_observed_fee_scenario_cashflows_v1(
    *, profile_id: str, currency: str, source_owner: KalshiFeeObservationOwnerV1,
    cohort: KalshiObservedFeeCohortV1, expected_market_ticker: str,
    as_of_monotonic_ns: int, fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...],
    balance_increment: Decimal, prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Consume an original same-process observation for hypothetical cashflows."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    if type(source_owner) is not KalshiFeeObservationOwnerV1:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_OBSERVATION_SCOPE")
    multiplier = source_owner.resolve_scenario_multiplier(
        cohort=cohort, expected_market_ticker=expected_market_ticker,
        as_of_monotonic_ns=as_of_monotonic_ns,
    )
    source_owner._check_inputs_v1(fills, balance_increment, prior_rounding_overpayment)
    result = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
        profile_id=profile_id, currency=currency, fills=fills,
        fee_multiplier=multiplier, balance_increment=balance_increment,
        prior_rounding_overpayment=prior_rounding_overpayment,
    )
    with source_owner._publication_fence_v1(
        cohort=cohort, expected_market_ticker=expected_market_ticker, as_of_monotonic_ns=as_of_monotonic_ns,
        fills=fills, balance_increment=balance_increment, prior_rounding_overpayment=prior_rounding_overpayment,
        route="DIRECT" if source_owner._session_origin is None else "SESSION_INTERNAL",
    ):
        return result


def _kalshi_scenario_inputs_v1(fills, balance_increment, prior_rounding_overpayment):
    if (type(fills) is not tuple or not 1 <= len(fills) <= 4096
            or any(type(row) is not KalshiQuadraticTakerBuyYesFillV1 for row in fills)):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_RESULT")
    for row in fills:
        try:
            values = {field.name: getattr(row, field.name)
                      for field in dataclasses.fields(KalshiQuadraticTakerBuyYesFillV1)}
        except AttributeError:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_RESULT") from None
        KalshiQuadraticTakerBuyYesFillV1(**values)
    _kalshi_bounded_fraction(balance_increment, "balance_increment", nonnegative=True, microdollars=True)
    _kalshi_bounded_fraction(prior_rounding_overpayment, "prior_rounding_overpayment",
                            nonnegative=True, microdollars=True)
    if balance_increment not in (Decimal("0.0001"), Decimal("0.01")):
        raise NumericDomainError(ReasonCode.OUT_OF_DOMAIN, "KALSHI_SCENARIO_SESSION_RESULT")


@dataclass(frozen=True, slots=True)
class KalshiObservedFeeScenarioResultV1:
    """Constructible hypothetical data, with no native admission or standing authority."""

    cashflows: KalshiConditionalCashflowTermsV1
    market_ticker: str
    event_ticker: str
    series_ticker: str
    fee_basis: str
    fee_multiplier: Decimal
    source_receipt_ref: str
    rights_receipt_ref: str
    account_scope: str
    operating_authorization_ref: str
    process_epoch_id: str
    monotonic_clock_id: str
    available_wall_ns: int
    available_monotonic_ns: int
    evaluated_monotonic_ns: int
    fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...]
    balance_increment: Decimal
    prior_rounding_overpayment: Decimal
    evidence_class: str = dataclasses.field(default="OBSERVED_FEE_HYPOTHETICAL_SCENARIO", init=False)

    def __post_init__(self) -> None:
        if (type(self.cashflows) is not KalshiConditionalCashflowTermsV1
                or type(self.fee_basis) is not str
                or self.fee_basis not in ("OBSERVED_SERIES_BASE", "OBSERVED_EVENT_OVERRIDE")):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_RESULT")
        try:
            amounts = {field.name: getattr(self.cashflows, field.name)
                       for field in dataclasses.fields(KalshiConditionalCashflowTermsV1)}
        except AttributeError:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_RESULT") from None
        KalshiConditionalCashflowTermsV1(**amounts)
        for value in (self.market_ticker, self.event_ticker, self.series_ticker,
                      self.source_receipt_ref, self.rights_receipt_ref, self.account_scope,
                      self.operating_authorization_ref, self.process_epoch_id, self.monotonic_clock_id):
            _native_ident(value)
        KalshiQuadraticSeriesFeeCandidateV1(self.series_ticker, self.fee_multiplier)
        if (any(type(value) is not int or not 0 <= value <= 2**63 - 1
                for value in (self.available_wall_ns, self.available_monotonic_ns, self.evaluated_monotonic_ns))
                or self.available_monotonic_ns > self.evaluated_monotonic_ns):
            raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "KALSHI_SCENARIO_SESSION_RESULT")
        _kalshi_scenario_inputs_v1(self.fills, self.balance_increment, self.prior_rounding_overpayment)


class KalshiFeeScenarioSessionV1:
    """One dormant producer-to-consumer call; upstream admission remains external."""

    __slots__ = ("__origin", "__lock", "__owner", "__context", "__state")

    def __init__(self, *, source_receipt: PITSourceCurrentizationReceiptV1,
                 rights_receipt: PITRightsAdmissionReceiptV1, account_scope: str,
                 internal_use_class: str, permitted_retention_class: str,
                 expected_market_ticker: str, process_epoch_id: str,
                 monotonic_clock_id: str, operating_authorization_ref: str,
                 authorization_expires_at_utc: datetime, deadline_monotonic_ns: int,
                 source_use_binding=None) -> None:
        if type(self) is not KalshiFeeScenarioSessionV1 or hasattr(self, "_KalshiFeeScenarioSessionV1__origin"):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_STATE")
        self.__origin = self
        self.__lock = RLock()
        self.__state = "FAILED"
        self.__owner = KalshiFeeObservationOwnerV1(
            source_receipt=source_receipt, rights_receipt=rights_receipt, account_scope=account_scope,
            internal_use_class=internal_use_class, permitted_retention_class=permitted_retention_class,
            expected_market_ticker=expected_market_ticker, process_epoch_id=process_epoch_id,
            monotonic_clock_id=monotonic_clock_id, operating_authorization_ref=operating_authorization_ref,
            authorization_expires_at_utc=authorization_expires_at_utc, deadline_monotonic_ns=deadline_monotonic_ns,
            source_use_binding=source_use_binding,
        )
        self.__owner._bind_session_v1(self)
        self.__context = (source_receipt.receipt_id, rights_receipt.receipt_id, account_scope,
                          expected_market_ticker, operating_authorization_ref, process_epoch_id, monotonic_clock_id)
        self.__state = "NEW"

    def __require_instance(self) -> None:
        if (type(self) is not KalshiFeeScenarioSessionV1 or self.__origin is not self
                or type(getattr(self, "_KalshiFeeScenarioSessionV1__owner", None)) is not KalshiFeeObservationOwnerV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_ASSOCIATION")

    def evaluate(self, *, fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...],
                 balance_increment: Decimal, prior_rounding_overpayment: Decimal) -> KalshiObservedFeeScenarioResultV1:
        lock = getattr(self, "_KalshiFeeScenarioSessionV1__lock", None)
        if lock is None:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_ASSOCIATION")
        with lock:
            self.__require_instance()
            if self.__state != "NEW":
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_STATE")
        _kalshi_scenario_inputs_v1(fills, balance_increment, prior_rounding_overpayment)
        with lock:
            self.__require_instance()
            if self.__state != "NEW":
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_STATE")
            self.__owner._check_inputs_v1(fills, balance_increment, prior_rounding_overpayment)
            owner, context = self.__owner, self.__context
            self.__state = "RUNNING"
        cohort = None
        try:
            cohort = owner.capture()
            evaluated = time.monotonic_ns()
            cashflows = compose_kalshi_observed_fee_scenario_cashflows_v1(
                profile_id="KALSHI_US_DCM_DIRECT", currency="USD", source_owner=owner, cohort=cohort,
                expected_market_ticker=context[3], as_of_monotonic_ns=evaluated, fills=fills,
                balance_increment=balance_increment, prior_rounding_overpayment=prior_rounding_overpayment,
            )
            result = KalshiObservedFeeScenarioResultV1(
                cashflows=cashflows, market_ticker=cohort.market_ticker, event_ticker=cohort.event_ticker,
                series_ticker=cohort.series_ticker, fee_basis=cohort.fee_basis, fee_multiplier=cohort.fee_multiplier,
                source_receipt_ref=context[0], rights_receipt_ref=context[1], account_scope=context[2],
                operating_authorization_ref=context[4], process_epoch_id=context[5], monotonic_clock_id=context[6],
                available_wall_ns=cohort.available_wall_ns, available_monotonic_ns=cohort.available_monotonic_ns,
                evaluated_monotonic_ns=evaluated, fills=fills, balance_increment=balance_increment,
                prior_rounding_overpayment=prior_rounding_overpayment,
            )
            with lock:
                self.__require_instance()
                if self.__state != "RUNNING":
                    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_STATE")
                if self.__owner is not owner or self.__context is not context:
                    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_ASSOCIATION")
                if owner.resolve_scenario_multiplier(cohort=cohort, expected_market_ticker=context[3],
                                                     as_of_monotonic_ns=evaluated) != result.fee_multiplier:
                    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_RESULT")
                with owner._publication_fence_v1(cohort=cohort, expected_market_ticker=context[3],
                    as_of_monotonic_ns=evaluated, fills=fills, balance_increment=balance_increment,
                    prior_rounding_overpayment=prior_rounding_overpayment, route="SESSION_FINAL"):
                    try:
                        owner.revoke()
                    except BaseException:
                        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_CLEANUP_FAILED") from None
                    self.__state = "CONSUMED"
                    return result
        except BaseException as error:
            with lock:
                if self.__state != "REVOKED":
                    self.__state = "FAILED"
                try:
                    owner.revoke()
                except BaseException:
                    BaseException.add_note(error, "KALSHI_SCENARIO_SESSION_CLEANUP_FAILED")
            raise
        finally:
            cohort = None

    def revoke(self) -> None:
        lock = getattr(self, "_KalshiFeeScenarioSessionV1__lock", None)
        if lock is None:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_ASSOCIATION")
        with lock:
            self.__require_instance()
            if self.__state in ("NEW", "RUNNING"):
                self.__state = "REVOKED"
                try:
                    self.__owner.revoke()
                except BaseException:
                    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "KALSHI_SCENARIO_SESSION_CLEANUP_FAILED") from None


def compose_kalshi_market_linked_series_base_cashflows_v1(
    *, profile_id: str, currency: str,
    raw_market_response: bytes, raw_event_response: bytes,
    raw_series_response: bytes, expected_market_ticker: str,
    fills: tuple[KalshiQuadraticTakerBuyYesFillV1, ...],
    balance_increment: Decimal, prior_rounding_overpayment: Decimal,
) -> KalshiConditionalCashflowTermsV1:
    """Compose a hypothetical Series-base scenario after joining supplied identities."""
    if type(profile_id) is not str or profile_id != "KALSHI_US_DCM_DIRECT":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact Kalshi profile required")
    if type(currency) is not str or currency != "USD":
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exact USD currency required")
    candidate = decode_kalshi_market_linked_series_fee_candidate_v1(
        raw_market_response=raw_market_response, raw_event_response=raw_event_response,
        raw_series_response=raw_series_response, expected_market_ticker=expected_market_ticker,
    )
    return compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
        profile_id=profile_id, currency=currency, fills=fills,
        fee_multiplier=candidate.fee_multiplier, balance_increment=balance_increment,
        prior_rounding_overpayment=prior_rounding_overpayment,
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_jsonl(path: Path) -> tuple[dict, ...]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return tuple(rows)


@dataclass(frozen=True)
class PreTradeRegistryView:
    rows: tuple[dict, ...]

    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(str(row["candidate_id"]) for row in self.rows)

    def by_candidate_id(self, candidate_id: str) -> dict:
        for row in self.rows:
            if row.get("candidate_id") == candidate_id:
                return dict(row)
        raise KeyError(candidate_id)

    def decision_packets(self) -> tuple[dict, ...]:
        return tuple(
            {
                "candidate_id": row["candidate_id"],
                "pretrade_decision_candidate_id": row["pretrade_decision_candidate_id"],
                "pretrade_decision_state": row["pretrade_decision_state"],
                "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
                "owner_review_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                "agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
                "edge_alpha_capture_map_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
                "submit_authority_created": row["submit_authority_created"],
                "order_authority_created": row["order_authority_created"],
                "profit_claim_created": row["profit_claim_created"],
            }
            for row in self.rows
        )

    def provider_pending_packets(self) -> tuple[dict, ...]:
        return tuple(
            packet
            for packet in self.decision_packets()
            if packet["pretrade_decision_state"] == "PRETRADE_PASS_PROVIDER_PENDING"
        )

    def downstream_consumers(self) -> tuple[str, ...]:
        consumers: set[str] = set()
        for row in self.rows:
            consumers.update(str(ref) for ref in row.get("downstream_consumer_refs", ()))
        return tuple(sorted(consumers))

    def authority_false_fields(self) -> tuple[str, ...]:
        fields: set[str] = set()
        for row in self.rows:
            for key, value in row.items():
                if key.endswith("_created") and value is False:
                    fields.add(key)
        return tuple(sorted(fields))


def load_registry(
    *,
    repo_root: str | Path | None = None,
    rows: Iterable[dict] | None = None,
) -> PreTradeRegistryView:
    if rows is not None:
        return PreTradeRegistryView(tuple(dict(row) for row in rows))
    root = Path(repo_root) if repo_root is not None else _repo_root()
    registry_path = root / REGISTRY_REF
    return PreTradeRegistryView(_read_jsonl(registry_path))


def resolve_st12g_projection_v2(
    resolution: "ST12GProjectionResolutionV2",
) -> "ST12GOwnerProjectionResolutionV2":
    """Select PRETRADE1 without I/O, core copying, or recomputation."""

    from ..stage1_prediction_markets.qku_computation_control_plane import (
        existing_owner_projection as st12g,
    )

    if type(resolution) is not st12g.ST12GProjectionResolutionV2:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "PRETRADE1 requires the exact central ST12-G resolution",
        )
    if (
        resolution.resolution_state
        is st12g.ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY
    ):
        bundle = resolution.projection_bundle
        if type(bundle) is not st12g.ST12GProjectionBundleV2 or type(
            bundle.pretrade
        ) is not st12g.ST12GPretradeEvidenceProjectionV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "PRETRADE1 projection is missing from the central bundle",
            )
        payload = bundle.pretrade
    else:
        payload = resolution.absence
        if type(payload) is not st12g.ST12GProjectionAbsenceV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "PRETRADE1 noncurrent resolution must preserve central absence",
            )
    return st12g.ST12GOwnerProjectionResolutionV2(
        consumer_id="PRETRADE1",
        source_request_id=resolution.request_id,
        resolution_state=resolution.resolution_state,
        payload=payload,
    )
