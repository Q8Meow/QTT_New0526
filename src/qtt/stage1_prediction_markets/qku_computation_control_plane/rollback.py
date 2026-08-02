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


@dataclass(frozen=True, slots=True)
class ReversalPostingHistoryV1:
    """Derived immutable reversal state for one committed original posting."""

    original_posting: JournalPostingV1
    cumulative_reversed_amount: AccountingAmountV1
    remaining_reversible_amount: AccountingAmountV1

    def __post_init__(self) -> None:
        if not isinstance(self.original_posting, JournalPostingV1):
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "reversal posting history requires one typed original posting",
            )
        for amount in (
            self.cumulative_reversed_amount,
            self.remaining_reversible_amount,
        ):
            if not isinstance(amount, AccountingAmountV1):
                raise AccountingContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "reversal posting history amounts must be typed",
                )
            if (
                amount.partition != self.original_posting.partition
                or amount.scale != self.original_posting.scale
                or amount.decimal < 0
            ):
                raise AccountingContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "reversal posting history dimensions conflict with the original",
                )
        if (
            self.cumulative_reversed_amount.decimal
            + self.remaining_reversible_amount.decimal
            != self.original_posting.magnitude
        ):
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "reversal posting history does not conserve the original magnitude",
            )


@dataclass(frozen=True, slots=True)
class ReversalHistoryViewV1:
    """Committed-snapshot history; accounting meaning is derived locally below."""

    original_transaction: JournalTransactionV1
    original_postings: tuple[JournalPostingV1, ...]
    committed_reversals: tuple[JournalReversalBundleV1, ...]
    snapshot_state: str = "COMMITTED_BEFORE_CURRENT_TRANSACTION"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.original_transaction, JournalTransactionV1)
            or not isinstance(self.original_postings, tuple)
            or any(
                not isinstance(posting, JournalPostingV1)
                for posting in self.original_postings
            )
            or not isinstance(self.committed_reversals, tuple)
            or any(
                not isinstance(bundle, JournalReversalBundleV1)
                for bundle in self.committed_reversals
            )
            or self.snapshot_state != "COMMITTED_BEFORE_CURRENT_TRANSACTION"
        ):
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "reversal history must be an exact committed typed snapshot",
            )

    @property
    def posting_history(self) -> tuple[ReversalPostingHistoryV1, ...]:
        return _derive_reversal_posting_history_v1(self)

    @property
    def cumulative_reversed_amounts(self) -> tuple[AccountingAmountV1, ...]:
        return tuple(row.cumulative_reversed_amount for row in self.posting_history)

    @property
    def remaining_reversible_amounts(self) -> tuple[AccountingAmountV1, ...]:
        return tuple(row.remaining_reversible_amount for row in self.posting_history)


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


def _history_amount_v1(
    original: JournalPostingV1,
    amount: Decimal,
) -> AccountingAmountV1:
    return AccountingAmountV1(
        amount_text=f"{amount:.{original.scale}f}",
        currency_or_asset=original.currency_or_asset,
        ledger_unit=original.ledger_unit,
        basis=original.basis,
        scale=original.scale,
        rounding_policy_ref="IDENTITY_FROM_ORIGINAL_POSTING",
    )


def _derive_reversal_posting_history_v1(
    history: ReversalHistoryViewV1,
) -> tuple[ReversalPostingHistoryV1, ...]:
    original = history.original_transaction
    original_postings = history.original_postings
    if (
        tuple(posting.posting_id for posting in original_postings)
        != original.posting_refs
        or len(original_postings) < 2
    ):
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "committed original journal and postings do not close exactly",
        )
    original_balance: dict[tuple[str, str, str], Decimal] = {}
    for posting in original_postings:
        if posting.journal_transaction_id != original.journal_transaction_id:
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "committed original posting references a different journal",
            )
        original_balance[posting.partition] = (
            original_balance.get(posting.partition, Decimal(0))
            + posting.signed_conservation_value
        )
    if any(value != 0 for value in original_balance.values()):
        raise AccountingContractError(
            ReasonCode.ACCOUNTING_IMBALANCE,
            "committed original journal is not balanced by partition",
        )

    cumulative = {posting.posting_id: Decimal(0) for posting in original_postings}
    seen_receipts: set[str] = set()
    seen_transactions: set[str] = set()
    seen_postings: set[str] = set()
    prior_recorded_at = original.recorded_at
    for bundle in history.committed_reversals:
        transaction = bundle.transaction
        postings = bundle.postings
        receipt = bundle.receipt
        if (
            receipt.reversal_receipt_id in seen_receipts
            or transaction.journal_transaction_id in seen_transactions
            or any(posting.posting_id in seen_postings for posting in postings)
        ):
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "committed reversal history contains duplicate linkage",
            )
        seen_receipts.add(receipt.reversal_receipt_id)
        seen_transactions.add(transaction.journal_transaction_id)
        seen_postings.update(posting.posting_id for posting in postings)
        if (
            transaction.reversal_of_transaction_id
            != original.journal_transaction_id
            or receipt.original_event_or_transaction_ref
            != original.journal_transaction_id
            or receipt.reversal_transaction_ref
            != transaction.journal_transaction_id
            or transaction.economic_event_refs
            != (receipt.reversal_event_ref,)
            or tuple(posting.posting_id for posting in postings)
            != transaction.posting_refs
            or len(postings) != len(original_postings)
            or receipt.recorded_at != transaction.recorded_at
            or receipt.effective_at != transaction.effective_at
            or transaction.recorded_at < prior_recorded_at
        ):
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "committed reversal journal, postings, and receipt do not close",
            )
        prior_recorded_at = transaction.recorded_at
        partition_balance: dict[tuple[str, str, str], Decimal] = {}
        for source, reversal in zip(original_postings, postings, strict=True):
            expected_side = (
                EntrySideV1.CREDIT
                if source.entry_side is EntrySideV1.DEBIT
                else EntrySideV1.DEBIT
            )
            if (
                reversal.journal_transaction_id
                != transaction.journal_transaction_id
                or reversal.source_event_ref != receipt.reversal_event_ref
                or reversal.account_id != source.account_id
                or reversal.entry_side is not expected_side
                or reversal.partition != source.partition
                or reversal.scale != source.scale
            ):
                raise AccountingContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed reversal posting conflicts with original dimensions",
                )
            updated = cumulative[source.posting_id] + reversal.magnitude
            if updated < 0 or updated > source.magnitude:
                raise AccountingContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed cumulative reversal exceeds the original posting",
                )
            cumulative[source.posting_id] = updated
            partition_balance[reversal.partition] = (
                partition_balance.get(reversal.partition, Decimal(0))
                + reversal.signed_conservation_value
            )
        if any(value != 0 for value in partition_balance.values()):
            raise AccountingContractError(
                ReasonCode.ACCOUNTING_IMBALANCE,
                "committed reversal is not balanced by partition",
            )
        expected_remaining = tuple(
            _history_amount_v1(
                source,
                source.magnitude - cumulative[source.posting_id],
            )
            for source in original_postings
        )
        if receipt.remaining_reversible_amounts != expected_remaining:
            raise AccountingContractError(
                ReasonCode.REVERSAL_INVALID,
                "committed reversal receipt has conflicting remaining amounts",
            )

    return tuple(
        ReversalPostingHistoryV1(
            original_posting=source,
            cumulative_reversed_amount=_history_amount_v1(
                source, cumulative[source.posting_id]
            ),
            remaining_reversible_amount=_history_amount_v1(
                source, source.magnitude - cumulative[source.posting_id]
            ),
        )
        for source in original_postings
    )


def validate_reversal_bundle_against_history_v1(
    *,
    history: ReversalHistoryViewV1,
    proposed: JournalReversalBundleV1,
) -> None:
    """Validate a proposed reversal solely from committed append-only history."""

    if not isinstance(history, ReversalHistoryViewV1) or not isinstance(
        proposed, JournalReversalBundleV1
    ):
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "typed committed reversal history and proposed bundle are required",
        )
    posting_history = history.posting_history
    if all(row.remaining_reversible_amount.decimal == 0 for row in posting_history):
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "the committed original transaction is already fully reversed",
        )
    historical_receipt_ids = {
        bundle.receipt.reversal_receipt_id
        for bundle in history.committed_reversals
    }
    historical_transaction_ids = {
        bundle.transaction.journal_transaction_id
        for bundle in history.committed_reversals
    }
    historical_posting_ids = {
        posting.posting_id
        for bundle in history.committed_reversals
        for posting in bundle.postings
    }
    if (
        proposed.receipt.reversal_receipt_id in historical_receipt_ids
        or proposed.transaction.journal_transaction_id in historical_transaction_ids
        or any(
            posting.posting_id in historical_posting_ids
            for posting in proposed.postings
        )
    ):
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "proposed reversal duplicates committed reversal linkage",
        )
    if len(proposed.postings) != len(history.original_postings):
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "proposed reversal does not align with every original posting",
        )
    requested = {
        original.posting_id: reversal.magnitude
        for original, reversal in zip(
            history.original_postings, proposed.postings, strict=True
        )
    }
    reversed_so_far = {
        row.original_posting.posting_id: row.cumulative_reversed_amount.decimal
        for row in posting_history
    }
    expected = build_journal_reversal_v1(
        original_transaction=history.original_transaction,
        original_postings=history.original_postings,
        reversal_receipt_id=proposed.receipt.reversal_receipt_id,
        reversal_event_ref=proposed.receipt.reversal_event_ref,
        reversal_transaction_id=proposed.transaction.journal_transaction_id,
        reversal_posting_ids=tuple(
            posting.posting_id for posting in proposed.postings
        ),
        requested_amount_by_original_posting=requested,
        previously_reversed_by_original_posting=reversed_so_far,
        reason_code=proposed.receipt.reason_code,
        authority_ref=proposed.receipt.authority_ref,
        effective_at=proposed.receipt.effective_at,
        recorded_at=proposed.receipt.recorded_at,
        replacement_ref=proposed.receipt.replacement_ref,
    )
    if proposed != expected:
        raise AccountingContractError(
            ReasonCode.REVERSAL_INVALID,
            "proposed reversal bundle conflicts with committed reversal history",
        )


class PrecommitRollbackStateV1(StrEnum):
    ROLLED_BACK = "ROLLED_BACK"


PRECOMMIT_ROLLBACK_RULE_V1 = "NO_AUTHORITATIVE_ECONOMIC_RECORD_SURVIVES"
PROJECTION_REBUILD_RULE_V1 = "REBUILD_FROM_APPEND_ONLY_RECORDS_AT_EXPLICIT_EFFECTIVE_AND_RECORDED_CUTOFFS"
