from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_agent_task_handoff_matrix():
    rows = load_records("PR163_C_AgentTaskHandoffMatrix.report.json")
    assert all(row["handoff_to_pr165"] for row in rows)
    assert all(row["handoff_to_pr165b"] for row in rows)
    assert all(row["handoff_to_replay_paper"] for row in rows)
