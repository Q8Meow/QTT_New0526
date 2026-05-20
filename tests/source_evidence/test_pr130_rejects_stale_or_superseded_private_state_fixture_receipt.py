from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_rejects_stale_or_superseded_private_state_fixture_receipt():
    states = {record["private_state_read_receipt_state"] for record in support.rejection_receipts()}

    assert "REJECTED_STALE_PRIVATE_STATE_RECEIPT" in states
    assert "REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT" in states
    assert support.main_report()["stale_private_state_receipt_rejection_count"] == 1
    assert support.main_report()["superseded_private_state_receipt_rejection_count"] == 1
