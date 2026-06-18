from tests.pr162e.helpers import plugin_rows


def test_overfit_fdr_fields_are_materialized():
    row = plugin_rows()[0]
    control = row["overfit_control"]
    assert control["purged_walk_forward_split_ref"]
    assert control["no_single_best_backtest_path_promotion"] is True
