from .test_support import ARTIFACT_DIR, read_json, read_jsonl


def test_builder_outputs_core_registry_and_reports() -> None:
    assert (ARTIFACT_DIR / "art_reg.json").is_file()
    assert read_json("missing_req.report.json")["fail_closed_flag"] is False
    receipt = read_json("run_receipt.report.json")
    assert receipt["branch_created_by_codex"] is True
    assert receipt["QOPT1_outputs_consumed"] is True
    assert receipt["paper_intent_candidate_packets_created"] is True
    assert read_jsonl("paper_intent_candidate.jsonl")
