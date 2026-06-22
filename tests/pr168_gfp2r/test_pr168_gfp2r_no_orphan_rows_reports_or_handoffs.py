from tests.pr168_gfp2r._helpers import all_generated_payloads, assert_all_reports_have_records


def test_pr168_gfp2r_no_orphan_rows_reports_or_handoffs() -> None:
    assert_all_reports_have_records()
    for payload in all_generated_payloads():
        if isinstance(payload, dict) and "no_orphan_status" in payload:
            assert payload["no_orphan_status"] == "NO_ORPHAN_ROUTED"
