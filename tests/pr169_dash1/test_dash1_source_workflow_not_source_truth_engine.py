from tests.pr169_dash1.conftest import jsonl


def test_source_panel_routes_workflow_without_source_truth_creation() -> None:
    rows = jsonl("owner_source_panel_contract.generated.jsonl")
    assert rows
    assert all(row["source_truth_created"] is False for row in rows)
    assert all(row["activation_route"] for row in rows)
