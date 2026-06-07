from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_consumes_every_pr164_trigger():
    rows = load_records("PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json")
    assert summary()["pr164_pr163c_trigger_rows_consumed"] == 1266
    assert len(rows) == summary()["pr164_pr163c_trigger_rows_consumed"]
    assert len({(row["candidate_packet_id"], row["qku_id"], row["pr164_trigger_ref"]) for row in rows}) == len(rows)
