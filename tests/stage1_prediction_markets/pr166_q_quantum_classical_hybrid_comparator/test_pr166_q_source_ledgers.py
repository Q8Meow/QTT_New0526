from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_q_source_reading_and_external_intake_are_candidate_only():
    source_rows = assert_report_contract("PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json")
    intake_rows = assert_report_contract("PR166_Q_ExternalCandidateIntakeLedger.report.json")
    assert len(source_rows) >= 12
    assert any(row["official_flag"] for row in source_rows)
    assert any(row["non_official_flag"] for row in source_rows)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in source_rows)
    assert all(row["candidate_authority_class"] == "REPLAY_PAPER_CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH" for row in intake_rows)
    assert sum(row["quantum_structures_extracted_count"] for row in source_rows) > 0
    assert sum(row["parameter_ranges_extracted_count"] for row in source_rows) > 0
