from tests.pr169_dash1.conftest import jsonl


def test_edge_alpha_rows_have_evidence_refs_or_actionable_routes() -> None:
    rows = jsonl("owner_edge_alpha_capture_view.generated.jsonl")
    expected = {"LIVE_EDGE_RADAR_PANEL", "EDGE_HYPOTHESIS_BOARD", "ALPHA_CANDIDATE_SCOREBOARD", "NO_TRADE_BOARD", "REPLAY_PAPER_TEST_QUEUE_PANEL"}
    assert expected.issubset({row["edge_id"].split("::", 1)[1] for row in rows})
    for row in rows:
        assert row["execution_adjusted_rank_ref"]
        assert row["TCA_adjusted_expected_net_cash_ref"]
        assert row["activation_route"]
