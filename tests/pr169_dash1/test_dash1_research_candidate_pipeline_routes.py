from src.qtt.dashboard.owner_dashboard_projection_builder import RESEARCH_PIPELINE_STATES
from tests.pr169_dash1.conftest import jsonl


def test_research_pipeline_connects_source_llm_qku_replay_paper_and_promotion_routes() -> None:
    rows = jsonl("owner_research_candidate_pipeline_view.generated.jsonl")
    assert {row["pipeline_state"] for row in rows} == set(RESEARCH_PIPELINE_STATES)
    for row in rows:
        assert row["source_workflow_ref"]
        assert row["llm_extraction_ref"]
        assert row["qku_materialization_ref"]
        assert row["replay_paper_route_ref"]
        assert row["promotion_route_ref"]
