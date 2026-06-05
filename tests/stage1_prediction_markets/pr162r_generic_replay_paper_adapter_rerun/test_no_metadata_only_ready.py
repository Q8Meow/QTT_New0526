def test_no_metadata_only_ready(summary, records):
    audit = records("PR162R_QKUNonPlaceholderCompletionAudit.report.json")[0]
    assert summary["metadata_only_ready_count"] == 0
    assert audit["metadata_only_ready_count"] == 0
    assert audit["placeholder_only_completion_count"] == 0
    assert audit["all_qkus_have_exact_computability_route_flag"] is True
