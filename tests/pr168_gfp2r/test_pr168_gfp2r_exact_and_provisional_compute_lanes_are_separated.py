from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_exact_and_provisional_compute_lanes_are_separated() -> None:
    assert {row["compute_lane"] for row in rows("formula_execution")} == {"PROVISIONAL_DATA_CONSUMER"}
    assert all(row["proof_authority_class"] == "PROVISIONAL_DATA_CONSUMER_NON_PROOF" for row in rows("provisional_compute"))
