from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_field_map_requires_accepted_source_packet_per_component():
    for record in support.field_maps():
        assert record["accepted_source_evidence_required_flag"] is True
        assert record["source_packet_ids_by_component"]
        assert record["accepted_source_packet_digest_by_component"]
        assert record["target_field_path_by_component"]
        assert record["raw_venue_field_locator_by_component"]
