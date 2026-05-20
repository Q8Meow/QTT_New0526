from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    REPO_ROOT,
    binding_report,
    main_report,
)


def test_pr128_no_network_io_or_production_connector_client():
    report = main_report()
    assert report["network_io_created_count"] == 0
    assert report["production_connector_client_count"] == 0
    assert report["connector_production_client_created_count"] == 0

    source_root = REPO_ROOT / "src/qtt/source_evidence/cross_venue_execution_normalization"
    forbidden_tokens = ("requests", "urllib", "socket", "http.client")
    for source_path in source_root.glob("*.py"):
        text = source_path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_tokens)
    for record in binding_report()["phase_binding_records"]:
        assert record["network_io_allowed_flag"] is False
        assert record["production_connector_use_allowed_flag"] is False
