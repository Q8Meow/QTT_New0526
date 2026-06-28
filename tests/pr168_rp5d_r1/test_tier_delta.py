from ._helpers import read_jsonl


def test_tier_delta_formula_is_materialized() -> None:
    row = read_jsonl("tier_delta.jsonl")[0]
    assert row["new_overlay_count"] == row["prior_executable_now_count"] + row["promoted_count"]
    assert row["upstream_mutation_flag"] is False
