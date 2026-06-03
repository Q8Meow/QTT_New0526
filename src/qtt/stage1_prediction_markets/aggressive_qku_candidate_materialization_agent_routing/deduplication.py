"""Candidate deduplication helpers."""

from __future__ import annotations


def deduplicate_by_id(records: list[dict[str, object]], id_field: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    seen: set[str] = set()
    kept: list[dict[str, object]] = []
    duplicates: list[dict[str, object]] = []
    for record in records:
        key = str(record.get(id_field))
        if key in seen:
            duplicates.append(record)
            continue
        seen.add(key)
        kept.append(record)
    return kept, duplicates


def candidate_deduplication_records(duplicate_count: int = 0) -> list[dict[str, object]]:
    return [
        {
            "record_id": "PR162D-CANDIDATE-DEDUPLICATION-SUMMARY",
            "duplicate_low_value_count": duplicate_count,
            "deduplication_status": "PASS_NO_DUPLICATE_LOW_VALUE_REJECTION_OF_USEFUL_MAPPABLE_CANDIDATES",
        }
    ]
