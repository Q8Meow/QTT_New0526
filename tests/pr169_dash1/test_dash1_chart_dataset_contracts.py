from tests.pr169_dash1.conftest import jsonl


def test_each_interactive_chart_has_dataset_contract() -> None:
    charts = jsonl("owner_interactive_chart_registry.generated.jsonl")
    contracts = {row["dataset_contract_id"] for row in jsonl("owner_chart_dataset_contract.generated.jsonl")}
    assert {row["data_contract_ref"] for row in charts}.issubset(contracts)
    assert all(row["read_only_data_semantics"] is True for row in jsonl("owner_chart_dataset_contract.generated.jsonl"))
