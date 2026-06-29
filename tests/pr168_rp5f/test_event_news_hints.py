from ._helpers import assert_rows_have_contract


def test_event_news_hints_require_future_revalidation() -> None:
    rows = assert_rows_have_contract("event_news_hints.jsonl")

    assert all(row["source_update_or_news_sensitivity_hint"] == "SOURCE_REQUIRED" for row in rows)
    assert all(row["source_change_event_trigger_revalidation_required_flag"] is True for row in rows)
    assert all(row["accepted_source_fact_flag"] is False for row in rows)
