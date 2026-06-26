from __future__ import annotations

from ._helpers import load_report, load_rows


def test_rp5c_deduplicates_without_deleting_or_banning() -> None:
    identities = load_rows("immutable_qku_formula_library")
    dedupe = load_rows("identity_deduplication_ledger")
    extracted_occurrences = load_report("PR168_RP5C_FinalSummary.report.json")["library_row_counts"][
        "extracted_identity_occurrence_count"
    ]

    assert len(dedupe) == len(identities)
    assert sum(int(row["duplicate_member_count"]) for row in dedupe) == extracted_occurrences
    assert all(row["dedupe_without_deletion_flag"] is True for row in dedupe)
    assert all(row["global_ban_flag"] is False for row in dedupe)
    assert {row["duplicate_status"] for row in identities}
