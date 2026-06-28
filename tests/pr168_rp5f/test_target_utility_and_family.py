from ._helpers import assert_rows_have_contract


def test_target_utility_and_family_are_selection_surfaces_only() -> None:
    utility = assert_rows_have_contract("target_utility.jsonl")
    family = assert_rows_have_contract("target_family.jsonl")

    assert all(row["selection_preference_only_flag"] is True for row in utility)
    assert all(row["profit_proof_flag"] is False for row in utility)
    assert all(row["final_ranking_flag"] is False for row in utility)
    assert all(row["future_mem1_consumer_flag"] is True for row in family)
    assert all(row["near_clone_cluster_id"] for row in family)

