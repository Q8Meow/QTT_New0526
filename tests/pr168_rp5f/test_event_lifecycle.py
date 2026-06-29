from ._helpers import assert_rows_have_contract


def test_event_lifecycle_requires_revalidation() -> None:
    rows = assert_rows_have_contract("event_lifecycle.jsonl")

    assert all(row["event_lifecycle_id"] for row in rows)
    assert all(row["source_revalidation_required_flag"] is True for row in rows)
    assert all(row["lifecycle_tradeability_status"].startswith("SOURCE_REQUIRED") for row in rows)
