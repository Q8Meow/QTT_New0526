from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_candidate_source_acquisition_accepts_nonofficial_candidates():
    rows = load_records("PR164_CandidateSourceAcquisitionLedger.report.json")
    accepted_nonofficial = [
        row
        for row in rows
        if row["source_class"]
        in {
            "ACADEMIC_RESEARCH",
            "INSTITUTIONAL_RESEARCH",
            "OPEN_SOURCE_REPO_RESEARCH_ONLY",
            "SOCIAL_SIGNAL_RESEARCH_ONLY",
            "NEWS_RESEARCH_ONLY",
        }
        and not row["source_policy_disposition"].startswith("REJECT_")
    ]
    assert accepted_nonofficial
    assert summary()["nonofficial_candidate_source_rows"] > 0
