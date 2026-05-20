from src.qtt.stage1_prediction_markets.credential_readiness.alias import secret_like_findings
from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_aliases_are_placeholders_not_secret_values():
    for record in support.alias_records():
        assert record["alias_placeholder_value"].startswith("PR131_")
        assert record["alias_value_is_secret"] is False
        assert record["alias_value_is_live_credential"] is False
        assert record["alias_value_is_environment_lookup"] is False
        assert secret_like_findings(record) == []
