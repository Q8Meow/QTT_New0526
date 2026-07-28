"""Typed input, source, venue, portfolio, and claim-binding contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json

from .errors import ContractValidationError, ReasonCode, SourcePolicyError
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

_EXACT_RETAINED_SOURCE_STATE_RULE_REFS = (
    ("ST12-SOURCE-RULE::007", "ST10-SOURCE::07"),
    ("ST12-SOURCE-RULE::021", "ST10-SOURCE::21"),
    ("ST12-SOURCE-RULE::022", "ST10-SOURCE::22"),
    ("ST12-SOURCE-RULE::023", "ST10-SOURCE::23"),
    ("ST12-SOURCE-RULE::024", "ST10-SOURCE::24"),
    ("ST12-SOURCE-RULE::025", "ST10-SOURCE::25"),
    ("ST12-SOURCE-RULE::026", "ST10-SOURCE::26"),
    ("ST12-SOURCE-RULE::027", "ST10-SOURCE::27"),
    ("ST12-SOURCE-RULE::028", "ST10-SOURCE::28"),
    ("ST12-SOURCE-RULE::029", "ST10-SOURCE::29"),
)


def get_source_claim_binding_rule(
    binding_rule_id: str,
) -> SourceClaimBindingRuleV1:
    """Resolve one exact retained rule without aliases or caller-selected claims."""

    if not isinstance(binding_rule_id, str) or not binding_rule_id:
        raise ContractValidationError(
            ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
            "source-claim binding identity must be nonempty text",
        )
    certified = tuple(
        rule
        for rule in SOURCE_CLAIM_BINDING_RULES
        if rule.binding_rule_id == binding_rule_id
    )
    if certified:
        if len(certified) != 1:
            raise ContractValidationError(
                ReasonCode.SOURCE_CONFLICT,
                f"duplicate source-claim binding: {binding_rule_id}",
            )
        return certified[0]

    retained_source_state_refs = tuple(
        source_state_id
        for rule_id, source_state_id in _EXACT_RETAINED_SOURCE_STATE_RULE_REFS
        if rule_id == binding_rule_id
    )
    if retained_source_state_refs:
        if len(retained_source_state_refs) != 1:
            raise ContractValidationError(
                ReasonCode.SOURCE_CONFLICT,
                f"duplicate retained source-state rule: {binding_rule_id}",
            )
        from .source_policy import get_source_state

        source = get_source_state(retained_source_state_refs[0])
        return SourceClaimBindingRuleV1(
            binding_rule_id=binding_rule_id,
            rule_class="EXACT_SOURCE_STATE_ATOMIC_FACT_BINDING",
            claim_selector="EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY",
            source_identity_ref=source.stable_source_identity,
            source_state_ref=source.source_state_id,
            exact_claims=source.exact_claims,
            permitted_consumers=(
                "SOURCE_CURRENTIZATION_OWNER",
                "EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION",
            ),
            research_completeness_state="COMPLETE_TERMINAL_EXACT_RULE",
        )

    from .specification import TRANCHE_B_MATH_SPECIFICATIONS

    matches: list[SourceClaimBindingRuleV1] = []
    for specification in TRANCHE_B_MATH_SPECIFICATIONS:
        row = json.loads(specification.original_row_json)
        declared_refs = tuple(row["source_claim_binding_rule_refs"])
        if binding_rule_id not in declared_refs:
            continue
        formal_ref = str(row["formal_derivation_ref"])
        method_ref = (
            f"METHOD::{specification.math_spec_id}::{specification.name}"
        )
        source_refs = tuple(row["source_identity_refs"])
        if method_ref not in source_refs or formal_ref not in source_refs:
            raise ContractValidationError(
                ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
                f"{binding_rule_id} lacks its exact retained method lineage",
            )
        matches.append(
            SourceClaimBindingRuleV1(
                binding_rule_id=binding_rule_id,
                rule_class=(
                    "EXACT_MATHEMATICAL_METHOD_OR_FORMAL_DERIVATION_BINDING"
                ),
                claim_selector="EXACT_MATH_SPEC_ID_ONLY",
                source_identity_ref=method_ref,
                source_state_ref=None,
                exact_claims=(
                    "Complete procedure, domains, assumptions, precision, and "
                    f"oracle obligations for {specification.math_spec_id} "
                    f"{specification.name}.",
                ),
                permitted_consumers=(specification.math_spec_id,),
                research_completeness_state="COMPLETE_TERMINAL_EXACT_RULE",
                formal_derivation_ref=formal_ref,
                math_spec_ref=specification.math_spec_id,
            )
        )
    if len(matches) != 1:
        raise ContractValidationError(
            ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
            f"source-claim rule does not resolve exactly: {binding_rule_id}",
        )
    return matches[0]


@dataclass(frozen=True, slots=True)
class CanonicalSourceBindingReceiptV1:
    receipt_id: str
    component_id: str
    input_field_id: str
    binding_rule_id: str
    source_state_id: str
    stable_source_identity: str
    effective_epoch: str
    rights_state: str
    freshness_policy: str
    exact_claim_refs: tuple[str, ...]
    consumer_ref: str
    terminal_route: str
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "component_id",
            "input_field_id",
            "binding_rule_id",
            "source_state_id",
            "stable_source_identity",
            "effective_epoch",
            "rights_state",
            "freshness_policy",
            "consumer_ref",
            "terminal_route",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"canonical source receipt {name} is required",
                )
        if (
            not isinstance(self.exact_claim_refs, tuple)
            or not self.exact_claim_refs
            or any(not isinstance(value, str) or not value for value in self.exact_claim_refs)
            or len(set(self.exact_claim_refs)) != len(self.exact_claim_refs)
            or type(self.no_authority_flag) is not bool
            or not self.no_authority_flag
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "canonical source receipt claims must be exact and no-authority",
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

    @staticmethod
    def resolve_canonical_source_input(
        *,
        component_id: str,
        input_field_id: str,
        source_state_id: str,
        allowed_binding_rule_ids: tuple[str, ...],
        context_source_epoch_id: str,
        as_of: datetime,
        asserted_source_identity: str | None = None,
        asserted_source_epoch_id: str | None = None,
        asserted_rights_state: str | None = None,
    ) -> tuple[SourceBindingV1, CanonicalSourceBindingReceiptV1]:
        from .source_policy import validate_effective_epoch

        if (
            not isinstance(allowed_binding_rule_ids, tuple)
            or not allowed_binding_rule_ids
            or any(
                not isinstance(value, str) or not value
                for value in allowed_binding_rule_ids
            )
            or len(set(allowed_binding_rule_ids))
            != len(allowed_binding_rule_ids)
        ):
            raise ContractValidationError(
                ReasonCode.SOURCE_BINDING_REQUIRED,
                f"{component_id}.{input_field_id} has no exact source rule",
            )
        try:
            source = validate_effective_epoch(source_state_id, as_of=as_of)
        except SourcePolicyError as exc:
            reason = (
                ReasonCode.SOURCE_BINDING_REQUIRED
                if exc.reason_code is ReasonCode.SOURCE_EPOCH_MISSING
                else exc.reason_code
            )
            raise ContractValidationError(
                reason,
                f"{component_id}.{input_field_id} canonical source lookup failed",
            ) from exc
        matching_rules = tuple(
            rule
            for rule in (
                get_source_claim_binding_rule(rule_id)
                for rule_id in allowed_binding_rule_ids
            )
            if rule.source_state_ref == source.source_state_id
            and rule.source_identity_ref == source.stable_source_identity
        )
        if len(matching_rules) != 1:
            raise ContractValidationError(
                ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
                f"{component_id}.{input_field_id} does not resolve one source rule",
            )
        rule = matching_rules[0]
        consumer_is_exact = component_id in rule.permitted_consumers
        consumer_is_adjudicated = (
            "EXACT_PARAMETER_OR_MATH_CONSUMERS_LISTED_BY_EVIDENCE_ADJUDICATION"
            in rule.permitted_consumers
        )
        if not (consumer_is_exact or consumer_is_adjudicated):
            raise ContractValidationError(
                ReasonCode.SOURCE_CLAIM_BINDING_MISMATCH,
                f"{component_id} is outside {rule.binding_rule_id} consumer scope",
            )
        assertions = (
            (
                asserted_source_identity,
                source.stable_source_identity,
                "source identity",
            ),
            (
                asserted_source_epoch_id,
                source.epoch,
                "source epoch",
            ),
            (
                asserted_rights_state,
                source.rights_and_use_state,
                "rights state",
            ),
        )
        for asserted, canonical, label in assertions:
            if asserted is not None and asserted != canonical:
                raise ContractValidationError(
                    ReasonCode.SOURCE_CONFLICT,
                    f"caller {label} assertion differs from canonical state",
                )
        if (
            source.epoch != context_source_epoch_id
            or source.availability_state != "CURRENT_AVAILABLE"
        ):
            raise ContractValidationError(
                ReasonCode.SOURCE_EPOCH_STALE,
                f"{source.source_state_id} is not current for the computation context",
            )
        binding = SourceBindingV1(
            source_state_id=source.source_state_id,
            stable_source_identity=source.stable_source_identity,
            effective_epoch=source.epoch,
            rights_state=source.rights_and_use_state,
            freshness_policy=source.ttl,
        )
        BindingResolverV1.build(
            binding_id=(
                f"ST12B-CANONICAL-SOURCE::{component_id}::{input_field_id}"
            ),
            version="1.0.0",
            inputs=(),
            sources=(binding,),
        )
        digest = "|".join(
            (
                component_id,
                input_field_id,
                rule.binding_rule_id,
                source.source_state_id,
                source.epoch,
                source.rights_and_use_state,
                source.ttl,
            )
        )
        receipt = CanonicalSourceBindingReceiptV1(
            receipt_id=(
                "SOURCE-BINDING::"
                + sha256(digest.encode("utf-8")).hexdigest()
            ),
            component_id=component_id,
            input_field_id=input_field_id,
            binding_rule_id=rule.binding_rule_id,
            source_state_id=source.source_state_id,
            stable_source_identity=source.stable_source_identity,
            effective_epoch=source.epoch,
            rights_state=source.rights_and_use_state,
            freshness_policy=source.ttl,
            exact_claim_refs=tuple(
                f"{rule.binding_rule_id}::CLAIM::{index:02d}"
                for index, _ in enumerate(rule.exact_claims, start=1)
            ),
            consumer_ref=component_id,
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::CANONICAL_SOURCE_INPUT"
            ),
        )
        return binding, receipt
