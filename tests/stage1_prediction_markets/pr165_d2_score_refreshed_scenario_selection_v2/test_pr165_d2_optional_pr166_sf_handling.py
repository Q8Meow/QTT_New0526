from __future__ import annotations


def test_pr166_sf_absence_is_optional_and_uses_pr166_sm_handoff(pr165_d2_records, pr165_d2_summary):
    optional_present = pr165_d2_summary["optional_pr166_sf_present"] is True
    assert (
        pr165_d2_summary["optional_pr166_sf_missing_handled_by_pr166_sm_repair_handoff"]
        is (not optional_present)
    )
    rows = pr165_d2_records["PR165_D2_OptionalInputResolutionLedger.report.json"]
    repaired_queue = next(row for row in rows if row["optional_artifact_ref"] == "PR166_SF_RepairedCandidateRetestQueue.report.json")
    expected_handling = (
        "OPTIONAL_PRESENT_CONSUMED_AS_STRENGTHENING_INPUT"
        if optional_present
        else "OPTIONAL_NOT_PRESENT_CONSUMED_PR166_SM_REPAIR_HANDOFF"
    )
    assert repaired_queue["absence_handling"] == expected_handling
