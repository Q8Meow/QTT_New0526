def test_pretrade_rejection_remediation_covers_pr163_rejects(records, summary):
    rows = records("PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json")
    rejected = [row for row in rows if row["paper_pretrade_status"] != "PAPER_PRETRADE_PASS"]
    assert len(rejected) == summary["pr163_reported_paper_pretrade_rejected_rows"] == 2394
    assert summary["valid_rejection_count"] > 0
    assert summary["artificial_infrastructure_rejection_count"] > 0
    assert summary["repairable_pre_launch_count"] > 0
