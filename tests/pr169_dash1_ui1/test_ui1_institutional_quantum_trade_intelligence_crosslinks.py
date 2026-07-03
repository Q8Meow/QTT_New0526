from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_institutional_quantum_trade_intelligence_crosslinks() -> None:
    text = ui_text()
    for token in (
        "TCA",
        "No-trade comparison",
        "Champion/challenger",
        "Quantum Control Center",
        "QKU / Formula / Stack Routes",
        "Trade Workbench",
    ):
        assert token in text
    assert boot_data()["institutional_metrics"]
    assert boot_data()["quantum_readiness"]
