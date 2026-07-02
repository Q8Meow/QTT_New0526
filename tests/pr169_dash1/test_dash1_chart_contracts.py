from src.qtt.dashboard.owner_dashboard_projection_builder import CHART_CONTRACTS
from tests.pr169_dash1.conftest import jsonl


def test_required_chart_contracts_are_present_and_read_only() -> None:
    rows = jsonl("owner_chart_surface_contract.generated.jsonl")
    assert {row["chart_id"] for row in rows} == set(CHART_CONTRACTS)
    for row in rows:
        assert row["source_dataset_refs"]
        assert row["staleness_policy"]
        assert row["empty_state_policy"]
        assert row["authority_boundary_ref"]
