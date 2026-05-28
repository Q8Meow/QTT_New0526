from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import route_records


def test_pr160_pr159_accepted_packets_used_only_when_target_field_exact():
    records = route_records(c.ReclassificationFinalRouteClass.ATOMICROWS_SOURCE_VALUE_MATERIALIZATION_ROUTE_PR161.value)
    assert records == []
