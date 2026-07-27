from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    OWNER_IDS,
)


def test_current_owner_bindings_are_unique_and_external() -> None:
    assert len(OWNER_IDS) == 10
    assert len(set(OWNER_IDS)) == len(OWNER_IDS)
    assert "QKUComputationControlPlaneV1" not in OWNER_IDS
