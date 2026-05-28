from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records


def test_pr160_no_fake_owner_approvals_or_private_doc_attestations():
    assert master_report()["fake_owner_approval_count"] == 0
    assert master_report()["fake_private_doc_attestation_count"] == 0
    assert all(item["owner_approval_created_flag"] is False for item in records())
    assert all(item["private_doc_attestation_created_flag"] is False for item in records())
