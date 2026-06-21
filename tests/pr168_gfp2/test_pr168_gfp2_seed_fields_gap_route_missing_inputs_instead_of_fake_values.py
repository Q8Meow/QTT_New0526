from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_seed_fields_gap_route_missing_inputs_instead_of_fake_values() -> None:
    for row in load("PR168_GFP2_TCADecompositionSeed.report.json"):
        assert row["required_input_state"] == "GAP_ROUTED_PENDING_ACCEPTED_REAL_DATA"
        assert row["accepted_truth_flag"] is False
