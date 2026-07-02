from tests.pr169_dash1.conftest import json_doc, registry


def test_single_canonical_registry_is_declared_and_only_registry_source() -> None:
    rows = registry()
    manifest = json_doc("owner_dashboard_registry_manifest.json")

    assert rows
    assert manifest["single_canonical_dashboard_registry"] is True
    assert manifest["manual_edit_allowed_only_for"] == ["owner_dashboard_surface_registry.jsonl"]
    assert len({row["feature_id"] for row in rows}) == len(rows)
