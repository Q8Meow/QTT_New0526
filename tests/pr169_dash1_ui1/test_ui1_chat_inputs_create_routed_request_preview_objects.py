from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc


def test_ui1_chat_inputs_create_routed_request_preview_objects() -> None:
    catalog = ui_doc("owner_dashboard_chat_trade_request_catalog.generated.json")
    objects = {row["object_type"] for row in catalog["requests"]}
    assert "OwnerMessageV1" in objects
    assert "OwnerTradeCheckRequestV1" in objects
    assert "QuantumStructureMappingRequestV1" in objects
    assert all(row["runtime_side_effect"] is False for row in catalog["requests"])
    assert boot_data()["communication_parity"]["chat_visible_desktop_mobile_pwa_native_telegram"] is True
