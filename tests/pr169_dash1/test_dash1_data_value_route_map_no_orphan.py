from pathlib import Path

from src.qtt.dashboard.owner_surface_models import REQUIRED_JSONL_OUTPUTS, REQUIRED_JSON_OUTPUTS, REQUIRED_UI_OUTPUTS
from tests.pr169_dash1.conftest import jsonl


def test_data_value_route_map_covers_every_generated_file_family() -> None:
    rows = jsonl("owner_data_value_route_map.generated.jsonl")
    mapped = {Path(row["artifact_path"]).name for row in rows}
    expected = {Path(name).name for name in ("owner_dashboard_surface_registry.jsonl", *REQUIRED_JSONL_OUTPUTS, *REQUIRED_JSON_OUTPUTS, *REQUIRED_UI_OUTPUTS)}
    assert expected.issubset(mapped)
    assert all(row["canonical_source_ref"] == "owner_dashboard_surface_registry.jsonl" for row in rows)
