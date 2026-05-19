from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    REPO_ROOT,
    artifacts,
)


def test_pr126_no_network_io_production_import_order_execution():
    report = artifacts()["main_report"]

    assert report["network_io_created_count"] == 0
    assert report["connector_production_client_created_count"] == 0
    assert report["order_authority_created"] is False
    assert report["runtime_cash_receipts_created_count"] == 0

    checked_files = [
        "src/qtt/source_evidence/connector_semantic_implementation/gate.py",
        "src/qtt/source_evidence/connector_semantic_implementation/manifest.py",
        "src/qtt/source_evidence/connector_semantic_implementation/validator.py",
        "tools/validate_connector_semantic_binding_implementation_gate.py",
        "tools/connector_semantic_binding_implementation_gate.py",
    ]
    forbidden_tokens = ("requests", "urllib", "socket", "aiohttp", "websocket")
    for relative_path in checked_files:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_tokens)
