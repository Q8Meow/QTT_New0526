from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_provisional_compute_is_non_proof_and_not_exact_qku_proof() -> None:
    provisional_rows = rows("provisional_compute")
    assert provisional_rows
    assert all(row["provisional_flag"] is True for row in provisional_rows)
    assert all(row["proof_authority_class"] == "PROVISIONAL_DATA_CONSUMER_NON_PROOF" for row in provisional_rows)
