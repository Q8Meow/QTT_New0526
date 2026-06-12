from .conftest import assert_rows


def test_pr166_sf_repaired_payloads_are_executable_or_routed(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairedPayloadRegistry.report.json")
    assert len(rows) == 6502
    assert all(row["deterministic_callable"] == "repaired_net_edge_after_costs" for row in rows[:50])
    assert all(row["smoke_test_result"] == "PASS" for row in rows[:50])
