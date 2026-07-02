from tests.pr169_dash1.conftest import jsonl


def test_owner_global_authority_policy_preserves_receipt_and_external_fact_boundary() -> None:
    row = jsonl("owner_global_authority_policy.generated.jsonl")[0]
    assert row["owner_global_internal_authority"] is True
    assert row["owner_action_receipt_required"] is True
    assert row["owner_action_may_not_bypass_required_execution_router"] is True
    assert row["external_fact_receipt_required_for_external_truth"] is True
    assert row["owner_may_not_convert_missing_external_fact_or_missing_runtime_receipt_into_truth_by_assertion"] is True
