from .test_support import records, report


def test_pr162c_owner_materialization_command_queue():
    summary = report("PR162C_FinalSummary.report.json")
    commands = records("PR162C_OwnerMaterializationCommandQueue.report.json")

    assert summary["owner_materialization_command_count"] == len(commands)
    assert len(commands) >= 1
    assert all(record["execute_in_default_ci_flag"] is False for record in commands)
    assert all(record["destination_path"].startswith("data/stage1_prediction_markets/nonlive_datasets/pr162c/") for record in commands)
