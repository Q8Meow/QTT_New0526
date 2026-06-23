from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_downstream_handoffs_cover_required_families() -> None:
    assert_rank3_valid()
    families = {row["handoff_family"] for row in rows("downstream_handoff")}
    assert {"RANK4", "RP4", "PR165B", "PR162EQ", "DATA1B", "SOURCE_PROVENANCE", "DASHBOARD"} <= families
