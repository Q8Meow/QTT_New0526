from tests.pr168_rank3._helpers import assert_rank3_valid, report


def test_offline_mode_materialized_from_committed_artifacts() -> None:
    assert_rank3_valid()
    assert report("PR168_RANK3_Input.report.json")["records"]["build_mode"] in {"offline", "verify-online-docs"}
