from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_no_forbidden_authority_counts_created():
    for rel_path in c.ALL_JSON_ARTIFACT_PATHS:
        payload = load(rel_path)
        for key in c.ZERO_AUTHORITY_COUNTS:
            assert payload[key] == 0
        assert all(value is False for value in payload["no_authority_confirmation"].values())

