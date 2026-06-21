from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_terminal_artifacts_require_terminal_reason_code() -> None:
    rows = load("PR168_GFP2_TerminalArtifactExceptionLedger.report.json")
    assert rows
    assert all(row["terminal_reason_code"] for row in rows)
