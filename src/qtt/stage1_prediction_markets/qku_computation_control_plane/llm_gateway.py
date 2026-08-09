"""Deterministic validation of pre-existing advisory annotations; no inference."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal
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
    "rewrite the number",
    "select the winner",
    "winner is",
    "change the parameter",
    "change the formula",
    "accept this source",
    "activate mode",
    "grant allow",
    "release order",
    "submit order",
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
        return cls(**dict(value))


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
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class QuotedNumericFactV1:
    numeric_fact_id: str
    evidence_ref: str
    unit_and_basis: str
    quoted_value: Decimal
    deterministic_evidence_value: Decimal

    def __post_init__(self) -> None:
        _text(self.numeric_fact_id, "numeric_fact_id")
        _text(self.evidence_ref, "evidence_ref")
        _text(self.unit_and_basis, "unit_and_basis")
        quoted = exact_decimal(self.quoted_value, field_name="quoted_value")
        evidence = exact_decimal(
            self.deterministic_evidence_value,
            field_name="deterministic_evidence_value",
        )
        object.__setattr__(self, "quoted_value", quoted)
        object.__setattr__(self, "deterministic_evidence_value", evidence)
        if quoted != evidence:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "quoted numeric fact differs from deterministic evidence",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "QuotedNumericFactV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "numeric fact payload must be a mapping")
        return cls(**dict(value))


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
    deterministic_numeric_recheck_receipt_refs: tuple[str, ...]
    upstream_budget_metadata: Mapping[str, object]
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
        if (
            self.untrusted_content_isolated is not True
            or self.numeric_recheck_passed is not True
            or type(self.no_effect_flags) is not NoEffectFlagsV1
        ):
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "normalized annotations require isolation, numeric recheck, and no-effect custody",
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
        payload["no_effect_flags"] = NO_EFFECTS_V1
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class GroundedLLMGatewayV1:
    """Normalizes a supplied packet and has no method that can perform inference."""

    def validate_and_normalize(
        self, packet: PreexistingAnnotationPacketV1
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
        if (
            len(citation_ids) != len(packet.citations)
            or len(claim_ids) != len(packet.claims)
            or len(numeric_ids) != len(packet.quoted_numeric_facts)
            or any(row.evidence_ref not in packet.evidence_bundle_refs for row in packet.citations)
            or any(not set(row.claim_ids) <= claim_ids for row in packet.citations)
            or any(not set(row.citation_ids) <= citation_ids for row in packet.claims)
            or any(not set(row.numeric_fact_ids) <= numeric_ids for row in packet.claims)
            or any(row.evidence_ref not in packet.evidence_bundle_refs for row in packet.quoted_numeric_facts)
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
            deterministic_numeric_recheck_receipt_refs=packet.deterministic_numeric_recheck_receipt_refs,
            upstream_budget_metadata=packet.upstream_budget_metadata,
            numeric_recheck_passed=True,
            no_effect_flags=NO_EFFECTS_V1,
        )
