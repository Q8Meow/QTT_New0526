import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    FormulaRuntimeSnapshotV1,
    LatencyHotPathSnapshotBoundaryAdapterV1,
)


def test_snapshot_is_version_pinned_contract_only() -> None:
    snapshot = FormulaRuntimeSnapshotV1(
        "snapshot-1",
        "spec-1",
        "implementation-v1",
        "binding-v1",
        "parameter-v1",
        ("source-epoch-1",),
    )
    assert not snapshot.activated
    with pytest.raises(ContractValidationError) as caught:
        FormulaRuntimeSnapshotV1(
            "snapshot-2",
            "spec-1",
            "implementation-v1",
            "binding-v1",
            "parameter-v1",
            ("source-epoch-1",),
            activated=True,
        )
    assert caught.value.reason_code is ReasonCode.RUNTIME_EFFECT_FORBIDDEN
    with pytest.raises(ContractValidationError):
        FormulaRuntimeSnapshotV1(
            "snapshot-3",
            "spec-1",
            "implementation-v1",
            "binding-v1",
            "parameter-v1",
            ("source-epoch-1", "source-epoch-1"),
        )
    owner = LatencyHotPathSnapshotBoundaryAdapterV1.load_view()
    assert owner.latency_scope == "PRECOMPUTED_SNAPSHOT_BOUNDARY"
    assert "BASE_HEAD_PREFIX" not in owner.report_contracts
    assert not owner.activation_allowed
