from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_future_production_launch_path():
    main = support.main_report()

    assert main["future_official_source_production_path_recorded"] is True
    assert main["future_production_launch_path_preserved"] is True
    assert main["production_values_filled_by_later_official_source_or_private_state_receipt_prs"] is True
    assert len(main["future_official_source_production_path"]) == 16
    assert all(record["future_production_launch_path_preserved"] is True for record in support.field_maps())
