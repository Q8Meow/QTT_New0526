from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.enums import FORBIDDEN_STATUS_VALUES


def test_pr166_sf_outputs_do_not_use_forbidden_status_values(pr166_sf_records, pr166_sf_summary):
    assert pr166_sf_summary["metadata_only_rows"] == 0
    assert pr166_sf_summary["placeholder_rows"] == 0
    assert pr166_sf_summary["unknown_status_rows"] == 0
    for rows in pr166_sf_records.values():
        for row in rows[:25]:
            assert not (set(str(value) for value in row.values() if isinstance(value, str)) & FORBIDDEN_STATUS_VALUES)
