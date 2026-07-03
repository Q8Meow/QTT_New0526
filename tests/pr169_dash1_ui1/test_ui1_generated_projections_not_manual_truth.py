from tests.pr169_dash1_ui1.conftest import UI, UI_ARTIFACT_FILES, ui_doc


def test_ui1_generated_projections_not_manual_truth() -> None:
    for name in UI_ARTIFACT_FILES:
        assert (UI / name).exists(), name
        meta = ui_doc(name)["meta"]
        assert meta["generated_from"].startswith("owner_dashboard_surface_registry.jsonl")
        assert meta["manual_edit_allowed"] is False
        assert meta["runtime_truth_authority"] is False
        assert meta["agent_consumable_authority"] is False
