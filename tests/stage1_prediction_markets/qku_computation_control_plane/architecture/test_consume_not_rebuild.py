from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.plugin_adapter import (
    PR162EPluginAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    load_legacy_formula_comparators,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    LatencyHotPathSnapshotBoundaryAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    ExistingOwnerProjectionAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (
    PR162EQuantumAdapterV1,
    QuantumModelKind,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    SourceRevalidationSchedulerAdapterV1,
)


def test_existing_plugin_and_mapper_owners_are_consumed_read_only() -> None:
    root = Path(__file__).resolve().parents[4]
    plugin_view = PR162EPluginAdapterV1(root).load_families()[0]
    quantum_view = PR162EQuantumAdapterV1(root).load_mappings(
        QuantumModelKind.QUBO
    )[0]
    assert plugin_view.source_owner == "PR162E_PLUGIN_FRAMEWORK"
    assert quantum_view.source_owner == "PR162E_Q_QUANTUM_AUTOMAPPER"
    projections = ExistingOwnerProjectionAdapterV1(root)
    projection_views = (
        projections.load_readiness(),
        projections.load_pretrade(),
        projections.load_svc(),
        projections.load_agent_orch(),
    )
    assert {view.owner_id for view in projection_views} == {
        "READINESS1",
        "PRETRADE1",
        "SVC1",
        "AGENT_ORCH1",
    }
    assert not any(
        view.projection_mutation_allowed or view.runtime_effect_allowed
        for view in projection_views
    )
    source_view = SourceRevalidationSchedulerAdapterV1.load_view()
    assert source_view.live_critical_interval == "P1D"
    assert source_view.low_risk_interval == "P7D"
    assert not source_view.network_retrieval_allowed
    snapshot_view = LatencyHotPathSnapshotBoundaryAdapterV1.load_view()
    assert snapshot_view.source_version == "PR137L"
    assert not snapshot_view.activation_allowed
    comparators = load_legacy_formula_comparators()
    assert len(comparators) == 7
    assert not any(view.exact_decimal_alias for view in comparators)
    with pytest.raises(FrozenInstanceError):
        plugin_view.plugin_count = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quantum_view.backend_execution_allowed = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        projection_views[0].runtime_effect_allowed = True  # type: ignore[misc]
