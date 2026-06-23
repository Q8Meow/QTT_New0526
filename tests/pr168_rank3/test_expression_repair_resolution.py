from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_expression_repair_resolutions_have_routes() -> None:
    assert_rank3_valid()
    resolutions = rows("expression_repair_resolution")
    assert len(resolutions) == 7
    assert all(row["formula_to_pnl_map_ref"] for row in resolutions)
    assert all(row["downstream_route"] == "MAP4_FORMULA_REPAIR_AND_RP4_RETEST" for row in resolutions)
