"""Typed input, source, venue, portfolio, and claim-binding contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ContractValidationError, ReasonCode
from .models import ComputationBindingProfileV1, SourceBindingV1, UnitBindingV1


@dataclass(frozen=True, slots=True)
class SourceClaimBindingRuleV1:
    binding_rule_id: str
    rule_class: str
    claim_selector: str
    source_identity_ref: str
    source_state_ref: str
    exact_claims: tuple[str, ...]
    permitted_consumers: tuple[str, ...]
    source_pack_as_primary_allowed: bool = False
    broad_regex_or_alias_matching_allowed: bool = False
    codex_source_selection_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "binding_rule_id",
            "rule_class",
            "claim_selector",
            "source_identity_ref",
            "source_state_ref",
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
            or not self.source_state_ref
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

SOURCE_CLAIM_BINDING_RULES = (SOURCE_RULE_011,)


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
