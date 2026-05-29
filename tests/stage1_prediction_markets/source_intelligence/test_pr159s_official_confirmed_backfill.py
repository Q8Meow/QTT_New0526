from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_official_confirmed_backfill_preserves_prior_packets():
    payload = load(c.OFFICIAL_CONFIRMED_BACKFILL_PATH)
    assert payload["official_confirmed_backfill_count"] == 11
    assert all(record["source_provenance_tag"] == c.SourceProvenanceTag.OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR.value for record in payload["records"])
    assert all(record["official_confirmed_flag"] is True for record in payload["records"])
    assert all(record["official_source_packet_id"] for record in payload["records"])

