from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework.paper_pretrade_checks import (
    REQUIRED_CHECKS,
)


def test_paper_pretrade_checks_cover_pass_and_reject(records):
    rows = records("PR163_PaperPreTradeCheckReceiptRegistry.report.json")
    statuses = {row["pretrade_status"] for row in rows}
    assert "PAPER_PRETRADE_PASS" in statuses
    assert "PAPER_PRETRADE_REJECT_WITH_EXACT_REASON" in statuses
    assert set(REQUIRED_CHECKS).issubset(rows[0]["check_results"])
