from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor import paths as p


def test_pr163_artifacts_are_consumed(records, summary):
    rows = records("PR163_B_PR162RB_PR163_ArtifactConsumptionLedger.report.json")
    consumed = {row["artifact_filename"] for row in rows if row["upstream_pr"] == "PR163"}
    assert set(p.PR163_REQUIRED_ARTIFACTS).issubset(consumed)
    assert summary["pr163_artifacts_consumed"] == len(p.PR163_REQUIRED_ARTIFACTS)
