from pathlib import Path

from src.qtt.dashboard.owner_surface_models import REQUIRED_JSONL_OUTPUTS
from tests.pr169_dash1.conftest import BASE, jsonl, registry_ids


def test_every_generated_projection_row_traces_to_registry() -> None:
    ids = registry_ids()
    for file_name in REQUIRED_JSONL_OUTPUTS:
        if file_name == "owner_surface_projection_manifest.generated.jsonl":
            continue
        for row in jsonl(file_name):
            assert row["generated_from"] == "owner_dashboard_surface_registry.jsonl", file_name
            assert row["manual_edit_allowed"] is False, file_name
            assert row["authoritative_source"] == "owner_dashboard_surface_registry.jsonl", file_name
            assert row["registry_row_ref"].rsplit("::", 1)[-1] in ids, (file_name, row)
    assert (BASE / "owner_dashboard_surface_registry.jsonl").exists()
    assert not any(Path(name).name.endswith("_hint.jsonl") for name in REQUIRED_JSONL_OUTPUTS)
