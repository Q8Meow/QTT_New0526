from src.qtt.dashboard.owner_dashboard_projection_builder import INTERACTIVE_CHART_FAMILIES
from tests.pr169_dash1.conftest import jsonl


def test_interactive_chart_registry_has_all_required_families() -> None:
    rows = jsonl("owner_interactive_chart_registry.generated.jsonl")
    assert {row["chart_family"] for row in rows} == set(INTERACTIVE_CHART_FAMILIES)
    assert all(row["data_contract_ref"] for row in rows)
