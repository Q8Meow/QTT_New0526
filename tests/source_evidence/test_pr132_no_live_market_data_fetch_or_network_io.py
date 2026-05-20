import ast
from pathlib import Path

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_live_market_data_fetch_or_network_io():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["live_market_data_fetch_count"] == 0
    assert evidence["network_io_count"] == 0
    assert evidence["rest_client_import_count"] == 0
    assert evidence["websocket_client_import_count"] == 0
    assert evidence["socket_import_count"] == 0
    assert evidence["network_import_count"] == 0

    scanned = [
        *Path("src/qtt/stage1_prediction_markets/market_data_ingest").glob("*.py"),
        *Path("tools").glob("venue_market_data_ingest*.py"),
        *Path("tests/source_evidence").glob("*pr132*market_data_ingest*.py"),
    ]
    banned = set(policy.BANNED_IMPORT_MODULES)
    for path in scanned:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imported = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            assert not any(
                name == item or name.startswith(f"{item}.")
                for name in imported
                for item in banned
            )
