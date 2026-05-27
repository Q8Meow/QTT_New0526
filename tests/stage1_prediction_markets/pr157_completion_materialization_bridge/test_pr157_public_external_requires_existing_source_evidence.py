from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_registry


def test_pr157_public_external_requires_existing_source_evidence():
    records = pr154_registry()["records"]
    captured_complete = [
        record
        for record in records
        if record["source_population"] == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value
    ]
    assert captured_complete
    assert all(record["source_packet_ref_or_null"] for record in captured_complete)
    assert all(record["quote_span_or_machine_field_locator_or_null"] for record in captured_complete)
