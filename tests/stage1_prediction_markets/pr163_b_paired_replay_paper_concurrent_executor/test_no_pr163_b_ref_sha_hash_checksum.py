from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor.authority_policy import validate_pr163_b_ref


def test_pr163_b_created_refs_are_plain_text(records):
    for filename in (
        "PR163_B_PairedReplayPaperRunInputRegistry.report.json",
        "PR163_B_ReplayLaneExecutionTraceRegistry.report.json",
        "PR163_B_PaperLaneExecutionTraceRegistry.report.json",
        "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
    ):
        for row in records(filename)[:100]:
            for key, value in row.items():
                if isinstance(value, str) and value.startswith("PR163B_") and key.endswith("_ref"):
                    assert validate_pr163_b_ref(value).ok
