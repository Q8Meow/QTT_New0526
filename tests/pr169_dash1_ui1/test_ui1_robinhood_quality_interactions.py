from tests.pr169_dash1_ui1.conftest import ui_text


def test_ui1_robinhood_quality_interactions() -> None:
    text = ui_text()
    for token in ("1D", "1W", "1M", "3M", "YTD", "1Y", "ALL"):
        assert token in text
    for token in ("chart-point", "openDrawer", "filter", "sort", "legend", "drilldownDrawer"):
        assert token in text
