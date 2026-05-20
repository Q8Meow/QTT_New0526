from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_rejects_missing_accepted_source_packet_for_cash_component():
    states = {record["runtime_cash_field_map_state"] for record in support.source_rejections()}

    assert "REJECTED_MISSING_ACCEPTED_SOURCE_PACKET" in states
    assert "REJECTED_MISSING_TARGET_FIELD_PATH" in states
    assert "REJECTED_MISSING_RAW_FIELD_LOCATOR" in states
    assert support.main_report()["missing_source_packet_rejection_count"] == 1
