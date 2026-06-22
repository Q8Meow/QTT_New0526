from tests.pr168_gfp2r._helpers import record_rows


def test_pr168_gfp2r_every_value_has_upstream_downstream_crosswalk() -> None:
    rows = record_rows("PR168_GFP2R_EveryValueUpstreamDownstreamCrosswalk")
    assert rows
    assert all(row["upstream_refs"] and row["downstream_consumers"] for row in rows)
