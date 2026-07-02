from tests.pr169_dash1.conftest import jsonl


def test_acknowledgment_action_is_never_live_approval() -> None:
    ack = [row for row in jsonl("owner_action_registry.generated.jsonl") if row["action_code"] == "ACK_OWNER_PACKET"][0]
    assert ack["is_acknowledgment"] is True
    assert ack["is_live_approval"] is False
    assert ack["creates_order_authority"] is False
