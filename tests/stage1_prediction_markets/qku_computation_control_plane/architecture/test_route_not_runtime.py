from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ContractFieldV1,
    OperationContractV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    ReadinessProjectionProtocolV1,
)


class FixtureReadinessProjection:
    def describe_readiness_route(self, qku_id: str) -> OperationContractV1:
        return OperationContractV1(
            f"readiness:{qku_id}",
            "QKUIdentityV1",
            "ReadinessRouteV1",
            "NoMutationFailClosedV1",
            request_fields=(
                ContractFieldV1("qku_id", "CanonicalQkuIdV1"),
            ),
            response_fields=(
                ContractFieldV1("route", "ReadinessRouteV1"),
            ),
            failure_reason_codes=(ReasonCode.OWNER_DATA_MISSING,),
        )


def test_projection_protocol_describes_route_without_applying_state() -> None:
    projection = FixtureReadinessProjection()
    assert isinstance(projection, ReadinessProjectionProtocolV1)
    route = projection.describe_readiness_route("QKU-1")
    assert not route.runtime_effect_authorized
    assert route.output_contract == "ReadinessRouteV1"
