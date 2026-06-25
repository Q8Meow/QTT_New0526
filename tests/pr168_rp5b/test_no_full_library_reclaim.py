from tests.pr168_rp5b._helpers import final_summary, load_rows


def test_no_full_library_reclaim() -> None:
    assert final_summary()["formula_reclaim_full_library_count"] == 0
    assert all(row.get("future_canonical_reclaim_pr") == "PR168_RP5C" for row in load_rows("qku_formula_identity_preservation_rows"))
