from __future__ import annotations


def test_external_signal_coverage_is_candidate_provisional(pr165_d2_records):
    signals = pr165_d2_records["PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json"]
    coverage = pr165_d2_records["PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json"]
    assert len(signals) == len(coverage) >= 1
    assert all(row["authority_class"] == "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH" for row in signals)
    assert all(row["source_truth_acceptance_count"] == 0 for row in coverage)
