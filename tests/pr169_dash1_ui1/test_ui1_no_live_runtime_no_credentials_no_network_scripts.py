from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_no_live_runtime_no_credentials_no_network_scripts() -> None:
    data = boot_data()
    text = ui_text().lower()
    assert "https://" not in text
    assert "http://" not in text
    assert "cdn." not in text
    assert "fetch(" not in text
    boundary = data["authority_boundary"]
    assert boundary["credentialed_connector_clients"] is False
    assert boundary["cash_account_reads"] is False
    assert boundary["connector_writes"] is False
    assert boundary["live_order_authority"] is False
