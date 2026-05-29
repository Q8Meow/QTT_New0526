from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_atomicrows_candidate_mapping_preserves_universe_and_no_bundle():
    payload = load(c.ATOMICROWS_CANDIDATE_READINESS_DELTA_PATH)
    assert payload["record_count"] == 845
    assert all(record["atomicrows_research_candidate_ready"] is True for record in payload["records"])
    assert all(record["atomicrows_official_source_ready"] is False for record in payload["records"])
    assert all(record["final_bundle_created_flag"] is False for record in payload["records"])
    assert all(record["bundle_checksum_hash_authority_created_flag"] is False for record in payload["records"])

