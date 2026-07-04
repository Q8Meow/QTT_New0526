from tests.pr169_dash1_ui1.conftest import ui_text


def test_ui1_chart_time_range_buttons_clickable() -> None:
    text = ui_text()
    for token in ("1D", "1W", "1M", "3M", "YTD", "1Y", "ALL", "data-local-range"):
        assert token in text
