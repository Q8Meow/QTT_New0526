from ._helpers import read_json, read_jsonl


def test_owner_audit_answers_are_materialized() -> None:
    run = read_json("run_receipt.report.json")
    pre = read_jsonl("self_audit_pre.jsonl")
    post = read_jsonl("self_audit_post.jsonl")
    assert "edge_alpha_profit_help" in run["owner_audit_answers"]
    assert any(row["question_id"] == "owner_profit_answer" for row in pre)
    assert all(row["answer_pass_flag"] for row in post)
