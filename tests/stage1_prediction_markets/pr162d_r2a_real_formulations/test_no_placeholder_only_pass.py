from __future__ import annotations


def test_no_placeholder_only_pass_is_backed_by_sample_records(records):
    audit = records("PR162D_R2A_NoPlaceholderOnlyCompletionAudit.report.json")[0]
    assert audit["placeholder_only_completion_count"] == 0
    assert audit["sample_checked_records"]
    assert all(row["materiality_fields_present"] for row in audit["sample_checked_records"])
