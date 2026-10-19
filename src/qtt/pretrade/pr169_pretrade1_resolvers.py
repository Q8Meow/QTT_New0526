from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

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
    ReasonCode,
)
from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    decode_kalshi_quadratic_series_fee_candidate_v1,
)
if TYPE_CHECKING:
    from ..stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
        ST12GOwnerProjectionResolutionV2,
        ST12GProjectionResolutionV2,
    )


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"


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
