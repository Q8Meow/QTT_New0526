from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (
    TRANCHE_A_TRUST_BOUNDARIES,
    TrustBoundary,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    validate_domain,
)


def test_declared_trust_boundaries_cover_all_frozen_security_surfaces() -> None:
    assert TRANCHE_A_TRUST_BOUNDARIES == tuple(TrustBoundary)
    assert {item.value for item in TRANCHE_A_TRUST_BOUNDARIES} == {
        "DATA_FLOW",
        "PRINCIPAL",
        "TOOL",
        "STORE",
        "PROVIDER_INTERFACE",
        "DASHBOARD_REQUEST",
        "RELEASE_SURFACE",
    }
    assert validate_domain("security").passed
