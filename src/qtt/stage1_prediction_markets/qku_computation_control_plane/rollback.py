"""Precommit rollback and append-only postcommit reversal contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from .accounting import AccountingAmountV1, EntrySideV1, JournalPostingV1, JournalTransactionV1
from .context import exact_decimal, parse_utc
from .errors import AccountingContractError, ContractValidationError, ReasonCode


@dataclass(frozen=True, slots=True)
class ReversalReceiptV1:
    reversal_receipt_id: str
    original_event_or_transaction_ref: str
    reversal_event_ref: str
    reversal_transaction_ref: str
    reason_code: str
    authority_ref: str
    effective_at: datetime | str
    recorded_at: datetime | str
    replacement_ref: str | None
    remaining_reversible_amounts: tuple[AccountingAmountV1, ...]

    def __post_init__(self) -> None:
        for name in (
            "reversal_receipt_id", "original_event_or_transaction_ref", "reversal_event_ref",
            "reversal_transaction_ref", "reason_code", "authority_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        if self.replacement_ref is not None and (not isinstance(self.replacement_ref, str) or not self.replacement_ref):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "replacement_ref must be nonempty when supplied")
        if not isinstance(self.remaining_reversible_amounts, tuple) or any(not isinstance(row, AccountingAmountV1) for row in self.remaining_reversible_amounts):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "remaining reversible amounts must be typed")
        if any(row.decimal < 0 for row in self.remaining_reversible_amounts):
            raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "remaining reversible amount cannot be negative")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


@dataclass(frozen=True, slots=True)
class JournalReversalBundleV1:
    transaction: JournalTransactionV1
    postings: tuple[JournalPostingV1, ...]
    receipt: ReversalReceiptV1


def build_journal_reversal_v1(
    *,
    original_transaction: JournalTransactionV1,
    original_postings: tuple[JournalPostingV1, ...],
    reversal_receipt_id: str,
    reversal_event_ref: str,
    reversal_transaction_id: str,
    reversal_posting_ids: tuple[str, ...],
    requested_amount_by_original_posting: Mapping[str, Decimal | str | int] | None,
    previously_reversed_by_original_posting: Mapping[str, Decimal | str | int],
    reason_code: str,
    authority_ref: str,
    effective_at: datetime | str,
    recorded_at: datetime | str,
    replacement_ref: str | None = None,
) -> JournalReversalBundleV1:
    """Create one linked balanced reversal without mutating the committed original."""

    if tuple(row.posting_id for row in original_postings) != original_transaction.posting_refs:
        raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "original transaction/postings do not align")
    if len(reversal_posting_ids) != len(original_postings) or len(set(reversal_posting_ids)) != len(reversal_posting_ids):
        raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "one unique reversal posting identity is required per original posting")
    requested = requested_amount_by_original_posting or {}
    reversed_so_far = {key: exact_decimal(value, field_name=f"previously_reversed[{key}]") for key, value in previously_reversed_by_original_posting.items()}
    original_ids = {row.posting_id for row in original_postings}
    if (requested and set(requested) != original_ids) or not set(reversed_so_far) <= original_ids:
        raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "reversal amount maps must reference the original postings exactly")
    parsed_recorded_at = parse_utc(recorded_at, field_name="recorded_at")
    if parsed_recorded_at < original_transaction.recorded_at:
        raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "reversal cannot be recorded before the original transaction")
    reversal_postings: list[JournalPostingV1] = []
    remaining_amounts: list[AccountingAmountV1] = []
    partition_balance: dict[tuple[str, str, str], Decimal] = {}
    for original, reversal_id in zip(original_postings, reversal_posting_ids, strict=True):
        previous = reversed_so_far.get(original.posting_id, Decimal(0))
        if previous < 0 or previous > original.magnitude:
            raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "previous reversal exceeds original posting")
        remaining = original.magnitude - previous
        amount = remaining if not requested else exact_decimal(requested.get(original.posting_id), field_name=f"requested[{original.posting_id}]")
        if amount <= 0 or amount > remaining:
            raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "requested reversal exceeds remaining amount")
        side = EntrySideV1.CREDIT if original.entry_side is EntrySideV1.DEBIT else EntrySideV1.DEBIT
        posting = JournalPostingV1(
            posting_id=reversal_id,
            journal_transaction_id=reversal_transaction_id,
            account_id=original.account_id,
            entry_side=side,
            amount_text=str(amount),
            ledger_unit=original.ledger_unit,
            currency_or_asset=original.currency_or_asset,
            basis=original.basis,
            scale=original.scale,
            effective_at=effective_at,
            recorded_at=parsed_recorded_at,
            source_event_ref=reversal_event_ref,
        )
        reversal_postings.append(posting)
        partition_balance[posting.partition] = partition_balance.get(posting.partition, Decimal(0)) + posting.signed_conservation_value
        remaining_amounts.append(
            AccountingAmountV1(
                amount_text=str(remaining - amount),
                currency_or_asset=original.currency_or_asset,
                ledger_unit=original.ledger_unit,
                basis=original.basis,
                scale=original.scale,
                rounding_policy_ref="IDENTITY_FROM_ORIGINAL_POSTING",
            )
        )
    if any(value != 0 for value in partition_balance.values()):
        raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "partial reversal is not exactly balanced by partition")
    reversal_transaction = JournalTransactionV1(
        journal_transaction_id=reversal_transaction_id,
        transaction_class="APPEND_ONLY_REVERSAL",
        economic_event_refs=(reversal_event_ref,),
        posting_refs=tuple(reversal_posting_ids),
        effective_at=effective_at,
        recorded_at=parsed_recorded_at,
        description_code=reason_code,
        authority_class=authority_ref,
        reversal_of_transaction_id=original_transaction.journal_transaction_id,
    )
    receipt = ReversalReceiptV1(
        reversal_receipt_id=reversal_receipt_id,
        original_event_or_transaction_ref=original_transaction.journal_transaction_id,
        reversal_event_ref=reversal_event_ref,
        reversal_transaction_ref=reversal_transaction_id,
        reason_code=reason_code,
        authority_ref=authority_ref,
        effective_at=effective_at,
        recorded_at=parsed_recorded_at,
        replacement_ref=replacement_ref,
        remaining_reversible_amounts=tuple(remaining_amounts),
    )
    return JournalReversalBundleV1(reversal_transaction, tuple(reversal_postings), receipt)


class PrecommitRollbackStateV1(StrEnum):
    ROLLED_BACK = "ROLLED_BACK"


PRECOMMIT_ROLLBACK_RULE_V1 = "NO_AUTHORITATIVE_ECONOMIC_RECORD_SURVIVES"
PROJECTION_REBUILD_RULE_V1 = "REBUILD_FROM_APPEND_ONLY_RECORDS_AT_EXPLICIT_EFFECTIVE_AND_RECORDED_CUTOFFS"
