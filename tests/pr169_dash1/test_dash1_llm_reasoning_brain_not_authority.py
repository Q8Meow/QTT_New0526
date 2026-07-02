from tests.pr169_dash1.conftest import jsonl


def test_llm_view_allows_reasoning_actions_but_forbids_root_authority() -> None:
    rows = jsonl("owner_reasoning_brain_view_contract.generated.jsonl")
    assert rows
    for row in rows:
        assert "research" in row["LLM_allowed_actions"]
        assert "order_release" in row["LLM_forbidden_authority"]
        assert row["live_LLM_call_created"] is False
