from tests.source_evidence.pr127_execution_lifecycle_support import (
    REPO_ROOT,
    main_report,
    model_records,
)


def test_pr127_no_network_io_or_production_connector_client():
    report = main_report()

    assert report["network_io_created_count"] == 0
    assert report["connector_production_client_created_count"] == 0
    assert report["production_connector_client_count"] == 0
    for model in model_records():
        assert model["network_io_allowed_flag"] is False
        assert model["production_connector_use_allowed_flag"] is False

    checked_files = [
        "src/qtt/source_evidence/execution_lifecycle/builder.py",
        "src/qtt/source_evidence/execution_lifecycle/validator.py",
        "tools/validate_per_venue_execution_lifecycle_model.py",
        "tools/per_venue_execution_lifecycle_model_builder.py",
    ]
    forbidden_tokens = ("requests", "urllib", "socket", "aiohttp", "websocket")
    for relative_path in checked_files:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_tokens)
