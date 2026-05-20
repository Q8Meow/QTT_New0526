from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_builds_fixture_private_state_receipts_for_three_stage1_venues():
    assert {record["venue_id"] for record in support.read_requests()} == support.stage1_venues()
    assert {record["venue_id"] for record in support.read_receipts()} == support.stage1_venues()
    assert {record["venue_id"] for record in support.account_receipts()} == support.stage1_venues()
    assert len(support.read_requests()) == 3
    assert len(support.read_receipts()) == 3
    assert len(support.account_receipts()) == 3
    assert all(
        record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        for record in support.read_receipts()
    )
