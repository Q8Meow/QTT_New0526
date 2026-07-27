from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    OperationContractV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    ReadinessProjectionProtocolV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    OPERATION_SCHEMA_REGISTRY,
)


class FixtureReadinessProjection:
    def describe_readiness_route(self, qku_id: str) -> OperationContractV1:
        if not qku_id:
            raise ValueError("qku_id is required")
        return OPERATION_SCHEMA_REGISTRY["ST10-OP::03"]


def test_projection_protocol_describes_route_without_applying_state() -> None:
    projection = FixtureReadinessProjection()
    assert isinstance(projection, ReadinessProjectionProtocolV1)
    route = projection.describe_readiness_route("QKU-1")
    assert not route.runtime_effect_authorized
    assert route.operation_name == "resolve_applicable_stack"
