from src.qtt.dashboard.owner_surface_models import REQUIRED_JSONL_OUTPUTS
from tests.pr169_dash1.conftest import jsonl


def test_generated_outputs_are_not_empty_metadata_only_rows() -> None:
    for file_name in REQUIRED_JSONL_OUTPUTS:
        rows = jsonl(file_name)
        assert rows, file_name
        for row in rows:
            assert len(row) >= 6, (file_name, row)
