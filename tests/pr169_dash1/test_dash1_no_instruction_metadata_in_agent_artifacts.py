from src.qtt.dashboard.owner_surface_models import FORBIDDEN_AGENT_FIELDS, REQUIRED_JSONL_OUTPUTS
from tests.pr169_dash1.conftest import jsonl


def test_agent_consumable_rows_do_not_include_codex_reasoning_metadata() -> None:
    for file_name in REQUIRED_JSONL_OUTPUTS:
        for row in jsonl(file_name):
            assert not (set(row) & FORBIDDEN_AGENT_FIELDS), (file_name, set(row) & FORBIDDEN_AGENT_FIELDS)
