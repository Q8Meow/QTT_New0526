def test_portfolio_ledger_cash_equation(records):
    rows = records("PR163_PaperPortfolioLedgerSnapshotRegistry.report.json")
    for row in rows[:250]:
        lhs = round(row["paper_cash_start"] - row["reserved_cash"] - row["spent_cash"] + row["received_cash"], 6)
        assert lhs == row["paper_cash_end"]
        assert row["runtime_cash_receipt_created"] is False
