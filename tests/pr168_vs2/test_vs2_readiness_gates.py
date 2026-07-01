from .test_support import packet_ids, read_json, read_jsonl


def test_readiness_report_matches_gate_rows() -> None:
    report = read_json("paper_readiness.report.json")
    readiness = read_jsonl("paper_readiness.jsonl")
    assert report["paper_readiness_row_count"] == len(readiness)
    assert {row["paper_intent_candidate_id"] for row in readiness} == packet_ids()


def test_all_gate_families_cover_packets() -> None:
    for name in (
        "paper_gate.jsonl",
        "paper_risk_check.jsonl",
        "paper_tca_check.jsonl",
        "paper_fill_latency_check.jsonl",
        "paper_capacity_check.jsonl",
        "paper_fdr_check.jsonl",
        "paper_scenario_check.jsonl",
        "paper_portfolio_check.jsonl",
        "paper_notrade_check.jsonl",
        "paper_model_risk_check.jsonl",
        "paper_stale_check.jsonl",
        "paper_source_fresh_check.jsonl",
    ):
        assert {row["paper_intent_candidate_id"] for row in read_jsonl(name)} == packet_ids()
