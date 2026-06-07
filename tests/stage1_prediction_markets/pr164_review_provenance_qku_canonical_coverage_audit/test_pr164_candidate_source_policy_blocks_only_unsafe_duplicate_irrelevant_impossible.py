from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.candidate_source_policy import REJECTED_DISPOSITIONS
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records


def test_pr164_candidate_source_policy_blocks_only_allowed_reasons():
    audit = load_records("PR164_CandidateSourcePolicyAudit.report.json")[0]
    rows = load_records("PR164_CandidateSourceAcquisitionLedger.report.json")
    rejected = [row for row in rows if row["source_policy_disposition"].startswith("REJECT_")]

    assert audit["rejected_only_for_allowed_reasons"] is True
    assert audit["nonofficial_rejected_merely_because_nonofficial_count"] == 0
    assert rejected
    assert all(row["source_policy_disposition"] in REJECTED_DISPOSITIONS for row in rejected)
