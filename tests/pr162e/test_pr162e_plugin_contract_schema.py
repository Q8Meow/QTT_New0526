from pathlib import Path

from tests.pr162e.helpers import REPO_ROOT, plugin_rows


def test_plugin_contract_schema_and_rows_exist():
    assert (REPO_ROOT / "src/qtt/stage1_prediction_markets/pr162e_plugin_framework/schemas/plugin_contract.schema.json").exists()
    rows = plugin_rows()
    assert len(rows) == 559
    assert all(row["authority_envelope_ref"] for row in rows)
