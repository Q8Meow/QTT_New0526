"""Deterministic validation of pre-existing advisory annotations; no inference."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, Protocol

from .context import exact_decimal, parse_utc
from .errors import ContractValidationError, ReasonCode
from .models import NO_EFFECTS_V1, NoEffectFlagsV1
from .serialization import deterministic_json


class LLMAdvisoryTaskV1(StrEnum):
    SUMMARIZE_EVIDENCE = "SUMMARIZE_EVIDENCE"
    IDENTIFY_INCONSISTENCIES = "IDENTIFY_INCONSISTENCIES"
    ANNOTATE_RESEARCH = "ANNOTATE_RESEARCH"
    CRITIQUE_ASSUMPTIONS = "CRITIQUE_ASSUMPTIONS"
    EXPLAIN_DISAGREEMENT = "EXPLAIN_DISAGREEMENT"
    PROPOSE_OWNER_REVIEW_QUESTIONS = "PROPOSE_OWNER_REVIEW_QUESTIONS"


_INSTRUCTION_MARKERS = (
    "ignore previous",
    "ignore all prior",
    "system prompt",
    "developer message",
    "follow these instructions",
    "tool escalation",
    "call a tool",
    "execute command",
    "reveal secret",
    "<script",
)
_AUTHORITY_MARKERS = (
    "change the threshold",
    "set the threshold",
    "rewrite the number",
    "select the winner",
    "winner is",
    "change the parameter",
    "set the parameter",
    "change the formula",
    "set the formula",
    "accept this source",
    "activate mode",
    "set the mode",
    "grant allow",
    "release order",
    "submit order",
    "place order",
    "allocate capital",
    "change capital",
    "mutate capital",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractValidationError(
            ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
            f"{name} must be canonical text",
        )
    return value


def _refs(value: object, name: str, *, required: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
        or (required and not value)
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
            f"{name} must be a unique reference tuple",
        )
    return value


@dataclass(frozen=True, slots=True)
class AnnotationCitationV1:
    citation_id: str
    evidence_ref: str
    claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.citation_id, "citation_id")
        _text(self.evidence_ref, "evidence_ref")
        _refs(self.claim_ids, "claim_ids", required=True)

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "AnnotationCitationV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "citation payload must be a mapping")
        payload = dict(value)
        payload["claim_ids"] = tuple(payload["claim_ids"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class AnnotationClaimV1:
    claim_id: str
    claim_text: str
    citation_ids: tuple[str, ...]
    numeric_fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.claim_id, "claim_id")
        _text(self.claim_text, "claim_text")
        _refs(self.citation_ids, "citation_ids", required=True)
        _refs(self.numeric_fact_ids, "numeric_fact_ids")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "AnnotationClaimV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "claim payload must be a mapping")
        payload = dict(value)
        payload["citation_ids"] = tuple(payload["citation_ids"])
        payload["numeric_fact_ids"] = tuple(payload["numeric_fact_ids"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class QuotedNumericFactV1:
    numeric_fact_id: str
    evidence_ref: str
    unit_and_basis: str
    quoted_value: Decimal
    claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.numeric_fact_id, "numeric_fact_id")
        _text(self.evidence_ref, "evidence_ref")
        _text(self.unit_and_basis, "unit_and_basis")
        _refs(self.claim_ids, "claim_ids", required=True)
        quoted = exact_decimal(self.quoted_value, field_name="quoted_value")
        object.__setattr__(self, "quoted_value", quoted)

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "QuotedNumericFactV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "numeric fact payload must be a mapping")
        payload = dict(value)
        payload["claim_ids"] = tuple(payload["claim_ids"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class CanonicalNumericEvidenceValueV1:
    """Read-only deterministic numeric custody returned by the evidence owner."""

    numeric_fact_id: str
    evidence_ref: str
    evidence_bundle_ref: str
    value: Decimal
    unit_and_basis: str
    evidence_receipt_ref: str
    numeric_recheck_receipt_ref: str
    input_lock_id: str
    source_epoch_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        for name in (
            "numeric_fact_id",
            "evidence_ref",
            "evidence_bundle_ref",
            "unit_and_basis",
            "evidence_receipt_ref",
            "numeric_recheck_receipt_ref",
            "input_lock_id",
        ):
            _text(getattr(self, name), name)
        _refs(self.source_epoch_refs, "source_epoch_refs", required=True)
        object.__setattr__(self, "value", exact_decimal(self.value, field_name="value"))
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "canonical numeric evidence validity precedes observation",
            )
        if not self.evidence_receipt_ref.startswith("ST12F-RECEIPT::") or not self.numeric_recheck_receipt_ref.startswith("ST12F-RECEIPT::"):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "canonical numeric evidence requires resolvable receipt-spine identities",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "CanonicalNumericEvidenceValueV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "canonical numeric evidence fields differ",
            )
        payload = dict(value)
        payload["source_epoch_refs"] = tuple(payload["source_epoch_refs"])
        return cls(**payload)


class CanonicalNumericEvidenceResolverProtocolV1(Protocol):
    def resolve_numeric_evidence(
        self,
        *,
        numeric_fact_id: str,
        evidence_ref: str,
    ) -> CanonicalNumericEvidenceValueV1: ...

    def receipt_exists(self, receipt_ref: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class PreexistingAnnotationPacketV1:
    annotation_id: str
    evidence_bundle_refs: tuple[str, ...]
    redacted_context_refs: tuple[str, ...]
    untrusted_content_fragments: tuple[str, ...]
    advisory_task: LLMAdvisoryTaskV1
    citations: tuple[AnnotationCitationV1, ...]
    claims: tuple[AnnotationClaimV1, ...]
    limitations: tuple[str, ...]
    abstentions: tuple[str, ...]
    quoted_numeric_facts: tuple[QuotedNumericFactV1, ...]
    deterministic_numeric_recheck_receipt_refs: tuple[str, ...]
    upstream_budget_metadata: Mapping[str, object]
    requested_actions: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.annotation_id, "annotation_id")
        _refs(self.evidence_bundle_refs, "evidence_bundle_refs", required=True)
        _refs(self.redacted_context_refs, "redacted_context_refs", required=True)
        _refs(self.untrusted_content_fragments, "untrusted_content_fragments")
        _refs(self.limitations, "limitations", required=True)
        _refs(self.abstentions, "abstentions")
        _refs(
            self.deterministic_numeric_recheck_receipt_refs,
            "deterministic_numeric_recheck_receipt_refs",
        )
        _refs(self.requested_actions, "requested_actions", required=True)
        if type(self.advisory_task) is not LLMAdvisoryTaskV1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "advisory task is not allowlisted",
            )
        if (
            not self.citations
            or any(type(row) is not AnnotationCitationV1 for row in self.citations)
            or not self.claims
            or any(type(row) is not AnnotationClaimV1 for row in self.claims)
            or any(type(row) is not QuotedNumericFactV1 for row in self.quoted_numeric_facts)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "annotation requires closed typed citation and claim schemas",
            )
        if not isinstance(self.upstream_budget_metadata, Mapping) or set(self.upstream_budget_metadata) != {
            "budget_source_ref",
            "supplied_upstream",
            "token_budget",
        }:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "upstream budget metadata field roster differs",
            )
        budget_source = self.upstream_budget_metadata["budget_source_ref"]
        supplied = self.upstream_budget_metadata["supplied_upstream"]
        token_budget = self.upstream_budget_metadata["token_budget"]
        if (
            not isinstance(budget_source, str)
            or not budget_source
            or supplied is not True
            or isinstance(token_budget, bool)
            or not isinstance(token_budget, int)
            or token_budget <= 0
        ):
            raise ContractValidationError(
                ReasonCode.BUDGET_EXCEEDED,
                "budget metadata must be supplied and bounded upstream",
            )
        object.__setattr__(
            self,
            "upstream_budget_metadata",
            MappingProxyType(dict(sorted(self.upstream_budget_metadata.items()))),
        )


@dataclass(frozen=True, slots=True)
class DeterministicEvidenceAnnotationContractV1:
    annotation_id: str
    schema_version: str
    contract_version: str
    evidence_bundle_refs: tuple[str, ...]
    redacted_context_refs: tuple[str, ...]
    untrusted_content_isolated: bool
    advisory_task: LLMAdvisoryTaskV1
    citations: tuple[AnnotationCitationV1, ...]
    claims: tuple[AnnotationClaimV1, ...]
    limitations: tuple[str, ...]
    abstentions: tuple[str, ...]
    quoted_numeric_facts: tuple[QuotedNumericFactV1, ...]
    canonical_numeric_evidence: tuple[CanonicalNumericEvidenceValueV1, ...]
    deterministic_numeric_recheck_receipt_refs: tuple[str, ...]
    upstream_budget_metadata: Mapping[str, object]
    input_lock_id: str
    source_epoch_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime
    numeric_recheck_passed: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if self.schema_version != "QTT_ST12F_DETERMINISTIC_EVIDENCE_ANNOTATION_V1_4" or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "annotation schema differs")
        packet = PreexistingAnnotationPacketV1(
            annotation_id=self.annotation_id,
            evidence_bundle_refs=self.evidence_bundle_refs,
            redacted_context_refs=self.redacted_context_refs,
            untrusted_content_fragments=(),
            advisory_task=self.advisory_task,
            citations=self.citations,
            claims=self.claims,
            limitations=self.limitations,
            abstentions=self.abstentions,
            quoted_numeric_facts=self.quoted_numeric_facts,
            deterministic_numeric_recheck_receipt_refs=self.deterministic_numeric_recheck_receipt_refs,
            upstream_budget_metadata=self.upstream_budget_metadata,
            requested_actions=(self.advisory_task.value,),
        )
        object.__setattr__(self, "upstream_budget_metadata", packet.upstream_budget_metadata)
        _text(self.input_lock_id, "input_lock_id")
        _refs(
            self.source_epoch_refs,
            "source_epoch_refs",
            required=bool(self.canonical_numeric_evidence),
        )
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        facts_by_id = {row.numeric_fact_id: row for row in self.quoted_numeric_facts}
        evidence_by_id = {
            row.numeric_fact_id: row for row in self.canonical_numeric_evidence
        }
        if (
            self.untrusted_content_isolated is not True
            or self.numeric_recheck_passed is not True
            or type(self.no_effect_flags) is not NoEffectFlagsV1
            or len(evidence_by_id) != len(self.canonical_numeric_evidence)
            or set(evidence_by_id) != set(facts_by_id)
            or observed > valid_until
        ):
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "normalized annotations require isolation, numeric recheck, and no-effect custody",
            )
        if not self.canonical_numeric_evidence and (
            self.input_lock_id != "EXPLICIT_ABSENCE"
            or self.source_epoch_refs
            or self.deterministic_numeric_recheck_receipt_refs
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "nonnumeric annotation cannot fabricate numeric lock, epoch, or recheck custody",
            )
        for numeric_fact_id, fact in facts_by_id.items():
            evidence = evidence_by_id[numeric_fact_id]
            if (
                evidence.evidence_ref != fact.evidence_ref
                or evidence.unit_and_basis != fact.unit_and_basis
                or evidence.value != fact.quoted_value
                or evidence.input_lock_id != self.input_lock_id
                or evidence.source_epoch_refs != self.source_epoch_refs
                or evidence.observed_at > self.observed_at
                or evidence.valid_until < self.valid_until
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                    "normalized numeric custody differs from canonical evidence",
                )
        if tuple(
            row.numeric_recheck_receipt_ref for row in self.canonical_numeric_evidence
        ) != self.deterministic_numeric_recheck_receipt_refs:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "normalized numeric recheck receipt custody differs",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "DeterministicEvidenceAnnotationContractV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "annotation payload fields differ")
        payload = dict(value)
        payload["advisory_task"] = LLMAdvisoryTaskV1(payload["advisory_task"])
        payload["citations"] = tuple(AnnotationCitationV1.from_canonical_mapping(row) for row in payload["citations"])
        payload["claims"] = tuple(AnnotationClaimV1.from_canonical_mapping(row) for row in payload["claims"])
        payload["quoted_numeric_facts"] = tuple(QuotedNumericFactV1.from_canonical_mapping(row) for row in payload["quoted_numeric_facts"])
        payload["canonical_numeric_evidence"] = tuple(
            CanonicalNumericEvidenceValueV1.from_canonical_mapping(row)
            for row in payload["canonical_numeric_evidence"]
        )
        for name in (
            "evidence_bundle_refs",
            "redacted_context_refs",
            "limitations",
            "abstentions",
            "deterministic_numeric_recheck_receipt_refs",
        ):
            payload[name] = tuple(payload[name])
        payload["source_epoch_refs"] = tuple(payload["source_epoch_refs"])
        payload["no_effect_flags"] = NO_EFFECTS_V1
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class GroundedLLMGatewayV1:
    """Normalizes a supplied packet and has no method that can perform inference."""

    def __init__(self, evidence_resolver: CanonicalNumericEvidenceResolverProtocolV1) -> None:
        if (
            not callable(getattr(evidence_resolver, "resolve_numeric_evidence", None))
            or not callable(getattr(evidence_resolver, "receipt_exists", None))
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "gateway requires the canonical read-only numeric evidence resolver",
            )
        self._evidence_resolver = evidence_resolver

    def validate_and_normalize(
        self,
        packet: PreexistingAnnotationPacketV1,
        *,
        evaluated_at: datetime,
    ) -> DeterministicEvidenceAnnotationContractV1:
        if type(packet) is not PreexistingAnnotationPacketV1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "gateway accepts one exact pre-existing annotation packet",
            )
        fragments = "\n".join(packet.untrusted_content_fragments).casefold()
        if any(marker in fragments for marker in _INSTRUCTION_MARKERS):
            raise ContractValidationError(
                ReasonCode.UNTRUSTED_CONTENT_INSTRUCTION_REJECTED,
                "untrusted content contains an instruction-shaped fragment",
            )
        if packet.requested_actions != (packet.advisory_task.value,):
            raise ContractValidationError(
                ReasonCode.LLM_TOOL_NOT_ALLOWED,
                "annotation requests an action outside the advisory allowlist",
            )
        citation_ids = {row.citation_id for row in packet.citations}
        claim_ids = {row.claim_id for row in packet.claims}
        numeric_ids = {row.numeric_fact_id for row in packet.quoted_numeric_facts}
        citations = {row.citation_id: row for row in packet.citations}
        claims = {row.claim_id: row for row in packet.claims}
        numeric_facts = {
            row.numeric_fact_id: row for row in packet.quoted_numeric_facts
        }
        if (
            len(citation_ids) != len(packet.citations)
            or len(claim_ids) != len(packet.claims)
            or len(numeric_ids) != len(packet.quoted_numeric_facts)
            or any(row.evidence_ref not in packet.evidence_bundle_refs for row in packet.citations)
            or any(not set(row.claim_ids) <= claim_ids for row in packet.citations)
            or any(not set(row.citation_ids) <= citation_ids for row in packet.claims)
            or any(not set(row.numeric_fact_ids) <= numeric_ids for row in packet.claims)
            or any(not set(row.claim_ids) <= claim_ids for row in packet.quoted_numeric_facts)
            or any(row.evidence_ref not in packet.evidence_bundle_refs for row in packet.quoted_numeric_facts)
            or any(
                citation.citation_id not in claims[claim_id].citation_ids
                for citation in packet.citations
                for claim_id in citation.claim_ids
            )
            or any(
                claim.claim_id not in citations[citation_id].claim_ids
                for claim in packet.claims
                for citation_id in claim.citation_ids
            )
            or any(
                claim.claim_id not in numeric_facts[numeric_id].claim_ids
                for claim in packet.claims
                for numeric_id in claim.numeric_fact_ids
            )
            or any(
                fact.numeric_fact_id not in claims[claim_id].numeric_fact_ids
                for fact in packet.quoted_numeric_facts
                for claim_id in fact.claim_ids
            )
            or any(
                len(
                    {
                        *(citations[citation_id].evidence_ref for citation_id in claim.citation_ids),
                        *(numeric_facts[numeric_id].evidence_ref for numeric_id in claim.numeric_fact_ids),
                    }
                )
                != 1
                for claim in packet.claims
                if claim.numeric_fact_ids
            )
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "citation, claim, numeric-fact, or evidence-reference join differs",
            )
        claim_text = "\n".join(row.claim_text for row in packet.claims).casefold()
        if any(marker in claim_text for marker in _AUTHORITY_MARKERS):
            raise ContractValidationError(
                ReasonCode.LLM_ADVISORY_ONLY,
                "annotation attempts a numerical or authority-bearing action",
            )
        if packet.quoted_numeric_facts and not packet.deterministic_numeric_recheck_receipt_refs:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "quoted numerical facts require independent deterministic recheck receipts",
            )
        evaluation_time = parse_utc(evaluated_at, field_name="evaluated_at")
        canonical_numeric_evidence: list[CanonicalNumericEvidenceValueV1] = []
        for fact in packet.quoted_numeric_facts:
            resolved = self._evidence_resolver.resolve_numeric_evidence(
                numeric_fact_id=fact.numeric_fact_id,
                evidence_ref=fact.evidence_ref,
            )
            if (
                type(resolved) is not CanonicalNumericEvidenceValueV1
                or resolved.numeric_fact_id != fact.numeric_fact_id
                or resolved.evidence_ref != fact.evidence_ref
                or resolved.evidence_bundle_ref != fact.evidence_ref
                or resolved.evidence_bundle_ref not in packet.evidence_bundle_refs
                or resolved.unit_and_basis != fact.unit_and_basis
                or resolved.value != fact.quoted_value
                or not resolved.observed_at <= evaluation_time <= resolved.valid_until
                or not self._evidence_resolver.receipt_exists(
                    resolved.evidence_receipt_ref
                )
                or not self._evidence_resolver.receipt_exists(
                    resolved.numeric_recheck_receipt_ref
                )
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                    "quoted numeric fact does not resolve to current canonical evidence",
                )
            canonical_numeric_evidence.append(resolved)
        resolved_recheck_refs = tuple(
            row.numeric_recheck_receipt_ref for row in canonical_numeric_evidence
        )
        if resolved_recheck_refs != packet.deterministic_numeric_recheck_receipt_refs:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "caller numeric-recheck references differ from canonical custody",
            )
        locks = {row.input_lock_id for row in canonical_numeric_evidence}
        epoch_sets = {row.source_epoch_refs for row in canonical_numeric_evidence}
        if canonical_numeric_evidence and (len(locks) != 1 or len(epoch_sets) != 1):
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "annotation numeric evidence spans conflicting lock or epoch custody",
            )
        observed_at = (
            max(row.observed_at for row in canonical_numeric_evidence)
            if canonical_numeric_evidence
            else evaluation_time
        )
        valid_until = (
            min(row.valid_until for row in canonical_numeric_evidence)
            if canonical_numeric_evidence
            else evaluation_time
        )
        return DeterministicEvidenceAnnotationContractV1(
            annotation_id=packet.annotation_id,
            schema_version="QTT_ST12F_DETERMINISTIC_EVIDENCE_ANNOTATION_V1_4",
            contract_version="1.4",
            evidence_bundle_refs=packet.evidence_bundle_refs,
            redacted_context_refs=packet.redacted_context_refs,
            untrusted_content_isolated=True,
            advisory_task=packet.advisory_task,
            citations=packet.citations,
            claims=packet.claims,
            limitations=packet.limitations,
            abstentions=packet.abstentions,
            quoted_numeric_facts=packet.quoted_numeric_facts,
            canonical_numeric_evidence=tuple(canonical_numeric_evidence),
            deterministic_numeric_recheck_receipt_refs=packet.deterministic_numeric_recheck_receipt_refs,
            upstream_budget_metadata=packet.upstream_budget_metadata,
            input_lock_id=(next(iter(locks)) if locks else "EXPLICIT_ABSENCE"),
            source_epoch_refs=(next(iter(epoch_sets)) if epoch_sets else ()),
            observed_at=observed_at,
            valid_until=valid_until,
            numeric_recheck_passed=True,
            no_effect_flags=NO_EFFECTS_V1,
        )
