from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.identity_adapter import (
    RP5CIdentityAdapterV1,
)


def test_identity_resolution_binds_to_rp5c_lineage() -> None:
    root = Path(__file__).resolve().parents[4]
    view = RP5CIdentityAdapterV1(root).get_formula("FORMULA_QKU")
    assert view.identity_row_id == "RP5C_IDENTITY_00000001"
    assert view.formula_id == "FORMULA_QKU"
    assert view.source_owner == "RP5C_IDENTITY_LIBRARY"
    assert view.library_version == "ImmutableQKUFormulaLibraryV1"
