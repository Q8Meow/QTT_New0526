from ._helpers import report, rows


def test_builder_creates_primary_artifacts() -> None:
    run_report = report("run_receipt.report.json")
    assert run_report["branch_created_by_codex"] is True
    assert run_report["RANK4_outputs_consumed"] is True
    assert run_report["RP5G_refs_preserved"] is True
    assert run_report["candidate_count"] >= 1
    assert rows("batch_select.jsonl")
