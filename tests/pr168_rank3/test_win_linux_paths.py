from tests.pr168_rank3._helpers import assert_rank3_valid, report


def test_generated_paths_are_posix_relative() -> None:
    assert_rank3_valid()
    paths = report("PR168_RANK3_PathAudit.report.json")["records"]["rows"]
    assert all("\\" not in row["path_ref"] for row in paths)
