from src.qtt.stage1_prediction_markets.pr162r_b_replay_paper_data_binding_completion import paths as p


def test_report_manifest_and_shards(records):
    rows = records("PR162R_B_ReportManifest.report.json")
    assert {row["report_filename"] for row in rows} == set(p.REPORT_FILENAMES)
    assert all(row["sharded_flag"] is False for row in rows)
