from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_pwa_native_runtime_boundaries_contract_only() -> None:
    for name in (
        "owner_dashboard_pwa_manifest_contract.generated.json",
        "owner_dashboard_native_shell_contract.generated.json",
        "owner_dashboard_mobile_runtime_boundary.generated.json",
    ):
        payload = ui_doc(name)
        meta = payload["meta"]
        assert meta["runtime_side_effect_allowed"] is False
        assert meta["credential_access_allowed"] is False
        assert meta["connector_access_allowed"] is False
        assert meta["order_execution_allowed"] is False
