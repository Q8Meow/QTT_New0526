from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_downstream_handoffs_route_all_major_consumers() -> None:
    assert_recovery1_valid()
    families = {row["handoff_family"] for row in rows("downstream_handoff")}
    assert {"RP5_RANK4_QOPT1", "DATA1B", "MAP4", "SOURCE_PROVENANCE", "PR165B", "PR162E_Q"} <= families
