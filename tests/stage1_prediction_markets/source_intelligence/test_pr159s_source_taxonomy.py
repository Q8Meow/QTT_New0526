from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_source_taxonomy_centralizes_required_enums():
    taxonomy = load(c.SOURCE_TAXONOMY_PATH)
    enum_sets = taxonomy["central_enum_value_sets"]
    assert c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value in enum_sets["source_provenance_tag"]
    assert c.ProfitValidationTag.PROFIT_NOT_TESTED.value in enum_sets["profit_validation_tag"]
    assert c.OpenResearchSourceClass.X_POST.value in enum_sets["open_research_source_class"]
    assert c.AuthorityClass.ACCEPTED_REPLAY_PAPER_TEST_CANDIDATE.value in enum_sets["authority_class"]

