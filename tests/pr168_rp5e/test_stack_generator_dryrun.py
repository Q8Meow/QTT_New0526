from ._helpers import read_json, read_jsonl


def test_stack_generator_materializes_preview_rows_only() -> None:
    previews = read_jsonl("tmp_previews.jsonl")
    topk = read_jsonl("topk.jsonl")
    receipt = read_json("run_receipt.report.json")

    assert len(previews) == receipt["runtime_stack_preview_rows"]
    assert len(topk) == receipt["retained_topk_preview_rows"]
    assert all(row["retain_or_discard"] == "RETAIN" for row in topk)
    assert all(row["final_trade_rank_flag"] is False for row in topk)
    assert all(row["champion_selected_flag"] is False for row in topk)
