from ._helpers import assert_rows_have_contract


def test_portfolio_capacity_context_carries_future_consumer_refs() -> None:
    rows = assert_rows_have_contract("port_cap.jsonl")

    assert all(row["venue_exposure"] == "SOURCE_REQUIRED" for row in rows)
    assert all(row["capacity_fit"] == "SOURCE_REQUIRED" for row in rows)
    assert all(row["crowding_risk"] == "SOURCE_REQUIRED" for row in rows)
    assert all({"RP5G", "RANK4", "QOPT1"} <= set(row["future_consumer_refs"]) for row in rows)

