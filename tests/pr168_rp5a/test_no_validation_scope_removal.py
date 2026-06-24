from tests.pr168_rp5a._helpers import load_report


def test_no_validation_scope_removal() -> None:
    report = load_report("PR168_RP5A_NoDeletionProof.report.json")
    assert report["validation_scope_removed_count"] == 0
    assert report["no_legacy_scope_removal_flag"] is True
