from ._helpers import report, rows


def test_authority_boundaries_are_false() -> None:
    assert report("authority_boundary.report.json")["authority_boundary_pass_flag"] is True
    for filename in ("rank_auth_block.jsonl", "rank_auto_trading_path.jsonl", "rank_live_ladder.jsonl"):
        for row in rows(filename):
            assert row["paper_submit_authority_created_flag"] is False
            assert row["live_authority_created_flag"] is False
            assert row["qopt_execution_flag"] is False

