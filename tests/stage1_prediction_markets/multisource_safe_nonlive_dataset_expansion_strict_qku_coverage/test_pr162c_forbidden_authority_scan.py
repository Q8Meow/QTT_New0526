from .test_support import records, report


def test_pr162c_forbidden_authority_scan():
    summary = report("PR162C_FinalSummary.report.json")
    scan = records("PR162C_ForbiddenAuthorityScan.report.json")[0]

    assert scan["scan_status"] == "PASS"
    assert scan["failure_count"] == 0
    assert summary["forbidden_authority_scan_result"] == "PASS"
    assert summary["no_sha_freeze_hash_authority_confirmed"] is True
    assert summary["no_atomicrows_bundle_mutation_confirmed"] is True
