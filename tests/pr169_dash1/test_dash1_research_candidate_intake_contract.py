from src.qtt.dashboard.owner_dashboard_projection_builder import RESEARCH_SOURCE_FAMILIES
from tests.pr169_dash1.conftest import jsonl


def test_research_candidate_intake_supports_required_source_families_without_truth_creation() -> None:
    rows = jsonl("owner_research_candidate_intake_contract.generated.jsonl")
    assert {row["source_family"] for row in rows} == set(RESEARCH_SOURCE_FAMILIES)
    assert all(row["source_truth_created"] is False for row in rows)
    assert all("SOURCE_CANDIDATE_CREATED" not in row.get("first_pipeline_state", "") for row in rows)
