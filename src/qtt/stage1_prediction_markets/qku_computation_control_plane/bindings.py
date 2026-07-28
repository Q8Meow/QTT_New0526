"""Typed input, source, venue, portfolio, and claim-binding contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json

from .errors import ContractValidationError, ReasonCode
from .models import ComputationBindingProfileV1, SourceBindingV1, UnitBindingV1


@dataclass(frozen=True, slots=True)
class SourceClaimBindingRuleV1:
    binding_rule_id: str
    rule_class: str
    claim_selector: str
    source_identity_ref: str
    source_state_ref: str | None
    exact_claims: tuple[str, ...]
    permitted_consumers: tuple[str, ...]
    source_pack_as_primary_allowed: bool = False
    broad_regex_or_alias_matching_allowed: bool = False
    codex_source_selection_allowed: bool = False
    research_completeness_state: str = ""
    formal_derivation_ref: str | None = None
    math_spec_ref: str | None = None
    original_row_json: str = ""

    def __post_init__(self) -> None:
        for name in (
            "binding_rule_id",
            "rule_class",
            "claim_selector",
            "source_identity_ref",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"source-claim {name} is required",
                )
        for name in ("exact_claims", "permitted_consumers"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(set(values)) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must contain unique exact strings",
                )
        for name in (
            "source_pack_as_primary_allowed",
            "broad_regex_or_alias_matching_allowed",
            "codex_source_selection_allowed",
        ):
            if type(getattr(self, name)) is not bool:
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a boolean",
                )
        if (
            not self.binding_rule_id
            or not self.source_identity_ref
            or not self.exact_claims
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "source-claim binding rule is incomplete",
            )
        if (
            self.source_pack_as_primary_allowed
            or self.broad_regex_or_alias_matching_allowed
            or self.codex_source_selection_allowed
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "source selection, broad matching, and source-pack primacy are forbidden",
            )
        source_binding = (
            self.rule_class == "EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING"
        )
        method_binding = (
            self.rule_class
            == "EXACT_MATHEMATICAL_METHOD_OR_FORMAL_DERIVATION_BINDING"
        )
        if source_binding == method_binding:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "source-claim rule class must be exactly source-state or method",
            )
        if source_binding and (
            not isinstance(self.source_state_ref, str)
            or not self.source_state_ref
            or self.formal_derivation_ref is not None
            or self.math_spec_ref is not None
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "source-state claim requires one exact source-state reference",
            )
        if method_binding and (
            self.source_state_ref is not None
            or not isinstance(self.formal_derivation_ref, str)
            or not self.formal_derivation_ref
            or not isinstance(self.math_spec_ref, str)
            or not self.math_spec_ref
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "method claim requires exact math and formal-derivation references",
            )
        if self.research_completeness_state and (
            self.research_completeness_state != "COMPLETE_TERMINAL_EXACT_RULE"
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "source-claim rule is not terminal",
            )
        if self.original_row_json:
            row = json.loads(self.original_row_json)
            if (
                not isinstance(row, dict)
                or row.get("binding_rule_id") != self.binding_rule_id
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "source-claim original-row lineage is malformed",
                )

    def permits_exact_claim(self, claim: str, consumer: str) -> bool:
        if not isinstance(claim, str) or not isinstance(consumer, str):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "claim and consumer selectors must be text",
            )
        return claim in self.exact_claims and consumer in self.permitted_consumers


SOURCE_RULE_011 = SourceClaimBindingRuleV1(
    binding_rule_id="ST12-SOURCE-RULE::011",
    rule_class="EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING",
    claim_selector="EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY",
    source_identity_ref=(
        "VENUE::ST10-SOURCE_11::POLYMARKET_GLOBAL_CURRENT_RATE_LIMITS"
    ),
    source_state_ref="ST10-SOURCE::11",
    exact_claims=(
        "DELETE /orders is limited to 2,000 requests per 10 seconds and "
        "15,000 requests per 10 minutes on the current direct official page.",
        "Request rate and per-request cardinality are different controls and must "
        "not be conflated.",
        "Rate-limit behavior is endpoint- and epoch-specific; a later typed source "
        "refresh may supersede these values.",
    ),
    permitted_consumers=(
        "SOURCE_CURRENTIZATION_OWNER",
        "EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION",
    ),
)

TRANCHE_A_SOURCE_CLAIM_BINDING_RULES = (SOURCE_RULE_011,)

_TRANCHE_B_SOURCE_CLAIM_BINDING_RULES_JSON = r'''
[{"binding_rule_id":"ST12-SOURCE-RULE::001","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["GET /historical/cutoff is the dynamic routing authority for markets/candlesticks, trades/fills, completed orders, and archived settled positions.","Records older than the applicable cutoff must use historical endpoints; the target live window is approximately three months and advances.","Historical public trades are a trade tape and do not establish historical L2, order identity, or native queue priority.","GET /historical/positions serves user-scoped settled positions older than market_positions_last_updated_ts; positions move per whole event, while unsettled positions remain on the live endpoint."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_01::KALSHI_HISTORICAL_DATA","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::01"},{"binding_rule_id":"ST12-SOURCE-RULE::002","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["GET /markets/{ticker}/orderbook is public and returns current aggregated YES and NO bid ladders.","Prices and quantities are fixed-point decimal strings; complementary asks are reconstructed from opposite-outcome bids.","The current aggregate book does not establish historical L2 or native order identity."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::02"},{"binding_rule_id":"ST12-SOURCE-RULE::003","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["The channel requires authentication, emits an orderbook_snapshot first, then incremental orderbook_delta messages.","Messages carry subscription and sequence fields plus timestamps on deltas.","The stream is aggregated by price level and does not expose full native order identity.","Subaccount-restricted session and private-channel scoping is versioned through the July 23 changelog and must be joined as a separate effective source binding rather than inferred from this channel page."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_03::KALSHI_WEBSOCKET_ORDERBOOK_UPDATES","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::03"},{"binding_rule_id":"ST12-SOURCE-RULE::004","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["Direct member balance precision is 0.0001 USD; non-direct member balance precision is 0.01 USD.","Trade fee is rounded up to the nearest 0.0001 USD; balance change is floored to target precision.","A per-order accumulator issues whole-cent rebates when accumulated rounding overpayment exceeds 0.01 USD."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_04::KALSHI_FEE_ROUNDING","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::04"},{"binding_rule_id":"ST12-SOURCE-RULE::010","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["Fees are determined per market at match time; market metadata is primary at runtime.","fee = contracts * fee_rate * price * (1-price).","Makers are not charged a fee; only takers pay the fee.","Current category matrix is exact as recorded in the Step 12 addendum, including Sports 0.05 and 15 percent maker-rebate share.","Fees are rounded to five decimals; the smallest nonzero fee is 0.00001."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_10::POLYMARKET_GLOBAL_FEES_CURRENT_DIRECT_DOCUMENTATION","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::10"},{"binding_rule_id":"ST12-SOURCE-RULE::011","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["DELETE /orders is limited to 2,000 requests per 10 seconds and 15,000 requests per 10 minutes on the current direct official page.","Request rate and per-request cardinality are different controls and must not be conflated.","Rate-limit behavior is endpoint- and epoch-specific; a later typed source refresh may supersede these values."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_11::POLYMARKET_GLOBAL_CURRENT_RATE_LIMITS","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::11"},{"binding_rule_id":"ST12-SOURCE-RULE::012","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY","codex_source_selection_allowed":false,"exact_claims":["Exchange-wide fee schedule is effective from 12 AM ET on July 1, 2026.","Fee or rebate amount equals theta times contracts times price times one minus price.","Taker theta is 0.06 and maker rebate theta is -0.0125.","Taker volume rebates use prior-calendar-month notional tiers of 10, 25, and 50 percent.","Polymarket US semantics are not generalized to Polymarket Global."],"permitted_consumers":["SOURCE_CURRENTIZATION_OWNER","EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING","source_identity_ref":"VENUE::ST10-SOURCE_12::POLYMARKET_US_FEE_SCHEDULE_EFFECTIVE_JULY_1_2026","source_pack_as_primary_allowed":false,"source_state_ref":"ST10-SOURCE::12"},{"binding_rule_id":"ST12-SOURCE-RULE::058","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_MATH_SPEC_ID_ONLY","codex_source_selection_allowed":false,"exact_claims":["Complete procedure, domains, assumptions, precision, and oracle obligations for MATH-20 PURGED_KFOLD_WITH_EMBARGO."],"formal_derivation_ref":"FORMAL_DERIVATION::MATH-20","math_spec_ref":"MATH-20","permitted_consumers":["MATH-20"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_MATHEMATICAL_METHOD_OR_FORMAL_DERIVATION_BINDING","source_identity_ref":"METHOD::MATH-20::PURGED_KFOLD_WITH_EMBARGO","source_pack_as_primary_allowed":false},{"binding_rule_id":"ST12-SOURCE-RULE::059","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_MATH_SPEC_ID_ONLY","codex_source_selection_allowed":false,"exact_claims":["Complete procedure, domains, assumptions, precision, and oracle obligations for MATH-21 COMBINATORIAL_PURGED_CROSS_VALIDATION."],"formal_derivation_ref":"FORMAL_DERIVATION::MATH-21","math_spec_ref":"MATH-21","permitted_consumers":["MATH-21"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_MATHEMATICAL_METHOD_OR_FORMAL_DERIVATION_BINDING","source_identity_ref":"METHOD::MATH-21::COMBINATORIAL_PURGED_CROSS_VALIDATION","source_pack_as_primary_allowed":false},{"binding_rule_id":"ST12-SOURCE-RULE::064","broad_regex_or_alias_matching_allowed":false,"claim_selector":"EXACT_MATH_SPEC_ID_ONLY","codex_source_selection_allowed":false,"exact_claims":["Complete procedure, domains, assumptions, precision, and oracle obligations for MATH-26 EXPECTED_VALUE_OF_INFORMATION."],"formal_derivation_ref":"FORMAL_DERIVATION::MATH-26","math_spec_ref":"MATH-26","permitted_consumers":["MATH-26"],"research_completeness_state":"COMPLETE_TERMINAL_EXACT_RULE","rule_class":"EXACT_MATHEMATICAL_METHOD_OR_FORMAL_DERIVATION_BINDING","source_identity_ref":"METHOD::MATH-26::EXPECTED_VALUE_OF_INFORMATION","source_pack_as_primary_allowed":false}]
'''


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _source_rule(row: object) -> SourceClaimBindingRuleV1:
    if not isinstance(row, dict):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "source-claim materialization row must be an object",
        )
    return SourceClaimBindingRuleV1(
        binding_rule_id=str(row["binding_rule_id"]),
        rule_class=str(row["rule_class"]),
        claim_selector=str(row["claim_selector"]),
        source_identity_ref=str(row["source_identity_ref"]),
        source_state_ref=(
            str(row["source_state_ref"]) if row.get("source_state_ref") else None
        ),
        exact_claims=tuple(str(value) for value in row["exact_claims"]),
        permitted_consumers=tuple(
            str(value) for value in row["permitted_consumers"]
        ),
        source_pack_as_primary_allowed=row[
            "source_pack_as_primary_allowed"
        ],
        broad_regex_or_alias_matching_allowed=row[
            "broad_regex_or_alias_matching_allowed"
        ],
        codex_source_selection_allowed=row["codex_source_selection_allowed"],
        research_completeness_state=str(row["research_completeness_state"]),
        formal_derivation_ref=(
            str(row["formal_derivation_ref"])
            if row.get("formal_derivation_ref")
            else None
        ),
        math_spec_ref=(
            str(row["math_spec_ref"]) if row.get("math_spec_ref") else None
        ),
        original_row_json=_canonical_json(row),
    )


_TRANCHE_B_SOURCE_ROWS = json.loads(
    _TRANCHE_B_SOURCE_CLAIM_BINDING_RULES_JSON
)
if (
    not isinstance(_TRANCHE_B_SOURCE_ROWS, list)
    or len(_TRANCHE_B_SOURCE_ROWS) != 10
    or any(not isinstance(row, dict) for row in _TRANCHE_B_SOURCE_ROWS)
    or len(
        {
            str(row["binding_rule_id"])
            for row in _TRANCHE_B_SOURCE_ROWS
        }
    )
    != 10
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "Tranche-B source roster must contain ten unique exact rules",
    )
_CERTIFIED_TRANCHE_B_SOURCE_RULES = tuple(
    _source_rule(row) for row in _TRANCHE_B_SOURCE_ROWS
)
_CERTIFIED_RULE_011 = next(
    rule
    for rule in _CERTIFIED_TRANCHE_B_SOURCE_RULES
    if rule.binding_rule_id == SOURCE_RULE_011.binding_rule_id
)
if (
    _CERTIFIED_RULE_011.rule_class != SOURCE_RULE_011.rule_class
    or _CERTIFIED_RULE_011.claim_selector != SOURCE_RULE_011.claim_selector
    or _CERTIFIED_RULE_011.source_identity_ref
    != SOURCE_RULE_011.source_identity_ref
    or _CERTIFIED_RULE_011.source_state_ref != SOURCE_RULE_011.source_state_ref
    or _CERTIFIED_RULE_011.exact_claims != SOURCE_RULE_011.exact_claims
    or _CERTIFIED_RULE_011.permitted_consumers
    != SOURCE_RULE_011.permitted_consumers
):
    raise ContractValidationError(
        ReasonCode.SOURCE_CONFLICT,
        "Tranche-B reused rule 011 differs from the preserved A owner",
    )
TRANCHE_B_SOURCE_CLAIM_BINDING_RULES = tuple(
    SOURCE_RULE_011 if rule.binding_rule_id == SOURCE_RULE_011.binding_rule_id else rule
    for rule in _CERTIFIED_TRANCHE_B_SOURCE_RULES
)
SOURCE_CLAIM_BINDING_RULES = TRANCHE_A_SOURCE_CLAIM_BINDING_RULES + tuple(
    rule
    for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
    if rule.binding_rule_id != SOURCE_RULE_011.binding_rule_id
)
if (
    len(TRANCHE_B_SOURCE_CLAIM_BINDING_RULES) != 10
    or len(SOURCE_CLAIM_BINDING_RULES) != 10
    or len({rule.binding_rule_id for rule in SOURCE_CLAIM_BINDING_RULES}) != 10
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "A/B source rules must preserve A and form a ten-identity union",
    )


class BindingResolverV1:
    """Build immutable profiles without connecting to a provider or private state."""

    @staticmethod
    def build(
        *,
        binding_id: str,
        version: str,
        inputs: tuple[UnitBindingV1, ...],
        sources: tuple[SourceBindingV1, ...],
        venue_scope: tuple[str, ...] = (),
    ) -> ComputationBindingProfileV1:
        if not isinstance(inputs, tuple) or any(
            not isinstance(item, UnitBindingV1) for item in inputs
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "inputs must be a tuple of UnitBindingV1 values",
            )
        if not isinstance(sources, tuple) or any(
            not isinstance(item, SourceBindingV1) for item in sources
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "sources must be a tuple of SourceBindingV1 values",
            )
        if not isinstance(venue_scope, tuple) or any(
            not isinstance(venue, str) or not venue for venue in venue_scope
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "venue_scope must be a tuple of nonempty strings",
            )
        if len({item.field_name for item in inputs}) != len(inputs):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "duplicate input binding"
            )
        if len({item.source_state_id for item in sources}) != len(sources):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "duplicate source-state binding"
            )
        from .source_policy import get_source_state

        for source in sources:
            source_state = get_source_state(source.source_state_id)
            if (
                source.stable_source_identity
                != source_state.stable_source_identity
                or source.effective_epoch != source_state.epoch
                or source.rights_state != source_state.rights_and_use_state
                or source.freshness_policy != source_state.ttl
            ):
                raise ContractValidationError(
                    ReasonCode.SOURCE_CONFLICT,
                    f"source binding lineage differs from {source.source_state_id}",
                )
        if len(set(venue_scope)) != len(venue_scope):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "duplicate venue scope"
            )
        return ComputationBindingProfileV1(
            binding_id=binding_id,
            version=version,
            input_bindings=inputs,
            source_bindings=sources,
            venue_scope=tuple(sorted(set(venue_scope))),
            portfolio_scope="NO_PRIVATE_STATE",
        )
