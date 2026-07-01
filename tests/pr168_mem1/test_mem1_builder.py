from .test_support import read_json, read_jsonl


def test_builder_outputs_core_registry_and_reports() -> None:
    assert read_json("missing_req.report.json")["fail_closed_flag"] is False
    receipt = read_json("run_receipt.report.json")
    assert receipt["branch_created_by_codex"] is True
    assert receipt["VS2_outputs_consumed"] is True
    assert receipt["conditioned_winning_recipe_registry_created"] is True
    assert receipt["quantum_structural_memory_registry_created"] is True
    assert read_jsonl("winning_recipe.jsonl")
