from src.qtt.dashboard.owner_action_registry import ACTION_DEFINITIONS
from tests.pr169_dash1.conftest import jsonl, registry


def test_all_registry_action_refs_resolve_to_central_action_registry() -> None:
    action_rows = jsonl("owner_action_registry.generated.jsonl")
    actions = {row["action_code"] for row in action_rows}
    assert actions == set(ACTION_DEFINITIONS)
    for row in registry():
        assert set(row["action_code_refs"]).issubset(actions)
    assert len(actions) == len(action_rows)
