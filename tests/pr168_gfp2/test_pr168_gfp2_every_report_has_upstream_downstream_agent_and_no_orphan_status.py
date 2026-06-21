from tests.pr168_gfp2.pr168_gfp2_test_support import validate_reports_exist


def test_every_report_has_upstream_downstream_agent_and_no_orphan_status() -> None:
    validate_reports_exist()
