from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import summary


def test_pr159s_every_target_has_source_and_profit_provenance():
    records = summary()["records"]
    assert len(records) == 868
    assert all(record["source_provenance_tag"] in c.SOURCE_PROVENANCE_TAGS for record in records)
    assert all(record["profit_validation_tag"] in c.PROFIT_VALIDATION_TAGS for record in records)
    assert sum(1 for record in records if record["replay_paper_candidate_flag"] is True) == 530
    assert sum(1 for record in records if record["source_provenance_tag"] == c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value) == 338

