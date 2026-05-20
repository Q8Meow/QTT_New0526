from src.qtt.stage1_prediction_markets.credential_readiness import policy
from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_policy_constants_are_centralized():
    constants = support.main_report()["PR131_NORMALIZED_POLICY_CONSTANTS"]

    assert tuple(constants["stage1_venue_ids"]) == policy.STAGE1_VENUE_IDS
    assert tuple(constants["shared_scope_ids"]) == policy.SHARED_SCOPE_IDS
    assert tuple(constants["allowed_alias_classes"]) == policy.ALLOWED_ALIAS_CLASSES
    assert tuple(constants["secret_like_rejection_classes"]) == policy.SECRET_LIKE_REJECTION_CLASSES
    assert tuple(constants["blocked_action_ids"]) == policy.BLOCKED_ACTION_IDS
    assert constants["package_authority_class"] == policy.PACKAGE_AUTHORITY_CLASS
