from tests.pr169_dash1.conftest import jsonl


def test_every_action_has_receipt_template_and_audit_boundary() -> None:
    actions = {row["action_code"] for row in jsonl("owner_action_registry.generated.jsonl")}
    receipts = {row["action_code"]: row for row in jsonl("owner_action_receipt_template.generated.jsonl")}
    assert set(receipts) == actions
    for row in receipts.values():
        assert row["owner_action_must_be_audited"] is True
        assert row["owner_action_may_not_bypass_execution_router"] is True
