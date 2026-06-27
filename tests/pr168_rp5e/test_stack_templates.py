from ._helpers import read_jsonl


def test_stack_templates_cover_generation_modes_and_required_roles() -> None:
    rows = read_jsonl("templates.jsonl")
    modes = {mode for row in rows for mode in row["mode_eligibility"]}
    assert {"HOT_PATH_PREVIEW", "WARM_REPLAY_PAPER_SEARCH", "COLD_RESEARCH_EXPANSION"} <= modes
    for row in rows:
        assert row["minimum_stack_size"] <= row["maximum_stack_size"]
        assert "classical_fallback_rule_ref" in row
        assert row["use_dump_policy_ref"]
