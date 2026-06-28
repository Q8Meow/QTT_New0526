from ._helpers import read_json, read_jsonl


def test_no_orphan_ledgers_close_artifact_and_qku_formula_routes() -> None:
    art = read_jsonl("orph_art.jsonl")
    qku = read_jsonl("orph_qku.jsonl")
    receipt = read_json("run_receipt.report.json")

    assert art and qku
    assert all(row["orphan_flag"] is False for row in art)
    assert all(row["orphan_flag"] is False for row in qku)
    assert receipt["orphan_artifact_count"] == 0
    assert receipt["orphan_qku_count"] == 0
    assert receipt["orphan_formula_count"] == 0
