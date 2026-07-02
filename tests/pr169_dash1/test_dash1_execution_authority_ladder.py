from src.qtt.dashboard.owner_dashboard_projection_builder import EXECUTION_LADDER_STATES
from tests.pr169_dash1.conftest import jsonl


def test_execution_authority_ladder_has_required_states_without_order_authority() -> None:
    rows = jsonl("owner_execution_authority_ladder_view.generated.jsonl")
    assert [row["current_stage"] for row in rows] == list(EXECUTION_LADDER_STATES)
    for row in rows:
        assert "buy" in row["forbidden_actions_in_dash1"]
        assert row["execution_router_gate_refs"]
